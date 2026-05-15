# Session 82 — A2 verdict: NULL (held-out test settles S80's open question)

_Generated 2026-05-15. The S81 oracle finished cleanly overnight; S82 trained v49_a2 and ran the pre-committed grader. Verdict: **NULL**._

## TL;DR — Plain language

**Did the oracle finish?** Yes. It ran for 15.5 hours overnight and wrote all 1,508,080 records cleanly. Output file is the expected 611 MB. No re-launches, no crashes.

**What did the held-out test show?** The new model (`v49_a2`) lost the test. It needed to score 75% or better on the held-out hands to ship; it scored **63.74%**. That's not just "a bit short" — it's below the NULL floor of 72%, and it's actually *worse* than the current production model `v44_dt`, which scored 65.86% on the same held-out hands.

**What does this mean?** Last session (S80) we got really excited because a similar model lifted match% from 67% to 80%. Today's test confirms the suspicion we flagged at the time: that 80% was the model **memorizing** the specific hands it was trained on, not learning a real pattern. When we tested it on hands it had never trained on, the lift disappeared. In fact, on the **trips_pair** category — which had the most dramatic in-sample lift in S80 — the new model is **12.83 percentage points worse** than v44 on held-out hands and bleeds **+$813 more per 1000 hands**.

**The verdict:** NULL — do not ship `v49_a2`. Production state UNCHANGED for the **eleventh consecutive session**.

**What we just confirmed about the project:** giving the model cleaner labels does NOT produce real learning improvement at v44's current size. We've now closed two of the obvious levers in adjacent sessions (Session 78 closed "add new features," Session 82 closes "use cleaner labels"). Two doors remain — and there's a real decision to make about which one to walk through next.

**Two paths forward — your call to make:**

1. **A3 — generate cleaner labels for ALL 6 million hands** (not just the 1.5M targeted in A2). Cost: ~5× the compute we just spent (so roughly 75-80 hours of overnight runs). The hypothesis is that label noise on the *non-targeted* categories may be polluting the targeted-category predictions; only a fully-clean grid can refute that. **Expected outcome based on today's data: small-to-zero held-out lift** — today's test suggests we're already near the noise-bound performance ceiling for a model this size.

2. **Headline-goal recalibration.** The original target — "human-memorizable rules that match the solver 95% of the time" — was set before we discovered that the underlying solver labels disagree with themselves 32% of the time (S79 finding). Today's NULL is the strongest evidence yet that **95% match-rate is not reachable** at the current label noise floor. Recalibrating means picking a new headline metric (e.g., "$/1000h regret < $X" instead of "match% > 95%") and reframing the cascade around it.

I'm not picking between these — the project is at a real fork that needs your input.

**The pre-committed verdict design was the methodological win of S82.** S81 locked the SHIP/NULL/MIXED thresholds in code before the data existed. The grader auto-fired NULL the moment it saw the numbers, with no opportunity for me to argue our way into a "MIXED reading" or "SHIP with caveats." That's the cleanest verdict the project has produced in the entire ML cascade.

---

## What S82 ran (timeline)

| Phase | Wall | What ran | Result |
|---|---:|---|---|
| 1 | ~5 min (verify) | `tail` + `ls` of S81 oracle artifacts | Oracle complete: 1,508,080 records, 611 MB, 15.5h wall time |
| 2 | 6.2 min | `train_v49_a2_dt.py --max-depth 36 --min-samples-leaf 1` | Model saved: 2,177,375 leaves, 1.31 GB |
| 3 | ~40s | `grade_v49_a2_holdout.py` | NULL verdict auto-fired |
| 4 | active | This report + Decision 117 + CURRENT_PHASE rewrite | — |
| 5 | session-end | Commit + push | Pending |

S81's pre-built training and grading scripts ran end-to-end with zero modifications. The whole "verdict-producing" workload of S82 was **~7 minutes of compute** plus interpretation.

---

## The numbers (the read of the experiment)

### Three-lens grade

|  | v44_dt (production) | v49_a2_dt (candidate) | Δ |
|---|---:|---:|---:|
| n_leaves | 2,248,173 | 2,177,375 | −70,798 |
| Lens 1 (N=200, 6M full) match% | 64.43% | 59.02% | **−5.42pp** |
| Lens 1 $/1000h regret | +$1,081 | +$1,245 | +$164 (worse) |
| Lens 2 (N=1000, 500K prefix) match% | 67.05% | **79.33%** | **+12.28pp** *(in-sample)* |
| Lens 2 $/1000h regret | +$686 | +$412 | −$274 (in-sample better) |
| **Lens 3 (N=1000, HELD-OUT 151K) match%** | **65.86%** | **63.74%** | **−2.12pp** *(OOS — the read)* |
| Lens 3 $/1000h regret | +$708 | +$904 | +$196 (worse) |

