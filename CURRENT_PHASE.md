# Current: Sprint 8 — Mining sprint complete. v14 is production. Next: DT regression on the grid.

> **🎯 IMMEDIATE NEXT ACTION (Session 27):** Two parallel tracks — (a) train a DecisionTreeRegressor on the full Oracle Grid using the v7-regression methodology (input = per-hand features, output = setting choice that maximizes grid-EV); (b) deploy v14 as the production strategy in any trainer or downstream tool that currently references v8_hybrid.

> **✅ SHIPPED (Decisions 044, 045, 046):** Full Oracle Grid + Query Harness + Strategy-Grading harness + 4 hand-coded rules (v9.1, v10, v12, v14) totaling +$1,014/1000h vs v8 (at N=1000 prefix fidelity).

> **🚫 ARCHIVED:** v11, v13, v15 — three high_only/trips simple-rule attempts that regressed. Multi-archetype categories don't yield to top-15-inspection-based rules; need DT/ML or much deeper discriminators.

> Updated: 2026-05-03 (end of Session 26)

---

## Headline state at end of Session 26

**v14_combined is the strategy of record.** It's the chain:
trips_pair (v12) → two_pair (v10) → single-pair (v9.2) → v8_hybrid fallback.

**Captured gain vs v8_hybrid:**
- At N=200 (full 6M grid): **+$120/1000h, +2.91 pp pct_optimal**
- At N=1000 (500K prefix grid): **+$1,014/1000h, +9.10 pp pct_optimal**

The N=200 grid was understating gains by ~8× due to MC noise. v14's true edge against the realistic 70/25/5 mixture is approximately $1,000/1000h ≈ $10 per hand.

**Cycle scoreboard (8 attempts, 4 ships, 3 regressions, 1 baseline-only):**

| Cycle | Target | Gain at N=200 | Status |
|---|---|---:|---|
| v9.1 | single pair (discriminator-tight) | +$24 | SHIPPED |
| v10  | two_pair (no-split) | +$81 incremental | SHIPPED |
| v11  | high_only (broad sacrifice-top) | −$1,745 | ARCHIVED |
| v12  | trips_pair (split trips, pair intact) | +$10 incremental | SHIPPED |
| v13  | trips (broad split-trips) | −$172 | ARCHIVED |
| v14  | single pair refine (v9.2) | +$5 incremental | SHIPPED |
| v15  | high_only DS-patch | −$296 | ARCHIVED |

---

## What's still on the table

| Category | $/1000h gap | Share | Total bleed | Status |
|---|---:|---:|---:|---|
| pair | $2,011 | 46.6% | $937 | mostly captured |
| high_only | $4,082 | 20.4% | $832 | 3 attempts failed; needs DT |
| two_pair | $3,371 | 22.3% | $752 | mostly captured |
| trips | $4,054 | 5.5% | $223 | 1 attempt failed; needs DT |
| trips_pair | $5,417 | 2.9% | $157 | mostly captured |
| three_pair | $4,529 | 1.9% | $86 | not attacked |
| quads | $9,670 | 0.2% | $19 | not attacked |
| composite | $10,883 | 0.2% | $22 | not attacked |

high_only + trips together = $1,055 of $3,033 remaining (35% of the gap). Cracking these is the biggest remaining opportunity.

---

## Methodology lessons (Decision 046 §"Methodology lessons")

1. **One-archetype categories** (two_pair, trips_pair) yield to top-15 inspection rules. One iteration suffices.
2. **Many-archetype categories** (high_only, trips) need a discriminator step BEFORE shipping a broad rule. Top-15 outliers are not representative; they show extreme wins for a narrow archetype that doesn't generalize.
3. **Simple rules hit diminishing returns.** v9.1=$24, v10=$81, v12=$10, v14=$5. To break out of this regime, need DT/regression or per-hand model.
4. **Prefix re-grade at N=1000 is a free sanity check.** Caught nothing wrong but tightened confidence dramatically.
5. **Run the grade harness on every candidate before shipping.** Three regressions (v11, v13, v15) would have been ship-time disasters; the grade caught them in 5-15 min each.

---

## What was built across Sessions 24-26

**Engine (Rust):**
- `oracle_grid.rs` — file format + writer + solver
- `opp_models.rs::opp_mfsuit_top_locked` — Decision 043 deterministic profile
- `monte_carlo.rs::OpponentModel::RealisticHumanMixture` — 70/25/5 dispatch
- `oracle-grid` CLI subcommand
- 141/141 tests pass

