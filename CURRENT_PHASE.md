# Current: Sprint 8 — Session 72 v46_dt NULL at depth=32 ml=3

S71's setting-rank diagnostic identified $147.59 WG of structurally-
addressable STRUCTURE-bucket leak in v44_dt's high_only residual,
dominated by the `SS_mu → SS_ms` mismatch family ($10+ WG across
K/Q/J/A × DS_NO_JOINT). S72 implemented H1 (2 ho_v6 features encoding
the SS+ms route-quality enumeration — direct SS-axis counterpart to
ho_v3's DS-axis pair that shipped +$79 in S57) and trained v46_dt at
the project-default regime **depth=32 ml=3** (deliberate change from
v44/v45's depth=36 ml=1 saturated regime).

**Result: NULL ship.** v46_dt regresses v44_dt by **−$32/1000h** on
the prefix grid ($686 → $718), with broad-based regression across pair
/ two_pair / trips / trips_pair / composite categories. Tripwire
indicators confirmed NULL pre-grader: ho_v6 features ranked **#79
(0.03%) and #105 (0.01%)** of 109 features — deep in the importance
tail; leaf count collapsed 51% (2.25M → 1.10M) under the regime change.

**The regime-confound is NOT YET disentangled.** v46's capacity loss
was dominated by depth+ml regime shift; we cannot conclude H1 features
are inert vs. killed-by-regime-change without an apples-to-apples
retry at v44's saturating hyperparams. **v46b_dt at depth=36 ml=1**
is the prescribed S73 retry to isolate feature effect from regime
effect.

> **🎯 IMMEDIATE NEXT ACTION (Session 73): v46b_dt retry at depth=36 ml=1**
>
>   Phase 1 (S73 ~10 min): retrain at v44's saturating hyperparams.
>     `PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v46_dt.py \
>        --max-depth 36 --min-samples-leaf 1 \
>        --output data/v46b_dt_model.npz`
>
>   Phase 2 (S73 ~5 min): copy strategy_v46_dt.py → strategy_v46b_dt.py
>   with MODEL_PATH pointing at v46b_dt_model.npz; copy grade_v46_dt.py
>   → grade_v46b_dt.py importing strategy_v46b_dt.
>
>   Phase 3 (S73 ~5 min): prefix grade vs v44_dt.
>
>   Phase 4 (S73 ~25 min): if prefix ≥ +$0/1000h, full grade vs v44_dt
>   (definitive within-cat high_only delta).
>
>   Phase 5 (S73 last ~30 min):
>     * If v46b ships ≥ +$10/1000h full → saturation hypothesis FALSE
>       for SS-axis; v46b is the new ML champion. Build v57_v46b_hybrid
>       per S70 v56 template (v44_dt → v46b_dt in trips/two_pair/
>       pair-PBOT routing of v54+v55+v56 chain).
>     * If v46b NULLs (≤ +$5/1000h full) → H1 is conclusively wrong;
>       pivot to H2 (route-tradeoff comparator) per
>       SESSION_71_V45_FEATURE_HYPOTHESES.md §6, OR pivot to gradient
>       boosting (XGBoost / LightGBM) which can correct single-tree
>       saturation residuals iteratively.
>
>   ALSO QUEUED (S73 if time permits): finish S72 Phase 4 full grader
>   for within-cat high_only WG delta on the v46_dt NULL record:
>     `PYTHONUNBUFFERED=1 python3 analysis/scripts/grade_v46_dt.py \
>        --grid full --baseline v44 2>&1 | tee data/session72/grade_v46_full.log`
>   Expected ~25-30 min; result appends to SESSION_72_V46_DT_NULL_REPORT.md.

> **✅ ARTIFACTS produced in S72:**
> 1. **`analysis/scripts/train_v46_dt.py`** — DT trainer; default
>    --max-depth 32 --min-samples-leaf 3; 107 v44 features + 2 ho_v6.
> 2. **`analysis/scripts/strategy_v46_dt.py`** — inference; loads
>    `data/v46_dt_model.npz`; ho_v6 features wired through.
> 3. **`analysis/scripts/grade_v46_dt.py`** — head-to-head grader
>    vs v44_dt (baseline) or v45_dt.
> 4. **`analysis/scripts/verify_v46_gating_S72.py`** — surgical-gating
>    sanity check (sample N hands per category; expect mismatches only
>    in high_only). **NOT run this session — queued S73.**
> 5. **`data/feature_table_high_only_aug_v6_gated.parquet`** (18.69 MB,
>    zstd) — 2 ho_v6 features × 6,009,159 canonical hands. Distribution
>    `n_configs ∈ {0,2,3,6}` matches the SS+ms enumeration algebra
>    (rest=2+2+1+1 → 2 configs; rest=3+2+1+0 → 3; rest=4+1+1+0 → 6).
> 6. **`data/v46_dt_model.npz`** (691.97 MB) — NULL model; kept for
>    reference, NOT production champion. 1,097,621 leaves at depth=32.
> 7. **`data/session72/persist_ho_v6.log`**,
>    **`data/session72/train_v46_dt.log`**,
>    **`data/session72/grade_v46_prefix.log`** — phase logs.
> 8. **`SESSION_72_V46_DT_NULL_REPORT.md`** — full NULL retrospective
>    + Decision 107 text (Appendix A) + S73 CURRENT_PHASE preview
>    (Appendix B).
> 9. **`DECISIONS_LOG.md`** — Decision 107 appended.
> 10. **`CURRENT_PHASE.md`** — rewritten for S73 (this file).
> 11. **`STRATEGY_GUIDE.md`** — Part 1 SKIPPED (no strategy of record
>     changed); Parts 2-6 front-matter date refresh only.
> 12. **Repo moved** from `~/Documents/claudecode/taiwanese/` to
>     `~/CODE/taiwanese/` mid-session to dodge macOS TCC
>     com.apple.provenance blocks on the Documents folder. See
>     S72 NULL report "BLOCKER" section.

> **📓 METHODOLOGY (Session 73+):**
> 1. **Tripwire predictions are reliable.** v45 ranked
>    #66/#97/#106/#110 → NULL. v46 ranked #79/#105 → NULL. The
>    "rank ≤50 = ship" threshold has held twice in a row. The leaf-
>    growth ≥10K criterion is a second-order confirm; on its own it
>    is confounded by hyperparam choice.
> 2. **Regime change is a separate experiment from feature design.**
>    When changing hyperparams AND feature set in the same run, NULL
>    results are uninterpretable — could be either or both. **The fix
>    is a single-variable retry** (v46b_dt at v44's regime). This is a
>    permanent addition to the 4-phase playbook: drill → hand-level →
>    features → train → **(NEW Phase 5) regime-isolation retry.**
> 3. **Surgical gating is regime-sensitive.** ho_v3/v4 were
>    byte-identical to baseline on non-high_only categories AT THE
>    SAME REGIME. Change regime + add gated features → cross-category
>    spillover. v46 regressed two_pair / trips / trips_pair by +$66 /
>    +$30 / +$183/1000h on prefix. **Same gating-by-zero, different
>    tree topology** — the byte-identity guarantee requires same
>    hyperparameters AND same base feature set. The
>    `verify_v46_gating_S72.py` script formalizes this check; queued
>    S73.
> 4. **Prefix grader is a strong NULL detector even without high_only
>    coverage.** The prefix grid has 0 high_only canonical IDs (per
>    grader by-cat breakdown — 100% pair/two_pair/trips/trips_pair/
>    three_pair/quads/composite). If a new model loses to baseline on
>    95%+ of prefix categories, the within-cat high_only improvement
>    on full would need to be HUGE to flip the verdict. v46's prefix
>    −$32 alone is decisive.
> 5. **Repo location matters for macOS TCC.** ~/Documents/ triggers
>    TCC com.apple.provenance xattrs that can block Claude Code's
>    sandboxed reads on pre-existing files. ~/CODE/ (or any
>    user-created top-level folder under ~/) is not TCC-protected.
>    **Project relocated to ~/CODE/taiwanese/** mid-S72. Future
>    sessions resume from the new path.
> 6. **"Speed is not necessary — clarity and perfection is."** S72's
>    NULL is informative: ruled out one branch of the hypothesis tree
>    cleanly. The diagnostic taxonomy (NOISE/MID/STRUCTURE) and the
>    "non-derivable feature" rule remain intact. S73 v46b_dt is the
>    cleanest possible follow-up: same features, v44's regime,
>    isolate one variable.

> Updated: 2026-05-12 (Session 72 end — v46_dt NULL at depth=32 ml=3;
> v46b_dt retry queued for S73; repo moved to ~/CODE/taiwanese/)

---

## Headline state at end of Session 72

**Strategies of record (UNCHANGED from S71):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v56_trips_hybrid** | PRODUCTION rule chain (blanket trips → v44_dt; else → v55). **$1,429 full / $794 prefix**. | `analysis/scripts/strategy_v56_trips_hybrid.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$348/1000h** (no change in S72 — pure ML retrain
attempt, NULL result).

**S72 v46_dt NULL grade summary (prefix grid, 500K canonical hands, n=1000 oracle):**

| Metric | v44_dt | v46_dt | Δ |
|---|---:|---:|---:|
| Prefix grid mean regret | 0.0686 | 0.0718 | **+0.0032** |
| Prefix grid $/1000h | $686 | **$718** | **+$32 worse** |
| Prefix grid pct_opt | 67.13% | **66.63%** | **−0.50pp** |
| Prefix p90 regret | 0.264 | 0.275 | worse |
| Prefix p99 regret | 0.624 | 0.645 | worse |
| Leaves | 2,248,173 | **1,097,621** | **−1,150,552 (−51%)** |
| Features | 107 | 109 | +2 ho_v6 |
| Depth | 36 (ml=1) | 32 (ml=3) | regime change |
| Training fit time | — | 478.3s | — |

**Per-category prefix breakdown:**

| category | n hands | v44 $/1000h | v46 $/1000h | Δ |
|---|---:|---:|---:|---:|
| pair | 215,162 | 595 | 580 | **−15 better** |
| two_pair | 204,275 | 663 | 729 | +66 worse |
| trips | 25,245 | 1,086 | 1,116 | +30 worse |
| trips_pair | 25,943 | 727 | 910 | +183 worse |
| three_pair | 25,614 | 1,143 | 1,130 | **−13 better** |
| quads | 1,100 | 783 | 743 | **−40 better** |
| composite | 2,661 | 1,226 | 1,382 | +156 worse |

**Tripwire feature importance ranking** (109 features total):

```
#79  ho_v6_topMax_SS_ms_max_mid_high_g   0.03%   (S71 prediction: top-50 = ship → AMBIGUOUS)
#105 ho_v6_topMax_SS_ms_n_configs_g      0.01%   (S71 prediction: top-50 = ship → NULL)
```

Both indicators flagged NULL pre-grader.

**Full grader NOT YET RUN.** Mid-session, macOS TCC re-applied
`com.apple.provenance` xattrs to pre-existing project files in
~/Documents/claudecode/taiwanese/, blocking `python3` and `git` from
reading project scripts. **Resolution:** repo relocated to
~/CODE/taiwanese/ which is not TCC-protected. Full grader is queued
for S73 (informational; ship/NULL decision was already decisive from
prefix).

---

## Hypothesis cascade status (per SESSION_71_V45_FEATURE_HYPOTHESES.md §6)

| Hypothesis | Description | Status |
|---|---|---|
| H1 | SS+ms route quality (2 features) | **TESTED → NULL at depth=32 ml=3.** v46b_dt at depth=36 ml=1 queued S73 to disentangle regime confound. |
| H2 | Route-tradeoff comparator (joint vs DS_NONJOINT signed delta) | UNTESTED. Queued for S74 if v46b NULLs. |
| H3 | SS+ms route VARIETY signal (max_top_suit_count) | UNTESTED. Stretch goal. |
| H4 | MS_ONLY discriminator (2 features) | UNTESTED. Smaller target ($4.39 WG). |
| H5 | Drop-max signal | UNTESTED. Needs H2 comparator to be useful. |

---

## Resume Prompt (Session 73 — v46b_dt regime-isolation retry)

```
Resume Session 73 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S72 — v46b_dt retry queued)
- SESSION_72_V46_DT_NULL_REPORT.md (NULL retrospective; the
  regime-confound story; Appendices A/B carry Decision 107 + S73
  prep text)
- SESSION_71_V45_FEATURE_HYPOTHESES.md (H2–H5 still queued)
- DECISIONS_LOG.md (latest: Decision 107 — v46_dt NULL)
- analysis/scripts/train_v46_dt.py (re-run with --max-depth 36
  --min-samples-leaf 1 --output data/v46b_dt_model.npz)
- analysis/scripts/strategy_v46_dt.py + grade_v46_dt.py
  (templates to copy for v46b variants)

State (end of S72):
- v46_dt NULL at depth=32 ml=3 (−$32/1000h prefix, broad-based;
  ho_v6 importance #79/#105; leaves collapsed 51% vs v44).
- Full grader DEFERRED (was blocked by macOS TCC; now unblocked
  after repo move to ~/CODE/taiwanese/). Queue for S73 alongside
  v46b training.
- Regime-confound NOT YET disentangled. v46b_dt at depth=36 ml=1
  same features is the single-variable retry.
- Repo moved from ~/Documents/claudecode/taiwanese/ to
  ~/CODE/taiwanese/ to dodge macOS TCC com.apple.provenance.

USER DIRECTIVE (S59-S72 re-confirmed):
- "Speed is not necessary — clarity and perfection is."

DIRECTION FOR SESSION 73 — v46b_dt retry + full S72 grader:

  PHASE 1 (S73 ~10 min) — Train v46b_dt at depth=36 ml=1:
  - `PYTHONUNBUFFERED=1 python3 analysis/scripts/train_v46_dt.py \
       --max-depth 36 --min-samples-leaf 1 \
       --output data/v46b_dt_model.npz`
  - Inspect feature importance + leaf count.
  - TRIPWIRE: ho_v6 features in top-50 + leaves ≥2.26M → ship
    signal. Otherwise NULL.

  PHASE 2 (S73 ~10 min) — Build v46b inference + grader scaffold:
  - cp strategy_v46_dt.py strategy_v46b_dt.py; change MODEL_PATH
    to v46b_dt_model.npz and rename function.
  - cp grade_v46_dt.py grade_v46b_dt.py; change import.

  PHASE 3 (S73 ~5 min) — Prefix grade v46b vs v44.
  - If v46b loses by >$10 → confirm NULL; H1 conclusively wrong.
  - If v46b wins or close → proceed to full grader.

  PHASE 4 (S73 ~30 min) — Full grade v46b vs v44 (definitive).
  - Compute within-cat high_only delta.
  - Per-category byte-identity sweep via verify_v46_gating_S72.py
    (with strategy_v46b_dt as the comparand).

  PHASE 5 (S73 last ~30 min) — Decision + hybrid extension:
  - If v46b ships ≥ +$10 WG full → Decision 108 ships v46b as new
    ML champion. Build v57_v46b_hybrid = v56 with v46b swapped in
    for v44_dt in trips/two_pair/pair-PBOT routing.
  - If v46b NULLs (≤ +$5 WG full) → Decision 108 confirms H1
    NULL; pivot to H2 OR gradient boosting (separate decision tree).

  ALSO QUEUED in parallel (S73): run S72 full grader to capture
  within-cat high_only WG delta for the NULL record:
    `PYTHONUNBUFFERED=1 python3 analysis/scripts/grade_v46_dt.py \
       --grid full --baseline v44 2>&1 | tee data/session72/grade_v46_full.log`
  (Append result table to SESSION_72_V46_DT_NULL_REPORT.md under a
  new "Phase 4 — full grader (S73 completion)" subsection.)

  ACCEPTANCE for Session 73:
  - v46b_dt trained + graded (prefix + full).
  - Decision 108 in DECISIONS_LOG.md: ship / NULL / partial.
  - If ship: STRATEGY_GUIDE.md Part 1 entry + v57 hybrid build.
  - If NULL: SESSION_73 NULL report mirroring SESSION_72; H2 or
    gradient-boosting pivot for S74.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- Session-end protocol: commit + push to origin/main (pre-authorized).
- Hyperparam choice for v46b: depth=36 ml=1 (DELIBERATE — v44's
  saturating regime, isolating feature effect from regime effect).
- Tripwire prediction: ho_v6 features at top-50 + leaves ≥2.26M
  → ship; ho_v6 features at #50+ + leaves <2.25M+1K → NULL.
- "Speed is not necessary — clarity and perfection is."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
