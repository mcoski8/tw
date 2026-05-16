# Current: Sprint 8 — Session 97 STRUCTURAL NULL on the MAINTENANCE lever. **Production v65 UNCHANGED.** v60-gate11 (the S96 MAINTENANCE candidate carried at "MIXED +$4.85/+$4.77") is empirically absorbed by v65 on 14,160 / 14,160 firing hands — Rule 25 = v60-gate12 already covers its firing zone with identical picker logic. Composite hypothesis collapses to v66-NARROW alone, locked MIXED at +$4.59/+$4.75 per S95. Decision 132 closes the maintenance lever. v44_dt UNCHANGED for 25th consecutive session. Rule count UNCHANGED at 25. Cumulative closure UNCHANGED at 92.09%. One new analysis script + one JSON output. No engine runs. No grader runs. No production change.

S97 executed S96's MAINTENANCE option — re-evaluate the two parked MIXED candidates as a joint composite ship. Phase A relocated both candidates' strategy scripts (`strategy_v60_mid_pair_ds_nomaxtop.py` defaults to gate=11; `strategy_v66_trips_layout_a_force_ds_bot.py` defaults to NARROW gate). Phase B identified a structural concern *before any code ran*: v60-gate11 fires on `max_sing ≤ J` (gate parameter = 11), while v65 ships v60-gate12 firing on `max_sing ≤ Q` (gate parameter = 12) with **the same picker function**. The two are not independent — gate-11's firing zone is a strict subset of gate-12's. Phase C confirmed empirically: 14,160 / 14,160 = 100.0000% of v60-gate11 firing hands have `v65_pick == v60_gate11_pick`. Zero hands fell through to v57. The S93 SECONDARY's "+$4.85 N=200 / +$4.77 N=1000" was measured against the **v57 baseline** (pre-Rule-25); not against current production v65. Phase D: the composite hypothesis reduces to v66-NARROW alone, which is locked MIXED at $+4.59/$+4.75 (both grids $0.25 short of the $5 SHIP bar) per S95's cached grading (`data/session95/grade_v66_n1000_summary.json`). Phase E (Decision 132): close the maintenance lever as STRUCTURAL NULL.

**No production change. v65 remains strategy of record. v66-NARROW characterization (MIXED) is unchanged.**

| metric | pre-S97 | post-S97 | Δ |
|---|---:|---:|---:|
| Full grid (N=200) | $1,633.79 | $1,633.79 | $0.00 |
| Prefix grid (N=1000) | $776.88 | $776.88 | $0.00 |
| Production vs v44_dt | $552.79 | $552.79 | $0.00 |
| Remaining gap to oracle | $111.41 | $111.41 | $0.00 |
| Cumulative closure since pre-S68 | 92.09% | 92.09% | 0.00pp |
| Rule count | 25 | 25 | 0 |

