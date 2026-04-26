"""
Buyout signature classifier — given hand features, return True if the hand
matches the empirical "harmful pair structure" signature for buyout.

From mining (mine_patterns_session12 §9):
  * 4-profile mean buyout (ev_mean < -4): 0.09% of hands.
  * Categorical lift over base-rate:
      quads      lift 117x   (signature concentrated in quads of 2-7)
      trips       lift 8x   (low trips, e.g. 2-5)
      trips_pair  lift 6.6x (trips+low pair pattern)
      everything else: ~0x (essentially zero buyout candidates)
  * Garbage hands (no pair, mostly low) are NOT buyout candidates
    (mean ev_mean = -0.98, only 1.1% qualify).

Signature rule (deterministic from hand features):
  * Quads of rank ≤ 7 → buyout
  * Pure trips of rank ≤ 5 (no pair) → buyout
  * Trips of rank ≤ 7 + pair of rank ≤ 5 → buyout

Validation: precision/recall vs the ground truth (ev_mean < -4) on the full
6M-hand feature table.

Intended consumer: trainer's "BUYOUT" badge. Doesn't require running MC at
runtime; the signature function operates on cards alone.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tw_analysis import read_canonical_hands  # noqa: E402
from tw_analysis.features import hand_features_batch  # noqa: E402


def buyout_signature(hf: dict) -> np.ndarray:
    """
    Vectorized predicate over a HAND_FEATURE_KEYS dict (as returned by
    hand_features_batch). Returns (N,) bool array.

    Tightened to maximise PRECISION at the cost of recall. The trainer
    can still surface a softer "consider buyout" via direct ev_mean lookup;
    this signature is for "almost certainly +EV to buy out" claims.
    """
    n_quads = hf["n_quads"]
    quads_rank = hf["quads_rank"]
    n_trips = hf["n_trips"]
    trips_rank = hf["trips_rank"]
    n_pairs = hf["n_pairs"]
    pair_high_rank = hf["pair_high_rank"]

    # Rule 1: quads of rank ≤ 5 (the strongest signature — 117x lift was
    # mostly carried by these very low quads).
    rule_quads = (n_quads >= 1) & (quads_rank <= 5)

    # Rule 2: trips + pair where BOTH are low (trip ≤ 4, pair ≤ 3).
    # This captures the "low trips + low pair" full-house-shape case.
    rule_trips_pair = (
        (n_trips >= 1) & (n_pairs >= 1)
        & (trips_rank <= 4) & (pair_high_rank <= 3)
    )

    return rule_quads | rule_trips_pair


def buyout_signature_scalar(
    n_quads: int, quads_rank: int,
    n_trips: int, trips_rank: int,
    n_pairs: int, pair_high_rank: int,
) -> bool:
    """Scalar version for trainer/runtime use. See buyout_signature docstring."""
    if n_quads >= 1 and quads_rank <= 5:
        return True
    if n_trips >= 1 and n_pairs >= 1 and trips_rank <= 4 and pair_high_rank <= 3:
        return True
    return False


def main() -> int:
    print(f"Loading feature table…")
    df = pq.read_table(ROOT / "data" / "feature_table.parquet").to_pandas()
    n = len(df)
    print(f"  {n:,} hands")

    # Ground truth: ev_mean < -4.
    truth = (df["ev_mean"] < -4.0).values

    # Signature predictions.
    hf = {
        "n_quads": df["n_quads"].values,
        "quads_rank": df["quads_rank"].values,
        "n_trips": df["n_trips"].values,
        "trips_rank": df["trips_rank"].values,
        "n_pairs": df["n_pairs"].values,
        "pair_high_rank": df["pair_high_rank"].values,
    }
    pred = buyout_signature(hf)

    print(f"\nGround truth (ev_mean < -4):    {int(truth.sum()):,}  ({100*truth.mean():.4f}%)")
    print(f"Signature predicts buyout:      {int(pred.sum()):,}  ({100*pred.mean():.4f}%)")

    # Confusion matrix.
    tp = int((pred & truth).sum())
    fp = int((pred & ~truth).sum())
    fn = int((~pred & truth).sum())
    tn = int((~pred & ~truth).sum())
    print()
    print(f"  TP (sig=Y, truth=Y): {tp:>8,}")
    print(f"  FP (sig=Y, truth=N): {fp:>8,}")
    print(f"  FN (sig=N, truth=Y): {fn:>8,}")
    print(f"  TN (sig=N, truth=N): {tn:>8,}")

    if tp + fp > 0:
        precision = tp / (tp + fp)
    else:
        precision = 0.0
    if tp + fn > 0:
        recall = tp / (tp + fn)
    else:
        recall = 0.0
    f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0.0
    print(f"\n  Precision: {100*precision:.2f}%  (when sig says BUYOUT, truth is BUYOUT)")
    print(f"  Recall:    {100*recall:.2f}%  (of all true BUYOUT hands, signature catches)")
    print(f"  F1:        {100*f1:.2f}%")

    # Stratify by category for diagnostic.
    print("\nBy category (TP/FP/FN/TN within category):")
    for cat in ("high_only", "pair", "two_pair", "three_pair",
                 "trips", "trips_pair", "quads"):
        mask = (df["category"] == cat).values
        ctp = int((pred & truth & mask).sum())
        cfp = int((pred & ~truth & mask).sum())
        cfn = int((~pred & truth & mask).sum())
        cn = int(mask.sum())
        if cn == 0:
            continue
        print(f"  {cat:<14}  n={cn:>9,}  TP={ctp:>5,}  FP={cfp:>5,}  FN={cfn:>5,}")

    # When signature flags but truth disagrees, what's ev_mean?
    fp_mask = pred & ~truth
    fn_mask = ~pred & truth
    if fp_mask.any():
        ev_fp = df.loc[fp_mask, "ev_mean"]
        print(f"\nFP analysis (signature said buyout, truth said no):")
        print(f"  ev_mean stats: min={ev_fp.min():+.2f}  median={ev_fp.median():+.2f}  "
              f"max={ev_fp.max():+.2f}  mean={ev_fp.mean():+.2f}")
    if fn_mask.any():
        ev_fn = df.loc[fn_mask, "ev_mean"]
        print(f"\nFN analysis (signature missed buyout cases):")
        print(f"  ev_mean stats: min={ev_fn.min():+.2f}  median={ev_fn.median():+.2f}  "
              f"max={ev_fn.max():+.2f}  mean={ev_fn.mean():+.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
