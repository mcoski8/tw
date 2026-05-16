# Current: Sprint 8 — Session 96 DOCUMENTATION-ONLY: **headline-goal recalibration**. 95% match%/agreement target formally retired (second-stage closure, Decision 131); **$/1000h on the production grid codified as the project's headline metric**. Production v65 UNCHANGED at $1,633.79/1000h full / $776.88 prefix; v44_dt UNCHANGED for 24th consecutive session. Three load-bearing zombie-95% references replaced (CLAUDE.md:12, CLAUDE.md:20, checklist.md:159); CURRENT_PHASE.md rewritten for S97; STRATEGY_GUIDE.md front-matter + Part 1 updated; DECISIONS_LOG Decision 131 appended; SESSION_96_REPORT.md created; MASTER_HANDOFF_01 + SPRINT_INDEX appended. **No code touched. No engine runs. No grader runs.** Rule count UNCHANGED at 25. Cumulative closure UNCHANGED at 92.09%. Match% retained as diagnostic only.

S96 closed a multi-session loop dating to Decision 033 (Session 16, 2026-04-27). Decision 033 retired the *shape-agreement* form of the 95% target in favor of "directional EV-loss reduction + non-negative absolute EV per profile" but its Consequence #1 — *"CLAUDE.md headline section may need an update reflecting the new goal framing (deferred to Session 17 — not blocking)"* — was never executed across 79 subsequent sessions. The *match%* form of the 95% target re-emerged after the S27+ ML pivot and surfaced in S79/S81/S82/S85/S95 framing despite four major lever cascades being characterized as saturated at the v44 ML architecture level: Decision 113 (S78) ML feature engineering closed at v44 capacity; Decision 117 (S82) label-quality A-path closed; Decisions 122-127 (S87-S92) chain-audit shipped $214.83/1000h then COMPLETE; Decision 129 (S94) rule-extraction bucket-level SATURATED at $5.08/1000h ceiling; Decision 130 (S95) rule-extraction intra-layout SATURATED on strongest candidate (trips B_DS_AVAIL_LKR MIXED at $4.59/$4.75). Plus S79's empirical finding that oracle labels self-disagree at 32% N=200↔N=1000 — meaning >68% match% is partially label-noise memorization, and the 95% target was set before this measurement.

Phase A audit found three load-bearing zombie-95% references in repo docs: `CLAUDE.md:12` ("Primary Goal: ... matches the solver 95%+ of the time"), `CLAUDE.md:20` ("Critical Output #4: ... matches the solver for 95-99% of hands"), `checklist.md:159` ("Push toward 95%+ agreement with conditional refinements"). Phase B drafted the replacement: PRIMARY headline metric = production strategy $/1000h on the full grid (currently $1,633.79); SECONDARY diagnostics = remaining gap to oracle ceiling ($111.41), two-track divergence ($552.79), rule count (25); operational ship standard unchanged at the pre-committed two-grid $5/1000h bar. Phase C applied edits in all six target files.

**No production change. v65 remains strategy of record. Match% retained as diagnostic only.**

| metric | pre-S96 | post-S96 | Δ |
|---|---:|---:|---:|
| Full grid (N=200) | $1,633.79 | $1,633.79 | $0.00 |
| Prefix grid (N=1000) | $776.88 | $776.88 | $0.00 |
| Production vs v44_dt | $552.79 | $552.79 | $0.00 |
| Remaining gap to oracle | $111.41 | $111.41 | $0.00 |
| Cumulative closure since pre-S68 | 92.09% | 92.09% | 0.00pp |
| Rule count | 25 | 25 | 0 |

