# Current: Sprint 8 — Session 80 M2 produced DECISIVE A-path verdict (v49_a1 lifts N=1000 match rate +13.15pp to 80.19%; v49_c2 NO LIFT at 64.92%); per-category lift profile mirrors S79's overfitting profile exactly (trips_pair +20.78pp, two_pair +18.43pp, quads +17.91pp); **S81 runs A2: generate N=1000 oracle labels for two_pair + trips_pair (1.51M hands, ~24-36 hr local compute), retrain v49_a2 on hybrid labels with held-out validation, settle the in-sample-evaluation caveat AND produce a real ship candidate**

S80 forked the v44 training pipeline twice with one knob each. A1 swapped the first 500K rows of training labels to N=1000 (cleaner) and kept v44's hyperparameters. C2 kept v44's labels (N=200) and regularized to max_leaf_nodes=500K with min_samples_leaf=5. A single vectorized grader compared all three (v44, v49_a1, v49_c2) against both oracle grids.

**Decision matrix outcome — Only A1 lifts (pre-committed threshold ≥70% N=1000 match rate):**

| Model | match% (N=200, 6M) | match% (N=1000, 500K) | $/1000h N=200 | $/1000h N=1000 |
|---|---:|---:|---:|---:|
| v44_dt (baseline) | 64.43% | 67.05% | +$1,081 | +$686 |
| **v49_a1_dt** (label noise) | 63.44% (−0.99pp) | **80.19% (+13.15pp)** | +$1,108 (+$27) | +$375 (−$311) |
| v49_c2_dt (regularize) | 52.19% (−12.24pp) | 64.92% (−2.13pp) | +$1,553 (+$472) | +$791 (+$105) |

**Per-category lift profile (v49_a1 vs v44 on N=1000 prefix 500K):**

| Category | n | v44 m% | **v49_a1 Δ** | v49_c2 Δ | (S79 shift) |
|---|---:|---:|---:|---:|---:|
| pair | 215,162 | 69.09% | **+8.76pp** | −0.28pp | +2.10pp |
| two_pair | 204,275 | 66.76% | **+18.43pp** | −3.60pp | −13.69pp |
| trips | 25,245 | 56.57% | **+11.08pp** | −2.15pp | −4.65pp |
| **trips_pair** | 25,943 | 63.15% | **+20.78pp** | −8.44pp | −19.43pp |
| three_pair | 25,614 | 67.73% | +2.16pp | +0.79pp | +1.59pp |
| **quads** | 1,100 | 65.27% | **+17.91pp** | +0.09pp | −12.82pp |
| composite | 2,661 | 55.69% | **+11.31pp** | −5.37pp | −9.62pp |

**The A1 per-category lift correlates with S79's per-category overfitting profile.** trips_pair, two_pair, quads — the categories S79 flagged as most-overfit to N=200 noise — are the categories with the largest A1 lifts. This is the load-bearing inference of S80: label noise is concentrated where S79 said it was, and A2's targeting (two_pair + trips_pair) addresses 25% of grid mass while capturing the largest expected N=1000 marginal value.

**Decision 115 (S80): A1 wins decisively. C2 NULL. S81 = A2 (targeted N=1000 expansion on two_pair + trips_pair + held-out validation).**

**Critical caveat acknowledged in Decision 115:** v49_a1's N=1000 match rate was measured on the same 500K hands used as training labels. Some fraction is in-sample memorization. Three convergent-evidence arguments (full-grid N=200 invariance / per-category alignment with S79 profile / broadly-distributed bucket lifts) make the A2-for-S81 decision robust despite this defect. S81 A2 protocol MUST include held-out N=1000 validation to settle it rigorously.

