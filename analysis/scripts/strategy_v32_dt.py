"""
Session 37 — strategy_v32_dt: identical feature set to v31b (83 features:
79 v30 + 4 trips_v2 round-2) but trained at v31's high-capacity config
(depth=32, min_samples_leaf=3).

Combines the trips_v2 feature ship (v31b, +$15) with the capacity expansion
(v31, +$58) on top of v30 — a single tree at the bigger leaf budget that
also has access to the round-2 trips routing features.

This module re-exports v31b's runtime harness pointed at the v32 model file.
The feature pipeline (9 gated families + base) is identical to v31b.
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
MODEL_PATH = ROOT / "data" / "v32_dt_model.npz"


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


def strategy_v32_dt(hand: np.ndarray) -> int:
    if _MODEL_CACHE is None:
        load_model()
    _v31b_harness._MODEL_CACHE = _MODEL_CACHE
    return _v31b_harness.strategy_v31b_dt(hand)