> **🎯 IMMEDIATE NEXT ACTION (Session 97): A3 ML retrain (PRIMARY, OPERATOR AUTHORIZATION REQUIRED), OR v52-DL exploit (SECONDARY), OR v44_RULE13 fallthrough replacement (TERTIARY), OR maintenance pass on parked MIXED candidates**
>
> All rule-shipping levers (chain-audit, both rule-extraction sub-classes) characterized as saturated on the current ML architecture. Headline metric is now $/1000h on the production grid; the per-candidate $5/1000h two-grid SHIP standard is unchanged. The set of remaining open levers is small and well-defined.
>
> 1. **PRIMARY (PROMOTED from S96 SECONDARY) — A3 ML retrain (full 6M × 105 × N=1000 grid).**
>    Formally closed at v44 in S78 (Decision 113); reopening requires explicit operator authorization. Option C infrastructure provides the foundation; ~70 hours wall on current hardware (6M / 27 hands/s ≈ 222,000 s ≈ 62 h, plus retraining + grading overhead). The structural saturation findings from S91-S95 raise the question of whether a richer ML champion (with the cleaner N=1000 labels across the full grid, not just the 500K prefix or sparse subsets) would shift the saturation boundary. **The only remaining lever with potential to recover $50+/1000h.** Honest expected-outcome prior: NULL more likely than SHIP per Decisions 113 + 117 — the cascade has already established that v44's capacity at 2.25M leaves is the saturating regime for ML feature engineering, and A2's targeted retrain (S81) failed Lens-3 OOS. A3 differs by attacking the *whole grid* with cleaner labels rather than targeted subsets; whether that shifts the bottleneck or just confirms the closure is the empirical question. **Substantial compute investment for credibility-low payoff** — operator decides whether to authorize the run or close the lever explicitly.
>
> 2. **SECONDARY (PROMOTED from S96 TERTIARY) — v52-defensive-low partial-effectiveness exploit (DEFERRED from S90).**
>    Per-hand picker between v52-defensive-low and v44_dt on the ~23% of S90 hands where v52-DL wins (Decision 125 finding). Speculative — Decision 125 noted v52-DL is partially effective (recovers ~50% of v47 bleed but not fully to v44_dt); the exploit picks v52-DL only when it would win. Smaller magnitude than A3 but lower compute cost. Cheap pre-drill on N=200 first (no Option C required).
>
> 3. **TERTIARY (PROMOTED from S96 DEFERRED) — v44_RULE13 fallthrough replacement.**
>    v54/v55/v56 absorb $731+/1000h of chain bleed across pair-family already; replacement primarily matters for HIGH_ONLY (which is already gated by v64/v65 ship chain). Likely modest impact at best. Worth attempting only if both A3 and v52-DL exploit are de-scoped.
>
> 4. **MAINTENANCE OPTION — Re-evaluate parked MIXED candidates.**
>    v60 gate-11 currently MIXED at +$4.85/+$4.77 (S93 SECONDARY finding); eligible for relaxed-bar or composite-rule re-evaluation. NARROW gate of S95's trips B_DS_AVAIL_LKR candidate is MIXED at +$4.59/+$4.75. These are honest misses on the $5 bar but might compose into a meaningful joint ship if multiple borderline rules can be combined. Smaller scope than A3 but lower-risk and matches the user's "speed is not necessary — clarity and perfection is" directive.

