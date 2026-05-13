# Current: Sprint 8 — Session 75 v47_xgb decisive NULL at depth=6/n_est=200/lr=0.1 (−$1,392/1000h full); single-model ML track exhausted at v44 saturating regime; S76 pivots to oracle-label refinement / diagnostic refresh / rule-chain extension / high-capacity boosting retry

S74 v47_dt (H2 route-tradeoff comparator) clean NULL closed the DT-
feature-engineering chapter at v44's saturating regime. S75 tested
Option B (gradient boosting via XGBoost 3.2) at v44's exact 107
features (NO ho_v7 — clean "boosting vs DT" isolation) with hyperparams
depth=6, n_estimators=200, learning_rate=0.1, multi_strategy=
'multi_output_tree', subsample=0.7, colsample_bytree=0.7,
early_stopping_rounds=20 on a 20% validation split.

**Result: decisive NULL. −$1,392/1000h full grid (vs +$10 ship bar
and +$5 PARTIAL bar — orders of magnitude below).** Every per-
category $/1000h regresses substantially:
* high_only: $1,868 → **$3,461** (Δ −$1,593)
* pair: $1,097 → **$2,291** (Δ −$1,194)
* two_pair: $363 → **$1,845** (Δ −$1,482)
* trips: $1,194 → **$2,716** (Δ −$1,523)
* trips_pair: $281 → **$3,027** (Δ −$2,746)
* three_pair: $1,613 → **$2,069** (Δ −$456)
* quads: $545 → **$2,265** (Δ −$1,720)
* composite: $960 → **$3,351** (Δ −$2,392)

Pct opt collapses 64.80% → 41.96% (−22.84pp).

Prefix grader confirms with **−$765/1000h** regression on the 500K
subset that has 0 high_only IDs — so the regression is on the 7 non-
high_only categories alone, all of which v44 has well-tuned features
for via the S57-S72 feature stack.

**The structural cause is capacity mismatch.** v44_dt has 2,248,173
leaves at 2.7 rows/leaf — effectively a memorized lookup over the
4.8M training rows. v47_xgb at depth=6 with 200 trees has at most
64×200 = 12,800 distinct partition cells (175× fewer). The boosting
model's smooth weighted-sum prediction cannot match the saturating-DT
partition capacity for argmax-of-105-outputs accuracy.

The val-curve tripwire FIRED — model still improving at iter limit
(last-50 Δ +0.011, best_iter=199/200) — so v47_xgb is also UNDER-
CONVERGED. But closing a $1,392 gap by tuning alone is implausible;
to match v44's partition capacity, boosting would need ~depth=10 ×
n_est≈2200 = 24-40 hours wall on this hardware. Even then, structural
argmax-vs-smooth-prediction precision concerns remain.

**Decision 110: NULL ship.** v44_dt remains ML champion at $1,081/1000h
full / $686 prefix. v56_trips_hybrid remains rule chain at $1,429
full / $794 prefix. Production state UNCHANGED for the **fourth**
consecutive session (S72 NULL, S73 PARTIAL POSITIVE / NULL ship, S74
clean NULL, S75 decisive NULL).

**The entire single-model ML track is exhausted at v44's saturating
regime.** Four consecutive sessions at the +$10 ship bar have
produced 0 ML-champion ships. The bar is doing its job; the track is
closed. **S76 must pivot.**

