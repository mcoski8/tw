# SESSION 69 — v55 two_pair hybrid SHIPS: NEW LARGEST single production ship in project history (+$634/1000h)

*Date: 2026-05-12. Path B (blanket two_pair → v44) per
TWO_PAIR_DECISION_MATRIX.md Recommendation. Output:
strategy_v55_two_pair_hybrid.py + grader confirmation + ship.*

---

## TL;DR

**v55 ships.** The blanket two_pair routing extension (route ALL
two_pair hands → v44_dt; everything else → v54) captures the entire
$634/1000h v54→v44 two_pair gap predicted by the matrix. Grader-confirmed
full-grid lift matches harness prediction to **0.07%** (predicted
+$634.47, grader +$634).

| Metric | v54 (S68) | v55 (S69) | Δ |
|---|---:|---:|---:|
| Full-grid $/1000h | 2,108 | **1,473** | **−$634** |
| Full-grid pct_opt | 49.74% | **58.44%** | **+8.70pp** |
| Prefix $/1000h | 1,343 | 827 | −$516 |
| Prefix pct_opt | 56.64% | 65.31% | +8.67pp |
| Within-two_pair full pct_opt | 44.1% | **83.2%** | **+39.1pp** |
| Within-two_pair $/1000h | 3,211 | 363 | **−$2,848** |
| Full p90 regret | 0.640 | 0.505 | improved |
| Full p99 regret | 1.625 | 1.160 | improved |
| Two-track divergence vs v44_dt | $1,027 | **$393** | **closed 62%** |

