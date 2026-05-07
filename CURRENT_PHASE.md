# Current: Sprint 8 — Session 38 wrap. **One ship, one negative.** v34_dt is the new ML champion ($1,681 full / $889 prefix; depth=34 ml=2 capacity-only retrain of v32's 83 features; +19.5% leaves; cumulative v30→v34 of $113/1000h is the largest cumulative ML arc in project history). Rule 6 v2 (the user's "C variant is wrong at low trip ranks" hypothesis) was validated at the oracle level but cannot be cashed via heuristic-A — sweep across all 13 trip-rank thresholds gave +$0.57/1000h max, within noise. v33's Rule 6 boundary stands.

> **🎯 IMMEDIATE NEXT ACTION (Session 39):**
>   (A) **Always-X structural baseline probes for remaining categories.** Rule 6 came from the trips diagnostic. Apply systematically:
>      - **three_pair** ($31/1000h whole-grid; untouched by gating; routed by v7_regression). Candidate rule: "always top = unpaired card; mid = highest pair; bot = 2 lower pairs."
>      - **composite** ($3.4/1000h whole-grid; high per-category regret). Heterogeneous category — may need sub-stratification.
>      - **two_pair** ($231 share; heavily ML-engineered already). Candidate: "always split high pair to mid".
>      - **high_only** ($574 share — biggest residual). Already routed via v3 in v8_hybrid; check if v3's structural decisions match the oracle.
>      Each probe writes `verify_rule_X_v33_<category>.py`, reports BOTH the oracle ceiling AND the closest heuristic-realizable headline (Session 38 lesson — heuristic ceilings are usually 30-95% smaller than oracle ceilings).
>
>   (B) **Round-3 within-trips features (or pair-r5 / two_pair-r2).** v34's trips category lifted to $1,291 within-cat — within-trips share is now 4.2% of grid. Diagnostic: write `distill_v34_trips.py` to find the within-trips structure that v34's 4 trips_v2 features still don't capture. If a structural baseline exists (analogous to "Always A∪C" surfacing Rule 6), feed it back into ML as a new gated feature family.
>
>   (C) **Learned A-vs-C decision tree for Rule 6.** The Session 38 negative-v34 result reframed the user's hypothesis as an ML target: a small classification tree on (trip_rank, max_kicker_rank, suit profile of kickers) trained against the oracle's A-or-C choice. Could capture another $5-13/1000h whole-grid IF the heuristic-A is replaced or augmented. Defer behind A and B unless trips diagnostic surfaces nothing new.
>
>   (D) **KK/AA single-suited Rule-4-bot residual** ($37/1000h below oracle, 52.9% of KK/AA, 1.95% of grid). Defer. v31a's tight gating shipped only +$6 — needs a different angle (meta-classifier feature trained on probe data, or sub-tree dedicated to KK/AA hands).

