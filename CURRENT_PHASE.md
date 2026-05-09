# Current: Sprint 8 — Session 41 wrap. **Rule 7 (three_pair) ships in production as v37.** Full 114K three_pair population probed exhaustively across all 286 (high_pair, middle_pair, low_pair) combinations. Final rule: "if highest pair ∈ {T, J, Q, K} → mid is the MIDDLE pair, else mid is the HIGHEST pair; top is always the singleton." +$43/1000h whole-grid lift vs v33 confirmed at full-grid scale (+$141/1000h on prefix grid). Three_pair within-cat regret drops 67% ($4,085 → $1,334). Earlier in the same session, an attempted Rule 7 for high_only (v36) was tested and archived: heuristic regressed $6/1000h whole-grid; the +$354/1000h oracle ceiling is unrealizable by any clean rule. high_only is officially ML-only territory.

> **🎯 IMMEDIATE NEXT ACTION (Session 42):**
>
>   (A) **Continue always-X probes for remaining categories** — 2 left from the original Session 38–39 queue:
>      - **composite** ($3.4/1000h whole-grid; high per-category regret per hand). Heterogeneous category — likely needs sub-stratification.
>      - **two_pair** ($218/1000h share; heavily ML-engineered already at v34_dt). Candidate: "always split high pair to mid".
>      Each probe writes `verify_rule_X_v33_<category>.py`; report BOTH oracle ceiling AND heuristic-realizable headline.
>
>   (B) **Round-3 within-trips features.** Diagnose v34's residual within-trips ($1,291) for new structural signal. Feed back into ML as a new gated feature family if found.
>
>   (C) **Learned A-vs-C decision tree for Rule 6** (deferred from Sessions 38–39). A small classification tree on (trip_rank, max_kicker_rank, kicker suit profile) trained against the oracle's A-or-C choice. **$5–13/1000h whole-grid ceiling.** Session 40's connectivity probe surfaced an additional within-SS suit-rotation signal (+$19.53/1000h whole-grid mean lift on disagreement subset) that's another input for this tree's training. If C delivers, production could finally adopt v35's sharper Rule 6 boundary as a v38 ship.
>
>   (D) **KK/AA single-suited Rule-4-bot residual** ($37/1000h below oracle, 1.95% of grid). Defer behind A, B, C.
>
>   (E) **v34_dt re-train on v37 baseline.** v37 changes the production strategy on the three_pair slice (1.9% of grid). The v34 ML model was trained against v33's labels via residual-fitting; a v34 retrain on v37's labels should pick up small additional ML signal where the rule chain has shifted. Low priority — the residual change is small.

> **✅ SHIPPED (Decision 073):** **v37_rule7_three_pair** as the new production strategy of record. Replaces v33 in `STRATEGY_GUIDE.md` Part 5 + Part 6 + cheat sheet. Lives at `analysis/scripts/strategy_v37_rule7_three_pair.py`. Production strategy chain is now 7 rules deep: Rule 1 (pair-to-bot DS), Rule 2 (two-pair no-split), Rule 3 (trips+pair split-2-1), Rule 4 (KK/AA stay-mid), Rule 5 (KK/AA rainbow override), Rule 6 (pure trips paired-mid + boundary), Rule 7 (three_pair top=singleton + RB-or-RA on highest-pair-rank).
>
> **🚫 ARCHIVED (Session 41 same session):** `strategy_v36_rule7_high_only.py` — failed Rule 7 attempt for high_only category. ARCHIVED docstring added; file retained for history. Methodology rule: high_only resists rule extraction; do not re-attempt without a multi-feature ML breakthrough.

