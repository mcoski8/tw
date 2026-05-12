# SESSION 67 — Pair PBOT-rule candidate sweep (C_PAIR_3, C_PAIR_5)

*Date: 2026-05-12. Phase 3 candidate sweep on pair category per CURRENT_PHASE.md S67 directive. Output: pair catalog harness + C_PAIR_3a/b/c verdicts + Q-pair fallback verdict + v53 ship.*

---

## TL;DR

**The PAIR_DECISION_MATRIX.md "$391 WG catalog-shippable PBOT-cell headroom" was OVERSTATED.** Twelve candidates tested across the C_PAIR_3 (6/7/8/9-pair) and C_PAIR_5 (Q-pair) PBOT-take rule families. **Eleven of twelve are T3 net-negative**; the headroom claim conflated v44's *selective* PBOT-routing with what a rule chain could realize. The only ship-clean candidate is **C_PAIR_5_joint = Q-pair × PBOT_DS_JOINT cell only**:

- Fire region: 28,512 canonical hands = 0.47% of grid (4.7% of pair)
- Capture vs v52: **+52.85%** within-cell gap closure
- Whole-grid lift vs v52: **+$8.50/1000h** (harness, oracle grid realistic_n200)
- Within-cell pct_optimal: 49.86% (rule) vs 31.95% (v52) — +17.9 pp absolute
- Non-targeted regression on entire pair category: **ZERO fires outside Q-pair × PBOT_DS_JOINT, $0 delta**

**Ships as v53. Grader-CONFIRMED: +$9/1000h full grid** (v52 $2,498 → v53 $2,490; harness-projected +$8.50 matched within 6%).

The pair PBOT-cell story is **structurally analogous to high_only's S60-S64 outcome** — the gap exists and is real, but capturing it requires v44's feature-gated selection, not a "one-sentence-statable" rule. Pair is **mostly ML-only at catalog granularity**, with the Q-pair JOINT cell as the lone exception.

---

## Phase 1 — Pair catalog harness `test_rule_catalog_pair.py` (DELIVERED)

Adapts S60's `test_rule_catalog.py` for the pair schema: keys by (pair_rank, cell) instead of (max_rank, cell), uses pre-computed cell tags from `data/drill_pair_v44_per_hand_structural.parquet`, and uses pre-computed v52 picks from `data/drill_pair_v52_per_hand.parquet` as the default baseline (avoids 2.8M Python function calls per audit).

Sanity check — Rule 11 reproduction:
- **Decision 079 grader-confirmed lift: +$6/1000h** (NOT +$11 as cited in S66 CURRENT_PHASE/RESUME — the prompt misquoted Decision 080, which actually ships Rule 12).
- Harness measured: **+$6.21/1000h** across J-pair-J hands.
- **Error: 3.5%** — well within the <5% bar. Harness validated.

---

## Phase 2 — C_PAIR_3 (6/7/8/9-pair PBOT-take) audit

Three sub-variants tested against v52 baseline. Total audit population: 475,200 hands (4 pair_ranks × 2 PBOT cells).

| Variant | Fires | Capture | WG lift | Verdict |
|---|---:|---:|---:|---|
| C_PAIR_3a (simple) | 475,200 | -202.28% | **-$315.39** | T3 |
| C_PAIR_3b (mid≥J) | 212,224 | -105.95% | **-$165.20** | T3 |
| C_PAIR_3c (joint-only) | 114,048 | -11.50% | **-$17.92** | T3 |

**All three T3 net-negative.** The simple variant (3a) is catastrophic; even tightening to JOINT-only (3c) — the structurally strongest PBOT play — still loses money.

**Root cause analysis (8-pair PBOT_DS_JOINT cell as exemplar):**
- Rule 3c fires 100% in this cell (n=28,512), routing all to PBOT_tmax_DS_ms.
- Rule pct_opt = 26.57% vs v52 baseline pct_opt = 44.69%.
- Top mismatch class: `PBOT_tmax_DS_ms → PMID_tmax_SS` n=8,695 mean=$+4,526/1000h.
- **30% of 8-pair JOINT hands have oracle preferring PMID, not PBOT.** Forcing PBOT is wrong on 73% of these hands.

**Mechanism:** at pair_ranks 6/7/8/9, oracle's PBOT preference averages 20-30%. Forcing PBOT on 100% of PBOT_DS-feasible hands at these ranks is wrong 70-80% of the time. The "$88.71 catalog ceiling" cited in PAIR_DECISION_MATRIX.md was the v52→v44 gap — v44 captures it by selective PMID/PBOT gating, not by always-PBOT.

---

## Phase 3 — Fallback experiments (mid-threshold tightening + C_PAIR_5)