> **🎯 IMMEDIATE NEXT ACTION (Session 98): A3 ML retrain (PRIMARY, OPERATOR AUTHORIZATION REQUIRED), OR v52-DL exploit (SECONDARY), OR v44_RULE13 fallthrough replacement (TERTIARY)**
>
> The MAINTENANCE option (S96 + S97 thread) is now CLOSED: both parked MIXED candidates have been fully accounted for (v60-gate11 STRUCTURALLY ABSORBED by v65 per Decision 132; v66-NARROW locked MIXED at $+4.59/$+4.75 per S95 / Decision 130). Headline metric remains $/1000h on the production grid (Decision 131). The pre-committed $5 two-grid SHIP standard is unchanged.
>
> 1. **PRIMARY (UNCHANGED from S97 plan) — A3 ML retrain (full 6M × 105 × N=1000 grid).**
>    Formally closed at v44 in S78 (Decision 113); reopening requires explicit operator authorization. Option C infrastructure provides the foundation; ~70 hours wall on current hardware (6M / 27 hands/s ≈ 222,000 s ≈ 62 h, plus retraining + grading overhead). The structural saturation findings from S91-S95 + S97 raise the question of whether a richer ML champion (with the cleaner N=1000 labels across the full grid, not just the 500K prefix or sparse subsets) would shift the saturation boundary. **The only remaining lever with potential to recover $50+/1000h.** Honest expected-outcome prior: NULL more likely than SHIP per Decisions 113 + 117 — the cascade has already established that v44's capacity at 2.25M leaves is the saturating regime for ML feature engineering, and A2's targeted retrain (S81) failed Lens-3 OOS. A3 differs by attacking the *whole grid* with cleaner labels rather than targeted subsets; whether that shifts the bottleneck or just confirms the closure is the empirical question. **Substantial compute investment for credibility-low payoff** — operator decides whether to authorize the run or close the lever explicitly.
>
> 2. **SECONDARY (UNCHANGED) — v52-defensive-low partial-effectiveness exploit.**
>    Per-hand picker between v52-defensive-low and v44_dt on the ~23% of S90 hands where v52-DL wins (Decision 125 finding). Speculative — Decision 125 noted v52-DL is partially effective (recovers ~50% of v47 bleed but not fully to v44_dt); the exploit picks v52-DL only when it would win. Smaller magnitude than A3 but lower compute cost. Cheap pre-drill on N=200 first (no Option C required). Single-session feasible to characterize.
>
> 3. **TERTIARY (UNCHANGED) — v44_RULE13 fallthrough replacement.**
>    v54/v55/v56 absorb $731+/1000h of chain bleed across pair-family already; replacement primarily matters for HIGH_ONLY (which is already gated by v64/v65 ship chain). Likely modest impact at best.
>
> 4. **MAINTENANCE OPTION — CLOSED (Decision 132).** v60-gate11 structurally absorbed by v65; v66-NARROW characterization unchanged from S95.

> **📓 METHODOLOGY (Session 98+ — carried + refined through S97):**
>
> 1. **PARKED-CANDIDATE BOOK-KEEPING MUST RECORD BASELINE + RE-GRADE BEFORE COMPOSITE HYPOTHESES (NEW S97).**
>    A candidate's "+$X lift" reading is baseline-relative. If a related candidate from the same cell ships between the grading and the composite-hypothesis attempt, the +$X reading becomes double-counted relative to current production. v60-gate11's +$4.85 from S93 SECONDARY was true vs v57 at the time, but became stale the moment Rule 25 (= v60-gate12) shipped — gate=11's firing zone is a strict subset of gate=12's. Future parked-candidate annotations should record (a) the baseline strategy the lift was measured against, and (b) a re-grade-against-current-production check before any composite hypothesis. Decision 131's lesson was about zombie *headline* framing; this is about zombie *candidate* framing.
>
> 2. **STRUCTURAL SUBSET CHECKS ARE CHEAP AND DECISIVE (carried, reinforced S97).**
>    Cells like `max_sing ≤ J` ⊂ `max_sing ≤ Q` are immediately testable on the per-hand picks NPZ that already exists; no engine run is needed to decide whether a candidate is structurally absorbed by current production. S97 closed the v60-gate11 question in ~5 minutes of code + 3.4 seconds of compute. If the structural relationship had been checked at S93 SECONDARY framing time, the candidate wouldn't have been carried as "open" for 4 sessions.
>
> 3. **HEADLINE METRIC: $/1000h ON THE PRODUCTION GRID (carried from S96, Decision 131).**
>    Production strategy $/1000h on the full grid (N=200, RealisticHumanMixture, 6M canonical hands). Currently $1,633.79. Secondary diagnostics: remaining gap to oracle ceiling, two-track divergence (production vs v44_dt), rule count. Match% retained as diagnostic only — still useful for debugging, still comparable across sessions, but not the headline. The pre-committed two-grid SHIP standard at $5/1000h is the operational form of the new headline.
>
> 4. **PICKER ALIGNMENT IS THE SECOND NECESSARY CONDITION FOR RULE EXTRACTION (carried from S95).**
>    Beyond S94's trigger-predictivity ≥ 62-70% requirement, the rule's deterministic picker must also align with oracle's specific pick within the predicted direction. High direction predictivity is necessary but not sufficient. Both conditions must be empirically verified for each new cell. Picker criteria are cell-specific, not transferable.
>
> 5. **OPTION C N=1000 SPARSE INFRASTRUCTURE IS PROJECT STANDARD (carried).**
>    Throughput ~25-27 hands/s parallel; bit-identical to existing prefix grid by construction; unblocks the two-grid SHIP standard on arbitrary cell subsets. Used in S93 (SHIP) and S95 (MIXED) so far. If A3 is authorized for S98, this infrastructure is what makes the ~70h wall feasible at all.
>
> 6. **PRE-COMMITTED VERDICT PATTERN (project standard, unchanged).**
>    Thresholds locked in code BEFORE the data is read. The verdict falls out mechanically. Critical for A3 — pre-commit a multi-grid bar ("retrained DT beats v44_dt by ≥$X full + ≥$Y prefix OR full grid ≥$Z absolute") before launching the ~70h run, not after.

