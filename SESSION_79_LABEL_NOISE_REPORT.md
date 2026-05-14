# Session 79 — Label-noise measurement (N=200 vs N=1000 on shared 500K prefix)

_Generated 2026-05-13 (Session 79 end)._

## TL;DR — Plain language

We ran a one-session diagnostic to answer: **is the 35-point gap to our 95%
match-rate goal because our model (v44_dt) is wrong, or because the answer
key itself is noisy?**

The answer is: **both. And the pre-committed decision criterion didn't
anticipate this.**

What we found, in plain English:

1. **The answer key IS noisy.** When we used a 5x-more-accurate version
   of the answer key (N=1000 samples per hand instead of N=200), the
   "right answer" changed on **32% of hands** — almost one in three.

2. **But v44 also memorized some of the noise.** The model scored 73% match
   against the noisy key (what we used in training) but only 67% match
   against the cleaner key. The 6-point drop is the model's overfitting to
   N=200-specific noise patterns becoming visible.

3. **Two opposing effects offset.** On hands where the noisy key said
   "v44 is right" (the MATCH bucket, 73% of hands), the cleaner key flipped
   22% of them to "v44 is wrong." On hands where the noisy key said
   "v44 is wrong" (the NOISE bucket, rank 2-3 errors at N=200), the
   cleaner key flipped 44% of them to "v44 is right." Net: 6pp drop.

4. **Per-category breakdown is informative.** Pair and three_pair categories
   show small POSITIVE shifts (+2.1pp, +1.6pp) — labels and model are
   roughly aligned there. Two_pair and trips_pair show the largest
   NEGATIVE shifts (−13.7pp, −19.4pp) — v44 is most overfit to N=200 noise
   in these categories.

5. **Strategic conclusion: MIXED.** The pre-committed criterion read
   "shift < +2pp → C-path (real model error, bigger model)" — but it
   assumed shift would be a clean indicator of label noise. The data
   refutes that assumption: oracle self-disagreement of 32% says labels
   are far from stable. The honest verdict is **MIXED — surface options
   to user, do not pre-commit.**

The headline question for the user is:

> Do we invest 3-5 sessions of compute in (A) better labels, (C) bigger
> models, or (M) a hybrid mid-path that addresses both the label noise
> and the memorization at once?

---

## How the measurement worked

For each of the first 500,000 canonical hands (the same hands that live
in both grids — the prefix is a head slice of the full grid), we computed:

1. **v44_pick**: the setting v44_dt picks for this hand (deterministic).
2. **n200_pick**: the setting the N=200 (full) oracle calls "best".
3. **n1000_pick**: the setting the N=1000 (prefix) oracle calls "best".
4. **n200_match**: did v44 match the N=200 argmax?
5. **n1000_match**: did v44 match the N=1000 argmax?
6. **v44_rank_n200**: where v44's pick ranks among 105 settings under
   N=200 labels (1 = top; the S76 setting-rank lens).

The match-rate shift `pct(n1000_match) − pct(n200_match)` was the
load-bearing metric in the pre-committed decision criterion.

Compute: 500,000 hands swept in 68.8s (~7,260 hands/s) on the laptop.
Memory-mapped both grids; never read full bytes; no oracle expansion
performed. **Free compute — no new oracle sampling.**

## Results

### Overall

| Metric | N=200 oracle | N=1000 oracle | Δ |
|---|---:|---:|---:|
| Match rate (v44 == oracle argmax) | **72.98%** | **67.05%** | **−5.93pp** |
| Mean regret ($/1000h vs that oracle) | $703 | $686 | −$17 |
| Oracle self-agreement (N=200 argmax == N=1000 argmax) | — | — | **68.00%** |

The 32% oracle self-disagreement is the most important number on this
page. **The N=200 labels disagree with the cleaner N=1000 labels on the
"best setting" for roughly 1 in 3 hands.** That is overwhelming evidence
that labels are far from stable.

