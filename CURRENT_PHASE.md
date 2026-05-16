# Current: Sprint 8 — Session 93 SHIPS v65 (= v64 + Rule 25 — MID pair × PMID_DS_NOMAXTOP × max_sing ≤ Q chain extension) at **+$6.43/1000h N=200 + +$6.34/1000h N=1000 (two-grid SHIP cleared)**; production $1,627.36 → $1,633.79/1000h; first project SHIP via two-grid bar on a prefix-uncovered cell, unblocking the v60 candidate parked since S86 (MIXED-by-methodology, 7 sessions) via NEW Option C N=1000 sparse-grid infrastructure (engine `--id-list-file` mode); rule count 24 → 25; cumulative closure 91.6% → 92.09%; v44_dt UNCHANGED for 21st consecutive session; combined S87-S93 production-chain recovery $221.26/1000h; CHAIN-AUDIT METHODOLOGY ARC remains COMPLETE per S92 — S93 is a rule-extraction ship (Option D-revised) NOT a chain-audit ship; project pivots to a different lever via the new infrastructure

S93 executed the S92-defined PRIMARY path verbatim: build the engine `--id-list-file` mode and retroactively validate v60. Phase A added `solve_grid_ids` to `engine/src/oracle_grid.rs` (sibling of `solve_grid_range`, each item carries its own canonical_id) + `--id-list-file` CLI option to `OracleGrid` subcommand. Phase B correctness test: 100 ids in [0, 500K) reproduced bit-identical EVs vs the existing prefix N=1000 grid. Phase C-1: identified 32,304 v60-gate12 changed canonical_ids from MID × PMID_DS_NOMAXTOP cell (114,048 hands) and reproduced S86's N=200 baselines to the penny. Phase C-2: invoked engine on the 32,304-id list, 21:17 wall at 25.3 hands/s. Phase C-3: two-grid grader with pre-committed thresholds cleared SHIP at gate=12 (N=200 +$6.43, N=1000 +$6.34, |Δ| $0.09). Built v65 (composes v64's HIGH_ONLY chain-audit gate with v60-gate12's MID pair rule — firing zones DISJOINT by construction). Final whole-grid grader confirmed +$6.43/1000h N=200 lift over v64; 0 disagreements on 50K out-of-cell random sample; production now **$1,633.79/1000h**.

**Two-grid SHIP standard results (S93 Phase C-3):**

| gate | n_changed | N=200 lift | N=1000 lift | |Δ| | sign-agree | verdict |
|---:|---:|---:|---:|---:|---:|---|
| 10 | 4,080 | +$1.63 | +$1.65 | $0.02 | 79.3% | MIXED |
| 11 | 14,160 | +$4.85 | +$4.77 | $0.09 | 79.0% | MIXED |
| **12** | **32,304** | **+$6.43** | **+$6.34** | **$0.09** | **77.8%** | **SHIP** |

**v65 final grade (S93 Phase C++):**

| metric | pre-S93 (v64) | post-S93 (v65) | Δ |
|---|---:|---:|---:|
| Full grid (N=200) | $1,627.36 | **$1,633.79** | **+$6.43** |
| Prefix grid (N=1000) | $776.88 | $776.88 | $0.00 |
| Production vs v44_dt | $546.36 | **$552.79** | **+$6.43** |
| Remaining gap to oracle | $117.84 | **$111.41** | **−$6.43** |
| Cumulative closure since pre-S68 | 91.6% | **92.09%** | +0.49pp |
| Rule count | 24 | **25** | +1 |

**Composition safety check (S93 Phase C+):** v64==v57 on 32,304/32,304 changed hands (100% — composition assumption holds); v65==v64 on 50,000/50,000 out-of-cell random sample (0 disagreements — firing zones disjoint). Production v65 = v64 + Rule 25 is empirically safe.

