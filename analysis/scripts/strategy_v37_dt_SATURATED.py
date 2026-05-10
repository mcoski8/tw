"""
Session 53 OVERNIGHT — strategy_v37_dt: capacity sweep at depth=38 ml=1.

ATTEMPTED but produced IDENTICAL tree to v36_dt:
  - v36_dt: depth=36, min_samples_leaf=1, 1,064,442 leaves, depth saturates at 33
  - v37_dt: depth=38, min_samples_leaf=1, 1,064,442 leaves, depth saturates at 33

Conclusion: at the current 83 features, ml=1 is the binding constraint
(NOT depth). Capacity is saturated. Further ML improvement requires NEW
features (feature engineering for pair zone, trips_pair, etc.).

DO NOT USE — kept as documentation that capacity-only sweeps have hit
the ceiling.

Future work: consider feature engineering for the largest residual zones:
  - pair AA/KK/QQ ($164/1000h diagonal)
  - trips_pair ($155/1000h)
  - high_only ($615/1000h, partially covered by Rule 17)
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
MODEL_PATH = ROOT / "data" / "v37_dt_model.npz"


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


def strategy_v37_dt_SATURATED(hand: np.ndarray) -> int:
    """v37 ML candidate: depth=38 ml=1; produces identical tree to v36."""
    saved = _v31b_harness.MODEL_PATH
    _v31b_harness._MODEL_CACHE = load_model()
    _v31b_harness.MODEL_PATH = MODEL_PATH
    try:
        return int(_v31b_harness.strategy_v31b_dt(hand))
    finally:
        _v31b_harness.MODEL_PATH = saved
