"""
Session 67 — test_rule_catalog_pair.py

Per-cell rule audit harness for the PAIR category. Mirrors S60's
``test_rule_catalog.py`` (high_only), adapted for the pair Phase 1 parquet
schema: keys by (pair_rank, cell) instead of (max_rank, cell), and uses
the 6-cell pair-specific taxonomy from S66.

Cells are pre-tagged in
``data/drill_pair_v44_per_hand_structural.parquet`` (S66 Phase 1
artifact). EVs come from ``data/oracle_grid_full_realistic_n200.bin``.
v52 picks are pre-computed in
``data/drill_pair_v52_per_hand.parquet`` (S66 Phase 2 artifact) so the
default baseline (v52) is a parquet lookup instead of a 2.8M Python
function call.

Typical use:

    from test_rule_catalog_pair import test_rule_on_cell

    res = test_rule_on_cell(
        rule_fn=strategy_v53_c_pair_3a,
        pair_rank=6,
        cell="PBOT_DS_JOINT",
        label="c_pair_3a_audit",
    )
    res.print_summary()

Sanity check helper at the bottom: reproduces Rule 11 (J-pair-J PBOT DS)
shipped lift vs its pre-Rule-11 predecessor (v41_rule10_v3_ds).
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
PAIR_PARQUET = ROOT / "data" / "drill_pair_v44_per_hand_structural.parquet"
V52_PARQUET = ROOT / "data" / "drill_pair_v52_per_hand.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

# Cell index → label, MUST match drill_pair_v44_S66.CELLS_ORDER.
CELLS_ORDER = [
    "PBOT_DS_JOINT", "PBOT_DS_PARTIAL",
    "PMID_DS_MAXTOP", "PMID_DS_NOMAXTOP",
    "PMID_SS_MAXTOP", "PMID_OTHER",
]
CELL_TO_IDX = {c: i for i, c in enumerate(CELLS_ORDER)}

SUIT_LABELS = {
    SUIT_PROFILE_DS: "DS", SUIT_PROFILE_SS: "SS",
    SUIT_PROFILE_RAINBOW: "RB", SUIT_PROFILE_THREE_ONE: "31",
    SUIT_PROFILE_FOUR_FLUSH: "4f",
}

_PLACEMENT_LABELS = {0: "PMID", 1: "PBOT", 2: "SPLIT"}
_TOP_TYPE_LABELS = {0: "PAIR", 1: "SING_MAX", 2: "SING_NOMAX"}


def classify_pick_pair_simple(hand_bytes, feats, idx: int, pair_pos_set, max_sing_pos) -> str:
    """Pair-specific compact label, e.g. 'PMID_tmax_SS', 'PBOT_tmax_DS_ms'.

    Mirrors classify_pick_pair in drill_pair_v44_S66.py but takes
    pre-computed pair_pos_set + max_sing_pos as inputs.
    """
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))
    suits = hand_bytes & 3

    n_pair_in_mid = sum(1 for p in mid_pos if p in pair_pos_set)
    n_pair_in_bot = sum(1 for p in bot_pos if p in pair_pos_set)
    if n_pair_in_mid == 2:
        placement = "PMID"
    elif n_pair_in_bot == 2:
        placement = "PBOT"
    else:
        placement = "SPLIT"

    if top_pos in pair_pos_set:
        top_type = "tpair"
    elif top_pos == max_sing_pos:
        top_type = "tmax"
    else:
        top_type = "tnomax"

    suit_lbl = SUIT_LABELS.get(int(feats.bot_suit_profile[idx]), "?")
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_suited = mid_suits[0] == mid_suits[1]
    ms_lbl = "ms" if mid_suited else "mu"
    if placement == "PMID":
        return f"PMID_{top_type}_{suit_lbl}"
    return f"{placement}_{top_type}_{suit_lbl}_{ms_lbl}"


def _pair_meta(hand_bytes):
    """Return (pair_pos_set, max_sing_pos) for a pair hand."""
    ranks = (hand_bytes // 4) + 2
    rc = Counter(int(r) for r in ranks)
    pair_rank = next(r for r, c in rc.items() if c == 2)
    pair_pos = {i for i in range(7) if int(ranks[i]) == pair_rank}
    sing_pos = [i for i in range(7) if i not in pair_pos]
    sing_ranks = [int(ranks[i]) for i in sing_pos]
    max_sing_rank = max(sing_ranks)
    max_sing_pos = sing_pos[sing_ranks.index(max_sing_rank)]
    return pair_pos, max_sing_pos


@dataclass
class CatalogResult:
    label: str
    pair_rank: int
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
        print(f"  pair_rank={RANK_CHAR[self.pair_rank]}  cell={self.cell}  n={self.n_hands:,}")
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
                print(f"    {cls:<36} n={n:>6,}  mean=${mean_reg:>+7.1f}/1000h")


_DATA_CACHE: dict = {}


def _load_data() -> dict:
    if "df" in _DATA_CACHE:
        return _DATA_CACHE
    print("[harness] loading pair parquet (cells + v44 + oracle) ...", flush=True)
    df = pq.read_table(PAIR_PARQUET).to_pandas()
    print(f"  rows: {len(df):,}", flush=True)
    print("[harness] loading v52 parquet (pre-computed v52 picks) ...", flush=True)
    df52 = pq.read_table(V52_PARQUET).to_pandas()
    # Join v52 picks onto pair parquet via canonical_id.
    df52_lookup = dict(zip(df52["canonical_id"].to_numpy(),
                           df52["v52_idx"].to_numpy()))
    v52_idx_arr = np.array([df52_lookup[int(cid)]
                            for cid in df["canonical_id"].to_numpy()],
                           dtype=np.int16)
    df["v52_idx"] = v52_idx_arr
    print("[harness] loading canonical hands ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    print("[harness] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    _DATA_CACHE.update({"df": df, "ch": ch, "gf": gf})
    print("[harness] cache ready.", flush=True)
    return _DATA_CACHE


def test_rule_on_cell(
    rule_fn: Callable,
    pair_rank: int,
    cell: str,
    *,
    baseline_fn: Optional[Callable] = None,
    label: str = "rule",
    progress: bool = True,
    progress_every: int = 50_000,
    extra_filter: Optional[Callable] = None,
) -> CatalogResult:
    """Score rule_fn against baseline_fn, v44_dt, and oracle on the
    (pair_rank, cell) subset of pair hands.

    rule_fn:     hand_bytes → Optional[int]. None means rule doesn't fire
                 → baseline_fn's pick is used.
    baseline_fn: hand_bytes → int. If None, the pre-computed v52 pick from
                 ``drill_pair_v52_per_hand.parquet`` is used as the
                 baseline (much faster on 2.8M hands than computing v52 per
                 hand). Pass a Python callable when you need a non-v52
                 baseline (e.g. Rule 11 vs v41).
    extra_filter: Optional hand_bytes → bool to further restrict the
                 subset (e.g. for Rule 11 sanity check: max_sing_rank<=10).

    Returns CatalogResult with all aggregate metrics.
    """
    data = _load_data()
    df = data["df"]; ch = data["ch"]; gf = data["gf"]

    cell_idx = CELL_TO_IDX[cell]
    mask = (df["pair_rank"].to_numpy() == pair_rank) & (df["cell_idx"].to_numpy() == cell_idx)
    sub = df[mask].reset_index(drop=True)
    n_total = len(sub)
    if n_total == 0:
        raise ValueError(f"No hands in (pair={pair_rank}, cell={cell})")

    # Optional extra filter (e.g. max_sing_rank gate for Rule 11 sanity).
    if extra_filter is not None:
        keep = np.zeros(n_total, dtype=bool)
        cids_all = sub["canonical_id"].to_numpy()
        for i in range(n_total):
            cid = int(cids_all[i])
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            keep[i] = bool(extra_filter(h))
        sub = sub[keep].reset_index(drop=True)
        if len(sub) == 0:
            raise ValueError(f"After extra_filter: no hands in (pair={pair_rank}, cell={cell})")

    n = len(sub)
    cids = sub["canonical_id"].to_numpy()
    oracle_idxs = sub["oracle_idx"].to_numpy()
    v44_idxs = sub["v44_idx"].to_numpy()
    v52_idxs = sub["v52_idx"].to_numpy()

    use_v52_baseline = baseline_fn is None

    rule_idxs = np.zeros(n, dtype=np.int16)
    baseline_idxs = np.zeros(n, dtype=np.int16)
    n_rule_fires = 0
    t0 = time.time()
    for i in range(n):
        cid = int(cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        if use_v52_baseline:
            b_idx = int(v52_idxs[i])
        else:
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

    # Vectorized EV lookups.
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

    # Rule-vs-oracle mismatch breakdown.
    mismatch_count: Counter = Counter()
    mismatch_regret: dict = {}
    diff_mask = rule_idxs != oracle_idxs
    diff_idx = np.where(diff_mask)[0]
    for j in diff_idx:
        cid = int(cids[j])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        feats = setting_features_from_bytes(h)
        pair_pos_set, max_sing_pos = _pair_meta(h)
        r_cls = classify_pick_pair_simple(h, feats, int(rule_idxs[j]), pair_pos_set, max_sing_pos)
        o_cls = classify_pick_pair_simple(h, feats, int(oracle_idxs[j]), pair_pos_set, max_sing_pos)
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
        pair_rank=pair_rank,
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
    pair_rank: int,
    *,
    baseline_fn: Optional[Callable] = None,
    cells: Optional[list] = None,
    label: str = "rule",
    extra_filter: Optional[Callable] = None,
) -> dict:
    """Run test_rule_on_cell for every cell at pair_rank; return dict of
    results. Useful for sanity checks that span all cells of a pair_rank.
    """
    if cells is None:
        cells = CELLS_ORDER
    results = {}
    for cell in cells:
        try:
            r = test_rule_on_cell(rule_fn, pair_rank, cell,
                                  baseline_fn=baseline_fn,
                                  label=f"{label}/{cell}",
                                  extra_filter=extra_filter)
            r.print_summary()
            results[cell] = r
        except ValueError as e:
            print(f"  [skip] (pair={RANK_CHAR[pair_rank]}, cell={cell}): {e}")
    return results


def audit_rule_across_pair_ranks(
    rule_fn: Callable,
    pair_ranks: list,
    cells: list,
    *,
    baseline_fn: Optional[Callable] = None,
    label: str = "rule",
) -> dict:
    """Run test_rule_on_cell for each (pair_rank, cell) pair. Returns
    nested dict {pair_rank: {cell: result}}.
    """
    out = {}
    for pr in pair_ranks:
        out[pr] = {}
        for cell in cells:
            try:
                r = test_rule_on_cell(rule_fn, pr, cell,
                                      baseline_fn=baseline_fn,
                                      label=f"{label}/p{RANK_CHAR[pr]}/{cell}")
                r.print_summary()
                out[pr][cell] = r
            except ValueError as e:
                print(f"  [skip] (pair={RANK_CHAR[pr]}, cell={cell}): {e}")
    return out


def sanity_check_rule11() -> None:
    """Reproduce Rule 11's shipped lift on J-pair-J hands.

    Decision 079 (S46): Rule 11 (J-pair pair-to-bot DS + max=J only) shipped
    as v42 with grader-confirmed +$6/1000h whole-grid lift on full grid
    (N=200). Rule 11 fires only when pair_rank=J AND max_rank=J (i.e.,
    pair=J AND no non-pair singleton higher than J = max_sing_rank in
    {2..10}).

    Baseline: v41_rule10_v3_ds (Rule 11's predecessor).

    Note: CURRENT_PHASE/RESUME prompt cited "Decision 080 +$11/1000h" — both
    were misquoted; Decision 080 ships Rule 12 (two_pair), and Rule 11's
    Decision 079 lift is +$6, not +$11.
    """
    from strategy_v42_rule11_jpair_pbot_ds import strategy_v42_rule11_jpair_pbot_ds
    from strategy_v41_rule10_v3_ds import strategy_v41_rule10_v3_ds

    print("\n" + "=" * 88)
    print("SANITY CHECK — Rule 11 vs pre-Rule-11 predecessor (v41_rule10_v3_ds)")
    print("Expected: ~+$11/1000h whole-grid on J-pair-J (S46 shipped lift).")
    print("=" * 88)

    # Filter to max_sing_rank<=10 (= max_rank=J condition).
    def _max_sing_lte_10(h):
        ranks = (h // 4) + 2
        rc = Counter(int(r) for r in ranks)
        pair_rank = next(r for r, c in rc.items() if c == 2)
        sing_ranks = [int(r) for r in ranks if int(r) != pair_rank]
        return max(sing_ranks) <= 10

    total_wg = 0.0
    total_n = 0
    total_fires = 0
    for cell in CELLS_ORDER:
        try:
            r = test_rule_on_cell(
                rule_fn=strategy_v42_rule11_jpair_pbot_ds,
                pair_rank=11,
                cell=cell,
                baseline_fn=strategy_v41_rule10_v3_ds,
                label=f"sanity_rule11/{cell}",
                extra_filter=_max_sing_lte_10,
            )
            r.print_summary()
            total_wg += r.lift_vs_baseline_whole_grid
            total_n += r.n_hands
            total_fires += r.n_rule_fires
        except ValueError as e:
            print(f"  [skip] cell={cell}: {e}")

    print(f"\n  ==> Sanity total J-pair-J whole-grid lift: ${total_wg:+.2f}/1000h "
          f"(n={total_n:,}, fires={total_fires:,})")
    print("      Expected +$6/1000h grader-confirmed (Decision 079). "
          "Within reason if between $5.70 and $6.30 (<5% error).")
    err_pct = abs(total_wg - 6.0) / 6.0 * 100 if total_wg != 0 else 100.0
    print(f"      Observed error vs $6 target: {err_pct:.1f}%")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--sanity", action="store_true",
                    help="Run Rule 11 sanity check (~3-5 min on full J-pair).")
    args = ap.parse_args()
    if args.sanity:
        sanity_check_rule11()
    else:
        print("Use --sanity to run Rule 11 sanity check.")
        print("Or `from test_rule_catalog_pair import test_rule_on_cell` in another script.")
