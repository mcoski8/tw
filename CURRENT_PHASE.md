# Current: Sprint 8 — Session 95 MIXED on trips B_DS_AVAIL_LKR intra-Layout-A force-best-DS-bot candidate (Rule 26); **production v65 UNCHANGED at $1,633.79/1000h**; NEW S95 methodology lesson — **picker alignment with oracle's specific pick is the SECOND necessary condition for rule extraction** (alongside S94's trigger-predictivity boundary); naive Rule-20 picker carry-over (`bot_pair_high` first) is catastrophically misaligned for trips Layout-A DS-bot (3-8% exact match in highest-P sub-buckets), corrected `TOP_HIGH then pair_tops` criterion lifts NARROW from $-3.22 to $+4.59 N=200 / $+4.75 N=1000 — still $0.25 short of $5 SHIP bar; two-grid noise small (|Δ|=$0.16 on NARROW); v44_dt UNCHANGED for 23rd consecutive session; Combined S87-S94 production-chain recovery $221.26/1000h (S95 contributes $0); chain-audit lever + bucket-level rule-extraction lever + intra-layout rule-extraction lever ALL characterized as saturated on the current ML architecture.

S95 executed the S94-defined PRIMARY path verbatim: build strategy_v66 with a Rule-20-analog "force-best-DS-bot-within-Layout-A" picker for trips B_DS_AVAIL_LKR, multi-gate pre-drill on N=200, run Option C N=1000 sparse-grid grader at pre-committed two-grid thresholds. Phase A re-confirmed S94's sub-bucket numbers from per-hand parquet — and surfaced that the resume prompt's n=210 + n=370 NARROW sizes were transcription typos (the S94 JSON shows the true n=1,618 + n=6,542 = 8,160 hands at 90.4% mean predictivity / $5.89 wg ceiling). Phase B's initial picker carried over the Rule 20 / Rule 25 criterion `bot_pair_high desc, bot_pair_2nd desc, top_rank desc` and produced a catastrophe — all three gates strongly NEGATIVE at N=200 ($-3.22 / $-6.25 / $-8.84). A diagnostic showed the rule's exact-pick match with oracle was only 7.5%-13.8% on the highest-predictivity sub-buckets despite 88.7% direction-predictivity in NARROW. An 8-criterion picker sweep identified **TOP_HIGH then pair_tops** as the correct criterion for trips (top tier wants the highest kicker because top scores as Hold'em 1+5 and the trip card already anchors the bot), lifting NARROW to $+4.59 / 85.2% swap-right rate — a $7.81/1000h swing from picker change alone. Phase C's Option C N=1000 grader on the 51,531-id WIDE superset (1,901s engine wall at 27.1 hands/s) returned **MIXED on all three gates** (NARROW $+4.59 N=200 / $+4.75 N=1000, MEDIUM $+2.95 / $+3.37, WIDE $+0.36 / $+2.09); the closest miss is NARROW at $0.25 below the $5 SHIP bar on each grid.

**S95 per-gate sub-bucket pivot (re-confirmed via per-hand parquet):**

| ksc | nkts | nbds | n | or_ds | P(oracle DS) | wg ($/1000h) |
|----:|-----:|-----:|---:|---:|---:|---:|
| 2 | 4 | 1 | 1,618 | 1,618 | 100.0% | $1.12 |
| 3 | 4 | 1 | 6,542 | 5,757 | 88.0% | $4.77 |
| 2 | 4 | 3 | 6,912 | 4,337 | 62.7% | $4.18 |
| 2 | 3 | 1 | 29,465 | 13,588 | 46.1% | $12.58 |
| 2 | 2 | 1 | 5,791 | 605 | 10.4% | $0.55 |
| 1 | 3 | 3 | 6,705 | 0 | 0.0% | $0.74 |

**S95 picker-sweep result (8 criteria × 3 gates, key entries):**

| Criterion | NARROW lift | MEDIUM lift | WIDE lift |
|---|---:|---:|---:|
| BOT_PAIR_HI then TOP_DESC (Rule 20/25 carry-over) | $-3.22 (36.6% sr) | $-6.25 (39.3%) | $-8.84 (47.6%) |
| **TOP_HIGH then pair_tops (correct for trips)** | **$+4.59 (85.2%)** | **$+2.95 (65.9%)** | **$+0.36 (57.2%)** |
| TOP_LOW then pair_tops | $-4.41 (32.6%) | $-6.55 (39.7%) | $-9.14 (47.7%) |
| BOT_SUM_HI then TOP_DESC | $-4.41 | $-6.55 | $-9.14 |

**S95 two-grid verdict:**

| Gate | n_changed | N=200 lift | N=1000 lift | \|Δ\| | sign-agree | Verdict |
|---|---:|---:|---:|---:|---:|---|
| NARROW | 8,751 | $+4.59 | **$+4.75** | $0.16 | 93.9% | **MIXED** |
| MEDIUM | 18,734 | $+2.95 | $+3.37 | $0.42 | 88.3% | MIXED |
| WIDE | 51,531 | $+0.36 | $+2.09 | $1.73 | 87.0% | MIXED |

**No production change. v65 remains strategy of record.**

| metric | pre-S95 | post-S95 | Δ |
|---|---:|---:|---:|
| Full grid (N=200) | $1,633.79 | $1,633.79 | $0.00 |
| Prefix grid (N=1000) | $776.88 | $776.88 | $0.00 |
| Production vs v44_dt | $552.79 | $552.79 | $0.00 |
| Remaining gap to oracle | $111.41 | $111.41 | $0.00 |
| Cumulative closure since pre-S68 | 92.09% | 92.09% | 0.00pp |
| Rule count | 25 | 25 | 0 |

> **🎯 IMMEDIATE NEXT ACTION (Session 96): headline-goal recalibration (PRIMARY, PROMOTED), OR A3 ML retrain (SECONDARY), OR v52-defensive-low partial-effectiveness exploit (TERTIARY)**
>
> Chain-audit lever exhausted (S91/S92). Bucket-level rule-extraction lever saturated (S94). Intra-layout rule-extraction lever saturated on the strongest candidate (S95). The Option D-revised rule-extraction track is now fully characterized.
>
> 1. **PRIMARY (PROMOTED from S94/S95 SECONDARY) — headline-goal recalibration.**
>    Doc-only session. With all three rule-shipping levers (chain-audit, bucket-level rule-extraction, intra-layout rule-extraction) characterized as saturated on the current ML architecture, make explicit that the 95% match% goal is unreachable from the current architecture and reset the success criterion to maximize $/1000h subject to the current cascade. This sharpens S97+ planning, affects MIXED-session interpretation, and recasts the project trajectory. Estimated effort: 1-2 hours of careful documentation work; no code changes; no engine runs.
>
> 2. **SECONDARY — A3 ML retrain (full 6M × 105 × N=1000 grid).**
>    Formally closed at v44 in S78 (Decision 113). Option C infrastructure now provides the foundation; ~70 hours wall on current hardware. Reopening requires either a new feature family or explicit operator authorization. The structural saturation findings from S91-S95 raise the question of whether a richer ML champion would shift the saturation boundary, but the path requires substantial compute investment and is the only remaining lever with potential to recover $50+/1000h.
>
> 3. **TERTIARY — v52-defensive-low partial-effectiveness exploit (DEFERRED from S90).**
>    Per-hand picker between v52-defensive-low and v44_dt on the ~23% of S90 hands where v52-DL wins. Speculative. Smaller magnitude than A3.
>
> 4. **DEFERRED — v44_RULE13 fallthrough replacement.** With v54/v55/v56 absorbing $731+/1000h of chain bleed across pair-family, replacement primarily matters for HIGH_ONLY (already gated by v64/v65).

> **📓 METHODOLOGY (Session 96+ — refined through S95):**
>
> 1. **PICKER ALIGNMENT IS THE SECOND NECESSARY CONDITION FOR RULE EXTRACTION (NEW S95).**
>    Beyond S94's trigger-predictivity ≥ 62-70% requirement, the rule's deterministic picker must also align with oracle's specific pick within the predicted direction. High direction predictivity (90%) is necessary but not sufficient. Both conditions must be empirically verified for each new cell. Rules 20 and 25 had ≥89% picker alignment by happy accident — their `bot_pair_high` criterion = oracle's. Don't assume.
>
> 2. **PICKER CRITERIA ARE CELL-SPECIFIC, NOT TRANSFERABLE (NEW S95).**
>    Rules 20 / 25 use `bot_pair_high` because for pair hands, bot pair strength dominates top single-card value. Trips invert this — bot strength = trip card, top wants the highest kicker. Validate empirically with an 8-criterion sweep (3-min cost; can swing lift by $7+/1000h).
>
> 3. **RESUME-PROMPT TRANSCRIPTION TYPO IS POSSIBLE (NEW S95).**
>    S94's resume prompt listed NARROW sub-buckets at n=580 / $0.53 wg — actually 8,160 hands / $5.89 wg per the audit JSON. Always cross-check anomalous numbers against the JSON of record at session start.
>
> 4. **OPTION D-REVISED RULE-EXTRACTION LEVER NOW EXHAUSTED ACROSS BOTH SUB-CLASSES (NEW S95).**
>    S94 closed bucket-level layout-flip rules. S95 closes intra-layout structural-feature rules on the strongest remaining candidate. With both sub-classes characterized as saturated, S96 PRIMARY = headline-goal recalibration.
>
> 5. **MIXED VERDICTS ARE INFORMATIVE EVEN WHEN THEY DON'T SHIP (carried).**
>    S95 produced no production change but characterized a genuinely-borderline candidate at $4.59/$4.75 (within $0.25 of SHIP on both grids). The candidate is honestly close to the bar but cleanly fails it; no methodology adjustment recovers it without lowering the two-grid SHIP standard.
>
> 6. **OPTION C N=1000 SPARSE INFRASTRUCTURE IS PROJECT STANDARD (carried from S93+S95).**
>    Throughput ~27 hands/s parallel; bit-identical to existing prefix grid by construction; unblocks two-grid SHIP standard on arbitrary cell subsets. Used twice now (S93 SHIP, S95 MIXED).
>
> 7. **PRE-COMMITTED VERDICT PATTERN (project standard, unchanged).**
>    Thresholds locked in code BEFORE the data is read. S95's grader hard-coded SHIP=both ≥ $5 and NULL=both ≤ $1 thresholds BEFORE reading the N=1000 sparse grid; verdict fell out mechanically.

> **✅ ARTIFACTS produced in S95:**
> 1. `analysis/scripts/phaseA_trips_b_ds_avail_lkr_intra_layout_a_S95.py` — re-confirm S94 numbers + lock 3 trigger gates (NEW)
> 2. `analysis/scripts/strategy_v66_trips_layout_a_force_ds_bot.py` — Rule 26 candidate with TOP_HIGH-first picker (NEW)
> 3. `analysis/scripts/sanity_v66_on_parquet_S95.py` — verify rule fires + produces Layout-A DS-bot output on 50 samples per gate (NEW)
> 4. `analysis/scripts/prepare_v66_id_list_S95.py` — N=200 baseline + per-hand picks + WIDE id list (NEW)
> 5. `analysis/scripts/diagnose_v66_picker_S95.py` — exact-match diagnostic that surfaced the picker mismatch (NEW)
> 6. `analysis/scripts/picker_sweep_v66_S95.py` — 8-criterion picker sweep across 3 gates (NEW)
> 7. `analysis/scripts/picker_sweep_subbucket_v66_S95.py` — per-sub-bucket and cumulative-slice analysis under TOP_HIGH variants (NEW)
> 8. `analysis/scripts/grade_v66_id_list_n1000_S95.py` — two-grid grader at pre-committed thresholds (NEW)
> 9. `data/session95/*` — full set of data artifacts: phaseA_summary, phaseB_prepare_summary, diagnose_v66_picker, picker_sweep, picker_sweep_subbucket logs; v66_per_hand_picks.npz; v66_id_list_wide.txt; v66_n1000_sparse.bin (21.8 MB); engine_n1000_sparse.log; grade_v66_n1000_summary.json
> 10. `SESSION_95_REPORT.md` — plain-language session report + full data (NEW)
> 11. `DECISIONS_LOG.md` — Decision 130 (S95 MIXED + 5 methodology refinements) appended
> 12. `CURRENT_PHASE.md` — this file, rewritten for S96
> 13. `STRATEGY_GUIDE.md` — Part 1 appended (Session 95 entry); front-matter "Last updated" updated to S95
> 14. `sprints/SPRINT_INDEX.md` — S95 entry appended

> Updated: 2026-05-16 (Session 95 end — **STRATEGY OF RECORD UNCHANGED: v65 remains production.** MIXED on trips B_DS_AVAIL_LKR intra-Layout-A force-best-DS-bot candidate. NEW S95 methodology lesson: picker alignment is the second necessary condition for rule extraction; picker criteria are cell-specific, not transferable. With chain-audit + both Option D-revised sub-classes characterized as saturated, S96 PRIMARY promotes to headline-goal recalibration.)

---

## Headline state at end of Session 95

**Strategies of record (UNCHANGED from S94):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for **23 sessions**, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$111.41/1000h** (UNCHANGED). Cumulative closure since pre-S68: $1,297.59 = **92.09% of original $1,409** (UNCHANGED).

Production vs v44_dt: production outperforms ML by **$552.79/1000h** (UNCHANGED).

**Total project rule count: 25** (UNCHANGED).

**S95 results (MIXED on all 3 gates):**

| Gate | n_changed | N=200 lift | N=1000 lift | Verdict |
|---|---:|---:|---:|---|
| NARROW [(2,4,1)+(3,4,1)] | 8,751 | $+4.59 | $+4.75 | MIXED |
| MEDIUM [+(2,4,3)] | 18,734 | $+2.95 | $+3.37 | MIXED |
| WIDE [+(2,3,1)] | 51,531 | $+0.36 | $+2.09 | MIXED |

---

## Hypothesis cascade status (updated after S95)

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
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — but Option C is now the foundation; ~70h wall on current hardware. PROMOTED to S96 SECONDARY. |
| Headline-goal recalibration | Concede 95% match% as unreachable | OPEN — now well-motivated by S91 + S92 + S94 + S95 saturation findings; **PROMOTED to S96 PRIMARY**. |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86/S93) | MID × PMID_DS_NOMAXTOP | SHIPPED — Rule 25 + $6.43 (Decision 128). |
| DAMAGE-CONTROL chain audit cells #1-4 (S87-S90) | HIGH_ONLY × various | SHIPPED 4 rules totaling $214.83/1000h (Decisions 122-125). |
| DAMAGE-CONTROL chain audit cell #5 (S91) | LOW pair PMID prefix-COVERED | NULL — population-divergence noise (Decision 126). |
| DAMAGE-CONTROL chain audit cell #6 + #7 (S92) | two_pair + trips chain audit | STRUCTURAL NULL — chain collapsed by v55/v56 blanket routing (Decision 127). |
| Chain-audit arc (S87-S92 closure) | 5 sessions across 4 categories | COMPLETE — 4 SHIPS ($214.83/1000h) + 2 NULLs at well-characterized boundaries. |
| Option C N=1000 oracle infrastructure (S93) | Engine `--id-list-file` mode | SHIPPED — bit-identical to prefix grid; ~25-27 hands/s parallel. Decision 128. Used twice (S93 SHIP, S95 MIXED). |
| Option D-revised rule extraction within-v44_dt residual (S94) | bucket-level on 10 cells | STRUCTURAL NULL — bucket-level trigger predictivity below 62-70% Rule 25/Rule 20 anchor across all 10 cells. Decision 129. |
| **Option D-revised rule extraction intra-Layout-A bot_suit (S95)** | **trips B_DS_AVAIL_LKR intra-Layout-A** | **MIXED — best gate NARROW $+4.59/$+4.75 N=200/N=1000, $0.25 short of $5 SHIP bar on each grid. Decision 130.** |
| **Rule-extraction arc (S83-S95 closure)** | **bucket-level + intra-layout sub-classes** | **COMPLETE.** 2 SHIPS (Rules 20, 25) + 2 MIXED (S84, S95) + 2 NULL (S85, S94 bucket-level). |
| v60 gate=11 (S93 SECONDARY finding) | MID × PMID_DS_NOMAXTOP × max_sing ≤ J | MIXED at +$4.85/+$4.77; eligible for relaxed-bar or composite-rule re-evaluation. |
| v52-defensive-low refinement (S90 finding) | Per-hand picker between v52-DL and v44 | DEFERRED — speculative; promoted to S96 TERTIARY. |

