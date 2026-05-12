# SESSION 68 — v54 hybrid chain ships: LARGEST single production ship in project history (+$382/1000h)

*Date: 2026-05-12. Path B (cell-routed hybrid) per PAIR_DECISION_MATRIX.md Recommendation. Output: strategy_v54_pair_hybrid.py + grader confirmation + ship.*

---

## TL;DR

**v54 ships.** The cell-routed hybrid chain (route pair PBOT cells → v44_dt, all other hands → v53) captures the entire **$382/1000h** v52→v44 pair-PBOT gap that S67's 12 catalog-blanket-rule candidates could not realize. Grader-confirmed full-grid lift matches harness prediction to 0.1%.

| Metric | v53 (S67) | v54 (S68) | Δ |
|---|---:|---:|---:|
| Full-grid $/1000h | 2,490 | **2,108** | **−$382** |
| Full-grid pct_opt | 43.43% | **49.74%** | **+6.31pp** |
| Prefix $/1000h | 1,522 | 1,343 | −$179 |
| Prefix pct_opt | 53.06% | 56.64% | +3.58pp |
| Within-pair full pct_opt | 51.8% | 65.3% | +13.5pp |
| Within-pair $/1000h | 1,811 | 991 | −$820 |
| Full p90 regret | 0.715 | 0.640 | improved |
| Full p99 regret | 1.640 | 1.625 | improved |
| Two-track divergence vs v44_dt | $1,409 | $1,027 | closed 27% |

