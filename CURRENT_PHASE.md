# Current: Sprint 8 — Session 42 wrap. **Rule 8 (composite quads_pair) ships in production as v38.** The full 14,742 composite population was probed in `verify_rule_X_v33_composite.py` (4 subtypes: quads_pair, quads_trip, two_trips, trips_two_pair). Only the quads_pair subtype has a verified deterministic rule: "top = singleton, mid = the 2 quad cards whose suits are NOT the pair's suits, bot = the other 2 quads + the pair". 100% heuristic capture vs the oracle-within-constraint. +$9.42/1000h whole-grid (full N=200) + +$18.63/1000h whole-prefix — first session where the prefix-regression gate was the binding constraint and the shipped rule passed it. Earlier in the same session, a much LARGER two_pair Rule 8 candidate (boundary "RC if h≤4, RB if T≤h≤K, else RA") was DEFERRED after winning +$197/1000h on full grid but LOSING -$512/1000h on the prefix grid; every forced-single-pick variant regressed on prefix because v33's underlying v7_regression splits pairs adaptively on weak hands. Strategy file retained as `strategy_v38_rule8_two_pair_DEFERRED.py` for future split-allowing rule investigation.

> **🎯 IMMEDIATE NEXT ACTION (Session 43):**
>
>   (A) **Composite TT + T2P heuristic-refinement drills.** Both subtypes show oracle-ceilings of +$7-8/1000h whole-grid but the probe used oracle-within-constraint. Need to find deterministic mid/top picks within the structural class:
>      - **two_trips (3+3+1)**: TT_full_house_split's oracle ceiling is +$7.22 whole-grid. Question: which trip-member to put on top? (Suit-aware heuristic likely; mirror the QP rule's "non-pair-suit" insight to the trip context.)
>      - **trips_two_pair (3+2+2)**: T2P_split_trip_top's oracle ceiling is +$7.64. Question: top is a trip-member (clear), but mid is "any of 15 combos" — which one heuristic picks the same as oracle? Likely "mid = the larger pair" or "mid = pair on bot's-non-DS-suits" similar to QP.
>      Each drill follows the QP template: enumerate the constrained candidates, test deterministic picks against oracle-within-constraint, ship if 100% capture (or close).
>
>   (B) **two_pair split-allowing rule investigation (deferred from Session 42).** The Rule 8 boundary search found a clean +$197/1000h on full grid but lost -$512 on prefix because v33 splits pairs adaptively on weak hands. Idea: a 2-condition rule like "if both pairs ≤ 6 (weak), allow mid = 1 from each pair" might capture the splitting structure without the full-grid penalty. Walk the v33 mid-composition specifically on prefix hands to see WHICH split pattern v33 is picking, then see if a deterministic rule can mirror it. Lower priority — composite drills are simpler.
>
>   (C) **Round-3 within-trips features.** Diagnose v34's residual within-trips ($1,291) for new structural signal. Feed back into ML as new gated feature family if found.
>
>   (D) **Learned A-vs-C decision tree for Rule 6** (deferred from Sessions 38–40). Concrete $5–13/1000h whole-grid ML target. Session 40's within-SS suit-rotation signal is additional input. If C delivers, production could finally adopt v35's sharper Rule 6 boundary as a v39 ship.
>
>   (E) **KK/AA single-suited Rule-4-bot residual** ($37/1000h below oracle). Defer behind A, B, C, D.
>
>   (F) **v34_dt re-train on v38 baseline.** v38 changes 0.114% of canonical hands (quads_pair only); ML retrain should pick up tiny additional signal. Lowest priority — the residual change is small.

