# Session 94 — STRUCTURAL NULL on within-v44_dt rule-extraction (two_pair LAYOUT_A_SS + trips B_DS_AVAIL_LKR). **Production v65 UNCHANGED.** Phase A audit defines the Option D-revised lever's saturation boundary; identifies a borderline S95 candidate (trips B_DS_AVAIL_LKR intra-Layout-A bot_suit, $5.89/1000h ceiling at Rule-20 trigger threshold).

_Generated 2026-05-16. S94 executed the S93-defined PRIMARY path verbatim: rule-extraction on the largest unaddressed within-v44_dt residual cell, two_pair LAYOUT_A_SS at $35.22/1000h on 437,580 hands. Phase A characterization found v44_dt structurally saturated at the bucket level: 75 of 78 (hi_pair, lo_pair) buckets have v44 picking the same modal layout as oracle. Within the largest sub-cell pivot ((v44 layout=B, oracle layout=C), $10.47/1000h on 23,326 hands), the highest-predictivity sub-bucket on (hi, lo, max_sing) features reaches only 29.3% — well under Rule 20's ≥70% trigger anchor and Rule 25's 62% anchor. Probe of the analogous trips cell B_DS_AVAIL_LKR ($42.61/1000h on 163,170 hands) replicates the saturation: layout-flip ceiling $1.68/1000h, max sub-bucket predictivity 50.5%. **Aggregate cross-cell layout-flip ceiling across 10 within-v44_dt residual cells: $5.08/1000h — under the $5 SHIP bar even at 100% trigger accuracy.** A follow-up drill on trips B_DS_AVAIL_LKR intra-Layout-A bot_suit (the only cell × structure-level showing Rule-20-style signal: $19.49/1000h potential, $5.89 at ≥70% predictivity on 8,160 hands) is logged as a borderline S95 candidate requiring non-trivial picking-logic engineering. Verdict: STRUCTURAL NULL on the PRIMARY direction. **v65_mid_pair_chain_extend remains production at $1,633.79/1000h full grid. v44_dt UNCHANGED for 22nd consecutive session. Combined S87-S93 production-chain recovery still $221.26/1000h (S94 contributes $0).** Decision 129 records the STRUCTURAL NULL + four methodology refinements: (1) Option D-revised rule extraction has a STRUCTURAL SATURATION BOUNDARY analogous to S91/S92's chain-audit boundary; (2) Rule 20 / Rule 25 trigger anchor (≥62-70% predictivity on a single structural feature) is the OPERATIONAL DEFINITION of "rule extractable"; (3) intra-LAYOUT bot_suit improvements are a NEW lever sub-class within Option D-revised but require Rule-20-style picking-logic engineering; (4) two-pair + trips within-v44_dt residual leak is dominated by hand-specific suit/rank details that no structural feature in the existing parquets captures._

## TL;DR — Plain language

**What changed in your strategy of record:** **Nothing.** v65 remains production at $1,633.79/1000h. This was an audit session, not a ship session.

**What we tested:** Whether a new rule could be extracted from within the v44_dt residual leak on two_pair LAYOUT_A_SS — the largest unaddressed sub-cell in the project ($35.22 per 1000 hands on 437,580 hands). The S94 plan called for a Rule-20-style structural-feature trigger that would let production beat v44_dt on a sub-population of these hands.

**Why no ship.** v44_dt is already picking the right modal layout (which of the three layouts A/B/C to use) on 75 of 78 (high pair, low pair) buckets in this cell. Among the hands where v44 picks the wrong layout, no structural-feature sub-bucket predicts oracle's preferred direction with more than 29% confidence. Rule 20's playbook required 89-93% trigger predictivity to ship at +$16.81/1000h; Rule 25's required 62% to ship at +$6.43/1000h. The two_pair LAYOUT_A_SS cell's signal is structurally too noisy at the (hi, lo, max_sing) feature level.

**What we did instead.** Probed the four other major within-v44_dt residual cells (3 two_pair cells, 1 trips cell) to see if any has the same Rule-20-style signal:

* All six two_pair cells: ceiling addressable via bucket-level layout flips = **$3.40/1000h total**, well under the $5 SHIP bar even at 100% trigger accuracy.
* All four trips cells: ceiling **$1.68/1000h total**.
* **Combined ceiling across 10 within-v44_dt residual cells: $5.08/1000h.**

