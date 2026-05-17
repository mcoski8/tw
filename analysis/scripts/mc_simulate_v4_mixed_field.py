"""
TRUE hand-by-hand Monte Carlo: V4 player vs 3 DISTINCT competent Taiwanese
opponents.

Field design — all 3 opponents are competent Taiwanese-aware players, but
each has a DIFFERENT strategic priority:

  - Opponent 1 ("The Balanced Pro" — MiddleFirstSuitAware):
      Picks the best 2-card Hold'em mid first, then takes the highest-rank
      singleton on top (preserving pairs in the bot), with a same-tier swap
      when an alternative mid leaves a better double-suited / single-suited
      bot shape. The strongest of the three on average; treats all tiers
      thoughtfully. ≈ the player who has read a Taiwanese strategy article
      and applies its core ideas.

  - Opponent 2 ("The Omaha Specialist" — OmahaFirst):
      Picks the 4-card bottom FIRST to maximize the Omaha shape (high cards,
      pairs, connectivity, wheel draws, DS suit pattern), then picks mid +
      top from the leftover 3. Different mental model: bottom is king,
      everything else is residual. Strong vs bottom-heavy hands, can leak
      EV on bottom-mid trades.

  - Opponent 3 ("The Top-Conscious Defender" — TopDefensive):
      Picks the top card FIRST as the highest non-pair-member singleton
      (preserving any pair as a mid/bot anchor), then takes the best mid +
      bot from the remaining 6. Conservative paradigm. Stronger on
      no-pair-singletons, can leave value on the table when a smart mid
      ordering would beat a strong top.

All 3 ports are faithful Python ports of the Rust engine's opp_models.rs
(opp_middle_first_suit_aware, opp_omaha_first, opp_top_defensive).

Player ("me"): strategy_v65_mid_pair_chain_extend (production rule chain;
closest proxy to V4 perfectly applied).

Stake: $10 per point.  Output: standalone interactive HTML chart.
"""
from __future__ import annotations

import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import plotly.graph_objects as go  # noqa: E402

from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend as v65_strategy,
)


# ============================================================
# Config
# ============================================================

LOOKUP_PATH = ROOT / "data" / "lookup_table.bin"
OUTPUT_HTML = ROOT / "MC_SIMULATION_V4_MIXED_FIELD.html"

STAKE_DOLLARS_PER_POINT = 10.0
N_SIMULATIONS = 10
HANDS_PER_SIMULATION = 1000

PTS_TOP, PTS_MID, PTS_BOT = 1, 2, 3
PTS_SCOOP_BONUS_REPLACE = 20

COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]


# ============================================================
# 5-card evaluator (same lookup-table approach as before)
# ============================================================

BINOM = np.zeros((52, 6), dtype=np.int64)
for n in range(52):
    BINOM[n, 0] = 1
    for k in range(1, 6):
        BINOM[n, k] = 0 if k > n else (1 if k == n else BINOM[n - 1, k - 1] + BINOM[n - 1, k])


def load_lookup_table(path: Path) -> np.ndarray:
    arr = np.frombuffer(path.read_bytes(), dtype=np.uint32)
    return arr if arr.size == 2_598_960 else arr[-2_598_960:].copy()


def colex_index_5_array(cards5: np.ndarray) -> np.ndarray:
    return (
        BINOM[cards5[:, 0], 1]
        + BINOM[cards5[:, 1], 2]
        + BINOM[cards5[:, 2], 3]
        + BINOM[cards5[:, 3], 4]
        + BINOM[cards5[:, 4], 5]
    )


COMBOS_6_CHOOSE_5 = np.array(list(combinations(range(6), 5)), dtype=np.int64)
COMBOS_7_CHOOSE_5 = np.array(list(combinations(range(7), 5)), dtype=np.int64)
COMBOS_4_CHOOSE_2 = np.array(list(combinations(range(4), 2)), dtype=np.int64)
COMBOS_5_CHOOSE_3 = np.array(list(combinations(range(5), 3)), dtype=np.int64)


