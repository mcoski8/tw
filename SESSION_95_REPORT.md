# Session 95 — MIXED on trips B_DS_AVAIL_LKR intra-Layout-A force-best-DS-bot candidate (Rule 26 candidate). **Production v65 UNCHANGED.** Picker-criterion sweep reveals naive Rule-20 carry-over (`bot_pair_high` first) is fundamentally misaligned with oracle; the correct `top_rank` first criterion lifts NARROW from -$3.22 to +$4.59 N=200 / +$4.75 N=1000 — both grids within $0.16, both below the $5 SHIP bar. Two-grid verdict: MIXED on all 3 gates (NARROW the closest to SHIP). NEW S95 methodology lesson: picker-alignment is the second necessary condition for rule extraction (alongside S94's trigger-predictivity boundary).

_Generated 2026-05-16. S95 executed the S94-defined PRIMARY path: design strategy_v66 with a Rule-20-analog "force-best-DS-bot-within-Layout-A" picker, multi-gate pre-drill on N=200, and Option C N=1000 grading. Phase A re-confirmed the S94 finding from per-hand data (note: the resume prompt's n=210/n=370 lines had transcription typos — the S94 JSON shows the true numbers: NARROW=8,160 hands at meanP=90.4%/$5.89 wg; MEDIUM=15,072@77.7%/$10.07; WIDE=44,537@56.8%/$22.64). Phase B built strategy_v66 with the naive `bot_pair_high` carry-over picker — all three gates landed strongly negative at N=200 ($-3.22 / $-6.25 / $-8.84). Diagnostic showed exact-pick match with oracle was only 7.5-13.8%, despite the high direction-predictivity. A picker-criterion sweep across 8 alternative orderings found **TOP_HIGH_then_pair_tops** (highest kicker on top, then bot pair-tops desc) lifts the NARROW gate to $+4.59 at 85.2% swap-right rate — within 9% of the $5 SHIP bar but not over it. Per-sub-bucket and cumulative-slice analysis: no slice of (cell × sub-bucket × gate) under any tested criterion clears $5 SHIP at N=200. Phase C N=1000 sparse-grid grading completes the two-grid standard verdict. **Verdict: MIXED on PRIMARY direction. v65 remains production. v44_dt UNCHANGED for 23rd consecutive session.**

## TL;DR — Plain language

**What changed in your strategy of record:** **Nothing.** v65 remains production at $1,633.79/1000h. This was an exploration session that confirmed the S94 candidate cannot ship cleanly.

**What we tested:** Whether a new trips rule could exploit the S94 finding — when v44_dt picks trips Layout A with a non-DS bot, can a rule force the best DS-bot config and recover the $19.49/1000h aggregate leak that oracle's picks exploit?

**Why no ship.** The first picker criterion we tried (carrying over the Rule 20 / Rule 25 logic of "best DS by bot_pair_high") was catastrophically wrong — it only matched oracle's specific setting 7.5% of the time in the highest-predictivity gate. Trips have a different optimal: the rule needs to put the **highest kicker on top**, not protect the bot pair. The corrected picker lifts the lift from $-3.22 to $+4.59 in the NARROW gate — clear progress, but still under the $5 SHIP bar.

**The key new methodology finding.** S94 established that trigger-predictivity ≥ 62-70% is the necessary condition for rule extraction. S95 adds the second necessary condition: **picker alignment with oracle's specific pick within the predicted direction**. Direction predictivity of 90% is useless if the rule picks a different config in 90% of cases. For Rules 20 and 25, the `bot_pair_high`-first picker happened to align with oracle 89%+. For trips Layout A DS-bot, the same picker only aligns 3-8% in the highest-P sub-buckets; switching to `top_rank`-first gets to 85%+ in NARROW. Different cells need different criteria; the S94 "predictivity ≥ 62%" gate is necessary but not sufficient.

**What's on the table for S96:** With the rule-extraction lever now fully characterized (both bucket-level AND intra-layout sub-classes) as saturated on the current ML architecture, the open options are:

1. **Headline-goal recalibration** (PROMOTED from S95 SECONDARY → S96 PRIMARY). Make explicit that 95% match% is unreachable on the current ML architecture; reset success criterion to maximize $/1000h subject to the current cascade.
2. **A3 ML retrain** (full 6M × 105 × N=1000 grid). Formally closed at v44 in S78 but Option C infrastructure now makes it feasible; ~70 h wall.
3. **v52-defensive-low partial-effectiveness exploit** (DEFERRED).

**The numbers (UNCHANGED from S94):**

* Production v65: **$1,633.79/1000h full grid / $776.88 prefix**.
* v44_dt: $1,081 full / $686 prefix (**UNCHANGED for 23 consecutive sessions**, since v44 in S58).
* Production vs v44_dt: $552.79/1000h.
* Remaining gap to oracle ceiling: $111.41/1000h.
* Cumulative closure since pre-S68: $1,297.59 of $1,409 = **92.09%**.
* Rule count: 25 (UNCHANGED).
* Combined S87-S93 production-chain recovery: $221.26/1000h. S94 + S95 contribute $0.

## The full story

### Phase A — re-confirm S94 finding from per-hand parquet

The S94 audit's `audit_rule_extraction_structural_summary.json` contains the authoritative numbers. The resume prompt and SESSION_94_REPORT.md had transcription typos for the sub-bucket sizes (e.g., n=210 instead of 1,618 for (2,4,1)). Re-deriving from `drill_trips_v44_per_hand_structural.parquet`:

Cell B_DS_AVAIL_LKR (cell_idx=1): 163,170 hands, $42.61/1000h.
* Layout-A agree (v44 = oracle = Layout A): 105,031 hands, $25.84/1000h.
* v44 non-DS bot population: 57,033 hands, $23.93/1000h.
* v44 non-DS bot AND oracle DS bot: 25,905 hands, $19.49/1000h.

Sub-bucket pivot on (kickers_max_suit_count, n_kickers_in_trip_suits, n_b_ds_routings):

| ksc | nkts | nbds |       n |  or_ds |   P(oracle DS)  |    wg ($/1000h) |
|----:|-----:|-----:|--------:|-------:|----------------:|----------------:|
|   2 |    4 |    1 |   1,618 |  1,618 |          100.0% |          $ 1.12 |
|   3 |    4 |    1 |   6,542 |  5,757 |           88.0% |          $ 4.77 |
|   2 |    4 |    3 |   6,912 |  4,337 |           62.7% |          $ 4.18 |
|   2 |    3 |    1 |  29,465 | 13,588 |           46.1% |          $12.58 |
|   2 |    2 |    1 |   5,791 |    605 |           10.4% |          $ 0.55 |
|   1 |    3 |    3 |   6,705 |      0 |            0.0% |          $ 0.74 |

Phase A locked the three pre-committed trigger gates:

| Gate | Triggers | n hands | mean P(oracle DS) | wg ceiling at 100% trigger |
|---|---|---:|---:|---:|
| NARROW | (2,4,1) + (3,4,1) | 8,160 | 90.4% | $5.89 |
| MEDIUM | + (2,4,3) | 15,072 | 77.7% | $10.07 |
| WIDE | + (2,3,1) | 44,537 | 56.8% | $22.64 |

### Phase B — design strategy_v66 and pre-drill on N=200

Built `analysis/scripts/strategy_v66_trips_layout_a_force_ds_bot.py`. Rule 26 fires when:
1. Hand is trips (one trip-rank, no pairs).
2. Cell is B_DS_AVAIL_LKR (b_ds_avail AND best_b_ds_kicker_2nd_rank < 10).
3. Sub-bucket (ksc, nkts, nbds) is in the active gate.
4. v44_dt picks Layout A with non-DS bot (v65 ≡ v44_dt on trips by construction since v56_trips_hybrid blanket-routes trips → v44_dt).

If triggered, enumerate all (mid_pair_of_trips × top_kicker) settings yielding DS bot and pick the best by a deterministic criterion. Initial implementation used the Rule 20 / Rule 25 carry-over criterion: **bot_pair_high desc, then bot_pair_2nd desc, then top_rank desc**.

**N=200 pre-drill (initial picker):** **All three gates strongly negative.**

| Gate | n_changed | swap-right rate | N=200 lift |
|---|---:|---:|---:|
| NARROW | 8,751 | 36.6% | **−$3.22** |
| MEDIUM | 18,734 | 39.3% | **−$6.25** |
| WIDE | 51,531 | 47.6% | **−$8.84** |

### The picker diagnostic

Phase A's predictivity numbers (90%+ in NARROW) said the rule's direction (force DS) should be right >90% of the time, so why was the swap-right rate 36-48%?

Direct check (`diagnose_v66_picker_S95.py`): among NARROW-gate fired hands where oracle picks DS (= 88.7% of fired), the rule's **specific setting matches oracle exactly only 7.5% of the time**. In MEDIUM that match rate is 13.8%; in WIDE it's 51.6%. Per-sub-bucket: (2,3,1) at 89.1% exact-match (single mostly-forced config), but (2,4,1) at 3.5% and (3,4,1) at 8.7%. The sub-buckets with multiple available DS configs get the picker wrong almost universally.

**Mean EV(v66 - oracle) on NARROW fired+oracle-DS: −656 ev units.** The rule's "best DS" pick is on average 656 ev-units WORSE than oracle's "best DS" pick. The picker criterion was wrong.

### Picker-criterion sweep

`picker_sweep_v66_S95.py` evaluates 8 deterministic Layout-A DS-bot picker criteria across the 3 gates. Result:

| Criterion | NARROW | MEDIUM | WIDE |
|---|---:|---:|---:|
| BOT_PAIR_HI then 2nd then TOP_DESC (initial) | $−3.22 (36.6%) | $−6.25 (39.3%) | $−8.84 (47.6%) |
| BOT_PAIR_HI then 2nd then TOP_ASC | $−4.56 (31.9%) | $−6.71 (39.4%) | $−9.30 (47.6%) |
| **TOP_HIGH then pair_tops** | **$+4.59 (85.2%)** | **$+2.95 (65.9%)** | **$+0.36 (57.2%)** |
| TOP_LOW then pair_tops | $−4.41 (32.6%) | $−6.55 (39.7%) | $−9.14 (47.7%) |
| BOT_SUM_HI then TOP_DESC | $−4.41 | $−6.55 | $−9.14 |
| BOT_MIN_HI then PAIR_TOP_DESC | $−4.41 | $−6.57 | $−9.16 |
| PAIR_TOP_2_HI then PAIR_TOP_1_HI | $−3.22 | $−6.25 | $−8.84 |
| TOP_NOT_IN_TRIP_SUIT then pair_tops | $−4.56 | $−7.59 | $−10.18 |

**TOP_HIGH wins decisively** — and its tertiary tiebreakers (varied for `pair_tops_then_botmin_lo/hi`, `pair_top_2_lo/hi`, etc.) are all redundant in practice: top_rank uniquely picks within each hand's available DS configs.

### Why TOP_HIGH wins for trips (and why Rule 20's logic carried over wrong)

Rules 20 / 25 are pair rules. The hand has a pair, the top tier holds 1 leftover singleton, and the pair anchors the bot. The deterministic pick puts the highest non-pair kicker into bot (to anchor the secondary pair) and leaves a smaller kicker on top — because pair strength in bot dominates top's single-card value.

For trips Layout A: the bot has 1 trip card + 3 kickers. The bot's strength is primarily the trip card itself (Omaha 2+3 + board) — adding a high kicker to bot only marginally helps. The top is a single kicker played as Hold'em 1+5; oracle treats top points as valuable for trips and prefers the **highest** kicker on top to win that tier outright. The "best DS by bot_pair_high" criterion that worked for pairs catastrophically misaligns here.

### Per-sub-bucket and cumulative-slice exploration under TOP_HIGH

`picker_sweep_subbucket_v66_S95.py` checks whether any single sub-bucket or sub-bucket combination clears $5:

| Slice | n_changed | swap-right | N=200 lift | Status |
|---|---:|---:|---:|---|
| (3,4,1) only | 7,056 | 82.0% | $+3.50 | mid |
| (2,4,1) only | 1,695 | 98.7% | $+1.08 | mid |
| (2,4,1) + (3,4,1) **NARROW** | 8,751 | 85.2% | $+4.59 | **mid (best)** |
| (2,4,3) only | 9,983 | 48.9% | $−1.64 | null |
| NARROW + (2,4,3) **MEDIUM** | 18,734 | 65.9% | $+2.95 | mid |
| (2,3,1) only | 32,797 | 52.3% | $−2.59 | null |
| (2,2,1) only | 6,022 | 10.0% | $−4.96 | null |

**No slice clears the $5 SHIP bar at N=200.** The best is NARROW at $+4.59 / 85.2% sr — below SHIP by $0.41, well above the $1 NULL threshold. Per pre-committed two-grid thresholds (SHIP both grids ≥ $5; NULL both ≤ $1; otherwise MIXED), this candidate is **locked at MIXED-at-best regardless of N=1000**.

### Phase C — Option C sparse N=1000 grading

Engine ran on the 51,531-id WIDE list (~31.7 min wall at 27.1 hands/s, base_seed=0xc0ffee, opp=RealisticHumanMixture, N=1000 samples). Sparse grid covers 100% of changed canonical_ids across all three gates.

**Two-grid grader result** (pre-committed thresholds: SHIP both ≥ $5; NULL both ≤ $1; MIXED otherwise):

| Gate | n_changed | N=200 lift | N=1000 lift | \|Δ\| | sign-agree | Verdict |
|---|---:|---:|---:|---:|---:|---|
| NARROW | 8,751 | **$+4.59** | **$+4.75** | $0.16 | 93.9% | **MIXED** |
| MEDIUM | 18,734 | $+2.95 | $+3.37 | $0.42 | 88.3% | MIXED |
| WIDE | 51,531 | $+0.36 | $+2.09 | $1.73 | 87.0% | MIXED |

The N=200 ↔ N=1000 estimates are extremely tight on NARROW (within $0.16) — confirming MC noise is small at the candidate's effect size. The NARROW verdict at $+4.75 N=1000 / $+4.59 N=200 (mean $+4.67) is **borderline below the $5 SHIP bar by ~$0.25 on each grid** but well above the $1 NULL bar — the project's two-grid standard cleanly locks it at MIXED.

WIDE has the largest N=200/N=1000 spread ($0.36 → $2.09 = $1.73) but both grids remain in the MIXED zone (above $1, below $5). MEDIUM is uniformly MIXED at $+3.16 average.

**No gate clears the SHIP bar on either grid.** Per the pre-committed thresholds, the candidate cannot ship.

### Verdict + production state

**VERDICT: MIXED.** Production v65 UNCHANGED.

| metric | pre-S95 (v65) | post-S95 (v65) | Δ |
|---|---:|---:|---:|
| Full grid (N=200) | $1,633.79 | $1,633.79 | $0.00 |
| Prefix grid (N=1000) | $776.88 | $776.88 | $0.00 |
| Production vs v44_dt | $552.79 | $552.79 | $0.00 |
| Remaining gap to oracle | $111.41 | $111.41 | $0.00 |
| Cumulative closure since pre-S68 | 92.09% | 92.09% | 0.00pp |
| Rule count | 25 | 25 | 0 |

* v44_dt ML champion: UNCHANGED ($1,081 full / $686 prefix) — **23 consecutive sessions** running.
* Combined S87-S93 production-chain recovery: $221.26/1000h. **S95 contributes $0.**

### Methodology lessons (S95)

1. **PICKER ALIGNMENT IS THE SECOND NECESSARY CONDITION (NEW S95).** S94 established trigger predictivity ≥ 62-70% as the operational definition of "rule extractable". S95 adds: even when direction predictivity is high (90%+), the rule's deterministic picker must align with oracle's specific pick. Rules 20 and 25 had 89%+ picker alignment by happy accident (their `bot_pair_high` criterion = oracle's). The trips analog under that same criterion got 3-8% alignment in the highest-P sub-buckets. **Predictivity is necessary; picker alignment within the predicted direction is also necessary.** Both conditions hold by accident in the pair rules; both must be empirically verified for new cells.

2. **PICKER CRITERIA ARE CELL-SPECIFIC, NOT TRANSFERABLE (NEW S95).** Rule 20 / 25 use `bot_pair_high` because the bot's pair value dominates top's single-card value for hands with a pair. Trips invert this — bot's strength is mostly the trip card, top wants the highest kicker. **Never assume a successful rule's picker criterion will carry over to a new cell;** validate empirically (8-criterion sweep takes ~3 min on this cell with the picker_sweep script template).

3. **RESUME PROMPT TRANSCRIPTION TYPO (operational lesson).** The S94 resume prompt and SESSION_94_REPORT.md listed the NARROW sub-buckets as n=210 + n=370 (a transcription typo from an earlier draft); the S94 audit JSON shows the true numbers n=1,618 + n=6,542 totaling 8,160 at 90.4% mean predictivity. Always cross-check resume-prompt numbers against the JSON of record at session start; if numbers look anomalously small, run the JSON.

4. **OPTION D-REVISED RULE-EXTRACTION LEVER IS NOW EXHAUSTED ACROSS BOTH SUB-CLASSES (carried + extended).** S94 closed bucket-level layout-flip rules. S95 closes intra-layout structural-feature rules on the largest remaining cell (trips B_DS_AVAIL_LKR). With both sub-classes exhausted on the current ML architecture, the headline-goal recalibration option promotes from SECONDARY to S96 PRIMARY: this is the moment to make explicit that 95% match% is unreachable on current architecture and reset the success criterion to maximize $/1000h subject to the current cascade.

### Artifacts (Session 95)

**New strategy file:**
* `analysis/scripts/strategy_v66_trips_layout_a_force_ds_bot.py` — Rule 26 candidate with the corrected `top_rank`-first picker criterion (TOP_HIGH then pair_tops desc).

**New analysis scripts:**
* `analysis/scripts/phaseA_trips_b_ds_avail_lkr_intra_layout_a_S95.py` — re-confirm S94 sub-bucket numbers, lock trigger gates.
* `analysis/scripts/sanity_v66_on_parquet_S95.py` — verify rule fires + produces Layout-A DS-bot on 50 parquet samples per gate.
* `analysis/scripts/prepare_v66_id_list_S95.py` — N=200 baseline + per-hand picks + WIDE id list for engine sparse mode.
* `analysis/scripts/diagnose_v66_picker_S95.py` — exact-match diagnostic that surfaced the picker-mismatch finding.
* `analysis/scripts/picker_sweep_v66_S95.py` — 8-criterion picker sweep across 3 gates.
* `analysis/scripts/picker_sweep_subbucket_v66_S95.py` — per-sub-bucket + cumulative-slice analysis under TOP_HIGH variants.
* `analysis/scripts/grade_v66_id_list_n1000_S95.py` — two-grid grader at pre-committed thresholds.

**New data artifacts:**
* `data/session95/phaseA_summary.{json,log}` — Phase A re-confirmation.
* `data/session95/phaseA_cids_gate_{NARROW,MEDIUM,WIDE}.txt` — canonical_id lists per trigger gate.
* `data/session95/phaseB_prepare.{log,summary.json}` — Phase B prepare run output.
* `data/session95/diagnose_v66_picker.log` — picker-misalignment diagnostic.
* `data/session95/picker_sweep.log` — 8-criterion sweep results.
* `data/session95/picker_sweep_subbucket.log` — per-sub-bucket TOP_HIGH analysis.
* `data/session95/v66_per_hand_picks.npz` — per-hand v65/v66-NARROW/v66-MEDIUM/v66-WIDE picks.
* `data/session95/v66_id_list_wide.txt` — 51,531 canonical_ids (WIDE superset).
* `data/session95/v66_n1000_sparse.bin` — Option C N=1000 sparse oracle grid on 51,531 hands.
* `data/session95/engine_n1000_sparse.log` — engine run log.
* `data/session95/grade_v66_n1000_summary.json` — two-grid grader output.

**Documentation:**
* `SESSION_95_REPORT.md` — this file.
* `DECISIONS_LOG.md` — Decision 130 (S95 MIXED + new picker-alignment methodology lesson).
* `CURRENT_PHASE.md` — rewritten for S96.
* `STRATEGY_GUIDE.md` — Part 1 appended with Session 95 entry.
* `sprints/SPRINT_INDEX.md` — S95 entry appended.

### State at end of S95

**Strategies of record (UNCHANGED from S94):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (**UNCHANGED for 23 sessions**, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

* **Total project rule count: 25** (UNCHANGED).
* **Cumulative closure since pre-S68: $1,297.59 of $1,409 = 92.09%** (UNCHANGED).
* **Remaining gap to oracle ceiling: $111.41/1000h** (UNCHANGED).
* **Production vs v44_dt: $552.79/1000h** (UNCHANGED).
* **Combined S87-S93 production-chain recovery: $221.26/1000h** (UNCHANGED). S94 + S95 contribute $0.
* **Chain-audit methodology arc: COMPLETE** (S92 closure holds).
* **Rule-extraction (Option D-revised) lever — bucket-level sub-class: SATURATED** (S94 closure).
* **Rule-extraction (Option D-revised) lever — intra-layout sub-class: SATURATED** (S95 finding on the strongest candidate; the candidate that S94 identified as borderline lands MIXED with picker engineering).

## What's on the table for S96

With chain-audit + both rule-extraction sub-classes characterized as saturated:

1. **PRIMARY (PROMOTED from S94/S95 SECONDARY) — headline-goal recalibration.** Make explicit that 95% match% is unreachable on the current ML architecture. Reset success criterion to maximize $/1000h subject to current cascade. Doc-only session.

2. **SECONDARY — A3 ML retrain (full 6M × 105 × N=1000 grid).** Formally closed at v44 in S78 but Option C N=1000 infrastructure provides the foundation. ~70 hours wall on current hardware. Reopening requires either a new feature family or explicit operator authorization. The structural saturation findings from S91-S95 raise the question of whether a richer ML champion would shift the saturation boundary.

3. **TERTIARY — v52-defensive-low partial-effectiveness exploit (DEFERRED from S90).** Still speculative.

4. **DEFERRED — v44_RULE13 fallthrough replacement.** With v54/v55/v56 absorbing $731+ of chain bleed across pair-family, replacement primarily matters for HIGH_ONLY (already gated by v64/v65).