> **🎯 IMMEDIATE NEXT ACTION (Session 81): A2 — Generate N=1000 oracle labels for two_pair + trips_pair (~1.51M hands, ~24-36 hr local compute), retrain v49_a2 on hybrid labels with held-out validation, produce a real ship candidate**
>
> The total session 81 wall-clock is dominated by oracle generation. Most of the work is launching the oracle job correctly and writing the held-out validation harness while it runs.
>
> 1. **(PHASE 1 — ~10 min)** Confirm S80 commit/push state; verify the existing engine oracle-grid CLI can accept a category-mask flag (or write a thin wrapper that filters canonical hands to two_pair + trips_pair before launch). Document the exact command + estimated wall time + estimated disk footprint.
>
> 2. **(PHASE 2 — ~30 min, oracle launch + held-out selection)** Decide held-out set:
>    * Strategy: from the 1,510,080 two_pair + trips_pair canonical_ids, reserve every 10th by index (151,008 hands ≈ 10%) as the held-out validation set. The other 1,359,072 enter v49_a2 training Y.
>    * Persist the held-out canonical_id list to `data/session81/v49_a2_holdout_ids.bin` (or .npy).
>    * **The oracle MUST generate labels for ALL 1.51M hands** — both training (1.36M) and held-out (151K) get N=1000 labels. The held-out designation only excludes them from v49_a2's training Y.
>    * Launch the N=1000 oracle generation in the background (Bash run_in_background with a Monitor). Pre-stash the expected wall-time estimate so subsequent sessions can pick up cleanly.
>
> 3. **(PHASE 3 — ~30 min, harness while oracle runs)** Write `analysis/scripts/train_v49_a2_dt.py`:
>    * Fork `train_v49_a1_dt.py`.
>    * Build Y as a three-zone hybrid:
>      - Zone 1 (first 500K from existing prefix grid): N=1000 labels (unchanged from A1).
>      - Zone 2 (training two_pair + trips_pair canonical_ids, ≈1.36M): N=1000 labels (newly generated).
>      - Zone 3 (everything else, ≈3.5M): N=200 labels.
>    * Hyperparameters: depth=36, min_samples_leaf=1 (v44/A1 identical).
>    * Output: `data/v49_a2_dt_model.npz`.
>
> 4. **(PHASE 4 — ~20 min, harness while oracle runs)** Write `analysis/scripts/grade_v49_a2_holdout.py`:
>    * Three sweeps:
>      - vs N=200 full grid (6M): production-baseline regret + match (the +$10 ship bar lens).
>      - vs N=1000 prefix grid (500K): same lens as S80.
>      - vs N=1000 held-out set (151K): the OUT-OF-SAMPLE test that settles the memorization question.
>    * Per-category + per-bucket decomposition on each.
>    * Pre-committed ship verdict:
>      - **SHIP v49_a2** if: held-out N=1000 match rate ≥ 75% AND N=200 regret within $50 of v44.
>      - **NULL v49_a2** if: held-out N=1000 match rate < 72% (essentially v44-level).
>      - **MIXED** if: held-out 72-75% — re-examine alongside A3.
>
> 5. **(PHASE 5 — overnight to 36 hr)** Oracle generation runs. The session may end here and resume in S82 if oracle isn't done — that's fine. Capture launch metadata in `data/session81/oracle_launch.json`.
>
> 6. **(PHASE 6 — when oracle done, may be S82+ depending on wall time)** Train v49_a2 (~15-20 min). Grade against three lenses. Declare ship verdict per pre-committed thresholds. Decision 116. Rewrite CURRENT_PHASE.md.
>
> ACCEPTANCE for Session 81:
> - Held-out canonical_id list saved to `data/session81/v49_a2_holdout_ids.bin`.
> - Oracle N=1000 generation launched and confirmed running on 1.51M two_pair + trips_pair hands.
> - `train_v49_a2_dt.py` written + smoke-tested on dry-run with prefix labels only.
> - `grade_v49_a2_holdout.py` written + smoke-tested.
> - Decision 116 OR an interim status entry in DECISIONS_LOG.md acknowledging the launch.
> - CURRENT_PHASE.md updated with current oracle status + ETA.
>
> **+$10 ship bar APPLIES in S81/S82+** — this is the first session since S78 where a ship candidate is genuinely on the table. v49_a2 must clear it on the N=200 full grid (the production-baseline lens) AND validate out-of-sample on the held-out N=1000 set.
>
> **📓 METHODOLOGY (Session 81+):**
>
> 1. **The decision matrix worked exactly as designed in S80.** A1 cleared its threshold by 10pp; C2 missed by 5pp. The pre-committed matrix produced an unambiguous mechanical verdict for the first time in this cascade. Continue pre-committing in S81: write down what held-out match rate ≥/= what triggers ship/NULL/mixed BEFORE running the oracle, not after seeing the numbers.
>
> 2. **In-sample evaluation is a real defect, not a footnote.** S80's A1 +13.15pp was measured on training data; the held-out test in S81 either confirms it as real signal or unmasks it as memorization. Be willing to NULL the A-path if held-out lifts < +5pp — don't talk the data into shipping.
>
> 3. **Per-category targeting is the production lens.** S80 confirmed S79's per-category overfitting profile drives where the lift lives. A2 targets the two highest-leverage categories (two_pair, trips_pair). A3 (full N=1000 grid) is reserved unless A2 demonstrates the cleaner labels lift OOSpaced, AND the residual gap warrants the 5-day-vs-1-day compute multiplier.
>
> 4. **Capacity lever is closed.** S75 (low-capacity boosting) NULL + S80 C2 (4.5× regularized DT) NULL + S78 (feature engineering) NULL together close the capacity-and-features lane at v44's saturating regime. Label quality is the remaining live lever.
>
> 5. **"Speed is not necessary — clarity and perfection is."** Honored in S80; reaffirmed in S81. The oracle generation will take 24-36 hr. Don't shortcut it (e.g. by running at N=500 instead of N=1000) — the answer depends on label quality being meaningfully cleaner than the existing N=200, and N=200→N=500 may not be enough delta to discriminate. N=1000 is the established benchmark.
>
> 6. **Free-compute moves continue.** While oracle runs, finish the entire S81 deliverable set: training script, grading script, held-out validation harness, pre-committed ship verdict. When oracle completes (S82?), grading is one command away.