Per CURRENT_PHASE.md's fallback directive: tested C_PAIR_3b at stricter mid thresholds AND C_PAIR_5 (Q-pair-only) variants.

### Block 1 — C_PAIR_3b at higher mid thresholds

| Variant | Fires | Capture | WG lift | Verdict |
|---|---:|---:|---:|---|
| C_PAIR_3b (mid≥Q=12) | 128,304 | -73.14% | **-$114.04** | T3 |
| C_PAIR_3b (mid≥K=13) | 51,360 | -31.24% | **-$48.71** | T3 |
| C_PAIR_3b (mid≥A=14) | 0 | +0.00% | $0.00 | T3 (no fires) |

**Mid-strength gating does not rescue 3b.** Tightening to mid≥K leaves 51K fires still net-negative. The failure is structural (selectivity is needed), not threshold-tunable.

### Block 2 — C_PAIR_5 (Q-pair)

| Variant | Fire region | Fires | Capture | WG lift | Verdict |
|---|---|---:|---:|---:|---|
| C_PAIR_5 simple | Q-pair × {JOINT, PARTIAL} | 118,800 | -24.60% | -$17.44 | T3 |
| **C_PAIR_5_joint** | **Q-pair × JOINT only** | **28,512** | **+11.99%** | **+$8.50** | **Below T1 (agg) / T2 within fire-cell** |