class Evaluator:
    def __init__(self, lookup_table: np.ndarray):
        self.table = lookup_table

    def eval_top(self, hole1: int, board5: np.ndarray) -> int:
        cards6 = np.empty(6, dtype=np.int64)
        cards6[0] = hole1
        cards6[1:] = board5
        combos = np.sort(cards6[COMBOS_6_CHOOSE_5], axis=1)
        return int(self.table[colex_index_5_array(combos)].max())

    def eval_mid(self, hole2: np.ndarray, board5: np.ndarray) -> int:
        cards7 = np.empty(7, dtype=np.int64)
        cards7[:2] = hole2
        cards7[2:] = board5
        combos = np.sort(cards7[COMBOS_7_CHOOSE_5], axis=1)
        return int(self.table[colex_index_5_array(combos)].max())

    def eval_bot(self, hole4: np.ndarray, board5: np.ndarray) -> int:
        hole_pairs = hole4[COMBOS_4_CHOOSE_2]
        board_triples = board5[COMBOS_5_CHOOSE_3]
        combos = np.empty((6, 10, 5), dtype=np.int64)
        combos[:, :, :2] = hole_pairs[:, None, :]
        combos[:, :, 2:] = board_triples[None, :, :]
        combos_flat = np.sort(combos.reshape(60, 5), axis=1)
        return int(self.table[colex_index_5_array(combos_flat)].max())


# ============================================================
# Card helpers (rank in 2..14, suit in 0..3, index in 0..51)
# ============================================================

def card_rank(c: int) -> int:
    return c // 4 + 2


def card_suit(c: int) -> int:
    return c % 4


# ============================================================
# Python ports of Rust opponent strategies
# ============================================================

def naive_mid_score(a: int, b: int) -> int:
    """Mirrors Rust naive_mid_score. Higher = stronger 2-card Hold'em mid."""
    r1, r2 = card_rank(a), card_rank(b)
    high, low = (r1, r2) if r1 >= r2 else (r2, r1)
    if high == low:
        return 200 + high * 2
    s = high * 3 + low * 2
    if card_suit(a) == card_suit(b):
        s += 8
    gap = high - low
    if gap == 1:
        s += 6
    elif gap == 2:
        s += 3
    if high == 14:
        s += 5
    return s


def middle_tier(a: int, b: int) -> int:
    """5-tier classifier. 5=pair, 4=suited broadway, 3=offsuit broadway, 2=suited ace/connector, 1=other."""
    r1, r2 = card_rank(a), card_rank(b)
    high, low = (r1, r2) if r1 >= r2 else (r2, r1)
    suited = card_suit(a) == card_suit(b)
    if high == low:
        return 5
    if low >= 10 and suited:
        return 4
    if low >= 10:
        return 3
    if suited and (high == 14 or (high - low) <= 2):
        return 2
    return 1


def bot_suit_score(bot4: list[int]) -> int:
    """5=DS (2+2), 4=SS (2+1+1), 3=rainbow, 2=3+1, 1=4-flush."""
    counts = [0, 0, 0, 0]
    for c in bot4:
        counts[card_suit(c)] += 1
    sorted_counts = sorted(counts, reverse=True)
    a, b = sorted_counts[0], sorted_counts[1]
    if a == 2 and b == 2:
        return 5
    if a == 2 and b == 1:
        return 4
    if a == 1 and b == 1:
        return 3
    if a == 3 and b == 1:
        return 2
    if a == 4 and b == 0:
        return 1
    return 0