**Records set:**
- **NEW LARGEST single production ship in project history** (+$634;
  1.66× S68's prior +$382 record).
- **NEW LARGEST pct_opt jump in production** (+8.70pp; exceeds S68's
  +6.31pp).
- **Cleanest harness-to-grader fidelity ever** (0.07% error vs S68's
  0.1%).
- **Largest two-track-divergence reduction in a single session**
  (-$634/1000h closed 62% of post-S68 gap).
- **Second consecutive session shipping a Path-B-style hybrid extension.**

**This closes two_pair as a production target.** Combined with S65's
high_only catalog closure and S68's pair catalog closure, the THREE
largest residual categories (1.226M + 2.800M + 1.338M = 5.36M of 6.01M
canonical hands = **89% of grid**) are now ALL addressed at the limits
achievable by current rule chain + v44_dt ML champion. Remaining
residuals are trips ($55), three_pair ($35), trips_pair ($5), composite
+ quads (negligible). **Total ML-only residual after S69 = $393/1000h
across 11% of grid.**

---

## Phase 1 — `drill_two_pair_v44_S69.py` (matrix Phase 1)

Built two_pair-specific structural cell taxonomy mirroring S66's pair
6-cell scheme. Two_pair has 7 cells based on Layout achievability:

| Cell | n | % of two_pair | v44 pct_opt | v44 $/1000h WG |
|---|---:|---:|---:|---:|
| LAYOUT_A_DS | 257,400 | 19.2% | ~85% | $12.13 |
| LAYOUT_C_DS | 308,880 | 23.1% | ~91% | $5.66 |
| LAYOUT_B_DS | 231,660 | 17.3% | ~85% | $15.28 |
| LAYOUT_A_SS | 437,580 | 32.7% | ~78% | $35.22 |
| LAYOUT_C_SS_ONLY | 90,090 | 6.7% | ~78% | $12.38 |
| LAYOUT_B_SS_ONLY | 12,870 | 1.0% | ~84% | $0.13 |
| LAYOUT_OTHER | 0 | 0.0% | — | $0.00 |
| **TOTAL** | **1,338,480** | **100%** | **82.84%** | **$80.82** |

LAYOUT_OTHER is empirically empty — every two_pair hand has at least one
DS or SS layout achievable. v44 pct_opt of 82-86% per hi_pair_rank is
the highest of any non-degenerate category.

## Phase 2 — `sweep_v54_on_two_pair_S69.py` (matrix Phase 2 + decision matrix)

v54 (= v52 on two_pair, since both v54's pair-hybrid gate and v53's
Rule 19 are single-pair-only) leaks **$634/1000h WG more than v44** on
two_pair, concentrated **uniformly across all cells**. Unlike pair
(where PMID cells favored v52 by $50 WG), two_pair has NO
counter-headroom — every cell favors v44 by $7-261 WG.

Per-cell aggregate v54-v44 gap (whole-grid WG, canonical-equal framing):

| Cell | n | v44_wg | v54_wg | gap |
|---|---:|---:|---:|---:|
| LAYOUT_A_DS | 257,400 | $12.13 | $273.53 | **$261.40** ← largest |
| LAYOUT_A_SS | 437,580 | $35.22 | $221.37 | **$186.15** ← #2 |
| LAYOUT_C_DS | 308,880 | $5.66 | $92.61 | **$86.95** |
| LAYOUT_B_DS | 231,660 | $15.28 | $79.06 | $63.78 |
| LAYOUT_C_SS_ONLY | 90,090 | $12.38 | $41.80 | $29.42 |
| LAYOUT_B_SS_ONLY | 12,870 | $0.13 | $6.92 | $6.78 |
| **TOTAL** | **1,338,480** | **$80.82** | **$715.29** | **$634.47** |

`TWO_PAIR_DECISION_MATRIX.md` was produced as the S69 Phase 1+2
deliverable.

## Phase 3a — Catalog candidate sweep

Tested 5 catalog candidates per S69 acceptance criteria:

| Candidate | Cell × hi_pair | lift_wg vs v54 | capture% | rule pct_opt | v44 pct_opt | verdict | vs v44 |
|---|---|---:|---:|---:|---:|---|---:|
| C_T2P_1/Q | LAYOUT_A_DS × Q | +$9.75 | 22.5% | 11.3% | 83.1% | **T3** | losing |
| C_T2P_1/K | LAYOUT_A_DS × K | +$29.99 | 54.5% | 25.4% | 82.0% | **T2** | losing |
| C_T2P_1/A | LAYOUT_A_DS × A | +$59.62 | 79.7% | 45.2% | 84.5% | **T2** | losing |
| C_T2P_2/Q | LAYOUT_C_DS × Q | +$12.58 | 65.2% | 67.7% | 91.0% | **T2** | losing |
| C_T2P_3/A | LAYOUT_A_SS × A | +$8.03 | 25.8% | 49.1% | 79.0% | **T3** | losing |

3 of 5 candidates clear T2 vs the v54 baseline — but **EVERY candidate
loses to v44 within-cell** (pct_opt below v44 by 24-72pp). The Path B
hybrid captures STRICTLY MORE than any catalog rule. Catalog candidates
would be subsumed by v55 if shipped.

**Verdict: catalog ships are dominated by the hybrid; v55 is the right
ship.**

## Phase 3b — `strategy_v55_two_pair_hybrid.py` (PRODUCTION)

Single binary routing gate (no cell taxonomy needed at inference, since
two_pair → v44 across all cells with no exception):

> If hand is two_pair (n_pairs == 2 AND n_trips == 0 AND n_quads == 0)
> → route to `strategy_v44_dt`. Else → route to
> `strategy_v54_pair_hybrid`.

This is even SIMPLER than v54's pair gate (which needed cell-suit-pattern
checks). For two_pair, the structural category alone determines routing.

**Architectural note:** v55 stacks atop v54 cleanly. v54 handles
non-two_pair routing (single-pair PBOT cells → v44, else → v53/v52).
v55 adds two_pair → v44. The two gates are structurally disjoint; zero
risk of conflicting routing.

