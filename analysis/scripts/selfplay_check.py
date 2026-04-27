"""
Self-play / regret check for the rule chain.

What this measures (and what it does NOT):

  * NOT pure self-play: by symmetry, two players using the same deterministic
    strategy on a uniform random hand distribution have mean net EV == 0
    exactly. That's a math fact, not an empirical question — it tells us
    nothing about strategy quality.

  * What we DO measure: "exploitability gap" of strategy_v3 against each of
    the 4 production opponent profiles. For each sampled hand H:
      best_ev[profile] = engine MC: max EV across all 105 settings.
      v3_ev[profile]   = engine MC: EV of the specific setting strategy_v3
                         picks for H.
    The gap (best_ev - v3_ev) is how much EV the rule chain leaves on the
    table per hand against that profile. Mean gap over many hands is the
    "average regret" — a Nash-distance proxy.

  * If the rule chain were truly Nash, mean gap would be 0 against every
    profile in the panel. In practice we expect small positive gaps (the
    rule chain is a 5-10 rule heuristic, not the solver).

Cost: ~300ms per (hand, profile) MC at samples=1000. For 200 hands × 4
profiles ≈ 4 minutes serial.
"""
from __future__ import annotations

import argparse
import random
import sys
import subprocess
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
sys.path.insert(0, str(HERE))

from tw_analysis.settings import Card  # noqa: E402
from encode_rules import strategy_v3, hand_decompose  # noqa: E402

ENGINE = ROOT / "engine" / "target" / "release" / "tw-engine"
LOOKUP = ROOT / "data" / "lookup_table.bin"

PROFILES = [
    ("MFSuitAware",     "mixed",    "mfsuitaware",  0.9),
    ("OmahaFirst",      "mixed",    "omaha",        0.9),
    ("TopDefensive",    "mixed",    "topdef",       0.9),
    ("RandomWeighted",  "weighted", "mfsuitaware",  0.9),
]


def deal_random_hand(rng: random.Random) -> list[str]:
    """Random 7-card hand as engine-format strings."""
    ranks = "23456789TJQKA"
    suits = "cdhs"
    deck = [r + s for r in ranks for s in suits]
    return rng.sample(deck, 7)


def hand_to_bytes(hand_strs: list[str]) -> np.ndarray:
    """Engine card-byte encoding, sorted ascending (canonical hand format)."""
    arr = np.array([Card.parse(s).idx for s in hand_strs], dtype=np.uint8)
    arr.sort()
    return arr


def bytes_to_strings(arr: np.ndarray) -> list[str]:
    """Inverse: byte array back to engine strings."""
    return [str(Card(int(b))) for b in arr]


def find_setting_index_in_tsv(
    tsv_text: str, want_top: str, want_mid: set[str], want_bot: set[str]
) -> tuple[int, float]:
    """Locate the row of (top, mid_set, bot_set) and return (idx, ev)."""
    for raw in tsv_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 9:
            continue
        idx = int(parts[0])
        ev = float(parts[1])
        top, m1, m2, b1, b2, b3, b4 = parts[2:]
        if top == want_top and {m1, m2} == want_mid and {b1, b2, b3, b4} == want_bot:
            return idx, ev
    raise ValueError("strategy setting not found in MC output")


def run_mc(hand_strs: list[str], opp: str, mix_base: str, mix_p: float,
           samples: int, seed: int) -> str:
    cmd = [
        str(ENGINE), "mc",
        "--hand", " ".join(hand_strs),
        "--samples", str(samples),
        "--tsv",
        "--opponent", opp,
        "--mix-base", mix_base,
        "--mix-p", str(mix_p),
        "--seed", str(seed),
        "--parallel",
        "--lookup", str(LOOKUP),
    ]
    p = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if p.returncode != 0:
        raise RuntimeError(f"engine mc failed: {p.stderr}")
    return p.stdout


def best_ev_from_tsv(tsv_text: str) -> float:
    best = -1e9
    for raw in tsv_text.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split("\t")
        if len(parts) != 9:
            continue
        ev = float(parts[1])
        if ev > best:
            best = ev
    return best