def omaha_bot_score(bot4: list[int]) -> int:
    """Signed score for a 4-card Omaha bottom (high cards, pairs, connectivity, suit shape)."""
    score = 0
    # High-card value: rank > 8 adds (rank - 8) * 2
    for c in bot4:
        r = card_rank(c)
        if r > 8:
            score += (r - 8) * 2
    # Pair/trip bonuses
    rank_counts = [0] * 15
    for c in bot4:
        rank_counts[card_rank(c)] += 1
    for r in range(2, 15):
        if rank_counts[r] == 2:
            score += 15 + r
        elif rank_counts[r] == 3:
            score += 30 + r * 2
        elif rank_counts[r] == 4:
            score += 60 + r * 3
    # Connectivity: longest run of consecutive distinct ranks
    ranks = sorted(set(card_rank(c) for c in bot4))
    max_run, cur = 1, 1
    for i in range(1, len(ranks)):
        if ranks[i] == ranks[i - 1] + 1:
            cur += 1
            max_run = max(max_run, cur)
        else:
            cur = 1
    score += max_run * 8
    # Wheel draw
    wheel_count = sum(1 for c in bot4 if card_rank(c) == 14 or 2 <= card_rank(c) <= 5)
    if wheel_count >= 3:
        score += 6
    elif wheel_count >= 2:
        score += 3
    # Suit pattern
    counts = [0, 0, 0, 0]
    for c in bot4:
        counts[card_suit(c)] += 1
    sc = sorted(counts, reverse=True)
    suit_bonus = {
        (2, 2): 14, (2, 1): 7, (1, 1): 0, (3, 1): -4, (4, 0): -8,
    }.get((sc[0], sc[1]), 0)
    return score + suit_bonus


def pick_top_from_rem5(rem5: list[int]) -> int:
    """Return position 0..4 of the chosen top card. Prefer highest-rank singleton; else highest-rank overall."""
    rank_counts = [0] * 15
    for c in rem5:
        rank_counts[card_rank(c)] += 1
    # Highest-rank singleton (tiebreak: higher card index).
    best_single = None
    for i in range(5):
        if rank_counts[card_rank(rem5[i])] != 1:
            continue
        if best_single is None:
            best_single = i
        else:
            ci, cb = rem5[i], rem5[best_single]
            if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
                best_single = i
    if best_single is not None:
        return best_single
    # Fallback: highest-rank overall (tiebreak: higher card index).
    top_i = 0
    for i in range(1, 5):
        ci, cb = rem5[i], rem5[top_i]
        if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
            top_i = i
    return top_i


def build_mid_top_bot_from_mid_choice(hand: np.ndarray, mi: int, mj: int) -> tuple[int, list[int], list[int]]:
    """Given hand (7 sorted cards) and chosen mid positions (mi, mj), return (top, mid_list, bot_list)."""
    mid = [int(hand[mi]), int(hand[mj])]
    rem5 = [int(hand[x]) for x in range(7) if x != mi and x != mj]
    top_local = pick_top_from_rem5(rem5)
    top = rem5[top_local]
    bot = [rem5[i] for i in range(5) if i != top_local]
    return top, mid, bot


def opp_middle_first_suit_aware(hand: np.ndarray) -> tuple[int, np.ndarray, np.ndarray]:
    """The Balanced Pro: best mid (Hold'em-strength tier + bot-shape aware), pair-preserving top."""
    best = (0, 1)
    best_key = (-1, -1, -1, -1, -1)
    for i in range(7):
        for j in range(i + 1, 7):
            tier = middle_tier(int(hand[i]), int(hand[j]))
            # Compute candidate bot after pair-preserving top selection.
            rem5 = [int(hand[x]) for x in range(7) if x != i and x != j]
            top_local = pick_top_from_rem5(rem5)
            cand_bot = [rem5[k] for k in range(5) if k != top_local]
            bot_sc = bot_suit_score(cand_bot)
            strength = naive_mid_score(int(hand[i]), int(hand[j]))
            min_idx = min(int(hand[i]), int(hand[j]))
            max_idx = max(int(hand[i]), int(hand[j]))
            # tiebreak: prefer lower indices (mirror Rust's u8::MAX - idx)
            key = (tier, bot_sc, strength, 255 - min_idx, 255 - max_idx)
            if key > best_key:
                best_key = key
                best = (i, j)
    top, mid, bot = build_mid_top_bot_from_mid_choice(hand, best[0], best[1])
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