> **🎯 IMMEDIATE NEXT ACTION (Session 94): rule-extraction on within-v44_dt residual leak (PRIMARY), OR validate other parked MIXED candidates via Option C (SECONDARY), OR headline-goal recalibration (TERTIARY)**
>
> Chain-audit lever remains exhausted on current architecture (S92 finding holds). S93's SHIP was a rule-extraction ship (Option D-revised) on a within-v44_dt residual leak, unblocked by NEW infrastructure (Option C). S94 default order:
>
> 1. **PRIMARY — rule-extraction (Option D-revised) on two_pair LAYOUT_A_SS.**
>    Largest unaddressed within-v44_dt cell: **$35.22/1000h on 437,580
>    hands**. S69 tested catalog candidates and confirmed v44_dt
>    dominates the aggregate; individual sub-cells were not exhaustively
>    probed. Could be amenable to a "drop max kicker into bot for DS-like
>    SS structure" rule similar to Rule 20's mechanism (S83). Now
>    testable under the two-grid bar via Option C if the cell extends
>    outside prefix coverage (which it largely does — two_pair cells
>    span cid 41K-6M).
>
> 2. **SECONDARY — validate other parked MIXED candidates via Option C.**
>    v60 gate=11 is currently MIXED at +$4.85 (N=200) / +$4.77 (N=1000)
>    on 14,160 hands. Both grids robustly POSITIVE but neither clears the
>    $5 SHIP bar. Could be revisited with a relaxed bar OR combined with
>    other near-miss rules into a multi-cell composition. S86's MIXED
>    candidate ($21.68 STRUCTURE leak on LOW pair × PMID_DS_MAXTOP) is
>    also amenable to Option C re-validation.
>
> 3. **TERTIARY — headline-goal recalibration.** Still open from S92's
>    framing. Make explicit that 95% match% is unreachable from current
>    architecture; reset target to maximize $/1000h subject to current
>    cascade. Affects how to read future MIXED ship sessions.
>
> 4. **DEFERRED — ML retrain (A3 full 6M-hand N=1000 grid).** Formally
>    closed at v44 in S78 (Decision 113). Reopening requires either a
>    new feature family or full A3 infrastructure — Option C is the
>    foundation; the full 6M-hand sweep at N=1000 would take
>    ~6M / 25 hands/s ≈ 70 hours wall on this hardware. Non-trivial but
>    no longer impossible.
>
> 5. **DEFERRED — v52-defensive-low partial-effectiveness exploit (S90 finding).**
>    Speculative.
>
> 6. **DEFERRED — v44_RULE13 fallthrough replacement.** With v54/v55/v56
>    absorbing $731/1000h of chain bleed across pair-family, replacement
>    primarily matters for HIGH_ONLY (already gated by v64/v65).