> **✅ ARTIFACTS produced in S97:**
> 1. `analysis/scripts/spot_check_v60g11_subset_v65_S97.py` — empirical verifier of v60-gate11 ⊂ v65 (NEW)
> 2. `data/session97/spot_check_v60g11_subset_v65.json` — structural-absorption result (NEW)
> 3. `SESSION_97_REPORT.md` — plain-language session report + full data (NEW)
> 4. `DECISIONS_LOG.md` — Decision 132 appended (APPEND)
> 5. `CURRENT_PHASE.md` — this file, rewritten for S98 (REWRITE)
> 6. `STRATEGY_GUIDE.md` — front-matter "Last updated" stanza updated for S97; Part 1 NOT updated (no champion change, S96 convention)
> 7. `MASTER_HANDOFF_01.md` — S97 entry appended (APPEND)
> 8. `sprints/SPRINT_INDEX.md` — S97 entry appended (APPEND)

> Updated: 2026-05-16 (Session 97 end — **STRATEGY OF RECORD UNCHANGED: v65 remains production. v66-NARROW characterization UNCHANGED: MIXED $+4.59/$+4.75.** MAINTENANCE LEVER CLOSED (Decision 132): v60-gate11 structurally absorbed by v65. S98 PRIMARY: A3 ML retrain (operator authorization required); S98 SECONDARY: v52-DL exploit; S98 TERTIARY: v44_RULE13 fallthrough replacement.)

---

## Headline state at end of Session 97

**Strategies of record (UNCHANGED from S96):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for **25 sessions**, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$111.41/1000h** (UNCHANGED). Cumulative closure since pre-S68: $1,297.59 = **92.09% of original $1,409** (UNCHANGED).

Production vs v44_dt: production outperforms ML by **$552.79/1000h** (UNCHANGED).

**Total project rule count: 25** (UNCHANGED).

**S97 results (MAINTENANCE LEVER CLOSED, no production change):**

| Lever | Change |
|---|---|
| Maintenance composite (v60-gate11 + v66-NARROW) | STRUCTURAL NULL — v60-gate11 absorbed by v65 (Decision 132) |
| v60-gate11 status | "MIXED parked candidate" → "STRUCTURALLY ABSORBED by v65" |
| v66-NARROW status | UNCHANGED — MIXED at $+4.59/$+4.75 (S95) |
| Pre-committed two-grid SHIP standard | UNCHANGED ($5/1000h both grids) |
| Headline metric | UNCHANGED — $/1000h on production grid (Decision 131) |

---

