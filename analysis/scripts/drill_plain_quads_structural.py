"""
Session 42 overnight — plain quads (4+1+1+1) structural drill.

plain_quads = 1 quad + 3 singletons (no second pair). 14,300 hands
(0.238% of canonical). v34_dt's residual is $9,670/1000h within-cat
which translates to ~$23/1000h whole-grid.

Possible structures:
  Q1: top = highest singleton, mid = 2 of quad, bot = other 2 quad + 2 sing
       → mid is paired by quad rank; bot has "2 of quad + 2 sing" Omaha
  Q2: top = highest singleton, mid = 2 lower singletons, bot = 4 quad cards
       → quads-on-bot (Omaha can't use 4-of-a-kind well; uses 2 of 4)
  Q3: top = quad-member (split quad), mid = 2 quad-leftovers, bot = ...
  Q4: top = highest singleton, mid = 2nd + 3rd singleton (≠ Q2 if rank order)

Heuristic candidates for Q1: which 2 quad cards to mid?
  - Q1a: 2 quad cards at suits NOT in singleton-suits (mirror QP rule)
  - Q1b: 2 quad cards at suits IN singleton-suits (so bot has matching pairs)
  - Q1c: canonical first-2

Heuristic candidates for Q2: which 2 singletons to mid?
  - Q2a: 2 lowest singletons (top=highest)
  - Q2b: 2 higher singletons (top=lowest, weird)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_plain_quads_structural.py
"""
from __future__ import annotations

import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0


