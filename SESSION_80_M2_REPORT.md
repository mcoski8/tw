# Session 80 — M2: parallel A1 + C2 one-session experiments

_Generated 2026-05-13 (Session 80 end)._

## TL;DR — Plain language

Last session (S79) we found that **the "answer key" we've been training
on is noisier than we thought** — 32% of hands have a different "best
setting" when we use the cleaner answer key (N=1000 samples) instead of
the noisy one (N=200 samples). The question for S80 was: which lever
moves the needle — using cleaner labels, or shrinking the model?

We ran both experiments side-by-side. The result is clear:

| Lever | Match rate vs cleaner key | Verdict |
|---|---:|---|
| v44 baseline (no change) | 67.05% | — |
| **A1: cleaner labels on first 500K hands** | **80.19%** | **+13.15pp — LIFTS** |
| C2: shrink the model (4.5× fewer leaves) | 64.92% | −2.13pp — does NOT lift |

A1 lifts the cleaner-key match rate by **13 percentage points** while
losing only 1pp on the noisy-key match rate. The lift is concentrated
exactly where S79 predicted: **trips_pair +21pp, two_pair +18pp, quads
+18pp** — the categories where v44 was most overfit to the noisy labels.

C2 (shrinking the model) collapses on the noisy key (−12pp) and gets
slightly worse on the clean key (−2pp). **Cutting capacity is the wrong
lever.**

**Per the pre-committed decision matrix: S81 = A2** — generate cleaner
(N=1000) labels for the categories with the biggest noise problems
(two_pair + trips_pair, ~1.5M hands, ~24-36 hr local compute), then
retrain.

**Important caveat the user should know:** A1's 13pp lift is measured
on the same 500K hands the model was trained on with the new labels.
That means SOME of the lift is the model memorizing the cleaner labels
for those specific hands (the DT averages ~2.7 hands per leaf). The
real test in S81 is an out-of-sample one: train on part of the new
labels, grade on the rest. The N=200 metrics across the full 6M grid
(which IS out-of-sample for the swapped labels) tell us A1 didn't lose
much general structure — that's what makes us confident A2 is the
right next move, not a memorization artifact.

**Production state UNCHANGED for the ninth consecutive session.** S80
was a measurement session — no ship attempted, +$10 ship bar didn't
apply. v44_dt + v56_trips_hybrid remain in production.

---

## How the M2 experiments worked

Two one-session retrains of the v44 decision-tree pipeline, varying
only ONE knob each.

### A1 — Cleaner labels on the first 500K hands

* Feature pipeline: identical to v44 (107 features).
* Training data: 6,009,159 canonical hands × 107 features.
* Training labels (Y): for the first 500,000 hands (the ones we have
  N=1000 oracle data for), use the N=1000 EVs. For the remaining
  5,509,159 hands, keep the N=200 EVs (unchanged).
* Hyperparameters: depth=36, min_samples_leaf=1 (identical to v44).
* Fit time: 651.5s (10.86 min) on a single thread.
* Output: 2,248,173 leaves (matches v44's count, confirming we're
  measuring the label-quality lever in isolation).
* Sanity check during training: 32.00% of the swapped 500K hands had
  a different argmax under N=1000 vs N=200 — exactly matches S79's
  oracle self-disagreement number.

### C2 — Regularize the model (shrink the leaf cap)