> **✅ SHIPPED (Decision 069):** v34_dt = same 83 features as v32, retrained at depth=34, min_samples_leaf=2. **874,548 leaves** (+19.5% over v32's 731,606, +$$5%$ over v31's 700K). 2nd capacity-only ship in project history.
>
> | Grid | v32 | **v34_dt** | Δ |
> |---|---:|---:|---:|
> | Full N=200 (6.0M) | $1,715 / 51.31% | **$1,681 / 52.02%** | **−$34 / +0.71pp** |
> | Prefix N=1000 (500K) | $904 / 62.47% | **$889 / 62.74%** | **−$15 / +0.27pp** |
>
> **Cumulative v30 → v34 = $113/1000h on full grid** is the largest cumulative ML ship arc in project history (beats Session 37's v30→v32 of $79). Decomposition: v30→v31 (+$58, capacity), v31→v32 (+$20, trips_v2 features), v32→v34 (+$34, capacity at ml=2). All eight categories improve simultaneously — textbook capacity-only signature, not gating signature.

> **🚫 ARCHIVED (Decision 070):** v34_rule6_v2. The user's Priority A hypothesis — that Rule 6's C variant (3rd trip card on top) is wrong for low/mid trip ranks — was directionally validated at the oracle level (best-A regret $82/1000h whole-grid vs best-C $608) but the heuristic-A could only realize **+$0.57/1000h whole-grid at the best threshold** ("trip ≥ T → C"). Rule 6 v2 sweep across `min_trip_for_C ∈ {3..14, A-only}` showed every threshold ≥ Q LOSES money to v33 (-$2.69 to -$71.96/1000h). v33's "trip > max_kicker → C" boundary stands as the human strategy of record. The remaining ~$5-13/1000h of A-vs-C oracle gap is reframed as a future ML target (learned A-heuristic or learned A-vs-C tree).

> **🔬 DIAGNOSTIC + DESIGN CHAIN (Session 38):**
> 1. **Capacity sweep at v32's 83 features** (Path A): trained two candidates at depth=34. **d34ml3 (control)** produced 731,611 leaves at achieved depth 33 — only +5 leaves vs v32 — proving **ml=3 was the binding leaf constraint, not depth=32**. Result: bit-identical to v32 ($1,715 / 51.31%). **d34ml2 (high-capacity)** produced 874,548 leaves (+19.5%) at achieved depth 33. Result: $1,681/1000h on full / $889 on prefix — ships.
> 2. **Per-category at v34:** every category lifts. Within-category gains: composite −$213, trips_pair −$168, trips −$68, two_pair −$59, quads −$32, pair −$20, high_only −$10, three_pair −$4. Whole-grid contribution dominated by two_pair (-$13 via 22.3% share) and pair (-$9 via 46.6% share).
> 3. **Rule 6 A-vs-C oracle probe** (`probe_rule6_c_variant.py`, Path B): on the same 30K trips probe sample as Session 37, computed best-A and best-C oracle EVs stratified by (trip_rank, max_kicker_rank). Best-A regret $82/1000h whole-grid; best-C regret $608/1000h. C wins overwhelmingly only at trip A (100% of cells, +$5,757 to +$14,139); at trip K (+$2,131 to +$7,240); narrowly at trip Q (-$278 to +$3,758 mixed); LOSES at trip ≤ J. **User's hypothesis is correct directionally.**
> 4. **Heuristic-realizable v34 sweep** (`probe_v34_sweep.py`): for `min_trip_for_C ∈ {3..14, A-only}`, build a Rule 6 v2 candidate and grade vs v33. Best result: **+$0.57/1000h at trip ≥ T → C**. Every tighter threshold (Q, K, A, A-only) LOSES money. The 95% gap between oracle and heuristic ceilings is the v33/v34 A-variant heuristic underperforming on flipped cells (at trip Q, heuristic-A loses ~$1,857/1000h within-trips on flipped cells; at trip J, ~$639/1000h). The bot-DS optimizer is the rate-limiting step.
> 5. **Ship/no-ship decisions:** v34_dt (capacity ship) shipped. v34_rule6_v2 (rule-extraction ship) archived as a probe-confirmed-but-heuristic-incapable result.

> **📓 METHODOLOGY LESSONS REINFORCED (Session 38):**
> - **min_samples_leaf=2 can unlock more capacity than depth.** When ml=3 saturates below the depth cap (control hit depth 33 of 34 cap), the next capacity unlock is ml=2, NOT deeper depth. **Refines Session 37's rule:** sweep `min_samples_leaf ∈ {3, 2}` at a generous depth cap (34+) and pick the smaller-ml winner if shape-agreement improves.
> - **Heuristic-realizable ceilings are smaller than oracle ceilings, sometimes by 95%.** Rule 6 captured 56% of $197 oracle (Session 37); Rule 6 v2 would capture ~5% of $13 oracle (Session 38). Future Always-X probes should report BOTH numbers to set realistic expectations BEFORE building a heuristic.
> - **Capacity ships move every category; gating ships move one.** v31 and v34 are capacity-only ships (broad cross-category gains, no new features). v20/v23/v24/v25/v26/v27/v29/v30/v32-trips_v2 are gating ships (one category lifts, others bit-identical). 2 + 9 instances now confirm the per-category shape distinguishes the two ship types.
> - **Tripwire is a feature-design diagnostic.** Capacity ships skip it (no new features); use leaf-count growth + per-category coverage instead. v34 had +19.5% leaves and broad cross-category lifts → both the right capacity-ship signals.

> Updated: 2026-05-06 (end of Session 38)

---

## Headline state at end of Session 38

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v34_dt** | ML champion (NEW, 874K leaves, 83 features at depth=34 ml=2 — same feature set as v32) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v33_rule6_trips | Human-memorizable strategy (Rule 6 ship from Session 37; +$112/1000h vs v28 on full, +$143 on prefix) | `STRATEGY_GUIDE.md` Part 6 + `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3, 83 features) | `analysis/scripts/strategy_v32_dt.py` + `data/v32_dt_model.npz` |
| v31_dt | 79 features at depth=32 ml=3 | `analysis/scripts/strategy_v31_dt.py` + `data/v31_dt_model.npz` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v32_d34ml3 | ARCHIVED — Session 38 control retrain (proves ml=3 was binding constraint, not depth=32) | `data/v32_d34ml3_dt_model.npz` |
| v34_rule6_v2 | ARCHIVED — Session 38 Rule 6 boundary candidate (negative result) | `analysis/scripts/strategy_v34_rule6_v2.py` |
| v28_rule5_rainbow | Predecessor human chain (v14 + Rule 4 + Rule 5) | `analysis/scripts/strategy_v28_rule5_rainbow.py` |
| v31a / v31b / v20b / v19 / v21 / v22 | ARCHIVED candidates | various |

**Capacity + feature progression (full 6M grid, N=200):**

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
| v32_d34ml3 | 34 (33 actual) | 3 | 83 (same as v32) | 731,611 | $1,715 | 51.31% | $0 vs v32 (control: ml=3 was leaf-binding) |
| **v34** | **34 (33 actual)** | **2** | **83 (same as v32)** | **874,548** | **$1,681** | **52.02%** | **−$34 vs v32, −$113 cumulative vs v30 (largest ML arc in project history)** |

**Same sweep on N=1000 prefix:**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v18e | $1,082 | 59.30% | — |
| v25 | $1,054 | 59.80% | −$28 |
| v26 | $1,002 | 60.80% | −$52 |
| v27 | $1,002 | 60.80% | $0 |
| v29 | $965 | 61.32% | −$37 vs v27 |
| v30 | $951 | 61.53% | −$15 vs v29 |
| v31 | $921 | 62.07% | −$29 vs v30 |
| v32 | $904 | 62.47% | −$18 vs v31 |
| **v34** | **$889** | **62.74%** | **−$15 vs v32, −$62 cumulative vs v30** |

**Per-category breakdown (full grid, N=200):**

| Category | v18e | v20 | v25 | v26 | v27 | v29 | v30 | v31 | v32 | v34 | Δ v34 vs v18e |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high_only  | $3,307 | $2,894 | $2,894 | $2,894 | $2,863 | $2,862 | $2,862 | $2,816 | $2,816 | **$2,806** | **−$501** |
| pair       | $1,873 | $1,873 | $1,771 | $1,771 | $1,771 | $1,674 | $1,674 | $1,639 | $1,639 | **$1,619** | **−$254** |
| two_pair   | $1,458 | $1,458 | $1,458 | $1,145 | $1,145 | $1,145 | $1,145 | $1,037 | $1,037 | **$978** | **−$480** |
| **trips**  | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,758 | $1,732 | $1,359 | **$1,291** | **−$706** |
| trips_pair | $1,608 | $1,608 | $1,446 | $1,445 | $1,445 | $1,443 | $1,442 | $1,225 | $1,225 | **$1,057** | **−$551** |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | $1,639 | $1,639 | **$1,635** | **−$18** |
| quads      | $724 | $724 | $723 | $723 | $723 | $723 | $723 | $645 | $645 | **$613** | **−$111** |
| composite  | $2,100 | $2,100 | $1,869 | $1,741 | $1,741 | $1,741 | $1,733 | $1,387 | $1,386 | **$1,173** | **−$927** |

**Nine category-gated wins now visible** plus two capacity-only ships (v31, v34). **v34 is a capacity-only ship that lifts every category simultaneously** — textbook capacity signature. Biggest within-category lifts: composite (−$213 vs v32), trips_pair (−$168), trips (−$68), two_pair (−$59).

**Human-strategy progression (full grid, N=200):**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v28_rule5_rainbow (+ Rule 4 + Rule 5) | $3,032 | 39.64% | −$1 |
| **v33_rule6_trips (+ Rule 6)** | **$2,920** | **40.68%** | **−$113** |

The v28 → v33 ship of −$112/1000h (Session 37) remains the largest single rule ship in project history. **Session 38 produced no human-strategy ship** — Rule 6 v2 was archived after sweep showed +$0.57/1000h max gain at heuristic level (well within noise) despite the user's hypothesis being directionally correct on oracle.

---

## What this leaves on the table

- v34 captures **44.6% of the v14→ceiling gap** at N=200 fidelity ($1,352/$3,033 vs v14)
- v34 captures **71.0% of the v14→ceiling gap** at N=1000 fidelity ($1,148/$2,037)
- Remaining gap to ceiling: **$1,681/1000h (full grid N=200)**, **$889/1000h (prefix N=1000)**
- v33 captures **3.7% of the v14→ceiling gap** for the human chain at N=200, **7.0%** at N=1000.
- Biggest residuals at full grid (per-category × share):
  - **high_only**: 20.4% × $2,806 = **$572 share** — largest residual
  - **pair**: 46.6% × $1,619 = **$754 share** — KK/AA single-suited Rule-4-bot is the largest sub-stratum (open)
  - **two_pair**: 22.3% × $978 = **$218 share** — capacity-improved at v34
  - **trips**: 5.5% × $1,291 = **$71 share** — v30, v32, v34 have all shipped; further work needs new diagnostic angles
  - three_pair: 1.9% × $1,635 = $31 (untouched by gating)
  - trips_pair: 2.86% × $1,057 = $30 (already gated; v34 capacity expansion)
  - composite: 0.245% × $1,173 = $2.9 (already gated; v34 capacity expansion)
- **Rule 6's heuristic capture is 56% of its oracle ceiling.** The remaining $86/1000h is now reframed as a future ML target (Decision 070).

---

## What Session 38 produced

### v34 ship + Rule 6 v2 archived

**1. Capacity sweep at v32's 83 features** (`train_v32_capacity_sweep.py`):
- d34ml3 control: 731,611 leaves at depth 33 — **proves ml=3 was the binding leaf constraint**, not depth.
- d34ml2 candidate: 874,548 leaves at depth 33 (+19.5% capacity).
- Grading on full + prefix grids: candidate ships −$34 full / −$15 prefix.
- Promoted to v34_dt; new ML champion.

**2. Rule 6 A-vs-C oracle probe** (`probe_rule6_c_variant.py`):
- best-A regret: $82/1000h whole-grid; best-C regret: $608/1000h.
- Per-cell stratification: C dominant only at trip ≥ K (+$2k–$14k); A dominant at trip ≤ J (−$1.7k to −$17k); mixed at trip Q (depends on max_kicker).
- Validates user's directional hypothesis at the oracle level.

**3. Rule 6 v2 sweep across boundary thresholds** (`probe_v34_sweep.py`):
- Tested `min_trip_for_C ∈ {3..14, A-only}` on the 30K probe sample.
- Best result: +$0.57/1000h at trip ≥ T → C (well within noise).
- Every threshold ≥ Q LOSES money to v33 (-$2.69 to -$71.96/1000h whole-grid).
- The bottleneck is the heuristic A-variant's bot-DS optimizer, not the threshold rule.

### Methodology lessons reinforced (Session 38)

1. **`min_samples_leaf=2` can unlock more capacity than deeper depth.** Specifically, when ml=3 saturates below the depth cap, ml=2 is the next unlock.
2. **Heuristic-realizable ceilings are typically much smaller than oracle ceilings.** Always-X probes should report both.
3. **Capacity ships move every category; gating ships move one.** Two clean capacity ships now confirm (v31, v34).
4. **Tripwire is a feature-design diagnostic; capacity ships skip it** (use leaf-count + per-category coverage).

---

## Resume Prompt (Session 39)

```
Resume Session 39 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Session 38 entry in Part 1; Part 2 has v34_dt as
  current champion; Part 6 has Rule 6 unchanged)
