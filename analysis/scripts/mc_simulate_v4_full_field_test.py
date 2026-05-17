"""
Full MC battery for V4 guide vs realistic competent fields.

Five scenarios run at 5,000 hands × 10 sims each:

  1. SYMMETRY  — v65 vs 3× v65         (validation: should yield ~$0)
  2. HOMOGENEOUS A — v65 vs 3× Pair-First Standardist (operator's described archetype)
  3. HOMOGENEOUS B — v65 vs 3× Top-Greedy Defender    (operator's described archetype)
  4. BASELINE    — v65 vs 3× Balanced Pro (mfsuitaware port — for comparison)
  5. MIXED       — v65 vs (1 Standardist + 1 Top-Greedy + 1 Balanced Pro)

Plus a deterministic grid-slice (infinite-sample EV for v65 vs each of the
project's pre-computed Rust opponent profiles).

Output:
  - Console: per-scenario stats + validation results
  - HTML: 2x3 subplot chart showing all 5 scenarios (drops the SYMMETRY panel
          if it passes the validation test; otherwise displays it loudly)

Stake: $10/point.  Sample size per scenario: 50,000 hands  →  stderr ~$0.58/hand.
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
from plotly.subplots import make_subplots  # noqa: E402

from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend as v65_strategy,
)

LOOKUP_PATH = ROOT / "data" / "lookup_table.bin"
GRID_PATH = ROOT / "data" / "oracle_grid_50k.npz"
OUTPUT_HTML = ROOT / "MC_SIMULATION_V4_FULL_FIELD.html"

STAKE = 10.0
N_SIMS = 10
HANDS_PER_SIM = 5000

PTS_TOP, PTS_MID, PTS_BOT = 1, 2, 3
PTS_SCOOP = 20

COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]


# ============================================================
# Evaluator (same lookup-table approach)
# ============================================================

BINOM = np.zeros((52, 6), dtype=np.int64)
for n in range(52):
    BINOM[n, 0] = 1
    for k in range(1, 6):
        BINOM[n, k] = 0 if k > n else (1 if k == n else BINOM[n - 1, k - 1] + BINOM[n - 1, k])


def load_lookup_table(path: Path) -> np.ndarray:
    arr = np.frombuffer(path.read_bytes(), dtype=np.uint32)
    return arr if arr.size == 2_598_960 else arr[-2_598_960:].copy()


def colex5(cards5: np.ndarray) -> np.ndarray:
    return (BINOM[cards5[:, 0], 1] + BINOM[cards5[:, 1], 2] + BINOM[cards5[:, 2], 3]
            + BINOM[cards5[:, 3], 4] + BINOM[cards5[:, 4], 5])


C65 = np.array(list(combinations(range(6), 5)), dtype=np.int64)
C75 = np.array(list(combinations(range(7), 5)), dtype=np.int64)
C42 = np.array(list(combinations(range(4), 2)), dtype=np.int64)
C53 = np.array(list(combinations(range(5), 3)), dtype=np.int64)


class Evaluator:
    def __init__(self, lookup): self.t = lookup

    def eval_top(self, hole1, board5):
        c6 = np.empty(6, dtype=np.int64); c6[0] = hole1; c6[1:] = board5
        return int(self.t[colex5(np.sort(c6[C65], axis=1))].max())

    def eval_mid(self, hole2, board5):
        c7 = np.empty(7, dtype=np.int64); c7[:2] = hole2; c7[2:] = board5
        return int(self.t[colex5(np.sort(c7[C75], axis=1))].max())

    def eval_bot(self, hole4, board5):
        hp, bt = hole4[C42], board5[C53]
        c = np.empty((6, 10, 5), dtype=np.int64)
        c[:, :, :2] = hp[:, None, :]; c[:, :, 2:] = bt[None, :, :]
        return int(self.t[colex5(np.sort(c.reshape(60, 5), axis=1))].max())


def card_rank(c): return c // 4 + 2
def card_suit(c): return c % 4


# ============================================================
# Helpers shared across opponent strategies
# ============================================================

def naive_mid_score(a, b):
    r1, r2 = card_rank(a), card_rank(b)
    high, low = (r1, r2) if r1 >= r2 else (r2, r1)
    if high == low: return 200 + high * 2
    s = high * 3 + low * 2
    if card_suit(a) == card_suit(b): s += 8
    gap = high - low
    if gap == 1: s += 6
    elif gap == 2: s += 3
    if high == 14: s += 5
    return s


def middle_tier(a, b):
    r1, r2 = card_rank(a), card_rank(b)
    high, low = (r1, r2) if r1 >= r2 else (r2, r1)
    suited = card_suit(a) == card_suit(b)
    if high == low: return 5
    if low >= 10 and suited: return 4
    if low >= 10: return 3
    if suited and (high == 14 or (high - low) <= 2): return 2
    return 1


def bot_suit_score(bot4):
    counts = [0, 0, 0, 0]
    for c in bot4: counts[card_suit(c)] += 1
    sc = sorted(counts, reverse=True)
    return {(2, 2): 5, (2, 1): 4, (1, 1): 3, (3, 1): 2, (4, 0): 1}.get((sc[0], sc[1]), 0)


def omaha_bot_score(bot4):
    score = 0
    for c in bot4:
        r = card_rank(c)
        if r > 8: score += (r - 8) * 2
    rc = [0] * 15
    for c in bot4: rc[card_rank(c)] += 1
    for r in range(2, 15):
        if rc[r] == 2: score += 15 + r
        elif rc[r] == 3: score += 30 + r * 2
        elif rc[r] == 4: score += 60 + r * 3
    ranks = sorted(set(card_rank(c) for c in bot4))
    max_run, cur = 1, 1
    for i in range(1, len(ranks)):
        if ranks[i] == ranks[i - 1] + 1:
            cur += 1; max_run = max(max_run, cur)
        else: cur = 1
    score += max_run * 8
    wheel = sum(1 for c in bot4 if card_rank(c) == 14 or 2 <= card_rank(c) <= 5)
    if wheel >= 3: score += 6
    elif wheel >= 2: score += 3
    counts = [0, 0, 0, 0]
    for c in bot4: counts[card_suit(c)] += 1
    sc = sorted(counts, reverse=True)
    suit_bonus = {(2, 2): 14, (2, 1): 7, (1, 1): 0, (3, 1): -4, (4, 0): -8}.get((sc[0], sc[1]), 0)
    return score + suit_bonus


def pick_top_from_rem5(rem5):
    rc = [0] * 15
    for c in rem5: rc[card_rank(c)] += 1
    best_single = None
    for i in range(5):
        if rc[card_rank(rem5[i])] != 1: continue
        if best_single is None: best_single = i
        else:
            ci, cb = rem5[i], rem5[best_single]
            if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
                best_single = i
    if best_single is not None: return best_single
    top_i = 0
    for i in range(1, 5):
        ci, cb = rem5[i], rem5[top_i]
        if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
            top_i = i
    return top_i


# ============================================================
# Opponent strategies (return (top_card, mid_2, bot_4))
# ============================================================

def opp_balanced_pro(hand):
    """MiddleFirstSuitAware port. Best Hold'em mid with same-tier swap for bot shape."""
    best, best_key = (0, 1), (-1, -1, -1, -1, -1)
    for i in range(7):
        for j in range(i + 1, 7):
            tier = middle_tier(int(hand[i]), int(hand[j]))
            rem5 = [int(hand[x]) for x in range(7) if x != i and x != j]
            top_local = pick_top_from_rem5(rem5)
            cand_bot = [rem5[k] for k in range(5) if k != top_local]
            bot_sc = bot_suit_score(cand_bot)
            strength = naive_mid_score(int(hand[i]), int(hand[j]))
            min_idx, max_idx = min(int(hand[i]), int(hand[j])), max(int(hand[i]), int(hand[j]))
            key = (tier, bot_sc, strength, 255 - min_idx, 255 - max_idx)
            if key > best_key:
                best_key, best = key, (i, j)
    i, j = best
    mid = [int(hand[i]), int(hand[j])]
    rem5 = [int(hand[x]) for x in range(7) if x != i and x != j]
    top_local = pick_top_from_rem5(rem5)
    top = rem5[top_local]
    bot = [rem5[k] for k in range(5) if k != top_local]
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


