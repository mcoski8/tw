"""
Session 69 Phase 2 — quick catalog-rule candidate sweep for two_pair.

Tests 3 catalog candidates against the v54 baseline + v44 ceiling on the
largest residual cells. The expected outcome (per
TWO_PAIR_DECISION_MATRIX.md): all 3 candidates land in T3 (ML-only) —
v44's selectivity is what wins the within-cell decisions, blanket
catalog rules cannot capture the headroom. This sweep documents the
ML-only-ness of two_pair at catalog granularity.

Candidates (each is a blanket "if cell X + condition → fixed layout
choice" rule):

  C_T2P_1 — Anti-Layout-A on LAYOUT_A_DS at hi_pair ∈ {Q, K, A}.
            Oracle picks Layout A only 17-25% in this cell despite
            A_DS being available; v54 over-picks A 85%. The rule
            forces Layout B (Hmid + Lbot) — mirroring oracle's
            dominant 50-60% preference. Expected: small lift if v54
            was over-picking A; large positive lift if v54 == oracle on
            most of the 85% A picks.

  C_T2P_2 — Q-pair-hi prefer Layout C on LAYOUT_C_DS.
            Oracle picks C 55% in this cell; v54 picks C 54% (already
            close). Rule forces Layout C, max sing on top, best SS bot.
            Expected: near-zero lift since v54 already picks C
            ~optimally on average — but the within-rule variance is
            high.

  C_T2P_3 — A-pair-hi LAYOUT_A_SS → blanket Layout B with max sing on
            top. Largest cell × biggest gap = highest catalog ceiling
            ($25.66 WG). Rule mirrors v44's behavior here.
            Expected: largest single rule lift if it works.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/test_two_pair_catalog_candidates_S69.py
"""
from __future__ import annotations

import json
import sys
import time
from collections import Counter
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "analysis" / "src"))

from test_rule_catalog_two_pair import test_rule_on_cell, RANK_CHAR  # noqa: E402
from tw_analysis.query import SETTING_HAND_INDICES  # noqa: E402


def _two_pair_layout_pick(
    hand: np.ndarray,
    target_layout: str,
    *,
    require_top_max: bool = True,
    bot_suit_preference: tuple[str, ...] = ("DS", "SS", "31", "RB"),
) -> int | None:
    """Brute-force enumerate all 105 settings and return the one matching
    target_layout (= 'A' / 'B' / 'C') with the best bot suit (per
    bot_suit_preference order) and (if require_top_max) max singleton on top.

    Returns None if no setting matches. Used by catalog candidates to
    construct a forced-layout pick.
    """
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    suits = h & 3
    rc = Counter(int(r) for r in ranks)
    pair_ranks = sorted([r for r, c in rc.items() if c == 2], reverse=True)
    if len(pair_ranks) != 2:
        return None
    hi, lo = pair_ranks[0], pair_ranks[1]
    hi_set = {i for i in range(7) if int(ranks[i]) == hi}
    lo_set = {i for i in range(7) if int(ranks[i]) == lo}
    sing_pos = [i for i in range(7) if i not in hi_set and i not in lo_set]
    sing_ranks = [int(ranks[p]) for p in sing_pos]
    max_sing_rank = max(sing_ranks)

    candidates = []
    for idx in range(105):
        pos = SETTING_HAND_INDICES[idx]
        top_pos = int(pos[0])
        mid_pos = (int(pos[1]), int(pos[2]))
        bot_pos = (int(pos[3]), int(pos[4]), int(pos[5]), int(pos[6]))

        n_hi_in_bot = sum(1 for p in bot_pos if p in hi_set)
        n_hi_in_mid = sum(1 for p in mid_pos if p in hi_set)
        n_lo_in_bot = sum(1 for p in bot_pos if p in lo_set)
        n_lo_in_mid = sum(1 for p in mid_pos if p in lo_set)

        if target_layout == "A":
            ok = (n_hi_in_bot == 2 and n_lo_in_bot == 2)
        elif target_layout == "B":
            ok = (n_hi_in_mid == 2 and n_lo_in_bot == 2)
        elif target_layout == "C":
            ok = (n_hi_in_bot == 2 and n_lo_in_mid == 2)
        else:
            ok = False
        if not ok:
            continue

        bot_suits = [int(suits[p]) for p in bot_pos]
        cnt = sorted(Counter(bot_suits).values(), reverse=True)
        if cnt == [2, 2]:
            bs = "DS"
        elif cnt == [2, 1, 1]:
            bs = "SS"
        elif cnt == [3, 1]:
            bs = "31"
        elif cnt == [4]:
            bs = "4f"
        else:
            bs = "RB"

        top_rank = int(ranks[top_pos])
        is_top_max = (top_rank == max_sing_rank
                       and top_pos not in hi_set
                       and top_pos not in lo_set)

        if require_top_max and not is_top_max:
            continue

        candidates.append({
            "idx": idx,
            "bs": bs,
            "top_rank": top_rank,
        })

    if not candidates:
        return None
    # Rank by (bot_suit_preference order, top_rank descending).
    bs_order = {bs: i for i, bs in enumerate(bot_suit_preference)}

    def keyf(c):
        return (bs_order.get(c["bs"], 999), -c["top_rank"])
    candidates.sort(key=keyf)
    return candidates[0]["idx"]