- CURRENT_PHASE.md (rewritten end of Session 38)
- DECISIONS_LOG.md (latest: Decision 069 v34_dt ship, Decision 070
  v34_rule6_v2 archived)
- analysis/scripts/strategy_v34_dt.py — current ML champion harness
- analysis/scripts/strategy_v33_rule6_trips.py — current human champion
- analysis/scripts/probe_rule6_c_variant.py — Rule 6 A-vs-C oracle probe
- analysis/scripts/probe_v34_sweep.py — Rule 6 boundary sweep (negative)

State (end of Session 38):
- v34_dt is the new ML champion: $1,681/1000h on full grid (52.02% opt),
  $889/1000h on prefix (62.74% opt). 874,548 leaves, depth=34, ml=2,
  same 83 features as v32. Cumulative v30 → v34 of -$113/1000h on
  full grid is the new largest cumulative ML arc in project history.
- v34_rule6_v2 was probed and archived. v33 remains the human champion.

Next session targets (priority order):

(A) Always-X structural baseline probes for remaining categories.
    Rule 6 came out of the trips diagnostic. Apply systematically:
    - three_pair (untouched by gating, 1.9% share)
    - composite (high per-category regret, tiny share)
    - two_pair (heavily ML-engineered already)
    - high_only (largest residual share, 20.4%)
    Each probe writes verify_rule_X_v33_<category>.py; report BOTH
    oracle ceiling AND heuristic-realizable headline.

