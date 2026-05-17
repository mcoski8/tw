"""
TRUE hand-by-hand Monte Carlo: V4 player vs 3 "competent" opponents.

Differences vs the EV-based version (mc_simulate_v4_vs_competent.py):
  - Real card dealing: 38 cards drawn without replacement from a 52-card
    deck per hand (4 players × 7 + 2 boards × 5).
  - Real strategy application: each player calls their strategy function
    on their 7-card hand to pick a setting (0-104).
  - Real tier evaluation using the project's 5-card lookup table:
      * top: best 5 of (1 hole + 5 board)        — 6 combos
      * mid: best 5 of (2 hole + 5 board)         — 21 combos
      * bot: Omaha 2+3 from (4 hole + 5 board)    — 60 combos
  - Real scoop detection: +20/-20 when one player wins all 6 matchups
    against the other with zero chops.
  - True variance: comes from the actual joint distribution of hand
    deals + board runouts, not from an externally-added noise term.

Player ("me"):       strategy_v65_mid_pair_chain_extend  (production rule chain)
Opponents (×3):      strategy_v3                          (project's "competent default" baseline)

Why strategy_v3 for opponents (matches user spec):
  v3 is the project's hand-coded baseline strategy from before the 25-rule
  expansion. It captures basic Hold'em/Omaha intuitions (pair-to-mid for
  KK/AA, never-split two pair, sensible no-pair setting) but MISSES every
  surgical refinement the project added in Sessions 25-97: no PMID-swap,
  no defensive inversion, no rainbow override, no DS-prioritized bot
  construction in narrow gates, no buyout. Exactly matches "competent
  Hold'em/Omaha winner who thinks Taiwanese has no leaks."

Stake: $10 per point.
Field size: 3 opponents (4-handed table).

Output:
  - Console: per-sim stats + aggregate stats
  - HTML chart: standalone, interactive (Plotly)
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

from encode_rules import strategy_v3  # noqa: E402
from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend as v65_strategy,
)


# ============================================================
# Configuration
# ============================================================

LOOKUP_PATH = ROOT / "data" / "lookup_table.bin"
OUTPUT_HTML = ROOT / "MC_SIMULATION_V4_TRUE_MC.html"

STAKE_DOLLARS_PER_POINT = 10.0
N_OPPONENTS = 3
N_SIMULATIONS = 10
HANDS_PER_SIMULATION = 1000

# Per-board tier point values (per opponent).
PTS_TOP = 1
PTS_MID = 2
PTS_BOT = 3
PTS_NORMAL_WIN = PTS_TOP + PTS_MID + PTS_BOT  # 6 per board, 12 per opp across 2 boards
PTS_SCOOP_BONUS_REPLACE = 20  # replaces 12 when all 6 matchups won, zero chops

# Color palette for the 10 sim lines.
COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]


# ============================================================
# 5-card evaluator (uses project's lookup_table.bin)
# ============================================================

# C(n, k) lookup, same as engine/src/lookup/mod.rs::BINOM.
BINOM = np.zeros((52, 6), dtype=np.int64)
for n in range(52):
    BINOM[n, 0] = 1
    for k in range(1, 6):
        if k > n:
            BINOM[n, k] = 0
        elif k == n:
            BINOM[n, k] = 1
        else:
            BINOM[n, k] = BINOM[n - 1, k - 1] + BINOM[n - 1, k]


def load_lookup_table(path: Path) -> np.ndarray:
    """Load the 5-card hand-rank lookup table as a uint32 array.

    Format mirrors engine/src/hand_eval.rs::write_to_disk — a flat array
    of 2,598,960 u32 values indexed by colex_index_5.
    """
    raw = path.read_bytes()
    arr = np.frombuffer(raw, dtype=np.uint32)
    n_5card = 2_598_960
    if arr.size < n_5card:
        raise ValueError(
            f"lookup table at {path} too small: {arr.size} u32s, "
            f"expected at least {n_5card}"
        )
    # The file may have a small header — heuristic: take last n_5card entries
    # if the file is larger, otherwise take the first n_5card.
    if arr.size == n_5card:
        return arr
    # Try the last n_5card entries (assumes a header prefix).
    return arr[-n_5card:].copy()


def colex_index_5_scalar(c0: int, c1: int, c2: int, c3: int, c4: int) -> int:
    """Colex-index for 5 sorted card values (in 0..52). Cards MUST be sorted ascending."""
    return int(
        BINOM[c0, 1]
        + BINOM[c1, 2]
        + BINOM[c2, 3]
        + BINOM[c3, 4]
        + BINOM[c4, 5]
    )


def colex_index_5_array(cards5: np.ndarray) -> np.ndarray:
    """Vectorized colex-index for an (N, 5) array of sorted card values.

    cards5 MUST be sorted ascending along axis=1.
    """
    return (
        BINOM[cards5[:, 0], 1]
        + BINOM[cards5[:, 1], 2]
        + BINOM[cards5[:, 2], 3]
        + BINOM[cards5[:, 3], 4]
        + BINOM[cards5[:, 4], 5]
    )


# Precomputed combination index tables.
COMBOS_6_CHOOSE_5 = np.array(list(combinations(range(6), 5)), dtype=np.int64)   # (6, 5)
COMBOS_7_CHOOSE_5 = np.array(list(combinations(range(7), 5)), dtype=np.int64)   # (21, 5)
COMBOS_4_CHOOSE_2 = np.array(list(combinations(range(4), 2)), dtype=np.int64)   # (6, 2)
COMBOS_5_CHOOSE_3 = np.array(list(combinations(range(5), 3)), dtype=np.int64)   # (10, 3)


class Evaluator:
    """Hand evaluator backed by the project's 5-card lookup table.

    Each eval_* method returns a u32 HandRank — higher = stronger. Equal
    ranks are exact chops.
    """

    def __init__(self, lookup_table: np.ndarray):
        self.table = lookup_table

    def eval_5(self, cards5: np.ndarray) -> int:
        """Evaluate a single 5-card hand. cards5 is a 5-element array of card indices 0..52."""
        sorted5 = np.sort(cards5)
        idx = colex_index_5_scalar(
            int(sorted5[0]), int(sorted5[1]), int(sorted5[2]),
            int(sorted5[3]), int(sorted5[4]),
        )
        return int(self.table[idx])

    def eval_top(self, hole1: int, board5: np.ndarray) -> int:
        """Hold'em best-5-of-6 with 1 hole card + 5 board cards."""
        cards6 = np.empty(6, dtype=np.int64)
        cards6[0] = hole1
        cards6[1:] = board5
        # 6 combos of 5 cards.
        combos = cards6[COMBOS_6_CHOOSE_5]      # (6, 5)
        combos = np.sort(combos, axis=1)
        ranks = self.table[colex_index_5_array(combos)]
        return int(ranks.max())

    def eval_mid(self, hole2: np.ndarray, board5: np.ndarray) -> int:
        """Hold'em best-5-of-7 with 2 hole cards + 5 board cards."""
        cards7 = np.empty(7, dtype=np.int64)
        cards7[:2] = hole2
        cards7[2:] = board5
        combos = cards7[COMBOS_7_CHOOSE_5]      # (21, 5)
        combos = np.sort(combos, axis=1)
        ranks = self.table[colex_index_5_array(combos)]
        return int(ranks.max())

    def eval_bot(self, hole4: np.ndarray, board5: np.ndarray) -> int:
        """Omaha best-5 with exactly 2-from-hole + 3-from-board (4+5 -> 60 combos)."""
        # Build 60 5-card combos via outer product of (4 choose 2) × (5 choose 3).
        hole_pairs = hole4[COMBOS_4_CHOOSE_2]                        # (6, 2)
        board_triples = board5[COMBOS_5_CHOOSE_3]                    # (10, 3)
        # Combine: (6, 1, 2) and (1, 10, 3) -> (6, 10, 5)
        combos = np.empty((6, 10, 5), dtype=np.int64)
        combos[:, :, :2] = hole_pairs[:, None, :]
        combos[:, :, 2:] = board_triples[None, :, :]
        combos_flat = combos.reshape(60, 5)
        combos_flat = np.sort(combos_flat, axis=1)
        ranks = self.table[colex_index_5_array(combos_flat)]
        return int(ranks.max())


