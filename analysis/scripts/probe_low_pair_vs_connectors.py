"""
Targeted probe for the user's Q2B: with a LOW pair (22-55), do the
"other cards" (suitedness/connectivity of the broadway non-pair cards)
ever flip the routing away from "pair to mid"?

Test 6 hands that vary along two axes:
  - Low pair: 22 / 55
  - Companion structure: suited connectors / unsuited high cards / single
                         broadway + low junk

Run each through v3, v7, oracle. Report which hands the strategies disagree
on and what wins.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SCRIPTS), str(SRC), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from encode_rules import strategy_v3  # noqa: E402
from strategy_v5_dt import strategy_v5_dt  # noqa: E402
from strategy_v7_regression import strategy_v7_regression  # noqa: E402
from engine import PROFILES, evaluate_all_profiles  # noqa: E402

_RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
         "T":10,"J":11,"Q":12,"K":13,"A":14}
_SUIT = {"c":0,"d":1,"h":2,"s":3}


def hand_to_bytes(card_strs):
    return np.array(sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in card_strs), dtype=np.uint8)


HANDS = [
    ("22 + Ks Js suited connector mid", "Ks Js Td 8c 5h 2c 2d"),
    ("22 + Ks Qs suited broadway",      "Ks Qs Tc 7d 5h 2c 2d"),
    ("22 + Ah Kc unsuited highs",       "Ah Kc Td 8s 5h 2c 2d"),
    ("22 + Js Td suited (1-gap)",       "Js Td 9c 7d 5h 2c 2d"),
    ("55 + Ks Js suited connector mid", "Ks Js Td 8c 7h 5c 5d"),
    ("55 + Ah Kc unsuited highs",       "Ah Kc Td 8s 7h 5c 5d"),
]


def main() -> int:
    profile_ids = [p.id for p in PROFILES]
    print(f"{'hand':<46}{'v3':>10}{'v7':>10}{'oracle':>10}{'mean Δ v7-v3':>16}{'mean Δ oracle-v7':>20}")
    print("-" * 120)
    for label, hand_str in HANDS:
        h = hand_to_bytes(hand_str.split())
        v3_idx = int(strategy_v3(h))
        v7_idx = int(strategy_v7_regression(h))
        results = evaluate_all_profiles(hand_str.split(), samples=2000, seed=0xC0FFEE)
        grid = np.zeros((4, 105), dtype=np.float64)
        for pi, (_p, mc) in enumerate(results):
            for s in mc.settings:
                grid[pi, s.setting_index] = s.ev

        oracle_idx = int(grid.mean(axis=0).argmax())
        v3_mean = float(grid.mean(axis=0)[v3_idx])
        v7_mean = float(grid.mean(axis=0)[v7_idx])
        oracle_mean = float(grid.mean(axis=0)[oracle_idx])
        delta_v7_v3 = (v7_mean - v3_mean) * 10000
        delta_oracle_v7 = (oracle_mean - v7_mean) * 10000

        print(f"{label:<46}{v3_idx:>10}{v7_idx:>10}{oracle_idx:>10}"
              f"{delta_v7_v3:>+12.0f}/1000h "
              f"{delta_oracle_v7:>+18.0f}/1000h")
        # Print actual setting layouts for v3, v7, oracle.
        for tag, idx in (("v3", v3_idx), ("v7", v7_idx), ("oracle", oracle_idx)):
            s = results[0][1].settings[idx]
            print(f"  {tag:<8} top={s.top}  mid=({s.mid[0]} {s.mid[1]})  bot=({' '.join(s.bot)})  "
                  f"per-profile EV: " +
                  " ".join(f"{pid}={grid[pi, idx]:+.2f}" for pi, pid in enumerate(profile_ids)))
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