### By setting-rank bucket (S76 lens)

v44_rank computed against the N=200 oracle. Then we check whether v44's
pick matches the N=1000 argmax within each bucket.

| Bucket | n | % share | N=200 match% | N=1000 match% | Δ | N=200 $/1000h | N=1000 $/1000h |
|---|---:|---:|---:|---:|---:|---:|---:|
| **MATCH** (rank 1) | 366,390 | 73.3% | **99.59%** | **77.70%** | **−21.89pp** | $0 | $370 |
| **NOISE** (rank 2-3) | 97,336 | 19.5% | 0.00% | **43.58%** | **+43.58pp** | $1,977 | $1,269 |
| **MID** (rank 4-9) | 32,854 | 6.6% | 0.00% | 23.66% | +23.66pp | $4,092 | $2,175 |
| **STRUCTURE** (rank ≥10) | 3,420 | 0.7% | 0.00% | 10.61% | +10.61pp | $7,186 | $3,686 |

Key reads:

- **MATCH bucket loses ~22pp.** Of the 73% of hands where v44 matched
  the N=200 oracle, ~22% of those flip to non-match at N=1000. This is
  v44 having memorized N=200 noise that doesn't survive at N=1000.
- **NOISE bucket gains +43.58pp.** Almost half of v44's "rank 2-3" mistakes
  at N=200 turn out to be matches at N=1000. The N=200 oracle was simply
  mislabeling the argmax due to sampling noise; v44's pick was right.
- **MID bucket gains +23.66pp.** A weaker version of the same pattern.
- **STRUCTURE bucket gains +10.61pp.** The smallest gain proportionally,
  but still positive — even the "worst" v44 mistakes are partly mislabeled.

The two largest effects (MATCH losing 21.9pp × 73% mass = −16.0pp; NOISE
gaining 43.6pp × 19.5% mass = +8.5pp) drive the overall −5.9pp shift.

### By hand category

| Category | n | % share | N=200 match% | N=1000 match% | Δ | N=200 $/1000h | N=1000 $/1000h |
|---|---:|---:|---:|---:|---:|---:|---:|
| pair | 215,162 | 43.0% | 67.00% | **69.09%** | **+2.10pp** | $830 | $595 |
| two_pair | 204,275 | 40.9% | 80.44% | 66.76% | **−13.69pp** | $457 | $663 |
| trips | 25,245 | 5.0% | 61.22% | 56.57% | −4.65pp | $1,194 | $1,086 |
| trips_pair | 25,943 | 5.2% | 82.58% | 63.15% | **−19.43pp** | $411 | $727 |
| three_pair | 25,614 | 5.1% | 66.15% | **67.73%** | **+1.59pp** | $1,356 | $1,143 |
| quads | 1,100 | 0.2% | 78.09% | 65.27% | −12.82pp | $711 | $783 |
| composite | 2,661 | 0.5% | 65.31% | 55.69% | −9.62pp | $1,156 | $1,226 |

Key reads:

- **pair (43% of mass) is the LEAST overfit category.** Tiny positive
  shift (+2.1pp). v44's pair decisions are roughly noise-stable.
- **trips_pair is the MOST overfit.** Match rate drops 19.4pp going
  N=200 → N=1000. v44 memorized N=200 trips_pair noise more aggressively
  than any other category. Note that S78's H6/H7/H8 work was in PAIR,
  which is exactly the wrong place to chase additional signal.
- **two_pair is the second-most overfit.** −13.7pp. Combined with pair
  this is 84% of the hand mass; the two_pair noise is doing meaningful
  damage.
- **three_pair behaves like pair** (+1.6pp). Two of the smallest
  categories — quads and composite — show moderate-to-large negative
  shifts but their tiny mass (0.2% + 0.5% = 0.7%) limits overall impact.

## Decision criterion — mechanical reading vs honest interpretation

