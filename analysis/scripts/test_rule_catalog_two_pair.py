"""
Session 69 — test_rule_catalog_two_pair.py

Per-cell rule audit harness for the TWO_PAIR category. Mirrors S67's
``test_rule_catalog_pair.py`` (pair), adapted for the two_pair Phase 1
parquet schema: keys by (hi_pair_rank, cell), uses the 7-cell two_pair
taxonomy from S69, and the v54 baseline parquet (= v52 on two_pair).

Cells are pre-tagged in
``data/drill_two_pair_v44_per_hand_structural.parquet`` (S69 Phase 1).
EVs come from ``data/oracle_grid_full_realistic_n200.bin``.
v54 picks are pre-computed in ``data/drill_two_pair_v54_per_hand.parquet``
(S69 Phase 2 artifact).

Typical use:

    from test_rule_catalog_two_pair import test_rule_on_cell

    res = test_rule_on_cell(
        rule_fn=my_candidate,
        hi_pair_rank=12,
        cell="LAYOUT_A_DS",
        label="C_T2P_1_audit",
    )
    res.print_summary()
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
TP_PARQUET = ROOT / "data" / "drill_two_pair_v44_per_hand_structural.parquet"
V54_PARQUET = ROOT / "data" / "drill_two_pair_v54_per_hand.parquet"

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159

RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

CELLS_ORDER = [
    "LAYOUT_A_DS", "LAYOUT_C_DS", "LAYOUT_B_DS",
    "LAYOUT_A_SS", "LAYOUT_C_SS_ONLY", "LAYOUT_B_SS_ONLY",
    "LAYOUT_OTHER",
]
CELL_TO_IDX = {c: i for i, c in enumerate(CELLS_ORDER)}


def _bot_suit_kind(suits):
    counts = sorted(Counter(int(s) for s in suits).values(), reverse=True)
    if counts == [4]:
        return "4f"
    if counts == [2, 2]:
        return "DS"
    if counts == [2, 1, 1]:
        return "SS"
    if counts == [3, 1]:
        return "31"
    return "RB"


def _two_pair_meta(hand_bytes):
    """Return (hi_pair_set, lo_pair_set, sing_ranks_sorted) for a two_pair
    hand."""
    ranks = (hand_bytes // 4) + 2
    rc = Counter(int(r) for r in ranks)
    pair_ranks = sorted([r for r, c in rc.items() if c == 2], reverse=True)
    hi, lo = pair_ranks[0], pair_ranks[1]
    hi_set = {i for i in range(7) if int(ranks[i]) == hi}
    lo_set = {i for i in range(7) if i != i and False} | {  # noqa: trivial
        i for i in range(7) if int(ranks[i]) == lo
    }
    sing_ranks_sorted = sorted(
        [int(ranks[i]) for i in range(7)
         if int(ranks[i]) not in (hi, lo)], reverse=True
    )
    return hi_set, lo_set, sing_ranks_sorted


def classify_pick_two_pair_simple(hand_bytes, idx, hi_set, lo_set,
                                   sing_ranks_sorted):
    pos = SETTING_HAND_INDICES[idx]
    top_pos = int(pos[0])
    mid_pos = (int(pos[1]), int(pos[2]))
    bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3

    n_hi_in_bot = sum(1 for p in bot_pos if p in hi_set)
    n_hi_in_mid = sum(1 for p in mid_pos if p in hi_set)
    n_lo_in_bot = sum(1 for p in bot_pos if p in lo_set)
    n_lo_in_mid = sum(1 for p in mid_pos if p in lo_set)

    if n_hi_in_bot == 2 and n_lo_in_bot == 2:
        layout = "A"
    elif n_hi_in_mid == 2 and n_lo_in_bot == 2:
        layout = "B"
    elif n_hi_in_bot == 2 and n_lo_in_mid == 2:
        layout = "C"
    else:
        layout = "SPLIT"
    bot_suit_kind = _bot_suit_kind([int(suits[p]) for p in bot_pos])
    top_rank = int(ranks[top_pos])
    if top_pos in hi_set or top_pos in lo_set:
        top_type = "tpair"
    elif top_rank == sing_ranks_sorted[0]:
        top_type = "tmax"
    elif top_rank == sing_ranks_sorted[2]:
        top_type = "tlow"
    else:
        top_type = "tmid"
    mid_suits = (int(suits[mid_pos[0]]), int(suits[mid_pos[1]]))
    mid_suited = mid_suits[0] == mid_suits[1]
    ms_lbl = "ms" if mid_suited else "mu"
    if layout in ("A", "B", "C"):
        return f"{layout}_{bot_suit_kind}_{top_type}_{ms_lbl}"
    return f"SPLIT_{bot_suit_kind}_{top_type}"


@dataclass
class CatalogResult:
    label: str
    hi_pair_rank: int
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
        print(f"  hi_pair={RANK_CHAR[self.hi_pair_rank]}  cell={self.cell}  n={self.n_hands:,}")
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
    print("[harness] loading two_pair parquet (cells + v44 + oracle) ...", flush=True)
    df = pq.read_table(TP_PARQUET).to_pandas()
    print(f"  rows: {len(df):,}", flush=True)
    print("[harness] loading v54 parquet (pre-computed v54 picks) ...", flush=True)
    df54 = pq.read_table(V54_PARQUET).to_pandas()
    df54_lookup = dict(zip(df54["canonical_id"].to_numpy(),
                            df54["v54_idx"].to_numpy()))
    v54_idx_arr = np.array([df54_lookup[int(cid)]
                             for cid in df["canonical_id"].to_numpy()],
                            dtype=np.int16)
    df["v54_idx"] = v54_idx_arr
    print("[harness] loading canonical hands ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    print("[harness] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    _DATA_CACHE.update({"df": df, "ch": ch, "gf": gf})
    print("[harness] cache ready.", flush=True)
    return _DATA_CACHE


def test_rule_on_cell(
    rule_fn: Callable,
    hi_pair_rank: int,
    cell: str,
    *,
    baseline_fn: Optional[Callable] = None,
    label: str = "rule",
    progress: bool = True,
    progress_every: int = 50_000,
    extra_filter: Optional[Callable] = None,
) -> CatalogResult:
    """Score rule_fn against baseline_fn (default: v54 from parquet),
    v44_dt, and oracle on the (hi_pair_rank, cell) subset.

    rule_fn: hand_bytes → Optional[int]. None means rule doesn't fire
             → baseline's pick is used.
    baseline_fn: hand_bytes → int. If None, the pre-computed v54 pick
                 is used as the baseline.
    """
    data = _load_data()
    df = data["df"]; ch = data["ch"]; gf = data["gf"]

    cell_idx = CELL_TO_IDX[cell]
    mask = (df["hi_pair_rank"].to_numpy() == hi_pair_rank) & (df["cell_idx"].to_numpy() == cell_idx)
    sub = df[mask].reset_index(drop=True)
    n_total = len(sub)
    if n_total == 0:
        raise ValueError(f"No hands in (hi_pair={hi_pair_rank}, cell={cell})")

    if extra_filter is not None:
        keep = np.zeros(n_total, dtype=bool)
        cids_all = sub["canonical_id"].to_numpy()
        for i in range(n_total):
            cid = int(cids_all[i])
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            keep[i] = bool(extra_filter(h))
        sub = sub[keep].reset_index(drop=True)
        if len(sub) == 0:
            raise ValueError(f"After extra_filter: no hands in "
                              f"(hi_pair={hi_pair_rank}, cell={cell})")

    n = len(sub)
    cids = sub["canonical_id"].to_numpy()
    oracle_idxs = sub["oracle_idx"].to_numpy()
    v44_idxs = sub["v44_idx"].to_numpy()
    v54_idxs = sub["v54_idx"].to_numpy()

    use_v54_baseline = baseline_fn is None

    rule_idxs = np.zeros(n, dtype=np.int16)
    baseline_idxs = np.zeros(n, dtype=np.int16)
    n_rule_fires = 0
    t0 = time.time()
    for i in range(n):
        cid = int(cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        if use_v54_baseline:
            b_idx = int(v54_idxs[i])
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

    mismatch_count: Counter = Counter()
    mismatch_regret: dict = {}
    diff_mask = rule_idxs != oracle_idxs
    diff_idx = np.where(diff_mask)[0]
    for j in diff_idx:
        cid = int(cids[j])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        # Reconstruct hi/lo set + sing ranks
        ranks = (h // 4) + 2
        rc = Counter(int(r) for r in ranks)
        prs = sorted([r for r, c in rc.items() if c == 2], reverse=True)
        hi, lo = prs[0], prs[1]
        hi_set = {i for i in range(7) if int(ranks[i]) == hi}
        lo_set = {i for i in range(7) if int(ranks[i]) == lo}
        sing_ranks_sorted = sorted(
            [int(ranks[i]) for i in range(7) if int(ranks[i]) not in (hi, lo)],
            reverse=True
        )
        r_cls = classify_pick_two_pair_simple(h, int(rule_idxs[j]),
                                                hi_set, lo_set,
                                                sing_ranks_sorted)
        o_cls = classify_pick_two_pair_simple(h, int(oracle_idxs[j]),
                                                hi_set, lo_set,
                                                sing_ranks_sorted)
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
        hi_pair_rank=hi_pair_rank,
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


if __name__ == "__main__":
    print("Use `from test_rule_catalog_two_pair import test_rule_on_cell` "
          "in another script.")
