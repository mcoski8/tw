"""
Session 36 — strategy_v31_dt: identical feature set to v30 (8 gated
families + base) but trained at higher capacity (depth=32 ml=3,
699,773 leaves). Ships +$58/1000h on full grid and +$29/1000h on
prefix vs v30 — the second-largest single ship in project history,
with NO new features. Capacity was the binding constraint.

This is the v31c overnight candidate from the Session 36 → 37 cascade,
promoted to the official v31 ML champion after winning head-to-head
against v31a (pair_r4v3 KK/AA-tight) and v31b (trips_v2 round 2).
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

# Re-export v30's harness with the v31 model path. The feature set is
# identical to v30; only the model file changes.
from strategy_v30_dt import (  # noqa: E402,F401
    load_model as _load_v30,
    strategy_v30_dt as _strategy_v30,
    _walk_tree_to_leaf,
)
import strategy_v30_dt as _v30_harness

_MODEL_CACHE: Optional[dict] = None
MODEL_PATH = ROOT / "data" / "v31_dt_model.npz"


def load_model(path: Optional[Path] = None) -> dict:
    global _MODEL_CACHE
    if _MODEL_CACHE is not None:
        return _MODEL_CACHE
    if path is None:
        path = MODEL_PATH
    # Reuse v30's model-loader but pointed at the v31 model file. We
    # swap the v30 harness's MODEL_PATH temporarily, prime its cache
    # for the v31 model, then return that cache as our own.
    saved = _v30_harness.MODEL_PATH
    _v30_harness._MODEL_CACHE = None
    _v30_harness.MODEL_PATH = path
    try:
        _MODEL_CACHE = _v30_harness.load_model()
    finally:
        _v30_harness.MODEL_PATH = saved
    return _MODEL_CACHE


def strategy_v31_dt(hand: np.ndarray) -> int:
    """Forward to v30's inference (same feature set), with v31 model loaded."""
    if _MODEL_CACHE is None:
        load_model()
    # Make sure v30 harness sees our cache so its inference walks the v31 tree
    _v30_harness._MODEL_CACHE = _MODEL_CACHE
    return _v30_harness.strategy_v30_dt(hand)
