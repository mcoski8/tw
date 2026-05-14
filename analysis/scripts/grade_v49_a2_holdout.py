#!/usr/bin/env python3
"""Session 81 — Grade v44_dt (baseline) and v49_a2_dt (targeted N=1000)
against THREE oracle lenses:

  Lens 1: oracle_grid_full_realistic_n200.bin           (N=200, 6M rows)
            → Production-baseline regret + match. v49_a2 must hold this
              within $50 of v44 to clear the ship bar.

  Lens 2: oracle_grid_prefix500k_n1000.bin              (N=1000, 500K rows)
            → Same lens as S80. Lets us see if A2 retains A1's prefix gain.

  Lens 3: data/session81/oracle_grid_s81_n1000.bin      (N=1000, 151K rows)
            → THE NEW LENS. Held-out subset of two_pair + trips_pair hands
              whose N=1000 labels v49_a2 did NOT see in training. This is
              the OOS test that settles the S80 in-sample-evaluation caveat.

Pre-committed ship verdict (CURRENT_PHASE S81, Decision 115 follow-up):
  SHIP v49_a2  if held-out N=1000 match ≥ 75% AND |N=200 regret − v44| ≤ $50
  NULL v49_a2  if held-out N=1000 match < 72%
  MIXED        otherwise (72-75% held-out match) — re-examine alongside A3

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v49_a2_holdout.py

Smoke-test (does NOT require v49_a2 model or S81 grid):
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v49_a2_holdout.py --smoke-test
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.grade_strategy import CATEGORY_NAMES, categorize_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from train_v44_dt import build_X  # noqa: E402

CANON = ROOT / "data" / "canonical_hands.bin"
GRID_FULL_N200 = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX_N1000 = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
GRID_S81_N1000 = ROOT / "data" / "session81" / "oracle_grid_s81_n1000.bin"

SUBSET_TO_CANONICAL = ROOT / "data" / "session81" / "v49_a2_subset_to_canonical.npy"
HOLDOUT_IDS = ROOT / "data" / "session81" / "v49_a2_holdout_ids.npy"
HOLDOUT_SUBSET_INDICES = ROOT / "data" / "session81" / "v49_a2_holdout_subset_indices.npy"
SUBSET_CATEGORIES = ROOT / "data" / "session81" / "v49_a2_subset_categories.npy"

OUT_DIR = ROOT / "data" / "session81"
OUT_JSON = OUT_DIR / "grade_v49_a2_holdout_summary.json"

EV_TO_DOLLARS = 10.0

MODEL_PATHS = {
    "v44_dt":    ROOT / "data" / "v44_dt_model.npz",
    "v49_a2_dt": ROOT / "data" / "v49_a2_dt_model.npz",
}

# Pre-committed ship-verdict thresholds.
SHIP_HOLDOUT_MATCH_MIN = 75.0   # %
SHIP_N200_REGRET_TOL_USD = 50.0  # $/1000h above v44
NULL_HOLDOUT_MATCH_MAX = 72.0   # %


def load_model_arrays(path: Path) -> dict:
    arr = np.load(path, allow_pickle=True)
    val = arr["leaf_values"]
    return {
        "children_left":  np.asarray(arr["children_left"],  dtype=np.int32),
        "children_right": np.asarray(arr["children_right"], dtype=np.int32),
        "feature":        np.asarray(arr["feature"],        dtype=np.int32),
        "threshold":      np.asarray(arr["threshold"],      dtype=np.float64),
        "leaf_argmax":    val.argmax(axis=1).astype(np.int16),
        "n_leaves":       int(arr["n_leaves"]),
        "depth":          int(arr["depth"]),
    }


def vectorized_predict(X: np.ndarray, m: dict) -> np.ndarray:
    """For each row in X, walk the tree to its leaf and return that leaf's
    argmax setting index. Returns (n,) int16."""
    cl   = m["children_left"]
    cr   = m["children_right"]
    feat = m["feature"]
    thr  = m["threshold"]
    leaf_argmax = m["leaf_argmax"]

    n = X.shape[0]
    nodes = np.zeros(n, dtype=np.int32)
    iters = 0
    max_iters = m["depth"] + 2
    while True:
        is_leaf = cl[nodes] == -1
        if is_leaf.all():
            break
        active = ~is_leaf
        idx = np.nonzero(active)[0]
        node_at = nodes[idx]
        feat_at = feat[node_at]
        x_vals = X[idx, feat_at].astype(np.float64, copy=False)
        thr_at = thr[node_at]
        go_left = x_vals <= thr_at
        nodes[idx] = np.where(go_left, cl[node_at], cr[node_at])
        iters += 1
        if iters > max_iters:
            raise RuntimeError(f"tree walk did not converge after {iters} iters")
    return leaf_argmax[nodes]


def grade_against_lens(
    picks: np.ndarray,        # (n_rows,) int16 — model picks for these row positions
    evs: np.ndarray,          # (n_rows, 105) float64 — oracle EVs at the lens samples
) -> dict:
    """Compute match-rate + mean regret of `picks` against argmax(evs)."""
    argmax = evs.argmax(axis=1).astype(np.int16)
    max_ev = evs.max(axis=1)
    chosen_ev = evs[np.arange(len(picks)), picks]
    regret = (max_ev - chosen_ev).astype(np.float64)
    match = (picks == argmax)
    return {
        "n": int(len(picks)),
        "match_pct": float(100.0 * match.mean()),
        "mean_regret_ev": float(regret.mean()),
        "mean_regret_dol": float(regret.mean() * EV_TO_DOLLARS * 1000),
        "match_mask": match,
        "argmax": argmax,
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument(
        "--smoke-test", action="store_true",
        help="Skip lenses requiring v49_a2 model + S81 grid; verify the v44 "
             "side of the pipeline + held-out plumbing.",
    )
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 100, flush=True)
    print("Session 81 — Grade v49_a2 with held-out OOS validation", flush=True)
    print("=" * 100, flush=True)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    # ---------------------------------------------------------------
    # [1/7] Build X (shared 107-feature pipeline).
    # ---------------------------------------------------------------
    print("\n[1/7] building X (shared 107-feature pipeline) ...", flush=True)
    t0 = time.time()
    X, n = build_X()
    print(f"  X={X.shape}  built in {time.time() - t0:.1f}s", flush=True)

    # ---------------------------------------------------------------
    # [2/7] Load held-out sidecars + S81 subset mapping.
    # ---------------------------------------------------------------
    print("\n[2/7] loading held-out sidecars ...", flush=True)
    holdout_canonical_ids = np.load(HOLDOUT_IDS)
    holdout_subset_idx = np.load(HOLDOUT_SUBSET_INDICES)
    subset_to_canonical = np.load(SUBSET_TO_CANONICAL)
    subset_cat = np.load(SUBSET_CATEGORIES)
    n_holdout = holdout_canonical_ids.shape[0]
    print(f"  held-out hands: {n_holdout:,}", flush=True)
    print(f"  subset hands:   {subset_to_canonical.shape[0]:,}", flush=True)
    # Sanity: cross-check holdout_canonical_ids[i] == subset_to_canonical[holdout_subset_idx[i]]
    if not np.array_equal(
        holdout_canonical_ids,
        subset_to_canonical[holdout_subset_idx],
    ):
        print("ERROR: held-out canonical_ids do NOT match "
              "subset_to_canonical[holdout_subset_idx]. "
              "Sidecars are inconsistent.", flush=True)
        return 1
    print("  ✓ holdout_ids and holdout_subset_idx cross-check OK.", flush=True)
    holdout_cat = subset_cat[holdout_subset_idx]

    # ---------------------------------------------------------------
    # [3/7] Load Lens 1: N=200 full grid.
    # ---------------------------------------------------------------
    print("\n[3/7] loading Lens 1: N=200 full grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL_N200, mode="memmap")
    full_evs = np.asarray(gf.evs[:n], dtype=np.float64)
    print(f"  full grid: {full_evs.shape}  samples={gf.header.samples}",
          flush=True)

    # ---------------------------------------------------------------
    # [4/7] Load Lens 2: N=1000 prefix grid.
    # ---------------------------------------------------------------
    print("\n[4/7] loading Lens 2: N=1000 prefix grid ...", flush=True)
    gp = read_oracle_grid(GRID_PREFIX_N1000, mode="memmap")
    n_prefix = len(gp)
    ids_p = np.asarray(gp.canonical_ids[:1000], dtype=np.uint32)
    ids_f = np.asarray(gf.canonical_ids[:1000], dtype=np.uint32)
    if not np.array_equal(ids_p, ids_f):
        print("ERROR: prefix and full canonical_ids disagree.", flush=True)
        return 1
    prefix_evs = np.asarray(gp.evs[:n_prefix], dtype=np.float64)
    print(f"  prefix grid: {prefix_evs.shape}  samples={gp.header.samples}",
          flush=True)

    # ---------------------------------------------------------------
    # [5/7] Load Lens 3: N=1000 S81 grid (held-out OOS lens).
    # ---------------------------------------------------------------
    print("\n[5/7] loading Lens 3: N=1000 S81 held-out subset ...", flush=True)
    have_lens3 = GRID_S81_N1000.exists() and not args.smoke_test
    if not have_lens3:
        if args.smoke_test:
            print("  --smoke-test: skipping S81 grid load.", flush=True)
        else:
            print(f"  WARNING: {GRID_S81_N1000} not found — Lens 3 disabled.",
                  flush=True)
        holdout_evs = None
    else:
        gs = read_oracle_grid(GRID_S81_N1000, mode="memmap")
        if gs.header.samples != 1000:
            print(f"ERROR: S81 grid samples={gs.header.samples}, expected 1000.",
                  flush=True)
            return 1
        if len(gs) != subset_to_canonical.shape[0]:
            print(f"ERROR: S81 grid has {len(gs)} records, subset expects "
                  f"{subset_to_canonical.shape[0]}. Run may be incomplete.",
                  flush=True)
            return 1
        # Pull the 151K held-out rows directly via subset positions.
        holdout_evs = np.asarray(
            gs.evs[holdout_subset_idx], dtype=np.float64
        )
        print(f"  S81 grid: {len(gs):,} records  samples={gs.header.samples}",
              flush=True)
        print(f"  held-out slice: {holdout_evs.shape}", flush=True)

    # Categorize all hands for Lens 1 & 2 (used in summary tables).
    ch = read_canonical_hands(CANON, mode="memmap")
    if len(ch) < n:
        print(f"ERROR: canonical hands ({len(ch)}) < n ({n}).", flush=True)
        return 1
    cats_full = categorize_hands(np.asarray(ch.hands[:n]))

    # ---------------------------------------------------------------
    # [6/7] Per-model predictions and per-lens grading.
    # ---------------------------------------------------------------
    print("\n[6/7] grading each model on each lens ...", flush=True)
    results: dict[str, dict] = {}
    for name, mp in MODEL_PATHS.items():
        if not mp.exists():
            print(f"\n  SKIP {name}: model file not found at {mp}",
                  flush=True)
            results[name] = {"missing": True}
            continue
        print(f"\n  ---- {name} ----", flush=True)
        t0 = time.time()
        m = load_model_arrays(mp)
        print(f"  loaded {mp.name}  leaves={m['n_leaves']:,}  "
              f"depth={m['depth']}  ({time.time() - t0:.1f}s)", flush=True)

        t0 = time.time()
        picks_full = vectorized_predict(X, m)
        print(f"  predicted {n:,} hands in {time.time() - t0:.1f}s "
              f"({n / max(time.time() - t0, 1e-9):.0f} hands/s)", flush=True)

        # Lens 1: N=200 full grid (all 6M).
        lens1 = grade_against_lens(picks_full, full_evs)
        print(f"  Lens 1 (N=200, full 6M):  "
              f"match%={lens1['match_pct']:6.2f}%  "
              f"$/1000h={lens1['mean_regret_dol']:>+8,.0f}", flush=True)

        # Lens 2: N=1000 prefix grid (first 500K).
        picks_prefix = picks_full[:n_prefix]
        lens2 = grade_against_lens(picks_prefix, prefix_evs)
        print(f"  Lens 2 (N=1000, prefix 500K):  "
              f"match%={lens2['match_pct']:6.2f}%  "
              f"$/1000h={lens2['mean_regret_dol']:>+8,.0f}", flush=True)

        # Lens 3: N=1000 S81 held-out (151K).
        if holdout_evs is not None:
            picks_holdout = picks_full[holdout_canonical_ids]
            lens3 = grade_against_lens(picks_holdout, holdout_evs)
            print(f"  Lens 3 (N=1000, HELD-OUT 151K):  "
                  f"match%={lens3['match_pct']:6.2f}%  "
                  f"$/1000h={lens3['mean_regret_dol']:>+8,.0f}", flush=True)
        else:
            lens3 = None

        # Per-category lens-3 breakdown (two_pair vs trips_pair).
        if lens3 is not None:
            print(f"  Lens 3 per-category breakdown:", flush=True)
            for cat_code, cat_name in [(2, "two_pair"), (4, "trips_pair")]:
                cmask = holdout_cat == cat_code
                n_c = int(cmask.sum())
                if n_c == 0:
                    continue
                m_pct = 100.0 * lens3["match_mask"][cmask].mean()
                # Compute regret on the masked rows.
                chosen = holdout_evs[cmask][
                    np.arange(n_c), picks_holdout[cmask]
                ]
                regret_c = (holdout_evs[cmask].max(axis=1) - chosen)
                reg_dol = float(regret_c.mean() * EV_TO_DOLLARS * 1000)
                print(f"    {cat_name:<12}  n={n_c:>7,}  "
                      f"match%={m_pct:6.2f}%  $/1000h={reg_dol:>+8,.0f}",
                      flush=True)

        results[name] = {
            "n_leaves": m["n_leaves"],
            "depth": m["depth"],
            "lens1_n200_full": {
                k: v for k, v in lens1.items()
                if k not in ("match_mask", "argmax")
            },
            "lens2_n1000_prefix": {
                k: v for k, v in lens2.items()
                if k not in ("match_mask", "argmax")
            },
            "lens3_n1000_holdout": (
                None if lens3 is None
                else {k: v for k, v in lens3.items()
                      if k not in ("match_mask", "argmax")}
            ),
            "_picks_full": picks_full,
            "_lens3_match_mask": (
                lens3["match_mask"] if lens3 is not None else None
            ),
        }

    # ---------------------------------------------------------------
    # [7/7] Headline 2-column comparison + Δ + ship verdict.
    # ---------------------------------------------------------------
    print("\n" + "=" * 100, flush=True)
    print("HEADLINE — v44_dt vs v49_a2_dt", flush=True)
    print("=" * 100, flush=True)

    base = results.get("v44_dt", {})
    cand = results.get("v49_a2_dt", {})

    def fmt_metric(label: str, base_v, cand_v, fmt_fn):
        bs = "MISSING" if base_v is None else fmt_fn(base_v)
        cs = "MISSING" if cand_v is None else fmt_fn(cand_v)
        print(f"  {label:<40}{bs:>16}{cs:>16}", flush=True)

    print(f"  {'metric':<40}{'v44_dt':>16}{'v49_a2_dt':>16}", flush=True)
    print(f"  {'-' * 72}", flush=True)
    if not base.get("missing"):
        fmt_metric("n_leaves",
                   base.get("n_leaves"),
                   cand.get("n_leaves") if not cand.get("missing") else None,
                   lambda v: f"{v:,}")
        fmt_metric("depth",
                   base.get("depth"),
                   cand.get("depth") if not cand.get("missing") else None,
                   lambda v: str(v))
        fmt_metric("Lens 1 match% (N=200, 6M)",
                   base["lens1_n200_full"]["match_pct"],
                   None if cand.get("missing") else cand["lens1_n200_full"]["match_pct"],
                   lambda v: f"{v:.2f}%")
        fmt_metric("Lens 1 $/1000h (N=200)",
                   base["lens1_n200_full"]["mean_regret_dol"],
                   None if cand.get("missing") else cand["lens1_n200_full"]["mean_regret_dol"],
                   lambda v: f"{v:+,.0f}")
        fmt_metric("Lens 2 match% (N=1000, prefix)",
                   base["lens2_n1000_prefix"]["match_pct"],
                   None if cand.get("missing") else cand["lens2_n1000_prefix"]["match_pct"],
                   lambda v: f"{v:.2f}%")
        fmt_metric("Lens 2 $/1000h (N=1000)",
                   base["lens2_n1000_prefix"]["mean_regret_dol"],
                   None if cand.get("missing") else cand["lens2_n1000_prefix"]["mean_regret_dol"],
                   lambda v: f"{v:+,.0f}")
        if base.get("lens3_n1000_holdout") is not None:
            fmt_metric("Lens 3 match% (N=1000, HELD-OUT)",
                       base["lens3_n1000_holdout"]["match_pct"],
                       (None if cand.get("missing") else
                        cand["lens3_n1000_holdout"]["match_pct"]
                        if cand.get("lens3_n1000_holdout") is not None else None),
                       lambda v: f"{v:.2f}%")
            fmt_metric("Lens 3 $/1000h (N=1000, HELD-OUT)",
                       base["lens3_n1000_holdout"]["mean_regret_dol"],
                       (None if cand.get("missing") else
                        cand["lens3_n1000_holdout"]["mean_regret_dol"]
                        if cand.get("lens3_n1000_holdout") is not None else None),
                       lambda v: f"{v:+,.0f}")

    # Δ vs v44.
    if not base.get("missing") and not cand.get("missing"):
        print("\n  Δ v49_a2_dt vs v44_dt:", flush=True)
        d_m1 = (cand["lens1_n200_full"]["match_pct"]
                - base["lens1_n200_full"]["match_pct"])
        d_r1 = (cand["lens1_n200_full"]["mean_regret_dol"]
                - base["lens1_n200_full"]["mean_regret_dol"])
        d_m2 = (cand["lens2_n1000_prefix"]["match_pct"]
                - base["lens2_n1000_prefix"]["match_pct"])
        d_r2 = (cand["lens2_n1000_prefix"]["mean_regret_dol"]
                - base["lens2_n1000_prefix"]["mean_regret_dol"])
        print(f"    Lens 1 Δmatch%={d_m1:+.2f}pp  "
              f"Δ$/1000h={d_r1:+,.0f}", flush=True)
        print(f"    Lens 2 Δmatch%={d_m2:+.2f}pp  "
              f"Δ$/1000h={d_r2:+,.0f}", flush=True)
        if (base.get("lens3_n1000_holdout") is not None
                and cand.get("lens3_n1000_holdout") is not None):
            d_m3 = (cand["lens3_n1000_holdout"]["match_pct"]
                    - base["lens3_n1000_holdout"]["match_pct"])
            d_r3 = (cand["lens3_n1000_holdout"]["mean_regret_dol"]
                    - base["lens3_n1000_holdout"]["mean_regret_dol"])
            print(f"    Lens 3 Δmatch%={d_m3:+.2f}pp  "
                  f"Δ$/1000h={d_r3:+,.0f}    "
                  f"<<< OUT-OF-SAMPLE LIFT", flush=True)

    # SHIP VERDICT.
    print("\n" + "=" * 100, flush=True)
    print("PRE-COMMITTED SHIP VERDICT", flush=True)
    print("=" * 100, flush=True)
    print(f"  SHIP rule:  Lens 3 match% ≥ {SHIP_HOLDOUT_MATCH_MIN:.1f}%  "
          f"AND  |Lens 1 $/1000h(v49_a2) − Lens 1 $/1000h(v44)| ≤ "
          f"${SHIP_N200_REGRET_TOL_USD:.0f}", flush=True)
    print(f"  NULL rule:  Lens 3 match% < {NULL_HOLDOUT_MATCH_MAX:.1f}%",
          flush=True)
    print(f"  MIXED:      everything in between → reassess alongside A3",
          flush=True)
    verdict = "UNDETERMINED"
    verdict_reason = ""
    if (base.get("missing") or cand.get("missing")
            or cand.get("lens3_n1000_holdout") is None):
        verdict = "UNDETERMINED"
        verdict_reason = "v49_a2 model or S81 grid missing"
    else:
        l3 = cand["lens3_n1000_holdout"]["match_pct"]
        d_r1 = (cand["lens1_n200_full"]["mean_regret_dol"]
                - base["lens1_n200_full"]["mean_regret_dol"])
        if l3 < NULL_HOLDOUT_MATCH_MAX:
            verdict = "NULL"
            verdict_reason = (
                f"Lens 3 match% {l3:.2f}% < {NULL_HOLDOUT_MATCH_MAX:.1f}% — "
                f"held-out lift insufficient; S80's in-sample 80.19% was "
                f"largely memorization."
            )
        elif l3 >= SHIP_HOLDOUT_MATCH_MIN and abs(d_r1) <= SHIP_N200_REGRET_TOL_USD:
            verdict = "SHIP"
            verdict_reason = (
                f"Lens 3 match% {l3:.2f}% ≥ {SHIP_HOLDOUT_MATCH_MIN:.1f}% "
                f"AND Lens 1 regret Δ {d_r1:+,.0f} within "
                f"${SHIP_N200_REGRET_TOL_USD:.0f} of v44 — both ship gates pass."
            )
        else:
            verdict = "MIXED"
            if l3 < SHIP_HOLDOUT_MATCH_MIN:
                verdict_reason = (
                    f"Lens 3 match% {l3:.2f}% in MIXED zone "
                    f"({NULL_HOLDOUT_MATCH_MAX:.1f}%-{SHIP_HOLDOUT_MATCH_MIN:.1f}%); "
                    f"OOS lift exists but below ship threshold."
                )
            else:
                verdict_reason = (
                    f"Lens 3 match% {l3:.2f}% clears OOS gate but "
                    f"Lens 1 regret Δ {d_r1:+,.0f} exceeds "
                    f"${SHIP_N200_REGRET_TOL_USD:.0f} tolerance — "
                    f"production-baseline cost too high."
                )
    print(f"\n  >>> VERDICT: {verdict}", flush=True)
    print(f"      {verdict_reason}", flush=True)

    # JSON summary.
    summary = {
        "schema_version": 1,
        "session": 81,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_full": int(n),
        "n_prefix": int(n_prefix),
        "n_holdout": int(n_holdout),
        "ship_rules": {
            "ship_holdout_match_min_pct": SHIP_HOLDOUT_MATCH_MIN,
            "ship_n200_regret_tol_dol": SHIP_N200_REGRET_TOL_USD,
            "null_holdout_match_max_pct": NULL_HOLDOUT_MATCH_MAX,
        },
        "verdict": verdict,
        "verdict_reason": verdict_reason,
        "models": {
            name: {k: v for k, v in r.items() if not k.startswith("_")}
            for name, r in results.items()
        },
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\n  wrote summary JSON: {OUT_JSON}", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