> **📓 METHODOLOGY (Session 94+ — refined through S93):**
>
> 1. **OPTION C N=1000 SPARSE INFRASTRUCTURE WORKS AT PRODUCTION QUALITY (NEW S93).**
>    Engine `--id-list-file` mode produces bit-identical EVs to the
>    prefix N=1000 grid at the same `--samples` / `--seed` / `--opponent`
>    (per-hand seed = `base_seed + canonical_id × φ` is deterministic).
>    Throughput ~25 hands/s parallel — manageable for cell-scale
>    validations (~22 min for 32K hands). The infrastructure is available
>    for ALL future "rule cell entirely outside prefix" candidates and
>    unlocks the two-grid SHIP standard on arbitrary cell subsets.
>
> 2. **MIXED-BY-METHODOLOGY IS RECOVERABLE IF THE ONLY BLOCKER WAS
>    PREFIX COVERAGE (NEW S93).** v60 was parked for 7 sessions carrying
>    a +$6.43 SHIP-signal that couldn't be confirmed. With infrastructure
>    in place, the SHIP was a single 22-minute engine run away. Future
>    candidates with the same shape (full-grid SHIP signal + cell outside
>    prefix range + no obvious mechanism flaw) should be queued for
>    Option C validation rather than written off.
>
> 3. **PRE-COMMITTED TWO-GRID THRESHOLDS ARE ROBUST AT LOW EFFECT SIZES (NEW S93).**
>    Per-hand sign-agreement between N=200 and N=1000 deltas was only
>    77.8% on the 32,304 changed hands — high per-hand MC noise — but
>    aggregate lifts agreed to $0.09/1000h. Per-hand noise matters for
>    per-hand picker design; cell-level rule SHIP verdicts survive high
>    per-hand variance cleanly. The two-grid bar at $5 SHIP / $1 NULL is
>    well-calibrated for cell-scale candidate validation.
>
> 4. **DISJOINT FIRING ZONES MAKE PRODUCTION COMPOSITION TRIVIALLY SAFE (NEW S93).**
>    v64 (HIGH_ONLY only) and Rule 25 (MID pair only) fire on demonstrably
>    DISJOINT hand sets. When zones are demonstrably disjoint, a composed
>    strategy can ship from cell-level grading alone — no separate full
>    whole-grid regrade required. This pattern applies to any future rule
>    that fires on a structurally orthogonal hand set vs current
>    production. (Confirmed empirically: 0 disagreements on 50K out-of-cell
>    random sample.)
>
> 5. **CHAIN-AUDIT-ARC-COMPLETE (S92) DOES NOT MEAN RULE-ARC-COMPLETE (NEW S93).**
>    S92 closed one specific lever (chain audit on prefix-silent cells).
>    S93's ship is a different lever (rule extraction on a within-v44_dt
>    residual leak), unblocked by infrastructure (Option C). The project
>    still has live levers — they're just different ones than what
>    dominated S87-S92. Natural next levers: rule extraction within
>    v44_dt residual; validation of parked MIXED candidates; possibly
>    A3-style ML retrain on Option C N=1000 sub-grids.
>
> 6. **PRE-FLIGHT CODE TRACE AS PIVOT-GATE (carried from S92).** When the
>    audit target's production chain can be read in <100 lines of strategy
>    code, read it first. S93 didn't trigger this gate because the v60
>    candidate was already characterized at the code level from S86; but
>    the pattern remains the default for any future chain-audit pivot.
>
> 7. **PRE-COMMITTED VERDICT PATTERN (project standard).** Threshold
>    locked in code BEFORE the data is read. S93's grader hard-coded
>    SHIP = both grids ≥ $5, NULL = both ≤ $1, MIXED otherwise; the
>    SHIP verdict at gate=12 + the MIXED verdicts at gates 10/11 fell out
>    mechanically.
>
> 8. **NEW PARKED-CANDIDATE PIPELINE (NEW S93 via combined S86 → S93 arc):**
>    a) full-grid grader auto-fires SHIP signal
>    b) prefix grader is silent (cell outside prefix coverage)
>    c) status = MIXED-by-methodology
>    d) wait for Option C infrastructure
>    e) Option C generates sparse N=1000 grid on changed-hand ids
>    f) two-grid grader applies pre-committed thresholds
>    g) SHIP / NULL / MIXED — verdict definitive
>    This is the canonical recovery pipeline for future MIXED-by-
>    methodology candidates.

> **✅ ARTIFACTS produced in S93:**
> 1. `engine/src/oracle_grid.rs` — added `solve_grid_ids` (sibling of `solve_grid_range`)
> 2. `engine/src/lib.rs` — re-exported `solve_grid_ids`
> 3. `engine/src/main.rs` — added `--id-list-file` CLI option + `run_oracle_grid_id_list` helper + `read_id_list` parser
> 4. `analysis/scripts/test_id_list_correctness_S93.py` — Phase B bit-exact correctness test (NEW)
> 5. `analysis/scripts/prepare_v60_id_list_S93.py` — Phase C-1 changed-hand id list + N=200 baseline reproduce (NEW)
> 6. `analysis/scripts/grade_v60_id_list_n1000_S93.py` — Phase C-3 two-grid grade with pre-committed thresholds (NEW)
> 7. `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` — production v65 (NEW)
> 8. `analysis/scripts/grade_v65_full_grid_S93.py` — final whole-grid v65 grade (NEW)
> 9. `data/session93/v60_gate12_changed_ids.txt` — 32,304 sorted canonical_ids
> 10. `data/session93/v60_per_hand_picks.npz` — v57 + v60-gate10/11/12 picks per cell hand
> 11. `data/session93/v60_n200_baseline.json` — N=200 baselines per gate (S86 reproduce)
> 12. `data/session93/v60_n1000_sparse.bin` — sparse N=1000 grid, 13.7 MB
> 13. `data/session93/engine_n1000_sparse.log` — engine run log
> 14. `data/session93/grade_v60_n1000.log` + `grade_v60_n1000_summary.json`
> 15. `data/session93/grade_v65_full_grid.log` + `grade_v65_full_grid_summary.json`
> 16. `SESSION_93_REPORT.md` — plain-language session report (NEW)
> 17. `DECISIONS_LOG.md` — Decision 128 (S93 SHIP + 5 methodology refinements) appended
> 18. `CURRENT_PHASE.md` — this file, rewritten for S94
> 19. `STRATEGY_GUIDE.md` — Part 1 appended (Session 93 entry); Parts 5+6 updated (v65 production, +Rule 25); front-matter "Last updated" prepended
> 20. `sprints/SPRINT_INDEX.md` — appended S92 + S93 entries

