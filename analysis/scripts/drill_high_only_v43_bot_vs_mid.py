"""
Session 58 — Drill HO8: Omaha-first vs Hold'em-first vs joint per max_rank.

QUESTION (from user S57 review):
  Does oracle optimize the BOT (Omaha) first or the MID (Hold'em) first
  or jointly? When JOINT (top=max, DS bot, ms mid) is achievable, which
  joint config does oracle pick — the one with the highest bot pair, the
  highest mid pair, or some balance?

METHOD:
  For each high_only hand, enumerate all JOINT-configs (top = max-rank,
  bot is 2+2 DS, mid 2 cards are suited). Each joint has a quality tuple:
    bot_pair_high  : higher-card of suited pair in bot (we use the max
                     across both suited pairs in a 2+2 bot)
    bot_sum        : sum of bot ranks
    bot_run        : longest run in bot
    mid_high       : higher-card of suited mid pair
    mid_sum        : sum of mid pair
    EV             : actual value from oracle grid
  Then rank the joint configs by:
    a. bot_pair_high (descending), tiebreak (bot_run, bot_sum)
    b. mid_high (descending), tiebreak mid_sum
    c. EV (descending) — this is the truth
  Where does oracle's pick land in each ranking?

  Also: for hands where JOINT is achievable, what fraction of the time does
  oracle take JOINT vs an alternative? When alt, which alternative
  (DS_mu, SS_ms, SS_mu, etc.)?

OUTPUTS:
  Per max_rank: distribution of oracle's bot-rank-pct, mid-rank-pct, EV-rank-pct.
  If oracle is bot-first → low bot-rank, high mid-rank.
  If oracle is mid-first → low mid-rank, high bot-rank.
  If joint → both moderately ranked (and EV-rank near 1).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_only_v43_bot_vs_mid.py
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import Counter, defaultdict
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
    setting_features_from_bytes, SETTING_HAND_INDICES,
    SUIT_PROFILE_DS,
)

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
RANK_CHAR = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8", 9: "9",
             10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}

EV_TO_DOL = 10.0
N_TOTAL_GRID = 6_009_159


def enum_joint_configs(hand_bytes):
    """Enumerate all (setting_idx, bot_pair_high, bot_sum, bot_run,
    mid_high, mid_sum) tuples for joint configs (top=max, DS bot,
    ms mid)."""
    ranks = (hand_bytes // 4) + 2
    suits = hand_bytes & 3
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    max_rank = max(int_ranks)
    max_pos = int_ranks.index(max_rank)

    configs = []
    # We need to find setting indices where top = max_pos, bot is 2+2 DS,
    # mid 2 cards share suit. Enumerate the 15 mid-pairs from the 6 non-top
    # cards.
    rest = [i for i in range(7) if i != max_pos]
    for mid_a, mid_b in combinations(rest, 2):
        if int_suits[mid_a] != int_suits[mid_b]:
            continue
        bot_pos = [i for i in rest if i != mid_a and i != mid_b]
        bs = [int_suits[i] for i in bot_pos]
        cnt = sorted(Counter(bs).values(), reverse=True)
        if cnt != [2, 2]:
            continue
        # Compute bot quality
        br = [int_ranks[i] for i in bot_pos]
        # Higher of suited pair (max across both suited pairs in DS)
        by_suit = defaultdict(list)
        for r, s in zip(br, bs):
            by_suit[s].append(r)
        bot_pair_high = max(max(rs) for rs in by_suit.values() if len(rs) >= 2)
        bot_sum = sum(br)
        # Longest run
        sr = sorted(set(br))
        longest = 1
        cur = 1
        for j in range(1, len(sr)):
            if sr[j] == sr[j - 1] + 1:
                cur += 1
                longest = max(longest, cur)
            else:
                cur = 1
        bot_run = longest
        mr = [int_ranks[mid_a], int_ranks[mid_b]]
        mid_high = max(mr)
        mid_sum = sum(mr)
        # Compute setting_idx via SETTING_HAND_INDICES — find the row
        # whose [top, mid_a, mid_b, bot...] matches (mid order in setting
        # index is sorted ascending; bot ordering doesn't affect index).
        # Easier: search for matching setting from the precomputed table.
        configs.append({
            "top_pos": max_pos, "mid_a": mid_a, "mid_b": mid_b,
            "bot_pos": tuple(bot_pos),
            "bot_pair_high": bot_pair_high, "bot_sum": bot_sum,
            "bot_run": bot_run,
            "mid_high": mid_high, "mid_sum": mid_sum,
        })
    return configs


def find_setting_idx(top_pos, mid_a, mid_b):
    """SETTING_HAND_INDICES is precomputed; find idx where [0]=top_pos and
    {[1],[2]}={mid_a,mid_b}. We linearly scan once to build a lookup."""
    # mid is sorted ascending in the table because of how mid_pairs is
    # generated (a < b). So canonical mid order is (min, max).
    mp_a, mp_b = sorted([mid_a, mid_b])
    table = SETTING_HAND_INDICES
    # top_i*15 + mid_combo_i where mid_combo iterates over (a,b) with
    # a<b in remaining. Compute mid_combo_i via the standard ordering.
    # Easier to just find by matching:
    for idx in range(105):
        if table[idx, 0] == top_pos and tuple(int(x) for x in sorted(table[idx, 1:3])) == (mp_a, mp_b):
            return idx
    return -1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 58 — Drill HO8: Omaha-first vs Hold'em-first vs joint")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/3] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    ho_idx = np.where(cats == 0)[0]
    if args.sample > 0 and len(ho_idx) > args.sample:
        rng = np.random.default_rng(args.seed)
        ho_idx = np.sort(rng.choice(ho_idx, size=args.sample, replace=False))
        print(f"  [sample mode: {args.sample:,}]")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    print(f"  high_only n={len(ho_idx):,}")

    print("\n[2/3] enumerating joint configs + ranking oracle picks ...",
          flush=True)
    n = len(ho_idx)
    # Precompute setting-idx lookup (top_pos, mid_lo, mid_hi) -> idx
    setting_idx_lookup = {}
    for idx in range(105):
        top_pos = int(SETTING_HAND_INDICES[idx, 0])
        mid_lo, mid_hi = sorted([int(SETTING_HAND_INDICES[idx, 1]),
                                  int(SETTING_HAND_INDICES[idx, 2])])
        setting_idx_lookup[(top_pos, mid_lo, mid_hi)] = idx

    # Per-max-rank stats
    rank_stats = defaultdict(lambda: {
        "n_with_joint": 0,         # hands where joint achievable
        "n_oracle_joint": 0,       # oracle picked a joint config
        "oracle_alt_when_joint_avail": Counter(),  # alt label -> n
        "joint_n_configs_dist": Counter(),
        # When oracle picked joint:
        "or_bot_rank_pct": [],     # 1.0 = oracle picked the BEST bot-quality joint
        "or_mid_rank_pct": [],
        "or_ev_rank_pct": [],      # should be ~1.0 by construction
        "or_picked_max_bot_pair_high": 0,
        "or_picked_max_mid_high": 0,
        "or_picked_balanced": 0,
        # When oracle did NOT pick joint:
        "alt_ev_minus_best_joint_ev": [],   # negative if joint is better
    })

    t0 = time.time()
    for k, cid in enumerate(ho_idx):
        cid = int(cid)
        h = np.asarray(ch.hands[cid], dtype=np.uint8)
        ranks = (h // 4) + 2
        max_rank = int(np.max(ranks))
        rowf = np.asarray(gf.evs[cid], dtype=np.float64)
        oracle_idx = int(np.argmax(rowf))

        configs = enum_joint_configs(h)
        if not configs:
            if (k + 1) % 50000 == 0:
                rate = (k + 1) / (time.time() - t0)
                eta = (n - k - 1) / rate
                print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                      f"ETA {eta:>5.0f}s", flush=True)
            continue

        rs = rank_stats[max_rank]
        rs["n_with_joint"] += 1
        rs["joint_n_configs_dist"][len(configs)] += 1

        # Compute setting_idx for each joint config + EV
        for cfg in configs:
            mid_lo, mid_hi = sorted([cfg["mid_a"], cfg["mid_b"]])
            idx = setting_idx_lookup.get((cfg["top_pos"], mid_lo, mid_hi))
            cfg["setting_idx"] = idx if idx is not None else -1
            cfg["ev"] = float(rowf[idx]) if idx is not None and idx >= 0 else -1e9

        # Did oracle pick a joint? (oracle_idx ∈ {cfg["setting_idx"]})
        joint_idx_set = {cfg["setting_idx"] for cfg in configs}
        if oracle_idx in joint_idx_set:
            rs["n_oracle_joint"] += 1
            # Rank oracle's pick within joint configs by bot_pair_high desc
            sorted_by_bot = sorted(configs, key=lambda c: (
                -c["bot_pair_high"], -c["bot_run"], -c["bot_sum"]))
            sorted_by_mid = sorted(configs, key=lambda c: (
                -c["mid_high"], -c["mid_sum"]))
            sorted_by_ev = sorted(configs, key=lambda c: -c["ev"])
            n_cfg = len(configs)
            # Find oracle's position
            for i, c in enumerate(sorted_by_bot):
                if c["setting_idx"] == oracle_idx:
                    rs["or_bot_rank_pct"].append(1.0 - i / max(1, n_cfg - 1) if n_cfg > 1 else 1.0)
                    if i == 0:
                        rs["or_picked_max_bot_pair_high"] += 1
                    break
            for i, c in enumerate(sorted_by_mid):
                if c["setting_idx"] == oracle_idx:
                    rs["or_mid_rank_pct"].append(1.0 - i / max(1, n_cfg - 1) if n_cfg > 1 else 1.0)
                    if i == 0:
                        rs["or_picked_max_mid_high"] += 1
                    break
            for i, c in enumerate(sorted_by_ev):
                if c["setting_idx"] == oracle_idx:
                    rs["or_ev_rank_pct"].append(1.0 - i / max(1, n_cfg - 1) if n_cfg > 1 else 1.0)
                    break
            # Was oracle's pick the "balanced" option (max of bot+mid)?
            sorted_by_balanced = sorted(configs, key=lambda c: -(
                c["bot_pair_high"] + c["mid_high"]))
            for i, c in enumerate(sorted_by_balanced):
                if c["setting_idx"] == oracle_idx:
                    if i == 0:
                        rs["or_picked_balanced"] += 1
                    break
        else:
            # Oracle picked something other than joint. Characterize alt.
            feats = setting_features_from_bytes(h)
            top_pos_o = int(SETTING_HAND_INDICES[oracle_idx, 0])
            mid_pos_o = (int(SETTING_HAND_INDICES[oracle_idx, 1]),
                         int(SETTING_HAND_INDICES[oracle_idx, 2]))
            top_rank_o = int(ranks[top_pos_o])
            mid_suits_o = (h[mid_pos_o[0]] & 3, h[mid_pos_o[1]] & 3)
            mid_suited_o = mid_suits_o[0] == mid_suits_o[1]
            bot_suit_o = int(feats.bot_suit_profile[oracle_idx])
            top_lbl = "tmax" if top_rank_o == max_rank else f"t<{top_rank_o}"
            suit_lbl = {0: "RB", 1: "SS", 2: "DS", 3: "31", 4: "4f"}.get(bot_suit_o, "?")
            mid_lbl = "ms" if mid_suited_o else "mu"
            alt = f"{top_lbl}_{suit_lbl}_{mid_lbl}"
            rs["oracle_alt_when_joint_avail"][alt] += 1
            best_joint_ev = max(c["ev"] for c in configs)
            rs["alt_ev_minus_best_joint_ev"].append(
                float(rowf[oracle_idx]) - best_joint_ev)

        if (k + 1) % 50000 == 0:
            rate = (k + 1) / (time.time() - t0)
            eta = (n - k - 1) / rate
            print(f"    progress {k+1:>8,}/{n:,}  rate={rate:>5.0f}/s  "
                  f"ETA {eta:>5.0f}s", flush=True)

    print(f"  done in {time.time()-t0:.1f}s\n")

    # ============================================================
    print("=" * 100)
    print("HO8: BOT-FIRST vs MID-FIRST vs JOINT per MAX_RANK")
    print("=" * 100)
    print(f"\n  {'max':>3} {'n_joint_avail':>14} {'n_or_joint':>12} {'%or_joint':>10} "
          f"{'%pickedMaxBotPH':>16} {'%pickedMaxMidH':>16} "
          f"{'%pickedBalanced':>16}")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[max_rank]
        if rs["n_with_joint"] == 0:
            continue
        nj = rs["n_with_joint"]
        no = rs["n_oracle_joint"]
        pct_or = 100 * no / nj if nj else 0
        pct_bot = 100 * rs["or_picked_max_bot_pair_high"] / no if no else 0
        pct_mid = 100 * rs["or_picked_max_mid_high"] / no if no else 0
        pct_bal = 100 * rs["or_picked_balanced"] / no if no else 0
        print(f"  {RANK_CHAR[max_rank]:>3} {nj:>14,} {no:>12,} {pct_or:>9.1f}% "
              f"{pct_bot:>15.1f}% {pct_mid:>15.1f}% "
              f"{pct_bal:>15.1f}%")

    print("\n  Oracle's bot/mid/EV rank percentile within joint configs (when oracle picks joint):")
    print(f"  {'max':>3} {'n':>10} {'mean_bot_pct':>14} {'mean_mid_pct':>14} "
          f"{'mean_ev_pct':>14}")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[max_rank]
        if not rs["or_bot_rank_pct"]:
            continue
        bp = float(np.mean(rs["or_bot_rank_pct"]))
        mp = float(np.mean(rs["or_mid_rank_pct"]))
        ep = float(np.mean(rs["or_ev_rank_pct"]))
        print(f"  {RANK_CHAR[max_rank]:>3} {len(rs['or_bot_rank_pct']):>10,} "
              f"{bp:>13.3f} {mp:>13.3f} {ep:>13.3f}")
    print("\n  (1.0 = oracle picked the top-ranked config in that ordering;")
    print("   0.0 = oracle picked the worst. Higher of bot vs mid → that axis dominates.)")

    print("\n  Oracle's joint-config-count distribution (when joint avail):")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[max_rank]
        if not rs["joint_n_configs_dist"]:
            continue
        s = ", ".join(f"{k}:{v:,}" for k, v in sorted(rs["joint_n_configs_dist"].items()))
        print(f"    max={RANK_CHAR[max_rank]}: {s}")

    print("\n  When joint is avail but oracle picks ALT — alt class breakdown:")
    for max_rank in sorted(rank_stats.keys(), reverse=True):
        rs = rank_stats[max_rank]
        if not rs["oracle_alt_when_joint_avail"]:
            continue
        n_alt = sum(rs["oracle_alt_when_joint_avail"].values())
        ranked = sorted(rs["oracle_alt_when_joint_avail"].items(),
                         key=lambda x: -x[1])[:6]
        s = ", ".join(f"{k}:{100*v/n_alt:.0f}%" for k, v in ranked)
        # Also: mean (alt_ev - best_joint_ev) — if positive, alt was strictly better
        if rs["alt_ev_minus_best_joint_ev"]:
            mean_diff = float(np.mean(rs["alt_ev_minus_best_joint_ev"]))
        else:
            mean_diff = 0.0
        print(f"    max={RANK_CHAR[max_rank]}  n_alt={n_alt:,}  "
              f"alt_ev−best_joint_ev mean=${mean_diff*EV_TO_DOL*1000:+.0f}/1000h  alts: {s}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
