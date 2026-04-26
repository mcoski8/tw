"""
Encode candidate rule sets as strategy functions and measure agreement
with the multiway-robust setting on all 6M canonical hands.

Three strategies are implemented:

  S0  NAIVE104  — always setting 104 (sort cards descending, slice [1, 2, 4]).
                  Baseline. Established at 20.1% agreement in probe_rules.

  S1  SIMPLE    — top of priority chain only. No conditionals on tier
                  composition. Gives the floor of "rules without nuance."
                    1. quads        → split 2-2-?
                    2. trips_pair   → trips → mid (no displacement consideration)
                    3. trips        → trips → mid
                    4. any pair     → highest pair → mid
                    5. default      → setting 104

  S2  REFINED   — adds the displacement and DS-feasibility considerations
                  that mining surfaced as material:
                    + With multiple pairs ≥ 9, the higher pair always wins mid
                    + With trips and high pair (≥ 9), STILL trips → mid
                      (mining showed 70.91% trips → mid for high/high; we
                      pick the dominant action even though it's not 95%+)
                    + Three-pair → highest pair → mid (singleton goes to top)
                    + Top selection: highest UNPAIRED rank when one exists
                    + Bot tie-breaker: when 2 candidate (top, mid) choices
                      give the same priority class, prefer the one whose bot
                      is double-suited.

For each strategy and each canonical hand we compare strategy_setting against
multiway_robust_setting and report:
  * overall agreement
  * agreement by hand category
  * agreement by agreement_class (unanimous vs contested)
  * worst-fail subset (rule fires + setting differs) for diagnosis
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tw_analysis import read_canonical_hands  # noqa: E402
from tw_analysis.features import decode_tier_positions  # noqa: E402


# ----------------------------------------------------------------------
# Inverse decoder: (top_pos, mid_positions) -> setting_index.
# ----------------------------------------------------------------------

# Pre-compute the 15 mid-pair lookups that decode_tier_positions uses.
_MID_PAIRS_OF_6 = []
for a in range(6):
    for b in range(a + 1, 6):
        _MID_PAIRS_OF_6.append((a, b))
_MID_PAIRS_INDEX = {p: i for i, p in enumerate(_MID_PAIRS_OF_6)}


def positions_to_setting_index(top_pos: int, mid_pos: tuple[int, int]) -> int:
    """Inverse of decode_tier_positions. ``mid_pos`` need not be sorted."""
    a, b = sorted(mid_pos)
    if a == top_pos or b == top_pos or a == b:
        raise ValueError(f"invalid positions: top={top_pos} mid={mid_pos}")
    remaining = [i for i in range(7) if i != top_pos]
    a_in_6 = remaining.index(a)
    b_in_6 = remaining.index(b)
    if a_in_6 > b_in_6:
        a_in_6, b_in_6 = b_in_6, a_in_6
    mid_inner = _MID_PAIRS_INDEX[(a_in_6, b_in_6)]
    return top_pos * 15 + mid_inner


# Sanity: round-trip every setting index.
for _s in range(105):
    _t, _m, _b = decode_tier_positions(_s)
    assert positions_to_setting_index(_t, _m) == _s, f"round-trip fail at {_s}"


# ----------------------------------------------------------------------
# Hand decomposition helpers used by all strategies.
# ----------------------------------------------------------------------

def hand_decompose(hand: np.ndarray) -> dict:
    """
    Compute the structures every strategy needs from a 7-card hand
    (uint8 array, sorted ascending). Returned dict has:
      ranks, suits          — np.array length 7
      rank_to_positions     — dict rank -> list[positions]
      suit_to_positions     — dict suit -> list[positions]
      pairs, trips, quads   — desc-sorted lists of (rank, [positions])
      singletons            — desc-sorted list of (rank, position)
    """
    ranks = (hand // 4) + 2
    suits = hand % 4
    rank_to_positions: dict[int, list[int]] = {}
    suit_to_positions: dict[int, list[int]] = {}
    for i in range(7):
        rank_to_positions.setdefault(int(ranks[i]), []).append(i)
        suit_to_positions.setdefault(int(suits[i]), []).append(i)

    quads, trips, pairs = [], [], []
    singletons = []
    for r, positions in sorted(rank_to_positions.items(), reverse=True):
        if len(positions) == 4:
            quads.append((r, positions))
        elif len(positions) == 3:
            trips.append((r, positions))
        elif len(positions) == 2:
            pairs.append((r, positions))
        else:
            singletons.append((r, positions[0]))
    return {
        "ranks": ranks,
        "suits": suits,
        "rank_to_positions": rank_to_positions,
        "suit_to_positions": suit_to_positions,
        "quads": quads,
        "trips": trips,
        "pairs": pairs,
        "singletons": singletons,
    }


def bot_is_double_suited(suits_at_positions: list[int]) -> bool:
    """Suit profile of 4 cards is exactly (2, 2)."""
    if len(suits_at_positions) != 4:
        return False
    counts = sorted(Counter(suits_at_positions).values(), reverse=True)
    while len(counts) < 2:
        counts.append(0)
    return counts[0] == 2 and counts[1] == 2


# ----------------------------------------------------------------------
# Strategy 0: NAIVE104 — always setting 104 (top=highest, mid=next 2,
# bot=lowest 4). The canonical-hand sort means highest byte is last.
# Setting 104: top_pos=6, mid=(4,5), bot=(0,1,2,3) — verified in tests.
# ----------------------------------------------------------------------

def strategy_naive_104(hand: np.ndarray) -> int:
    return 104


# ----------------------------------------------------------------------
# Strategy 1: SIMPLE — basic priority chain.
# ----------------------------------------------------------------------

def _pick_top_default(d: dict, used_positions: set[int]) -> int:
    """
    Default top-pick: highest UNPAIRED singleton rank in remaining cards.
    Falls back to highest remaining rank if every remaining card is paired.
    """
    remaining = [i for i in range(7) if i not in used_positions]
    # Try singletons first (rank appears exactly once in the WHOLE hand).
    sing_in_remaining = [(r, p) for (r, p) in d["singletons"] if p in remaining]
    if sing_in_remaining:
        return sing_in_remaining[0][1]  # highest-rank singleton
    # Fallback: highest-rank remaining card (will break a pair/trip).
    return max(remaining, key=lambda i: d["ranks"][i])


def strategy_simple(hand: np.ndarray) -> int:
    d = hand_decompose(hand)

    # ---- 1. Quads → split 2 mid + 2 bot (one quad-card to bot via "remaining 4") ----
    if d["quads"]:
        quad_rank, qpos = d["quads"][0]
        # Mid = first 2 positions of the quad (any 2 of the 4 work; pick lowest 2 indices).
        mid = (qpos[0], qpos[1])
        # Top = highest unpaired card if any, else fallback to highest remaining.
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # ---- 2. Trips → mid as pair-of-trips, 1 trip-card to bot ----
    if d["trips"]:
        trip_rank, tpos = d["trips"][0]
        mid = (tpos[0], tpos[1])
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # ---- 3. Any pair → highest pair to mid ----
    if d["pairs"]:
        pair_rank, ppos = d["pairs"][0]
        mid = (ppos[0], ppos[1])
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # ---- 4. Default (no pair) → naive 104 ----
    return 104


# ----------------------------------------------------------------------
# Strategy 2: REFINED — adds displacement-aware handling and bot-DS tie-break.
# ----------------------------------------------------------------------

def _bot_ds_tiebreak(d: dict, used_top_mid: tuple[int, int, int]) -> int:
    """
    For a fixed (top, mid) the bot is forced (the other 4 positions). This
    helper returns the setting_index for the given (top, mid) — used so that
    REFINED can score multiple candidates and pick the one whose bot is DS.
    """
    top, mid_a, mid_b = used_top_mid
    return positions_to_setting_index(top, (mid_a, mid_b))


def strategy_refined(hand: np.ndarray) -> int:
    d = hand_decompose(hand)
    pairs_desc = d["pairs"]
    trips_desc = d["trips"]
    quads_desc = d["quads"]

    # ---- Quads → split 2 mid + 2 bot. ----
    if quads_desc:
        quad_rank, qpos = quads_desc[0]
        mid = (qpos[0], qpos[1])
        # If there's a high pair too (≥9), top is the highest unpaired or
        # highest pair-card singleton remaining; default singleton choice.
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # ---- Trips + pair (full house shape) ----
    if trips_desc and pairs_desc:
        trip_rank, tpos = trips_desc[0]
        pair_rank, ppos = pairs_desc[0]
        # Mining showed: trips → mid usually wins; the only sub-case where
        # pair-displaces-trips is non-trivial is low_trips + high_pair.
        # We still favor trips → mid because it's the modal answer in all
        # 4 quadrants. Refinement worth investigating later.
        mid = (tpos[0], tpos[1])
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # ---- Pure trips ----
    if trips_desc:
        trip_rank, tpos = trips_desc[0]
        mid = (tpos[0], tpos[1])
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # ---- Three pair: highest pair → mid, singleton → top, two lower pairs to bot. ----
    if len(pairs_desc) == 3:
        high_pair_rank, hpos = pairs_desc[0]
        mid = (hpos[0], hpos[1])
        # Top is the singleton (the only unpaired rank).
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # ---- Two pair: highest pair → mid; second pair stays in bot. ----
    if len(pairs_desc) == 2:
        high_pair_rank, hpos = pairs_desc[0]
        mid = (hpos[0], hpos[1])
        used = {mid[0], mid[1]}
        # Top = highest unpaired card if any. With 2 pairs (4 cards) + 3
        # singletons, top is the highest singleton.
        top = _pick_top_default(d, used)
        # Bot tie-break is moot: bot is forced.
        return positions_to_setting_index(top, mid)

    # ---- One pair: high pair → mid. ----
    if len(pairs_desc) == 1:
        pair_rank, ppos = pairs_desc[0]
        mid = (ppos[0], ppos[1])
        used = {mid[0], mid[1]}
        # Top = highest singleton (unpaired card). Choose the candidate whose
        # bot has the best DS structure if multiple top-card choices give
        # the same singleton-rank class.
        # In practice: there's only one highest-rank singleton (ties resolved
        # by position, then rank-ascending hand layout means highest byte wins).
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # ---- No pair: pick the top with the highest unpaired rank (= highest
    #      singleton), mid = next two highest ranks, bot = the rest.
    #      This is essentially setting 104 but might differ if our top-pick
    #      is structurally different. ----
    sing = d["singletons"]  # already desc-sorted by rank
    # All 7 ranks are singletons; take top 3 by rank.
    top_pos = sing[0][1]
    mid_a, mid_b = sing[1][1], sing[2][1]
    return positions_to_setting_index(top_pos, (mid_a, mid_b))


# ----------------------------------------------------------------------
# Strategy 3: HI_ONLY_SEARCH — REFINED + structural search for high_only.
#
# For no-pair hands, naive (top=highest, mid=2nd-3rd, bot=rest) only matches
# the robust shape 19.5% of the time. Mining showed:
#   * top = highest hand-rank is right 83% of robust answers (keep it)
#   * mid ≠ (2nd, 3rd) in 79.6% of cases — robust mid is suited 58%,
#     connected 85% of the time
#   * bot is double-suited 55% when feasible (suit_2nd ≥ 2)
#
# This strategy keeps top=highest singleton, then enumerates the 15 (mid, bot)
# splits of the remaining 6 cards and picks the one maximising a small
# composite score: DS bot (heavy weight), then mid-suited, then mid-connected.
# Tie-break favours higher mid-rank-sum. Still expressible as a rule:
#   "Top = highest. Then choose the bot that is double-suited if possible,
#    and among the remaining mid choices prefer suited+connected pairs."
# ----------------------------------------------------------------------

def _bot_is_double_suited_at(suits: np.ndarray, positions: tuple) -> bool:
    counts = [0, 0, 0, 0]
    for p in positions:
        counts[int(suits[p])] += 1
    counts.sort(reverse=True)
    return counts[0] == 2 and counts[1] == 2


def _max_run_in_ranks(ranks_iter) -> int:
    """Longest consecutive run including wheel-low ace."""
    rs = set(int(r) for r in ranks_iter)
    if 14 in rs:
        rs = rs | {1}
    if not rs:
        return 0
    best = cur = 0
    last = -2
    for r in sorted(rs):
        cur = cur + 1 if r == last + 1 else 1
        best = max(best, cur)
        last = r
    return best


def _hi_only_pick(d: dict) -> tuple[int, tuple[int, int]]:
    """
    Search-based pick for no-pair hands: top = highest singleton, then
    score 15 (mid, bot) splits with MID-FIRST emphasis.

    Diagnostic findings (50K sample of high_only):
      * Inter-profile shape-agreement averages ~36% — the answer is
        opponent-dependent. Single-rule shape-ceiling ≈ MFSA agreement.
      * mid_suited rate in robust 58.4% > bot_DS rate (when feasible) 55.4%
      * Original composite scoring at +10pp (19.5% → 29.96%); this version
        rebalances weights toward mid structure.

    Score weights:
      mid suited+connected:  +6
      mid suited only:       +4
      mid connected (gap≤2): +2
      bot DS:                +5  (still meaningful, but no longer dominant)
      bot connectivity ≥ 4:  +2
      bot n_broadway ≥ 2:    +1
      mid rank-sum × 1/100 (final tiebreak, prefer higher value mid)
    """
    ranks = d["ranks"]
    suits = d["suits"]
    sing = d["singletons"]

    top_pos = sing[0][1]
    remaining = [i for i in range(7) if i != top_pos]

    best_score = -1e9
    best_mid: tuple[int, int] = (remaining[0], remaining[1])
    for ai in range(6):
        for bi in range(ai + 1, 6):
            mid_a, mid_b = remaining[ai], remaining[bi]
            bot_pos = tuple(p for p in remaining if p not in (mid_a, mid_b))

            ra, rb = int(ranks[mid_a]), int(ranks[mid_b])
            mid_hi, mid_lo = max(ra, rb), min(ra, rb)
            mid_suited = int(suits[mid_a]) == int(suits[mid_b])
            mid_gap = mid_hi - mid_lo
            mid_connected = mid_gap <= 2

            bot_ranks_sorted = sorted(int(ranks[p]) for p in bot_pos)
            bot_ds = _bot_is_double_suited_at(suits, bot_pos)
            bot_conn = _max_run_in_ranks(bot_ranks_sorted)
            bot_n_bw = sum(1 for r in bot_ranks_sorted if r >= 10)

            score = 0.0
            if mid_suited and mid_connected:
                score += 6.0
            elif mid_suited:
                score += 4.0
            elif mid_connected:
                score += 2.0
            if bot_ds:
                score += 5.0
            if bot_conn >= 4:
                score += 2.0
            if bot_n_bw >= 2:
                score += 1.0
            score += (mid_hi + mid_lo) / 100.0

            if score > best_score:
                best_score = score
                best_mid = (mid_a, mid_b)

    return top_pos, best_mid


def strategy_hi_only_search(hand: np.ndarray) -> int:
    d = hand_decompose(hand)
    pairs_desc = d["pairs"]
    trips_desc = d["trips"]
    quads_desc = d["quads"]

    # Same as REFINED for non-high_only hands.
    if quads_desc:
        quad_rank, qpos = quads_desc[0]
        mid = (qpos[0], qpos[1])
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)
    if trips_desc and pairs_desc:
        trip_rank, tpos = trips_desc[0]
        mid = (tpos[0], tpos[1])
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)
    if trips_desc:
        trip_rank, tpos = trips_desc[0]
        mid = (tpos[0], tpos[1])
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)
    if len(pairs_desc) >= 1:
        # Same handling as REFINED for any-pair hands.
        pair_rank, ppos = pairs_desc[0]
        mid = (ppos[0], ppos[1])
        used = {mid[0], mid[1]}
        top = _pick_top_default(d, used)
        return positions_to_setting_index(top, mid)

    # NEW: search-based high_only fallback.
    top_pos, mid = _hi_only_pick(d)
    return positions_to_setting_index(top_pos, mid)


# ----------------------------------------------------------------------
# Strategy 4: REFINED_V2 — adds DS-aware top search to pair / two_pair /
# trips_pair branches, plus the high_only search.
#
# For pair-based hands the mid is locked (= the highest pair), but the
# choice of TOP determines which singletons end up in the bot 4. If we
# pick a different top we can sometimes upgrade the bot to DS.
#
# Mining showed: for pair hands, robust mid = the pair only 85%, top =
# highest singleton 77%, bot DS picked only 35% (38% when feasible).
# So we don't FORCE DS — we use it as a tiebreaker.
#
# Score for a given (top, mid) — the bot is auto-forced:
#   bot DS:                +3
#   bot connectivity ≥ 4:  +1
#   top is highest-rank singleton:  +5  (strongest preference)
#   top rank itself / 100             (final tiebreaker; prefer high)
# Mid composition is fixed (the pair) so doesn't enter the score.
# ----------------------------------------------------------------------

def _score_top_choice_for_locked_mid(d: dict, top: int, mid: tuple[int, int]) -> float:
    """Composite score for a (top, mid) pair where mid is locked."""
    suits = d["suits"]
    ranks = d["ranks"]
    bot_pos = tuple(p for p in range(7) if p != top and p not in mid)
    bot_ds = _bot_is_double_suited_at(suits, bot_pos)
    bot_ranks_sorted = sorted(int(ranks[p]) for p in bot_pos)
    bot_conn = _max_run_in_ranks(bot_ranks_sorted)

    # Is `top` the highest-rank singleton?
    sing_positions = [p for (_, p) in d["singletons"]]
    if sing_positions and top == sing_positions[0]:
        top_pref = 5.0
    elif top in sing_positions:
        top_pref = 0.0  # not the highest singleton
    else:
        # top is breaking a pair / trip — strongly disprefer.
        top_pref = -10.0

    score = top_pref
    if bot_ds:
        score += 3.0
    if bot_conn >= 4:
        score += 1.0
    score += int(ranks[top]) / 100.0
    return score


def _best_top_for_locked_mid(d: dict, mid: tuple[int, int]) -> int:
    """
    For a locked mid pair, enumerate the 5 remaining positions for top
    and return the one with highest composite score.
    """
    candidates = [p for p in range(7) if p not in mid]
    best_top = candidates[0]
    best_score = -1e18
    for t in candidates:
        s = _score_top_choice_for_locked_mid(d, t, mid)
        if s > best_score:
            best_score = s
            best_top = t
    return best_top


def strategy_refined_v2(hand: np.ndarray) -> int:
    d = hand_decompose(hand)
    pairs_desc = d["pairs"]
    trips_desc = d["trips"]
    quads_desc = d["quads"]

    # ---- Quads — split 2 mid + 2 bot. Top via search. ----
    if quads_desc:
        quad_rank, qpos = quads_desc[0]
        mid = (qpos[0], qpos[1])
        top = _best_top_for_locked_mid(d, mid)
        return positions_to_setting_index(top, mid)

    # ---- Trips + pair (full house shape). Trips → mid (dominant). ----
    if trips_desc and pairs_desc:
        trip_rank, tpos = trips_desc[0]
        mid = (tpos[0], tpos[1])
        top = _best_top_for_locked_mid(d, mid)
        return positions_to_setting_index(top, mid)

    # ---- Pure trips → mid. ----
    if trips_desc:
        trip_rank, tpos = trips_desc[0]
        mid = (tpos[0], tpos[1])
        top = _best_top_for_locked_mid(d, mid)
        return positions_to_setting_index(top, mid)

    # ---- Any pair-based hand → highest pair → mid, top via search. ----
    if pairs_desc:
        pair_rank, ppos = pairs_desc[0]
        mid = (ppos[0], ppos[1])
        top = _best_top_for_locked_mid(d, mid)
        return positions_to_setting_index(top, mid)

    # ---- High_only via search. ----
    top_pos, mid = _hi_only_pick(d)
    return positions_to_setting_index(top_pos, mid)


# ----------------------------------------------------------------------
# Scorer.
# ----------------------------------------------------------------------

STRATEGIES = {
    "naive_104":      strategy_naive_104,
    "simple":         strategy_simple,
    "refined":        strategy_refined,
    "hi_only_search": strategy_hi_only_search,
    "refined_v2":     strategy_refined_v2,
}


def setting_shape(hand: np.ndarray, setting_index: int) -> tuple:
    """
    Tier-rank-shape of a (hand, setting): (top_rank, sorted_mid_ranks, sorted_bot_ranks).
    Two settings with the same shape are functionally equivalent — they only
    differ in which specific suited card occupies each position. This is the
    correct unit of rule-correctness comparison, since the canonical robust
    answer's choice between equivalent shapes is a tie-break artifact, not a
    rule decision.
    """
    t, m, b = decode_tier_positions(int(setting_index))
    ranks = (hand // 4) + 2
    return (
        int(ranks[t]),
        tuple(sorted([int(ranks[i]) for i in m])),
        tuple(sorted([int(ranks[i]) for i in b])),
    )


def score_strategy(
    name: str,
    fn,
    hands: np.ndarray,
    multiway_robust: np.ndarray,
    df: pd.DataFrame,
    chunk_size: int = 100_000,
) -> dict:
    n = hands.shape[0]
    print(f"  Scoring {name}...")
    pred = np.empty(n, dtype=np.uint8)
    shape_agree = np.empty(n, dtype=bool)
    for start in range(0, n, chunk_size):
        end = min(start + chunk_size, n)
        for i in range(start, end):
            p = fn(hands[i])
            pred[i] = p
            shape_agree[i] = (
                setting_shape(hands[i], p)
                == setting_shape(hands[i], int(multiway_robust[i]))
            )
        if (end // chunk_size) % 5 == 0:
            print(f"    {end:,}/{n:,} ({100*end/n:5.1f}%)")
    agree = pred == multiway_robust
    overall = float(agree.mean())
    overall_shape = float(shape_agree.mean())
    print(f"    literal agreement: {100*overall:.2f}%   shape agreement: {100*overall_shape:.2f}%")

    # By category.
    by_cat = {}
    by_cat_shape = {}
    for cat in ("high_only", "pair", "two_pair", "three_pair",
                 "trips", "trips_pair", "quads"):
        mask = (df["category"] == cat).values
        if mask.any():
            by_cat[cat] = float(agree[mask].mean())
            by_cat_shape[cat] = float(shape_agree[mask].mean())

    # By agreement_class.
    by_ac = {}
    by_ac_shape = {}
    for ac in ("unanimous", "3of4", "2of4", "split2_2", "split1_1_1_1"):
        mask = (df["agreement_class"] == ac).values
        if mask.any():
            by_ac[ac] = float(agree[mask].mean())
            by_ac_shape[ac] = float(shape_agree[mask].mean())

    return {
        "name": name,
        "predictions": pred,
        "shape_agree": shape_agree,
        "overall": overall,
        "overall_shape": overall_shape,
        "by_category": by_cat,
        "by_category_shape": by_cat_shape,
        "by_agreement_class": by_ac,
        "by_agreement_class_shape": by_ac_shape,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--canonical", type=Path,
                    default=ROOT / "data" / "canonical_hands.bin")
    ap.add_argument("--table", type=Path,
                    default=ROOT / "data" / "feature_table.parquet")
    ap.add_argument("--limit", type=int, default=0,
                    help="if > 0, only score the first N canonical hands")
    args = ap.parse_args()

    print(f"Loading canonical hands from {args.canonical}…")
    canonical = read_canonical_hands(args.canonical)
    n_total = canonical.header.num_hands
    cards = canonical.hands
    print(f"  {n_total:,} hands")

    print(f"Loading feature table from {args.table}…")
    df = pq.read_table(args.table, columns=["category", "agreement_class",
                                              "multiway_robust"]).to_pandas()
    print(f"  {len(df):,} rows")

    if args.limit > 0:
        n = min(args.limit, n_total)
        cards = cards[:n]
        df = df.iloc[:n].reset_index(drop=True)
        print(f"\nLimiting to first {n:,} hands.")
    else:
        n = n_total

    multiway_robust = df["multiway_robust"].values.astype(np.uint8)

    print()
    results = {}
    for name, fn in STRATEGIES.items():
        results[name] = score_strategy(name, fn, cards, multiway_robust, df)

    # ------------------------------------------------------------------
    # Report.
    # ------------------------------------------------------------------
    print()
    print("=" * 78)
    print("OVERALL AGREEMENT vs multiway-robust  (literal / shape)")
    print("=" * 78)
    print(f"{'strategy':<14} {'literal':>10} {'shape':>10}")
    for name, r in results.items():
        print(f"{name:<14} {100*r['overall']:>9.2f}% {100*r['overall_shape']:>9.2f}%")

    print()
    print("=" * 78)
    print("BY HAND CATEGORY (shape-agreement; ignores suit tie-breaks)")
    print("=" * 78)
    cats = ("high_only", "pair", "two_pair", "three_pair",
            "trips", "trips_pair", "quads")
    print(f"{'category':<14} " + " ".join(f"{n:>10}" for n in STRATEGIES))
    for cat in cats:
        row = f"{cat:<14}"
        for name in STRATEGIES:
            v = results[name]["by_category_shape"].get(cat, float("nan"))
            row += f" {100*v:>9.2f}%"
        print(row)

    print()
    print("=" * 78)
    print("BY AGREEMENT CLASS (shape-agreement)")
    print("=" * 78)
    print(f"{'agreement_class':<18} " + " ".join(f"{n:>10}" for n in STRATEGIES))
    for ac in ("unanimous", "3of4", "2of4", "split2_2", "split1_1_1_1"):
        row = f"{ac:<18}"
        for name in STRATEGIES:
            v = results[name]["by_agreement_class_shape"].get(ac, float("nan"))
            row += f" {100*v:>9.2f}%"
        print(row)

    print()
    print("=" * 78)
    print("WHERE REFINED FAILS (shape-mismatch only — true rule misses)")
    print("=" * 78)
    miss = ~results["refined"]["shape_agree"]
    print(f"REFINED shape-misses: {int(miss.sum()):,} hands ({100*miss.mean():.2f}%)")
    miss_df = df[miss].copy()
    print()
    print("Miss breakdown by hand category (share of misses, share of category):")
    for cat in cats:
        cat_misses = int((miss_df["category"] == cat).sum())
        cat_total = int((df["category"] == cat).sum())
        if cat_total == 0:
            continue
        print(f"  {cat:<14} misses={cat_misses:>9,}  "
              f"share_of_misses={100*cat_misses/max(int(miss.sum()),1):5.1f}%  "
              f"miss_rate_in_cat={100*cat_misses/cat_total:5.1f}%")

    print()
    print("Miss breakdown by agreement_class:")
    for ac in ("unanimous", "3of4", "2of4", "split2_2", "split1_1_1_1"):
        ac_misses = int((miss_df["agreement_class"] == ac).sum())
        ac_total = int((df["agreement_class"] == ac).sum())
        if ac_total == 0:
            continue
        print(f"  {ac:<18} misses={ac_misses:>9,}  "
              f"share_of_misses={100*ac_misses/max(int(miss.sum()),1):5.1f}%  "
              f"miss_rate_in_ac={100*ac_misses/ac_total:5.1f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
