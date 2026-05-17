"""
Vectorized v65 vs 3× Oracle (clairvoyant adversary).

Each opp picks the setting from 105 that minimizes me's score, given they
see me's setting AND both boards. This is the maximum-exploitation upper
bound — real humans can't do this.

Vectorized: per opp hand, only 7+21+35=63 unique tier evals (× 2 boards)
instead of 105 × 6 = 630 naive evals. ~6× speedup.

Run scale: 5 sims × 5,000 hands.
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

LOOKUP_PATH = ROOT / "data" / "lookup_table.bin"
OUTPUT_HTML = ROOT / "MC_SIMULATION_V4_VS_ORACLE.html"

STAKE = 10.0
N_SIMS = 5
HANDS_PER_SIM = 5000

PTS_TOP, PTS_MID, PTS_BOT, PTS_SCOOP = 1, 2, 3, 20
COLORS = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd"]

# ============================================================
# Lookup + evaluator
# ============================================================

BINOM = np.zeros((52, 6), dtype=np.int64)
for n in range(52):
    BINOM[n, 0] = 1
    for k in range(1, 6):
        BINOM[n, k] = 0 if k > n else (1 if k == n else BINOM[n - 1, k - 1] + BINOM[n - 1, k])


def load_lookup(p):
    arr = np.frombuffer(p.read_bytes(), dtype=np.uint32)
    return arr if arr.size == 2_598_960 else arr[-2_598_960:].copy()


def colex5(c):
    return BINOM[c[:, 0], 1] + BINOM[c[:, 1], 2] + BINOM[c[:, 2], 3] + BINOM[c[:, 3], 4] + BINOM[c[:, 4], 5]


C65 = np.array(list(combinations(range(6), 5)), dtype=np.int64)
C75 = np.array(list(combinations(range(7), 5)), dtype=np.int64)
C42 = np.array(list(combinations(range(4), 2)), dtype=np.int64)
C53 = np.array(list(combinations(range(5), 3)), dtype=np.int64)


class Ev:
    def __init__(self, t): self.t = t

    def top_scalar(self, h1, b5):
        c = np.empty(6, dtype=np.int64); c[0] = h1; c[1:] = b5
        return int(self.t[colex5(np.sort(c[C65], axis=1))].max())

    def mid_scalar(self, h2, b5):
        c = np.empty(7, dtype=np.int64); c[:2] = h2; c[2:] = b5
        return int(self.t[colex5(np.sort(c[C75], axis=1))].max())

    def bot_scalar(self, h4, b5):
        hp, bt = h4[C42], b5[C53]
        c = np.empty((6, 10, 5), dtype=np.int64)
        c[:, :, :2] = hp[:, None, :]; c[:, :, 2:] = bt[None, :, :]
        return int(self.t[colex5(np.sort(c.reshape(60, 5), axis=1))].max())

    # ----- Batched evaluators for oracle: all 7 tops, 21 mid-pairs, 35 bot-quads -----

    def all_tops_for_hand(self, hand7: np.ndarray, board5: np.ndarray) -> np.ndarray:
        """Return (7,) array of top-ranks: best 5 of (hand[i] + board) for each i."""
        # 7 tops × 6-card-combos-of-5 = 42 combos. Build them once and look up.
        out = np.empty(7, dtype=np.int64)
        for i in range(7):
            c = np.empty(6, dtype=np.int64); c[0] = hand7[i]; c[1:] = board5
            out[i] = self.t[colex5(np.sort(c[C65], axis=1))].max()
        return out

    def all_mids_for_hand(self, hand7: np.ndarray, board5: np.ndarray, pairs21: np.ndarray) -> np.ndarray:
        """pairs21: (21, 2) of hand positions. Returns (21,) mid ranks."""
        out = np.empty(21, dtype=np.int64)
        for i in range(21):
            a, b = pairs21[i]
            c = np.empty(7, dtype=np.int64); c[0] = hand7[a]; c[1] = hand7[b]; c[2:] = board5
            out[i] = self.t[colex5(np.sort(c[C75], axis=1))].max()
        return out

    def all_bots_for_hand(self, hand7: np.ndarray, board5: np.ndarray, quads35: np.ndarray) -> np.ndarray:
        """quads35: (35, 4) of hand positions. Returns (35,) bot ranks (Omaha 2+3)."""
        out = np.empty(35, dtype=np.int64)
        for i in range(35):
            cards = hand7[quads35[i]]
            hp, bt = cards[C42], board5[C53]
            c = np.empty((6, 10, 5), dtype=np.int64)
            c[:, :, :2] = hp[:, None, :]; c[:, :, 2:] = bt[None, :, :]
            out[i] = self.t[colex5(np.sort(c.reshape(60, 5), axis=1))].max()
        return out


# ============================================================
# Precompute setting-decoding tables (global, hand-independent)
# ============================================================

_MID_PAIRS_LOCAL = np.array(list(combinations(range(6), 2)), dtype=np.int64)

MID_PAIRS_GLOBAL = np.array(list(combinations(range(7), 2)), dtype=np.int64)  # (21, 2)
BOT_COMBOS_GLOBAL = np.array(list(combinations(range(7), 4)), dtype=np.int64)  # (35, 4)

# Map (sorted tuple) -> index for fast lookup.
_MID_PAIR_TO_IDX = {tuple(MID_PAIRS_GLOBAL[i]): i for i in range(21)}
_BOT_COMBO_TO_IDX = {tuple(BOT_COMBOS_GLOBAL[i]): i for i in range(35)}

# For each of 105 settings, store: (top_pos, mid_pair_idx_in_21, bot_combo_idx_in_35)
SETTING_TOP_POS = np.empty(105, dtype=np.int64)
SETTING_MID_PAIR_IDX = np.empty(105, dtype=np.int64)
SETTING_BOT_COMBO_IDX = np.empty(105, dtype=np.int64)
# Also store the actual hand-positions for the bot quad (for returning the setting).
SETTING_BOT_POS = np.empty((105, 4), dtype=np.int64)
SETTING_MID_POS = np.empty((105, 2), dtype=np.int64)

for top_i in range(7):
    remaining = [i for i in range(7) if i != top_i]
    for mid_combo_i in range(15):
        a, b = _MID_PAIRS_LOCAL[mid_combo_i]
        mi, mj = remaining[int(a)], remaining[int(b)]
        bot_pos = sorted([remaining[j] for j in range(6) if j != int(a) and j != int(b)])
        setting_idx = top_i * 15 + mid_combo_i
        SETTING_TOP_POS[setting_idx] = top_i
        SETTING_MID_PAIR_IDX[setting_idx] = _MID_PAIR_TO_IDX[(min(mi, mj), max(mi, mj))]
        SETTING_BOT_COMBO_IDX[setting_idx] = _BOT_COMBO_TO_IDX[tuple(bot_pos)]
        SETTING_MID_POS[setting_idx] = [mi, mj]
        SETTING_BOT_POS[setting_idx] = bot_pos


# ============================================================
# v65 picker
# ============================================================

def me_strategy(hand: np.ndarray):
    setting_idx = int(v65_strategy(hand))
    pos_top = int(SETTING_TOP_POS[setting_idx])
    pos_mid = SETTING_MID_POS[setting_idx]
    pos_bot = SETTING_BOT_POS[setting_idx]
    hand_i = hand.astype(np.int64)
    top = int(hand_i[pos_top])
    mid = np.array([hand_i[pos_mid[0]], hand_i[pos_mid[1]]], dtype=np.int64)
    bot = np.array([hand_i[pos_bot[0]], hand_i[pos_bot[1]], hand_i[pos_bot[2]], hand_i[pos_bot[3]]], dtype=np.int64)
    return top, mid, bot


# ============================================================
# Oracle: vectorized over all 105 settings for an opp hand
# ============================================================

def opp_oracle_score(opp_hand: np.ndarray, me_set, ba: np.ndarray, bb: np.ndarray, ev: Ev) -> int:
    """Return me's score (per hand, including scoop) when opp plays the best response.

    The best response is the setting that minimizes me's score.
    """
    opp_hand_i = opp_hand.astype(np.int64)

    # Compute me's per-tier ranks ONCE (me's setting is fixed).
    me_top_a = ev.top_scalar(me_set[0], ba)
    me_top_b = ev.top_scalar(me_set[0], bb)
    me_mid_a = ev.mid_scalar(me_set[1], ba)
    me_mid_b = ev.mid_scalar(me_set[1], bb)
    me_bot_a = ev.bot_scalar(me_set[2], ba)
    me_bot_b = ev.bot_scalar(me_set[2], bb)

    # Compute opp's 7 unique top ranks × 2 boards.
    opp_top_a_unique = ev.all_tops_for_hand(opp_hand_i, ba)  # (7,)
    opp_top_b_unique = ev.all_tops_for_hand(opp_hand_i, bb)  # (7,)
    # Compute opp's 21 unique mid pair ranks × 2 boards.
    opp_mid_a_unique = ev.all_mids_for_hand(opp_hand_i, ba, MID_PAIRS_GLOBAL)  # (21,)
    opp_mid_b_unique = ev.all_mids_for_hand(opp_hand_i, bb, MID_PAIRS_GLOBAL)  # (21,)
    # Compute opp's 35 unique bot quad ranks × 2 boards.
    opp_bot_a_unique = ev.all_bots_for_hand(opp_hand_i, ba, BOT_COMBOS_GLOBAL)  # (35,)
    opp_bot_b_unique = ev.all_bots_for_hand(opp_hand_i, bb, BOT_COMBOS_GLOBAL)  # (35,)

    # Map setting_idx -> rank for each tier.
    opp_top_a = opp_top_a_unique[SETTING_TOP_POS]            # (105,)
    opp_top_b = opp_top_b_unique[SETTING_TOP_POS]
    opp_mid_a = opp_mid_a_unique[SETTING_MID_PAIR_IDX]       # (105,)
    opp_mid_b = opp_mid_b_unique[SETTING_MID_PAIR_IDX]
    opp_bot_a = opp_bot_a_unique[SETTING_BOT_COMBO_IDX]      # (105,)
    opp_bot_b = opp_bot_b_unique[SETTING_BOT_COMBO_IDX]

    # Compute me's score vs each opp setting (vectorized).
    # +pts if me wins, -pts if opp wins, 0 if chop.
    top_a_d = np.sign(me_top_a - opp_top_a)
    top_b_d = np.sign(me_top_b - opp_top_b)
    mid_a_d = np.sign(me_mid_a - opp_mid_a)
    mid_b_d = np.sign(me_mid_b - opp_mid_b)
    bot_a_d = np.sign(me_bot_a - opp_bot_a)
    bot_b_d = np.sign(me_bot_b - opp_bot_b)

    pts = (PTS_TOP * (top_a_d + top_b_d) +
           PTS_MID * (mid_a_d + mid_b_d) +
           PTS_BOT * (bot_a_d + bot_b_d))  # (105,) normal scoring

    # Scoop detection.
    all_me_win = (top_a_d == 1) & (top_b_d == 1) & (mid_a_d == 1) & (mid_b_d == 1) & (bot_a_d == 1) & (bot_b_d == 1)
    all_opp_win = (top_a_d == -1) & (top_b_d == -1) & (mid_a_d == -1) & (mid_b_d == -1) & (bot_a_d == -1) & (bot_b_d == -1)
    pts = np.where(all_me_win, PTS_SCOOP, pts)
    pts = np.where(all_opp_win, -PTS_SCOOP, pts)

    # Opp picks the setting that MINIMIZES me's score.
    return int(pts.min())


def main():
    print("Loading lookup ...")
    lookup = load_lookup(LOOKUP_PATH)
    ev = Ev(lookup)
    print(f"  {lookup.size:,} entries\n")

    print(f"Running {N_SIMS} sims × {HANDS_PER_SIM:,} hands × 3 oracle opps per hand ...")
    print(f"  (vectorized: 63 unique tier evals per opp instead of 630)\n", flush=True)

    cum = np.empty((N_SIMS, HANDS_PER_SIM), dtype=np.float64)
    all_pts = []

    for s in range(N_SIMS):
        rng = np.random.default_rng(seed=9000 + s)
        t0 = time.time()
        pts = np.empty(HANDS_PER_SIM, dtype=np.float64)
        for h in range(HANDS_PER_SIM):
            deck = rng.permutation(52)
            me_h = np.sort(deck[:7]).astype(np.uint8)
            op_h = [np.sort(deck[7 + 7*k:14 + 7*k]).astype(np.uint8) for k in range(3)]
            ba = deck[28:33].astype(np.int64)
            bb = deck[33:38].astype(np.int64)
            me_set = me_strategy(me_h)
            tot = 0
            for k in range(3):
                tot += opp_oracle_score(op_h[k], me_set, ba, bb, ev)
            pts[h] = tot
            if (h + 1) % 250 == 0:
                rate = (h + 1) / (time.time() - t0)
                eta_sec = (HANDS_PER_SIM - h - 1) / rate
                print(f"  sim {s+1}: {h+1}/{HANDS_PER_SIM}  ({rate:.0f} hands/s, ETA {eta_sec:.0f}s)", flush=True)
        elapsed = time.time() - t0
        cum[s] = np.cumsum(pts * STAKE)
        all_pts.append(pts)
        print(f"  sim {s+1}: final=${cum[s,-1]:+,.0f}  pts/h={pts.mean():+.3f}  ({elapsed:.0f}s)", flush=True)

    flat = np.concatenate(all_pts)
    finals = cum[:, -1]
    print()
    print(f"AGGREGATE ({N_SIMS * HANDS_PER_SIM:,} hands total):")
    print(f"  mean pts/hand        = {flat.mean():+.4f}  (${flat.mean()*STAKE:+.2f}/hand)")
    print(f"  stdev pts/hand       = {flat.std():.3f}")
    print(f"  mean final           = ${finals.mean():+,.0f}")
    print(f"  stdev final          = ${finals.std():,.0f}")
    print(f"  range                = ${finals.min():+,.0f} to ${finals.max():+,.0f}")
    print()

    # Chart.
    x = np.arange(1, HANDS_PER_SIM + 1)
    fig = go.Figure()
    for i in range(N_SIMS):
        fig.add_trace(go.Scatter(
            x=x, y=cum[i], mode="lines", name=f"Sim {i+1}",
            line=dict(color=COLORS[i], width=1.8),
            hovertemplate=f"<b>Sim {i+1}</b><br>Hand #%{{x:,}}<br>$%{{y:+,.0f}}<extra></extra>",
        ))
    mean_per_hand = float(flat.mean() * STAKE)
    fig.add_trace(go.Scatter(
        x=x, y=mean_per_hand * x, mode="lines", name="Mean trend",
        line=dict(color="black", width=2.5, dash="dash"),
        hovertemplate=f"<b>Mean</b><br>Hand #%{{x:,}}<br>$%{{y:+,.0f}}<extra></extra>",
    ))
    fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"),
                  annotation_text="break-even", annotation_position="top right")

    ann = (f"<b>v65 vs 3× Oracle (clairvoyant)</b><br><br>"
           f"<b>Setup</b><br>"
           f"• ${STAKE:.0f}/point · 4-handed<br>"
           f"• Each opp sees your setting + boards<br>"
           f"&nbsp; before choosing from 105 settings<br>"
           f"• Upper bound on exploitation<br>"
           f"<br>"
           f"<b>Results ({N_SIMS} sims × {HANDS_PER_SIM:,} hands)</b><br>"
           f"• Mean pts/hand: {flat.mean():+.3f}<br>"
           f"• Mean $/hand: ${mean_per_hand:+.2f}<br>"
           f"• Mean final: ${finals.mean():+,.0f}<br>"
           f"• Range: ${finals.min():+,.0f} to ${finals.max():+,.0f}<br>"
           f"<br>"
           f"<i>This is the worst case. Real humans</i><br>"
           f"<i>cannot see your pick + boards.</i>")
    fig.add_annotation(
        xref="paper", yref="paper", x=0.012, y=0.985,
        xanchor="left", yanchor="top", text=ann, showarrow=False,
        bgcolor="rgba(255,255,255,0.92)", bordercolor="rgba(0,0,0,0.4)",
        borderwidth=1, borderpad=10, font=dict(size=11, family="monospace"),
        align="left",
    )
    fig.update_layout(
        title=dict(text=(
            "<b>v65 vs 3× Oracle (clairvoyant adversary) — exploitation upper bound</b><br>"
            f"<sub>{N_SIMS} sims × {HANDS_PER_SIM:,} hands · vectorized brute-force best response per opp hand</sub>"
        ), x=0.5, xanchor="center", font=dict(size=17)),
        xaxis=dict(title="Hand number", showgrid=True, gridcolor="rgba(0,0,0,0.08)",
                   zeroline=False, tickformat=","),
        yaxis=dict(title="Cumulative $ won/lost", showgrid=True,
                   gridcolor="rgba(0,0,0,0.08)", zeroline=False, tickformat="+$,.0f"),
        hovermode="x unified",
        legend=dict(x=0.99, y=0.99, xanchor="right", yanchor="top",
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.3)", borderwidth=1, font_size=11),
        plot_bgcolor="white", width=1400, height=750,
        margin=dict(l=80, r=40, t=100, b=70),
    )
    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn", full_html=True,
                   config={"displayModeBar": True, "displaylogo": False})
    print(f"Chart: {OUTPUT_HTML}")


if __name__ == "__main__":
    main()
