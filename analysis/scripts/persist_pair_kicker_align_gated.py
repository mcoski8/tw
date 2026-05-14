"""
Session 78 — persist H7 (pair_kicker_max_in_pair_suit_g) to parquet.

Output: data/feature_table_pair_kicker_align_gated.parquet
"""
from __future__ import annotations

import sys
import time
from collections import Counter
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

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from pair_kicker_align_features_gated import compute_pair_kicker_align_batch  # noqa: E402

OUT = ROOT / "data" / "feature_table_pair_kicker_align_gated.parquet"

t0 = time.time()
canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
hands = canonical.hands
N = len(hands)
print(f"loaded {N:,} canonical hands ({time.time()-t0:.1f}s)")

print("computing pair_kicker_max_in_pair_suit_g ...")
t0 = time.time()
augmented = compute_pair_kicker_align_batch(hands)
print(f"  done ({time.time()-t0:.1f}s)")

vals = augmented["pair_kicker_max_in_pair_suit_g"]
table = pa.table({
    "canonical_id": np.arange(N, dtype=np.uint32),
    "pair_kicker_max_in_pair_suit_g": pa.array(vals, type=pa.int8()),
})

print(f"writing {OUT} (compression=zstd) ...")
pq.write_table(table, OUT, compression="zstd", compression_level=3,
                write_statistics=True)
print(f"wrote {OUT.stat().st_size/1024/1024:.2f} MB")

print("\nre-reading for sanity ...")
back = pq.read_table(OUT).to_pandas()
print(f"  rows: {len(back):,}")
vv = back["pair_kicker_max_in_pair_suit_g"].values
uniq, counts = np.unique(vv, return_counts=True)
summary = ", ".join(f"{int(u)}:{int(c):,}" for u, c in zip(uniq, counts) if c > 0)
print(f"    pair_kicker_max_in_pair_suit_g  {summary}")

print("\nverifying zero-on-non-single-pair-hands ...")
t0 = time.time()
n_nonsingle_pair = 0
n_nonzero_at_nonsingle = 0
for i in range(N):
    h = np.asarray(hands[i], dtype=np.uint8)
    ranks = (h // 4) + 2
    rc = Counter(int(r) for r in ranks)
    cs = list(rc.values())
    n_pairs = sum(1 for c in cs if c == 2)
    n_trips = sum(1 for c in cs if c == 3)
    n_quads = sum(1 for c in cs if c == 4)
    is_single_pair = (n_pairs == 1 and n_trips == 0 and n_quads == 0)
    if not is_single_pair:
        n_nonsingle_pair += 1
        if vv[i] != 0:
            n_nonzero_at_nonsingle += 1
    if (i + 1) % 2_000_000 == 0:
        print(f"  scanned {i+1:,}/{N:,}  elapsed {time.time()-t0:.1f}s", flush=True)
print(f"  non-single-pair hands: {n_nonsingle_pair:,}")
print(f"  non-zero values at non-single-pair: {n_nonzero_at_nonsingle:,}")
if n_nonzero_at_nonsingle != 0:
    print("FAIL: gating broken")
    sys.exit(1)
print("PASS: zero on all non-single-pair hands.")