## Hypothesis cascade status (updated after S97)

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
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — Option C is the foundation; ~70h wall on current hardware. **S98 PRIMARY (operator authorization required).** |
| Headline-goal recalibration | Concede 95% match% as unreachable | CLOSED — Decision 131 (S96). Match% retired as headline; $/1000h on production grid is the new metric. |
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
| Headline-goal recalibration (S96) | Match% retired second-stage; $/1000h on production grid codified | CLOSED — Decision 131. CLAUDE.md + checklist.md updated. |
| **Maintenance composite (S97)** | **Re-evaluate parked MIXED candidates as joint composite** | **STRUCTURAL NULL — v60-gate11 absorbed by v65 (Rule 25 = v60-gate12); composite reduces to v66-NARROW alone (MIXED). Decision 132.** |
| v60 gate=11 status | MID × PMID_DS_NOMAXTOP × max_sing ≤ J | **STRUCTURALLY ABSORBED by v65 (Decision 132, S97). 14,160 / 14,160 firing hands have v65_pick == v60_gate11_pick.** |
| v66 NARROW (trips × B_DS_AVAIL_LKR × intra-Layout-A) | Per Decision 130 (S95) | Status unchanged: MIXED $+4.59/$+4.75, locked by two-grid bar. |
| v52-defensive-low refinement (S90 finding) | Per-hand picker between v52-DL and v44 | DEFERRED — speculative; remains S98 SECONDARY. |

**Cascade verdict (post S97):** Chain-audit lever exhausted. Rule-extraction lever exhausted across both sub-classes. Headline-goal recalibration closed (Decision 131). Maintenance lever closed (Decision 132). All remaining open levers (A3 ML retrain, v52-DL exploit, v44_RULE13 replacement) require either operator authorization (A3, ~70h wall) or are speculative/lower-magnitude (v52-DL, v44_RULE13).

* **ML cascade:** EXHAUSTED at v44 saturating regime (no change since S78 / Decision 113). A3 retrain is the only remaining lever.
* **Rule-layer cascade — chain audit (S87-S92):** COMPLETE. $214.83/1000h shipped + 2 NULLs at boundaries.
* **Rule-layer cascade — Option D-revised rule extraction (S83-S95):** $23.24/1000h cumulative across two ships (Rules 20 + 25) + S94 bucket-level saturation + S95 intra-layout MIXED. Both sub-classes EXHAUSTED.
* **Infrastructure cascade (S93+S95):** Option C N=1000 sparse-grid infrastructure available for any future cell-scale validation. Used twice (S93 SHIP, S95 MIXED).
* **Headline-goal cascade (S96):** Recalibrated. $/1000h on production grid is the headline metric. Match% retained as diagnostic.
* **Maintenance cascade (S97):** Closed. v60-gate11 absorbed by v65; v66-NARROW unchanged MIXED.

---

## Resume Prompt (Session 98 — A3 ML retrain / v52-DL exploit / v44_RULE13 replacement)

