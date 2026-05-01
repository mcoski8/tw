"""
Investigate high_only: v7 picks differently than v3 on 83% of high_only
hands but loses $0.02 EV/hand on average. Why?

Approach: from the 50K grid, find high_only hands where:
  (a) v7 != v3, and v7 picks the WORSE one (loses to v3 in mean EV).
Look at what v3 picked, what v7 picked, what oracle picked, and the
distinguishing feature pattern.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SCRIPTS), str(SRC), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from encode_rules import strategy_v3, decode_tier_positions, hand_decompose  # noqa: E402
from strategy_v7_regression import strategy_v7_regression  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_50k.npz"


def main() -> int:
    arr = np.load(GRID_PATH, allow_pickle=True)
    hands_bytes = arr["hands_bytes"]
    ev_grid = arr["ev_grid"]
    n = hands_bytes.shape[0]
    print(f"Loaded {n:,} hands from grid.")

    # Filter to high_only (no pairs, no trips, no quads).
    high_only_idx = []
    for i in range(n):
        d = hand_decompose(hands_bytes[i])
        if not d["pairs"] and not d["trips"] and not d["quads"]:
            high_only_idx.append(i)
    high_only_idx = np.array(high_only_idx)
    n_high_only = len(high_only_idx)
    print(f"  high_only: {n_high_only:,} ({100*n_high_only/n:.1f}% of all hands)\n")

    # Compute v3, v7, oracle picks for these hands.
    print("Computing strategy picks ...")
    n_v3_v7_diff = 0
    v7_wins = 0
    v7_loses = 0
    v3_wins_amount = 0.0
    v7_wins_amount = 0.0
    v3_loses_to_oracle_amount = 0.0
    v7_loses_to_oracle_amount = 0.0

    diff_examples = []  # for top losses
    for idx in high_only_idx:
        h = hands_bytes[idx]
        v3_idx = int(strategy_v3(h))
        v7_idx = int(strategy_v7_regression(h))
        mean_ev = ev_grid[idx].mean(axis=0)
        oracle_idx = int(mean_ev.argmax())
        v3_ev = float(mean_ev[v3_idx])
        v7_ev = float(mean_ev[v7_idx])
        oracle_ev = float(mean_ev[oracle_idx])
        v3_loses_to_oracle_amount += (oracle_ev - v3_ev)
        v7_loses_to_oracle_amount += (oracle_ev - v7_ev)
        if v3_idx != v7_idx:
            n_v3_v7_diff += 1
            delta = v7_ev - v3_ev
            if delta > 0:
                v7_wins += 1
                v7_wins_amount += delta
            else:
                v7_loses += 1
                v3_wins_amount += -delta
            if delta < -0.3:  # v7 worse by ≥0.3 EV
                diff_examples.append({
                    "hand_str": " ".join(byte_to_str(int(b)) for b in h),
                    "v3_idx": v3_idx,
                    "v7_idx": v7_idx,
                    "oracle_idx": oracle_idx,
                    "v3_ev": v3_ev,
                    "v7_ev": v7_ev,
                    "oracle_ev": oracle_ev,
                    "delta": delta,
                })

    print(f"  v3 != v7: {n_v3_v7_diff} ({100*n_v3_v7_diff/n_high_only:.1f}%)")
    print(f"  v7 better: {v7_wins} (avg gain {v7_wins_amount/max(1,v7_wins):+.4f})")
    print(f"  v7 worse:  {v7_loses} (avg loss {v3_wins_amount/max(1,v7_loses):+.4f})")
    print(f"  net: {(v7_wins_amount - v3_wins_amount)/n_high_only:+.4f} EV/hand "
          f"= {(v7_wins_amount - v3_wins_amount)/n_high_only*10000:+.0f} $/1000h on high_only subset")
    print(f"\n  v3 vs oracle (always-loses): {v3_loses_to_oracle_amount/n_high_only:+.4f} EV/hand "
          f"= {v3_loses_to_oracle_amount/n_high_only*10000:+.0f} $/1000h headroom")
    print(f"  v7 vs oracle (always-loses): {v7_loses_to_oracle_amount/n_high_only:+.4f} EV/hand "
          f"= {v7_loses_to_oracle_amount/n_high_only*10000:+.0f} $/1000h headroom")

    # Top-10 worst v7 misses on high_only.
    diff_examples.sort(key=lambda r: r["delta"])
    print(f"\nTop-10 hands where v7 LOSES MOST to v3 on high_only:")
    for r in diff_examples[:10]:
        print(f"  {r['hand_str']:<32}  v3=#{r['v3_idx']:<3} ev={r['v3_ev']:+.3f}  "
              f"v7=#{r['v7_idx']:<3} ev={r['v7_ev']:+.3f}  oracle=#{r['oracle_idx']:<3} ev={r['oracle_ev']:+.3f}  "
              f"v7-v3={r['delta']:+.3f}")
    return 0


def byte_to_str(b: int) -> str:
    rank = (b // 4) + 2
    suit = b % 4
    return "23456789TJQKA"[rank-2] + "cdhs"[suit]


if __name__ == "__main__":
    sys.exit(main())
