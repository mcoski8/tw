"""
Session 38 — Sweep the v34 trip-rank boundary to find any improvement over v33.

For each candidate min_trip_for_C in {2..14}, compute the rule:
    use_C iff (trip_rank >= min_trip_for_C) AND (trip_rank > max_kicker_rank)

min=2 reproduces v33 exactly. Higher = more aggressive A-variant flipping.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
EV_TO_DOLLARS = 10.0
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}


def make_strategy(min_trip_for_C: int):
    """Return a closure implementing Rule 6 with given min-trip threshold."""
    from strategy_v28_rule5_rainbow import strategy_v28_rule5_rainbow
    from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb
    from strategy_v33_rule6_trips import (
        _bot_suit_profile_score,
        _bot_longest_run,
    )

    def detect(hand: np.ndarray) -> Optional[int]:
        h = np.asarray(hand, dtype=np.uint8)
        if h.shape[0] != 7:
            return None
        ranks = (h // 4) + 2
        suits = h & 0b11
        rank_counts = np.bincount(ranks, minlength=15)
        n_t = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
        n_p = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
        n_q = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
        if n_t != 1 or n_p != 0 or n_q != 0:
            return None

        trip_rank = next(r for r in range(2, 15) if rank_counts[r] == 3)
        trip_idx = sorted(j for j in range(7) if int(ranks[j]) == trip_rank)
        kicker_idx = sorted(
            (j for j in range(7) if j not in trip_idx),
            key=lambda j: -int(ranks[j]),
        )
        max_kicker_rank = int(ranks[kicker_idx[0]])

        use_c = (trip_rank >= min_trip_for_C) and (trip_rank > max_kicker_rank)
        if use_c:
            return _setting_index_from_tmb(trip_idx[0], trip_idx[1], trip_idx[2])

        top_pos = kicker_idx[0]
        other_kickers = kicker_idx[1:4]
        other_kicker_suits = [int(suits[j]) for j in other_kickers]
        other_kicker_ranks = [int(ranks[j]) for j in other_kickers]
        best_score = -1
        best_setting: Optional[int] = None
        for trip_for_bot_pos_idx in range(3):
            trip_for_bot = trip_idx[trip_for_bot_pos_idx]
            trips_for_mid = [trip_idx[i] for i in range(3)
                             if i != trip_for_bot_pos_idx]
            bot_suits = [int(suits[trip_for_bot])] + other_kicker_suits
            bot_ranks = [int(ranks[trip_for_bot])] + other_kicker_ranks
            profile = _bot_suit_profile_score(bot_suits)
            rank_sum = sum(bot_ranks)
            run = _bot_longest_run(bot_ranks)
            score = profile * 1_000_000 + rank_sum * 1_000 + run * 100
            if score > best_score:
                best_score = score
                best_setting = _setting_index_from_tmb(
                    top_pos, trips_for_mid[0], trips_for_mid[1])
        return best_setting

    def strat(hand: np.ndarray) -> int:
        chosen = detect(hand)
        if chosen is not None:
            return int(chosen)
        return int(strategy_v28_rule5_rainbow(hand))

    return strat


def main() -> int:
    print("loading data ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads", "trips_rank"])
    n_trips = ft["n_trips"].to_numpy()
    n_pairs = ft["n_pairs"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    trips_rank_full = ft["trips_rank"].to_numpy()
    mask_trips = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0)
    pop_share = float(mask_trips.mean())

    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:len(ft)])

    trips_idx = np.where(mask_trips)[0]
    rng = np.random.RandomState(0)
    SAMPLE_N = 30000
    sample_pos = rng.choice(len(trips_idx), SAMPLE_N, replace=False)
    sample_pos.sort()
    sample_canonical_ids = trips_idx[sample_pos]
    sample_trip_ranks = trips_rank_full[sample_canonical_ids]

    # Pre-cache hands and oracle EVs.
    hands = []
    evs_list = []
    oracle_ev = np.empty(SAMPLE_N, dtype=np.float64)
    for i, cid in enumerate(sample_canonical_ids):
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        evs = np.asarray(Y[cid], dtype=np.float64)
        hands.append(h)
        evs_list.append(evs)
        oracle_ev[i] = evs.max()

    def fmt_in(x): return x * EV_TO_DOLLARS * 1000
    def fmt_grid(x): return x * EV_TO_DOLLARS * 1000 * pop_share

    print("\n" + "=" * 80)
    print("Sweep min_trip_for_C: regret + Δ-vs-v33 on 30K trips probe")
    print("=" * 80)
    print(f"  {'min':>5}  {'rule':<25}  {'reg_$':>10}  {'vs_v33_$':>10}  {'changed':>7}")

    # Baseline v33
    from strategy_v33_rule6_trips import strategy_v33_rule6_trips  # noqa: E402
    v33_ev = np.array([evs_list[i][int(strategy_v33_rule6_trips(hands[i]))]
                       for i in range(SAMPLE_N)])
    v33_reg = (oracle_ev - v33_ev).mean()
    print(f"  {'v33':>5}  {'(trip > maxK = orig)':<25}  ${fmt_grid(v33_reg):>+8.2f}  "
          f"  {'baseline':>10}  {'—':>7}")

    # Sweep
    best_min = None
    best_delta = 0.0
    for min_trip in range(2, 16):
        if min_trip == 2:
            continue  # equivalent to v33; skip
        if min_trip > 14:
            continue
        strat = make_strategy(min_trip)
        ev = np.empty(SAMPLE_N, dtype=np.float64)
        n_changed = 0
        for i in range(SAMPLE_N):
            pick = int(strat(hands[i]))
            ev[i] = evs_list[i][pick]
            if ev[i] != v33_ev[i]:
                n_changed += 1
        reg = (oracle_ev - ev).mean()
        delta_vs_v33 = (v33_reg - reg)  # positive ⇒ v34 better
        label = f"trip ≥ {RANK_CHARS.get(min_trip, str(min_trip))} → C"
        marker = "*" if delta_vs_v33 > 0 else " "
        print(f"  {RANK_CHARS.get(min_trip, str(min_trip)):>5}  {label:<25}  "
              f"${fmt_grid(reg):>+8.2f}  ${fmt_grid(delta_vs_v33):>+8.2f}{marker} "
              f"{n_changed:>6,}")
        if delta_vs_v33 > best_delta:
            best_delta = delta_vs_v33
            best_min = min_trip

    # Pure "always-A" candidate (no C ever). Equivalent to min_trip = 15 (impossible).
    strat_always_a = make_strategy(min_trip_for_C=15)
    ev = np.array([evs_list[i][int(strat_always_a(hands[i]))]
                   for i in range(SAMPLE_N)])
    reg = (oracle_ev - ev).mean()
    delta_vs_v33 = v33_reg - reg
    n_changed = int((ev != v33_ev).sum())
    print(f"  {'A-only':>5}  {'always A (no C)':<25}  ${fmt_grid(reg):>+8.2f}  "
          f"${fmt_grid(delta_vs_v33):>+8.2f}  {n_changed:>6,}")

    print("\n" + "=" * 80)
    if best_min is None:
        print("  No improvement over v33 found in sweep. v33's boundary stands.")
    else:
        print(f"  BEST: min_trip_for_C = {RANK_CHARS.get(best_min, str(best_min))}, "
              f"gain = ${fmt_grid(best_delta):+.2f}/1000h whole-grid.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
