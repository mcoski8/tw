"""
Quick diagnostic: where v5_dt and v6_ensemble disagree on the 2000-hand
seed=42 baseline, what's the per-profile EV-loss pattern? Helps decide
whether path A.2 is worth refining or whether to pivot to A.1.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent.parent
PROFILE_IDS = ("mfsuitaware", "omaha", "topdef", "weighted")


def main() -> int:
    v5 = pq.read_table(ROOT / "data" / "v5_dt_records.parquet").to_pandas()
    v6 = pq.read_table(ROOT / "data" / "v6_ensemble_records.parquet").to_pandas()
    assert (v5["hand_str"].values == v6["hand_str"].values).all(), \
        "hand sequences differ — re-run with same seed"
    n = len(v5)
    diff_mask = v5["v3_idx"].values != v6["v3_idx"].values
    n_diff = int(diff_mask.sum())
    print(f"Total hands: {n}")
    print(f"Disagreement: {n_diff} ({100*n_diff/n:.2f}%)")
    print(f"Agreement:    {n - n_diff}")
    print()

    print("=== EV on the 90.25% agreement subset ===")
    agree_mask = ~diff_mask
    for pid in PROFILE_IDS:
        v5_ev = v5.loc[agree_mask, f"v3_ev_{pid}"].mean()
        v6_ev = v6.loc[agree_mask, f"v3_ev_{pid}"].mean()
        # Should be ~equal up to MC noise (different per-hand seed).
        print(f"  {pid:<14}  v5={v5_ev:+.4f}  v6={v6_ev:+.4f}  "
              f"Δ={v6_ev - v5_ev:+.4f}")

    print()
    print("=== EV on the 9.75% disagreement subset ===")
    for pid in PROFILE_IDS:
        v5_ev = v5.loc[diff_mask, f"v3_ev_{pid}"].mean()
        v6_ev = v6.loc[diff_mask, f"v3_ev_{pid}"].mean()
        diff = v6_ev - v5_ev
        per_1000 = diff * 10000 * (n_diff / n)  # weight by share to get $/1000h impact
        print(f"  {pid:<14}  v5={v5_ev:+.4f}  v6={v6_ev:+.4f}  "
              f"Δ={diff:+.4f}  $/1000h impact = {per_1000:+.0f}")

    print()
    print("=== Worst-10 disagreement hands (highest |v6 EV-loss − v5 EV-loss|) ===")
    diff_df = v5.loc[diff_mask, ["hand_str", "v3_idx"]].copy()
    diff_df["v5_idx"] = v5.loc[diff_mask, "v3_idx"].values
    diff_df["v6_idx"] = v6.loc[diff_mask, "v3_idx"].values
    diff_df = diff_df.drop(columns=["v3_idx"])
    for pid in PROFILE_IDS:
        diff_df[f"v5_loss_{pid}"] = np.clip(v5.loc[diff_mask, f"loss_{pid}"].values, 0, None)
        diff_df[f"v6_loss_{pid}"] = np.clip(v6.loc[diff_mask, f"loss_{pid}"].values, 0, None)
    diff_df["mean_v5_loss"] = diff_df[[f"v5_loss_{p}" for p in PROFILE_IDS]].mean(axis=1)
    diff_df["mean_v6_loss"] = diff_df[[f"v6_loss_{p}" for p in PROFILE_IDS]].mean(axis=1)
    diff_df["delta_loss"] = diff_df["mean_v6_loss"] - diff_df["mean_v5_loss"]

    worst_v6 = diff_df.nlargest(10, "delta_loss")[
        ["hand_str", "v5_idx", "v6_idx", "mean_v5_loss", "mean_v6_loss", "delta_loss"]
    ]
    print(worst_v6.to_string(index=False, float_format=lambda x: f"{x:+.3f}"))

    print()
    print("=== Best-10 disagreement hands (v6 wins biggest) ===")
    best_v6 = diff_df.nsmallest(10, "delta_loss")[
        ["hand_str", "v5_idx", "v6_idx", "mean_v5_loss", "mean_v6_loss", "delta_loss"]
    ]
    print(best_v6.to_string(index=False, float_format=lambda x: f"{x:+.3f}"))

    # What fraction of disagreement-subset hands does v6 win vs lose?
    n_v6_wins = int((diff_df["delta_loss"] < 0).sum())
    n_v6_losses = int((diff_df["delta_loss"] > 0).sum())
    print(f"\nOn the {n_diff} disagreement hands:")
    print(f"  v6 better (lower mean loss):  {n_v6_wins} ({100*n_v6_wins/n_diff:.1f}%)")
    print(f"  v6 worse  (higher mean loss): {n_v6_losses} ({100*n_v6_losses/n_diff:.1f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
