# Current: Sprint 8 — Session 82 NULL verdict on v49_a2 (held-out match% 63.74% < 72.0% NULL floor); A-path closes; Session 83 opens with the user-owned A3-vs-recalibration decision

S82 ran end-to-end: confirmed the S81 oracle finished cleanly (1,508,080 records, 611 MB, 15.5h wall time, within 0.83h of pilot estimate); trained v49_a2_dt (depth=36 ml=1, 2,177,375 leaves, 6.2 min fit, 1.31 GB); ran the pre-committed three-lens grader. **The grader auto-fired NULL** based on hardcoded thresholds locked in code in S81 — no interpretation arbitrage.

The held-out test settled S80's open question definitively: **A1's 80.19% in-sample lift was largely memorization.** v49_a2 — with 3.4× the N=1000 training-label coverage of A1, concentrated entirely on the highest-overfit categories — scored 79.33% on the in-sample prefix lens (matching A1's signal) but only **63.74% on held-out hands** (well below v44's 65.86% baseline AND below the 72% NULL floor). The 15.59pp in-sample-vs-OOS gap on v49_a2 vs the 1.19pp gap on v44 is the memorization, quantified directly. trips_pair — the most-overfit category and the biggest A1 winner — regressed **−12.83pp on held-out and bled +$813/1000h MORE regret** than v44.

**Production state UNCHANGED for the eleventh consecutive session.** v56_trips_hybrid + v44_dt as before. No code changes in S82.