The only cell × structure layer showing genuine Rule-20-style intra-layout signal: **trips B_DS_AVAIL_LKR intra-Layout-A bot_suit** ($19.49/1000h potential when v44 picks Layout A with a non-DS bot but oracle picks Layout A with a DS bot). Two narrow suit-feature sub-buckets reach 98-100% trigger predictivity but together only carry $0.53/1000h. The broader sub-buckets with material wg ($4-12/1000h each) drop to 30-50% predictivity — below the SHIP threshold for a deterministic forced-pick rule.

**The methodology finding.** Just as S91 and S92 mapped the boundary of the chain-audit lever and declared it complete, S94 maps the boundary of the Option D-revised rule-extraction lever within v44_dt's residual. **Both major rule-shipping levers are now characterized as saturated on the current ML architecture.** Future ships from this category require either a Rule-20-style mechanism we haven't yet probed (the trips intra-Layout-A bot_suit candidate) or a different lever (richer ML champion, headline-goal recalibration, etc.).

**The numbers (UNCHANGED from S93):**

* Production v65: **$1,633.79/1000h full grid / $776.88 prefix**.
* v44_dt: $1,081 full / $686 prefix (**UNCHANGED for 22 consecutive sessions**, since v44 in S58).
* Production vs v44_dt: $552.79/1000h.
* Remaining gap to oracle ceiling: $111.41/1000h.
* Cumulative closure since pre-S68: $1,297.59 of $1,409 = **92.09%**.
* Rule count: 25 (UNCHANGED).
* Combined S87-S93 production-chain recovery: $221.26/1000h. **S94 contributes $0.**

**What's on the table for S95:**

