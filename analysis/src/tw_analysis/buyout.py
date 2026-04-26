"""
Buyout signature: deterministic predicate over hand features for the
"should I pay 4 to fold?" decision in the user's home-game variant.

Empirical basis (mine_patterns_session12 §9):
  * 0.09% of hands have ev_mean < -4 across the 4 production opponent profiles.
  * Buyout candidates concentrate in two structural buckets:
      - VERY low quads (rank ≤ 5): set/full-house targets that rarely materialize.
      - VERY low full-house shapes (trips ≤ 4 + pair ≤ 3): trapped pair structure.
  * Garbage hands (no pair, mostly low) are NOT buyout candidates — they
    average -0.98 EV, bad but not catastrophic.

Validated on 6,009,159 canonical hands (analysis/scripts/buyout_signature.py):
  precision 26.30%, recall 46.56%, F1 33.6% vs ground truth (ev_mean < -4).

The trainer should treat this as a "high-confidence BUYOUT" signal. For
softer cases the trainer can additionally look up the hand's actual
ev_mean from feature_table.parquet and surface a "consider buyout" badge.
"""
from __future__ import annotations

import numpy as np


def buyout_signature_scalar(
    n_quads: int,
    quads_rank: int,
    n_trips: int,
    trips_rank: int,
    n_pairs: int,
    pair_high_rank: int,
) -> bool:
    """
    Per-hand buyout predicate. All inputs are integers from the
    HAND_FEATURE_KEYS schema (rank values are 2..14).
    """
    if n_quads >= 1 and quads_rank <= 5:
        return True
    if (n_trips >= 1 and n_pairs >= 1
            and trips_rank <= 4 and pair_high_rank <= 3):
        return True
    return False


def buyout_signature_batch(hf: dict) -> np.ndarray:
    """
    Vectorized form. ``hf`` is the dict returned by hand_features_batch
    (or any equivalent column store). Returns (N,) bool array.
    """
    n_quads = np.asarray(hf["n_quads"])
    quads_rank = np.asarray(hf["quads_rank"])
    n_trips = np.asarray(hf["n_trips"])
    trips_rank = np.asarray(hf["trips_rank"])
    n_pairs = np.asarray(hf["n_pairs"])
    pair_high_rank = np.asarray(hf["pair_high_rank"])

    rule_quads = (n_quads >= 1) & (quads_rank <= 5)
    rule_trips_pair = (
        (n_trips >= 1) & (n_pairs >= 1)
        & (trips_rank <= 4) & (pair_high_rank <= 3)
    )
    return rule_quads | rule_trips_pair
