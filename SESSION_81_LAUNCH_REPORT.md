# Session 81 — A2 launch: subset built, oracle running, harness shipped

_Generated 2026-05-14 (Session 81 end). The oracle is still running in the background; this report covers everything S81 produced. Session 82 will run the training + grading once the oracle completes._

## TL;DR — Plain language

Last session (S80) we found that retraining v44 on cleaner labels (N=1000 instead of N=200) on the first 500K hands lifted the "cleaner-key" match rate from 67% to 80%. The problem: that 80% was measured on the same 500K hands the model was trained on, so some unknown fraction was the model memorizing those specific hands' answers rather than learning a real pattern.

Session 81 set up the experiment that settles that question:

1. **Built a targeted subset.** We selected the **1,510,080 hands** in the two_pair + trips_pair categories — the two categories that S79 flagged as most overfit to noisy labels, and the two categories with the biggest A1 lifts in S80.

2. **Reserved a held-out set.** Of those 1.51M hands, we reserved **151,008 (every 10th)** as held-out. v49_a2 will NOT see these hands' answers during training. When we grade v49_a2 on the held-out hands' clean (N=1000) answers, we're asking it to predict the right setting for hands it never trained on with the cleaner labels — a fair test of whether the cleaner labels teach a real pattern.

3. **Launched the cleaner-labels-generator.** We started a background job that, over the next ~15 hours (faster than the 24-36 hour estimate), generates fresh N=1000 answers for all 1.51M hands. We pilot-tested it on the first 2,000 hands and confirmed it works correctly; the throughput is 28.5 hands/sec.

