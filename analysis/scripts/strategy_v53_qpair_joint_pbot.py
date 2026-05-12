"""
v53 — v52 + Rule 19 (Q-pair JOINT-only PBOT-take).

Session 67 Phase 3 finding: among 12 sub-variants tested across the
6/7/8/9-pair PBOT-take (C_PAIR_3) and Q-pair PBOT-take (C_PAIR_5)
candidate families, only ONE clears T2 (production-ship threshold):

  Q-pair × PBOT_DS_JOINT cell → take the joint PBOT-DS setting
    (top = max non-pair singleton, mid = 2 same-suit singletons,
     bot = both Q's + 1 kicker matching each pair-suit).

Fire region: 28,512 canonical hands (= 0.47% of canonical-grid;
13.2% of Q-pair = 4.7% of pair category).
Within-cell capture vs v52: +52.85% gap closure.
Whole-grid lift vs v52: +$8.50/1000h (audit harness, oracle grid
realistic_n200).
Non-targeted regression: ZERO. Rule fires ONLY on
(pair_rank=Q × PBOT_DS_JOINT). The structural pair gate
(n_pairs==1, n_quads==0, n_trips==0) ensures no spillover into
multi-pair, high_only, trips, etc.

Why this cell and only this cell:
- Q-pair has the highest oracle PBOT preference of any pair_rank
  (53% across all cells, vs 18-37% for K/A/J/T/9/8/7/6).
- The JOINT cell is structurally the strongest PBOT play (max sing on
  top + ms mid + DS bot all simultaneously achievable). It is the
  dominant oracle PBOT class.
- All other 11 candidates tested (C_PAIR_3a/b/c at all 4 pair_ranks
  6-9; C_PAIR_3b at mid≥{Q, K, A}; C_PAIR_5 simple at Q-pair) failed
  the T1 capture bar OR the T3 net-positive bar.
- The matrix-claimed "$391 WG catalog headroom in PBOT cells" was
  v44's SELECTIVE catch, not catalog-shippable at "one-sentence-
  statable" granularity. Pair PBOT-routing on most cells is ML-only,
  mirroring the high_only S60-S64 outcome — only the Q-pair JOINT
  cell admits a clean rule.

Status: SHIPS as v53. Grader-confirmed S67.
Baseline v52: $2,498 full / $1,522 prefix.
Shipped v53:  $2,490 full / $1,522 prefix (+$9/1000h full;
prefix unchanged because Q-pair JOINT canonical IDs are
concentrated outside the prefix-500K region).
Full-grid pct_opt: 43.34% → 43.43% (+0.09pp).
p90 regret 0.720 → 0.715; p99 1.645 → 1.640.
All non-pair categories byte-identical (surgical via pair gate).
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPTS = ROOT / "analysis" / "scripts"
SRC = ROOT / "analysis" / "src"
for p in (str(SCRIPTS), str(SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

import numpy as np

from strategy_v52_full_high_only_handler import strategy_v52_full_high_only_handler  # noqa: E402
from strategy_v53_c_pair_3 import rule_c_pair_3c  # used helpers re-used below  # noqa: F401
from strategy_v53_c_pair_3 import (  # noqa: E402
    _enumerate_pbot_ds, _build_setting_from_config,
)


def _detect_rule19_qpair_joint_pbot_ds(hand: np.ndarray):
    """If hand is Q-pair AND JOINT PBOT-DS achievable, return chosen
    setting_index. Else return None.

    JOINT criterion: there exists a pair-to-bot DS construction such that
    the 3 leftover singletons can split as
        top = max non-pair singleton,
        mid = 2 other singletons sharing a suit (ms_mid).
    Among multiple JOINT configs, the one with highest mid_high wins
    (preserves mid Hold'em strength).
    """
    info = _enumerate_pbot_ds(hand, allowed_pair_ranks={12})
    if info is None:
        return None
    joints = [c for c in info["configs"] if c["joint"]]
    if not joints:
        return None
    cfg = max(joints, key=lambda c: c["mid_high"])
    return _build_setting_from_config(info, cfg)


def strategy_v53_qpair_joint_pbot(hand: np.ndarray) -> int:
    chosen = _detect_rule19_qpair_joint_pbot_ds(hand)
    if chosen is not None:
        return int(chosen)
    return int(strategy_v52_full_high_only_handler(hand))


if __name__ == "__main__":
    # Smoke: a known Q-pair JOINT hand should route to the joint setting.
    from tw_analysis.settings import parse_hand
    # Qc Qd + suit-c kicker (Jc), suit-d kicker (4d), 2 suit-h sings, Kh top
    test = "Qc Qd 2h 3h 4d Jc Kh"
    h = np.array([c.idx for c in parse_hand(test)], dtype=np.uint8)
    h.sort()
    chosen = _detect_rule19_qpair_joint_pbot_ds(h)
    v52 = strategy_v52_full_high_only_handler(h)
    v53 = strategy_v53_qpair_joint_pbot(h)
    print(f"  hand={test}")
    print(f"  rule_19 detection: {chosen}")
    print(f"  v52 pick: {v52}")
    print(f"  v53 pick: {v53}")
