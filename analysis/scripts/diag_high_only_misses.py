"""
Diagnose high_only misses: where does hi_only_search disagree with robust,
and what are the systematic differences in mid composition / bot structure?
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import numpy as np
import pyarrow.parquet as pq

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Make encode_rules importable.
sys.path.insert(0, str(HERE))

from tw_analysis import read_canonical_hands  # noqa: E402
from tw_analysis.features import decode_tier_positions  # noqa: E402
from encode_rules import strategy_hi_only_search  # noqa: E402


def shape(hand, setting):
    t, m, b = decode_tier_positions(int(setting))
    ranks = (hand // 4) + 2
    suits = hand % 4
    return {
        "top_rank": int(ranks[t]),
        "mid_ranks": tuple(sorted(int(ranks[i]) for i in m)),
        "bot_ranks": tuple(sorted(int(ranks[i]) for i in b)),
        "mid_suited": suits[m[0]] == suits[m[1]],
        "bot_ds": _is_ds(suits, b),
    }


def _is_ds(suits, positions):
    counts = sorted(Counter(int(suits[p]) for p in positions).values(), reverse=True)
    while len(counts) < 2:
        counts.append(0)
    return counts[0] == 2 and counts[1] == 2


def main() -> int:
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    cards = canonical.hands
    df = pq.read_table(
        ROOT / "data" / "feature_table.parquet",
        columns=["category", "multiway_robust", "agreement_class"],
    ).to_pandas()

    mask = (df["category"] == "high_only").values
    sub = df[mask].reset_index(drop=True)
    sub_hands = cards[mask]
    n = len(sub)
    print(f"high_only: {n:,} hands")

    # Random sample for inspection.
    rng = np.random.default_rng(42)
    sample_idx = rng.choice(n, 5000, replace=False)

    n_match = 0
    n_mid_match = 0
    n_bot_ds_robust = 0
    n_bot_ds_mine = 0

    # When DS disagrees, what's the robust pattern?
    bot_ds_diffs = Counter()  # (mine_ds, robust_ds) tally
    mid_suited_diffs = Counter()
    mid_rank_sum_distribution_robust = []
    mid_rank_sum_distribution_mine = []
    rank_sum_diff_when_diff = []

    for idx in sample_idx:
        hand = sub_hands[idx]
        robust = int(sub.iloc[idx]["multiway_robust"])
        mine = strategy_hi_only_search(hand)

        rs = shape(hand, robust)
        ms = shape(hand, mine)

        if (rs["top_rank"], rs["mid_ranks"], rs["bot_ranks"]) == \
           (ms["top_rank"], ms["mid_ranks"], ms["bot_ranks"]):
            n_match += 1
        if rs["mid_ranks"] == ms["mid_ranks"]:
            n_mid_match += 1

        if rs["bot_ds"]:
            n_bot_ds_robust += 1
        if ms["bot_ds"]:
            n_bot_ds_mine += 1

        bot_ds_diffs[(ms["bot_ds"], rs["bot_ds"])] += 1
        mid_suited_diffs[(ms["mid_suited"], rs["mid_suited"])] += 1

        mid_rank_sum_distribution_robust.append(sum(rs["mid_ranks"]))
        mid_rank_sum_distribution_mine.append(sum(ms["mid_ranks"]))
        if rs["mid_ranks"] != ms["mid_ranks"]:
            rank_sum_diff_when_diff.append(sum(rs["mid_ranks"]) - sum(ms["mid_ranks"]))

    print(f"\nSample (n=5000):")
    print(f"  full shape match: {100*n_match/5000:.2f}%")
    print(f"  mid only match:   {100*n_mid_match/5000:.2f}%")
    print(f"  bot DS rate (mine):   {100*n_bot_ds_mine/5000:.2f}%")
    print(f"  bot DS rate (robust): {100*n_bot_ds_robust/5000:.2f}%")

    print("\nbot_ds (mine, robust) count:")
    for (m, r), c in sorted(bot_ds_diffs.items()):
        print(f"  ({m!s:>5}, {r!s:>5}): {c:>5}  ({100*c/5000:.2f}%)")

    print("\nmid_suited (mine, robust) count:")
    for (m, r), c in sorted(mid_suited_diffs.items()):
        print(f"  ({m!s:>5}, {r!s:>5}): {c:>5}  ({100*c/5000:.2f}%)")

    if rank_sum_diff_when_diff:
        diffs = np.array(rank_sum_diff_when_diff)
        print(f"\nWhen mid differs ({len(diffs):,} cases):")
        print(f"  rank_sum diff (robust − mine):")
        print(f"    mean: {diffs.mean():+.2f}")
        print(f"    median: {np.median(diffs):+.2f}")
        print(f"    p25/p75: {np.quantile(diffs, 0.25):+.0f} / {np.quantile(diffs, 0.75):+.0f}")
        print(f"    share negative (robust mid LOWER): {100*(diffs < 0).mean():.1f}%")
        print(f"    share positive (robust mid HIGHER): {100*(diffs > 0).mean():.1f}%")

    print(f"\nMid rank-sum distributions:")
    print(f"  robust: mean={np.mean(mid_rank_sum_distribution_robust):.2f} median={np.median(mid_rank_sum_distribution_robust):.0f}")
    print(f"  mine:   mean={np.mean(mid_rank_sum_distribution_mine):.2f} median={np.median(mid_rank_sum_distribution_mine):.0f}")

    # Show 30 example mismatches with full hand + shape detail.
    print("\n--- 30 example mismatches ---")
    shown = 0
    for idx in sample_idx:
        if shown >= 30:
            break
        hand = sub_hands[idx]
        robust = int(sub.iloc[idx]["multiway_robust"])
        mine = strategy_hi_only_search(hand)
        rs = shape(hand, robust)
        ms = shape(hand, mine)
        if (rs["top_rank"], rs["mid_ranks"], rs["bot_ranks"]) != \
           (ms["top_rank"], ms["mid_ranks"], ms["bot_ranks"]):
            ranks = list((hand // 4) + 2)
            suits = list(hand % 4)
            suit_str = ["c", "d", "h", "s"]
            cardstr = " ".join(f"{r}{suit_str[s]}" for r, s in zip(ranks, suits))
            print(f"  hand: {cardstr}")
            print(f"    robust top={rs['top_rank']:>2} mid={rs['mid_ranks']!s:>10} bot={rs['bot_ranks']!s:>16} "
                  f"midS={rs['mid_suited']!s:>5} botDS={rs['bot_ds']!s:>5}")
            print(f"    mine   top={ms['top_rank']:>2} mid={ms['mid_ranks']!s:>10} bot={ms['bot_ranks']!s:>16} "
                  f"midS={ms['mid_suited']!s:>5} botDS={ms['bot_ds']!s:>5}")
            print(f"    AC: {sub.iloc[idx]['agreement_class']}")
            shown += 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
