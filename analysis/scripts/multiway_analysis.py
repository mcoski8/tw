"""
Multiway analysis: does the user's intuition that "multiway play favors
weaker top, stronger mid+bot" hold up against the data?

Approach:
  For each canonical hand, we have 4 best-response setting choices (one per
  opponent profile). The "multiway-robust" setting against a mixed population
  of those 4 archetypes is approximated by the MODE of the 4 settings —
  the choice that's optimal against the most opponents simultaneously.

  When all 4 BRs agree (unanimous, ~27% of hands) the robust answer is
  uncontroversial. When 3-of-4 agree, the 3-of-4 majority is the robust
  choice. When 2-2 splits or all-4-distinct (~24% combined), there's no
  single robust answer — those hands genuinely need a per-opponent read.

Hypothesis test:
  Is the top-card rank in the MULTIWAY-ROBUST setting systematically
  LOWER than in the per-profile heads-up BRs? Same for mid (pair vs
  broadway?), bot (double-suited frequency)?

  If yes, the intuition is empirically supported.
  If no, it's wrong — and we have a data-backed answer to teach in the
  trainer.

Outputs:
  * Top-rank histogram comparison (heads-up BR vs multiway-robust)
  * Mid-tier composition comparison (pair %, mean rank-sum)
  * Bot-tier composition comparison (double-suited %, suit-distribution)
  * Hypothesis verdict per axis (top / mid / bot)
"""
from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402

from tw_analysis import read_canonical_hands, read_br_file  # noqa: E402
from tw_analysis.cross_model import build_cross_model  # noqa: E402


# --- Setting-index → tier-composition decoder (works without full HandSetting decode) ---
# Setting index = top_outer_idx * 15 + mid_inner_idx
# Top-outer: which of the 7 hand cards goes to top (0..6).
# Mid-inner: which pair of the remaining 6 indices forms the middle (0..14, lex order).
# Bottom = the other 4 of the 6 remaining.
#
# Canonical hands store cards sorted ASCENDING by card index. Card index =
# (rank-2)*4 + suit, so high-rank/high-suit cards have higher index.

# Pre-compute the 15 mid-pair index lookups: 6-choose-2 in lex order.
_MID_PAIRS_OF_6 = []
for a in range(6):
    for b in range(a + 1, 6):
        _MID_PAIRS_OF_6.append((a, b))
assert len(_MID_PAIRS_OF_6) == 15


def decode_tier_indices(setting_index: int) -> tuple[int, tuple[int, int], tuple[int, int, int, int]]:
    """
    Given a setting_index (0..104), return (top_outer_idx, mid_pair_indices, bot_indices)
    where indices refer to the canonical hand's card array (length 7).

    All indices in the returned bot tuple are positions within the original 7-card hand,
    NOT within the remaining-6 array.
    """
    top_outer = setting_index // 15
    mid_inner = setting_index % 15

    # Indices 0..6 of the original 7-card hand, with top_outer removed.
    remaining_positions = [i for i in range(7) if i != top_outer]
    a_in_6, b_in_6 = _MID_PAIRS_OF_6[mid_inner]
    mid_positions = (remaining_positions[a_in_6], remaining_positions[b_in_6])
    bot_positions = tuple(p for p in remaining_positions if p not in mid_positions)
    return top_outer, mid_positions, bot_positions


