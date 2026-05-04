"""
Session 28 — Quick probe: among high_only hands where v16 has high regret,
does the oracle's chosen setting frequently put a SUITED PAIR of cards in mid?

If yes, that's a clean v18 candidate signal: "for high_only, prefer mids
that are same-suit, especially when both cards are >= T."

Heuristic check (no full grid scan): pull the top-10K high_only hands by
v16 regret, decode oracle setting, count how often mid is single-suited.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from high_only_v16_residual import build_X, walk_to_leaf, decode_setting, ALPHA_MAP  # noqa: E402

MODEL_PATH = ROOT / "data" / "v16_dt_model.npz"
GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON = ROOT / "data" / "canonical_hands.bin"


def mid_is_suited(hand_bytes: np.ndarray, setting_idx: int) -> bool:
    top_idx, (a, b), _ = (
        decode_setting(setting_idx)[0],
        decode_setting(setting_idx)[1],
        decode_setting(setting_idx),
    )
    a, b = decode_setting(setting_idx)[1]
    return (hand_bytes[a] % 4) == (hand_bytes[b] % 4)


def card_rank(b: int) -> int:
    return (b // 4) + 2  # 2..14


def mid_min_rank(hand_bytes: np.ndarray, setting_idx: int) -> int:
    a, b = decode_setting(setting_idx)[1]
    return min(card_rank(int(hand_bytes[a])), card_rank(int(hand_bytes[b])))


def main() -> int:
    print("loading model + features ...", flush=True)
    arr = np.load(MODEL_PATH, allow_pickle=True)
    feature_columns = [str(c) for c in arr["feature_columns"]]
    model = {
        "children_left": np.asarray(arr["children_left"], dtype=np.int32),
        "children_right": np.asarray(arr["children_right"], dtype=np.int32),
        "feature": np.asarray(arr["feature"], dtype=np.int32),
        "threshold": np.asarray(arr["threshold"], dtype=np.float64),
        "leaf_values": np.asarray(arr["leaf_values"], dtype=np.float32),
        "depth": int(arr["depth"]),
        "n_leaves": int(arr["n_leaves"]),
    }
    X, cd = build_X(feature_columns)
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    ch = read_canonical_hands(CANON, mode="memmap")
    Y = np.asarray(grid.evs[:X.shape[0]])
    hands = np.asarray(ch.hands[:X.shape[0]])
    n = X.shape[0]

    print("walking + computing v16 regret ...", flush=True)
    leaf_ids = walk_to_leaf(X, model)
    chosen_idx = model["leaf_values"][leaf_ids].argmax(axis=1).astype(np.int16)
    oracle_idx = Y.argmax(axis=1).astype(np.int16)
    chosen_ev = Y[np.arange(n), chosen_idx]
    oracle_ev = Y[np.arange(n), oracle_idx]
    regret = (oracle_ev - chosen_ev).astype(np.float32)

    high_only_mask = (cd["category_id"] == ALPHA_MAP["high_only"])
    ho_idx = np.where(high_only_mask)[0]
    ho_regret = regret[ho_idx]

    # Top 10K worst-regret high_only hands.
    sort_order = np.argsort(-ho_regret)[:10000]
    worst = ho_idx[sort_order]
    print(f"\nanalyzing top 10K worst-regret high_only hands (mean regret {ho_regret[sort_order].mean():.3f}) ...\n", flush=True)

    # Compare: oracle mid suited?  v16 mid suited?  Also stratify by mid_min_rank.
    rows = []
    for ri in worst:
        hb = hands[ri].astype(np.uint8)
        v16_idx = int(chosen_idx[ri])
        ora_idx = int(oracle_idx[ri])
        rows.append({
            "v16_mid_suited": mid_is_suited(hb, v16_idx),
            "v16_mid_min_rank": mid_min_rank(hb, v16_idx),
            "ora_mid_suited": mid_is_suited(hb, ora_idx),
            "ora_mid_min_rank": mid_min_rank(hb, ora_idx),
            "regret": float(regret[ri]),
        })
    df = pd.DataFrame(rows)
    print("Top 10K worst-regret high_only hands — overall stats:")
    print(f"  v16 mid suited: {df['v16_mid_suited'].mean()*100:.1f}%")
    print(f"  oracle mid suited: {df['ora_mid_suited'].mean()*100:.1f}%")
    print(f"  v16 mid min-rank: mean={df['v16_mid_min_rank'].mean():.1f}, median={df['v16_mid_min_rank'].median():.1f}")
    print(f"  oracle mid min-rank: mean={df['ora_mid_min_rank'].mean():.1f}, median={df['ora_mid_min_rank'].median():.1f}")

    print(f"\n  hands where oracle mid is suited but v16 mid is not: "
          f"{int(((~df['v16_mid_suited']) & df['ora_mid_suited']).sum())} / 10000  "
          f"({((~df['v16_mid_suited']) & df['ora_mid_suited']).mean()*100:.1f}%)")
    print(f"  hands where v16 mid is suited but oracle mid is not: "
          f"{int((df['v16_mid_suited'] & (~df['ora_mid_suited'])).sum())} / 10000  "
          f"({(df['v16_mid_suited'] & (~df['ora_mid_suited'])).mean()*100:.1f}%)")
    print(f"  hands where both pick the same suit-mid status: "
          f"{int((df['v16_mid_suited'] == df['ora_mid_suited']).sum())} / 10000")

    # Compare to baseline: ALL high_only hands oracle-mid-suited rate.
    print("\nbaseline: random sample of 100K high_only hands (not regret-filtered):")
    samp = np.random.default_rng(0).choice(ho_idx, size=min(100000, len(ho_idx)), replace=False)
    rows2 = []
    for ri in samp:
        hb = hands[ri].astype(np.uint8)
        v16_idx = int(chosen_idx[ri])
        ora_idx = int(oracle_idx[ri])
        rows2.append({
            "v16_mid_suited": mid_is_suited(hb, v16_idx),
            "ora_mid_suited": mid_is_suited(hb, ora_idx),
        })
    df2 = pd.DataFrame(rows2)
    print(f"  v16 mid suited: {df2['v16_mid_suited'].mean()*100:.1f}%")
    print(f"  oracle mid suited: {df2['ora_mid_suited'].mean()*100:.1f}%")

    return 0


if __name__ == "__main__":
    sys.exit(main())