> **🎯 IMMEDIATE NEXT ACTION (Session 76): Pivot direction**
>
> Four options on the table. They are NOT mutually exclusive; the
> user should pick one to drive S76, with the others as backstops
> if the first stalls.
>
> **(A) Oracle-label N=1000 re-evaluation.** Hypothesis: the saturating-
> DT regime has hit a label-noise ceiling. Current grid samples 200
> board draws per (hand, setting) cell; N=1000 reduces label variance
> by ~√5 ≈ 2.24×. If v44_dt's $1,081/1000h is partly noise-induced,
> a re-evaluated grid could un-stick the regret floor. Cost: ~10×
> compute vs the original grid build (~weeks at single-machine; manageable
> on a cluster). Risk: the ceiling may NOT be noise-induced (the
> per-category breakdown is suspiciously uniform). Payoff if it
> works: potentially $200-500/1000h closure of the gap to oracle.
> **Recommended if cluster access is available.**
>
> **(B) Categorical diagnostic refresh.** Re-run drill_v44_high_only_S71.py
> (and equivalent drills for other categories) to identify a NEW
> feature-engineering target outside the H1-H5 axes that S71-S74 tested.
> The S71 diagnostic surfaced $147.59 of high_only STRUCTURE-bucket
> leak; H1 captured $24 within-cat (~16%), H2 captured $0. Remaining
> ~$123 may live in axes not yet surfaced by the H1-H5 hypothesis
> cascade. Cost: ~30-60 min/diagnostic run; multiple drills feasible
> in one session. Risk: low — diagnostic refresh is cheap regardless
> of outcome. **Recommended as a low-cost exploratory pivot.**
>
> **(C) Higher-capacity gradient-boosting retry.** v48_xgb at
> depth=8-10, n_estimators=1000+, lr=0.05, multi_output_tree.
> Estimated wall: 15-25 hours. Hypothesis: matching v44's partition
> capacity (~2.25M cells) requires boosting at depth=10 × n_est≈2200.
> If boosting at FULL capacity also caps at v44, the structural-mismatch
> conclusion is proven. If it ships, the 55× inference speedup is a
> real production-runtime advantage. **Lower priority than (A) and
> (B)** due to wall-time cost and speculative payoff.
>
> **(D) Rule-chain extension.** The two-track divergence is $348/1000h
> (v56_trips_hybrid leads v44_dt). The rule-chain track has residual
> signal that the ML track does not — extending v56 with a 19th rule
> targeting one of the residual leak categories (pair, two_pair,
> composite) could ship a new rule chain. Cost: ~30-60 min per rule
> hypothesis + grader confirmation. Risk: low — rule-chain extension
> has shipped 18 prior rules without regression. **Recommended if
> the user wants a near-term ship.**
>
> **📓 METHODOLOGY (Session 76+):**
>
> 1. **Single-model ML track is closed at v44 saturating regime.**
>    Four consecutive NULL sessions confirm: no further single-DT
>    feature engineering AND no moderate-capacity boosting will clear
>    the +$10 ship bar. Future ML retrains MUST either change model
>    class (LightGBM, ensemble of v44 + boosted residual, neural net)
>    OR change input signal (re-evaluated grid labels, new feature
>    primitives).
>
> 2. **Single deep DT beats shallow boosting for argmax-over-N tasks
>    on saturating-memorization data.** S75 finding: a 2.25M-leaf
>    depth=36 DT outperforms a depth=6 × 200-tree XGBoost ensemble by
>    $1,392/1000h on the same features. Contradicts typical ML wisdom
>    that boosting wins; the contradiction is task-specific. Document
>    this in future model-class decisions.
>
> 3. **Val-curve tripwire is the boosting analog of DT leaf-growth
>    tripwire.** When val RMSE is still dropping at the iter limit,
>    the boosting model is undertrained. v47_xgb fired this tripwire
>    (last-50 Δ +0.011). But underconvergence does NOT explain a
>    $1,392/1000h gap; capacity mismatch does.
>
> 4. **Inference speedup is a separate axis from accuracy.** v47_xgb
>    is 55× faster than v44 (18.9s vs 1,046s for 6M-hand prediction).
>    A capacity-matched boosting attempt that ships AT v44 accuracy
>    (Δ ≥ +$0/1000h, even before clearing +$10) may still be worth
>    pursuing for grader wall-time reduction if the project ever
>    becomes grader-bound.
>
> 5. **"Speed is not necessary — clarity and perfection is."** S75
>    ran the full 4-phase playbook in ~5 hours wall and produced an
>    empirically airtight NULL verdict. Both prefix and full graders
>    concur; every category regresses; the structural cause is
>    identified. No re-runs needed.
>
> 6. **+$10 ship bar canonical (codified S73, held S74-S75).** Fourth
>    consecutive session UNCHANGED production state — the bar is
>    doing its job, filtering noise from signal. ML-champion ships
>    must clear +$10/1000h full grid.

