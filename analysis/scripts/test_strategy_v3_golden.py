"""
Golden-hand regression tests for ``encode_rules.strategy_v3``.

strategy_v3 is the production rule chain (Sprint 7 Phase B+, Session 14).
It scores 56.16% shape-agreement against the multiway-robust setting on
all 6M canonical hands. These tests lock in its current behaviour so any
future refactor that drifts from the published rules surfaces immediately.

Test design:

  1. **Per-branch golden hands.** One or more 7-card hands per dispatch
     branch in strategy_v3 (quads, trips_pair, pure trips, two_pair AAKK,
     two_pair low ≤5, two_pair default, three_pair, single pair,
     high_only). Each case asserts both the literal setting_index and the
     decoded (top_rank, mid_ranks, bot_ranks) shape — the index pins
     position-level layout, the shape pins the rule-level decision.

  2. **Setting-104 sanity.** Verifies our shared mental model: the
     "naive" sort-and-slice arrangement decodes to setting 104 with
     top_pos=6, mid=(4,5), bot=(0,1,2,3).

  3. **v3 ≠ v4 lockstep.** Captures a known hand where the v4 weight
     rebalance changes the answer; if anyone accidentally collapses v4
     into v3, this test fires.

  4. **100-hand fixed-seed fixture.** Runs strategy_v3 on 100 random
     hands (seed=42) and asserts a sha256 of the predictions + a sha256
     of the decoded shapes. Guards against drift the per-branch hands
     don't hit.

The values below were captured 2026-04-27 from the production
strategy_v3 / strategy_v4 in encode_rules.py. The capture command lives
in this file's docstring for reproducibility.
"""
from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.settings import Card  # noqa: E402
from tw_analysis.features import decode_tier_positions  # noqa: E402
from encode_rules import (  # noqa: E402
    positions_to_setting_index,
    setting_shape,
    strategy_v3,
    strategy_v4,
)


# ---------------------------------------------------------------------------
# Helpers.
# ---------------------------------------------------------------------------

def _sorted_bytes(card_strs: list[str]) -> np.ndarray:
    arr = np.array([Card.parse(c).idx for c in card_strs], dtype=np.uint8)
    arr.sort()
    return arr


# ---------------------------------------------------------------------------
# 1. Per-branch golden hands.
#
# Each tuple: (case_name, cards_input, expected_setting_idx, expected_shape, branch).
# ``cards_input`` is the human-readable order; the test sorts to engine order.
# ``expected_shape`` is (top_rank, sorted_mid_ranks_tuple, sorted_bot_ranks_tuple).
# ---------------------------------------------------------------------------

