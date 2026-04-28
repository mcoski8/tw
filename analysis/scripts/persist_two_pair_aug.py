"""
Session 19 — persist the 3 two_pair augmented features to a parquet file.

Saves data/feature_table_two_pair_aug.parquet with columns:
  canonical_id                              uint32   (matches feature_table.parquet)
  default_bot_is_ds_tp                      int8     0/1, vacuous (0) on non-two_pair
  n_routings_yielding_ds_bot_tp             int8     0-6, vacuous on non-two_pair
  swap_high_pair_to_bot_ds_compatible       int8     0/1, vacuous on non-two_pair

Rationale: compute_two_pair_aug_batch is ~17s on the two_pair sub-population
(11.24% of 6M is the 3-of-4 slice, plus the rest of the two_pair full
distribution). Persisting once amortises across future sessions and
chain-extraction runs (mirrors the pair-aug + high_only-aug persistence pattern).
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
from two_pair_aug_features import compute_two_pair_aug_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_two_pair_aug.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("reading feature_table.parquet (category column only)...")
t0 = time.time()
df_cat = pq.read_table(ROOT / "data" / "feature_table.parquet",
                       columns=["category"]).to_pandas()
two_pair_mask = (df_cat["category"].values == "two_pair")
print(f"  done ({time.time()-t0:.1f}s); two_pair: {two_pair_mask.sum():,}")

print("computing augmented features ...")
t0 = time.time()
augmented = compute_two_pair_aug_batch(hands, two_pair_mask)
print(f"  done ({time.time()-t0:.1f}s)")

table = pa.table({
    "canonical_id": np.arange(N, dtype=np.uint32),
    "default_bot_is_ds_tp": pa.array(augmented["default_bot_is_ds_tp"], type=pa.int8()),
    "n_routings_yielding_ds_bot_tp": pa.array(augmented["n_routings_yielding_ds_bot_tp"], type=pa.int8()),
    "swap_high_pair_to_bot_ds_compatible": pa.array(augmented["swap_high_pair_to_bot_ds_compatible"], type=pa.int8()),
})

print(f"writing {OUT} (compression=zstd)...")
pq.write_table(table, OUT, compression="zstd", compression_level=3, write_statistics=True)
print(f"wrote {OUT.stat().st_size/1024/1024:.2f} MB")

print()
print("re-reading for sanity...")
back = pq.read_table(OUT).to_pandas()
print(f"  rows: {len(back):,}")
print("  per-feature distribution:")
for c in ("default_bot_is_ds_tp", "n_routings_yielding_ds_bot_tp",
          "swap_high_pair_to_bot_ds_compatible"):
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{c:,}" for u, c in zip(uniq, counts))
    print(f"    {c:<40} {dist}")