def card_rank(card_byte: int) -> int:
    """Rank 2-14 from a packed Card.idx (2c=0 → rank 2, As=51 → rank 14)."""
    return (int(card_byte) // 4) + 2


def card_suit(card_byte: int) -> int:
    """Suit 0..3 from a packed Card.idx."""
    return int(card_byte) % 4


def setting_features(hand_cards: np.ndarray, setting_index: int) -> dict:
    """
    Return a dict of features for a (canonical hand, setting) pair.

    Features tracked (for the multiway hypothesis test):
      - top_rank: 2..14
      - mid_is_pair: bool
      - mid_rank_sum: int (sum of mid two ranks)
      - bot_is_double_suited: bool (suit distribution = (2,2))
      - bot_max_suit_count: int (1..4)
      - bot_rank_sum: int
    """
    top_pos, mid_pos, bot_pos = decode_tier_indices(setting_index)
    top_card = int(hand_cards[top_pos])
    mid_cards = [int(hand_cards[i]) for i in mid_pos]
    bot_cards = [int(hand_cards[i]) for i in bot_pos]

    mid_ranks = [card_rank(c) for c in mid_cards]
    bot_ranks = [card_rank(c) for c in bot_cards]
    bot_suits = [card_suit(c) for c in bot_cards]
    bot_suit_counts = Counter(bot_suits)
    sorted_suit_counts = sorted(bot_suit_counts.values(), reverse=True)

    return {
        "top_rank": card_rank(top_card),
        "mid_is_pair": mid_ranks[0] == mid_ranks[1],
        "mid_rank_sum": sum(mid_ranks),
        "bot_is_double_suited": sorted_suit_counts[:2] == [2, 2],
        "bot_max_suit_count": sorted_suit_counts[0] if sorted_suit_counts else 0,
        "bot_rank_sum": sum(bot_ranks),
    }


def mode_setting(per_profile_settings: tuple[int, ...]) -> tuple[int, str]:
    """
    Return (mode_setting_index, agreement_class) for an N-tuple of settings.
    agreement_class ∈ {'unanimous', '3of4', '2of4', 'split2_2', 'split1_1_1_1'}
    """
    counts = Counter(per_profile_settings)
    most_common = counts.most_common()
    top_count = most_common[0][1]
    n = len(per_profile_settings)
    if n != 4:
        # Generic fallback
        if top_count == n:
            return most_common[0][0], "unanimous"
        return most_common[0][0], f"mode={top_count}of{n}"

    if top_count == 4:
        cls = "unanimous"
    elif top_count == 3:
        cls = "3of4"
    elif top_count == 2 and len(most_common) == 2:
        cls = "split2_2"
    elif top_count == 2 and len(most_common) == 3:
        cls = "2of4"  # 2-1-1
    elif top_count == 1:
        cls = "split1_1_1_1"
    else:
        cls = "other"
    return most_common[0][0], cls


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--canonical", type=Path,
                    default=ROOT / "data" / "canonical_hands.bin")
    ap.add_argument("--bin-dir", type=Path,
                    default=ROOT / "data" / "best_response_cloud")
    ap.add_argument("--sample", type=int, default=0,
                    help="if > 0, analyze a random sample of this many hands "
                    "(0 = all 6M hands)")
    ap.add_argument("--seed", type=int, default=20260426)
    args = ap.parse_args()

    print("Loading canonical hands...")
    canonical = read_canonical_hands(args.canonical)
    n_total = canonical.header.num_hands
    cards_arr = canonical.hands  # (n_total, 7) uint8
    print(f"  {n_total:,} canonical hands")

    print("Loading 4 best-response files...")
    profile_files = [
        ("MF-SA", args.bin_dir / "mfsuitaware_mixed90.bin"),
        ("Omaha", args.bin_dir / "omahafirst_mixed90.bin"),
        ("TopDef", args.bin_dir / "topdefensive_mixed90.bin"),
        ("RandWeighted", args.bin_dir / "randomweighted.bin"),
    ]
    brs = []
    for label, p in profile_files:
        br = read_br_file(p, mode="memmap")
        brs.append(br)
        print(f"  {label}: {len(br):,} records")

    cm = build_cross_model(brs)
    settings = cm.settings  # shape (n_total, 4)
    profile_labels = ["MF-SA", "Omaha", "TopDef", "RandWeighted"]

    # Sample selection.
    if args.sample > 0 and args.sample < n_total:
        rng = np.random.default_rng(args.seed)
        idxs = rng.choice(n_total, args.sample, replace=False)
        idxs.sort()
        print(f"\nAnalyzing random sample of {args.sample:,} hands "
              f"(seed={args.seed})")
    else:
        idxs = np.arange(n_total)
        print(f"\nAnalyzing ALL {n_total:,} canonical hands")

    # Buckets.
    feat_per_profile = [[] for _ in range(4)]
    feat_robust = []
    feat_robust_unanimous_only = []
    agreement_class_counts = Counter()

    print("Computing features (this is the hot loop — ~3-5 min for full 6M)...")
    for k, ci in enumerate(idxs):
        hand = cards_arr[ci]  # uint8[7]
        per_profile = tuple(int(settings[ci, j]) for j in range(4))
        mode_set, agreement = mode_setting(per_profile)
        agreement_class_counts[agreement] += 1

        # Per-profile features (heads-up BR for each archetype).
        for j in range(4):
            feat_per_profile[j].append(setting_features(hand, per_profile[j]))

        # Multiway-robust features (the mode).
        feat_robust.append(setting_features(hand, mode_set))

        # Subset: only hands where all 4 agree (cleanest "robust" signal).
        if agreement == "unanimous":
            feat_robust_unanimous_only.append(setting_features(hand, mode_set))

        if (k + 1) % 500_000 == 0:
            print(f"  ...{k + 1:,}/{len(idxs):,}")

    print()
    print("=" * 72)
    print("Multiway analysis results")
    print("=" * 72)
    print()
    n = len(idxs)
    print(f"Sample size: {n:,} hands")
    print()
    print("Agreement class breakdown (4 profiles per hand):")
    for cls in ("unanimous", "3of4", "2of4", "split2_2", "split1_1_1_1"):
        c = agreement_class_counts.get(cls, 0)
        print(f"  {cls:<18} {c:>10,}  ({100.0 * c / n:5.2f}%)")
    print()

    def summarize(rows: list[dict], label: str) -> dict:
        if not rows:
            return {}
        top_ranks = np.array([r["top_rank"] for r in rows])
        mid_pair_rate = float(np.mean([r["mid_is_pair"] for r in rows]))
        mid_sum = np.array([r["mid_rank_sum"] for r in rows])
        bot_ds_rate = float(np.mean([r["bot_is_double_suited"] for r in rows]))
        bot_max_suit = np.array([r["bot_max_suit_count"] for r in rows])
        bot_sum = np.array([r["bot_rank_sum"] for r in rows])
        out = {
            "label": label,
            "n": len(rows),
            "top_rank_mean": float(top_ranks.mean()),
            "top_rank_median": float(np.median(top_ranks)),
            "mid_pair_rate": mid_pair_rate,
            "mid_rank_sum_mean": float(mid_sum.mean()),
            "bot_double_suited_rate": bot_ds_rate,
            "bot_max_suit_mean": float(bot_max_suit.mean()),
            "bot_rank_sum_mean": float(bot_sum.mean()),
        }
        return out

    print(f"{'Strategy source':<28} {'top_rank':>10} {'mid_pair%':>10} {'mid_sum':>9} {'bot_DS%':>9} {'bot_sum':>9}")
    print("-" * 72)
    rows = []
    for j, lab in enumerate(profile_labels):
        s = summarize(feat_per_profile[j], f"BR vs {lab} (heads-up)")
        rows.append(s)
        print(f"{s['label']:<28} {s['top_rank_mean']:>10.2f} "
              f"{100*s['mid_pair_rate']:>9.2f}% {s['mid_rank_sum_mean']:>9.2f} "
              f"{100*s['bot_double_suited_rate']:>8.2f}% {s['bot_rank_sum_mean']:>9.2f}")

    print()
    s_robust = summarize(feat_robust, "Multiway-robust (mode)")
    print(f"{s_robust['label']:<28} {s_robust['top_rank_mean']:>10.2f} "
          f"{100*s_robust['mid_pair_rate']:>9.2f}% {s_robust['mid_rank_sum_mean']:>9.2f} "
          f"{100*s_robust['bot_double_suited_rate']:>8.2f}% {s_robust['bot_rank_sum_mean']:>9.2f}")

    s_unan = summarize(feat_robust_unanimous_only, "Robust (unanimous only)")
    if s_unan:
        print(f"{s_unan['label']:<28} {s_unan['top_rank_mean']:>10.2f} "
              f"{100*s_unan['mid_pair_rate']:>9.2f}% {s_unan['mid_rank_sum_mean']:>9.2f} "
              f"{100*s_unan['bot_double_suited_rate']:>8.2f}% {s_unan['bot_rank_sum_mean']:>9.2f}")

    print()
    print("=" * 72)
    print("Hypothesis test: 'Multiway favors weaker top, stronger mid+bot'")
    print("=" * 72)
    avg_headsup_top = float(np.mean([r["top_rank_mean"] for r in rows]))
    avg_headsup_mid_pair = float(np.mean([r["mid_pair_rate"] for r in rows]))
    avg_headsup_mid_sum = float(np.mean([r["mid_rank_sum_mean"] for r in rows]))
    avg_headsup_bot_ds = float(np.mean([r["bot_double_suited_rate"] for r in rows]))
    avg_headsup_bot_sum = float(np.mean([r["bot_rank_sum_mean"] for r in rows]))

    delta_top  = s_robust["top_rank_mean"]      - avg_headsup_top
    delta_mid_pair = s_robust["mid_pair_rate"]  - avg_headsup_mid_pair
    delta_mid_sum  = s_robust["mid_rank_sum_mean"] - avg_headsup_mid_sum
    delta_bot_ds   = s_robust["bot_double_suited_rate"] - avg_headsup_bot_ds
    delta_bot_sum  = s_robust["bot_rank_sum_mean"]    - avg_headsup_bot_sum

    print(f"  Δ top rank            : {delta_top:+.3f}  (negative supports 'weaker top')")
    print(f"  Δ mid pair rate       : {100*delta_mid_pair:+.2f}%  (positive supports 'stronger mid')")
    print(f"  Δ mid rank-sum        : {delta_mid_sum:+.3f}")
    print(f"  Δ bot double-suited % : {100*delta_bot_ds:+.2f}%  (positive supports 'stronger bot')")
    print(f"  Δ bot rank-sum        : {delta_bot_sum:+.3f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
