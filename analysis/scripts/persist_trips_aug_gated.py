"""
Session 36 — persist the 6 trips-gated aug features to parquet.

Output: data/feature_table_trips_aug_gated.parquet with columns:
  canonical_id                         uint32
  trips_b_ds_avail_g                   int8   (0/1)
  trips_b_ds_n_routings_g              int8   (0..3)
  trips_kickers_max_suit_count_g       int8   (0..4)
  trips_kickers_max_rank_g             int8   (0..14)
  trips_n_broadway_kickers_g           int8   (0..4)
  trips_n_low_kickers_g                int8   (0..4)
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
from trips_aug_features_gated import compute_trips_features_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_trips_aug_gated.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing trips_aug features ...")
t0 = time.time()
augmented = compute_trips_features_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table = pa.table({
    "canonical_id":                    np.arange(N, dtype=np.uint32),
    "trips_b_ds_avail_g":              pa.array(augmented["trips_b_ds_avail_g"],            type=pa.int8()),
    "trips_b_ds_n_routings_g":         pa.array(augmented["trips_b_ds_n_routings_g"],       type=pa.int8()),
    "trips_kickers_max_suit_count_g":  pa.array(augmented["trips_kickers_max_suit_count_g"], type=pa.int8()),
    "trips_kickers_max_rank_g":        pa.array(augmented["trips_kickers_max_rank_g"],      type=pa.int8()),
    "trips_n_broadway_kickers_g":      pa.array(augmented["trips_n_broadway_kickers_g"],    type=pa.int8()),
    "trips_n_low_kickers_g":           pa.array(augmented["trips_n_low_kickers_g"],         type=pa.int8()),
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
    "trips_b_ds_avail_g",
    "trips_b_ds_n_routings_g",
    "trips_kickers_max_suit_count_g",
    "trips_kickers_max_rank_g",
    "trips_n_broadway_kickers_g",
    "trips_n_low_kickers_g",
):
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts))
    print(f"    {c:<36} {dist}")

# Sanity check: trips_b_ds_avail_g rate among trips hands should match diagnostic (68.6%)
print()
print("Sanity check on B-DS availability:")
nonzero_avail = int((back["trips_b_ds_avail_g"] > 0).sum())
nonzero_routings = int((back["trips_b_ds_n_routings_g"] > 0).sum())
# Trip-gated count: any feature nonzero implies trip hand
n_trips = int((back["trips_kickers_max_rank_g"] > 0).sum())
print(f"  trips hands (kickers_max_rank > 0): {n_trips:,}")
print(f"  trips_b_ds_avail_g > 0:             {nonzero_avail:,}")
if n_trips > 0:
    pct = 100.0 * nonzero_avail / n_trips
    print(f"  B-DS available rate within trips:   {pct:.1f}%  (expected ~68.6% from diagnostic)")
