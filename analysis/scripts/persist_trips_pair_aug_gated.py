"""
Session 31 — persist the 6 trips_pair-gated aug features to a parquet.

Output: data/feature_table_trips_pair_aug_gated.parquet
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
from trips_pair_aug_features_gated import compute_trips_pair_aug_gated_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_trips_pair_aug_gated.parquet"


def main() -> int:
    t0 = time.time()
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    hands = canonical.hands
    N = len(hands)
    print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)", flush=True)

    print("computing trips_pair-gated aug features ...", flush=True)
    t0 = time.time()
    feats = compute_trips_pair_aug_gated_batch(np.asarray(hands), log_every=500_000)
    print(f"  done ({time.time()-t0:.1f}s)", flush=True)

    table = pa.table({
        "canonical_id": pa.array(np.arange(N, dtype=np.uint32)),
        "tp_trip_rank_g": pa.array(feats["tp_trip_rank_g"]),
        "tp_pair_rank_g": pa.array(feats["tp_pair_rank_g"]),
        "tp_high_singleton_rank_g": pa.array(feats["tp_high_singleton_rank_g"]),
        "tp_low_singleton_rank_g": pa.array(feats["tp_low_singleton_rank_g"]),
        "tp_singletons_suited_g": pa.array(feats["tp_singletons_suited_g"]),
        "tp_pair_routing_is_ds_g": pa.array(feats["tp_pair_routing_is_ds_g"]),
    })
    print(f"writing {OUT} ...", flush=True)
    pq.write_table(table, OUT, compression="zstd")
    sz = OUT.stat().st_size
    print(f"  done; {sz/1e6:.2f} MB on disk", flush=True)

    n_nonzero = int((feats["tp_trip_rank_g"] > 0).sum())
    print(f"\n  hands with non-zero trips_pair gated features: {n_nonzero:,} ({100.0*n_nonzero/N:.2f}%)")
    print("  (should match trips_pair fraction ~8.7%)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