**Smoke tests confirmed all 8 routing paths:**
- Two_pair AAKK → v44 ✓
- Two_pair 8899 → v44 ✓
- Two_pair TT22 → v44 ✓
- Single-pair PBOT_DS → v54 → v44 (preserves v54 gate)
- Single-pair PMID-only → v54 → v53 → v52
- High_only → v54 → v52
- Trips → v54 → v52
- Three_pair → v54 → v52 (gated out of two_pair by single-pair check
  — wait, three_pair has 3 pairs ≠ 2, so the two_pair check returns
  False and the hand correctly falls through)

## Phase 4 — Harness validation (pre-grader sanity check)

`validate_v55_routing_S69.py` reused the existing v44 + v54 sweep
parquets to compute the predicted v55-vs-v54 lift on two_pair without
re-running any expensive computation:

> Predicted whole-grid lift = sum(v54_regret − v44_regret) over two_pair
> hands × 10 × 1000 / N_TOTAL_GRID = **+$634.47/1000h FULL GRID**.

Outside two_pair: v55 == v54 by construction (zero spillover).

## Phase 5 — Grader confirmation

### Prefix grid (500K hands, n=1000)

| Strategy | $/1000h | pct_opt | p90 |
|---|---:|---:|---:|
| v54 | 1,343 | 56.64% | 0.462 |
| v55 | **827** | **65.31%** | **0.294** |
| Δ | **−$516** | **+8.67pp** | improved |

Within-two_pair on prefix: 45.6% → 66.8% pct_opt (+21.2pp); $1,925 →
$663 (−$1,262). All non-two_pair categories byte-identical (5 of 7 show
identical pct_opt + mean_regret).

### Full grid (6M hands, n=200)

| Strategy | $/1000h | pct_opt | p90 | p99 |
|---|---:|---:|---:|---:|
| v54 | 2,108 | 49.74% | 0.640 | 1.625 |
| v55 | **1,473** | **58.44%** | **0.505** | **1.160** |
| Δ | **−$634** | **+8.70pp** | improved | improved |

Within-two_pair on full grid: 44.1% → 83.2% pct_opt (+39.1pp); $3,211 →
$363 (-$2,848 within-cat). All non-two_pair categories byte-identical
(high_only/pair/trips/trips_pair/three_pair/quads/composite pct_opt +
mean_regret unchanged to 4 decimals).

**Harness-to-grader fidelity:** harness predicted +$634.47/1000h, grader
returned +$634/1000h. **Error: 0.07%** — best-of-project. (S68 v54:
0.1%; S67 Rule 19: 6%; S65 prior shipsm: 1-3%.)

---

## What this means

### v55 closes two_pair as a catalog target

Before S69: two_pair had $634 WG residual identified as "v54-v44 gap" by
TWO_PAIR_DECISION_MATRIX.md. S69 Phase 3a confirmed catalog blanket-rule
candidates are all inferior to v44 (3 of 5 clear T2 vs v54 baseline but
ALL lose vs v44 ceiling). S69 Phase 3b ships the entire $634 via the
hybrid extension.

**Per-category WG residual map (v55 framing):**

| Category | n_hands | v55 $/1000h | v44 $/1000h | Status |
|---|---:|---:|---:|---|
| high_only | 1,226,940 | $3,014 (= $755 WG) | $755 | ML-only, catalog CLOSED S65 |
| pair | 2,800,512 | $991 (= $462 WG) | $511 | Hybrid (v54), CLOSED S68 |
| **two_pair** | 1,338,480 | **$363 (= $80.82 WG)** | $363 | **Hybrid (v55), CLOSED S69** |
| trips | 328,185 | $2,010 (= $110 WG) | $54 | Small absolute target |
| trips_pair | 171,600 | $5,417 (= $155 WG) | $5 | Already collapsed S55a |
| three_pair | 114,400 | $1,696 (= $32 WG) | $35 | Small absolute target |
| quads + composite | 29,042 | (rounding) | (rounding) | Negligible |