> **🎯 IMMEDIATE NEXT ACTION (Session 83): user-owned strategic decision; no compute work until the user picks a path**
>
> The A-path (oracle-label-quality lever) closes here. Two doors remain on the cascade. **The user must choose** — both have honest expected-value reads attached:
>
> ### Option 1 — A3 (full 6M-hand N=1000 grid)
> Generate fresh N=1000 labels for the entire canonical set (5× A2's compute, ~75-80h overnight runs). Retrain v49_a3_dt on uniformly-clean labels. The hypothesis is that label noise on *non-targeted* categories propagates second-order errors into targeted-category predictions.
> * **Cost:** 5× A2 compute.
> * **Expected outcome under today's NULL:** small-to-zero structural lift on held-out. The 1.19pp v44 in-sample-vs-OOS gap on the prefix lens suggests the noise-bound match rate is already very close to v44's saturating performance, and A2's failure on the most-targeted categories suggests adding clean labels on more categories extends the same memorization pattern to a wider surface.
> * **Honest read:** expensive insurance against a hypothesis the data already disfavors. Hard to justify on its own.
>
> ### Option 2 — Headline-goal recalibration
> The original target — "human-memorizable rules that match the solver 95% of the time" — was set before we discovered (S79) that the underlying solver labels disagree with themselves 32% of the time at N=200. Today's NULL is the strongest evidence that **95% match-rate is not reachable** at the current label noise floor.
> * Recalibrating means picking a new headline metric (e.g., "$/1000h regret < $X" instead of "match% > 95%") and reframing the cascade around it.
> * **What this gets you:** a cascade you can actually finish.
> * **What this costs:** giving up the original framing.
>
> **My read:** A3 is expensive insurance against a hypothesis the data already disfavors; recalibration is the harder conversation but it points the cascade somewhere it can win. I'd lean toward recalibration but it's a strategic call the user owns. **No compute is launched in S83 until the user picks.**
>
> ### What S83 does (depending on user pick)
>
> * **If user picks A3:** S83 launches the full N=1000 oracle (background, ~80h overnight + cross-day), writes the train/grade harness in parallel (same playbook as S81), and Decision 118 records the launch.
> * **If user picks recalibration:** S83 is a planning session. Read `DECISIONS_LOG.md` Decision 114 (S79 noise-floor finding), Decision 117 (S82 NULL), and the current STRATEGY_GUIDE.md residual landscape. Propose 2-3 candidate headline metrics with worked-example targets, surface the trade-offs, and write Decision 118 capturing the recalibration choice.
> * **If user picks something else** (e.g., "let's revisit Option D rule-chain extension on S77 LOW pair findings" — the dormant lever from Decision 113): S83 implements that path.
>
> ### Why this is a fork, not a continuation
>
> The cascade has now tested both ends of the lever — better features (S78 NULL) and better labels (S82 NULL) — at v44's saturating capacity. Both NULLed. The remaining doors are either (a) more compute on the same path with low expected yield (A3), or (b) a strategic re-framing. Continuing on momentum without choosing is what produced the eleven UNCHANGED sessions. The user should pick.

> **📓 METHODOLOGY (Session 83+):**
>
> 1. **Trust the grader's verdict — done.** S81/S82's pre-committed grader is the new template for any ship-or-null experiment. Lock thresholds in code before the data exists; the grader auto-fires; no interpretation arbitrage.
>
> 2. **In-sample vs OOS gap is the memorization meter.** Always compute both. The 13× difference between v49_a2's gap (15.59pp) and v44's gap (1.19pp) is the entire story of S80→S82.
>
> 3. **Two adjacent zero-signal levers means the bottleneck has moved.** S78 closed feature engineering at v44 saturation. S82 closes label quality at v44 capacity. The bottleneck is no longer "more levers to test" — it's "the noise floor itself or the headline target."
>
> 4. **The v44 OOS match rate (65.86%) is the noise floor lower bound** for any v44-class model on the targeted categories. Any future candidate that doesn't beat this on Lens 3 is relabeling, not learning.
>
> 5. **"Speed is not necessary — clarity and perfection is."** S82 produced the cleanest NULL in the cascade in 40 seconds of grader runtime because S81 spent the prior 15+ hours writing the harness. The pattern stands.

> **✅ ARTIFACTS produced in S82:**
> 1. `data/v49_a2_dt_model.npz` — 1.31 GB, 2,177,375 leaves (gitignored).
> 2. `data/session82/train_v49_a2.log` — fit log.
> 3. `data/session82/grade_v49_a2.log` — grader output incl. NULL verdict.
> 4. `data/session81/grade_v49_a2_holdout_summary.json` — machine-readable verdict summary.
> 5. `SESSION_82_REPORT.md` — session report with plain-language TL;DR.
> 6. `DECISIONS_LOG.md` — Decision 117 (NULL verdict + memorization finding + path-forward fork).
> 7. `CURRENT_PHASE.md` — this file, rewritten for S83.
>
> **No new code in S82.** All scripts already shipped in S81; S82 ran them end-to-end against the completed oracle.

> Updated: 2026-05-15 (Session 82 end — A2 verdict NULL: oracle finished cleanly overnight (15.53h wall, 1.51M records, 611 MB), trained v49_a2_dt (2.18M leaves, 6.2 min fit), pre-committed grader auto-fired NULL on Lens-3 held-out match% 63.74% < 72.0% floor; A1's 80.19% S80 in-sample lift confirmed empirically as memorization (v49_a2 in-sample-vs-OOS gap 15.59pp vs v44's 1.19pp gap — 13× larger); trips_pair regressed −12.83pp held-out and bled +$813/1000h MORE regret than v44; **production state UNCHANGED for the eleventh consecutive session — v56_trips_hybrid + v44_dt as before; no code changes; STRATEGY_GUIDE.md unchanged.** A-path closes here. S83 opens with user-owned strategic fork: A3 (full 6M N=1000 grid, 5× compute, low expected yield based on today's data) vs headline-goal recalibration (concede the 95% match-rate target as unreachable at the 32% noise floor and pick a new metric); my honest read is recalibration but the user owns the strategic call. No compute launched in S83 until user picks. Pre-committed grader pattern (S81+S82) is the new template for any ship-or-null experiment in the cascade going forward.)

---

## Headline state at end of Session 82

**Strategies of record (UNCHANGED for the ELEVENTH consecutive session):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion. $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change).

**S82 candidate result (NULLED):**

| Candidate | Hyperparams | Training Y | Verdict |
|---|---|---|---|
| v49_a2_dt | depth=36, ml=1, 2.18M leaves | 3-zone hybrid, 27.80% N=1000 share | **NULL** — Lens-3 held-out 63.74% < 72.0% floor |

---

## Hypothesis cascade status (updated after S82)

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
| **A2 (S81/S82)** | Targeted N=1000 expansion on two_pair + trips_pair + held-out validation | **CLEAN NULL** — Lens-3 held-out 63.74% < 72.0% floor; A1's S80 lift confirmed as memorization (Decision 117). |
| **A-path (oracle-label-quality lever)** | All variants tested at v44 capacity | **FORMALLY CLOSED** at v44 regime (Decision 117). |
| A3 | Full 6M-hand N=1000 grid | **DEPRIORITIZED post-S82** — 5× A2 compute against a hypothesis today's data already disfavors. Surfaced as Option 1 in S83 fork; user-owned decision. |
| C1 | High-capacity boosting (depth=10-12, n_est=1000-2000) | DEPRIORITIZED — S75 NULL + S80 C2 NULL together close the capacity lever. |
| M1 | Hybrid: regularized DT trained on N=1000 prefix labels | DEPRIORITIZED — C2's NULL means hybrid C-side adds no value over pure A-side. |
| Option D | Rule-chain extension on S77 LOW pair findings | DORMANT — operates at rule layer outside DT saturation; revivable if user picks during S83 fork. |
| **Headline-goal recalibration** | Concede 95% match% as unreachable; pick new metric | **NEW CASCADE OPTION post-S82** — Surfaced as Option 2 in S83 fork; user-owned decision. |

**Cascade verdict (updated post S82):** The cascade has now tested both ends of the lever — better features (S78 NULL) and better labels (S82 NULL) — at v44's saturating capacity. Both NULLed. The remaining doors are A3 (low expected yield), Option D (rule-layer, untested at the new diagnostic clarity), or headline-goal recalibration. **S83 opens with the strategic fork; no compute until user picks.**

---

## Resume Prompt (Session 83 — A3 vs recalibration; user-owned fork)

```
Resume Session 83 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S82 — opens the A3-vs-
  recalibration fork)
- DECISIONS_LOG.md (latest: Decision 117 — S82 v49_a2 NULL +
  A-path closure + path-forward fork surfaced)
- SESSION_82_REPORT.md (S82 NULL verdict, plain-language TL;DR,
  the two paths forward)
- SESSION_81_LAUNCH_REPORT.md (S81 launch + harness session for
  A2 — context for what A3 would scale)
- SESSION_80_M2_REPORT.md (S80 A1+C2 results — the in-sample lift
  S82's held-out test settled)

KEY DATA FILES (no new generation in S83 unless user picks A3):
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/session81/oracle_grid_s81_n1000.bin — 1.51M × 105 at N=1000
  (NEW S81 grid; tp/3p subset)
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 11 sessions)
- data/v49_a2_dt_model.npz — S82 NULLed candidate (kept for diagnostic use)

STATE (end of S82):
- Production UNCHANGED for the ELEVENTH consecutive session:
  v56_trips_hybrid ($1,429 full / $794 prefix) + v44_dt
  ($1,081 full / $686 prefix). Two-track divergence $348/1000h.
- v49_a2 NULLED by pre-committed grader: Lens-3 held-out match%
  63.74% < 72.0% floor. A1's S80 80.19% in-sample lift confirmed
  empirically as memorization (15.59pp in-sample-vs-OOS gap on
  v49_a2 vs 1.19pp on v44, 13× larger).
- A-path (oracle-label-quality lever) FORMALLY CLOSED at v44 capacity.
- Two adjacent zero-signal levers (S78 features NULL, S82 labels NULL)
  strongly suggest the bottleneck is the noise floor itself or the
  95% headline target.

USER DIRECTIVE:
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; any strategic discussion must lead with
  plain-language framing of trade-offs.
- The S83 fork is a USER-OWNED strategic call — do not pick for the
  user. Surface the options + the honest expected-value read; wait
  for the user to choose.
- No compute is launched in S83 until the user picks a path.

DIRECTION FOR SESSION 83 — surface the fork; do NOT pre-commit:

  PHASE 1 (~5 min) — Read the four context files above + any newer
  context the user adds in their message.

  PHASE 2 (~10-15 min) — Open with the fork:
    Briefly summarize where we are (eleven UNCHANGED sessions; both
    feature-engineering and label-quality levers NULLed at v44 capacity).
    Restate the two doors:
      Option 1: A3 — full 6M-hand N=1000 grid (5× compute, low
                expected yield based on today's data).
      Option 2: Headline-goal recalibration — concede 95% match-rate
                as unreachable at the 32% noise floor; pick new metric.
    Surface the dormant Option D (rule-chain extension on S77 LOW
    pair findings) as a third alternative.
    Give an honest "my read" but DO NOT pick. Wait for user.

  PHASE 3 — depends on user choice:
    A3 → launch the full N=1000 oracle in background (~80h),
         write train/grade harness in parallel (same playbook as
         S81), Decision 118 records the launch.
    Recalibration → planning session. Read DECISIONS_LOG.md
         Decision 114 (S79 noise-floor) + Decision 117 (S82 NULL),
         propose 2-3 candidate headline metrics with worked-example
         targets, write Decision 118 capturing the recalibration.
    Option D → implement the rule-chain extension on S77 LOW pair
         kicker_max-in-pair-suit discriminator; ship gate is +$5
         prefix grid (the grader Δ that S78 also used).
    Other → implement what the user picks.

  PHASE 4 — Session-end commit + push (pre-authorized).

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged.
- The pre-committed-verdict pattern (S81 + S82) is the new template
  for any ship-or-null experiment going forward.
- "Speed is not necessary — clarity and perfection is."
- The user is non-technical; any session report opens with a
  plain-language TL;DR before any numbers.
- DO NOT pick the strategic path for the user. Surface options;
  wait for direction.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