> **🔬 ARTIFACTS (Session 41):**
> 1. **`analysis/scripts/verify_rule_X_v33_high_only.py`** — first always-X probe for high_only. Three candidates (top=highest, rank-down 1-2-4, mid is two same-suit cards). Found X3 has +$355 oracle ceiling but no realizable heuristic.
> 2. **`analysis/scripts/probe_high_only_suited_mid_drill.py`** — 6 different tiebreakers tested for "which same-suit mid to pick"; all regressed vs v33. Confirmed high_only is ML-only.
> 3. **`analysis/scripts/strategy_v36_rule7_high_only.py`** — ARCHIVED production attempt. Heuristic regression of $6/1000h confirmed at full-grid scale.
> 4. **`analysis/scripts/grade_v36_rule7.py`** — full-grid grader for v36 (now archived).
> 5. **`analysis/scripts/verify_rule_X_v33_three_pair.py`** — full 114K population probe across 4 candidate rules (RA/RB/RC/RD). Found RA, RB both improve over v33; RC/RD regress.
> 6. **`analysis/scripts/probe_three_pair_boundary.py`** — full 286-cell (high, mid, low) breakdown. Tested ~20 boundary rules and found "RB if high ∈ {T,J,Q,K}" as the cleanest 1-condition winner.
> 7. **`analysis/scripts/probe_three_pair_final_rule.py`** — final rule pin-down + per-(high, low) reference table for human-readable form.
> 8. **`analysis/scripts/strategy_v37_rule7_three_pair.py`** — NEW PRODUCTION STRATEGY. Replaces v33 at runtime.
> 9. **`analysis/scripts/grade_v37_rule7.py`** — full-grid grader for v37; confirms +$43/1000h whole-grid (full) and +$141/1000h (prefix; three_pair has higher share there).

> **📓 METHODOLOGY LESSONS (Session 41):**
> - **NEW: Heuristic-realizable ceilings vary by category.** high_only's heuristic ceiling is essentially zero (−$6 vs +$355 oracle ceiling — 0% capture). three_pair's heuristic ceiling is much higher (+$43 vs +$71 oracle ceiling — 60% capture). The difference: three_pair's optimal-pick structure is rank-driven (single feature: highest pair rank), while high_only's optimal-pick structure is multivariate (suit pattern × singleton × bot composition × rank correlations). **Always-X probes should check whether the optimal-pick structure is uni-variate before declaring a category rule-extractable.**
> - **NEW: v33's diagnostics tell you which always-X candidate to test first.** v33's per-category routing reveals what it's already doing: "v33 picks mid=highest-pair on 68% of three_pair hands" → RA is the de facto current rule. Test the alternatives (RB, RC) immediately; don't waste a probe iteration confirming what v33 already does. Saved 2-3 iterations on three_pair.
> - **NEW: high_only is officially ML-only (do not re-attempt rule extraction).** Three rule attempts have now failed: v11 omaha-first (Session 26, −$1,745/1000h), v15 DS-patch (Session 26, −$296), v36 same-suit-mid (Session 41, −$6). The X3 oracle ceiling shows +$355/1000h IS available, but the within-suited-mid choice is multivariate (broadway-bearing has +0.13 lift, connected has +0.07 lift, bot-DS has −0.03 lift, rank-sum has 0.76 percentile correlation — none of these alone gets above 50% oracle agreement). The category is bound to v34_dt's gated `ho_*_g` features.
> - **REINFORCED (Session 38, 39, 40, 41): Two-track shipping is now standard.** Sessions 38–40 had v35 (human-only) sharper Rule 6 + v33 (production) keeping the simpler rule. Session 41's v37 Rule 7 ships in BOTH tracks (heuristic-realizable, no two-track needed). Future probes should default-test the heuristic version first; only fall back to two-track if the heuristic regresses.

> Updated: 2026-05-08 (end of Session 41)

---

## Headline state at end of Session 41

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v37_rule7_three_pair** | NEW PRODUCTION strategy of record (7 rules: v33 + Rule 7 three_pair) | `analysis/scripts/strategy_v37_rule7_three_pair.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v35_rule6_v3 | Human strategy of record for trips (sharper Rule 6 boundary). NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` + STRATEGY_GUIDE.md Part 6 Rule 6 |
| v33_rule6_trips | Prior production runtime (Session 37 ship; superseded by v37 in Session 41) | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v36_rule7_high_only | ARCHIVED — Session 41 failed Rule 7 attempt for high_only | `analysis/scripts/strategy_v36_rule7_high_only.py` (ARCHIVED docstring) |
| v34_rule6_v2 | ARCHIVED — Session 38 negative-result candidate | `analysis/scripts/strategy_v34_rule6_v2.py` |
| v32_d34ml3 | ARCHIVED — Session 38 control retrain | `data/v32_d34ml3_dt_model.npz` |
| v28_rule5_rainbow | Predecessor human chain (v14 + Rule 4 + Rule 5) | `analysis/scripts/strategy_v28_rule5_rainbow.py` |
| v31a / v31b / v20b / v19 / v21 / v22 | ARCHIVED candidates | various |

