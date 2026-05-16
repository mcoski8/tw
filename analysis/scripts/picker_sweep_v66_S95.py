"""S95 picker sweep — try multiple deterministic Layout-A DS-bot picker
criteria and measure swap-right rate + EV(v66-v65) per criterion.

If no criterion clears the $5 SHIP bar at any gate, the rule-extraction
lever is structurally exhausted for this cell × intra-layout opportunity.
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
for p in (str(HERE), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v66_trips_layout_a_force_ds_bot import GATE_TRIGGERS  # noqa: E402
from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

DATA = ROOT / "data"
EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159


def enumerate_layout_a_ds_bot_settings(hand: np.ndarray):
    """Yield all Layout-A DS-bot settings for a trips hand.

    Yields: (setting_idx, top_rank, pair_tops_desc, bot_min, bot_sum,
             top_kicker_suit_in_trip_suits)
    """
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    rc = np.bincount(ranks.astype(int), minlength=15)
    if int((rc == 3).sum()) != 1:
        return
    trip_rank = int(np.where(rc == 3)[0][0])
    trip_pos = [int(i) for i in range(7) if int(ranks[i]) == trip_rank]
    kicker_pos = [int(i) for i in range(7) if int(ranks[i]) != trip_rank]
    trip_suits = sorted(int(suits[p]) for p in trip_pos)

    for bot_trip_local in range(3):
        bot_trip_pos = trip_pos[bot_trip_local]
        mid_trip_locals = sorted(i for i in range(3) if i != bot_trip_local)
        mid_a_pos = trip_pos[mid_trip_locals[0]]
        mid_b_pos = trip_pos[mid_trip_locals[1]]
        bot_trip_suit = int(suits[bot_trip_pos])

        for top_kicker_local in range(4):
            bot_kicker_locals = [k for k in range(4) if k != top_kicker_local]
            bot_kicker_pos_list = [kicker_pos[k] for k in bot_kicker_locals]
            bot_kicker_suits = [int(suits[p]) for p in bot_kicker_pos_list]
            bot_kicker_ranks = [int(ranks[p]) for p in bot_kicker_pos_list]
            bot_suits_arr = [bot_trip_suit] + bot_kicker_suits
            cnt = sorted(Counter(bot_suits_arr).values(), reverse=True)
            if cnt != [2, 2]:
                continue
            # Compute features
            by_suit = {}
            by_suit.setdefault(bot_trip_suit, []).append(int(ranks[bot_trip_pos]))
            for r, s in zip(bot_kicker_ranks, bot_kicker_suits):
                by_suit.setdefault(s, []).append(r)
            pair_tops = sorted(
                (max(rs) for rs in by_suit.values() if len(rs) >= 2),
                reverse=True,
            )
            top_pos_actual = kicker_pos[top_kicker_local]
            top_rank = int(ranks[top_pos_actual])
            top_suit = int(suits[top_pos_actual])
            bot_min = min([int(ranks[bot_trip_pos])] + bot_kicker_ranks)
            bot_sum = int(ranks[bot_trip_pos]) + sum(bot_kicker_ranks)
            top_in_trip_suit = int(top_suit in trip_suits)

            setting_idx = _setting_index_from_tmb(
                top_pos_actual, mid_a_pos, mid_b_pos
            )
            yield {
                "setting_idx": int(setting_idx),
                "top_rank": top_rank,
                "pair_top_1": int(pair_tops[0]),
                "pair_top_2": int(pair_tops[1]) if len(pair_tops) > 1 else 0,
                "bot_min": int(bot_min),
                "bot_sum": int(bot_sum),
                "top_in_trip_suit": top_in_trip_suit,
                "top_suit": top_suit,
            }


# Candidate picker criteria — each maps a config dict to a sortable key.
# Best = max under the key.
CRITERIA = {
    "BOT_PAIR_HI_then_2_then_TOP_DESC": lambda c: (c["pair_top_1"], c["pair_top_2"], c["top_rank"]),
    "BOT_PAIR_HI_then_2_then_TOP_ASC": lambda c: (c["pair_top_1"], c["pair_top_2"], -c["top_rank"]),
    "TOP_HIGH_then_pair_tops": lambda c: (c["top_rank"], c["pair_top_1"], c["pair_top_2"]),
    "TOP_LOW_then_pair_tops": lambda c: (-c["top_rank"], c["pair_top_1"], c["pair_top_2"]),
    "BOT_SUM_HI_then_TOP_DESC": lambda c: (c["bot_sum"], c["top_rank"]),
    "BOT_MIN_HI_then_PAIR_TOP_DESC": lambda c: (c["bot_min"], c["pair_top_1"], c["pair_top_2"]),
    "PAIR_TOP_2_HI_then_PAIR_TOP_1_HI": lambda c: (c["pair_top_2"], c["pair_top_1"], c["top_rank"]),
    "TOP_NOT_IN_TRIP_SUIT_then_pair_tops": lambda c: (-c["top_in_trip_suit"], c["pair_top_1"], c["pair_top_2"]),
}


def main():
    df = pd.read_parquet(DATA / "drill_trips_v44_per_hand_structural.parquet")
    c1 = df[df["cell_idx"] == 1]
    target = c1[(c1["v44_layout"] == 0) & (c1["v44_bot_suit"] != 0)].copy()
    canonical_ids = target["canonical_id"].astype(np.int64).to_numpy()
    v44_idx = target["v44_idx"].astype(np.int16).to_numpy()
    oracle_idx = target["oracle_idx"].astype(np.int16).to_numpy()
    or_bot_suit = target["or_bot_suit"].astype(np.int8).to_numpy()
    ksc = target["kickers_max_suit_count"].astype(np.int8).to_numpy()
    nkts = target["n_kickers_in_trip_suits"].astype(np.int8).to_numpy()
    nbds = target["n_b_ds_routings"].astype(np.int8).to_numpy()
    n_target = len(target)
    print(f"target n={n_target:,}")

    ch = read_canonical_hands(DATA / "canonical_hands.bin", mode="memmap")
    hands_arr = ch.hands
    grid = read_oracle_grid(DATA / "oracle_grid_full_realistic_n200.bin", mode="memmap")
    evs = grid.evs

    # Pre-compute per-hand list of (DS config metadata + setting_idx)
    print("enumerating Layout-A DS-bot configs per hand (one pass)")
    t0 = time.time()
    all_configs = []  # list of lists (per-hand)
    n_skipped = 0
    for i in range(n_target):
        cid = int(canonical_ids[i])
        h = np.asarray(hands_arr[cid], dtype=np.uint8)
        cfgs = list(enumerate_layout_a_ds_bot_settings(h))
        if not cfgs:
            all_configs.append(None)
            n_skipped += 1
        else:
            all_configs.append(cfgs)
    print(f"  done in {time.time()-t0:.1f}s; skipped {n_skipped:,}")

    # For each (gate, criterion), compute the lift
    print("\nGate × Criterion sweep:")
    print(f"  {'CRITERION':<48} | {'GATE':<8} | {'n_fired':>8} | {'changed':>8} | {'sr%':>6} | {'lift':>8}")
    print(f"  {'-'*48}-+-{'-'*8}-+-{'-'*8}-+-{'-'*8}-+-{'-'*6}-+-{'-'*8}")

    results = []
    for crit_name, crit_fn in CRITERIA.items():
        # Pre-compute the picker per hand
        rule_pick = np.empty(n_target, dtype=np.int16)
        for i in range(n_target):
            cfgs = all_configs[i]
            if cfgs is None:
                rule_pick[i] = v44_idx[i]
            else:
                best = max(cfgs, key=crit_fn)
                rule_pick[i] = int(best["setting_idx"])

        for gate_name in ["NARROW", "MEDIUM", "WIDE"]:
            triggers = GATE_TRIGGERS[gate_name]
            mask = np.zeros(n_target, dtype=bool)
            for tk in triggers:
                mask |= ((ksc == tk[0]) & (nkts == tk[1]) & (nbds == tk[2]))
            # Apply rule only when hand has DS configs available; else v65
            applicable = mask & np.array([c is not None for c in all_configs])
            v66 = np.where(applicable, rule_pick, v44_idx)
            n_fired = int(applicable.sum())
            n_chg = int((v66 != v44_idx).sum())
            # EV
            sum_delta = 0.0
            n_better = 0
            for i in np.where(applicable)[0]:
                cid = int(canonical_ids[i])
                er = evs[cid]
                d = float(er[int(v66[i])]) - float(er[int(v44_idx[i])])
                sum_delta += d
                if d > 0: n_better += 1
            lift = sum_delta / N_TOTAL_GRID * EV_TO_DOL * 1000
            sr = (n_better / n_chg) if n_chg > 0 else 0.0
            print(f"  {crit_name:<48} | {gate_name:<8} | {n_fired:>8,} | {n_chg:>8,} | "
                  f"{sr*100:>5.1f}% | ${lift:>+6.2f}")
            results.append({
                "criterion": crit_name, "gate": gate_name,
                "n_fired": n_fired, "n_changed": n_chg, "swap_right": sr,
                "lift_dol_per_1000h_n200": lift,
            })

    print("\n" + "=" * 80)
    print("BEST GATE × CRITERION (by N=200 lift):")
    best = max(results, key=lambda r: r["lift_dol_per_1000h_n200"])
    print(f"  Criterion: {best['criterion']}")
    print(f"  Gate:      {best['gate']}")
    print(f"  Lift:      ${best['lift_dol_per_1000h_n200']:+.2f}/1000h")
    print(f"  Swap-right: {best['swap_right']*100:.1f}%")
    print(f"  n_changed: {best['n_changed']:,}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
