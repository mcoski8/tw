"""
Session 53 — Drill O: Q-high no-pair, non-Q-on-top sub-zone characterization.

Drill N (Session 52) found that for Q-high hands, oracle picks Q-on-top
only 49.37% of the time. The 51% non-Q-on-top sub-zone breaks down as:
  - 2 on top: 15.69% (defensive top inversion)
  - J on top: 10.40%
  - 3 on top: 7.79%
  - T on top: 4.15%
  - 4-9 on top: ~2-4% each

Drill O scopes to those non-Q-on-top hands and characterizes the oracle
pick to identify Rule 17 candidates.

Key questions:
  1. Where does v47 actually pick (which top card) on these hands?
  2. What's the regret on these hands (since v47 picks Q-on-top, it's
     specifically wrong here)?
  3. Are there structural patterns that distinguish "oracle wants 2-on-top"
     hands from "oracle wants J-on-top" hands?
  4. What's the bot/mid composition oracle uses?

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_Q_high_non_Q_top_characterization.py
"""
from __future__ import annotations

import argparse
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
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from tw_analysis.query import (  # noqa: E402
    setting_features_from_bytes,
    SUIT_PROFILE_DS, SUIT_PROFILE_SS, SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE, SUIT_PROFILE_FOUR_FLUSH,
)
from strategy_v47_rule16_Qhigh_DS import strategy_v47_rule16_Qhigh_DS  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}
QUEEN = 12


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 53 Drill O: Q-high non-Q-on-top sub-zone characterization")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    n_total = len(ch.hands)
    ho_idx = np.where(cats == 0)[0]

    print("\n[2/4] filtering to Q-high (max=Q) ...", flush=True)
    t0 = time.time()
    scope_cids = []
    second_high = []
    for cid in ho_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        if int(ranks.max()) != QUEEN:
            continue
        sorted_ranks = sorted(int(r) for r in ranks)
        s2 = sorted_ranks[-2]
        scope_cids.append(int(cid))
        second_high.append(s2)
    scope_cids = np.asarray(scope_cids, dtype=np.int64)
    second_high = np.asarray(second_high, dtype=np.int8)
    print(f"  Q-high scope: {len(scope_cids):,}")

    if args.sample > 0 and len(scope_cids) > args.sample:
        rng = np.random.default_rng(args.seed)
        idx = rng.choice(len(scope_cids), size=args.sample, replace=False)
        idx_sorted = np.sort(idx)
        scope_cids = scope_cids[idx_sorted]
        second_high = second_high[idx_sorted]

    print("\n[3/4] loading oracle grid ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print("  ready.")

    SUIT_LABELS = {SUIT_PROFILE_DS: "DS", SUIT_PROFILE_SS: "SS",
                    SUIT_PROFILE_RAINBOW: "rainbow",
                    SUIT_PROFILE_THREE_ONE: "3+1",
                    SUIT_PROFILE_FOUR_FLUSH: "4-flush"}

    # Per-oracle-top-rank buckets — the entire hand by what oracle puts on top
    by_top = defaultdict(lambda: {
        "n": 0, "regret_sum": 0.0, "v47_top_rank_dist": Counter(),
        "oracle_bot_suit": Counter(), "oracle_mid_has_Q": 0,
        "oracle_bot_has_Q": 0, "by_s2": Counter(),
        "oracle_top_pos_kind": Counter(),  # lowest/2nd-lowest/middle/2nd-highest/Q/etc
    })

    n_processed = 0
    print("\n[4/4] per-hand non-Q-on-top characterization ...", flush=True)
    t0 = time.time()
    for i in range(len(scope_cids)):
        cid = int(scope_cids[i])
        s2 = int(second_high[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        suits = h & 3
        queen_pos = next(j for j in range(7) if int(ranks[j]) == QUEEN)

        feats = setting_features_from_bytes(h)
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))
        v47_idx = int(strategy_v47_rule16_Qhigh_DS(h))

        oracle_top_pos = oracle_idx // 15
        oracle_top_rank = int(ranks[oracle_top_pos])

        v47_top_pos = v47_idx // 15
        v47_top_rank = int(ranks[v47_top_pos])

        oracle_ev = float(rowf[oracle_idx])
        v47_ev = float(rowf[v47_idx])
        regret = oracle_ev - v47_ev

        # Bucket by oracle top rank
        bucket = by_top[oracle_top_rank]
        bucket["n"] += 1
        bucket["regret_sum"] += regret
        bucket["v47_top_rank_dist"][v47_top_rank] += 1
        bucket["oracle_bot_suit"][int(feats.bot_suit_profile[oracle_idx])] += 1
        # Did oracle put Q in mid? bot?
        # Determine where Q ended up in oracle pick
        # The setting decoding: top is 1 card, mid is 2, bot is 4.
        # The setting_index encodes which positions go where, but we can use feats:
        if feats.mid_pair_rank[oracle_idx] == QUEEN:
            bucket["oracle_mid_has_Q"] += 1  # but mid_is_pair shouldn't apply since no pair
        if int(feats.bot_pair_rank[oracle_idx]) == QUEEN:
            bucket["oracle_bot_has_Q"] += 1
        # Better: compute Q's position in oracle's setting from setting_index
        # We have queen_pos in original hand. Where is queen in oracle's setting?
        # Use the setting decoder logic. But for now, simple: Q is in mid if
        # one of the mid positions (oracle_idx % 15 maps to 2-pair index).
        # Skip for now — use top_pos check.
        bucket["by_s2"][s2] += 1

        # Classify oracle top position by rank order
        sorted_pos = sorted(range(7), key=lambda j: -int(ranks[j]))  # desc
        # oracle_top_pos's index in sorted_pos
        rank_idx = sorted_pos.index(oracle_top_pos)
        # 0=highest (Q), 1=2nd-highest, ..., 6=lowest
        rank_label = ["Q (highest)", "2nd-highest", "3rd-highest", "4th-highest",
                       "5th-highest", "6th-highest", "lowest"][rank_idx]
        bucket["oracle_top_pos_kind"][rank_label] += 1

        n_processed += 1
        if n_processed % 20000 == 0:
            rate = n_processed / (time.time() - t0)
            print(f"    progress {n_processed:>7,}/{len(scope_cids):,}  rate={rate:.0f}/s",
                  flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n")

    # Reporting
    print("=" * 100)
    print(f"AGGREGATE — Q-high non-Q-on-top breakdown by oracle's top card rank")
    print("=" * 100)

    # Sort buckets by frequency
    sorted_buckets = sorted(by_top.items(), key=lambda x: -x[1]["n"])
    total = n_processed

    print(f"\n  Total Q-high hands: {total:,}")
    print(f"\n  {'top_rank':<10} {'n':>8} {'%':>7} {'mean_regret':>14} "
          f"{'rank_pos':<26} {'oracle_DS%':>10}")
    print("-" * 95)
    for top_rank, b in sorted_buckets:
        if b["n"] == 0: continue
        mean_regret = b["regret_sum"] / b["n"] * EV_TO_DOL * 1000
        # Most common rank position
        most_pos, _ = b["oracle_top_pos_kind"].most_common(1)[0]
        ds_pct = 100 * b["oracle_bot_suit"].get(SUIT_PROFILE_DS, 0) / b["n"]
        print(f"  {RANK_CHAR[top_rank]:<10} {b['n']:>8,} {100*b['n']/total:>6.2f}% "
              f"${mean_regret:>+12.1f}  {most_pos:<26} {ds_pct:>8.1f}%")

    # Detailed defensive (2-on-top) sub-zone
    if 2 in by_top:
        print(f"\n── DEFENSIVE 2-ON-TOP DEEP-DIVE ──")
        b = by_top[2]
        print(f"  n hands oracle wants 2 on top: {b['n']:,} ({100*b['n']/total:.2f}%)")
        print(f"  Mean regret on these hands:    ${b['regret_sum']/b['n']*EV_TO_DOL*1000:>+8.1f}/1000h")
        print(f"  Whole-grid contribution:       ${b['regret_sum']*EV_TO_DOL*1000/n_total:>+8.2f}/1000h "
              f"(if Rule 17 captures 100%)")
        print(f"\n  Stratified by 2nd-highest:")
        for s2 in range(11, 1, -1):
            n_s2 = b["by_s2"].get(s2, 0)
            if n_s2 > 0:
                print(f"    2nd={RANK_CHAR[s2]}: {n_s2:>5,}  ({100*n_s2/b['n']:>5.1f}%)")
        print(f"\n  v47's actual top-card pick on these hands (always Q):")
        for r, n in b["v47_top_rank_dist"].most_common():
            print(f"    {RANK_CHAR[r]}: {n:,}  ({100*n/b['n']:.1f}%)")
        print(f"\n  Oracle bot suit on these hands:")
        for code, label in SUIT_LABELS.items():
            n = b["oracle_bot_suit"].get(code, 0)
            if n > 0:
                print(f"    {label:<10}: {n:>5,}  ({100*n/b['n']:>5.1f}%)")

    # All "low-card on top" oracle picks (defensive zone)
    print(f"\n── DEFENSIVE TOP-INVERSION ZONE (oracle picks 2-7 on top) ──")
    defensive_n = sum(by_top[r]["n"] for r in range(2, 8) if r in by_top)
    defensive_regret = sum(by_top[r]["regret_sum"] for r in range(2, 8) if r in by_top)
    if defensive_n > 0:
        print(f"  Total defensive hands: {defensive_n:,} ({100*defensive_n/total:.2f}% of Q-high)")
        print(f"  Mean regret:           ${defensive_regret/defensive_n*EV_TO_DOL*1000:>+8.1f}/1000h within defensive zone")
        print(f"  Whole-grid potential:  ${defensive_regret*EV_TO_DOL*1000/n_total:>+8.2f}/1000h "
              f"(if rule captures 100%)")

    # Q-on-mid offensive zone (oracle picks J or T on top)
    print(f"\n── 'Q-ANCHOR-IN-MID' ZONE (oracle picks J or T on top) ──")
    mid_n = sum(by_top[r]["n"] for r in (10, 11) if r in by_top)
    mid_regret = sum(by_top[r]["regret_sum"] for r in (10, 11) if r in by_top)
    if mid_n > 0:
        print(f"  Total: {mid_n:,} ({100*mid_n/total:.2f}% of Q-high)")
        print(f"  Mean regret:           ${mid_regret/mid_n*EV_TO_DOL*1000:>+8.1f}/1000h within zone")
        print(f"  Whole-grid potential:  ${mid_regret*EV_TO_DOL*1000/n_total:>+8.2f}/1000h "
              f"(if rule captures 100%)")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
