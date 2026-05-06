# Current: Sprint 8 — Session 37 wrap. **TWO ships, both records:** v32_dt is the new ML champion (cumulative v30→v32 of −$79/1000h on full grid beats v26's $70 to become the largest single-session ML ship in project history); v33_rule6_trips is the new human strategy of record (+$112/1000h vs v28 on full, +$143 on prefix — the largest single rule ship in project history). Rule 6 statement: "On pure trips, the third trip card never goes to bot."

> **🎯 IMMEDIATE NEXT ACTION (Session 38):**
>   (A) **Capacity sweep at v32's higher feature count.** v32 has 83 features and 731,606 leaves. Per the methodology rule, leaf-count grew +5% over v31 — borderline; the next ship that adds ≥6 features should also re-test capacity at depth=34 ml=2 explicitly. Build `train_v32_capacity_sweep.py` that retrains v32's 83 features at depth=34 ml=2 (and depth=34 ml=3 as control). Could potentially unlock another $10-30/1000h.
>   (B) **Always-X structural baseline probes for remaining categories.** Rule 6 came out of the trips diagnostic. Apply the same pattern systematically: write `verify_rule_X_v33_<category>.py` for high_only, two_pair, trips_pair (likely covered by v12 already but verify), three_pair, composite. Each probe checks whether v33 + Rule X (always-X) has a measurable gain. Highest-priority candidates by expected value:
>      - **composite** ($1,386/1000h within-category × 0.245% share = $3.4/1000h whole-grid — small but the per-category regret is highest in the project)
>      - **three_pair** ($1,639 × 1.9% = $31/1000h — moderate, untouched by gating)
>      - **high_only** ($2,816 × 20.4% = $574/1000h — by far the largest residual share; even a $20/1000h within-category improvement = $4/1000h whole-grid)
>      - **two_pair** ($1,037 × 22.3% = $231/1000h — heavily ML-engineered, harder to find rule-extractable structure)
>   (C) **KK/AA single-suited Rule-4-bot residual** ($37/1000h below oracle, 52.9% of KK/AA, 1.95% of grid). v31a's KK/AA-tight features shipped only +$6 — a different angle is needed. Options: (i) meta-classifier feature trained on probe data, (ii) sub-tree dedicated to KK/AA hands, (iii) leave open, focus on Rule X.
>   (D) **v33 → v34 candidate: tighter A-vs-C heuristic.** Rule 6's heuristic captures 56% of the $197 oracle ceiling. The remaining 44% ($86/1000h) requires better A-vs-C choice on edge cases (e.g., trip rank 9-12 where the kicker boundary is closer). Probe-driven decision tree on (trip_rank, max_kicker_rank, suit profile of kickers) might capture another 10-20%.

> **✅ SHIPPED (Decision 067 + 068):** Two ships in Session 37:
>
> - **v32_dt** — depth=32, ml=3, **731,606 leaves** (+31,833 vs v31, +4.6% capacity), 83 features (79 v30 + 4 trips_v2 round-2). 9th gating-template instance and FIRST within-trips iteration (analogous to v25→v29 for pair). **−$20/1000h full vs v31, −$18/1000h prefix.** Cumulative v30→v32 of **−$79/1000h on full grid beats v26's record ($70)** as the largest single-session ML ship in project history. Tripwire: 0/4 in top-30 (positions 55, 60, 72, 73). 7 ships in a row now confirm tripwire predicts conversion rate (~10-15%), not absolute opportunity.
>
> - **v33_rule6_trips** — codifies Rule 6 ("On pure trips, the third trip card never goes to bot"). Decision tree: `trip_rank > max_kicker_rank → C variant (top = trip rank); else → A variant (top = highest kicker)`; within A variant, choose which trip → bot for max bot DS-ness. **+$112/1000h on full grid (v28 $3,032 → v33 $2,920), +$143/1000h on prefix.** Trips category drops from $4,054 → $2,010 within-trips (almost halved); trips' optimal-pick rate jumps 19.9% → 39.0%. **Largest single rule ship in project history** — bigger than Rule 4 + Rule 5 combined.