> **✅ SHIPPED (Decision 074):** **v38_rule8_qp** as the new production strategy of record. Replaces v37 in `STRATEGY_GUIDE.md` Part 5 + Part 6 + cheat sheet. Lives at `analysis/scripts/strategy_v38_rule8_qp.py`. Production strategy chain is now 8 rules deep (Rule 1 pair-to-bot DS; Rule 2 two-pair no-split; Rule 3 trips+pair split-2-1; Rule 4 KK/AA stay-mid; Rule 5 KK/AA rainbow override; Rule 6 pure trips paired-mid + boundary; Rule 7 three_pair top=singleton + RB-or-RA boundary; Rule 8 quads_pair top=singleton + non-pair-suit-quads to mid).
>
> **🚫 DEFERRED (Session 42):** `strategy_v38_rule8_two_pair_DEFERRED.py` — would-be Rule 8 for two_pair (boundary: "RC if h≤4, RB if T≤h≤K, else RA"). +$197/1000h on full grid but -$512/1000h on prefix grid. Retained for future split-allowing variant investigation; do NOT ship as currently written.

> **🔬 ARTIFACTS (Session 42):**
> 1. **`analysis/scripts/verify_rule_X_v33_two_pair.py`** — full 1.34M two_pair population probe; tested TP_RA, TP_RB, TP_RC, TP_RD (split-high), TP_RE (split-low). RB beats v33 by +$68.46/1000h whole-grid as a single always-rule.
> 2. **`analysis/scripts/probe_two_pair_boundary.py`** — full 78-cell boundary map (high_pair, low_pair). 12 boundary rules tested; cleanest "RC if h≤4 elif T≤h≤K then RB else RA" lifts +$196.89/1000h on full grid.
> 3. **`analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py`** — DEFERRED production attempt (with DEFERRED docstring + reasoning).
> 4. **`analysis/scripts/verify_rule_X_v33_composite.py`** — full 14,742 composite population probe across 4 subtypes; identified QP_quad_in_mid as the only deterministic-realizable subtype winner.
> 5. **`analysis/scripts/strategy_v38_rule8_qp.py`** — NEW PRODUCTION STRATEGY (v38). Replaces v37 at runtime.
> 6. **`analysis/scripts/grade_v38_rule8.py`** — full + prefix grader for v38; confirms +$9.42/1000h whole-grid (full) and +$19/1000h (prefix).