The CURRENT_PHASE pre-committed criterion was:

> If shift ≥ +5pp on prefix: A-PATH (label noise dominates → invest in N=1000).
> If shift < +2pp: C-PATH (labels stable → invest in higher-capacity model).
> If +2pp ≤ shift < +5pp: MIXED — surface options to user.

**Mechanical reading of our −5.93pp shift: C-PATH** (it falls below +2pp).

But the criterion's *underlying assumption* was that match-rate shift is
a clean indicator of label noise impact. **The data refutes that
assumption.** Oracle self-disagreement of 32% says labels are anything
but stable. The criterion has a blind spot for the case where v44 is
memorizing the noisy training labels — in that case, moving to cleaner
labels makes v44 *look worse* even though labels are *more* noisy, not
less.

The script printed `C_PATH` per strict reading. **The honest verdict on
this report is MIXED** — the data is inconsistent with either the
A-PATH or C-PATH model assumed by the criterion, and the path forward
needs user input.

## Strategic options (Phase 4)

Three families of options surface from this data:

### A-family — Better labels

* **A1. N=1000 retrain.** Retrain a v44-class DT on the existing 500K
  N=1000 prefix labels (instead of N=200 labels). Smoke-tests the
  memorization hypothesis directly — if a model trained on N=1000 shows
  similar regret on the prefix but better match rate, the noise
  hypothesis is confirmed. ~1 hour compute. Smallest commitment.
* **A2. Targeted N=1000 expansion.** Expand N=1000 oracle generation
  specifically to two_pair + trips_pair (the worst-affected categories,
  ~46% of grid mass). At ~5× the per-hand cost of N=200 and ~2.75M
  hands, estimated ~24-36 hr local compute.
* **A3. Full N=1000 grid generation.** ~5 days local compute. Heaviest
  commitment.

### C-family — Bigger / different model

* **C1. High-capacity boosting retry.** XGBoost at depth=10-12,
  n_est=1000-2000, longer early stopping. ~3-6 hr compute. Would have
  HIGHER capacity than v44's DT and might memorize MORE N=200 noise —
  risk is real.
* **C2. Regularized v44 retrain.** Refit the same DT family with lower
  capacity (max_leaves cap, higher min_samples_leaf) — directly test
  whether less memorization closes the N=200 → N=1000 match-rate gap.
  ~30 min compute. Cleanest test of the memorization hypothesis from
  the C side.

### M-family — Hybrid (the option the criterion didn't surface)

* **M1. A1 + C2 combined.** Retrain a regularized DT on N=1000 prefix
  labels. Tests both halves of the hypothesis simultaneously. ~1 hour
  compute. Cleanest single experiment.
* **M2. Diagnose first, choose second.** Run A1 and C2 as one-session
  experiments in parallel; compare their regret + match-rate against
  N=1000 to learn which lever moves the needle. ~2 hours compute.

### Recommendation

The M-family is the highest-information-per-hour path. Specifically:

**S80 plan recommendation — M2 (parallel A1 + C2 one-session experiments):**

1. **A1 experiment** (~30 min): Retrain v44-architecture DT on the 500K
   N=1000 prefix labels only. Grade vs both N=200 full grid (regret
   metric) and N=1000 prefix grid (match-rate metric). If match rate
   vs N=1000 rises materially above v44's 67.05%, the noise hypothesis
   is confirmed — go to A2 in S81.

2. **C2 experiment** (~30 min): Retrain v44-architecture DT with
   max_leaves=500K (vs v44's 2.25M) and min_samples_leaf=5 (vs v44's 1)
   on the same N=200 full-grid training data. Grade vs both grids.
   If match rate vs N=1000 rises (despite using N=200 training), the
   memorization hypothesis is confirmed from the C side — go to C1 in
   S81.

