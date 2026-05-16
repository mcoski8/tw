# Current: Sprint 8 — Session 94 STRUCTURAL NULL on within-v44_dt rule-extraction (Option D-revised) applied to two_pair LAYOUT_A_SS + 9 adjacent residual cells; **production v65 UNCHANGED at $1,633.79/1000h**; Phase A audit DEFINES the rule-extraction lever's structural saturation boundary (analogous to S91/S92's chain-audit boundary closure); the only candidate showing Rule-20-style intra-layout signal is **trips B_DS_AVAIL_LKR intra-Layout-A bot_suit (S95 borderline ship candidate)** — $5.89/1000h on 8,160 hands at ≥70% trigger predictivity, $19.49 aggregate at 100% accuracy, requires Rule-20-style picking-logic engineering; v44_dt UNCHANGED for 22nd consecutive session; Combined S87-S94 production-chain recovery $221.26/1000h (S94 contributes $0); chain-audit + bucket-level rule-extraction levers are BOTH characterized as saturated on the current ML architecture.

S94 executed the S93-defined PRIMARY path verbatim: rule-extraction on two_pair LAYOUT_A_SS at $35.22/1000h on 437,580 hands. Phase A characterization found v44_dt is structurally saturated at the (hi_pair, lo_pair) bucket level (75 of 78 buckets have matching modal layouts). Sub-bucket trigger search across 691 (hi, lo, max_sing) sub-buckets within v44_layout=B found ZERO buckets with P(oracle=Layout C | v44=Layout B) ≥ 70% (Rule 20 anchor); top sub-bucket reaches 50% on 4 hands; no large sub-bucket exceeds 35%. Probe of the analogous trips cell B_DS_AVAIL_LKR ($42.61/1000h on 163K hands) replicates the bucket-level saturation. Cross-cell audit across all 10 within-v44_dt residual cells confirms structural saturation: **aggregate bucket-level layout-flip ceiling $5.08/1000h, under the $5 SHIP bar even at 100% trigger accuracy**. Intra-Layout-A bot_suit follow-up on trips B_DS_AVAIL_LKR (the only cell × structure-layer showing Rule-20-style intra-layout signal): $19.49/1000h aggregate when v44 picks non-DS bot but oracle picks DS bot within Layout-A-agree; two narrow sub-buckets reach ≥70% predictivity totaling 8,160 hands at $5.89/1000h — **borderline S95 ship candidate**.

**Cross-cell saturation map (S94 Phase A):**

| Category | Cell | n | wg ($/1000h) | bucket-flip ceiling | max sub-bucket P |
|---|---|---:|---:|---:|---:|
| two_pair | LAYOUT_A_DS | 257,400 | $12.13 | $0.00 | 28.4% |
| two_pair | LAYOUT_C_DS | 308,880 | $5.66 | $0.27 | 19.0% |
| two_pair | LAYOUT_B_DS | 231,660 | $15.28 | $0.59 | 20.2% |
| two_pair | LAYOUT_A_SS | 437,580 | **$35.22** | $1.60 | 29.3% |
| two_pair | LAYOUT_C_SS_ONLY | 90,090 | $12.38 | $0.94 | 42.1% |
| two_pair | LAYOUT_B_SS_ONLY | 12,870 | $0.13 | $0.00 | — |
| trips | B_DS_AVAIL_HKR | 62,055 | $16.85 | $0.00 | 57.5% |
| trips | B_DS_AVAIL_LKR | 163,170 | **$42.61** | $1.68 | 50.5% |
| trips | NO_BDS_CTOP | 20,592 | $1.21 | $0.00 | 32.0% |
| trips | NO_BDS_AKDOM | 82,368 | $4.52 | $0.00 | 20.9% |
| **TOTAL** | | **2,008,070** | **$146.00** | **$5.08** | **max 57.5%** |

**Intra-Layout-A bot_suit signal (S94 Phase A.2 — only cell × structure-level showing Rule-20-style signal):**

