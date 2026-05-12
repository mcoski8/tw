"""
Session 60 — test_rule_catalog.py

Per-cell rule audit harness. Given a candidate rule_fn and a (max_rank, cell)
subset of high_only, score the rule against:
  - a baseline strategy (e.g., v52 or a predecessor rule chain)
  - v44_dt (the ML champion)
  - the oracle ceiling (best EV per hand from the realistic-mixture grid)

Reports within-cell and whole-grid lift in $/1000h, capture % against
both baseline and v44, and rule-vs-oracle mismatch detail.

Cell tagging is derived from data/drill_ho_v44_per_hand_structural.parquet
(Session 59 artifact). EVs come from data/oracle_grid_full_realistic_n200.bin.

Typical use:

    from test_rule_catalog import test_rule_on_cell

    res = test_rule_on_cell(
        rule_fn=strategy_v45_rule14_Ahigh_DS,
        max_rank=14,
        cell="DS_NO_JOINT",
        baseline_fn=strategy_v52_full_high_only_handler,
        label="rule14_audit",
    )
    res.print_summary()

The harness keeps a module-level data cache so the parquet, canonical hands,
and oracle grid are loaded once per process.

Sanity check helper at the bottom: reproduces Rule 14's known whole-grid lift
vs its pre-Rule-14 predecessor (v44_rule13).
"""
from __future__ import annotations

import sys
import time
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SETTING_HAND_INDICES,
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH,
)

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
PARQUET = ROOT / "data" / "drill_ho_v44_per_hand_structural.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

ALL_CELLS = ["JOINT_HIGH", "JOINT_MED", "JOINT_LOW",
             "DS_NO_JOINT", "DS_NO_MAXTOP", "MS_ONLY", "NEITHER"]

SUIT_LABELS = {
    SUIT_PROFILE_DS: "DS", SUIT_PROFILE_SS: "SS",
    SUIT_PROFILE_RAINBOW: "RB", SUIT_PROFILE_THREE_ONE: "31",
    SUIT_PROFILE_FOUR_FLUSH: "4f",
}


def vectorized_cells(df) -> np.ndarray:
    """Tag each parquet row with its structural cell (JOINT_HIGH/MED/LOW,
    DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, NEITHER) — same definition as
    drill_high_only_v44_deepdive.cell_for_hand."""
    n_joint = df["n_joint_DS_ms_max_top"].to_numpy()
    best_ms = df["best_ms_mid_high"].to_numpy()
    n_DS_top = df["n_DS_bot_with_max_top"].to_numpy()
    n_DS = df["n_DS_bot_configs"].to_numpy()
    n_ms_top = df["n_ms_mid_with_max_top"].to_numpy()
    cells = np.empty(len(df), dtype=object)
    j_mask = n_joint > 0
    cells[j_mask & (best_ms >= 11)] = "JOINT_HIGH"
    cells[j_mask & (best_ms >= 8) & (best_ms < 11)] = "JOINT_MED"
    cells[j_mask & (best_ms < 8)] = "JOINT_LOW"
    cells[(~j_mask) & (n_DS_top > 0)] = "DS_NO_JOINT"
    cells[(~j_mask) & (n_DS_top == 0) & (n_DS > 0)] = "DS_NO_MAXTOP"
    cells[(~j_mask) & (n_DS == 0) & (n_ms_top > 0)] = "MS_ONLY"
    cells[(~j_mask) & (n_DS == 0) & (n_ms_top == 0)] = "NEITHER"
    return cells


def classify_pick(hand_bytes, feats, idx: int) -> str:
    """Return a compact label for a chosen setting, like 'tA_DS_ms'."""
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = pos[1:3]
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    top_rank = int(ranks[top_pos])
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_lbl = "ms" if mid_suits[0] == mid_suits[1] else "mu"
    suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    return f"t{RANK_CHAR[top_rank]}_{suit_lbl}_{mid_lbl}"


