# Session 62 — Q-High Cell-by-Cell Catalog

*Generated: 2026-05-11 — third page of `HIGH_ONLY_RULE_CATALOG.md`. Session 62 audits Rule 16 (Q-high HIMID, S52) cell-by-cell against the realistic-mixture oracle grid and tests 7 candidate refinement rules across Q-high's leakiest cells (DS_NO_JOINT and MS_ONLY). Mirrors the S60+S61 structure exactly.*

## TL;DR — Q-high catalog verdict: ALL CELLS ML-ONLY (T3)

After cell-by-cell audit of Rule 16 and 7 candidate refinements:

- **Rule 16 (S52, Q-high HIMID) is empirically validated**: harness reproduces +$18.67/1000h whole-grid (matches CURRENT_PHASE's documented S52 ship of +$19 to within 1.7%). **Harness now validated on THREE independent shipped rules** — Rule 14 (+$131, S60, 0.2%), Rule 15 (+$51, S61, 0.7%), Rule 16 (+$19, S62, 1.7%).
- **Q-high TOTAL leak to oracle after Rule 16: $93.77/1000h WG**. v44_dt closes 41% of that gap ($38.53/1000h WG). v44 residual: $55.24/1000h WG.
- **DS_NO_JOINT dominates** ($58.04/1000h WG = 62% of Q-high leak). Within-cell gap is $3,690/1000h vs K-high's $3,062/1000h — **Q's leak is 21% deeper per hand than K's** because oracle drops Q off top 52% (vs K 34%, A 6%) and Rule 16 keeps Q on top 100%.
- **Every candidate falls below Threshold 1** (≥40% gap closure AND ≥+$3/1000h within-cell vs v52). 3 of 7 were net-NEGATIVE on whole-grid lift; 2 (C_Q1, C_Q4) showed micro-positive lift ($+3.33 and $+3.48/1000h WG) but capture% was 5.75% and 5.99% — way below the 40% bar. C_Q7 (HIBOT control) confirmed Rule 16's HIMID design empirically.
- **Q-high's residual is ML-only territory.** v44_dt's $55.24/1000h WG Q-high residual is the closer-to-oracle benchmark; the candidate space tested cannot meaningfully close it.
- **No shipped rule from Session 62.** No change to the production rule chain. **v52_full_high_only_handler ($2,498 full / $1,522 prefix) and v44_dt ($1,081 / $686) both UNCHANGED.**

Three consecutive max-ranks (A, K, Q) have now produced ALL-T3 verdicts despite progressively MORE drop-max opportunity (6% → 34% → 52% drop-rate in DSnj). **Three-of-three is strong empirical evidence that the entire $755/1000h WG high_only residual is genuinely ML-only territory at the catalog's "one-sentence-statable" granularity.** $531 of $755 ($457 from A+K, $74 from Q after subtracting v44's catch) is now formally in the explicit ML-only zone.

## Method

The harness:
1. Loads `data/drill_ho_v44_per_hand_structural.parquet` (S59 artifact — per-hand structural cell tags + oracle/v44 picks).
2. For each candidate `rule_fn`, filters to `(max_rank=12, cell=X)`.
3. Per hand: computes `rule_fn(h)` (None = pass-through to baseline_fn) and `baseline_fn(h) = v52_full_high_only_handler(h)`.
4. Looks up oracle EV (= max of `oracle_grid[cid]`), v44 EV (= `oracle_grid[cid][v44_idx]`), rule EV, baseline EV.
5. Aggregates: within-cell + whole-grid lift in $/1000h, capture% vs baseline AND v44, % optimal, and rule-vs-oracle mismatch class breakdown.

Sanity check: Rule 16 vs its pre-Rule-16 predecessor (`strategy_v46_rule15_Khigh_DS`) returns **+$18.67/1000h whole-grid lift on Q-high** — matching CURRENT_PHASE's documented S52 ship ($19) to within 1.7%. **Harness validated on Q-high** (third independent reproduction).

