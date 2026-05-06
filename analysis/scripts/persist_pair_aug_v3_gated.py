"""
Session 36 — persist the 4 pair-r4v3 KK/AA-tight gated features to parquet.

Output: data/feature_table_pair_aug_v3_gated.parquet with columns:
  canonical_id                          uint32
  pair_r4v3_kkaa_dom_suit_count_g       int8   (0..4, 0 outside KK/AA)
  pair_r4v3_kkaa_dom_suit_max_rank_g    int8   (0..14)
  pair_r4v3_kkaa_n_high_kickers_g       int8   (0..5)
  pair_r4v3_kkaa_pair_suit_alignment_g  int8   (0..2)
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
from pair_aug_v3_features_gated import compute_pair_r4v3_features_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_pair_aug_v3_gated.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing pair_r4v3 features ...")
t0 = time.time()
augmented = compute_pair_r4v3_features_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table = pa.table({
    "canonical_id":                          np.arange(N, dtype=np.uint32),
    "pair_r4v3_kkaa_dom_suit_count_g":       pa.array(augmented["pair_r4v3_kkaa_dom_suit_count_g"],     type=pa.int8()),
    "pair_r4v3_kkaa_dom_suit_max_rank_g":    pa.array(augmented["pair_r4v3_kkaa_dom_suit_max_rank_g"],  type=pa.int8()),
    "pair_r4v3_kkaa_n_high_kickers_g":       pa.array(augmented["pair_r4v3_kkaa_n_high_kickers_g"],     type=pa.int8()),
    "pair_r4v3_kkaa_pair_suit_alignment_g":  pa.array(augmented["pair_r4v3_kkaa_pair_suit_alignment_g"],type=pa.int8()),
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
    "pair_r4v3_kkaa_dom_suit_count_g",
    "pair_r4v3_kkaa_dom_suit_max_rank_g",
    "pair_r4v3_kkaa_n_high_kickers_g",
    "pair_r4v3_kkaa_pair_suit_alignment_g",
):
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    dist = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts))
    print(f"    {c:<40} {dist}")

# Sanity: dom_suit_count > 0 should equal KK/AA pair count (~430,848 from diagnostic)
nonzero = int((back["pair_r4v3_kkaa_dom_suit_count_g"] > 0).sum())
print(f"\n  KK/AA hands (dom_suit_count > 0): {nonzero:,} (expect ~430,848 from Session 35 diagnostic)")
