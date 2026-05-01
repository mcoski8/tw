"""
Inspect v7_regression's learned decision tree:
  1. Top of the tree (first 3 levels) — the highest-priority questions.
  2. Feature importance — which of the 37 features the tree relies on most.
  3. Setting-coverage — how many of the 105 possible settings does v7 actually use.
  4. Worked examples — trace 7 archetypal hands (one per category) through v7
     showing every split that fires + the final setting.
"""
from __future__ import annotations

import sys
from pathlib import Path
from collections import Counter

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SCRIPTS), str(SRC), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v7_regression import load_model  # noqa: E402
from strategy_v5_dt import compute_feature_vector  # noqa: E402
from encode_rules import decode_tier_positions  # noqa: E402

_RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
         "T":10,"J":11,"Q":12,"K":13,"A":14}
_SUIT = {"c":0,"d":1,"h":2,"s":3}


def hh(*cards):
    bytes_ = sorted((_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards)
    return np.array(bytes_, dtype=np.uint8)


def decode_setting_for_hand(hand_str: str, setting_index: int) -> str:
    """Return human-readable (top, mid, bot) for a setting on a specific hand."""
    cards = hand_str.split()
    bytes_ = sorted([(_RANK[c[0]]-2)*4 + _SUIT[c[1]] for c in cards])
    # Map back to human-readable in byte order
    sorted_cards = []
    for b in bytes_:
        rank = (b // 4) + 2
        suit = b % 4
        rank_str = "23456789TJQKA"[rank-2]
        suit_str = "cdhs"[suit]
        sorted_cards.append(rank_str + suit_str)

    top_pos, mid_pos, bot_pos = decode_tier_positions(setting_index)
    top = sorted_cards[top_pos]
    mid = (sorted_cards[mid_pos[0]], sorted_cards[mid_pos[1]])
    bot = tuple(sorted_cards[p] for p in bot_pos)
    return f"top={top}  mid=({' '.join(mid)})  bot=({' '.join(bot)})"


def trace_path(hand_arr: np.ndarray, model: dict) -> list:
    """Return list of (depth, feature_name, threshold, value, direction, node_id)."""
    feat_meta = {"cat_map": model["cat_map"], "feature_columns": model["feature_columns"]}
    x = compute_feature_vector(hand_arr, feat_meta)
    cl = model["children_left"]
    cr = model["children_right"]
    feat = model["feature"]
    thr = model["threshold"]
    feature_columns = model["feature_columns"]

    path = []
    node = 0
    depth = 0
    while cl[node] != -1:
        f = int(feat[node])
        t = float(thr[node])
        v = int(x[f])
        direction = "≤" if v <= t else ">"
        new_node = int(cl[node]) if v <= t else int(cr[node])
        path.append({
            "depth": depth,
            "feature": feature_columns[f],
            "threshold": t,
            "hand_value": v,
            "direction": direction,
            "node_id": node,
        })
        node = new_node
        depth += 1
    leaf_vec = model["leaf_values"][node]
    setting = int(leaf_vec.argmax())
    margin = float(np.sort(leaf_vec)[-1] - np.sort(leaf_vec)[-2])
    return path, setting, leaf_vec[setting], margin


def feature_importance_by_split_depth(model: dict, max_depth: int = 5) -> dict:
    """For each feature, count how often it appears at each tree depth."""
    cl = model["children_left"]
    cr = model["children_right"]
    feat = model["feature"]
    feature_columns = model["feature_columns"]

    counts: dict[int, dict[str, int]] = {d: {} for d in range(max_depth + 1)}

    # BFS from root, tracking depth of each node
    queue = [(0, 0)]  # (node, depth)
    while queue:
        next_queue = []
        for node, depth in queue:
            if cl[node] == -1:
                continue  # leaf
            if depth <= max_depth:
                fname = feature_columns[int(feat[node])]
                counts[depth][fname] = counts[depth].get(fname, 0) + 1
            next_queue.append((int(cl[node]), depth + 1))
            next_queue.append((int(cr[node]), depth + 1))
        queue = next_queue
    return counts


def setting_coverage(model: dict) -> dict:
    """For each of the 27,909 nodes, what setting would each leaf return?
    Then count — how many leaves point at each of the 105 settings."""
    cl = model["children_left"]
    leaf_values = model["leaf_values"]
    leaf_argmax = leaf_values.argmax(axis=1)
    is_leaf = (cl == -1)
    leaf_settings = leaf_argmax[is_leaf]
    return Counter(leaf_settings.tolist())


def main() -> int:
    model = load_model()
    feature_columns = model["feature_columns"]

    print("=" * 80)
    print("V7 TREE STRUCTURE OVERVIEW")
    print("=" * 80)
    print(f"  depth         : {model['depth']}")
    print(f"  n_leaves      : {model['n_leaves']:,}")
    print(f"  features used : {len(feature_columns)} (37 baseline + augmented)")

    # ROOT
    root_feature_idx = int(model["feature"][0])
    root_threshold = float(model["threshold"][0])
    print(f"\n  ROOT split    : {feature_columns[root_feature_idx]} ≤ {root_threshold}")
    print(f"  Children      : left={int(model['children_left'][0])}, right={int(model['children_right'][0])}")

    # FEATURE IMPORTANCE by tree depth (top splits)
    print("\n" + "=" * 80)
    print("TOP-LEVEL SPLITS (first 4 levels of the tree)")
    print("=" * 80)
    counts_by_depth = feature_importance_by_split_depth(model, max_depth=3)
    for d in sorted(counts_by_depth.keys()):
        print(f"\n  Depth {d}:")
        for fname, cnt in sorted(counts_by_depth[d].items(), key=lambda x: -x[1]):
            print(f"    {fname:<40}  {cnt:>3} nodes split on this")

    # OVERALL FEATURE USAGE across the whole tree
    print("\n" + "=" * 80)
    print("OVERALL FEATURE USAGE (across entire tree)")
    print("=" * 80)
    cl = model["children_left"]
    feat = model["feature"]
    is_internal = (cl != -1)
    internal_features = feat[is_internal]
    feature_counts = Counter(internal_features.tolist())
    total = sum(feature_counts.values())
    print(f"  Total internal nodes: {total:,}")
    print(f"\n  Top 15 most-split features:")
    for fidx, cnt in feature_counts.most_common(15):
        pct = 100 * cnt / total
        print(f"    {feature_columns[fidx]:<40}  {cnt:>5} ({pct:5.1f}%)")

    print(f"\n  Features rarely or never split on:")
    used_features = set(feature_counts.keys())
    for i, fname in enumerate(feature_columns):
        cnt = feature_counts.get(i, 0)
        if cnt < total * 0.005:  # < 0.5%
            print(f"    {fname:<40}  {cnt:>5}")

    # SETTING COVERAGE
    print("\n" + "=" * 80)
    print("SETTING COVERAGE")
    print("=" * 80)
    coverage = setting_coverage(model)
    print(f"  Out of 105 possible settings, v7 uses {len(coverage)} distinct settings across its leaves.")
    print(f"\n  Top 15 most-used settings (by leaf count):")
    for setting, cnt in coverage.most_common(15):
        pct = 100 * cnt / sum(coverage.values())
        # decode setting via positions for description
        top_pos, mid_pos, bot_pos = decode_tier_positions(setting)
        print(f"    setting {setting:>3}  ({cnt:>4} leaves, {pct:5.1f}%)  "
              f"top_pos={top_pos}  mid_pos={mid_pos}  bot_pos={bot_pos}")

    # WORKED EXAMPLES — one per category
    print("\n" + "=" * 80)
    print("WORKED EXAMPLES — trace each category type through v7's decision path")
    print("=" * 80)

    examples = [
        ("user's example #1 (one-pair, broadway sing)",  "Ks Qs 8h 8d 7d 5h Ac"),
        ("low-pair w/ broadway connectors",               "Jd Td 9c 4h 2c 2d 6s"),
        ("two-pair AAKK (the special case)",              "Ac Ad Kc Kh 7s 5d 2h"),
        ("two-pair low (≤5)",                             "5h 5c 3d 3s Kh Qd 9c"),
        ("high_only with DS-able bot",                    "Ah Kc Qd Jh 7d 5d 3c"),
        ("trips + pair (full house)",                     "Qc Qd Qh 7s 7d Ah 2c"),
        ("pure trips",                                    "9c 9d 9h Kh Qs Jc 6d"),
        ("quads",                                         "Ah As Ad Ac 6s 4d 2c"),
    ]

    for label, hand_str in examples:
        print(f"\n  {label}: {hand_str}")
        try:
            hand_arr = hh(*hand_str.split())
            path, setting, leaf_ev, margin = trace_path(hand_arr, model)
            print(f"    DECISION PATH:")
            for step in path:
                print(f"      depth {step['depth']:>2}  "
                      f"{step['feature']:<32} {step['direction']:>2} {step['threshold']:<8.3f}  "
                      f"(hand has {step['hand_value']})")
            print(f"    LEAF: setting {setting}  predicted_mean_EV={leaf_ev:+.3f}  "
                  f"margin_to_2nd_choice={margin:+.3f}")
            print(f"    PLAY: {decode_setting_for_hand(hand_str, setting)}")
        except Exception as e:
            print(f"    (error: {e})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
