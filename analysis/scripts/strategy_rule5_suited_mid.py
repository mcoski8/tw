"""
Session 31 — Rule 5: high_only suited high mid.

Distillation of v20's gated suited features (Session 31, see distill
output for v20_dt_model.npz, "TOP GATED-SUITED SPLITS" section). The
v20 ML champion's high_only EV gain (-$413/1000h vs v18e) is driven by
the gated `max_suited_pair_high_rank_g` feature.

The probe `probe_v20_high_only_routing.py` confirmed:
  - oracle picks suited-mid 53.7% of the time on high_only;
    v18e picks 28.4%, v20 lifts to 36.9%.
  - v20's gain peaks at max_suited_pair_high_rank_g in 11..12 (J/Q
    suited): +$58 / +$53 per 1000h on slice. Tapers down for AKs
    holdings where alternative routings compete.
  - 147K high_only hands flip from non-suited mid (v18e) to suited mid
    (v20); on those v20 saves $+257/1000h on slice = $+30/1000h on the
    high_only category.

**Rule 5 statement:** When the hand is high_only (no pair / trip / quad)
and there exists a same-suit pair of cards where the higher card is
rank 9 or above (9, T, J, Q, K, or A), place those two suited cards
together in your middle hand — even if it displaces the default
"2nd-and-3rd-highest cards in mid" choice. Highest non-mid card goes on
top, the remaining 4 go to bot.

Tie-breaking among multiple suited pairs: prefer the pair with the
highest max-rank, then the highest min-rank.

This rule is the human-memorizable approximation of v20's gated
high_only routing. It does not capture v20 fully (oracle still beats it
by ~$280/1000h on high_only), but it's a clean 30-second decision rule
that picks up part of the gap and is consistent with what every
solver-validated DT discovers.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

from strategy_v8_hybrid import strategy_v8_hybrid  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

RULE5_MIN_HIGH_RANK = 9  # max-rank threshold for "high suited pair"


def _detect_rule5_setting(hand_bytes: np.ndarray) -> int | None:
    """If hand qualifies for Rule 5 (high_only with a suited pair whose
    max-rank >= 9), return the chosen setting_index; else None.

    Selection: among suited pairs with max-rank >= 9, pick the one with
    the largest max-rank (then largest min-rank). Place those two in
    mid, highest remaining card on top, the other 4 on bot.
    """
    if hand_bytes.shape[0] != 7:
        return None
    ranks = (hand_bytes // 4) + 2  # 2..14
    suits = hand_bytes & 0b11

    # high_only gate: all 7 ranks distinct.
    if len(set(int(r) for r in ranks)) != 7:
        return None

    best = None  # (max_rank, min_rank, i, j) with i < j
    for i in range(7):
        for j in range(i + 1, 7):
            if suits[i] == suits[j]:
                ri, rj = int(ranks[i]), int(ranks[j])
                hi = ri if ri > rj else rj
                lo = ri if ri < rj else rj
                if hi >= RULE5_MIN_HIGH_RANK:
                    cand = (hi, lo, i, j)
                    if best is None or cand > best:
                        best = cand
    if best is None:
        return None

    _, _, i, j = best
    # Highest non-mid card goes on top. Canonical sort is ascending by
    # card-index, and rank dominates suit in card-index, so the largest
    # remaining position is also the highest-rank remaining card.
    rest = [k for k in range(7) if k != i and k != j]
    top_idx = rest[-1]
    return _setting_index_from_tmb(top_idx, i, j)


def strategy_rule5_suited_mid(hand: np.ndarray) -> int:
    chosen = _detect_rule5_setting(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v8_hybrid(hand))


if __name__ == "__main__":
    # Self-test: run a few sample hands and print the chosen setting.
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,"T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"c":0,"d":1,"h":2,"s":3}

    def hh(*cards):
        bytes_ = sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards)
        return np.array(bytes_, dtype=np.uint8)

    cases = [
        # high_only + suited high pair
        ("2c 5d 6h 7s Ts Kd Ad", "TsKsAs(no), but 5d-Kd-Ad has Kd-Ad=A diamonds, 5d=2nd"),
        ("3c 7c 9d Th Js Qh Kc", "no suited high pair (rainbow-ish)"),
        ("3c 9c Td Jh Qs Kc Ah", "9c-Kc clubs, max=K"),
        ("2c 3c 4c 5d 6h 7s 8c", "many low clubs but max-rank=8 < 9, no fire"),
        ("Tc Jc Qd Kd Ah 2s 3s", "Tc-Jc clubs (max=J) AND Qd-Kd diamonds (max=K) → pick K"),
        # has pair → don't fire
        ("Ac Ad Kh Qs Jc Th 9d", "AA pair → high_only fails"),
    ]
    for s, label in cases:
        h = hh(*s.split())
        print(f"{s:30s}  {label}")
        idx = _detect_rule5_setting(h)
        if idx is None:
            print(f"   Rule 5 does NOT fire (handing off to v8)")
        else:
            print(f"   Rule 5 fires → setting_idx={idx}")
