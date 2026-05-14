# Current: Sprint 8 — Session 82 check-in confirmed oracle still running and healthy (~16h ETA remaining at S82 open); train + grade + ship-verdict deferred until oracle completes (estimated ~2026-05-15 ~00:30 CDT). Session 82 plan unchanged; resume same prompt when oracle is done.

**S82 check-in (2026-05-14 08:40 CDT) — read first:** Verified oracle process PID 4112 alive (851% CPU, RUNNING state), last log write fresh (17 seconds before check), file growing on disk. Progress at check-in: **28,000 / 1,508,080 records (1.86%)**, sustained rate **~25.8 hands/s** — slightly slower than the 28.5 hands/s pilot, but within 10%. **Updated ETA: ~57,336 s ≈ 15.9 hours from log time of 08:40**, putting oracle completion at ~**2026-05-15 00:35 CDT** — still consistent with the "morning of 2026-05-15 Pacific" window the S82 resume prompt was written for. **No train + grade run in this check-in by design** (oracle data not yet available). Production state UNCHANGED for the eleventh consecutive session by virtue of the oracle still running. **The S82 resume prompt below is unchanged and remains the correct prompt to use when the oracle finishes.**

---



S81 built the 1,510,080-hand two_pair + trips_pair subset, reserved 151,008 hands (every 10th) as held-out, ran a 2,000-hand N=1000 pilot to measure throughput (28.5 hands/sec), and launched the full N=1000 RealisticHumanMixture oracle in the background with empirical ETA ~14.7 hours from launch (materially faster than the 24-36 hour estimate). While the oracle runs, S81 wrote and smoke-tested both downstream scripts: `train_v49_a2_dt.py` (three-zone hybrid Y → DT fit) and `grade_v49_a2_holdout.py` (three-lens grader with pre-committed SHIP/NULL/MIXED verdict thresholds embedded in code). All S81 acceptance gates are met; the only blocker to declaring a ship verdict is the oracle finishing.

**Pre-committed ship verdict (hardcoded in `grade_v49_a2_holdout.py`):**
- **SHIP v49_a2** if Lens-3 (held-out N=1000) match% ≥ **75.0%** AND |Lens-1 (N=200 full) $/1000h(v49_a2) − $/1000h(v44)| ≤ **$50**.
- **NULL v49_a2** if Lens-3 match% < **72.0%**.
- **MIXED** if 72.0% ≤ Lens-3 match% < 75.0% (re-examine alongside A3 in S83+).

**Training-set zone composition (validated by smoke test):**

| Zone | Source | Hands | Share | What it covers |
|---|---|---:|---:|---|
| Zone 1 | N=1000 prefix grid | 476,978 | 8.14% | canonical_id < 500,000, not held-out |
| Zone 2 | N=1000 S81 grid (NEW) | 1,151,876 | 19.66% | canonical_id ≥ 500,000, tp/3p, not held-out |
| Zone 3 | N=200 full grid | 4,229,297 | 72.20% | everything else not held-out |
| **N=1000 share** | | **1,628,854** | **27.80%** | (vs 8.14% in A1; 3.4× cleaner-label coverage on the worst-overfit categories) |