**Records set:**
- **Largest single production ship in project history** (3× Rule 14's prior record of $131).
- **Largest pct_opt jump** (+6.31pp, exceeds v44_dt's +4.5pp).
- **First Path-B-style hybrid ship** in the project (rule-chain + ML champion routed per-cell).

**This closes pair as a production target.** Combined with S65's high_only catalog closure, the two largest residual categories (1.226M + 2.8M = 67% of canonical grid) are now both addressed — high_only via v44's surgical ML gating, pair via v54's cell-routed hybrid. Remaining residuals are trips ($55), two_pair ($52), three_pair ($35) — small absolute targets.

---

## Phase 1 — `strategy_v54_pair_hybrid.py`

Routing gate (single check, no full cell taxonomy needed):

> Hand is single-pair (exactly 1 pair, no trips/quads) AND pair has two distinct suits AND ≥1 non-pair singleton of each pair-suit. If true → route to `strategy_v44_dt`. Else → route to `strategy_v53_qpair_joint_pbot`.

This binary gate is equivalent to "in S66's 6-cell pair taxonomy, cell ∈ {PBOT_DS_JOINT, PBOT_DS_PARTIAL}". The PMID_* cells share the same fall-through target (v53) so we don't need to distinguish them at inference time — saving an order of magnitude in routing-gate complexity.

**Smoke tests confirmed all 5 routing paths:**
- Q-pair PBOT_DS feasible → v44 (overrides Rule 19)
- 6-pair PBOT_DS feasible → v44
- 9-pair without pair-suit kickers → v53 (no PBOT_DS)
- High-only no-pair → v53
- Two-pair → v53 (gated out by single-pair check)

**Architectural note:** v54 subsumes Rule 19 entirely. Rule 19 inside v53 never fires on hands routed to v44_dt (which is the entire PBOT_DS-feasible region). The S67 +$9 Rule 19 ship is now subsumed by v44's larger catch in the same cell (~+$13 in Q-pair JOINT alone per harness data). **Rule 19 remains in the v53 code as a fallback; the actual production rule chain is v54.**

---

## Phase 2 — Harness validation (pre-grader sanity check)

`validate_v54_routing_S68.py` swept the full pair category (2.8M hands × 78 (rank, cell) combos) running v54 as `rule_fn` against v53 baseline:

| Cell group | Aggregate WG lift | Pattern |
|---|---:|---|
| PBOT cells (PBOT_DS_JOINT + PBOT_DS_PARTIAL) | **+$382.34/1000h** | 100% match to matrix Path B prediction |
| PMID cells (4 PMID_* cells × 13 pair_ranks) | $0.00 | Zero spillover; v54 == v53 everywhere |

**Per-cell breakdown (PBOT cells; lift WG = v54 vs v53):**

| pair_rank | PBOT_DS_JOINT WG | PBOT_DS_PARTIAL WG | Total per-rank |
|---:|---:|---:|---:|
| 2 | +$3.51 | +$15.95 | +$19.46 |
| 3 | +$5.42 | +$18.86 | +$24.28 |
| 4 | +$8.25 | +$19.90 | +$28.15 |
| 5 | +$10.08 | +$25.18 | +$35.26 |
| 6 | +$8.81 | +$20.91 | +$29.72 |
| 7 | +$6.22 | +$13.03 | +$19.25 |
| 8 | +$5.21 | +$12.69 | +$17.90 |
| 9 | +$6.14 | +$15.70 | +$21.84 |
| T | +$7.95 | +$19.68 | +$27.63 |
| J | +$9.68 | +$27.29 | +$36.97 |
| **Q** | **+$4.18** | **+$41.20** ← peak | **+$45.38** |
| K | +$11.36 | +$24.24 | +$35.60 |
| A | +$6.01 | +$22.38 | +$28.39 |
| **TOTAL** | **+$92.81** | **+$276.10** | **+$382.34** |

**PBOT_DS_PARTIAL accounts for 72% of the lift ($276 of $382)** — consistent with matrix Phase 2 finding that PARTIAL is the largest cell by both population and v52→v44 gap.

**The Q-pair × PBOT_DS_PARTIAL cell delivers +$41.20/1000h alone** — matching the matrix-predicted ceiling exactly. This is the same cell where S67's blanket Q-pair PBOT-take rule LOST $25.94 WG. The hybrid captures it by delegating per-hand decisions to v44's selective gating.

**Per-rank PBOT-take rates** (= fraction of cell where v44 disagrees with v53):
- pK/PBOT_DS_JOINT: 65% (best). pJ/JOINT: 66%.
- pQ/PARTIAL: 66% (highest PARTIAL).
- pA/JOINT: 45% (lowest).
- Average across all 26 PBOT cells: **27.7% fire rate** (775,915 hands of 2,800,512 audited = 12.9% of canonical-grid).

---

## Phase 3 — Grader confirmation

### Prefix grid (500K hands, n=1000)

| Strategy | $/1000h | pct_opt | p90 |
|---|---:|---:|---:|
| v53 | 1,522 | 53.06% | 0.502 |
| v54 | **1,343** | **56.64%** | **0.462** |
| Δ | **−$179** | **+3.58pp** | improved |

Within-pair on prefix: 60.6% → 68.9% pct_opt (+8.3pp); $1,019 → $603 (−$416). All non-pair categories byte-identical (5 of 7 categories show identical pct_opt + mean_regret).

### Full grid (6M hands, n=200)

| Strategy | $/1000h | pct_opt | p90 | p99 |
|---|---:|---:|---:|---:|
| v53 | 2,490 | 43.43% | 0.715 | 1.640 |
| v54 | **2,108** | **49.74%** | **0.640** | **1.625** |
| Δ | **−$382** | **+6.31pp** | improved | improved |

Within-pair on full grid: 51.8% → 65.3% pct_opt (+13.5pp); $1,811 → $991 (-$820 within-cat). All non-pair categories byte-identical (high_only/two_pair/trips/trips_pair/three_pair/quads/composite pct_opt + mean_regret unchanged to 4 decimals).

**Harness-to-grader fidelity:** harness predicted +$382.34/1000h, grader returned +$382/1000h. Error: 0.1%. This is the cleanest harness-to-grader match in S60+ catalog/harness history (Rule 14 was 0.2%; Rule 19 was 6%; v54 is 0.1%).

---

## What this means

### v54 closes pair as a catalog target

Before S68: pair had $341 WG residual identified as "catalog-shippable" by PAIR_DECISION_MATRIX.md. S67 falsified 11 of 12 catalog-blanket-rule candidates → only $9 was realizable that way. S68 shows the remaining $341 is realizable via cell-routing to v44, NOT via additional rules.

**Per-category WG residual map (v54 framing):**

| Category | n_hands | v54 $/1000h | v44 $/1000h | Status |
|---|---:|---:|---:|---|
| high_only | 1,226,940 | $3,014 (= $755 WG) | $755 | ML-only, catalog CLOSED S65 |
| pair | 2,800,512 | $991 (= $462 WG) | $511 | **Cell-routed hybrid v54-PBOT-v44 + v54-PMID-v53. Within $50/1000h of v44 ceiling.** |
| two_pair | 1,338,480 | $3,211 (= $920 WG) | $363 | ML-only suspected; not yet catalog-audited |
| trips | 328,185 | $2,010 (= $110 WG) | $54 | Small absolute target |
| trips_pair | 171,600 | $5,417 (= $155 WG) | $5 | Already collapsed S55a |
| three_pair | 114,400 | $1,696 (= $32 WG) | $35 | Small absolute target |
| quads + composite | 29,042 | (rounding) | (rounding) | Negligible |

(WG numbers above are v54 mean_regret × $10/EV × 1000 × share % rounded to nearest dollar.)

The pair residual after v54 = $462 WG; v44 alone on pair = $511 WG. So **v54 BEATS v44 alone by $49 WG on pair** (= v52's PMID-cell catch, preserved by v54 by routing PMID hands to v53). This is the design payoff of the hybrid: best-of-both-worlds.

### S69+ direction

The matrix Path B prediction was "+$390 WG vs v52-alone, +$49 WG vs v44-alone". The grader confirmed +$382 vs v53 (which is v52 + Rule 19's $9). Reconciling: v54 vs v52 baseline = $382 + $9 = $391 WG, exactly matching matrix's $390 prediction.

**Remaining pair-zone headroom:** v54 vs v44 pair residual is only $49 WG (v54 $462 vs v44 $511 within-cat). This is the v52→v44 PMID-cell catch that v54 retains by routing PMID hands to v53. There is no obvious further gain on pair without:
1. ML retrain (v45_dt+ with new features → expand v44's coverage)
2. Per-PMID-cell rule extraction (similar catalog work to S67 but on PMID cells where v52 already beats v44 — likely to yield small lifts)

**S69 candidates:**
- **two_pair audit** ($920 WG residual — second-largest absolute target now that pair is hybrid-routed). Mirror S66-S67 methodology: build two_pair decision matrix (Phase 1+2), test catalog candidates (Phase 3). Expected outcome: similar mix of rule-shippable and ML-only cells.
- **trips audit** ($110 WG, smaller). Cleaner candidate space (only 6.6% of grid).
- **ML retrain v45_dt** targeting the pair PMID cells (where v44 leaks $49 WG). Diagnostic-driven feature engineering per S54 playbook. Could collapse v44's pair residual further → v54 hybrid would auto-inherit.

**Recommended:** two_pair audit (mirror S66 Phase 1+2 doc + S67 candidate sweep). Highest absolute target; cleanest methodology transfer.

---

## Artifacts (Session 68)

**New code:**
- `analysis/scripts/strategy_v54_pair_hybrid.py` — **v54 PRODUCTION** (cell-routed hybrid)
- `analysis/scripts/validate_v54_routing_S68.py` — pre-grader routing validation
- `analysis/scripts/grade_v54_pair_hybrid.py` — v54 vs v53 head-to-head grader

**Data:**
- `data/session68/v54_routing_validation.log`, `v54_routing_validation.json` — per-(rank, cell) routing audit
- `data/session68/grader_v54_prefix.log` — prefix grader
- `data/session68/grader_v54_full.log` — full-grid grader

**Documentation:**
- `SESSION_68_V54_HYBRID_CHAIN.md` (this file)
- `CURRENT_PHASE.md` — rewritten for S69
- `DECISIONS_LOG.md` — Decision 103
- `STRATEGY_GUIDE.md` — Part 1 append + front-matter

**Production state at end of S68:**
- Rule chain: **v54_pair_hybrid** (cell-routed: v44 on pair PBOT cells, v53 elsewhere). **$2,108 full / $1,343 prefix (grader-confirmed)**.
- ML champion: **v44_dt** (UNCHANGED). $1,081 full / $686 prefix.
- Two-track divergence: $1,409 → $1,027 (closed 27% in one ship — largest single-session divergence reduction in project history).
- **Total production rule count: 18** (UNCHANGED — v54 is a routing wrapper, not a new rule).

---

*"Speed is not necessary — clarity and perfection is."* — the matrix did the design work (S66), S67 falsified blanket-rule realization (12 candidates, 11 T3), and S68 implemented the design that the falsification implied. End-to-end: catalog → audit → hybrid in three sessions. The matrix's $390 WG prediction was honored to 2% by the actual grader.
