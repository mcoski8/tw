"""
Session 42 — v38 = v37 + Rule 8 (two_pair: where do the two pairs go?).

verify_rule_X_v33_two_pair.py + probe_two_pair_boundary.py walked the
full 1.34M two_pair population (22.27% of the canonical hand grid):

  Always RA (mid=HIGH pair):    Δ -$87.71/1000h whole-grid
  Always RB (mid=LOW pair):     Δ +$68.46/1000h whole-grid
  Always RC (double-pair bot):  Δ -$1,988    /1000h whole-grid
  Best per cell (oracle ceil.): Δ +$624.65   /1000h whole-grid

Per-(high, low)-cell winners across the 78 cells:
  - high ∈ {A}:      RA wins on 10 of 12 cells (AA stays in mid)
  - high ∈ {T,J,Q,K}: RB wins on 33 of 38 cells (broadway non-A → bot)
  - high ∈ {6,7,8,9}: RA wins on 22 of 22 cells
  - high ∈ {2,3,4}:   RC wins on 5 of 6 cells (double-pair bot)
  - high = 5: transition zone (RB / RC mixed)

Cleanest 1-condition rule (boundary search):
  "RC if high ≤ 4, elif T ≤ high ≤ K then RB, else RA"
  Δ = +$196.89/1000h whole-grid (within-cat $+883.9)
  Captures 32% of the per-cell oracle ceiling.

Compare to other tested rules:
  RB if T<=high<=K else RA              (three_pair Rule-7 shape, no RC):
                                        +$184.52/1000h
  RB if high >= T else RA               +$116.74/1000h
  RB always                              +$68.46/1000h

The RC tail for high ∈ {2,3,4} adds +$12.4/1000h vs the no-RC variant.

Rule 8 (two_pair):
  TOP = HIGHEST singleton (always)

  if high_pair ≤ 4:
      MID = the 2 lower singletons       (RC: double-pair bot)
      BOT = HIGH pair + LOW pair (4 cards = both pairs intact)
  elif 10 ≤ high_pair ≤ 13:  (T, J, Q, K — broadway non-A)
      MID = LOW pair                     (RB)
      BOT = HIGH pair + 2 lower singletons
  else:  (high = A, or 5 ≤ high ≤ 9)
      MID = HIGH pair                    (RA)
      BOT = LOW pair + 2 lower singletons

Why these regimes:
  - AA stays in mid (like three_pair Rule 7): pairing AA in Hold'em is
    so dominant that you don't move it.
  - A broadway non-Ace pair (T-K) on the bot anchors a strong 2-pair
    Omaha hand; the high pair becomes a trips draw on board pairs.
  - Below T (high pair = 5..9), the "high" pair isn't strong enough on
    the bot to outpace what an opponent might hit; keep it in mid for
    Hold'em equity.
  - For very low pairs (high ≤ 4), neither pair anchors the bot well.
    Better to keep both pairs together on the bot (= 2-pair on board)
    and use the singletons to play the mid as a high-card Hold'em hand.

Production-ship candidate: replaces v37 as the strategy of record.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402


def _detect_rule8_two_pair_setting(hand: np.ndarray) -> Optional[int]:
    """If hand is exactly two_pair (2 pairs + 3 singletons, no trips/quads),
    return Rule 8's pick. Else return None (caller falls back to v37)."""
    h = np.asarray(hand, dtype=np.uint8)
    if h.shape[0] != 7:
        return None
    ranks = (h // 4) + 2
    rank_counts = np.bincount(ranks, minlength=15)
    n_pairs = int(sum(rank_counts[r] == 2 for r in range(2, 15)))
    n_trips = int(sum(rank_counts[r] == 3 for r in range(2, 15)))
    n_quads = int(sum(rank_counts[r] >= 4 for r in range(2, 15)))
    if n_pairs != 2 or n_trips != 0 or n_quads != 0:
        return None

    pair_ranks = sorted([r for r in range(2, 15) if rank_counts[r] == 2],
                        reverse=True)
    sing_ranks = sorted([r for r in range(2, 15) if rank_counts[r] == 1],
                        reverse=True)
    hpr, lpr = pair_ranks
    s_hi, s_mid_r, s_lo = sing_ranks

    pos_hi_pair = sorted([j for j in range(7) if int(ranks[j]) == hpr])
    pos_lo_pair = sorted([j for j in range(7) if int(ranks[j]) == lpr])
    pos_s_hi = next(j for j in range(7) if int(ranks[j]) == s_hi)
    pos_s_mid = next(j for j in range(7) if int(ranks[j]) == s_mid_r)
    pos_s_lo = next(j for j in range(7) if int(ranks[j]) == s_lo)

    # Boundary: top is always the highest singleton; mid depends on
    # high-pair rank.
    if hpr <= 4:
        # RC: double-pair bot (high+low pairs together).
        return int(_setting_index_from_tmb(pos_s_hi, pos_s_mid, pos_s_lo))
    if 10 <= hpr <= 13:
        # RB: low pair to mid (broadway non-A → bot anchors Omaha 2-pair).
        return int(_setting_index_from_tmb(pos_s_hi,
                                           pos_lo_pair[0], pos_lo_pair[1]))
    # RA: high pair to mid (5..9 or A).
    return int(_setting_index_from_tmb(pos_s_hi,
                                       pos_hi_pair[0], pos_hi_pair[1]))


def strategy_v38_rule8_two_pair(hand: np.ndarray) -> int:
    """v38 = v37 + Rule 8 (two_pair routing override)."""
    chosen = _detect_rule8_two_pair_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v37_rule7_three_pair(hand))


