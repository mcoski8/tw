"""
Session 81 — train_v49_a2_dt: A2 experiment from S80 M2 follow-up plan
(Decision 115).

Builds a v44-class DecisionTreeRegressor on a THREE-ZONE hybrid label
matrix that overlays N=1000 oracle labels in two non-overlapping regions of
the canonical-hand index space and falls back to N=200 elsewhere:

  Zone 1 (canonical_id 0..500K-1) — labels from data/oracle_grid_prefix500k_n1000.bin
    The pre-existing N=1000 prefix grid. Reused unchanged from A1.

  Zone 2 (canonical_id >=500K AND category in {two_pair, trips_pair} AND
          NOT in held-out set) — labels from
          data/session81/oracle_grid_s81_n1000.bin
    The new S81-generated subset N=1000 grid. Keyed by SUBSET canonical_id
    (0..1.51M-1), so each tp/3p row's label is fetched via the
    subset_to_canonical mapping built by build_s81_subset.py.

  Zone 3 (everything else NOT in held-out set) — labels from
          data/oracle_grid_full_realistic_n200.bin
    The default N=200 full grid. Same source v44 trained on.

Held-out rows (per data/session81/v49_a2_holdout_ids.npy) are EXCLUDED from
both X_train and Y_train. Their N=1000 labels live in the S81 grid and are
consumed by grade_v49_a2_holdout.py during grading, never during training.

Hyperparameters identical to v44_dt / v49_a1_dt: max_depth=36, ml=1,
random_state=42, criterion=squared_error.

Feature pipeline identical to v44_dt: build_X imported from train_v44_dt
(107 features = v43 base 103 + 4 high_only_aug_v4 gated).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/train_v49_a2_dt.py \\
      --max-depth 36 --min-samples-leaf 1 \\
      --output data/v49_a2_dt_model.npz

Smoke-test mode (does NOT require S81 oracle output, runs in <1 min):
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/train_v49_a2_dt.py \\
      --smoke-test
"""
from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.tree import DecisionTreeRegressor

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from train_v44_dt import build_X, FEATURE_COLUMNS  # noqa: E402
from train_v27_dt import ALPHA_MAP  # noqa: E402

GRID_FULL_N200 = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX_N1000 = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
GRID_S81_N1000 = ROOT / "data" / "session81" / "oracle_grid_s81_n1000.bin"