The aggregate "Below T1" label is misleading because the audit pool includes PBOT_DS_PARTIAL (where joint-only doesn't fire, diluting capture). **Within the actual fire region (Q-pair × PBOT_DS_JOINT, n=28,512):**

- Capture vs v52: **+52.85%** (clears T1's 40% bar)
- WG lift: **+$8.50/1000h** (clears T2's $5 bar)
- Within-cell pct_optimal: rule 49.86% vs v52 31.95% vs v44 73.25%

**C_PAIR_5_joint clears T2** as a candidate.

### Q-pair × PBOT_DS_PARTIAL alone is also catastrophic

C_PAIR_5_simple's PBOT_DS_PARTIAL slice (n=90,288): **-$25.94/1000h WG**, rule pct_opt 21.27% vs baseline 30.67%. Top mismatch: `PBOT_tnomax_DS_mu → PMID_tmax_SS` n=5,154 mean=$+13,780. The matrix's "$41.20 ceiling for Q-pair PBOT_DS_PARTIAL refinement" is unrealizable by blanket rules.

---

## Non-targeted regression check (C_PAIR_5_joint)

Swept entire pair category (13 pair_ranks × 6 cells = 78 (rank, cell) combos, 2,800,512 hands):

- **Rule fires ONLY on Q-pair × PBOT_DS_JOINT (28,512 hands).**
- **All other 77 (rank, cell) combos: 0 fires, $0 lift.**
- **Total pair-category WG: +$8.50/1000h** (matches audit exactly to 2 decimals).

Non-pair categories: structurally excluded by the pair gate (`n_pairs==1, n_quads==0, n_trips==0`) — rule cannot fire. **Regression check: CLEAN.**

---

## Ship decision — v53 = v52 + Rule 19 (Q-pair JOINT PBOT-DS)

| Metric | v52 (current) | v53 (CONFIRMED) | Δ |
|---|---:|---:|---:|
| Full-grid (grader) | $2,498 | **$2,490** | **+$9/1000h** |
| Full-grid pct_opt | 43.34% | 43.43% | +0.09pp |
| Prefix-grid | $1,522 | $1,522 | $0 |
| Prefix-grid pct_opt | 53.06% | 53.06% | $0 |
| Full p90 regret | 0.720 | 0.715 | improved |
| Full p99 regret | 1.645 | 1.640 | improved |

**Grader confirms harness projection within 6%** (+$9 actual vs +$8.50 projected). Non-pair categories byte-identical (surgical via the pair gate). Within pair: 51.6% → 51.8% pct_opt; $1,829 → $1,811.

**Rule 19 design (codified in `analysis/scripts/strategy_v53_qpair_joint_pbot.py`):**

> If hand has exactly one pair AND pair_rank = Q (12) AND the JOINT pair-to-bot DS setting is achievable (max non-pair singleton on top + 2 same-suit singletons in mid + 2 kickers matching pair-suits in bot completing DS), play that JOINT setting. Otherwise fall through to v52.

**Tie-breaks (when multiple JOINT configs exist):** choose the construction with the highest mid_high (preserves mid Hold'em strength).

---

## What this means for S68+ direction

**Pair PBOT-routing is mostly ML-only at catalog granularity** — confirmed by 11 of 12 candidates failing T1. Only one structurally favorable cell (Q-pair × PBOT_DS_JOINT, where oracle PBOT preference is at its 53% peak) admits a clean rule.

The matrix's "$391 WG PBOT-cell headroom" claim was decomposed by this session:
- Q-pair × JOINT: ~$8.50 catalog-shippable (= Rule 19 capture)
- Q-pair × PARTIAL: $41 v52→v44 gap, but UNREALIZABLE by blanket rule (regresses -$26 if forced)
- 6/7/8/9 × {JOINT, PARTIAL}: $107 v52→v44 gap, but UNREALIZABLE by blanket rule (regresses up to -$315 if forced)
- K-pair, A-pair × PBOT cells (C_PAIR_1, C_PAIR_2): UNTESTED but **likely same structural problem** since oracle PBOT preference at K-pair is 37%, A-pair 18% (lower than Q-pair).

### Recommended S68 direction

**Path B (hybrid chain) becomes the primary candidate for the pair $341 WG gap.** Per PAIR_DECISION_MATRIX.md Recommendation Path B: cell-routed hybrid (v44 on PBOT pair cells, v52 on PMID pair cells) captures $390 WG vs v52-alone, $49 WG vs v44-alone. This commits production to v44_dt on PBOT pair cells but is implementationally simple (the cell taxonomy is already pre-computed).

**Path A (rule extension) is mostly exhausted on PBOT cells.** Remaining low-hanging Path-A candidates per the matrix:
- **C_PAIR_4 — drop "single Ace" predicate from v9_2.** v9_2 fires on pair_rank ∈ {2-5, T-J-Q} only when an Ace is present. Removing the Ace predicate broadens v9_2's fire region 3×. ESTIMATED $30-50 WG but UNTESTED. Probably suffers the same structural problem (the Ace-presence is selective: v9_2's $-positive cells likely require the Ace as a "PMID-mid-is-strong-enough-to-trust-DS-bot-with-pair" signal).
- **C_PAIR_anti-SPLIT** — the pair=3/4 SPLIT bug observed in Phase 1 ($138 WG combined). This was NOT v52 vs v44 (v52 already beats v44 on pair=3,4); it's a v44 anti-pattern. Out of scope for the rule chain.

### Acceptance for S67

| Criterion | Status |
|---|---|
| Pair catalog harness produced | ✓ `analysis/scripts/test_rule_catalog_pair.py` |
| Rule 11 reproduction <5% error | ✓ 3.5% error vs corrected $6 target |
| C_PAIR_3a/b/c verdicts assigned | ✓ All T3 net-negative |
| Fallback C_PAIR_5 tested | ✓ Joint-only ships clean, simple/partial T3 |
| Non-targeted regression check on T2 candidate | ✓ Zero spillover, exact match to audit |
| Ship v53 | ✓ Code written; prefix grader confirms unchanged; full grader pending |
| S68 direction recommendation | ✓ Path B (hybrid chain) primary; C_PAIR_4 secondary |

---

## Artifacts (Session 67)

**New code:**
- `analysis/scripts/test_rule_catalog_pair.py` — pair catalog harness
- `analysis/scripts/strategy_v53_c_pair_3.py` — C_PAIR_3 sub-variant candidates + shared PBOT_DS enumeration helpers
- `analysis/scripts/strategy_v53_qpair_joint_pbot.py` — **v53 PRODUCTION** (v52 + Rule 19)
- `analysis/scripts/audit_c_pair_3_S67.py` — Phase 2 audit driver
- `analysis/scripts/audit_c_pair_fallback_S67.py` — Phase 3 fallback driver
- `analysis/scripts/regression_check_c_pair_5_S67.py` — full pair-category regression check
- `analysis/scripts/grade_v53_qpair_joint_pbot.py` — head-to-head grader

**Data:**
- `data/session67/c_pair_3_audit.log`, `c_pair_3_audit_summary.json` — Phase 2 sweep
- `data/session67/c_pair_fallback.log`, `c_pair_fallback_summary.json` — Phase 3 sweep
- `data/session67/regression_check.log`, `regression_check_c_pair_5.json` — regression sweep
- `data/session67/sanity_rule11.log` — harness validation
- `data/session67/grader_v53_prefix.log` — prefix grader output
- `data/session67/grader_v53_full.log` — full-grid grader output (filled at session end)

**Doc updates:**
- `SESSION_67_C_PAIR_3_AUDIT.md` (this file)
- `CURRENT_PHASE.md` — rewritten for S68 direction
- `DECISIONS_LOG.md` — Decision 102 appended

---

*"Speed is not necessary — clarity and perfection is."* The C_PAIR_3 family was decisively falsified (11/12 candidates T3) by patient sub-variant sweep; the matrix's catalog-ceiling estimates conflated v44's selective catch with rule-chain headroom. Only one structurally favorable cell yielded a ship, and S68 pivots to hybrid-chain as primary direction. Pair PBOT-routing is mostly ML-only territory.
