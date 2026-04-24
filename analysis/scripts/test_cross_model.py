"""
Self-tests for ``tw_analysis.cross_model``.

Uses hand-rolled synthetic ``BrFile`` records (no real .bin files) so the tests
run in milliseconds and don't require the full 6M-record solve output.

Run:
    python3 analysis/scripts/test_cross_model.py
"""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402

from tw_analysis.br_reader import (  # noqa: E402
    NUM_SETTINGS,
    RECORD_DTYPE,
    BrFile,
    BrHeader,
)
from tw_analysis.cross_model import (  # noqa: E402
    build_cross_model,
    consensus_setting_counts,
    pairwise_agreement,
    unanimous_mask,
    unanimous_setting_counts,
    unique_settings_per_hand,
)


def expect(cond: bool, msg: str) -> None:
    if not cond:
        print(f"  FAIL: {msg}")
        raise SystemExit(1)


def fake_br(
    settings: list[int],
    evs: list[float],
    tag: int,
    label_for_path: str,
) -> BrFile:
    n = len(settings)
    assert len(evs) == n
    recs = np.empty(n, dtype=RECORD_DTYPE)
    recs["canonical_id"] = np.arange(n, dtype=np.uint32)
    recs["best_setting_index"] = np.array(settings, dtype=np.uint8)
    recs["best_ev"] = np.array(evs, dtype=np.float32)
    header = BrHeader(
        version=1,
        samples=1000,
        base_seed=0,
        canonical_total=n,
        opp_model_tag=tag,
    )
    return BrFile(
        path=Path(f"/tmp/{label_for_path}.bin"),
        header=header,
        records=recs,
        is_complete=True,
    )


def test_single_file_is_trivially_unanimous() -> None:
    br = fake_br([0, 1, 104, 50], [0.0, 1.0, 2.0, 3.0], 1, "a")
    cm = build_cross_model([br])
    expect(cm.n_models == 1, "n_models should be 1")
    expect(cm.n_hands == 4, "n_hands should be 4")
    mask = unanimous_mask(cm)
    expect(mask.all(), "single-file case: every hand is unanimous")
    uniq = unique_settings_per_hand(cm)
    expect(np.all(uniq == 1), "single-file case: unique-count is 1 per hand")


def test_two_files_unanimity_and_uniqueness() -> None:
    # 5 hands: 0,1,2 unanimous (same setting); 3,4 differ.
    a = fake_br([10, 20, 30, 40, 50], [0, 0, 0, 0, 0], 1, "a")
    b = fake_br([10, 20, 30, 41, 55], [0, 0, 0, 0, 0], 2, "b")
    cm = build_cross_model([a, b])
    mask = unanimous_mask(cm)
    expect(mask.tolist() == [True, True, True, False, False],
           f"unanimous mask wrong: {mask.tolist()}")
    uniq = unique_settings_per_hand(cm)
    expect(uniq.tolist() == [1, 1, 1, 2, 2],
           f"unique-count wrong: {uniq.tolist()}")


def test_three_files_various_distinct_counts() -> None:
    # 4 hands.
    #  h0: all agree on 10 → 1 distinct
    #  h1: A=B, C different → 2 distinct
    #  h2: all different → 3 distinct
    #  h3: all different → 3 distinct
    a = fake_br([10, 20, 30, 40], [0] * 4, 1, "a")
    b = fake_br([10, 20, 31, 41], [0] * 4, 2, "b")
    c = fake_br([10, 21, 32, 42], [0] * 4, 3, "c")
    cm = build_cross_model([a, b, c])
    uniq = unique_settings_per_hand(cm)
    expect(uniq.tolist() == [1, 2, 3, 3],
           f"unique-count wrong: {uniq.tolist()}")
    mask = unanimous_mask(cm)
    expect(mask.tolist() == [True, False, False, False],
           f"unanimous mask wrong: {mask.tolist()}")


def test_pairwise_agreement_matrix() -> None:
    # 5 hands.
    # A vs B: agree on h0,h1,h2 → 3/5 = 0.6
    # A vs C: agree on h0 only → 1/5 = 0.2
    # B vs C: agree on h0, h3, h4 (both 99) → 3/5 = 0.6
    a = fake_br([10, 20, 30, 40, 50], [0] * 5, 1, "a")
    b = fake_br([10, 20, 30, 99, 99], [0] * 5, 2, "b")
    c = fake_br([10, 99, 99, 99, 99], [0] * 5, 3, "c")
    cm = build_cross_model([a, b, c])
    pa = pairwise_agreement(cm)
    expect(pa.shape == (3, 3), f"shape wrong: {pa.shape}")
    expect(np.allclose(np.diag(pa), 1.0), "diagonal must be 1.0")
    expect(np.allclose(pa, pa.T), "matrix must be symmetric")
    expect(abs(pa[0, 1] - 0.6) < 1e-9, f"A/B agreement: {pa[0, 1]}")
    expect(abs(pa[0, 2] - 0.2) < 1e-9, f"A/C agreement: {pa[0, 2]}")
    expect(abs(pa[1, 2] - 0.6) < 1e-9, f"B/C agreement: {pa[1, 2]}")