> Updated: 2026-05-16 (Session 93 end — **STRATEGY OF RECORD CHANGED: v64 → v65_mid_pair_chain_extend.** S93 executed the S92-defined PRIMARY path verbatim: build Option C N=1000 oracle generator infrastructure via engine `--id-list-file` mode and retroactively validate v60. Engine changes: added `solve_grid_ids` to `oracle_grid.rs` (each item carries own canonical_id, per-hand seed identical to sequential mode) + `--id-list-file` CLI option to `OracleGrid` subcommand. Output is a SPARSE TWOG file with header `canonical_total` = id-list length so resume + header-mismatch guards still work. Phase B correctness test: 100/100 rows bit-identical to existing prefix N=1000 grid (same samples/seed/opp). Phase C-1: identified 32,304 changed-hand canonical_ids at v60-gate12 from MID × PMID_DS_NOMAXTOP cell (114,048 hands); recomputed S86 N=200 baselines exact-match to the penny (gate 10 +$1.63 / gate 11 +$4.85 / gate 12 +$6.43). Phase C-2 engine run: 21:17 wall at 25.3 hands/s producing `data/session93/v60_n1000_sparse.bin` (13.7 MB). Phase C-3 two-grid grader (pre-committed thresholds LOCKED before reading the sparse grid): gate 12 lift = **+$6.34/1000h N=1000** (|Δ vs N=200| = $0.09); **SHIP cleared by two-grid standard**. Built strategy_v65 composing v64's HIGH_ONLY chain-audit gate with v60-gate12's MID pair rule (firing zones DISJOINT — HIGH_ONLY = no pair; MID pair = exactly one pair of rank 8-T). Final whole-grid grader (15.2 s in-cell + 27.3 s out-of-cell): v65 whole-grid N=200 lift over v64 = **+$6.43/1000h** (matches Phase C-1 to the penny); v64==v57 on 32,304/32,304 changed hands (composition assumption holds); v65==v64 on 50,000/50,000 out-of-cell random sample (0 disagreements). **Production: $1,627.36 → $1,633.79/1000h on full grid; prefix UNCHANGED at $776.88 (rule fires outside prefix coverage); production vs v44_dt $546.36 → $552.79; remaining gap to oracle $117.84 → $111.41/1000h; cumulative closure since pre-S68 91.6% → 92.09%; rule count 24 → 25.** Decision 128 records SHIP + 5 methodology refinements: (1) Option C N=1000 sparse infrastructure works at production quality (bit-identical to existing prefix grid), (2) MIXED-by-methodology candidates recoverable if blocker was prefix coverage (v60 parked 7 sessions), (3) pre-committed two-grid thresholds robust at low effect sizes (77.8% per-hand sign-agree but $0.09 aggregate agree), (4) disjoint firing zones make composition trivially safe (0 out-of-cell disagreements), (5) chain-audit-arc-complete (S92) does NOT mean rule-arc-complete — S93 is rule-extraction (Option D-revised) NOT chain-audit. Engine pre-flight: cargo build clean + 141 tests pass. v44_dt UNCHANGED for 21st consecutive session. Combined S87-S93 production-chain recovery: $221.26/1000h. CHAIN-AUDIT METHODOLOGY ARC remains COMPLETE per S92 finding. S94 default plan: rule-extraction on within-v44_dt residual leak — two_pair LAYOUT_A_SS at $35.22/1000h on 437K hands (PRIMARY), OR validate other parked MIXED candidates via Option C — v60 gate=11 at +$4.85/+$4.77 currently MIXED (SECONDARY), OR headline-goal recalibration (TERTIARY).)