**Python harness:**
- `tw_analysis.oracle_grid` — reader + memmap + integrity check
- `tw_analysis.query` — vectorized features (~115 µs/hand) + filter combinators + `compare_setting_classes`
- `tw_analysis.grade_strategy` — score any deterministic strategy against the grid in ~4 min

**Strategies (in dependency chain order):**
- `strategy_v9_1_pair_to_bot_ds` — narrow pair-to-bot rule (DS-feasible, kicker symmetric, pair rank zone)
- `strategy_v9_2_pair_to_bot_ds` — extends v9.1 with (1,3)/(3,1) kickers
- `strategy_v10_two_pair_no_split` — never split a two-pair, enumerate 9 candidates
- `strategy_v12_trips_pair` — for trips_pair: split trips 2+1, pair intact, DS bot
- `strategy_v14_combined` — the production chain: v12 → v10 → v9.2 → v8

**Analysis scripts:**
- `find_worst_v8_two_pair.py` — generic top-N regret-finder (parameterizable by --category --strategy)
- `q4_inspect_top10.py`, `q4_characterize_b_wins.py`, `q4_discriminator_diagnostic.py` — Q4 (pair) analysis
- `high_only_archetype_discriminator.py` — high_only feature/archetype cross-tab
- `oracle_grid_full_queries.py` — Q1-Q5 user-locked questions on full grid
- `grade_*_full_grid.py` family — full-grid graders for each candidate
- `grade_against_prefix.py` — N=1000 prefix re-grade harness

**Compute artifacts (gitignored):**
- `data/oracle_grid_full_realistic_n200.bin` (2.55 GB) — full 6M grid at N=200
- `data/oracle_grid_prefix500k_n1000.bin` (212 MB) — 500K-prefix at N=1000

---

## Resume Prompt (Session 27)

```
Resume Session 27 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 26)
- DECISIONS_LOG.md (latest: Decision 046 — mining sprint summary)
- analysis/scripts/strategy_v14_combined.py — production strategy
- analysis/src/tw_analysis/grade_strategy.py — grading harness
- analysis/scripts/strategy_v7_regression.py — prior DT-regression precedent

State (end of Session 26):
- v14 is the production strategy of record at $3,033/1000h vs ceiling
  (full grid N=200) / $2,037 (prefix N=1000). +$120/1000h vs v8 at
  N=200, +$1,014/1000h at N=1000.
- 4 hand-coded rules shipped (v9.1, v10, v12, v14).
- 3 simple-rule regressions archived (v11, v13, v15) — high_only and
  trips have multiple optimal archetypes; simple rules over-fire.
- 141 Rust tests pass. Full grid + prefix grid on disk.

Two parallel tracks for Session 27:

(A) **DT regression v16.** Train an sklearn DecisionTreeRegressor on
    the full Oracle Grid using v7's prior methodology:
      - Input: per-hand features (pair_rank, suit_dist, broadway_count,
        longest_run, ace_present, etc. — see q4_discriminator_diagnostic.py
        for feature list).
      - Output: 105-EV vector (regression target) OR setting argmax.
      - Training data: full 6M canonical hands × N=200 (or N=1000
        prefix for tighter labels).
    Likely captures another $500-1000/1000h on multi-archetype categories.
    Reference: analysis/scripts/strategy_v7_regression.py — old DT
    that beat v3 by $445/1000h on the OLD 4-profile mixture.

(B) **v14 deployment.** Find every place v8_hybrid is referenced as
    "production" and update to v14_combined. Likely just trainer/src/
    and tournament_50k.py reference points. Sanity-check the trainer's
    setting-encoding round-trip works (Decision 041 str-sort bug
    must remain fixed).

Optional follow-ups:
(C) Investigate Q4 B-wins canonical_ids 425562, 3546583, etc. as
    targets for v9.3 refinement (multi-pair archetypes).
(D) Investigate suit_dist=(4,1,1,1) high_only sub-cluster (worst v8
    bleed at $5,500/1000h, no DS-feasible).
(E) Two_pair refinement — v10's tiebreak heuristics may not always
    match oracle on edge cases.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1 (Session 24 lesson).
- N=200 grades understate true gain by ~8× vs N=1000 prefix.
- 4-min full-grid grade is the validation gate; never ship a candidate
  that grades negative even on N=200.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
