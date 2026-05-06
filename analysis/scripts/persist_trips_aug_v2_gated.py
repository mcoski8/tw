"""Session 36 — persist 4 trips_v2 round-2 features to parquet."""
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
from trips_aug_v2_features_gated import compute_trips_v2_features_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_trips_aug_v2_gated.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing trips_v2 features ...")
t0 = time.time()
augmented = compute_trips_v2_features_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table = pa.table({
    "canonical_id":                       np.arange(N, dtype=np.uint32),
    "trips_v2_c_top_advantage_g":         pa.array(augmented["trips_v2_c_top_advantage_g"],         type=pa.int8()),
    "trips_v2_b_ds_kicker_max_rank_g":    pa.array(augmented["trips_v2_b_ds_kicker_max_rank_g"],    type=pa.int8()),
    "trips_v2_b_ds_kicker_2nd_rank_g":    pa.array(augmented["trips_v2_b_ds_kicker_2nd_rank_g"],    type=pa.int8()),
    "trips_v2_n_kickers_in_trip_suits_g": pa.array(augmented["trips_v2_n_kickers_in_trip_suits_g"], type=pa.int8()),
})

print(f"writing {OUT} (compression=zstd) ...")
pq.write_table(table, OUT, compression="zstd", compression_level=3, write_statistics=True)
print(f"wrote {OUT.stat().st_size/1024/1024:.2f} MB")

print()
print("re-reading for sanity ...")
back = pq.read_table(OUT).to_pandas()
print(f"  rows: {len(back):,}")
print("  per-feature distribution:")
for c in (
    "trips_v2_c_top_advantage_g",
    "trips_v2_b_ds_kicker_max_rank_g",
    "trips_v2_b_ds_kicker_2nd_rank_g",
    "trips_v2_n_kickers_in_trip_suits_g",
):
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts))
    print(f"    {c:<40} {dist}")