def main() -> int:
    print("=" * 80)
    print("Session 42 overnight: plain quads (4+1+1+1) structural drill")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] identifying plain-quads hands ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    quads_idx = np.where(cats == 6)[0]  # cat 6 = quads (no second pair)
    n_q = len(quads_idx)
    pop_share_full = n_q / len(ch.hands)
    print(f"  plain_quads: {n_q:,} ({100*pop_share_full:.4f}%)")

    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    in_pref = quads_idx < 500_000
    pop_share_pref = int(in_pref.sum()) / 500_000

    full_v37 = np.zeros(n_q)
    full_oracle = np.zeros(n_q)
    pref_v37 = np.full(n_q, np.nan)
    pref_oracle = np.full(n_q, np.nan)

    # Per-hand fields
    quad_rank_arr = np.zeros(n_q, dtype=np.int8)
    s_high_arr = np.zeros(n_q, dtype=np.int8)
    s_mid_arr = np.zeros(n_q, dtype=np.int8)
    s_low_arr = np.zeros(n_q, dtype=np.int8)
    # Settings
    full_q1a = np.zeros(n_q)  # Q1: top=hi-sing, mid=2 quads at non-sing-suits
    full_q1b = np.zeros(n_q)  # Q1: top=hi-sing, mid=2 quads at sing-suits
    full_q1_oc = np.zeros(n_q)  # oracle within Q1 class
    full_q2a = np.zeros(n_q)  # Q2: top=hi-sing, mid=2 lower singletons, bot=4 quads
    full_q3_oc = np.zeros(n_q)  # split-quad oracle
    pref_q1a = np.full(n_q, np.nan)
    pref_q2a = np.full(n_q, np.nan)

    t0 = time.time()
    for i, cid in enumerate(quads_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        Q = next(r for r in range(2, 15) if rc[r] >= 4)
        sings = sorted([r for r in range(2, 15) if rc[r] == 1], reverse=True)
        quad_rank_arr[i] = Q
        s_high_arr[i] = sings[0]
        s_mid_arr[i] = sings[1]
        s_low_arr[i] = sings[2]

        pos_quad = sorted(j for j in range(7) if int(ranks[j]) == Q)
        pos_shi = next(j for j in range(7) if int(ranks[j]) == sings[0])
        pos_smid = next(j for j in range(7) if int(ranks[j]) == sings[1])
        pos_slo = next(j for j in range(7) if int(ranks[j]) == sings[2])

        sing_suits = sorted({int(suits[pos_shi]),
                              int(suits[pos_smid]),
                              int(suits[pos_slo])})
        # Q1a: mid = 2 quad cards at suits NOT in sing_suits
        non_sing_quads = sorted(j for j in pos_quad
                                 if int(suits[j]) not in sing_suits)
        if len(non_sing_quads) >= 2:
            q1a_setting = _setting_index_from_tmb(pos_shi, non_sing_quads[0],
                                                   non_sing_quads[1])
        else:
            # If less than 2 quads at non-sing-suits (rare: when 3+ singletons
            # cover 3+ different suits), fall back to canonical first 2
            q1a_setting = _setting_index_from_tmb(pos_shi, pos_quad[0], pos_quad[1])

        # Q1b: mid = 2 quad cards at suits IN sing_suits
        in_sing_quads = sorted(j for j in pos_quad
                                if int(suits[j]) in sing_suits)
        if len(in_sing_quads) >= 2:
            q1b_setting = _setting_index_from_tmb(pos_shi, in_sing_quads[0],
                                                   in_sing_quads[1])
        else:
            q1b_setting = q1a_setting

        # Q2a: mid = 2 lower singletons (s_mid + s_low), bot = 4 quad cards
        q2a_setting = _setting_index_from_tmb(pos_shi, pos_smid, pos_slo)

        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v37[i] = rowf[int(strategy_v37_rule7_three_pair(h))]
        full_oracle[i] = rowf.max()
        full_q1a[i] = rowf[q1a_setting]
        full_q1b[i] = rowf[q1b_setting]
        full_q2a[i] = rowf[q2a_setting]

        # Q1 oracle: best of all 6 quad-pair-mid choices (with top=hi-sing)
        q1_best = -np.inf
        for a in range(4):
            for b in range(a+1, 4):
                s = _setting_index_from_tmb(pos_shi, pos_quad[a], pos_quad[b])
                q1_best = max(q1_best, float(rowf[s]))
        full_q1_oc[i] = q1_best

        # Q3 oracle: top = a quad-member (split quad)
        q3_best = -np.inf
        for top_pos in pos_quad:
            block = rowf[top_pos*15:top_pos*15+15]
            q3_best = max(q3_best, float(block.max()))
        full_q3_oc[i] = q3_best

        if cid < 500_000:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v37[i] = rowp[int(strategy_v37_rule7_three_pair(h))]
            pref_oracle[i] = rowp.max()
            pref_q1a[i] = rowp[q1a_setting]
            pref_q2a[i] = rowp[q2a_setting]

        if i % 2000 == 0 and i > 0:
            rate = i / (time.time() - t0)
            print(f"    progress {i:>6,}/{n_q:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.0f}s")

    full_v37_reg = full_oracle - full_v37
    pref_v37_reg = pref_oracle[in_pref] - pref_v37[in_pref]

    print(f"\n[2/3] HEADLINES")
    print(f"  v37 baseline: full ${full_v37_reg.mean()*EV_TO_DOL*1000:+.1f}/1000h within-st  "
          f"(${full_v37_reg.mean()*EV_TO_DOL*1000*pop_share_full:+.2f}/1000h whole-grid)")

    def _row(name, full_picked, pref_picked=None, kind="det"):
        full_reg = full_oracle - full_picked
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        s = f"  {name:<55}  full ${full_delta:>+8.2f}/1000h"
        if pref_picked is not None:
            pref_reg = pref_oracle[in_pref] - pref_picked[in_pref]
            pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
            s += f"  pref ${pref_delta:>+8.2f}/1000h"
        s += f"  [{kind}]"
        print(s)
        return full_delta

    _row("v37 baseline", full_v37, pref_v37, "actual")
    print(f"  {'─'*100}")
    _row("Q1a det: top=hi-sing, mid=2-quads at non-sing-suits",
         full_q1a, pref_q1a)
    _row("Q1b det: top=hi-sing, mid=2-quads at sing-suits",
         full_q1b)
    _row("Q2a det: top=hi-sing, mid=2-lower-sing, bot=4-quads",
         full_q2a, pref_q2a)
    _row("Q1 oracle (best 1 of 6 quad-pair-mid choices)", full_q1_oc, kind="oracle")
    _row("Q3 oracle (split-quad-top, oracle-best)", full_q3_oc, kind="oracle")

    # Per-Q-rank breakdown
    print(f"\n[3/3] Per-quad-rank summary:")
    print(f"  {'Q_rank':>6}  {'n':>4}  {'v37$':>9}  {'Q1a$':>9}  {'Q1b$':>9}  {'Q2a$':>9}  best")
    cells = defaultdict(list)
    for i in range(n_q):
        cells[int(quad_rank_arr[i])].append(i)
    for Q in sorted(cells.keys(), reverse=True):
        idxs = np.array(cells[Q], dtype=np.int64)
        v37m = full_v37_reg[idxs].mean()
        q1am = (full_oracle[idxs] - full_q1a[idxs]).mean()
        q1bm = (full_oracle[idxs] - full_q1b[idxs]).mean()
        q2am = (full_oracle[idxs] - full_q2a[idxs]).mean()
        means = {"Q1a": q1am, "Q1b": q1bm, "Q2a": q2am}
        best = min(means, key=means.get)
        chars = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",10:"T",11:"J",12:"Q",13:"K",14:"A"}
        print(f"  {chars[Q]:>6}  {len(idxs):>4,}  ${v37m*EV_TO_DOL*1000:>+8.1f}  "
              f"${q1am*EV_TO_DOL*1000:>+8.1f}  ${q1bm*EV_TO_DOL*1000:>+8.1f}  "
              f"${q2am*EV_TO_DOL*1000:>+8.1f}  {best}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