def opp_omaha_first(hand: np.ndarray) -> tuple[int, np.ndarray, np.ndarray]:
    """The Omaha Specialist: best 4-card bot first, then top=highest of rem3, mid=other 2."""
    best_score = -10**9
    best_bot_idx = (0, 1, 2, 3)
    for combo in combinations(range(7), 4):
        bot = [int(hand[c]) for c in combo]
        s = omaha_bot_score(bot)
        if s > best_score or (s == best_score and combo < best_bot_idx):
            best_score = s
            best_bot_idx = combo
    bot = np.array([int(hand[c]) for c in best_bot_idx], dtype=np.int64)
    rem3_idx = [i for i in range(7) if i not in best_bot_idx]
    rem3 = [int(hand[i]) for i in rem3_idx]
    # Top: highest rank in rem3 (tiebreak higher card index).
    top_local = 0
    for i in range(1, 3):
        ci, cb = rem3[i], rem3[top_local]
        if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
            top_local = i
    top = rem3[top_local]
    mid = np.array([rem3[i] for i in range(3) if i != top_local], dtype=np.int64)
    return top, mid, bot


def opp_top_defensive(hand: np.ndarray) -> tuple[int, np.ndarray, np.ndarray]:
    """The Top-Conscious Defender: highest non-pair-member singleton on top, then best mid from rem6."""
    # Rank counts in the 7-card hand.
    rc = [0] * 15
    for c in hand:
        rc[card_rank(int(c))] += 1
    # Singletons (rank count = 1)
    singletons = [i for i in range(7) if rc[card_rank(int(hand[i]))] == 1]
    if singletons:
        # Highest-rank singleton, tiebreak by higher card index.
        top_i = singletons[0]
        for i in singletons[1:]:
            ci, cb = int(hand[i]), int(hand[top_i])
            if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
                top_i = i
    else:
        # All paired: highest rank overall with index tiebreak.
        top_i = 0
        for i in range(1, 7):
            ci, cb = int(hand[i]), int(hand[top_i])
            if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
                top_i = i
    rem6_indices = [i for i in range(7) if i != top_i]
    rem6 = [int(hand[i]) for i in rem6_indices]
    # Best mid from rem6 by naive_mid_score.
    best = (0, 1)
    best_score = naive_mid_score(rem6[0], rem6[1])
    for a in range(6):
        for b in range(a + 1, 6):
            if (a, b) == (0, 1):
                continue
            s = naive_mid_score(rem6[a], rem6[b])
            if s > best_score:
                best_score = s
                best = (a, b)
    mid = np.array([rem6[best[0]], rem6[best[1]]], dtype=np.int64)
    bot = np.array([rem6[i] for i in range(6) if i != best[0] and i != best[1]], dtype=np.int64)
    return int(hand[top_i]), mid, bot


OPPONENTS = [
    ("The Balanced Pro (MiddleFirstSuitAware)", opp_middle_first_suit_aware),
    ("The Omaha Specialist (OmahaFirst)",       opp_omaha_first),
    ("The Top-Conscious Defender (TopDefensive)", opp_top_defensive),
]


# ============================================================
# v65 setting decoder (returns tuple)
# ============================================================

_MID_PAIRS = np.array(list(combinations(range(6), 2)), dtype=np.int64)


def decode_v65(hand: np.ndarray, setting_idx: int) -> tuple[int, np.ndarray, np.ndarray]:
    top_i, mid_combo_i = divmod(setting_idx, 15)
    a, b = _MID_PAIRS[mid_combo_i]
    remaining = [i for i in range(7) if i != top_i]
    mid_pos = (remaining[int(a)], remaining[int(b)])
    bot_pos = [remaining[j] for j in range(6) if j != int(a) and j != int(b)]
    top = int(hand[top_i])
    mid = np.array([hand[mid_pos[0]], hand[mid_pos[1]]], dtype=np.int64)
    bot = np.array([hand[p] for p in bot_pos], dtype=np.int64)
    return top, mid, bot


