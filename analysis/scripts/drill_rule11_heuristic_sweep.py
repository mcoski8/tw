"""
Session 47 — Drill E: Rule 11 heuristic variant sweep.

v42 (Rule 11) captures 56% of the A5 oracle ceiling at J-pair-J. The gap
(+$1,664/1000h within fires; +$5/1000h whole-grid full) is heuristic-vs-
oracle. This drill sweeps tie-break variants to find the best within-fires
heuristic.

Variants tested per fire (J-pair-J AND DS-achievable):

  V_LOLO  : LOW pair → bot,  LOW top  (v42 current)
  V_LOMID : LOW pair → bot,  MID top
  V_LOHI  : LOW pair → bot,  HIGH top
  V_HILO  : HIGH pair → bot, LOW top
  V_HIMID : HIGH pair → bot, MID top
  V_HIHI  : HIGH pair → bot, HIGH top

Where:
  - LOW pair = pick the 2 lowest-rank singletons that complete DS bot
  - HIGH pair = pick the 2 highest-rank singletons that complete DS bot
  - LOW/MID/HIGH top = lowest / middle / highest of the 3 remaining
                       singletons (after pair-bot pick)

For Case A (J's same-suit X), we also pick which non-X suit Y to use.
Default: prefer the Y with the lowest-rank pair available (for V_LO*) or
highest-rank pair available (for V_HI*).

Reports per variant:
  - n fires (should be the same across variants — DS achievability gates fires)
  - mean lift vs v41 production pick (within-hand, full grid)
  - mean lift vs v42 (within-hand, full grid)
  - mean residual gap to A5 oracle (within-hand, full grid)
  - whole-grid full lift (extrapolated)

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_rule11_heuristic_sweep.py
"""
from __future__ import annotations

import argparse
import sys
import time
from itertools import combinations
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
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SUIT_PROFILE_DS,
)
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v41_rule10_v3_ds import strategy_v41_rule10_v3_ds  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
P_J = 11

VARIANTS = ["V_LOLO", "V_LOMID", "V_LOHI",
            "V_HILO", "V_HIMID", "V_HIHI"]