def opp_pair_first_standardist(hand):
    """Operator's described archetype: QQ/KK/AA → mid; then A/K/Q → top; bot = rem4.

    Fallback for no premium pair: still puts highest broadway on top, builds
    best Omaha bot from remaining 6, mid gets leftover.
    """
    cards = [int(c) for c in hand]
    rank_counts = [0] * 15
    for c in cards:
        rank_counts[card_rank(c)] += 1

    # Force QQ/KK/AA into mid (highest premium pair first).
    mid_pair_rank = None
    for r in [14, 13, 12]:
        if rank_counts[r] >= 2:
            mid_pair_rank = r
            break

    if mid_pair_rank is not None:
        # Extract the pair for mid.
        mid_cards, rem = [], []
        for c in cards:
            if len(mid_cards) < 2 and card_rank(c) == mid_pair_rank:
                mid_cards.append(c)
            else:
                rem.append(c)
        # Pick top: highest-rank broadway (A/K/Q) if available, else highest overall.
        rem_sorted = sorted(rem, key=lambda x: (card_rank(x), x), reverse=True)
        top = rem_sorted[0]
        bot_cards = rem_sorted[1:]  # 4 cards
        return top, np.array(mid_cards, dtype=np.int64), np.array(bot_cards, dtype=np.int64)

    # No premium pair: pick top first (highest broadway), best Omaha bot from rem6, mid = leftover.
    cards_sorted = sorted(cards, key=lambda x: (card_rank(x), x), reverse=True)
    top = cards_sorted[0]
    rem6 = cards_sorted[1:]
    # Best Omaha bot from rem6.
    best_score, best_combo = -10**9, (0, 1, 2, 3)
    for combo in combinations(range(6), 4):
        cand = [rem6[c] for c in combo]
        s = omaha_bot_score(cand)
        if s > best_score:
            best_score, best_combo = s, combo
    bot = [rem6[c] for c in best_combo]
    mid = [rem6[i] for i in range(6) if i not in best_combo]
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