---

## Headline state at end of Session 93

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 21 sessions, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$111.41/1000h** (was $117.84). Cumulative closure since pre-S68: $1,297.59 = **92.09% of original $1,409** (was 91.6%).

Production vs v44_dt: production outperforms ML by **$552.79/1000h** (was $546.36).

**Total project rule count: 25** (Rule 25 added in S93).

**S93 results (SHIP):**

| target | mechanism | N=200 lift | N=1000 lift | verdict |
|---|---|---:|---:|---|
| MID × PMID_DS_NOMAXTOP × max_sing ≤ Q × tmax-style (Rule 25) | force PMID_tnomax_DS | +$6.43 | +$6.34 | **SHIP** |

---

## Hypothesis cascade status (updated after S93)

| Hypothesis | Description | Status |
|---|---|---|
| H1 | high_only SS+ms route quality | NULL ship +$5 (S73). |
| H2 | high_only route-tradeoff | CLEAN NULL +$0 (S74). |
| Option B (S75) | Gradient boosting at depth=6 / n_est=200 | DECISIVE NULL −$1,392/1000h. |
| S76 / S77 diagnostics | Cross-cat → pair drill | Shipped diagnostics; identified H6/H7/H8 + LOW pair under-coverage. |
| H6 / H7 / H8 (S78) | Pair gated features | CLEAN NULL +$2 prefix. |
| Single-model ML feature-engineering track | At v44 saturating regime | FORMALLY CLOSED (Decision 113). |
| S79 label-noise measurement | Existing N=1000 prefix vs N=200 full | MIXED — 32% oracle disagreement reveals criterion blind spot (Decision 114). |
| A1 (S80) | Retrain v44 DT on N=1000 prefix labels | LIFTS +13.15pp on N=1000 match rate; in-sample evaluation caveat (Decision 115). |
| C2 (S80) | Regularize v44 DT (max_leaf_nodes=500K, ml=5) | NULL −2.13pp on N=1000, −12.24pp on N=200 (Decision 115). |
| A2 (S81/S82) | Targeted N=1000 expansion on two_pair + trips_pair + held-out validation | CLEAN NULL — Lens-3 held-out 63.74% < 72.0% floor (Decision 117). |
| A-path (oracle-label-quality lever) | All variants tested at v44 capacity | FORMALLY CLOSED at v44 regime (Decision 117). |
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — but Option C is now the foundation; ~70h wall on current hardware. |
| Headline-goal recalibration | Concede 95% match% as unreachable | OPEN — chain-audit arc complete, but new infra (Option C) opens fresh levers; recalibration deferred. |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). Re-confirmed via S91 layer attribution. |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). Now eligible for Option C re-validation. |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86) | MID × PMID_DS_NOMAXTOP | **SHIPPED IN S93** — was MIXED-BY-METHODOLOGY (Decision 121) until S93 generated the N=1000 sparse grid via Option C. v60 + gate=12 became Rule 25 / v65. **Decision 128.** |
| DAMAGE-CONTROL chain audit cell #1 (S87) | HIGH_ONLY × DS_NO_JOINT × {J-A} v52-chain regression | SHIPPED — Rule 21 + $98.67 full-grid (Decision 122). |
| DAMAGE-CONTROL chain audit cell #2 (S88) | HIGH_ONLY × {DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH} × {J-A} v47-chain regression | SHIPPED — Rule 22 + $98.84 full-grid (Decision 123). |
| DAMAGE-CONTROL chain audit cell #3 (S89) | HIGH_ONLY × {JOINT_MED, JOINT_LOW} × {J-A} v47-chain regression | SHIPPED — Rule 23 + $10.09 full-grid (Decision 124). |
| DAMAGE-CONTROL chain audit cell #4 (S90) | HIGH_ONLY × {5 cells} × {8, 9, T} v47-chain regression (first v52-defensive-low audit) | SHIPPED — Rule 24 + $7.23 full-grid (Decision 125). HIGH_ONLY × max ≥ 8 ZONE COMPLETE. |
| DAMAGE-CONTROL chain audit cell #5 (S91) | LOW pair PMID prefix-COVERED cells (FIRST prefix-COVERED chain audit) | NULL — three candidates all FAIL two-grid SHIP standard (Decision 126). |
| DAMAGE-CONTROL chain audit cell #6 + #7 (S92) | two_pair + trips chain audit | STRUCTURAL NULL — chain-audit candidate set EMPTY by construction (Decision 127). |
| Chain-audit arc (S87-S92 closure) | 5 sessions across HIGH_ONLY + single-pair + two_pair + trips | COMPLETE — 4 SHIPS ($214.83/1000h) + 2 NULLs at well-characterized boundaries. |
| **Option C N=1000 oracle generator infrastructure (S93)** | **engine `--id-list-file` mode** | **SHIPPED — bit-identical to existing prefix N=1000 grid; ~25 hands/s parallel. Decision 128.** |
| **v60 retroactive validation (S93)** | **MID × PMID_DS_NOMAXTOP × max_sing ≤ Q at N=1000** | **SHIPPED → Rule 25 / v65. +$6.34 N=1000 / +$6.43 N=200; both grids clear two-grid bar. Decision 128.** |
| **Within-v44_dt residual rule extraction (S94 candidate)** | **two_pair LAYOUT_A_SS at $35.22/1000h on 437K hands** | **OPEN — natural S94 PRIMARY, now testable under two-grid bar via Option C. Largest unaddressed within-v44_dt cell.** |
| v60 gate=11 (S93 SECONDARY finding) | MID × PMID_DS_NOMAXTOP × max_sing ≤ J on 14,160 hands | MIXED at +$4.85/+$4.77 (both grids POSITIVE but neither clears $5). Eligible for relaxed-bar or composite-rule re-evaluation in S94+. |
| v52-defensive-low refinement (S90 finding) | Per-hand picker between v52-DL and v44 on S90 target hands | DEFERRED — speculative. |