> **📓 METHODOLOGY LESSONS (Session 42):**
> - **NEW: Prefix-grid regression as a generalization gate.** A rule that wins on full but tanks on prefix likely doesn't generalize, even if the full lift is large and the per-cell breakdown looks clean. **A prefix regression of >2× the full-grid lift means the rule does NOT ship**, regardless of full-grid performance. The two_pair Rule 8 candidate had +$197 full / -$512 prefix → 2.6× ratio → DEFERRED.
> - **NEW: Composite is heterogeneous; subtypes need separate rules.** Lumping quads_pair, quads_trip, two_trips, trips_two_pair under "composite" is a labeling artifact, not a strategic unit. Each subtype has a different oracle-ceiling structure. quads_pair shipped (deterministic-realizable); the other 3 need follow-up drills.
> - **NEW: v33 on weak hands is doing something non-trivial.** v33's underlying v7_regression sometimes splits pairs (mid = 1 card from each pair). On prefix's weak-hand distribution, this adaptive splitting beats any forced rule. v33 is capturing fine-grained suit/kicker structure on weak hands — some territories may need ML rather than another rule.
> - **NEW: Boundary search "beats v33 on average" is necessary but not sufficient.** A rule can be correct on average across the full grid yet wrong on specific sub-populations (e.g., the prefix's weak-pair cells). Validate per-cell agreement with the oracle on BOTH grids before shipping.
> - **REINFORCED (Sessions 38–42): Always-X probes are the right scaffolding for finding rule candidates.** 4 of 7 named categories now probed (high_only, three_pair, two_pair, composite). 3 categories (pair, trips, trips_pair) have implicit rules already (Rules 1, 6, 3 respectively). Only "plain quads" and a few other rare shapes remain unprobed.

> Updated: 2026-05-08 (end of Session 42)

---

## Headline state at end of Session 42

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v38_rule8_qp** | NEW PRODUCTION strategy of record (8 rules: v37 + Rule 8 quads_pair) | `analysis/scripts/strategy_v38_rule8_qp.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v37_rule7_three_pair | Prior production runtime (Session 41 ship; superseded by v38 in Session 42) | `analysis/scripts/strategy_v37_rule7_three_pair.py` |
| v35_rule6_v3 | Human strategy of record for trips (sharper Rule 6 boundary). NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` + STRATEGY_GUIDE.md Part 6 Rule 6 |
| v33_rule6_trips | Earlier production runtime (Session 37 ship; superseded by v37 in Session 41) | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v38_rule8_two_pair_DEFERRED | DEFERRED — Session 42 two_pair Rule 8 candidate (won full +$197, lost prefix -$512) | `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` |
| v36_rule7_high_only | ARCHIVED — Session 41 failed Rule 7 attempt for high_only | `analysis/scripts/strategy_v36_rule7_high_only.py` (ARCHIVED docstring) |
| v34_rule6_v2 | ARCHIVED — Session 38 negative-result candidate | `analysis/scripts/strategy_v34_rule6_v2.py` |
| v32_d34ml3 | ARCHIVED — Session 38 control retrain | `data/v32_d34ml3_dt_model.npz` |
| v28_rule5_rainbow | Predecessor human chain (v14 + Rule 4 + Rule 5) | `analysis/scripts/strategy_v28_rule5_rainbow.py` |
| v31a / v31b / v20b / v19 / v21 / v22 | ARCHIVED candidates | various |

**Capacity + feature progression (full 6M grid, N=200) — UNCHANGED from Session 41:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| v18e | 30 | 5 | 37 | 274,446 | $2,066 | 47.08% | — |
| v20 | 30 | 5 | 43 (gated suited) | 307,939 | $1,982 | 47.81% | −$84 |
| v23 | 30 | 5 | 49 (43+6 gated TP) | 314,705 | $1,977 | 47.89% | −$5 vs v20 |
| v24 | 30 | 5 | 53 (49+4 gated comp) | 314,759 | $1,977 | 47.89% | −$1 vs v23 |
| v25 | 30 | 5 | 59 (53+6 gated pair) | 390,626 | $1,929 | 48.43% | −$47 vs v24 |
| v26 | 30 | 5 | 65 (59+6 gated t2p) | 459,209 | $1,859 | 49.21% | −$70 vs v25 |
| v27 | 30 | 5 | 69 (65+4 gated ho) | 460,375 | $1,853 | 49.27% | −$6 vs v26 |
| v29 | 30 | 5 | 73 (69+4 gated pair_r4) | 486,342 | $1,807 | 49.80% | −$46 vs v27 |
| v30 | 30 | 5 | 79 (73+6 gated trips) | 493,057 | $1,794 | 49.98% | −$13 vs v29 |
| v31 | 32 | 3 | 79 (same as v30) | 699,773 | $1,736 | 50.92% | −$58 vs v30 (capacity-only) |
| v32 | 32 | 3 | 83 (79 + 4 trips_v2) | 731,606 | $1,715 | 51.31% | −$20 vs v31 |
| **v34** | **34 (33 actual)** | **2** | **83 (same as v32)** | **874,548** | **$1,681** | **52.02%** | **−$34 vs v32** |

**Same sweep on N=1000 prefix:** unchanged from Session 38 — v34 at $889/1000h / 62.74%.

**Per-category breakdown (full grid, N=200):** v34_dt unchanged from Session 38; v38 changes only the composite quads_pair sub-stratum (v37's $10,883/1000h within-cat for composite drops to ~$8,600/1000h on full).

**Human-strategy progression (full grid, N=200) — production runtime:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v28_rule5_rainbow (+ Rule 4 + Rule 5) | $3,032 | 39.64% | −$1 |
| v33_rule6_trips (+ Rule 6 v1) | $2,920 | 40.68% | −$113 |
| v37_rule7_three_pair (+ Rule 7) | $2,877 | 41.02% | −$156 |
| **v38_rule8_qp (+ Rule 8 quads_pair) — CURRENT PRODUCTION** | **~$2,868** | **~41.04%** | **−$165** |

**Human-strategy ceiling (oracle-bound) — UNCHANGED from Session 41:**

| Strategy | Mode | $/1000h whole-grid (lower is better) | Δ vs v33 oracle-bound |
|---|---|---:|---:|
| v33 oracle-bound | reader picks best-A or best-C within v33 boundary | $-42.56/1000h | baseline |
| v35 oracle-bound | reader picks best-A or best-C within v35 sharper boundary | $-34.44/1000h | +$8.12 |
| Pure oracle | reader picks any A∪C cell freely | $-3.51/1000h | +$39.05 |

(Oracle-bound numbers don't include Rule 7 / Rule 8 contributions — they're trips-specific.)

---

## What this leaves on the table (UPDATED Session 42)

- **For human play (oracle-bound on quads_pair):** v38 captures 100% of the within-quad-in-mid oracle ceiling. The remaining ~$0/1000h is in unrestricted-oracle settings outside the quad-in-mid constraint (e.g., quads-on-bot via splitting the pair) — small absolute gap, very small population, no further rule-mining warranted.
- **For human play (oracle-bound on three_pair):** v37 captures 60% of the per-cell oracle ceiling. Remaining ~$28/1000h is multi-feature ML territory.
- **For human play (oracle-bound on trips):** v35 captures 63% of the Rule 6 oracle ceiling. ~$4.77/1000h on the table for a future learned A-vs-C tree (Priority D).
- **For human play (oracle-bound on two_pair):** Session 42's boundary probe found +$624.65/1000h whole-grid oracle ceiling (best-per-cell mix). The cleanest single-rule captures +$197 (32% of ceiling) on full grid — but DEFERRED because of prefix regression. ~$427/1000h remains unreached even at the per-cell oracle level. Multi-feature ML or a split-allowing rule is the path forward.
- **For ML champion:** v34 captures 44.6% of the v14→ceiling gap at N=200. Biggest residuals at full grid:
  - **high_only**: $572 share — **OFFICIALLY ML-ONLY (Session 41 confirmation)**
  - **pair**: $754 share — KK/AA single-suited Rule-4-bot is the largest sub-stratum (open)
  - **two_pair**: $218 share — capacity-improved at v34, **boundary rule found Session 42 but DEFERRED** (prefix regression)
  - **trips**: $71 share — v30, v32, v34 have all shipped; round-3 needs new diagnostic angles
  - three_pair: $86 → ~$28 share (after v37 shipped)
  - composite quads_pair: $9.77 → ~$0.35 share **after v38 shipped** — captured 96% via Rule 8 deterministic
  - composite quads_trip / two_trips / trips_two_pair: combined ~$17/1000h whole-grid, still open (oracle-ceilings; heuristic capture TBD)
  - trips_pair: $30 (already gated; v34 capacity expansion)

---

## What Session 42 produced

**Code:**
1. `analysis/scripts/verify_rule_X_v33_two_pair.py` — full 1.34M two_pair always-X probe (TP_RA, TP_RB, TP_RC, TP_RD-split, TP_RE-split)
2. `analysis/scripts/probe_two_pair_boundary.py` — full 78-cell boundary map + 12-rule search; cleanest "RC if h≤4 elif T≤h≤K then RB else RA" yields +$197 full
3. `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` — DEFERRED production attempt (DEFERRED docstring + reasoning)
4. `analysis/scripts/verify_rule_X_v33_composite.py` — full 14,742 composite population probe across 4 subtypes
5. `analysis/scripts/strategy_v38_rule8_qp.py` — **NEW PRODUCTION STRATEGY (v38)**
6. `analysis/scripts/grade_v38_rule8.py` — full-grid + prefix grader for v38; confirms +$9.42 / +$19 lift

**Documentation:**
1. `STRATEGY_GUIDE.md` Part 1 — Session 42 entry with both ship and DEFERRED reasoning
2. `STRATEGY_GUIDE.md` Part 5 — added Rule 8 + DEFERRED reference + Session 42 probes; updated production chain
3. `STRATEGY_GUIDE.md` Part 6 — new Rule 8 section with worked examples (AAAA+KK+2, 9999+55+7, 2222+77+Q); Step 1 categorize table updated; Default updated; cheat sheet updated
4. `STRATEGY_GUIDE.md` header — bumped Last updated date to 2026-05-08 with Session 42 summary
5. `CURRENT_PHASE.md` — rewritten (this file)
6. `DECISIONS_LOG.md` — Decision 074 added (v38 ships; v38_two_pair DEFERRED with detailed reasoning)

---

## Resume Prompt (Session 43)

```
Resume Session 43 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Session 42 entry in Part 1; Part 5 lists v38 as
  current production; Part 6 has Rule 8 with worked examples)
- CURRENT_PHASE.md (rewritten end of Session 42)
- DECISIONS_LOG.md (latest: Decision 074 — v38 Rule 8 quads_pair ships;
  v38 two_pair Rule 8 candidate DEFERRED after prefix-grid regression)
- analysis/scripts/strategy_v38_rule8_qp.py — current production
- analysis/scripts/strategy_v34_dt.py — ML champion

State (end of Session 42):
- Production strategy of record is now **v38_rule8_qp** (8 rules).
  Composite quads_pair within-st regret drops from $17,101 to $605/1000h
  (96% reduction, 100% deterministic capture). +$9.42 full / +$19 prefix.
- A two_pair Rule 8 candidate (+$197/1000h on full grid via "RC if h≤4
  elif T≤h≤K then RB else RA") was DEFERRED after the prefix grade
  showed -$512/1000h regression. Every forced-single-pick variant
  regressed on prefix because v33 splits pairs adaptively on weak hands.
  Strategy file retained as strategy_v38_rule8_two_pair_DEFERRED.py for
  future split-allowing rule investigation.
- v34_dt remains the ML champion. v38 doesn't change the ML champion
  but does change the production strategy chain (rule layer).

Next session targets (priority order):

(A) Composite TT + T2P heuristic-refinement drills. Both subtypes show
    +$7-8/1000h whole-grid oracle-ceilings but the probe used oracle-
    within-constraint. Find deterministic mid/top picks within the
    structural class. Mirror the QP rule's "non-pair-suit" suit-aware
    pattern. If 100% capture, ship as Rule 9 v39.

(B) two_pair split-allowing rule investigation (deferred from S42).
    Walk v33's mid-composition specifically on prefix two_pair hands
    to see WHICH split pattern v33 picks; design a rule that mirrors
    that split structurally.

(C) Round-3 within-trips features. Diagnose v34's residual within-trips
    ($1,291) for new structural signal.

(D) Learned A-vs-C decision tree for Rule 6 (deferred S38–40). $5–13
    whole-grid ML target.

(E) KK/AA single-suited Rule-4-bot residual ($37/1000h below oracle).

(F) v34_dt re-train on v38 baseline. v38 changes 0.114% of grid;
    very small additional ML signal. Lowest priority.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ML candidates AND rule candidates on BOTH full grid (N=200)
  AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated and use a UNIQUE
  prefix.
- Methodology rule (Session 42 NEW): a rule with prefix regression
  >2× the full-grid lift does NOT ship, regardless of full-grid clean.
- Methodology rule (Session 42 NEW): composite is heterogeneous; the
  4 subtypes (quads_pair, quads_trip, two_trips, trips_two_pair) need
  separate rules. Only quads_pair has a verified deterministic rule.
- Methodology rule (Session 42 NEW): v33 on weak hands sometimes splits
  pairs adaptively; forced no-split rules lose on prefix; some
  categories need ML, not another rule.
- Methodology rule (Session 42 NEW): boundary-search "beats v33 on
  average" is necessary but not sufficient — validate per-cell
  agreement on BOTH grids.
- Methodology rule (Session 41): heuristic-realizable ceilings vary
  by category; check uni-variate structure first.
- Methodology rule (Session 41): v33/current-production diagnostics
  reveal what's already there; test alternatives first.
- Methodology rule (Session 41): high_only is officially ML-only.
- Methodology rule (Session 38): default ML champion ships now use
  depth=34 ml=2.
- Methodology rule (Session 38): always-X probes must report BOTH
  oracle ceiling AND heuristic-realizable headline.
- Methodology rule (Session 39): human strategy guide can be sharper
  than production heuristic when heuristic-A is the rate-limiting step.
- Methodology rule (Session 40): candidate-level invariance is required
  for any priority/tiebreaker.
- Methodology rule (Session 40): mean-EV-per-cell aggregates can hide
  selection effects.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