**Capacity + feature progression (full 6M grid, N=200) — UNCHANGED from Session 40:**

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

**Per-category breakdown (full grid, N=200):** unchanged from Session 38 for ML champion. The v37 ship changes the human-strategy chain's per-category numbers on three_pair (within-cat regret drops 67%); per-category breakdown for v37 is in the Session 41 entry of STRATEGY_GUIDE Part 1.

**Human-strategy progression (full grid, N=200) — production runtime:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v28_rule5_rainbow (+ Rule 4 + Rule 5) | $3,032 | 39.64% | −$1 |
| v33_rule6_trips (+ Rule 6 v1 — prior production) | $2,920 | 40.68% | −$113 |
| **v37_rule7_three_pair (+ Rule 7 — CURRENT PRODUCTION)** | **~$2,877** | **~41.2%** | **−$156** |

(v37 numbers pending full-grid grade confirmation; pre-grade estimate from drill of +$43/1000h vs v33.)

**Human-strategy ceiling (oracle-bound):**

| Strategy | Mode | $/1000h whole-grid (lower is better) | Δ vs v33 oracle-bound |
|---|---|---:|---:|
| v33 oracle-bound | reader picks best-A or best-C within v33 boundary | $-42.56/1000h | baseline |
| v35 oracle-bound | reader picks best-A or best-C within v35 sharper boundary | $-34.44/1000h | +$8.12 |
| Pure oracle | reader picks any A∪C cell freely | $-3.51/1000h | +$39.05 |