# ============================================================
# Setting decoder (mirrors tw_analysis.settings.decode_setting)
# ============================================================

# 15 mid-pair (a, b) combos with a < b from 0..6.
_MID_PAIRS = np.array(list(combinations(range(6), 2)), dtype=np.int64)  # (15, 2)


def decode_setting_indices(setting_idx: int):
    """Return (top_i, mid_a, mid_b, bot_indices) where each is a position in
    the 7-card hand (0..6). All indices refer to the SORTED-ascending hand.
    """
    top_i, mid_combo_i = divmod(setting_idx, 15)
    a, b = _MID_PAIRS[mid_combo_i]
    # remaining = positions in 0..6 except top_i
    remaining = [i for i in range(7) if i != top_i]
    mid_card_positions = (remaining[a], remaining[b])
    bot_card_positions = tuple(remaining[j] for j in range(6) if j != a and j != b)
    return top_i, mid_card_positions, bot_card_positions


def apply_setting(hand: np.ndarray, setting_idx: int):
    """Decode setting_idx into (top_card, mid_cards_2, bot_cards_4) given a SORTED 7-card hand."""
    top_i, mid_pos, bot_pos = decode_setting_indices(setting_idx)
    top_card = int(hand[top_i])
    mid_cards = np.array([hand[mid_pos[0]], hand[mid_pos[1]]], dtype=np.int64)
    bot_cards = np.array([hand[bot_pos[0]], hand[bot_pos[1]],
                          hand[bot_pos[2]], hand[bot_pos[3]]], dtype=np.int64)
    return top_card, mid_cards, bot_cards