> **📓 METHODOLOGY (Session 97+ — carried + refined through S96):**
>
> 1. **HEADLINE METRIC: $/1000h ON THE PRODUCTION GRID (NEW S96).**
>    Production strategy $/1000h on the full grid (N=200, RealisticHumanMixture, 6M canonical hands). Currently $1,633.79. Secondary diagnostics: remaining gap to oracle ceiling, two-track divergence (production vs v44_dt), rule count. **Match% is retained as a diagnostic only** — still useful for debugging, still comparable across sessions, but not the headline. The pre-committed two-grid SHIP standard at $5/1000h is the operational form of the new headline; nothing about per-candidate evaluation changes.
>
> 2. **DOC DRIFT COMPOUNDS — PERIODIC AUDITS CATCH IT (NEW S96).**
>    Decision 033 deferred a CLAUDE.md update as "not blocking" → never done across 79 sessions. The zombie 95% framing lurked in load-bearing docs through ~30 sessions of saturation evidence accumulating. **Annual or post-pivot audits of CLAUDE.md / checklist.md headlines against actual project state are worth running** (~1 session of grep + careful editing).
>
> 3. **HEADLINE RECALIBRATIONS REQUIRE MULTI-LEVER CLOSURE EVIDENCE (NEW S96).**
>    The S96 recalibration is not a "lowering the bar to ship" move — the per-candidate $5/1000h SHIP standard is unchanged. It is a "calling the finish-line where the evidence already pointed" move, motivated by three saturation closures (Decisions 113, 117, 129+130) plus two completions (Decisions 122-127) over 18 sessions. **Cascade recalibrations should require this kind of multi-lever closure pattern, not a single NULL session.**
>
> 4. **$/1000H SURVIVES LABEL NOISE WHERE MATCH% DOES NOT (NEW S96).**
>    32% oracle self-disagreement at N=200↔N=1000 (S79) means any match% > 68% on N=200 is partially memorizing label noise. $/1000h averaged across 6M × 105 × N is robust by CLT. Pick a metric the data quality supports.
>
> 5. **PICKER ALIGNMENT IS THE SECOND NECESSARY CONDITION FOR RULE EXTRACTION (carried from S95).**
>    Beyond S94's trigger-predictivity ≥ 62-70% requirement, the rule's deterministic picker must also align with oracle's specific pick within the predicted direction. High direction predictivity is necessary but not sufficient. Both conditions must be empirically verified for each new cell. Picker criteria are cell-specific, not transferable — Rule 20/25's `bot_pair_high` priorities bot strength which doesn't carry over to trips where bot strength = trip card. Validate empirically via 8-criterion sweep (3-min cost; can swing lift by $7+/1000h).
>
> 6. **OPTION C N=1000 SPARSE INFRASTRUCTURE IS PROJECT STANDARD (carried).**
>    Throughput ~25-27 hands/s parallel; bit-identical to existing prefix grid by construction; unblocks the two-grid SHIP standard on arbitrary cell subsets. Used in S93 (SHIP) and S95 (MIXED) so far. If A3 is authorized for S97, this infrastructure is what makes the ~70h wall feasible at all.
>
> 7. **PRE-COMMITTED VERDICT PATTERN (project standard, unchanged).**
>    Thresholds locked in code BEFORE the data is read. The verdict falls out mechanically. Critical for A3 — pre-commit a multi-grid bar ("retrained DT beats v44_dt by ≥$X full + ≥$Y prefix OR full grid ≥$Z absolute") before launching the ~70h run, not after.

> **✅ ARTIFACTS produced in S96:**
> 1. `CLAUDE.md` — lines 12 + 20 rewritten; Decisions-033+131 pointer paragraph added (EDIT)
> 2. `checklist.md` — lines 158-159 struck through with decision pointers; line 160 deprioritized (EDIT)
> 3. `DECISIONS_LOG.md` — Decision 131 appended (APPEND)
> 4. `CURRENT_PHASE.md` — this file, rewritten for S97 (REWRITE)
> 5. `STRATEGY_GUIDE.md` — front-matter "Last updated" stanza updated for S96; Part 1 appended with Session 96 entry (MIXED — front-matter + Part 1)
> 6. `SESSION_96_REPORT.md` — plain-language session report + full data (NEW)
> 7. `handoff/MASTER_HANDOFF_01.md` — S96 entry appended (APPEND)
> 8. `sprints/SPRINT_INDEX.md` — S96 entry appended (APPEND)