```
Resume Session 98 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md (UPDATED end of S96 — Primary Goal + Critical Output #4 rewritten;
  Decisions-033+131 pointer paragraph under Primary Goal)
- CURRENT_PHASE.md (rewritten end of S97 — opens with the S98 pivot plan;
  MAINTENANCE lever closed, headline metric is $/1000h on production grid)
- DECISIONS_LOG.md (latest: Decision 132 — S97 maintenance lever closure;
  v60-gate11 empirically absorbed by v65, composite hypothesis collapses)
- SESSION_97_REPORT.md (S97 spot-check session report; full structural-
  absorption proof on 14,160 / 14,160 v60-gate11 firing hands)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/session93/v60_n1000_sparse.bin — S93 sparse N=1000 grid (32,304 hands)
- data/session95/v66_n1000_sparse.bin — S95 sparse N=1000 grid (51,531 hands)
- data/session97/spot_check_v60g11_subset_v65.json — S97 structural-
  absorption proof (NEW)
- data/v44_dt_model.npz — production ML champion (UNCHANGED 25 sessions)

STATE (end of S97):
- Production rule chain: v65_mid_pair_chain_extend ($1,633.79 full /
  $776.88 prefix). UNCHANGED from S93.
- ML champion v44_dt UNCHANGED (25 consecutive sessions).
- Two-track divergence (remaining gap to oracle): $111.41/1000h.
- Rule count: 25 (UNCHANGED).
- Cumulative closure since pre-S68: 92.09% of original $1,409.
- Combined S87-S93 production-chain recovery: $221.26/1000h.
  S94 + S95 + S96 + S97 contribute $0.
- KEY S97 OUTCOME: maintenance lever closed as STRUCTURAL NULL
  (Decision 132). v60-gate11 (parked at +$4.85/+$4.77 from S93 SECONDARY)
  empirically absorbed by v65 on 14,160 / 14,160 firing hands — Rule 25
  = v60-gate12 already covers the firing zone with byte-identical picker.
  The S93 lift was measured vs v57 baseline (pre-Rule-25); not vs current
  v65. Composite reduces to v66-NARROW alone, MIXED at +$4.59/+$4.75 per
  S95 (locked by two-grid bar). NO code changes to strategy or engine.
  ONE new analysis script (spot_check_v60g11_subset_v65_S97.py) + one
  JSON output.
- The MAINTENANCE option is now CLOSED. Remaining open lever set: A3,
  v52-DL exploit, v44_RULE13 replacement.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard."
- User is non-technical; session reports lead with plain-language TL;DR.
- Session-end commit + push is pre-authorized.

DIRECTION FOR SESSION 98 — A3 / v52-DL / v44_RULE13:

  PRIMARY (UNCHANGED from S97 plan):
  A3 ML retrain (full 6M × 105 × N=1000 grid).

  Formally closed at v44 in S78 (Decision 113); reopening requires
  explicit operator authorization. Option C infrastructure provides
  the foundation; ~70 hours wall on current hardware. The only
  remaining lever with potential to recover $50+/1000h. **Honest
  expected-outcome prior: NULL more likely than SHIP** per Decisions
  113 + 117. Substantial compute investment for credibility-low payoff
  — operator decides whether to authorize or close the lever explicitly.

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
      UNCHANGED). Per-hand picker between v52-DL and v44_dt on the
      ~23% of S90 hands where v52-DL wins (Decision 125 finding).
      Speculative — Decision 125 noted v52-DL is partially effective
      (recovers ~50% of v47 bleed but not fully to v44_dt); the exploit
      picks v52-DL only when it would win. Smaller magnitude than A3
      but lower compute cost. Cheap pre-drill on N=200 first (no
      Option C required). Single-session feasible to characterize.

  (b) v44_RULE13 fallthrough replacement (TERTIARY, UNCHANGED).
      v54/v55/v56 absorb $731+/1000h of chain bleed across pair-family
      already; replacement primarily matters for HIGH_ONLY (already
      gated by v64/v65 chain). Likely modest impact at best.

  MAINTENANCE OPTION is CLOSED (Decision 132, S97).

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged (25 sessions).
- v65_mid_pair_chain_extend is the production rule chain (UNCHANGED).
- v55_two_pair_hybrid + v56_trips_hybrid blanket-route their targets to
  v44_dt unconditionally — DO NOT undo this routing without quantifying
  the $515+$33 bleed they currently absorb (S92 finding).
- v54 + Rule 29 absorb $195 of chain bleed on LOW pair (S91 quantified).
- The pre-committed-verdict pattern is project standard. Critical for
  A3: pre-commit a multi-grid bar BEFORE launching the ~70h run.
- HEADLINE METRIC IS $/1000h ON PRODUCTION GRID (Decision 131, S96).
  Match% retained as diagnostic only.
- NEW S97: PARKED-CANDIDATE BOOK-KEEPING MUST RECORD BASELINE + RE-GRADE
  BEFORE COMPOSITE HYPOTHESES (Decision 132). A "+$X lift" reading is
  baseline-relative; if a related candidate from the same cell ships
  between the grading and the composite-hypothesis attempt, the +$X
  becomes double-counted relative to current production. Always record
  the baseline strategy name with the lift, and re-grade against current
  production before any composite hypothesis.
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