# ============================================================
# Pairwise scoring
# ============================================================

def score_matchup(me_setting, opp_setting, board5: np.ndarray, evaluator: Evaluator) -> int:
    """Return me's POINT delta vs ONE opponent on ONE board.

    me_setting / opp_setting are tuples (top_card, mid_cards_2, bot_cards_4).
    A scoop (all 3 tiers won with zero chops) returns +20 / -20.
    """
    me_top, me_mid, me_bot = me_setting
    op_top, op_mid, op_bot = opp_setting

    me_top_r = evaluator.eval_top(me_top, board5)
    op_top_r = evaluator.eval_top(op_top, board5)
    me_mid_r = evaluator.eval_mid(me_mid, board5)
    op_mid_r = evaluator.eval_mid(op_mid, board5)
    me_bot_r = evaluator.eval_bot(me_bot, board5)
    op_bot_r = evaluator.eval_bot(op_bot, board5)

    # Per-tier outcomes: +pts if me wins, -pts if opp wins, 0 if chop.
    top_delta = (PTS_TOP if me_top_r > op_top_r else (-PTS_TOP if me_top_r < op_top_r else 0))
    mid_delta = (PTS_MID if me_mid_r > op_mid_r else (-PTS_MID if me_mid_r < op_mid_r else 0))
    bot_delta = (PTS_BOT if me_bot_r > op_bot_r else (-PTS_BOT if me_bot_r < op_bot_r else 0))

    return top_delta + mid_delta + bot_delta