4. **Wrote and smoke-tested the next two scripts ahead of time.** While the oracle runs, we already wrote (a) the training script that combines the new clean labels with the existing data and (b) the grading script that compares v49_a2 to v44 on three different "answer keys" and **automatically declares ship/null/mixed against thresholds we locked in code today** (so when the data lands, there's no room to talk ourselves into a verdict).

**What happens next:** when the oracle finishes (estimated tomorrow morning Pacific), Session 82 runs two commands totaling ~18 minutes, the grader prints the verdict, and we either ship v49_a2 (first ML-champion change since v44 was committed) or NULL it and revisit whether the 95% match-rate goal is even reachable.

**Production state UNCHANGED for the tenth consecutive session.** S81 was a launch + harness session — no ship was attempted by design.

**Pre-committed verdict thresholds (in `analysis/scripts/grade_v49_a2_holdout.py`):**
- **SHIP v49_a2** if held-out N=1000 match% ≥ 75% AND |N=200 regret(v49_a2) − N=200 regret(v44)| ≤ $50/1000h.
- **NULL v49_a2** if held-out N=1000 match% < 72%.
- **MIXED** if 72-75% — reassess alongside A3 (full N=1000 grid) in S83+.

---

## What S81 produced (detailed)

### Subset construction — `analysis/scripts/build_s81_subset.py`

Categorized all 6,009,159 canonical hands using `tw_analysis.grade_strategy.categorize_hands`. Counts match the expected pre-committed numbers exactly:

| Category | Count | Expected | Match |
|---|---:|---:|:---:|
| two_pair | 1,338,480 | 1,338,480 | ✓ |
| trips_pair | 171,600 | 171,600 | ✓ |
| **Total target** | **1,510,080** | **1,510,080** | ✓ |

Selected every 10th subset index (offset 0) as held-out: **151,008 hands (10.000% of subset)**. Held-out category distribution mirrors the full subset within 0.04 percentage points (two_pair 88.68% vs 88.64% / trips_pair 11.32% vs 11.36%) — stratified sampling came for free from the deterministic stride.

Wrote the following artifacts to `data/session81/`:

| File | Size | Purpose |
|---|---:|---|
| `canonical_hands_s81_subset.bin` | 10.57 MB | canonical_hands.bin format; subset hands in original lex order. Fed to `tw-engine oracle-grid`. |
| `v49_a2_subset_to_canonical.npy` | 6.04 MB | uint32[1,510,080]; maps subset_index → full canonical_id. |
| `v49_a2_holdout_ids.npy` | 0.60 MB | uint32[151,008]; full canonical_ids of held-out hands. |
| `v49_a2_holdout_subset_indices.npy` | 0.60 MB | uint32[151,008]; subset positions of held-out hands (direct S81-grid lookup). |
| `v49_a2_subset_categories.npy` | 1.51 MB | int8[1,510,080]; per-row category for breakdown. |
| `build_summary.json` | <1 KB | Input/output sha256 + counts for downstream provenance. |

Wall time: ~5 seconds (one vectorized one-hot pass over 6M rows + five small writes).

### Oracle pilot + launch

**Pilot:** 2,000 hands at N=1000 on the subset file, block_size=500, opp=realistic. Output header validated: TWOG magic, samples=1000, opp=RealisticHumanMixture (tag 8), canonical_total=1,510,080. First-record argmax=76 ev=−5.265, last-record argmax=60 ev=−2.092.

Sustained throughput: **28.5 hands/sec** (blocks 17.41-17.72s each). Full-run ETA computed from pilot: (1,510,080 − 2,000) / 28.5 ≈ **52,915 s ≈ 14.7 hours**, materially faster than the 24-36 hour pre-launch estimate. The improvement comes from the subset being uniformly tp/3p (slightly faster eval profile than the full distribution).

**Full launch:** background task `b2nqj55g5`, command captured in `data/session81/oracle_launch.json`. Resume verified — engine detected the 2,000 records on disk and resumed at canonical_id=2,000. Block_size raised to 1,000 for the long run (slightly less syscall overhead than 500). Per-block log lines stream to `data/session81/oracle_full_run.log` with `rate=27.5 hands/s ETA=54580s` style output at S81 close.

### Training script — `analysis/scripts/train_v49_a2_dt.py`

Forked `train_v49_a1_dt.py`. Same 107-feature pipeline (`build_X` from `train_v44_dt`). Same hyperparameters: depth=36, ml=1, criterion=squared_error, random_state=42.

Y is a three-zone hybrid (mutually exclusive in canonical_id space):

| Zone | Range | Source | Size | Share of training |
|---|---|---|---:|---:|
| Zone 1 | canonical_id < 500,000 | `oracle_grid_prefix500k_n1000.bin` (N=1000) | 476,978 | 8.14% |
| Zone 2 | canonical_id ≥ 500,000 AND tp/3p AND not held-out | `data/session81/oracle_grid_s81_n1000.bin` (N=1000, NEW) | 1,151,876 | 19.66% |
| Zone 3 | everything else not held-out | `oracle_grid_full_realistic_n200.bin` (N=200) | 4,229,297 | 72.20% |

**N=1000 share of training labels = 27.80%** (vs 8.14% in v49_a1 — a 3.4× increase concentrated on the most-overfit categories).

Held-out rows (151,008) are dropped from both X_train and Y_train entirely. They retain N=1000 labels in the S81 grid for use during grading.

Smoke-tested without the S81 grid present (`--smoke-test` flag). Zone composition validated. Fit step skipped in smoke mode.

> **Implementation note — why Option B (zones are mutually exclusive in canonical_id space)** rather than Option A (S81 grid wins for tp/3p rows in the first 500K): both options yield statistically equivalent labels (both N=1000 RealisticHumanMixture, just different RNG seeds). Option B is the literal reading of the resume prompt and is auditable against earlier S80 decisions. The choice doesn't affect the ship-verdict logic — only the small fraction of tp/3p rows in the first 500K get a different RNG seed.
>
> **Implementation note — why Zone 1 has 476,978 rows instead of 500,000:** 23,022 held-out rows fall within the first 500K full-grid canonical_ids. The tp/3p density in the first 500K is ~46% (much higher than the overall 25%) because the canonical hand list is lex-sorted by packed card bytes, and that ordering concentrates tp/3p patterns in the early indices. Not a bug — just a quirk of the data exposed by the diagnostic print.

### Grading script — `analysis/scripts/grade_v49_a2_holdout.py`

Three lenses, all pre-committed:

| Lens | Source | Rows graded | Purpose |
|---|---|---:|---|
| Lens 1 | N=200 full grid | 6,009,159 (all) | Production-baseline regret + match. v49_a2 must hold within $50 of v44 to clear ship gate. |
| Lens 2 | N=1000 prefix grid (500K) | 500,000 | Same lens as S80. Lets us see if A2 retains A1's prefix gain. |
| **Lens 3** | **N=1000 S81 grid (held-out 151K)** | **151,008** | **OOS test. Settles the S80 in-sample evaluation question.** |

Held-out EVs fetched directly via subset positions (`gs.evs[holdout_subset_idx]`) — no per-row search. Per-category Lens-3 breakdown (two_pair vs trips_pair) printed automatically.

**Pre-committed ship verdict logic baked into the grader:**

```python
SHIP_HOLDOUT_MATCH_MIN     = 75.0   # %
SHIP_N200_REGRET_TOL_USD   = 50.0   # $/1000h above v44
NULL_HOLDOUT_MATCH_MAX     = 72.0   # %

if lens3_match_pct < NULL_HOLDOUT_MATCH_MAX:
    verdict = "NULL"
elif lens3_match_pct >= SHIP_HOLDOUT_MATCH_MIN \
        and abs(lens1_regret_dol - v44_lens1_regret_dol) <= SHIP_N200_REGRET_TOL_USD:
    verdict = "SHIP"
else:
    verdict = "MIXED"
```

The grader prints the verdict line and a one-sentence reason next to the numbers. This removes any interpretation arbitrage when the data lands.

Smoke-tested with v44_dt only (v49_a2 doesn't exist yet, S81 grid still generating). v44 reproduces its S80 numbers exactly:

| metric | v44_dt (S80 reported) | v44_dt (S81 smoke) | Match |
|---|---:|---:|:---:|
| match% (N=200, full 6M) | 64.43% | 64.43% | ✓ |
| match% (N=1000, prefix 500K) | 67.05% | 67.05% | ✓ |
| $/1000h (N=200) | +$1,081 | +$1,081 | ✓ |
| $/1000h (N=1000) | +$686 | +$686 | ✓ |

Plumbing for Lens 3 validated end-to-end via the held-out sidecar cross-check (`holdout_ids` == `subset_to_canonical[holdout_subset_idx]` at startup).

---

## What Session 82 will run

Once the oracle completes (estimated ~2026-05-15 morning Pacific):

| Phase | Wall | Action |
|---|---:|---|
| 1 | ~5 min | Verify oracle finished cleanly (`tail oracle_full_run.log`; expect ~611 MB output). |
| 2 | ~15-20 min | `python3 analysis/scripts/train_v49_a2_dt.py`. Output: `data/v49_a2_dt_model.npz` (~1.2 GB, gitignored). |
| 3 | ~3 min | `python3 analysis/scripts/grade_v49_a2_holdout.py`. Auto-fires SHIP/NULL/MIXED verdict. |
| 4 | ~30 min | Write `SESSION_82_REPORT.md` with plain-language TL;DR. Decision 117 records verdict. If SHIP: update `STRATEGY_GUIDE.md`. |
| 5 | ~5 min | Commit + push (pre-authorized per `feedback_taiwanese_commits` memory). |

**Total Session 82 wall ≈ 1 hour of work + ~15 hour wait for oracle (most of which spans the gap between sessions, not active work time).**

---

## Headline state at end of S81 (UNCHANGED — tenth consecutive session)

* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix). Grader-confirmed.
* ML champion: **v44_dt** ($1,081 full / $686 prefix).
* Two-track divergence: $348/1000h.
* Total project rule count: 18.
* **No ship attempted in S81 by design — oracle-launch + harness-prep session.**
* **v49_a2 is the first real ship candidate since S78.** Verdict deferred to S82.

---

## Methodology notes (Session 81)

1. **Empirical throughput pilot before overnight launch.** The 2,000-hand pilot took 70 seconds and produced a real ETA (14.7h) that beat the 24-36h estimate. The pilot's output is byte-identical to what the full run would have written for those rows, so no compute is wasted — the pilot IS the first 2,000 records of the real run. Right pattern for any multi-hour batch: brief pilot with the actual binary on the actual input always beats a wall-time model.

2. **Free-compute during the wait.** Wrote both downstream scripts and smoke-tested them while the oracle generates the data they consume. When the oracle completes, the entire remaining Session 82 workload is two commands plus interpretation. "Speed is not necessary — clarity and perfection is" cashes out here as "use the long wait for the careful work."

3. **Smoke-test without the real labels.** Both the trainer (`--smoke-test` skips DT fit + S81 grid read) and the grader (`--smoke-test` skips Lens 3 + v49_a2 model) ran cleanly. Trainer validated zone composition (8.14% / 19.66% / 72.20%). Grader reproduced v44's S80 numbers exactly, confirming the X pipeline and Lens 1/2 plumbing. The only thing untested is the part that requires the oracle to finish — which is unavoidable.

4. **Pre-committed verdict in code, not in a doc.** The grader has SHIP/NULL/MIXED thresholds hardcoded; it prints the verdict next to the numbers, with reasoning. Removes any interpretation arbitrage when the data lands.

5. **Resume-from-anywhere is the right batch-job pattern.** The engine's `OgWriter` detects existing records on disk and resumes at the next position. Pilot + full-run sequence proved this end-to-end. No state machine, no checkpoint files — just "open the output file, count the records, start there."

6. **Held-out sidecar redundancy is worth the storage.** Both `holdout_ids.npy` (full canonical_ids) and `holdout_subset_indices.npy` (subset positions) are stored. Either alone would suffice, but the redundancy lets each consumer pick the cheapest lookup path and lets the grader cross-check them at startup (which it does — a single line of safety that would have caught a silent shuffle bug).

7. **Stratification was free.** Held-out hands distribute 88.68% / 11.32% across two_pair / trips_pair, vs 88.64% / 11.36% in the full subset — within 0.04 percentage points of the population mean. Every 10th subset index gave us stratified sampling without explicit stratification logic.

8. **The 27.8% vs 8.1% leverage.** v49_a1 had 8.14% of training labels at N=1000 and produced a +13.15pp prefix match-rate lift (in-sample). v49_a2 has 27.80% at N=1000, concentrated on the two highest-overfit categories. If OOS Lens 3 match% on the held-out 151K beats ~72%, A2 has succeeded structurally; if it clears 75% with N=200 regret within $50 of v44, it ships.

---

## Files (Session 81)

**New code (committed):**
* `analysis/scripts/build_s81_subset.py` — subset + held-out construction.
* `analysis/scripts/train_v49_a2_dt.py` — three-zone hybrid trainer.
* `analysis/scripts/grade_v49_a2_holdout.py` — three-lens grader with pre-committed ship verdict.

**New artifacts (all gitignored under `data/session81/`):**
* `canonical_hands_s81_subset.bin` (10.57 MB; 1,510,080 hands).
* `v49_a2_subset_to_canonical.npy` (6.04 MB).
* `v49_a2_holdout_ids.npy` (0.60 MB).
* `v49_a2_holdout_subset_indices.npy` (0.60 MB).
* `v49_a2_subset_categories.npy` (1.51 MB).
* `build_summary.json`, `oracle_launch.json`.
* `oracle_grid_s81_n1000.bin` — IN PROGRESS, ~611 MB at completion.
* `oracle_full_run.log` — IN PROGRESS.
* `oracle_pilot.log`, `build_subset.log`, `train_v49_a2_smoke.log`, `grade_v49_a2_smoke.log`.

**Documentation:**
* `SESSION_81_LAUNCH_REPORT.md` — this file.
* `DECISIONS_LOG.md` — Decision 116 (interim launch + S82 plan).
* `CURRENT_PHASE.md` — rewritten for S82.