**Cascade verdict (post S93):** Chain-audit lever remains exhausted on current architecture (S92 finding holds). The natural next lever shifted from chain audit to **rule extraction on within-v44_dt residuals**, unblocked by Option C infrastructure. S93 shipped the first such rule (Rule 25) by proving the new pipeline end-to-end:

* **ML cascade:** EXHAUSTED at v44 saturating regime (no change since S78 / Decision 113).
* **Rule-layer cascade — chain audit (S87-S92):** COMPLETE. $214.83/1000h shipped + 2 NULLs at boundaries.
* **Rule-layer cascade — Option D-revised rule extraction (S83-S93):** ACTIVE. $16.81 (Rule 20) + $6.43 (Rule 25) = **$23.24/1000h cumulative across two ships over 11 sessions**. Slower cadence than chain audit but lever-still-open. S86's MIXED Rule 20 extension + new candidates (two_pair LAYOUT_A_SS, trips B_DS_AVAIL_LKR) are now testable under two-grid bar.
* **Infrastructure cascade (S93 NEW):** Option C N=1000 sparse-grid infrastructure SHIPPED + validated. Unlocks (i) two-grid SHIP standard on arbitrary cell subsets, (ii) re-validation of parked MIXED candidates, (iii) future smaller-effect rule probing, (iv) foundation for A3-style full 6M N=1000 grid.

---

## Resume Prompt (Session 94 — rule-extraction on within-v44_dt residual / parked-candidate re-validation)