> **🔬 DIAGNOSTIC + DESIGN CHAIN (Session 37):**
> 1. **Path A executed:** v32 = stack v31b's trips_v2 round-2 features on v31's high-capacity config. Probe (Session 36 cascade) had predicted ~$15 incremental on top of v31's $58 = $73 vs v30. Actual: $79 vs v30 (slight positive interaction). v32's gain is concentrated in trips: full-grid $1,732 → $1,359 (−$373 within-trips, +$20 whole-grid given 5.5% trips share).
> 2. **Path B verification surfaced a $197/1000h ceiling.** `verify_rule6_v14_trips.py` traced v14_combined on a 30K pure-trips sample. Three findings: (a) v14 picks "mid is paired" only 94.3% of the time — 5.4% of trips go to B (3rd trip on bot), losing $3,609/1000h within-trips ($197 whole-grid); (b) v14's A-vs-C decision is empirically correct on the 94.3% it gets right — equivalent to top = max(trip_rank, max_kicker_rank); (c) the cleanest rule formulation is "Always A∪C" (mid is paired with trip rank, top is either the 3rd trip card or the highest kicker).
> 3. **v33 codified Rule 6 with override-everything semantics.** Two variants tested empirically on 30K probe: override-only-when-B captured $37/1000h; override-everything captured $111/1000h. Override-everything wins because the heuristic's bot-DS optimization on the A variant beats v14/v8_hybrid's learned routing on average. **Methodology rule (Session 37): rule chains should default to override-everything within scope, not just patch mistakes.**
> 4. **Heuristic captures 56% of the oracle ceiling.** The $86/1000h gap is the limit of "no peeking at oracle EVs"; closing it would require a learned routing within A∪C, out of scope for the human rule chain.
> 5. **Final headlines: v32 + v33 ship simultaneously**, neither modifies the other (v32 already encodes trips routing via the gated `trips_*_g` and `trips_v2_*_g` feature families; v33 is a human-strategy ship targeting the v28 chain).