def opp_top_greedy_defender(hand):
    """Operator's archetype, with operator's refinement:

      - When max card is **Q, K, or A** (premium top achievable):
          Top = highest card ALWAYS. Then best Omaha bot from rem6, mid = leftover.
          (The "top very strong" mindset.)

      - When max card is **J or lower** (no premium top available):
          Pivot to Omaha-first. Build best 4-card Omaha bot from all 7 cards
          prioritizing connectivity / suitedness, then top = highest of rem3,
          mid = the other 2.
          (Operator: "they'll prioritize omaha rundown first and then throw
          whatever back on top to have better suitedness or connectivity.")
    """
    cards = [int(c) for c in hand]
    max_card = max(cards, key=lambda x: (card_rank(x), x))
    max_rank = card_rank(max_card)

    if max_rank >= 12:  # Q, K, or A available — keep Top-Greedy behavior.
        top = max_card
        rem6 = [c for c in cards if c != top]
        best_score, best_combo = -10**9, (0, 1, 2, 3)
        for combo in combinations(range(6), 4):
            cand = [rem6[c] for c in combo]
            s = omaha_bot_score(cand)
            if s > best_score:
                best_score, best_combo = s, combo
        bot = [rem6[c] for c in best_combo]
        mid = [rem6[i] for i in range(6) if i not in best_combo]
        return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)

    # max ≤ J: pivot to Omaha-first. Best 4-card bot from all 7.
    best_score, best_combo = -10**9, (0, 1, 2, 3)
    for combo in combinations(range(7), 4):
        cand = [cards[c] for c in combo]
        s = omaha_bot_score(cand)
        if s > best_score:
            best_score, best_combo = s, combo
    bot = [cards[c] for c in best_combo]
    rem3 = [cards[i] for i in range(7) if i not in best_combo]
    # Top = highest-rank of rem3 (tiebreak by higher card index).
    top_local = 0
    for i in range(1, 3):
        ci, cb = rem3[i], rem3[top_local]
        if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
            top_local = i
    top = rem3[top_local]
    mid = [rem3[i] for i in range(3) if i != top_local]
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