def score_hand_vs_opponent(me_setting, opp_setting, board_a: np.ndarray, board_b: np.ndarray,
                           evaluator: Evaluator) -> int:
    """Return me's POINT delta vs ONE opponent across BOTH boards, with scoop bonus.

    Scoop = win all 6 matchups (3 tiers × 2 boards) with zero chops → +20.
    Reverse-scoop (opponent wins all 6 with zero chops) → -20.
    Otherwise: sum of per-tier-per-board deltas (range -12 to +12).
    """
    me_top, me_mid, me_bot = me_setting
    op_top, op_mid, op_bot = opp_setting

    # Evaluate each tier on each board.
    me_top_a = evaluator.eval_top(me_top, board_a)
    op_top_a = evaluator.eval_top(op_top, board_a)
    me_mid_a = evaluator.eval_mid(me_mid, board_a)
    op_mid_a = evaluator.eval_mid(op_mid, board_a)
    me_bot_a = evaluator.eval_bot(me_bot, board_a)
    op_bot_a = evaluator.eval_bot(op_bot, board_a)

    me_top_b = evaluator.eval_top(me_top, board_b)
    op_top_b = evaluator.eval_top(op_top, board_b)
    me_mid_b = evaluator.eval_mid(me_mid, board_b)
    op_mid_b = evaluator.eval_mid(op_mid, board_b)
    me_bot_b = evaluator.eval_bot(me_bot, board_b)
    op_bot_b = evaluator.eval_bot(op_bot, board_b)

    # Per-matchup wins (treating chops as neither side winning).
    me_wins = [
        me_top_a > op_top_a, me_mid_a > op_mid_a, me_bot_a > op_bot_a,
        me_top_b > op_top_b, me_mid_b > op_mid_b, me_bot_b > op_bot_b,
    ]
    op_wins = [
        me_top_a < op_top_a, me_mid_a < op_mid_a, me_bot_a < op_bot_a,
        me_top_b < op_top_b, me_mid_b < op_mid_b, me_bot_b < op_bot_b,
    ]

    if all(me_wins):
        return PTS_SCOOP_BONUS_REPLACE
    if all(op_wins):
        return -PTS_SCOOP_BONUS_REPLACE

    # Normal scoring per tier per board.
    points = 0
    for me_r, op_r, pts in [
        (me_top_a, op_top_a, PTS_TOP),
        (me_mid_a, op_mid_a, PTS_MID),
        (me_bot_a, op_bot_a, PTS_BOT),
        (me_top_b, op_top_b, PTS_TOP),
        (me_mid_b, op_mid_b, PTS_MID),
        (me_bot_b, op_bot_b, PTS_BOT),
    ]:
        if me_r > op_r:
            points += pts
        elif me_r < op_r:
            points -= pts
    return points


# ============================================================
# Single hand simulation
# ============================================================

def simulate_one_hand(rng: np.random.Generator, evaluator: Evaluator) -> tuple[int, int, int]:
    """Deal one hand, score me (v65) vs 3 opponents (v3). Return (me_pts_vs_field, _, _)
    where the second/third elements are reserved for per-opp diagnostics.
    """
    # Deal 38 cards from a 52-card deck (4 players × 7 + 2 boards × 5).
    deck = rng.permutation(52)
    me_hand_raw = deck[:7]
    op1_hand_raw = deck[7:14]
    op2_hand_raw = deck[14:21]
    op3_hand_raw = deck[21:28]
    board_a = deck[28:33].astype(np.int64)
    board_b = deck[33:38].astype(np.int64)

    # Sort hands ascending (strategy functions expect this).
    me_hand = np.sort(me_hand_raw).astype(np.uint8)
    op1_hand = np.sort(op1_hand_raw).astype(np.uint8)
    op2_hand = np.sort(op2_hand_raw).astype(np.uint8)
    op3_hand = np.sort(op3_hand_raw).astype(np.uint8)

    # Pick settings.
    me_setting_idx = int(v65_strategy(me_hand))
    op1_setting_idx = int(strategy_v3(op1_hand))
    op2_setting_idx = int(strategy_v3(op2_hand))
    op3_setting_idx = int(strategy_v3(op3_hand))

    # Decode settings.
    me_set = apply_setting(me_hand.astype(np.int64), me_setting_idx)
    op1_set = apply_setting(op1_hand.astype(np.int64), op1_setting_idx)
    op2_set = apply_setting(op2_hand.astype(np.int64), op2_setting_idx)
    op3_set = apply_setting(op3_hand.astype(np.int64), op3_setting_idx)

    # Score me vs each opponent across both boards (with scoop detection per opponent).
    me_vs_op1 = score_hand_vs_opponent(me_set, op1_set, board_a, board_b, evaluator)
    me_vs_op2 = score_hand_vs_opponent(me_set, op2_set, board_a, board_b, evaluator)
    me_vs_op3 = score_hand_vs_opponent(me_set, op3_set, board_a, board_b, evaluator)

    total = me_vs_op1 + me_vs_op2 + me_vs_op3
    return total, me_vs_op1, me_vs_op2 + me_vs_op3  # last two not used downstream


# ============================================================
# Main: run simulations + plot
# ============================================================

