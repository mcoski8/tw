"""
Session 34 — persist the 4 high_only-gated aug features to parquet.

Output: data/feature_table_high_only_aug_gated.parquet with columns:
  canonical_id                          uint32
  ho_n_broadway_in_2nd_suit_g            int8   (0..3; 0 if non-high_only)
  ho_n_broadway_in_3rd_suit_g            int8   (0..3; 0 if non-high_only)
  ho_connectivity_high_g                 int8   (0..5; 0 if non-high_only)
  ho_n_broadway_pairs_adj_g              int8   (0..4; 0 if non-high_only)
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
from high_only_aug_features_gated import compute_high_only_aug_gated_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_high_only_aug_gated.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing high_only_aug_gated features ...")
t0 = time.time()
augmented = compute_high_only_aug_gated_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table = pa.table({
    "canonical_id":                   np.arange(N, dtype=np.uint32),
    "ho_n_broadway_in_2nd_suit_g":    pa.array(augmented["ho_n_broadway_in_2nd_suit_g"], type=pa.int8()),
    "ho_n_broadway_in_3rd_suit_g":    pa.array(augmented["ho_n_broadway_in_3rd_suit_g"], type=pa.int8()),
    "ho_connectivity_high_g":         pa.array(augmented["ho_connectivity_high_g"],      type=pa.int8()),
    "ho_n_broadway_pairs_adj_g":      pa.array(augmented["ho_n_broadway_pairs_adj_g"],   type=pa.int8()),
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
    "ho_n_broadway_in_2nd_suit_g",
    "ho_n_broadway_in_3rd_suit_g",
    "ho_connectivity_high_g",
    "ho_n_broadway_pairs_adj_g",
):
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts))
    print(f"    {c:<36} {dist}")