# ============================================================
# v65 setting decoder
# ============================================================

_MID_PAIRS = np.array(list(combinations(range(6), 2)), dtype=np.int64)


def decode_v65(hand, setting_idx):
    top_i, mid_combo_i = divmod(setting_idx, 15)
    a, b = _MID_PAIRS[mid_combo_i]
    remaining = [i for i in range(7) if i != top_i]
    mid_pos = (remaining[int(a)], remaining[int(b)])
    bot_pos = [remaining[j] for j in range(6) if j != int(a) and j != int(b)]
    top = int(hand[top_i])
    mid = np.array([hand[mid_pos[0]], hand[mid_pos[1]]], dtype=np.int64)
    bot = np.array([hand[p] for p in bot_pos], dtype=np.int64)
    return top, mid, bot


def me_strategy(hand):
    """V4 player = v65 production chain."""
    setting_idx = int(v65_strategy(hand))
    return decode_v65(hand.astype(np.int64), setting_idx)


# ============================================================
# Pairwise score (me vs ONE opponent, includes scoop logic)
# ============================================================

def score_pair(me_set, opp_set, ba, bb, ev):
    mt, mm, mb = me_set
    ot, om, ob = opp_set
    rk = [
        (ev.eval_top(mt, ba), ev.eval_top(ot, ba), PTS_TOP),
        (ev.eval_mid(mm, ba), ev.eval_mid(om, ba), PTS_MID),
        (ev.eval_bot(mb, ba), ev.eval_bot(ob, ba), PTS_BOT),
        (ev.eval_top(mt, bb), ev.eval_top(ot, bb), PTS_TOP),
        (ev.eval_mid(mm, bb), ev.eval_mid(om, bb), PTS_MID),
        (ev.eval_bot(mb, bb), ev.eval_bot(ob, bb), PTS_BOT),
    ]
    me_win = [a > b for a, b, _ in rk]
    op_win = [a < b for a, b, _ in rk]
    if all(me_win): return PTS_SCOOP
    if all(op_win): return -PTS_SCOOP
    pts = 0
    for a, b, p in rk:
        if a > b: pts += p
        elif a < b: pts -= p
    return pts


# ============================================================
# Run one scenario (me vs 3 opp_fns)
# ============================================================

def run_scenario(name, me_fn, opp_fns, n_sims, n_hands, ev, seed_base=2000):
    """Returns: cumulative_per_sim (n_sims, n_hands), per_opp_totals (n_sims, 3), all_pts (n_sims * n_hands,)"""
    assert len(opp_fns) == 3
    print(f"\n=== {name} ===")
    print(f"  Me: v65   |   Opps: {[fn.__name__ for fn in opp_fns]}")
    cum = np.empty((n_sims, n_hands), dtype=np.float64)
    per_opp_tot = np.zeros((n_sims, 3), dtype=np.float64)
    all_pts = []
    for s in range(n_sims):
        rng = np.random.default_rng(seed=seed_base + s)
        t0 = time.time()
        pts = np.empty(n_hands, dtype=np.float64)
        po = np.zeros(3, dtype=np.float64)
        for h in range(n_hands):
            deck = rng.permutation(52)
            me_h = np.sort(deck[:7]).astype(np.uint8)
            op_h = [np.sort(deck[7 + 7*k:14 + 7*k]).astype(np.uint8) for k in range(3)]
            ba = deck[28:33].astype(np.int64)
            bb = deck[33:38].astype(np.int64)
            me_set = me_fn(me_h)
            tot = 0
            for k in range(3):
                opp_set = opp_fns[k](op_h[k])
                d = score_pair(me_set, opp_set, ba, bb, ev)
                po[k] += d
                tot += d
            pts[h] = tot
        cum[s] = np.cumsum(pts * STAKE)
        per_opp_tot[s] = po * STAKE
        all_pts.append(pts)
        elapsed = time.time() - t0
        print(f"  sim {s+1:2d}: final=${cum[s,-1]:+,.0f}  pts/h={pts.mean():+.3f}  "
              f"opps=[${po[0]*STAKE:+,.0f}, ${po[1]*STAKE:+,.0f}, ${po[2]*STAKE:+,.0f}]  ({elapsed:.1f}s)")
    flat = np.concatenate(all_pts)
    print(f"  AGGREGATE: mean ${flat.mean()*STAKE:+.2f}/h  stdev_pts={flat.std():.2f}  "
          f"final mean ${cum[:,-1].mean():+,.0f} ± ${cum[:,-1].std():,.0f}")
    return cum, per_opp_tot, flat


