"""
Session 53 OVERNIGHT — strategy_v36_dt: capacity-only retrain of v34_dt
at depth=36, min_samples_leaf=1.

Same feature set (83) as v32/v34. Trained against the same full oracle
grid. Just bigger leaf budget.

v34_dt: depth=34, min_samples_leaf=2, 874,548 leaves
v36_dt: depth=36, min_samples_leaf=1, 1,064,442 leaves (+21.7%)

Hypothesis: more leaves → finer-grained partitioning → lower regret.
Pattern from past retrains:
  - v31 (capacity-only retrain, depth=32 ml=3): +$58/1000h vs v30
  - v34 (capacity-only retrain, depth=34 ml=2): −$34/1000h vs v32
  - v36 (capacity-only retrain, depth=36 ml=1): TBD

Feature importances: dominated by n_broadway (43%), pair_high_rank (13%),
third_rank (11%). Top-30 mostly base features.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import strategy_v31b_dt as _v31b_harness  # noqa: E402

_MODEL_CACHE: Optional[dict] = None
MODEL_PATH = ROOT / "data" / "v36_dt_model.npz"


def load_model(path: Optional[Path] = None) -> dict:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if path is None:
        path = MODEL_PATH
    saved = _v31b_harness.MODEL_PATH
    _v31b_harness._MODEL_CACHE = None
    _v31b_harness.MODEL_PATH = path
    try:
        _MODEL_CACHE = _v31b_harness.load_model()
    finally:
        _v31b_harness.MODEL_PATH = saved
    return _MODEL_CACHE


def strategy_v36_dt(hand: np.ndarray) -> int:
    """v36 ML candidate: 83 features at depth=36, min_samples_leaf=1."""
    saved = _v31b_harness.MODEL_PATH
    _v31b_harness._MODEL_CACHE = load_model()
    _v31b_harness.MODEL_PATH = MODEL_PATH
    try:
        return int(_v31b_harness.strategy_v31b_dt(hand))
    finally:
        _v31b_harness.MODEL_PATH = saved