# ============================================================
# Pairwise scoring (me vs one opponent, with scoop detection)
# ============================================================

def score_hand_vs_opp(me_set, opp_set, board_a, board_b, ev: Evaluator) -> int:
    me_top, me_mid, me_bot = me_set
    op_top, op_mid, op_bot = opp_set

    me_top_a = ev.eval_top(me_top, board_a); op_top_a = ev.eval_top(op_top, board_a)
    me_mid_a = ev.eval_mid(me_mid, board_a); op_mid_a = ev.eval_mid(op_mid, board_a)
    me_bot_a = ev.eval_bot(me_bot, board_a); op_bot_a = ev.eval_bot(op_bot, board_a)
    me_top_b = ev.eval_top(me_top, board_b); op_top_b = ev.eval_top(op_top, board_b)
    me_mid_b = ev.eval_mid(me_mid, board_b); op_mid_b = ev.eval_mid(op_mid, board_b)
    me_bot_b = ev.eval_bot(me_bot, board_b); op_bot_b = ev.eval_bot(op_bot, board_b)

    me_wins = [me_top_a > op_top_a, me_mid_a > op_mid_a, me_bot_a > op_bot_a,
               me_top_b > op_top_b, me_mid_b > op_mid_b, me_bot_b > op_bot_b]
    op_wins = [me_top_a < op_top_a, me_mid_a < op_mid_a, me_bot_a < op_bot_a,
               me_top_b < op_top_b, me_mid_b < op_mid_b, me_bot_b < op_bot_b]

    if all(me_wins):
        return PTS_SCOOP_BONUS_REPLACE
    if all(op_wins):
        return -PTS_SCOOP_BONUS_REPLACE

    pts = 0
    for me_r, op_r, p in [
        (me_top_a, op_top_a, PTS_TOP), (me_mid_a, op_mid_a, PTS_MID), (me_bot_a, op_bot_a, PTS_BOT),
        (me_top_b, op_top_b, PTS_TOP), (me_mid_b, op_mid_b, PTS_MID), (me_bot_b, op_bot_b, PTS_BOT),
    ]:
        if me_r > op_r:
            pts += p
        elif me_r < op_r:
            pts -= p
    return pts


# ============================================================
# Simulate a single hand
# ============================================================

def simulate_one_hand(rng: np.random.Generator, ev: Evaluator) -> tuple[int, list[int]]:
    """Deal one hand, return (total_pts_me_vs_field, [pts_vs_each_opp])."""
    deck = rng.permutation(52)
    me_raw = deck[:7]
    opp_raws = [deck[7:14], deck[14:21], deck[21:28]]
    board_a = deck[28:33].astype(np.int64)
    board_b = deck[33:38].astype(np.int64)

    me_hand = np.sort(me_raw).astype(np.uint8)
    opp_hands = [np.sort(h).astype(np.uint8) for h in opp_raws]

    me_setting_idx = int(v65_strategy(me_hand))
    me_set = decode_v65(me_hand.astype(np.int64), me_setting_idx)

    # Each opponent uses a DIFFERENT strategy.
    per_opp_pts = []
    total = 0
    for opp_idx, (label, opp_fn) in enumerate(OPPONENTS):
        opp_set = opp_fn(opp_hands[opp_idx].astype(np.int64))
        pts = score_hand_vs_opp(me_set, opp_set, board_a, board_b, ev)
        per_opp_pts.append(pts)
        total += pts
    return total, per_opp_pts


# ============================================================
# Main
# ============================================================