| sub-bucket (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings) | n | P(oracle DS) | wg ($/1000h) |
|---|---:|---:|---:|
| (2, 4, 1) | 210 | **100.0%** | $0.17 |
| (3, 4, 1) | 370 | **98.4%** | $0.36 |
| (2, 4, 3) | 4,911 | 48.4% | $2.42 |
| (2, 3, 1) | 17,838 | 28.9% | $4.70 |
| Sub-buckets at ≥70% trigger threshold | **8,160** | (mixed) | **$5.89** |

**No production change. v65 remains strategy of record.**

| metric | pre-S94 | post-S94 | Δ |
|---|---:|---:|---:|
| Full grid (N=200) | $1,633.79 | $1,633.79 | $0.00 |
| Prefix grid (N=1000) | $776.88 | $776.88 | $0.00 |
| Production vs v44_dt | $552.79 | $552.79 | $0.00 |
| Remaining gap to oracle | $111.41 | $111.41 | $0.00 |
| Cumulative closure since pre-S68 | 92.09% | 92.09% | 0.00pp |
| Rule count | 25 | 25 | 0 |

> **🎯 IMMEDIATE NEXT ACTION (Session 95): trips B_DS_AVAIL_LKR intra-Layout-A bot_suit candidate (PRIMARY), OR headline-goal recalibration (SECONDARY), OR A3 ML retrain (TERTIARY)**
>
> Chain-audit lever remains exhausted (S92 finding). Bucket-level rule-extraction lever is now characterized as saturated (S94 finding). The only OPEN candidate at the rule-extraction layer is the trips B_DS_AVAIL_LKR intra-Layout-A bot_suit improvement identified in S94's Phase A.2.
>
> 1. **PRIMARY — trips B_DS_AVAIL_LKR intra-Layout-A bot_suit rule (NEW S94 finding).**
>    Borderline at $5.89/1000h on 8,160 hands at ≥70% trigger predictivity ($19.49/1000h aggregate at 100% trigger accuracy). Engineering scope:
>    * **Phase A** (~30 min): re-confirm S94 finding from per-hand data; lock the trigger definition (likely a multi-gate sweep over the suit-feature buckets).
>    * **Phase B** (~1-2 hours): design "force-best-DS-bot-within-Layout-A" picking logic (analog of Rule 20's "best DS configuration"). Pre-drill multiple trigger widths (narrow at ≥70%, medium, wide) on N=200 full grid. Identify swap-right rate, n_changed, lift.
>    * **Phase C** (~10-15 min wall + ~5 min grader): if N=200 ≥ $5 SHIP bar, run Option C sparse N=1000 on changed canonical_ids, then two-grid grader at pre-committed thresholds (SHIP both ≥ $5; NULL both ≤ $1; otherwise MIXED).
>    * **Phase D** (if SHIP): build strategy_v66 composing v65 with new trips rule (firing zones likely disjoint — trips vs HIGH_ONLY + MID pair). Final whole-grid grader + session-end protocol.
>    * **Estimated ship probability: 20-40%** — most likely lands MIXED at the two-grid grader.
>
> 2. **SECONDARY — headline-goal recalibration.**
>    Carried from S92/S93/S94 TERTIARY. With both chain-audit and bucket-level rule-extraction levers characterized as saturated, this is the moment to make explicit that 95% match% is unreachable on current ML architecture and reset the success criterion to maximize $/1000h. Affects future MIXED-session interpretation, resource allocation, and S96+ planning.
>
> 3. **TERTIARY — ML retrain (A3 full 6M-hand N=1000 grid).** Formally closed at v44 in S78 (Decision 113). Option C infrastructure now provides the foundation; ~70 hours wall on current hardware. Reopening requires either a new feature family or explicit operator authorization. The structural saturation findings from S91-S94 raise the question of whether a richer ML champion would shift the saturation boundary.
>
> 4. **DEFERRED — v52-defensive-low partial-effectiveness exploit (S90 finding).** Still speculative.
>
> 5. **DEFERRED — v44_RULE13 fallthrough replacement.** With v54/v55/v56 absorbing $731/1000h of chain bleed across pair-family, replacement primarily matters for HIGH_ONLY (already gated by v64/v65).

> **📓 METHODOLOGY (Session 95+ — refined through S94):**
>
> 1. **OPTION D-REVISED HAS A STRUCTURAL SATURATION BOUNDARY (NEW S94).**
>    Just as the chain-audit lever has a saturation boundary (S91/S92 NULLs), the rule-extraction lever applied to within-v44_dt residuals has a STRUCTURAL TRIGGER-PREDICTIVITY BOUNDARY. The boundary is **trigger predictivity ≥ 62-70%** at the (cell × structural feature) level. Chain-audit + bucket-level rule-extraction levers are BOTH saturated on the current ML architecture.
>
> 2. **TRIGGER PREDICTIVITY IS THE OPERATIONAL DEFINITION OF "RULE EXTRACTABLE" (NEW S94).**
>    Rule 20 trigger predictivity ≥ 89% (S83). Rule 25 trigger predictivity = 62% (S86 + S93). These are the empirical anchors. Below ~62%, a deterministic-pick rule cannot ship cleanly because false-positive cost dominates true-positive gain. **Predictivity is the gating signal; the leak magnitude alone is insufficient.** Two_pair LAYOUT_A_SS has $35.22/1000h leak but no trigger above 29.3% — leak alone does not imply extractability.
>
> 3. **INTRA-LAYOUT IMPROVEMENTS ARE A DISTINCT LEVER SUB-CLASS WITHIN OPTION D-REVISED (NEW S94).**
>    Bucket-level layout-flip rules capture only $5.08/1000h across all 10 within-v44_dt residual cells — under SHIP bar. The Rule-20-style mechanism is INTRA-LAYOUT (within the modal layout choice, flip a sub-structural feature like bot_suit). Trips B_DS_AVAIL_LKR intra-Layout-A bot_suit is the first identified candidate of this sub-class on a within-v44_dt residual cell.
>
> 4. **HAND-SPECIFIC RESIDUAL DOMINATES STRUCTURAL RESIDUAL ON THESE CELLS (NEW S94).**
>    Two_pair LAYOUT_A_SS's $35.22/1000h leak distributes across 702 (hi_pair, lo_pair, max_sing) sub-buckets with no concentration: top-30 sum to $3.82; top-100 sum to $11.18. The residual is not waiting for a structural rule — it's hand-specific variance that requires either oracle-quality picks (richer ML champion) or a different lever entirely.
>
> 5. **NULL AUDIT SESSIONS DEFINE THE LEVER BOUNDARY (carried + extended from S91/S92).**
>    S91/S92 closed the chain-audit lever. S94 closes the bucket-level rule-extraction lever on within-v44_dt residuals. Both are honest, useful, complete-cycle sessions. The cumulative effect is to characterize the architecture's saturation surface — which is necessary to make the case for an architecture pivot (A3 ML retrain or headline-goal recalibration).
>
> 6. **OPTION C N=1000 SPARSE INFRASTRUCTURE REMAINS AVAILABLE (carried from S93).**
>    For ANY future cell-scale validation, the engine `--id-list-file` mode is ready. Throughput ~25 hands/s parallel; bit-identical to existing prefix N=1000 grid; unblocks two-grid SHIP standard on arbitrary cell subsets.
>
> 7. **PRE-COMMITTED VERDICT PATTERN (project standard).**
>    Threshold locked in code BEFORE the data is read. S94's audit script hard-coded the Rule 20 / Rule 25 trigger predictivity anchors (≥ 0.70, ≥ 0.62) BEFORE reading the parquet; the verdict at NO sub-bucket reaching threshold fell out mechanically.

> **✅ ARTIFACTS produced in S94:**
> 1. `analysis/scripts/audit_rule_extraction_structural_S94.py` — cross-cell saturation audit + intra-Layout-A bot_suit follow-up (NEW)
> 2. `data/session94/audit_summary.log` — full audit script output (NEW)
> 3. `data/session94/audit_rule_extraction_structural_summary.json` — per-cell saturation evidence + sub-bucket trigger search + intra-Layout-A bot_suit pivot table (NEW)
> 4. `SESSION_94_REPORT.md` — plain-language session report + complete saturation evidence (NEW)
> 5. `DECISIONS_LOG.md` — Decision 129 (S94 STRUCTURAL NULL + 4 methodology refinements) appended
> 6. `CURRENT_PHASE.md` — this file, rewritten for S95
> 7. `STRATEGY_GUIDE.md` — Part 1 appended (Session 94 entry; no production change, saturation-boundary documentation)
> 8. `sprints/SPRINT_INDEX.md` — S94 entry appended

> Updated: 2026-05-16 (Session 94 end — **STRATEGY OF RECORD UNCHANGED: v65 remains production.** S94 executed the S93-defined PRIMARY path verbatim: rule-extraction on two_pair LAYOUT_A_SS at $35.22/1000h on 437,580 hands. Phase A characterization found v44_dt structurally saturated at the (hi_pair, lo_pair) bucket level (75 of 78 buckets have matching modal layouts; max sub-bucket trigger predictivity 29.3%, well under Rule 20's 70% anchor and Rule 25's 62% anchor). Cross-cell audit across all 10 within-v44_dt residual cells (6 two_pair + 4 trips) confirmed structural saturation: aggregate bucket-level layout-flip ceiling $5.08/1000h, under the $5 SHIP bar even at 100% trigger accuracy. Intra-Layout-A bot_suit follow-up on trips B_DS_AVAIL_LKR identified $19.49/1000h aggregate signal (when v44 picks non-DS bot but oracle picks DS bot within Layout-A-agree); two narrow sub-buckets at (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings) = (2, 4, 1) and (3, 4, 1) reach 100% and 98.4% trigger predictivity respectively but together only carry $0.53/1000h; ≥70% sub-buckets total 8,160 hands at $5.89/1000h aggregate — borderline S95 ship candidate. Verdict: STRUCTURAL NULL on PRIMARY. Production v65 UNCHANGED. v44_dt UNCHANGED for 22nd consecutive session. Combined S87-S93 production-chain recovery still $221.26/1000h. Decision 129 records the NULL + 4 methodology refinements: (1) Option D-revised rule extraction has a STRUCTURAL SATURATION BOUNDARY analogous to S91/S92's chain-audit boundary; (2) Rule 20 / Rule 25 trigger anchor (≥62-70% predictivity on structural feature) is the OPERATIONAL DEFINITION of "rule extractable"; (3) intra-layout bot_suit improvements are a NEW lever sub-class within Option D-revised but require Rule-20-style picking-logic engineering; (4) two_pair + trips within-v44_dt residual leak is dominated by hand-specific suit/rank details that no structural feature in the existing parquets captures. Both chain-audit + bucket-level rule-extraction levers are now characterized as saturated on the current ML architecture. S95 default plan: trips B_DS_AVAIL_LKR intra-Layout-A bot_suit candidate (PRIMARY, borderline 20-40% ship probability), OR headline-goal recalibration (SECONDARY), OR A3 ML retrain (TERTIARY).)

---

## Headline state at end of Session 94

**Strategies of record (UNCHANGED from S93):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 22 sessions, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence (remaining gap to oracle ceiling): **$111.41/1000h** (UNCHANGED). Cumulative closure since pre-S68: $1,297.59 = **92.09% of original $1,409** (UNCHANGED).

Production vs v44_dt: production outperforms ML by **$552.79/1000h** (UNCHANGED).

**Total project rule count: 25** (UNCHANGED).

**S94 results (STRUCTURAL NULL):**

| target | verdict | notes |
|---|---|---|
| two_pair LAYOUT_A_SS rule extraction | STRUCTURAL NULL | 75/78 (hi,lo) buckets match v44/oracle modal layout; max sub-bucket trigger P = 29.3%, below 62% Rule 25 anchor |
| 10-cell cross-cell saturation map | CONFIRMED SATURATED | aggregate bucket-level ceiling $5.08/1000h; max sub-bucket P across all cells = 57.5% |
| trips B_DS_AVAIL_LKR intra-Layout-A bot_suit | S95 CANDIDATE (borderline) | $5.89/1000h on 8,160 hands at ≥70% trigger; requires picking-logic engineering |

---

## Hypothesis cascade status (updated after S94)

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
| Headline-goal recalibration | Concede 95% match% as unreachable | OPEN — now well-motivated by S91 + S92 + S94 saturation findings; promoted to S95 SECONDARY. |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86/S93) | MID × PMID_DS_NOMAXTOP | SHIPPED — Rule 25 + $6.43 (Decision 128). |
| DAMAGE-CONTROL chain audit cells #1-4 (S87-S90) | HIGH_ONLY × various | SHIPPED 4 rules totaling $214.83/1000h (Decisions 122-125). |
| DAMAGE-CONTROL chain audit cell #5 (S91) | LOW pair PMID prefix-COVERED | NULL — population-divergence noise (Decision 126). |
| DAMAGE-CONTROL chain audit cell #6 + #7 (S92) | two_pair + trips chain audit | STRUCTURAL NULL — chain collapsed by v55/v56 blanket routing (Decision 127). |
| Chain-audit arc (S87-S92 closure) | 5 sessions across 4 categories | COMPLETE — 4 SHIPS ($214.83/1000h) + 2 NULLs at well-characterized boundaries. |
| Option C N=1000 oracle infrastructure (S93) | Engine `--id-list-file` mode | SHIPPED — bit-identical to prefix grid; ~25 hands/s parallel. Decision 128. |
| **Option D-revised rule extraction within-v44_dt residual (S94)** | **two_pair LAYOUT_A_SS + 9 adjacent cells** | **STRUCTURAL NULL — bucket-level trigger predictivity below 62-70% Rule 25/Rule 20 anchor across all 10 cells. Decision 129.** |
| **Rule-extraction arc (S83-S94 closure on bucket-level)** | **two_pair + trips + LOW pair + MID pair within-v44_dt residual** | **COMPLETE for bucket-level layout-flip rules.** 2 SHIPS (Rules 20, 25) + 2 MIXED (S84) + 1 NULL (S85) + S94 STRUCTURAL NULL saturation map. |
| **Intra-Layout-A bot_suit candidate (S95 PRIMARY)** | **trips B_DS_AVAIL_LKR, $19.49 aggregate / $5.89 at ≥70% trigger** | **OPEN — borderline S95 candidate. Requires Rule-20-style picking-logic engineering.** |
| v60 gate=11 (S93 SECONDARY finding) | MID × PMID_DS_NOMAXTOP × max_sing ≤ J | MIXED at +$4.85/+$4.77; eligible for relaxed-bar or composite-rule re-evaluation. |
| v52-defensive-low refinement (S90 finding) | Per-hand picker between v52-DL and v44 | DEFERRED — speculative. |

**Cascade verdict (post S94):** Chain-audit lever exhausted (S92 closure). Bucket-level rule-extraction lever exhausted on within-v44_dt residuals (S94 closure). The only OPEN rule-layer candidate is the trips B_DS_AVAIL_LKR intra-Layout-A bot_suit improvement.

* **ML cascade:** EXHAUSTED at v44 saturating regime (no change since S78 / Decision 113).
* **Rule-layer cascade — chain audit (S87-S92):** COMPLETE. $214.83/1000h shipped + 2 NULLs at boundaries.
* **Rule-layer cascade — Option D-revised rule extraction (S83-S94):** $23.24/1000h cumulative across two ships (Rules 20 + 25) + S94 saturation map. Bucket-level lever EXHAUSTED. Intra-layout sub-lever OPEN (S95 PRIMARY).
* **Infrastructure cascade (S93+):** Option C N=1000 sparse-grid infrastructure available for any future cell-scale validation.

---

## Resume Prompt (Session 95 — trips B_DS_AVAIL_LKR intra-Layout-A bot_suit candidate / headline-goal recalibration / A3 retrain)

```
Resume Session 95 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S94 — opens with the S95 pivot plan
  + alternative-direction options)
- DECISIONS_LOG.md (latest: Decision 129 — S94 STRUCTURAL NULL on
  within-v44_dt rule-extraction; production v65 UNCHANGED; defines the
  rule-extraction lever's saturation boundary analogous to S91/S92's
  chain-audit closure; identifies trips B_DS_AVAIL_LKR intra-Layout-A
  bot_suit as the only OPEN rule-layer candidate — borderline at
  $5.89/1000h on 8,160 hands at ≥70% trigger predictivity)
- SESSION_94_REPORT.md (S94 STRUCTURAL NULL audit, cross-cell
  saturation map across 10 within-v44_dt residual cells, intra-Layout-A
  bot_suit follow-up identifying the S95 candidate, methodology
  lessons defining the operational boundary)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/session93/v60_n1000_sparse.bin — S93 sparse N=1000 grid (32,304 hands)
- data/drill_pair_v44_per_hand_structural.parquet — pair per-hand
- data/drill_two_pair_v44_per_hand_structural.parquet — two_pair per-hand
- data/drill_trips_v44_per_hand_structural.parquet — trips per-hand
  (S95 target — B_DS_AVAIL_LKR at $42.61/1000h on 163K hands)
- data/v44_dt_model.npz — production ML champion (UNCHANGED 22 sessions)
- data/session94/* — S94 saturation audit artifacts (audit_summary.log,
  audit_rule_extraction_structural_summary.json)

STATE (end of S94):
- Production rule chain: v65_mid_pair_chain_extend ($1,633.79 full /
  $776.88 prefix). UNCHANGED from S93.
- ML champion v44_dt UNCHANGED (22 consecutive sessions).
- Two-track divergence (remaining gap to oracle): $111.41/1000h.
- Rule count: 25 (UNCHANGED).
- Cumulative closure since pre-S68: 92.09% of original $1,409.
- Combined S87-S93 production-chain recovery: $221.26/1000h.
  S94 contributes $0.
- KEY S94 FINDING: rule-extraction (Option D-revised) on within-v44_dt
  residual cells is STRUCTURALLY SATURATED at the bucket level. 75 of 78
  (hi_pair, lo_pair) buckets in two_pair LAYOUT_A_SS have matching
  v44/oracle modal layouts; max sub-bucket trigger predictivity across
  all 10 within-v44_dt residual cells is 57.5%, below the 62-70%
  Rule 25 / Rule 20 SHIP anchor. Aggregate bucket-level layout-flip
  ceiling = $5.08/1000h across all 10 cells (under SHIP bar even at
  100% trigger accuracy).
- KEY S94 CANDIDATE: trips B_DS_AVAIL_LKR intra-Layout-A bot_suit
  ($19.49 aggregate, $5.89 at ≥70% trigger on 8,160 hands). Borderline
  ship — requires Rule-20-style picking-logic engineering and is
  estimated 20-40% likely to clear the two-grid SHIP bar.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard."
- User is non-technical; session reports lead with plain-language TL;DR.
- Session-end commit + push is pre-authorized.

DIRECTION FOR SESSION 95 — trips B_DS_AVAIL_LKR intra-Layout-A bot_suit / headline-goal recalibration / A3 retrain:

  PRIMARY (NEW S94 finding, BORDERLINE 20-40% ship probability):
  Trips B_DS_AVAIL_LKR intra-Layout-A bot_suit candidate.

  Engineering scope: design Rule-20-analog rule for trips that fires on
  (hand is trips) × (cell B_DS_AVAIL_LKR) × (Layout-A modal pick agreed
  with oracle) × (v44 picks non-DS bot, suit-features predict oracle
  picks DS bot). Forced pick: best Layout-A setting with DS bot.

  Phase A (~30 min): re-confirm S94 finding via per-hand data; lock the
  trigger definition. Likely a multi-gate sweep over the suit-feature
  buckets identified in S94:
    - Narrow trigger (≥70% predictivity): (kickers_max_suit_count, 
      n_kickers_in_trip_suits, n_b_ds_routings) ∈ {(2,4,1), (3,4,1)} 
      — 580 hands at near-100% but only $0.53 wg.
    - Medium trigger: include (2,4,3) at 48% — adds 4,911 hands, $2.42 wg.
    - Wide trigger: include (2,3,1) at 29% — adds 17,838 hands, $4.70 wg.

  Phase B (~1-2 hours): design "force-best-DS-bot-within-Layout-A"
  picking logic (analog of Rule 20's "best DS configuration" — needs to
  enumerate Layout-A settings, find the highest-bot-pair-high config
  with DS bot). Pre-drill each gate on N=200 full grid. Identify
  swap-right rate, n_changed, lift.

  Phase C (~10-15 min wall + ~5 min grader): if N=200 ≥ $5 SHIP bar,
  run Option C sparse N=1000 on changed canonical_ids, then two-grid
  grader at pre-committed thresholds (SHIP both ≥ $5; NULL both ≤ $1;
  otherwise MIXED).

  Phase D (if SHIP): build strategy_v66 composing v65 with new trips
  rule (firing zones likely disjoint — trips vs HIGH_ONLY + MID pair).
  Final whole-grid grader + session-end protocol (commit + push + docs).

  ALTERNATIVE DIRECTIONS:

  (a) Headline-goal recalibration (SECONDARY, doc-only session). With
      both chain-audit and bucket-level rule-extraction levers
      characterized as saturated, make explicit that 95% match% is
      unreachable on current ML architecture; reset success criterion
      to maximize $/1000h subject to current cascade. Doc-only session
      — useful for sharpening S96+ planning.

  (b) A3 ML retrain (TERTIARY, multi-session compute investment).
      Formally closed at v44 in S78 (Decision 113). Option C
      infrastructure provides the foundation; ~70 hours wall on
      current hardware (6M / 25 hands/s ≈ 240,000 s ≈ 67 h).
      Reopening requires either a new feature family or explicit
      operator authorization. The S91-S94 saturation findings raise
      the question of whether a richer ML champion would shift the
      saturation boundary.

  (c) v52-defensive-low partial-effectiveness exploit (DEFERRED from S90).

  (d) v44_RULE13 fallthrough replacement (DEFERRED).

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged (22 sessions).
- v65_mid_pair_chain_extend is the production rule chain (UNCHANGED).
- v55_two_pair_hybrid + v56_trips_hybrid blanket-route their targets to
  v44_dt unconditionally — DO NOT undo this routing without quantifying
  the $515+$33 bleed they currently absorb (S92 finding).
- v54 + Rule 29 absorb $195 of chain bleed on LOW pair (S91 quantified).
- The pre-committed-verdict pattern is project standard.
- NEW S94: trigger predictivity ≥ 62-70% is the OPERATIONAL DEFINITION
  of "rule extractable" (Rule 20: 89%, Rule 25: 62%). Below this, a
  deterministic-pick rule cannot ship cleanly because false-positive
  cost dominates true-positive gain.
- NEW S94: leak magnitude alone does not imply extractability —
  two_pair LAYOUT_A_SS has $35.22/1000h leak but max trigger 29.3%.
- NEW S94: bucket-level layout-flip rules + chain-audit + ML cascade
  are ALL characterized as saturated on current ML architecture.
- Option C N=1000 sparse infrastructure remains available (S93 ship).
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
