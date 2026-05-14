"""
Session 81 — build the two_pair + trips_pair subset for the v49_a2 targeted
N=1000 oracle pass (Decision 115, S81 plan).

Inputs:
  data/canonical_hands.bin                 — 6,009,159 canonical 7-card hands.

Outputs (all under data/session81/):
  canonical_hands_s81_subset.bin           — canonical_hands.bin format,
                                             1,510,080 two_pair + trips_pair
                                             hands in original lex order.
                                             Feed this to tw-engine oracle-grid.
  v49_a2_subset_to_canonical.npy           — uint32 array len 1,510,080.
                                             Maps subset_index → original
                                             full-grid canonical_id. Critical
                                             for re-joining the new N=1000
                                             oracle output to the full grid
                                             during training and grading.
  v49_a2_holdout_ids.npy                   — uint32 array len ≈151,008.
                                             ORIGINAL canonical_ids reserved
                                             for held-out validation. Sampled
                                             as every 10th subset index.
  v49_a2_holdout_subset_indices.npy        — uint32 array len ≈151,008.
                                             SUBSET indices of the held-out
                                             hands. For direct lookup into
                                             the new oracle grid file.
  v49_a2_subset_categories.npy             — int8 array len 1,510,080.
                                             Per-row category code (2 or 4).
                                             Lets grader split lift by
                                             two_pair vs trips_pair on the
                                             held-out set without recomputing.
  build_summary.json                       — provenance: counts, sha-of-input,
                                             rng seed for held-out selection.

This script is pure-Python + numpy; no engine call required. Wall time on a
modern Mac: ~30 seconds (the categorize_hands one-hot pass over 6M rows is
the long pole).
"""
from __future__ import annotations

import hashlib
import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from tw_analysis.canonical import (  # noqa: E402
    CANON_HEADER_SIZE,
    CANON_MAGIC,
    CANON_VERSION,
    read_canonical_hands,
)
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402

CANONICAL_PATH = ROOT / "data" / "canonical_hands.bin"
OUT_DIR = ROOT / "data" / "session81"

# Category codes (from tw_analysis.grade_strategy.categorize_hands).
TWO_PAIR = 2
TRIPS_PAIR = 4

# Per CURRENT_PHASE.md the expected counts on the 6,009,159-hand canonical
# grid are 1,338,480 two_pair + 171,600 trips_pair = 1,510,080 total. If the
# observed counts disagree, halt loudly — the entire S81 budget is sized to
# this number.
EXPECTED_TWO_PAIR = 1_338_480
EXPECTED_TRIPS_PAIR = 171_600
EXPECTED_TOTAL = EXPECTED_TWO_PAIR + EXPECTED_TRIPS_PAIR  # 1,510,080

# Held-out stride: take every 10th subset row, giving ≈10% (151,008) for the
# out-of-sample N=1000 grading lens.
HOLDOUT_STRIDE = 10
HOLDOUT_OFFSET = 0  # first held-out subset_index = 0; deterministic & seedless


def sha256_file(path: Path, chunk: int = 1 << 20) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            block = f.read(chunk)
            if not block:
                break
            h.update(block)
    return h.hexdigest()


def write_canonical_subset(path: Path, subset_hands: np.ndarray) -> None:
    """Write a canonical_hands.bin in the same binary format as the engine.

    Format mirrors tw_analysis.canonical: 32-byte header (TWCH + version u32
    + num_hands u64 + 16-byte reserved) then num_hands × 7 bytes (sorted,
    packed cards).

    subset_hands must already be in the same lex order as canonical_hands.bin
    (we filter without re-sorting, so iteration order is preserved).
    """
    if subset_hands.dtype != np.uint8 or subset_hands.ndim != 2 or subset_hands.shape[1] != 7:
        raise ValueError(
            f"subset_hands must be (N, 7) uint8, got shape={subset_hands.shape} "
            f"dtype={subset_hands.dtype}"
        )
    n = subset_hands.shape[0]
    header = bytearray(CANON_HEADER_SIZE)
    header[0:4] = CANON_MAGIC
    header[4:8] = CANON_VERSION.to_bytes(4, "little")
    header[8:16] = n.to_bytes(8, "little")
    # bytes [16..32] stay zero (reserved).

    with open(path, "wb") as f:
        f.write(bytes(header))
        f.write(subset_hands.tobytes(order="C"))


