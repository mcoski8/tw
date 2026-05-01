"""
Side-by-side comparison of v3, v5_dt, and v6_ensemble on the same 2000-hand
seed=42 baseline. Reads the three records parquets and emits the table
expected by CURRENT_PHASE.md / DECISIONS_LOG entry 040.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent.parent
PROFILE_IDS = ("mfsuitaware", "omaha", "topdef", "weighted")


def load(name: str):
    df = pq.read_table(ROOT / "data" / f"{name}_records.parquet").to_pandas()
    return df


def per_profile_summary(df, label: str) -> dict:
    """Compute per-profile mean EV, mean EV-loss, and grand means."""
    out = {"label": label}
    for pid in PROFILE_IDS:
        ev = df[f"v3_ev_{pid}"].values  # column is named v3_* but values are strategy's
        loss = np.clip(df[f"loss_{pid}"].values, 0, None)
        br_ev = df[f"br_ev_{pid}"].values
        out[f"ev_{pid}"] = float(ev.mean())
        out[f"loss_{pid}"] = float(loss.mean())
        out[f"br_ev_{pid}"] = float(br_ev.mean())
    out["mean_ev"] = float(np.mean([out[f"ev_{p}"] for p in PROFILE_IDS]))
    out["mean_loss"] = float(np.mean([out[f"loss_{p}"] for p in PROFILE_IDS]))
    out["mean_br_ev"] = float(np.mean([out[f"br_ev_{p}"] for p in PROFILE_IDS]))
    return out


def main() -> int:
    have = {}
    for name in ("v3_evloss", "v5_dt", "v6_ensemble"):
        path = ROOT / "data" / f"{name}_records.parquet"
        if path.exists():
            have[name] = load(name)
        else:
            print(f"  (missing) {path}")
    if not have:
        print("No records found.")
        return 1

    summaries = []
    for name, df in have.items():
        # rename "v3_evloss" → "v3" for the report label
        label = "v3" if name == "v3_evloss" else name
        summaries.append((label, per_profile_summary(df, label), df))

    # ---- Per-profile mean EV (absolute) ----
    print("\n=== Mean absolute EV per profile (positive = winning) ===")
    print(f"{'strategy':<14}" + "".join(f"{p:>13}" for p in PROFILE_IDS) + f"{'mean':>12}")
    for label, s, _ in summaries:
        row = f"{label:<14}"
        for p in PROFILE_IDS:
            row += f"{s[f'ev_{p}']:>+13.4f}"
        row += f"{s['mean_ev']:>+12.4f}"
        print(row)
    # BR row from v3 (BR EV is profile-truth, same across all parquets to MC noise).
    s0 = summaries[0][1]
    row = f"{'BR-omniscient':<14}"
    for p in PROFILE_IDS:
        row += f"{s0[f'br_ev_{p}']:>+13.4f}"
    row += f"{s0['mean_br_ev']:>+12.4f}"
    print(row)

    # ---- Per-profile EV-loss (vs BR per profile) ----
    print("\n=== Mean EV-loss per profile (vs profile-BR) ===")
    print(f"{'strategy':<14}" + "".join(f"{p:>13}" for p in PROFILE_IDS) + f"{'mean':>12}")
    for label, s, _ in summaries:
        row = f"{label:<14}"
        for p in PROFILE_IDS:
            row += f"{s[f'loss_{p}']:>+13.4f}"
        row += f"{s['mean_loss']:>+12.4f}"
        print(row)

    # ---- $/1000h deltas at $10/EV-pt ----
    if len(summaries) >= 2:
        v3 = next((s for l, s, _ in summaries if l == "v3"), None)
        v5 = next((s for l, s, _ in summaries if l == "v5_dt"), None)
        print("\n=== $/1000h deltas at $10/EV-pt ===")
        print(f"{'strategy':<14}" + "".join(f"{p:>14}" for p in PROFILE_IDS) + f"{'mean':>14}")
        for label, s, _ in summaries:
            if label == "v3" or v3 is None:
                continue
            row = f"{label:<14} (vs v3)"
            for p in PROFILE_IDS:
                row += f"{(s[f'ev_{p}'] - v3[f'ev_{p}']) * 10000:>+14.0f}"
            row += f"{(s['mean_ev'] - v3['mean_ev']) * 10000:>+14.0f}"
            print(row)
            if v5 is not None and label != "v5_dt":
                row = f"{label:<14} (vs v5)"
                for p in PROFILE_IDS:
                    row += f"{(s[f'ev_{p}'] - v5[f'ev_{p}']) * 10000:>+14.0f}"
                row += f"{(s['mean_ev'] - v5['mean_ev']) * 10000:>+14.0f}"
                print(row)

    # ---- Cross-strategy choice agreement on the 2000 hands ----
    print("\n=== Choice agreement across the 2000 hands ===")
    pairs = [(a, b) for i, a in enumerate(summaries) for b in summaries[i+1:]]
    for (la, _, da), (lb, _, db) in pairs:
        agree = float((da["v3_idx"].values == db["v3_idx"].values).mean()) * 100
        print(f"  {la:<14} vs {lb:<14}  literal-agreement: {agree:.2f}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
