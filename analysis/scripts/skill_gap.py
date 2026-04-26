"""
Skill-gap analysis: how much EV does optimal play extract over the naive
"sort cards descending and slice [1, 2, 4]" strategy (= setting index 104)?

For each of the 3 production opponent profiles currently on disk, sample
N random canonical hands, run Monte Carlo for all 105 settings, and report:

  * mean EV of optimal best-response play
  * mean EV of always-setting-104 (naive) play
  * the gap (mean EV per hand the optimizer extracts vs the naive player)
  * how many hands of play it takes for the gap to dominate per-hand variance

This is the empirical answer to "is Taiwanese Poker just luck?"
If the gap is large relative to per-hand standard deviation, the game is
skill-driven and the optimizer wins reliably over reasonable session lengths.
If the gap is small, then yes, your friends are right and it's a coin flip.
"""
from __future__ import annotations

import argparse
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import numpy as np  # noqa: E402

from tw_analysis import read_canonical_hands  # noqa: E402
from trainer.src.engine import (  # noqa: E402
    PROFILES,
    evaluate_hand_profile,
)


SETTING_104 = 104  # the "naive sort-and-slice" enumeration position


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hands", type=int, default=200,
                    help="number of canonical hands to sample (default 200)")
    ap.add_argument("--samples", type=int, default=1000,
                    help="MC samples per setting (default 1000, matches solver)")
    ap.add_argument("--seed", type=int, default=20260424)
    args = ap.parse_args()

    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    n_total = canonical.header.num_hands

    rng = random.Random(args.seed)
    indices = rng.sample(range(n_total), args.hands)

    # All 4 production profiles.
    target_profiles = list(PROFILES)

    print(f"Sampling {args.hands} canonical hands; {args.samples} MC samples/setting; "
          f"{len(target_profiles)} opponent profiles.")
    print(f"Total MC runs: {args.hands * len(target_profiles)} "
          f"(estimated wall time: ~{args.hands * len(target_profiles) * 0.3:.0f}s)")
    print()

    # Per-profile rows of (best_ev, naive_ev) for each sampled hand.
    results: dict[str, list[tuple[float, float]]] = {p.id: [] for p in target_profiles}

    for k, idx in enumerate(indices, start=1):
        hand_cards = canonical.hand_cards(idx)
        hand_str_list = [str(c) for c in hand_cards]
        for p in target_profiles:
            mc = evaluate_hand_profile(hand_str_list, p, samples=args.samples)
            best_ev = mc.best().ev
            naive_ev = mc.settings[SETTING_104].ev
            results[p.id].append((best_ev, naive_ev))
        if k % 20 == 0:
            print(f"  ...{k}/{args.hands} hands done")

    print()
    print("=" * 72)
    print(f"Skill-gap results (N={args.hands} hands per profile)")
    print("=" * 72)

    for p in target_profiles:
        rows = np.array(results[p.id])
        best = rows[:, 0]
        naive = rows[:, 1]
        gap = best - naive

        # Sample standard deviation of per-hand EV among optimal play —
        # a rough proxy for the variance a skilled player faces.
        # (Real variance includes board variance which we already averaged
        # over via MC; this is variance ACROSS hands, ie how much hand
        # quality differs.)
        sd_best = float(best.std(ddof=1))
        sd_gap = float(gap.std(ddof=1))

        print()
        print(f"Profile: {p.label}")
        print(f"  mean EV of OPTIMAL play    : {best.mean():+.4f}  (sd across hands {sd_best:.3f})")
        print(f"  mean EV of NAIVE (idx 104) : {naive.mean():+.4f}")
        print(f"  GAP (optimizer wins by)    : {gap.mean():+.4f} per hand")
        print(f"  sd of gap across hands     : {sd_gap:.3f}")
        # How many hands until the optimizer's edge clears 2-sigma noise?
        # We use sd_best as the per-hand variance proxy (conservative).
        if gap.mean() > 0:
            hands_to_2sigma = (2.0 * sd_best / gap.mean()) ** 2
            print(f"  → after {hands_to_2sigma:.0f} hands, edge dominates 2-sigma noise.")
        # Distribution of gap.
        n_strict_loss = int((gap < -0.01).sum())
        n_tie         = int((np.abs(gap) <= 0.01).sum())
        n_strict_win  = int((gap > 0.01).sum())
        print(f"  per-hand outcome (vs naive): "
              f"optimizer better on {n_strict_win} hands, "
              f"tied on {n_tie}, "
              f"naive better on {n_strict_loss}")

    print()
    print("Verdict — is the game skill-driven?")
    overall_gaps = np.array([
        np.mean([row[0] - row[1] for row in results[p.id]])
        for p in target_profiles
    ])
    overall_sd = np.array([
        np.std([row[0] for row in results[p.id]], ddof=1)
        for p in target_profiles
    ])
    avg_gap = float(overall_gaps.mean())
    avg_sd = float(overall_sd.mean())
    print(f"  Cross-profile mean gap        : {avg_gap:+.3f} EV / hand")
    print(f"  Cross-profile mean sd         : {avg_sd:.3f} EV / hand (per-hand variability)")
    if avg_gap > 0:
        n_hands = (2.0 * avg_sd / avg_gap) ** 2
        print(f"  Hands required for 2-sigma confidence in skill edge: ~{n_hands:.0f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