### Per-category Lens-3 breakdown (the categories A2 specifically targeted)

| Category | n | v44 match% | v49_a2 match% | Δ | v44 regret | v49_a2 regret | Δ |
|---|---:|---:|---:|---:|---:|---:|---:|
| two_pair | 133,914 | 66.79% | 66.04% | −0.75pp | +$708 | +$825 | +$117 |
| trips_pair | 17,094 | 58.59% | 45.76% | **−12.83pp** | +$707 | +$1,520 | **+$813** |

### The pre-committed verdict (auto-fired by the grader)

```
SHIP rule:  Lens 3 match% ≥ 75.0%  AND  |Lens 1 $/1000h(v49_a2) − Lens 1 $/1000h(v44)| ≤ $50
NULL rule:  Lens 3 match% < 72.0%
MIXED:      everything in between → reassess alongside A3

>>> VERDICT: NULL
    Lens 3 match% 63.74% < 72.0% — held-out lift insufficient;
    S80's in-sample 80.19% was largely memorization.
```

---

## What this answers (the four reads)

### 1. The memorization question (the load-bearing read)

This was the entire point of the experiment.

* v49_a2 in-sample (Lens 2): **79.33%**
* v49_a2 OOS (Lens 3): **63.74%**
* **Gap: 15.59pp** ← this is the memorization

Compare to v44_dt, which never saw any N=1000 labels:

* v44_dt in-sample (Lens 2): 67.05%
* v44_dt OOS (Lens 3): 65.86%
* **Gap: 1.19pp** ← essentially calibrated

v49_a2's memorization gap is **13× larger than v44_dt's**. The model with cleaner labels learned its training rows by heart and didn't generalize. This is exactly the failure mode the held-out experiment was designed to detect, and it detected it cleanly.

### 2. The "cleaner labels alone don't help" finding

A2 had 3.4× the N=1000 label coverage of A1 (27.80% of training labels at N=1000 vs A1's 8.14%), concentrated entirely on the most-overfit categories. **The held-out match rate dropped 2.12pp vs v44.** Cleaner labels at v44's saturating capacity (depth=36, min_samples_leaf=1, 2M+ leaves) do not produce structural lift — they produce more elaborate memorization.

This is the data-side mirror of Decision 113's finding that single-model feature engineering also saturates at v44's capacity. Both ends of the lever — better features, better labels — have now been tested at this capacity and both have NULLed.

### 3. The trips_pair regression is the sharpest signal

trips_pair was the most-overfit category in S79 (−19.43pp shift) and the biggest A1 winner in S80 (+20.78pp in-sample). On held-out hands, **v49_a2 is 12.83pp WORSE than v44** on this category, with **+$813/1000h MORE regret**.

The cleaner labels overfit *hardest* exactly where they were supposed to help most. That's the strongest signal in the entire experiment.

### 4. The pre-committed grader is the new methodological standard

The grader has SHIP/NULL/MIXED thresholds hardcoded. It printed `>>> VERDICT: NULL` automatically with one-line reasoning. There was no opportunity for "let me re-examine the numbers" or "let's call this a MIXED outcome" — the verdict was determined before the data existed.

This pattern is now the template for any future ship-or-null experiment. Locking the verdict in code is a single line of self-discipline that pays in trustworthiness.

---

## What S82 does NOT change

* **Production state UNCHANGED for the eleventh consecutive session.**
  * Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix).
  * ML champion: **v44_dt** ($1,081 full / $686 prefix).
  * Two-track divergence: $348/1000h.
  * Total project rule count: 18.
* **STRATEGY_GUIDE.md Part 1 is NOT updated** — no strategy of record changed. Per `session-end-prompt.md`, when no strategy ships, Part 1 is skipped.
* **STRATEGY_GUIDE.md Parts 2-6 are NOT updated** — no champion change to refresh.
* **No code changes** beyond the v49_a2 model file (gitignored).

---

## Path-forward decision (surfaced to user — the next-session question)

The A-path closes here. Two doors remain on the cascade:

### Option 1: A3 — full 6M-hand N=1000 grid