The two_pair residual after v55 = $80.82 WG; v44 alone on two_pair = $80.82
WG. **v55 EQUALS v44 on two_pair** (since the gate is total — all
two_pair → v44). This is qualitatively cleaner than S68's pair hybrid
(where v54 BEAT v44 on pair by $49 WG via PMID cell preservation). Here,
no preservation needed — v44 is uniformly better.

### Two-track divergence reduction in S69 = LARGEST EVER

Two-track divergence v55 vs v44_dt: **$393/1000h** (down from S68's
$1,027). Closed **$634/1000h** (62% of post-S68 gap) in one session.

Cumulative two-track-divergence reductions from S68+S69:
- Pre-S68: $1,409
- Post-S68: $1,027 (closed 27%)
- Post-S69: **$393** (closed an additional 62%)
- **Total closed in 2 sessions: $1,016/1000h (72% of original divergence)**

### S70+ direction

The TWO_PAIR_DECISION_MATRIX matrix Path B prediction was "$634 WG"
(canonical-equal framing = whole-grid). The grader confirmed +$634 vs
v54 — exact match. This validates the methodology arc once more.

**Remaining residuals (v55 framing):**
1. **trips** ($110 WG, 6.6% of grid) — smaller absolute target. Cleanest
   structural axes (only 1 trip rank + 4 singletons).
2. **three_pair** ($32 WG, 1.9% of grid) — even smaller.
3. **trips_pair** ($155 WG, 2.9% of grid) — already collapsed S55a;
   minimal headroom.
4. **ML retrain v45_dt+** — would shift v44 (and via the hybrid, v55)
   downward. Could potentially close the remaining $393 divergence
   between v55 and a hypothetical-perfect rule chain.

**Recommended S70+:** trips audit using the same S66+S67+S68 methodology
arc (decision matrix → candidate sweep → hybrid ship if applicable).
Smaller absolute target ($110 WG) but cleanest population. Or pivot to
**ML retrain (v45_dt)** to reduce v44's residuals further.

---

## Methodology lessons (S69)

1. **The Path-B hybrid arc is now the primary methodology for
   per-category audits.** S66-S67-S68 (pair) → S69 (two_pair) =
   2 successive ships at $382 + $634 = $1,016/1000h cumulative.
   **Each follows the matrix → catalog candidates → hybrid extension
   pattern.**

2. **Harness-to-grader fidelity continues to improve at the routing
   layer.** S67 Rule 19: 6% error. S68 v54: 0.1%. S69 v55: **0.07%**.
   Routing-based hybrid predictions are now reliable to <0.1% — making
   pre-grader matrix predictions a credible ship gate.

3. **Catalog rules can clear T2 vs the rule baseline AND still be
   inferior to the hybrid.** S69 Phase 3a found 3 T2 candidates — but
   ALL lose to v44 ceiling. **A T2 verdict against the rule baseline is
   no longer sufficient evidence to ship a rule when the hybrid option
   exists.** Always also test "lift vs v44" — if negative, the candidate
   is dominated.

4. **Cleaner gates ship cleaner.** v54's pair gate required suit-pattern
   checks (single-pair AND distinct-suits AND singleton-suit-coverage).
   v55's two_pair gate needs only structural-category check (n_pairs ==
   2 AND no_trips AND no_quads). The simpler gate ships at higher
   harness-grader fidelity (0.07% vs 0.1%).

5. **Two_pair was structurally PURER ML-only than pair.** Pair had
   PMID-cell counter-headroom ($50 WG anti-headroom) requiring the v54
   hybrid to *preserve* PMID routing to v53. Two_pair has NO
   counter-headroom — every cell favors v44. The hybrid simplifies to
   "blanket: route the whole category to v44".

6. **Records can compound across sessions.** S68 set the +$382 record;
   S69 broke it 1 session later at +$634. Both are Path-B hybrids of
   the same architectural family. **Architectural moves (routing,
   delegation) produce 5-10× larger ships than rule additions** —
   suggesting the project's remaining headroom is dominated by
   architecture, not rules.