@dataclass
class CatalogResult:
    label: str
    max_rank: int
    cell: str
    n_hands: int
    n_rule_fires: int

    rule_pct_optimal: float
    baseline_pct_optimal: float
    v44_pct_optimal: float

    rule_mean_ev: float
    baseline_mean_ev: float
    v44_mean_ev: float
    oracle_ceiling_ev: float

    capture_pct_vs_baseline: float
    capture_pct_vs_v44: float

    lift_vs_baseline_within_cell: float
    lift_vs_baseline_whole_grid: float
    lift_vs_v44_within_cell: float
    lift_vs_v44_whole_grid: float

    rule_vs_oracle_mismatch: list = field(default_factory=list)

    def print_summary(self) -> None:
        print(f"\n══ {self.label} ══")
        print(f"  max_rank={RANK_CHAR[self.max_rank]}  cell={self.cell}  n={self.n_hands:,}")
        fr_pct = 100 * self.n_rule_fires / max(self.n_hands, 1)
        print(f"  n_rule_fires={self.n_rule_fires:,} ({fr_pct:.1f}%)")
        print(f"  pct_optimal: rule={self.rule_pct_optimal:.2f}%  "
              f"baseline={self.baseline_pct_optimal:.2f}%  "
              f"v44={self.v44_pct_optimal:.2f}%")
        print(f"  mean_ev:     rule={self.rule_mean_ev:+.4f}  "
              f"baseline={self.baseline_mean_ev:+.4f}  "
              f"v44={self.v44_mean_ev:+.4f}  "
              f"oracle={self.oracle_ceiling_ev:+.4f}")
        gap_b = self.oracle_ceiling_ev - self.baseline_mean_ev
        gap_v = self.oracle_ceiling_ev - self.v44_mean_ev
        print(f"  gap_to_oracle: baseline={gap_b:+.4f} EV "
              f"(${gap_b*EV_TO_DOL*1000:+.1f}/1000h within-cell)  "
              f"v44={gap_v:+.4f} EV (${gap_v*EV_TO_DOL*1000:+.1f}/1000h within-cell)")
        print(f"  capture:     vs_baseline={self.capture_pct_vs_baseline:+.2f}%  "
              f"vs_v44={self.capture_pct_vs_v44:+.2f}%")
        print(f"  lift vs BASELINE: within_cell ${self.lift_vs_baseline_within_cell:+.2f}/1000h  "
              f"whole_grid ${self.lift_vs_baseline_whole_grid:+.2f}/1000h")
        print(f"  lift vs V44:      within_cell ${self.lift_vs_v44_within_cell:+.2f}/1000h  "
              f"whole_grid ${self.lift_vs_v44_whole_grid:+.2f}/1000h")
        if self.rule_vs_oracle_mismatch:
            print("  top rule-vs-oracle mismatch classes (by $ regret within cell):")
            for cls, n, mean_reg in self.rule_vs_oracle_mismatch[:5]:
                print(f"    {cls:<32} n={n:>6,}  mean=${mean_reg:>+7.1f}/1000h")


_DATA_CACHE: dict = {}