def main() -> int:
    print("=" * 100, flush=True)
    print("Session 81 — build_s81_subset (v49_a2 plan, Decision 115)", flush=True)
    print("=" * 100, flush=True)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"out dir: {OUT_DIR}", flush=True)

    print(f"\n[1/5] reading canonical_hands.bin from {CANONICAL_PATH}", flush=True)
    t0 = time.time()
    ch = read_canonical_hands(CANONICAL_PATH, mode="load")
    n_total = len(ch)
    print(f"  loaded {n_total:,} canonical hands in {time.time() - t0:.1f}s",
          flush=True)

    print("\n[2/5] categorizing all hands (vectorized one-hot pass) ...",
          flush=True)
    t0 = time.time()
    cat = categorize_hands(ch.hands)
    print(f"  categorize_hands done in {time.time() - t0:.1f}s", flush=True)
    # Distribution sanity print.
    unique, counts = np.unique(cat, return_counts=True)
    name_map = {
        0: "high_only", 1: "pair", 2: "two_pair", 3: "trips",
        4: "trips_pair", 5: "three_pair", 6: "quads", 7: "composite",
    }
    print("  category distribution:", flush=True)
    for code, n in zip(unique, counts):
        print(f"    {int(code)} {name_map[int(code)]:<12} {int(n):>10,}",
              flush=True)

    print("\n[3/5] selecting two_pair + trips_pair canonical_ids ...", flush=True)
    target_mask = (cat == TWO_PAIR) | (cat == TRIPS_PAIR)
    n_two_pair = int((cat == TWO_PAIR).sum())
    n_trips_pair = int((cat == TRIPS_PAIR).sum())
    n_target = int(target_mask.sum())
    print(f"  two_pair    {n_two_pair:>10,}  (expected {EXPECTED_TWO_PAIR:,})",
          flush=True)
    print(f"  trips_pair  {n_trips_pair:>10,}  (expected {EXPECTED_TRIPS_PAIR:,})",
          flush=True)
    print(f"  total       {n_target:>10,}  (expected {EXPECTED_TOTAL:,})",
          flush=True)
    if (n_two_pair, n_trips_pair) != (EXPECTED_TWO_PAIR, EXPECTED_TRIPS_PAIR):
        print(
            "ERROR: observed counts disagree with EXPECTED_* constants. "
            "Halting — the S81 oracle budget is sized to those exact counts.",
            flush=True,
        )
        return 1

    # ORIGINAL canonical_ids of the subset, in ascending order.
    subset_to_canonical = np.flatnonzero(target_mask).astype(np.uint32)
    assert subset_to_canonical.shape == (EXPECTED_TOTAL,)

    # Per-row category for the subset.
    subset_cat = cat[target_mask].astype(np.int8)
    assert subset_cat.shape == (EXPECTED_TOTAL,)

    # Subset hand bytes (already in lex order because filtering preserves order).
    subset_hands = ch.hands[target_mask]
    assert subset_hands.shape == (EXPECTED_TOTAL, 7)

    # Sanity: confirm the lex-ordering of subset_to_canonical is monotonic
    # (it should be, since np.flatnonzero is monotonic in input position).
    assert np.all(np.diff(subset_to_canonical) > 0), \
        "subset_to_canonical must be strictly increasing"

    print("\n[4/5] choosing held-out subset (every 10th) ...", flush=True)
    holdout_subset_indices = np.arange(
        HOLDOUT_OFFSET, EXPECTED_TOTAL, HOLDOUT_STRIDE, dtype=np.uint32
    )
    holdout_canonical_ids = subset_to_canonical[holdout_subset_indices]
    n_holdout = holdout_subset_indices.shape[0]
    print(f"  held-out hands: {n_holdout:,} "
          f"(every {HOLDOUT_STRIDE}th starting at offset {HOLDOUT_OFFSET})",
          flush=True)
    # Sanity: held-out category distribution should roughly mirror the subset.
    holdout_cat = subset_cat[holdout_subset_indices]
    h_tp = int((holdout_cat == TWO_PAIR).sum())
    h_3p = int((holdout_cat == TRIPS_PAIR).sum())
    print(f"  held-out two_pair    {h_tp:>10,}  "
          f"({100 * h_tp / n_holdout:.2f}%; subset = "
          f"{100 * n_two_pair / EXPECTED_TOTAL:.2f}%)",
          flush=True)
    print(f"  held-out trips_pair  {h_3p:>10,}  "
          f"({100 * h_3p / n_holdout:.2f}%; subset = "
          f"{100 * n_trips_pair / EXPECTED_TOTAL:.2f}%)",
          flush=True)

    print("\n[5/5] writing outputs ...", flush=True)
    t0 = time.time()
    out_subset_path = OUT_DIR / "canonical_hands_s81_subset.bin"
    write_canonical_subset(out_subset_path, subset_hands)
    print(f"  wrote {out_subset_path.name} "
          f"({out_subset_path.stat().st_size / 1e6:.2f} MB)", flush=True)

    out_map_path = OUT_DIR / "v49_a2_subset_to_canonical.npy"
    np.save(out_map_path, subset_to_canonical)
    print(f"  wrote {out_map_path.name} "
          f"({out_map_path.stat().st_size / 1e6:.2f} MB)", flush=True)

    out_holdout_ids_path = OUT_DIR / "v49_a2_holdout_ids.npy"
    np.save(out_holdout_ids_path, holdout_canonical_ids)
    print(f"  wrote {out_holdout_ids_path.name} "
          f"({out_holdout_ids_path.stat().st_size / 1e6:.2f} MB)", flush=True)

    out_holdout_subset_path = OUT_DIR / "v49_a2_holdout_subset_indices.npy"
    np.save(out_holdout_subset_path, holdout_subset_indices)
    print(f"  wrote {out_holdout_subset_path.name} "
          f"({out_holdout_subset_path.stat().st_size / 1e6:.2f} MB)", flush=True)

    out_cat_path = OUT_DIR / "v49_a2_subset_categories.npy"
    np.save(out_cat_path, subset_cat)
    print(f"  wrote {out_cat_path.name} "
          f"({out_cat_path.stat().st_size / 1e6:.2f} MB)", flush=True)

    # Round-trip sanity: re-read the subset bin and confirm shape + first/last
    # row matches what we wrote.
    rt = read_canonical_hands(out_subset_path, mode="load")
    assert len(rt) == EXPECTED_TOTAL, f"round-trip len {len(rt)} != {EXPECTED_TOTAL}"
    assert np.array_equal(rt.hands[0], subset_hands[0]), "round-trip row 0 mismatch"
    assert np.array_equal(rt.hands[-1], subset_hands[-1]), "round-trip last mismatch"
    print(f"  subset file round-trip OK ({time.time() - t0:.1f}s total write)",
          flush=True)

    # Persist provenance for downstream sessions.
    print("\n  computing sha256 of inputs/outputs for provenance ...", flush=True)
    summary = {
        "session": 81,
        "purpose": "v49_a2 targeted N=1000 oracle subset (two_pair + trips_pair)",
        "input": {
            "canonical_hands": str(CANONICAL_PATH.relative_to(ROOT)),
            "canonical_hands_sha256": sha256_file(CANONICAL_PATH),
            "n_hands": n_total,
        },
        "subset": {
            "path": str(out_subset_path.relative_to(ROOT)),
            "sha256": sha256_file(out_subset_path),
            "n_hands": EXPECTED_TOTAL,
            "n_two_pair": n_two_pair,
            "n_trips_pair": n_trips_pair,
        },
        "holdout": {
            "stride": HOLDOUT_STRIDE,
            "offset": HOLDOUT_OFFSET,
            "n_hands": n_holdout,
            "n_two_pair": h_tp,
            "n_trips_pair": h_3p,
        },
        "outputs": {
            "subset_to_canonical": str(out_map_path.relative_to(ROOT)),
            "holdout_canonical_ids": str(out_holdout_ids_path.relative_to(ROOT)),
            "holdout_subset_indices": str(out_holdout_subset_path.relative_to(ROOT)),
            "subset_categories": str(out_cat_path.relative_to(ROOT)),
        },
    }
    summary_path = OUT_DIR / "build_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2))
    print(f"  wrote {summary_path.name}", flush=True)

    print("\nDONE.", flush=True)
    print("Next step: launch oracle generation on the subset file:", flush=True)
    print(
        f"  ./engine/target/release/tw-engine oracle-grid \\\n"
        f"    --canonical data/session81/canonical_hands_s81_subset.bin \\\n"
        f"    --out       data/session81/oracle_grid_s81_n1000.bin \\\n"
        f"    --samples   1000 \\\n"
        f"    --opponent  realistic",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