> Updated: 2026-05-16 (Session 96 end — **STRATEGY OF RECORD UNCHANGED: v65 remains production. HEADLINE METRIC FORMALLY RECALIBRATED: 95% match% retired (second-stage closure, Decision 131); $/1000h on the production grid is the project's headline metric.** No code touched. No engine runs. Match% retained as diagnostic only. S97 PRIMARY: A3 ML retrain (operator authorization required); S97 SECONDARY: v52-DL exploit; S97 TERTIARY: v44_RULE13 fallthrough replacement; MAINTENANCE option: re-evaluate parked MIXED candidates.)

---

## Headline state at end of Session 96

**Strategies of record (UNCHANGED from S95):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for **24 sessions**, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$111.41/1000h** (UNCHANGED). Cumulative closure since pre-S68: $1,297.59 = **92.09% of original $1,409** (UNCHANGED).

Production vs v44_dt: production outperforms ML by **$552.79/1000h** (UNCHANGED).

**Total project rule count: 25** (UNCHANGED).

**S96 results (HEADLINE RECALIBRATED, no production change):**

| Lever | Change |
|---|---|
| Headline metric | Match% → $/1000h on production grid (Decision 131) |
| CLAUDE.md Primary Goal | Updated to drop 95%+ framing; Decisions-033+131 pointer added |
| CLAUDE.md Critical Output #4 | Reworded to report $/1000h + remaining gap + two-track divergence |
| checklist.md 70%+ / 95%+ agreement tasks | Struck through with decision pointers |
| Pre-committed two-grid SHIP standard | UNCHANGED ($5/1000h both grids) |

---

## Hypothesis cascade status (updated after S96)

| Hypothesis | Description | Status |
|---|---|---|
| H1 | high_only SS+ms route quality | NULL ship +$5 (S73). |
| H2 | high_only route-tradeoff | CLEAN NULL +$0 (S74). |
| Option B (S75) | Gradient boosting at depth=6 / n_est=200 | DECISIVE NULL −$1,392/1000h. |
| S76 / S77 diagnostics | Cross-cat → pair drill | Shipped diagnostics; identified H6/H7/H8 + LOW pair under-coverage. |
| H6 / H7 / H8 (S78) | Pair gated features | CLEAN NULL +$2 prefix. |
| Single-model ML feature-engineering track | At v44 saturating regime | FORMALLY CLOSED (Decision 113). |
| A1 (S80) | Retrain v44 DT on N=1000 prefix labels | LIFTS +13.15pp on N=1000 match rate; in-sample evaluation caveat (Decision 115). |
| C2 (S80) | Regularize v44 DT (max_leaf_nodes=500K, ml=5) | NULL −2.13pp on N=1000, −12.24pp on N=200 (Decision 115). |
| A2 (S81/S82) | Targeted N=1000 expansion on two_pair + trips_pair + held-out validation | CLEAN NULL — Lens-3 held-out 63.74% < 72.0% floor (Decision 117). |
| A-path (oracle-label-quality lever) | All variants tested at v44 capacity | FORMALLY CLOSED at v44 regime (Decision 117). |
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — Option C is the foundation; ~70h wall on current hardware. **PROMOTED to S97 PRIMARY (operator authorization required).** |
| Headline-goal recalibration | Concede 95% match% as unreachable | **CLOSED — Decision 131 (S96). Match% retired as headline; $/1000h on production grid is the new metric. Match% retained as diagnostic only.** |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86/S93) | MID × PMID_DS_NOMAXTOP | SHIPPED — Rule 25 + $6.43 (Decision 128). |
| DAMAGE-CONTROL chain audit cells #1-4 (S87-S90) | HIGH_ONLY × various | SHIPPED 4 rules totaling $214.83/1000h (Decisions 122-125). |
| DAMAGE-CONTROL chain audit cell #5 (S91) | LOW pair PMID prefix-COVERED | NULL — population-divergence noise (Decision 126). |
| DAMAGE-CONTROL chain audit cell #6 + #7 (S92) | two_pair + trips chain audit | STRUCTURAL NULL — chain collapsed by v55/v56 blanket routing (Decision 127). |
| Chain-audit arc (S87-S92 closure) | 5 sessions across 4 categories | COMPLETE — 4 SHIPS ($214.83/1000h) + 2 NULLs at well-characterized boundaries. |
| Option C N=1000 oracle infrastructure (S93) | Engine `--id-list-file` mode | SHIPPED — bit-identical to prefix grid; ~25-27 hands/s parallel. Decision 128. Used in S93 (SHIP) and S95 (MIXED). |
| Option D-revised rule extraction within-v44_dt residual (S94) | bucket-level on 10 cells | STRUCTURAL NULL — bucket-level trigger predictivity below 62-70% Rule 25/Rule 20 anchor across all 10 cells. Decision 129. |
| Option D-revised rule extraction intra-Layout-A bot_suit (S95) | trips B_DS_AVAIL_LKR intra-Layout-A | MIXED — best gate NARROW $+4.59/$+4.75 N=200/N=1000, $0.25 short of $5 SHIP bar on each grid. Decision 130. |
| Rule-extraction arc (S83-S95 closure) | bucket-level + intra-layout sub-classes | COMPLETE. 2 SHIPS (Rules 20, 25) + 2 MIXED (S84, S95) + 2 NULL (S85, S94 bucket-level). |
| **Headline-goal recalibration (S96)** | **Match% retired second-stage; $/1000h on production grid codified** | **CLOSED — Decision 131. CLAUDE.md + checklist.md updated.** |
| v60 gate=11 (S93 SECONDARY finding) | MID × PMID_DS_NOMAXTOP × max_sing ≤ J | MIXED at +$4.85/+$4.77; eligible for relaxed-bar or composite-rule re-evaluation. |
| v52-defensive-low refinement (S90 finding) | Per-hand picker between v52-DL and v44 | DEFERRED — speculative; **PROMOTED to S97 SECONDARY**. |

