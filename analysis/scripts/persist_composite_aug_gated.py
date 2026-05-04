"""
Session 31 — persist the 4 composite-gated aug features to a parquet.

Output: data/feature_table_composite_aug_gated.parquet
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
from composite_aug_features_gated import compute_composite_aug_gated_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_composite_aug_gated.parquet"


def main() -> int:
    t0 = time.time()
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    hands = canonical.hands
    N = len(hands)
    print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)", flush=True)

    print("computing composite-gated aug features ...", flush=True)
    t0 = time.time()
    feats = compute_composite_aug_gated_batch(np.asarray(hands), log_every=500_000)
    print(f"  done ({time.time()-t0:.1f}s)", flush=True)

    table = pa.table({
        "canonical_id": pa.array(np.arange(N, dtype=np.uint32)),
        "comp_archetype_g": pa.array(feats["comp_archetype_g"]),
        "comp_lower_trip_rank_g": pa.array(feats["comp_lower_trip_rank_g"]),
        "comp_singleton_rank_g": pa.array(feats["comp_singleton_rank_g"]),
        "comp_higher_pair_rank_g": pa.array(feats["comp_higher_pair_rank_g"]),
    })
    print(f"writing {OUT} ...", flush=True)
    pq.write_table(table, OUT, compression="zstd")
    sz = OUT.stat().st_size
    print(f"  done; {sz/1e6:.2f} MB on disk", flush=True)

    n_nonzero = int((feats["comp_archetype_g"] > 0).sum())
    print(f"\n  hands with non-zero composite gated features: {n_nonzero:,} ({100.0*n_nonzero/N:.2f}%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
