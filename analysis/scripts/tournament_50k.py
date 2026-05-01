"""
Strategy tournament: run every named strategy through the 50K-hand oracle
grid (data/oracle_grid_50k.npz) and report per-profile mean EV without
any new MC compute. Each profile gets its own column — no grand-mean
hiding the omaha asymmetry.

Profiles in order:
  mfsuitaware  — "Middle-First Suit-Aware", the strongest realistic
                 heuristic per project Decision 005. Closest proxy to
                 a competent human opponent.
  omaha        — Omaha-First, plays the bottom strongly.
  topdef       — Top-Defensive, plays the top tier strongly.
  weighted     — Random-Weighted (RandomWeighted opponent model).

Each strategy's grand mean is also reported for context, but the per-profile
breakdown is the headline (per user feedback Session 22).

Output also includes:
  - vs-best-opponent column (highest EV achieved, identifies weak opponent)
  - vs-worst-opponent column (lowest EV, identifies hardest opponent)
  - $/1000h delta vs v3 per profile (since v3 is the production reference)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SCRIPTS), str(SRC), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from encode_rules import strategy_v3, strategy_v3_no_top_bias  # noqa: E402
from strategy_v5_dt import strategy_v5_dt  # noqa: E402
from strategy_v6_ensemble import strategy_v6_ensemble  # noqa: E402
from strategy_v7_regression import strategy_v7_regression  # noqa: E402
from strategy_v7_patched import strategy_v7_patched  # noqa: E402
from strategy_v8_hybrid import strategy_v8_high_only_only, strategy_v8_hybrid  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_50k.npz"

STRATEGIES = [
    ("v3 (production hand-coded)",  strategy_v3),
    ("v5_dt (shape DT)",              strategy_v5_dt),
    ("v6_ensemble (4-DT vote)",       strategy_v6_ensemble),
    ("v7_regression (EV DT)",         strategy_v7_regression),
    ("v7_patched (v7 + AAKK rule)",   strategy_v7_patched),
    ("v8_high_only_only (v7 + v3 high_only)",  strategy_v8_high_only_only),
    ("v8_hybrid (v7 + v3 high_only + pair)",   strategy_v8_hybrid),
]


def main() -> int:
    print(f"Loading {GRID_PATH} ...")
    arr = np.load(GRID_PATH, allow_pickle=True)
    hands_bytes = arr["hands_bytes"]
    ev_grid = arr["ev_grid"]                # (N, 4, 105)
    profile_ids = list(arr["profile_ids"])
    n = hands_bytes.shape[0]
    n_profiles = len(profile_ids)
    print(f"  {n:,} hands × {n_profiles} profiles × 105 settings\n")

    # Compute each strategy's pick per hand.
    print("Computing strategy picks ...")
    strategy_picks: dict[str, np.ndarray] = {}
    for label, fn in STRATEGIES:
        t0 = time.time()
        picks = np.empty(n, dtype=np.int32)
        for i in range(n):
            picks[i] = int(fn(hands_bytes[i]))
        elapsed = time.time() - t0
        print(f"  {label:<38}  {elapsed:>5.1f}s  ({n/elapsed:,.0f} hands/s)")
        strategy_picks[label] = picks

    # Add the oracle as a benchmark.
    br_per_profile = ev_grid.argmax(axis=2)              # (N, P)
    argmax_mean = ev_grid.mean(axis=1).argmax(axis=1)    # (N,)
    strategy_picks["oracle_argmax_mean (hedge)"] = argmax_mean

    # Compute per-profile mean EV for each strategy.
    rows = []
    for label, picks in strategy_picks.items():
        if picks.ndim == 1:
            ev_per_profile = np.empty((n, n_profiles), dtype=np.float64)
            for p in range(n_profiles):
                ev_per_profile[:, p] = ev_grid[np.arange(n), p, picks]
        else:
            # br_per_profile case (per-profile picks)
            ev_per_profile = np.empty((n, n_profiles), dtype=np.float64)
            for p in range(n_profiles):
                ev_per_profile[:, p] = ev_grid[np.arange(n), p, picks[:, p]]
        means = ev_per_profile.mean(axis=0)
        rows.append({
            "label": label,
            "per_profile": means,
            "grand_mean": float(means.mean()),
            "best_profile_ev": float(means.max()),
            "worst_profile_ev": float(means.min()),
            "best_profile": profile_ids[int(means.argmax())],
            "worst_profile": profile_ids[int(means.argmin())],
        })

    # Add oracle-BR per profile (knows opponent — upper bound).
    br_per_profile_evs = np.empty((n, n_profiles), dtype=np.float64)
    for p in range(n_profiles):
        br_per_profile_evs[:, p] = ev_grid[np.arange(n), p, br_per_profile[:, p]]
    br_means = br_per_profile_evs.mean(axis=0)
    rows.append({
        "label": "oracle_BR_per_profile (cheating)",
        "per_profile": br_means,
        "grand_mean": float(br_means.mean()),
        "best_profile_ev": float(br_means.max()),
        "worst_profile_ev": float(br_means.min()),
        "best_profile": profile_ids[int(br_means.argmax())],
        "worst_profile": profile_ids[int(br_means.argmin())],
    })

    # Reference: v3's per-profile means for delta computation.
    v3_row = next(r for r in rows if r["label"].startswith("v3 (production"))
    v3_means = v3_row["per_profile"]

    print("\n" + "=" * 130)
    print(f"TOURNAMENT — {n:,} hands per (strategy, profile) cell")
    print("=" * 130 + "\n")
    header = f"{'strategy':<38}"
    for pid in profile_ids:
        header += f"{pid:>14}"
    header += f"{'grand_mean':>12}{'best_opp':>14}{'worst_opp':>16}"
    print(header)
    print("-" * len(header))
    for r in rows:
        row_str = f"{r['label']:<38}"
        for ev in r["per_profile"]:
            row_str += f"{ev:>+14.4f}"
        row_str += f"{r['grand_mean']:>+12.4f}"
        row_str += f"{r['best_profile_ev']:>+8.4f} {r['best_profile']:<7}"
        row_str += f"{r['worst_profile_ev']:>+8.4f} {r['worst_profile']:<7}"
        print(row_str)

    print("\n" + "=" * 130)
    print(f"$/1000h DELTA vs v3 — per profile  ($10/EV-pt)")
    print("=" * 130 + "\n")
    header = f"{'strategy':<38}"
    for pid in profile_ids:
        header += f"{pid:>14}"
    header += f"{'grand':>12}"
    print(header)
    print("-" * len(header))
    for r in rows:
        if r["label"].startswith("v3 (production"):
            continue
        row_str = f"{r['label']:<38}"
        for j, ev in enumerate(r["per_profile"]):
            delta = (ev - v3_means[j]) * 10000
            row_str += f"{delta:>+14.0f}"
        delta_grand = (r["grand_mean"] - v3_row["grand_mean"]) * 10000
        row_str += f"{delta_grand:>+12.0f}"
        print(row_str)

    return 0


if __name__ == "__main__":
    sys.exit(main())