GOLDEN_CASES: list[tuple[str, list[str], int, tuple, str]] = [
    # --- Quads branch ---
    ("quads_low_with_high_singletons",
     ["2c", "2d", "2h", "2s", "Ah", "Kh", "5d"],
     90, (14, (2, 2), (2, 2, 5, 13)), "quads"),
    ("quads_high_kings_low_kickers",
     ["Ks", "Kh", "Kc", "Kd", "7s", "4h", "2c"],
     39, (7, (13, 13), (2, 4, 13, 13)), "quads"),

    # --- Trips + pair (full house shape) ---
    ("trips_pair_low_trips_high_pair",
     ["5c", "5d", "5h", "Ks", "Kd", "8s", "2c"],
     65, (8, (5, 5), (2, 5, 13, 13)), "trips_pair"),
    ("trips_pair_high_trips_low_pair",
     ["As", "Ad", "Ah", "4c", "4d", "9h", "2s"],
     57, (9, (14, 14), (2, 4, 4, 14)), "trips_pair"),

    # --- Pure trips ---
    ("pure_trips_8s_with_KQ_singletons",
     ["8c", "8d", "8h", "Ks", "Qd", "5h", "2c"],
     99, (13, (8, 8), (2, 5, 8, 12)), "trips"),

    # --- Two-pair AAKK exception (KK to mid) ---
    ("two_pair_AAKK_low_pair_to_mid",
     ["As", "Ah", "Kd", "Kh", "7c", "4d", "2s"],
     39, (7, (13, 13), (2, 4, 14, 14)), "two_pair_aakk"),

    # --- Two-pair low (high <= 5): both pairs to bot, mid = highest 2 singletons ---
    ("two_pair_low_4422_no_pair_mid",
     ["4c", "4d", "2h", "2s", "Ks", "Qh", "9c"],
     104, (13, (9, 12), (2, 2, 4, 4)), "two_pair_low"),
    ("two_pair_low_5533_no_pair_mid",
     ["5c", "5d", "3h", "3s", "Ah", "Kc", "7s"],
     104, (14, (7, 13), (3, 3, 5, 5)), "two_pair_low"),

    # --- Two-pair default (high >= 6, not AAKK): high pair to mid ---
    ("two_pair_default_TT88_with_AK",
     ["Tc", "Td", "8h", "8s", "As", "Kh", "4d"],
     102, (14, (10, 10), (4, 8, 8, 13)), "two_pair_default"),
    ("two_pair_default_KKQQ_low_kickers",
     ["Ks", "Kh", "Qd", "Qc", "9s", "4h", "2c"],
     44, (9, (13, 13), (2, 4, 12, 12)), "two_pair_default"),

    # --- Three pair (highest pair to mid via generic pairs branch) ---
    ("three_pair_AAKK99_with_4_kicker",
     ["As", "Ad", "Kh", "Kc", "9h", "9s", "4c"],
     14, (4, (14, 14), (9, 9, 13, 13)), "three_pair"),

    # --- Single pair ---
    ("single_pair_KK_high_kickers",
     ["Kc", "Kh", "As", "Qd", "Jc", "8h", "4d"],
     104, (14, (13, 13), (4, 8, 11, 12)), "pair"),

    # --- High_only (no-pair) via search ---
    ("high_only_broadway_DS_bot",
     ["As", "Kh", "Qs", "Jh", "Th", "9s", "4d"],
     94, (14, (4, 13), (9, 10, 11, 12)), "high_only"),
    ("high_only_low_no_DS_no_run",
     ["As", "Kh", "Qd", "9s", "7d", "4h", "2c"],
     92, (14, (2, 9), (4, 7, 12, 13)), "high_only"),
]


def _check_case(name: str, cards: list[str], exp_idx: int, exp_shape: tuple) -> None:
    arr = _sorted_bytes(cards)
    got_idx = int(strategy_v3(arr))
    got_shape = setting_shape(arr, got_idx)
    assert got_idx == exp_idx, (
        f"{name}: setting_index drift  got={got_idx}  expected={exp_idx}\n"
        f"  got_shape={got_shape}  expected_shape={exp_shape}"
    )
    assert got_shape == exp_shape, (
        f"{name}: shape drift  got={got_shape}  expected={exp_shape}"
    )


def test_golden_quads():
    for case in GOLDEN_CASES:
        if case[4] == "quads":
            _check_case(case[0], case[1], case[2], case[3])


def test_golden_trips_pair():
    for case in GOLDEN_CASES:
        if case[4] == "trips_pair":
            _check_case(case[0], case[1], case[2], case[3])


def test_golden_pure_trips():
    for case in GOLDEN_CASES:
        if case[4] == "trips":
            _check_case(case[0], case[1], case[2], case[3])


def test_golden_two_pair_aakk():
    for case in GOLDEN_CASES:
        if case[4] == "two_pair_aakk":
            _check_case(case[0], case[1], case[2], case[3])


def test_golden_two_pair_low():
    for case in GOLDEN_CASES:
        if case[4] == "two_pair_low":
            _check_case(case[0], case[1], case[2], case[3])


def test_golden_two_pair_default():
    for case in GOLDEN_CASES:
        if case[4] == "two_pair_default":
            _check_case(case[0], case[1], case[2], case[3])


def test_golden_three_pair():
    for case in GOLDEN_CASES:
        if case[4] == "three_pair":
            _check_case(case[0], case[1], case[2], case[3])


def test_golden_single_pair():
    for case in GOLDEN_CASES:
        if case[4] == "pair":
            _check_case(case[0], case[1], case[2], case[3])


def test_golden_high_only():
    for case in GOLDEN_CASES:
        if case[4] == "high_only":
            _check_case(case[0], case[1], case[2], case[3])


# ---------------------------------------------------------------------------
# 2. Setting-104 sanity. Pins the (top_pos, mid_pos, bot_pos) decomposition
#    that all golden tests implicitly rely on.
# ---------------------------------------------------------------------------

def test_setting_104_decomposes_to_naive_layout():
    t, m, b = decode_tier_positions(104)
    assert t == 6, f"setting 104 top_pos={t} expected 6"
    assert m == (4, 5), f"setting 104 mid={m} expected (4, 5)"
    assert b == (0, 1, 2, 3), f"setting 104 bot={b} expected (0, 1, 2, 3)"