**Cascade verdict (post S96):** Chain-audit lever exhausted. Rule-extraction lever exhausted across both sub-classes. Headline-goal recalibration **closed** (Decision 131). All remaining open levers (A3 ML retrain, v52-DL exploit, v44_RULE13 replacement) require either operator authorization (A3, ~70h wall) or are speculative/lower-magnitude (v52-DL, v44_RULE13).

* **ML cascade:** EXHAUSTED at v44 saturating regime (no change since S78 / Decision 113). A3 retrain is the only remaining lever.
* **Rule-layer cascade — chain audit (S87-S92):** COMPLETE. $214.83/1000h shipped + 2 NULLs at boundaries.
* **Rule-layer cascade — Option D-revised rule extraction (S83-S95):** $23.24/1000h cumulative across two ships (Rules 20 + 25) + S94 bucket-level saturation + S95 intra-layout MIXED. Both sub-classes EXHAUSTED.
* **Infrastructure cascade (S93+S95):** Option C N=1000 sparse-grid infrastructure available for any future cell-scale validation. Used twice (S93 SHIP, S95 MIXED).
* **Headline-goal cascade (S96):** Recalibrated. $/1000h on production grid is the headline metric. Match% retained as diagnostic.

---

## Resume Prompt (Session 97 — A3 ML retrain / v52-DL exploit / v44_RULE13 replacement / maintenance pass)

