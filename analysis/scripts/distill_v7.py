"""
Distillation step: train a shallow depth-5 DecisionTreeClassifier on v7's
predictions to extract a memorable rule chain.

The full v7 tree has 13,955 leaves (depth=15) — not memorable. But we can
treat v7 as the oracle and ask "what's the simplest tree that approximates
v7?" That gives us a depth-≤5 tree with at most 32 leaves — within the
soft rule-count cap the user discussed (Decision 033).

Procedure:
  1. Take the 50K training hands (data/oracle_grid_50k.npz).
  2. Compute v7's predicted setting for each.
  3. Compute the 37 features for each.
  4. Fit DecisionTreeClassifier(max_depth=5) on (X, y_v7).
  5. Print the resulting tree as if/elif chain.
  6. Report the agreement rate (small tree vs v7).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np
from sklearn.tree import DecisionTreeClassifier, export_text

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SCRIPTS), str(SRC), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from strategy_v5_dt import compute_feature_vector  # noqa: E402
from strategy_v7_regression import load_model as load_v7  # noqa: E402
from encode_rules import decode_tier_positions  # noqa: E402


def setting_layout(setting_idx: int) -> str:
    """Describe a setting in position-relative terms (independent of the actual hand)."""
    top_pos, mid_pos, bot_pos = decode_tier_positions(setting_idx)
    # Recall: positions in BYTE-sorted order.
    # pos 0 = lowest byte (lowest rank, lowest suit), pos 6 = highest.
    pos_label = {0: "lowest", 1: "2nd-lowest", 2: "3rd-lowest", 3: "middle",
                 4: "3rd-highest", 5: "2nd-highest", 6: "highest"}
    return (f"top={pos_label[top_pos]} | "
            f"mid=({pos_label[mid_pos[0]]}, {pos_label[mid_pos[1]]}) | "
            f"bot=({', '.join(pos_label[p] for p in bot_pos)})")


def main() -> int:
    print("loading 50K oracle grid + computing features ...")
    arr = np.load(ROOT / "data" / "oracle_grid_50k.npz", allow_pickle=True)
    hands_bytes = arr["hands_bytes"]
    n = hands_bytes.shape[0]
    print(f"  {n:,} hands")

    # Compute features.
    v7 = load_v7()
    feat_meta = {"cat_map": v7["cat_map"], "feature_columns": v7["feature_columns"]}
    n_features = len(v7["feature_columns"])
    X = np.empty((n, n_features), dtype=np.int16)
    t0 = time.time()
    for i in range(n):
        X[i] = compute_feature_vector(hands_bytes[i], feat_meta)
        if (i + 1) % 10000 == 0 or i + 1 == n:
            print(f"  features {i+1:,}/{n:,}  ({time.time()-t0:.1f}s)")

    # Compute v7 predictions on the 50K hands (vectorised tree walk).
    print("\ncomputing v7 predictions on 50K ...")
    t0 = time.time()
    cl = v7["children_left"]
    cr = v7["children_right"]
    feat = v7["feature"]
    thr = v7["threshold"]
    leaf_values = v7["leaf_values"]

    node = np.zeros(n, dtype=np.int32)
    active = np.ones(n, dtype=bool)
    for _ in range(v7["depth"] + 5):
        if not active.any():
            break
        cur_nodes = node[active]
        cur_features = feat[cur_nodes]
        cur_thresholds = thr[cur_nodes]
        cur_left = cl[cur_nodes]
        cur_right = cr[cur_nodes]
        leaf_mask = (cur_left == -1)
        row_idx = np.where(active)[0]
        vals = X[row_idx, cur_features]
        go_left = vals <= cur_thresholds
        new_node = np.where(go_left, cur_left, cur_right)
        new_node = np.where(leaf_mask, cur_nodes, new_node)
        node[row_idx] = new_node
        active[row_idx] = ~leaf_mask
    y_v7 = leaf_values[node].argmax(axis=1).astype(np.int32)
    print(f"  done ({time.time()-t0:.1f}s)")

    print(f"\nv7 prediction distribution:")
    from collections import Counter
    cnt = Counter(y_v7.tolist())
    for setting, c in cnt.most_common(10):
        pct = 100 * c / n
        print(f"  setting {setting:>3}: {c:>6,} hands ({pct:5.2f}%)  {setting_layout(setting)}")

    # Fit shallow distillation tree at multiple depths.
    for depth in (3, 4, 5, 6):
        print(f"\n{'='*70}")
        print(f"DISTILLED TREE: max_depth={depth}")
        print(f"{'='*70}")
        dt = DecisionTreeClassifier(max_depth=depth, random_state=42, criterion="gini")
        dt.fit(X, y_v7)
        n_leaves = dt.get_n_leaves()
        train_acc = float(dt.score(X, y_v7)) * 100
        print(f"  n_leaves: {n_leaves}  agreement-with-v7: {train_acc:.2f}%")

        # Print the tree structure.
        feature_names = list(v7["feature_columns"])
        tree_text = export_text(dt, feature_names=feature_names, max_depth=depth, decimals=2)
        print("\n  Decision chain (numbers in [...] are setting indices):")
        for line in tree_text.split("\n")[:120]:
            print(f"  {line}")

    # Plain-English distillation at depth=4 with leaf descriptions.
    print(f"\n{'='*70}")
    print(f"PLAIN-ENGLISH DISTILLATION (depth=4)")
    print(f"{'='*70}")
    dt = DecisionTreeClassifier(max_depth=4, random_state=42, criterion="gini")
    dt.fit(X, y_v7)
    tree = dt.tree_
    feature_columns = list(v7["feature_columns"])

    # Walk every leaf, print its rule + setting + sample-count.
    def walk(node, conditions):
        if tree.children_left[node] == -1:
            # leaf
            class_idx = int(tree.value[node].argmax())
            setting = int(dt.classes_[class_idx])
            samples = int(tree.value[node].sum())
            yield (conditions, setting, samples)
            return
        f = int(tree.feature[node])
        t = float(tree.threshold[node])
        fname = feature_columns[f]
        yield from walk(int(tree.children_left[node]),
                        conditions + [(fname, "<=", t)])
        yield from walk(int(tree.children_right[node]),
                        conditions + [(fname, ">", t)])

    leaves = list(walk(0, []))
    leaves.sort(key=lambda x: -x[2])
    total = sum(s for _, _, s in leaves)
    print(f"\n  All {len(leaves)} leaves of the depth-4 distillation, sorted by hand-count:\n")
    for i, (conds, setting, samples) in enumerate(leaves, 1):
        pct = 100 * samples / total
        cond_str = "  AND  ".join(f"{f}{op}{v:.1f}" for f, op, v in conds)
        print(f"  Rule {i}: ({samples:>5,} hands, {pct:5.2f}%)")
        print(f"    IF   {cond_str}")
        print(f"    THEN setting {setting}: {setting_layout(setting)}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