> **✅ ARTIFACTS produced in S80:**
> 1. `analysis/scripts/train_v49_a1_dt.py` — A1 training script.
> 2. `analysis/scripts/train_v49_c2_dt.py` — C2 training script.
> 3. `analysis/scripts/grade_v49_experiments.py` — 3-way grader.
> 4. `data/v49_a1_dt_model.npz` (1.2 GB; 2,248,173 leaves, gitignored).
> 5. `data/v49_c2_dt_model.npz` (337 MB; 500,000 leaves, gitignored).
> 6. `data/session80/grade_v49_experiments_summary.json` (6.0 KB, gitignored).
> 7. `data/session80/train_v49_a1.log`, `train_v49_c2.log`, `grade_v49_experiments.log` (gitignored).
> 8. `SESSION_80_M2_REPORT.md` — Phase 1-6 report including plain-language TL;DR.
> 9. `DECISIONS_LOG.md` — Decision 115 (A1 wins + A2 plan for S81 with held-out validation).
> 10. `CURRENT_PHASE.md` — rewritten for S81 (this file).

> Updated: 2026-05-13 (Session 80 end — M2 parallel A1 + C2 experiments completed; A1 lifts N=1000 match rate from 67.05% to 80.19% (+13.15pp) with only −0.99pp N=200 cost, per-category lifts concentrated in trips_pair / two_pair / quads exactly matching S79's overfitting profile; C2 NULL with −2.13pp on N=1000 and −12.24pp on N=200 closing the capacity-shrinkage lever; pre-committed decision matrix unambiguously selects A-path, Decision 115 records A1 verdict + S81 = A2 plan; critical in-sample-evaluation caveat acknowledged and addressed by S81's held-out validation protocol. **No production state change in S80 — ninth consecutive UNCHANGED session.** S81 plan: A2 = generate N=1000 oracle labels for 1.51M two_pair + trips_pair hands, reserve 151K (10%) as held-out validation, train v49_a2 on hybrid labels (N=1000 where it exists / N=200 elsewhere), grade on three lenses (N=200 full / N=1000 prefix / N=1000 held-out); pre-committed ship verdict: ship if held-out match ≥75% AND N=200 regret within $50 of v44, NULL if held-out match <72%, MIXED in between; estimated wall time ~24-36 hr local compute for the oracle, ~15-20 min for the train/grade. +$10 ship bar REAPPLIES in S81/S82+.)

---

## Headline state at end of Session 80

**Strategies of record (UNCHANGED for the NINTH consecutive session):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion. $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S80 — pure measurement session; no shipping candidate validated yet).

**S80 candidates (measurement-only, NOT production):**

| Candidate | Hyperparams | match% N=200 | match% N=1000 | $/1000h N=200 | $/1000h N=1000 |
|---|---|---:|---:|---:|---:|
| v49_a1_dt | depth=36, ml=1, N=1000 labels on prefix 500K | 63.44% | 80.19% | +$1,108 | +$375 |
| v49_c2_dt | depth=36, ml=5, max_leaf_nodes=500K, N=200 labels | 52.19% | 64.92% | +$1,553 | +$791 |

