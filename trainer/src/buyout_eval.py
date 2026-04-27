"""
Bridge from the trainer to the validated buyout signature module.

The user's home-game variant allows paying ``BUYOUT_COST`` points (per
willing opponent) to fold and avoid playing a hand. The trainer surfaces
two distinct buyout signals:

* ``signature`` — a high-precision structural rule firing on quads ≤ 5 and
  low full-house shapes (trips ≤ 4 + pair ≤ 3). Validated empirically at
  precision 26%, recall 47% vs ground truth ev_mean < -4 (see
  ``tw_analysis/buyout.py``). When this fires, the trainer shows a
  prominent BUYOUT badge.

* ``soft_recommend`` — fires when the best-EV play against a specific
  opponent profile is worse than ``-BUYOUT_COST``, meaning even optimal
  play loses more than the cost of folding. This is the "consider buyout
  vs <profile>" signal. Computed per-profile from the live MC result.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
ANALYSIS_SRC = REPO_ROOT / "analysis" / "src"
if str(ANALYSIS_SRC) not in sys.path:
    sys.path.insert(0, str(ANALYSIS_SRC))

from tw_analysis.buyout import buyout_signature_scalar  # noqa: E402
from tw_analysis.features import hand_features_scalar  # noqa: E402
from tw_analysis.settings import Card  # noqa: E402


BUYOUT_COST: float = 4.0


def _hand_to_bytes(hand_strs: List[str]) -> List[int]:
    return [Card.parse(s).idx for s in hand_strs]


def _signature_reason(hf: dict) -> str:
    rank_name = {2: "deuces", 3: "threes", 4: "fours", 5: "fives",
                 6: "sixes", 7: "sevens", 8: "eights", 9: "nines",
                 10: "tens", 11: "jacks", 12: "queens", 13: "kings",
                 14: "aces"}
    if hf["n_quads"] >= 1 and hf["quads_rank"] <= 5:
        qr = int(hf["quads_rank"])
        return (
            f"Quads of {rank_name.get(qr, qr)} — at this rank, your "
            f"full-house and quad shapes lose to almost any pair the board "
            f"makes for the opponent."
        )
    if (hf["n_trips"] >= 1 and hf["n_pairs"] >= 1
            and hf["trips_rank"] <= 4 and hf["pair_high_rank"] <= 3):
        tr, pr = int(hf["trips_rank"]), int(hf["pair_high_rank"])
        return (
            f"Trips of {rank_name.get(tr, tr)} plus a pair of "
            f"{rank_name.get(pr, pr)} — locked into a very low "
            f"full-house. Easily out-paired by the board."
        )
    return ""


def evaluate_buyout(
    hand_strs: List[str],
    best_ev: Optional[float] = None,
) -> Dict:
    """
    Compute buyout signals for a 7-card hand.

    Args:
        hand_strs: 7-card list in trainer's "Rs" format (e.g., "As", "Kh").
        best_ev: Optional best-EV against a chosen opponent profile. When
                 provided, drives the soft recommendation signal.

    Returns dict with:
        signature: bool — high-precision structural rule fired.
        signature_reason: str — plain-English description (empty if no fire).
        soft_recommend: bool — best_ev < -BUYOUT_COST (only meaningful when
                       best_ev was supplied).
        best_ev: float | None — passed through.
        expected_loss: float | None — -best_ev (positive = how much you'd
                       lose at optimal play).
        cost: float — BUYOUT_COST, the price of folding.
    """
    bytes_ = _hand_to_bytes(hand_strs)
    hf = hand_features_scalar(bytes_)
    fires = bool(buyout_signature_scalar(
        n_quads=int(hf["n_quads"]),
        quads_rank=int(hf["quads_rank"]),
        n_trips=int(hf["n_trips"]),
        trips_rank=int(hf["trips_rank"]),
        n_pairs=int(hf["n_pairs"]),
        pair_high_rank=int(hf["pair_high_rank"]),
    ))
    reason = _signature_reason(hf) if fires else ""
    soft = (best_ev is not None) and (best_ev < -BUYOUT_COST)
    expected_loss = (-best_ev) if best_ev is not None else None
    return {
        "signature": fires,
        "signature_reason": reason,
        "soft_recommend": soft,
        "best_ev": best_ev,
        "expected_loss": expected_loss,
        "cost": BUYOUT_COST,
    }
