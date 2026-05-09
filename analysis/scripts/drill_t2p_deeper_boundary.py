"""
Session 42 deep-dive — T2P deeper boundary search.

Initial T2P drill found "always F2" gives +$2.04 full / +$9.57 prefix.
This drill expands the boundary search to try many more conditions and
combinations, looking for a clean rule that captures more of the +$4.17
F2-oracle ceiling.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_t2p_deeper_boundary.py
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

RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def main() -> int:
    print("=" * 80)
    print("Session 42 deep-dive: T2P deeper boundary search")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] identifying T2P (3+2+2) hands ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    t2p_idx = []
    for cid in np.where(cats == 7)[0]:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        n_t = int(sum(rc[r] == 3 for r in range(2, 15)))
        n_q = int(sum(rc[r] >= 4 for r in range(2, 15)))
        n_p = int(sum(rc[r] == 2 for r in range(2, 15)))
        if n_t == 1 and n_p == 2 and n_q == 0:
            t2p_idx.append(int(cid))
    n_t2p = len(t2p_idx)
    pop_share_full = n_t2p / len(ch.hands)
    print(f"  T2P: {n_t2p:,} hands ({100*pop_share_full:.4f}%)")

    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    in_pref = np.array([cid < 500_000 for cid in t2p_idx], dtype=bool)
    pop_share_pref = int(in_pref.sum()) / 500_000

    # Pre-compute per-hand fields and oracle/F2/F3/F1 EVs (deterministic).
    print(f"\n[2/3] enumerating per-hand structural EVs ...", flush=True)
    full_v37 = np.zeros(n_t2p)
    full_oracle = np.zeros(n_t2p)
    full_F1 = np.zeros(n_t2p)
    full_F2 = np.zeros(n_t2p)
    full_F3 = np.zeros(n_t2p)
    pref_v37 = np.full(n_t2p, np.nan)
    pref_oracle = np.full(n_t2p, np.nan)
    pref_F1 = np.full(n_t2p, np.nan)
    pref_F2 = np.full(n_t2p, np.nan)
    pref_F3 = np.full(n_t2p, np.nan)
    T_arr = np.zeros(n_t2p, dtype=np.int8)
    H_arr = np.zeros(n_t2p, dtype=np.int8)
    L_arr = np.zeros(n_t2p, dtype=np.int8)

    t0 = time.time()
    for i, cid in enumerate(t2p_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        T = next(r for r in range(2, 15) if rc[r] == 3)
        pairs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        H, L = pairs
        T_arr[i] = T
        H_arr[i] = H
        L_arr[i] = L
        pos_T = sorted(j for j in range(7) if int(ranks[j]) == T)
        pos_H = sorted(j for j in range(7) if int(ranks[j]) == H)
        pos_L = sorted(j for j in range(7) if int(ranks[j]) == L)
        pair_suits = set(int(suits[j]) for j in pos_H) | set(int(suits[j]) for j in pos_L)
        # Top-T heuristic: T-card whose suit ∉ pair_suits if exists
        outside = [j for j in pos_T if int(suits[j]) not in pair_suits]
        top_T = outside[0] if outside else pos_T[0]
        mid_a, mid_b = sorted(j for j in pos_T if j != top_T)
        f1 = _setting_index_from_tmb(top_T, mid_a, mid_b)
        f2 = _setting_index_from_tmb(top_T, pos_H[0], pos_H[1])
        f3 = _setting_index_from_tmb(top_T, pos_L[0], pos_L[1])

        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v37[i] = rowf[int(strategy_v37_rule7_three_pair(h))]
        full_oracle[i] = rowf.max()
        full_F1[i] = rowf[f1]
        full_F2[i] = rowf[f2]
        full_F3[i] = rowf[f3]
        if cid < 500_000:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v37[i] = rowp[int(strategy_v37_rule7_three_pair(h))]
            pref_oracle[i] = rowp.max()
            pref_F1[i] = rowp[f1]
            pref_F2[i] = rowp[f2]
            pref_F3[i] = rowp[f3]
    print(f"  done in {time.time()-t0:.0f}s")

    full_v37_reg = full_oracle - full_v37
    pref_v37_reg = pref_oracle[in_pref] - pref_v37[in_pref]

    print(f"\n[3/3] BOUNDARY SEARCH ({len(t2p_idx):,} hands × many rules)")
    print(f"  v37 baseline regret: full ${full_v37_reg.mean()*EV_TO_DOL*1000:+.1f}/1000h")
    print(f"  {'rule':<60}  {'full_Δ':>10}  {'pref_Δ':>10}")

    def evaluate(rule_fn, label):
        pick = np.empty(n_t2p, dtype=int)
        for i in range(n_t2p):
            pick[i] = rule_fn(int(T_arr[i]), int(H_arr[i]), int(L_arr[i]))
        full_picked = np.choose(pick, [full_F1, full_F2, full_F3])
        full_reg = full_oracle - full_picked
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        pref_picked = np.choose(pick[in_pref], [pref_F1[in_pref], pref_F2[in_pref], pref_F3[in_pref]])
        pref_reg = pref_oracle[in_pref] - pref_picked
        pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
        marker = "★" if (full_delta > 1 and pref_delta > 1) else ""
        print(f"  {label:<60}  ${full_delta:>+8.2f}  ${pref_delta:>+8.2f}  {marker}")
        return full_delta + pref_delta

    rules = [
        ("always F2", lambda T,H,L: 1),
        ("always F3", lambda T,H,L: 2),
        ("F1 if T>=H else F2", lambda T,H,L: 0 if T >= H else 1),
        ("F1 if T>=H else F3", lambda T,H,L: 0 if T >= H else 2),
        ("F2 if T<H else F3", lambda T,H,L: 1 if T < H else 2),
        ("F2 if T<H AND H<10 else F3", lambda T,H,L: 1 if (T < H and H < 10) else (2 if T < H else 0)),
        ("F2 if T==H else F3 (T+H pair?)", lambda T,H,L: 1 if T == H else 2),  # T==H impossible by construction
        # T-vs-H comparisons
        ("F1 if T>H else F2 if H<=8 else F3", lambda T,H,L: 0 if T > H else (1 if H <= 8 else 2)),
        ("F1 if T>=H else F2 if H<=8 else F3", lambda T,H,L: 0 if T >= H else (1 if H <= 8 else 2)),
        # H-driven
        ("F2 if H<=8 else F3", lambda T,H,L: 1 if H <= 8 else 2),
        ("F2 if H<=9 else F3", lambda T,H,L: 1 if H <= 9 else 2),
        ("F2 if H<=10 else F3", lambda T,H,L: 1 if H <= 10 else 2),
        ("F2 if H<=11 else F3", lambda T,H,L: 1 if H <= 11 else 2),
        ("F3 if H>=A else F2", lambda T,H,L: 2 if H == 14 else 1),
        ("F3 if H>=K else F2", lambda T,H,L: 2 if H >= 13 else 1),
        # Combined
        ("F1 if T>=H elif H<=8 then F2 else F3", lambda T,H,L: 0 if T >= H else (1 if H <= 8 else 2)),
        ("F1 if T>=H elif H<=9 then F2 else F3", lambda T,H,L: 0 if T >= H else (1 if H <= 9 else 2)),
        ("F1 if T>=H elif H<=11 then F2 else F3", lambda T,H,L: 0 if T >= H else (1 if H <= 11 else 2)),
        # T-extreme
        ("F3 if T<=4 else F2", lambda T,H,L: 2 if T <= 4 else 1),
        ("F3 if T<=5 else F2", lambda T,H,L: 2 if T <= 5 else 1),
        ("F3 if T<=6 else F2", lambda T,H,L: 2 if T <= 6 else 1),
        ("F2 if T>=10 else F3", lambda T,H,L: 1 if T >= 10 else 2),
        ("F2 if T>=8 else F3", lambda T,H,L: 1 if T >= 8 else 2),
    ]

    scored = []
    for label, fn in rules:
        score = evaluate(fn, label)
        scored.append((label, score))
    scored.sort(key=lambda kv: -kv[1])
    print(f"\n  Top 5 rules by combined Δ (full + prefix):")
    for label, score in scored[:5]:
        print(f"    {label:<60}  combined ${score:+.2f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
