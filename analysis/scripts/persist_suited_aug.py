"""
Session 29 — persist the 6 suited-broadway aug features for ALL 6M
canonical hands (not gated by category). Mirrors persist_high_only_aug.py
but with no slice mask.

Output: data/feature_table_suited_aug.parquet with columns:
  canonical_id                      uint32
  n_suited_pairs_total              int8  (0..21)
  max_suited_pair_high_rank         int8  (0,2..14)
  max_suited_pair_low_rank          int8  (0,2..14)
  has_suited_broadway_pair          int8  (0/1)
  has_suited_premium_pair           int8  (0/1)
  n_broadway_in_largest_suit        int8  (0..7)
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis import read_canonical_hands  # noqa: E402
from suited_aug_features import compute_suited_aug_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_suited_aug.parquet"


def main() -> int:
    t0 = time.time()
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    hands = canonical.hands
    N = len(hands)
    print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)", flush=True)

    print("computing suited-broadway aug features (all hands) ...", flush=True)
    t0 = time.time()
    feats = compute_suited_aug_batch(np.asarray(hands), log_every=500_000)
    print(f"  done ({time.time()-t0:.1f}s)", flush=True)

    table = pa.table({
        "canonical_id": pa.array(np.arange(N, dtype=np.uint32)),
        "n_suited_pairs_total": pa.array(feats["n_suited_pairs_total"]),
        "max_suited_pair_high_rank": pa.array(feats["max_suited_pair_high_rank"]),
        "max_suited_pair_low_rank": pa.array(feats["max_suited_pair_low_rank"]),
        "has_suited_broadway_pair": pa.array(feats["has_suited_broadway_pair"]),
        "has_suited_premium_pair": pa.array(feats["has_suited_premium_pair"]),
        "n_broadway_in_largest_suit": pa.array(feats["n_broadway_in_largest_suit"]),
    })
    print(f"writing {OUT} ...", flush=True)
    pq.write_table(table, OUT, compression="zstd")
    sz = OUT.stat().st_size
    print(f"  done; {sz/1e6:.2f} MB on disk", flush=True)

    # Quick sanity check: print histograms.
    print("\nFeature distributions:")
    for col in [
        "n_suited_pairs_total", "max_suited_pair_high_rank", "max_suited_pair_low_rank",
        "has_suited_broadway_pair", "has_suited_premium_pair", "n_broadway_in_largest_suit",
    ]:
        arr = feats[col]
        unique, counts = np.unique(arr, return_counts=True)
        print(f"  {col}:")
        for u, c in zip(unique, counts):
            print(f"    {int(u):>3d}: {int(c):>10,}  ({100.0*c/N:5.2f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