3. **Decision matrix** at end of S80:
   * Both A1 and C2 lift match-rate → hybrid M1 in S81.
   * Only A1 lifts → label noise is dominant → A2 in S81.
   * Only C2 lifts → memorization is dominant → C1 in S81.
   * Neither lifts → headline-goal recalibration: 95% may not be
     attainable against any noisy oracle; reframe the project goal.

## Why C-PATH alone is a risky default

The mechanical verdict of C-PATH (bigger model) is the most concerning
single-option recommendation: a higher-capacity model is MORE likely
to memorize N=200 noise than v44 already does. The S75 boosting NULL
($-1,392/1000h) is a warning shot from this exact direction. C-PATH
without first addressing label noise risks repeating S75's failure
mode with a costlier model.

## Why A-PATH alone defers the harder question

Even with N=1000 labels everywhere, the 32% oracle self-disagreement
at N=200 → N=1000 suggests N=1000 may not be the ceiling either.
At some point the oracle's own variance bottoms out, and what's left
*is* genuine model error. A-PATH alone doesn't tell us whether v44's
architecture can capture the remaining 30-35pp of true gap.

## Files (Session 79)

**New code:**
* `analysis/scripts/label_noise_measurement_S79.py` — the measurement script.

**Data (gitignored, local-only — per project convention for summary JSONs):**
* `data/label_noise_S79_summary.json` — full summary breakdown (4.4 KB).
* `data/session79/label_noise_measurement_full.log` — full sweep log.

**Documentation:**
* `SESSION_79_LABEL_NOISE_REPORT.md` — this file.
* `DECISIONS_LOG.md` — Decision 114 (MIXED verdict + criterion blind spot
  + recommend M2 for S80).
* `CURRENT_PHASE.md` — rewritten for S80 with M2 plan.

## Production state at end of S79 (UNCHANGED — eighth consecutive session)

* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix). Grader-confirmed.
* ML champion: **v44_dt** ($1,081 full / $686 prefix on prefix grid;
  $686/1000h confirmed in this report against N=1000 labels too).
* Two-track divergence: $348/1000h (no change).
* Total project rule count: 18 (UNCHANGED).
* **No ship attempted in S79 by design — measurement-only session.**

## Methodology notes for future sessions

1. **Pre-committed criteria need to anticipate all directions of the
   metric.** S79's criterion assumed shift would be zero or positive;
   negative shifts fell into the "stable labels" bin by default, which
   is exactly the wrong interpretation when v44 is overfit to noisy
   labels. Future criteria should specify what each sign of the metric
   means under the criterion's model, and explicitly note when the
   metric is inconsistent with that model.

2. **The 32% oracle self-disagreement number should have been measured
   sessions ago.** It's a one-line addition to any S71+ diagnostic. The
   "oracle is ground truth" framing carried us through S25-S78 unchallenged.

3. **Setting-rank bucketing was the right lens.** The bucket-level shift
   pattern (MATCH losing 22pp, NOISE gaining 44pp) is what made the
   memorization hypothesis legible. Without bucketing, the −5.93pp
   overall shift would have looked like a single number and the
   mechanical verdict (C-PATH) would have been adopted.

4. **Category breakdown identifies where to invest.** S77/S78 invested in
   pair (least-overfit category). The data says trips_pair and two_pair
   are where the memorization is concentrated. Future N=1000 expansion
   or memorization-reduction work should target those categories first.

5. **"Speed is not necessary — clarity and perfection is."** Followed.
   500K-hand sweep ran in 69 seconds; bulk of the session was on
   interpretation rather than compute. The MIXED verdict is the clearest
   defensible call given the data; rushing to C-PATH per the mechanical
   read would have repeated the S75 boosting failure mode.

6. **Free compute moves like this one should be earlier in the cascade.**
   S75-S78 spent four sessions on feature engineering and capacity
   experiments under the implicit assumption that labels were stable.
   S79's measurement could have been done after S75's boosting NULL —
   four sessions earlier. Generalize: "before doubling down on either
   model or features, validate the labels."