def _positions_to_cards(hand_bytes: np.ndarray, top_pos: int,
                        mid_pos: tuple[int, int]) -> tuple[str, set[str], set[str]]:
    top_card = str(Card(int(hand_bytes[top_pos])))
    mid_cards = {str(Card(int(hand_bytes[i]))) for i in mid_pos}
    bot_pos = [i for i in range(7) if i != top_pos and i not in mid_pos]
    bot_cards = {str(Card(int(hand_bytes[i]))) for i in bot_pos}
    return top_card, mid_cards, bot_cards


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--hands", type=int, default=200,
                    help="number of random hands to sample (default 200)")
    ap.add_argument("--samples", type=int, default=1000,
                    help="MC samples per hand (default 1000)")
    ap.add_argument("--seed", type=int, default=20260426)
    args = ap.parse_args()

    if not ENGINE.exists():
        print(f"ERROR: engine binary not found at {ENGINE}", file=sys.stderr)
        return 2
    if not LOOKUP.exists():
        print(f"ERROR: lookup table not found at {LOOKUP}", file=sys.stderr)
        return 2

    from encode_rules import positions_to_setting_index, decode_tier_positions

    rng = random.Random(args.seed)
    print(f"Sampling {args.hands} hands. Engine MC: samples={args.samples}, "
          f"4 profiles per hand. Expect ~{args.hands * 4 * 300 / 1000:.0f}s.")
    print()

    # Per-profile aggregates.
    sums = {label: {"v3_ev": 0.0, "best_ev": 0.0, "gap": 0.0,
                    "matched": 0, "n": 0}
            for (label, *_) in PROFILES}

    t0 = time.time()
    seed_counter = args.seed
    for hi in range(args.hands):
        hand_strs = deal_random_hand(rng)
        hand_bytes = hand_to_bytes(hand_strs)
        # Strategy_v3 is defined over the canonical sort order (ascending bytes).
        v3_setting = strategy_v3(hand_bytes)
        t_pos, m_pos, b_pos = decode_tier_positions(v3_setting)
        v3_top, v3_mid_set, v3_bot_set = _positions_to_cards(
            hand_bytes, t_pos, m_pos
        )

        for (label, opp, mix_base, mix_p) in PROFILES:
            seed_counter += 1
            tsv = run_mc(hand_strs, opp, mix_base, mix_p,
                         samples=args.samples, seed=seed_counter)
            best_ev = best_ev_from_tsv(tsv)
            v3_idx, v3_ev = find_setting_index_in_tsv(
                tsv, v3_top, v3_mid_set, v3_bot_set
            )
            gap = best_ev - v3_ev
            matched = (gap < 1e-6)
            d = sums[label]
            d["v3_ev"] += v3_ev
            d["best_ev"] += best_ev
            d["gap"] += gap
            d["matched"] += int(matched)
            d["n"] += 1

        if (hi + 1) % 25 == 0 or hi == args.hands - 1:
            elapsed = time.time() - t0
            rate = (hi + 1) / max(elapsed, 1e-6)
            eta = (args.hands - (hi + 1)) / max(rate, 1e-6)
            print(f"  {hi+1:>4}/{args.hands}   "
                  f"elapsed {elapsed:5.0f}s   eta {eta:5.0f}s")

    print()
    print("=" * 78)
    print(f"REGRET vs each profile  ({args.hands} random hands, "
          f"samples={args.samples})")
    print("=" * 78)
    print(f"{'profile':<18} {'mean v3 EV':>12} {'mean best EV':>14} "
          f"{'mean gap':>10} {'match%':>8}")
    for label, *_ in PROFILES:
        d = sums[label]
        n = d["n"]
        print(f"{label:<18} {d['v3_ev']/n:>+12.4f} {d['best_ev']/n:>+14.4f} "
              f"{d['gap']/n:>+10.4f} {100*d['matched']/n:>7.1f}%")

    print()
    print("Interpretation:")
    print("  * mean v3 EV: average net EV per hand if you use strategy_v3.")
    print("    Positive = you BEAT this profile, negative = you LOSE.")
    print("  * mean best EV: average net EV if you played the SOLVER's best "
          "setting.")
    print("    Strictly ≥ mean v3 EV per hand.")
    print("  * mean gap: average EV left on the table by the rule chain. The")
    print("    closer to 0, the closer to Nash against this profile. >0.50 is")
    print("    meaningful, <0.10 is essentially Nash on average.")
    print("  * match%: fraction of sampled hands where v3's setting IS the")
    print("    solver's best.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
