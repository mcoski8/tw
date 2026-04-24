"""
Cross-model join and agreement analysis over best-response files.

Each ``.bin`` file records, for every canonical 7-card hand, the best-response
setting index against one specific opponent model. This module joins those
records by ``canonical_id`` across several files and computes:

  * Per-hand setting matrix (N_hands x M_models)
  * Per-hand EV matrix (N_hands x M_models) — note EVs are NOT directly
    comparable across models because the opponent differs, but the per-hand
    spread (max-min) is still a useful "how much does opponent choice matter
    for this hand?" signal.
  * Unanimity: hands where every model picks the same setting
  * Unique-settings-per-hand histogram (how many distinct settings chosen across the M models)
  * Pairwise agreement matrix

All files must share the same ``canonical_total`` (i.e. be run over the same
canonical universe). A completed file has records in canonical_id order
0..N-1; ``read_br_file`` loads them in that order, so joining is a straight
column-stack.

Intended call pattern::

    files = [read_br_file(p) for p in paths]
    cm = build_cross_model(files)
    print_report(cm)
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

import numpy as np

from tw_analysis.br_reader import BrFile, NUM_SETTINGS


@dataclass(frozen=True)
class CrossModel:
    """Joined cross-model view over ``len(files)`` best-response files."""

    files: tuple[BrFile, ...]
    labels: tuple[str, ...]
    n_hands: int
    settings: np.ndarray  # shape (n_hands, n_models), dtype uint8
    evs: np.ndarray       # shape (n_hands, n_models), dtype float32

    @property
    def n_models(self) -> int:
        return len(self.files)


def build_cross_model(files: Sequence[BrFile]) -> CrossModel:
    """
    Join the given best-response files by canonical_id.

    Raises ValueError if files have mismatched canonical_total, are incomplete,
    or fail the canonical_id monotonicity invariant.
    """
    if not files:
        raise ValueError("build_cross_model: need at least one file")

    totals = {f.header.canonical_total for f in files}
    if len(totals) != 1:
        raise ValueError(
            f"files have mismatched canonical_total: "
            f"{[(str(f.path), f.header.canonical_total) for f in files]}"
        )

    n_hands = next(iter(totals))

    for f in files:
        if len(f.records) != n_hands:
            raise ValueError(
                f"{f.path}: incomplete ({len(f.records)} of {n_hands} records). "
                "Cross-model join requires complete files."
            )
        ids = f.records["canonical_id"]
        # Trust validate_br_file for the full 0..N-1 invariant, but cheap spot-check.
        if int(ids[0]) != 0 or int(ids[-1]) != n_hands - 1:
            raise ValueError(
                f"{f.path}: canonical_id range {int(ids[0])}..{int(ids[-1])} "
                f"doesn't span 0..{n_hands - 1}"
            )

    m = len(files)
    settings = np.empty((n_hands, m), dtype=np.uint8)
    evs = np.empty((n_hands, m), dtype=np.float32)
    for j, f in enumerate(files):
        settings[:, j] = f.records["best_setting_index"]
        evs[:, j] = f.records["best_ev"]

    labels = tuple(f.header.opp_label for f in files)
    return CrossModel(
        files=tuple(files),
        labels=labels,
        n_hands=n_hands,
        settings=settings,
        evs=evs,
    )


def unanimous_mask(cm: CrossModel) -> np.ndarray:
    """Boolean mask of hands where every model picked the same setting."""
    if cm.n_models == 1:
        return np.ones(cm.n_hands, dtype=bool)
    first = cm.settings[:, 0:1]
    return np.all(cm.settings == first, axis=1)


def unique_settings_per_hand(cm: CrossModel) -> np.ndarray:
    """
    For each hand, count the number of distinct setting indices chosen across
    the models. Values range from 1 (unanimous) to min(n_models, NUM_SETTINGS).
    """
    # Sort each row and count position-to-position differences + 1.
    sorted_rows = np.sort(cm.settings, axis=1)
    diffs = sorted_rows[:, 1:] != sorted_rows[:, :-1]
    return 1 + diffs.sum(axis=1).astype(np.int32)


def pairwise_agreement(cm: CrossModel) -> np.ndarray:
    """
    Symmetric M x M matrix of pairwise agreement rates.
    ``out[i, j]`` = fraction of hands where model i and model j picked the same setting.
    Diagonal is 1.0.
    """
    m = cm.n_models
    out = np.ones((m, m), dtype=np.float64)
    if cm.n_hands == 0:
        return out
    for i in range(m):
        for j in range(i + 1, m):
            agree = float(np.mean(cm.settings[:, i] == cm.settings[:, j]))
            out[i, j] = agree
            out[j, i] = agree
    return out


def consensus_setting_counts(cm: CrossModel) -> np.ndarray:
    """
    Histogram of setting indices across all (hand x model) cells.
    Shape (NUM_SETTINGS,), summing to n_hands * n_models.

    Useful for showing the overall popularity of each setting independent of model.
    """
    return np.bincount(
        cm.settings.reshape(-1).astype(np.int64),
        minlength=NUM_SETTINGS,
    )


def unanimous_setting_counts(cm: CrossModel) -> np.ndarray:
    """
    Histogram of setting indices but only over unanimous hands.
    Shape (NUM_SETTINGS,). Tells you which settings are robustly optimal
    regardless of opponent.
    """
    mask = unanimous_mask(cm)
    if not mask.any():
        return np.zeros(NUM_SETTINGS, dtype=np.int64)
    chosen = cm.settings[mask, 0].astype(np.int64)
    return np.bincount(chosen, minlength=NUM_SETTINGS)