# ============================================================
# Step 1: deterministic grid slice
# ============================================================

def run_grid_slice():
    print("\n" + "=" * 70)
    print("STEP 1 — Deterministic grid slice (infinite-sample EV vs each Rust profile)")
    print("=" * 70)
    if not GRID_PATH.exists():
        print(f"  SKIP — {GRID_PATH} not found")
        return None
    arr = np.load(GRID_PATH, allow_pickle=True)
    hands_bytes = arr["hands_bytes"]
    ev_grid = arr["ev_grid"]
    profile_ids = list(arr["profile_ids"])
    print(f"  Grid: {hands_bytes.shape[0]:,} hands × {len(profile_ids)} profiles × 105 settings")
    print(f"  Computing v65 picks across all hands ...")
    t0 = time.time()
    picks = np.empty(hands_bytes.shape[0], dtype=np.int32)
    for i in range(hands_bytes.shape[0]):
        picks[i] = int(v65_strategy(hands_bytes[i]))
    print(f"  picks done in {time.time()-t0:.1f}s")
    results = {}
    print(f"\n  v65 expected EV per opponent (mean across {hands_bytes.shape[0]:,} hands):")
    print(f"  {'Profile':<25} {'pts/hand vs 1 opp':>20} {'$ vs 1 opp':>15} {'$ vs 3 opp':>15}")
    for p_idx, p_id in enumerate(profile_ids):
        evs = ev_grid[np.arange(hands_bytes.shape[0]), p_idx, picks]
        mean = float(np.mean(evs))
        std = float(np.std(evs))
        results[p_id] = mean
        print(f"  {p_id:<25} {mean:>+20.4f} {mean*STAKE:>+15.2f} {mean*STAKE*3:>+15.2f}  (±{std:.2f} cross-hand)")
    print()
    print(f"  → vs ANY single profile: stderr is sqrt(var/N) per hand; over 1,000 hands ~$0.5-1/hand.")
    return results


# ============================================================
# Main
# ============================================================