def test_consensus_histograms() -> None:
    # 3 hands. A picks [10, 10, 20]. B picks [10, 20, 20].
    # all-cells counts: setting 10 → 3, setting 20 → 3, everything else 0.
    # unanimous hands: h0 (both=10), h2 (both=20). h1 differs.
    # unanimous_counts: setting 10 → 1, setting 20 → 1.
    a = fake_br([10, 10, 20], [0] * 3, 1, "a")
    b = fake_br([10, 20, 20], [0] * 3, 2, "b")
    cm = build_cross_model([a, b])

    all_counts = consensus_setting_counts(cm)
    expect(all_counts.shape == (NUM_SETTINGS,), f"shape: {all_counts.shape}")
    expect(int(all_counts[10]) == 3, f"cell count for 10: {all_counts[10]}")
    expect(int(all_counts[20]) == 3, f"cell count for 20: {all_counts[20]}")
    expect(int(all_counts.sum()) == 6,
           f"sum must equal cells (6): {all_counts.sum()}")

    u_counts = unanimous_setting_counts(cm)
    expect(int(u_counts[10]) == 1, f"unanimous count for 10: {u_counts[10]}")
    expect(int(u_counts[20]) == 1, f"unanimous count for 20: {u_counts[20]}")
    expect(int(u_counts.sum()) == 2,
           f"sum must equal unanimous hands (2): {u_counts.sum()}")


def test_mismatched_canonical_total_rejected() -> None:
    a = fake_br([10, 10, 10], [0] * 3, 1, "a")
    b = fake_br([10, 10, 10, 10], [0] * 4, 2, "b")
    try:
        build_cross_model([a, b])
    except ValueError as e:
        expect("canonical_total" in str(e),
               f"error message should mention canonical_total: {e}")
        return
    expect(False, "mismatched canonical_total should have raised")


def test_empty_file_list_rejected() -> None:
    try:
        build_cross_model([])
    except ValueError:
        return
    expect(False, "empty file list should have raised")


def test_settings_and_evs_matrix_shapes() -> None:
    a = fake_br([10, 20], [1.5, -1.5], 1, "a")
    b = fake_br([11, 21], [2.5, -2.5], 2, "b")
    cm = build_cross_model([a, b])
    expect(cm.settings.shape == (2, 2), f"settings shape: {cm.settings.shape}")
    expect(cm.evs.shape == (2, 2), f"evs shape: {cm.evs.shape}")
    expect(cm.settings[0, 0] == 10 and cm.settings[0, 1] == 11,
           f"row 0 settings: {cm.settings[0]}")
    expect(abs(float(cm.evs[0, 0]) - 1.5) < 1e-6, f"EV[0,0]: {cm.evs[0, 0]}")
    expect(abs(float(cm.evs[1, 1]) + 2.5) < 1e-6, f"EV[1,1]: {cm.evs[1, 1]}")


def test_labels_come_from_headers() -> None:
    # tag 2 = MiddleFirstSuitAware (bare name), tag 1_003_090 = HeuristicMixed OmahaFirst p=.90
    a = fake_br([10], [0], 2, "a")
    b = fake_br([20], [0], 1_003_090, "b")
    cm = build_cross_model([a, b])
    expect(cm.labels[0] == "MiddleFirstSuitAware", f"label 0: {cm.labels[0]}")
    expect("OmahaFirst" in cm.labels[1] and "p=0.90" in cm.labels[1],
           f"label 1: {cm.labels[1]}")


def main() -> int:
    tests = [
        ("single_file_is_trivially_unanimous", test_single_file_is_trivially_unanimous),
        ("two_files_unanimity_and_uniqueness", test_two_files_unanimity_and_uniqueness),
        ("three_files_various_distinct_counts", test_three_files_various_distinct_counts),
        ("pairwise_agreement_matrix", test_pairwise_agreement_matrix),
        ("consensus_histograms", test_consensus_histograms),
        ("mismatched_canonical_total_rejected", test_mismatched_canonical_total_rejected),
        ("empty_file_list_rejected", test_empty_file_list_rejected),
        ("settings_and_evs_matrix_shapes", test_settings_and_evs_matrix_shapes),
        ("labels_come_from_headers", test_labels_come_from_headers),
    ]
    for name, fn in tests:
        print(f"- {name} ... ", end="")
        fn()
        print("ok")
    print(f"All {len(tests)} tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