**Pre-committed decision matrix (from S80 Phase 5):**
* Both lift → S81 = M1 hybrid.
* Only A1 lifts → **S81 = A2 (targeted N=1000 on two_pair + trips_pair) ← CHOSEN**
* Only C2 lifts → S81 = C1 (high-capacity boosting).
* Neither lifts → headline-goal recalibration.

---

## Hypothesis cascade status (updated after S80)

| Hypothesis | Description | Status |
|---|---|---|
| H1 | high_only SS+ms route quality | NULL ship +$5 (S73). |
| H2 | high_only route-tradeoff | CLEAN NULL +$0 (S74). |
| Option B (S75) | Gradient boosting at depth=6 / n_est=200 | DECISIVE NULL −$1,392/1000h. |
| S76 / S77 diagnostics | Cross-cat → pair drill | Shipped diagnostics; identified H6/H7/H8. |
| H6 / H7 / H8 (S78) | Pair gated features | CLEAN NULL +$2 prefix. |
| Single-model ML feature-engineering track | At v44 saturating regime | FORMALLY CLOSED (Decision 113). |
| S79 label-noise measurement | Existing N=1000 prefix vs N=200 full | MIXED — 32% oracle disagreement reveals criterion blind spot (Decision 114). |
| **A1 (S80)** | Retrain v44 DT on N=1000 prefix labels (N=200 elsewhere) | **LIFTS +13.15pp on N=1000 match rate; in-sample evaluation caveat acknowledged (Decision 115).** |
| **C2 (S80)** | Regularize v44 DT (max_leaf_nodes=500K, ml=5) | **NULL −2.13pp on N=1000, −12.24pp on N=200 (Decision 115).** |
| **A2 (S81)** | Targeted N=1000 expansion on two_pair + trips_pair + held-out validation | **PRIORITIZED — primary work for S81/S82+.** |
| A3 | Full 6M-hand N=1000 grid | Reserved — run only if A2 demonstrates held-out lift AND residual gap warrants 5× compute multiplier. |
| C1 | High-capacity boosting (depth=10-12, n_est=1000-2000) | DEPRIORITIZED — S75 NULL + S80 C2 NULL together close the capacity lever. |
| M1 | Hybrid: regularized DT trained on N=1000 prefix labels | DEPRIORITIZED — C2's NULL means hybrid C-side adds no value over pure A-side. |
| Option D | Rule-chain extension on S77 LOW pair findings | DORMANT — pair is the least-overfit category; deprioritized vs A2's per-category targeting. |

**Cascade verdict (updated post S80):** A-path is empirically confirmed by S80's A1 result. C-path is empirically closed by S75 NULL + S80 C2 NULL. S81 is the first session since S78 with a real ship candidate on the table.

---

## Resume Prompt (Session 81 — A2: targeted N=1000 expansion + held-out validation)