(B) Round-3 within-trips features (or pair-r5 / two_pair-r2).
    Diagnose v34's residual within-trips ($1,291) for new structural
    signal. Feed back into ML as a new gated feature family if found.

(C) Learned A-vs-C decision tree for Rule 6. Reframes Session 38's
    negative result: a small classification tree on (trip_rank,
    max_kicker_rank, suit profile) trained against oracle's A-or-C
    choice. $5-13/1000h ML target.

(D) KK/AA single-suited Rule-4-bot residual ($37/1000h below oracle).
    Different angle needed than v31a's tight gating.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated and use a UNIQUE
  prefix. Claimed: `_g` (suited), `tp_*_g` (trips_pair), `comp_*_g`
  (composite), `pair_*_g` (pair v1), `t2p_*_g` (two_pair), `ho_*_g`
  (high_only), `pair_r4_*_g` (pair v2), `trips_*_g` (trips), and
  `trips_v2_*_g` (trips round 2). Archived: `pair_r4v3_*_g`.
- Methodology rule (Session 38): default future ML champion ships
  to depth=34 ml=2. When evaluating capacity, sweep ml ∈ {3, 2} at
  generous depth cap (34+) and pick smaller-ml winner if shape-
  agreement improves.
- Methodology rule (Session 37): rule chains should default to override-
  everything within scope, not just patch mistakes.
- Methodology rule (Session 38): always-X probes should report BOTH
  oracle ceiling AND closest heuristic-realizable headline.
- Methodology rule (Session 36+37): tripwire predicts conversion rate
  (~10-15%), not absolute opportunity. Capacity ships skip tripwire.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