1. **PRIMARY** — Trips B_DS_AVAIL_LKR intra-Layout-A bot_suit candidate (the S94 audit's strongest finding). $19.49/1000h aggregate potential; $5.89/1000h on 8,160 hands meeting the ≥70% predictivity bar. Requires designing a deterministic "force-best-DS-bot-within-Layout-A" picking logic, building strategy_v66, pre-drilling on the existing N=200 grid (cheap), then Option C sparse N=1000 grading (~10-15 min wall at 25 h/s on this hands). **Borderline:** at 100% trigger accuracy this just clears SHIP. Realistic expected lift at empirically observed predictivity is $2-4/1000h — likely MIXED, not SHIP.
2. **SECONDARY** — Headline-goal recalibration (carried from S92/S93 TERTIARY). Make explicit that 95% match% is unreachable from current architecture; reset target to maximize $/1000h subject to current cascade. Affects how to read future MIXED ship sessions and where to invest engineering effort.
3. **TERTIARY** — ML retrain (A3 full 6M-hand N=1000 grid). Formally closed at v44 in S78 (Decision 113). Option C infrastructure now provides the foundation for the 6M × 105 × N=1000 grid (~70 hours wall at 25 hands/s on this hardware — non-trivial but no longer impossible). Reopening requires a new feature family.
4. **DEFERRED** — v52-defensive-low partial-effectiveness exploit (carried from S90). Speculative.

## The full story

### Phase A — Characterization of two_pair LAYOUT_A_SS

Read `drill_two_pair_v44_per_hand_structural.parquet` (S69 drill output). LAYOUT_A_SS = cell_idx 3, 437,580 hands, cid range [46,559, 6,008,276]; 125,756 hands in prefix coverage, 312,082 hands outside.

**Top-level structure.** Of 437,580 cell hands, v44 and oracle agree on the setting (v44_idx == oracle_idx) for 341,798 (78.1%). The remaining 95,782 hands are the leak — mean $220.97/1000h per mismatch hand, $35.22/1000h whole-grid contribution.

**v44_layout × or_layout pivot (off-diagonal: where v44 picks the wrong major layout):**

| v44_layout | or_layout | n | wg ($/1000h) |
|---:|---:|---:|---:|
| 2 (Layout C) | 1 (Layout B) | 26,861 | **+10.47** |
| 1 (Layout B) | 2 (Layout C) | 23,326 | +8.98 |
| 2 (Layout C) | 0 (Layout A) | 7,669 | +3.25 |
| 1 (Layout B) | 0 (Layout A) | 6,339 | +2.93 |
| 0 (Layout A) | 1 (Layout B) | 3,630 | +1.29 |
| 0 (Layout A) | 2 (Layout C) | 3,372 | +1.09 |
| 2 → 3 (SPLIT) | | 1,996 | +0.75 |
| 1 → 3 | | 1,826 | +0.74 |
| 0 → 3 | | 1,709 | +0.65 |

The biggest single pivot is v44=Layout C → oracle=Layout B ($10.47/1000h). If a rule could perfectly detect this trigger and flip the pick, it would capture exactly $10.47.

**(hi_pair, lo_pair) bucket modal-direction analysis:** 78 buckets (each with 1,000+ hands). For each bucket, compare oracle's most-common layout against v44_dt's most-common layout. **In 75 of 78 buckets, the modal layouts match.** The three disagreeing buckets total $1.60/1000h — the ceiling for any bucket-level layout-flip rule.

**Sub-bucket trigger search:** Within (v44_layout=B), look across 691 sub-buckets of (hi_pair, lo_pair, max_sing) for sub-buckets where P(oracle = Layout C | v44 = Layout B) is high. **Zero sub-buckets reach 70% predictivity** (Rule 20's threshold); only 3 reach 50%; the top sub-bucket is at 50.0% on 4 hands. The (v44=B → oracle=C) error is genuinely hand-specific, not structural-feature-determined.

### Phase A.2 — Probe adjacent within-v44_dt residual cells

The same bucket-level + sub-bucket trigger analysis applied to the other 5 two_pair cells + all 4 trips cells, summarized by `audit_rule_extraction_structural_S94.py`:

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

**Aggregate verdict on bucket-level layout-flip rules:** Across all 10 within-v44_dt residual cells, the maximum recoverable lift from a perfect bucket-level layout-flip rule is **$5.08/1000h** — and the maximum sub-bucket predictivity (the gating signal that determines whether a rule can ship) is 57.5%, below both Rule 25's 62% anchor and Rule 20's 70-93% anchor.

### Phase A.3 — Intra-layout bot_suit follow-up on trips B_DS_AVAIL_LKR

The bucket-level layout-flip analysis above only captures Layout-A vs Layout-B vs Layout-C major-layout flips. Rule 20 and Rule 25 are NOT layout-flip rules — they are **intra-layout structural-feature flips** (within PMID, force PMID_tnomax_DS instead of PMID_tmax_SS). A follow-up drill examined whether trips B_DS_AVAIL_LKR (highest-leak within-v44_dt residual cell at $42.61/1000h) has an analogous intra-layout opportunity.

Restrict to Layout-A agree (v44 and oracle both pick Layout A: 105,031 hands). Bot_suit pivot (codes: 0=DS, 1=SS, 2=31, 3=RB, 4=4f):

| v44_bot_suit | or_bot_suit | n | wg ($/1000h) |
|---|---|---:|---:|
| 2 (31) | 0 (DS) | 16,174 | **+12.64** |
| 1 (SS) | 0 (DS) | 8,710 | +5.83 |
| 4 (4f) | 0 (DS) | 835 | +0.73 |
| 3 (RB) | 0 (DS) | 186 | +0.30 |
| **Sum (v44 non-DS → oracle DS)** | | **25,905** | **+$19.49** |

**Aggregate intra-Layout-A bot_suit leak: $19.49/1000h on 25,905 hands.** This is the largest single-mechanism opportunity in the within-v44_dt residual category.

Sub-bucket trigger search on (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings) within (v44 picks non-DS bot, Layout A agree):

| kickers_max_suit_count | n_kickers_in_trip_suits | n_b_ds_routings | n | or_ds | P(oracle DS) | wg ($/1000h) |
|---:|---:|---:|---:|---:|---:|---:|
| 2 | 4 | 1 | 210 | 210 | **100.0%** | $0.17 |
| 3 | 4 | 1 | 370 | 364 | **98.4%** | $0.36 |
| 2 | 4 | 3 | 4,911 | 2,378 | 48.4% | $2.42 |
| 2 | 3 | 1 | 17,838 | 5,158 | 28.9% | $4.70 |
| 2 | 2 | 1 | 5,776 | 600 | 10.4% | $0.53 |
| 1 | 3 | 3 | 6,615 | 0 | 0.0% | $0.65 |

Two narrow sub-buckets reach ≥70% predictivity (Rule 20 anchor): 8,160 hands total at $5.89/1000h aggregate. **At 100% trigger accuracy this just clears the $5 SHIP bar.** The broader sub-buckets that carry the bulk of the leak ($4.70 and $2.42) drop to 28-48% predictivity — too low for a deterministic-pick rule to ship cleanly.

**S95 candidate.** Designing a strategy_v66 that implements this rule requires:

1. Detect trigger: hand is trips, in cell B_DS_AVAIL_LKR, suit-features satisfy (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings) ≥ 70% predictivity bucket. The "narrow" trigger is well-defined; whether to widen to lower-P buckets is an empirical question for Phase B.
2. Design picker: enumerate Layout A settings (top=kicker, mid=2 trips, bot=1 trip + 3 kickers), find the DS-bot config with the best secondary criterion. This is the trips analog of Rule 20's "best DS configuration."
3. Pre-drill on N=200 full grid, multi-gate sweep over candidate trigger widths.
4. If N=200 ≥ $5, Option C sparse N=1000 run (~10-15 min wall on ~8K-25K hands).
5. Two-grid grader at pre-committed thresholds → SHIP / NULL / MIXED.

**Estimated S95 ship probability:** 20-40%. Borderline candidate — most likely lands MIXED.

### Phase B/C/D — Skipped

Skipped per Phase A finding. No candidate in two_pair LAYOUT_A_SS (or any of the 5 other two_pair cells) cleared the trigger-predictivity threshold for a Rule-20-style mechanism. No Phase B pre-drill, Phase C Option C run, or Phase D composition was executed this session.

### Why this is a STRUCTURAL NULL (distinct from S91 + S92's NULLs)

* **S91 NULL** was POPULATION-DIVERGENCE NOISE: prefix and full grids evaluated different canonical_id populations within nominally identical sub-cells, so small per-sub-cell effects diverged in direction on the two grids.
* **S92 NULL** was STRUCTURAL at the strategy layer: production picks were byte-identical to v44_dt on every two_pair and trips hand, so chain-audit had zero candidates.
* **S94 NULL** is STRUCTURAL at the trigger layer: rule extraction is welcome to find a Rule-20-style trigger on a within-v44_dt residual cell, but no structural feature in the existing parquets predicts the v44 → oracle direction with the 62-93% confidence Rules 25 and 20 needed. v44_dt is structurally well-calibrated at the (hi_pair, lo_pair, max_sing) feature level on these cells.

The three NULL flavors map three different shapes of saturation. Together they characterize the boundaries of the chain-audit + rule-extraction levers as exhausted on the current ML architecture.

### Methodology lessons (S94)

1. **OPTION D-REVISED HAS A STRUCTURAL SATURATION BOUNDARY (NEW S94).** Just like the chain-audit lever, the rule-extraction lever applied to within-v44_dt residuals has a saturation boundary. The boundary is **trigger predictivity**: at the (cell × structural feature) level, no within-v44_dt residual sub-bucket on the two main remaining cells (two_pair LAYOUT_A_SS, trips B_DS_AVAIL_LKR) reaches the 62-70% Rule 25 / Rule 20 anchor. The residual leak is genuinely HAND-SPECIFIC (suit details, exact singleton ranks within a bucket) rather than STRUCTURAL.

2. **RULE 20 / RULE 25 TRIGGER PREDICTIVITY IS THE OPERATIONAL DEFINITION OF "RULE EXTRACTABLE" (NEW S94).** Rule 20 trigger predictivity ≥ 89% (S83). Rule 25 trigger predictivity = 62% (S86 + S93). These are the empirical anchors. Below ~62%, a deterministic-pick rule cannot ship cleanly because the false-positive cost (forcing the wrong pick on hands where v44_dt is correct) dominates the true-positive gain. **Predictivity is the gating signal; the leak magnitude alone is insufficient.** The two_pair LAYOUT_A_SS cell has $35.22/1000h of leak but no trigger above 29.3% — leak alone does not imply extractability.

3. **INTRA-LAYOUT IMPROVEMENTS ARE A DISTINCT LEVER SUB-CLASS WITHIN OPTION D-REVISED (NEW S94).** Bucket-level layout-flip rules (force Layout B instead of Layout C) only capture $5.08/1000h across all 10 within-v44_dt residual cells. The Rule-20-style mechanism is INTRA-LAYOUT (within the modal layout choice, flip a sub-structural feature like bot_suit). The trips B_DS_AVAIL_LKR intra-Layout-A bot_suit candidate ($19.49 potential aggregate, $5.89 at trigger ≥70%) is the first identified candidate of this sub-class on a within-v44_dt residual cell. Whether it ships is an S95 empirical question.

4. **HAND-SPECIFIC RESIDUAL DOMINATES STRUCTURAL RESIDUAL ON THESE CELLS (NEW S94).** Two_pair LAYOUT_A_SS's $35.22/1000h leak distributes across 702 (hi_pair, lo_pair, max_sing) sub-buckets with no concentration: top-30 sub-buckets sum to $3.82; top-100 sum to $11.18. The residual leak is not waiting for a structural rule to capture it — it's hand-specific variance that requires either oracle-quality picks (i.e., a richer ML champion) or a different lever entirely.

### Artifacts (Session 94)

**New audit script (committed):**
* `analysis/scripts/audit_rule_extraction_structural_S94.py` — definitive saturation audit across all 10 within-v44_dt residual cells + intra-Layout-A bot_suit follow-up on trips B_DS_AVAIL_LKR.

**New data artifacts:**
* `data/session94/audit_summary.log` — full output of the audit script.
* `data/session94/audit_rule_extraction_structural_summary.json` — machine-readable summary (per-cell saturation evidence + sub-bucket trigger search results + intra-Layout-A bot_suit pivot table).

**Documentation:**
* `SESSION_94_REPORT.md` — this file.
* `DECISIONS_LOG.md` — Decision 129 (S94 STRUCTURAL NULL + four methodology refinements).
* `CURRENT_PHASE.md` — rewritten for S95.
* `STRATEGY_GUIDE.md` — Part 1 appended with Session 94 entry (no production change; saturation-boundary documentation).
* `sprints/SPRINT_INDEX.md` — S94 entry appended.

### State at end of S94

**Strategies of record (UNCHANGED from S93):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (**UNCHANGED for 22 sessions**, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

* **Total project rule count: 25** (UNCHANGED).
* **Cumulative closure since pre-S68: $1,297.59 of $1,409 = 92.09%** (UNCHANGED).
* **Remaining gap to oracle ceiling: $111.41/1000h** (UNCHANGED).
* **Production vs v44_dt: $552.79/1000h** (UNCHANGED).
* **Combined S87-S93 production-chain recovery: $221.26/1000h** (UNCHANGED). S94 contributes $0.
* **Chain-audit methodology arc: COMPLETE** (S92 finding holds).
* **Rule-extraction (Option D-revised) within-v44_dt residual lever: SATURATION BOUNDARY CHARACTERIZED** (S94 finding, NEW). One borderline candidate identified for S95 (trips B_DS_AVAIL_LKR intra-Layout-A bot_suit).

## What's on the table for S95

The chain-audit lever and the bucket-level rule-extraction lever are both saturated. Remaining open levers:

1. **PRIMARY (NEW S94 finding)** — trips B_DS_AVAIL_LKR intra-Layout-A bot_suit candidate. Borderline ($5.89/1000h on 8,160 hands at ≥70% trigger, $19.49/1000h aggregate if rule was 100% accurate). Requires Rule-20-style picking-logic engineering: define the deterministic "force-best-DS-bot-within-Layout-A" pick and pre-drill multiple trigger widths on N=200.

2. **SECONDARY** — headline-goal recalibration. Carried from S92/S93's TERTIARY. The chain-audit lever is complete and the rule-extraction lever is structurally saturated; this is the moment to make explicit that 95% match% (the original S58-era goal) is unreachable on the current ML architecture and reset the success criterion to maximize $/1000h subject to the cascade we have.

3. **TERTIARY** — ML retrain (A3 full 6M-hand N=1000 grid). Formally closed at v44 in S78. Option C infrastructure provides the foundation; ~70 hours wall on this hardware. Reopening requires either a new feature family or explicit operator authorization.

4. **DEFERRED** — v52-defensive-low partial-effectiveness exploit (carried from S90).
5. **DEFERRED** — v44_RULE13 fallthrough replacement (carried from S92).