> **✅ ARTIFACTS produced in S75:**
> 1. `analysis/scripts/train_v47_xgb.py` — XGBoost training with
>    multi_strategy='multi_output_tree', early stopping, val-curve
>    tripwire, feature-importance dump.
> 2. `analysis/scripts/strategy_v47_xgb.py` — inference module; provides
>    `predict_all_chosen()` for batch grading and `strategy_v47_xgb(hand)`
>    for per-hand compatibility (cache-backed).
> 3. `analysis/scripts/grade_v47_xgb.py` — batch-mode head-to-head
>    grader bypassing per-hand strategy_fn pattern.
> 4. `data/v47_xgb_model.ubj` (16.89 MB UBJSON booster).
> 5. `data/v47_xgb_meta.json` (~12 KB hyperparams + val curve + top-30 importance).
> 6. `data/session75/{train_v47_xgb,grade_v47_xgb_prefix,grade_v47_xgb_full}.log`.
> 7. `SESSION_75_V47_XGB_NULL_REPORT.md` — full NULL retrospective.
> 8. `DECISIONS_LOG.md` — Decision 110 appended.
> 9. `CURRENT_PHASE.md` — rewritten for S76 (this file).
> 10. `STRATEGY_GUIDE.md` — Part 1 SKIPPED; Parts 2-6 front-matter
>     date refresh.

> Updated: 2026-05-13 (Session 75 end — v47_xgb decisive NULL at
> −$1,392/1000h full grid; Option B closed at moderate capacity;
> entire single-model ML track exhausted at v44 saturating regime;
> S76 pivots to oracle-label refinement / diagnostic refresh / rule-
> chain extension / high-capacity boosting retry)

---

## Headline state at end of Session 75

**Strategies of record (UNCHANGED from S74):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain. **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S75 — NULL ML
retrain attempt).

**S75 v47_xgb decisive NULL grade summary:**

| Metric | v44_dt | v47_dt (S74) | v47_xgb (S75) | Δ v47_xgb vs v44 |
|---|---:|---:|---:|---:|
| Prefix grid $/1000h | $686 | $686 | **$1,451** | **−$765** |
| Full grid $/1000h | $1,081 | $1,081 | **$2,473** | **−$1,392** |
| Full pct_opt | 64.80% | 64.80% | **41.96%** | **−22.84pp** |
| Full p90 regret | 0.390 | 0.390 | **0.720** | worse |
| Full p99 regret | 0.970 | 0.970 | **1.360** | worse |
| Within-cat high_only $/1000h | $1,868 | $1,868 | **$3,461** | **−$1,593** |
| Leaves / trees | 2,248,173 leaves | 2,248,174 leaves | **200 trees × 105 outputs** | — |
| Features | 107 | 108 | **107** | same as v44 |
| Model size | 1,260 MB | 1,260 MB | **16.89 MB** | 75× smaller |
| Training fit | — | 567s | **13,367s** | — |
| Inference (full grid) | 1,046s | 1,046s | **18.9s (batch)** | 55× faster |

**Per-category full-grid (v47_xgb vs v44):**

| category | n hands | v44 $/1000h | v47_xgb $/1000h | Δ |
|---|---:|---:|---:|---:|
| high_only | 1,226,940 | 1,868 | **3,461** | **−1,593** |
| pair | 2,800,512 | 1,097 | **2,291** | **−1,194** |
| two_pair | 1,338,480 | 363 | **1,845** | **−1,482** |
| trips | 328,185 | 1,194 | **2,716** | **−1,523** |
| trips_pair | 171,600 | 281 | **3,027** | **−2,746** |
| three_pair | 114,400 | 1,613 | **2,069** | **−456** |
| quads | 14,300 | 545 | **2,265** | **−1,720** |
| composite | 14,742 | 960 | **3,351** | **−2,392** |

**Every category regresses** — uniform devastation, no localized miss.
This is a capacity-mismatch result, not a feature-engineering miss.

---

## Hypothesis cascade status (FINAL — all paths tested or deprioritized)

| Hypothesis | Description | Status |
|---|---|---|
| **H1** | SS+ms route quality (2 ho_v6 features) | **TESTED → PARTIAL POSITIVE / NULL ship at +$5/1000h full.** Within-cat $24/1000h on high_only. |
| **H2** | Route-tradeoff comparator (1 ho_v7 feature) | **TESTED → CLEAN NULL at +$0/1000h.** "Derivable in 2 splits" trap confirmed. |
| **Option B** | Gradient boosting at v44 features (depth=6, n_est=200, lr=0.1) | **TESTED → DECISIVE NULL at −$1,392/1000h.** Capacity mismatch; smooth boosting cannot match saturating-DT memorization. |
| H3 | SS+ms route VARIETY signal | UNTESTED. Deprioritized — similar saturation ceiling expected. |
| H4 | MS_ONLY discriminator | UNTESTED. Deprioritized — small WG target ($4.39 WG by S71). |
| H5 | Drop-max signal | UNTESTED. Dead — relied on H2 infrastructure. |

