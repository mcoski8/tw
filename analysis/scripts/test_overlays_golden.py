"""
Golden-hand regression tests for the per-profile overlays
``strategy_omaha_overlay`` and ``strategy_topdef_overlay`` (Sprint 7
Phase C, Session 15).

Sample-measured headline (300K-hand random sample):
  * OmahaFirst overlay: 45.82% → 54.69% vs br_omaha (+8.87pp)
  * TopDef overlay:     46.12% → 50.14% vs br_topdef  (+4.02pp)

These tests lock in current behaviour so future weight tweaks or branch
edits surface immediately. Same structure as ``test_strategy_v3_golden``:

  1. Per-branch goldens for each overlay (setting_index + shape).
  2. Cases that specifically exercise overlay-vs-v3 divergence (premium
     pair to bot, top-sacrifice on Q-or-lower max, etc.).
  3. 100-hand seed=42 SHA fixture per overlay.
  4. Dispatcher round-trip via ``strategy_for_profile``.

Captured 2026-04-27 from encode_rules.strategy_omaha_overlay /
strategy_topdef_overlay.
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
from encode_rules import (  # noqa: E402
    setting_shape,
    strategy_for_profile,
    strategy_omaha_overlay,
    strategy_topdef_overlay,
    strategy_v3,
)


def _sorted_bytes(card_strs: list[str]) -> np.ndarray:
    arr = np.array([Card.parse(c).idx for c in card_strs], dtype=np.uint8)
    arr.sort()
    return arr


# ---------------------------------------------------------------------------
# 1. OmahaFirst overlay goldens.
#
# Cases marked OVERLAY-DIVERGES are where the overlay deliberately differs
# from v3 (premium-pair-to-bot or pair-rank-special-to-bot). Cases marked
# AGREES_WITH_V3 verify the overlay falls through to v3 behaviour for
# branches where mining showed no rule-level shift (quads, trips, etc.).
# ---------------------------------------------------------------------------

OMAHA_GOLDEN: list[tuple[str, list[str], int, tuple]] = [
    # Quads / trips / trips_pair — all v3-equivalent.
    ("quads_low_with_high_singletons",
     ["2c","2d","2h","2s","Ah","Kh","5d"],     90, (14, (2, 2),  (2, 2, 5, 13))),
    ("quads_high_kings",
     ["Ks","Kh","Kc","Kd","7s","4h","2c"],     39, (7,  (13, 13), (2, 4, 13, 13))),
    ("trips_pair_low_high",
     ["5c","5d","5h","Ks","Kd","8s","2c"],     65, (8,  (5, 5),   (2, 5, 13, 13))),
    ("trips_pair_high_low",
     ["As","Ad","Ah","4c","4d","9h","2s"],     57, (9,  (14, 14), (2, 4, 4, 14))),
    ("pure_trips",
     ["8c","8d","8h","Ks","Qd","5h","2c"],     99, (13, (8, 8),   (2, 5, 8, 12))),

    # Two-pair OVERLAY-DIVERGES — premium high pair to bot.
    ("two_pair_AAKK_v3_compatible",
     ["As","Ah","Kd","Kh","7c","4d","2s"],     39, (7,  (13, 13), (2, 4, 14, 14))),
    ("two_pair_AAQQ_premium_high_to_bot",
     ["As","Ah","Qd","Qc","9s","4h","2c"],     39, (9,  (12, 12), (2, 4, 14, 14))),
    ("two_pair_KKJJ_premium_high_to_bot",
     ["Kc","Kd","Jc","Jh","9s","6h","2c"],     39, (9,  (11, 11), (2, 6, 13, 13))),
    ("two_pair_TTJJ_both_pairs_10_to_12",
     ["Tc","Td","Jh","Js","Ah","6c","2d"],     99, (14, (10, 10), (2, 6, 11, 11))),
    ("two_pair_default_KKQQ_premium_high_to_bot",
     ["Ks","Kh","Qd","Qc","9s","4h","2c"],     39, (9,  (12, 12), (2, 4, 13, 13))),

    # Two_pair low (high <= 5) — both to bot, same as v3.
    ("two_pair_low_4422_no_pair_mid",
     ["4c","4d","2h","2s","Ks","Qh","9c"],    104, (13, (9, 12),  (2, 2, 4, 4))),

    # Two-pair default mid range — same as v3 (mid pair → mid).
    ("two_pair_default_TT88_v3_compatible",
     ["Tc","Td","8h","8s","As","Kh","4d"],    102, (14, (10, 10), (4, 8, 8, 13))),

    # Three pair OVERLAY-DIVERGES — premium-pair-flip (high_pair >= 13):
    # high → BOT, mid pair → MID. v3 default was AA→MID with both KK+99 in bot.
    ("three_pair_premium_flip",
     ["As","Ad","Kh","Kc","9h","9s","4c"],      9, (4,  (13, 13), (9, 9, 14, 14))),

    # Single-pair OVERLAY-DIVERGES — pair rank ∈ {A, K, 2} → bot.
    ("single_pair_AA_to_bot",
     ["As","Ah","Kc","Qd","Jc","8h","4d"],     69, (13, (11, 12), (4, 8, 14, 14))),
    ("single_pair_KK_to_bot",
     ["Kc","Kh","As","Qd","Jc","8h","4d"],     99, (14, (11, 12), (4, 8, 13, 13))),
    ("single_pair_22_to_bot",
     ["2c","2d","Kh","Qs","Jc","8h","4d"],    104, (13, (11, 12), (2, 2, 4, 8))),
    ("single_pair_QQ_v3_default",
     ["Qc","Qd","Kh","Js","9c","6h","3d"],    104, (13, (12, 12), (3, 6, 9, 11))),

    # High-only — same shape as v3 here (DS+8/conn+4 weights only swing
    # decisions when bot DS feasible AND mid suited+connected compete).
    ("high_only_broadway",
     ["As","Kh","Qs","Jh","Th","9s","4d"],     94, (14, (4, 13),  (9, 10, 11, 12))),
    ("high_only_low",
     ["As","Kh","Qd","9s","7d","4h","2c"],     92, (14, (2, 9),   (4, 7, 12, 13))),
]


# ---------------------------------------------------------------------------
# 2. TopDef overlay goldens.
#
# Top-sacrifice rule applies only to single-pair and high_only branches.
# All other categories must match v3 byte-for-byte.
# ---------------------------------------------------------------------------

TOPDEF_GOLDEN: list[tuple[str, list[str], int, tuple]] = [
    # Quads / trips / trips_pair / two_pair / three_pair — all match v3.
    ("quads_low_with_high_singletons",
     ["2c","2d","2h","2s","Ah","Kh","5d"],     90, (14, (2, 2),   (2, 2, 5, 13))),
    ("quads_high_kings",
     ["Ks","Kh","Kc","Kd","7s","4h","2c"],     39, (7,  (13, 13), (2, 4, 13, 13))),
    ("trips_pair_low_high_v3_default",
     ["5c","5d","5h","Ks","Kd","8s","2c"],     65, (8,  (5, 5),   (2, 5, 13, 13))),
    # Premium trips (rank >= 13) trips_pair — break-down: 1 trip on top,
    # 2 trips in mid, pair stays in bot.
    ("trips_pair_premium_KKK_44_breakdown",
     ["Kc","Kd","Kh","4c","4d","9h","2s"],     74, (13, (13, 13), (2, 4, 4, 9))),
    ("pure_trips_low_v3_default",
     ["8c","8d","8h","Ks","Qd","5h","2c"],     99, (13, (8, 8),   (2, 5, 8, 12))),
    ("pure_trips_premium_AAA_breakdown",
     ["Ac","Ad","Ah","Ks","Qd","5h","2c"],     74, (14, (14, 14), (2, 5, 12, 13))),
    # Two-pair AAKK — TopDef AAKK reverse: AA→MID (vs v3's KK→MID).
    ("two_pair_AAKK_aa_to_mid",
     ["As","Ah","Kd","Kh","7c","4d","2s"],     44, (7,  (14, 14), (2, 4, 13, 13))),
    ("two_pair_AAQQ_v3_default",
     ["As","Ah","Qd","Qc","9s","4h","2c"],     44, (9,  (14, 14), (2, 4, 12, 12))),
    ("two_pair_default_KKQQ_v3_default",
     ["Ks","Kh","Qd","Qc","9s","4h","2c"],     44, (9,  (13, 13), (2, 4, 12, 12))),
    ("two_pair_low_4422",
     ["4c","4d","2h","2s","Ks","Qh","9c"],    104, (13, (9, 12),  (2, 2, 4, 4))),
    ("two_pair_default_TT88",
     ["Tc","Td","8h","8s","As","Kh","4d"],    102, (14, (10, 10), (4, 8, 8, 13))),
    ("three_pair",
     ["As","Ad","Kh","Kc","9h","9s","4c"],     14, (4,  (14, 14), (9, 9, 13, 13))),

    # Single-pair: top-sacrifice fires only when highest singleton < Q.
    ("single_pair_AA_max_unpaired_K_keeps_top",
     ["As","Ah","Kc","Qd","Jc","8h","4d"],     74, (13, (14, 14), (4, 8, 11, 12))),
    ("single_pair_KK_max_unpaired_A_keeps_top",
     ["Kc","Kh","As","Qd","Jc","8h","4d"],    104, (14, (13, 13), (4, 8, 11, 12))),
    ("single_pair_22_max_unpaired_K_keeps_top",
     ["2c","2d","Kh","Qs","Jc","8h","4d"],     90, (13, (2, 2),   (4, 8, 11, 12))),
    ("single_pair_QQ_max_unpaired_K_keeps_top",
     ["Qc","Qd","Kh","Js","9c","6h","3d"],    104, (13, (12, 12), (3, 6, 9, 11))),
    ("topdef_pair_Q_max_keeps_top_threshold_12",
     ["8c","8d","Qh","Js","9c","6h","3d"],     99, (12, (8, 8),   (3, 6, 9, 11))),
    ("topdef_pair_J_max_sacrifices_to_lowest",
     ["7c","7d","Jh","Ts","9c","6h","3d"],      5, (3,  (7, 7),   (6, 9, 10, 11))),

    # High-only: same threshold via _hi_only_pick_topdef.
    ("high_only_broadway",
     ["As","Kh","Qs","Jh","Th","9s","4d"],     94, (14, (4, 13),  (9, 10, 11, 12))),
    ("high_only_low",
     ["As","Kh","Qd","9s","7d","4h","2c"],     92, (14, (2, 9),   (4, 7, 12, 13))),
]


def _check(strategy_fn, name, cards, exp_idx, exp_shape):
    arr = _sorted_bytes(cards)
    got = int(strategy_fn(arr))
    sh = setting_shape(arr, got)
    assert got == exp_idx, (
        f"{name}: setting drift  got={got} expected={exp_idx}\n"
        f"  got_shape={sh}  expected_shape={exp_shape}"
    )
    assert sh == exp_shape, f"{name}: shape drift  got={sh} expected={exp_shape}"


def test_omaha_overlay_goldens():
    for case in OMAHA_GOLDEN:
        _check(strategy_omaha_overlay, *case)


def test_topdef_overlay_goldens():
    for case in TOPDEF_GOLDEN:
        _check(strategy_topdef_overlay, *case)


# ---------------------------------------------------------------------------
# 3. Overlay-vs-v3 divergence assertions on representative cases.
# Catches accidental "the overlay just calls v3" regressions.
# ---------------------------------------------------------------------------

OMAHA_MUST_DIFFER_FROM_V3 = [
    ["As","Ah","Qd","Qc","9s","4h","2c"],   # AAQQ premium-to-bot
    ["Kc","Kd","Jc","Jh","9s","6h","2c"],   # KKJJ premium-to-bot
    ["Tc","Td","Jh","Js","Ah","6c","2d"],   # TTJJ both 10-12
    ["As","Ah","Kc","Qd","Jc","8h","4d"],   # AA single-pair → bot
    ["2c","2d","Kh","Qs","Jc","8h","4d"],   # 22 single-pair → bot
    ["As","Ad","Kh","Kc","9h","9s","4c"],   # 3-pair AAKK99 — premium flip
]


def test_omaha_overlay_diverges_from_v3():
    for cards in OMAHA_MUST_DIFFER_FROM_V3:
        arr = _sorted_bytes(cards)
        s_v3 = int(strategy_v3(arr))
        s_om = int(strategy_omaha_overlay(arr))
        assert s_v3 != s_om, (
            f"omaha_overlay collapsed to v3 on {cards}: both gave setting {s_v3}"
        )


def test_topdef_overlay_diverges_from_v3_on_low_max_singleton():
    # Hand max singleton is J (< Q threshold) → topdef sacrifices to lowest.
    cards = ["7c","7d","Jh","Ts","9c","6h","3d"]
    arr = _sorted_bytes(cards)
    s_v3 = int(strategy_v3(arr))
    s_td = int(strategy_topdef_overlay(arr))
    assert s_v3 != s_td, (
        f"topdef_overlay collapsed to v3 on {cards}: both gave setting {s_v3}"
    )


TOPDEF_PREMIUM_TRIPS_DIVERGENT = [
    ["Ac","Ad","Ah","Ks","Qd","5h","2c"],   # AAA — top-trip break-down
    ["Kc","Kd","Kh","Qs","9d","5h","2c"],   # KKK — same
    ["Kc","Kd","Kh","4c","4d","9h","2s"],   # KKK + 44 trips_pair break-down
    ["As","Ah","Kd","Kh","7c","4d","2s"],   # AAKK reverse: AA→MID
]


def test_topdef_premium_trips_breakdown_and_aakk_reverse():
    """Lock in the Phase C+ rules: premium trips top-break-down + AAKK reverse."""
    for cards in TOPDEF_PREMIUM_TRIPS_DIVERGENT:
        arr = _sorted_bytes(cards)
        s_v3 = int(strategy_v3(arr))
        s_td = int(strategy_topdef_overlay(arr))
        assert s_v3 != s_td, (
            f"topdef_overlay must differ from v3 on {cards}; both gave {s_v3}"
        )


# ---------------------------------------------------------------------------
# 4. 100-hand fixed-seed SHA fixtures.
# ---------------------------------------------------------------------------

EXPECTED_OMAHA_OUTPUT_SHA = (
    "3099dfd77305f4dc5c489cfdb5175eaf10410ea640acdf92bde92fbf23cfd801"
)
EXPECTED_OMAHA_SHAPE_SHA = (
    "6bc16fed95d33d238195a0d4604bc9afa170c67b96022c92b957e6b8e7e1eb24"
)
EXPECTED_TOPDEF_OUTPUT_SHA = (
    "6490e324593b1a3959cc29b14dbb6a9b5f437d1c0069cb6ae4e19de5f4aafb25"
)
EXPECTED_TOPDEF_SHAPE_SHA = (
    "71faf6a19e47e325eb1072d86f5760ea0307ba560c36b9111d97c91c847f9f2f"
)


def _seeded_hands(n: int, seed: int) -> list[np.ndarray]:
    rng = np.random.default_rng(seed)
    out = []
    for _ in range(n):
        h = rng.choice(52, size=7, replace=False).astype(np.uint8)
        h.sort()
        out.append(h)
    return out


def _check_sha(strategy_fn, hands, exp_out_sha, exp_shape_sha, label):
    outs = np.array([strategy_fn(h) for h in hands], dtype=np.uint8)
    out_sha = hashlib.sha256(outs.tobytes()).hexdigest()
    assert out_sha == exp_out_sha, (
        f"{label} 100-hand output hash drifted\n"
        f"  got      {out_sha}\n  expected {exp_out_sha}"
    )
    shapes = [setting_shape(hands[i], int(outs[i])) for i in range(len(hands))]
    sr = ";".join(
        f"{s[0]}|{','.join(map(str, s[1]))}|{','.join(map(str, s[2]))}"
        for s in shapes
    )
    sha = hashlib.sha256(sr.encode()).hexdigest()
    assert sha == exp_shape_sha, (
        f"{label} 100-hand shape hash drifted\n"
        f"  got      {sha}\n  expected {exp_shape_sha}"
    )


def test_omaha_seeded_100_hand_signature():
    hands = _seeded_hands(100, 42)
    _check_sha(strategy_omaha_overlay, hands,
               EXPECTED_OMAHA_OUTPUT_SHA, EXPECTED_OMAHA_SHAPE_SHA,
               "omaha_overlay")


def test_topdef_seeded_100_hand_signature():
    hands = _seeded_hands(100, 42)
    _check_sha(strategy_topdef_overlay, hands,
               EXPECTED_TOPDEF_OUTPUT_SHA, EXPECTED_TOPDEF_SHAPE_SHA,
               "topdef_overlay")


# ---------------------------------------------------------------------------
# 5. Dispatcher round-trip.
# ---------------------------------------------------------------------------

def test_dispatcher_routes_to_correct_strategy():
    cards = ["As","Ah","Qd","Qc","9s","4h","2c"]   # AAQQ — overlay flips for omaha
    arr = _sorted_bytes(cards)
    expected = {
        "multiway":    int(strategy_v3(arr)),
        "mfsuitaware": int(strategy_v3(arr)),
        "weighted":    int(strategy_v3(arr)),
        "omaha":       int(strategy_omaha_overlay(arr)),
        "topdef":      int(strategy_topdef_overlay(arr)),
    }
    for prof, exp in expected.items():
        got = int(strategy_for_profile(arr, prof))
        assert got == exp, f"profile={prof}: got {got} expected {exp}"

    # Unknown profile falls back to v3.
    fallback = int(strategy_for_profile(arr, "no-such-profile"))
    assert fallback == expected["multiway"]


# ---------------------------------------------------------------------------
# Test runner.
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