```
Resume Session 81 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S80 — S81 runs A2: targeted
  N=1000 expansion on two_pair + trips_pair with held-out validation)
- SESSION_80_M2_REPORT.md (S80 M2 A1+C2 verdict; A1 LIFTS +13.15pp;
  C2 NULL; per-category lift profile mirrors S79 overfitting profile)
- DECISIONS_LOG.md (latest: Decision 115 — A1 wins + A2 plan + ship
  verdict pre-committed)
- analysis/scripts/train_v49_a1_dt.py (template for v49_a2 to fork)
- analysis/scripts/grade_v49_experiments.py (template for v49_a2 grader)

KEY DATA FILES (UNCHANGED from S80):
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/canonical_hands.bin — 6M canonical 7-card hands
- data/v44_dt_model.npz — production ML champion (baseline)
- data/v49_a1_dt_model.npz — S80 A1 model (label-noise lever) — 1.2 GB
- data/v49_c2_dt_model.npz — S80 C2 model (regularization lever) — 337 MB
- data/session80/grade_v49_experiments_summary.json — S80 grading summary

STATE (end of S80):
- v44_dt match% N=200: 64.43% / N=1000: 67.05%
- v49_a1_dt match% N=200: 63.44% (−0.99pp) / N=1000: 80.19% (+13.15pp)
- v49_c2_dt match% N=200: 52.19% (−12.24pp) / N=1000: 64.92% (−2.13pp)
- v49_a1 per-category lifts: trips_pair +20.78pp, two_pair +18.43pp,
  quads +17.91pp, composite +11.31pp, trips +11.08pp, pair +8.76pp
- Production: v56_trips_hybrid ($1,429 full / $794 prefix) + v44_dt
  ($1,081 full / $686 prefix). UNCHANGED for ninth consecutive session.
- Decision 115: A1 wins decisively (LIFTS), C2 NULL; S81 = A2.

USER DIRECTIVE (S80 end-of-session):
- "Speed is not necessary — clarity and perfection is."
- +$10 ship bar REAPPLIES in S81/S82+ — v49_a2 is the first real ship
  candidate since S78.
- Continue the held-out validation protocol — the in-sample evaluation
  caveat from S80 must be settled before any S82+ ship decision.

DIRECTION FOR SESSION 81 — A2: targeted N=1000 expansion on two_pair +
trips_pair with held-out validation:

  PHASE 1 (~10 min) — Confirm S80 commit/push state; read S80 report
    + Decision 115. Inspect engine/src/oracle_grid.rs (or similar) to
    determine the CLI for running oracle generation on a subset of
    canonical hands.

  PHASE 2 (~30 min) — Held-out selection + oracle launch.
    Build the two_pair + trips_pair canonical_id list (1,510,080
    hands) from data/canonical_hands.bin using the category functions
    in analysis/src/tw_analysis/grade_strategy.py. Reserve every 10th
    (151,008) as held-out. Save the held-out canonical_id list to
    data/session81/v49_a2_holdout_ids.npy.
    Launch oracle N=1000 generation on the full 1.51M list (NOT
    minus the held-out — the held-out hands ALSO need N=1000 labels,
    they're just excluded from v49_a2's training Y). Run in background.

  PHASE 3 (~30 min, while oracle runs) — Write
    analysis/scripts/train_v49_a2_dt.py. Fork train_v49_a1_dt.py.
    Build Y as three-zone hybrid:
      Zone 1: first 500K from existing prefix grid → N=1000.
      Zone 2: training two_pair + trips_pair (~1.36M) → N=1000.
      Zone 3: everything else (~3.5M) → N=200 (unchanged).
    Hyperparams identical to v44/A1 (depth=36, ml=1).
    Output: data/v49_a2_dt_model.npz.

  PHASE 4 (~20 min, while oracle runs) — Write
    analysis/scripts/grade_v49_a2_holdout.py with three lenses:
      - vs N=200 full grid (6M): production-baseline regret + match.
      - vs N=1000 prefix grid (500K): same lens as S80.
      - vs N=1000 held-out set (151K): OUT-OF-SAMPLE test.
    Per-category + per-bucket decomposition on each.
    Pre-committed ship verdict:
      SHIP v49_a2 if held-out N=1000 match ≥75% AND N=200 regret
        within $50 of v44.
      NULL v49_a2 if held-out N=1000 match <72%.
      MIXED if held-out 72-75% → re-examine alongside A3.

  PHASE 5 (overnight to 36 hr) — Oracle generation runs.
    Capture launch metadata in data/session81/oracle_launch.json.
    Session may end here; resume in S82 when oracle done.

  PHASE 6 (when oracle done; may be S82+) — Train v49_a2.
    Grade on three lenses. Declare ship verdict.
    Decision 116. SESSION_82_*.md. Rewrite CURRENT_PHASE.md.

  ACCEPTANCE for Session 81:
  - data/session81/v49_a2_holdout_ids.npy saved.
  - Oracle N=1000 generation launched + confirmed running on 1.51M
    hands.
  - train_v49_a2_dt.py written + smoke-tested.
  - grade_v49_a2_holdout.py written + smoke-tested.
  - Decision 116 OR interim launch-status entry in DECISIONS_LOG.md.
  - CURRENT_PHASE.md updated with current oracle status + ETA.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo (the engine binary may need a build
  first; check engine/Cargo.toml for the oracle-grid subcommand).
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- v44_dt model + features remain unchanged.
- +$10 ship bar APPLIES in S81/S82+ — v49_a2 must clear it on the
  N=200 full grid AND validate out-of-sample on held-out N=1000.
- "Speed is not necessary — clarity and perfection is."
- The user is non-technical; the session report should open with a
  plain-language summary of (a) oracle launch status + ETA, (b) the
  held-out protocol, (c) when the ship verdict is expected.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