def main():
    print("=" * 70)
    print("MC FULL FIELD TEST — V4 guide vs realistic competent fields")
    print("=" * 70)
    print(f"  Sample: {N_SIMS} sims × {HANDS_PER_SIM:,} hands = {N_SIMS*HANDS_PER_SIM:,} hands per scenario")
    print(f"  Stake: ${STAKE:.0f}/point")

    grid_results = run_grid_slice()

    print(f"\nLoading lookup table ...")
    lookup = load_lookup_table(LOOKUP_PATH)
    print(f"  {lookup.size:,} entries")
    ev = Evaluator(lookup)

    scenarios = []

    # ----- Validation: symmetry test (v65 vs 3× v65) -----
    print("\n" + "=" * 70)
    print("STEP 2 — Validation: v65 vs 3× v65 (should yield ~$0)")
    print("=" * 70)
    sym_cum, sym_po, sym_flat = run_scenario(
        "SYMMETRY (v65 vs 3×v65)",
        me_strategy,
        [me_strategy, me_strategy, me_strategy],
        N_SIMS, HANDS_PER_SIM, ev, seed_base=3000,
    )
    sym_final_mean = float(sym_cum[:, -1].mean())
    sym_final_se = float(sym_cum[:, -1].std() / np.sqrt(N_SIMS))
    print(f"\n  SYMMETRY VERDICT: final mean ${sym_final_mean:+,.0f} ± ${sym_final_se:,.0f} (SE across sims)")
    z = sym_final_mean / sym_final_se if sym_final_se > 0 else 0
    if abs(z) < 2.0:
        print(f"  ✅ PASS — |z| = {abs(z):.2f} < 2.0, consistent with $0 expected mean")
    else:
        print(f"  ❌ WARNING — |z| = {abs(z):.2f} ≥ 2.0, possible bias in simulator")
    scenarios.append(("Symmetry (v65 vs 3× v65) — validation", sym_cum, sym_po, sym_flat))

    # ----- Main: 4 opponent scenarios -----
    print("\n" + "=" * 70)
    print("STEP 3 — Main scenarios (4 opponent field configurations)")
    print("=" * 70)

    scenarios.append(("v65 vs 3× Pair-First Standardist", *run_scenario(
        "HOMOGENEOUS A — Pair-First Standardist",
        me_strategy,
        [opp_pair_first_standardist] * 3,
        N_SIMS, HANDS_PER_SIM, ev, seed_base=4000,
    )))

    scenarios.append(("v65 vs 3× Top-Greedy Defender", *run_scenario(
        "HOMOGENEOUS B — Top-Greedy Defender",
        me_strategy,
        [opp_top_greedy_defender] * 3,
        N_SIMS, HANDS_PER_SIM, ev, seed_base=5000,
    )))

    scenarios.append(("v65 vs 3× Balanced Pro (baseline)", *run_scenario(
        "BASELINE — Balanced Pro (mfsuitaware port)",
        me_strategy,
        [opp_balanced_pro] * 3,
        N_SIMS, HANDS_PER_SIM, ev, seed_base=6000,
    )))

    scenarios.append(("v65 vs Mixed field (Standardist + Top-Greedy + Balanced)", *run_scenario(
        "MIXED — Standardist + Top-Greedy + Balanced",
        me_strategy,
        [opp_pair_first_standardist, opp_top_greedy_defender, opp_balanced_pro],
        N_SIMS, HANDS_PER_SIM, ev, seed_base=7000,
    )))

    # ----- Build chart -----
    print("\n" + "=" * 70)
    print("STEP 4 — Building chart")
    print("=" * 70)
    build_chart(scenarios, sym_passed=(abs(z) < 2.0))