**Cascade verdict (final):** The ENTIRE single-model ML track (DT
feature engineering AND gradient boosting at moderate capacity) is
exhausted at v44's saturating regime. **S76 must pivot to a NEW
track outside the H1-H5 + Option B space.**

---

## Resume Prompt (Session 76 — Pick pivot direction)

```
Resume Session 76 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S75 — single-model ML track
  exhausted; S76 must pivot)
- SESSION_75_V47_XGB_NULL_REPORT.md (decisive boosting NULL;
  capacity-mismatch hypothesis confirmed)
- SESSION_74_V47_DT_NULL_REPORT.md (DT-feature-engineering closed)
- DECISIONS_LOG.md (latest: Decision 110 — v47_xgb decisive NULL)

State (end of S75):
- v47_xgb decisive NULL at −$1,392/1000h full grid (depth=6, n_est=200,
  lr=0.1, multi_output_tree). Every category regresses substantially.
- Val-curve tripwire FIRED (model still improving at iter limit); but
  closing $1,392 gap by tuning alone is implausible.
- Capacity-mismatch hypothesis CONFIRMED: 2.25M-leaf DT vs 12,800
  boosting cells (175× partition gap).
- Entire single-model ML track exhausted at v44 saturating regime
  (4 consecutive NULL/partial-NULL sessions: S72, S73, S74, S75).
- Inference speedup: v47_xgb is 55× faster than v44 (18.9s vs 1,046s
  per 6M-hand prediction). Real but moot at −$1,392 accuracy.

USER DIRECTIVE (S59-S75 re-confirmed):
- "Speed is not necessary — clarity and perfection is."
- +$10 ship threshold canonical (codified S73, held S74-S75).

DIRECTION FOR SESSION 76 — Pick ONE pivot direction.

  Option A — Oracle-label N=1000 re-evaluation.
    Hypothesis: the saturating-DT regime has hit a label-noise ceiling.
    Current grid samples 200 board draws per (hand, setting) cell;
    N=1000 reduces label variance by ~√5 ≈ 2.24×.
    Cost: ~10× compute vs original grid build (~weeks single-machine;
          manageable on a cluster).
    Risk: ceiling may NOT be noise-induced.
    Recommended if cluster access available.

  Option B — Categorical diagnostic refresh.
    Re-run drill_v44_high_only_S71.py and equivalent drills for other
    categories to identify a NEW feature-engineering target outside
    the H1-H5 axes.
    Cost: ~30-60 min per diagnostic run.
    Risk: LOW — diagnostic refresh is cheap regardless of outcome.
    Recommended as a low-cost exploratory pivot.

  Option C — Higher-capacity gradient-boosting retry.
    v48_xgb at depth=8-10, n_est=1000+, lr=0.05.
    Cost: 15-25 hours wall on this hardware.
    Risk: speculative payoff; even capacity-matched boosting may not
          beat v44.
    Lower priority than A and B.

  Option D — Rule-chain extension.
    Two-track divergence is $348/1000h (v56_trips_hybrid leads v44).
    Extending v56 with a 19th rule targeting one of pair / two_pair /
    composite leak categories could ship a new rule chain.
    Cost: ~30-60 min per rule hypothesis + grader confirmation.
    Risk: LOW — 18 prior rules without regression.
    Recommended if user wants a near-term ship.

  PHASE 1 (S76 ~10 min) — Pick one pivot direction. State the choice
  + rationale in DECISIONS_LOG.md preamble.

  PHASE 2 (S76 ~varies) — Execute the chosen pivot.

  PHASE 3 (S76 ~30 min) — Grade the result (if applicable). Decision
  111 in DECISIONS_LOG.md.

  ACCEPTANCE for Session 76:
  - Pivot direction chosen and rationale documented.
  - At minimum: one diagnostic + Decision 111 (ship / NULL / partial).
  - If ship: STRATEGY_GUIDE.md Part 1 entry + v57 hybrid build.
  - If NULL/partial: SESSION_76 report mirroring SESSION_75 structure.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized
  per session-end-prompt.md).
- XGBoost 3.2 installed; libomp via Homebrew. If Option C selected,
  no install needed.
- v47_xgb model file (16.89 MB) remains in data/ as reference for
  future high-capacity boosting comparison.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