(Oracle-bound numbers don't include Rule 7's three_pair-only impact — they're trips-specific.)

---

## What this leaves on the table (UPDATED Session 41)

- **For human play (oracle-bound on three_pair):** v37 captures 60% of the per-cell oracle ceiling on three_pair. The remaining ~$28/1000h is in K-high cells with low-pair-7+ edge cases, A-high cells with very low-pair (low ≤ 3), and multi-feature signal (suits, singleton-rank correlations). Not capturable by simple rules — it's ML / per-cell-table territory.
- **For human play (oracle-bound on trips):** unchanged from Session 39 — v35 captures 63% of the Rule 6 oracle ceiling. Still ~$4.77/1000h on the table for a future learned A-vs-C tree (Priority C).
- **For production runtime:** v37 + v33 stack — v37 fires on three_pair (1.9% of hands), v33 handles trips + the rest. v37's three_pair lift (+$43) is realized; v33's trips lift (+$112 over v28) is realized; the Rule 6 boundary gap (~$80 on trips' full A∪C ceiling) is still ML-only territory.
- **For ML champion:** v34 captures 44.6% of the v14→ceiling gap at N=200. Biggest residuals at full grid (per Session 38 breakdown):
  - **high_only**: $572 share — **OFFICIALLY ML-ONLY (Session 41 confirmation)**, will not see another rule attempt
  - **pair**: $754 share — KK/AA single-suited Rule-4-bot is the largest sub-stratum (open)
  - **two_pair**: $218 share — capacity-improved at v34, always-X probe pending
  - **trips**: $71 share — v30, v32, v34 have all shipped; round-3 needs new diagnostic angles
  - three_pair: $86 → ~$28 share **after v37 ships** — captured 67% via Rule 7
  - trips_pair: $30 (already gated; v34 capacity expansion)
  - composite: $2.9 (already gated; always-X probe pending)

---

## What Session 41 produced

**Code:**
1. `analysis/scripts/verify_rule_X_v33_high_only.py` — initial high_only always-X probe (3 candidates)
2. `analysis/scripts/probe_high_only_suited_mid_drill.py` — same-suit-mid drill (6 tiebreakers, all regressed)
3. `analysis/scripts/strategy_v36_rule7_high_only.py` — ARCHIVED Rule 7 high_only attempt
4. `analysis/scripts/grade_v36_rule7.py` — full-grid grader for v36 (regression confirmed)
5. `analysis/scripts/verify_rule_X_v33_three_pair.py` — three_pair always-X probe (RA/RB/RC/RD)
6. `analysis/scripts/probe_three_pair_boundary.py` — full 286-cell breakdown + boundary search
7. `analysis/scripts/probe_three_pair_final_rule.py` — final rule pin-down + A-2 reference
8. `analysis/scripts/strategy_v37_rule7_three_pair.py` — **NEW PRODUCTION STRATEGY (v37)**
9. `analysis/scripts/grade_v37_rule7.py` — full-grid + prefix grader for v37

**Documentation:**
1. `STRATEGY_GUIDE.md` Part 6 — new Rule 7 section (after Rule 6) with worked examples for AA, KK, QQ, JJ, TT, 99, and 44-high cases. "Default" section updated to remove three_pair. Cheat sheet updated to include three_pair handling.
2. `STRATEGY_GUIDE.md` Part 5 — added v37 to current-production-chain reference + Session 41 probes.
3. `STRATEGY_GUIDE.md` Part 1 Session 41 entry — full session log with both methodology lessons (heuristic ceilings vary by category; v33 diagnostics surface candidates).
4. `STRATEGY_GUIDE.md` header — bumped Last updated date to 2026-05-08.
5. `CURRENT_PHASE.md` — rewritten (this file).
6. `DECISIONS_LOG.md` — Decision 073 added (v37 ships; v36 archived; high_only is ML-only).

---

## Resume Prompt (Session 42)

```
Resume Session 42 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Session 41 entry in Part 1; Part 5 lists v37 as
  current production; Part 6 has Rule 7 with worked examples)
- CURRENT_PHASE.md (rewritten end of Session 41)
- DECISIONS_LOG.md (latest: Decision 073 — v37 Rule 7 three_pair ships;
  v36 Rule 7 high_only archived; high_only is officially ML-only)
- analysis/scripts/strategy_v37_rule7_three_pair.py — current production
- analysis/scripts/strategy_v34_dt.py — ML champion

State (end of Session 41):
- Production strategy of record is now **v37_rule7_three_pair** (7 rules).
  Three_pair within-cat regret dropped 67% ($4,085 → $1,334) on the
  prefix grade. +$43/1000h whole-grid lift confirmed at full-grid scale.
- high_only is OFFICIALLY ML-only territory after the v36 Rule 7
  attempt failed. Three rule attempts (v11, v15, v36) have now regressed
  by $1,745, $296, $6 respectively. The X3 oracle ceiling of $355/1000h
  is multivariate and unrealizable by any rule.
- v34_dt remains the ML champion. v37 doesn't change the ML champion
  but does change the production strategy chain (rule layer).

Next session targets (priority order):

(A) Always-X probes for the 2 remaining categories — composite + two_pair.
    Apply the same template (verify_rule_X_v33_<cat>.py) used for
    high_only and three_pair this session. Composite is heterogeneous
    (likely needs sub-stratification). Two_pair may already have its
    structural rule baked into v33 via Rule 2 + v3's pair routing.

(B) Round-3 within-trips features. Diagnose v34's residual within-trips
    ($1,291) for new structural signal.

(C) Learned A-vs-C decision tree for Rule 6 (deferred from Sessions 38–40).
    Concrete $5–13/1000h whole-grid ML target. With Session 40's within-SS
    suit-rotation signal as additional training input.

(D) KK/AA single-suited Rule-4-bot residual ($37/1000h below oracle).

(E) v34_dt re-train on v37 baseline. v37's three_pair changes affect
    1.9% of grid; ML retrain may pick up small additional signal.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated and use a UNIQUE
  prefix.
- Methodology rule (Session 41 NEW): heuristic-realizable ceilings vary
  by category; check whether the optimal-pick structure is uni-variate
  before declaring a category rule-extractable.
- Methodology rule (Session 41 NEW): v33/current-production diagnostics
  reveal what's already doing; test alternatives first to skip iterations.
- Methodology rule (Session 41 NEW): high_only is officially ML-only;
  do not re-attempt rule extraction without a multi-feature breakthrough.
- Methodology rule (Session 38): default ML champion ships now use
  depth=34 ml=2. Capacity sweeps: ml ∈ {3, 2} at depth=34+.
- Methodology rule (Session 38): always-X probes must report BOTH
  oracle ceiling AND heuristic-realizable headline.
- Methodology rule (Session 39): the human strategy guide can be
  sharper than the production heuristic when heuristic-A is the
  rate-limiting step. Two-track ship (guide ships, runtime stays).
- Methodology rule (Session 40): candidate-level invariance is a
  prerequisite for any candidate-level priority/tiebreaker.
- Methodology rule (Session 40): mean-EV-per-cell aggregates can hide
  selection effects.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
