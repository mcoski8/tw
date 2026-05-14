#!/usr/bin/env python3
"""Session 80 — Grade v44_dt (baseline), v49_a1_dt (label-noise lever),
v49_c2_dt (memorization lever) against BOTH oracle grids:

  - oracle_grid_full_realistic_n200.bin   (N=200 labels, 6M rows)
  - oracle_grid_prefix500k_n1000.bin      (N=1000 labels, first 500K rows)

For each model, computes:
  * Match rate vs N=200 (production-baseline lens, full 6M)
  * Match rate vs N=1000 (S79 load-bearing lens, prefix 500K)
  * Mean regret vs N=200 ($/1000h on full grid)
  * Mean regret vs N=1000 ($/1000h on prefix grid)

Decomposes match-rate vs N=1000 by:
  * Setting-rank bucket (S76 lens; rank computed against N=200 oracle)
  * Hand category (S79 lens)

Builds X once via train_v44_dt.build_X (shared feature pipeline — v49_a1
and v49_c2 train on the same 107 features).  Walks each tree vectorized
in numpy and reads only leaf argmax indices, avoiding the 2.5 GB cost of
materializing per-hand 105-dim EV predictions.

Output:
  - stdout 3-column comparison table.
  - data/session80/grade_v49_experiments_summary.json
  - data/session80/grade_v49_experiments_full.log (when run via tee)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v49_experiments.py
"""
from __future__ import annotations

import argparse
import json
import sys
import time
from collections import Counter, defaultdict
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
GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
OUT_DIR = ROOT / "data" / "session80"
OUT_JSON = OUT_DIR / "grade_v49_experiments_summary.json"

EV_TO_DOLLARS = 10.0
BUCKETS_ORDER = ["MATCH", "NOISE", "MID", "STRUCTURE"]

MODEL_PATHS = {
    "v44_dt":     ROOT / "data" / "v44_dt_model.npz",
    "v49_a1_dt":  ROOT / "data" / "v49_a1_dt_model.npz",
    "v49_c2_dt":  ROOT / "data" / "v49_c2_dt_model.npz",
}


def rank_bucket(rank: int) -> str:
    """S76 convention. rank==1 means strategy == oracle argmax."""
    if rank == 1:
        return "MATCH"
    if rank <= 3:
        return "NOISE"
    if rank <= 9:
        return "MID"
    return "STRUCTURE"


