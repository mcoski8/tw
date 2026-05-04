"""
Session 31 — composite category deep-dive on v20.

The "composite" category in `grade_strategy.categorize_hands` is the
catch-all bucket for rare 7-card combinations: quads+pair, quads+trip,
two_trips, trips+two_pair. v20 has the **largest per-hand bleed** here
($2,100/1000h on N=200) despite the population being only ~14k of 6M
hands (0.2%). Adding a `composite_aug_gated` feature family is on the
Session 31 menu, so this probe asks: is composite a single residual or
several archetypes?

Pipeline:
  1. Run categorize_hands(canonical_hands) — composite is code 7.
  2. Sub-categorize by (n_quads, n_trips, n_pairs):
       (1, 0, 1) = quads + pair
       (1, 1, 0) = quads + trip
       (0, 2, 0) = two_trips
       (0, 1, 2) = trips + two_pair
       other     = leftover
  3. Walk v20's tree to get chosen_idx; compute regret per hand.
  4. Per archetype: count, mean v20 regret, mean oracle EV, top-3 v20
     and oracle settings (mode of chosen indices).
  5. Spot-check 5 worst-regret hands per archetype: print hand string +
     v20 setting + oracle setting.

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/composite_v20_residual.py
"""
from __future__ import annotations

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
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from probe_v20_high_only_routing import (  # noqa: E402
    build_column_data,
    build_X_for_columns,
    load_model,
    walk_to_leaf,
)
from high_only_v16_residual import setting_str  # noqa: E402

V20_PATH = ROOT / "data" / "v20_dt_model.npz"
GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"


def archetype_label(n_quads: int, n_trips: int, n_pairs: int) -> str:
    if n_quads == 1 and n_pairs == 1 and n_trips == 0:
        return "quads_pair"
    if n_quads == 1 and n_trips == 1 and n_pairs == 0:
        return "quads_trip"
    if n_quads == 0 and n_trips == 2 and n_pairs == 0:
        return "two_trips"
    if n_quads == 0 and n_trips == 1 and n_pairs == 2:
        return "trips_two_pair"
    if n_quads == 1 and n_pairs >= 1:
        return "quads_other"
    return "other_composite"


def main() -> int:
    print("loading column data + v20 model ...", flush=True)
    cd, n = build_column_data()
    v20 = load_model(V20_PATH)
    X20 = build_X_for_columns(cd, v20["feature_columns"])

    print("walking v20 tree ...", flush=True)
    t0 = time.time()
    leaf20 = walk_to_leaf(X20, v20)
    chosen20 = v20["leaf_values"][leaf20].argmax(axis=1).astype(np.int16)
    print(f"  walk + argmax: {time.time()-t0:.1f}s", flush=True)

    print("loading oracle grid + canonical hands ...", flush=True)
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    Y = np.asarray(grid.evs[:n])
    hands = np.asarray(ch.hands[:n])
    rows = np.arange(n)
    oracle_idx = Y.argmax(axis=1).astype(np.int16)
    ev_oracle = Y[rows, oracle_idx]
    ev20 = Y[rows, chosen20]
    regret = (ev_oracle - ev20).astype(np.float32)

    cats = categorize_hands(np.asarray(hands, dtype=np.uint8))
    composite = (cats == 7)
    n_comp = int(composite.sum())
    comp_idx = np.where(composite)[0]
    print(f"\ncomposite category: {n_comp:,} hands ({n_comp / n * 100:.3f}% of all)", flush=True)
    print(f"  v20 mean regret on composite: {regret[composite].mean():.4f}  "
          f"≈ ${regret[composite].mean() * 10 * 1000:,.0f}/1000h", flush=True)

    # Sub-categorize.
    print("\nsub-categorizing composite by (n_quads, n_trips, n_pairs) ...", flush=True)
    nq = cd["n_quads"][composite]
    nt = cd["n_trips"][composite]
    np_ = cd["n_pairs"][composite]
    archetypes = np.array([archetype_label(int(nq[i]), int(nt[i]), int(np_[i]))
                           for i in range(n_comp)])

    print(f"\n{'archetype':<18}  {'count':>7}  {'mean_regret':>12}  {'$/1000h':>10}  "
          f"{'pct_optimal':>11}  {'share_of_comp%':>14}", flush=True)
    print("-" * 90, flush=True)
    archetype_counts = Counter(archetypes)
    archetype_data = {}
    for arche, cnt in archetype_counts.most_common():
        m_local = archetypes == arche
        glob_idx = comp_idx[m_local]
        reg_a = regret[glob_idx]
        n_a = cnt
        mr = reg_a.mean()
        share = n_a / n_comp * 100
        pct_opt = (reg_a == 0).mean() * 100
        archetype_data[arche] = {"glob_idx": glob_idx, "regret": reg_a,
                                  "count": n_a, "share": share}
        print(f"{arche:<18}  {n_a:>7,}  {mr:>12.4f}  "
              f"${mr * 10 * 1000:>8,.0f}  {pct_opt:>10.1f}%  {share:>13.1f}%", flush=True)

    # Per archetype, dump the top-3 v20 chosen settings and top-3 oracle settings.
    print(f"\n=== top settings per archetype ===", flush=True)
    for arche, data in archetype_data.items():
        gidx = data["glob_idx"]
        n_a = data["count"]
        if n_a < 50:
            continue
        v20_settings = chosen20[gidx]
        oracle_settings = oracle_idx[gidx]
        c20 = Counter(v20_settings.tolist()).most_common(3)
        cor = Counter(oracle_settings.tolist()).most_common(3)
        print(f"\n  {arche}  ({n_a:,} hands)", flush=True)
        print(f"    v20 top-3 settings: {[(s, f'{c/n_a*100:.1f}%') for s, c in c20]}",
              flush=True)
        print(f"    oracle top-3 settings: {[(s, f'{c/n_a*100:.1f}%') for s, c in cor]}",
              flush=True)
        # Spot-check 3 worst-regret hands per archetype.
        worst_local = np.argsort(-data["regret"])[:3]
        worst_global = gidx[worst_local]
        print(f"    worst-regret hands:", flush=True)
        for ri in worst_global:
            hb = np.asarray(hands[ri], dtype=np.uint8)
            v20_idx = int(chosen20[ri])
            ora_idx = int(oracle_idx[ri])
            print(f"      regret={regret[ri]:.3f}  v20:{setting_str(hb, v20_idx)}", flush=True)
            print(f"                       ora:{setting_str(hb, ora_idx)}", flush=True)

    return 0


if __name__ == "__main__":
    sys.exit(main())