> **📓 METHODOLOGY LESSONS REINFORCED (Session 37):**
> - **Tripwire confirmed 7×** (v25 5/6→+$47, v26 3/6→+$70, v27 0/4→+$6, v29 3/4→+$46, v30 0/6→+$13, v31a 0/4→+$6, v31b 0/4→+$15, v32 0/4→+$20). Tripwire predicts CONVERSION rate, not absolute opportunity. Round-2 within-category iterations are bearish-tripwire-but-positive-headline by template now.
> - **Orthogonal axis stacking works.** v31's capacity expansion ($58) and v31b's trips_v2 features ($15) stacked additively to v32's $79 cumulative (with a small extra $6 from interaction). Future template: standalone diagnostic-driven feature design at depth=32 ml=3, then re-test capacity at depth=34 ml=2 if leaf-count grows substantially.
> - **Always-X structural baselines surface Rule-N candidates worth shipping.** Rule 6 was directly seeded by Session 36's trips diagnostic. Future sessions should systematically probe each category for an always-X baseline — Rule 6's $112-143/1000h ship is the validation that this pattern can produce material gains.
> - **Rule chain ships should default to override-everything within scope.** The "preserve v14 when already-A∪C" variant captured only $37/1000h vs override-everything's $112. Rule heuristics often have structural reasoning that beats the learned strategy's fine-grained choices, even within the rule's scope.
> - **Trips is now the 4th-best-handled category in v32** ($1,359 within-trips, behind two_pair $1,037, trips_pair $1,225, and ahead of composite $1,386). The combined v30+v32 trips work has lifted trips by −$638/1000h within-trips (from v18e's $1,997), the second-largest absolute within-category improvement after composite ($2,100 → $1,386 = −$714).

> Updated: 2026-05-06 (end of Session 37)

---

## Headline state at end of Session 37

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v33_rule6_trips** | Human-memorizable strategy (NEW, +$112/1000h vs v28 on full, +$143 on prefix) | `STRATEGY_GUIDE.md` Part 6 + `analysis/scripts/strategy_v33_rule6_trips.py` |
| **v32_dt** | ML champion (731,606 leaves, 83 features at depth=32 ml=3 — 37 base + 9 gated families: 6 suited + 6 trips_pair + 4 composite + 6 pair v1 + 6 two_pair + 4 high_only + 4 pair_r4 + 6 trips + 4 trips_v2) | `analysis/scripts/strategy_v32_dt.py` + `data/v32_dt_model.npz` |
| v31_dt | Predecessor (79 features, depth=32 ml=3, 700K leaves) | `analysis/scripts/strategy_v31_dt.py` + `data/v31_dt_model.npz` |
| v30_dt | Older baseline (depth=30 ml=5, 79 features, 493K leaves) | `analysis/scripts/strategy_v30_dt.py` + `data/v30_dt_model.npz` |
| v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Superseded baselines; retained | `data/v*_dt_model.npz` |
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
| **v32** | **32** | **3** | **83 (79 + 4 trips_v2)** | **731,606** | **$1,715** | **51.31%** | **−$20 vs v31, −$79 cumulative vs v30 (largest single-session ship)** |

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
| **v32** | **$904** | **62.47%** | **−$18 vs v31, −$47 cumulative vs v30** |

**Per-category breakdown (full grid, N=200):**

| Category | v18e | v20 | v25 | v26 | v27 | v29 | v30 | v31 | v32 | Δ v32 vs v18e |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high_only  | $3,307 | $2,894 | $2,894 | $2,894 | $2,863 | $2,862 | $2,862 | $2,816 | **$2,816** | **−$491** |
| pair       | $1,873 | $1,873 | $1,771 | $1,771 | $1,771 | $1,674 | $1,674 | $1,639 | **$1,639** | **−$234** |
| two_pair   | $1,458 | $1,458 | $1,458 | $1,145 | $1,145 | $1,145 | $1,145 | $1,037 | **$1,037** | **−$421** |
| **trips**  | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,758 | $1,732 | **$1,359** | **−$638** |
| trips_pair | $1,608 | $1,608 | $1,446 | $1,445 | $1,445 | $1,443 | $1,442 | $1,225 | **$1,225** | **−$383** |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | $1,639 | **$1,639** | **−$14** |
| quads      | $724 | $724 | $723 | $723 | $723 | $723 | $723 | $645 | **$645** | **−$79** |
| composite  | $2,100 | $2,100 | $1,869 | $1,741 | $1,741 | $1,741 | $1,733 | $1,387 | **$1,386** | **−$714** |

**Nine category-gated wins now visible** plus one capacity-only ship (v31). v32 is the FIRST within-category iteration of the trips template (analogous to v25→v29 for pair).

**Human-strategy progression (full grid, N=200):**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v28_rule5_rainbow (+ Rule 4 + Rule 5) | $3,032 | 39.64% | −$1 |
| **v33_rule6_trips (+ Rule 6)** | **$2,920** | **40.68%** | **−$113** |

The v28 → v33 ship of **−$112/1000h is larger than the cumulative gain from Rules 1-5 combined** (which moved v8_hybrid → v28 by −$121, of which −$120 came from Rules 1-3 in v14 and only −$1 from Rules 4-5).

---

## What this leaves on the table

- v32 captures **43.5% of the v14→ceiling gap** at N=200 fidelity ($1,318/$3,033 vs v14)
- v32 captures **70.6% of the v14→ceiling gap** at N=1000 fidelity ($1,133/$2,037)
- Remaining gap to ceiling: **$1,715/1000h (full grid N=200)**, **$904/1000h (prefix N=1000)**
- v33 captures **3.7% of the v14→ceiling gap** for the human chain at N=200, **7.0%** at N=1000.
- Biggest residuals at full grid (per-category × share):
  - **high_only**: 20.4% × $2,816 = **$574 share** — largest residual
  - **pair**: 46.6% × $1,639 = **$764 share** — KK/AA single-suited Rule-4-bot is the largest sub-stratum (open)
  - **two_pair**: 22.3% × $1,037 = **$231 share** — already gated + capacity-improved
  - **trips**: 5.5% × $1,359 = **$75** — both v30 and v32 have shipped; further work needs new diagnostic angles
  - three_pair: 1.9% × $1,639 = $31 (untouched by gating)
  - trips_pair: 2.86% × $1,225 = $35 (already gated)
  - composite: 0.245% × $1,386 = $3.4 (already gated)
- **Rule 6's heuristic capture is 56% of its oracle ceiling.** Closing the remaining 44% ($86/1000h on the trips slice = $5/1000h whole-grid given 5.5% share) requires probe-driven A-vs-C tiebreaking, an open v34_rule6_v2 candidate.

---

## What Session 37 produced

### v32 ship + Rule 6 verification + v33 ship

**1. v32 trained and shipped** — 83 features (v30's 79 + 4 trips_v2 round-2) at v31's high-capacity config (depth=32, min_samples_leaf=3). 731,606 leaves. **−$20 full / −$18 prefix vs v31; −$79 full / −$47 prefix cumulative vs v30.** All categories except trips bit-identical (textbook gating signature). 9th gating-template instance, FIRST within-trips iteration.

**2. Rule 6 verification** (`verify_rule6_v14_trips.py`): v14_combined picks "mid is paired with trip rank" on only 94.3% of pure trips. 5.4% B-routings (3rd trip on bot) systematically lose $3,609/1000h within-trips ($197 whole-grid). Always-A∪C oracle ceiling = $197/1000h whole-grid over v14.

**3. v33_rule6_trips designed and shipped** (`strategy_v33_rule6_trips.py`):
- Decision tree: trip_rank > max_kicker → C variant; else → A variant.
- Within A: pick which trip → bot to maximize bot DS profile.
- Override-everything semantics (within-rule scope) — captured $111 vs preserve-A∪C-when-good's $37 on the 30K probe.
- **Full grid: +$112/1000h vs v28** (trips $4,054 → $2,010 within-trips).
- **Prefix: +$143/1000h vs v28** (trips $4,576 → $1,744 within-trips).
- Largest single rule ship in project history; subsumes the prior Rule 4 (extended) for KKK/AAA.

### Methodology lessons reinforced (Session 37)

1. **Orthogonal axis stacking works.** Capacity + features compose additively (v32 = $58 v31 capacity + $20 trips_v2 features = $79 cumulative).
2. **Always-X structural baselines surface big rule ships.** Rule 6 → +$112-143/1000h. Apply systematically to remaining categories next session.
3. **Rule heuristics override learned strategy within scope.** Override-everything beats preserve-when-already-OK by 3× on the trips slice.
4. **Tripwire conversion rate continues to be ~10-15% on round-2 features.** 7 ships now confirm.

---

## Resume Prompt (Session 38)

```
Resume Session 38 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (last updated end of Session 37 — Session 37 entry
  in Part 1 covers BOTH v32 and v33 ships; Part 6 has Rule 6)
- CURRENT_PHASE.md (rewritten end of Session 37)
- DECISIONS_LOG.md (latest: Decision 067 v32 ship, Decision 068 v33 ship)
- analysis/scripts/strategy_v32_dt.py — current ML champion
- analysis/scripts/strategy_v33_rule6_trips.py — current human champion
- analysis/scripts/verify_rule6_v14_trips.py — diagnostic that surfaced Rule 6
- analysis/scripts/probe_v33_trips.py — fast empirical check (3s on 30K trips)

State (end of Session 37):
- v32_dt is the new ML champion: $1,715/1000h on full grid (51.31% opt),
  $904/1000h on prefix (62.47% opt). 731,606 leaves, depth=32, ml=3,
  83 features (79 v30 + 4 trips_v2 round-2).
- Cumulative v30→v32 of -$79/1000h on full grid is the largest single-
  session ML ship in project history (beats v26's $70).
- v33_rule6_trips is the new human strategy of record: $2,920/1000h on
  full grid (40.68% opt), $1,894/1000h on prefix (48.81% opt).
  +$112 vs v28 on full, +$143 on prefix. Largest single rule ship in
  project history.

Next session targets (priority order):

(A) Capacity sweep at v32's higher feature count (depth=34 ml=2 + ml=3
    control). Per Session 37 methodology rule, leaf-count grew +5% over
    v31; the next ship that adds ≥6 features should re-test capacity
    explicitly. Could potentially unlock $10-30/1000h.

(B) Always-X structural baseline probes for remaining categories. Rule 6
    came out of the trips diagnostic. Apply the same pattern to:
    - composite (high per-category regret, tiny share)
    - three_pair (untouched by gating, 1.9% share)
    - high_only (largest residual share, 20.4%)
    - two_pair (heavily ML-engineered already)
    Write `verify_rule_X_<category>.py` for each; ship if probe shows
    measurable gain.

(C) v34_rule6_v2 — tighter A-vs-C heuristic on probe-driven decision
    tree. Captures additional $10-50/1000h on the trips slice (=
    $0.5-3/1000h whole-grid). Smaller than (A) and (B); deprioritize.

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
  `trips_v2_*_g` (trips round 2 — shipped in v32). Archived: `pair_r4v3_*_g`.
- Methodology rule (Session 36+37): default future ML champion ships
  to depth=32 ml=3. Re-test capacity (depth=34 ml=2) when feature count
  grows substantially or when a ship has bearish tripwire AND leaf-count
  gain ≤10K.
- Methodology rule (Session 37): rule chains should default to override-
  everything within scope, not just patch mistakes.
- Methodology rule (Session 37): always-X structural baselines surface
  big rule ships. Apply systematically to remaining categories.
- Methodology rule (Session 36+37): tripwire predicts conversion rate
  (~10-15%), not absolute opportunity. 7 ships now confirm.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
