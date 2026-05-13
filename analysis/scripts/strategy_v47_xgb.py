"""
Session 75 — strategy_v47_xgb: inference scaffolding for the XGBoost
gradient-boosting model trained on v44's 107 features.

The XGBoost model is too slow for per-hand inference at grader scale
(6M canonical hands × per-call overhead). This module exposes a
*batch* prediction path:

    predict_all_chosen(grid_rows) -> np.ndarray  shape (N,) int16

The grader script `grade_v47_xgb.py` uses this directly. A per-hand
fallback `strategy_v47_xgb(hand_bytes)` is provided for ad-hoc use
(unit tests, single-hand spot checks); it precomputes the full chosen-
indices array on first call and looks up by canonical_id thereafter.
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import numpy as np
import xgboost as xgb

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from train_v44_dt import build_X as build_X_v44, FEATURE_COLUMNS as V44_COLUMNS  # noqa: E402

MODEL_PATH = ROOT / "data" / "v47_xgb_model.ubj"
FEATURE_COLUMNS = list(V44_COLUMNS)  # 107 features

_BOOSTER_CACHE: Optional[xgb.Booster] = None
_CHOSEN_CACHE: Optional[np.ndarray] = None  # (N,) int16 — canonical_id-indexed
_HAND_TO_ID_CACHE: Optional[dict] = None  # tuple(hand_bytes) -> canonical_id


def load_booster(path: Optional[Path] = None) -> xgb.Booster:
    global _BOOSTER_CACHE
    if _BOOSTER_CACHE is not None:
        return _BOOSTER_CACHE
    if path is None:
        path = MODEL_PATH
    bst = xgb.Booster()
    bst.load_model(str(path))
    _BOOSTER_CACHE = bst
    return bst


def predict_chosen_for_X(X: np.ndarray, chunk_rows: int = 200_000,
                          model_path: Optional[Path] = None) -> np.ndarray:
    """Batch-predict chosen setting indices for a feature matrix X.

    Returns int16 array of shape (X.shape[0],) with values in [0, 105).
    Predicts in chunks to keep memory bounded (each chunk allocates
    chunk_rows × 105 × 4 bytes float prediction).
    """
    bst = load_booster(model_path)
    n = X.shape[0]
    out = np.empty(n, dtype=np.int16)
    X = np.ascontiguousarray(X, dtype=np.float32)
    for start in range(0, n, chunk_rows):
        end = min(start + chunk_rows, n)
        dmat = xgb.DMatrix(X[start:end])
        pred = bst.predict(dmat)  # (chunk_rows, 105)
        out[start:end] = pred.argmax(axis=1).astype(np.int16)
    return out


def predict_all_chosen(model_path: Optional[Path] = None) -> np.ndarray:
    """Build X for all canonical hands and predict chosen setting per hand."""
    global _CHOSEN_CACHE
    if _CHOSEN_CACHE is not None:
        return _CHOSEN_CACHE
    X, n = build_X_v44()
    print(f"  [strategy_v47_xgb] built X={X.shape} for prediction", flush=True)
    _CHOSEN_CACHE = predict_chosen_for_X(X, model_path=model_path)
    return _CHOSEN_CACHE


def _build_hand_to_id_cache():
    """Build dict mapping tuple(hand_bytes) -> canonical_id from canonical
    file. Used by per-hand strategy_fn fallback."""
    global _HAND_TO_ID_CACHE
    if _HAND_TO_ID_CACHE is not None:
        return _HAND_TO_ID_CACHE
    from tw_analysis.canonical import read_canonical_hands
    CANON = ROOT / "data" / "canonical_hands.bin"
    ch = read_canonical_hands(CANON, mode="memmap")
    hands_arr = np.asarray(ch.hands, dtype=np.uint8)
    _HAND_TO_ID_CACHE = {tuple(int(b) for b in hands_arr[i]): i
                          for i in range(len(hands_arr))}
    return _HAND_TO_ID_CACHE


def strategy_v47_xgb(hand: np.ndarray) -> int:
    """Per-hand inference for grade_strategy compatibility. Slow first call
    (precomputes all 6M predictions); fast lookup thereafter."""
    chosen = predict_all_chosen()
    cache = _build_hand_to_id_cache()
    key = tuple(int(b) for b in hand)
    return int(chosen[cache[key]])