def main() -> int:
    print(f"Loading lookup table ...")
    lookup = load_lookup_table(LOOKUP_PATH)
    print(f"  {lookup.size:,} entries\n")

    ev = Evaluator(lookup)

    print(f"Opponent field ({len(OPPONENTS)} distinct competent archetypes):")
    for i, (label, _) in enumerate(OPPONENTS):
        print(f"  Seat {i+1}: {label}")
    print()

    print(f"Running {N_SIMULATIONS} sims × {HANDS_PER_SIMULATION:,} hands ...")
    cumulative_per_sim = np.empty((N_SIMULATIONS, HANDS_PER_SIMULATION), dtype=np.float64)
    per_opp_totals = np.zeros((N_SIMULATIONS, len(OPPONENTS)), dtype=np.float64)
    all_points = []

    for sim_idx in range(N_SIMULATIONS):
        rng = np.random.default_rng(seed=2000 + sim_idx)
        t0 = time.time()
        pts_arr = np.empty(HANDS_PER_SIMULATION, dtype=np.float64)
        per_opp_run = np.zeros(len(OPPONENTS), dtype=np.float64)
        for h in range(HANDS_PER_SIMULATION):
            tot, per = simulate_one_hand(rng, ev)
            pts_arr[h] = tot
            for k in range(len(OPPONENTS)):
                per_opp_run[k] += per[k]
        elapsed = time.time() - t0
        dollars = pts_arr * STAKE_DOLLARS_PER_POINT
        cumulative_per_sim[sim_idx] = np.cumsum(dollars)
        per_opp_totals[sim_idx] = per_opp_run * STAKE_DOLLARS_PER_POINT
        final = cumulative_per_sim[sim_idx, -1]
        all_points.append(pts_arr)
        print(f"  sim {sim_idx+1:2d}: final=${final:+,.0f}  "
              f"pts/hand={pts_arr.mean():+.3f}  "
              f"vs opps=[${per_opp_run[0]*STAKE_DOLLARS_PER_POINT:+,.0f}, "
              f"${per_opp_run[1]*STAKE_DOLLARS_PER_POINT:+,.0f}, "
              f"${per_opp_run[2]*STAKE_DOLLARS_PER_POINT:+,.0f}]  "
              f"({elapsed:.1f}s)")

    all_points_flat = np.concatenate(all_points)
    final_dollars = cumulative_per_sim[:, -1]
    print()
    print(f"Aggregate over {N_SIMULATIONS * HANDS_PER_SIMULATION:,} hands:")
    print(f"  mean pts/hand (field) = {all_points_flat.mean():+.4f}  "
          f"(${all_points_flat.mean()*STAKE_DOLLARS_PER_POINT:+.2f}/hand)")
    print(f"  stdev pts/hand        = {all_points_flat.std():.3f}")
    print(f"  mean final $          = ${final_dollars.mean():+,.0f}")
    print(f"  stdev final $         = ${final_dollars.std():,.0f}")
    print(f"  range                 = ${final_dollars.min():+,.0f} to ${final_dollars.max():+,.0f}")
    print()
    print(f"Per-opponent breakdown (mean $ won across {N_SIMULATIONS} sims):")
    for k, (label, _) in enumerate(OPPONENTS):
        m = float(per_opp_totals[:, k].mean())
        s = float(per_opp_totals[:, k].std())
        print(f"  vs {label:60s}  mean=${m:+,.0f}  std=${s:,.0f}")
    print()

    # Build chart.
    print(f"Building chart ...")
    x = np.arange(1, HANDS_PER_SIMULATION + 1)
    fig = go.Figure()
    for i in range(N_SIMULATIONS):
        fig.add_trace(go.Scatter(
            x=x, y=cumulative_per_sim[i], mode="lines",
            name=f"Sim {i+1}",
            line=dict(color=COLORS[i], width=1.8),
            hovertemplate=f"<b>Sim {i+1}</b><br>Hand #%{{x:,}}<br>Cumulative: $%{{y:+,.0f}}<extra></extra>",
        ))
    expected_per_hand = float(all_points_flat.mean() * STAKE_DOLLARS_PER_POINT)
    fig.add_trace(go.Scatter(
        x=x, y=expected_per_hand * x, mode="lines",
        name="Empirical mean trend",
        line=dict(color="black", width=2.5, dash="dash"),
        hovertemplate=f"<b>Mean trend</b><br>Hand #%{{x:,}}<br>Mean: $%{{y:+,.0f}}<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"),
                  annotation_text="break-even", annotation_position="bottom right",
                  annotation_font_size=10)

    per_opp_mean_str = "<br>".join(
        f"• vs Seat {k+1}: ${float(per_opp_totals[:,k].mean()):+,.0f}"
        for k in range(len(OPPONENTS))
    )
    summary = (
        f"<b>True MC, mixed competent field</b><br><br>"
        f"<b>Setup</b><br>"
        f"• Stake: ${STAKE_DOLLARS_PER_POINT:.0f}/point · 4-handed<br>"
        f"• Me: v65 production chain<br>"
        f"<br>"
        f"<b>Opponent seats (different styles)</b><br>"
        f"• Seat 1: Balanced Pro<br>"
        f"• Seat 2: Omaha Specialist<br>"
        f"• Seat 3: Top-Conscious Defender<br>"
        f"<br>"
        f"<b>Results across {N_SIMULATIONS} sims × {HANDS_PER_SIMULATION:,} hands</b><br>"
        f"• Mean final: ${final_dollars.mean():+,.0f}<br>"
        f"• Std final: ${final_dollars.std():,.0f}<br>"
        f"• Worst sim: ${final_dollars.min():+,.0f}<br>"
        f"• Best sim:  ${final_dollars.max():+,.0f}<br>"
        f"• Mean per-hand: {all_points_flat.mean():+.3f} pts  "
        f"(${expected_per_hand:+.2f}/hand)<br>"
        f"<br>"
        f"<b>Per-opponent edge (mean $ over 1,000h)</b><br>"
        f"{per_opp_mean_str}<br>"
        f"<br>"
        f"<i>Real card deals + boards + scoop detection.</i>"
    )
    fig.add_annotation(
        xref="paper", yref="paper", x=0.012, y=0.985,
        xanchor="left", yanchor="top",
        text=summary, showarrow=False,
        bgcolor="rgba(255,255,255,0.92)", bordercolor="rgba(0,0,0,0.4)",
        borderwidth=1, borderpad=10,
        font=dict(size=11, family="monospace"), align="left",
    )
    fig.update_layout(
        title=dict(
            text=(
                "<b>TRUE Monte Carlo: V4 Guide vs Mixed Field of 3 Distinct Competent Opponents</b><br>"
                f"<sub>{N_SIMULATIONS} sims × {HANDS_PER_SIMULATION:,} hands · $10/pt · "
                f"Seat 1: Balanced · Seat 2: Omaha-First · Seat 3: Top-Defensive</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=17),
        ),
        xaxis=dict(title="Hand number", showgrid=True, gridcolor="rgba(0,0,0,0.08)",
                   zeroline=False, tickformat=","),
        yaxis=dict(title="Cumulative $ won/lost (at $10/point)", showgrid=True,
                   gridcolor="rgba(0,0,0,0.08)", zeroline=False, tickformat="+$,.0f"),
        hovermode="x unified",
        hoverlabel=dict(bgcolor="rgba(255,255,255,0.95)",
                        bordercolor="rgba(0,0,0,0.4)", font_size=12),
        legend=dict(x=0.99, y=0.01, xanchor="right", yanchor="bottom",
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.3)", borderwidth=1, font_size=11),
        plot_bgcolor="white",
        width=1400, height=800,
        margin=dict(l=80, r=40, t=100, b=70),
    )
    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn", full_html=True,
                   config={"displayModeBar": True, "displaylogo": False})
    print(f"Chart written to {OUTPUT_HTML}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