```
Resume Session 97 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md (UPDATED end of S96 — Primary Goal + Critical Output #4 rewritten;
  Decisions-033+131 pointer paragraph added under Primary Goal)
- CURRENT_PHASE.md (rewritten end of S96 — opens with the S97 pivot plan;
  headline metric is now $/1000h on production grid; all rule-shipping
  levers characterized as saturated)
- DECISIONS_LOG.md (latest: Decision 131 — S96 headline-goal recalibration;
  95% match% formally retired second-stage; $/1000h on production grid
  codified as headline metric)
- SESSION_96_REPORT.md (S96 doc-only session report; full audit + draft +
  edits trail)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/session93/v60_n1000_sparse.bin — S93 sparse N=1000 grid (32,304 hands)
- data/session95/v66_n1000_sparse.bin — S95 sparse N=1000 grid (51,531 hands)
- data/v44_dt_model.npz — production ML champion (UNCHANGED 24 sessions)

STATE (end of S96):
- Production rule chain: v65_mid_pair_chain_extend ($1,633.79 full /
  $776.88 prefix). UNCHANGED from S93.
- ML champion v44_dt UNCHANGED (24 consecutive sessions).
- Two-track divergence (remaining gap to oracle): $111.41/1000h.
- Rule count: 25 (UNCHANGED).
- Cumulative closure since pre-S68: 92.09% of original $1,409.
- Combined S87-S93 production-chain recovery: $221.26/1000h.
  S94 + S95 + S96 contribute $0.
- KEY S96 OUTCOME: headline metric formally recalibrated to $/1000h on
  the production grid (Decision 131). 95% match% retired second-stage
  (Decision 033 had retired the shape-agreement form in S16, never
  applied to docs). CLAUDE.md + checklist.md zombie-95% framing replaced;
  STRATEGY_GUIDE.md front-matter + Part 1 updated; CURRENT_PHASE.md
  rewritten for S97. NO code touched. NO engine runs.
- Match% retained as diagnostic only — still informative for debugging,
  comparable across sessions, but not the headline.
- All rule-shipping levers (chain-audit, bucket-level rule-extraction,
  intra-layout rule-extraction) characterized as saturated on current
  ML architecture. Remaining open lever set: A3, v52-DL exploit,
  v44_RULE13 replacement.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard."
- User is non-technical; session reports lead with plain-language TL;DR.
- Session-end commit + push is pre-authorized.

DIRECTION FOR SESSION 97 — A3 / v52-DL / v44_RULE13 / maintenance pass:

  PRIMARY (PROMOTED from S96 SECONDARY):
  A3 ML retrain (full 6M × 105 × N=1000 grid).

  Formally closed at v44 in S78 (Decision 113); reopening requires
  explicit operator authorization. Option C infrastructure provides
  the foundation; ~70 hours wall on current hardware (6M / 27 hands/s
  ≈ 222,000 s ≈ 62 h + retraining + grading overhead). The only
  remaining lever with potential to recover $50+/1000h. **Honest
  expected-outcome prior: NULL more likely than SHIP** per Decisions
  113 + 117 — the cascade has already established v44's 2.25M-leaf
  capacity as the saturating regime for ML feature engineering, and
  A2's targeted retrain (S81) failed Lens-3 OOS. A3 differs by
  attacking the *whole grid* with cleaner N=1000 labels rather than
  targeted subsets; whether that shifts the bottleneck or just
  confirms the closure is the empirical question. Substantial compute
  investment for credibility-low payoff — operator decides whether to
  authorize or close the lever explicitly.

  Engineering scope (multi-session):
  * Phase A (~1 session): pre-flight pilot run on 50K-hand subset to
    confirm engine throughput + checkpoint logic at N=1000 on full
    grid (current Option C runs are 30K-50K hands).
  * Phase B (~3 days wall + monitoring): launch full 6M run via
    Option C `--id-list-file` mode with checkpoint/resume; estimated
    ~70h wall. Background; check progress every 8-12h.
  * Phase C (~1 session): retrain v44_dt architecture (depth=36 ml=1,
    107 features) on the new labels; capacity-retest at depth=34 ml=2
    and depth=32 ml=3 (per project_taiwanese_capacity_retest memory).
  * Phase D (~1 session): grade vs v44_dt + v65 production at
    pre-committed bars (e.g., new DT beats v44_dt by ≥$X full +
    ≥$Y prefix; new production = v65 with new DT substituted beats
    current v65 by ≥$5 full + ≥$5 prefix per the two-grid SHIP standard).

  ALTERNATIVE DIRECTIONS:

  (a) v52-defensive-low partial-effectiveness exploit (SECONDARY,
      promoted from S96 TERTIARY). Per-hand picker between v52-DL
      and v44_dt on the ~23% of S90 hands where v52-DL wins
      (Decision 125 finding). Speculative — Decision 125 noted
      v52-DL is partially effective (recovers ~50% of v47 bleed but
      not fully to v44_dt); the exploit picks v52-DL only when it
      would win. Smaller magnitude than A3 but lower compute cost.
      Cheap pre-drill on N=200 first (no Option C required).

  (b) v44_RULE13 fallthrough replacement (TERTIARY, promoted from
      S96 DEFERRED). v54/v55/v56 absorb $731+/1000h of chain bleed
      across pair-family already; replacement primarily matters for
      HIGH_ONLY (already gated by v64/v65 chain). Likely modest
      impact at best.

  (c) MAINTENANCE — Re-evaluate parked MIXED candidates as composite
      rules. v60 gate-11 MIXED at +$4.85/+$4.77 (S93 SECONDARY);
      S95 NARROW gate MIXED at +$4.59/+$4.75. Both honest misses on
      the $5 bar; might compose into a meaningful joint ship.
      Smaller scope than A3, lower-risk, matches "speed is not
      necessary — clarity and perfection is" directive.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged (24 sessions).
- v65_mid_pair_chain_extend is the production rule chain (UNCHANGED).
- v55_two_pair_hybrid + v56_trips_hybrid blanket-route their targets to
  v44_dt unconditionally — DO NOT undo this routing without quantifying
  the $515+$33 bleed they currently absorb (S92 finding).
- v54 + Rule 29 absorb $195 of chain bleed on LOW pair (S91 quantified).
- The pre-committed-verdict pattern is project standard. Critical for
  A3: pre-commit a multi-grid bar BEFORE launching the ~70h run.
- NEW S96: HEADLINE METRIC IS $/1000h ON PRODUCTION GRID (Decision 131).
  Match% retained as diagnostic only.
- NEW S96: Doc drift compounds — periodic audits of CLAUDE.md /
  checklist.md against actual project state catch zombie targets cheaply.
- CARRIED from S94: trigger predictivity ≥ 62-70% is the operational
  definition of "rule extractable" (Rule 20: 89%, Rule 25: 62%).
- CARRIED from S95: picker alignment with oracle's specific pick is the
  SECOND necessary condition for rule extraction. Picker criteria are
  cell-specific, not transferable.
- Option C N=1000 sparse infrastructure remains available (S93 + S95 use);
  for A3, scale from sparse-subset to full-grid is the empirical question.
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