def _enumerate_DS_pair_bot_settings(hand: np.ndarray):
    """Return list of (pair_singletons, top_pos, mid_a, mid_b, setting_idx,
    pair_rank_sum, top_rank) for every (sing_a, sing_b, top_pos) combination
    such that pair-bot + DS holds. Used to find LOW/HIGH/MID variants.
    """
    h = np.asarray(hand, dtype=np.uint8)
    ranks = (h // 4) + 2
    suits = h & 3
    pair_pos = sorted(j for j in range(7) if int(ranks[j]) == P_J)
    sing_pos_all = [j for j in range(7) if int(ranks[j]) != P_J]

    j_suit_a = int(suits[pair_pos[0]])
    j_suit_b = int(suits[pair_pos[1]])

    out = []
    # Enumerate all 2-subsets of singletons for bot
    for sa, sb in combinations(sing_pos_all, 2):
        # Check DS: bot suits = J_a + J_b + sa + sb must form 2+2
        bot_suits = [j_suit_a, j_suit_b, int(suits[sa]), int(suits[sb])]
        cnt = np.bincount(bot_suits, minlength=4)
        if not (np.sort(cnt)[-2:] == [2, 2]).all():
            continue

        bot_sings = [sa, sb]
        remaining = [j for j in sing_pos_all if j not in (sa, sb)]
        # remaining has 3 singletons. Try each as TOP.
        for top_pos in remaining:
            mid_pair = sorted(j for j in remaining if j != top_pos)
            setting_idx = _setting_index_from_tmb(top_pos, mid_pair[0], mid_pair[1])
            out.append({
                "pair_sings": tuple(sorted(bot_sings)),
                "top_pos": top_pos,
                "mid": mid_pair,
                "idx": setting_idx,
                "pair_rank_sum": int(ranks[sa]) + int(ranks[sb]),
                "top_rank": int(ranks[top_pos]),
            })
    return out


def _pick_variant(settings: list[dict], variant: str) -> int:
    """Pick the setting per variant. Returns setting index, or -1 if none.

    Variant decoding:
      V_{PAIR}{TOP}
      PAIR ∈ {LO, HI} : low-rank pair-sings vs high-rank pair-sings for bot
      TOP  ∈ {LO, MID, HI} : low / middle / high top among the 3 remaining
    """
    if not settings:
        return -1
    pair_pref = variant[2:4]
    top_pref = variant[4:]

    # 1. Group by pair_sings
    pair_groups = {}
    for s in settings:
        key = s["pair_sings"]
        pair_groups.setdefault(key, []).append(s)
    # Pick the pair-sings group with lowest or highest pair_rank_sum
    keys = list(pair_groups.keys())
    if pair_pref == "LO":
        keys.sort(key=lambda k: pair_groups[k][0]["pair_rank_sum"])
    elif pair_pref == "HI":
        keys.sort(key=lambda k: -pair_groups[k][0]["pair_rank_sum"])
    chosen_pair = keys[0]
    candidates = pair_groups[chosen_pair]

    # 2. Among candidates (which differ only by top_pos), pick by top rank
    candidates_sorted = sorted(candidates, key=lambda s: s["top_rank"])
    if top_pref == "LO":
        return candidates_sorted[0]["idx"]
    elif top_pref == "MID":
        # 3 candidates; middle one
        return candidates_sorted[1]["idx"]
    elif top_pref == "HI":
        return candidates_sorted[-1]["idx"]
    return -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 47 Drill E: Rule 11 heuristic variant sweep")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    pair_idx = np.where(cats == 1)[0]

    print("\n[2/4] filtering to J-pair-J (P=11 AND max=11) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    for cid in pair_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) != 11:
            continue
        rc = np.bincount(ranks, minlength=15)
        P = next(r for r in range(2, 15) if rc[r] == 2)
        if P != 11:
            continue
        scope_cids.append(int(cid))
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    print(f"  scope: {len(scope_cids):,}")
    print(f"  done in {time.time()-t0:.1f}s")

    if args.sample > 0 and len(scope_cids) > args.sample:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(scope_cids), size=args.sample, replace=False)
        scope_cids = scope_cids[np.sort(idx)]
        print(f"  [sample mode: {args.sample:,}]")

    print("\n[3/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    # Per-variant accumulators
    sum_ev_full = {v: 0.0 for v in VARIANTS}
    n_fires = {v: 0 for v in VARIANTS}
    sum_ev_v41 = 0.0
    n_v41_recorded = 0
    sum_ev_a5_oracle = 0.0
    n_a5_recorded = 0

    # Track when a variant pick equals A5-oracle (perfect capture)
    n_perfect = {v: 0 for v in VARIANTS}

    print("\n[4/4] per-hand variant evaluation ...", flush=True)
    t0 = time.time()
    n_total = len(scope_cids)
    n_fired_overall = 0
    for i in range(n_total):
        cid = int(scope_cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        settings = _enumerate_DS_pair_bot_settings(h)
        if not settings:
            continue  # Rule 11 doesn't fire
        n_fired_overall += 1

        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        v41_ev = float(rowf[strategy_v41_rule10_v3_ds(h)])

        # A5 oracle: best EV among all DS pair-bot settings
        a5_oracle_ev = max(float(rowf[s["idx"]]) for s in settings)

        sum_ev_v41 += v41_ev
        n_v41_recorded += 1
        sum_ev_a5_oracle += a5_oracle_ev
        n_a5_recorded += 1

        for variant in VARIANTS:
            idx = _pick_variant(settings, variant)
            if idx < 0:
                continue
            ev = float(rowf[idx])
            sum_ev_full[variant] += ev
            n_fires[variant] += 1
            if abs(ev - a5_oracle_ev) < 1e-9:
                n_perfect[variant] += 1

        if (i + 1) % 5000 == 0:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>7,}/{n_total:,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.")
    print(f"  n_fires: {n_fired_overall:,} ({100*n_fired_overall/n_total:.1f}% of J-pair-J)\n")

    # ── Reporting ──
    print("=" * 100)
    print(f"VARIANT COMPARISON (within-hand, full grid)")
    print("=" * 100)
    n_total_grid = 6_009_159  # for whole-grid extrapolation
    grid_share = n_fired_overall / n_total_grid

    if n_v41_recorded == 0:
        print("(no fires)")
        return 0

    mean_v41 = sum_ev_v41 / n_v41_recorded
    mean_a5_oracle = sum_ev_a5_oracle / n_a5_recorded
    a5_lift = (mean_a5_oracle - mean_v41) * EV_TO_DOL * 1000

    print(f"\n  v41 mean EV per fire     : ${mean_v41 * EV_TO_DOL:>+10.2f}")
    print(f"  A5 oracle mean EV per fire: ${mean_a5_oracle * EV_TO_DOL:>+10.2f}")
    print(f"  A5 oracle lift vs v41    : ${a5_lift:>+10.1f}/1000h within fires")
    print(f"  → A5 oracle whole-grid full lift ceiling: "
          f"${a5_lift * grid_share:>+8.2f}/1000h (across {n_fired_overall:,} hands)")

    print(f"\n  {'variant':<10} {'fires':>7} {'perfect%':>9} "
          f"{'mean_EV':>11} {'lift_vs_v41':>14} {'whole_grid':>12} {'gap_to_A5':>12}")
    print("-" * 80)
    for v in VARIANTS:
        if n_fires[v] == 0:
            continue
        mean_ev = sum_ev_full[v] / n_fires[v]
        lift = (mean_ev - mean_v41) * EV_TO_DOL * 1000
        wg_lift = lift * grid_share
        gap = (mean_a5_oracle - mean_ev) * EV_TO_DOL * 1000
        perfect_pct = 100 * n_perfect[v] / n_fires[v]
        print(f"  {v:<10} {n_fires[v]:>7,} {perfect_pct:>8.1f}% "
              f"${mean_ev * EV_TO_DOL:>+9.2f} ${lift:>+11.1f} "
              f"${wg_lift:>+10.2f} ${gap:>+10.1f}")

    print(f"\n  v42 (current production) is V_LOLO.  Whole-grid lift cap ≈ "
          f"${a5_lift * grid_share:.2f}/1000h.")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
