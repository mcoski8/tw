"""
Session 32 — persist the 6 pair-gated aug features to parquet.

Output: data/feature_table_pair_aug_gated.parquet with columns:
  canonical_id                          uint32
  pair_kickers_in_pair_suit_max_g       int8   (0..5; 0 if non-pair)
  pair_kickers_in_pair_suit_min_g       int8   (0..5; 0 if non-pair)
  pair_default_top_rank_g               int8   (0..14; 0 if non-pair)
  pair_alt_top_rank_g                   int8   (0..14; 0 if non-pair)
  pair_alt_mid_suited_g                 int8   (0/1; 0 if non-pair)
  pair_alt_mid_n_broadway_g             int8   (0..2; 0 if non-pair)
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
from pair_aug_features_gated import compute_pair_aug_gated_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_pair_aug_gated.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing pair_aug_gated features ...")
t0 = time.time()
augmented = compute_pair_aug_gated_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table = pa.table({
    "canonical_id": np.arange(N, dtype=np.uint32),
    "pair_kickers_in_pair_suit_max_g": pa.array(augmented["pair_kickers_in_pair_suit_max_g"], type=pa.int8()),
    "pair_kickers_in_pair_suit_min_g": pa.array(augmented["pair_kickers_in_pair_suit_min_g"], type=pa.int8()),
    "pair_default_top_rank_g":         pa.array(augmented["pair_default_top_rank_g"],         type=pa.int8()),
    "pair_alt_top_rank_g":             pa.array(augmented["pair_alt_top_rank_g"],             type=pa.int8()),
    "pair_alt_mid_suited_g":           pa.array(augmented["pair_alt_mid_suited_g"],           type=pa.int8()),
    "pair_alt_mid_n_broadway_g":       pa.array(augmented["pair_alt_mid_n_broadway_g"],       type=pa.int8()),
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
    "pair_kickers_in_pair_suit_max_g",
    "pair_kickers_in_pair_suit_min_g",
    "pair_default_top_rank_g",
    "pair_alt_top_rank_g",
    "pair_alt_mid_suited_g",
    "pair_alt_mid_n_broadway_g",
):
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts))
    print(f"    {c:<36} {dist}")