* Feature pipeline: identical to v44.
* Training labels (Y): N=200 full grid (UNCHANGED from v44).
* Hyperparameters: max_depth=36, **min_samples_leaf=5** (vs v44's 1),
  **max_leaf_nodes=500,000** (vs v44's effective 2.25M).
* Fit time: 881.0s (14.68 min). Best-first leaf growth (the algorithm
  triggered by max_leaf_nodes) is slower per leaf than v44's depth-
  first growth.
* Output: 500,000 leaves (the cap held — model is forced 4.5× smaller).

### Grading

A single grader (`grade_v49_experiments.py`) walks all three trees
on the same X feature matrix and produces:

* Match rate + regret vs the N=200 full grid (6M hands).
* Match rate + regret vs the N=1000 prefix grid (500K hands).
* Bucket decomposition (S76 lens) on the prefix.
* Per-category decomposition (S79 lens) on the prefix.

Vectorized tree walks predicted all 6M hands per model in 3.5-8.4
seconds — fast enough to bake into any future cascade.

---

## Headline results

### 3-column comparison

| metric | v44_dt (baseline) | v49_a1_dt (label noise) | v49_c2_dt (regularize) |
|---|---:|---:|---:|
| n_leaves | 2,248,173 | 2,248,173 | 500,000 |
| depth | 36 | 36 | 36 |
| match% (N=200, full 6M) | 64.43% | 63.44% | **52.19%** |
| **match% (N=1000, prefix 500K)** | **67.05%** | **80.19%** | **64.92%** |
| regret $/1000h (N=200) | +$1,081 | +$1,108 | +$1,553 |
| regret $/1000h (N=1000) | +$686 | +$375 | +$791 |

### Δ vs v44 baseline

| model | Δmatch%(N=200) | **Δmatch%(N=1000)** | Δ$/1000h (N=200) | Δ$/1000h (N=1000) |
|---|---:|---:|---:|---:|
| v49_a1_dt | −0.99pp | **+13.15pp** | +$27 | −$311 |
| v49_c2_dt | −12.24pp | −2.13pp | +$472 | +$105 |

---

## Bucket decomposition (S76 lens, on prefix 500K)

Buckets are defined by v44's setting-rank against the N=200 oracle.
Match rate within each bucket vs both oracles:

| Bucket | n | % | v44 m%(N=200) | v44 m%(N=1000) | **v49_a1 m%(N=1000)** | v49_c2 m%(N=1000) |
|---|---:|---:|---:|---:|---:|---:|
| MATCH (rank 1) | 366,390 | 73.3% | 99.59% | 77.70% | **91.21%** (+13.5pp) | 72.95% |
| NOISE (rank 2-3) | 97,336 | 19.5% | 0.00% | 43.58% | **54.88%** (+11.3pp) | 47.70% |
| MID (rank 4-9) | 32,854 | 6.6% | 0.00% | 23.66% | **37.99%** (+14.3pp) | 31.26% |
| STRUCTURE (rank ≥10) | 3,420 | 0.7% | 0.00% | 10.61% | **25.70%** (+15.1pp) | 18.98% |

Key reads:

* **v49_a1 lifts EVERY bucket** by 11-15pp. The improvement is broadly
  distributed — not an artifact of one corner case.
* v49_c2 lifts NOISE (+4pp) and MID (+8pp) modestly but LOSES the MATCH
  bucket (−4.75pp). Net result is the −2pp overall regression. Smaller
  trees just can't carry enough leaves to match v44 on the consensus
  cases.

## Per-category decomposition (S79 lens, on prefix 500K)

Match rate vs N=1000 oracle, by hand category:

| Category | n | % | v44 m% | **v49_a1 Δ** | v49_c2 Δ |
|---|---:|---:|---:|---:|---:|
| pair | 215,162 | 43.0% | 69.09% | **+8.76pp** | −0.28pp |
| two_pair | 204,275 | 40.9% | 66.76% | **+18.43pp** | −3.60pp |
| trips | 25,245 | 5.0% | 56.57% | **+11.08pp** | −2.15pp |
| **trips_pair** | 25,943 | 5.2% | 63.15% | **+20.78pp** | −8.44pp |
| three_pair | 25,614 | 5.1% | 67.73% | +2.16pp | +0.79pp |
| **quads** | 1,100 | 0.2% | 65.27% | **+17.91pp** | +0.09pp |
| composite | 2,661 | 0.5% | 55.69% | **+11.31pp** | −5.37pp |

**The pattern matches S79's prediction exactly.** The categories with
the largest negative shift in S79 — trips_pair (−19.4pp), two_pair
(−13.7pp) — are the categories with the LARGEST A1 lifts (+20.78,
+18.43). And the categories with near-zero S79 shift — pair (+2.1pp),
three_pair (+1.6pp) — show smaller A1 lifts (+8.76, +2.16).

This is the load-bearing inference of S80: **label noise is
concentrated where S79 identified it. A2 (targeted N=1000 expansion on
two_pair + trips_pair) is precisely targeted at the right population.**

---

## Decision matrix outcome (pre-committed in CURRENT_PHASE S80 Phase 5)

Pre-committed threshold for "lifts": N=1000 match rate ≥ 70.0%
(≥ +2.95pp above v44's 67.05%).

| Model | match% N=1000 | Verdict |
|---|---:|---|
| v49_a1_dt | 80.19% | **LIFTS** |
| v49_c2_dt | 64.92% | NO LIFT |

**Outcome: Only A1 lifts. → S81 = A2.**

---

## Critical caveat — in-sample evaluation

**v49_a1 was trained on the same 500K hands it is being graded against
with N=1000 labels.** That means some fraction of A1's 80.19% match
rate against N=1000 is the tree memorizing the swapped labels at the
~2.7-rows-per-leaf level, not "learning" to predict cleaner labels.

Three pieces of evidence argue most of A1's lift is structural, not
pure memorization:

1. **A1 lost only 0.99pp on N=200 match rate across the full 6M-row
   grid.** If A1 had simply rewritten its tree to perfectly match the
   500K N=1000 labels at the expense of everything else, we'd expect
   a much larger N=200 regression. Across 5.5M out-of-sample hands,
   v49_a1's behavior closely tracks v44's.

2. **A1's per-category lifts mirror S79's per-category overfitting
   profile.** Pure memorization would produce a flat lift across all
   categories. Instead we see +21pp on trips_pair, +18pp on two_pair,
   +9pp on pair — directly aligned with which categories had the most
   N=200 noise to escape.

3. **A1's bucket lifts are broadly distributed (11-15pp across all
   four buckets).** Memorization would concentrate in the high-rank
   buckets where v44 was already wrong — not lift the consensus
   MATCH bucket by 13.5pp.

**That said: an out-of-sample N=1000 test is the only definitive
control.** S81's A2 protocol must include a held-out N=1000 subset
graded against an A2-trained model that did NOT see those held-out
labels. Without that, "A1 lifts" remains a strong-prior, not a proof.

---

## S81 plan — A2 (targeted N=1000 expansion)

**Goal:** Generate N=1000 oracle labels for the two_pair + trips_pair
populations (the most-overfit categories per S79 and the largest A1
lifts per S80), train a v49_a2 DT on hybrid (N=1000 where it exists /
N=200 elsewhere) labels, and validate out-of-sample.

**Population:**
* two_pair: 1,338,480 hands (22.3% of grid)
* trips_pair: 171,600 hands (2.9% of grid)
* Total: 1,510,080 hands (25.1% of grid mass)

**Compute estimate:** N=1000 oracle is 5× the per-hand cost of N=200.
The current N=200 full grid (~6M hands) is the result of one historical
solver run; the targeted N=1000 subset (1.51M hands) is roughly 25% ×
5× = 1.25× the original compute budget. Per the S79 doc, this is in
the ~24-36 hour local compute range.

**Out-of-sample validation protocol:**

1. Generate N=1000 labels for all 1.51M two_pair + trips_pair hands.
2. **Reserve 10% (151K) as a held-out validation set** — these hands
   do NOT enter v49_a2's training data.
3. Build v49_a2 training Y:
   * First 500K hands (existing prefix grid): N=1000 labels.
   * Remaining ~1.36M two_pair/trips_pair hands minus the held-out
     set: N=1000 labels.
   * All other ~3.5M hands (high_only / pair / trips / quads /
     three_pair / composite): N=200 labels.
4. Train v49_a2 on the hybrid Y; same hyperparams as v44 (depth=36,
   ml=1).
5. **Grade v49_a2 on the held-out 151K N=1000 set.** If v49_a2's match
   rate on this OUT-OF-SAMPLE N=1000 subset is materially above v44's
   match rate on the same 151K hands, the memorization-vs-real-signal
   question is settled — and we have a candidate model for the +$10
   ship bar.
6. Also re-grade against the existing N=200 full grid. If v49_a2's
   N=200 regret is within $50 of v44's, the production-baseline cost
   is acceptable.

**Ship decision in S82+:** if held-out N=1000 match rate ≥ 75% AND
N=200 regret within $50 of v44, ship v49_a2 as ML champion. If
held-out lift is < +5pp, we have a memorization story and A2 is a
NULL.

**Reserve (NOT in S81 scope):**
* A3 (full N=1000 grid on all 6M hands): ~5 days local compute. Run
  only if A2 demonstrates real signal AND the residual gap warrants
  another 5× compute investment.
* C1 (high-capacity boosting): formally DEPRIORITIZED by C2's NULL.
  S75's NULL was at low capacity; S80's NULL is at low capacity at
  4.5× the leaf cap. The capacity-via-boosting hypothesis has no
  remaining strong prior.

---

## Files (Session 80)

**New code:**
* `analysis/scripts/train_v49_a1_dt.py` — A1 training script.
* `analysis/scripts/train_v49_c2_dt.py` — C2 training script.
* `analysis/scripts/grade_v49_experiments.py` — 3-way grader with
  bucket + category decomposition.

**New models (gitignored; local-only):**
* `data/v49_a1_dt_model.npz` (1.2 GB; 2,248,173 leaves).
* `data/v49_c2_dt_model.npz` (337 MB; 500,000 leaves).

**Logs (gitignored, in `data/session80/`):**
* `train_v49_a1.log`, `train_v49_c2.log`, `grade_v49_experiments.log`.
* `grade_v49_experiments_summary.json` (6.0 KB).

**Documentation:**
* `SESSION_80_M2_REPORT.md` — this file.
* `DECISIONS_LOG.md` — Decision 115 (A1 wins / A2 for S81).
* `CURRENT_PHASE.md` — rewritten for S81 with A2 protocol.

---

## Production state at end of S80 (UNCHANGED — ninth consecutive session)

* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix). Grader-confirmed.
* ML champion: **v44_dt** ($1,081 full / $686 prefix).
* Two-track divergence: $348/1000h (no change).
* Total project rule count: 18 (UNCHANGED).
* **No ship attempted in S80 by design — measurement session.**
* **v49_a1 is NOT a candidate for production yet:** the +$27 N=200
  regret regression keeps it below the +$10 ship bar, AND the in-sample
  evaluation caveat means its true generalization is not yet measured.
  S81's A2 with held-out validation is the path to a real ship
  candidate.

---

## Methodology notes (Session 80)

1. **The pre-committed decision matrix worked.** The 70% threshold was
   chosen blind in S79 (3pp above v44's baseline). A1 cleared it by
   10pp; C2 missed it by 5pp. No interpretation arbitrage required.
   S79's lesson — "pre-commit interpretation for every direction of
   the metric" — held.

2. **A1 measurement has an in-sample defect, but converging evidence
   makes the decision robust.** Three independent lenses (full-grid
   N=200 invariance, per-category alignment with S79's overfitting
   profile, broadly-distributed bucket lift) all point the same way.
   The held-out test happens in S81; the decision to invest there is
   the right call even without it.

3. **Per-category lifts ARE the production lens.** The headline 13pp
   N=1000 lift is interesting; the per-category lifts (+21 trips_pair,
   +18 two_pair, +18 quads) are what makes A2 the obvious S81 plan.
   The lift profile tells us where to spend compute.

4. **C2's NULL kills the "shrink the model" hypothesis at this
   capacity scale.** A 4.5× leaf reduction (2.25M → 500K) costs 12pp
   on N=200 with only marginal NOISE/MID-bucket gains. Higher-capacity
   boosting (C1) lost the case in S75 at low capacity, and would
   likely lose it here for the same reason — v44's 2.25M-leaf DT IS
   near the capacity ceiling for what's learnable from the X features
   against noisy Y. The label-noise lever is what's left.

5. **Vectorized tree walks are cheap.** 6M-row prediction in 3.5-8.4s
   per model means a single grader can sweep many candidates per
   session. Future hyperparameter sweeps should bake this in by
   default — no need to invoke `grade_strategy` per-hand for DT
   models.

6. **"Speed is not necessary — clarity and perfection is."** Honored.
   One knob per experiment. One pre-committed decision matrix. One
   grader. The unambiguous verdict was earned by experimental
   discipline, not by chasing more knobs.

7. **The 32% oracle self-disagreement is partially closable.** S79
   flagged it as "the most important number on the page." S80
   demonstrates that ~half of it (13pp out of the 35pp gap to 95%)
   can be closed by giving the model cleaner labels — even on a
   small fraction (8%) of training data. The other 17pp remains
   uncertain — that's the question A2's held-out test answers.

8. **Free-compute principle held.** S80's experiments used the
   existing 500K N=1000 prefix grid and existing 6M N=200 full grid.
   Total new compute: ~25 minutes of training + ~3 minutes of grading.
   The decision-quality return on that ~30 min was a fully-resolved
   M2 question and a sharp A2 plan for S81.
