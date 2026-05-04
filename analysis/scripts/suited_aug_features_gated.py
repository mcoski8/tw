"""
Session 30 — gated suited-broadway aug features.

The Session 29 attempt (suited_aug_features.py) computed 6 features for
ALL 6M hands without category gating. Result: v19 won the full-grid grade
but FAILED the prefix tripwire (−$16/1000h on N=1000 vs v18). The
pair-category prefix regression suggested the new features were noise-
fitting on hands they shouldn't matter for.

This v2 implements the SAME 6 features but **gated to high_only hands
only** — returns zeros for any hand with n_pairs ≥ 1 / n_trips ≥ 1 /
n_quads ≥ 1. Mirrors how `compute_high_only_aug_for_hand` is gated to
the high_only category.

The hypothesis: the suited-broadway signal is real for high_only hands
(the targeted population per Session 28's high_only deep-dive), but the
DT was using cross-category leakage to overfit the noise on N=200
labels. Gating eliminates the spurious-fit surface.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from suited_aug_features import compute_suited_aug_for_hand  # noqa: E402


def is_high_only_from_ranks(hand: np.ndarray) -> bool:
    """Check if 7-card hand has all distinct ranks (high_only)."""
    if hand.shape[0] != 7:
        return False
    ranks = (hand // 4) + 2
    return len(set(int(r) for r in ranks)) == 7


def compute_suited_aug_gated_for_hand(hand: np.ndarray) -> tuple[int, int, int, int, int, int]:
    """Returns the 6 suited-aug features but ONLY for high_only hands;
    otherwise returns all zeros."""
    if not is_high_only_from_ranks(hand):
        return (0, 0, 0, 0, 0, 0)
    return compute_suited_aug_for_hand(hand)


def compute_suited_aug_gated_batch(hands: np.ndarray, log_every: int = 500_000) -> dict[str, np.ndarray]:
    """Compute the gated 6 features for all hands. Non-high_only rows → 0."""
    N = hands.shape[0]
    a = np.zeros(N, dtype=np.int8)
    b = np.zeros(N, dtype=np.int8)
    c = np.zeros(N, dtype=np.int8)
    d = np.zeros(N, dtype=np.int8)
    e = np.zeros(N, dtype=np.int8)
    f = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        f1, f2, f3, f4, f5, f6 = compute_suited_aug_gated_for_hand(h)
        a[i] = f1; b[i] = f2; c[i] = f3
        d[i] = f4; e[i] = f5; f[i] = f6
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  suited_aug_gated {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "n_suited_pairs_total_g": a,
        "max_suited_pair_high_rank_g": b,
        "max_suited_pair_low_rank_g": c,
        "has_suited_broadway_pair_g": d,
        "has_suited_premium_pair_g": e,
        "n_broadway_in_largest_suit_g": f,
    }
