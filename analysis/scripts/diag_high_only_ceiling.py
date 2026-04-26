"""
Diagnose high_only:
  1. Agreement-class distribution within high_only.
  2. Per-profile BR shape-agreement of hi_only_search vs each individual
     profile's BR (instead of multiway_robust). If we score much higher
     against MFSA than against multiway_robust, the rule chain may be
     mining-saturated and the ceiling is set by mode-noise.
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
sys.path.insert(0, str(HERE))

from tw_analysis import read_canonical_hands  # noqa: E402
from tw_analysis.features import decode_tier_positions  # noqa: E402
from encode_rules import strategy_hi_only_search  # noqa: E402


def shape(hand, setting):
    t, m, b = decode_tier_positions(int(setting))
    ranks = (hand // 4) + 2
    return (
        int(ranks[t]),
        tuple(sorted(int(ranks[i]) for i in m)),
        tuple(sorted(int(ranks[i]) for i in b)),
    )


def main() -> int:
    canonical = read_canonical_hands(ROOT / "data" / "canonical_hands.bin")
    cards = canonical.hands
    df = pq.read_table(
        ROOT / "data" / "feature_table.parquet",
        columns=["category", "agreement_class", "multiway_robust",
                  "br_mfsuitaware", "br_omaha", "br_topdef", "br_weighted"],
    ).to_pandas()

    mask = (df["category"] == "high_only").values
    sub = df[mask].reset_index(drop=True)
    sub_hands = cards[mask]
    n = len(sub)
    print(f"high_only: {n:,} hands")

    print("\nAgreement-class within high_only:")
    ac_counts = sub["agreement_class"].value_counts(normalize=True)
    for ac in ("unanimous", "3of4", "2of4", "split2_2", "split1_1_1_1"):
        share = float(ac_counts.get(ac, 0))
        print(f"  {ac:<18} {100*share:5.2f}%")

    # Sample for shape-agreement against each profile.
    rng = np.random.default_rng(0)
    sample_idx = rng.choice(n, 50_000, replace=False)

    print(f"\nShape-agreement of hi_only_search on {len(sample_idx):,} sampled high_only hands:")
    targets = {
        "multiway_robust":  sub["multiway_robust"].values,
        "br_mfsuitaware":   sub["br_mfsuitaware"].values,
        "br_omaha":         sub["br_omaha"].values,
        "br_topdef":        sub["br_topdef"].values,
        "br_weighted":      sub["br_weighted"].values,
    }

    for name, tgt in targets.items():
        n_match = 0
        for idx in sample_idx:
            hand = sub_hands[idx]
            mine = strategy_hi_only_search(hand)
            if shape(hand, mine) == shape(hand, int(tgt[idx])):
                n_match += 1
        print(f"  vs {name:<20} shape-agreement = {100*n_match/len(sample_idx):.2f}%")

    # Inter-profile agreement.
    print("\nInter-profile shape-agreement on the same sample:")
    profs = ["br_mfsuitaware", "br_omaha", "br_topdef", "br_weighted"]
    for i, p1 in enumerate(profs):
        for p2 in profs[i+1:]:
            v1 = sub[p1].values
            v2 = sub[p2].values
            n_match = 0
            for idx in sample_idx:
                hand = sub_hands[idx]
                if shape(hand, int(v1[idx])) == shape(hand, int(v2[idx])):
                    n_match += 1
            print(f"  {p1} ↔ {p2}: {100*n_match/len(sample_idx):.2f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
