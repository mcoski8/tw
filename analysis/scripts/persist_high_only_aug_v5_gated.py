"""
Session 59 — persist 4 high_only_aug_v5 features to parquet.

Output: data/feature_table_high_only_aug_v5_gated.parquet
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
from high_only_aug_v5_features_gated import compute_high_only_v5_features_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_high_only_aug_v5_gated.parquet"

V5_COLS = [
    "ho_v5_topNonMax_DS_ms_max_mid_high_g",
    "ho_v5_topNonMax_DS_ms_best_combined_q_g",
    "ho_v5_topNonMax_DS_max_in_bot_pair_n_g",
    "ho_v5_topMax_4f_ms_n_configs_g",
]

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing high_only_aug_v5 features ...")
t0 = time.time()
augmented = compute_high_only_v5_features_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table_dict = {"canonical_id": np.arange(N, dtype=np.uint32)}
for c in V5_COLS:
    table_dict[c] = pa.array(augmented[c], type=pa.int8())
table = pa.table(table_dict)

print(f"writing {OUT} (compression=zstd) ...")
pq.write_table(table, OUT, compression="zstd", compression_level=3,
                write_statistics=True)
print(f"wrote {OUT.stat().st_size/1024/1024:.2f} MB")

print("\nre-reading for sanity ...")
back = pq.read_table(OUT).to_pandas()
print(f"  rows: {len(back):,}")
for c in V5_COLS:
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    summary = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts) if c > 0)
    if len(summary) > 110:
        summary = summary[:110] + "..."
    print(f"    {c:<42} {summary}")