> **🎯 IMMEDIATE NEXT ACTION (Session 82): wait for oracle, then train + grade**
>
> 1. **(PHASE 1 — ~5 min)** Verify oracle completed cleanly. The S81 oracle launched at 2026-05-14 08:22 with empirical ETA ~14.7 hours. By morning of 2026-05-15, run:
>    * `tail -5 data/session81/oracle_full_run.log` — expect a final `Done in <wall_time>. Wrote 1508080 records to data/session81/oracle_grid_s81_n1000.bin.` line.
>    * `ls -lh data/session81/oracle_grid_s81_n1000.bin` — expect ~611 MB.
>    * If oracle is still running, `tail -1` shows current ETA. If terminated mid-run, the resume command is idempotent: re-launch the exact command from `data/session81/oracle_launch.json` and it picks up at the next unwritten record.
>
> 2. **(PHASE 2 — ~15-20 min)** Train v49_a2:
>    ```
>    PYTHONUNBUFFERED=1 python3 -u analysis/scripts/train_v49_a2_dt.py \
>        --max-depth 36 --min-samples-leaf 1 \
>        --output data/v49_a2_dt_model.npz 2>&1 \
>        | tee data/session82/train_v49_a2.log
>    ```
>    Expect ~10-12 minutes fit time (similar to v49_a1's 10.86 min on same hyperparameters), ~2.25M leaves, ~1.2 GB output (gitignored).
>
> 3. **(PHASE 3 — ~3 min)** Grade on three lenses:
>    ```
>    PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v49_a2_holdout.py 2>&1 \
>        | tee data/session82/grade_v49_a2.log
>    ```
>    The grader prints:
>    * v44 vs v49_a2 2-column comparison on all three lenses.
>    * Per-category breakdown (two_pair vs trips_pair) on the OOS held-out lens.
>    * Δ versus v44 baseline.
>    * **Auto-fires the pre-committed SHIP/NULL/MIXED verdict.**
>    * Writes `data/session81/grade_v49_a2_holdout_summary.json`.
>
> 4. **(PHASE 4 — ~30 min)** Interpret + record.
>    * Write `SESSION_82_REPORT.md` opening with a plain-language TL;DR. Include: held-out match% and how it compares to A1's in-sample 80.19% (the gap quantifies how much of A1's "lift" was memorization vs structural); per-category lift; N=200 regret cost; the verdict reasoning.
>    * Decision 117 records the SHIP/NULL/MIXED outcome.
>    * Update STRATEGY_GUIDE.md only if SHIP — Part 1 append + Parts 2-6 update in place. If NULL/MIXED, skip Part 1 (no strategy change) and update only the "ML champion" line if relevant.
>    * Rewrite this file (CURRENT_PHASE.md) for S83.
>
> 5. **(PHASE 5 — session end)** Commit + push per `session-end-prompt.md` (pre-authorized for this project per `feedback_taiwanese_commits` memory).
>
> ACCEPTANCE for Session 82:
> * Oracle completion confirmed (1,508,080 records in `oracle_grid_s81_n1000.bin`, header validates).
> * `data/v49_a2_dt_model.npz` saved.
> * Three-lens grade run end-to-end, output in `data/session82/grade_v49_a2.log` + summary JSON.
> * Verdict declared with the pre-committed thresholds — no interpretation arbitrage.
> * Decision 117 written.
> * `SESSION_82_REPORT.md` written with plain-language TL;DR for the non-technical user.
>
> **+$10 ship bar APPLIES in S82.** v49_a2 is the first genuine ship candidate since S78. The N=200 regret window is ±$50 around v44's +$1,081 (i.e. anywhere from +$1,031 to +$1,131 passes the production-baseline gate); the headline OOS test is whether Lens 3 match% clears 75%.
>
> **📓 METHODOLOGY (Session 82+):**
>
> 1. **Trust the grader's verdict.** The thresholds are committed in code. If the grader prints SHIP, ship. If it prints NULL, file it and pivot to A3 (full N=1000 grid) or the headline-goal recalibration discussion the user paused at end-of-S78. Do not re-interpret the thresholds after seeing the data.
>
> 2. **The memorization question is the load-bearing read.** Compare Lens 3 match% to A1's 80.19% in-sample. If Lens 3 hits ~80%, A1's lift was essentially all structural; A2's targeted compute is doubly justified. If Lens 3 hits ~70%, A1's lift was ~half memorization, and the structural signal from cleaner labels is much smaller than S80 suggested. The verdict thresholds (72% / 75%) sit in this range deliberately.
>
> 3. **Per-category lens decides which lever is next.** If two_pair lifts substantially but trips_pair doesn't (or vice versa), category-specific follow-ups become available. If both lift uniformly, A2 is a clean general improvement and the next question is A3 (full grid) vs ship-and-move-on.
>
> 4. **Production state has been UNCHANGED for ten consecutive sessions.** If v49_a2 SHIPs, this is the first ML champion change since v44 was committed. If it NULLs, it's the eleventh UNCHANGED session and we're back to discussing whether the 95% match-rate target is even reachable given the 32% oracle self-disagreement floor (Decision 114's open question).
>
> 5. **"Speed is not necessary — clarity and perfection is."** Already paying dividends — S81's pre-committed grader will produce the unambiguous verdict S82 needs.

> **✅ ARTIFACTS produced in S81:**
> 1. `analysis/scripts/build_s81_subset.py` — subset + held-out construction.
> 2. `analysis/scripts/train_v49_a2_dt.py` — three-zone hybrid trainer (smoke-tested).
> 3. `analysis/scripts/grade_v49_a2_holdout.py` — three-lens grader with pre-committed ship verdict (smoke-tested).
> 4. `data/session81/canonical_hands_s81_subset.bin` (10.57 MB; 1.51M tp/3p hands).
> 5. `data/session81/v49_a2_subset_to_canonical.npy` (6.04 MB).
> 6. `data/session81/v49_a2_holdout_ids.npy` (0.60 MB; 151,008 canonical_ids).
> 7. `data/session81/v49_a2_holdout_subset_indices.npy` (0.60 MB; subset positions).
> 8. `data/session81/v49_a2_subset_categories.npy` (1.51 MB; per-row int8 category).
> 9. `data/session81/oracle_launch.json` — launch metadata + ETA.
> 10. `data/session81/build_summary.json` — input/output sha256 provenance.
> 11. `data/session81/oracle_grid_s81_n1000.bin` — IN PROGRESS, ~611 MB at completion.
> 12. `data/session81/oracle_full_run.log`, `oracle_pilot.log`, `build_subset.log`, `train_v49_a2_smoke.log`, `grade_v49_a2_smoke.log`.
> 13. `SESSION_81_LAUNCH_REPORT.md` — session report.
> 14. `DECISIONS_LOG.md` — Decision 116 (interim launch + S82 plan).
> 15. `CURRENT_PHASE.md` — this file, rewritten for S82.

> Updated: 2026-05-14 (Session 81 end — A2 launched: built 1.51M tp/3p subset with 151,008 held-out, pilot confirmed engine throughput 28.5 hands/sec on subset file, full N=1000 RealisticHumanMixture oracle running in background with ETA ~14.7 hours; training + grading scripts written and smoke-tested before oracle output exists; pre-committed SHIP/NULL/MIXED verdict thresholds embedded in `grade_v49_a2_holdout.py` (SHIP ≥75% held-out match AND N=200 regret within $50 of v44; NULL <72% held-out match; MIXED 72-75%); v49_a2 training Y is three-zone hybrid with 27.80% N=1000 share (vs A1's 8.14%) concentrated on the most-overfit categories; **no production state change in S81 — tenth consecutive UNCHANGED session, oracle-launch + harness-prep session.** S82 plan: when oracle completes (estimated 2026-05-15 morning Pacific), train v49_a2 (~15 min), grade three lenses (~3 min), declare verdict mechanically per grader's hardcoded thresholds; +$10 ship bar APPLIES; v49_a2 is the first real ship candidate since S78.)

---

## Headline state at end of Session 81

**Strategies of record (UNCHANGED for the TENTH consecutive session):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion. $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change — S81 was a pure launch + harness session).

**S82 candidate (in training queue, will exist when oracle completes):**

| Candidate | Hyperparams | Training Y | Verdict source |
|---|---|---|---|
| v49_a2_dt | depth=36, ml=1 | 3-zone hybrid, 27.80% N=1000 share | Lens-3 held-out N=1000 match% vs pre-committed thresholds |

**Oracle status at session close:** running in background (task ID `b2nqj55g5`); 8,000 / 1,510,080 records written by S81 end; ETA ~14.7 hours from launch. Resume mechanism verified — if the process dies, re-launching the same command continues from the next unwritten record. See `data/session81/oracle_launch.json` for the full command + metadata.

---

## Hypothesis cascade status (updated after S81)

| Hypothesis | Description | Status |
|---|---|---|
| H1 | high_only SS+ms route quality | NULL ship +$5 (S73). |
| H2 | high_only route-tradeoff | CLEAN NULL +$0 (S74). |
| Option B (S75) | Gradient boosting at depth=6 / n_est=200 | DECISIVE NULL −$1,392/1000h. |
| S76 / S77 diagnostics | Cross-cat → pair drill | Shipped diagnostics; identified H6/H7/H8. |
| H6 / H7 / H8 (S78) | Pair gated features | CLEAN NULL +$2 prefix. |
| Single-model ML feature-engineering track | At v44 saturating regime | FORMALLY CLOSED (Decision 113). |
| S79 label-noise measurement | Existing N=1000 prefix vs N=200 full | MIXED — 32% oracle disagreement reveals criterion blind spot (Decision 114). |
| A1 (S80) | Retrain v44 DT on N=1000 prefix labels | LIFTS +13.15pp on N=1000 match rate; in-sample evaluation caveat (Decision 115). |
| C2 (S80) | Regularize v44 DT (max_leaf_nodes=500K, ml=5) | NULL −2.13pp on N=1000, −12.24pp on N=200 (Decision 115). |
| **A2 (S81 launch / S82 verdict)** | Targeted N=1000 expansion on two_pair + trips_pair + held-out validation | **HARNESS SHIPPED, oracle running; verdict in S82.** Pre-committed thresholds: SHIP ≥75% / NULL <72% / MIXED 72-75% held-out match (Decision 116). |
| A3 | Full 6M-hand N=1000 grid | Reserved — run only if A2 demonstrates held-out lift AND residual gap warrants 5× compute multiplier. |
| C1 | High-capacity boosting (depth=10-12, n_est=1000-2000) | DEPRIORITIZED — S75 NULL + S80 C2 NULL together close the capacity lever. |
| M1 | Hybrid: regularized DT trained on N=1000 prefix labels | DEPRIORITIZED — C2's NULL means hybrid C-side adds no value over pure A-side. |
| Option D | Rule-chain extension on S77 LOW pair findings | DORMANT — pair is the least-overfit category; deprioritized vs A2's per-category targeting. |

**Cascade verdict (updated post S81):** A-path harness shipped and oracle generating. S82's grader will mechanically declare ship/null/mixed against pre-committed thresholds. If SHIP: first ML-champion change since S78, and the +$10 bar is cleared from above for the first time in the cascade. If NULL: A-path closes here; pivot to A3 (full grid) only if compute-multiplier is justified, else surface the 95% target reachability question.

---

## Resume Prompt (Session 82 — train + grade v49_a2; declare ship verdict)

```
Resume Session 82 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S81 — S82 runs train + grade after
  the S81 oracle completes)
- DECISIONS_LOG.md (latest: Decision 116 — A2 launch + S82 plan + ship
  verdict thresholds pre-committed in code)
- SESSION_81_LAUNCH_REPORT.md (S81 launch + harness session)
- SESSION_80_M2_REPORT.md (S80 A1+C2 verdict; A1 LIFTS +13.15pp in-sample;
  the question S82 settles)
- analysis/scripts/build_s81_subset.py (subset + held-out construction)
- analysis/scripts/train_v49_a2_dt.py (three-zone hybrid trainer)
- analysis/scripts/grade_v49_a2_holdout.py (three-lens grader with
  pre-committed SHIP/NULL/MIXED verdict)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200 (Lens 1)
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000 (Lens 2)
- data/session81/oracle_grid_s81_n1000.bin — 1.51M × 105 at N=1000
  (NEW; tp/3p subset; will be ~611 MB when complete) (Lens 3 source)
- data/session81/v49_a2_subset_to_canonical.npy — subset_pos → full id
- data/session81/v49_a2_holdout_ids.npy — held-out full canonical_ids
- data/session81/v49_a2_holdout_subset_indices.npy — held-out subset pos
- data/session81/v49_a2_subset_categories.npy — per-row category
- data/canonical_hands.bin — 6M canonical 7-card hands
- data/v44_dt_model.npz — production ML champion (baseline for grading)

STATE (end of S81):
- Oracle launched 2026-05-14 08:22 background task b2nqj55g5
  (data/session81/oracle_full_run.log). Empirical ETA 14.7 hours.
  Resume command in data/session81/oracle_launch.json.
- 8,000 / 1,510,080 records persisted at S81 end.
- v49_a2 training Y composition: Zone 1 = 8.14% N=1000 prefix,
  Zone 2 = 19.66% N=1000 S81 (tp/3p), Zone 3 = 72.20% N=200 fallback.
  Held-out: 151,008 rows (every 10th subset index), EXCLUDED from training.
- v49_a2_dt model NOT yet trained — needs the S81 oracle to complete.
- Pre-committed ship verdict (hardcoded in grader):
    SHIP if Lens-3 (held-out N=1000) match% ≥ 75% AND
         |Lens-1 (N=200) $/1000h(v49_a2) − $/1000h(v44)| ≤ $50.
    NULL if Lens-3 match% < 72%.
    MIXED if 72% ≤ Lens-3 match% < 75%.
- Production: v56_trips_hybrid ($1,429 full / $794 prefix) + v44_dt
  ($1,081 full / $686 prefix). UNCHANGED for tenth consecutive session.

USER DIRECTIVE:
- "Speed is not necessary — clarity and perfection is."
- +$10 ship bar APPLIES in S82 — v49_a2 is the first real ship candidate
  since S78.
- User is non-technical; session report MUST open with plain-language
  TL;DR explaining (a) did the oracle finish, (b) what the held-out
  test showed, (c) the verdict and what it means.

DIRECTION FOR SESSION 82 — train + grade v49_a2; declare verdict:

  PHASE 1 (~5 min) — Verify oracle finished.
    tail -5 data/session81/oracle_full_run.log
    ls -lh data/session81/oracle_grid_s81_n1000.bin (expect ~611 MB)
    If still running: report ETA from log tail, wait or end session.
    If terminated early: re-launch the exact command from
      data/session81/oracle_launch.json (resume is idempotent).

  PHASE 2 (~15-20 min) — Train v49_a2.
    mkdir -p data/session82
    PYTHONUNBUFFERED=1 python3 -u analysis/scripts/train_v49_a2_dt.py \
        --max-depth 36 --min-samples-leaf 1 \
        --output data/v49_a2_dt_model.npz 2>&1 \
        | tee data/session82/train_v49_a2.log

  PHASE 3 (~3 min) — Grade on three lenses.
    PYTHONUNBUFFERED=1 python3 -u analysis/scripts/grade_v49_a2_holdout.py \
        2>&1 | tee data/session82/grade_v49_a2.log
    The grader auto-fires the pre-committed ship verdict.

  PHASE 4 (~30 min) — Interpret + record.
    Write SESSION_82_REPORT.md with plain-language TL;DR.
    Decision 117 records the SHIP/NULL/MIXED outcome.
    If SHIP: update STRATEGY_GUIDE.md Part 1 (append) + Parts 2-6 (update
      in place); commit v49_a2 as new ML champion.
    If NULL/MIXED: skip STRATEGY_GUIDE Part 1; surface A3 vs recalibration
      decision to user.
    Rewrite CURRENT_PHASE.md for S83.

  PHASE 5 — Session-end commit + push (pre-authorized).
    Follow session-end-prompt.md.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo (engine likely already built).
- v44_dt model + features remain unchanged.
- +$10 ship bar APPLIES — v49_a2 must clear it on Lens 1 (N=200 full)
  AND the OOS gate on Lens 3 (held-out N=1000).
- "Speed is not necessary — clarity and perfection is."
- TRUST THE GRADER'S VERDICT. The thresholds are pre-committed in code
  exactly so the data lands with no interpretation arbitrage.
- The user is non-technical; the session report must open with a
  plain-language TL;DR before any numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
