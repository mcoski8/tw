"""
Session 74 — persist 1 high_only_aug_v7 feature (H2 route-tradeoff
comparator) to parquet.

H2 — signed JOINT-vs-DS_NONJOINT route trade-off comparator. Targets
the drop-max-top decision in the high_only zone after H1 (ho_v6
SS+ms route quality) landed at +$5/1000h full (PARTIAL POSITIVE,
below +$10 ship bar per Decision 108).

Output: data/feature_table_high_only_aug_v7_gated.parquet (~3 MB)

Queued for S74 train_v47_dt.py at depth=36 ml=1 (v44's saturating
regime, LOCKED per S73 methodology lesson #1). 109 (v46b) + 1 (v7) =
110 features.
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
from high_only_aug_v7_features_gated import compute_high_only_v7_features_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_high_only_aug_v7_gated.parquet"

V7_COLS = [
    "ho_v7_route_tradeoff_joint_minus_nonjoint_g",
]

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing high_only_aug_v7 features ...")
t0 = time.time()
augmented = compute_high_only_v7_features_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

table_dict = {"canonical_id": np.arange(N, dtype=np.uint32)}
for c in V7_COLS:
    table_dict[c] = pa.array(augmented[c], type=pa.int8())
table = pa.table(table_dict)

print(f"writing {OUT} (compression=zstd) ...")
pq.write_table(table, OUT, compression="zstd", compression_level=3,
                write_statistics=True)
print(f"wrote {OUT.stat().st_size/1024/1024:.2f} MB")

print("\nre-reading for sanity ...")
back = pq.read_table(OUT).to_pandas()
print(f"  rows: {len(back):,}")
for c in V7_COLS:
    vals = back[c].values
    uniq, counts = np.unique(vals, return_counts=True)
    summary = ", ".join(f"{int(u)}:{int(cn):,}" for u, cn in zip(uniq, counts) if cn > 0)
    if len(summary) > 110:
        summary = summary[:110] + "..."
    print(f"    {c:<46} {summary}")