def test_positions_to_setting_index_round_trip_all_105():
    """Inverse mapping is sound across all 105 settings."""
    for s in range(105):
        t, m, _ = decode_tier_positions(s)
        assert positions_to_setting_index(t, m) == s, (
            f"round-trip failed at s={s}  decoded=(t={t}, m={m})"
        )


# ---------------------------------------------------------------------------
# 3. v3 ≠ v4 lockstep.
#
# Session 14 measured v4 = 56.12% vs v3 = 56.16% — they differ on roughly
# 0.04% of 6M hands. The hand below is one such case found by random
# search; the assertion locks in that v3 and v4 are not collapsed.
# ---------------------------------------------------------------------------

V3_V4_DIVERGENT_HAND = ["3s", "4c", "5d", "6s", "7h", "9d", "Ac"]
V3_EXPECTED = (97, (14, (4, 7), (3, 5, 6, 9)))
V4_EXPECTED = (104, (14, (7, 9), (3, 4, 5, 6)))


def test_v3_and_v4_differ_on_known_hand():
    arr = _sorted_bytes(V3_V4_DIVERGENT_HAND)
    s3 = int(strategy_v3(arr))
    s4 = int(strategy_v4(arr))
    sh3 = setting_shape(arr, s3)
    sh4 = setting_shape(arr, s4)
    assert (s3, sh3) == V3_EXPECTED, f"v3 drift: got=({s3}, {sh3})"
    assert (s4, sh4) == V4_EXPECTED, f"v4 drift: got=({s4}, {sh4})"
    assert s3 != s4, "v3 and v4 must not produce the same setting on this hand"


# ---------------------------------------------------------------------------
# 4. 100-hand fixed-seed fixture.
#
# Hashes the strategy_v3 outputs over a deterministic 100-hand sample. Drift
# in any non-tested branch surfaces here even if the per-branch goldens still
# pass.
# ---------------------------------------------------------------------------

EXPECTED_V3_OUTPUT_SHA256 = (
    "80647f0359f012d32e05579596fe725863ab5134d6306df7f14b633b3be7821e"
)
EXPECTED_V3_SHAPE_SHA256 = (
    "8492a15807147648317dce3ab82055c7155c0fb9f95cb898fd5715d60761783e"
)


def _seeded_hands(n: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        h = rng.choice(52, size=7, replace=False).astype(np.uint8)
        h.sort()
        out.append(h)
    return out


def test_seeded_100_hand_v3_signature():
    hands = _seeded_hands(100, 42)
    outs = np.array([strategy_v3(h) for h in hands], dtype=np.uint8)
    out_hash = hashlib.sha256(outs.tobytes()).hexdigest()
    assert out_hash == EXPECTED_V3_OUTPUT_SHA256, (
        f"strategy_v3 100-hand output hash drifted\n"
        f"  got      {out_hash}\n"
        f"  expected {EXPECTED_V3_OUTPUT_SHA256}\n"
        f"  first 5 outputs: {list(outs[:5])}"
    )

    shapes = [setting_shape(hands[i], int(outs[i])) for i in range(len(hands))]
    shape_repr = ";".join(
        f"{s[0]}|{','.join(map(str, s[1]))}|{','.join(map(str, s[2]))}"
        for s in shapes
    )
    shape_hash = hashlib.sha256(shape_repr.encode()).hexdigest()
    assert shape_hash == EXPECTED_V3_SHAPE_SHA256, (
        f"strategy_v3 100-hand shape hash drifted\n"
        f"  got      {shape_hash}\n"
        f"  expected {EXPECTED_V3_SHAPE_SHA256}"
    )


# ---------------------------------------------------------------------------
# Test runner — same convention as analysis/scripts/test_features.py.
# ---------------------------------------------------------------------------

def main() -> int:
    failures: list[tuple[str, Exception]] = []
    test_funcs = [v for k, v in globals().items()
                  if k.startswith("test_") and callable(v)]
    for fn in test_funcs:
        try:
            fn()
            print(f"  PASS  {fn.__name__}")
        except Exception as e:  # noqa: BLE001
            failures.append((fn.__name__, e))
            print(f"  FAIL  {fn.__name__} — {type(e).__name__}: {e}")
    print()
    if failures:
        print(f"{len(failures)} of {len(test_funcs)} tests failed.")
        return 1
    print(f"All {len(test_funcs)} tests passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