def main() -> int:
    print(f"Loading lookup table from {LOOKUP_PATH} ...")
    lookup = load_lookup_table(LOOKUP_PATH)
    print(f"  table loaded: {lookup.size:,} entries, dtype={lookup.dtype}")

    # Quick sanity check on the evaluator: AKQJT spades (royal flush) should be the strongest.
    evaluator = Evaluator(lookup)
    # Royal flush of spades: T♠ J♠ Q♠ K♠ A♠ = card indices (8*4+3, 9*4+3, 10*4+3, 11*4+3, 12*4+3)
    royal = np.array([8*4+3, 9*4+3, 10*4+3, 11*4+3, 12*4+3], dtype=np.int64)
    royal_rank = evaluator.eval_5(royal)
    # 7-2 offsuit garbage: 2c, 3c, 4c, 5c, 7c (not a straight)
    garbage = np.array([0, 4, 8, 12, 20], dtype=np.int64)
    garbage_rank = evaluator.eval_5(garbage)
    print(f"  sanity: royal-flush rank = {royal_rank:,}, garbage rank = {garbage_rank:,}  "
          f"(royal > garbage: {royal_rank > garbage_rank})")
    if royal_rank <= garbage_rank:
        print("  ERROR: lookup table sanity failed. Aborting.")
        return 1
    print()

    print(f"Running {N_SIMULATIONS} simulations × {HANDS_PER_SIMULATION:,} hands each ...")
    cumulative_per_sim = np.empty((N_SIMULATIONS, HANDS_PER_SIMULATION), dtype=np.float64)
    points_per_hand_all = []

    for sim_idx in range(N_SIMULATIONS):
        rng = np.random.default_rng(seed=1000 + sim_idx)
        sim_start = time.time()
        points = np.empty(HANDS_PER_SIMULATION, dtype=np.float64)
        for h in range(HANDS_PER_SIMULATION):
            pts, _, _ = simulate_one_hand(rng, evaluator)
            points[h] = pts
        elapsed = time.time() - sim_start
        dollars = points * STAKE_DOLLARS_PER_POINT
        cumulative_per_sim[sim_idx] = np.cumsum(dollars)
        final = cumulative_per_sim[sim_idx, -1]
        avg_per_hand = points.mean()
        print(f"  sim {sim_idx+1:2d}/{N_SIMULATIONS}: final=${final:+,.0f}  "
              f"avg pts/hand={avg_per_hand:+.3f}  "
              f"({elapsed:.1f}s, {HANDS_PER_SIMULATION/elapsed:,.0f} hands/s)")
        points_per_hand_all.append(points)

    # Aggregate stats.
    final_dollars = cumulative_per_sim[:, -1]
    all_points = np.concatenate(points_per_hand_all)
    mean_pts_per_hand = float(all_points.mean())
    std_pts_per_hand = float(all_points.std())
    print()
    print(f"Aggregate over {N_SIMULATIONS} sims × {HANDS_PER_SIMULATION:,} hands "
          f"= {N_SIMULATIONS * HANDS_PER_SIMULATION:,} total hands:")
    print(f"  mean points/hand     = {mean_pts_per_hand:+.4f}  "
          f"(${mean_pts_per_hand*STAKE_DOLLARS_PER_POINT:+.2f} at $10/pt)")
    print(f"  stdev points/hand    = {std_pts_per_hand:.4f}")
    print(f"  mean final $         = ${final_dollars.mean():+,.0f}")
    print(f"  stdev final $        = ${final_dollars.std():,.0f}")
    print(f"  worst final $        = ${final_dollars.min():+,.0f}")
    print(f"  best final $         = ${final_dollars.max():+,.0f}")
    print(f"  expected (theoretic) = ${mean_pts_per_hand*STAKE_DOLLARS_PER_POINT*HANDS_PER_SIMULATION:+,.0f}")
    print()

    # Build the Plotly chart.
    print(f"Building Plotly chart ...")
    hand_numbers = np.arange(1, HANDS_PER_SIMULATION + 1)

    fig = go.Figure()

    # Sim lines.
    for sim_idx in range(N_SIMULATIONS):
        fig.add_trace(go.Scatter(
            x=hand_numbers,
            y=cumulative_per_sim[sim_idx],
            mode="lines",
            name=f"Simulation {sim_idx+1}",
            line=dict(color=COLORS[sim_idx], width=1.8),
            hovertemplate=(
                f"<b>Sim {sim_idx+1}</b><br>"
                "Hand #%{x:,}<br>"
                "Cumulative: $%{y:+,.0f}"
                "<extra></extra>"
            ),
        ))

    # Expected trend (theoretical mean × n).
    expected_per_hand = mean_pts_per_hand * STAKE_DOLLARS_PER_POINT
    expected_trend = expected_per_hand * hand_numbers
    fig.add_trace(go.Scatter(
        x=hand_numbers,
        y=expected_trend,
        mode="lines",
        name="Expected trend (mean × n)",
        line=dict(color="black", width=2.5, dash="dash"),
        hovertemplate=(
            "<b>Expected trend</b><br>"
            "Hand #%{x:,}<br>"
            "Expected: $%{y:+,.0f}"
            "<extra></extra>"
        ),
    ))

    fig.add_hline(
        y=0,
        line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"),
        annotation_text="break-even",
        annotation_position="bottom right",
        annotation_font_size=10,
    )

    # Annotation box.
    expected_total = expected_per_hand * HANDS_PER_SIMULATION
    summary_text = (
        f"<b>TRUE Monte Carlo</b> (hand-by-hand)<br>"
        f"<br>"
        f"<b>Setup</b><br>"
        f"• Stake: ${STAKE_DOLLARS_PER_POINT:.0f}/point<br>"
        f"• 4-handed table (me + {N_OPPONENTS} opponents)<br>"
        f"• Me: v65 production rule chain<br>"
        f"&nbsp; (proxy for V4 perfectly applied)<br>"
        f"• Opps: strategy_v3<br>"
        f"&nbsp; (project's competent-default baseline)<br>"
        f"<br>"
        f"<b>Results across {N_SIMULATIONS} sims</b><br>"
        f"• Expected: ${expected_total:+,.0f}/1000h<br>"
        f"• Mean final: ${final_dollars.mean():+,.0f}<br>"
        f"• Std final: ${final_dollars.std():,.0f}<br>"
        f"• Worst sim: ${final_dollars.min():+,.0f}<br>"
        f"• Best sim: ${final_dollars.max():+,.0f}<br>"
        f"<br>"
        f"<b>Per-hand stats</b><br>"
        f"• Mean: {mean_pts_per_hand:+.3f} pts (${expected_per_hand:+.2f})<br>"
        f"• Stdev: {std_pts_per_hand:.2f} pts<br>"
        f"<br>"
        f"<i>Scoops + chops + actual board luck included.</i>"
    )

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.012, y=0.985,
        xanchor="left", yanchor="top",
        text=summary_text,
        showarrow=False,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="rgba(0,0,0,0.4)",
        borderwidth=1,
        borderpad=10,
        font=dict(size=11, family="monospace"),
        align="left",
    )

    fig.update_layout(
        title=dict(
            text=(
                "<b>TRUE Monte Carlo: V4 Guide vs 3 Competent Opponents</b><br>"
                f"<sub>{N_SIMULATIONS} simulations × {HANDS_PER_SIMULATION:,} hands each · "
                f"$10/point · real deal-by-deal evaluation</sub>"
            ),
            x=0.5,
            xanchor="center",
            font=dict(size=18),
        ),
        xaxis=dict(
            title="Hand number",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.08)",
            zeroline=False,
            tickformat=",",
        ),
        yaxis=dict(
            title="Cumulative $ won/lost (at $10/point)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.08)",
            zeroline=False,
            tickformat="+$,.0f",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.4)",
            font_size=12,
        ),
        legend=dict(
            x=0.99, y=0.01,
            xanchor="right", yanchor="bottom",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1,
            font_size=11,
        ),
        plot_bgcolor="white",
        width=1400,
        height=800,
        margin=dict(l=80, r=40, t=100, b=70),
    )

    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        OUTPUT_HTML,
        include_plotlyjs="cdn",
        full_html=True,
        config={"displayModeBar": True, "displaylogo": False},
    )
    print(f"Chart written to {OUTPUT_HTML}")
    print("Open in a browser to interact.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
