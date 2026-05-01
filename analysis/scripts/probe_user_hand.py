"""
Quick probe: take a user-supplied hand, run the engine MC against all 4
profiles, and report:
  - v3's pick + its per-profile EV
  - per-profile BR (oracle, profile known)
  - argmax_mean (oracle hedge, blind to profile)
  - the user's proposed alternative routing (if they specify it)

Usage:
  python3 analysis/scripts/probe_user_hand.py "Ks Qs 8h 8d 7d 5h Ac" \
    --alt-top Ac --alt-mid "Ks Qs" --alt-bot "8h 8d 7d 5h"
"""
from __future__ import annotations

import argparse
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
from engine import PROFILES, evaluate_all_profiles, find_setting_index  # noqa: E402

_RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
         "T":10,"J":11,"Q":12,"K":13,"A":14}
_SUIT = {"c":0,"d":1,"h":2,"s":3}


def hand_str_to_bytes(hand_str: str) -> np.ndarray:
    cards = hand_str.split()
    bytes_ = sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards)
    return np.array(bytes_, dtype=np.uint8)


def setting_to_str(s) -> str:
    return f"top={s.top}  mid=({s.mid[0]} {s.mid[1]})  bot=({' '.join(s.bot)})"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("hand", help='7 cards e.g. "Ks Qs 8h 8d 7d 5h Ac"')
    ap.add_argument("--alt-top", default=None, help="alt-routing top (1 card)")
    ap.add_argument("--alt-mid", default=None, help="alt-routing mid (2 cards)")
    ap.add_argument("--alt-bot", default=None, help="alt-routing bot (4 cards)")
    ap.add_argument("--samples", type=int, default=2000, help="MC samples per setting")
    args = ap.parse_args()

    hand_str = args.hand
    cards = hand_str.split()
    if len(cards) != 7:
        print(f"ERROR: need 7 cards, got {len(cards)}: {cards}", file=sys.stderr)
        return 1

    print(f"Hand: {hand_str}\n")
    hand_bytes = hand_str_to_bytes(hand_str)

    v3_idx = int(strategy_v3(hand_bytes))
    v5_idx = int(strategy_v5_dt(hand_bytes))
    v7_idx = int(strategy_v7_regression(hand_bytes))

    # MC against all 4 profiles. evaluate_all_profiles is cached per
    # (hand, profile, samples, seed); fresh hand → fresh MC.
    print(f"Running MC at samples={args.samples} on all 4 profiles ...")
    results = evaluate_all_profiles(cards, samples=args.samples, seed=0xC0FFEE)
    profile_ids = [p.id for p in PROFILES]
    n_profiles = len(profile_ids)

    # Build (4, 105) EV grid.
    grid = np.zeros((n_profiles, 105), dtype=np.float64)
    for pi, (_p, mc) in enumerate(results):
        for s in mc.settings:
            grid[pi, s.setting_index] = s.ev

    # Oracle hedges.
    br_per_profile = grid.argmax(axis=1)
    argmax_mean = grid.mean(axis=0).argmax()

    # User's alt routing.
    alt_idx = None
    if args.alt_top and args.alt_mid and args.alt_bot:
        alt_cards = (
            args.alt_top.split()
            + args.alt_mid.split()
            + args.alt_bot.split()
        )
        if len(alt_cards) != 7:
            print(f"ERROR: alt routing needs 1+2+4 = 7 cards, got {len(alt_cards)}",
                  file=sys.stderr)
            return 1
        # Use first profile's mc to look up setting_index (same across profiles).
        mc0 = results[0][1]
        alt_idx = find_setting_index(mc0, alt_cards)

    # Print all the candidates.
    candidates = [
        ("v3 (production)", v3_idx),
        ("v5_dt (DT shape)", v5_idx),
        ("v7_regression (NEW)", v7_idx),
        (f"oracle_argmax_mean (hedge)", int(argmax_mean)),
    ]
    for pi, pid in enumerate(profile_ids):
        candidates.append((f"BR_{pid} (knows opp)", int(br_per_profile[pi])))
    if alt_idx is not None:
        candidates.append(("user's alt routing", alt_idx))

    # Header
    header = f"{'strategy':<28}{'setting (top/mid/bot)':<48}"
    for pid in profile_ids:
        header += f"{'EV vs '+pid:>15}"
    header += f"{'mean EV':>10}"
    print(header)
    print("-" * len(header))

    for label, idx in candidates:
        s = results[0][1].settings[idx]
        s_str = setting_to_str(s)
        evs = [grid[pi, idx] for pi in range(n_profiles)]
        mean_ev = float(np.mean(evs))
        row = f"{label:<28}{s_str:<48}"
        for ev in evs:
            row += f"{ev:>+15.3f}"
        row += f"{mean_ev:>+10.3f}"
        print(row)

    print()
    if alt_idx is not None:
        v3_mean = float(np.mean([grid[pi, v3_idx] for pi in range(n_profiles)]))
        alt_mean = float(np.mean([grid[pi, alt_idx] for pi in range(n_profiles)]))
        delta = alt_mean - v3_mean
        print(f"Alt vs v3 (mean across 4 profiles): {delta:+.3f} EV/hand "
              f"= {delta*10000:+.0f} $/1000h at $10/EV-pt")
        oracle_mean = float(grid.mean(axis=0)[argmax_mean])
        print(f"Oracle ceiling vs v3: {oracle_mean - v3_mean:+.3f} EV/hand "
              f"= {(oracle_mean - v3_mean)*10000:+.0f} $/1000h")
    return 0


if __name__ == "__main__":
    sys.exit(main())