**Cascade verdict (post S95):** Chain-audit lever exhausted (S92 closure). Rule-extraction lever exhausted across both bucket-level (S94) AND intra-layout (S95) sub-classes on the current ML architecture. **The Option D-revised rule-extraction track is now fully characterized.** All remaining open levers (A3 ML retrain, headline-goal recalibration) require either substantial compute investment or doc-only project repositioning.

* **ML cascade:** EXHAUSTED at v44 saturating regime (no change since S78 / Decision 113).
* **Rule-layer cascade — chain audit (S87-S92):** COMPLETE. $214.83/1000h shipped + 2 NULLs at boundaries.
* **Rule-layer cascade — Option D-revised rule extraction (S83-S95):** $23.24/1000h cumulative across two ships (Rules 20 + 25) + S94 bucket-level saturation + S95 intra-layout MIXED. Both sub-classes EXHAUSTED.
* **Infrastructure cascade (S93+S95):** Option C N=1000 sparse-grid infrastructure available for any future cell-scale validation. Used twice (S93 SHIP, S95 MIXED).

---

## Resume Prompt (Session 96 — headline-goal recalibration / A3 retrain / v52-DL exploit)

```
Resume Session 96 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S95 — opens with the S96 pivot plan;
  rule-extraction lever now characterized as exhausted across BOTH
  bucket-level and intra-layout sub-classes)
- DECISIONS_LOG.md (latest: Decision 130 — S95 MIXED on trips
  B_DS_AVAIL_LKR intra-Layout-A force-best-DS-bot candidate; NEW S95
  methodology lesson: picker alignment is the SECOND necessary condition
  for rule extraction alongside S94's trigger-predictivity boundary;
  picker criteria are cell-specific not transferable)
- SESSION_95_REPORT.md (S95 MIXED, picker-criterion sweep methodology,
  borderline NARROW at $+4.59/$+4.75 — $0.25 short of $5 SHIP bar)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/session93/v60_n1000_sparse.bin — S93 sparse N=1000 grid (32,304 hands)
- data/session95/v66_n1000_sparse.bin — S95 sparse N=1000 grid (51,531 hands)
- data/drill_trips_v44_per_hand_structural.parquet — trips per-hand
- data/v44_dt_model.npz — production ML champion (UNCHANGED 23 sessions)
- data/session95/* — full S95 artifact set

STATE (end of S95):
- Production rule chain: v65_mid_pair_chain_extend ($1,633.79 full /
  $776.88 prefix). UNCHANGED from S93.
- ML champion v44_dt UNCHANGED (23 consecutive sessions).
- Two-track divergence (remaining gap to oracle): $111.41/1000h.
- Rule count: 25 (UNCHANGED).
- Cumulative closure since pre-S68: 92.09% of original $1,409.
- Combined S87-S93 production-chain recovery: $221.26/1000h.
  S94 + S95 contribute $0.
- KEY S95 FINDING: trips B_DS_AVAIL_LKR intra-Layout-A force-best-DS-bot
  candidate lands cleanly MIXED on all 3 gates. NARROW (the closest gate)
  at N=200 $+4.59 / N=1000 $+4.75, |Δ|=$0.16, 93.9% sign-agreement —
  $0.25 short of $5 SHIP bar on each grid. The two-grid noise is small;
  this is an honest miss.
- KEY S95 METHODOLOGY LESSON: picker alignment is the SECOND necessary
  condition for rule extraction (alongside S94's trigger-predictivity
  boundary). Rules 20/25 had ≥89% picker alignment by happy accident;
  the same `bot_pair_high desc` criterion gave 3-8% picker alignment for
  trips Layout-A DS-bot. The corrected `TOP_HIGH then pair_tops` lifted
  NARROW from $-3.22 to $+4.59 — a $7.81/1000h swing from picker change
  alone. **Picker criteria are cell-specific, not transferable.**
- Both Option D-revised rule-extraction sub-classes (bucket-level + intra-
  layout) now characterized as saturated on the current ML architecture.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard."
- User is non-technical; session reports lead with plain-language TL;DR.
- Session-end commit + push is pre-authorized.

DIRECTION FOR SESSION 96 — headline-goal recalibration / A3 retrain / v52-DL exploit:

  PRIMARY (PROMOTED from S94/S95 SECONDARY):
  Headline-goal recalibration.

  Doc-only session. With all three rule-shipping levers (chain-audit,
  bucket-level rule-extraction, intra-layout rule-extraction) characterized
  as saturated on the current ML architecture, make explicit that the
  95% match% goal is unreachable from the current architecture and reset
  the success criterion to maximize $/1000h subject to the current
  cascade. Affects S97+ planning, MIXED-session interpretation, and
  recasts the project trajectory.

  Engineering scope (~1-2 hours of careful documentation):
  * Phase A (~30 min): audit STRATEGY_GUIDE.md, CLAUDE.md, and historical
    decisions for explicit references to "95% match%" or equivalent
    headline goals.
  * Phase B (~30 min): draft new success criterion — maximize $/1000h
    subject to current cascade. Document the saturation evidence from
    S91-S95 that motivates the pivot.
  * Phase C (~30 min): update STRATEGY_GUIDE.md (in-place), DECISIONS_LOG
    (append Decision 131), CURRENT_PHASE.md (rewrite for S97).
  * No code changes. No engine runs. No grader runs.

  ALTERNATIVE DIRECTIONS:

  (a) A3 ML retrain (SECONDARY, multi-session compute investment).
      Formally closed at v44 in S78 (Decision 113). Option C
      infrastructure provides the foundation; ~70 hours wall on
      current hardware (6M / 27 hands/s ≈ 222,000 s ≈ 62 h). Reopening
      requires either a new feature family or explicit operator
      authorization. The S91-S95 saturation findings raise the question
      of whether a richer ML champion would shift the saturation
      boundary — this is the only remaining lever with potential to
      recover $50+/1000h. Substantial compute investment.

  (b) v52-defensive-low partial-effectiveness exploit (TERTIARY,
      DEFERRED from S90). Per-hand picker between v52-DL and v44_dt on
      the ~23% of S90 hands where v52-DL wins. Speculative; smaller
      magnitude than A3.

  (c) v44_RULE13 fallthrough replacement (DEFERRED).

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged (23 sessions).
- v65_mid_pair_chain_extend is the production rule chain (UNCHANGED).
- v55_two_pair_hybrid + v56_trips_hybrid blanket-route their targets to
  v44_dt unconditionally — DO NOT undo this routing without quantifying
  the $515+$33 bleed they currently absorb (S92 finding).
- v54 + Rule 29 absorb $195 of chain bleed on LOW pair (S91 quantified).
- The pre-committed-verdict pattern is project standard.
- NEW S94: trigger predictivity ≥ 62-70% is the operational definition
  of "rule extractable" (Rule 20: 89%, Rule 25: 62%).
- NEW S95: picker alignment with oracle's specific pick is the SECOND
  necessary condition for rule extraction. High direction predictivity
  is NOT sufficient.
- NEW S95: picker criteria are cell-specific, not transferable. A
  successful Rule's picker won't necessarily carry over to a new cell.
  Validate via 8-criterion sweep (3-min cost).
- Option C N=1000 sparse infrastructure remains available (S93 + S95 use).
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