SUBSET_TO_CANONICAL = ROOT / "data" / "session81" / "v49_a2_subset_to_canonical.npy"
HOLDOUT_IDS = ROOT / "data" / "session81" / "v49_a2_holdout_ids.npy"
SUBSET_CATEGORIES = ROOT / "data" / "session81" / "v49_a2_subset_categories.npy"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-depth", type=int, default=36)
    ap.add_argument("--min-samples-leaf", type=int, default=1)
    ap.add_argument("--output", type=Path,
                    default=ROOT / "data" / "v49_a2_dt_model.npz")
    ap.add_argument("--smoke-test", action="store_true",
                    help="Build Y without requiring the S81 grid; skip fit. "
                         "Verifies the three-zone overlay logic + held-out "
                         "removal end-to-end before the oracle is done.")
    args = ap.parse_args()

    print("=" * 100, flush=True)
    print("Session 81 — train_v49_a2_dt (A2 experiment, Decision 115)", flush=True)
    print("=" * 100, flush=True)
    print(f"  Three-zone hybrid Y:", flush=True)
    print(f"    Zone 1: canonical_id < 500K → N=1000 prefix grid", flush=True)
    print(f"    Zone 2: canonical_id >= 500K AND tp/3p AND not held-out "
          f"→ N=1000 S81 grid", flush=True)
    print(f"    Zone 3: everything else not held-out → N=200 full grid", flush=True)
    print(f"  Held-out rows: EXCLUDED from training entirely.", flush=True)
    print(f"  Hyperparams: depth={args.max_depth}, ml={args.min_samples_leaf}.\n",
          flush=True)

    # -----------------------------------------------------------------------
    # [1/6] Build X (shared with v44/A1 pipeline).
    # -----------------------------------------------------------------------
    print("[1/6] building X (shared with v44 pipeline) ...", flush=True)
    t0 = time.time()
    X, n = build_X()
    print(f"  X={X.shape}  ({len(FEATURE_COLUMNS)} features)  "
          f"built in {time.time()-t0:.1f}s", flush=True)

    # -----------------------------------------------------------------------
    # [2/6] Load N=200 full grid as default Y (Zone 3).
    # -----------------------------------------------------------------------
    print("\n[2/6] loading default Y from N=200 full grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL_N200, mode="memmap")
    if len(gf) < n:
        print(f"ERROR: full grid has {len(gf)} records but X has {n} rows.",
              flush=True)
        return 1
    Y = np.asarray(gf.evs[:n], dtype=np.float32).copy()
    print(f"  Y={Y.shape}  {Y.nbytes/1e6:.1f} MB  (N=200 labels everywhere "
          f"to start)", flush=True)

    # -----------------------------------------------------------------------
    # [3/6] Zone 1 overlay: first 500K rows → N=1000 prefix grid.
    # -----------------------------------------------------------------------
    print("\n[3/6] Zone 1 overlay: first 500K rows ← N=1000 prefix grid ...",
          flush=True)
    gp = read_oracle_grid(GRID_PREFIX_N1000, mode="memmap")
    n_prefix = len(gp)
    print(f"  prefix grid: n_records={n_prefix:,}, samples={gp.header.samples}, "
          f"opp={gp.header.opp_label}", flush=True)
    # Verify alignment: prefix and full canonical_ids must match in first n_prefix rows.
    ids_prefix = np.asarray(gp.canonical_ids[:1000], dtype=np.uint32)
    ids_full = np.asarray(gf.canonical_ids[:1000], dtype=np.uint32)
    if not np.array_equal(ids_prefix, ids_full):
        print("ERROR: prefix and full canonical_ids disagree in first 1000 rows.",
              flush=True)
        return 1
    print("  ✓ canonical_ids align (first 1000 spot-checked).", flush=True)
    n_z1 = n_prefix
    Y[:n_z1] = np.asarray(gp.evs[:n_z1], dtype=np.float32)
    print(f"  swapped first {n_z1:,} rows to N=1000 prefix labels.", flush=True)

    # -----------------------------------------------------------------------
    # [4/6] Zone 2 overlay: tp/3p rows with canonical_id >= 500K AND not
    # held-out → N=1000 S81 grid. Indexed via subset_to_canonical mapping.
    # -----------------------------------------------------------------------
    print("\n[4/6] Zone 2 overlay: tp/3p training rows (≥500K) ← N=1000 S81 grid ...",
          flush=True)
    subset_to_canonical = np.load(SUBSET_TO_CANONICAL)
    holdout_ids = np.load(HOLDOUT_IDS)
    subset_cat = np.load(SUBSET_CATEGORIES)
    n_subset = subset_to_canonical.shape[0]
    n_holdout = holdout_ids.shape[0]
    print(f"  subset hands: {n_subset:,}", flush=True)
    print(f"  held-out hands: {n_holdout:,}", flush=True)

    # Compute the held-out mask over subset indices (boolean, len 1.51M).
    holdout_set = set(int(x) for x in holdout_ids)
    subset_holdout_mask = np.zeros(n_subset, dtype=bool)
    for i, cid in enumerate(subset_to_canonical):
        if int(cid) in holdout_set:
            subset_holdout_mask[i] = True
    assert subset_holdout_mask.sum() == n_holdout, \
        f"held-out mask mismatch: {subset_holdout_mask.sum()} vs {n_holdout}"

    # Zone 2 mask: subset rows that are NOT held-out AND canonical_id >= 500K.
    zone2_mask = (~subset_holdout_mask) & (subset_to_canonical >= n_z1)
    zone2_subset_indices = np.flatnonzero(zone2_mask)
    zone2_canonical_ids = subset_to_canonical[zone2_subset_indices]
    n_z2 = zone2_subset_indices.shape[0]
    print(f"  zone-2 rows (tp/3p, ≥{n_z1:,}, not held-out): {n_z2:,}",
          flush=True)

    if args.smoke_test:
        print("\n  --smoke-test active: skipping S81 grid read + DT fit.",
              flush=True)
        print(f"  Y unmodified for Zone 2; Y dtype={Y.dtype}, shape={Y.shape}.",
              flush=True)
    else:
        if not GRID_S81_N1000.exists():
            print(f"ERROR: S81 grid not found at {GRID_S81_N1000}. "
                  f"Wait for the background oracle job to complete, then re-run.",
                  flush=True)
            return 1
        gs = read_oracle_grid(GRID_S81_N1000, mode="memmap")
        if len(gs) != n_subset:
            print(f"ERROR: S81 grid has {len(gs)} records, subset expects "
                  f"{n_subset}. Oracle still running?", flush=True)
            return 1
        if gs.header.samples != 1000:
            print(f"ERROR: S81 grid samples={gs.header.samples}, expected 1000.",
                  flush=True)
            return 1
        # Pull the zone-2 EVs from the S81 grid at the subset positions
        # (the S81 grid's canonical_id field equals row position, since it
        # was generated over the subset file 0..1.51M-1).
        s81_evs = np.asarray(gs.evs[zone2_subset_indices], dtype=np.float32)
        # Overlay into Y at the ORIGINAL canonical_ids.
        Y[zone2_canonical_ids] = s81_evs
        print(f"  ✓ overlaid {n_z2:,} rows with S81 N=1000 labels.", flush=True)

    # -----------------------------------------------------------------------
    # [5/6] Drop held-out rows from X and Y to form training set.
    # -----------------------------------------------------------------------
    print("\n[5/6] removing held-out rows from training set ...", flush=True)
    train_mask = np.ones(n, dtype=bool)
    train_mask[holdout_ids] = False
    n_train = int(train_mask.sum())
    assert n_train == n - n_holdout, \
        f"train_mask sanity: {n_train} != {n} - {n_holdout}"
    X_train = X[train_mask]
    Y_train = Y[train_mask]
    print(f"  X_train={X_train.shape}, Y_train={Y_train.shape}", flush=True)
    print(f"  ({n_holdout:,} held-out rows removed)", flush=True)

    # Zone composition summary on the training set.
    zone1_in_train = int(np.sum(train_mask[:n_z1]))
    zone2_in_train = n_z2  # zone2_mask already excludes held-out
    zone3_in_train = n_train - zone1_in_train - zone2_in_train
    print(f"\n  training set zone composition:", flush=True)
    print(f"    Zone 1 (N=1000 prefix, first 500K):    {zone1_in_train:>10,} "
          f"({100*zone1_in_train/n_train:.2f}%)", flush=True)
    print(f"    Zone 2 (N=1000 S81, tp/3p ≥500K):       {zone2_in_train:>10,} "
          f"({100*zone2_in_train/n_train:.2f}%)", flush=True)
    print(f"    Zone 3 (N=200 fallback):                {zone3_in_train:>10,} "
          f"({100*zone3_in_train/n_train:.2f}%)", flush=True)
    n1000_share = (zone1_in_train + zone2_in_train) / n_train
    print(f"    Total N=1000 share of training labels: "
          f"{100*n1000_share:.2f}%", flush=True)

    if args.smoke_test:
        print("\n  --smoke-test complete: zone overlays + holdout removal "
              "validated. Skipping fit.", flush=True)
        return 0

    # -----------------------------------------------------------------------
    # [6/6] Fit DT and persist.
    # -----------------------------------------------------------------------
    print(f"\n[6/6] fitting DT depth={args.max_depth} ml={args.min_samples_leaf} "
          f"on {n_train:,} rows ...", flush=True)
    t0 = time.time()
    dt = DecisionTreeRegressor(
        max_depth=args.max_depth, min_samples_leaf=args.min_samples_leaf,
        random_state=42, criterion="squared_error",
    )
    dt.fit(X_train, Y_train)
    print(f"  fit {time.time()-t0:.1f}s  leaves={dt.get_n_leaves():,}  "
          f"depth={dt.get_depth()}", flush=True)

    tree = dt.tree_
    val = tree.value
    if val.ndim == 3:
        val = val[:, :, 0]
    np.savez_compressed(
        args.output,
        children_left=tree.children_left.astype(np.int32),
        children_right=tree.children_right.astype(np.int32),
        feature=tree.feature.astype(np.int32),
        threshold=tree.threshold.astype(np.float64),
        leaf_values=val.astype(np.float32),
        feature_columns=np.array(FEATURE_COLUMNS, dtype=object),
        cat_map_keys=np.array(list(ALPHA_MAP.keys()), dtype=object),
        cat_map_values=np.array(list(ALPHA_MAP.values()), dtype=np.int32),
        depth=np.int32(dt.get_depth()),
        n_leaves=np.int32(dt.get_n_leaves()),
        training_grid=np.array(
            ["v49_a2_hybrid_500K_n1000_plus_tp3p_n1000_plus_n200_minus_holdout"],
            dtype=object),
        max_depth=np.int32(args.max_depth),
        min_samples_leaf=np.int32(args.min_samples_leaf),
        n_zone1=np.int32(zone1_in_train),
        n_zone2=np.int32(zone2_in_train),
        n_zone3=np.int32(zone3_in_train),
        n_holdout_excluded=np.int32(n_holdout),
    )
    print(f"\nsaved {args.output} "
          f"({args.output.stat().st_size/1e6:.2f} MB)", flush=True)

    fi = dt.feature_importances_
    order = np.argsort(-fi)
    print(f"\nTop-15 feature importances:", flush=True)
    for r, idx in enumerate(order[:15], 1):
        print(f"  {r:>3d}. {FEATURE_COLUMNS[idx]:<42} {100*fi[idx]:6.2f}%",
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
