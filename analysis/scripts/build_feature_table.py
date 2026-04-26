"""
Build the Sprint-7 feature table: hand-level features + per-profile BR
choices + multiway-robust setting + robust-setting tier features. One
Parquet file per run, joined by canonical_id.

Output columns
--------------
canonical_id            uint32
br_mfsuitaware          uint8     0..104
br_omaha                uint8
br_topdef               uint8
br_weighted             uint8
multiway_robust         uint8
agreement_class         dictionary[str]   {unanimous,3of4,2of4,split2_2,split1_1_1_1}
mode_count              uint8     1..4
ev_mfsuitaware          float32   net points heads-up vs that profile
ev_omaha                float32
ev_topdef               float32
ev_weighted             float32
ev_mean                 float32   average of the 4 — multiway proxy
ev_min                  float32   worst-case (toughest opponent for THIS hand)
ev_max                  float32   best-case (weakest opponent)

(Hand-level — see tw_analysis.features.HAND_FEATURE_KEYS)
n_pairs, pair_high_rank, pair_low_rank, pair_third_rank,
n_trips, trips_rank, n_quads, quads_rank,
top_rank, second_rank, third_rank,
suit_max, suit_2nd, suit_3rd, suit_4th,
n_suits_present, is_monosuit,
connectivity, n_broadway,
category                dictionary[str]   {high_only,pair,...,quads}

(Robust-setting tier — see tw_analysis.features.TIER_FEATURE_KEYS, prefixed `robust_`)
robust_top_rank, robust_mid_is_pair, robust_mid_is_suited,
robust_mid_high_rank, robust_mid_low_rank, robust_mid_rank_sum,
robust_bot_suit_max, robust_bot_is_double_suited,
robust_bot_n_pairs, robust_bot_pair_high,
robust_bot_high_rank, robust_bot_low_rank, robust_bot_rank_sum,
robust_bot_n_broadway, robust_bot_connectivity

The pipeline streams in chunks (default 250K rows) to keep peak memory low,
runs scalar/batch parity on the first chunk's first 200 rows as a regression
gate (Decision 028), and writes a single concatenated Parquet at the end.
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import pyarrow as pa  # noqa: E402
import pyarrow.parquet as pq  # noqa: E402

from tw_analysis import (  # noqa: E402
    AGREEMENT_ORDER,
    CATEGORY_ORDER,
    HAND_FEATURE_KEYS,
    TIER_FEATURE_KEYS,
    assert_scalar_batch_parity,
    compute_multiway_robust,
    hand_features_batch,
    read_br_file,
    read_canonical_hands,
    tier_features_batch,
)


PROFILE_LABELS = ("mfsuitaware", "omaha", "topdef", "weighted")
PROFILE_FILENAMES = {
    "mfsuitaware": "mfsuitaware_mixed90.bin",
    "omaha":       "omahafirst_mixed90.bin",
    "topdef":      "topdefensive_mixed90.bin",
    "weighted":    "randomweighted.bin",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--canonical", type=Path,
                    default=ROOT / "data" / "canonical_hands.bin")
    ap.add_argument("--bin-dir", type=Path,
                    default=ROOT / "data" / "best_response_cloud")
    ap.add_argument("--out", type=Path,
                    default=ROOT / "data" / "feature_table.parquet")
    ap.add_argument("--limit", type=int, default=0,
                    help="if > 0, process only the first N canonical hands "
                         "(useful for sanity tests)")
    ap.add_argument("--chunk", type=int, default=250_000,
                    help="rows per processing chunk (default 250K)")
    ap.add_argument("--skip-parity", action="store_true",
                    help="skip the scalar/batch parity check (don't unless you "
                         "have a reason)")
    args = ap.parse_args()

    print(f"Loading canonical hands from {args.canonical}…")
    canonical = read_canonical_hands(args.canonical)
    n_total = canonical.header.num_hands
    cards = canonical.hands  # (n_total, 7) uint8
    print(f"  {n_total:,} canonical hands, dtype={cards.dtype}, shape={cards.shape}")

    print(f"Loading 4 best-response files from {args.bin_dir}…")
    brs = []
    for label in PROFILE_LABELS:
        p = args.bin_dir / PROFILE_FILENAMES[label]
        br = read_br_file(p, mode="memmap")
        brs.append(br)
        print(f"  {label:14s} {len(br):>10,} records  opp={br.header.opp_label}")

    if any(len(br) != n_total for br in brs):
        raise SystemExit("ERROR: at least one BR file size != canonical_total")

    # Stack per-profile settings into (n_total, 4).
    per_profile = np.column_stack([
        br.records["best_setting_index"] for br in brs
    ]).astype(np.uint8)
    per_profile_ev = np.column_stack([
        br.records["best_ev"] for br in brs
    ]).astype(np.float32)

    n_to_process = min(args.limit, n_total) if args.limit > 0 else n_total
    print(f"\nProcessing {n_to_process:,} hands in chunks of {args.chunk:,}.")
    if args.limit > 0:
        cards = cards[:n_to_process]
        per_profile = per_profile[:n_to_process]
        per_profile_ev = per_profile_ev[:n_to_process]

    if not args.skip_parity:
        print("Running scalar/batch parity check on first chunk's first 200 rows…")
        first_chunk = cards[:min(args.chunk, n_to_process)]
        first_chunk_pp = per_profile[:first_chunk.shape[0]]
        first_robust = compute_multiway_robust(first_chunk_pp)
        assert_scalar_batch_parity(first_chunk, first_robust.multiway_robust, sample_size=200, seed=0)
        print("  Parity OK.")

    chunks: list[pa.Table] = []
    t0 = time.time()
    n_done = 0
    while n_done < n_to_process:
        chunk_end = min(n_done + args.chunk, n_to_process)
        slice_hands = cards[n_done:chunk_end]
        slice_pp = per_profile[n_done:chunk_end]
        slice_ev = per_profile_ev[n_done:chunk_end]

        robust = compute_multiway_robust(slice_pp)
        hf = hand_features_batch(slice_hands)
        tf = tier_features_batch(slice_hands, robust.multiway_robust)

        cols: dict[str, np.ndarray] = {
            "canonical_id": np.arange(n_done, chunk_end, dtype=np.uint32),
            "br_mfsuitaware": slice_pp[:, 0],
            "br_omaha":       slice_pp[:, 1],
            "br_topdef":      slice_pp[:, 2],
            "br_weighted":    slice_pp[:, 3],
            "multiway_robust": robust.multiway_robust,
            "mode_count":      robust.mode_count,
            "ev_mfsuitaware": slice_ev[:, 0],
            "ev_omaha":       slice_ev[:, 1],
            "ev_topdef":      slice_ev[:, 2],
            "ev_weighted":    slice_ev[:, 3],
            "ev_mean":        slice_ev.mean(axis=1).astype(np.float32),
            "ev_min":         slice_ev.min(axis=1).astype(np.float32),
            "ev_max":         slice_ev.max(axis=1).astype(np.float32),
        }
        for k in HAND_FEATURE_KEYS:
            if k == "category_id":
                # Map category_id → string for downstream readability via dictionary encoding.
                cat_strs = np.array(CATEGORY_ORDER, dtype=object)[hf[k]]
                cols["category"] = cat_strs
            else:
                cols[k] = hf[k]
        for k in TIER_FEATURE_KEYS:
            cols[f"robust_{k}"] = tf[k]
        # agreement_class as dictionary[str]
        cols["agreement_class"] = np.array(AGREEMENT_ORDER, dtype=object)[robust.agreement_id]

        # Build pyarrow table for this chunk.
        arrays: dict[str, pa.Array] = {}
        for name, arr in cols.items():
            if arr.dtype == np.bool_:
                arrays[name] = pa.array(arr, type=pa.bool_())
            elif arr.dtype == np.float32:
                arrays[name] = pa.array(arr, type=pa.float32())
            elif arr.dtype.kind in ("u", "i"):
                arrays[name] = pa.array(arr)
            elif name in ("category", "agreement_class"):
                arrays[name] = pa.array(arr.tolist(), type=pa.dictionary(pa.int8(), pa.string()))
            else:
                arrays[name] = pa.array(arr.tolist())
        chunks.append(pa.table(arrays))

        n_done = chunk_end
        elapsed = time.time() - t0
        rate = n_done / elapsed if elapsed > 0 else 0.0
        eta = (n_to_process - n_done) / rate if rate > 0 else 0.0
        print(f"  {n_done:>10,}/{n_to_process:,}  "
              f"({100*n_done/n_to_process:5.1f}%)  "
              f"elapsed={elapsed:6.1f}s rate={rate:8,.0f} hands/s eta={eta:6.1f}s")

    print(f"\nConcatenating {len(chunks)} chunks…")
    table = pa.concat_tables(chunks)
    print(f"  total rows: {table.num_rows:,}, columns: {table.num_columns}")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    print(f"Writing Parquet to {args.out}…")
    pq.write_table(
        table,
        args.out,
        compression="zstd",
        compression_level=3,
        use_dictionary=["category", "agreement_class"],
        write_statistics=True,
    )
    out_bytes = args.out.stat().st_size
    print(f"  done — {out_bytes/1024/1024:.1f} MB on disk")

    print("\n=== Quick stats ===")
    print(f"Rows: {table.num_rows:,}")
    print(f"Columns: {table.num_columns}")
    print(f"Schema:\n{table.schema}")

    # Agreement class breakdown — should match the multiway_analysis.py numbers
    # in CURRENT_PHASE.md (unanimous 26.6%, 3of4 40.4%, etc.) within sample noise.
    ac_col = table.column("agreement_class").to_pandas()
    counts = ac_col.value_counts(normalize=True).sort_index()
    print("\nAgreement class breakdown (full table):")
    for cls in AGREEMENT_ORDER:
        share = float(counts.get(cls, 0.0))
        print(f"  {cls:<18} {share*100:5.2f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
