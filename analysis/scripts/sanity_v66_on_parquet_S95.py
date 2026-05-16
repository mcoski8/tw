"""S95 sanity — verify strategy_v66 fires on the exact hands the parquet
identifies, and that the forced pick produces Layout A with DS bot.

Sampling: 50 hands per gate from the per-hand parquet matching:
  cell B_DS_AVAIL_LKR, Layout-A agree, v44 non-DS bot, sub-bucket in gate.

For each, assert:
  1. strategy_v66 fires (returns a setting different from v65).
  2. The forced setting is Layout A (top=kicker, mid=2 trips).
  3. The forced setting has DS bot (bot suits in 2+2).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v44_dt import strategy_v44_dt  # noqa: E402
from strategy_v65_mid_pair_chain_extend import strategy_v65_mid_pair_chain_extend  # noqa: E402
from strategy_v66_trips_layout_a_force_ds_bot import (  # noqa: E402
    _detect_trips_layout_a_force_ds_bot,
    GATE_TRIGGERS,
    make_strategy_v66,
)
from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.query import SETTING_HAND_INDICES  # noqa: E402

DATA = ROOT / "data"
CANON = DATA / "canonical_hands.bin"


def classify(hand: np.ndarray, pick: int):
    """Return (layout_label, bot_suit_label) for a (hand, pick)."""
    positions = SETTING_HAND_INDICES[pick]
    top_pos = int(positions[0])
    mid_a, mid_b = int(positions[1]), int(positions[2])
    bot_positions = [int(p) for p in positions[3:7]]

    ranks = (hand // 4) + 2
    suits = hand & 3
    rc = np.bincount(ranks.astype(int), minlength=15)
    trip_rank = int(np.where(rc == 3)[0][0])
    trip_pos_set = {int(i) for i in range(7) if int(ranks[i]) == trip_rank}

    n_trip_top = 1 if top_pos in trip_pos_set else 0
    n_trip_mid = sum(1 for p in (mid_a, mid_b) if p in trip_pos_set)
    n_trip_bot = sum(1 for p in bot_positions if p in trip_pos_set)

    if n_trip_top == 0 and n_trip_mid == 2 and n_trip_bot == 1:
        layout = "A"
    elif n_trip_bot == 2:
        layout = "B"
    elif n_trip_top == 1 and n_trip_mid == 2 and n_trip_bot == 0:
        layout = "C"
    else:
        layout = "SPLIT"

    bot_suits = [int(suits[p]) for p in bot_positions]
    cnt = sorted(Counter(bot_suits).values(), reverse=True)
    if cnt == [2, 2]:
        bot_suit = "DS"
    elif cnt == [2, 1, 1]:
        bot_suit = "SS"
    elif cnt == [3, 1]:
        bot_suit = "31"
    elif cnt == [4]:
        bot_suit = "4f"
    else:
        bot_suit = "RB"

    return layout, bot_suit


def main():
    ch = read_canonical_hands(CANON, mode="memmap")
    hands_arr = ch.hands

    df = pd.read_parquet(DATA / "drill_trips_v44_per_hand_structural.parquet")
    c1 = df[df["cell_idx"] == 1]
    agree_A = c1[(c1["v44_layout"] == 0) & (c1["or_layout"] == 0)]
    nonDS = agree_A[agree_A["v44_bot_suit"] != 0]
    print(f"target pop n={len(nonDS):,}")

    rng = np.random.default_rng(42)

    for gate_name in ["NARROW", "MEDIUM", "WIDE"]:
        triggers = GATE_TRIGGERS[gate_name]
        mask = np.zeros(len(nonDS), dtype=bool)
        for ksc, nkts, nbds in triggers:
            mask |= (
                (nonDS["kickers_max_suit_count"] == ksc)
                & (nonDS["n_kickers_in_trip_suits"] == nkts)
                & (nonDS["n_b_ds_routings"] == nbds)
            )
        seg = nonDS[mask]
        n_seg = len(seg)
        n_sample = min(50, n_seg)
        idx_sample = rng.choice(n_seg, size=n_sample, replace=False)
        rows = seg.iloc[idx_sample]
        print(f"\n=== Gate {gate_name}: sampling {n_sample}/{n_seg:,} ===")

        n_fired = 0
        n_layout_a = 0
        n_ds_bot = 0
        n_changed_from_v65 = 0
        for _, row in rows.iterrows():
            cid = int(row["canonical_id"])
            h = np.asarray(hands_arr[cid], dtype=np.uint8)
            v44 = int(strategy_v44_dt(h))
            v65 = int(strategy_v65_mid_pair_chain_extend(h))
            forced = _detect_trips_layout_a_force_ds_bot(h, triggers)
            if forced is None:
                # The rule didn't fire — diagnose why
                # Possible: v65's pick differs from v44's pick (chain divergence)
                # or v65 pick isn't Layout A non-DS
                v65_layout, v65_bot = classify(h, v65)
                v44_layout, v44_bot = classify(h, v44)
                if v65_layout != "A" or v65_bot == "DS":
                    pass  # expected non-fire — v65 differs from v44
                else:
                    # v65 IS layout-A non-DS — rule should have fired
                    print(f"    UNEXPECTED non-fire cid={cid}: v44={v44_layout}/{v44_bot} v65={v65_layout}/{v65_bot}")
                continue
            n_fired += 1
            f_layout, f_bot = classify(h, forced)
            if f_layout == "A":
                n_layout_a += 1
            if f_bot == "DS":
                n_ds_bot += 1
            if forced != v65:
                n_changed_from_v65 += 1
            if f_layout != "A" or f_bot != "DS":
                print(f"    BAD forced pick cid={cid}: layout={f_layout} bot={f_bot} (expected A/DS)")

        print(f"  fired={n_fired}/{n_sample}")
        print(f"  forced is Layout A: {n_layout_a}/{n_fired}")
        print(f"  forced has DS bot: {n_ds_bot}/{n_fired}")
        print(f"  forced changed from v65: {n_changed_from_v65}/{n_fired}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