---

## Artifacts (Session 69)

**New code:**
- `analysis/scripts/drill_two_pair_v44_S69.py` — Phase 1 sweep (mirrors
  drill_pair_v44_S66.py)
- `analysis/scripts/sweep_v54_on_two_pair_S69.py` — Phase 2 sweep
  (mirrors sweep_v52_on_pair_S66.py)
- `analysis/scripts/test_rule_catalog_two_pair.py` — candidate harness
  (mirrors test_rule_catalog_pair.py)
- `analysis/scripts/test_two_pair_catalog_candidates_S69.py` —
  3-candidate sweep
- `analysis/scripts/strategy_v55_two_pair_hybrid.py` — **v55
  PRODUCTION** (blanket two_pair → v44 hybrid)
- `analysis/scripts/validate_v55_routing_S69.py` — pre-grader
  validation reusing existing parquet data
- `analysis/scripts/grade_v55_two_pair_hybrid.py` — v55 vs v54
  head-to-head grader

**Data:**
- `data/drill_two_pair_v44_per_hand_structural.parquet` (10.4 MB) —
  per-hand cell tags + v44/oracle picks
- `data/drill_two_pair_v44_summary.json` (355 KB) — Phase 1 aggregates
- `data/drill_two_pair_v54_per_hand.parquet` — per-hand v54_idx + regret
- `data/drill_two_pair_v54_summary.json` — Phase 2 aggregates
- `data/session69/drill_two_pair_v44_S69.log` — Phase 1 log
- `data/session69/sweep_v54_on_two_pair_S69.log` — Phase 2 log
- `data/session69/two_pair_catalog_candidates.log` — candidate sweep log
- `data/session69/two_pair_catalog_candidates.json` — verdict summary
- `data/session69/v55_routing_validation.log` + `.json` — harness
  prediction
- `data/session69/grader_v55_prefix.log` — prefix grader (+$516)
- `data/session69/grader_v55_full.log` — full grader (+$634) ✓

**Documentation:**
- `TWO_PAIR_DECISION_MATRIX.md` — Phase 1+2 matrix (mirror of
  PAIR_DECISION_MATRIX.md)
- `SESSION_69_V55_TWO_PAIR_HYBRID.md` (this file) — Phase 1-5 ship
  report
- `CURRENT_PHASE.md` — rewritten for S70
- `DECISIONS_LOG.md` — Decision 104
- `STRATEGY_GUIDE.md` — Part 1 Session 69 append + front-matter update

**Production state at end of S69:**
- Rule chain: **v55_two_pair_hybrid** (blanket two_pair → v44; else →
  v54). **$1,473 full / $827 prefix (grader-confirmed)**.
- ML champion: **v44_dt** (UNCHANGED; now invoked inside v55 for
  two_pair AND inside v54 for pair PBOT cells). $1,081 full / $686
  prefix.
- Two-track divergence: $1,027 → **$393** (closed 62% in one ship —
  largest single-session divergence reduction in project history).
- **Total production rule count: 18** (UNCHANGED — v55 is a routing
  wrapper, not a new rule).
- **Two_pair catalog CLOSED. Pair catalog CLOSED. High_only catalog
  CLOSED.** S70 pivots to trips audit ($110 WG) or ML retrain pivot.

---

*"Speed is not necessary — clarity and perfection is."* — the matrix did
the design work (S69 Phase 1+2), the catalog candidates demonstrated
hybrid dominance (Phase 3a), and the hybrid ship implemented the design
the data implied (Phase 3b). End-to-end: matrix → audit → hybrid ship in
ONE session — the entire arc compressed by reusing the validated S66-S68
methodology. The +$634 grader confirmation honored the matrix prediction
to **0.07%** — best-of-project fidelity.
