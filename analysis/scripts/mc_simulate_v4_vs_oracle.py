"""
MC test: v65 vs 3× Oracle (clairvoyant adversary).

Each opponent's strategy is the per-hand brute-force best response: enumerate
all 105 settings for the opp's 7-card hand, evaluate each one against v65's
pick on the actual two boards being dealt this hand, and the opp picks the
setting that MINIMIZES v65's score (= maximizes opp's score).

This is the strongest possible opponent — they see your setting and the
boards before deciding. It's an upper bound on v65's exploitability.

Run scale: 5 sims × 5,000 hands = 25,000 hands total. Slow because each
hand requires 3 × 105 = 315 brute-force setting evaluations.
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
# Lookup + evaluator (same as before)
# ============================================================

BINOM = np.zeros((52, 6), dtype=np.int64)
for n in range(52):
    BINOM[n, 0] = 1
    for k in range(1, 6):
        BINOM[n, k] = 0 if k > n else (1 if k == n else BINOM[n - 1, k - 1] + BINOM[n - 1, k])


def load_lookup(p): arr = np.frombuffer(p.read_bytes(), dtype=np.uint32); return arr if arr.size == 2_598_960 else arr[-2_598_960:].copy()


def colex5(c): return BINOM[c[:, 0], 1] + BINOM[c[:, 1], 2] + BINOM[c[:, 2], 3] + BINOM[c[:, 3], 4] + BINOM[c[:, 4], 5]


C65 = np.array(list(combinations(range(6), 5)), dtype=np.int64)
C75 = np.array(list(combinations(range(7), 5)), dtype=np.int64)
C42 = np.array(list(combinations(range(4), 2)), dtype=np.int64)
C53 = np.array(list(combinations(range(5), 3)), dtype=np.int64)


class Ev:
    def __init__(self, t): self.t = t

    def top(self, h1, b5):
        c = np.empty(6, dtype=np.int64); c[0] = h1; c[1:] = b5
        return int(self.t[colex5(np.sort(c[C65], axis=1))].max())

    def mid(self, h2, b5):
        c = np.empty(7, dtype=np.int64); c[:2] = h2; c[2:] = b5
        return int(self.t[colex5(np.sort(c[C75], axis=1))].max())

    def bot(self, h4, b5):
        hp, bt = h4[C42], b5[C53]
        c = np.empty((6, 10, 5), dtype=np.int64)
        c[:, :, :2] = hp[:, None, :]; c[:, :, 2:] = bt[None, :, :]
        return int(self.t[colex5(np.sort(c.reshape(60, 5), axis=1))].max())


# ============================================================
# Pre-compute all 105 setting decodings for a hand
# ============================================================

_MID_PAIRS = np.array(list(combinations(range(6), 2)), dtype=np.int64)

# Build a lookup: setting_idx -> (top_idx_in_hand, mid_idx_a_in_hand, mid_idx_b_in_hand, bot_idx_arr_in_hand)
# Once per script — these positions are the same for any hand.
_SETTING_POS = []
for top_i in range(7):
    remaining = [i for i in range(7) if i != top_i]
    for mid_combo_i in range(15):
        a, b = _MID_PAIRS[mid_combo_i]
        mi, mj = remaining[int(a)], remaining[int(b)]
        bi = [remaining[j] for j in range(6) if j != int(a) and j != int(b)]
        _SETTING_POS.append((top_i, mi, mj, bi[0], bi[1], bi[2], bi[3]))
_SETTING_POS = np.array(_SETTING_POS, dtype=np.int64)  # (105, 7) — top, mid_a, mid_b, bot_0..3


def decode_setting_for_hand(hand_i64: np.ndarray, setting_idx: int):
    """hand_i64: (7,) int64 of card indices. Returns (top, mid, bot) cards."""
    pos = _SETTING_POS[setting_idx]
    top = int(hand_i64[pos[0]])
    mid = np.array([hand_i64[pos[1]], hand_i64[pos[2]]], dtype=np.int64)
    bot = np.array([hand_i64[pos[3]], hand_i64[pos[4]], hand_i64[pos[5]], hand_i64[pos[6]]], dtype=np.int64)
    return top, mid, bot


def me_strategy(hand: np.ndarray):
    setting_idx = int(v65_strategy(hand))
    return decode_setting_for_hand(hand.astype(np.int64), setting_idx)


# ============================================================
# Scoring
# ============================================================

def score_pair(me_set, opp_set, ba, bb, ev):
    mt, mm, mb = me_set
    ot, om, ob = opp_set
    ranks = [
        (ev.top(mt, ba), ev.top(ot, ba), PTS_TOP),
        (ev.mid(mm, ba), ev.mid(om, ba), PTS_MID),
        (ev.bot(mb, ba), ev.bot(ob, ba), PTS_BOT),
        (ev.top(mt, bb), ev.top(ot, bb), PTS_TOP),
        (ev.mid(mm, bb), ev.mid(om, bb), PTS_MID),
        (ev.bot(mb, bb), ev.bot(ob, bb), PTS_BOT),
    ]
    if all(a > b for a, b, _ in ranks): return PTS_SCOOP
    if all(a < b for a, b, _ in ranks): return -PTS_SCOOP
    pts = 0
    for a, b, p in ranks:
        if a > b: pts += p
        elif a < b: pts -= p
    return pts


# ============================================================
# Oracle opponent: brute-force best response
# ============================================================

def opp_oracle(opp_hand: np.ndarray, me_set, ba: np.ndarray, bb: np.ndarray, ev: Ev):
    """For this opp hand, return the setting that minimizes me's score (= max opp's score).

    Brute-force over all 105 settings. Uses the actual boards being dealt
    (clairvoyant — sees boards + me's pick).
    """
    opp_hand_i = opp_hand.astype(np.int64)
    best_my_score = 10**9  # we want to MINIMIZE my score
    best_set = None
    for setting_idx in range(105):
        opp_set = decode_setting_for_hand(opp_hand_i, setting_idx)
        # Score from me's perspective.
        my_score = score_pair(me_set, opp_set, ba, bb, ev)
        if my_score < best_my_score:
            best_my_score = my_score
            best_set = opp_set
            if best_my_score == -PTS_SCOOP:
                break  # can't do worse than getting scooped
    return best_set


# ============================================================
# Run
# ============================================================

def main():
    print("Loading lookup ...")
    lookup = load_lookup(LOOKUP_PATH)
    ev = Ev(lookup)
    print(f"  {lookup.size:,} entries\n")

    print(f"Running {N_SIMS} sims × {HANDS_PER_SIM:,} hands × 3 oracle opps per hand ...")
    print(f"  (each hand requires 315 brute-force setting evaluations)\n")

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
                opp_set = opp_oracle(op_h[k], me_set, ba, bb, ev)
                tot += score_pair(me_set, opp_set, ba, bb, ev)
            pts[h] = tot
            if (h + 1) % 500 == 0:
                rate = (h + 1) / (time.time() - t0)
                eta = (HANDS_PER_SIM - h - 1) / rate
                print(f"  sim {s+1}: {h+1}/{HANDS_PER_SIM}  ({rate:.0f} hands/s, ETA {eta:.0f}s)")
        elapsed = time.time() - t0
        cum[s] = np.cumsum(pts * STAKE)
        all_pts.append(pts)
        print(f"  sim {s+1}: final=${cum[s,-1]:+,.0f}  pts/h={pts.mean():+.3f}  ({elapsed:.0f}s)")

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
           f"&nbsp; before choosing their 105 settings<br>"
           f"• Upper bound on exploitation<br>"
           f"<br>"
           f"<b>Results ({N_SIMS} sims × {HANDS_PER_SIM:,} hands)</b><br>"
           f"• Mean pts/hand: {flat.mean():+.3f}<br>"
           f"• Mean $/hand: ${mean_per_hand:+.2f}<br>"
           f"• Mean final: ${finals.mean():+,.0f}<br>"
           f"• Range: ${finals.min():+,.0f} to ${finals.max():+,.0f}<br>"
           f"<br>"
           f"<i>This is the worst-case opponent.</i><br>"
           f"<i>Real humans can't see your pick + boards.</i>")
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
            f"<sub>{N_SIMS} sims × {HANDS_PER_SIM:,} hands · brute-force best response per opp hand</sub>"
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
