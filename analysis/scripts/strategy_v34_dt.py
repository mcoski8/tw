"""
Session 38 — strategy_v34_dt: identical feature set to v31b/v32 (83 features:
79 v30 + 4 trips_v2 round-2) but trained at higher capacity (depth=34,
min_samples_leaf=2).

The Session 38 capacity sweep at v32's 83 features showed:
  * depth=34 ml=3 produced 731,611 leaves (+5 vs v32) — ml=3 was the binding
    constraint, not depth. Result: $1,715 full / $904 prefix (= v32 exactly).
  * depth=34 ml=2 produced 874,548 leaves (+19.5% vs v32) — capacity unlock.
    Result: $1,681 full / $889 prefix.

v34 ships: −$34/1000h on full grid, −$15/1000h on prefix grid vs v32. Per-
category gains are broadly distributed (composite −$213 within-category,
trips_pair −$133, two_pair −$59, trips −$68, pair −$20).

This module re-exports v31b's runtime harness pointed at the v34 model file.
Same feature pipeline (9 gated families + base) as v31b/v32.
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
MODEL_PATH = ROOT / "data" / "v34_dt_model.npz"


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


def strategy_v34_dt(hand: np.ndarray) -> int:
    """v34 ML champion: 83 features at depth=34, min_samples_leaf=2."""
    saved = _v31b_harness.MODEL_PATH
    _v31b_harness._MODEL_CACHE = load_model()
    _v31b_harness.MODEL_PATH = MODEL_PATH
    try:
        return int(_v31b_harness.strategy_v31b_dt(hand))
    finally:
        _v31b_harness.MODEL_PATH = saved
