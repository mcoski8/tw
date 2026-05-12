"""
Session 63 — Cross-check sanity: v52 vs v47 across all of high_only.

The S53 OVERNIGHT report (page lines 17-20) says:
    v48 (= v47 + Rules 17-21 HIMID) → +$8 vs v47
    v52 (= v47 + Rule 17 offensive + Rules 22-28 defensive) → +$17 vs v47

Our Phase 2 sanity measured v48 vs v47 on J-high only = +$5.48/1000h, which
is consistent with v48's $8 across J-7-high. CURRENT_PHASE's "Rule 17 = +$17"
attribution actually folds in the v52 defensive rules.

This script confirms the (re-)interpretation by measuring v52 vs v47 across
ALL high_only — expecting ~$17.

It also measures Rule 24's specific J-high contribution: v52 vs v48 on J-high
s2 ≤ 8 subset.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from test_rule_catalog import _load_data  # noqa: E402
from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402
from strategy_v48_rules17_21_high_only_HIMID import strategy_v48_rules17_21_high_only_HIMID  # noqa: E402
from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS  # noqa: E402

EV_TO_DOL = 10.0
N_TOTAL = 6_009_159


def compare(rule_fn, baseline_fn, mask, label, ch, gf, cids):
    n = int(mask.sum())
    if n == 0:
        print(f"  [{label}] empty")
        return 0.0
    rule_evs = np.empty(n, dtype=np.float64)
    base_evs = np.empty(n, dtype=np.float64)
    idxs = np.where(mask)[0]
    for k, i in enumerate(idxs):
        cid = int(cids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        rule_evs[k] = float(gf.evs[cid][int(rule_fn(h))])
        base_evs[k] = float(gf.evs[cid][int(baseline_fn(h))])
    within = (rule_evs.mean() - base_evs.mean()) * EV_TO_DOL * 1000
    wg = (rule_evs - base_evs).sum() * EV_TO_DOL * 1000 / N_TOTAL
    print(f"  [{label}]  n={n:,}  within=${within:+8.2f}/1000h  WG=${wg:+7.2f}/1000h")
    return wg


def main():
    print("=" * 88)
    print("Session 63 — cross-check sanity")
    print("Expect v52 vs v47 across all high_only ≈ +$17/1000h WG (S53 ship).")
    print("=" * 88)
    data = _load_data()
    df = data["df"]
    ch = data["ch"]
    gf = data["gf"]
    cids = df["canonical_id"].to_numpy()
    max_arr = df["max_rank"].to_numpy()
    n_total = len(df)

    # Compute s2 once for all high_only hands
    s2_arr = np.zeros(n_total, dtype=np.int16)
    for i in range(n_total):
        h = np.asarray(ch.hands[int(cids[i])], dtype=np.uint8)
        ranks = (h // 4) + 2
        sr = sorted(int(r) for r in ranks)
        s2_arr[i] = sr[-2]

    print("\n--- v52 vs v47 across ALL high_only (n={:,}) ---".format(n_total))
    all_mask = np.ones(n_total, dtype=bool)
    wg_total = compare(strategy_v52_full_high_only_handler, strategy_v47_rule16_Qhigh_DS,
                        all_mask, "all high_only", ch, gf, cids)
    print(f"\n  ==> Expected ≈ +$17/1000h (S53 OVERNIGHT line 20). "
          f"Got ${wg_total:+.2f}.")

    print("\n--- v52 vs v47 by max_rank ---")
    for mr in [14, 13, 12, 11, 10, 9, 8, 7]:
        sub = max_arr == mr
        if int(sub.sum()) == 0:
            continue
        compare(strategy_v52_full_high_only_handler, strategy_v47_rule16_Qhigh_DS,
                sub, f"max={mr}", ch, gf, cids)

    print("\n--- Decomposition: Rule 17 (v48 vs v47) vs Rule 24 (v52 vs v48) on J-high ---")
    J_mask = max_arr == 11
    print("[Rule 17 alone, v48 vs v47, all J-high]")
    compare(strategy_v48_rules17_21_high_only_HIMID, strategy_v47_rule16_Qhigh_DS,
            J_mask, "v48-vs-v47 / J-high", ch, gf, cids)
    print("[Rule 17 alone, v48 vs v47, J-high s2 > 8]")
    compare(strategy_v48_rules17_21_high_only_HIMID, strategy_v47_rule16_Qhigh_DS,
            J_mask & (s2_arr > 8), "v48-vs-v47 / J-high s2>8", ch, gf, cids)
    print("[Rule 17 alone, v48 vs v47, J-high s2 ≤ 8]")
    compare(strategy_v48_rules17_21_high_only_HIMID, strategy_v47_rule16_Qhigh_DS,
            J_mask & (s2_arr <= 8), "v48-vs-v47 / J-high s2≤8", ch, gf, cids)
    print("[Rule 24 contribution, v52 vs v48, J-high s2 ≤ 8]")
    compare(strategy_v52_full_high_only_handler, strategy_v48_rules17_21_high_only_HIMID,
            J_mask & (s2_arr <= 8), "v52-vs-v48 / J-high s2≤8", ch, gf, cids)
    print("[Rule 17 + Rule 24 net, v52 vs v47, all J-high]")
    compare(strategy_v52_full_high_only_handler, strategy_v47_rule16_Qhigh_DS,
            J_mask, "v52-vs-v47 / J-high", ch, gf, cids)


if __name__ == "__main__":
    main()
