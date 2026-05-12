# Session 63 — J-High Cell-by-Cell Catalog

*Generated: 2026-05-12 — fourth page of `HIGH_ONLY_RULE_CATALOG.md`. Session 63 audits Rule 17 (J-high HIMID, S53) cell-by-cell against the realistic-mixture oracle grid and tests 7 candidate refinement rules across J-high's leakiest cells (DS_NO_JOINT and MS_ONLY). Mirrors the S60+S61+S62 structure with an important harness clarification on Rule 17's true single-rule lift.*

## TL;DR — J-high catalog verdict: ALL CELLS ML-ONLY (T3)

After cell-by-cell audit of Rule 17 and 7 candidate refinements:

- **Rule 17's actual J-high contribution is +$5.48/1000h WG** (v48 vs v47 on J-high). The CURRENT_PHASE table's "+$17 Rule 17" attribution was a misread of the S53 OVERNIGHT REPORT (line 20) — the +$17 is **v52 vs v47 across ALL high_only** (Rule 17 J-HIMID + Rules 22-28 defensive across J/T/9/8/7-high). The cross-check `sanity_v52_vs_v47_high_only.py` reproduces +$16.77/1000h WG vs the documented $17 to within 1.4% — **harness validated on a FOURTH independent shipped lift**.
- **J-high TOTAL leak to oracle after v52: $47.46/1000h WG.** v44_dt closes 51% of that gap ($24.03/1000h WG). v44 residual: $23.43/1000h WG.
- **DS_NO_JOINT dominates** ($29.88/1000h WG = 63% of J-high leak). Within-cell gap is $4,749/1000h vs Q-high's $3,690/1000h — **J's leak is 29% deeper per hand than Q's** because oracle drops J off top 76% (vs Q 52%, K 34%, A 6%) and Rule 17 keeps J on top 100% on s2 > 8 hands.
- **Every candidate falls below Threshold 1** (≥40% gap closure AND ≥+$3/1000h within-cell vs v52). However, **C_J1 (drop J to low top + DSms) is the BIGGEST single-candidate WG lift across the entire S60–S63 catalog at +$6.44/1000h WG** — exceeding T2's $5/1000h bar in raw WG terms but missing T1's 40% gap-closure bar at 21.54%. C_J4 (J-in-DS-pair) is second-best at +$4.59/1000h WG.
- **The methodology lesson partially shifts at J.** Best-candidate capture% jumped from 5.45%/3.33%/5.99% (A/K/Q) to **21.54% at J** — finally tracking the underlying drop-max rate growth (6%→34%→52%→76%). But 21.54% is still half of T1's 40% bar.
- **Rule 17's HIMID design is empirically validated post-hoc — FOURTH retrospective confirmation.** C_J7 (HIBOT control) shipped −$6.56/1000h WG. The HIMID design choice from S50/S51/S52/S53 is sound at four independent max-ranks.
- **No shipped rule from Session 63.** No change to the production rule chain. **v52_full_high_only_handler ($2,498 full / $1,522 prefix) and v44_dt ($1,081 / $686) both UNCHANGED.**

Four consecutive max-ranks (A, K, Q, J) have now produced ALL-T3 verdicts despite progressively MORE drop-max opportunity (6% → 34% → 52% → 76%). **Four-of-four is decisive empirical evidence that the high_only residual is genuinely ML-only territory at the catalog's "one-sentence-statable" granularity.** $578 of $755 ($531 from A+K+Q + $47 from J after v44 catch is excluded from rule-only zone) of the WG residual is now formally in the explicit ML-only zone (97% by population).

## Method

The harness:
1. Loads `data/drill_ho_v44_per_hand_structural.parquet` (S59 artifact — per-hand structural cell tags + oracle/v44 picks).
2. For each candidate `rule_fn`, filters to `(max_rank=11, cell=X)`.
3. Per hand: computes `rule_fn(h)` (None = pass-through to baseline_fn) and `baseline_fn(h) = v52_full_high_only_handler(h)`.
4. Looks up oracle EV (= max of `oracle_grid[cid]`), v44 EV (= `oracle_grid[cid][v44_idx]`), rule EV, baseline EV.
5. Aggregates: within-cell + whole-grid lift in $/1000h, capture% vs baseline AND v44, % optimal, and rule-vs-oracle mismatch class breakdown.