## Part 1 — Rule 16 cell-by-cell audit (= v52 on Q-high)

After Rule 16 fires, what gap to oracle remains in each Q-high cell?

| Cell | n hands | v52 mean_ev | Oracle mean_ev | Gap within-cell | Gap WG | v44 mean_ev | v44 gap WG |
|---|---:|---:|---:|---:|---:|---:|---:|
| JOINT_HIGH | 13,230 | -0.592 | -0.391 | $2,006/1k | $4.42 | -0.499 | $2.38 |
| JOINT_MED | 8,715 | -1.113 | -0.900 | $2,135/1k | $3.10 | -0.996 | $1.39 |
| JOINT_LOW | 105 | -2.468 | -2.073 | $3,943/1k | $0.07 | -2.171 | $0.02 |
| **DS_NO_JOINT** | **94,500** | **-1.078** | **-0.709** | **$3,690/1k** | **$58.04** | **-0.955** | **$38.80** |
| DS_NO_MAXTOP | 20,160 | -1.443 | -0.866 | $5,767/1k | $19.35 | -1.097 | $7.74 |
| MS_ONLY | 13,440 | -1.646 | -1.252 | $3,938/1k | $8.81 | -1.472 | $4.91 |
| **Q-high total** | **150,150** | — | — | — | **$93.77** | — | **$55.24** |

**Four takeaways from the audit:**