def build_chart(scenarios, sym_passed=True):
    # Layout: 2 rows × 3 cols. Slot 0 = symmetry, slots 1-4 = real scenarios, slot 5 = aggregate summary.
    titles = [s[0] for s in scenarios] + ["Per-scenario summary"]
    fig = make_subplots(
        rows=2, cols=3,
        subplot_titles=titles,
        horizontal_spacing=0.07, vertical_spacing=0.13,
    )

    x = np.arange(1, HANDS_PER_SIM + 1)
    for idx, (name, cum, per_opp_totals, flat) in enumerate(scenarios):
        row = idx // 3 + 1
        col = idx % 3 + 1
        for i in range(N_SIMS):
            fig.add_trace(go.Scatter(
                x=x, y=cum[i], mode="lines",
                name=f"Sim {i+1}",
                line=dict(color=COLORS[i], width=1.4),
                showlegend=(idx == 0),
                hovertemplate=f"<b>{name}</b><br>Sim {i+1}<br>Hand #%{{x:,}}<br>$%{{y:+,.0f}}<extra></extra>",
                legendgroup=f"sim{i+1}",
            ), row=row, col=col)
        # Mean trend.
        mean_per_hand = float(flat.mean() * STAKE)
        fig.add_trace(go.Scatter(
            x=x, y=mean_per_hand * x, mode="lines",
            name="Mean trend",
            line=dict(color="black", width=2, dash="dash"),
            showlegend=(idx == 0),
            legendgroup="mean",
            hovertemplate=f"<b>Mean trend</b><br>Hand #%{{x:,}}<br>$%{{y:+,.0f}}<extra></extra>",
        ), row=row, col=col)
        fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"),
                      row=row, col=col)
        # Per-subplot annotation with stats.
        final = cum[:, -1]
        ann = (f"<b>{flat.mean()*STAKE:+.2f}/hand</b><br>"
               f"Final mean: ${final.mean():+,.0f}<br>"
               f"Stdev: ${final.std():,.0f}<br>"
               f"Range: ${final.min():+,.0f} to ${final.max():+,.0f}")
        # Plotly uses "x" not "x1" for the first subplot.
        x_axis = "x" if idx == 0 else f"x{idx+1}"
        y_axis = "y" if idx == 0 else f"y{idx+1}"
        fig.add_annotation(
            xref=f"{x_axis} domain", yref=f"{y_axis} domain",
            x=0.02, y=0.97, xanchor="left", yanchor="top",
            text=ann, showarrow=False,
            bgcolor="rgba(255,255,255,0.88)", bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1, borderpad=6,
            font=dict(size=10, family="monospace"), align="left",
        )

    # 6th slot — summary bar comparing final means per scenario.
    summary_names = [s[0].split("(")[0].strip() for s in scenarios]
    summary_means = [float(s[1][:, -1].mean()) for s in scenarios]
    summary_stds = [float(s[1][:, -1].std()) for s in scenarios]
    colors_bar = ["#aaaaaa" if "Symmetry" in s[0] else "#1f77b4" for s in scenarios]
    fig.add_trace(go.Bar(
        x=summary_names, y=summary_means,
        error_y=dict(type="data", array=summary_stds, visible=True),
        marker_color=colors_bar,
        showlegend=False,
        text=[f"${m:+,.0f}" for m in summary_means],
        textposition="outside",
        hovertemplate="<b>%{x}</b><br>Mean final: $%{y:+,.0f}<extra></extra>",
    ), row=2, col=3)
    fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"),
                  row=2, col=3)

    # Layout polish.
    fig.update_layout(
        title=dict(
            text=(
                "<b>V4 Guide MC Field Test — 5,000 hands × 10 sims per scenario</b><br>"
                f"<sub>Stake $10/pt · 4-handed · Validation + 4 competent opponent fields · "
                f"{'✅ SYMMETRY PASSED' if sym_passed else '❌ SYMMETRY FAILED'}</sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=18),
        ),
        plot_bgcolor="white",
        width=1800, height=1100,
        margin=dict(l=60, r=40, t=110, b=60),
        hovermode="closest",
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.05,
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.3)", borderwidth=1, font_size=10),
    )
    # Axes per subplot.
    for r in range(1, 3):
        for c in range(1, 4):
            if (r, c) == (2, 3): continue  # summary bar slot
            fig.update_xaxes(title="Hand #", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                             zeroline=False, tickformat=",", row=r, col=c)
            fig.update_yaxes(title="$ won/lost", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                             zeroline=False, tickformat="+$,.0f", row=r, col=c)
    # Summary bar axes.
    fig.update_xaxes(title="Scenario", tickangle=-25, row=2, col=3)
    fig.update_yaxes(title="Final mean $ (±1 std bars)", showgrid=True,
                     gridcolor="rgba(0,0,0,0.06)", tickformat="+$,.0f", row=2, col=3)

    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn", full_html=True,
                   config={"displayModeBar": True, "displaylogo": False})
    print(f"\nChart written to: {OUTPUT_HTML}")


if __name__ == "__main__":
    sys.exit(main() or 0)
