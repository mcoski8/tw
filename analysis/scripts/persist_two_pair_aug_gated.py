"""
Session 33 — persist the 6 two_pair-gated aug features to parquet.

Output: data/feature_table_two_pair_aug_gated.parquet with columns:
  canonical_id                          uint32
  t2p_layout_a_bot_is_ds_g               int8   (0/1; 0 if non-two_pair)
  t2p_n_layout_b_routings_ds_g           int8   (0..3; 0 if non-two_pair)
  t2p_top_singleton_rank_g               int8   (0..14; 0 if non-two_pair)
  t2p_low_singleton_rank_g              int8   (0..14; 0 if non-two_pair)
  t2p_singletons_max_suit_count_g        int8   (0..3; 0 if non-two_pair)
  t2p_high_pair_rank_g                   int8   (0..14; 0 if non-two_pair)
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
from two_pair_aug_features_gated import compute_two_pair_aug_gated_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_two_pair_aug_gated.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing two_pair_aug_gated features ...")
t0 = time.time()
augmented = compute_two_pair_aug_gated_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table = pa.table({
    "canonical_id": np.arange(N, dtype=np.uint32),
    "t2p_layout_a_bot_is_ds_g":          pa.array(augmented["t2p_layout_a_bot_is_ds_g"],          type=pa.int8()),
    "t2p_n_layout_b_routings_ds_g":      pa.array(augmented["t2p_n_layout_b_routings_ds_g"],      type=pa.int8()),
    "t2p_top_singleton_rank_g":          pa.array(augmented["t2p_top_singleton_rank_g"],          type=pa.int8()),
    "t2p_low_singleton_rank_g":          pa.array(augmented["t2p_low_singleton_rank_g"],          type=pa.int8()),
    "t2p_singletons_max_suit_count_g":   pa.array(augmented["t2p_singletons_max_suit_count_g"],   type=pa.int8()),
    "t2p_high_pair_rank_g":              pa.array(augmented["t2p_high_pair_rank_g"],              type=pa.int8()),
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
    "t2p_layout_a_bot_is_ds_g",
    "t2p_n_layout_b_routings_ds_g",
    "t2p_top_singleton_rank_g",
    "t2p_low_singleton_rank_g",
    "t2p_singletons_max_suit_count_g",
    "t2p_high_pair_rank_g",
):
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts))
    print(f"    {c:<36} {dist}")