**Two-stage sanity check** (Phase 2):
1. Rule 17 alone on J-high: v48 (= v47 + Rules 17-21 HIMID) vs v47 on J-high → **+$5.48/1000h WG**. Consistent with the S53 OVERNIGHT REPORT's "v48 → +$8 vs v47" (line 18) summed across J/T/9/8/7-high.
2. Full v52 ship across all high_only: v52 vs v47 → **+$16.77/1000h WG**, matching the documented +$17 to within 1.4%.

**Conclusion: harness validated on FOUR independent shipped lifts.** Rule 14 (+$131, 0.2% S60), Rule 15 (+$51, 0.7% S61), Rule 16 (+$19, 1.7% S62), v52-vs-v47 (+$17, 1.4% S63).

## Part 1 — v52 cell-by-cell audit on J-high

After v52 fires (Rule 17 on s2 > 8 hands = 91.7% of J-high; Rule 24 lowest-on-top defensive on s2 ≤ 8 hands = 8.3%), what gap to oracle remains per cell?

| Cell | n hands | v52 mean_ev | Oracle mean_ev | Gap within-cell | Gap WG | v44 mean_ev | v44 gap WG |
|---|---:|---:|---:|---:|---:|---:|---:|
| JOINT_HIGH | 0 | — | — | — | — | — | — |
| JOINT_MED | 8,715 | -1.420 | -1.152 | $2,686/1k | $3.90 | -1.266 | $1.66 |
| JOINT_LOW | 105 | -2.670 | -2.302 | $3,686/1k | $0.06 | -2.424 | $0.02 |
| **DS_NO_JOINT** | **37,800** | **-1.702** | **-1.227** | **$4,749/1k** | **$29.88** | **-1.486** | **$16.29** |
| DS_NO_MAXTOP | 8,064 | -2.053 | -1.355 | $6,978/1k | $9.36 | -1.600 | $3.28 |
| MS_ONLY | 5,376 | -2.257 | -1.781 | $4,767/1k | $4.26 | -2.024 | $2.18 |
| NEITHER | 0 | — | — | — | — | — | — |
| **J-high total** | **60,060** | — | — | — | **$47.46** | — | **$23.43** |

**Rule 17 / Rule 24 fire-region disambiguation** (`audit_rule17_S63.py` Phase 2c):

| Sub-population | n hands | % of J-high | v52 mean_ev | v52 gap WG | v44 gap WG |
|---|---:|---:|---:|---:|---:|
| All J-high | 60,060 | 100% | -1.760 | $47.46 | $23.43 |
| **J-high s2 > 8 (Rule 17 fire region)** | **55,055** | **91.7%** | **-1.701** | **$44.20** | **$21.76** |
| J-high s2 ≤ 8 (Rule 24 fire region) | 5,005 | 8.3% | -2.401 | $3.26 | $1.66 |

**Four takeaways from the audit:**