if __name__ == "__main__":
    from tw_analysis.canonical import canonicalize
    RANK = {"2": 2, "3": 3, "4": 4, "5": 5, "6": 6, "7": 7, "8": 8, "9": 9,
            "T": 10, "J": 11, "Q": 12, "K": 13, "A": 14}
    SUIT = {"c": 0, "d": 1, "h": 2, "s": 3}

    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                        dtype=np.uint8)

    cases = [
        # high=A → RA (high pair to mid)
        ("Ah Ad Kc Kh 7s 5d 2c",
         "AAKK + 752 (high=A) → RA: mid=AA, bot=KK+75"),
        ("Ah Ad 8c 8h 6s 4d 3c",
         "AA88 + 643 (high=A) → RA: mid=AA, bot=88+64"),
        # high=K → RB (low pair to mid)
        ("Kh Kd Qc Qh 7s 5d 2c",
         "KKQQ + 752 (high=K) → RB: mid=QQ, bot=KK+75"),
        ("Kh Kd 8c 8h 7s 5d 2c",
         "KK88 + 752 (high=K) → RB: mid=88, bot=KK+75"),
        # high=Q → RB
        ("Qh Qd Jc Jh 9s 7d 5c",
         "QQJJ + 975 (high=Q) → RB: mid=JJ, bot=QQ+97"),
        # high=J → RB
        ("Jh Jd Tc Th 9s 7d 5c",
         "JJTT + 975 (high=J) → RB: mid=TT, bot=JJ+97"),
        # high=T → RB
        ("Th Td 9c 9h 7s 5d 2c",
         "TT99 + 752 (high=T) → RB: mid=99, bot=TT+75"),
        # high=9 → RA
        ("9h 9d 8c 8h 7s 5d 2c",
         "9988 + 752 (high=9) → RA: mid=99, bot=88+75"),
        # high=6 → RA
        ("6h 6d 5c 5h 4s 3d 2c",
         "6655 + 432 (high=6) → RA: mid=66, bot=55+43"),
        # high=4 → RC (double-pair bot)
        ("4h 4d 3c 3h 8s 6d 2c",
         "4433 + 862 (high=4) → RC: mid=62, bot=44+33"),
        # high=2 → RC (impossible: high≥3 always since low<high)
        # high=3, low=2 → RC
        ("3h 3d 2c 2h Qs 8d 5c",
         "3322 + Q85 (high=3) → RC: mid=85, bot=33+22"),
    ]
    print(f"{'hand':<28}{'desc':<60}{'v37':>5}  {'v38':>5}  diff")
    for s, label in cases:
        h_arr = canonicalize(hh(*s.split()))
        v37 = strategy_v37_rule7_three_pair(h_arr)
        v38 = strategy_v38_rule8_two_pair(h_arr)
        marker = "*" if v37 != v38 else " "
        print(f"  {s:<26}{label:<60}{v37:>5d}  {v38:>5d}  {marker}")
