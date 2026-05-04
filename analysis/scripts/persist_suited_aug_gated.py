"""
Session 30 — persist the 6 GATED suited-broadway features to a parquet.

Output: data/feature_table_suited_aug_gated.parquet
Same schema as feature_table_suited_aug.parquet but features are 0 for
all non-high_only hands.
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
from suited_aug_features_gated import compute_suited_aug_gated_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_suited_aug_gated.parquet"


def main() -> int:
    t0 = time.time()
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    hands = canonical.hands
    N = len(hands)
    print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)", flush=True)

    print("computing GATED suited-broadway aug features ...", flush=True)
    t0 = time.time()
    feats = compute_suited_aug_gated_batch(np.asarray(hands), log_every=500_000)
    print(f"  done ({time.time()-t0:.1f}s)", flush=True)

    table = pa.table({
        "canonical_id": pa.array(np.arange(N, dtype=np.uint32)),
        "n_suited_pairs_total_g": pa.array(feats["n_suited_pairs_total_g"]),
        "max_suited_pair_high_rank_g": pa.array(feats["max_suited_pair_high_rank_g"]),
        "max_suited_pair_low_rank_g": pa.array(feats["max_suited_pair_low_rank_g"]),
        "has_suited_broadway_pair_g": pa.array(feats["has_suited_broadway_pair_g"]),
        "has_suited_premium_pair_g": pa.array(feats["has_suited_premium_pair_g"]),
        "n_broadway_in_largest_suit_g": pa.array(feats["n_broadway_in_largest_suit_g"]),
    })
    print(f"writing {OUT} ...", flush=True)
    pq.write_table(table, OUT, compression="zstd")
    sz = OUT.stat().st_size
    print(f"  done; {sz/1e6:.2f} MB on disk", flush=True)

    # Sanity check.
    n_nonzero = int((feats["n_suited_pairs_total_g"] > 0).sum())
    print(f"\n  hands with non-zero gated suited features: {n_nonzero:,} ({100.0*n_nonzero/N:.2f}%)")
    print("  (should match high_only fraction ~20.4%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