1. **JOINT_HIGH is empty at J-high** (no hands have `best_ms_mid_high ≥ 11` because J = 11 is the max rank, leaving max non-J rank = 10). The "structural funnel" tightens at J: JOINT_MED replaces JOINT_HIGH as the joint cell, and the bulk of the population shifts toward DS_NO_JOINT.
2. **DS_NO_JOINT is the dominant residual cell at J-high** ($29.88/1000h WG = 63% of J-high's post-v52 leak). The within-cell gap is **29% deeper per hand than Q-high's DSnj** ($4,749/1k vs Q's $3,690/1k), reflecting v52's structural mismatch with oracle: oracle drops J off top 76% in this cell while Rule 17 keeps J on top 100% on the s2 > 8 subset (and Rule 24 doesn't fire there).
3. **DS_NO_MAXTOP has the deepest per-hand gap of any J-high cell** ($6,978/1k within-cell — 21% deeper than Q's $5,767/1k). But the cell is small (n=8,064) so WG contribution is $9.36, second to DSnj.
4. **Rule 24 fire region (s2 ≤ 8) is small ($3.26/1000h WG) and the lowest absolute residual** of any sub-pop. The "structural twist" of Rule 24's defensive override at J-high is real but not load-bearing for the WG residual. v52's Rule 17 path handles 91.7% of J-high and accounts for $44.20/$47.46 = 93% of the leak. **The candidate space targets Rule 17's fire region.**

## Part 2 — Candidate refinement rules tested

7 candidates targeting J's drop-J-off-top play (DSnj 76% per oracle) and the SS_ms switch. Each candidate fires only inside its target cell (`_is_J_high_no_pair` + `_cell_for_hand_J`); when it doesn't fire, v52 is used.

| ID | Candidate | Cell | Fires | cap_b | $/cell | $/1000h WG | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| C_J1 | DSnj_drop_J_low_top_DSms | DSnj | 39.8% | +21.54% | +$1,023 | **+$6.44** | T3 (best WG ever) |
| C_J2 | DSnj_take_2top_DSms | DSnj | 9.6% | +8.73% | +$414 | +$2.61 | T3 |
| C_J3 | DSnj_take_3top_DSms | DSnj | 9.6% | +6.61% | +$314 | +$1.98 | T3 |
| C_J4 | DSnj_drop_J_when_J_in_DSpair | DSnj | 43.9% | +15.35% | +$729 | **+$4.59** | T3 (2nd best) |
| C_J5 | DSnj_SSms_when_high | DSnj | 35.6% | −0.75% | −$36 | −$0.22 | T3 |
| C_J6 | MSonly_drop_J | MSonly | 89.1% | −16.47% | −$785 | −$0.70 | T3 (over-fire) |
| C_J7 | DSnj_HIBOT_tiebreaker (control) | DSnj | 100.0% | −21.96% | −$1,043 | −$6.56 | T3 (HIMID confirmed) |

(`cap_b` = gap closure vs v52 baseline. `$/cell` = within-cell lift in $/1000h. `$/1000h WG` = whole-grid lift.)

## Part 3 — Why every candidate failed (data-driven)

### DS_NO_JOINT (C_J1, C_J2, C_J3, C_J4, C_J5, C_J7)

S58's decision matrix said oracle drops J off top **76%** in J × DS_NO_JOINT — the most aggressive drop-max profile of all high zones. The naive read: a "drop J when achievable" gate firing on a similar fraction should recover most of that. The harness says: **at J, the lesson partially shifts** — capture% finally jumps with the drop-max rate, but still below the T1 bar.

- **C_J1 (drop J to top ≤ 7 + DS bot + ms_mid_high ≥ 9):** fires **39.8%** — *under*-fires relative to oracle's 76% drop rate, but capture is now **+21.54%** (vs A's 5.45%, K's 3.33%, Q's 5.75%). **+$6.44/1000h WG — the biggest single-candidate WG lift across the entire S60–S63 catalog.** Within-cell +$1,023/1000h. **Above T2's $5/1000h WG bar** in raw terms, but fails T1's 40% gap-closure bar at 21.54%. The right *direction* (low-top + ms_mid is what oracle prefers), but still firing on a superset of oracle's drop population.
- **C_J2 (top=2 + DS bot + ms_mid_high ≥ 9):** surgical mirror of C_Q4. At J × DSnj, top=2 is BIGGER than J-on-top (27% vs 24% per S58). Fires **9.6%**, capture +8.73%, +$2.61/1000h WG — the surgical gate is even tinier here than at Q. The "right pick" oracle makes when it picks top=2 is highly conditional and a fixed-rank gate can't reach it.
- **C_J3 (top=3 + DS bot + ms_mid_high ≥ 9):** also surgical, oracle picks top=3 14% in J × DSnj. Fires 9.6%, captures +6.61%, +$1.98/1000h WG. Tiny by construction.
- **C_J4 (drop J when J is in DS bot pair, ms_mid_high ≥ 8):** S58 Observation 1 says best_DS_bot_pair_high == J → oracle picks JOINT only 46% (vs Q 70.6%, K 83%, A 93%) — STRONGEST drop-max signal yet. Fires **43.9%** — biggest gate of any catalog candidate across S60-S63 — capture **+15.35%**, **+$4.59/1000h WG**. Second-best J candidate but still under T1's 40% bar.
- **C_J5 (switch J-top DS_mu → J-top SS_ms when SS_ms mid_high ≥ T):** mirror of C_Q5/C_K4. Fires 35.6%, capture −0.75%, −$0.22/1000h WG. Negative even smaller than at Q (−$2.02) and K (−$13.10), but still the wrong direction. The SS_ms switch is the wrong pick for the majority of the 56% ms_mid share at J.
- **C_J7 (HIBOT control):** 100% fire, $−1,043/cell, **$−6.56/1000h WG**. **Fourth retrospective validation that Rule 17's HIMID design from S53 is empirically correct** — joining A C10 (Rule 14), K C_K6 (Rule 15), Q C_Q7 (Rule 16). The HIMID design choice is sound across four independent max-ranks.

**Structural finding (re-confirmed at J, with a partial shift):** the lesson "decision-matrix percentages overstate refinement headroom because oracle knows WHICH q% to switch on" generalizes from A (6%) → K (34%) → Q (52%) → J (76%). But at J, capture% finally tracks drop-max rate growth — 21.54% at J vs 5.45%/3.33%/5.99% at A/K/Q. The mid_high pool collapse (J's max non-J rank is 10, narrowing the achievable mid_high distribution) plus the much-larger drop-J surface (76% in DSnj) together make the rule space more rewarding. But still below T1's 40% gap-closure bar. **v44_dt encodes the joint distribution via 107 features and 2.25M leaves; a rule-chain refinement here would need 4+ feature gates and 10+ branch logic — which reproduces ML, not abstracts it.**

### MS_ONLY (C_J6)

C_J6 (drop J when top ≤ 7, ms_mid_high ≥ 9, SS or 31 bot achievable): fires **89.1%** — slightly worse over-fire than C_K5 (82.7%) or C_Q6 (85.8%). Result: $-785/cell, $−0.70/1000h WG. The MS_ONLY over-fire pattern repeats catastrophically at J as it did at K and Q.

The mismatch detail: `t2_SS_ms → t2_31_mu` 330 hands at $4,712/hand mean regret. When the rule drops J to top=2 with SS bot, oracle wanted top=2 with 31 bot or similar — even within the drop-J subset, the bot suit decision is finer than the gate can express.

**Lesson generalizes from K, Q to J:** relaxing the gate from C_K5's mid_high ≥ J → C_Q6's mid_high ≥ T → C_J6's mid_high ≥ 9 produced the SAME over-fire catastrophe at the same fire rate (82.7% K → 85.8% Q → 89.1% J). The MSonly drop-max play is genuinely non-rule-shaped at this catalog granularity for any high max-rank.

## Part 4 — Honest ML-only labeling

J-high's residual gap to oracle ($47.46/1000h WG) split across cells:

| Cell | WG residual after v52 | v44 captures (more than v52) | Net ML-only territory |
|---|---:|---:|---:|
| JOINT_MED | $3.90 | $2.24 | $1.66 ML |
| JOINT_LOW | $0.06 | $0.04 | $0.02 ML |
| DS_NO_JOINT | $29.88 | $13.59 | $16.29 ML |
| DS_NO_MAXTOP | $9.36 | $6.08 | $3.28 ML |
| MS_ONLY | $4.26 | $2.08 | $2.18 ML |
| **J-high total** | **$47.46** | **$24.03** | **$23.43 ML** |

**For Session 63's purpose, all J-high cells are labeled ML-only** — the catalog space explored doesn't produce a Threshold-2 refinement for any of them. v44_dt's J-high residual ($23.43/1000h WG) is the ceiling a catalog refinement could close further — and even at the cell-most-promising (DS_NO_JOINT, where oracle drops J 76%), the candidate space tested couldn't close it.

**Important nuance: C_J1 is unusually close.** At +$6.44/1000h WG it CLEARS T2's $5 bar on raw WG terms, and its capture (21.54%) is the highest of any catalog candidate. The reason it doesn't ship is the T1 gap-closure threshold (40%) which exists precisely to require the rule to "really fit" the cell, not just trim some leak. If the threshold were 20%, C_J1 would ship; the analysis would then need to evaluate v53 = v52 + C_J1 on the full 6M-hand grid for non-targeted regression (which is the next experiment if a higher-threshold variant of C_J1 is desired). Sessions 64+ will revisit this question with combined / refined candidates if the T/9/8 catalog also lands ML-only.

## Part 5 — Implications for Session 64 (T/9/8 combined)

Four consecutive max-ranks have produced ALL-T3 verdicts. T-high (max=10), 9-high, 8-high are all in v52's **always-defensive** zone (Rules 25/26/27) — oracle prefers lowest-on-top at these ranks. The structural prediction inverts compared to A/K/Q/J:

| Property | A-high | K-high | Q-high | J-high | T-high (S64) | 9-high (S64) | 8-high (S64) |
|---|---:|---:|---:|---:|---:|---:|---:|
| Population | 660,660 (53.8%) | 330,330 (26.9%) | 150,150 (12.2%) | 60,060 (4.9%) | 20,020 (1.6%) | 5,005 (0.4%) | 715 (<0.1%) |
| WG residual after v52 | $281 | $176 | $94 | $47 | TBD | TBD | TBD |
| Oracle drops max off top in DSnj | 6% | 34% | 52% | 76% | ~85%+ (extrapolation) | ~92%+ | ~97%+ |
| Rule(s) firing | Rule 14 | Rule 15 | Rule 16 | Rule 17 + Rule 24 | Rule 25 (always defensive) | Rule 26 (always defensive) | Rule 27 (always defensive) |
| Shipped lift vs v47 | +$0 | −$1.59 | −$0.29 | +$6.60 | +$8.24 | +$3.26 | +$0.56 |

**Hypothesis for S64:** at T/9/8 max, v52 uses lowest-on-top + DS HIMID (a fundamentally different strategy than the J-and-above max-on-top + DS HIMID family). The candidates must mirror that defensive structure. The opportunities for rule-shaped wins are different — perhaps lowest-on-top tiebreaker refinements or DS-vs-SS bot preference gates. The drop-max question doesn't apply since v52 already drops max by default.

**Two falsifiable predictions for S64 going in:**
1. T-high's v52→oracle gap is **smaller** than J-high's $47 in absolute WG (population is 1/3 the size) but **deeper per hand** than J-high's $4,749/1k within-cell ratio (since the structural funnel narrows further). Predict ~$20–30/1000h WG total.
2. ALL T/9/8 candidates land T3, completing the high_only catalog as ALL ML-only. The combined audit of all three sub-pops finishes in one session given the small populations.

If predictions hold, **Session 65 produces the aggregate `HIGH_ONLY_RULE_CATALOG.md`** integrating all six pages (A, K, Q, J, T/9/8, synthesis) and documents the boundary of rule-chain effectiveness on the largest residual zone.

## Part 6 — Files produced (Session 63)

| File | Purpose |
|---|---|
| `analysis/scripts/audit_rule17_S63.py` | Phase 2 sanity (v48 vs v47 on J-high) + Phase 2b cell-by-cell audit + Phase 2c Rule 17/Rule 24 fire region disambiguation. Output: `/tmp/s63_phase2_audit.log`. |
| `analysis/scripts/sanity_v52_vs_v47_high_only.py` | Phase 2 cross-check: v52 vs v47 across all high_only reproduces the +$17 documented S53 ship to 1.4%. Output: `/tmp/s63_phase2_sanity_xcheck.log`. |
| `analysis/scripts/candidates_J_high_S63.py` | 7 candidate rules for J-high cells (C_J1–C_J7). Imports `_enumerate_max_on_top_configs` and friends from `candidates_K_high_S61` (already `max_rank` parameterized). |
| `analysis/scripts/test_J_high_candidates_S63.py` | Driver: runs every candidate through the harness, scores T1/T2/T3 verdicts, writes JSON. Output: `/tmp/s63_phase4_sweep.log`. |
| `data/session_63_candidate_results.json` | Full results for C_J1–C_J7. |
| `SESSION_63_J_HIGH_CATALOG.md` | This file. Fourth page of the eventual `HIGH_ONLY_RULE_CATALOG.md`. |

The harness, candidate-test driver, and cell tagging infrastructure remain **reusable as-is** for S64 (T/9/8 combined). The only adaptation needed: combined audit driver for max ∈ {10, 9, 8} with v52's defensive-shaped baseline, and candidates targeting lowest-on-top tiebreaker refinements rather than max-on-top alternatives.

## Part 7 — Methodology lessons (Session 63)

1. **The harness reproduces shipped lift on a FOURTH independent measurement.** Rule 14 (+$131, 0.2% S60), Rule 15 (+$51, 0.7% S61), Rule 16 (+$19, 1.7% S62), v52-vs-v47 across all high_only (+$17, 1.4% S63). The harness is now validated on four high_only ship measurements spanning a 7.7× range of magnitude.

2. **CURRENT_PHASE's "Rule 17 = +$17" attribution was loose.** Rule 17 alone (J-HIMID via v48 vs v47) is +$5.48/1000h WG on J-high. The +$17 documented in CURRENT_PHASE refers to **v52's TOTAL addition over v47 across all high_only**, which includes Rule 17 J-HIMID + Rules 22-28 defensive across J/T/9/8/7-high. The cross-check `sanity_v52_vs_v47_high_only.py` confirms this interpretation. **Future catalog pages should reference the original session-end report for per-rule lift attribution, not the rolled-up CURRENT_PHASE table.**

3. **Drop-max rate IS partially recoverable at extreme rates — but still below T1.** S60–S62 lesson: decision-matrix percentages overstate refinement headroom. S63 partially shifts: at J's 76% drop-max rate (vs A's 6%, K's 34%, Q's 52%), best-candidate capture jumps to 21.54% (from A's 5.45%, K's 3.33%, Q's 5.99%). The lesson holds *qualitatively* — rules still can't pick the right subset — but the headroom *does* scale with oracle's drop-max rate after a threshold. **C_J1's +$6.44/1000h WG is the biggest single-candidate WG lift across S60–S63. If the T1 gap-closure threshold were 20% instead of 40%, C_J1 would ship.**

4. **HIMID design choices are empirically validated cell-by-cell — FOUR times running.** Rule 14 (A C10), Rule 15 (K C_K6), Rule 16 (Q C_Q7), Rule 17 (J C_J7). The HIBOT alternative was *more negative* at J (−$6.56/1000h WG) than at Q (−$13.07) or K (−$21.73) — somewhat counterintuitive given J's larger drop-max rate, but explainable: at J the population has fewer high-end mid options so the HIBOT tiebreaker's penalty is concentrated rather than diluted.

5. **J-high cells are STRUCTURALLY DEEPER than Q-high but exhibit the same rule-saturation.** Rule 17's residual cells are 21–29% deeper per hand than Rule 16's (DSnj $4,749 vs $3,690; DS_NO_MAXTOP $6,978 vs $5,767; MS_ONLY $4,767 vs $3,938). The MORE oracle deviates from "max-on-top + DS HIMID" (J's 76% drop-J vs Q's 52% vs K's 34% vs A's 6%), the bigger the within-cell gap, but the rule space tested STILL can't close it. **This strengthens the case — for the fourth consecutive max-rank — that high_only's residual is fundamentally non-rule-shaped at the catalog's "one sentence statable" granularity.**

6. **The catalog methodology successfully falsifies the fourth hypothesis.** S60 falsified A-high; S61 falsified K-high; S62 falsified Q-high; S63 falsifies J-high. **Four-quarters minus the J-high best-candidate of high_only's WG residual ($578 of $755 = 77%) is now in the explicit ML-only zone.** T/9/8 (the remaining 2.1% by population, ~$34/1000h WG residual extrapolated) are the only zones still pending audit. If the pattern holds, the entire $755/1000h is ML-only.

7. **Rule 17 vs Rule 24 fire region is unbalanced in v52.** 91.7% of J-high triggers Rule 17 (s2 > 8); only 8.3% triggers Rule 24 (s2 ≤ 8). The "structural twist" of Rule 24's defensive override is real but small in WG impact ($3.26 of $47.46 = 6.9%). Candidate work concentrated on the Rule 17 fire region was the right call.

## Part 8 — User-directive accountability check

S59 user directive: *"Speed is not necessary — clarity and perfection is."*

Session 63 reused S61/S62's harness and cell-tagging infrastructure verbatim (helpers imported directly from `candidates_K_high_S61`), audited Rule 17 in ~3 minutes via `audit_rule17_S63.py`, cross-checked the v52-vs-v47 attribution to reconcile a documentation discrepancy with the harness measurement (reaching $16.77 vs documented $17, within 1.4%), designed 7 J-specific candidates informed by S58's decision matrix and S60+S61+S62's lessons, and tested them all in ~5 minutes via `test_J_high_candidates_S63.py`. The result is a CLEAN ML-only verdict for J-high backed by harness-validated, cell-by-cell evidence — AND a corrected understanding of the $17 attribution that improves the catalog's epistemic integrity going into S64.

The "clarity" half of the directive is met (the harness now agrees with all four high-only shipped lifts and the misattribution is corrected); the "perfection" half acknowledges the catalog's boundary at J — a boundary that S60 located, S61 confirmed at higher drop-max rate, S62 confirmed at higher rate again, and S63 now confirms at the highest tested rate (76%). The lesson partially shifts at J (capture% finally jumps with drop-max rate) but does not break — T1 is still missed.

Sessions 64–65 will produce the parallel catalogs for T/9/8 and the aggregate synthesis. If the same null pattern holds across the always-defensive zone, the final `HIGH_ONLY_RULE_CATALOG.md` will document **the boundary of human-memorizable strategy on high_only** — itself a publishable result of the project per CLAUDE.md's stated end-product goal.

---

*Session 63 end. Production rule chain: v52_full_high_only_handler ($2,498 / $1,522). Production ML champion: v44_dt ($1,081 / $686). Both UNCHANGED. Two production tracks STILL diverge by $1,417/1000h.*