* Generate fresh N=1000 labels for the entire canonical set (6,009,159 hands × 105 settings).
* **Cost: ~5× A2's compute** (≈ 75-80 hours of overnight runs at the same throughput).
* **Hypothesis:** label noise on the *non-targeted* categories propagates second-order errors into targeted-category predictions. Only a fully-clean grid can refute this.
* **Expected outcome under today's NULL:** small-to-zero held-out structural lift. The 1.19pp v44 in-sample-vs-OOS gap on the prefix lens suggests the noise-bound match rate is already very close to v44's saturating performance, and A2's failure on the most-targeted categories suggests adding "cleaner labels on more categories" extends the same memorization pattern to a wider surface.
* **Honest read:** the expected value of A3 looks low. Spending 80h to confirm what today's data already strongly suggests is hard to justify on its own.

### Option 2: Headline-goal recalibration

* The original target — "human-memorizable rules that match the solver 95% of the time" — was set before we discovered (S79) that the underlying solver labels disagree with themselves 32% of the time at N=200.
* Today's NULL is the strongest evidence yet that **95% match-rate is not reachable** at the current label noise floor.
* Recalibrating means picking a new headline metric (e.g., "$/1000h regret < $X" instead of "match% > 95%") and reframing the cascade around it.
* **What this gets you:** a cascade you can actually finish. Right now we're chasing a target that may be physically unreachable; recalibrating lets us define "done" honestly.
* **What this costs:** giving up the original framing. The 95% target was the definition of project success since Day 0.

**My read of the two:** A3 is expensive insurance against a hypothesis the data already disfavors. Recalibration is a harder conversation but it points the cascade somewhere it can win. I'd lean toward recalibration, but it's a strategic call the user owns — I'm surfacing both.

I have not chosen between these. The next session opens with this decision.

---

## Headline state at end of S82 (UNCHANGED — eleventh consecutive session)

* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix). Grader-confirmed.
* ML champion: **v44_dt** ($1,081 full / $686 prefix).
* Two-track divergence: $348/1000h.
* Total project rule count: 18.
* **A-path closes here.** No more N=1000-on-subset variations.
* **The +$10 ship bar held** — v49_a2 was the first real ship candidate since S78, and it cleanly NULLed by the pre-committed criteria.

---

## Methodology notes (Session 82)

1. **Pre-committed verdict in code is the new template.** First in design (S81): forced thresholds before data existed. Second in execution (S82): the verdict fired automatically on the numbers; no opportunity to re-argue. Cleanest methodological win since the prefix tripwire.

2. **In-sample vs OOS gap quantifies memorization directly.** v49_a2 gap = 15.59pp; v44 gap = 1.19pp. The 13× difference is the entire story of the experiment.

3. **Targeted compute amplifies the failure mode it was meant to fix.** A2 concentrated 3.4× more clean labels on the categories most prone to memorization. The OOS regression on those exact categories (trips_pair −12.83pp) is the strongest signal that *targeting* is not the lever — the lever (if any) is *capacity reduction*, which Decision 115's C2 already NULLed.

4. **Two zero-signal levers in adjacent sessions strongly suggest the headline target is the bottleneck.** Decision 113 closed single-model feature engineering at v44 saturation. Decision 117 closes label-quality improvements at v44 capacity. The pattern is the bottleneck moving from "cascade has more levers to test" to "cascade has tested all the obvious levers and the residual is the noise floor."

5. **The v44 in-sample-vs-OOS gap of 1.19pp is the noise floor lower bound.** v44's OOS match rate of 65.86% is what the underlying data supports without cleaner-label assistance. Any candidate that doesn't beat 65.86% on Lens 3 is not finding new structural signal; it's relabeling.

6. **The empirical pilot was right (again).** S81's 14.7h pilot estimate landed within 0.83h of actual wall time (15.53h). Brief pilot with actual binary on actual input always beats a wall-time model.

7. **"Speed is not necessary — clarity and perfection is."** The S82 ship attempt is the cleanest NULL in the cascade because S81 spent its compute window writing the harness, not waiting. The verdict landed in 40 seconds of grader runtime; everything else was decided before the data existed.

---

## Files (Session 82)

**New artifacts (all gitignored):**
* `data/v49_a2_dt_model.npz` — 1.31 GB, 2.18M leaves.
* `data/session82/train_v49_a2.log` — fit log.
* `data/session82/grade_v49_a2.log` — grader output incl. verdict.
* `data/session81/grade_v49_a2_holdout_summary.json` — machine-readable verdict summary.

**Documentation (committed):**
* `SESSION_82_REPORT.md` — this file.
* `DECISIONS_LOG.md` — Decision 117 appended.
* `CURRENT_PHASE.md` — rewritten for S83 (A3 vs recalibration as the next-session question).

**No new code in S82.** All scripts already shipped in S81; S82 ran them end-to-end against the now-complete oracle output.