def load_model_arrays(path: Path) -> dict:
    arr = np.load(path, allow_pickle=True)
    val = arr["leaf_values"]            # (n_nodes, 105) float32
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
    """For each row in X, walk the tree to a leaf and return that leaf's
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
        # X is int16 — cast row values to float for compare against threshold.
        x_vals = X[idx, feat_at].astype(np.float64, copy=False)
        thr_at = thr[node_at]
        go_left = x_vals <= thr_at
        nodes[idx] = np.where(go_left, cl[node_at], cr[node_at])
        iters += 1
        if iters > max_iters:
            raise RuntimeError(f"tree walk did not converge after {iters} iterations")
    return leaf_argmax[nodes]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--full-only", action="store_true",
                    help="Skip N=1000 prefix metrics (quick smoke test).")
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 100, flush=True)
    print("Session 80 — Grade v49 experiments (M2 plan)", flush=True)
    print("=" * 100, flush=True)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/6] building X (shared 107-feature pipeline) ...", flush=True)
    t0 = time.time()
    X, n = build_X()
    print(f"  X={X.shape}  built in {time.time()-t0:.1f}s", flush=True)

    print("\n[2/6] loading N=200 full grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    full_evs = np.asarray(gf.evs[:n], dtype=np.float64)
    print(f"  full grid: {full_evs.shape}  samples={gf.header.samples}", flush=True)
    n200_argmax = full_evs.argmax(axis=1).astype(np.int16)
    n200_max_ev = full_evs.max(axis=1)

    if not args.full_only:
        print("\n[3/6] loading N=1000 prefix grid ...", flush=True)
        gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
        n_prefix = len(gp)
        # Verify alignment.
        ids_p = np.asarray(gp.canonical_ids[:1000], dtype=np.uint32)
        ids_f = np.asarray(gf.canonical_ids[:1000], dtype=np.uint32)
        if not np.array_equal(ids_p, ids_f):
            print("ERROR: prefix and full canonical_ids disagree.", flush=True)
            return 1
        prefix_evs = np.asarray(gp.evs[:n_prefix], dtype=np.float64)
        print(f"  prefix grid: {prefix_evs.shape}  samples={gp.header.samples}",
              flush=True)
        n1000_argmax = prefix_evs.argmax(axis=1).astype(np.int16)
        n1000_max_ev = prefix_evs.max(axis=1)

        # Oracle self-agreement (sanity vs S79).
        oracle_self_match_pct = float(
            (n200_argmax[:n_prefix] == n1000_argmax).mean()
        ) * 100.0
        print(f"  oracle self-agreement (N=200 argmax == N=1000 argmax) = "
              f"{oracle_self_match_pct:.2f}%   (S79 reported 68.00%)", flush=True)
    else:
        n_prefix = 0
        prefix_evs = None
        n1000_argmax = None
        n1000_max_ev = None
        oracle_self_match_pct = None

    print("\n[4/6] loading canonical hands + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    if len(ch) < n:
        print(f"ERROR: canonical hands ({len(ch)}) < n ({n}).", flush=True)
        return 1
    cats = categorize_hands(np.asarray(ch.hands[:n]))
    cat_counts = Counter(int(c) for c in cats)
    print(f"  categorized {n:,} hands.", flush=True)
    for code in range(8):
        print(f"    cat {code} {CATEGORY_NAMES[code]:<12} n={cat_counts.get(code, 0):,}",
              flush=True)

    # ---------------------------------------------------------------
    # PER-MODEL PREDICTIONS
    # ---------------------------------------------------------------
    results = {}  # name -> dict of metrics
    for name, mp in MODEL_PATHS.items():
        if not mp.exists():
            print(f"  SKIP {name}: model file not found at {mp}", flush=True)
            results[name] = {"missing": True}
            continue
        print(f"\n[5/6] grading {name} ...", flush=True)
        t0 = time.time()
        m = load_model_arrays(mp)
        print(f"  loaded {mp.name}  leaves={m['n_leaves']:,}  depth={m['depth']}  "
              f"in {time.time()-t0:.1f}s", flush=True)

        t0 = time.time()
        picks = vectorized_predict(X, m)
        print(f"  predicted {n:,} hands in {time.time()-t0:.1f}s "
              f"({n/(time.time()-t0):.0f} hands/s)", flush=True)

        # vs N=200 (full grid)
        n200_match = (picks == n200_argmax)
        chosen_ev_n200 = full_evs[np.arange(n), picks]
        regret_n200 = (n200_max_ev - chosen_ev_n200).astype(np.float64)
        m_pct_n200 = 100.0 * n200_match.mean()
        regret_dol_n200 = float(regret_n200.mean()) * EV_TO_DOLLARS * 1000

        if n_prefix > 0:
            picks_prefix = picks[:n_prefix]
            n1000_match = (picks_prefix == n1000_argmax)
            chosen_ev_n1000 = prefix_evs[np.arange(n_prefix), picks_prefix]
            regret_n1000 = (n1000_max_ev - chosen_ev_n1000).astype(np.float64)
            m_pct_n1000 = 100.0 * n1000_match.mean()
            regret_dol_n1000 = float(regret_n1000.mean()) * EV_TO_DOLLARS * 1000
        else:
            n1000_match = None
            regret_n1000 = None
            m_pct_n1000 = None
            regret_dol_n1000 = None

        results[name] = {
            "n_leaves": m["n_leaves"],
            "depth": m["depth"],
            "picks": picks,                       # (n,) int16
            "n200_match": n200_match,             # (n,) bool
            "regret_n200": regret_n200,           # (n,) float64 (raw EV)
            "match_pct_n200": m_pct_n200,
            "regret_dol_n200": regret_dol_n200,
            "n1000_match": n1000_match,
            "regret_n1000": regret_n1000,
            "match_pct_n1000": m_pct_n1000,
            "regret_dol_n1000": regret_dol_n1000,
        }

        print(f"  match%(N=200)={m_pct_n200:6.2f}%  "
              f"$/1000h(N=200)={regret_dol_n200:>+8,.0f}", flush=True)
        if n_prefix > 0:
            print(f"  match%(N=1000)={m_pct_n1000:6.2f}%  "
                  f"$/1000h(N=1000)={regret_dol_n1000:>+8,.0f}", flush=True)

    # ---------------------------------------------------------------
    # 3-COLUMN HEADLINE TABLE
    # ---------------------------------------------------------------
    print("\n" + "=" * 100, flush=True)
    print("HEADLINE — 3-column comparison", flush=True)
    print("=" * 100, flush=True)
    header = f"  {'metric':<32}"
    for name in MODEL_PATHS:
        header += f"{name:>14}"
    print(header, flush=True)
    print("  " + "-" * (32 + 14 * len(MODEL_PATHS)), flush=True)

    def row(label, getter, fmt):
        line = f"  {label:<32}"
        for name in MODEL_PATHS:
            r = results.get(name, {})
            if r.get("missing"):
                line += f"{'MISSING':>14}"
                continue
            v = getter(r)
            line += fmt(v).rjust(14) if v is not None else f"{'-':>14}"
        return line

    print(row("n_leaves", lambda r: r.get("n_leaves"),
              lambda v: f"{v:,}"), flush=True)
    print(row("depth", lambda r: r.get("depth"),
              lambda v: str(v)), flush=True)
    print(row("match% (N=200, full 6M)", lambda r: r.get("match_pct_n200"),
              lambda v: f"{v:.2f}%"), flush=True)
    print(row("match% (N=1000, prefix 500K)", lambda r: r.get("match_pct_n1000"),
              lambda v: f"{v:.2f}%"), flush=True)
    print(row("regret $/1000h (N=200)", lambda r: r.get("regret_dol_n200"),
              lambda v: f"{v:+,.0f}"), flush=True)
    print(row("regret $/1000h (N=1000)", lambda r: r.get("regret_dol_n1000"),
              lambda v: f"{v:+,.0f}"), flush=True)

    # Δ vs v44 baseline
    base = results.get("v44_dt", {})
    if not base.get("missing") and n_prefix > 0:
        print("\n  Δ vs v44_dt baseline:", flush=True)
        for name in ("v49_a1_dt", "v49_c2_dt"):
            r = results.get(name, {})
            if r.get("missing"):
                print(f"    {name}: MISSING", flush=True)
                continue
            d_match_n200 = r["match_pct_n200"] - base["match_pct_n200"]
            d_match_n1000 = r["match_pct_n1000"] - base["match_pct_n1000"]
            d_reg_n200 = r["regret_dol_n200"] - base["regret_dol_n200"]
            d_reg_n1000 = r["regret_dol_n1000"] - base["regret_dol_n1000"]
            print(f"    {name:<12}  "
                  f"Δmatch%(N=200)={d_match_n200:+.2f}pp  "
                  f"Δmatch%(N=1000)={d_match_n1000:+.2f}pp  "
                  f"Δ$/1000h(N=200)={d_reg_n200:+,.0f}  "
                  f"Δ$/1000h(N=1000)={d_reg_n1000:+,.0f}", flush=True)

    # ---------------------------------------------------------------
    # BUCKET DECOMPOSITION (S76 lens; rank computed against N=200 on prefix)
    # ---------------------------------------------------------------
    bucket_summary = {}
    if n_prefix > 0:
        print("\n" + "=" * 100, flush=True)
        print("BUCKET DECOMPOSITION on PREFIX 500K", flush=True)
        print("(rank computed against N=200 oracle, lens of S76; uses v44's pick "
              "to define each row's bucket)", flush=True)
        print("=" * 100, flush=True)

        # Compute v44's rank vs N=200 on each prefix row.
        v44_picks = results["v44_dt"]["picks"][:n_prefix]
        v44_ev_n200 = full_evs[:n_prefix][np.arange(n_prefix), v44_picks]
        # rank: number of settings with strictly higher EV + 1.
        v44_rank_n200 = (full_evs[:n_prefix] > v44_ev_n200[:, None]).sum(axis=1) + 1

        bucket_idx = np.full(n_prefix, -1, dtype=np.int8)
        for i, b in enumerate(BUCKETS_ORDER):
            if b == "MATCH":
                mask = v44_rank_n200 == 1
            elif b == "NOISE":
                mask = (v44_rank_n200 >= 2) & (v44_rank_n200 <= 3)
            elif b == "MID":
                mask = (v44_rank_n200 >= 4) & (v44_rank_n200 <= 9)
            else:  # STRUCTURE
                mask = v44_rank_n200 >= 10
            bucket_idx[mask] = i

        # Header
        head = f"  {'bucket':<11}{'n':>9}{'pct':>7}"
        for name in MODEL_PATHS:
            head += f"{name + ' m%(N=200)':>22}"
            head += f"{name + ' m%(N=1000)':>23}"
        print(head, flush=True)

        for i, b in enumerate(BUCKETS_ORDER):
            mask = bucket_idx == i
            n_b = int(mask.sum())
            if n_b == 0:
                continue
            pct = 100.0 * n_b / n_prefix
            line = f"  {b:<11}{n_b:>9,}{pct:>6.1f}%"
            bucket_summary[b] = {"n": n_b, "pct_share": pct, "models": {}}
            for name in MODEL_PATHS:
                r = results.get(name, {})
                if r.get("missing"):
                    line += f"{'MISSING':>22}{'MISSING':>23}"
                    continue
                # m%(N=200) restricted to PREFIX rows in this bucket
                m200 = 100.0 * r["n200_match"][:n_prefix][mask].mean()
                m1000 = 100.0 * r["n1000_match"][mask].mean()
                line += f"{m200:>21.2f}%"
                line += f"{m1000:>22.2f}%"
                bucket_summary[b]["models"][name] = {
                    "match_pct_n200": m200,
                    "match_pct_n1000": m1000,
                }
            print(line, flush=True)

    # ---------------------------------------------------------------
    # CATEGORY DECOMPOSITION (S79 lens; on prefix subset for N=1000)
    # ---------------------------------------------------------------
    category_summary = {}
    if n_prefix > 0:
        print("\n" + "=" * 100, flush=True)
        print("CATEGORY DECOMPOSITION on PREFIX 500K", flush=True)
        print("=" * 100, flush=True)

        cats_prefix = cats[:n_prefix]
        head = f"  {'category':<12}{'n':>9}{'pct':>7}"
        for name in MODEL_PATHS:
            head += f"{name + ' m%(N=200)':>22}"
            head += f"{name + ' m%(N=1000)':>23}"
        print(head, flush=True)
        for code in range(8):
            mask = cats_prefix == code
            n_c = int(mask.sum())
            if n_c == 0:
                continue
            pct = 100.0 * n_c / n_prefix
            cname = CATEGORY_NAMES[code]
            line = f"  {cname:<12}{n_c:>9,}{pct:>6.1f}%"
            category_summary[cname] = {"n": n_c, "pct_share": pct, "models": {}}
            for name in MODEL_PATHS:
                r = results.get(name, {})
                if r.get("missing"):
                    line += f"{'MISSING':>22}{'MISSING':>23}"
                    continue
                m200 = 100.0 * r["n200_match"][:n_prefix][mask].mean()
                m1000 = 100.0 * r["n1000_match"][mask].mean()
                line += f"{m200:>21.2f}%"
                line += f"{m1000:>22.2f}%"
                category_summary[cname]["models"][name] = {
                    "match_pct_n200": m200,
                    "match_pct_n1000": m1000,
                }
            print(line, flush=True)

    # ---------------------------------------------------------------
    # PER-CATEGORY SHIFTS — focus the lens on two_pair / trips_pair
    # (the most-overfit categories per S79)
    # ---------------------------------------------------------------
    if n_prefix > 0 and not base.get("missing"):
        print("\n" + "=" * 100, flush=True)
        print("PER-CATEGORY shift vs v44 baseline (N=1000 prefix match%)", flush=True)
        print("=" * 100, flush=True)
        for cname, cs in category_summary.items():
            base_m1000 = cs["models"].get("v44_dt", {}).get("match_pct_n1000")
            if base_m1000 is None:
                continue
            for name in ("v49_a1_dt", "v49_c2_dt"):
                m1000 = cs["models"].get(name, {}).get("match_pct_n1000")
                if m1000 is None:
                    continue
                d = m1000 - base_m1000
                marker = "  ***" if abs(d) >= 1.0 else ""
                print(f"  {cname:<12}  {name:<12}  {d:+6.2f}pp"
                      f"   (v44 {base_m1000:.2f}% → {m1000:.2f}%){marker}",
                      flush=True)

    # ---------------------------------------------------------------
    # SAVE JSON SUMMARY
    # ---------------------------------------------------------------
    summary = {
        "schema_version": 1,
        "session": 80,
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "n_full": n,
        "n_prefix": n_prefix,
        "oracle_self_match_pct": oracle_self_match_pct,
        "models": {
            name: {
                k: v for k, v in r.items()
                if k not in ("picks", "n200_match", "n1000_match",
                             "regret_n200", "regret_n1000")
            }
            for name, r in results.items()
        },
        "bucket_decomposition": bucket_summary,
        "category_decomposition": category_summary,
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\n  wrote summary JSON: {OUT_JSON}", flush=True)

    # ---------------------------------------------------------------
    # DECISION MATRIX (PRE-COMMITTED IN S79 / DECISION 114)
    # ---------------------------------------------------------------
    if n_prefix > 0 and not base.get("missing"):
        print("\n" + "=" * 100, flush=True)
        print("DECISION MATRIX (pre-committed in CURRENT_PHASE S80, Phase 5)", flush=True)
        print("=" * 100, flush=True)
        threshold = 70.0  # ≥ +3pp above v44's 67.05%
        print(f"  Threshold for 'lifts': N=1000 match rate ≥ {threshold:.2f}%", flush=True)
        print(f"  v44 baseline: {base['match_pct_n1000']:.2f}%", flush=True)
        for name in ("v49_a1_dt", "v49_c2_dt"):
            r = results.get(name, {})
            if r.get("missing"):
                print(f"    {name}: MISSING — cannot evaluate.", flush=True)
                continue
            v = r["match_pct_n1000"]
            verdict = "LIFTS" if v >= threshold else "NO LIFT"
            print(f"    {name}: {v:.2f}% → {verdict}", flush=True)
        a1_lifts = (results.get("v49_a1_dt", {}).get("match_pct_n1000") or 0) >= threshold
        c2_lifts = (results.get("v49_c2_dt", {}).get("match_pct_n1000") or 0) >= threshold
        print()
        if a1_lifts and c2_lifts:
            print("  >>> VERDICT: BOTH lift. S81 = M1 hybrid (regularized DT on N=1000 labels).", flush=True)
        elif a1_lifts and not c2_lifts:
            print("  >>> VERDICT: Only A1 lifts. S81 = A2 (targeted N=1000 expansion on two_pair + trips_pair).", flush=True)
        elif c2_lifts and not a1_lifts:
            print("  >>> VERDICT: Only C2 lifts. S81 = C1 (high-capacity well-regularized boosting at depth=10-12, n_est=1000-2000).", flush=True)
        else:
            print("  >>> VERDICT: Neither lifts. Headline-goal recalibration required — surface to user.", flush=True)
            print(f"      32% oracle self-disagreement may imply 95% match rate is unattainable against any noisy oracle.", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