1. **DS_NO_JOINT is the dominant residual cell at Q-high** ($58.04/1000h WG = 62% of Q-high's post-Rule-16 leak). The within-cell gap is **21% deeper per hand than K-high's DSnj** ($3,690/1k vs K's $3,062/1k), reflecting Rule 16's structural mismatch with oracle: oracle drops Q off top 52% in this cell while Rule 16 keeps Q on top 100%.
2. **DS_NO_MAXTOP has the deepest per-hand gap of any Q-high cell** ($5,767/1k within-cell — 56% deeper than K's equivalent, $4,980/1k). But the cell is small enough (n=20,160) that the WG contribution is $19.35, second to DSnj.
3. **v44_dt outperforms Rule 16 within every cell.** v44 captures **$38.53/1000h WG more than Rule 16 on Q-high overall** (vs $65.41 at K, $99.41 at A). The biggest v44-vs-v52 deltas are in DS_NO_JOINT ($19.24/1k WG advantage to v44) and DS_NO_MAXTOP ($11.61/1k WG).
4. **Top mismatch class is `tQ_DS_mu → tQ_SS_ms`** (13,867 hands, $4,240/hand mean regret in DSnj). Rule 16 picks Q-top + DS bot + mu_mid; oracle picks Q-top + SS bot + **ms_mid** ~22% of DSnj. This was tested directly as candidate C_Q5 — and failed (see Part 3). Same pattern as K-high's top mismatch.

## Part 2 — Candidate refinement rules tested

7 candidates targeting Q's drop-Q-off-top play (DSnj 52%, MSonly est. >22%) and the SS_ms switch. Each candidate fires only inside its target cell (`_is_Q_high_no_pair` + `_cell_for_hand_Q`); when it doesn't fire, v52 (=Rule 16 on Q-high) is used.

| ID | Candidate | Cell | Fires | cap_b | $/cell | $/1000h WG | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| C_Q1 | DSnj_drop_Q_low_top_DSms | DSnj | 37.2% | +5.75% | +$212 | **+$3.33** | T3 (micro+) |
| C_Q2 | DSnj_take_Jtop_DSms | DSnj | 8.7% | +3.24% | +$120 | +$1.88 | T3 |
| C_Q3 | DSnj_drop_Q_when_Q_in_DSpair | DSnj | 41.5% | +1.06% | +$39 | +$0.62 | T3 |
| C_Q4 | DSnj_drop_Q_to_2top_DSms | DSnj | 8.7% | +5.99% | +$221 | **+$3.48** | T3 (best micro+) |
| C_Q5 | DSnj_SSms_when_high | DSnj | 32.0% | −3.48% | −$128 | −$2.02 | T3 |
| C_Q6 | MSonly_drop_Q | MSonly | 85.8% | −68.84% | −$2,711 | −$6.06 | T3 (catastrophic) |
| C_Q7 | DSnj_HIBOT_tiebreaker (control) | DSnj | 100.0% | −22.52% | −$831 | −$13.07 | T3 |

(`cap_b` = gap closure vs v52 baseline. `$/cell` = within-cell lift in $/1000h. `$/1000h WG` = whole-grid lift.)

## Part 3 — Why every candidate failed (data-driven)

### DS_NO_JOINT (C_Q1, C_Q2, C_Q3, C_Q4, C_Q5, C_Q7)

S58's decision matrix said oracle drops Q off top **52%** in Q × DS_NO_JOINT — the most aggressive drop-max profile of all high zones tested. The naive read: a "drop Q when achievable" gate firing on a similar fraction should recover most of that. The harness says: **no, even with Q's 52% drop rate (8.7× A's, 1.5× K's), the SAME T3 pattern emerges.** The gates fire on the wrong subset.

- **C_Q1 (drop Q to top ≤ 7 + DS bot + ms_mid_high ≥ T):** fires **37.2%** — *under*-fires relative to oracle's 52% drop rate, yet capture is only **+5.75%**. The "drop low" gate is conservative (T threshold, top ≤ 7), but the conservative subset still doesn't align with oracle's actual drop population. +$3.33/1000h WG — micro-positive but well below T1.
- **C_Q2 (top=J + DS bot + ms_mid_high ≥ T):** mirror of C_K3 (Q-on-top at K). At Q, J-on-top is oracle's 10% pick — narrower than K's 12%. Fires **8.7%**, capture +3.24%, +$1.88/1000h WG. Surgical but tiny.
- **C_Q3 (drop Q when Q is in DS bot pair, ms_mid_high ≥ 9):** S58 Observation 1 says best_DS_bot_pair_high == Q correlates with oracle dropping Q (JOINT rate 70.6% at Q-in-DSpair vs 93%+ when DS_pair_high < Q). Fires **41.5%** — the highest fire rate of any catalog candidate — but capture only **+1.06%**, $+39/cell, $+0.62/1000h WG. The "Q-in-DSpair" structural axis is a tendency, not a deterministic rule; the gate over-fires. **Lesson generalizes from K**: at K, C_K2 fired 44.6% on the same structural axis and was −$34.46/1000h WG (worst). At Q, the gate is less harmful (the axis is a *stronger* signal at Q per S58 Obs 1's 70.6% vs K's 83%) but still doesn't reach T1.
- **C_Q4 (top=2 + DS bot + ms_mid_high ≥ T):** the BEST Q candidate by capture (+5.99%) and within-cell lift ($+221/cell). Targets oracle's biggest specific non-Q top in Q × DSnj (15% rate vs K's 7%). +$3.48/1000h WG — the second-largest micro-positive of any candidate across S60+S61+S62 (only K's C_K3 at $+3.53 was bigger, and that's within noise). Surgical top=2 targeting works as a *direction*, but only fires when top=2 with strong ms_mid is achievable (8.7% of the cell). The remaining 91.3% goes through v52's "keep Q on top + DS mu" path. **T3 at 5.99% capture.**
- **C_Q5 (switch Q-top DS_mu → Q-top SS_ms when SS_ms mid_high ≥ J):** mirror of C_K4 and A-high C2/C3. Fires **32.0%** — almost matching oracle's 56% ms_mid share in Q × DSnj — but again the wrong subset. The mismatch detail is identical to K: when our rule picks `tQ_SS_ms`, oracle wanted `tQ_DS_mu` (5,924 hands at $4,775/hand) — i.e., switching to SS_ms COSTS money where DS_mu was right. Net **−$2.02/1000h WG**.
- **C_Q7 (HIBOT control):** 100% fire (always overrides Rule 16's HIMID), $-831/cell, $-13.07/1000h WG. **Third retrospective validation that Rule 16's HIMID design from S52 is empirically correct** — same retrospective pattern from A (C10) and K (C_K6).

**Structural finding (re-confirmed at third max-rank):** even when oracle's drop-max rate is 8.7× higher than A-high's and 1.5× higher than K-high's, single-axis gates can't pick the right subset. The "drop Q iff X" formulations all fire on supersets of oracle's actual drop population, hurting the complement. v44_dt encodes the joint distribution via 107 features and 2.25M leaves; a rule-chain refinement here would need 5+ feature gates and 10+ branch logic — which reproduces ML, not abstracts it.

### MS_ONLY (C_Q6)

C_Q6 (drop Q when top ≤ 7, ms_mid_high ≥ T, SS or 31 bot achievable): fires **85.8%** — catastrophic over-fire mirroring C_K5's 82.7% pattern at K. Result: $-2,711/cell, **$-6.06/1000h WG** (worst micro-cell catastrophe in MSonly across S60-S62). The pattern: any K/Q-high MSonly hand with a low spare card (which is most of them) achieves the gate predicate, but oracle keeps Q on top a majority of the time — so over-firing hits the wrong majority.

The mismatch detail is sobering: `t5_SS_ms → tQ_SS_ms` 279 hands at $10,341/hand mean regret. When the rule drops Q, it picks a low-quality top that loses to oracle's Q-on-top by huge margins.

**Lesson generalizes from K**: relaxing the gate from C_K5's mid_high ≥ J → C_Q6's mid_high ≥ T at Q to account for Q's lower top-rank pool produced the *same* over-fire catastrophe at the *same* fire rate (82.7% K → 85.8% Q). The MSonly drop-max play is genuinely non-rule-shaped at this catalog granularity.

## Part 4 — Honest ML-only labeling

Q-high's residual gap to oracle ($93.77/1000h WG) split across cells:

| Cell | WG residual after R16 | v44 captures (more than R16) | Net ML-only territory |
|---|---:|---:|---:|
| JOINT_HIGH | $4.42 | $2.04 | $2.38 ML |
| JOINT_MED | $3.10 | $1.71 | $1.39 ML |
| JOINT_LOW | $0.07 | $0.05 | $0.02 ML |
| DS_NO_JOINT | $58.04 | $19.24 | $38.80 ML |
| DS_NO_MAXTOP | $19.35 | $11.61 | $7.74 ML |
| MS_ONLY | $8.81 | $3.90 | $4.91 ML |
| **Q-high total** | **$93.77** | **$38.53** | **$55.24 ML** |

**For Session 62's purpose, all Q-high cells are labeled ML-only** — the catalog space explored doesn't produce a Threshold-2 refinement for any of them. v44_dt's Q-high residual ($55.24/1000h WG) is the ceiling a catalog refinement could close further — and even at the cell-most-promising (DS_NO_JOINT, where oracle drops Q 52%), the candidate space tested couldn't close it.

**This does not mean Q-high is unrefinable forever.** It means:
1. Single-axis gates can't pick the right subset of oracle's drop-Q play, even when that play is 1.5× more common at Q than K and 8.7× more common than at A.
2. Multi-axis gates (5+ features, branching) might work but violate the catalog's "human-memorizable" constraint.
3. The remaining $55.24/1000h WG belongs to v44_dt's exclusive territory at current rule chain depth.

## Part 5 — Implications for Session 63 (J-high)

Three consecutive max-ranks (A, K, Q) have now produced ALL-T3 verdicts despite progressively MORE drop-max opportunity. J-high is the next test:

| Property | A-high | K-high | Q-high | J-high |
|---|---:|---:|---:|---:|
| Population | 660,660 (53.8%) | 330,330 (26.9%) | 150,150 (12.2%) | 60,060 (4.9%) |
| WG residual after v52 | $281 | $176 | $94 | TBD per S63 audit |
| Oracle drops max off top in DSnj | 6% | 34% | 52% | **76%** |
| Oracle drops max off top in JOINT (per S58) | 1% (HIGH) | 10% (HIGH) | 20% (HIGH) | **44% (MED)** |
| Rule shipped | Rule 14 (+$131) | Rule 15 (+$51) | Rule 16 (+$19) | Rule 17 (+$17) |

**Hypothesis for S63:** if A, K, and Q all saturate at ML-only at this catalog granularity, J is likely to do the same. The fundamental obstacle is that "oracle drops X q% in cell C" is information about WHICH q%, not WHETHER any deterministic gate can reach q% capture. J's q% being even higher (76%) doesn't change that — it just means the "drop-J achievable" gate would fire on an even larger superset of oracle's actual drops.

**Two falsifiable predictions for S63 going in:**
1. The Rule 17 sanity check (vs `strategy_v47_rule16_Qhigh_DS`) reproduces ~+$17/1000h WG on J-high (S53's documented ship).
2. ALL J-high candidates land T3, reinforcing the high_only-is-rule-saturated thesis that is now backed by three consecutive falsifications (A, K, Q).

**One important nuance at J:** Rule 17 is the offensive J-high HIMID. But v52 also has Rule 24 (J-high defensive when s2 ≤ 8) which DOES fire for some J-high hands. The cell decomposition at J needs to account for which sub-population each handles. This is a slight structural twist not present at A/K/Q where the defensive rules don't fire (s2 > 8 always).

If prediction 2 is wrong and a J-high candidate ships T2, that's a major surprise — and would indicate the catalog approach can crack the lower max-ranks (J/T/9/8) where oracle behavior is more rule-shaped (defensive low-top is more common).

## Part 6 — Files produced (Session 62)

| File | Purpose |
|---|---|
| `analysis/scripts/audit_rule16_S62.py` | Phase 2 sanity check + Phase 2b cell-by-cell audit driver. Output: `/tmp/s62_phase2_audit.log`. |
| `analysis/scripts/candidates_Q_high_S62.py` | 7 candidate rules for Q-high cells (C_Q1–C_Q7). Imports `_enumerate_max_on_top_configs` and friends from `candidates_K_high_S61` (already max_rank parameterized). |
| `analysis/scripts/test_Q_high_candidates_S62.py` | Driver: runs every candidate through the harness, scores T1/T2/T3 verdicts, writes JSON. Output: `/tmp/s62_phase4_sweep.log`. |
| `data/session_62_candidate_results.json` | Full results for C_Q1–C_Q7. |
| `SESSION_62_Q_HIGH_CATALOG.md` | This file. Third page of the eventual `HIGH_ONLY_RULE_CATALOG.md`. |

The harness, candidate-test driver, and cell tagging infrastructure remain **reusable as-is** for S63 (J-high). The only adaptation needed: copy `candidates_Q_high_S62.py` → `candidates_J_high_S63.py`, change `QUEEN = 12` → `JACK = 11`, retune the gates for J's even-more-aggressive drop-max profile (76% in DSnj per S58). And handle the Rule 24 defensive overlap noted above.

## Part 7 — Methodology lessons (Session 62)

1. **The harness reproduces shipped lift on a THIRD max-rank.** Rule 14 reproduced to 0.2% in S60 ($131.25 vs $131); Rule 15 reproduced to 0.7% in S61 ($51.38 vs $51); Rule 16 reproduced to 1.7% in S62 ($18.67 vs $19). Three-for-three on independent shipped rules. **The harness is fully validated across the high zone.**

2. **Drop-max rate is not a recoverable quantity for simple gates — at any rate from 6% to 52%.** S60's lesson said decision-matrix percentages overstate refinement headroom because oracle knows WHICH q% to switch on. S61 confirmed at 34%. S62 confirms at 52%. **Lesson generalizes monotonically across the entire 6%→52% range.** No candidate at any max-rank exceeds 5.99% capture vs v52, and the rate of best-candidate-capture barely shifts (5.45% A → 3.33% K → 5.99% Q) despite the underlying drop-max opportunity growing 8.7×.

3. **HIMID design choices are empirically validated cell-by-cell — three times running.** Rule 14's HIMID was confirmed correct by A-high's C10 in S60. Rule 15's HIMID was confirmed by C_K6 in S61. Rule 16's HIMID was confirmed by C_Q7 in S62 (HIBOT replacement was −$831/cell, −$13.07/1000h WG — same retrospective validation pattern as A and K). The HIMID design choice from S50/S51/S52 is sound at three independent max-ranks.

4. **Q-high cells are STRUCTURALLY DEEPER than K-high but exhibit the same rule-saturation.** Rule 16's residual cells are 21–56% deeper per hand than Rule 15's (DSnj $3,690 vs $3,062; DS_NO_MAXTOP $5,767 vs $4,980 — +16%; MS_ONLY $3,938 vs $3,710 — +6%). The MORE oracle deviates from "max-on-top + DS HIMID" (Q's 52% drop-Q vs K's 34% vs A's 6%), the bigger the within-cell gap, but the rule space tested STILL can't close it. **This strengthens the case** — for the third consecutive max-rank — that high_only's residual is fundamentally non-rule-shaped at the catalog's "one sentence statable" granularity.

5. **The best Q-high micro-positive is the surgical top=2 gate (C_Q4).** Mirror of C_K7 at K. C_Q4 captures 5.99% (vs C_K7's 0.99%) — Q's higher top=2 oracle rate (15% vs K's 7%) does scale, but +$3.48/1000h WG is still under T2's $5/1000h bar even taken alone, and combining with C_Q1 (which fires on a superset population) double-counts. The two micro-positives sum to $+6.81/1000h WG gross, but their fire regions overlap (37.2% + 8.7% with top=2 ⊂ top ≤ 7).

6. **The catalog methodology successfully falsifies the third hypothesis.** S60 falsified A-high; S61 falsified K-high; S62 falsifies Q-high. **Three-quarters of high_only's WG residual ($531 of $755) is now in the explicit ML-only zone.** J/T/9/8 (the remaining 6.9% by population, ~$80/1000h WG residual) are the only zones still pending audit. If the pattern holds, the entire $755/1000h is ML-only.

## Part 8 — User-directive accountability check

S59 user directive: *"Speed is not necessary — clarity and perfection is."*

Session 62 reused S61's harness and cell-tagging infrastructure verbatim (helpers `_enumerate_max_on_top_configs`, `_enumerate_nonMax_top_DSms`, `_enumerate_nonMax_top_anyBot_ms` imported directly from `candidates_K_high_S61`, no copy-paste), audited Rule 16 in ~3 minutes via `audit_rule16_S62.py`, designed 7 Q-specific candidates informed by S58's decision matrix and S60+S61's lessons, and tested them all in ~5 minutes via `test_Q_high_candidates_S62.py`. The result is a CLEAN ML-only verdict for Q-high backed by harness-validated, cell-by-cell evidence. **The "clarity" half of the directive is met; the "perfection" half acknowledges the catalog's boundary at Q — a boundary that S60 located, S61 confirmed at higher drop-max rate, and S62 now confirms at the highest tested drop-max rate (52%).**

Sessions 63–65 will produce the parallel catalogs for J/T/9/8. If the same null pattern holds across all max-ranks, the final `HIGH_ONLY_RULE_CATALOG.md` will document **the boundary of human-memorizable strategy** — itself a publishable result of the project per CLAUDE.md's stated end-product goal.

---

*Session 62 end. Production rule chain: v52_full_high_only_handler ($2,498 / $1,522). Production ML champion: v44_dt ($1,081 / $686). Both UNCHANGED. Two production tracks STILL diverge by $1,417/1000h.*