```
Resume Session 94 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S93 — opens with the S94 pivot plan
  + alternative-direction options)
- DECISIONS_LOG.md (latest: Decision 128 — S93 SHIPS v65 / Rule 25 via
  Option C N=1000 sparse-grid infrastructure; two-grid SHIP bar cleared
  at gate=12 with N=200 +$6.43 + N=1000 +$6.34; unblocks v60 candidate
  parked since S86; rule count 24 → 25; cumulative closure 91.6% → 92.09%;
  5 methodology refinements including new MIXED-by-methodology recovery
  pipeline and disjoint-firing-zone composition argument)
- SESSION_93_REPORT.md (S93 v65 SHIP, plain-language TL;DR, full
  validation chain across Phase A engine mod + Phase B correctness +
  Phase C-1 prep + Phase C-2 sparse run + Phase C-3 two-grid grade +
  Phase C+ v65 build + Phase C++ final whole-grid grade)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/session93/v60_n1000_sparse.bin — NEW: 32,304 × 105 at N=1000
  (S93 sparse grid for MID × PMID_DS_NOMAXTOP × max_sing ≤ Q changed
  hands; first project sparse N=1000 grid)
- data/drill_pair_v44_per_hand_structural.parquet — pair per-hand
- data/drill_two_pair_v44_per_hand_structural.parquet — two_pair per-hand
  (likely S94 target — LAYOUT_A_SS at $35.22/1000h on 437K hands)
- data/drill_trips_v44_per_hand_structural.parquet — trips per-hand
- data/v44_dt_model.npz — production ML champion (UNCHANGED 21 sessions)
- data/session93/* — S93 artifacts (engine run log, grader summaries,
  v65 per-hand picks)

STATE (end of S93):
- Production rule chain: v65_mid_pair_chain_extend ($1,633.79 full /
  $776.88 prefix). UP from v64 by +$6.43/1000h.
- ML champion v44_dt UNCHANGED (21 consecutive sessions).
- Two-track divergence (remaining gap to oracle): $111.41/1000h
  (DOWN from $117.84).
- Rule count: 25 (UP from 24 with Rule 25 = MID pair × PMID_DS_NOMAXTOP
  × max_sing ≤ Q × v57-pick-tmax-style → force PMID_tnomax_DS).
- Cumulative closure since pre-S68: 92.09% of original $1,409
  (UP from 91.6%).
- Combined S87-S93 production-chain recovery: $221.26/1000h
  = $214.83 (chain-audit S87-S90) + $6.43 (rule extraction S93).
- KEY S93 INFRASTRUCTURE: Option C N=1000 sparse-grid generator
  SHIPPED via engine `--id-list-file` mode (added solve_grid_ids to
  oracle_grid.rs + CLI option to main.rs). Bit-identical to existing
  prefix N=1000 grid on 100-id correctness test. Throughput ~25 hands/s
  parallel at N=1000. NOW AVAILABLE for ALL future cell-scale
  validations.
- KEY S93 METHODOLOGY: pre-committed two-grid SHIP standard works at
  low effect sizes despite high per-hand MC variance (77.8% per-hand
  sign-agreement BUT $0.09 aggregate agreement). MIXED-by-methodology
  candidates RECOVERABLE if blocker was prefix coverage (v60 parked
  7 sessions, shipped in single 22-min engine run). Disjoint firing
  zones make composition trivially safe (0 out-of-cell disagreements).
  Chain-audit-arc-complete does NOT mean rule-arc-complete.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard." (Strategic priority anchor — see memory
  project_taiwanese_damage_control_priority.md.)
- User is non-technical; any strategic discussion / session report must
  lead with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 94 — rule-extraction on within-v44_dt residual leak / parked-candidate re-validation:

  PRIMARY (S94 default plan, PROMOTED from S93 SECONDARY):
  Rule-extraction on two_pair LAYOUT_A_SS — largest unaddressed
  within-v44_dt cell at $35.22/1000h on 437,580 hands.

  Engineering scope: identify candidate rule mechanism (likely a
  "drop max kicker into bot for DS-like SS structure" pattern similar
  to Rule 20). Iterate through Phase A (cell coverage / cid distribution
  — likely partially outside prefix), Phase B (pre-drill on full N=200
  grid for addressability), Phase C (Option C sparse N=1000 run on
  changed-hand subset), Phase D (two-grid SHIP grader + production
  composition).

  Phase A: read drill_two_pair_v44_per_hand_structural.parquet,
    filter to LAYOUT_A_SS, map cid distribution against prefix
    boundary. If wholly outside prefix → plan for Option C as default.
    If partially overlapping → use both natively + Option C for
    out-of-prefix subset.

  Phase B: enumerate candidate rules (single-rank trigger? max_sing
    gate? v57-pick restriction?). Pre-drill on N=200 full grid for
    each candidate variant. Identify swap-right rate, n_changed, and
    per-rank breakdown to choose the lift-maximizing gate.

  Phase C: if candidate clears the N=200 SHIP bar but the cell is
    outside prefix coverage, run Option C on the changed-hand id list
    (~22 min wall per 30K hands). Two-grid SHIP grader applies
    pre-committed thresholds: SHIP requires both N=200 and N=1000 ≥ $5.

  Phase D: if SHIP, build strategy_v66 composing v65 with new rule
    (likely disjoint firing zone — two_pair vs v65's HIGH_ONLY +
    MID pair → safe composition). Final whole-grid grader confirms.
    Then session-end protocol (commit + push + docs).

  ALTERNATIVE DIRECTIONS:

  (a) Validate other parked MIXED candidates via Option C (SECONDARY).
      v60 gate=11 currently MIXED at +$4.85/+$4.77 on 14,160 hands.
      Doesn't clear $5 SHIP bar but is robustly POSITIVE in both grids.
      Could be revisited with a relaxed bar OR as part of a composite
      multi-cell rule. S86's MIXED LOW × PMID_DS_MAXTOP candidate
      ($21.68 STRUCTURE leak) is also now eligible for Option C
      re-validation.

  (b) Headline-goal recalibration (TERTIARY).
      Make explicit that 95% match% is unreachable from current
      architecture; reset goal to maximize $/1000h subject to current
      cascade. Affects future MIXED-session interpretation.

  (c) v52-defensive-low partial-effectiveness exploit (DEFERRED from S90).

  (d) v44_RULE13 fallthrough replacement (DEFERRED).

  (e) ML retrain — formally closed at v44 (DEFERRED); Option C is now
      the foundation for A3 if user ever reopens.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged (21 sessions).
- v65_mid_pair_chain_extend is the new production rule chain.
- v65 = v64 + Rule 25 (MID pair × PMID_DS_NOMAXTOP × max_sing ≤ Q ×
  tmax-style → force PMID_tnomax_DS); firing zones are DISJOINT from
  v64's HIGH_ONLY chain-audit zone — composition is additive.
- v55_two_pair_hybrid + v56_trips_hybrid blanket-route their targets to
  v44_dt unconditionally — DO NOT undo this routing without quantifying
  the $515+$33 bleed they currently absorb (S92 finding).
- v54 + Rule 29 absorb $195 of chain bleed on LOW pair (S91 quantified).
- The pre-committed-verdict pattern is project standard.
- The 3-pronged CHAIN-AUDIT APPLICABILITY TEST (from S92): (a)
  prefix-silent OR (b) ≥$5 both-grid residual, AND (c) production picks
  differ from v44_dt on at least some audit cells — but note S93's ship
  was NOT a chain-audit, so this test may not apply to S94's rule
  extraction.
- NEW S93 PARKED-CANDIDATE PIPELINE: a) full-grid SHIP signal + b)
  prefix silent (cell outside coverage) + c) MIXED-by-methodology → d)
  Option C sparse N=1000 → e) two-grid grader → f) verdict definitive.
- NEW S93 DISJOINT-FIRING-ZONE COMPOSITION argument: when two rules
  fire on demonstrably disjoint hand sets, composition is additive
  and safe; cell-level grader sufficient (no whole-grid regrade
  needed). Confirm with out-of-cell random sample (0 disagreements
  expected).
- NEW S93 PRE-COMMITTED TWO-GRID THRESHOLDS at low effect sizes work
  cleanly even with 22% per-hand sign-disagreement, because aggregate
  variance collapses over ~30K-hand subsets.
- The PIVOT-GATE pattern (S87+, extended S92): cheap pre-drill before
  infrastructure; pre-flight code-trace before pre-drill.
- A NULL audit session is a COMPLETE cycle. Worth the time.
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
