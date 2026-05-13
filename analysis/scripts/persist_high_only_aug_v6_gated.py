"""
Session 71 — persist 2 high_only_aug_v6 features to parquet.

H1 — SS+ms route quality (direct SS-axis counterpart to ho_v3's
DS-axis pair). Targets the `SS_mu → SS_ms` STRUCTURE-bucket mismatch
family identified in drill_v44_high_only_S71.py.

Output: data/feature_table_high_only_aug_v6_gated.parquet (~6 MB)

Queued for S72 train_v46_dt.py at depth=32 ml=3 (project default per
CURRENT_PHASE.md). 107 (v44) + 2 (v6) = 109 features.
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
from high_only_aug_v6_features_gated import compute_high_only_v6_features_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_high_only_aug_v6_gated.parquet"

V6_COLS = [
    "ho_v6_topMax_SS_ms_n_configs_g",
    "ho_v6_topMax_SS_ms_max_mid_high_g",
]

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing high_only_aug_v6 features ...")
t0 = time.time()
augmented = compute_high_only_v6_features_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table_dict = {"canonical_id": np.arange(N, dtype=np.uint32)}
for c in V6_COLS:
    table_dict[c] = pa.array(augmented[c], type=pa.int8())
table = pa.table(table_dict)

print(f"writing {OUT} (compression=zstd) ...")
pq.write_table(table, OUT, compression="zstd", compression_level=3,
                write_statistics=True)
print(f"wrote {OUT.stat().st_size/1024/1024:.2f} MB")

print("\nre-reading for sanity ...")
back = pq.read_table(OUT).to_pandas()
print(f"  rows: {len(back):,}")
for c in V6_COLS:
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    summary = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts) if c > 0)
    if len(summary) > 110:
        summary = summary[:110] + "..."
    print(f"    {c:<42} {summary}")