# ============================================================
# C_T2P_1: Anti-Layout-A on LAYOUT_A_DS at hi_pair ∈ {Q, K, A}
#   → force Layout B with max sing on top
# ============================================================
def candidate_C_T2P_1(hand: np.ndarray):
    """Fire on LAYOUT_A_DS cell at hi_pair ∈ {Q, K, A}, return Layout B
    pick. Note: the harness already restricts to (hi_pair, cell) — so
    the rule_fn doesn't need to re-check those; it just picks Layout B.
    """
    return _two_pair_layout_pick(hand, "B",
                                  require_top_max=True,
                                  bot_suit_preference=("DS", "SS", "31", "RB"))


# ============================================================
# C_T2P_2: Q-pair-hi prefer Layout C on LAYOUT_C_DS
# ============================================================
def candidate_C_T2P_2(hand: np.ndarray):
    return _two_pair_layout_pick(hand, "C",
                                  require_top_max=True,
                                  bot_suit_preference=("DS", "SS", "31", "RB"))


# ============================================================
# C_T2P_3: A-pair-hi LAYOUT_A_SS → Layout B with max sing on top
# ============================================================
def candidate_C_T2P_3(hand: np.ndarray):
    return _two_pair_layout_pick(hand, "B",
                                  require_top_max=True,
                                  bot_suit_preference=("DS", "SS", "31", "RB"))


def main():
    print("=" * 90)
    print(f"S69 Phase 2 — two_pair catalog candidate sweep")
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 90)

    results = {}

    # C_T2P_1 — Anti-A on LAYOUT_A_DS at Q/K/A
    print("\n## C_T2P_1: Anti-Layout-A on LAYOUT_A_DS (force Layout B)")
    print("   Target ranks: Q, K, A (largest LAYOUT_A_DS WG)")
    for pr in [12, 13, 14]:
        try:
            r = test_rule_on_cell(
                candidate_C_T2P_1, pr, "LAYOUT_A_DS",
                label=f"C_T2P_1/p{RANK_CHAR[pr]}",
                progress=False,
            )
            r.print_summary()
            results[f"C_T2P_1/p{RANK_CHAR[pr]}/LAYOUT_A_DS"] = {
                "lift_vs_baseline_wg": r.lift_vs_baseline_whole_grid,
                "capture_pct": r.capture_pct_vs_baseline,
                "rule_pct_opt": r.rule_pct_optimal,
                "v44_pct_opt": r.v44_pct_optimal,
                "n_fires": r.n_rule_fires,
                "n_total": r.n_hands,
            }
        except ValueError as e:
            print(f"  [skip] p{RANK_CHAR[pr]}: {e}")

    # C_T2P_2 — Layout-C on LAYOUT_C_DS at Q-pair-hi
    print("\n## C_T2P_2: Force Layout C on LAYOUT_C_DS (Q-pair-hi)")
    for pr in [12]:
        try:
            r = test_rule_on_cell(
                candidate_C_T2P_2, pr, "LAYOUT_C_DS",
                label=f"C_T2P_2/p{RANK_CHAR[pr]}",
                progress=False,
            )
            r.print_summary()
            results[f"C_T2P_2/p{RANK_CHAR[pr]}/LAYOUT_C_DS"] = {
                "lift_vs_baseline_wg": r.lift_vs_baseline_whole_grid,
                "capture_pct": r.capture_pct_vs_baseline,
                "rule_pct_opt": r.rule_pct_optimal,
                "v44_pct_opt": r.v44_pct_optimal,
                "n_fires": r.n_rule_fires,
                "n_total": r.n_hands,
            }
        except ValueError as e:
            print(f"  [skip] p{RANK_CHAR[pr]}: {e}")

    # C_T2P_3 — Layout B on LAYOUT_A_SS at A-pair-hi
    print("\n## C_T2P_3: Force Layout B on LAYOUT_A_SS (A-pair-hi)")
    for pr in [14]:
        try:
            r = test_rule_on_cell(
                candidate_C_T2P_3, pr, "LAYOUT_A_SS",
                label=f"C_T2P_3/p{RANK_CHAR[pr]}",
                progress=False,
            )
            r.print_summary()
            results[f"C_T2P_3/p{RANK_CHAR[pr]}/LAYOUT_A_SS"] = {
                "lift_vs_baseline_wg": r.lift_vs_baseline_whole_grid,
                "capture_pct": r.capture_pct_vs_baseline,
                "rule_pct_opt": r.rule_pct_optimal,
                "v44_pct_opt": r.v44_pct_optimal,
                "n_fires": r.n_rule_fires,
                "n_total": r.n_hands,
            }
        except ValueError as e:
            print(f"  [skip] p{RANK_CHAR[pr]}: {e}")

    # ============================================================
    # Verdict summary
    # ============================================================
    print("\n" + "=" * 90)
    print("VERDICT SUMMARY (T1 = ≥40% gap closure + ≥+$3/1000h within-cell;")
    print("                 T2 = T1 + ≥+$5/1000h whole-grid lift; T3 = no T1)")
    print("=" * 90)
    print(f"  {'candidate':<40}{'lift_wg':>10}{'capture':>10}{'rule_opt':>10}{'verdict':>10}")
    for k, v in results.items():
        verdict = "T3"
        if v["capture_pct"] >= 40 and v["lift_vs_baseline_wg"] >= 3:
            verdict = "T1"
            if v["lift_vs_baseline_wg"] >= 5:
                verdict = "T2"
        print(f"  {k:<40}${v['lift_vs_baseline_wg']:>+8.2f}"
              f"{v['capture_pct']:>+9.1f}%{v['rule_pct_opt']:>9.1f}%"
              f"{verdict:>10}")

    out_path = ROOT / "data" / "session69" / "two_pair_catalog_candidates.json"
    out_path.parent.mkdir(exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(results, f, indent=2)
    print(f"\n  Wrote: {out_path}")
    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