def _load_data() -> dict:
    if "df" in _DATA_CACHE:
        return _DATA_CACHE
    print("[harness] loading parquet ...", flush=True)
    df = pq.read_table(PARQUET).to_pandas()
    print(f"  rows: {len(df):,}", flush=True)
    print("[harness] loading canonical hands ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    print("[harness] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("[harness] computing cell tags ...", flush=True)
    cells = vectorized_cells(df)
    _DATA_CACHE.update({"df": df, "ch": ch, "gf": gf, "cells": cells})
    return _DATA_CACHE


def test_rule_on_cell(
    rule_fn: Callable,
    max_rank: int,
    cell: str,
    *,
    baseline_fn: Optional[Callable] = None,
    label: str = "rule",
    progress: bool = True,
    progress_every: int = 50_000,
) -> CatalogResult:
    """Score rule_fn against baseline_fn, v44_dt, and oracle on the
    (max_rank, cell) subset of high_only.

    rule_fn:     hand_bytes → Optional[int]. None means rule doesn't fire
                 → baseline_fn's pick is used.
    baseline_fn: hand_bytes → int. Defaults to v52_full_high_only_handler.
                 Production-shipping rules treat this as 'what's already in
                 the chain'.

    Returns CatalogResult with all aggregate metrics.
    """
    data = _load_data()
    df = data["df"]; ch = data["ch"]; gf = data["gf"]; cells_arr = data["cells"]

    if baseline_fn is None:
        from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler
        baseline_fn = strategy_v52_full_high_only_handler

    mask = (df["max_rank"].to_numpy() == max_rank) & (cells_arr == cell)
    sub = df[mask].reset_index(drop=True)
    n = len(sub)
    if n == 0:
        raise ValueError(f"No hands in (max={max_rank}, cell={cell})")

    cids = sub["canonical_id"].to_numpy()
    oracle_idxs = sub["oracle_idx"].to_numpy()
    v44_idxs = sub["v44_idx"].to_numpy()

    rule_idxs = np.zeros(n, dtype=np.int16)
    baseline_idxs = np.zeros(n, dtype=np.int16)
    n_rule_fires = 0
    t0 = time.time()
    for i in range(n):
        cid = int(cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        b_idx = int(baseline_fn(h))
        baseline_idxs[i] = b_idx
        r = rule_fn(h)
        if r is None:
            rule_idxs[i] = b_idx
        else:
            rule_idxs[i] = int(r)
            n_rule_fires += 1
        if progress and (i + 1) % progress_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (n - i - 1) / rate if rate > 0 else 0
            print(f"    [{label}] {i+1:>7,}/{n:,}  "
                  f"rate={rate:>5.0f}/s  ETA {eta:>4.0f}s", flush=True)

    # Vectorized EV lookups (one row per hand, four indices).
    rule_evs = np.empty(n, dtype=np.float64)
    baseline_evs = np.empty(n, dtype=np.float64)
    v44_evs = np.empty(n, dtype=np.float64)
    oracle_evs = np.empty(n, dtype=np.float64)
    for i in range(n):
        rowf = gf.evs[int(cids[i])]
        rule_evs[i] = float(rowf[rule_idxs[i]])
        baseline_evs[i] = float(rowf[baseline_idxs[i]])
        v44_evs[i] = float(rowf[v44_idxs[i]])
        oracle_evs[i] = float(rowf[oracle_idxs[i]])

    rule_mean = rule_evs.mean()
    baseline_mean = baseline_evs.mean()
    v44_mean = v44_evs.mean()
    oracle_mean = oracle_evs.mean()

    gap_b = oracle_mean - baseline_mean
    gap_v = oracle_mean - v44_mean
    cap_b = 100.0 * (rule_mean - baseline_mean) / gap_b if gap_b > 1e-12 else 0.0
    cap_v = 100.0 * (rule_mean - v44_mean) / gap_v if gap_v > 1e-12 else 0.0

    lift_b = (rule_mean - baseline_mean) * EV_TO_DOL * 1000
    lift_b_wg = (rule_evs - baseline_evs).sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID
    lift_v = (rule_mean - v44_mean) * EV_TO_DOL * 1000
    lift_v_wg = (rule_evs - v44_evs).sum() * EV_TO_DOL * 1000 / N_TOTAL_GRID

    # Rule-vs-oracle mismatch breakdown (by oracle pick class).
    mismatch_count: Counter = Counter()
    mismatch_regret: dict = {}
    diff_mask = rule_idxs != oracle_idxs
    diff_idx = np.where(diff_mask)[0]
    for j in diff_idx:
        cid = int(cids[j])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        r_cls = classify_pick(h, feats, int(rule_idxs[j]))
        o_cls = classify_pick(h, feats, int(oracle_idxs[j]))
        key = f"{r_cls} -> {o_cls}"
        mismatch_count[key] += 1
        mismatch_regret[key] = mismatch_regret.get(key, 0.0) + (oracle_evs[j] - rule_evs[j])
    top_mismatches = []
    for key, total_reg in sorted(mismatch_regret.items(), key=lambda x: -x[1])[:10]:
        nn = mismatch_count[key]
        mean_reg = total_reg / nn * EV_TO_DOL * 1000
        top_mismatches.append((key, nn, mean_reg))

    return CatalogResult(
        label=label,
        max_rank=max_rank,
        cell=cell,
        n_hands=n,
        n_rule_fires=n_rule_fires,
        rule_pct_optimal=100.0 * (rule_idxs == oracle_idxs).mean(),
        baseline_pct_optimal=100.0 * (baseline_idxs == oracle_idxs).mean(),
        v44_pct_optimal=100.0 * (v44_idxs == oracle_idxs).mean(),
        rule_mean_ev=rule_mean,
        baseline_mean_ev=baseline_mean,
        v44_mean_ev=v44_mean,
        oracle_ceiling_ev=oracle_mean,
        capture_pct_vs_baseline=cap_b,
        capture_pct_vs_v44=cap_v,
        lift_vs_baseline_within_cell=lift_b,
        lift_vs_baseline_whole_grid=lift_b_wg,
        lift_vs_v44_within_cell=lift_v,
        lift_vs_v44_whole_grid=lift_v_wg,
        rule_vs_oracle_mismatch=top_mismatches,
    )


def audit_rule_across_cells(
    rule_fn: Callable,
    max_rank: int,
    *,
    baseline_fn: Optional[Callable] = None,
    cells: Optional[list] = None,
    label: str = "rule",
) -> dict:
    """Run test_rule_on_cell for every cell at max_rank; return dict of results.

    For an audit of an existing rule: pass baseline_fn=rule_fn so
    lift_vs_baseline = 0 (rule == baseline) and the report focuses on
    rule_mean vs oracle gap. For a candidate refinement: pass
    baseline_fn=v52 (or Rule 14 directly, since they match on A-high).
    """
    if cells is None:
        cells = ALL_CELLS
    results = {}
    for cell in cells:
        try:
            r = test_rule_on_cell(rule_fn, max_rank, cell,
                                  baseline_fn=baseline_fn,
                                  label=f"{label}/{cell}")
            r.print_summary()
            results[cell] = r
        except ValueError as e:
            print(f"  [skip] (max={RANK_CHAR[max_rank]}, cell={cell}): {e}")
    return results


def sanity_check_rule14() -> None:
    """Reproduce Rule 14's known whole-grid lift vs its pre-Rule-14 predecessor.

    Rule 14 was shipped in Session 50; expected to beat v44_rule13 by ~$131/1000h
    whole-grid on A-high. If this harness reproduces that within reason, the
    audit and candidate-refinement results below are trustworthy.
    """
    from strategy_v45_rule14_Ahigh_DS import strategy_v45_rule14_Ahigh_DS
    from strategy_v44_rule13_three_pair_DS import strategy_v44_rule13_three_pair_DS

    print("\n" + "=" * 88)
    print("SANITY CHECK — Rule 14 vs pre-Rule-14 predecessor (v44_rule13)")
    print("Expected: ~+$131/1000h whole-grid on A-high (S50 shipped lift).")
    print("=" * 88)

    total_wg = 0.0
    total_n = 0
    for cell in ALL_CELLS:
        try:
            r = test_rule_on_cell(
                rule_fn=strategy_v45_rule14_Ahigh_DS,
                max_rank=14,
                cell=cell,
                baseline_fn=strategy_v44_rule13_three_pair_DS,
                label=f"sanity_rule14/{cell}",
            )
            r.print_summary()
            total_wg += r.lift_vs_baseline_whole_grid
            total_n += r.n_hands
        except ValueError as e:
            print(f"  [skip] cell={cell}: {e}")

    print(f"\n  ==> Sanity total A-high whole-grid lift: ${total_wg:+.2f}/1000h "
          f"(n={total_n:,})")
    print("      Expected ~+$131/1000h (CURRENT_PHASE table). Within reason if "
          "between $100 and $160.")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sanity", action="store_true",
                    help="Run Rule 14 sanity check (~5 min on full A-high).")
    args = ap.parse_args()
    if args.sanity:
        sanity_check_rule14()
    else:
        print("Use --sanity to run Rule 14 sanity check.")
        print("Or `from test_rule_catalog import test_rule_on_cell` in another script.")
