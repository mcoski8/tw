"""
Session 18 — persist the 3 high_only augmented features to a parquet file.

Saves data/feature_table_high_only_aug.parquet with columns:
  canonical_id                       uint32   (matches feature_table.parquet)
  default_bot_is_ds_high             int8     0/1, vacuous (0) on non-high_only
  n_mid_choices_yielding_ds_bot      int8     0-15, vacuous on non-high_only
  best_ds_bot_mid_max_rank           int8     0 or 4-14, vacuous on non-high_only

Rationale: compute_high_only_aug_batch is ~17s on the high_only sub-population
(7.71% of 6M). Persisting once amortises across future sessions and
chain-extraction runs (mirrors the pair-aug persistence pattern).
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
from high_only_aug_features import compute_high_only_aug_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_high_only_aug.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("reading feature_table.parquet (category column only)...")
t0 = time.time()
df_cat = pq.read_table(ROOT / "data" / "feature_table.parquet",
                       columns=["category"]).to_pandas()
high_mask = (df_cat["category"].values == "high_only")
print(f"  done ({time.time()-t0:.1f}s); high_only: {high_mask.sum():,}")

print("computing augmented features ...")
t0 = time.time()
augmented = compute_high_only_aug_batch(hands, high_mask)
print(f"  done ({time.time()-t0:.1f}s)")

table = pa.table({
    "canonical_id": np.arange(N, dtype=np.uint32),
    "default_bot_is_ds_high": pa.array(augmented["default_bot_is_ds_high"], type=pa.int8()),
    "n_mid_choices_yielding_ds_bot": pa.array(augmented["n_mid_choices_yielding_ds_bot"], type=pa.int8()),
    "best_ds_bot_mid_max_rank": pa.array(augmented["best_ds_bot_mid_max_rank"], type=pa.int8()),
})

print(f"writing {OUT} (compression=zstd)...")
pq.write_table(table, OUT, compression="zstd", compression_level=3, write_statistics=True)
print(f"wrote {OUT.stat().st_size/1024/1024:.2f} MB")

print()
print("re-reading for sanity...")
back = pq.read_table(OUT).to_pandas()
print(f"  rows: {len(back):,}")
print("  per-feature distribution:")
for c in ("default_bot_is_ds_high", "n_mid_choices_yielding_ds_bot",
          "best_ds_bot_mid_max_rank"):
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{c:,}" for u, c in zip(uniq, counts))
    print(f"    {c:<32} {dist}")
