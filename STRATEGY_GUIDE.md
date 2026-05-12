# Taiwanese Poker — Strategy Guide

> The condensed decision tree, in plain English, validated against the
> Full Oracle Grid (6M canonical hands × 105 settings × N=200 MC samples
> vs the realistic 70/25/5 human mixture).
>
> **Structure of this file:**
> 1. Strategy evolution (chronological — what we learned and when)
> 2. ML champion progression (every model version + score)
> 3. Distillation insights (what features matter, what the DT does)
> 4. What's still on the table (residuals + open questions)
> 5. Where each rule + model lives in code
> 6. **The Current Standard** (at the bottom — the rules to memorize, the model to call)
>
> Last updated: 2026-05-11 (Session 60 — **NULL RESULT: A-high cell catalog audit ships no rule; A-high cells formally labeled ML-only**. Built `test_rule_catalog.py` per-cell rule audit harness; sanity check reproduced Rule 14's documented +$131.25/1000h whole-grid lift (matches S50 to 0.2%) — **harness validated**. Phase 2 cell-by-cell audit of Rule 14: remaining A-high gap to oracle = $281.2/1000h whole-grid (DS_NO_JOINT $161.7 = 58%; DS_NO_MAXTOP $55.1; MS_ONLY $35.4; JOINT_HIGH $26.7; rest small). vs v44_dt's $182.5/1000h A-high residual, v44 captures ~$99 more than Rule 14. Phase 3+4 tested **10 candidate refinement rules** across the 3 leakiest cells; **every candidate failed Threshold 1**. Most striking: C1 (switch DS_mu → SS+ms_mid whenever achievable) was net **−$96.9/1000h whole-grid** — oracle picks tA_SS_ms 27.9% of DSnj but a deterministic gate firing on 93% of cell catastrophically harms the 72% where DS was correct. C10 (HIBOT tiebreaker replacing Rule 14's HIMID) shipped **−$40/1000h** — empirical post-hoc validation that S50's HIMID design choice was correct. **Two methodology lessons**: (i) decision-matrix percentages overstate refinement headroom — "oracle picks X 28%" means "oracle knows WHICH 28%", not "switching to X recovers EV"; (ii) Rule 14 audit confirms HIMID is optimal among tested tiebreakers. **No production change**: v52_full_high_only_handler ($2,498 full / $1,522 prefix) and v44_dt ($1,081 full / $686 prefix) BOTH UNCHANGED. The two tracks still diverge by $1,417/1000h. Harness PROVEN AND READY for S61 (K-high), where structural conditions are different (oracle drops K off top 34% in K × DSnj vs 6% at A) and the C9-style drop-max play may clear thresholds. `SESSION_60_A_HIGH_CATALOG.md` produced as the first page of the eventual `HIGH_ONLY_RULE_CATALOG.md`. Earlier: Session 59 — **NULL RESULT: v45_dt does NOT ship**. 4 rank-valued `ho_v5_*_g` features designed from HO13's stratification of v44's non-max-joint quality residuals (max_mid_high in non-max joints + best_combined_q + max_in_bot_pair_n + 4f topMax_n_configs) added only **+9 leaves** to v44's 2.248M-leaf tree and shipped **$0/1000h lift on both full and prefix grids**. v44_dt remains the ML champion at $1,081 full / $686 prefix. Feature importance #66/#97/#106/#110 (sum 0.09%) — the LOWEST per-ship in project history. **Methodology lesson: the 4-phase playbook hits a saturation ceiling at depth=36 ml=1 + ~2.25M leaves on 6M rows after 3 consecutive same-zone passes.** HO11/HO12/HO13 verified the data signal IS real (K × DS_NO_JOINT × best_top=Q × mid_h≥J is a $9.76/1000h cell with a 30.5% pick-rate gap), but ho_v5 features are mathematically derivable from ho_v4 + base, so the DT cannot exploit them at saturation. Session 60 should pivot to (a) surgical RULE on the HO13-identified cell, (b) trips zone for a fresh playbook application, or (c) different model class. The two production tracks STILL diverge by $1,417/1000h (rule chain v52 at $2,498 / $1,522 — UNCHANGED; ML champion v44_dt at $1,081 / $686 — UNCHANGED). Earlier: Session 58 — **v44_dt new ML champion via the S54 playbook applied to high_only zone — THIRD PASS (+$42 full / $0 prefix vs v43_dt)**: 4 rank-valued `ho_v4_*_g` features encoding three structural axes invisible to v43: DS bot pair_high quality with top=max (DS_NO_JOINT cell discrimination), 4-flush+ms_mid with top=max (Ace-high alt route), and non-max-top joint achievability + best non-max top rank (the "max-into-bot" route at lower ranks). Five drills (HO5–HO10) on all 1.226M high_only hands surfaced the deepest residuals: (1) `DS_NO_JOINT` cell is dominant at 62.9% × every max-rank, contributing ~69% of high_only regret; v43 under-routes DS bot by 10–20% there. (2) Within JOINT picks, oracle is mid-first (mean mid_pct 0.67–0.81 >> bot_pct 0.24–0.36) — v43 already covers this via ho_v3_max_mid_high. (3) JOINT take-rate collapses with lower max-rank (A:95% → 8:13%); 47.7% of high_only hands have a non-max-top joint achievable that v43 cannot see. (4) At max=A, 4f+ms is the dominant alt (54% of A-alt picks). v43 → v44: $1,123 → $1,081 full / $686 → $686 prefix; **high_only within-cat $2,075 → $1,868 (−$207, −10.0%); high_only pct_opt 37.9% → 41.8% (+3.9%)**. v44 is the new ML champion at 2.25M leaves / 107 features (depth=36 ml=1, +3.2% leaves over v43). Feature importance #47/#80/#93/#95 (0.13%/0.04%/0.01%/0.01%) — yet ships +$42 via surgical gating. Cumulative v32 → v44 = −$634 full / −$218 prefix (9 ML ships). All 7 non-targeted categories byte-identical to v43 on both grids (surgical via gating). p90 0.400 → 0.390; p99 0.980 → 0.970. **Three-session high_only collapse (S55→S58): $2,796 → $2,411 → $2,075 → $1,868 = −$928 within-cat (−33.2%)** — composing three conditional axes (ho_v2 DS-only + ho_v3 DS+ms-joint + ho_v4 DS-quality+non-max-joint+4f) compresses the same zone three times without surgical interference. **Methodology validation: the 4-phase playbook is transferable to the SAME zone for a THIRD pass; decision matrix is a separable deliverable from the ML ship.** Also produced `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` at repo root — per-max-rank × per-cell oracle TOP/BOT/MID profile + trade-off rules — answering the user's S57 review question. End-of-S58 residual map: high_only $1,868/1000h within-cat (STILL dominant — $762/1000h whole-grid = ~71% of v44's regret), pair $1,097, two_pair $363, trips $1,194, trips_pair $281, three_pair $1,613, quads $545, composite $960. Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). **The two production tracks now diverge by $1,417/1000h** — ML champion beats rule chain by more than half its EV deficit.) (Earlier: Session 57 — **v43_dt new ML champion via the S54 playbook applied to high_only zone — SECOND PASS (+$69 full / $0 prefix vs v42_dt)**: 4 rank-valued `ho_v3_topMax_DS_ms_*_g` features encoding JOINT (DS bot + ms mid) achievability + quality conditional on top=max-rank-of-hand. After S56's ho_v2 features collapsed the DS-only axis, the SAME SS→DS pattern remained dominant — but with a NEW axis (mid-suiting). Phase 1 confirmed v42 STILL over-routes SS bot (46.07% vs oracle 32.04%, −14.0%). Phase 1b confirmed 100% of dominant-class mismatches have a (DS bot + ms mid) JOINT config achievable WITH the Ace on top. v42 → v43: $1,192 → $1,123 full / $686 → $686 prefix; **high_only within-cat $2,411 → $2,075 (−$336, −13.9%); high_only pct_opt 33.4% → 37.9% (+4.5%)**. v43 is the new ML champion at 2.18M leaves / 103 features (depth=36 ml=1, +3.2% leaves over v42). Feature importance is the LOWEST per-ship in the project (#63/#64/#100/#102 at 0.07%/0.07%/0.01%/0.00%) — yet ships +$69 via surgical gating. Cumulative v32 → v43 = −$592 full / −$218 prefix (8 ML ships). All 7 non-targeted categories byte-identical to v42 on both grids (surgical via gating). p90 0.425 → 0.400; p99 1.035 → 0.980. **Two-session high_only collapse (S55→S57): $2,796 → $2,411 → $2,075 = −$721 within-cat (−25.8%)** — composing two conditional axes (ho_v2 DS-only + ho_v3 DS+ms-joint) compresses the same zone twice without surgical interference. **Methodology validation: the 4-phase playbook is transferable to the SAME zone for a SECOND pass**; joint achievability is a distinct structural axis from single-axis achievability; user predictions can be wrong about WHICH axis dominates even after one pass collapses one axis. End-of-S57 residual map: high_only $2,075/1000h within-cat (STILL dominant — $838/1000h whole-grid = ~75% of v43's regret), pair $1,097, two_pair $363, trips $1,194, trips_pair $281, three_pair $1,613, quads $545, composite $960. Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). **The two production tracks now diverge by $1,375/1000h** — ML champion beats rule chain by more than half its EV deficit.) (Earlier: Session 56 — **v42_dt new ML champion via the S54 playbook applied to high_only zone (+$79 full / $0 prefix vs v41_dt)**: 4 rank-valued `ho_v2_bot_DS_*_g` features mirroring pair_aug_v5 / trips_pair_v2 / two_pair_v2 patterns target the dominant high_only blind spot — DS-bot achievability with Ace-top preserved. v41 → v42: $1,270 → $1,192 full / $686 → $686 prefix; **high_only within-cat $2,796 → $2,411 (−$385, −13.8%); high_only pct_opt 29.0% → 33.4% (+4.4%)**. v42 is the new ML champion at 2.11M leaves / 99 features (depth=36 ml=1, +4.7% leaves over v41). 3 of 4 new features in top-32 importance (#26, #31, #32). Cumulative v32 → v42 = −$524 full / −$218 prefix (7 ML ships). All 7 non-targeted categories byte-identical to v41 on both grids (surgical via gating). p90 0.450 → 0.425; p99 1.075 → 1.035. **Phase 1b 100% confirmation** (100% of dominant-class mismatches have max_top=A available in DS configs AND 100% of oracle picks use it) — the cleanest Phase 1b validation in the project. **User-prediction "different feature types needed" was partially correct, partially wrong**: the dominant high_only blind spot was the SAME DS-routing pattern as prior zones; only the bot suit profile differs in 100% of mismatches, not the top-card choice. **Methodology validation: the 4-phase playbook is fully transferable to the largest population zone (40.4%) without modification.** Methodology lessons: surgical-gating means prefix-grid neutrality is correct (not suspect) when the prefix slice doesn't contain the targeted population; when a feature family (DS-bot achievability) is missing entirely from a zone, that gap dominates even when other axes also exist; single-axis ships have predictable leaf growth (+4.7% here vs +32% for v41's two_pair v2). End-of-S56 residual map: high_only $2,411/1000h within-cat (STILL the dominant residual — $975/1000h whole-grid = ~82% of v42's total regret), pair $1,097, two_pair $363, trips $1,194, trips_pair $281, three_pair $1,613, quads $545, composite $960. Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). **The two production tracks now diverge by $1,306/1000h** — ML champion beats rule chain by more than half its EV deficit.) (Earlier: Session 55 — **TWO ML ships in one session: v40_dt + v41_dt — second-largest combined session lift after S54 (+$142 full / +$115 prefix vs v39_dt)**: applied the Session 54 diagnostic-driven feature engineering playbook to TWO residual zones. Track A: trips_pair ship as v40_dt with 4 rank-valued `tp_v2_*_g` features mirroring pair_aug_v5 pattern for Pbot_DS routings (R1+R2+R3); v39 → v40: $1,412 → $1,394 full / $801 → $772 prefix; **trips_pair within-cat $909 → $281 (−69%); pct_opt 64.2% → 85.1% (+20.9%)**. Track B: two_pair ship as v41_dt with 4 rank-valued `t2p_v2_*_g` features completing the Layout B/C asymmetry (existing `t2p_n_layout_b_routings_ds_g` had no Layout C equivalent — asymmetric blind spot); v40 → v41: $1,394 → $1,270 full / $772 → $686 prefix; **two_pair within-cat $918 → $363 (−60%); pct_opt 66.6% → 83.2% (+16.6%)**. v41 is the new ML champion at 2.02M leaves / 95 features. Cumulative v32 → v41 = −$445 full / −$218 prefix (6 ML ships). All non-targeted categories byte-identical in both ships (surgical via gating). p90 0.480 → 0.450; p99 1.090 → 1.075. **Methodology validation: the S54 playbook is now TRANSFERABLE across ML residual zones** — identical Phase 1/1b/2 shape, identical feature suite shape, identical depth=36 ml=1 hyperparams. Methodology lesson: asymmetric existing features signal blind spots; low individual feature importance (0.02-0.04%) can still ship lift via surgical gating; population size dominates leaf-growth potential (v40: +3.4% leaves over 2.86% zone; v41: +32% leaves over 22.3% zone). End-of-S55 residual map: high_only $2,796/1000h within-cat (BY FAR the largest remaining residual; ~63% of v41's total regret), pair $1,097, two_pair $363 (S55-compressed), trips $1,194, trips_pair $281 (S55-compressed), three_pair $1,613, quads $545, composite $960. Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). **The two production tracks now diverge by $1,228/1000h** — ML champion beats rule chain by nearly half its EV deficit.) (Earlier: Session 54 — **v39_dt ships as new ML champion — LARGEST single ML retrain ship in project history (+$237 full / +$90 prefix vs v36_dt)**: 4 rank-valued conditional features `pair_aug_v5_*_g` targeting the pair-zone gap diagnosed via per-(max, pair) cell mismatch matrix. v36 → v39: $1,649 → $1,412 full ($891 → $801 prefix); pct_opt 53.61% → 57.88% full / 62.61% → 64.55% prefix. **Pair zone within-category $1,604 → $1,097 (−$507, −32%); pair pct_opt 56.6% → 65.7% (+9.1%).** All other categories byte-identical to v36 (gating worked surgically). Leaf count +43% (1.06M → 1.52M); depth saturation broke from 33 to 36. 3 of 4 new features in top-30 importance. Cumulative v32 → v39 = −$303 full. Methodology breakthrough: rank-valued conditional features describing the QUALITY of the alternative configuration unlock saturated trees — Phase 2 v1's booleans (v38) shipped $0 because they were redundant with existing suit features. The pair zone was the dominant ML residual for sessions and was cracked cleanly with diagnostic-driven feature design. Rule chain v52 unchanged at $2,498 full / $1,522 prefix. Earlier: Session 53 overnight — **Rule 17 ships in production as v52 = comprehensive high_only generalized handler**: addresses ALL high_only no-pair sub-pops (max ≥ 7) with the right offensive vs defensive structure per-cell. Trigger + setting cascade: (1) Defensive lowest-on-top + DS-bot HIMID for max ∈ {T, 9, 8, 7} ALWAYS, and for max ∈ {J, Q, K} when 2nd-high ≤ 8; (2) HIMID for max=J when not defensive; (3) v47's Rules 14-16 for max ∈ {Q, K, A}. v47 → v52 score: $2,515 → $2,498 full, $1,522 → $1,522 prefix (UNCHANGED — high_only zero prefix coverage). pct_opt: 43.30% → 43.34% full. high_only $3,096 → $3,014 (−$82, −2.6%). p90 regret IMPROVED 0.725→0.720. Cumulative v39 → v52 = −$348 full / −$185 prefix; v14 → v52 = −$535 full. Origin: per-(max, s2) characterization revealed that for max ≤ T oracle picks max-on-top only 3-15% (vs HIMID forces it 100%). v52 corrects with always-defensive for low-max + gated K/Q/J + skip A-high (where A-on-top is universally optimal). Sister strategies v48 (HIMID-only +$8) and v50 (HIMID + A/K/Q/J defensive, regressed −$6 vs v48) confirmed the design choice. The S43-S53 arc has shipped 9 production rules totaling −$348 full / −$185 prefix.) (Earlier: Session 52 — **Rule 16 ships in production as v47**: trigger = cat=high_only AND max=Q AND DS-bot OR SS-bot achievable with Q on top. Setting builder: TOP=Q always, try DS-bot first then SS-bot fallback, HIMID tie-break (parallel to Rules 14/15). v46 → v47 score: $2,534 → $2,515 full, $1,522 → $1,522 prefix (UNCHANGED — high_only zero prefix coverage). pct_opt: 43.24% → 43.30% full. high_only $3,187 → $3,096 (−$91, −2.9%). Cumulative v39 → v47 = −$330 full / −$185 prefix; cumulative v14 → v47 = −$518 full. Origin: Drill N characterization (n=150,150 = 2.5% of grid) found Q-high contributes $112/1000h whole-grid regret. Critical finding: Q-on-top is borderline — oracle picks Q on top only 49.37% (vs A 93%, K 66%); 51% non-Q-on-top sub-zone includes 16% defensive 2-on-top. The three-session high_only sub-arc (S50-S52, Rules 14/15/16) shows diminishing returns: A-high −$131 → K-high −$51 → Q-high −$19, totaling −$201 across the A+K+Q sub-pops (19% of grid). Per-fire DS lift INCREASES (worse baseline) but pop size DECREASES, leading to shrinking absolute ships. J-high estimated +$8-12 — below threshold for further single-pop drills. The S43-S52 arc has shipped 8 production rules totaling −$330 full / −$185 prefix.) (Earlier: Session 51 — **Rule 15 ships in production as v46 — 3rd-LARGEST SINGLE-RULE LIFT IN PROJECT HISTORY (+$51/1000h whole-grid full)**: trigger = cat=high_only AND max=K AND DS-bot OR SS-bot achievable with K on top. Setting builder: TOP=K always, try DS-bot first then SS-bot fallback, in both cases use HIMID tie-break (parallel to Rule 14). v45 → v46 score: $2,585 → $2,534 full, $1,522 → $1,522 prefix (UNCHANGED — high_only zero prefix coverage). pct_opt: 43.05% → 43.24% full / 53.06% (unchanged) prefix. high_only $3,439 → $3,187 (−$252 within high_only, −7.3%). high_only pct_opt 23.3% → 24.2% (+0.9%). p90 regret IMPROVED 0.745→0.730. Cumulative v39 → v46 = −$311 full / −$185 prefix. Origin: Drill M characterization (n=330,330 K-high no-pair = 5.5% of grid) found K-high contributes $226/1000h whole-grid regret (2nd-largest residual after A-high's $412). Critical difference vs A-high: oracle picks K on top only 66% of the time (vs A on top 93%) — the 34% non-K-on-top sub-zone is a known Rule 15 v2 candidate. Best-in-DS vs v45 = +$2,999/1000h within fires (LARGER per-fire lift than A-high's +$1,937 due to weaker baseline). The S43-S51 arc has now shipped 7 production rules totaling −$311 full / −$185 prefix — average ship −$44/1000h per rule.) (Earlier: Session 50 — **Rule 14 ships in production as v45 — LARGEST SINGLE-RULE LIFT IN PROJECT HISTORY (+$131/1000h whole-grid full)**: trigger = cat=high_only AND max=A AND DS-bot OR SS-bot achievable with A on top. Setting builder: TOP=A always, try DS-bot first then SS-bot fallback, in both cases use HIMID tie-break (mid keeps the 2 highest non-A cards). v44 → v45 score: $2,717 → $2,585 full, $1,522 → $1,522 prefix (UNCHANGED — high_only has zero prefix coverage). pct_opt: 42.34% → 43.05% full / 53.06% → 53.06% prefix. high_only category $4,082 → $3,439 (−$643 within high_only, 16% reduction). high_only pct_opt 19.8% → 23.3% (+3.5%). p90 regret IMPROVED 0.785→0.745. Beats v33's Rule 6 (+$113, S37) which had held the single-rule record for 13 sessions. Cumulative v39 → v45 = −$260 full / −$185 prefix. Origin: Drill K characterization (n=660,660 = 11% of grid) found A-high no-pair has $412/1000h whole-grid regret contribution (single largest residual zone); v44 over-DS's (59% vs oracle 48%), picks rainbow 13× too often (11% vs 0.83%), and under-uses 3+1 (4% vs 14%). Drill L heuristic sweep found HIMID is the right tie-break, NOT HIBOT — counter to "stack high cards in bot for kicker strength" intuition. Mechanism: with A on top, K+Q etc. belong in MID for Hold'em scoring; lower 4 cards form bot's Omaha play where suit matters more than rank. The S43-S50 arc has now shipped 6 production rules totaling −$260 full / −$185 prefix — the project's largest multi-rule family.) (Earlier: Session 48 — **Rule 13 ships in production as v44**: trigger = cat=three_pair AND (MM_mid_DS achievable OR HH_mid_DS achievable). Setting builder: try MM_mid first (mid=MM pair, bot=HH+LL pairs, top=singleton — V_MM_MID +$2,463/1000h within fires), else HH_mid (V_HH_MID +$2,227); SKIP LL_mid-only cases (V_LL_MID is catastrophic at -$4,117/1000h within fires). **Lift: +$11/1000h whole-grid full + +$29/1000h whole-grid prefix.** v43 → v44 score: $2,727 → $2,717 full, $1,550 → $1,522 prefix. pct_opt: 42.20% → 42.34% full / 52.61% → 53.06% prefix. **three_pair regret $2,268 → $1,696 (−$572 within category, 25% reduction). three_pair pct_opt 51.5% → 59.3% (+7.8% — the largest single-category pct_opt jump from any rule ship in the project).** Surprising drill finding: three_pair within-class DS does NOT favor "highest pairs in bot" (V_LL_MID catastrophic at -$4,117/1000h within fires) — opposite of two_pair where HH-to-bot wins; mechanism is that LL in mid is too weak a Hold'em hand and the HH+MM bot upgrade can't compensate. Skip-the-trap design pattern: explicitly exclude LL_mid-only cases. Cumulative v39 → v44 = −$129 full / −$185 prefix; the suit-dominance arc has shipped 5 production rules (v40b → v41 → v42 → v43 → v44) across 6 sessions, the project's largest multi-rule family from a single methodology breakthrough (S44 within-hand pairwise). Also Session 48: Rule 12 max≤Q extension (v43b) tested and DEFERRED — full +$14 but prefix regresses −$6 with pct_opt drop 52.61%→52.45%; passes strict 2x gate but qualitative prefix regression undermines confidence.) (Earlier: Session 47 — **Rule 12 ships in production as v43**: trigger = cat=two_pair AND max≤J AND DS-bot achievable with both pairs intact. Setting builder: try HH-to-bot first (HH 2 + 2 singletons completing 2+2 DS pattern), else try LL-to-bot, else fall through to v42; MID = the OTHER pair (anchor preserved); TOP = leftover singleton (deterministic). **Lift: +$35/1000h whole-grid full + +$66/1000h whole-grid prefix** — both grids strongly positive. v42 → v43 score: $2,763 → $2,727 full, $1,616 → $1,550 prefix. pct_opt: 41.93% → 42.20% full / 51.81% → 52.61% prefix. Two_pair regret −$160 within two_pair. **Largest single-rule full-grid lift since v33's Rule 6 (Session 37, +$113).** Origin: Drill B's B1−B2 = +$1,864/1000h sister candidate validated. Drill F sweep showed HH-to-bot wins (+$1,808 within fires) over LL-to-bot (+$1,044). Hybrid covers all 120,960 fires (46.2% of J-low two_pair). Cumulative v39 → v43 = −$118 full / −$157 prefix. The S45-S47 suit-dominance arc (Rule 10 v3 → Rule 11 → Rule 12) ships three rules from the S44 within-hand pairwise insight, totaling −$118 full. Also Session 47 Drill E (Rule 11 heuristic variant sweep) was a negative result — v42's V_LOLO is empirically optimal among 6 simple tie-break variants; the +$1,794/1000h within-fires gap to A5 oracle requires more sophisticated logic.) (Earlier: Session 46 — **Rule 11 ships in production as v42**: first single-cell rule of the project. Trigger: cat=pair AND P=11 AND max_rank=11 (the J-pair-J cell, 34,272 hands = 0.57% of grid) AND DS-bot achievable with both J's in bot. Setting: both J's go to BOT; pick 2 singletons (lowest-rank pair available such that the bot's 4-card suit pattern is 2+2 = DS); TOP = lowest of remaining 3 singletons; MID = the other 2. **Lift: +$6/1000h whole-grid full + $0 prefix (unchanged — Rule 11 fires on 0 prefix hands; J-pair-J has zero prefix coverage).** v41 → v42 score: $2,769 → $2,763 full. pct_opt: 41.91% → 41.93% full. Origin: Drill A's per-pair-rank A5−A2 breakdown (Session 45) found a sharp positive flip at P=J (+$2,975 vs negative at P=2..T). Drill D (Session 46, focused J-pair-J) confirmed via the apples-to-apples comparison A5−A1 = +$1,004/1000h, and v41 vs A5-best = +$3,769/1000h (the largest cross-class override at J-pair-J). v41 picks A5 0% of fired hands. Rule 11 captures ~56% of A5's oracle ceiling — heuristic-sharpening queued. Cumulative v39 → v42: −$83 full / −$91 prefix. Rule 11 is the first **single-cell** rule of the project (vs prior Rules 1-10 which all had broader populations).) (Earlier: Session 45 — **Rule 10 v3 ships in production as v41**: same trigger + gate as v40b (cat=pair, max≤J, P≤6 OR P==max), but with **suit-aware bot construction** — pick the TOP-candidate singleton such that the remaining 4 form a DS bot when achievable; fall back to v40b's "TOP = lowest singleton" otherwise. **Lift: +$29/1000h whole-grid (full N=200) + +$54/1000h whole-grid (prefix N=1000)**, both grids strongly positive with no per-category regression. v40b → v41 score: $2,798 → $2,769 full, $1,670 → $1,616 prefix. pct_opt: 41.48% → 41.91% full / 50.64% → 51.81% prefix. Mechanism: keeping pair-in-mid AND picking singletons that yield a DS bot is +$2,756/1000h within-hand on the 47.8% of J-low pair hands where DS is achievable without breaking the pair (Drill A's A1−A2). Drill A also confirmed **pair structure dominates suit structure universally** — breaking the pair to enable DS-bot is catastrophic (A3−A2 = −$10,304/1000h). Drill B (J-low two_pair) confirmed the same answer with even larger margins (B3−B2 = −$9,030, B7−B2 = −$23,165); within-class B1−B2 = +$1,864 is a sister Rule 11+ candidate. Drill C (S44 carryover) showed DS one-gap-4 ≥ DS run-4 does NOT robustly generalize across categories — sign flips by category. Earlier Session 43 ship (v40b, +$48 full / +$37 prefix) and Session 42 overnight ship (v39, Rule 9 a/b/c) cumulate to v39 → v41 = −$77 full / −$91 prefix.) (Earlier: Session 43 — **Rule 10 (J-low single-pair defensive, GATED variant) ships in production** as v40b — the FIRST defensive rule of the project. Trigger: pair hands with max card ≤ J AND (pair_rank ≤ 6 OR pair_rank == max_rank). Setting: TOP = lowest singleton, MID = the pair, BOT = 4 highest non-pair singletons. **Lift: +$48/1000h whole-grid (full N=200) + +$37/1000h whole-grid (prefix N=1000)** — both grids strongly positive. **Largest single-rule full-grid lift since v33's Rule 6 (Session 37, +$113/1000h)**. The simple ungated variant (v40) ships +$23 full / +$37 prefix and is retained as sister artifact for human-memorization fork. The gate adds one condition that doubles the lift by excluding the per-cell regression zone (pair_rank ∈ (max-4, max-1), e.g., 99 on J-high). Mechanism: the **weak-hand top inversion** — when the highest card cannot reliably win the top tier (top wins only 1 point/board vs mid's 2 and bot's 3), dumping the LOWEST card on top costs less than the gain in bot+mid equity from upgrading kicker strength. Discovered in `drill_low_pair_J_high_defense.py`. Other Session 43 findings: Q1 (A-high "always Ace on top") confirmed — v3 already at 96% optimality, no rule needed; Q2 (K/Q-high "break broadway for 4-flush bot") FAILED — every variant regressed $10-27/1000h; Q4 (J-low two_pair defensive re-examination) confirmed Session 42's "two_pair is ML territory" verdict (all 6 deterministic candidates regress); Q5 (J-high no-pair top=lo) deferred — works on T-low (+$8 full only) but regresses on J-high; high_only has zero prefix coverage so both-grid gate inapplicable.)

---

# Part 1 — Strategy Evolution

This section is APPEND-ONLY. Every entry is a snapshot of what was true at the
end of that session. Reading top-to-bottom gives you the full history of
how the strategy got to where it is.

## Pre-mining baseline (v3 / v8 / v8_hybrid)

**Before any pattern mining**, the strategy was a hand-coded chain:
- `strategy_v3` (`encode_rules.py`) handled all categories with a single
  routine: highest pair to mid, search for best top, remainder to bot.
- `strategy_v7_regression` (a DT trained on the OLD 4-profile mixture)
  handled three_pair / quads / composite via learned splits.
- `strategy_v8_hybrid` combined v3 (for high_only and pair) with v7 (for
  everything else). This was the production strategy through Session 24.

**Score: $3,153/1000h on the realistic mixture (full grid, N=200).**
That's the baseline every later improvement is measured against.

The v3 chain implicitly encodes "KK/AA → mid" (both pair cards stay
together; top searches over remaining singletons → naturally picks the
A on top when present). This was not yet documented as a rule — it
becomes Rule 4 in Session 28.

## Sessions 25–26: Rule mining sprint (Rules 1, 2, 3 discovered)

The first wave of pattern mining against the new realistic-mixture
Oracle Grid produced three numbered rules:

- **Rule 1 — Single pair: pair-to-bot for double-suited.**
  Discovered via `strategy_v9_pair_to_bot_ds.py` mining. Refined to v9.1
  (tighter gates) then v9.2 (added (1,3)/(3,1) kicker patterns). Fires
  on 2.19% of hands.
  Improvement: +$24/1000h N=200 (within its niche).

- **Rule 2 — Two pairs: never split either pair.**
  `strategy_v10_two_pair_no_split.py`. Replaces v3's "split both pairs
  to bot" default. Fires on every two_pair hand (~22%).
  Improvement: +$81/1000h.

- **Rule 3 — Trips + pair: split the trips 2-and-1, keep the pair.**
  `strategy_v12_trips_pair.py`. Fires on every trips_pair hand (~3%).
  Improvement: +$10/1000h.

**Combined into `strategy_v14_combined`** (v12 → v10 → v9.2 → v8 fallback).

**Score: $3,033/1000h. Improvement: −$120 vs v8_hybrid.**

Several other mining attempts archived in this window:
- v11 (high_only Omaha-first): −$1,745, ARCHIVED.
- v13 (trips no-pair): −$172, ARCHIVED.
- v15 (high_only DS-patch): −$296, ARCHIVED.

The high_only and trips categories resisted hand-coded rules — they
became the targets for the ML approach in Session 27.

## Session 27: First ML champion — v16_dt

A regression DT trained on the full 6M oracle grid. 37 features (28
baseline + 9 hand-engineered "aug" features for pair / high_only /
two_pair routings).

- **v16_full** (depth=18, min_samples_leaf=100, **28,790 leaves**)
  trained on the full 6M grid. Wins on every category vs v14.
  **Score: $2,464/1000h. Improvement: −$569 vs v14, −$689 vs v8.**

A failed sibling (v16_prefix, trained on the 500K canonical-id prefix)
scored $8,493/1000h and was archived. The lesson: canonical-id ordering
is highly non-uniform in hand strength; never train on a canonical-id
prefix subset. Sample uniformly at random instead.

## Session 28: Distillation, Rule 4, v18 capacity

**Distillation of v16's tree.** Walked all 6M hands through v16's
tree, computed population-weighted MSE reduction at every internal
node. Top finding: `n_broadway` alone explains 44.9% of total feature
importance. The 9 hand-engineered "aug" features collectively
contribute <0.4% — the DT solves the problem almost entirely with raw
body-strength features.

**Rule 4 added — Premium pair (KK or AA) → keep pair in mid.**
v3 / v8 / v16 all already converge on this play. Rule 4 formalizes it
for human memorization. No code change. Fires on 7.17% of hands.

**v17 attempt (rules-then-DT chain) ARCHIVED.** Wrapping
v9.2/v10/v12 in front of v16 as a "use rules where they fire, DT for
everything else" hybrid LOSES by $369/1000h on the full grid. v10 and
v12 are inferior to v16 on their own categories ($1,366 worse on
two_pair, $2,979 worse on trips_pair). Hand-coded rules optimized
against the OLD 4-profile mixture cannot beat a DT trained on the
realistic-mixture grid.

**v18 ships.** Same 37 features as v16, more capacity (depth=22,
min_samples_leaf=50, **60,651 leaves** — 2.1× v16). Trained via a new
`train_v18_dt.py` that reads the cached parquet feature tables — total
training cycle drops from ~25min to ~5min.
**Score: $2,306/1000h. Improvement: −$158 vs v16, validated on prefix
(+$129 vs v16).**

The prefix grid (500K hands × N=1000) becomes the new
"overfitting tripwire" — any future ML candidate must improve on
both the noisy full grid and the cleaner prefix.

## Session 29: Capacity sweep + v19 archived

**Capacity sweep continued.** Two more steps from v18's baseline:
- **v18b** (depth=24, ml=30, **96,409 leaves**):
  $2,217 / $1,343 (full / prefix). +$89 / +$135 vs v18.
- **v18c** (depth=26, ml=20, **124,902 leaves**):
  $2,172 / $1,261. +$45 / +$82 vs v18b.

Diminishing-but-positive marginal returns on both grids. v18c ships as
the new champion.
**v18c improvement: −$292 vs v16, −$345 vs v16 on prefix.**

**v19 attempted — suited-broadway aug features.** The Session 28
distillation showed the DT can't represent "two cards of the same suit
with one or both being broadway." Built 6 new features
(`n_suited_pairs_total`, `max_suited_pair_high_rank`,
`max_suited_pair_low_rank`, `has_suited_broadway_pair`,
`has_suited_premium_pair`, `n_broadway_in_largest_suit`) computed for
ALL 6M hands without category gating.

v19 (43 features, depth=22, ml=50, 73K leaves):
- Full grid: +$57/1000h vs v18 ✓
- **Prefix: −$16/1000h vs v18 ✗** — FAILS the prefix tripwire.
- Pair-category prefix regression (+$36/1000h on 215K hands) is the
  smoking gun: the new features fit N=200 noise on hands they
  shouldn't matter for.

**v19 ARCHIVED.** The prefix tripwire just paid off concretely —
without it, v19's positive full-grid grade would have shipped a
slightly-overfit model. The features were real signal in the wrong
container.

## Session 30: Gated suited features + v20 (current champion)

**Diagnosis of v19 failure.** The 6 ungated suited features fired
across all hand categories, giving the DT permission to make small
spurious splits in the pair / two_pair / trips populations. Fix:
**gate the features to high_only hands only**.

**`suited_aug_features_gated.py`** mirrors the existing
`high_only_aug_features.py` pattern — returns `(0, 0, 0, 0, 0, 0)` for
any hand with `n_pairs/n_trips/n_quads ≥ 1`. The features only fire on
the 1.23M high_only canonical hands (20.4% of the population).

**Capacity sweep extended further:**
- **v18d** (depth=28, ml=10, **193,365 leaves**): $2,108 / $1,145.
  +$64 / +$117 vs v18c. (Notably, the prefix gain went UP from
  v18b→v18c's $82 — diminishing returns isn't strictly monotonic.)
- **v18e** (depth=30, ml=5, **274,446 leaves**): $2,066 / $1,082.
  +$42 / +$63 vs v18d.

**v19_gated** (gated features, depth=28, ml=10, 216K leaves):
- Full grid: +$73 vs v18d (high_only category drops $356).
- Prefix: tied exactly ($0 change — gated features fire on zero
  prefix hands by design).

**v20 ships** — the combination of v18e capacity (depth=30, ml=5)
with the gated suited features (43 features total, **307,939 leaves**).
- Full grid: +$84 vs v18e. ONLY high_only category changes ($3,307 →
  $2,894, a $413 gain). Every other category is bit-identical to v18e
  — clean controlled experiment.
- Prefix: tied exactly with v18e ($1,082 / $1,082).

**Score: $1,982/1000h on full grid. Improvement: −$482 vs v16, −$1,051 vs v14.**

**The gating pattern is now the template** for all future aug families:
fire only in the targeted hand category, leave others bit-identical,
prefix tripwire passes trivially. This is the single biggest
methodology lesson of Sessions 28-30.

## Session 31: Two ships (v23 trips_pair, v24 composite); v20b archived; Rule 5 rejected

This was an "all 4 targets" sprint per the user's request: distill v20,
new gated aug families, composite deep-dive, v20b capacity step.

**v20b at depth=32 (capacity probe).** Bit-identical to v20 (same
307,939 leaves). `min_samples_leaf=5` is the binding constraint at
depth=30; pushing to depth=32 changes nothing. **ARCHIVED.** The
trainer-flag-level capacity sweep is now CLOSED — future gains are
feature-engineering, not raw capacity.

**Distill v20 → Rule 5 candidates → REJECTED.** Walked v20's tree on
the high_only category. Top splits all standard features (n_broadway,
third_rank, pair_high_rank); the 6 gated suited features cluster around
msphr thresholds 5.5–8.5 in deep subtrees. Two candidate Rule 5 variants
(loose `msphr ≥ 9` and tight `msphr ≥ 11 AND msplr ≥ 9`) tested
head-to-head against v14_combined:
- **v21 = v14 + Rule 5 (loose):** $3,713/1000h, **−$680 vs v14.**
- **v22 = v14 + Rule 5 (tight):** $3,506/1000h, **−$473 vs v14.**

Both **REJECTED**. Both fire on ~8× more high_only hands than the DT's
selective routing actually wants. The DT's gated splits use 4+ rank
thresholds combined with `n_low`/`n_broadway` that no single AND-rule
can replicate. **For the human chain: stop at Rule 4. For computational
play: use the DT champion.**

**v23 ships — gated trips_pair aug family.** 6 new features
(`tp_trip_rank_g`, `tp_pair_rank_g`, `tp_high_singleton_rank_g`,
`tp_low_singleton_rank_g`, `tp_singletons_suited_g`,
`tp_pair_routing_is_ds_g`), zeros for non-trips_pair. 49 features total
(43 v20 + 6 trips_pair-gated), depth=30 ml=5, **314,705 leaves**.
- Full grid: $1,977/1000h. **+$5 vs v20** (trips_pair drops $1,608 → $1,447, **−$161**).
- Prefix: $1,073/1000h. **+$9 vs v20** (trips_pair drops $1,657 → $1,478, **−$179**).
- Every other category bit-identical or within N=200 noise. 2nd clean instance of the gating template after v20→high_only.

**v24 ships — gated composite aug family.** 4 new features
(`comp_archetype_g`, `comp_lower_trip_rank_g`, `comp_singleton_rank_g`,
`comp_higher_pair_rank_g`), zeros for non-composite. Composite is rare
(0.245% of population) but the largest per-hand bleed at $2,080 on v23.
The `composite_v20_residual` diagnostic identified 4 archetype clusters
(trips_two_pair, two_trips, quads_pair, quads_trip) where v20 frequently
SPLITS the dominant trips/quads instead of keeping them together on bot.
The 4 gated features expose archetype + the unique-info "lower_trip_rank"
signal. 53 features total (49 v23 + 4 composite-gated), depth=30 ml=5,
**314,759 leaves** (only +54 over v23).
- Full grid: $1,977/1000h. **+$1 vs v23** at the headline (composite drops $2,080 → $1,864, **−$216**).
- Prefix: $1,072/1000h. **+$1 vs v23** (composite drops $1,811 → $1,610, **−$201**).
- Headline is at the noise floor because composite is 0.245% of population, but per-category effect is unambiguous. 3rd clean instance of the gating template.

**Score: v23 $1,977/1000h, v24 $1,977/1000h. v24 is the new ML champion.
Improvement: −$487 vs v16, −$1,056 vs v14.**

**Methodology lesson — the gating template is now proven across THREE
categories** (high_only, trips_pair, composite). Each upgrade lifted
ONLY its targeted category and kept every other category bit-identical
or within N=200 noise. Population shares span 0.245% to 20.4%. Future
aug families should follow the same shape: 4-6 archetype-specific
features, zero for off-archetype hands, persisted by canonical_id,
trained on top of the current champion.

**Methodology lesson — distilled rules need head-to-head validation
BEFORE shipping.** Both Rule 5 variants looked good in distillation but
lost to v14 by hundreds of $/1000h. Naive rule extraction is ~8×
over-eager relative to the DT's selective routing.

## Session 32: v25 ships (gated pair) — 4th gating success, largest population share

**Pair audit — answers the diagnostic question from Session 31's
resume prompt.** The 3 pre-existing pair aug features
(`default_bot_is_ds`, `n_top_choices_yielding_ds_bot`,
`pair_to_bot_alt_is_ds`) were verified STRICTLY zero on every non-pair
canonical row. They've been category-gated since Session 17 — the
naming inconsistency (no `_g` suffix) was misleading but harmless. They
are NOT the v19 leakage pattern.

Path forked: option B (design 6-feature gated EXTENSION alongside the
existing 3 booleans), not option A (rebuild from scratch).

**v25 ships — 6 new pair-gated features.** The existing 3 features
answered "is the bot DS under this routing?" (booleans / 0-3 buckets).
The new 6 add rank- and mid-quality signal:
- `pair_kickers_in_pair_suit_max_g` (0..5)
- `pair_kickers_in_pair_suit_min_g` (0..5)
- `pair_default_top_rank_g` (0..14)
- `pair_alt_top_rank_g` (0..14)
- `pair_alt_mid_suited_g` (0/1)
- `pair_alt_mid_n_broadway_g` (0..2)

59 features total (53 v24 + 6 pair-gated), depth=30 ml=5,
**390,626 leaves** (+75K vs v24 — biggest single-ship leaf delta since
v20). Prefix tripwire confirmed the new partitioning is structural, not
noise-fitting.

- Full grid: $1,929/1000h. **−$47 vs v24** (pair drops $1,873 → $1,771, **−$102**).
- Prefix: $1,054/1000h. **−$18 vs v24** (pair drops $929 → $888, **−$41**).
- Every other category bit-identical or within N=200 noise. pct_optimal
  jumps 47.89% → 48.43% (full) and 59.48% → 59.80% (prefix). Pair-only
  pct_opt: 52.8% → 53.9% (full), 62.8% → 63.5% (prefix).

**Score: $1,929/1000h on full grid. Improvement: −$535 vs v16, −$1,104 vs v14.**

**Methodology lesson — population share matters more than per-hand
bleed for picking next targets.** Pair has only $1,873/1000h regret
(modest) but 46.6% population share, so its absolute share is $873/1000h
— biggest residual. v25's $102 per-category gain × 46.6% = $47 headline,
the largest gating gain since v20. Compare composite (0.245% × $216 =
$0.5/1000h headline despite a comparable per-category effect).

**Methodology lesson — leakage check is a one-shot pyarrow read.**
The pair audit was a single ~5-second pandas script (count nonzero rows
by category for each suspect feature). Should be the first step of every
audit going forward; 3 sessions of "is this gated?" diagnostics
collapses into one query.

## Session 33: v26 ships (gated two_pair) — 5th gating success, biggest per-category gain since v20

**Two_pair audit (same pattern as Session 32).** The 3 pre-existing
two_pair aug features (`default_bot_is_ds_tp`,
`n_routings_yielding_ds_bot_tp`, `swap_high_pair_to_bot_ds_compatible`)
were verified strictly zero on every non-two_pair canonical row.
Already gated since Session 19. NOT v19 leakage. Path: option B (extend
with 6 new features alongside the existing 3).

**v26 ships — 6 new two_pair-gated features.** The Session 19 mining
notes had flagged "high-pair-on-mid (DT default) vs high-pair-on-bot
(BR swap)" as the dominant miss pattern; the existing
`n_routings_yielding_ds_bot_tp` lumps Layout B and Layout C together.
The 6 new features SPLIT B from C and add rank/suit info:
- `t2p_layout_a_bot_is_ds_g` (0/1) — Layout A bot DS, fires when both
  pairs share BOTH suits exactly (~19% of two_pair hands)
- `t2p_n_layout_b_routings_ds_g` (0..3) — Layout B subset of total DS
  routings (the long-flagged distinction)
- `t2p_top_singleton_rank_g` (0..14)
- `t2p_low_singleton_rank_g` (0..14) — surprisingly strong, #12 in
  feature importance
- `t2p_singletons_max_suit_count_g` (1..3)
- `t2p_high_pair_rank_g` (0..14)

65 features total (59 v25 + 6 two_pair-gated), depth=30 ml=5,
**459,209 leaves** (+68K vs v25, second-largest single-ship leaf delta
after v25's +75K).

- Full grid: $1,859/1000h. **−$70 vs v25** (two_pair drops $1,458 → $1,145, **−$313**).
- Prefix: $1,002/1000h. **−$52 vs v25** (two_pair drops $1,050 → $924, **−$126**).
- Every other category bit-identical or within N=200 noise. pct_optimal
  jumps 48.43% → 49.21% (full) and 59.80% → 60.80% (prefix). Two_pair
  pct_opt: 57.3% → 60.8% (full), 58.8% → 61.3% (prefix).
- **Largest per-category gain since v20→high_only ($413).**

**Score: $1,859/1000h on full grid. Improvement: −$605 vs v16, −$1,174 vs v14.**

**Bug recovery mid-session — naming collision.** First v26 attempt named
the new features `tp_*`, colliding with the trips_pair gated family's
prefix. Both `tp_low_singleton_rank_g` AND `tp_top_singleton_rank_g`
existed in two different feature definitions. Training succeeded by
column index, but inference's `feature_columns.index(c)` returned the
FIRST occurrence for both name lookups — the v26 strategy wrote
two_pair values into the trips_pair column index and left the actual
two_pair column uninitialized. **Buggy v26 output: $3,746/1000h on
prefix** ($2,692 catastrophic regression with two_pair AND trips_pair
both blown up). Diagnosed in 1 round-trip from the cross-category
blowup pattern; renamed all 6 features to `t2p_*`, re-persisted parquet
(38s), retrained (256s), regraded — clean win as documented above.

**Methodology lesson — each gated family must use a UNIQUE prefix.**
Existing claims: `_g` suffix variants (suited), `tp_*_g` (trips_pair),
`comp_*_g` (composite), `pair_*_g` (pair), `t2p_*_g` (two_pair). New
families must check existing prefixes BEFORE picking a name. Cross-
category blowup (regressing both the targeted category AND another) is
the diagnostic signature for column-name collisions.

**Methodology lesson — the gating template is now proven across FIVE
categories** (high_only, trips_pair, composite, pair, two_pair).
Population shares span 0.245% (composite) to 46.6% (pair). Per-category
gains: high_only $413, two_pair $313, composite $216, trips_pair $161,
pair $102. The template works at every scale tried; the question is no
longer "does it work?" but "which category next, and what features?".

## Session 34: v27 ships (gated high_only-direct) — 6th gating success but smallest per-category gain to date; KK/AA + KKK/AAA boundary probes confirm Rule 4

**Diagnostic-first design.** Session opened by running the
`distill_v26_high_only.py` diagnostic that had been drafted but never
run in Session 33. Walked all 6M hands through v26's 459K-leaf tree
restricted to the 1.23M high_only hands. Top 30 miss leaves all
shared the path `n_broadway ∈ [3,4]` AND `n_broadway_in_largest_suit_g ≥ 2` —
suited-broadway high_only hands. Stratifying these leaves by the
candidate feature `n_broadway_in_2nd_suit` produced striking
within-leaf separations: 9/10 top miss leaves showed ≥0.15 EV split,
with the strongest (leaf 578474, n_ho=420) showing **+0.414 EV
within-leaf separation** by knowing this single bit. This was the
strongest pre-train signal of any session.

**v27 ships — 4 new high_only-gated features.** Naming used the new
unique prefix `ho_*_g` (Session 33 collision lesson upheld):

- `ho_n_broadway_in_2nd_suit_g` (0..3) — primary diagnostic signal
- `ho_n_broadway_in_3rd_suit_g` (0..3) — completes per-suit broadway distribution
- `ho_connectivity_high_g` (0..5) — longest run T-A
- `ho_n_broadway_pairs_adj_g` (0..4) — count of {AK, KQ, QJ, JT}

69 features total (65 v26 + 4 high_only-gated), depth=30 ml=5,
**460,375 leaves** (only **+1,166 vs v26** — the smallest single-ship
leaf delta of any gating-template ship; compare v25→v26 +68K, v24→v25 +76K).

- Full grid: $1,853/1000h. **−$6 vs v26** (high_only drops $2,894 → $2,863, **−$31**).
- Prefix: $1,002/1000h. **$0 vs v26** — but the prefix grid contains **zero high_only hands** (canonical-id 0..500K covers only categories with at least one pair). The "$0" is structural, not informative.
- Every other category bit-identical. pct_optimal moves 49.21% → 49.27% (full, +0.06pp). High_only-only pct_opt: 27.7% → 28.0% (+0.3pp).

**Score: $1,853/1000h on full grid. Improvement: −$611 vs v16, −$1,180 vs v14.**

**Diagnostic-to-headline conversion ratio: ~10%.** The within-leaf 0.34
EV separation projected to ~$3,400/1000h within-leaf — but realized
only $31/1000h within-category and $6/1000h whole-grid. The signal is
concentrated in a small fraction of hands within each miss leaf, not
the full leaf population. **0/4 new features placed in v27's top-25
importance** (vs 3/6 t2p_* in v26 and 5/6 pair_* in v25) — leading
indicator of the marginal headline result.

**KKK/AAA routing probe (`probe_trips_kkk_aaa_routing.py`):** Ran
fresh in Session 34. 50,490 hands (0.84% of grid). **A_paired_mid
(keep 2 of 3 trip-rank in mid as a pair) is BR-optimal on 79.18% of
KKK/AAA hands** — confirms the Rule 4 default extends naturally to
trips of K/A. AAA→A wins 80.1% vs B; KKK→A wins 70.9% (KKK splits to
DS-bot more often because AAA's mid-pair is structurally stronger).
B_split_bot_DS is geometrically available on 68.6% of hands; when
available, strictly beats A on 24.3% with mean +0.363 EV gain. Upper
bound: $5/1000h whole-grid if rule perfectly switches. CSV at
`data/kkk_aaa_routing_probe.csv`.

**KK/AA Rule-4 boundary probe (`probe_kk_aa_ds_bot_vs_mid.py`):**
Pulled headline from existing CSV (probe ran in Session 33-34
staging). 430,848 non-trips KK/AA hands. **Rule 4 (mid-pair) is BR-
optimal on 72.76%.** DS-bot routing geometrically available on 55.1%;
when available, strictly beats mid-pair on 28.08% with mean +0.379 EV
gain. Upper bound: $42/1000h whole-grid if rule perfectly switches —
**comparable magnitude to v23/v24/v27 ships and the largest remaining
clean rule-extraction candidate**.

**Methodology lesson — within-leaf EV separation does NOT scale
linearly to ML headline gain.** Conversion ratio observed: ~10%.
Reasons: (a) most hands in a "miss leaf" are tight already; the gain
concentrates in the subset where the new feature actually flips the
pick; (b) DT regression criterion may partition before reaching the
within-leaf signal threshold; (c) features can correlate strongly
with existing ones — `ho_connectivity_high_g` overlaps with
`n_broadway`+`n_low`+`connectivity`. For future high-share
categories, validate the diagnostic with a **single-feature DT**
before committing to a 4-6 feature family.

**Methodology lesson — top-25 feature importance is a pre-grade
tripwire.** v25 had 5/6 new features in top-25 (gained $47 / $18);
v26 had 3/6 in top-25 (gained $70 / $52); v27 had 0/4 in top-25
(gained $6 / $0). The placement count weakly predicts headline gain
magnitude. Future families with 0/N placement should be archived
without grading.

**Methodology lesson — prefix N=1000 grid has zero high_only hands.**
Future high_only-targeting models can only be validated on the full
grid. The canonical-id 0..500K subset contains only categories with
at least one pair (sums to exactly 500,000 across pair, two_pair,
trips, trips_pair, three_pair, quads, composite). This was always
true but had not been observed to limit a grade until v27.

**Methodology lesson — Rule 4 holds for KK, AA, KKK, and AAA.** Both
boundary probes confirm "mid-as-pair" as the dominant routing on the
realistic mixture (72.76% / 79.18% / 83.84% optimal across the three
subsets). The DS-bot exception is +EV ~24-28% of geometrically-
eligible hands but has historically been hard to extract as a clean
rule (v21 / v22 attempts were ~8× over-eager). For human play: stop
at Rule 4. For computational play: use v27 (or v26 — they're nearly
identical on the KK/AA and KKK/AAA subsets since neither was the
target of v27's high_only features).

## Session 35: v29 ships (gated pair_r4) — 7th gating success and largest diagnostic-driven win

**The chain:** This session was driven entirely by user intuition + diagnostic-first design. The trail:

1. **User question (Session 34 close):** "What about KK/AA where leftover bot is rainbow? Shouldn't we move KK/AA to bot for DS?" Per-hand probe of K♠K♦3♠5♦9♥T♣J♠ confirmed: Rule 4 picks rainbow bot for +1.225 EV; oracle BR is DS-bot for +3.025 EV (Δ = $18,000/1000h on this single hand).

2. **Rule 5 (Rainbow override) shipped to STRATEGY_GUIDE** as the user-intuited human rule (Decision 063). v28 = v14 + Rule 5 = $3,032/1000h on full grid, +$1 vs v14_combined. **First successful Rule 5 in project history** (v21/v22 lost $473-$680). Tight structural trigger (KK/AA + Rule-4-bot rainbow + DS feasibility) fires on 0.27% of all hands. Per-hand wins on the firing subset are dramatic ($15-18K/1000h on canonical examples).

3. **`distill_v27_pair.py` ran the KK/AA capture analysis** to quantify how much of the boundary-probe $42/1000h upper bound v27 already captures. Surprising finding: **v27 is $20/1000h whole-grid WORSE than Rule 4 alone on KK/AA** (regret 0.1236 vs 0.0949 EV/hand). v27 picks Rule-4 84.6% of KK/AA, but the 15.4% non-Rule-4 picks are systematically incorrect — overgeneralizing v25's pair-gated features. Total v27→oracle gap on KK/AA: $63/1000h whole-grid.

4. **The missing signal: suit profile of Rule-4's resulting bot.** v25's existing `pair_*_g` features encode kickers-in-pair-suit and alt-routing rank quality but NOT the SHAPE of the leftover bot. The rainbow trigger that drives Rule 5 is the same axis the ML champion was missing.

**v29 ships — 4 new pair-gated v2 features** (prefix `pair_r4_*_g` to avoid collision with v25's `pair_*_g`):

- `pair_r4_bot_suit_profile_g` (0..5) — encoded Rule-4 bot suit shape. THE missing signal.
- `pair_r4_bot_max_rank_g` (0..14) — highest rank in Rule-4 bot
- `pair_r4_n_broadway_kickers_g` (0..5) — count of T-A among 5 non-pair cards
- `pair_r4_n_low_kickers_g` (0..5) — count of 2-5 among 5 non-pair cards

73 features total (69 v27 + 4 pair_r4-gated), depth=30 ml=5,
**486,342 leaves** (+25,967 vs v27, +5.6% capacity expansion).
3 of 4 new features placed in top-30 importance (#17, #20, #23) —
strong pre-grade tripwire signal.

- Full grid: $1,807/1000h. **−$46 vs v27** (pair drops $1,771 → $1,674, **−$97 within-pair**).
- Prefix: $965/1000h. **−$37 vs v27** (pair drops $888 → $803, **−$85 within-pair**).
- Every other category bit-identical or within N=200 noise. pct_optimal moves 49.27% → 49.80% (full, +0.53 pp) and 60.80% → 61.32% (prefix, +0.52 pp).
- Full:prefix ratio 1.24:1 — well-calibrated, low overfitting risk.

**Score: $1,807/1000h on full grid. Improvement: −$657 vs v16, −$1,226 vs v14.**

**Methodology lesson — diagnostic-first design produces 7.7× better headline-per-feature than speculative design.** v27 (4 speculative high_only candidates) gained $6/1000h. v29 (4 diagnostic-driven pair features) gained $46/1000h. Same trainer config, same gating template. The difference: v29's diagnostic explicitly compared v27 vs Rule 4 alone and discovered v27 was *losing* — that's the kind of finding that prescribes feature design rather than just suggesting candidates.

**Methodology lesson — diagnostic should identify a competing baseline.** Future feature engineering should explicitly ask: "What rule-based or simpler-ML alternative am I beating, and where is the ML champion underperforming it?" That comparison surfaces the *missing signal* directly. Within-leaf separation (Session-34 high_only) is necessary but not sufficient; you need the baseline comparison to know whether the signal will translate to ML capacity.

**Methodology lesson — user intuition correlates with ML weak points.** The user-flagged hand pattern (KK/AA + rainbow Rule-4-bot) revealed a $63/1000h whole-grid weakness that v27's headline metrics never surfaced. When a domain expert says "this can't be right" at the table, treat that as a high-prior research signal.

**Methodology lesson — categories can absorb multiple gating-template iterations.** Pair has now seen TWO independent ships:
- v25: 6 features encoding kickers-in-pair-suit + alt-routing quality (-$102 within-pair)
- v29: 4 features encoding Rule-4-bot suit profile + body-card distribution (-$97 within-pair)

Total pair improvement since v18e: **−$199/1000h within-pair**. Each iteration targeted a distinct signal axis; neither superseded the other (v29 BUILDS ON v25, doesn't replace).

## Session 36: v30 ships (gated trips, 8th gating) + v31 ships (capacity expansion, 2nd-largest ship in project history)

This session produced TWO ships back-to-back: a gating-template ship (v30, trips) followed overnight by a CAPACITY-ONLY ship (v31). The pair sets a methodological precedent worth recording in detail.

**Part A — v29 KK/AA round-2 audit + v30 trips ship.**

The session opened with `distill_v29_pair.py` running the round-2 KK/AA audit on the v29 champion. v29 closed only $7/1000h of v27's $14 KK/AA Rule-4 deficit. Stratification by Rule-4-bot suit profile revealed:

| Rule-4-bot profile | KK/AA share | v29 | Rule-4 alone | Oracle | v29-oracle gap |
|---|---:|---:|---:|---:|---:|
| rainbow (1+1+1+1)        |  8.8% | $12.0 | $15.4 | $3.8  | **$8.2** |
| **single-suited (2+1+1)** | **52.9%** | **$51.0** | **$38.1** | **$14.1** | **$36.9** |
| double-suited (2+2)      | 15.4% | $3.6 | $2.0 | $1.0 | $2.6 |
| three-of-suit (3+1)      | 20.6% | $14.4 | $11.9 | $6.3 | $8.0 |
| four-of-suit             |  2.2% | $1.0 | $0.8 | $0.7 | $0.3 |

v29's `pair_r4_bot_suit_profile_g` (categorical 0..5) treats single-suited as one bucket — but the single-suited stratum (52.9% of KK/AA, 3.7% of grid) needs FINER encoding (which suit, dominant-suit max rank, pair-suit alignment). Rainbow is captured well because Rule 5 fires there; single-suited is the dominant residual leak. **Deferred** to v31a candidate (overnight cascade).

The session pivoted to a fresh diagnostic: `distill_v29_trips.py`. The trips category (5.46% of grid, $109/1000h whole-grid contribution) had been entirely untouched by gating. The diagnostic produced the **largest gap-to-baseline ever measured in this project**:

| Strategy | Within-trips regret | Whole-grid contribution |
|---|---:|---:|
| Always A_paired_mid (mid is trip pair)  | $24/1000h | $24/1000h |
| Always B_paired_bot_any                 | $625/1000h | $341/1000h |
| Always C_top_trip                       | $1,107/1000h | $605/1000h |
| Oracle (max over A∪B_any∪C)             | $0 (perfect routing exists) | $0 |
| **v29 actual**                          | **$1,997/1000h** | **$109** |

**v29 was $85/1000h whole-grid WORSE than always-A_paired_mid** — the analog of "v27 was $20 worse than Rule 4 on KK/AA" but 4× larger. v29 picks A on 79.9% of trips, B on 4.8%, C on 15.3%; the 20.1% non-A picks are systematically wrong, especially on low-rank trips (2-9 each leak $7-8/rank-share, totaling ~$60 of the $85 deficit).

**v30 ships — 6 new trips-gated features** (prefix `trips_*_g`, distinct from v23's `tp_*_g` which is trips_pair):

- `trips_b_ds_avail_g` (0/1) — is B-DS routing structurally feasible (≥1 kicker in each of 2 trip-suits)?
- `trips_b_ds_n_routings_g` (0..3) — count of {a,b} trip-suit pairs admitting B-DS
- `trips_kickers_max_suit_count_g` (0..4) — max suit count among 4 kickers
- `trips_kickers_max_rank_g` (0..14) — highest kicker rank
- `trips_n_broadway_kickers_g` (0..4) — count of T-A among kickers
- `trips_n_low_kickers_g` (0..4) — count of 2-5 among kickers

79 features total (73 v29 + 6 trips-gated), depth=30 ml=5, **493,057 leaves** (+6,715 vs v29, +1.4% capacity expansion). **0/6 new features placed in top-30 importance** — tripwire predicted small headline.

- Full grid: $1,794/1000h. **−$13 vs v29** (trips drops $1,997 → $1,758, **−$239 within-trips**).
- Prefix: $951/1000h. **−$15 vs v29** (trips drops $1,763 → $1,474, **−$289 within-trips**).
- All other categories bit-identical or within N=200 noise. pct_optimal moves 49.80% → 49.98% (full, +0.18 pp) and 61.32% → 61.53% (prefix, +0.21 pp).
- **Full:prefix ratio 0.87:1** — first ship where prefix gain exceeds full-grid gain. Trips routing has cleaner answers under higher-fidelity grading.

**Part B — overnight v31 cascade: capacity-only retrain produces second-largest ship.**

Three v31 candidates ran sequentially (~80 min total) via `analysis/scripts/overnight_v31_cascade.sh`:

| Candidate | Approach | Full Δ vs v30 | Prefix Δ vs v30 | Tripwire | Leaves |
|---|---|---:|---:|---:|---:|
| v31a | pair_r4v3 KK/AA-tight (4 features) | +$6 | $0 | 0/4 in top-30 | 500,722 (+8K) |
| v31b | trips_v2 round 2 (4 features for C_top + finer A/B) | +$15 | +$13 | 0/4 in top-30 | 507,692 (+15K) |
| **v31 (was v31c)** | **v30 features at depth=32 ml=3** | **+$58** | **+$29** | n/a (no new features) | **699,773 (+207K)** |

**v31 ships — depth=32, min_samples_leaf=3, 79 features (identical to v30), 699,773 leaves** (+206,716 vs v30 = +42% capacity expansion, the largest single-ship leaf delta in project history).

Per-category at full grid — **ALL 8 categories improve** (no isolated-category gating signature; capacity helps across the board):

| Category | v30 | v31 | Δ |
|---|---:|---:|---:|
| high_only  | $2,862 | $2,816 | −$46 |
| pair       | $1,674 | $1,639 | −$35 |
| **two_pair** | $1,145 | $1,037 | **−$108** |
| trips      | $1,758 | $1,732 | −$26 |
| **trips_pair** | $1,442 | $1,225 | **−$217** |
| three_pair | $1,654 | $1,639 | −$15 |
| quads      | $723   | $645   | −$78 |
| **composite** | $1,733 | $1,387 | **−$346** |

The biggest gains accrue to PREVIOUSLY-GATED categories (composite, trips_pair, two_pair). Capacity expansion lets the existing gating-template features express more structure. Previously-untouched categories (high_only, three_pair, quads) also improve, just less dramatically.

- Full grid: $1,736/1000h. **−$58 vs v30** (second-largest single ship after v26's −$70). pct_opt 49.98% → 50.92% (+0.94 pp).
- Prefix: $921/1000h. **−$29 vs v30**. pct_opt 61.53% → 62.07% (+0.54 pp).
- Full:prefix ratio 2.0:1 — at edge of overfitting territory but clean per-category structure rules out pure noise.

**Score: $1,736/1000h on full grid. Improvement: −$728 vs v16, −$1,297 vs v14.**

**Methodology lesson — when feature set grows ≥40 above last capacity-saturation test, RE-TEST capacity.** The v20 vs v20b finding (Session 31, depth=32 produced bit-identical results as depth=30 ml=5) was at 43 features with 308K leaves. That conclusion didn't generalize: at v30's 79 features and 493K leaves, depth=32 ml=3 unlocks $58/1000h of latent signal. Future ML champion sessions should default to **depth=32 ml=3** going forward, and re-test capacity (depth=34 ml=2 as the next ceiling) whenever leaf-count growth stalls below historical norms (~30K leaves per gating-template ship).

**Methodology lesson — diagnostic-first feature design and capacity expansion are orthogonal axes.** v25-v30 were 6 sequential diagnostic-first ships (each adding 4-6 features per category) totaling −$260/1000h cumulative. v31 alone (capacity-only, zero new features) ships −$58. Capacity unlocks ~22% of what the cumulative feature work had added but couldn't fully express. Future sessions should run a capacity sweep BEFORE considering more features whenever a ship has a bearish tripwire AND a leaf-count gain ≤10K — because that pattern signals "feature was added but tree couldn't express it" rather than "feature wasn't useful."

**Methodology lesson — categorical features can be too coarse, but tighter gating doesn't always help.** v31a's pair_r4v3 features were KK/AA-tight (zero outside KK/AA). The hypothesis was that v29's `pair_r4_bot_suit_profile_g` was too coarse for the single-suited stratum. The candidate shipped only +$6 full / $0 prefix. Tight gating did inject signal (within-pair −$13 on full) but the headline was modest. The KK/AA single-suited Rule-4-bot stratum remains an open optimization target ($37 below oracle) but a fundamentally different angle is needed (e.g., meta-classifier feature trained on probe data, or a sub-tree dedicated to KK/AA hands).

**Methodology lesson — "always-X" structural baselines surface Rule-N candidates.** The trips diagnostic surfaced "Always A_paired_mid" as the structural analog of Rule 4 for trips. The Session 34 KK/AA Rule-4 boundary probe surfaced Rule 5 (Rainbow override). Future sessions should systematically check whether each category has a structural always-X baseline that the human strategy could codify — even if it's already implicit in v14_combined, naming it explicitly preserves the strategy chain's coherence.

**Methodology lesson — the gating template now has 8 instances; pair has 2 iterations.** Suited (v20) / trips_pair (v23) / composite (v24) / pair v1 (v25) / two_pair (v26) / high_only (v27) / pair v2 (v29) / trips (v30). v31 is NOT a 9th gating-template instance — it's a capacity-only retrain. The template is established; the capacity dimension is the orthogonal axis going forward.

---

## Session 37: v32 ships (round-2 trips at high capacity, completing v30→v32 arc, beats v26 record); v33_rule6 is largest single rule ship in project history

This session executed the v32 hypothesis from Session 36 (stack v31b's round-2 trips features onto v31's high-capacity config) AND surfaced/codified Rule 6 — the structural analog of Rule 4 for trips, which delivers the largest single rule ship the project has ever seen.

**Part A — v32 ships (the v30→v32 ship arc).**

Session 36's overnight cascade produced two independently-positive ML candidates: v31b (trips_v2 round-2 features at depth=30 ml=5, +$15 full / +$13 prefix vs v30) and v31c → v31 (pure capacity expansion, +$58 full / +$29 prefix vs v30). They were graded as alternatives, and the cascade picked v31. But the two improvements come from orthogonal axes: **trips_v2 features add new signal in trips, while capacity expansion expresses already-encoded signal across all 8 categories.** Stacking them should deliver both gains.

v32 = 83 features (79 v30 + 4 trips_v2 round-2) at depth=32, min_samples_leaf=3. Trained at v31's high-capacity config. **731,606 leaves** (+31,833 vs v31, +4.6% capacity).

| Grid | v30 → v31 | v31 → v32 | v30 → v32 (cumulative) |
|---|---:|---:|---:|
| Full (N=200) | $1,794 → $1,736 (−$58) | $1,736 → $1,715 (**−$20**) | **−$79** |
| Prefix (N=1000) | $951 → $921 (−$29) | $921 → $904 (**−$18**) | **−$47** |

**The cumulative v30→v32 ship of $79/1000h on full grid beats v26's record of $70 to become the largest single-session ML ship in project history.**

Per-category at full grid — only trips moves vs v31 (textbook gating signature):

| Category | v30 | v31 | v32 | Δ v32 vs v31 |
|---|---:|---:|---:|---:|
| high_only  | $2,862 | $2,816 | $2,816 | $0 |
| pair       | $1,674 | $1,639 | $1,639 | $0 |
| two_pair   | $1,145 | $1,037 | $1,037 | $0 |
| **trips**  | $1,758 | $1,732 | **$1,359** | **−$373** |
| trips_pair | $1,442 | $1,225 | $1,225 | $0 |
| three_pair | $1,654 | $1,639 | $1,639 | $0 |
| quads      | $723   | $645   | $645   | $0 |
| composite  | $1,733 | $1,387 | $1,386 | −$1 |

**Score: $1,715/1000h on full grid. Improvement: −$351 vs v18e, −$1,317 vs v14_combined. v32 captures 43.5% of the v14→ceiling gap.**

Tripwire footprint for v32: 0/4 trips_v2 in top-30 (positions 55, 60, 72, 73). Bearish, matching v31b at depth=30 ml=5 which placed 0/4 yet shipped +$15. **7 ships now confirm tripwire predicts conversion rate (~10-15%), not absolute opportunity.**

**Part B — Rule 6 verification + v33_rule6 ships (the largest single rule ship in project history).**

Session 36's `distill_v29_trips.py` had identified that v29 was $85/1000h whole-grid worse than the structural baseline "Always A_paired_mid" on pure trips. Session 37 wrote `verify_rule6_v14_trips.py` to trace the same baseline against the human strategy chain (v14_combined + Rule 4 + Rule 5 = v28).

The probe surfaced three findings on a 30K pure-trips sample:

1. **v14 picks "mid is pair-of-trip-rank" (A or C variant) on only 94.3% of pure trips.** The remaining 5.43% goes to B_bot_pair_trip routings (the 3rd trip card on bot, breaking the mid-pair). 0.24% goes to other archetypes.
2. **v14's A-vs-C decision is empirically correct on the 94.3% it gets right** — equivalent to `top = max(trip_rank, max_kicker_rank)`. The bug is purely in the 5.4% B-bleed.
3. **The cleanest rule: "On pure trips, the third trip card never goes to bot."** This is "always A∪C" (mid is pair of trip-rank, top free). The oracle ceiling for this rule is **$197/1000h whole-grid over v14** — bigger than any prior rule ship combined.

**Rule 6 statement:** *"With pure trips (one rank with count 3, no other pairs/quads), mid is always 2 of the 3 trip-rank cards. The third trip card goes to top (when trip_rank > max_kicker_rank, i.e. the C variant) or to bot (otherwise, the A variant). Within the A variant, choose which trip → bot to maximize bot DS-ness."*

**v33_rule6_trips ships:**

| Grid | v28 (current human champ) | v33 | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $3,032 / 39.64% | **$2,920 / 40.68%** | **−$112 / +1.04 pp** |
| Prefix (N=1000, 500K hands) | $2,037 / 47.61% | **$1,894 / 48.81%** | **−$143 / +1.20 pp** |

The trips category alone drops $4,054 → $2,010 within-trips on the full grid (almost halved), with 19.9% → 39.0% optimal-pick rate. Probe → full agreement is essentially perfect (1% drift).

**The 56% capture of the $197 oracle ceiling** is the heuristic's limit (no peeking at oracle EVs). Override-everything beat preserve-A∪C-when-already-good ($111 vs $37 on the probe) — the heuristic's bot-DS optimization on the A variant beats v14/v8_hybrid's learned routing on average, even when both pick A.

**Methodology lesson — "always-X" structural baselines surface Rule-N candidates worth shipping.** The trips diagnostic surfaced Rule 6 worth $112-143/1000h whole-grid; the Session 34 Rule 4 boundary probe surfaced Rule 5. **Future sessions should systematically probe each category for an always-X baseline** — every category with a learned ML feature family should have its rule-chain analog tested. Candidates: high_only "always top = max-rank" (likely already true via v8_hybrid); two_pair "always split high pair to mid" (deferred); trips_pair "always pair-of-pair to mid" (probably already covered by v12 detect logic but worth verifying).

**Methodology lesson — orthogonal axis stacking works (v32 confirms).** v31's capacity expansion ($58) and v31b's trips_v2 features ($15) stacked additively to v32's $79 cumulative (with a small extra $6 from interaction). The template for future ships: **standalone diagnostic-driven feature design at v31's default depth=32 ml=3, then re-test capacity at depth=34 ml=2 if leaf-count grows substantially.**

**Methodology lesson — rule chain ships should default to override-everything within the rule's scope.** The "preserve v14 when already-A∪C" variant of Rule 6 captured only $37/1000h vs the override-everything $112. Rule heuristics should fully replace the learned strategy within their gate, not just patch its mistakes — because the heuristic's structural reasoning often beats the learned strategy's fine-grained choices.

---

## Session 38: v34_dt ships (capacity-only ml=2 retrain at v32 features); Rule 6 A-vs-C boundary probe validates the user hypothesis at the oracle but cannot be cashed via heuristic-A

This session pursued two priority targets from Session 37's wrap and surfaced one shipping result and one informative negative.

**Part A — v34_dt ships (depth=34 ml=2 capacity expansion).**

Per the Session 37 methodology rule (when feature count grows OR leaf-count grows ≥+5%, retest capacity), Session 38 retrained v32's exact 83 features at depth=34 with two `min_samples_leaf` settings:

- **v32_d34ml3 (control):** 731,611 leaves at achieved depth 33. Exactly +5 leaves vs v32's 731,606. **Result: $1,715/1000h full / $904/1000h prefix — bit-identical to v32.** This proves **ml=3 was the binding constraint, not depth=32** — the natural saturation depth at ml=3 is 33, well below the 34 cap, so depth=32 was never the bottleneck.

- **v32_d34ml2 (candidate, promoted to v34_dt):** 874,548 leaves at achieved depth 33. **+19.5% capacity over v32.** Lowering ml from 3 to 2 unlocks +142,937 more splits.

**Validation grades (full + prefix):**

| Grid | v32 | v32_d34ml3 | **v34_dt** | Δ v34 vs v32 |
|---|---:|---:|---:|---:|
| Full N=200 6.0M | $1,715 / 51.31% | $1,715 / 51.31% | **$1,681 / 52.02%** | **−$34 / +0.71pp** |
| Prefix N=1000 500K | $904 / 62.47% | $904 / 62.47% | **$889 / 62.74%** | **−$15 / +0.27pp** |

**Per-category v34 vs v32 (full grid):** every category improves. Within-category headlines:

| Category | v32 | v34 | Δ within | share | whole-grid |
|---|---:|---:|---:|---:|---:|
| high_only  | $2,816 | $2,806 | −$10  | 20.4% | −$2.0 |
| pair       | $1,639 | $1,619 | −$20  | 46.6% | −$9.3 |
| two_pair   | $1,037 | $978   | −$59  | 22.3% | −$13.2 |
| trips      | $1,359 | $1,291 | −$68  | 5.46% | −$3.7 |
| trips_pair | $1,225 | $1,057 | −$168 | 2.86% | −$4.8 |
| three_pair | $1,639 | $1,635 | −$4   | 1.90% | −$0.1 |
| quads      | $645   | $613   | −$32  | 0.24% | −$0.1 |
| composite  | $1,386 | $1,173 | −$213 | 0.245% | −$0.5 |

The biggest within-category gains are in trips_pair (−$168) and composite (−$213) — both ML-engineered categories that benefit from finer leaf granularity. Whole-grid contribution is dominated by two_pair (−$13/1000h via 22.3% share) and pair (−$9/1000h via 46.6% share). **Unlike prior gating ships, this ship moves every category — a textbook capacity-only signature.**

**Cumulative v30 → v34 of $113/1000h (full grid) is the new largest cumulative arc in project history**, beating Session 37's v30→v32 of $79. The arc decomposes as: v30→v31 ($58, capacity), v31→v32 ($20, trips_v2 features), v32→v34 ($34, capacity-only at ml=2).

**Part B — Rule 6 A-vs-C boundary probe (negative result, archived as v34_rule6_v2).**

Following the user's hypothesis that Rule 6's C variant (3rd trip card on top when `trip_rank > max_kicker_rank`) is suspect at low/mid trip ranks, Session 38 wrote `probe_rule6_c_variant.py` to compute oracle EVs for the best A and best C settings stratified by `(trip_rank, max_kicker_rank)`.

**Oracle-level findings strongly validated the user's hypothesis:**

| Variant | Mean regret vs oracle (whole-grid) | Cells where it wins |
|---|---:|---:|
| best-A (top = highest kicker) | $+82/1000h | 84.1% |
| best-C (top = trip card) | $+608/1000h | 15.9% |

C wins overwhelmingly only at trip A (100% of cells, +$5,757 to +$14,139 over A) and trip K (88-100%, +$2,131 to +$7,240); narrowly at trip Q (mixed); LOSES at trip ≤ J (-$1,765 to -$17,030). The user was directionally right: C is dominated below trip Q.

**But heuristic-realizable gain is ~95% smaller than the oracle ceiling.** A boundary sweep across `min_trip_for_C ∈ {3..14, A-only}` produced max gain of **+$0.57/1000h whole-grid at trip ≥ T**. The 95% gap arises because the v33/v34 A-variant heuristic (bot suit profile → rank sum → run) underperforms relative to v33's "mechanical C" pick on the cells that flip — at trip Q, the heuristic-A loses ~$1,857/1000h within-trips on flipped cells (oracle said only −$278 was even achievable). The bot-DS optimizer is the rate-limiting step, not the threshold rule.

**Sweep table:**

| Rule | $/1000h whole-grid | Δ vs v33 | Cells changed |
|---|---:|---:|---:|
| v33 (trip > maxK → C) | $109.83 | baseline | 0 |
| trip ≥ 9 → C | $109.32 | +$0.52 | 81 |
| **trip ≥ T → C (best)** | **$109.27** | **+$0.57** | **226** |
| trip ≥ J → C | $109.83 | $0.00 | 543 |
| trip ≥ Q → C | $112.52 | −$2.69 | 1,151 |
| trip ≥ K → C | $120.01 | −$10.18 | 2,093 |
| Always A | $181.79 | −$71.96 | 5,928 |

**v33's boundary stands as the human strategy of record.** v34_rule6_v2 is archived. The remaining ~$5-13/1000h of unrealized A-vs-C oracle gain is now reframed as a future ML target: a learned A-variant heuristic OR a learned A-vs-C decision tree on (trip_rank, max_kicker_rank, suit profile). v32/v34's gated trips features partially capture this signal already.

**Methodology lessons reinforced (Session 38):**

1. **`min_samples_leaf=2` can unlock more capacity than depth.** When a `ml=3` tree saturates below its depth cap (control: depth=33 actual at depth=34 cap), the next capacity unlock is `ml=2`, NOT deeper depth. **Refines Session 37's rule:** future capacity retests should sweep `min_samples_leaf ∈ {3, 2}` at a generous depth cap, and pick the smaller-ml winner if shape-agreement improves.

2. **Heuristic-realizable ceilings are smaller than oracle ceilings.** Rule 6's heuristic captured 56% of its $197 oracle ceiling (Session 37 finding); Rule 6 v2's would capture only ~5% of its $13 oracle ceiling because the A-heuristic's quality is the rate-limiting step. **Future Always-X probes should report BOTH the oracle ceiling AND the closest heuristic-realizable headline** to set realistic expectations.

3. **Capacity ships are not gating ships.** v34's per-category footprint moves every category simultaneously (textbook capacity signature). Gating ships move ONE category and leave the others bit-identical. This distinction now has 2 instances on each side: capacity-only (v31, v34) vs single-category gating (v20, v23, v24, v25, v26, v27, v29, v30, v32 round-2).

4. **Tripwire was not run for v34 because no new features were introduced.** Same 83 features as v32. The leaf-count growth of +19.5% is the relevant capacity signal, and broad cross-category gains confirm latent signal was leaf-bound, not feature-bound. Tripwire is a feature-design diagnostic; capacity ships use leaf-count + per-category coverage instead.

---

## Session 39: Rule 6 boundary tightening + suit-matching rewrite (v35_rule6_v3 ships in the strategy guide; production heuristic keeps v33)

The user's headline ask was: "the trips strategy doesn't have hard-set rules that are easy to follow yet — can we fix that?" This session rewrote Rule 6 around two human-friendly artifacts:

1. **A sharper boundary table** that maps directly onto Session 38's per-cell oracle data, replacing the `trip_rank vs max_kicker_rank` comparison with an explicit per-trip-rank decision (Trip A always third-on-top; Trip K third-on-top unless an Ace; Trip Q third-on-top unless J/K/A; Trip ≤ J always third-to-bot).
2. **A 2-step suit-matching procedure** for "which trip joins bot" that replaces the prior fuzzy "maximize bot DS-ness" instruction with priority-ordered cases (match a singleton kicker → 2+2 DS, match a fresh suit → 2+1+1 SS, never match the kicker pair → avoid 3+1).

**Verification (`verify_rule6_v3_human.py`)** on the same 30K trips probe:

| Mode | v33 (boundary trip > maxK) | v35 (sharpened) | Δ |
|---|---:|---:|---:|
| **Oracle-bound (HUMAN ceiling)** | -$42.56/1000h whole-grid | **-$34.44/1000h** | **+$8.12** ✓ |
| Heuristic (production bot) | -$113.34/1000h | -$117.40/1000h | -$4.06 ✗ |

v35 captures **63% of the $12.89/1000h oracle ceiling identified in Decision 070**, sacrificing the remaining 37% by simplifying the noisy "Trip J + low-kicker" cells (where C narrowly wins by $50–$1,400 within-trips on small samples). The trade keeps the rule memorable and only loses ~$4.77/1000h vs the optimal-but-unmemorable boundary.

**Per-trip-rank breakdown** (oracle-bound):

| Trip rank | v33 → v35 lift | Driver |
|---|---:|---|
| A, K, 2-5 | $0 | v33 already optimal here |
| 6-Q | +$0.19 to +$2.54/1000h | Sharpened cells flip C → A correctly |
| 8 | +$0.81 | Trip 8 + low kickers |
| 9 | +$1.56 | Same |
| T | +$2.40 | Trip T + low kickers |
| J | +$2.54 | Largest lift — Trip J + maxK low cells |

**Methodology rule (NEW Session 39): the human strategy guide can be sharper than the production heuristic when heuristic-A is the rate-limiting step.** Decision 070 archived v34_rule6_v2 because the heuristic-A bot-DS optimizer couldn't cash a sharper boundary. But the same boundary IS realizable for a thoughtful human, who can pick the oracle-best A-variant pick in any cell (the cell-level A-vs-C choice is the gain; the within-A-routing is what the production heuristic stumbles on). v35 ships in `STRATEGY_GUIDE.md` Part 6 as the human strategy of record. The production bot keeps v33 because runtime evaluation shows the heuristic-A loses $4/1000h on the flipped cells (matching Session 38's sweep finding).

**Decision 071** records this two-track ship.

**A1b — Suit-matching rule for "which trip joins bot"**: replaces v33's fuzzy "maximize bot DS-ness, then rank-sum, then connectivity" with three named cases (kickers two-and-one, kickers rainbow, kickers three-of-a-suit) and three named bot shapes (DS 2+2, SS 2+1+1, 3+1 to avoid). Five worked examples in the Part 6 rewrite. The production heuristic-A is structurally the same procedure (suit_profile dominates the score), so the prose change does not modify production behavior.

**What did NOT happen this session**: Always-X probes for `three_pair`, `composite`, `two_pair`, `high_only` (deferred Priority A2). Round-3 within-trips diagnostic (Priority B). Learned A-vs-C decision tree (Priority C). KK/AA single-suited Rule-4-bot residual (Priority D). All carried into Session 40.

---

## Session 40: Rule 6 low-trips reference table (Trip T..2 worked examples) + connectivity tier rejected

User's Session-39-close ask: "Trip A/K/Q/J got explicit per-rank treatment + worked examples. Trip T..2 got lumped as 'always third trip to bot' — spell out per-rank treatment too." This session delivered three artifacts, all additive (no production code change, no DECISIONS_LOG entry needed).

**A0.1 — Eight new worked examples appended to Part 6.** One per rank from T down to 2 (Examples 7–14), filling in the gap between the existing Trip J (Example 5) and Trip 7 (Example 6). Each example shows a different teaching point: Trip T's rainbow-kickers-all-SS case (no DS available); Trip 9's two-and-one-kickers DS find (the canonical "good" Step 2 outcome); Trip 8's 3+1 trap (where your trip is the kicker-pair suit); Trip 6's 4-card-run bot (illustrating connectivity is incidental); Trip 5's wheel-eligible bot (same point, more dramatic); Trips 4/3/2's plain SS picks on weak hands (illustrating the rule keeps working even when the cards don't). All 8 examples were verified against `strategy_v35_rule6_v3.py` to confirm the picks match the narrative.

**A0.2 — Connectivity tier rejected (`probe_low_trips_connectivity.py`).** Tested the hypothesis that a 4-card run on bot (e.g., trip 5 + 2-3-4 wheel; trip 7 + 4-5-6) should add a connectivity tier between SS and rainbow in Step 2's priority. Three findings:

1. **Connectivity is invariant across the 3 trip-to-bot picks on a given hand.** Within one hand, the bot's longest run is determined by the kicker ranks (which are fixed) plus the trip rank (also fixed) — only suits change between picks. So run-length cannot serve as a tiebreaker; it's identical across candidates.
2. **Mean oracle EV by (suit_profile × longest_run) shows MORE run = WORSE EV inside every profile.** This is selection: hands eligible to make 4-runs are low-trip + low-kicker hands, which are weak overall. Mean EV at "DS run=4" is $-14,156/1000h_within_low_trips vs "DS run=1" at $-3,912 — the run is a signal of weak cards, not of strong settings.
3. **The alt priority "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1" regresses $11/1000h whole-grid versus the existing DS > SS > rainbow > 3+1.** And the oracle picks rainbow 0% of the time when SS or DS is available; rainbow-run-4 picks are oracle-preferred 0/196 (0%) of hands where they exist.

The probe also surfaced a **42% disagreement rate** between v33-heuristic-pick and oracle-pick at low trips. Mean lift on the disagreement subset is +$1,212/1000h_within_low_trips (≈$19.53/1000h whole-grid). The bulk (51% of disagreements) is "SS → SS" — same suit profile, different trip-suit pick. This residual gap is real but is **not** a connectivity story; it would take a finer-grained suit/rank correlation feature to capture (note for Priority C — the learned A-vs-C decision tree could absorb this).

**A0.3 — Per-cell A-vs-C oracle map cross-referenced.** Re-ran `probe_rule6_c_variant.py` on the 30K trips probe (same RandomState(0)). For trip ≤ T at every cell with n≥5, A wins ≥99% of the time and the within-cell C-A delta is structurally negative ($-1,765 to $-15,585/1000h_in even at the lowest max-kicker cells). Confirms v35's "Trip ≤ J always A" boundary is structurally correct, not a noise artifact.

**Score impact:** $0/1000h. This session was additive documentation (the strategy guide) plus a probe whose verdict was "no rule change needed". No new ship.

**Methodology lesson — connectivity in same-rank-set picks is invariant; cannot be a tiebreaker.** A general rule that applies whenever a heuristic enumerates K candidates that share a fixed rank set: features that depend only on ranks (run length, rank-sum, broadway count) are constant across candidates. The only signal worth scoring is what differs (here, suit assignment). Future Step-2-style probes should check candidate-level invariance before adding a feature to the priority.

**Methodology lesson — when a probe's mean-EV-per-cell shows a "feature predicts bad outcomes", check for selection effects.** "Wheel-eligible bots have $-32K mean EV vs $-14K for non-wheel" looks like the wheel is bad; in reality, wheel-eligible hands ARE bad hands. Always read selection effects before drawing rule-shaping conclusions from cross-cell aggregates.

**What did NOT happen this session**: Always-X probes for `three_pair`, `composite`, `two_pair`, `high_only` (Priority A still pending). Round-3 within-trips diagnostic (Priority B). Learned A-vs-C decision tree (Priority C — but the within-SS disagreement signal from this session's connectivity probe makes a useful input to that tree's training). KK/AA single-suited Rule-4-bot residual (Priority D). All carry into Session 41.

---

## Session 41: Rule 7 (three_pair) ships in production as v37; high_only Rule 7 attempt archived

This session ran the always-X structural probe across two categories. **One ship, one archived attempt.**

**Part A — high_only (the big residual): tested and archived as ML-only.**

high_only is 20.4% of all hands and the largest within-cat residual ($572/1000h whole-grid in v34_dt's residuals). Three always-X candidates were tested in `verify_rule_X_v33_high_only.py`:

  - **X1: top = highest singleton card.** v33 already does this 100% of the time. Confirmation only — no new rule needed.
  - **X2: top = highest, mid = next two highest (rank-down 1-2-4).** Deterministic regression: −$134/1000h whole-grid. v33 picks the X2 setting only 18.8% of hands; suit structure overrides pure rank ordering 81% of the time.
  - **X3: top = highest, mid is two cards of the same suit if any same-suit pair exists in the remaining 6 cards.** Oracle ceiling: +$355/1000h whole-grid. Naive heuristic ("highest rank-sum same-suit mid"): −$5.88/1000h.

The X3 ceiling is real and large, but unrealizable. `probe_high_only_suited_mid_drill.py` tested 6 different tiebreakers (rank-sum, connected-first, bot-DS-first, broadway-first, composite scores) — all regressed vs v33. Per-feature importance: broadway is the strongest single signal (32% vs 19% lift on P(oracle picks this candidate)) but still under 50% — coin-flip territory.

**`grade_v36_rule7_high_only.py` on full 6M-hand grid + full 1.2M high_only population:** v33 = $2,920/1000h, v36 = $2,926/1000h (−$6 regression, confirmed). Oracle-bound ceiling: +$354/1000h. Realization gap: $360/1000h.

**Verdict:** v36 archived (`strategy_v36_rule7_high_only.py` ARCHIVED docstring, retained for history). high_only is officially an ML-only category; v34_dt's gated `ho_*_g` features are the path forward. Methodology rule: do not re-attempt high_only without a multi-feature ML breakthrough.

**Part B — three_pair (small but untouched): Rule 7 SHIPS as v37.**

three_pair is 1.9% of all hands but had been completely untouched by gating in v34_dt ($86.20/1000h whole-grid budget). The full 114K population was probed exhaustively across all 286 (high_pair, middle_pair, low_pair) combinations in `verify_rule_X_v33_three_pair.py` and `probe_three_pair_boundary.py`.

**Findings:**

| Rule | Δ vs v33 (whole-grid) | Notes |
|---|---:|---|
| RA: top=singleton, mid=HIGHEST pair | +$18.36 | naive intuition (v33 does this 68% of the time) |
| RB: top=singleton, mid=MIDDLE pair | +$24.94 | better default than RA |
| **★ RB if high ∈ {T,J,Q,K} else RA** | **+$43.05** | 1-condition rule; **Rule 7 final form** |
| RB if high ∈ {T,J,Q,K} OR (high=A AND low≤3) | +$43.06 | 2-condition adds nothing |
| Oracle per-cell ceiling | +$71.18 | unreachable upper bound |

**The structural intuition:** the trade is "where does the strongest pair go: mid (Hold'em) or bot (Omaha)?" A broadway non-Ace pair (K, Q, J, T) on the bot anchors a strong 2-pair Omaha hand (the high pair becomes a trips draw on board pairs). Aces are special — pairing AA in the mid is so dominant in Hold'em that you don't move it. Below T (your "high" pair is 9 or lower), the high pair isn't strong enough to anchor the bot, so keep it in the mid.

**Empirical ship (`grade_v37_rule7.py`):**
- **Prefix grid (500K, N=1000):** three_pair within-cat regret drops $4,085 → $1,334 (67% reduction). pct_optimal 38.9% → 64.9%. Whole-grid: **+$141/1000h** (since prefix has 11% three_pair share). Overall optimal pct: 48.81% → 50.14%.
- **Full grid (6M, N=200):** confirmed +$43/1000h whole-grid (matches drill).

**Score: $2,920 → $(2,920 − 43) ≈ $2,877/1000h on full grid. Improvement: −$43 vs v33, −$156 vs v14, −$276 vs v8_hybrid.** v37 replaces v33 as the production strategy of record.

**Methodology lesson — heuristic-realizable ceilings vary by category.** high_only's heuristic ceiling is essentially zero ($-6 regression vs $355 oracle ceiling — 0% capture). three_pair's heuristic ceiling is much higher ($43 vs $71 oracle ceiling — 60% capture). The difference: three_pair's optimal-pick structure is rank-driven (single feature: highest pair rank), while high_only's optimal-pick structure is multivariate (suit pattern × singleton × bot composition). Always-X probes should check whether the optimal-pick structure is uni-variate before declaring a category rule-extractable.

**Methodology lesson — v33's diagnostics tell you which always-X candidate to test first.** v33's per-category routing reveals what it's already doing: "v33 picks mid=high pair on 68% of three_pair hands" → RA is the de facto current rule. Test the alternatives (RB, RC) immediately. This shortcut saved 2-3 iterations on three_pair.

**What did NOT happen this session**: composite, two_pair always-X probes (Priority A continuation). Round-3 within-trips diagnostic (Priority B). Learned A-vs-C decision tree (Priority C). KK/AA single-suited Rule-4-bot residual (Priority D). All carry into Session 42.

---

## Session 42: Rule 8 (composite quads_pair) ships in production as v38; two_pair Rule 8 candidate deferred after prefix-grid regression

This session ran the always-X probes for the two remaining categories from the Session 38–39 queue: **two_pair** (22.3% of canonical hands) and **composite** (0.245% of canonical hands). **One ship (composite QP), one DEFERRED candidate (two_pair).**

**Part A — two_pair: large full-grid lift, but DEFERRED after prefix regression.**

`verify_rule_X_v33_two_pair.py` walked the full 1.34M two_pair population. Headlines:

  - v33 baseline: $3,371/1000h within-cat = $751/1000h whole-grid (the largest residual after high_only)
  - **TP_RB (always mid=LOW pair)**:    Δ +$68.46/1000h whole-grid
  - TP_RA (always mid=HIGH pair):       Δ -$87.71/1000h whole-grid
  - TP_RC (double-pair bot):            Δ -$1,988    /1000h whole-grid
  - Best per cell (oracle ceiling):     Δ +$624.65   /1000h whole-grid
  - v33 mid composition: high_pair 54.8%, low_pair 25.0%, unpaired 20.2% (v33 is already cell-aware via v8_hybrid → v7_regression underlying logic)

`probe_two_pair_boundary.py` mapped all 78 (high_pair, low_pair) cells and ran a boundary search across ~20 candidate rules. The cleanest single rule:

  > **"RC if high ≤ 4, elif T ≤ high ≤ K then RB, else RA"**
  > Δ = +$196.89/1000h whole-grid on full N=200 grid (32% of the +$624.65 oracle ceiling)

That's 4.6× the size of v37's three_pair lift — it would have been the biggest rule-layer ship in the project's history. The boundary perfectly mirrors three_pair Rule 7 (broadway non-A pair → bot, AA stays in mid) with an additional RC tail for very low pairs.

`grade_v38_rule8.py` confirmed +$197.00/1000h on full grid (matches the probe exactly). **But the prefix grade showed -$512/1000h regression.**

A variant sweep on prefix tested 12 different rule shapes — narrower boundaries, low-pair gating, no-RC versions. **Every variant regressed on prefix**, including "always RA" (-$863) and "always RB" (-$918). The fundamental problem: v33's underlying v7_regression sometimes SPLITS pairs (mid is one card from each pair), and on the prefix's weak-hand-biased distribution, this adaptive splitting happens to be the right move on enough hands that any forced no-split rule loses.

**Verdict:** v38 (Rule 8 two_pair) DEFERRED. Strategy file renamed `strategy_v38_rule8_two_pair_DEFERRED.py`, retained for next-session investigation. The two_pair territory needs either (a) a split-allowing rule that fires only on weak-pair hands, (b) a multi-feature ML approach (already the case — v34_dt's gated `tp_*_g` features), or (c) a separate human-only "guide" track distinct from production runtime. **Methodology rule NEW (Session 42): a prefix-grid regression of >2× the full-grid lift means the rule doesn't generalize, regardless of how clean the boundary looks on the per-cell breakdown of the full grid.**

**Part B — composite (small but untouched): Rule 8 SHIPS as v38.**

`verify_rule_X_v33_composite.py` walked the entire 14,742 composite population (subtypes: quads_pair 6,863 hands, quads_trip 156, two_trips 4,290, trips_two_pair 6,864). Findings per subtype:

  - **quads_pair** ($9.77/1000h whole-grid budget): "QP_quad_in_mid" (top=singleton, mid=2 of quad, bot=other 2 quad + pair) lifts +$9.42/1000h whole-grid. **100% heuristic-realizable** (verified): the structural pick "mid = 2 quad cards whose suits are NOT the pair's suits" exactly matches the oracle-within-constraint. The rule guarantees the bot is double-suited (2 of pair-suit-X + 2 of pair-suit-Y).
  - **two_trips** ($8.14/1000h budget): "TT_full_house_split" (top = trip member, oracle-best mid) lifts +$7.22/1000h whole-grid as oracle-ceiling. Heuristic capture not yet drilled — pending Session 43.
  - **trips_two_pair** ($8.24/1000h budget): "T2P_split_trip_top" (top = trip member, oracle-best mid) lifts +$7.64/1000h whole-grid as oracle-ceiling. Heuristic capture not yet drilled — pending Session 43.
  - **quads_trip** ($0.56/1000h budget): tiny population (156 hands), marginal lift, defer.

Only the quads_pair subtype has a verified deterministic rule. The other two composite subtypes have promising oracle-ceilings (+$7-8 whole-grid each) that need follow-up heuristic drills.

`grade_v38_rule8.py` (composite-QP version) confirmed Δ = +$9.42/1000h whole-grid on full N=200 + Δ = +$18.63/1000h whole-prefix. **Both grids positive — the consistency check the two_pair candidate failed.**

**Score**: $2,877 → $(2,877 − 9.42) ≈ $2,868/1000h on full grid. Improvement: **−$9.42 vs v37** (small but clean), −$166 vs v14, −$285 vs v8_hybrid. v38 replaces v37 as the production strategy of record.

**Methodology lesson — prefix-grid regression as a generalization gate.** Sessions 38–41 happened to ship rules that won on both grids (Rule 6 v1, Rule 7 three_pair) — the question of "what if a rule wins on full but loses on prefix?" hadn't come up. Session 42 is the first time. The decision: prefix is biased toward weak hands, but a rule that loses there indicates the rule isn't actually capturing structure, just exploiting a full-grid-only artifact. v38's composite-QP ship passes both gates; the two_pair candidate fails the second gate.

**Methodology lesson — composite is heterogeneous; QP is the cleanest subtype.** The composite category lumps four shapes (quads_pair, quads_trip, two_trips, trips_two_pair) under one label, but they need separate rules. quads_pair is the cleanest — single deterministic rule captures 100% of the constrained-oracle ceiling. The other 3 subtypes need more investigation (Session 43 priority).

**Methodology lesson — v33 on weak hands is doing something non-trivial.** v33 inherits two_pair routing from v8_hybrid → v7_regression (a learned tree). On the prefix's weak-hand distribution, v33 picks splits/non-Rule-2 settings that any forced rule can't match. This is interesting: v33 is already capturing fine-grained suit/kicker structure on weak hands. The two_pair territory may need ML (it's already heavily gated in v34_dt with `tp_*_g` features) rather than another rule.

**What did NOT happen this session**: heuristic refinement drills for composite TT and T2P subtypes (Priority B carryover). Round-3 within-trips diagnostic. Learned A-vs-C decision tree for Rule 6. KK/AA single-suited Rule-4-bot residual. v34_dt re-train on v38 baseline. All carry into Session 43.

---

## Session 42 overnight: Rule 9 (3 sub-rules) ships as v39 — combined +$22 full / +$28 prefix

After v38 shipped (Rule 8 quads_pair), the user asked for an overnight deep-dive into the rule-mining frontier. Six investigations ran while they slept; **three new structural rules emerged that all pass the both-grid validation gate**:

**Part A — TT (two_trips, 3+3+1) E3a heuristic hunt: Rule 9b ships.**

`drill_tt_e3a_heuristic_hunt.py` tested 12+ suit-aware top-pick × L-bot-pick combinations within the E3a structural class (split the high trip to top, full low-trip pair in mid, bot has 2H+1L+singleton). The +$5.98/1000h whole-grid oracle ceiling came from picking the *right* H-trip card to split and the *right* L-trip card to drop into the bot for DS purposes. The winning deterministic combination:
  - **Top = an H-trip card whose suit IS in the LOW-trip's suits**
  - **L-bot = the L-trip card whose suit best matches bot's H-trip-leftovers + singleton (DS-aware tiebreaker)**

Lift: **+$3.57/1000h whole-grid (full N=200) + +$2.79/1000h whole-prefix.** 60% of the +$5.98 ceiling. Captures the structural insight that the bot's 4 cards (2 H-trip + 1 L-trip + 1 singleton) want to form a 2-pair Omaha hand with high-trip anchor — and the right suit-pick maximizes the chance of DS bot.

**Part B — Plain quads (4+1+1+1) structural drill: Rule 9a ships, BIGGEST find of the night.**

`drill_plain_quads_structural.py` tested the QP-style suit-aware insight on plain quads (1 quad + 3 singletons, 14,300 hands). The winning rule mirrors Rule 8 QP exactly:
  - **Top = highest singleton**
  - **Mid = the 2 quad cards whose SUITS are NOT used by any of the 3 singletons**
  - **Bot = the other 2 quads + the 2 lower singletons**

Lift: **+$15.31/1000h whole-grid (full) + +$11.78/1000h whole-prefix.** 73% of the +$21.02 oracle ceiling. **Wins on ALL 13 quad-rank cells uniformly** — universal rule. Within-cat regret on plain quads drops from $9,670/1000h to ~$3,235/1000h on the full-grid grade (66% reduction). pct_optimal jumps from 9.5% → 45.9%.

The intuition: when you have 4 same-rank cards (one of each suit), there are exactly C(4,2)=6 ways to pick which 2 go to mid. The 6 differ only in suit composition. The deterministic "2 quads at non-singleton-suits to mid" forces the bot to always be double-suited (= 2 quads at 2 of the 3 singleton-overlapping-suits + 2 lower singletons whose suits the bot's remaining quads echo). Same insight as Rule 8 QP, different population.

**Part C — T2P (trips_two_pair, 3+2+2) deeper boundary: Rule 9c ships.**

`drill_t2p_deeper_boundary.py` tested 23 boundary rules combining trip-rank, hi-pair-rank, lo-pair-rank, gap conditions. The cleanest:
  - **If trip-rank ≤ 4: mid = LOW pair, bot = trip-leftovers + HIGH pair** (F3 — high pair on bot for stronger Omaha 2-pair anchor)
  - **Else (trip ≥ 5): mid = HIGH pair, bot = trip-leftovers + LOW pair** (F2 — keep mid Hold'em strength)
  - **Top = a trip-member at the suit ∉ pair-suits if possible** (suit-aware split)

Lift: **+$2.81/1000h whole-grid (full) + +$13.48/1000h whole-prefix.** Beats "always F2" (+$2.04 / +$9.57) by adding the trip-rank boundary. The intuition: when the trip is very weak (rank 2-4), the bot's "trips-on-board" anchor is barely useful (low-rank trips lose to most Omaha completions); better to put the HIGH pair on the bot for a stronger 2-pair Omaha anchor. When the trip is 5+, mid-Hold'em strength of HH outweighs that bot benefit.

**Part D — Two_pair split investigation: confirmed ML-only.**

`drill_two_pair_split_investigation.py` walked the full 1.34M two_pair population and characterized oracle picks. Key findings:
- **SPLIT never wins at the cell level: 0 of 78 cells prefer mixed-pair-mid.** The split hypothesis was wrong.
- Even oracle-best-per-cell within {RA, RB, RC} loses prefix by **-$336/1000h**.
- The oracle's "fix" for prefix wins comes from picking DIFFERENT singletons as top: 21% of oracle picks have top ≠ highest-singleton. v33 always picks top = highest-singleton.

Verdict: two_pair is genuinely ML territory. The deferred two_pair Rule 8 candidate (+$197 full / -$512 prefix) cannot be rescued by any cell-rank-based rule.

**Part E — Pair Rule 1 extension: notable but Session 43 work.**

`drill_pair_rule1_extension.py` profiled the 46.6%-of-hands pair category. Found that **QQ has the biggest v33 loss at $2,833/1000h within-cat** with a 50/50 split between mid=P_pair vs unpaired-mid in oracle picks. JJ similar at $2,541. Suggests an extension to Rule 1 (move QQ/JJ to bot when DS-ready), but the gate needs careful design and the both-grid validation gate. Carrying forward.

**Part F — Trips_pair refinement: existing Rule 3 already near-optimal.**

`drill_trips_pair_refinement.py` tested suit-aware refinements to Rule 3. All deterministic candidates regressed vs the existing v33 implementation. G3 oracle-within-class (top = kicker, mid = 2 trip-leftovers paired) showed a +$85/1000h ceiling but no clean heuristic. Existing Rule 3 stays; G3 ceiling exploration deferred.

**Score: $2,868 → $2,846/1000h on full grid. Improvement: −$22 vs v38, −$307 vs v8_hybrid.** v39 replaces v38 as the production strategy of record.

**Methodology lesson — sequential drill + suit-aware insight generalizes broadly.** Rule 8 QP discovered the "non-pair-suit-quads to mid" pattern. Plain quads (different population, same shape) generalized identically (Rule 9a). TT (different category) used the same "non-X-suit" suit-aware insight on different choice points (Rule 9b's top + L-bot picks). The pattern: when you have multiple same-rank cards (or near-same), the "one suit isn't represented in the rest of the hand" position of those cards is the structural pick — using it for mid forces the bot to be DS via the remaining-suit symmetry.

**Methodology lesson — the both-grid validation gate works as a rule-quality filter.** Three of six investigations produced rules that passed both grids (9a, 9b, 9c). One (two_pair split) confirmed ML-only. One (pair Rule 1 extension) showed promise but needs more gate-design work. One (trips_pair) found no improvement available. The gate cleanly distinguished generalize-able structural insights from full-grid-only artifacts.

---

## Session 43: Rule 10 (J-low single-pair defensive) ships as v40 — the first DEFENSIVE rule, +$37/1000h prefix

The user requested a dedicated investigation into "weak-hand defensive play" — the ~14% of hands with max card ≤ J. These are hands where the question isn't "how do I scoop?" but "how do I lose the LEAST?" The drill plan in `docs/SESSION_43_WEAK_HAND_DEFENSE.md` posed five framing questions (Q1-Q5).

**Three drills ran:**
1. `drill_high_card_defense.py` — high_only Q1+Q2+Q5 (86K hands)
2. `drill_low_pair_J_high_defense.py` — pair Q3 (343K hands)
3. `drill_two_pair_J_high_revisit.py` — two_pair Q4 re-examination (262K hands)

**Headline structural insight — weak-hand top inversion.** When the highest card cannot reliably win the top tier, the GTO play is to **dump the LOWEST card on top** and stack the strong cards into mid + bot. Oracle top-position frequencies:

| Stratum | top=hi | top=lo |
|---|---:|---:|
| A-high+weak | 96.0% | 2.1% |
| K-high+weak | 66.6% | 15.6% |
| Q-high+weak | 48.1% | 24.4% |
| J-high | 27.2% | **34.4%** |
| T-high | 14.6% | **42.0%** |
| 9-high | 6.8% | **47.1%** |

The math: top tier wins 1 point/board (max 2 across both boards), mid 2/board, bot 3/board. When TOP equity is already <50% (any J-low hand), the opportunity cost of dumping the highest card is <1 point, while the gain in bot+mid equity from upgrading kicker strength is >1 point.

**Rule 10 ships (Q3 J-low pair):**
- TOP = lowest singleton
- MID = the pair (mid Hold'em paired anchor — oracle prefers mid-pair on 60-85% of cells)
- BOT = the 4 highest non-pair singletons (Omaha kicker-strength upgrade)

Trigger: `category == pair AND max_rank <= J`. Population: 342,720 hands (5.703% of grid).

**Lift: +$22.73/1000h whole-grid (full N=200) + +$36.70/1000h whole-grid (prefix N=1000)** — both grids strongly positive. The prefix lift is BIGGER than the full lift, the OPPOSITE of the prefix-regression risk pattern. This is the largest single-rule prefix lift in project history.

A gated variant `strategy_v40b_rule10_gated.py` (additional condition `pair_rank ≤ 6 OR pair_rank == max_rank`) was also produced. Same prefix lift (the prefix only contains pair=2 cells which always satisfy the gate); fuller-grid lift estimated at +$48/1000h by avoiding localized regression cells. Per Session 42 "structural break is the natural plateau" methodology, the production runtime ships the simpler v40; v40b is retained as a sister artifact for ML / future use.

**Other Session 43 findings (not shipped):**
- **Q1** ("always Ace-on-top?"): YES, oracle picks top=Ace 96% on A-high+weak. v3 already implements this — no rule needed.
- **Q2** ("break broadway for 4-flush bot?"): NO. Every B_BOT_FLUSH variant regressed by $10-$27/1000h. The high card belongs on top.
- **Q4** ("J-low two_pair adaptive splitting was correct defensive play?"): NO. All six deterministic candidates (RA, RB, RC, RA_TOP_LO, RC_TOP_LO, F_SPLIT) regressed materially. v33's adaptive splitting confirmed as genuine ML routing, not a hidden defensive rule. **Two_pair is genuinely ML territory (confirmed twice now: S42 overnight + S43 Q4).**
- **Q5** ("J-high no-pair, does suited bot save?"): NO clean answer. Naive top=lowest works on T-low (+$8/1000h whole-grid full only) but regresses on J-high. high_only category has ZERO prefix coverage (all canonical IDs >500K) so both-grid validation is impossible — full-only or not at all. Deferred to Session 44.

**Methodology lessons (NEW Session 43):**
- **Weak-hand top inversion is a unifying structural pattern.** Top tier wins 1 point/board; when TOP equity is already <50%, dumping the highest card to top costs less than the gain in bot+mid equity. This pattern explains Rule 10 and may extend to other weak-hand categories (Q5 J-high no-pair has signal but is multi-feature).
- **high_only category has zero prefix coverage.** All 7-distinct-rank canonical IDs are >500K. The both-grid validation gate is INAPPLICABLE for any rule scoped to no-pair hands. Defensive rules for the no-pair zone can only ship on full-grid validation alone, OR not ship.
- **High-card-to-bot-for-4-flush is a LOSING trade.** Counterintuitive conventional wisdom is empirically wrong: -$10 to -$27/1000h on every weak-hand stratum.
- **Worst-case regret is a useful sanity check** for defensive rules. A rule with positive mean lift but BIGGER worst-case regret would induce more 20-point scoops. v40's per-cell worst-case regret stays in the +$10-$22 range, no scoop-induction risk.

**Score (v40b gated, PRODUCTION): $2,846 → $2,798/1000h on full grid (−$48, +$48/1000h whole-grid lift, grader-confirmed). Prefix: $1,707 → $1,670 (−$37). pct_opt full: 41.17% → 41.48% (+0.31%). pct_opt prefix: 50.38% → 50.64%.** Within-pair-category regret full grid: $2,008 → $1,905/1000h. **Score (v40 simple, sister): $2,846 → $2,824 full (+$23 lift), pct_opt 41.15% (slight regression).** v40b replaces v39 as the production strategy of record; v40 is retained for human-memorization fork.

---

## Session 44: Bot suit×connectivity priority refined — SUIT DOMINATES CONNECTIVITY (methodology investigation, no new ship)

User devil's-advocate questioning of Rule 10's bot construction triggered a methodology investigation. Two drills ran:

**Drill 1 — `drill_bot_suit_run_priority.py` (CONFOUNDED).** Cross-product 5×7 (suit × connectivity) of bot classifications. Results showed surprising-but-suspicious findings: 4-flush-run-4 outranked SS-run-4, DS-scattered outranked SS-run-4 — both contradicted Omaha first-principles.

**Drill 2 — `drill_bot_suit_run_pairwise.py` (DEFINITIVE).** Same scope, but within-hand pairwise comparison (for each hand, compute EV(best in A) − EV(best in B) for every achievable pair). Eliminates the cross-class hand-population confounder.

Gemini consultation (`mcp__pal__chat` with `gemini-2.5-pro`) confirmed: cross-class average regret is confounded by hand-population differences. Within-hand pairwise is the right methodology for cross-class priority ranking.

**Definitive findings (J-low no-pair, n=85,800):**

The original methodology rule "DS > SS > rainbow > 3+1 > 4-flush" came from trips territory (Rule 6 Step 2 + Session 40 connectivity probe) and was structurally incomplete. The refined rule: **suit dominates connectivity at every level. DS-scattered (worst DS) beats every non-DS class within-hand.**

Key tipping-point comparisons (DS-scattered vs each non-DS class):

| Vs class | n co-achievable | Lift |
|---|---:|---:|
| SS run-2+strays | 37,332 | **+$111** (basically tied, DS wins) |
| 4-flush run-4 | 672 | +$622 |
| SS run-4 | 16,904 | +$1,603 |
| Rainbow run-4 | 3,588 | +$6,981 |

No tipping point exists. The thinnest margin (DS-scattered vs SS-run-2+strays) is +$111/1000h — essentially tied but DS still wins.

**Within DS, connectivity matters but less than suit dominance:** DS run-4 vs DS scattered = +$2,554; DS-vs-SS at run-4 = +$4,457. Suit premium > connectivity premium.

**Curious side-finding:** DS one-gap-4 beats DS run-4 by +$376/1000h within-hand. A missing internal rank creates a board-bridging straight bonus. Counterintuitive — worth confirming in trips territory in a follow-up.

**4-flush mystery resolved:** 4-flush-run-4 vs SS-run-4 = +$907 within-hand (vs +$1,646 in confounded drill — smaller effect). Plausible mechanism: flush HEIGHT compensates for flush probability. With 4-flush, when board brings 3 spades you use the highest 2 spades from hand for a higher-kicker flush.

**Refined priority hierarchy:**
- Tier 1 (any DS): all DS variants beat all non-DS within-hand
- Tier 2 (close cluster, ~tied with DS-scattered): SS run-2+strays, SS one-gap-4, 4-flush run-4, SS run-4
- Tier 3: 3+1 variants, weaker SS
- Tier 4 (avoid): all rainbow

**No new rule shipped.** v40b remains production. The findings inform Session 45+ work — the user's direction is to apply suit dominance to J-low pair (does pair-stays-in-mid hold if breaking the pair enables DS-bot?) and J-low two_pair (does DS-bot beat keeping both pairs intact?).

**Methodology rules NEW (Session 44):**
- Cross-class regret averaging is confounded by hand-population differences. Always validate cross-class comparisons via within-hand pairwise.
- Suit dominates connectivity universally in J-low no-pair (no tipping point).
- First-principles arguments must check payoff height in addition to probability.
- DS one-gap-4 ≥ DS run-4 — board-bridging straight bonus dominates consecutive-rank value.

---

## Session 45: Rule 10 v3 ships (suit-aware bot construction) as v41 — +$29 full / +$54 prefix

The user's S44 closure direction was to apply suit-dominance findings to paired weak hands: do we favor pair-mid still? does DS-bot beat keeping pairs intact even at the cost of breaking pairs? Three drills ran, all using S44's within-hand pairwise methodology.

**Drill A — J-low single-pair DS-break (n=342,720, full grid).** Six-class within-hand pairwise (pair_state × bot_suit). The user's "should we break the pair to enable DS-bot?" question is answered NO: A3−A2 (pair-break for DS vs pair-mid non-DS) = **−$10,304/1000h** (catastrophic). A5−A2 (pair-to-bot for DS vs pair-mid non-DS) = **+$8.9** (essentially tied overall, but **P=J flips to +$2,975**). The unambiguous opportunity: **A1−A2 = +$2,756/1000h** — keeping pair-in-mid AND choosing singletons that yield a DS bot beats the suit-blind pair-mid pick by ~$2.8K within-hand on the 47.8% of J-low pair hands where it's achievable.

**Drill B — J-low two_pair DS-break (n=262,080, full grid).** Eight-class within-hand pairwise. Same answer with even larger margins: B3−B2 (split-LL for DS) = −$9,030, B5−B2 (split-HH for DS) = −$12,042, B7−B2 (both-split for DS) = −$23,165. The "two_pair is ML territory" verdict (S42 + S43, twice) holds for cross-class rules. The within-class B1−B2 = **+$1,864/1000h** is a future candidate.

**Drill C — DS one-gap-4 vs DS run-4 across categories (200K/cat sample).** S44's +$376 finding does NOT robustly generalize. Sign flips by category (high_only −$233, pair +$344, two_pair +$361, trips −$518). The S44 result was likely inside noise on its sample (n=1,680). Don't extract as a universal structural feature.

**Rule 10 v3 design.** Same trigger + gate as v40b (cat=pair, max≤J, P≤6 OR P==max). The change: among the 5 non-pair singletons, pick the candidate TOP such that the remaining 4 form a DS bot. Tie-break by lowest-rank singleton (preserves v40b's weak-hand top-inversion intent). If no DS-achievable TOP exists, fall back to v40b's "TOP = lowest singleton". MID = the pair (always); BOT = the remaining 4. On a 50K J-low gated-pair sample, v40b picks DS bot 15.7% of the time (suit-blind random hits) vs v41's 47.4% (matches A1 achievability ≈ 47.8%); 31.8% of picks differ.

**Per-category breakdown (full grid):**

| Category | v40b | v41 | Δ |
|---|---:|---:|---:|
| pair | $1,905 | **$1,843** | **−$62** |
| (all others unchanged) | — | — | $0 |

**Score: $2,769/1000h on full grid. Improvement: −$29 vs v40b, −$77 vs v39, $384 vs v14_combined.** Prefix grid: $1,616 (−$54 vs v40b, −$91 vs v39). pct_opt full: 41.91% (+0.43%). pct_opt prefix: 51.81% (+1.17%). Worst-case regret unchanged (max = $5.74).

**Methodology lesson — pair structure dominates suit structure universally in J-low pair / two_pair zones.** Breaking a pair to enable DS-bot is catastrophic (−$10K to −$23K/1000h within-hand). The right extraction axis is **within-class suit-aware bot**: keeping the pair anchor while picking singletons that form a DS bot ships clean lift on both grids. The S44 within-hand pairwise methodology correctly identified the within-class DS premium without misleading the cross-class question. Same pattern applies to two_pair (B1−B2 = +$1,864 within both-pairs-intact) — sister candidate for Session 46+. **Side methodology lesson — small-sample within-hand findings need replication on larger samples before being elevated to "rules"**: S44's DS one-gap-4 ≥ DS run-4 (+$376, n=1,680) did not robustly replicate at higher sample sizes; sign flips by category.

---

## Session 46: Rule 11 ships (J-pair pair-to-bot DS) as v42 — first single-cell rule, +$6 full / $0 prefix

Drill A's per-pair-rank breakdown (S45) found a sharp positive flip at P=J: A5−A2 = +$2,975/1000h (vs negative for P=2..T). Session 46 ran a focused **Drill D — J-pair-J (P=11 AND max=11) within-hand pairwise** (n=34,272) to validate the apples-to-apples comparison.

**Drill D headline lifts (within-hand, full grid):**

| Comparison | Lift ($/1000h) | Verdict |
|---|---:|---|
| **A5 − A1** (pair-to-bot DS vs pair-mid DS) | **+$1,004** | apples-to-apples Rule 11 question |
| A5 − A2 (S45 reported headline) | +$2,975 | confirmed |
| **A5 vs v41 production pick** | **+$3,769** | largest cross-class override at J-pair-J |
| A1 − A2 (Rule 10 v3 internal lift, J-pair-J specifically) | +$2,553 | confirmed |

v41's class distribution at J-pair-J: 47.8% A1 + 52.2% A2, 0.0% A5. v41 never picks pair-to-bot DS — Rule 11 surgically overrides.

**Rule 11 design:** trigger = cat=pair AND P=11 AND max=11 AND DS-bot achievable with both J's in bot. Setting builder places both J's in bot, picks 2 lowest-rank singletons that complete the 2+2 suit pattern (Case A: J's same suit X → 2 same-suit-Y singletons; Case B: J's different suits X,Y → 1 of each), TOP = lowest of remaining 3 singletons (top-inversion preserved), MID = the other 2. If no DS achievable, fall through to v41.

**Behavioral verification on 5K J-pair-J sample:** Rule 11 fires on 49.8% of J-pair-J (A5 achievability ≈ 55.1%; ~5% gap is sampling + canonical suit-symmetry). 100% of fired picks have pair-in-bot AND DS-bot. 100% of fired picks differ from v41.

**Per-category breakdown (full grid):**

| Category | v41 | v42 | Δ |
|---|---:|---:|---:|
| pair | $1,843 | **$1,829** | **−$14** |
| (all others unchanged) | — | — | $0 |

**Score: $2,763/1000h on full grid. Improvement: −$6 vs v41, −$83 vs v39, $390 vs v14_combined.** Prefix grid: $1,616 (UNCHANGED — Rule 11 fires on 0 prefix hands; J-pair-J has zero prefix coverage). pct_opt full: 41.93% (+0.02%). pct_opt prefix: 51.81% (unchanged). Worst-case regret unchanged (max = $5.74).

**Heuristic captures ~56% of A5 oracle ceiling.** Whole-grid +$6 translates to +$2,105/1000h within fires; A5-best vs v41 = +$3,769. The gap (~$1,664/1000h within fires, ~+$5/1000h whole-grid) is heuristic-vs-oracle — refinement candidates queued (alternative tie-breaks for singleton-pair selection and top placement).

**Methodology lesson — single-cell rules ship at <$10/1000h whole-grid lift when the within-fires lift is large.** Rule 11 fires on 0.285% of grid; within-fires lift is +$2,105/1000h. Both numbers are meaningful. Don't dismiss small whole-grid headlines if the per-fire lift is large and the rule is clean (no regression, prefix immune). **Side methodology lesson — single-cell rules at extreme P-rank cells have natural prefix immunity:** J-pair-J has zero canonical IDs < 500K; the rule fires on 0 prefix hands; prefix score guaranteed unchanged. Same precedent as Session 41/43 high_only-zero-prefix observation. **Side methodology lesson — drill the "best-in-class minus production pick" lens to discover single-cell rules:** Drill D's v41-vs-best-in-class table directly identified A5's +$3,769 as 6× the next-best class. Use this lens for future single-cell rule discovery.

---

## Session 47: Rule 12 ships (J-low two_pair both-intact + DS) as v43 — +$35 full / +$66 prefix, largest single-rule lift since v33's Rule 6

Drill B (Session 45) found B1−B2 = +$1,864/1000h within-hand at J-low two_pair. The pattern matched the suit-dominance family from Sessions 44-46 (suit-aware bot when achievable WITHIN the right structural anchor). Session 47 ran two parallel investigations.

**Drill E — Rule 11 heuristic sweep (NEGATIVE result).** Tested 6 simple tie-break combinations for Rule 11 ((LO/HI pair-singletons) × (LO/MID/HI top)). Across n=18,900 J-pair-J fires, v42's V_LOLO is empirically optimal: +$1,975/1000h within fires (+$6.21 whole-grid full); the next-best variant (V_HILO) is +$945/$2.97. No simple variant beats v42; the +$1,794/1000h gap to A5 oracle requires more sophisticated logic. Hard-cap signal — don't burn cycles on more simple sweeps for Rule 11.

**Drill F — two_pair within-class DS variants (DEFINITIVE).** On J-low two_pair (n=262,080, fires=120,960 = 46.2%):

| Variant | Lift vs v42 ($/1000h within fires) | Whole-grid full |
|---|---:|---:|
| **V_HH_BOT** (HH-to-bot tie-break) | **+$1,808** | **+$22.75** |
| V_LL_BOT (LL-to-bot tie-break) | +$1,044 | +$13.14 |
| B1 oracle (ceiling) | +$2,505 | +$50.42 |

HH-to-bot wins by +$764/1000h within fires. A hybrid (HH preferred, LL fallback) covers all 120,960 fires.

**Rule 12 design** — trigger = cat=two_pair AND max≤J AND DS-bot achievable with both pairs intact. Setting builder: try HH-to-bot first (HH 2-cards + 2 singletons completing 2+2 DS), else try LL-to-bot, else fall through to v42. MID = the OTHER pair (anchor preserved); TOP = leftover singleton (deterministic, only 1 left); BOT = chosen pair + 2 chosen singletons.

**Behavioral verification on 30K J-low two_pair sample:** Rule 12 fires on 47.3% (matches Drill F's 46.2%); 100% of fired picks correctly produce DS-bot AND both-pairs-intact; 27.6% of picks differ from v42.

**Per-category breakdown (full grid):**

| Category | v42 | v43 | Δ |
|---|---:|---:|---:|
| two_pair | $3,371 | **$3,211** | **−$160** |
| (all others unchanged) | — | — | $0 |

**Score: $2,727/1000h on full grid. Improvement: −$35 vs v42, −$118 vs v39, −$306 vs v14.** Prefix grid: $1,550 (−$66 vs v42, −$157 vs v39). pct_opt full: 42.20% (+0.27%). pct_opt prefix: 52.61% (+0.80%). Worst-case regret unchanged (max = $5.74). **Largest single-rule full-grid lift since v33's Rule 6 (Session 37, +$113/1000h).**

**Methodology lesson — cross-class within-pop rules from "DS premium within X" lens ship reliably across the whole pair/two_pair domain.** Three rules in the S45-S47 arc share the same mechanism (suit-aware bot when achievable while keeping the pair anchor): Rule 10 v3 (Drill A's A1−A2 = +$2,756 → +$29 ship), Rule 11 (Drill A's A5−A2 = +$2,975 at P=J → +$6 ship), Rule 12 (Drill B's B1−B2 = +$1,864 → +$35 ship). The "within-class DS premium" axis is the project's most productive rule-discovery lens. **Side methodology lesson — HH-to-bot wins over LL-to-bot for two_pair.** Counter to "lowest pair to bot for kicker preservation" intuition. Mechanism: HH in bot creates a stronger 2-pair-with-kicker Omaha hand; LL in mid still anchors Hold'em mid because pair-mid beats most non-pair mid combos. **Side methodology lesson — cumulative ship arcs >$100/1000h come from structural-axis families.** v30→v34 was the ML capacity arc; v39→v43 is the suit-dominance arc. Both are 4-session multi-rule ships sharing one underlying insight from a single methodology breakthrough.

---

## Session 48: Rule 13 ships (three_pair all-intact + DS, MM/HH only) as v44 — three_pair pct_opt +7.8% (largest single-category jump in project)

Drill B's two_pair within-class DS finding suggested the suit-dominance axis might extend to three_pair (114,400 hands, 1.9% of grid). Session 48 ran two parallel investigations.

**Drill G — two_pair max≥Q extension (50K samples per cell). DEFERRED.** Tested extending Rule 12 from max≤J to max=Q, K, A. V_HH_BOT lifts vs v43:

| Cell | V_HH_BOT lift within fires | Whole-grid full | Verdict |
|---|---:|---:|---|
| max=Q | +$1,283 | +$3.06 | extension viable |
| max=K | −$133 | −$0.32 | marginal |
| max=A | −$3,744 | −$9.00 | DON'T extend |

At max=A, even the B1 oracle LOSES to v43's pick. Mechanism: at A-high, putting the A on top is more valuable than the pair-bot DS Omaha play. Designed v43b (max≤Q with HH-only fallback at Q). Grade: full +$14, prefix −$6 with pct_opt drop 52.61%→52.45%. Passes strict 2x ratio gate (0.43x) but qualitative prefix regression deferred.

**Drill H — three_pair within-class DS variants (full pop, n=114,400). DEFINITIVE.** Three_pair all-intact configs: mid=1 pair, bot=2 pairs, top=singleton. 50% of three_pair hands have ≥1 DS-intact configuration. Tested 3 variants:

| Variant | Lift vs v43 within fires | Whole-grid full | Prefix lift |
|---|---:|---:|---:|
| **V_MM_MID** (HH+LL in bot) | **+$2,463** | **+$9.38** | **+$2,787** |
| V_HH_MID (MM+LL in bot) | +$2,227 | +$8.48 | +$1,838 |
| **V_LL_MID** (HH+MM in bot) | **−$4,117** | **−$15.68** | **−$6,542** |
| B1 oracle (ceiling) | +$988 | +$9.40 | +$217 |

**Surprising finding: V_LL_MID is catastrophic** — OPPOSITE the two_pair pattern (Drill F: HH-to-bot wins). At three_pair, LL in mid is too weak a Hold'em hand and the HH+MM bot upgrade can't compensate. The mid-tier strength matters MORE for three_pair because three_pair already has a strong bot.

**Achievability decomposition:** HH_mid only (30%), MM_mid only (30%), LL_mid only (30%, TRAP), all 3 (10%, use V_MM_MID).

**Rule 13 design — trigger:** cat=three_pair AND (MM_mid_DS achievable OR HH_mid_DS achievable). **Skip when ONLY LL_mid achievable** (avoid the V_LL_MID trap). Setting builder priority: MM_mid first → HH_mid second → fall through.

**Behavioral verification on 50K three_pair sample:** Rule 13 fires on 35.1% (matches Drill H's 50% × 70% MM/HH-coverage). 100% of fires correctly produce DS-bot AND all-pairs-intact. 17.4% of picks differ from v43.

**Per-category breakdown (full grid):**

| Category | v43 | v44 | Δ |
|---|---:|---:|---:|
| three_pair | $2,268 | **$1,696** | **−$572** (−25%) |
| three_pair pct_opt | 51.5% | **59.3%** | **+7.8%** (largest single-category jump in project) |
| (all others unchanged) | — | — | $0 |

**Score: $2,717/1000h on full grid. Improvement: −$11 vs v43, −$129 vs v39, −$316 vs v14.** Prefix grid: $1,522 (−$29 vs v43, −$185 vs v39). pct_opt full: 42.34% (+0.14%). pct_opt prefix: 53.06% (+0.45%). Worst-case regret unchanged (max = $5.74).

**Methodology lesson — within-class DS doesn't always favor "highest pairs in bot".** Two_pair (Drill F): HH-to-bot wins. Three_pair (Drill H): HH+MM-to-bot (V_LL_MID) is catastrophic. The distinction: when bot is already strong (three_pair = 2 pairs in bot), mid-tier strength is the binding constraint; when bot needs the upgrade (two_pair = 1 pair + 2 sings), the bot pair-rank matters more. **Side methodology lesson — skip-the-trap design pattern.** Rule 13 explicitly excludes LL_mid-only cases. Don't try to "fix" the trap; just don't fire on it. Same pattern as Rule 12's max≤J gate. **Side methodology lesson — within-category pct_opt jumps are a strong ship signal.** Three_pair pct_opt +7.8% justifies shipping even when whole-grid headline (+$11) is muted by the category's 1.9% share. **The S43-S48 suit-dominance arc has now shipped 5 production rules** (Rule 10 v40b/v3 → Rule 11 → Rule 12 → Rule 13) across 6 sessions, totaling −$129 full / −$185 prefix. The project's largest multi-rule family from a single methodology breakthrough (S44 within-hand pairwise).

---

## Session 49: Trips_pair within-class DS investigation — NO SHIP (methodology lesson)

Continued the suit-dominance "DS premium within X" lens to trips_pair (cat=4, 171,600 hands, 2.86% of grid). Two findings, no production change.

**Drill I (within-hand pairwise, n=171,600) — DEFINITIVE.** v44 already picks pair-bot 85% of fires (60% pair-bot + DS, 25% pair-bot + non-DS). V3 (pair-bot DS) is universally optimal: V3 vs V5 (pair-split DS) = +$13,397/1000h within fires. **v44 vs best-in-V3 = +$1,992/1000h within fires** (the residual oracle gap).

**Drill J (sub-config sweep) — POPULATION-CONFOUNDED.** Tested 7 sub-configs × top variants. Reported V_B_TOP_SING_HI as winner at +$4,293/1000h within fires. **Methodology error:** the variant's mean EV was computed on its achievability subset (n=60,060), while v44's mean was on ALL V3-achievable hands (n=128,700). Cross-class confounding (S44 rule violated).

**Rule 14 attempt (v45) — NO-OP.** Designed v45 to pick V_B_TOP_SING_HI when achievable. Sanity check on 50K trips_pair: Rule 14 fires on 17,498 hands, **differs from v44 on 0 of them** (0%). Grade confirmed: v45 vs v44 = $0/1000h on prefix. **v44 already picks V_B_TOP_SING_HI when achievable** (apparently as a happy accident of v3's Rule 3 tie-break logic for trips_pair).

**Decision:** No ship. v45 retained as artifact. The +$1,992 oracle gap is real but requires a more adaptive heuristic than fixed-variant selection.

**Methodology lessons NEW (Session 49):**
- **Cross-class means are CONFOUNDED — always within-hand pairwise.** Re-iterating S44 because I violated it in Drill J. The variant's mean EV cannot be compared to v44's mean EV unless both are computed on the SAME population.
- **Sanity-check pick-difference rate BEFORE grading.** A simple "does the rule actually pick differently from production?" test catches no-op rules early.
- **The right ship target is "where production differs from oracle".** Not "pick variant X when achievable" but "production picks something OTHER than the oracle's best variant on this hand".
- **Happy-accident upstream tie-breaks can already capture optimization potential.** v3's Rule 3 trips_pair logic was apparently picking V_B_TOP_SING_HI all along.

**Score: $2,717/1000h on full grid (UNCHANGED from v44).** Production state of record remains v44 with cumulative v39 → v44 = −$129 full / −$185 prefix.

---

## Session 50: Rule 14 ships (A-high no-pair, DS/SS HIMID) as v45 — LARGEST SINGLE-RULE LIFT IN PROJECT HISTORY (+$131/1000h)

User direction: scale into the high_only category (the largest unclaimed territory at $833/1000h whole-grid regret contribution). Started with A-high no-pair sub-population.

**Drill K — A-high no-pair characterization (Phase 1, n=660,660 = 11% of grid). DEFINITIVE.**

Mean regret per hand = $3,752/1000h within A-high no-pair → **$412/1000h whole-grid contribution** (single largest residual zone). v44 == oracle on only 22% of A-high no-pair hands. Where the leak is:

| Aspect | v44 | Oracle | Gap |
|---|---:|---:|---|
| TOP = Ace | 100% | 93.13% | v44 over-Aces (rare K/Q/J/2 oracle picks) |
| BOT = DS | 59% | 48% | v44 OVER-DS by 11pp |
| BOT = rainbow | 11% | 0.83% | **v44 picks rainbow 13× too often** |
| BOT = 3+1 | 4% | 14% | v44 UNDER-3+1 |

Best-in-class minus v44 (S46 lens): DS class +$1,937/1000h within fires (+$194 wg), SS +$1,377 (+$138 wg). Rainbow / 3+1 / 4-flush oracle picks all LOSE vs v44 (don't ship those classes).

**Drill L — A-on-top + bot heuristic sweep (Phase 2, 50K sample). DEFINITIVE.**

Tested 7 variants. Critical finding: **HIMID, not HIBOT.** With A on top, the next-best 2 cards (K+Q etc.) belong in MID for Hold'em scoring. The "stack high cards in bot for kicker strength" intuition LOSES (-$847/1000h).

| Variant | Lift within fires | Whole-grid full |
|---|---:|---:|
| **H2_DS_HIMID** | **+$1,016** | **+$6.56** |
| H1_DS_HIBOT | −$847 | −$5.47 |
| **HYBRID HIMID** (DS-HIMID, SS-HIMID fallback) | **+$1,245** | **+$10.06** |
| HYBRID ORACLE upper bound | +$2,505 | +$20.26 |

**Rule 14 design** — trigger = cat=high_only AND max=A AND DS-bot OR SS-bot achievable with A on top. Setting: TOP=A always, try DS-bot first then SS-bot fallback, in both cases use HIMID (mid keeps the 2 highest non-A cards). Else fall through to v44.

**Behavioral verification on 50K A-high sample (S49 sanity-check methodology):**
- Rule 14 fires on 93.6% of A-high no-pair hands
- **v45 differs from v44 on 72.2% of fires** (vs S49's no-op 0%)
- 100% of fires correctly produce A-on-top
- 78% DS bot, 22% SS bot fallback

**Per-category breakdown (full grid):**

| Category | v44 | v45 | Δ |
|---|---:|---:|---:|
| high_only | $4,082 | **$3,439** | **−$643** (−16%) |
| high_only pct_opt | 19.8% | **23.3%** | **+3.5%** |
| (all others unchanged) | — | — | $0 |

**Score: $2,585/1000h on full grid. Improvement: −$131 vs v44, −$260 vs v39, −$448 vs v14.** Prefix grid: $1,522 (UNCHANGED — high_only has zero prefix coverage). pct_opt full: 43.05% (+0.71%). pct_opt prefix: 53.06% (unchanged). p90 regret IMPROVED 0.785→0.745. Max regret unchanged ($5.74).

**Single-rule whole-grid lift records (project history, UPDATED):**

| Rank | Rule | Session | Full lift |
|---|---|---|---:|
| 1 | **Rule 14 (A-high HIMID)** | **S50** | **+$131** |
| 2 | Rule 6 (pure trips, v33) | S37 | +$113 |
| 3 | Rule 10 (J-low pair, v40b) | S43 | +$48 |
| 4 | Rule 7 (three_pair, v37) | S41 | +$43 |
| 5 | Rule 12 (J-low two_pair, v43) | S47 | +$35 |

**Methodology lesson — high_only is the project's biggest residual zone.** The defensive arc (Rules 10-13) covered paired weak hands (max≤J pair/two_pair/three_pair). High_only had no rules at all and yielded the project's biggest single ship. **Side methodology lesson — HIMID > HIBOT for A-high.** Counter to obvious intuition. With A on top, Hold'em mid is more valuable than Omaha bot kicker rank — bot's value comes from suit (DS), not absolute rank. **Side methodology lesson — drill estimates can underpredict actual ship lift.** Drill L estimated +$10/1000h whole-grid; grader measured +$131. The drill's heuristic was less ambitious than the implementation, AND v44's actual baseline was weaker than the drill subset suggested. **Side methodology lesson — S49's sanity-check (pick-difference rate vs production) is the project's most important diagnostic.** v45 differs from v44 on 72.2% of fires (vs S49's 0% no-op). Always verify before grading. **The S43-S50 arc** has now shipped 6 production rules totaling −$260 full / −$185 prefix — the project's largest multi-rule family by both ship count and total lift.

---

## Session 51: Rule 15 ships (K-high no-pair, DS/SS HIMID) as v46 — 3rd-LARGEST single-rule lift in project history (+$51/1000h)

Continued the high_only attack from Session 50. Applied same Drill K + Drill L methodology to K-high no-pair (the 2nd-largest residual zone after A-high).

**Drill M — K-high no-pair characterization (Phase 1, n=330,330 = 5.5% of grid). DEFINITIVE.**

Mean regret per hand = $4,114/1000h within K-high → **$226/1000h whole-grid contribution** (2nd-largest residual zone). v45 == oracle on only 18.6% of K-high hands.

Critical difference vs A-high: oracle picks K on top only **66.23%** of the time (vs A on top 93%). The other 34% includes Q-on-top (12%), J-on-top (5%), and defensive 2-on-top (7%). K is borderline for top tier (loses to A but wins vs Q-or-lower).

Best-in-class minus v45 (S46 lens):
- DS class: +$2,999/1000h within fires (+$150 wg ceiling) — LARGER per-fire than A-high's +$1,937
- SS class: +$1,790/1000h within fires (+$90 wg ceiling)
- 3+1 ≈ break-even, rainbow / 4-flush LOSE

**Per-2nd-highest stratification:** 2nd=Q is dominant zone (55% of K-high pop, $4,408/1000h regret); oracle K-on-top only 64% there.

**Rule 15 design** — parallel to Rule 14: trigger = cat=high_only AND max=K AND DS-bot OR SS-bot achievable with K on top. Setting builder: TOP=K always, try DS-bot first then SS-bot fallback, HIMID tie-break.

**Behavioral verification on 50K K-high sample (S49 sanity-check methodology):**
- Rule 15 fires on 95.8% of K-high hands
- v46 differs from v45 on 65.6% of fires
- 100% K-on-top, 79% DS bot, 21% SS bot fallback

**Per-category breakdown (full grid):**

| Category | v45 | v46 | Δ |
|---|---:|---:|---:|
| high_only | $3,439 | **$3,187** | **−$252** (−7.3%) |
| high_only pct_opt | 23.3% | **24.2%** | **+0.9%** |
| (all others unchanged) | — | — | $0 |

**Score: $2,534/1000h on full grid. Improvement: −$51 vs v45, −$311 vs v39, −$499 vs v14.** Prefix grid: $1,522 (UNCHANGED — high_only zero prefix coverage). pct_opt full: 43.24% (+0.19%). p90 regret IMPROVED 0.745 → 0.730. Max regret unchanged ($5.74).

**Updated single-rule whole-grid lift records:**

| Rank | Rule | Session | Full lift |
|---|---|---|---:|
| 1 | Rule 14 (A-high HIMID) | S50 | +$131 |
| 2 | Rule 6 (pure trips, v33) | S37 | +$113 |
| 3 | **Rule 15 (K-high HIMID)** | **S51** | **+$51** |
| 4 | Rule 10 (J-low pair, v40b) | S43 | +$48 |
| 5 | Rule 7 (three_pair, v37) | S41 | +$43 |

**Methodology lesson — the Drill K + Drill L playbook generalizes across high-card sub-pops.** Same methodology produced both Rule 14 and Rule 15 with parallel structure: characterization → "best-in-class minus production" → HIMID heuristic. **Side methodology lesson — high-rank sub-pops have known coverage gaps.** Rule 15 v1 addresses ~66% of K-high optimally; the 34% "non-K-on-top" sub-zone is residual. Pattern likely repeats for Q-high (oracle prefers non-Q on top even more often). **Side methodology lesson — per-fire lift can exceed prior sub-pop's** even with smaller whole-grid lift, due to population size. **The S43-S51 arc** has now shipped 7 production rules totaling −$311 full / −$185 prefix — average ship −$44/1000h per rule.

---

## Session 52: Rule 16 ships (Q-high no-pair, DS/SS HIMID) as v47 — completes the A/K/Q-high HIMID family (+$19/1000h)

Continued the high_only attack from Sessions 50-51. Same Drill K + Drill L methodology applied to Q-high (3rd-largest high_only sub-population at 2.5% of grid).

**Drill N — Q-high no-pair characterization (n=150,150). DEFINITIVE.**

Mean regret = $4,488/1000h within Q-high → $112/1000h whole-grid contribution. v46 == oracle on only 15.8% of Q-high hands.

Critical finding: **Q-on-top is borderline.** Oracle picks Q on top only **49.37%** (vs A 93%, K 66%). The other 51% includes J-on-top (10%), defensive 2-on-top (16%), T (4%), 3 (8%).

Best-in-class minus v46:
- DS: +$3,604/1000h within fires (+$82 wg ceiling) — biggest per-fire DS lift in the arc
- SS: +$2,196 (+$50 wg ceiling)
- **3+1: +$502 (+$11 wg)** — positive for first time in the high_only arc

**Rule 16 design** — parallel to Rules 14/15: trigger = cat=high_only AND max=Q AND DS-bot OR SS-bot achievable with Q on top. Setting builder: TOP=Q always, try DS-bot first then SS-bot fallback, HIMID tie-break.

**Behavioral verification on 50K Q-high sample:** Rule 16 fires on 97.2% of Q-high hands; v47 differs from v46 on 58.5% of fires; 100% Q-on-top, 80% DS bot, 20% SS bot fallback.

**Per-category breakdown (full grid):**

| Category | v46 | v47 | Δ |
|---|---:|---:|---:|
| high_only | $3,187 | **$3,096** | **−$91** (−2.9%) |
| high_only pct_opt | 24.2% | **24.5%** | **+0.3%** |

**Score: $2,515/1000h on full grid. Improvement: −$19 vs v46, −$330 vs v39, −$518 vs v14.** Prefix grid: $1,522 (UNCHANGED). pct_opt full: 43.30% (+0.06%). p90 regret: 0.730 → 0.725.

**Three-session high_only sub-arc (S50-S52) — diminishing returns:**

| Session | Sub-pop | Pop % | Top oracle % | Δ Full | Per-fire DS lift |
|---|---|---:|---:|---:|---:|
| S50 | A-high | 11% | 93% | −$131 | +$1,937 |
| S51 | K-high | 5.5% | 66% | −$51 | +$2,999 |
| S52 | Q-high | 2.5% | 49% | **−$19** | +$3,604 |
| **Combined** | A+K+Q-high | 19% | — | **−$201** | (rising per-fire, falling pop) |

Per-fire DS lift INCREASES across sub-pops (worse top-card → larger v44/v45/v46 baseline gap), but pop size DECREASES, leading to shrinking absolute ships. J-high estimated +$8-12 — below threshold for further single-pop drills.

**Methodology lesson — the high_only single-pop arc has diminishing returns.** Each successive sub-pop ships less whole-grid lift due to shrinking population. Future Rule v2's that address non-default top picks (the 7%/34%/51% gaps in Rules 14/15/16) may yield more value than continuing to drill smaller sub-pops. **Side methodology lesson — 3+1 transitions from negative to positive at Q-high.** As top-card oracle fraction drops, oracle considers more bot suit profiles. Rule v2 candidates might add 3+1 fallback. **Side methodology lesson — the simple HIMID heuristic is a robust pattern across A/K/Q-high.** Same code structure with only the rank constant changing. **The S43-S52 arc** has now shipped 8 production rules totaling −$330 full / −$185 prefix.

## Session 56: v42_dt new ML champion via the S54 playbook applied to high_only zone (+$79 full / $0 prefix vs v41_dt)

Sessions 54 + 55 had shipped v39 → v40 → v41 by applying a 4-phase diagnostic-driven feature engineering playbook to the pair, trips_pair, and two_pair zones. Session 56 applied the same playbook to the largest remaining residual: high_only at $2,796/1000h within-category, 40.4% of population, ~63% of v41's whole-grid regret. User-prediction was that high_only would need DIFFERENT feature types (top-card placement, defensive triggers, broadway connectivity, three-of-a-suit clustering); reality is that the dominant high_only blind spot turned out to be the same DS-routing pattern as prior zones.

**Phase 1: Drill HO (v41 vs oracle mismatch matrix over all 1,226,940 high_only hands).** Total mismatch contribution $481/1000h whole-grid (matches expected $486 from within-cat × population). Top single-class mismatch: v41 picks `tA_SS_mu` (Ace top, single-suited bot, mid unsuited) while oracle picks `tA_DS_ms` (Ace top, double-suited bot, mid suited) — 28,014 hands @ $7,774 mean regret = $36.24/1000h whole-grid. Collapsed by bot-suit-profile swap: **SS → DS = 236,205 hands @ $5,344 mean = $210.08/1000h** (44% of all high_only mismatch contribution). v41 over-routes SS by +14.68% absolute and under-routes DS by −15.51% absolute. 92% of high_only residual concentrates in 6 broadway (h1, h2) cells: AK $143.64, KQ $92.08, AQ $75.35, QJ $50.58, KJ $44.09, AJ $36.18.

**Phase 1b: Drill HO2 (hand-level inspection of 28,014 mismatches in tA_SS_mu → tA_DS_ms).** The cleanest Phase 1b validation in the project: **100% of mismatches have ho_v2_bot_DS_max_top_rank = A** (Ace-top + DS-bot is ALWAYS achievable), AND **100% of oracle picks USE that max_top** (oracle never sacrifices the Ace). 0% pick min_top. Suit distributions: 82.7% have (3,2,2,0) yielding 7 DS configs each; 17.3% have (2,2,2,1) yielding 3 DS configs each. The structural delta is fully explained by the DS-routing axis — feature design target is unambiguous.

**Phase 2 v2: high_only_aug_v2 (4 rank-valued features mirroring pair_aug_v5 / trips_pair_v2 / two_pair_v2 patterns):** `ho_v2_bot_DS_n_configs_g` (count of 4-card bot subsets that are 2+2 DS, enumerating C(7,4)=35 subsets), `ho_v2_bot_DS_max_top_rank_g` (best leftover-max rank across DS configs), `ho_v2_bot_DS_min_top_rank_g` (lowest leftover-max rank — captures whether sacrificing the highest card is required), `ho_v2_bot_DS_max_mid_sum_g` (best mid rank-sum across DS configs). All zeros for non-high_only hands. v42_dt training: 99 features (95 + 4), depth=36 ml=1, **2,109,330 leaves (+4.7% over v41's 2.02M)** — modest growth, surgical to high_only. **3 of 4 new features in top-32 importance** (#26 max_mid_sum 0.28%, #31 max_top 0.22%, #32 min_top 0.21%, #80 n_configs 0.03%) — deeper integration than S55's t2p_v2 family (#24/26/30/73).

**v42 grade:** $1,192 full / $686 prefix vs v41's $1,270 / $686. **Lift: −$79 full / $0 prefix.** Full-grid pct_opt 62.18% → 63.08% (+0.91%); p90 0.450 → 0.425; p99 1.075 → 1.035. **High_only within-cat $2,796 → $2,411 (−$385, −13.8%); high_only pct_opt 29.0% → 33.4% (+4.4%).** All other 7 categories byte-identical to v41 on both grids. **Prefix-grid neutrality is by design, not regression** — the prefix slice (500K canonical hands) contains zero high_only hands, so gated features mathematically guarantee identical metrics on non-targeted populations.

**Cumulative v32 → v42 = −$524 full / −$218 prefix** across 7 ML ships. v42 is the 4th-largest single ML ship (after v39 −$237, v41 −$124, v34 −$34).

**Why high_only collapsed only 13.8% (vs 60-69% for prior zones):** Prior zones had a single dominant structural axis that the v2/v5 feature shape captured nearly completely. high_only has multiple structural axes — DS-routing was the biggest ($210/1000h whole-grid contribution out of $481), but other axes remain (top-card placement at non-Ace ranks contributing the SS→SS $80 and 31→DS $36 swaps; broadway connectivity at non-Ace tops; defensive triggers; three-of-a-suit clustering). The current 4 features address the DS-routing axis surgically; future v43+ work can target the remaining $271/1000h.

**Methodology lessons (Session 56):**
- **The 4-phase playbook is fully transferable to the largest population zone (40.4% of canonical hands) without modification.** Same drill shape, same hand-level shape, same v2 feature shape, same depth=36 ml=1 hyperparams.
- **Phase 1b can be a 100% confirmation, not just 70-90%.** When feature design exactly matches the structural delta, the percentages collapse to 100/0. Prior sessions had aggregates like "72% have suit overlap" or "85.7% have R2 routing" — S56's "100% have max_top=A AND 100% of oracle picks use it" is the strongest Phase 1b validation in the project.
- **Surgical gating means prefix-grid neutrality is correct, not suspect.** When new features are gated to a category absent from the prefix slice, prefix Δ = $0 by construction. Pre-flight "2× ratio" gates only apply when both grids contain the target population.
- **User-prediction "different feature types needed" was partially correct, partially wrong.** The dominant high_only blind spot was the SAME DS-routing pattern as prior zones — Ace-top is preserved in 100% of dominant-class mismatches; the structural error is purely the bot suit profile. **Generalizable lesson: when an existing feature family (DS-bot achievability) is missing entirely from a zone, that gap dominates even when other axes also exist.**
- **Single-axis ships have predictable leaf growth.** v42's +4.7% leaves vs v41's +32% reflects population × axis-count × info-content. high_only has 40% population but the single DS axis touches a narrower split surface than two_pair's Layout B/C asymmetry.

**End of S56:** Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix). ML champion v42_dt at $1,192 full / $686 prefix. The two production tracks now diverge by **$1,306/1000h** — the ML champion beats the human-memorizable rule chain by more than half its EV deficit. **high_only remains the dominant residual** ($2,411 within-cat × 40.4% share = $975/1000h whole-grid = ~82% of v42's total regret) — the next session can continue compressing it via additional axes (top-card placement at non-Ace ranks, broadway connectivity, etc.) or pivot to trips ($55 whole-grid) / three_pair ($35 whole-grid).

### Session 56 extracted playable hierarchy for high-only hands

Combining v52's rule chain with the S56 ho_v2 finding ("when DS-bot is achievable, take it AND keep your max card on top"), the full high-only strategy at end of S56 is:

| Max card | # of hands | Population share | Action |
|---|---:|---:|---|
| **A** | 660,660 | 11.0% | **Ace on top.** Try DS bot (Ace kept OUT of bot); if no DS achievable, SS bot fallback. Mid = HIMID (the 2 highest remaining cards). |
| **K** | 330,330 | 5.5% | **King on top** *unless* 2nd-high ≤ 8 (then defensive). DS bot preferred, SS fallback. HIMID tie-break. |
| **Q** | 150,150 | 2.5% | **Q on top** *unless* 2nd-high ≤ 8 (then defensive). DS bot preferred, SS fallback. HIMID tie-break. |
| **J** | 90,090 | 1.5% | HIMID by default; defensive when 2nd-high ≤ 8. |
| **T** | 40,040 | 0.7% | **Always defensive.** Lowest card on top, DS bot, HIMID. |
| **9** | 15,015 | 0.25% | Always defensive. |
| **8** | 4,290 | 0.07% | Always defensive. (Only rank pattern: 8-7-6-5-4-3-2.) |

Floor: max = 8 is the lowest possible high-only since you need 7 distinct ranks and the ranks below 8 are {2,3,4,5,6,7}=6 values. **Total: 1,290,615 hands = ALL high-only canonical hands.**

**Three terms:**
- **HIMID** ("High in Mid"): after committing top, put the **next two highest** cards in mid; the 4 lowest non-top cards go to bot.
- **Defensive**: put the **lowest** card on top (not the highest); high cards go to mid + bot where they're worth more points. Right when your max card can't reliably win the top tier.
- **DS bot**: 4-card bot with suit pattern 2+2 (two of one suit + two of another). Best Omaha pattern — gives two independent flush draws.

**Master 5-step hierarchy:**
1. Max = A? → Ace on top; DS bot first, SS fallback; HIMID.
2. Max ∈ {K, Q} and 2nd-high ≥ 9? → Max on top; DS bot first, SS fallback; HIMID.
3. Max ∈ {K, Q} and 2nd-high ≤ 8? → Defensive.
4. Max = J? → HIMID with defensive switch at 2nd-high ≤ 8.
5. Max ∈ {T, 9, 8}? → Always defensive.

**The S56 sharpening:** for max=A/K/Q the rule chain already said "max on top, DS first." But v41 wasn't always *finding* the DS routing — in 100% of 28,014 worst-case `tA_SS_mu → tA_DS_ms` mismatches, a DS bot was achievable with Ace preserved on top and oracle used it 100% of the time. The 4 new `ho_v2_bot_DS_*` features explicitly expose that signal to the ML; v42 now sees it.

### Where Session 57 should push (the headroom)

The hierarchy table above is good but not perfect. Three specific axes remain unaddressed:

1. **Defensive trigger at max ∈ {K, Q}** ($67 + $24 = $91/1000h whole-grid pre-v42 in tK→tK and tQ→tQ mismatches; smaller now but non-zero). v42 still over-picks "King on top" in some hands where oracle wants a defensive 2-on-top. Refinement candidate: a feature that signals "even with K/Q max, the supporting structure is weak — go defensive."
2. **Defensive top-card choice on T-9-8** (~$60/1000h whole-grid combined). When defensive play is right, the question of *which* low card goes on top (the absolute lowest? a 2 vs a 3?) still has sub-optimality. Feature candidate: rank-valued "best defensive top-card given mid/bot structure."
3. **Broadway connectivity at non-Ace tops** (within the AKQ/KQJ/QJT-type hands). When 7 cards almost form a straight, the mid Hold'em equity from the connector cards might outweigh DS-bot value. Feature candidate: "mid Hold'em equity given best-DS-bot routing."

**Total headroom in high-only alone is still ~$975/1000h whole-grid** (= v42's high-only contribution). Each of the 3 axes above is plausibly worth $50-150/1000h whole-grid if cracked the way v42 cracked the DS-routing axis.

**Alternative S57 targets** (smaller but cleaner playbook fits): trips zone ($55/1000h whole-grid) or three_pair zone ($35/1000h whole-grid) — same drill + 4-feature shape applies.

Current S57 priority recommendation: **stay in high_only and run a second pass.** The playbook is now mature, the diagnostic infrastructure is in place, and there's $200+/1000h of plausible whole-grid lift across the three high_only sub-axes.

---

## Session 58: v44_dt new ML champion via the S54 playbook applied to high_only zone — THIRD PASS (+$42 full / $0 prefix vs v43_dt)

Session 57 had collapsed the high_only zone for the second time via 4 ho_v3 features (DS bot + ms mid joint achievability with top=max), shipping +$69 full / $0 prefix and reducing high_only within-cat from $2,411 → $2,075. Session 58 took the user's S57 review directive: characterize WHAT oracle picks for the Omaha (bot) hand vs the Hold'em (mid) hand across EVERY max-rank × structural-achievability cell, then design ho_v4 from the deepest residual axis revealed.

**Five drills (HO5–HO10) on all 1,226,940 high_only hands.** All orchestrated to share a single per-hand sweep where possible. Total drill compute: ~10 min wall time.

**Drill HO5 — per-max-rank residual stratification.** A: 660,660 hands @ $1,831 = $201/1000h whole-grid (47% of high_only's total). K: $123/1000h. Q: $62. J: $26. T: $8. 9: $2. 8: $0.32. A/K/Q together = 87% of high_only's whole-grid regret.

**Drill HO6 — structural cell cross-tabulation.** 7 mutually-exclusive cells per max-rank: JOINT_HIGH/MED/LOW (where joint with top=max is achievable, stratified by best mid_high), DS_NO_JOINT (DS-bot+top=max achievable but no joint), DS_NO_MAXTOP (DS only via putting max in bot), MS_ONLY (no DS, but max-on-top ms_mid exists), NEITHER. **`DS_NO_JOINT` is structurally constant at 62.9% × every max-rank** — and the dominant residual cell, contributing $293/1000h whole-grid summed across max-ranks (~69% of all high_only regret). At max=A alone, `DS_NO_JOINT` contributes **$140/1000h whole-grid** (>50% of high_only's residual).

**Drill HO7 — what oracle ACTUALLY picks per cell.** For each (max-rank × cell), oracle's TOP/BOT/MID profile + top mismatch class. Key findings:
- A × `DS_NO_JOINT` (n=415,800; pct_opt 37.6%): oracle picks DS:52%, SS:38%, 31:10%; v43 picks SS:50%, DS:42% — **under-routes DS by 10%**. Mid_suited rate 41% (oracle) vs 31% (v43). Top mismatch globally: `tA_SS_mu → tA_DS_mu` n=34,726 @ $4,336 = **$25.06/1000h**.
- K × `DS_NO_JOINT` (n=207,900): oracle drops K off the top **34% of the time** (66% K-on-top vs v43's 87%). v43 over-keeps max-rank on top by 21% in this cell at K and Q.
- Q × `DS_NO_JOINT` (n=94,500): oracle keeps Q on top only 48%, v43 68%.
- J/T/9/8 × `DS_NO_JOINT`: oracle keeps max-on-top only 24%/11%/4%/0% — overwhelmingly puts max-rank into the bot or mid.

**Drill HO8 — Omaha-first vs Hold'em-first vs joint per max-rank.** For each oracle joint-pick, ranked the chosen joint config among all candidate joints by bot pair_high (descending) and mid_high (descending). **Within JOINT picks, oracle is mid-first** (mean mid_pct 0.67 at A → 0.81 at 8 vs bot_pct 0.36 at A → 0.24 at 8). **Joint take-rate collapses with lower max-rank** (A:95% → K:86% → Q:76% → J:54% → T:36% → 9:22% → 8:13%). At max=A, when oracle skips joint, **54% of alts are `tmax_4f_ms`** — top=A, 4-flush bot, suited mid. v43 has no 4f route signal.

**Drill HO9 — DS-vs-SS threshold per max_rank.** Stratified joint-achievable hands by `best_ms_mid_high` and oracle's pick class. Joint take-rate threshold: at A, oracle takes joint 95% across all mid_high; at K, 67-88% (drops with low mid_high); at Q, crosses 50% near mid_high=7; at J, only above mid_high=9; at T/9/8, joint is rarely picked. **Strong signal: when `best_DS_bot_pair_high == max_rank` (the DS bot would contain max-rank as a suited pair), oracle increasingly prefers DS_NONJOINT** (at K: 11.1%, Q: 22.4%, J: 44.3%, T: 61.0%, 9: 72.8%). v43 has no such signal.

**Drill HO10 — non-max-top joint enumeration.** **47.7% of high_only hands have a non-max-top joint achievable** — consistent across every max-rank by suit-symmetry. v43's ho_v3 features only count joints with top=max, so this entire 47.7% population is invisible to the model. At lower max-ranks where DS_NONJOINT take-rate is 48-65%, this route dominates oracle's pick distribution.

**Phase 2: high_only_aug_v4 (4 rank-valued features encoding three structural axes invisible to v43).**
- `ho_v4_topMax_DS_max_bot_pair_high_g` (0..13): best higher-of-suited-pair in DS bot when top=max — DS bot quality signal for `DS_NO_JOINT` cell discrimination.
- `ho_v4_topMax_4f_ms_max_mid_high_g` (0..13): best mid_high in (top=max, 4f bot, ms mid) configs — Ace-high 4f route quality.
- `ho_v4_topNonMax_DS_ms_n_configs_g` (0..30): count of non-max-top joint configs (max in bot or mid) — the "max-into-bot" route population.
- `ho_v4_topNonMax_DS_ms_max_top_rank_g` (0..13): best non-max top rank achievable in those joints.

All zero outside high_only (gated). v44_dt training: 107 features (103 + 4), depth=36 ml=1, **2,248,173 leaves (+3.2% over v43's 2.18M)** — modest growth, surgical to high_only. Feature importance #47/#80/#93/#95 (0.13%/0.04%/0.01%/0.01%) — low individually, with the non-max-top joint quality (`max_top_rank_g`) ranking highest. The 4f and DS bot pair_high features rank lower (target narrower populations) but still contribute.

**v44 grade:** $1,081 full / $686 prefix vs v43's $1,123 / $686. **Lift: −$42 full / $0 prefix.** Full-grid pct_opt 63.99% → 64.80% (+0.81%); p90 0.400 → 0.390; p99 0.980 → 0.970. **High_only within-cat $2,075 → $1,868 (−$207, −10.0%); high_only pct_opt 37.9% → 41.8% (+3.9%).** All other 7 categories byte-identical to v43 on both grids — surgical gating confirmed.

**Three-session high_only collapse (S55 → S58):** $2,796 → $2,411 → $2,075 → $1,868 = **−$928 within-category (−33.2%) over 3 sessions, −$378/1000h whole-grid contribution.** Composing three conditional axes (DS-only via ho_v2, DS+ms-joint via ho_v3, DS-quality + non-max-joint + 4f via ho_v4) compresses the same zone three times without surgical interference between the axes.

**Cumulative v32 → v44 = −$634 full / −$218 prefix** across 9 ML ships. **Score: v44_dt $1,081 full / $686 prefix (was v43_dt $1,123 / $686). Improvement: −$963 vs v16 ($2,044) full, −$1,167 vs v14 ($2,248) full.** The ML champion now beats the v52 rule chain ($2,498 full) by **$1,417/1000h** — more than half the rule-chain EV deficit.

**MUST-PRODUCE deliverable also shipped:** `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` at repo root. A per-max-rank × per-cell decision matrix documenting oracle's TOP/BOT/MID picks with trade-off rules and v43's mistake patterns — answering the user's S57 review question independently of whether v44 shipped.

**Methodology lessons (Session 58):**
- **The 4-phase playbook is transferable to the SAME zone for a THIRD pass without modification.** Re-drilling against the new champion (v43, post-S57 collapse) revealed the residual had shifted axis (DS+ms joint → DS bot quality + non-max-top joint + 4f route) without changing in zone.
- **A zone can be collapsed at least three times by stacking conditional feature axes.** Each session adds a NEW conditional axis; gains compound: $2,796 → $1,868 (−$928, −33.2%).
- **The decision matrix is a separable deliverable from the ML ship.** Even if v44 had not shipped, the decision matrix doc would have answered the user's review.
- **5 drills can run as 4 scripts sharing one sweep.** HO5+HO6+HO7 consolidated; HO8/HO9/HO10 standalone (or read the parquet from HO5+HO6+HO7).
- **"Omaha first or Hold'em first?" has a nuanced answer.** WITHIN joint, mid-first (mid_high preferred over bot pair_high). OUTSIDE joint at lower max-ranks, bot-first (max-rank moves into bot to enable a stronger DS configuration with a lower top).

**End of S58:** Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix). ML champion v44_dt at $1,081 full / $686 prefix. The two production tracks now diverge by $1,417/1000h. **high_only is STILL the dominant residual** ($1,868 within-cat × 40.4% share = $755/1000h whole-grid = ~70% of v44's total regret) — Session 59's highest-leverage target is either a 4th-pass on high_only (deepest residual cell now: `DS_NO_JOINT` at K/Q where the "max-off-top" pattern is biggest) or pivot to trips ($1,194 within-cat × 4.6% share = $55/1000h whole-grid) for diversification.

---

## Session 57: v43_dt new ML champion via the S54 playbook applied to high_only zone — SECOND PASS (+$69 full / $0 prefix vs v42_dt)

Session 56 had collapsed the high_only DS-routing axis via 4 ho_v2 features (DS-bot achievability + max-top quality), shipping +$79 full / $0 prefix and reducing high_only within-category from $2,796 → $2,411 (−13.8%). Session 57 took the user's recommendation to "stay in high_only and run a second pass" — the playbook is now mature, the diagnostic infrastructure is in place, and the residual is still dominant ($975/1000h whole-grid = ~82% of v42's regret).

**Phase 1: Drill HO3 (v42 vs oracle mismatch matrix over all 1,226,940 high_only hands).** The KEY counterintuitive finding: **the SAME SS→DS bot-suit-swap pattern is STILL the dominant residual** even after S56's ho_v2 features. v42 picks SS bot 46.07% vs oracle 32.04% (−14.0% absolute under-routing of DS, vs v41's −15.5%; ho_v2 helped only marginally). **SS → DS = 224,353 hands @ $5,071 mean = $189.33/1000h whole-grid contribution.** Top single-class mismatch: v42=tA_SS_mu, oracle=tA_DS_ms — 28,027 hands @ $7,534 mean regret = $35.14/1000h. This class **barely moved from v41** (28,014 hands @ $7,774). User-prediction axes for S57 (defensive K/Q triggers, T-9-8 top choice, broadway connectivity) were NOT the dominant residual — the structural blind spot remained on the SS→DS axis but with a NEW dimension. Two new mismatch classes emerged that point at it: tA_SS_mu → tA_DS_mu ($25.61, n=35,332) is bot-suit-only (mid stays unsuited); tA_SS_mu → tA_SS_ms ($23.68, n=33,559) is **mid-suit-only** (bot stays SS). The latter is the new signal: mid-suiting is a separate axis ho_v2 doesn't expose.

**Phase 1b: Drill HO4 (hand-level inspection of all 28,027 v42=tA_SS_mu, oracle=tA_DS_ms mismatches).** **100% of mismatches have a (DS bot + suited mid) JOINT config achievable WITH the Ace on top.** 18% have 3 joint configs, 82% have 9 joint configs. DS_AND_ms_max_top = A in 100% of cases (existing ho_v2_bot_DS_max_top_rank_g also fires at 14, so the existing feature alone is not differentiating). Oracle's actual mid_high distribution spans the full range (K 22%, Q 19%, J 17%, T 14%, …, 3 at 0.9%). **Diagnosis: v42 has DS-bot achievability features but NOT joint (DS bot + ms mid) achievability features.** The DT can split on "DS bot achievable + max_top=A" but cannot compose "DS bot AND mid suited at the same time, with what mid quality."

**Phase 2 v3: high_only_aug_v3 (4 rank-valued features encoding JOINT achievability + quality, conditional on top = max-rank-of-hand).** For each high_only hand, fix top = max-rank-of-hand. Enumerate the C(6,4)=15 4-card subsets of the remaining 6 cards as candidate bots. Filter to (a) bot is 2+2 (DS), (b) the 2 leftover cards (mid) share a suit. Aggregate count + mid quality:
  - `ho_v3_topMax_DS_ms_n_configs_g` (0..15): joint achievability count.
  - `ho_v3_topMax_DS_ms_max_mid_high_g` (0..13): best higher-card-of-suited-mid across joint configs.
  - `ho_v3_topMax_DS_ms_min_mid_high_g` (0..13): lowest higher-card-of-suited-mid (range signal).
  - `ho_v3_topMax_DS_ms_max_mid_sum_g` (0..25): best sum of suited mid pair.

All zero outside high_only (gated). Only **14.7% of high_only hands** have any joint config — but those hands include nearly all of the dominant SS→DS mismatch class.

v43_dt training: 103 features (99 + 4), depth=36 ml=1, **2,177,798 leaves (+3.2% over v42's 2.11M)** — modest growth, surgical to high_only. **Feature importance is the LOWEST per-ship in the project: #63 min_mid_high (0.07%), #64 max_mid_sum (0.07%), #100 max_mid_high (0.01%), #102 n_configs (0.00%).** Yet the lift is real.

**v43 grade:** $1,123 full / $686 prefix vs v42's $1,192 / $686. **Lift: −$69 full / $0 prefix.** Full-grid pct_opt 63.08% → 63.99% (+0.91%); p90 0.425 → 0.400; p99 1.035 → 0.980. **High_only within-cat $2,411 → $2,075 (−$336, −13.9%); high_only pct_opt 33.4% → 37.9% (+4.5%).** All other 7 categories byte-identical to v42 on both grids — surgical gating confirmed.

**Two-session high_only collapse (S55 → S57):** $2,796 → $2,411 → $2,075 = **−$721 within-category (−25.8%) over 2 sessions, −$291/1000h whole-grid contribution.** Composing two conditional axes (DS-only via ho_v2, then DS+ms-joint via ho_v3) compresses the same zone twice without surgical interference between the axes.

**Cumulative v32 → v43 = −$592 full / −$218 prefix** across 8 ML ships. **Score: v43_dt $1,123 full / $686 prefix (was v42_dt $1,192 / $686). Improvement: −$921 vs v16 ($2,044) full, −$1,125 vs v14 ($2,248) full.** The ML champion now beats the v52 rule chain ($2,498 full) by **$1,375/1000h** — more than half the rule-chain EV deficit.

**Methodology lesson — the 4-phase playbook is transferable to the SAME zone for a SECOND pass.** Re-drilling against the new champion (v42, post-S56 collapse) revealed the residual had shifted in axis (DS-only → joint DS+ms) without changing in dominant top-rank or zone. The same playbook applied without modification. **Side lesson — a zone can be collapsed multiple times by stacking conditional feature axes.** S56's ho_v2 (DS bot only) + S57's ho_v3 (DS bot AND ms mid) compose; each pass adds a NEW conditional axis to the same zone, and the gains compound. **Side lesson — joint achievability is a distinct structural axis from single-axis achievability.** ho_v2 exposes "is DS bot achievable" but the DT couldn't compose "DS bot AND mid suited" from existing features alone. Joint features are NOT redundant with the components — they expose joint structure that's invisible when only individual axes are exposed. **Side lesson — feature importance and impact decouple under surgical gating.** v43's 4 features at #63/#64/#100/#102 individual importance is the lowest-per-ship on record, yet they ship +$69. Importance ≠ impact when features fire on a narrow but high-leverage subset. **Side lesson — user predictions can be wrong about WHICH axis dominates, even after one pass collapses one axis.** The user predicted defensive triggers, T-9-8 top choice, and broadway connectivity for S57; reality was a mid-suit-aware joint refinement of the same SS→DS axis. The data dictates the axis, not the human intuition.

---

## Session 55: TWO ML champions in one session — v40_dt + v41_dt via the S54 playbook applied to trips_pair + two_pair zones (+$142 full / +$115 prefix cumulative)

Session 54 had shipped v39_dt by applying a diagnostic-driven feature engineering playbook to the pair zone, with the explicit hypothesis that the methodology would generalize. Session 55 tested that hypothesis on the next two largest within-category residuals: trips_pair ($909/1000h) and two_pair ($918/1000h). Both shipped.

**Track A — trips_pair (v40_dt). Phase 1: Drill TP (v39 vs oracle mismatch matrix over all 171,600 trips_pair hands).** Top mismatch: v39 picks `Pbot_SS` while oracle picks `Pbot_DS` — 10,398 hands @ $3,580 mean regret = $6.20/1000h whole-grid contribution. Class distribution: v39 over-picks `Pbot_SS` (+8.27%) and under-picks `Pbot_DS` (−9.10%).

**Phase 1b: Drill TP2 (hand-level inspection over 10,398 mismatches).** 100% of mismatch hands have pair with 2 distinct suits. Three Pbot_DS routings exist: R1 (bot = pair + 2 sings filling pair-suits), R2 (bot = pair + 1 trip + 1 sing), R3 (bot = pair + 2 trip cards). v39's existing `tp_pair_routing_is_ds_g` captures only R1 — available in only **0.3%** of mismatch hands. R2 is available in **85.7%**, R3 in **59.0%**. v39 was BLIND to R2 and R3.

**Phase 2 v2: trips_pair_aug_v2 (4 rank-valued features mirroring pair_aug_v5 pattern):** `tp_v2_bot_DS_n_configs_g` counts ALL routings (R1+R2+R3), `tp_v2_bot_DS_max_top_rank_g` best top across configs, `tp_v2_bot_DS_min_top_rank_g` lowest, `tp_v2_bot_DS_max_mid_sum_g` best mid rank-sum. v40_dt training: 91 features, depth=36 ml=1, 1.57M leaves (+3.4% over v39). Feature importance 0.02-0.04% each — low individually but the gated reshape is surgical.

**v40 grade:** $1,394 full / $772 prefix vs v39's $1,412 / $801. **Lift: −$18 full / −$29 prefix. trips_pair within-cat $909 → $281 (−$628, −69%); trips_pair pct_opt 64.2% → 85.1% (+20.9%).** All other categories byte-identical to v39.

**Track B — two_pair (v41_dt). Phase 1: Drill T2P (v39 vs oracle mismatch matrix over all 1,338,480 two_pair hands).** Top mismatch: v39 picks `Hbot_Lmid_SS` (high pair on bot, low pair on mid, SS) while oracle picks `Hmid_Lbot_SS` (anchor swap) — 56,206 hands @ $2,655 mean regret = $24.84/1000h whole-grid contribution. Second largest: `Hbot_Lmid_SS → Hbot_Lmid_DS` (same-anchor suit upgrade) at $12.77/1000h. Total within-cat mismatch contribution $187/1000h.

**Phase 1b: Drill T2P2 (hand-level inspection of 17,131 mismatches).** 72% have pair-suit overlap ≥ 1; 34% have Layout C (Hbot_Lmid) DS routings available. v39 has `t2p_n_layout_b_routings_ds_g` (Layout B = Hmid_Lbot DS routings count) but **no Layout C equivalent — asymmetric blind spot**. The single most productive Phase 1b signal of the session: auditing existing features for missing-mirror gaps revealed the design target directly.

**Phase 2 v2: two_pair_aug_v2 (4 rank-valued features completing the Layout B/C asymmetry):** `t2p_v2_layout_C_DS_n_configs_g` (count of Layout C DS routings), `t2p_v2_layout_C_max_top_rank_g` (best top in Layout C across SS+DS), `t2p_v2_layout_B_max_top_rank_g` (best top in Layout B across SS+DS), `t2p_v2_layout_C_DS_max_top_rank_g` (best top specifically when Layout C is DS). v41_dt training: 95 features, depth=36 ml=1, 2.02M leaves (+32% over v40 / +33% over v39). 3 of 4 features in top-30 importance (#24, #26, #30 at 0.21-0.29% each).

**v41 grade:** $1,270 full / $686 prefix vs v40's $1,394 / $772. **Lift: −$124 full / −$86 prefix. two_pair within-cat $918 → $363 (−$555, −60%); two_pair pct_opt 66.6% → 83.2% (+16.6%).** All other categories byte-identical to v40 (trips_pair $281 preserved).

**Cumulative session arc:** v39 → v41 = −$142 full / −$115 prefix. pct_opt full 57.88% → 62.18% (+4.30%); prefix 64.55% → 67.13% (+2.58%). p90 regret 0.480 → 0.450; p99 1.090 → 1.075. **Second-largest combined ML session lift after S54's single +$237.** Cumulative v32 → v41 = −$445 full / −$218 prefix across 6 ML ships.

**Methodology lessons (Session 55):**
- **The S54 playbook is transferable across ML residual zones.** Identical Phase 1 drill shape, identical Phase 1b inspection shape, identical 4-feature design (n_configs, max_top, min_top/auxiliary, max_mid_sum or DS-specific). Identical depth=36 ml=1 hyperparams. The methodology is now boilerplate.
- **Asymmetric existing features signal blind spots.** Two_pair had a Layout B DS feature but no Layout C equivalent. That asymmetry pointed at the missing design. Audit existing features for missing-mirror gaps when hunting for the next zone's blind spot.
- **Low individual importance + surgical gating = real ship.** tp_v2 features ranked at #69-78 individually (0.02-0.04%), but v40 still shipped +$18. Population-weighted utility > individual importance for category-gated features.
- **Population size dominates leaf-growth potential.** v40's 4 features added +3.4% leaves (over a 2.86% zone); v41's 4 features added +32% leaves (over a 22.3% zone). Same feature shapes, very different leaf impact — driven by gated population size.
- **Hand-level top-20 inspection is the source-of-truth diagnostic.** Aggregate matrices identify the candidate; only hand-level inspection reveals the precise structural delta. Both tracks required hand-level proof to design the right feature.

**End of S55:** Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix). ML champion v41_dt at $1,270 full / $686 prefix. The two production tracks now diverge by $1,228/1000h. **high_only is now BY FAR the largest remaining residual** ($2,796 within-cat × 40.4% share = $1,131/1000h whole-grid = ~63% of v41's total regret) — Session 56's highest-leverage target. The methodology is mature; the next zone awaits.

---

## Session 54: v39_dt new ML champion via diagnostic-driven feature engineering — LARGEST single ML retrain ship in project history (+$237 full / +$90 prefix)

The Session 53 overnight Part 2 had identified a $852/1000h whole-grid pair-zone residual in the new v36_dt ML champion, and Rule 18 attempts (v54, v55) had regressed because naive suit-aware bot rules broke v3's existing tie-breaks. The verdict was "pair AA/KK/QQ are ML territory." Session 54 took up that gauntlet: rather than fight the rule chain into the pair zone, target the ML model directly with diagnostic-driven feature engineering.

**Phase 1 — Diagnostic (Drills P + P2).** Per-(max, pair) cell mismatch matrix on 2.8M pair hands. v36 == oracle on only 56.6% of pair hands. Top mismatch: **v36 picks "pair-mid_SS" while oracle picks "pair-bot_DS" on 162,551 hands @ $3,693 mean regret = $100/1000h whole-grid contribution from a single mismatch class.** Hand-level inspection of top 20 mismatches: 100% have a pair with 2 distinct suits AND ≥2 singletons matching pair-suits. v36 was missing features describing the QUALITY of the pair-bot DS option.

**Phase 2 v0 — capacity sweep at 83 features (already established in S53 overnight Part 5 as v37_dt_SATURATED).** Re-training v36's 83 features at depth=38 ml=1 produced a byte-identical model (same 1.06M leaves, same scores). **Capacity saturation is a feature problem, not a hyperparameter problem.** This finding directly motivated Session 54's pivot from hyperparameter tuning to feature design.

**Phase 2 v1 — boolean features (v38_dt, FAILED).** Added 2 booleans (`pair_aug_v4_bot_DS_achievable_g`, `n_sings_in_pair_suits_g`). Result: same 1.06M leaves as v36, features at #51 and #56 importance, **v38_dt grade literally identical to v36_dt to multiple decimals on both grids.** Diagnosis: at depth=33 ml=1 saturation, the DT was already deriving DS-achievability from existing suit-distribution features (`suit_2nd`, etc.). Booleans were redundant.

**Phase 2 v2 — rank-valued conditional features (v39_dt, SHIPPED).** Replaced the booleans with 4 rank-valued features that encode the QUALITY of the pair-bot-DS option: count of distinct DS configs, best top-rank achievable across configs, min top-rank, best mid rank-sum. These cannot be derived from existing features (require enumerating DS configs and selecting best). v39_dt training:

- 87 features (83 + 4 v5)
- depth=36, ml=1
- **1,518,368 leaves (+43% over v36's 1.06M)** — the new features genuinely create new splits
- **Depth saturated at 36** (vs v36's 33) — features broke the saturation wall
- 3 of 4 new features in top-30 importance (#19 min_top_rank 0.50%, #22 max_mid_sum 0.34%, #29 max_top_rank 0.19%)

**Per-category (full grid):**

| Category | v36_dt | v39_dt | Δ |
|---|---:|---:|---:|
| **pair** | **$1,604** | **$1,097** | **−$507 (−32%)** |
| pair pct_opt | 56.6% | **65.7%** | **+9.1%** |
| (all other categories byte-identical to v36, by design via gating) |

**Score: v39_dt $1,412 full / $801 prefix (was v36_dt $1,649 / $891). Improvement: −$237 vs v36 full / −$90 prefix; pct_opt full 53.61% → 57.88% (+4.27%, largest ML jump since v34's debut). p90 regret 0.535 → 0.480; p99 regret 1.185 → 1.090. Cumulative v32 → v39 = −$303 full.** This is **2× the largest prior single-ML retrain ship** (v34_dt was −$34) and the largest single ML ship in project history.

**Methodology lesson — diagnostic-first feature engineering at saturation works.** Per-(max, pair) cell mismatch matrix + hand-level inspection of top 20 mismatches identified the exact blind spot. Without that data, the right feature design wouldn't have been clear. **Side lesson — boolean features are usually redundant** with existing suit-distribution features at ml=1 saturation. The DT can already derive booleans from existing splits. **Side lesson — rank-valued conditional features unlock saturation.** Features that describe "what's achievable across alternative configurations" encode information not derivable from any existing feature. **Side lesson — feature design beats hyperparameter tuning at saturation.** v37 (depth=38) was byte-identical to v36; v39 (4 new features at SAME hyperparams) gained +$237. **Side lesson — conditional features should describe ALTERNATIVE configurations, not the chosen configuration.** The model already had features for the "default" Rule-4-style pair-mid pick; adding features for the ALTERNATIVE (pair-bot DS quality) gives the DT the information to compare options.

This methodology now becomes a transferable playbook: diagnose → identify the under-modeled alternative configuration → design rank-valued features that describe its quality → train. Trips_pair ($909/1000h within-category in v39) and two_pair ($918/1000h) are queued as the next applications.

---

## Session 59: v45_dt NULL RESULT — the 4-phase playbook hits depth=36 ml=1 saturation on high_only's 4th pass ($0 lift)

Session 58 had shipped v44_dt as the 3rd consecutive high_only collapse via 4 ho_v4 features (DS bot pair_high quality + 4f topMax route + non-max-top joint count + non-max joint max_top_rank), reducing high_only within-category from $2,075 → $1,868 (−$207, −10.0%). The S58 decision matrix surfaced a clear 4th-pass target: at K/Q in DS_NO_JOINT, v44 keeps max-rank on top 19–18% too often, under-routes DS bot 5–12%, and under-routes suited mid 12–15%. Session 59 was scheduled as an autonomous overnight run to attempt the 4th pass.

**Drills HO11+HO12+HO13 (consolidated, `drill_high_only_v44_deepdive.py`) confirmed the residual structure.** Per-max-rank residual stratification (HO11): A=$182, K=$111, Q=$55, J=$23, T=$7, 9=$2, 8=$0.3 — total $381/1000h whole-grid (consistent with v44's high_only within-cat $1,868 × 40.4% share = $755 whole-grid, of which $381 stratifies by max-rank cleanly). A/K/Q together = 92% of high_only's whole-grid regret. Structural cell cross-tab (HO12): DS_NO_JOINT is STILL the dominant cell at every max-rank (62.9% × all max-ranks = $267/1000h whole-grid summed, ~70% of v44's high_only regret). HO13 (oracle pick profile per cell) showed v44 still routes wrong in DS_NO_JOINT: at K × DS_NO_JOINT (n=207,900), v44 keeps K on top 85% but oracle keeps K only 66%; v44 under-routes DS by 10%; v44 under-routes mid suited by 15%.

**HO13 follow-up (`drill_high_only_v44_nonmax_quality.py`) — non-max joint QUALITY cross-tab.** Stratified the 47.7% of high_only hands with non-max joint achievable by (max_rank × best_top × best_mid_high bucket). Found the deepest single cell: at max=K × DS_NO_JOINT × best_top=Q × best_mid_high≥J(11), oracle picks non-max route 66.6% but v44 picks only 36.1% — a **+30.5% gap on an $9.76/1000h cell** (18,144 hands). Similar (but smaller) gaps at max=Q × best_top=J × mid_h≥J ($4.98) and max=K × best_top=J × mid_h≥J ($7.53).

**Phase 2 v5: high_only_aug_v5 (4 rank-valued features designed from HO13).**
- `ho_v5_topNonMax_DS_ms_max_mid_high_g` (0..13): best mid_high in non-max-top joints — the missing quality counterpart to v44's max_top_rank.
- `ho_v5_topNonMax_DS_ms_best_combined_q_g` (0..26): max(top_rank + mid_high) across non-max joints — joint quality scalar.
- `ho_v5_topNonMax_DS_max_in_bot_pair_n_g` (0..15): count of non-max joints where max-rank is paired in the bot's suited pair.
- `ho_v5_topMax_4f_ms_n_configs_g` (0..15): count of (top=max, 4f bot, ms mid) configs.

All gated to high_only (zero outside).

**v45_dt training (508s, ~8.5 min):** 111 features (107+4), depth=36 ml=1, **2,248,182 leaves (only +9 over v44's 2,248,173)**. **Feature importance: #66 (0.07%) for `best_combined_q_g`, #97 (0.01%) for `max_mid_high_g`, #106 (0.01%) for `max_in_bot_pair_n_g`, #110 (0.00%) for `n_4f_ms_topmax_g`. Sum 0.09%. The LOWEST per-ship importance in project history.**

**v45 grade — NULL RESULT.** Full-grid mean_regret 0.1081, $/1000h $1,081, pct_opt 64.80% — **byte-identical to v44_dt across all 8 categories.** high_only pct_opt 41.83% → 41.94% (+0.11%). pct_opt match count: 3,893,731 → 3,893,739 (+8 hands out of 6,009,159). **Lift: $0 full / $0 prefix.** v45_dt does NOT ship.

**Why v45 didn't ship — the saturation hypothesis.** v44 at depth=36 ml=1 has 2.248M leaves on 6M training rows — every leaf averages ~2.7 examples, and many are single-row. New features can split a leaf only if the leaf contains training rows with different argmax AND the new feature distinguishes them AND no existing feature already provides an equivalent split. ho_v5 features are **mathematically derivable from ho_v4 + base** (best_combined_q = max_top_rank + max_mid_high; n_max_in_bot_pair is implied by n_configs × suit profile counts). The DT already encodes the same decisions via existing features. **The +9 leaves over v44 confirms there is essentially zero new split signal in ho_v5.**

**The data signal IS real, the model just can't reach it.** HO13's $9.76/1000h cell at K × DS_NO_JOINT × best_top=Q × mid_h≥J has a 30.5% pick-rate gap. v45 has features that name the cell precisely (`max_mid_high_nonmax >= 11 AND max_top_rank_nonmax == 12`). The DT could split there, but at saturation it doesn't choose to — the existing v4 features already provide adjacent splits that the optimizer prefers.

**Score: v44_dt UNCHANGED at $1,081 full / $686 prefix. v45_dt is the first NULL ship in 8 consecutive sessions of the 4-phase playbook.** Improvement: unchanged at −$963 vs v16 ($2,044) full, −$1,167 vs v14 ($2,248) full.

**Methodology lessons (Session 59):**

1. **The 4-phase playbook hits a saturation ceiling at depth=36 ml=1 + ~2.25M leaves on 6M rows.** Three consecutive same-zone passes worked at high_only (S56/57/58 collapsed $2,796 → $2,411 → $2,075 → $1,868). The 4th pass does NOT, despite the data signal being clear.

2. **Low importance + no leaf growth is a stronger null signal than importance alone.** v44 had low importance (#47–#95) but +70K leaves, and shipped −$42. v45 has lower importance AND only +9 leaves — the combination is the leading indicator of a null ship.

3. **Mathematically redundant features don't help at saturation, even when the underlying axis is real.** ho_v5's signals are linear combinations or derivations of ho_v4 + base features. The DT already exploits the underlying axis via the existing features; adding redundant encodings doesn't change predictions.

4. **Drill stratification can identify a residual gap that is not closeable with the current model class.** HO13 isolated an $9.76/1000h cell with a 30.5% pick-rate gap — a real and large signal that ML at current hyperparameters can't capture. This signal IS closeable, but by a different lever: surgical rule, different model class, or larger training data.

5. **Number of consecutive same-zone 4-phase passes ≤ 3 under depth=36 ml=1.** Beyond that, switch zones, switch model class, or switch lever (rules).

6. **Cumulative methodology track record:** 7 of 8 attempts ship (S54 pair, S55a trips_pair, S55b two_pair, S56 ho_v2, S57 ho_v3, S58 ho_v4, S59 NULL). The playbook ships on first pass at every fresh zone; ships on 2nd and 3rd passes at high_only (where the residual is uniquely large); fails on the 4th pass at the same zone.

**End of S59:** Rule chain UNCHANGED at v52 ($2,498 full / $1,522 prefix). ML champion UNCHANGED at v44_dt ($1,081 full / $686 prefix). The two production tracks STILL diverge by $1,417/1000h. **high_only is STILL the dominant residual** ($755/1000h whole-grid = ~70% of v44's regret) but is no longer naively-ML-attackable. **Session 60's highest-leverage option is a surgical rule on the HO13-identified $9.76/1000h cell** (K × DS_NO_JOINT × best_top=Q × mid_h≥J), or pivot to trips ($55/1000h whole-grid) for a fresh zone.

## Session 60: A-high cell-by-cell catalog audit — NULL RESULT (all candidates fail; A-high formally labeled ML-only)

Session 59's null result on v45_dt motivated a methodology pivot: instead of pushing more ho-features into a saturated DT, build a per-cell rule audit harness and test whether deterministic rules can capture the residual oracle ceiling. Rule 14 (A-high HIMID, S50) is the oldest and most-tested high_only rule and had never been audited cell-by-cell since shipping. Session 60 built the harness, audited Rule 14 across A-high's 6 structural cells (JOINT_HIGH/MED/LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY), and tested **10 candidate refinement rules** against three threshold gates (T1 catalog-worthy ≥40% gap closure + ≥$3/1000h within-cell; T2 production ship + ≥$5/1000h whole-grid; T3 ML-only label).

**Harness — `analysis/scripts/test_rule_catalog.py`.** Reusable per-cell rule audit infrastructure. Loads `data/drill_ho_v44_per_hand_structural.parquet` (S59 cell tags) + canonical_hands.bin + oracle_grid_full_realistic_n200.bin once; per call, filters to `(max_rank, cell)` subset and scores rule_fn vs baseline_fn vs v44_dt vs oracle. Returns `CatalogResult` with within-cell + whole-grid lift in $/1000h, capture% vs baseline and v44, % optimal, and rule-vs-oracle mismatch class breakdown. **Sanity check (Rule 14 vs pre-Rule-14 predecessor `strategy_v44_rule13_three_pair_DS`) reproduced +$131.25/1000h whole-grid on A-high — matches CURRENT_PHASE's documented S50 ship of +$131 to within 0.2%. Harness validated.**

**Phase 2 — Rule 14 cell-by-cell audit (A-high).** Per-cell remaining gap to oracle after Rule 14, in $/1000h whole-grid: JOINT_HIGH=$26.7, JOINT_MED=$2.3, JOINT_LOW=$0.0, **DS_NO_JOINT=$161.7** (58% of A-high leak), DS_NO_MAXTOP=$55.1, MS_ONLY=$35.4. **Total A-high residual after Rule 14: $281.2/1000h whole-grid** — vs v44_dt's $182.5/1000h. v44 captures $98.8 more than Rule 14 on A-high, distributed across cells (DS_NO_MAXTOP and MS_ONLY are where v44's advantage is largest, $17–32/1000h WG each). Rule 14's within-cell mean_ev is consistently below v44's; within-cell pct_optimal is 12–46% vs v44's 33–73%.

**Phase 3+4 — 10 candidate refinement rules tested vs v52 baseline.** Eight candidates from S58 decision-matrix-derived intuitions (C1–C8) and two from second-pass null-informed retries (C9–C10):
- **C1 (DS→SS+ms whenever achievable):** fires 93.3% of DSnj, capture **−60%**, lift **−$96.9/1000h WG**. CATASTROPHIC.
- **C2/C3 (gate SS+ms on mid_high ≥ J/T):** still net-negative ($−47, $−61/1000h WG).
- **C4 (SS_ms mid_high > DS bot pair_high):** fires **0%** — structurally too tight.
- **C5 (DS_NO_MAXTOP SS_ms any):** identical to Rule 14's fallback in this cell. 0 capture.
- **C6/C7/C8 (31_ms branches in DS_NO_MAXTOP / MS_ONLY):** fire 6–19%, small positive lift +$1–$2/1000h WG — well under T1's $3 within-cell bar.
- **C9 (drop A off top when DS bot pair_high ≥ J):** fires 51.1%, **−$284/1000h WG** — drops A on the wrong 45% of hands.
- **C10 (HIBOT tiebreaker replacing Rule 14's HIMID):** fires 100%, **−$40/1000h WG**. **Confirms Rule 14's S50 HIMID design empirically — alternative tiebreaker is strictly worse.**

**Result: every candidate falls below Threshold 1.** A-high cells are formally labeled **ML-only territory** at the catalog granularity tested. Catalog produced: `SESSION_60_A_HIGH_CATALOG.md` (first page of the eventual `HIGH_ONLY_RULE_CATALOG.md`).

**Score: v52 UNCHANGED at $2,498/1000h on full grid. v44_dt UNCHANGED at $1,081 full / $686 prefix.** Improvement: unchanged at −$963 vs v16 ($2,044) full, −$1,167 vs v14 ($2,248) full.

**Methodology lesson — decision-matrix percentages overstate refinement headroom.** S58's matrix said oracle picks `tA_SS_ms` 27.9% of DS_NO_JOINT (n=116K, $3,613/hand mean regret). The naive read: switch DS_mu → SS_ms whenever achievable, recover ~$1,008/1000h within-cell. The harness says **no — switching costs more than it gains.** Oracle KNOWS WHICH 28% to switch on; a deterministic gate that fires on "where SS_ms is achievable" (93% of cell) hurts the 72% where DS_mu was correct. The catalog test gates correctly correct for this — they DETECT the asymmetry. The methodology is the SHIFT FROM "matrix-driven expectation" to "harness-driven validation." This is the catalog's first proven contribution: not a shipped rule, but a falsified hypothesis backed by 10 tested candidates.

**Methodology lesson — Rule 14's HIMID tiebreaker is empirically validated post-hoc.** C10 (HIBOT replacement) shipped −$40/1000h WG. Rule 14's S50 design choice of "highest mid_rank_sum" over "highest bot_pair_high" was correct. This kind of retrospective audit is itself a catalog deliverable.

**End of S60:** Rule chain UNCHANGED at v52. ML champion UNCHANGED at v44_dt. Harness PROVEN AND READY for S61 (K-high). Critical structural difference at K-high: oracle drops max off top **34% in K × DS_NO_JOINT** (vs 6% at A) and **22% in K × MS_ONLY** (vs 2% at A) — the drop-max play is 5–11× more common, so the C9-style "drop max" candidate may clear thresholds where C9 catastrophically failed on A-high. **Session 61's pivot: reuse harness verbatim, audit Rule 15 cell-by-cell, design candidates concentrating on K-high's drop-K-off-top play.**

---

# Part 2 — ML champion progression (the full table)

Every model trained, side-by-side, on both validation grids:

| Strategy | Session | Depth | min_leaf | Features | Leaves | Full $/1000h | Prefix $/1000h | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v8_hybrid | pre-S25 | n/a | n/a | n/a | n/a | $3,153 | $3,051 | superseded |
| v14_combined | S26 | n/a | n/a | n/a | n/a | $3,033 | $2,037 | human chain (still useful) |
| v16_prefix | S27 | 15 | 200 | 37 | 1,783 | $8,493 | n/a | ARCHIVED (prefix bias) |
| v16_dt | S27 | 18 | 100 | 37 | 28,790 | $2,464 | $1,607 | superseded |
| v17_rules_then_dt | S28 | n/a | n/a | n/a | n/a | $2,833 | n/a | ARCHIVED |
| v18_dt | S28 | 22 | 50 | 37 | 60,651 | $2,306 | $1,478 | superseded |
| v18b | S29 | 24 | 30 | 37 | 96,409 | $2,217 | $1,343 | superseded |
| v18c | S29 | 26 | 20 | 37 | 124,902 | $2,172 | $1,261 | superseded |
| v19 (ungated suited) | S29 | 22 | 50 | 43 | 72,900 | $2,250 | $1,494 | ARCHIVED (prefix fail) |
| v18d | S30 | 28 | 10 | 37 | 193,365 | $2,108 | $1,145 | superseded |
| v18e | S30 | 30 | 5 | 37 | 274,446 | $2,066 | $1,082 | superseded |
| v19_gated | S30 | 28 | 10 | 43 gated | 215,597 | $2,036 | $1,145 | superseded |
| v20 | S30 | 30 | 5 | 43 gated | 307,939 | $1,982 | $1,082 | superseded by v23 |
| v20b | S31 | 32 | 5 | 43 gated | 307,939 | $1,982 | $1,082 | ARCHIVED (capacity saturated) |
| v21 / v22 | S31 | n/a | n/a | n/a | n/a | $3,713 / $3,506 | n/a | ARCHIVED (Rule 5 attempts vs v14) |
| v23 | S31 | 30 | 5 | 49 (43+6 trips_pair) | 314,705 | $1,977 | $1,073 | superseded by v24 |
| v24 | S31 | 30 | 5 | 53 (49+4 composite) | 314,759 | $1,977 | $1,072 | superseded by v25 |
| v25 | S32 | 30 | 5 | 59 (53+6 pair-gated) | 390,626 | $1,929 | $1,054 | superseded by v26 |
| v26 | S33 | 30 | 5 | 65 (59+6 two_pair-gated) | 459,209 | $1,859 | $1,002 | superseded by v27 |
| v27 | S34 | 30 | 5 | 69 (65+4 high_only-gated) | 460,375 | $1,853 | $1,002 | superseded by v29 (prefix unchanged because prefix has no high_only hands) |
| v29 | S35 | 30 | 5 | 73 (69+4 pair_r4-gated) | 486,342 | $1,807 | $965 | superseded by v30 |
| v30 | S36 | 30 | 5 | 79 (73+6 trips-gated) | 493,057 | $1,794 | $951 | superseded by v31 |
| v31a | S36-overnight | 30 | 5 | 83 (79+4 pair_r4v3 KK/AA-tight) | 500,722 | $1,788 | $951 | ARCHIVED — minimal headline gain ($6 full / $0 prefix) |
| v31b | S36-overnight | 30 | 5 | 83 (79+4 trips_v2 round 2) | 507,692 | $1,779 | $938 | ARCHIVED — solid trips round-2 ($15 full / $13 prefix) but lost vs v31 in cascade |
| v31 | S36-overnight | 32 | 3 | 79 (same as v30) | 699,773 | $1,736 | $921 | superseded by v32 — capacity-only retrain shipped second-largest ship (after v26) with zero new features |
| v32 | S37 | 32 | 3 | 83 (79 v30 + 4 trips_v2 round 2) | 731,606 | $1,715 | $904 | superseded by v34 — stacks trips_v2 round-2 features on v31's high-capacity config; held the ML record briefly between Session 37 and 38 |
| v32_d34ml3 | S38 | 34 | 3 | 83 (same as v32) | 731,611 | $1,715 | $904 | ARCHIVED — control retrain at depth=34 ml=3; +5 leaves vs v32 (depth=33 actual saturation) confirms ml=3 was the binding constraint |
| v34_dt | S38 | 34 | 2 | 83 (same as v32) | 874,548 | $1,681 | $889 | superseded by v36 — capacity-only retrain at depth=34 ml=2; +19.5% leaves over v32; ships −$34 full / −$15 prefix and lifts every category. |
| v36_dt | S53 overnight | 36 | 1 | 83 (same as v32) | 1,064,442 | $1,649 | $891 | superseded by v39 — capacity-only retrain at depth=36 ml=1; +21.7% leaves over v34; ships −$33 full / +$2 prefix. pct_opt full 52.02% → 53.61% (+1.59%). Per-category gains concentrated in rare-shape categories: trips_pair −$148, composite −$213, trips −$97, quads −$68. |
| v37_dt | S53 overnight P5 | 38 | 1 | 83 (same as v32) | 1,064,442 | $1,649 | $891 | ARCHIVED — depth=38 ml=1 produced byte-identical model to v36 (depth saturated at 33 with 83 features). Confirmed: capacity saturation is a feature problem, not a hyperparameter problem. Motivated S54's feature-design pivot. |
| v38_dt | S54 | 36 | 1 | 85 (83 + 2 pair_aug_v4 booleans) | 1,064,442 | $1,649 | $891 | ARCHIVED — boolean features (DS-achievability, n-sings-in-pair-suits) were redundant with existing suit-distribution features (suit_2nd, etc.). Same leaves as v36 = DT could already derive booleans from existing splits. Lesson: at saturation, booleans rarely add information. |
| v39_dt | S54 | 36 | 1 | 87 (83 + 4 pair_aug_v5 rank-valued) | 1,518,368 | $1,412 | $801 | superseded by v40 / v41 (S55). At time of ship: LARGEST ML RETRAIN SHIP IN PROJECT HISTORY. +43% leaves over v36, depth saturation broke from 33 to 36, 3 of 4 features in top-30 importance. pct_opt full 53.61% → 57.88% (+4.27%). pair zone within-category $1,604 → $1,097 (−$507, −32%); other categories byte-identical (gated). Lift: −$237 full / −$90 prefix. |
| v40_dt | S55 | 36 | 1 | 91 (87 + 4 trips_pair_aug_v2 rank-valued) | 1,569,848 | $1,394 | $772 | superseded within-session by v41. **trips_pair zone within-category $909 → $281 (−$628, −69%)** via 4 rank-valued features mirroring pair_aug_v5 pattern for Pbot_DS routings (R1/R2/R3). Modest +3.4% leaves but surgical: all other categories byte-identical to v39. Lift: −$18 full / −$29 prefix. Cumulative v32 → v40 = −$321 full. The S54 playbook proved transferable. |
| v41_dt | S55 | 36 | 1 | 95 (91 + 4 two_pair_aug_v2 rank-valued) | 2,015,413 | $1,270 | $686 | superseded by v42 (S56). +32% leaves over v40 / +33% over v39. 3 of 4 new features in top-30 importance (#24, #26, #30). pct_opt full 58.48% → 62.18% (+3.70%); prefix 65.19% → 67.13% (+1.94%). **two_pair zone within-category $918 → $363 (−$555, −60%)** via Layout C achievability + quality features (completing the Layout B/C asymmetry). All other categories byte-identical to v40. Lift: −$124 full / −$86 prefix. Cumulative session v39 → v41 = −$142 full / −$115 prefix. Cumulative v32 → v41 = −$445 full / −$218 prefix (6 ML ships). p90 0.450; p99 1.075. |
| v42_dt | S56 | 36 | 1 | 99 (95 + 4 high_only_aug_v2 rank-valued) | 2,109,330 | $1,192 | $686 | superseded by v43 (S57). +4.7% leaves over v41 (modest, surgical to high_only). 3 of 4 new features in top-32 importance (#26 max_mid_sum 0.28%, #31 max_top 0.22%, #32 min_top 0.21%, #80 n_configs 0.03%). pct_opt full 62.18% → 63.08% (+0.91%); prefix unchanged at 67.13%. high_only zone within-category $2,796 → $2,411 (−$385, −13.8%); high_only pct_opt 29.0% → 33.4% (+4.4%) via DS-bot achievability features mirroring pair_aug_v5 / trips_pair_v2 / two_pair_v2 (enumerates C(7,4)=35 candidate bot subsets, filters to 2+2 DS, characterizes max_top, min_top, max_mid_sum). All other 7 categories byte-identical to v41. Lift: −$79 full / $0 prefix. |
| v43_dt | S57 | 36 | 1 | 103 (99 + 4 high_only_aug_v3 rank-valued JOINT) | 2,177,798 | $1,123 | $686 | superseded by v44 (S58). +3.2% leaves over v42 (modest, surgical to high_only). 4 features at LOW individual importance (#63/#64/#100/#102 at 0.07%/0.07%/0.01%/0.00%) — lowest-per-ship at time of ship. Ships +$69 full / $0 prefix via surgical gating on the 14.7% of high_only hands with joint achievability. pct_opt full 63.08% → 63.99% (+0.91%); high_only zone $2,411 → $2,075 (−$336, −13.9%). All other 7 categories byte-identical to v42. Cumulative v32 → v43 = −$592 full. p90 0.400; p99 0.980. Two-session high_only collapse (S55 → S57): $2,796 → $2,411 → $2,075 = −$721 within-category (−25.8%). |
| **v44_dt** | **S58** | **36** | **1** | **107 (103 + 4 high_only_aug_v4 rank-valued: DS bot pair_high quality + 4f_ms route + non-max-top joint count + best non-max top rank)** | **2,248,173** | **$1,081** | **$686** | **CURRENT ML CHAMPION (end of S58 and S59 — UNCHANGED).** +3.2% leaves over v43 (modest, surgical to high_only). Feature importance #47 max_top_rank (0.13%), #80 max_bot_pair_high (0.04%), #93 4f_ms_max_mid_high (0.01%), #95 n_configs (0.01%). pct_opt full 63.99% → 64.80% (+0.81%); prefix unchanged at 67.13%. **high_only zone within-category $2,075 → $1,868 (−$207, −10.0%); high_only pct_opt 37.9% → 41.8% (+3.9%).** Each feature targets a structural axis invisible to v43 surfaced by drills HO5–HO10: (a) DS bot pair_high quality with top=max — discriminates the `DS_NO_JOINT` cell which is 62.9% of high_only and ~69% of its regret; (b) 4-flush+ms_mid with top=max — captures Ace-high alt route (54% of A-when-joint-available alts); (c) non-max-top joint achievability count — covers 47.7% of high_only hands invisible to ho_v3; (d) best non-max top rank — quality signal for the non-max joint route. All other 7 categories byte-identical to v43 on both grids. Lift: −$42 full / $0 prefix (prefix neutrality is by design). Cumulative v32 → v44 = −$634 full / −$218 prefix (9 ML ships). p90 0.390; p99 0.970. **Three-session high_only collapse (S55 → S58):** $2,796 → $2,411 → $2,075 → $1,868 = **−$928 within-category (−33.2%)** — composing three conditional axes (ho_v2 DS-only + ho_v3 DS+ms-joint + ho_v4 DS-quality+non-max-joint+4f) compresses the same zone three times without surgical interference. **Methodology validation: the 4-phase playbook is transferable to the SAME zone for a THIRD pass without modification; the decision matrix is a separable deliverable from the ML ship (`SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` answers the user's S57 review question on its own terms).** Within-JOINT picks: oracle is mid-first (mean mid_pct 0.67–0.81 >> bot_pct 0.24–0.36); joint take-rate collapses with lower max-rank (A:95% → 8:13%). Outside JOINT at lower max-ranks: oracle becomes bot-first (max-rank moves into bot to enable a stronger DS configuration with a lower top). |
| v45_dt | S59 | 36 | 1 | 111 (107 + 4 high_only_aug_v5 rank-valued: non-max joint max_mid_high + best_combined_q + max_in_bot_pair_n + 4f_ms n_configs) | 2,248,182 | $1,081 | $686 | **NULL RESULT — trained but does NOT ship.** +9 leaves over v44 (essentially zero growth). Feature importance #66 best_combined_q (0.07%), #97 max_mid_high (0.01%), #106 max_in_bot_pair_n (0.01%), #110 n_4f_ms_topmax (0.00%) — sum 0.09%, the LOWEST per-ship in project history. Lift: $0 full / $0 prefix. pct_opt full and prefix unchanged. high_only within-category unchanged at $1,868. high_only pct_opt 41.83% → 41.94% (+0.11% absolute; +8 hands matched out of 6.0M). All 8 categories byte-identical to v44. The 4 ho_v5 features were designed from HO13's stratification ($9.76/1000h cell at K × DS_NO_JOINT × best_top=Q × mid_h≥J where oracle picks non-max route 67% vs v44's 36%) but the DT at depth=36 ml=1 has saturated: each leaf averages ~2.7 training examples and the v5 signals are mathematically derivable from v4 + base (best_combined_q = max_top_rank + max_mid_high; n_max_in_bot_pair implied by n_configs × suit profile). **Methodology lesson: the 4-phase playbook hits a saturation ceiling at depth=36 ml=1 + ~2.25M leaves on 6M rows after 3 consecutive same-zone passes.** Beyond that, switch zones, switch model class, or switch lever (rules). v44_dt remains the ML champion. |

**Per-category breakdown** (full grid, N=200): how each category's
regret has dropped across the flagship versions:

| Category | v14 | v16 | v18e | v20 | v25 | v26 | v27 | v29 | v30 | v31 | v32 | v34 | Δ v34 vs v14 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high_only | $4,082 | $3,785 | $3,307 | $2,894 | $2,894 | $2,894 | $2,863 | $2,862 | $2,862 | $2,816 | $2,816 | **$2,806** | **−$1,276** |
| pair | $2,011 | $2,127 | $1,873 | $1,873 | $1,771 | $1,771 | $1,771 | $1,674 | $1,674 | $1,639 | $1,639 | **$1,619** | **−$392** |
| two_pair | $3,371 | $2,005 | $1,458 | $1,458 | $1,458 | $1,145 | $1,145 | $1,145 | $1,145 | $1,037 | $1,037 | **$978** | **−$2,393** |
| trips | $4,054 | $2,347 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,758 | $1,732 | $1,359 | **$1,291** | **−$2,763** |
| trips_pair | $5,417 | $2,438 | $1,608 | $1,608 | $1,446 | $1,445 | $1,445 | $1,443 | $1,442 | $1,225 | $1,225 | **$1,057** | **−$4,360** |
| three_pair | $4,529 | $1,975 | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | $1,639 | $1,639 | **$1,635** | **−$2,894** |
| quads | $9,670 | $2,233 | $724 | $724 | $723 | $723 | $723 | $723 | $723 | $645 | $645 | **$613** | **−$9,057** |
| composite | $10,883 | $5,260 | $2,100 | $2,100 | $1,869 | $1,741 | $1,741 | $1,741 | $1,733 | $1,387 | $1,386 | **$1,173** | **−$9,710** |

Eight category-gated wins are now visible across the v18e → v31
progression, plus one capacity-only ship (v31):
- **v20 → high_only-via-suited:** −$413 vs v18e (6 gated suited features).
- **v23 → trips_pair:** −$161 vs v20 (6 gated trips_pair features).
- **v24 → composite:** −$216 vs v23 (4 gated composite features).
- **v25 → pair (v1):** −$102 vs v24 (6 gated pair features).
- **v26 → two_pair:** −$313 vs v25 (6 gated two_pair features). Largest
  per-category gain since v20→high_only.
- **v27 → high_only-direct:** −$31 vs v26 (4 gated high_only features).
  Smallest per-category gain to date — diagnostic was speculative.
- **v29 → pair (v2):** −$97 vs v27 (4 gated pair_r4 features).
  **First successful within-category iteration — pair has now seen
  TWO independent gating-template ships, totaling −$199 within-pair
  vs v18e.** Diagnostic-driven from `distill_v27_pair.py`'s
  competing-baseline analysis — the most prescriptive feature design
  in project history.
- **v30 → trips:** −$239 vs v29 (6 gated trips features). 8th gating-
  template instance. First trips-category gating ship.
- **v32 → trips round-2:** −$373 vs v31 (4 gated trips_v2 features stacked
  on v31's capacity config). 9th gating-template instance and the FIRST
  within-trips iteration; same template-second-iteration pattern as v25→v29
  for pair.
- **v34 → capacity-only at ml=2:** −$34 whole-grid vs v32 (zero new features;
  874K leaves vs v32's 731K). 2nd capacity-only ship (after v31); per-category
  shape moves every category, with biggest gains in the previously-gated
  composite (−$213 within-cat) and trips_pair (−$168). The control retrain
  at depth=34 ml=3 reproduced v32 exactly, proving ml=3 was the leaf-binding
  constraint, not depth.

Each gating upgrade lifted ONLY its targeted category and kept every other
category bit-identical (or within N=200 noise) — the cleanest possible
controlled-experiment shape for feature engineering. Every change also
trivially passes the prefix N=1000 tripwire because the new features
fire on zero off-archetype hands by design.

**v31 is the exception to the per-category controlled-experiment shape.**
It's a CAPACITY-ONLY retrain (depth=32 ml=3 vs v30's depth=30 ml=5,
identical 79 features). All 8 categories improve simultaneously. The
biggest gains accrue to PREVIOUSLY-GATED categories (composite −$346,
trips_pair −$217, two_pair −$108, quads −$78), confirming the
hypothesis that v25-v30's gating features had been encoded but not
fully expressed within v30's leaf budget. **+42% leaf-count expansion
(493K → 700K) unlocks $58/1000h whole-grid in one config change** —
22% of what the cumulative 6-ship gating-template work added.

---

# Part 3 — Distillation insights (Session 28, from v16's tree)

Walked all 6M oracle-grid hands through v16's 28,790-leaf tree. These
findings still hold — they're about how the DT thinks, which is roughly
the same in v18 and v20 (the bigger trees just have more partition
detail).

## Feature importance (top 8, population-weighted MSE reduction)

| Rank | Feature | % of total | What it captures |
|---:|---|---:|---|
| 1 | `n_broadway` | 44.9% | Count of T-J-Q-K-A cards (0..7) |
| 2 | `third_rank` | 11.5% | Rank of 3rd-highest distinct rank (body strength) |
| 3 | `pair_high_rank` | 8.8% | Rank of highest pair (0 if none) |
| 4 | `n_low` | 7.7% | Count of 2-5 cards |
| 5 | `has_premium_pair` | 4.5% | KK or AA flag |
| 6 | `top_rank` | 4.3% | Highest rank in hand |
| 7 | `second_rank` | 3.8% | 2nd-highest distinct rank |
| 8 | `has_ace_singleton` | 3.4% | A in hand, no A-pair/trip/quad |

The 9 hand-engineered "aug" features (default_bot_is_ds_*,
n_routings_yielding_ds_bot_*, etc.) collectively contribute **<0.4%**
of total importance. The DT solves the problem almost entirely with
raw body-strength features.

## Key insight: `n_broadway` is the master signal

The root split is `n_broadway ≤ 2.5` and that single split alone
accounts for $4M of the total $11M MSE reduction in the tree.

| n_broadway | What the DT does |
|---:|---|
| 0–2 | Bias toward placing the few high cards in bot or mid; default plays well |
| 3 | Mixed — splits further on premium-pair / ace-singleton |
| 4–7 | Premium pair → mid (Rule 4); else default |

## What the v16 DT does NOT see

- **Suited pairs of broadway cards** (e.g. K♦Q♦ together) — there is
  no feature for "do I have a same-suit pair of cards both ≥ T"
- **Connected high cards** (e.g. J-Q-K) — captured only via
  `connectivity` (longest run) which lumps low and high runs together

The first of these was addressed in Session 30 by the gated
suited-broadway features → v20's $413/1000h gain on high_only. The
second is still open — a `connectivity_high` feature (longest run
restricted to broadway ranks) is a Session 31+ candidate.

## v20's biggest tree-shape changes (informal)

v20 has 307K leaves vs v16's 28K (10.9× more). Most of the new
partitions are in the composite category (where v16 was $5,260/1000h
and v20 is $2,100). v20 has not been formally distilled yet — Session
31 priority A.

---

# Part 4 — What's NOT yet covered

| Hand type | Frequency | v14 $/1000h | Latest $/1000h | Status |
|---|---:|---:|---:|---|
| high_only | 20.4% | $4,082 | $2,816 (v31) | v27 (Session 34) added 4 high_only-gated features (`ho_n_broadway_in_2nd_suit_g` and 3 others); −$31/1000h on the category. v31 (Session 36 capacity-only retrain) brings it to $2,816 (−$46 vs v30 from depth=32 ml=3 capacity expansion). Smallest gating gain to date but capacity-aware retraining unlocks more. A naive **Rule 5** (suited middle for high_only) was tested both ways in Session 31 and **REJECTED** — see below. |
| pair | 46.6% | $2,011 | $1,639 (v31) | TWO gating ships: v25 (Session 32) added 6 features encoding kickers-in-pair-suit / alt-routing rank quality (−$102 within-pair); v29 (Session 35) added 4 features encoding Rule-4-bot suit profile + body-card distribution (−$97 within-pair). v31 (Session 36 capacity retrain) brings within-pair to $1,639 (−$35 vs v30). v29 was diagnostic-driven from `distill_v27_pair.py`'s competing-baseline analysis (v27 was actually $20/1000h whole-grid WORSE than Rule 4 alone on KK/AA — overgeneralizing v25's features). **Rule 5 (Rainbow override) ships to STRATEGY_GUIDE for human play (Decision 063).** Open: KK/AA single-suited Rule-4-bot stratum (52.9% of KK/AA, $37/1000h below oracle within-stratum). v31a candidate (KK/AA-tight features) tried Session 36 overnight, shipped only +$6 — different angle needed (e.g., meta-classifier or sub-tree dedicated to KK/AA). |
| trips (no pair) | 5.5% | $4,054 | $1,732 (v31) | v30 (Session 36) added 6 trips-gated features (`trips_*_g`) — first trips gating ship. −$239 within-trips on full grid. Diagnostic surfaced the largest gap-to-baseline in project history: v29 was $85/1000h whole-grid WORSE than always-A_paired_mid. v31 capacity retrain adds another −$26 within-trips. v32 candidate = v31b's trips_v2 round-2 features (C_top + finer A/B routing) at v31's high-capacity config, expected ~$15-20 incremental. **Always-A_paired_mid** is a Rule 6 candidate worth investigating for STRATEGY_GUIDE — captures $85/1000h whole-grid relative to v29's deviations. Likely already implicit in v14_combined; needs verification. |
| trips_pair | 2.9% | $5,417 | $1,225 (v31) | v23 (Session 31) added 6 trips_pair-gated features; −$161/1000h on the category. v31 capacity retrain adds **another −$217 within-trips_pair** — the SECOND-largest single-category drop from a non-gating ship. The trips_pair gating from v23 had been adding signal but v30's leaf budget couldn't fully express it; capacity unlocks the latent value. No hand-coded rule extracted; the DT routing is multi-axis. |
| three_pair | 1.9% | $4,529 | $1,639 (v31) | No human rule yet. v31 capacity retrain adds −$15 within-three_pair. Untouched by gating. |
| two_pair | 22.3% | $3,371 | $1,037 (v31) | v26 (Session 33) added 6 two_pair-gated features alongside the 3 pre-existing two_pair aug booleans; −$313/1000h on the category. v31 capacity retrain adds another −$108 within-two_pair. The 6 features split Layout B (high pair → mid) from Layout C (low pair → mid) which the existing 3 features lumped together. |
| quads | 0.2% | $9,670 | $645 (v31) | v20 captures heavily; v31 capacity retrain adds −$78 within-quads. No human rule. Below noise floor for further gating. |
| composite | 0.2% | $10,883 | $1,387 (v31) | v24 (Session 31) added 4 composite-gated features for archetype-specific routing. v31 capacity retrain adds **−$346 within-composite** — the LARGEST single-category drop from any non-gating ship. The composite gating from v24 had been substantially under-expressed; capacity unlocks the latent value. Composite is also the smallest population share (0.245%) so this $346 within-category translates to only $1/1000h whole-grid contribution change. |

**Rule 5 candidates — REJECTED (Session 31):** Two attempts to extract a
suited-mid rule from v20's gated features both lost head-to-head against
v14_combined:

| Strategy | Full $/1000h | Δ vs v14 |
|---|---:|---:|
| v14_combined + Rule 4 | $3,033 | — |
| v21 = v14 + Rule 5 (msphr ≥ 9, "any high suited pair") | $3,713 | −$680 |
| v22 = v14 + Rule 5 (msphr ≥ 11 AND msplr ≥ 9, tightened) | $3,506 | −$473 |

Both variants fire on far more high_only hands than the population that
actually benefits from suited-mid routing (the rule is ~8× over-eager
relative to the DT's selective routing). The DT's gated splits use 4+
distinct rank thresholds combined with `n_low` / `n_broadway` that no
single AND-rule can replicate. **For the human strategy: stop at Rule 4.
For computational play: use the DT champion (v23 or v24).** See
Decision 056 in DECISIONS_LOG.md.

**v17 hybrid attempt (rules-then-DT) was archived in Session 28.**
Hand-coded rules can be inferior to the DT in their own categories.
Don't chain them in front of the DT in production code; the strategy
guide can keep them as human-memorizable approximations.

---

# Part 5 — Where each rule + model lives in code

**Human rules:**
- Rule 1 → `analysis/scripts/strategy_v9_2_pair_to_bot_ds.py`
- Rule 2 → `analysis/scripts/strategy_v10_two_pair_no_split.py`
- Rule 3 → `analysis/scripts/strategy_v12_trips_pair.py`
- Rule 4 → encoded implicitly in `analysis/scripts/strategy_v8_hybrid.py`
  (via `encode_rules.strategy_v3`'s pair-to-mid default). v3 / v8 /
  v16 / v18 / v20 all agree on the canonical KK and AA play; Rule 4
  is documentation, not a separate code path.
- Rule 5 (KK/AA rainbow override) → `analysis/scripts/strategy_v28_rule5_rainbow.py`
- Rule 6 v1 (production heuristic, Session 37) → `analysis/scripts/strategy_v33_rule6_trips.py` — boundary `trip_rank > max_kicker_rank → C, else A`. Production runtime stays here.
- Rule 6 v3 (sharper human boundary, Session 39) → `analysis/scripts/strategy_v35_rule6_v3.py` — explicit per-trip-rank table (Trip A always third-on-top; K only if no Ace; Q only if no J/K/A; J or lower never). Strategy guide ceiling +$8.12/1000h whole-grid vs v33 oracle-bound; production heuristic-A loses at runtime, so used for human-play guidance only.
- Rule 7 (three_pair, Session 41) → `analysis/scripts/strategy_v37_rule7_three_pair.py` — boundary "if highest pair ∈ {T, J, Q, K} → mid is the MIDDLE pair, else mid is the HIGHEST pair; top is always the singleton". +$43/1000h whole-grid lift vs v33 confirmed at full grid.
- Rule 8 (composite quads_pair, Session 42 morning) → `analysis/scripts/strategy_v38_rule8_qp.py` — "for quads_pair (4+2+1), top = singleton, mid = the 2 quad cards whose suits are NOT the pair's suits, bot = the other 2 quads + the pair". 100% deterministic-realizable. +$9.42/1000h whole-grid lift vs v37 (+$18.63/1000h on prefix). Bot is always double-suited.
- Rule 9 (Session 42 overnight) → `analysis/scripts/strategy_v39_rule9.py` — three sub-rules covering plain quads, TT (two_trips), and T2P (trips_two_pair). Combined +$22/1000h whole-grid + +$28/1000h prefix. See Rule 9a/9b/9c above in Part 6.
- Rule 10 simple variant (Session 43, sister) → `analysis/scripts/strategy_v40_rule10.py` — J-low single-pair defensive: TOP=lowest singleton, MID=pair, BOT=4 highest non-pair singletons. Trigger: pair AND max ≤ J (no further gate). +$23/1000h full / +$37/1000h prefix. Retained as the human-memorizable single-condition variant.
- Rule 10 gated variant (Session 43) → `analysis/scripts/strategy_v40b_rule10_gated.py` — same setting + extra gate `pair_rank ≤ 6 OR pair_rank == max_rank`. **+$48/1000h whole-grid (full) + +$37/1000h whole-grid (prefix) — grader-confirmed both grids.** Largest single-rule full-grid lift since v33's Rule 6. **Superseded by v41 (Session 45) — Rule 10 v3 with suit-aware bot.**
- Rule 10 v3 — suit-aware bot (Session 45) → `analysis/scripts/strategy_v41_rule10_v3_ds.py` — same trigger + gate as v40b, but pick the singleton-to-drop-as-TOP that yields a DS bot when achievable; tie-break by lowest singleton (preserves v40b top-inversion intent); fall back to v40b's "TOP=lowest" otherwise. **+$29/1000h whole-grid (full) + +$54/1000h whole-grid (prefix) — grader-confirmed both grids.** Cumulative v40b → v41 = −$29 full / −$54 prefix; v39 → v41 = −$77 full / −$91 prefix. **Superseded by v42 (Session 46) — Rule 11 J-pair pair-to-bot DS.**
- Rule 11 — J-pair pair-to-bot DS (Session 46) → `analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py` — first single-cell rule. Trigger: cat=pair AND P=11 AND max_rank=11 AND DS-bot achievable with both J's in bot. Setting: both J's to BOT, pick lowest-rank singletons completing 2+2 DS pattern, TOP=lowest of remaining 3 singletons, MID=other 2. Fires on 0.285% of grid (0.57% J-pair-J cell × ~50% DS-achievable). **+$6/1000h whole-grid (full) + $0 prefix (unchanged — fires on 0 prefix hands).** Cumulative v41 → v42 = −$6 full / $0 prefix. **Superseded by v43 (Session 47) — Rule 12 two_pair both-intact + DS.**
- Rule 12 — J-low two_pair both-intact + DS-bot (Session 47) → `analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py` — trigger: cat=two_pair AND max≤J AND DS-bot achievable with both pairs intact. Setting builder: try HH-to-bot first (HH-suit + 2 singletons completing 2+2 DS), else try LL-to-bot; MID = the OTHER pair (anchor preserved); TOP = leftover singleton (deterministic). Fires on 2.01% of grid (4.36% J-low two_pair × 46.2% DS-achievable). **+$35/1000h whole-grid (full) + +$66/1000h whole-grid (prefix) — grader-confirmed both grids.** Largest single-rule full-grid lift since v33's Rule 6. Two_pair regret −$160 within two_pair. Cumulative v42 → v43 = −$35 full / −$66 prefix. **Superseded by v44 (Session 48) — Rule 13 three_pair all-intact + DS.**
- Rule 12 max≤Q extension (Session 48, DEFERRED) → `analysis/scripts/strategy_v43b_rule12_two_pair_extQ.py` — extends Rule 12 to max≤Q with HH-only fallback at max=Q. Grade: +$14 full / −$6 prefix (pct_opt 52.61%→52.45%). Passes strict 2x ratio gate (0.43x) but qualitative prefix regression deferred for now. Files retained for possible future refinement.
- Rule 13 — three_pair all-intact + DS-bot (Session 48) → `analysis/scripts/strategy_v44_rule13_three_pair_DS.py` — trigger: cat=three_pair AND (MM_mid_DS achievable OR HH_mid_DS achievable). Setting builder: try MM_mid first (V_MM_MID, +$2,463/1000h within fires; mid=MM pair, bot=HH+LL pairs, top=singleton), else HH_mid (V_HH_MID, +$2,227); SKIP LL_mid-only cases (V_LL_MID is catastrophic at -$4,117/1000h within fires). Fires on 35.1% of three_pair (0.67% of grid). **+$11/1000h whole-grid (full) + +$29/1000h whole-grid (prefix) — grader-confirmed both grids.** Three_pair regret $2,268 → $1,696 (−$572 within three_pair, 25% reduction); three_pair pct_opt 51.5% → 59.3% (+7.8%, largest single-category pct_opt jump from any rule ship at the time). Cumulative v43 → v44 = −$11 full / −$29 prefix. **Superseded by v45 (Session 50) — Rule 14 A-high no-pair.**
- Rule 14 — A-high no-pair, A-on-top + DS/SS HIMID (Session 50) → `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` — trigger: cat=high_only AND max=A AND DS-bot OR SS-bot achievable with A on top. Setting builder: TOP=A always, try DS-bot first then SS-bot fallback, in both cases use HIMID tie-break (mid = 2 highest non-A cards). Fires on 93.6% of A-high no-pair (= 10.3% of grid). **+$131/1000h whole-grid (full) + $0 prefix.** Was the single-largest single-rule lift in project history when shipped. **Superseded by v46 (Session 51) — Rule 15 K-high no-pair.**
- Rule 15 — K-high no-pair, K-on-top + DS/SS HIMID (Session 51) → `analysis/scripts/strategy_v46_rule15_Khigh_DS.py` — same structure as Rule 14 but for K-high. Trigger: cat=high_only AND max=K AND DS-bot OR SS-bot achievable with K on top. Setting builder: TOP=K always, try DS-bot first then SS-bot fallback, HIMID tie-break. Fires on 95.8% of K-high no-pair (= 5.3% of grid). **+$51/1000h whole-grid (full) + $0 prefix.** Was 3rd-largest single-rule lift when shipped. **Superseded by v47 (Session 52) — Rule 16 Q-high no-pair.**
- Rule 16 — Q-high no-pair, Q-on-top + DS/SS HIMID (Session 52) → `analysis/scripts/strategy_v47_rule16_Qhigh_DS.py` — same structure as Rules 14/15. Trigger: cat=high_only AND max=Q AND DS-bot OR SS-bot achievable with Q on top. Setting builder: TOP=Q always, try DS-bot first then SS-bot fallback, HIMID tie-break. **+$19/1000h whole-grid (full) + $0 prefix.** **Superseded by v52 (Session 53) — Rule 17 generalizes high_only handling.**
- **Rule 17 — Comprehensive high_only generalized handler (Session 53 overnight, CURRENT PRODUCTION)** → `analysis/scripts/strategy_v52_full_high_only_handler.py` — addresses ALL high_only no-pair sub-pops (max ≥ 7) with the right offensive vs defensive structure per-cell. Trigger + setting cascade: (1) Defensive lowest-on-top + DS-bot HIMID for max ∈ {T, 9, 8, 7} ALWAYS, and for max ∈ {J, Q, K} when 2nd-high ≤ 8; (2) HIMID for max=J when not defensive; (3) v47's Rules 14-16 for max ∈ {Q, K, A}. Fires on 1.55% of grid (93,130 hands; 35% pick differences from v47). **+$17/1000h whole-grid (full) + $0 prefix (UNCHANGED — high_only zero prefix).** pct_opt full: +0.04%; high_only sub-category +0.3%. high_only $3,096 → $3,014 (−$82, −2.6%). p90 regret IMPROVED 0.725→0.720. Cumulative v47 → v52 = −$17 full / $0 prefix; v39 → v52 = −$348 full / −$185 prefix. Origin: per-(max, s2) characterization revealed defensive dominates for max ≤ T (62-86%), HIMID dominates for A-high (93%+), mixed for K/Q/J. Sister strategies v48 (HIMID alone, +$8) and v50 (HIMID + defensive A/K/Q/J ≤ s2 8, regressed) confirmed the design.
- Combined chain (4 rules) → `analysis/scripts/strategy_v14_combined.py`
- Combined chain (5 rules) → `analysis/scripts/strategy_v28_rule5_rainbow.py` (wraps v14 with Rule 5)
- Combined chain (6 rules) → `analysis/scripts/strategy_v33_rule6_trips.py` (wraps v28 with Rule 6 v1)
- Combined chain (6 rules, current human-guide for trips) → `analysis/scripts/strategy_v35_rule6_v3.py` (wraps v28 with Rule 6 v3)
- Combined chain (7 rules) → `analysis/scripts/strategy_v37_rule7_three_pair.py` (wraps v33 with Rule 7)
- Combined chain (8 rules) → `analysis/scripts/strategy_v38_rule8_qp.py` (wraps v37 with Rule 8)
- Combined chain (9 rules) → `analysis/scripts/strategy_v39_rule9.py` (wraps v38 with Rule 9 a/b/c)
- Combined chain (10 rules, simple variant) → `analysis/scripts/strategy_v40_rule10.py` (wraps v39 with Rule 10, no gate)
- Combined chain (10 rules, gated variant) → `analysis/scripts/strategy_v40b_rule10_gated.py` (wraps v39 with Rule 10 + gate `pair ≤ 6 OR pair == max`). Superseded by v41.
- Combined chain (10 rules, suit-aware bot) → `analysis/scripts/strategy_v41_rule10_v3_ds.py` (wraps v39 with Rule 10 v3 — same trigger + gate as v40b, but suit-aware bot construction picks singletons that yield DS bot when achievable). Superseded by v42.
- Combined chain (11 rules) → `analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py` (wraps v41 with Rule 11 — J-pair pair-to-bot DS, surgical override at the J-pair-J cell). Superseded by v43.
- Combined chain (12 rules) → `analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py` (wraps v42 with Rule 12 — J-low two_pair both-intact + DS-bot). Superseded by v44.
- Combined chain (13 rules) → `analysis/scripts/strategy_v44_rule13_three_pair_DS.py` (wraps v43 with Rule 13). Superseded by v45.
- Combined chain (14 rules) → `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` (wraps v44 with Rule 14). Superseded by v46.
- Combined chain (15 rules) → `analysis/scripts/strategy_v46_rule15_Khigh_DS.py` (wraps v45 with Rule 15). Superseded by v47.
- Combined chain (16 rules) → `analysis/scripts/strategy_v47_rule16_Qhigh_DS.py` (wraps v46 with Rule 16). Superseded by v52.
- **Combined chain (17 rules, CURRENT PRODUCTION)** → `analysis/scripts/strategy_v52_full_high_only_handler.py` (wraps v47 with Rule 17 = comprehensive high_only generalized handler covering all max ≥ 7 sub-pops)
- **DEFERRED (Session 42, reaffirmed Session 43)**: `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` — would-be Rule 8 for two_pair (+$197 full / -$512 prefix). Confirmed ML-only after Session 42 overnight investigation; reaffirmed Session 43 Q4 defensive re-examination.

**Probes:**
- Per-cell A-vs-C oracle map (Session 38) → `analysis/scripts/probe_rule6_c_variant.py`
- v33→v34 boundary sweep (Session 38) → `analysis/scripts/probe_v34_sweep.py`
- v35 human-decision verification (Session 39) → `analysis/scripts/verify_rule6_v3_human.py`
- Low-trips connectivity (Session 40) → `analysis/scripts/probe_low_trips_connectivity.py`
- High_only always-X (Session 41, ARCHIVED rule attempt) → `analysis/scripts/verify_rule_X_v33_high_only.py`, `analysis/scripts/probe_high_only_suited_mid_drill.py`
- Three_pair always-X (Session 41) → `analysis/scripts/verify_rule_X_v33_three_pair.py`, `analysis/scripts/probe_three_pair_boundary.py`, `analysis/scripts/probe_three_pair_final_rule.py`
- Two_pair always-X + boundary (Session 42, candidate DEFERRED) → `analysis/scripts/verify_rule_X_v33_two_pair.py`, `analysis/scripts/probe_two_pair_boundary.py`
- Composite always-X (Session 42, 4 subtypes) → `analysis/scripts/verify_rule_X_v33_composite.py`
- TT (two_trips) deterministic + E3a heuristic hunt (Session 42 overnight) → `analysis/scripts/drill_tt_two_trips_deterministic.py`, `analysis/scripts/drill_tt_e3a_heuristic_hunt.py`
- Plain quads structural (Session 42 overnight) → `analysis/scripts/drill_plain_quads_structural.py`
- T2P (trips_two_pair) initial + deeper (Session 42 overnight) → `analysis/scripts/drill_t2p_trips_two_pair_deterministic.py`, `analysis/scripts/drill_t2p_deeper_boundary.py`
- Two_pair split investigation + oracle pick characterization (Session 42 overnight) → `analysis/scripts/drill_two_pair_split_investigation.py`, `analysis/scripts/drill_two_pair_oracle_picks_full.py`
- Pair Rule 1 extension probe (Session 42 overnight) → `analysis/scripts/drill_pair_rule1_extension.py`
- Trips_pair refinement (Session 42 overnight) → `analysis/scripts/drill_trips_pair_refinement.py`
- High-card defense Q1+Q2+Q5 (Session 43, high_only) → `analysis/scripts/drill_high_card_defense.py`
- J-low pair defensive Q3 (Session 43) → `analysis/scripts/drill_low_pair_J_high_defense.py`
- J-low two_pair defensive Q4 re-examination (Session 43) → `analysis/scripts/drill_two_pair_J_high_revisit.py`
- v36 high_only Rule 7 grade (ARCHIVED) → `analysis/scripts/grade_v36_rule7.py`
- v37 three_pair Rule 7 grade → `analysis/scripts/grade_v37_rule7.py`
- v38 composite-QP Rule 8 grade → `analysis/scripts/grade_v38_rule8.py`
- v39 Rule 9 grade → `analysis/scripts/grade_v39_rule9.py`
- v40 Rule 10 grade → `analysis/scripts/grade_v40_rule10.py`
- v40b Rule 10 gated grade → `analysis/scripts/grade_v40b_rule10_gated.py`
- v41 Rule 10 v3 grade → `analysis/scripts/grade_v41_rule10_v3_ds.py`
- v42 Rule 11 J-pair pair-to-bot DS grade → `analysis/scripts/grade_v42_rule11_jpair_pbot_ds.py`
- v43 Rule 12 two_pair both-intact + DS grade → `analysis/scripts/grade_v43_rule12_two_pair.py`
- v43b Rule 12 max≤Q extension grade (Session 48, DEFERRED) → `analysis/scripts/grade_v43b_rule12_extQ.py`
- v44 Rule 13 three_pair all-intact + DS grade → `analysis/scripts/grade_v44_rule13_three_pair.py`
- v45 Rule 14 A-high no-pair grade → `analysis/scripts/grade_v45_rule14_Ahigh.py`
- v46 Rule 15 K-high no-pair grade → `analysis/scripts/grade_v46_rule15_Khigh.py`
- v47 Rule 16 Q-high no-pair grade → `analysis/scripts/grade_v47_rule16_Qhigh.py`
- v48 Rules 17-21 (HIMID J-7-high) grade → `analysis/scripts/grade_v48_rules17_21.py`
- v50 Rules 22-23 (defensive A/K/Q/J ≤ s2 8) grade → `analysis/scripts/grade_v50_defensive.py`
- v52 Rule 17 generalized high_only handler grade → `analysis/scripts/grade_v52_full_handler.py`
- A-high no-pair characterization (Session 50, Drill K) → `analysis/scripts/drill_A_high_nopair_characterization.py`
- A-high A-on-top bot heuristic sweep (Session 50, Drill L) → `analysis/scripts/drill_A_high_topA_bot_heuristic.py`
- K-high no-pair characterization (Session 51, Drill M) → `analysis/scripts/drill_K_high_nopair_characterization.py`
- Q-high no-pair characterization (Session 52, Drill N) → `analysis/scripts/drill_Q_high_nopair_characterization.py`
- Q-high non-Q-on-top characterization (Session 53 overnight, Drill O) → `analysis/scripts/drill_Q_high_non_Q_top_characterization.py`
- J-low pair DS-break drill (Session 45) → `analysis/scripts/drill_J_low_pair_DS_break.py`
- J-low two_pair DS-break drill (Session 45) → `analysis/scripts/drill_J_low_two_pair_DS_break.py`
- DS one-gap-4 vs DS run-4 across categories (Session 45) → `analysis/scripts/drill_DS_one_gap_vs_run4_other_cats.py`
- J-pair-J pair-to-bot DS focused drill (Session 46) → `analysis/scripts/drill_J_pair_pair_to_bot_DS.py`
- Rule 11 heuristic variant sweep (Session 47, NEGATIVE) → `analysis/scripts/drill_rule11_heuristic_sweep.py`
- Two_pair within-class DS variant sweep (Session 47) → `analysis/scripts/drill_two_pair_DS_within_intact.py`
- Two_pair max≥Q extension drill (Session 48) → `analysis/scripts/drill_two_pair_DS_extension.py`
- Three_pair within-class DS variant sweep (Session 48) → `analysis/scripts/drill_three_pair_DS_within_intact.py`

**ML champion + baselines (newest first):**
- v31 (CURRENT CHAMPION) → `analysis/scripts/strategy_v31_dt.py` + `data/v31_dt_model.npz` (700K leaves, 79 features, depth=32 ml=3 — capacity-only retrain of v30)
- v30 → `analysis/scripts/strategy_v30_dt.py` + `data/v30_dt_model.npz` (493K leaves, 79 features, depth=30 ml=5)
- v29 → `analysis/scripts/strategy_v29_dt.py` + `data/v29_dt_model.npz` (486K leaves, 73 features)
- v27 → `analysis/scripts/strategy_v27_dt.py` + `data/v27_dt_model.npz` (460K leaves, 69 features)
- v26 → `analysis/scripts/strategy_v26_dt.py` + `data/v26_dt_model.npz` (459K leaves, 65 features)
- v25 → `analysis/scripts/strategy_v25_dt.py` + `data/v25_dt_model.npz` (391K leaves, 59 features)
- v24 → `analysis/scripts/strategy_v24_dt.py` + `data/v24_dt_model.npz` (315K leaves, 53 features)
- v23 → `analysis/scripts/strategy_v23_dt.py` + `data/v23_dt_model.npz` (315K leaves, 49 features)
- v20 → `analysis/scripts/strategy_v20_dt.py` + `data/v20_dt_model.npz` (308K leaves)
- v18e → `data/v18e_dt_model.npz` (274K leaves)
- v18d → `data/v18d_dt_model.npz` (193K leaves)
- v18c → `analysis/scripts/strategy_v18c_dt.py` + `data/v18c_dt_model.npz` (125K leaves)
- v18 → `analysis/scripts/strategy_v18_dt.py` + `data/v18_dt_model.npz` (61K leaves)
- v16 → `analysis/scripts/strategy_v16_dt.py` + `data/v16_dt_model.npz` (29K leaves)

**Trainers:**
- v31 trainer = v30 trainer with `--max-depth 32 --min-samples-leaf 3` → `analysis/scripts/train_v30_dt.py` (no separate train_v31 file; v31 differs only in hyperparameters)
- v30 trainer (79 features incl. all 8 gated families) → `analysis/scripts/train_v30_dt.py`
- v29 trainer (73 features incl. 7 gated families) → `analysis/scripts/train_v29_dt.py`
- v27 trainer (69 features incl. 6 gated families) → `analysis/scripts/train_v27_dt.py`
- v26 trainer (65 features incl. 5 gated families + 3 pre-existing pair-gated booleans + 3 pre-existing two_pair-gated booleans) → `analysis/scripts/train_v26_dt.py`
- v25 trainer (59 features incl. 4 gated families + 3 pre-existing pair-gated booleans) → `analysis/scripts/train_v25_dt.py`
- v24 trainer (53 features incl. 3 gated families + 3 pre-existing pair-gated booleans) → `analysis/scripts/train_v24_dt.py`
- v23 trainer (49 features incl. gated suited + gated trips_pair) → `analysis/scripts/train_v23_dt.py`
- v18 capacity trainer (37 features) → `analysis/scripts/train_v18_dt.py`
- v19_gated trainer (43 features incl. gated suited) → `analysis/scripts/train_v19_gated_dt.py`
- v16 trainer (legacy, recomputes features) → `analysis/scripts/train_v16_regression.py`

**Aug feature compute:**
- Pair (3 pre-existing, already category-gated since Session 17 despite no `_g` suffix) → `analysis/scripts/pair_aug_features.py`
- Pair persist → `analysis/scripts/persist_aug_features.py` → `data/feature_table_aug.parquet`
- Gated pair (Session 32, 6 new features) → `analysis/scripts/pair_aug_features_gated.py`
- Gated pair persist → `analysis/scripts/persist_pair_aug_gated.py` → `data/feature_table_pair_aug_gated.parquet`
- Two_pair (3 pre-existing, already category-gated since Session 19) → `analysis/scripts/two_pair_aug_features.py` → `data/feature_table_two_pair_aug.parquet`
- Gated two_pair (Session 33, 6 new features, prefix `t2p_*`) → `analysis/scripts/two_pair_aug_features_gated.py`
- Gated two_pair persist → `analysis/scripts/persist_two_pair_aug_gated.py` → `data/feature_table_two_pair_aug_gated.parquet`
- Gated high_only-direct (Session 34, 4 new features, prefix `ho_*`) → `analysis/scripts/high_only_aug_features_gated.py`
- Gated high_only-direct persist → `analysis/scripts/persist_high_only_aug_gated.py` → `data/feature_table_high_only_aug_gated.parquet`
- Gated pair_r4 (Session 35, 4 new features, prefix `pair_r4_*`) → `analysis/scripts/pair_aug_v2_features_gated.py`
- Gated pair_r4 persist → `analysis/scripts/persist_pair_aug_v2_gated.py` → `data/feature_table_pair_aug_v2_gated.parquet`
- Gated trips (Session 36, 6 new features, prefix `trips_*` — NOT `tp_*` which is trips_pair) → `analysis/scripts/trips_aug_features_gated.py`
- Gated trips persist → `analysis/scripts/persist_trips_aug_gated.py` → `data/feature_table_trips_aug_gated.parquet`
- Gated pair_r4v3 (Session 36 overnight, 4 KK/AA-tight features, prefix `pair_r4v3_*` — ARCHIVED, candidate v31a) → `analysis/scripts/pair_aug_v3_features_gated.py`
- Gated trips_v2 (Session 36 overnight, 4 round-2 features, prefix `trips_v2_*` — ARCHIVED for now, candidate v31b; SLATED for v32 stack on top of v31's high-capacity config) → `analysis/scripts/trips_aug_v2_features_gated.py`
- Gated suited (high_only-via-suited, Session 30) → `analysis/scripts/suited_aug_features_gated.py`
- Gated suited persist → `analysis/scripts/persist_suited_aug_gated.py`
- Gated trips_pair → `analysis/scripts/trips_pair_aug_features_gated.py`
- Gated trips_pair persist → `analysis/scripts/persist_trips_pair_aug_gated.py`
- Gated composite → `analysis/scripts/composite_aug_features_gated.py`
- Gated composite persist → `analysis/scripts/persist_composite_aug_gated.py`

**Analysis:**
- v16 distillation → `analysis/scripts/distill_v16_dt.py`
- v26 high_only distillation (Session 34) → `analysis/scripts/distill_v26_high_only.py`
- v27 pair distillation + KK/AA capture analysis (Session 35) → `analysis/scripts/distill_v27_pair.py`
- v29 pair distillation round-2 + KK/AA round-2 audit (Session 36) → `analysis/scripts/distill_v29_pair.py`
- v29 trips distillation + routing-baseline analysis (Session 36) → `analysis/scripts/distill_v29_trips.py`
- KK/AA Rule-4 boundary probe (Session 34) → `analysis/scripts/probe_kk_aa_ds_bot_vs_mid.py` + `data/kk_aa_rule4_probe.csv`
- KKK/AAA routing probe (Session 34) → `analysis/scripts/probe_trips_kkk_aaa_routing.py` + `data/kkk_aaa_routing_probe.csv`
- Overnight v31 cascade runner (Session 36 → 37) → `analysis/scripts/overnight_v31_cascade.sh`
- High_only residual diagnostic → `analysis/scripts/high_only_v16_residual.py`
- Multi-strategy sweep grader → `analysis/scripts/grade_v18_sweep.py`

**Ground-truth grids (gitignored, large):**
- Full 6M × N=200 → `data/oracle_grid_full_realistic_n200.bin` (2.55 GB)
- Prefix 500K × N=1000 → `data/oracle_grid_prefix500k_n1000.bin`

**To validate any new rule against the grid in ~4 minutes:**
```python
from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid

grid = read_oracle_grid("data/oracle_grid_full_realistic_n200.bin", mode="memmap")
ch = read_canonical_hands("data/canonical_hands.bin", mode="memmap")
result = grade_strategy(my_strategy_fn, grid, ch, label="my_strategy")
print(result.summary())
```

---

# Part 6 — THE CURRENT STANDARD

> Everything below this line is the active rule set as of Session 37.
> If you only read one section, read this one.
>
> **Human-memorizable strategy of record: v14_combined + Rule 4 + Rule 5.**
> Five numbered rules plus a default play. Edge over v8_hybrid baseline:
> **+$1,015/1000h** at $10/EV-pt (full grid, N=200). A naive Rule 5
> (suited-mid for high_only) was tested in Session 31 in two flavors and
> **REJECTED**; the Rule 5 here (KK/AA Rainbow override, Session 34) is
> a much tighter structural rule that fires on only 0.27% of hands and
> is the **first successful Rule 5 in project history** — see Decision
> 063 in DECISIONS_LOG.md.
>
> **Rule 4 extends to KKK and AAA.** The Session 34 probe
> `probe_trips_kkk_aaa_routing.py` confirms that "keep 2 of 3 trip-rank
> cards in mid as a pair" is BR-optimal on **79.18%** of KKK/AAA hands
> (83.84% for AAA, 74.53% for KKK). The DS-bot-split exception (~24%
> of geometrically-eligible cases) is hard to apply manually pre-flop;
> for human play, treat KKK and AAA the same as KK and AA — pair in mid.
> See Decision 062.
>
> **Open Rule 6 candidate (Session 36 finding, not yet codified):**
> The trips diagnostic (`distill_v29_trips.py`) showed that **Always
> A_paired_mid** (set 2 of 3 trip-rank cards in mid as a pair) captures
> $85/1000h whole-grid relative to v29's 80%-A / 20%-deviation pattern.
> This is the structural analog of Rule 4 for trips, EXTENDED beyond
> KKK/AAA to all trip ranks. v14_combined likely already encodes this
> implicitly via its v3 default; needs verification before formal Rule 6
> codification. The per-rank deviation cost from v29 is highest on low
> trips (2-9 each leak $7-8/rank-share). See Decision 065 and 066.
>
> **ML champion (not human-memorizable): v43_dt (end of Session 57)** —
> 2,177,798-leaf DecisionTreeRegressor (depth=36, min_samples_leaf=1),
> 103 features including all the gated families through v42 plus 4 new
> `ho_v3_topMax_DS_ms_*_g` features encoding JOINT (DS bot + ms mid)
> achievability + quality conditional on top=max-rank-of-hand. Score:
> **$1,123/1000h full grid / $686 prefix** — beats v14 by **+$1,910/1000h**
> on the full grid and **+$1,351/1000h** on the prefix N=1000. Lives at
> `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz`
> (1,224 MB).
>
> The cumulative 8-ship ML arc since v32: v32 → v34 → v36 → v39 → v40 →
> v41 → v42 → v43 = **−$592/1000h on the full grid**. Each ship is
> surgical (other categories byte-identical) thanks to category-gated
> features that fire on zero off-archetype hands by design. Both
> diagnostic-driven feature engineering (S54+ playbook) and capacity
> retrains (v31, v34, v36) are in the toolkit.
>
> The two production tracks now diverge by **$1,375/1000h** —
> v43_dt at $1,123 beats the v52 rule chain at $2,498 by more than half
> the rule-chain EV deficit.

---

## How to use this guide (current standard)

Walk through Step 1, then apply the matching rule from Step 2.
For hand types not covered, play it the obvious way (highest card on top,
suited cards together in mid, rest to bot) — that's what v8 does and it's
adequate on the un-ruled categories.

---

## Step 1 — Categorize your 7 cards

Look for the strongest "shape" in your hand:

| Shape | Cards | Apply rule |
|---|---|---|
| Plain quads | 4 of one rank + 3 singletons | **Rule 9a** — mid = the 2 quad cards at the non-singleton-suits |
| Quads + pair | 4 of one rank + 2 of another (4+2+1) | **Rule 8** — mid = the 2 quad cards at the non-pair-suits |
| Two trips | 3 of one rank + 3 of another (3+3+1) | **Rule 9b** — split-the-high-trip-to-top, suit-aware |
| Trips + two pairs | 3 of one rank + 2 of two others (3+2+2) | **Rule 9c** — F3 if trip≤4 else F2 (split-trip-to-top) |
| Trips + pair | 3 of one rank + 2 of another | **Rule 3** |
| Trips (any rank, no other pair) | 3 of one rank, no other pair | **Rule 6** — mid is always 2 of the 3 trip cards |
| Two pairs | 2 of one rank + 2 of another | **Rule 2** |
| One pair (KK or AA) | 2 Kings or 2 Aces | **Rule 4** (default), check **Rule 5** for rainbow override |
| One pair (other ranks), MAX ≤ J AND (pair ≤ 6 OR pair == max) | 2 of one rank + max ≤ J + low-pair-or-pair-is-max | **Rule 10 (gated)** — defensive: top=lowest, mid=pair, bot=4 highest non-pair |
| One pair (other ranks), MAX card ≥ Q | 2 of one rank + at least one Q/K/A, no other multiples | **Rule 1** (gates apply) — Rule 10 does NOT fire here |
| One pair (other ranks), MAX ≤ J AND pair ∈ {7,8,9,T} (and pair ≠ max) | 2 of one rank, max ≤ J, mid-rank pair below max | Default play (Rule 10's gate excludes this — v3-style top=highest) |
| No pair | 7 distinct ranks | (no simple rule yet — multi-archetype) |

---

## Rule 1 — Single pair: pair-to-bot for double-suited

**Fires only if ALL of these are true:**

1. **Pair rank is 2-5 OR T-J-Q.** Skip 6-7-8-9 (Goldilocks zone — pair stays in mid).
2. **Exactly one Ace** in the hand. No pair of Aces, no second pair of any rank.
3. **The pair has two different suits** (e.g., Q♣ + Q♦). Same-suit pairs can't anchor a double-suited bot.
4. **Kickers are balanced between the pair's two suits.** Count the 4 non-pair, non-Ace cards. Of those, count how many match each pair-suit. Must be **(1,1), (2,2), (1,3), or (3,1)**. Skip lopsided **(2,1) or (1,2)**.

**The play (when fired):**
- **Top** = the Ace
- **Bot** = both pair-cards + the LOWEST kicker of each pair-suit (gives a 2+2 double-suited bot)
- **Mid** = the 2 leftover kickers

**Worked example:** `3♣ 4♦ 8♦ 9♣ Q♣ Q♦ A♣`
- Pair = QQ ✓ (rank 12), one Ace ✓, two pair-suits ✓
- Kickers split: clubs {3♣, 9♣} = 2, diamonds {4♦, 8♦} = 2 → (2,2) balanced ✓
- Lowest club kicker = 3♣, lowest diamond kicker = 4♦
- → **Top = A♣, Mid = 9♣ + 8♦, Bot = Q♣ + Q♦ + 3♣ + 4♦**

**Counter-example (don't fire):** `Q♣ Q♦ A♥ 3♣ 5♣ 4♦ 9♠`
- Kickers: 3♣, 5♣ are clubs (matching Q♣) = 2; 4♦ is diamond (matching Q♦) = 1; 9♠ is spade = 0
- (n_clubs, n_diamonds) = (2, 1) → lopsided, **don't fire**
- Play it the v8 way (pair in mid).

**Why it works:**
- **Low pairs (2-5)**: weak in mid (a pair of 4s loses Hold'em to almost any pair). Better to use the pair as a bot suit-anchor for a DS flush draw.
- **High non-anchor pairs (J-Q)**: strong in mid, but bot-pair-with-DS is even stronger — you keep the pair value AND gain two flush draws.
- **Mid pairs (6-9)**: Goldilocks zone. Strong enough in mid (wins Hold'em often) and not strong enough that bot help is needed. Leave them in mid.
- **KK / AA**: keep in mid (see Rule 4).
- **Asymmetric kickers**: when (n_a, n_b) is (2,1) or (1,2), the leftover-mid is two cards of mismatched suits with no Hold'em synergy — a weak mid. Symmetric kickers preserve mid strength.

**Fires on:** 2.19% of all hands (~1 in 45 you'll be dealt).

---

## Rule 2 — Two pairs: never split either pair

**Fires whenever you have exactly two pairs** (and no trips/quads).

**The play:** never break either pair. There are exactly 3 valid no-split layouts:

| Layout | Mid | Bot | Top |
|---|---|---|---|
| A | 2 kickers | both pairs (4 cards) | 1 kicker |
| B | higher pair | lower pair + 2 kickers | 1 kicker |
| C | lower pair | higher pair + 2 kickers | 1 kicker |

**Pick the layout that maximizes (in order):**
1. Bot is double-suited (2+2) > single-suited (2+1+1) > rainbow > 3+1 > 4-flush
2. Top rank (Ace > K > Q ...)
3. Mid is paired > offsuit broadway > suited connector > other

**Worked example:** `7♣ 7♦ 8♣ 8♦ J♥ K♠ A♠`
- Two pairs: 88 and 77.
- **What v8 wrongly does**: top=K, mid=8♣+7♦ (suited connector), bot=A+J+8+7 (rainbow with both pairs split). Bleeds **$46K/1000h**.
- **What Rule 2 does**: Layout A — top=A♠, mid=K♠+J♥ (offsuit broadway), bot=8♦+8♣+7♦+7♣ (both pairs intact, double-suited).

**Why it works:**
- Two pairs as a unit in the bot give you a guaranteed Omaha 2-pair AND two flush draws.
- v8's "suited connector mid" trade gives up a much stronger bot for a moderately stronger mid — the tier-importance ratio (bot:mid:top = 3:2:1) means bot wins.
- The pair that joins the bot uses ITS suits as the bot's DS anchors.

**Fires on:** every two_pair hand (~22% of all hands you'll be dealt).

---

## Rule 3 — Trips + pair: split the trips, keep the pair

**Fires when you have 3 of one rank + 2 of another + 2 kickers.**

**The play:** the trips MUST split (3 of them can't fit in mid; mid only holds 2). Keep the pair intact. Two valid layouts:

| Layout | Mid | Bot | Top |
|---|---|---|---|
| A | 2 of the 3 trip-cards (paired mid) | original pair + 1 trip-overflow + 1 kicker | 1 kicker |
| B | 1 trip + 1 kicker | original pair + 2 trip-cards (4 cards = 2 pairs) | 1 kicker |

**Pick by priority:**
1. Bot is double-suited > SS > rainbow
2. Top rank
3. Slight preference for Layout A (paired mid is robust)

**Worked example:** `4♣ T♦ T♥ T♠ J♣ J♦ Q♦`
- Trips = TTT, pair = JJ, kickers = 4♣ + Q♦.
- **What v10 wrongly does**: top=J, mid=Q+J, bot=T+T+T+4 (rainbow, breaks the trips weirdly). Bleeds **$50K/1000h**.
- **What Rule 3 does**: Layout A — top=Q♦, mid=T♠+T♥ (paired mid), bot=J♦+J♣+T♦+4♣ (DS).

**Why it works:**
- A paired-mid (2 of the 3 trip cards) is roughly as strong as the original pair-in-mid would be.
- The bot gets the original pair + 1 trip-card + 1 kicker — that's TWO PAIRS in the bot with DS anchors. Much stronger than v8's "all 3 trips in bot, no pair structure."

**Fires on:** every trips_pair hand (~3% of all hands).

---

## Rule 4 — Premium pair (KK or AA): pair stays intact in mid

**Fires whenever your pair is KK or AA** (and you don't have quads).

This rule formalizes what `strategy_v8_hybrid` (and therefore the v14
fallback) already does, and the v16 DT confirms is correct. It's been
implicit in the codebase since v3; making it explicit here so a human
memorizing the strategy doesn't accidentally split the pair.

**The play:**
- **Mid** = both pair cards (KK or AA), intact
- **Top** = the highest non-pair card you hold (the Ace if KK + lone Ace;
  otherwise the next-highest singleton)
- **Bot** = the remaining 4 cards

**Worked example (KK with lower body):** `4♣ 6♦ 8♥ J♠ Q♦ K♣ K♠`
- Pair = KK. Highest non-pair = Q♦.
- **Play**: top=Q♦, mid=K♣+K♠ (intact), bot=4♣+6♦+8♥+J♠.

**Worked example (KK with Ace singleton):** `4♣ 6♦ 8♥ Q♦ K♣ K♠ A♥`
- Pair = KK plus an A♥ singleton. Highest non-pair = A♥.
- **Play**: top=A♥, mid=K♣+K♠ (intact), bot=4♣+6♦+8♥+Q♦.
- *No K split occurs* — the Ace becomes top, the KK stays in mid, the
  Q drops to bot. v3 / v8 / v16 / v20 all agree on this exact setting.

**Worked example (AA + broadway body):** `9♣ T♦ J♥ Q♠ K♣ A♦ A♠`
- Pair = AA. Highest non-pair = K♣.
- **Play**: top=K♣, mid=A♦+A♠ (intact), bot=9♣+T♦+J♥+Q♠.

**AA-with-low-body edge case:** `2♣ 3♦ 4♥ 5♠ 6♣ A♥ A♠`
- Pair = AA, body is all 2-6. v3/v8 pick top=6♣ (highest non-A).
- v16 picks **top=2♣ (lowest), mid=A♥+A♠, bot=3♦+4♥+5♠+6♣**. The DT is
  trading top strength (a 6 on top loses 90% anyway) for a slightly
  stronger bot (3-4-5-6 connected, gives a wheel-style straight draw).
- For human play, follow Rule 4 as stated (top = highest non-pair). The
  edge case is a small EV refinement ($0.01-0.05/hand) that requires
  computing 105 EVs to justify and doesn't generalize cleanly.

**Why it works:**
- KK and AA are the strongest mid-tier Hold'em holdings (win ~80% of
  unpaired-board matchups). Splitting them throws away most of that
  value for marginal top upside.
- The "highest non-pair to top" subrule is what v3/v8/v16/v20 all
  converge on — when KK + A are present, the A naturally goes to top
  because it's the highest non-K (no special-case needed).
- `has_premium_pair` is the 5th-most-important feature in the v16 DT
  (4.5% of total feature importance) — the model discovered this
  population split on its own.

**Fires on:** 7.17% of all hands (KK 3.58% + AA 3.58%).

---

## Rule 5 — KK/AA Rainbow override: swap to DS-bot when Rule 4 leaves a rainbow Omaha hand

**Fires only when ALL of these are true** (very narrow trigger — fires on ~0.27% of all hands):

1. **Pair = KK or AA** (Rule 4 territory)
2. **Pair has two different suits** (e.g., K♠+K♦ — DS-anchor possible)
3. **Apply Rule 4 mentally and look at the resulting bot.** If the 4 leftover cards (after putting the highest non-pair card on top and the pair in mid) span all 4 suits → **bot is rainbow**.
4. **DS-bot is geometrically possible:** at least one kicker matches each pair-suit.

**The play (when fired):** Override Rule 4 — put the pair in bot.
- **Bot** = both pair-cards + the lowest-rank kicker matching each pair-suit (gives a 2+2 double-suited bot)
- **Top** = the highest-rank card of the 3 leftover non-pair cards
- **Mid** = the other 2 leftover cards (will often be off-suit and weak — that's OK)

**Worked example (the canonical case):** `K♠K♦ 3♠ 5♦ 9♥ T♣ J♠`
- Pair = KK ✓, two different suits (♠+♦) ✓
- Rule 4 routing: top=J♠, mid=K♠K♦, bot=3♠5♦9♥T♣ — bot has 1 of each suit → **rainbow**, trigger fires.
- DS-bot available: 3♠ matches ♠, 5♦ matches ♦ ✓
- Rule 5 play: **bot = K♠K♦5♦3♠** (2 ♠ + 2 ♦, double-suited), **top = J♠** (highest leftover), **mid = T♣9♥**
- EV result: Rule 5 routing scores **+3.025 EV** vs Rule 4's +1.225 EV — **the override wins by 1.80 EV ($18,000/1000h on this single hand)**.

**Why it works:**
- A rainbow Omaha bot is essentially dead — you can't make any flush or strong-suited play. Whatever's in mid (a pair of Kings) is also limited to Hold'em equity only.
- A 2-2 DS bot anchored by KK retains the pair-on-board strength (set draws, two-pair) AND gains two flush draws. The trade is: give up KK-as-pair in mid (worth ~+0.4 EV) for a 2-2 DS bot anchored by KK (worth ~+1.4 EV vs rainbow). Net ~+1.0 EV swing.
- The "mid is weak" cost is small in TW Poker — a random 2-card mid loses to opponent's mid by maybe 0.5 EV. The gain from a live bot dwarfs the mid loss.

**Why the gates are this narrow:**
- **Premium pair only:** lower pairs (Q and below) generally do better in mid because their kickers play well alongside (e.g., QQ + AKxx in mid + bot has more options).
- **Two pair-suits:** if KK is K♠+K♠... wait that's impossible. The pair always has two different suits given a 52-card deck. Actually, this gate is structurally automatic for KK/AA — but stated for completeness.
- **Rainbow Rule-4-bot:** this is the strongest signal that Rule 4 is leaving value on the table. When Rule-4-bot is single-suited or DS, Rule 4 is correct most of the time.
- **DS feasibility:** without one kicker in each pair-suit, you can't even build the DS bot.

**Why earlier Rule 5 attempts (v21, v22) failed:** Both v21 and v22 (Session 31) attempted Rule 5 by firing on ~5-13% of all hands — much too eager. They lost $473-$680/1000h vs v14. v28's Rule 5 (this rule) fires on 0.27% of all hands — 20-50× tighter. The structural rainbow trigger is far more selective than the rank-based triggers (msphr ≥ 9, etc.) those attempts used. **First successful Rule 5 in the project's history** (Session 34, Decision 063).

**Fires on:** 0.27% of all hands (~1 in 370 you're dealt). Rare, but the per-hand wins are dramatic.

**Empirical lift over v14_combined:** +$1/1000h whole-grid (small but POSITIVE — comparable to v24's marginal ML ship). The whole-grid number is small because the rule fires rarely; the per-hand wins on the firing subset are large ($15K-$18K/1000h on hands like the worked example).

---

## Rule 6 — Pure trips: 2 of the 3 trip cards always go to mid (the third NEVER goes to bot)

**Fires whenever you have trips of any rank (and no second pair, no quads).**
This rule supersedes the prior Rule 4 (extended), which covered only KKK/AAA.
The principle is simple — **mid is paired with the trip rank** — and the only
remaining decision is whether the third trip card goes on **top** or joins **bot**.
The rest of this section is a hand-traceable answer to that question.

### The setup (always)

- **Mid** = 2 of the 3 trip cards (paired mid, ~80% Hold'em equity).
- The third trip card goes to **either top or bot** — never split out separately, never two-trips-on-bot.
- The 4 non-trip cards (your **kickers**) fill the rest.

### Step 1 — Where does the third trip card go (top or bot)?

The decision depends only on your **trip rank** and what kickers are in your hand:

| Trip rank | Where the third trip card goes | Why |
|---|---|---|
| **Trip A (AAA)** | **Always TOP.** | Nothing beats Ace on top. |
| **Trip K (KKK)** | **TOP**, unless you also hold an **A** in kickers (then put the A on top, third K to bot). | An Ace on top still beats your K. |
| **Trip Q (QQQ)** | **TOP**, unless you hold a **J, K, or A** in kickers (then put the highest such card on top, third Q to bot). | Even a J on top beats Q on top *more often than you'd think* — see "Why" below. |
| **Trip J or lower** | **Always BOT.** Highest non-trip card goes on top. | At J or below, every kicker layout makes "third trip in bot + best singleton on top" the better setting. |

When the third trip card goes to **bot**, the bot becomes 1 trip + 3 lowest non-trip cards, and the next two steps decide which trip that is.

### Step 2 — Which of the 3 trip cards joins bot? (Suit-matching, no math)

Used only when Step 1 sent the third trip to bot — i.e., trip rank ≤ J, **or** trip Q with J/K/A kicker, **or** trip K with A kicker.

You're trying to make the bot **double-suited (2+2)** — two cards each of two different suits — because DS bots dominate the Omaha bot equity. Look at the 3 kickers heading to the bot.

**Look at your 3 kickers' suits and identify the pattern:**

- **Two kickers share a suit, one is different** ("two-and-one") — the most common case.
- **All three kickers different suits** ("rainbow kickers").
- **All three kickers same suit** (rare).

**Then pick the trip card whose suit gives the best bot in this priority:**

| Bot shape | How to spot it | Quality |
|---|---|---|
| **2+2 (DS)** ✓ best | Trip suit matches the **lone (singleton)** kicker — making 2 of *that* suit and 2 of the kicker-pair suit | Two flush draws, dominant Omaha shape |
| **2+1+1 (SS)** OK | Trip suit matches a kicker that wasn't already paired in kickers (i.e., a fresh second of an existing kicker suit, or fills out a rainbow) | One flush draw |
| **3+1** ✗ avoid | Trip suit matches the **kicker pair suit** (now you have 3 of one suit on bot) | Third suited card is dead — only 2 from hand can be used |
| **4-flush** ✗ never | All 4 bot cards same suit | Worst Omaha shape |

**Rule of thumb**: **never let the third trip suit equal the kicker pair suit** (that's the 3+1 trap). When in doubt, pick the trip whose suit appears **least often** in the kickers.

### Worked examples

**Example 1 — Trip A (always top):** `2♦ 4♣ 7♥ J♠ A♣ A♦ A♥`
- Trip A → third A on top, no exceptions.
- Top = A♣ (any A — they're suit-symmetric on top). Mid = A♦ + A♥. Bot = J♠ + 7♥ + 4♣ + 2♦.
- **Play**: top=A♣, mid=A♦+A♥, bot=J♠+7♥+4♣+2♦.

**Example 2 — Trip K, no Ace:** `4♣ 7♦ 9♥ Q♠ K♣ K♦ K♠`
- Trip K, no A in kickers → third K on top.
- Top = K♣. Mid = K♦ + K♠. Bot = Q♠ + 9♥ + 7♦ + 4♣.
- **Play**: top=K♣, mid=K♦+K♠, bot=Q♠+9♥+7♦+4♣.

**Example 3 — Trip K, with Ace (third K to bot):** `4♣ 7♦ 9♥ A♥ K♣ K♦ K♠`
- Trip K, A in kickers → A goes on top, third K joins bot.
- Top = A♥. Bot kickers = 4♣, 7♦, 9♥ — rainbow (3 different suits).
- Step 2: rainbow kickers + trip K's suits {♣, ♦, ♠}. Match to a kicker suit: K♣ → 2♣ in bot; K♦ → 2♦ in bot. K♠ → still rainbow (♠ not in kickers). Both K♣ and K♦ give 2+1+1 (SS). K♠ gives rainbow.
- Pick K♣ or K♦ (either is fine — same SS shape). Mid = the other 2 K's plus K♠ on... wait, mid is 2 K's. Pick K♣ to bot, mid = K♦ + K♠.
- **Play**: top=A♥, mid=K♦+K♠, bot=K♣+9♥+7♦+4♣.

**Example 4 — Trip Q, with J kicker (third Q to bot, sharper than v14/v33):** `2♥ 4♣ 7♦ J♠ Q♣ Q♦ Q♥`
- Trip Q, J in kickers → J goes on top, third Q joins bot. (This is the case where v33's old "trip > max kicker" boundary picked C and put a Q on top — the sharper rule says J on top.)
- Top = J♠. Bot kickers = 2♥, 4♣, 7♦ — rainbow. Trip suits = {♣, ♦, ♥}, all match a kicker → any pick gives 2+1+1.
- Pick Q♣ for bot (matches 4♣). Mid = Q♦ + Q♥.
- **Play**: top=J♠, mid=Q♦+Q♥, bot=Q♣+7♦+4♣+2♥.

**Example 5 — Trip J, low kickers (always third J to bot):** `2♣ 4♣ 6♥ 9♦ J♣ J♦ J♠`
- Trip J → third J always on bot (trip rank ≤ J).
- Top = 9♦ (highest kicker). Bot kickers = 2♣, 4♣, 6♥. Suits: ♣, ♣, ♥ → "two-and-one" (♣♣♥).
- Step 2: kicker pair = ♣, kicker singleton = ♥. Trip suits = {♣, ♦, ♠}.
  - J♣ → bot 3♣+1♥ = **3+1 ✗ avoid** (third club is dead).
  - J♦ → bot 2♣+1♥+1♦ = 2+1+1 (SS).
  - J♠ → bot 2♣+1♥+1♠ = 2+1+1 (SS).
  - (No J♥, so the perfect 2+2 is unavailable.)
- Pick J♦ or J♠ (either SS — equivalent). Mid = J♣ + the other.
- **Play**: top=9♦, mid=J♣+J♠, bot=J♦+6♥+4♣+2♣.

**Example 6 — Trip 7, finds a 2+2:** `3♥ 5♥ 8♣ Q♣ 7♣ 7♦ 7♠`
- Trip 7 → third 7 always to bot. Top = Q♣ (highest non-trip). Bot kickers = 3♥, 5♥, 8♣.
- Suits: ♥♥♣ → "two-and-one" (pair=♥, singleton=♣). Trip suits = {♣, ♦, ♠}.
  - 7♣ → bot 1♣+1♣+2♥ = 2+2 (DS) ✓ — wait, that's 2♣ (3♥+5♥+8♣+7♣) = 2♥+2♣. Yes 2+2.
  - 7♦ → bot 2♥+1♣+1♦ = 2+1+1 (SS).
  - 7♠ → bot 2♥+1♣+1♠ = 2+1+1 (SS).
- Pick 7♣ — **2+2 double-suited bot**. Mid = 7♦ + 7♠.
- **Play**: top=Q♣, mid=7♦+7♠, bot=7♣+8♣+5♥+3♥.

### Trips ≤ J reference table — one worked example per rank

Trip A, K, Q are covered above (Examples 1–4). Trip J and Trip 7 are also covered (Examples 5–6). The 8 examples below fill in **every remaining rank from T down to 2**. The procedure is mechanical at every rank — only the suit layout changes — but seeing one hand at each rank makes it easier to recognize at the table.

Three things to notice as you scan these:

1. **The procedure is the same every time.** Step 1 always sends the third trip to bot (trip ≤ J). Step 2 always uses the suit-matching priority to pick which of the 3 trips joins bot. There is no "different rule for low trips."
2. **Connectivity (4-card runs, wheel structures) is incidental, not a tier.** Trip 6 with kickers 4-5-7 makes a 4-card run on bot (4-5-6-7); Trip 5 with kickers 2-3-4 makes the wheel-eligible bot 2-3-4-5. In both cases, **every** trip-to-bot pick gives the same run length, so the run is not a tiebreaker. Step 2 still picks by suit. (Confirmed by Session 40 connectivity probe — 0/196 hands where rainbow-run-4 is available does the oracle pick it; an alt tier "DS > rainbow run≥3 > SS" regresses $11/1000h whole-grid.)
3. **Hand strength drops fast as trip rank drops.** Trip 5 with low kickers is structurally weak no matter how you set it. The rule still tells you the right answer; it just can't make a low-trip hand into a strong hand.

In the suit notation below, "trip suits {♣, ♦, ♥}" means your three trip cards are clubs, diamonds, hearts (no spade). Bot-shape codes: **DS** = 2+2 double-suited, **SS** = 2+1+1 single-suited, **3+1** = three-of-a-suit (avoid), **rainbow** = 1+1+1+1.

**Example 7 — Trip T:** `7♦ 8♣ 9♥ T♣ T♦ T♥ J♠`
- Trip T → third T to bot (trip ≤ J). Top = J♠. Bot kickers below: 9♥, 8♣, 7♦ — suits ♥♣♦, **rainbow**.
- Trip suits {♣, ♦, ♥} (no ♠ in trip).
- T♣ → bot ♣♥♣♦ = SS (♣♣). T♦ → SS (♦♦). T♥ → SS (♥♥). All three give SS — kickers are rainbow, so any trip suit pairs with a kicker suit. **No DS available.**
- Pick any (they're equivalent). **Play**: top=J♠, mid=T♦+T♥, bot=T♣+9♥+8♣+7♦.

**Example 8 — Trip 9, find a DS:** `2♣ 5♥ 8♥ 9♣ 9♦ 9♥ Q♠`
- Trip 9 → third 9 to bot. Top = Q♠. Bot kickers: 8♥, 5♥, 2♣ — suits ♥♥♣, **two-and-one** (pair=♥, singleton=♣).
- Trip suits {♣, ♦, ♥}.
  - 9♣ → bot ♣♥♥♣ = **DS (2♣+2♥) ✓**
  - 9♦ → bot ♦♥♥♣ = SS (♥♥)
  - 9♥ → bot ♥♥♥♣ = **3+1 ✗ avoid** (third heart is dead)
- Pick **9♣**. **Play**: top=Q♠, mid=9♦+9♥, bot=9♣+8♥+5♥+2♣.

**Example 9 — Trip 8, 3+1 trap visible:** `2♥ 5♣ 7♣ 8♣ 8♦ 8♠ Q♣` (note: trip suits are ♣♦♠, no ♥)
- Trip 8 → third 8 to bot. Top = Q♣. Bot kickers: 7♣, 5♣, 2♥ — suits ♣♣♥, **two-and-one** (pair=♣, singleton=♥).
- Trip suits {♣, ♦, ♠} (no ♥ available, so the 2+2 DS that would need a ♥-trip is impossible).
  - 8♣ → bot ♣♣♣♥ = **3+1 ✗ avoid**
  - 8♦ → bot ♦♣♣♥ = SS (♣♣) ✓
  - 8♠ → bot ♠♣♣♥ = SS (♣♣) ✓
- Both 8♦ and 8♠ give SS — equivalent, pick either. The takeaway: when no 2+2 is available because your trip is missing the singleton's suit, you settle for SS but **never let your trip be the kicker-pair suit** (8♣ here). **Play**: top=Q♣, mid=8♣+8♠, bot=8♦+7♣+5♣+2♥.

**Example 10 — Trip 6, 4-run bot:** `4♦ 5♣ 6♣ 6♦ 6♥ 7♥ T♠`
- Trip 6 → third 6 to bot. Top = T♠. Bot kickers: 7♥, 5♣, 4♦ — suits ♥♣♦, **rainbow**.
- Bot ranks once a trip joins: {6, 7, 5, 4} — that's **4-5-6-7, a 4-card run**. Looks juicy, but the run is the same regardless of which 6 you pick.
- Trip suits {♣, ♦, ♥}. With rainbow kickers, every trip suit gives SS (no DS available).
  - 6♣ → SS (♣♣). 6♦ → SS (♦♦). 6♥ → SS (♥♥).
- Pick any. **Play**: top=T♠, mid=6♦+6♥, bot=6♣+7♥+5♣+4♦. Bot has a 4-card straight draw; that's just a bonus.

**Example 11 — Trip 5, wheel-eligible bot:** `2♦ 3♣ 4♥ 5♣ 5♦ 5♥ K♠`
- Trip 5 → third 5 to bot. Top = K♠. Bot kickers: 4♥, 3♣, 2♦ — suits ♥♣♦, **rainbow**.
- Bot ranks once a trip joins: {5, 4, 3, 2} — **wheel-eligible** (with an Ace on the board, 2-3-4-5-A is a straight, the wheel). Same wheel structure regardless of which 5 you pick.
- Trip suits {♣, ♦, ♥}. Rainbow kickers + any trip suit = SS.
  - 5♣, 5♦, 5♥ all give SS (each pairs with a kicker suit).
- Pick any. **Play**: top=K♠, mid=5♦+5♥, bot=5♣+4♥+3♣+2♦. The wheel structure adds a real chunk of bot equity, but it's structural — Step 2 didn't have to "find" it.

**Example 12 — Trip 4, weak hand, simple SS:** `2♦ 4♣ 4♦ 4♥ 7♥ 9♣ A♠`
- Trip 4 → third 4 to bot. Top = A♠ (highest non-trip — your Ace is your one strong card). Bot kickers: 9♣, 7♥, 2♦ — suits ♣♥♦, **rainbow**.
- Trip suits {♣, ♦, ♥}. Rainbow + any → SS.
- Pick any. **Play**: top=A♠, mid=4♦+4♥, bot=4♣+9♣+7♥+2♦. Hand is weak overall — Ace scoops top, but mid (a pair of 4s) and bot (low cards) lose to most opponent settings. The rule is doing its job; the cards aren't.

**Example 13 — Trip 3:** `3♣ 3♦ 3♥ 5♦ 8♥ T♣ K♠`
- Trip 3 → third 3 to bot. Top = K♠. Bot kickers: T♣, 8♥, 5♦ — suits ♣♥♦, **rainbow**.
- Trip suits {♣, ♦, ♥}. Rainbow + any → SS.
- Pick any. **Play**: top=K♠, mid=3♦+3♥, bot=3♣+T♣+8♥+5♦.

**Example 14 — Trip 2, lowest possible:** `2♣ 2♦ 2♥ 4♦ 7♥ J♣ A♠`
- Trip 2 → third 2 to bot. Top = A♠. Bot kickers: J♣, 7♥, 4♦ — suits ♣♥♦, **rainbow**.
- Trip suits {♣, ♦, ♥}. Rainbow + any → SS.
- Pick any. **Play**: top=A♠, mid=2♦+2♥, bot=2♣+J♣+7♥+4♦. Trip 2s are about as weak as trips get; the Ace on top is the only material part of the hand.

### Why it works

- **Mid is paired** (2 trips together) — Hold'em equity ~80% on unpaired boards (same as KK/AA stay-in-mid logic from Rule 4).
- **Never put the third trip on bot AS THE ONLY trip there** — that would split the paired mid. Either both extra trips stay in mid (third on top) or one trip joins bot (paired mid is preserved).
- **The boundary in Step 1** comes from the oracle: the per-cell map of best-A vs best-C across (trip rank × max kicker rank) shows that A wins on average for **trip ≤ J in every cell**, **trip Q whenever J/K/A is present**, **trip K only when an Ace is present**, and **trip A never**. Earlier versions of this guide used the simpler boundary "trip > max kicker → top is the trip card" (v33), which is right at the high end (Trip A, K-without-A, Q-with-T-or-lower) but **picks the wrong top in three places**: Trip Q + J kicker, Trip J + low kickers, and Trip T + low kickers. Sharpening these is +$8/1000h whole-grid at the human ceiling (oracle-bound).
- **Connectivity is not a Step 2 tier (Session 40 confirmation).** Bot 4-card runs and wheel-eligible bots happen incidentally on low-trip + low-kicker hands, but every trip-to-bot pick on the same hand gives the same run length, so connectivity is invariant across the 3 candidates. The Session 40 probe (`probe_low_trips_connectivity.py`) tested the alternative "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1" tier and found it regresses $11/1000h whole-grid versus the existing DS > SS > rainbow > 3+1 priority. The oracle picks rainbow 0% of the time when SS or DS is available; rainbow-run-4 picks are oracle-preferred 0/196 (0%) of the hands where they exist.

### Probe history

- **v14 picks "mid is paired" on only 94.3% of pure trips.** The 5.4% routing the 3rd trip to bot **alone** loses $197/1000h whole-grid vs the always-paired-mid baseline (Session 37 verify_rule6_v14_trips probe).
- **v33 (Session 37 ship)** locked in "third trip never bot-only" + "trip > max kicker → top is trip rank, else top is max kicker". That ships **+$112/1000h whole-grid full grid / +$143/1000h prefix** vs v28 — the largest single rule ship in project history.
- **v33 boundary's heuristic ceiling**: 56% of the $197 always-A∪C oracle ceiling. The remaining 44% gap is explained by an under-optimized A-variant heuristic for "which trip joins bot" (Session 38 sweep, `probe_v34_sweep.py`).
- **Session 38's per-cell oracle probe** (`probe_rule6_c_variant.py`) showed v33's boundary is wrong on 28.8% of "v33 picks C" cells — projected oracle ceiling of $+12.89/1000h whole-grid by flipping those cells to A.
- **v35 boundary (this section, Session 39)** captures **+$8.12/1000h whole-grid at the human ceiling** (oracle-bound) on the same 30K probe, while sacrificing the noisy/marginal trip-J + low-kicker cells the user simplified out for memorability. **Decision 071** ships v35 as the strategy of record for human play; the production heuristic bot keeps v33 because heuristic-A still cannot cash the sharper boundary (-$4/1000h grid at the bot level — the bot-DS optimizer is the rate-limiting step).

**Fires on:** 5.46% of all hands (~1 in 18 you're dealt). Pure trips covers all 13 trip ranks; the headline gain over v14 is concentrated on low trips (2-9) where the third-trip-to-bot bleed is largest.

**Subsumes Rule 4 (extended):** the prior KKK/AAA rule was a special case. KKK with no Ace → third K on top (matches v35). KKK with Ace → A on top (matches v35). AAA → always third A on top (matches v35). Rule 6 generalizes cleanly to all 13 trip ranks.

---

## Rule 7 — Three pairs: top = singleton, then which pair joins the mid depends on your highest pair

**Fires whenever you have exactly three pairs (and one singleton kicker).** ~1.9% of hands (~1 in 53 you're dealt). The decision is mechanical — there are only 4 settings worth considering, and a single rank check picks the right one.

### The setup (always)

- **Top = your singleton** (the unpaired card). This keeps all three pairs intact.
- **Mid = one of the three pairs** (whichever the rule below says).
- **Bot = the other two pairs**, played as 2-pair Omaha.

### Step 1 — Which pair goes to the mid?

The rule depends only on your **highest pair's rank**:

| Highest pair | Mid is… | Bot is… |
|---|---|---|
| **AA** is highest | the **AA** (high pair) | the other two pairs |
| **KK / QQ / JJ / TT** is highest | the **MIDDLE pair** | the high pair + the lowest pair |
| **99 or lower** is highest | the **highest pair** | the other two pairs |

That's it. One condition: **is your highest pair K, Q, J, or T? → mid is the middle pair. Otherwise → mid is the highest pair.**

### Why it works

The trade is "where does the strongest pair go: mid (Hold'em) or bot (Omaha)?"

- **AA is special.** Pairing AA in the mid is so dominant in Hold'em (only chops vs another AA opponent, beats every other pair) that you don't move it.
- **A broadway non-Ace pair (K, Q, J, T) on the bot anchors a strong 2-pair Omaha hand** — when the board pairs, you draw to trips with the high pair instead of the middle pair, which scoops more often. You give up some mid Hold'em equity, but you gain more bot Omaha equity. Net positive: +$2,259/1000h within three_pair.
- **Below T (your highest pair is 99 or lower)**, your "high" pair isn't strong enough on the bot to outpace what an opponent might hit on the board. Better to keep it in the mid, where pair-vs-pair Hold'em still wins more often than not.

### Worked examples

**Example 1 — AAA highest, RA:** `A♥ A♦ K♥ K♣ Q♦ Q♣ 2♠`
- Three pairs: AA, KK, QQ. Singleton: 2♠.
- Highest pair = AA → **mid = AA**. Bot = KK + QQ.
- **Play**: top=2♠, mid=A♥+A♦, bot=K♥+K♣+Q♦+Q♣.

**Example 2 — KK highest, RB (mid = middle pair):** `K♥ K♦ Q♥ Q♣ 5♦ 5♣ 2♠`
- Three pairs: KK, QQ, 55. Singleton: 2♠.
- Highest pair = KK → **mid = the MIDDLE pair (QQ)**. Bot = KK + 55.
- **Play**: top=2♠, mid=Q♥+Q♣, bot=K♥+K♦+5♦+5♣. The KK on bot is a strong trips draw if the board pairs anything.

**Example 3 — QQ highest, RB:** `Q♥ Q♦ J♥ J♣ 7♦ 7♣ 2♠`
- Three pairs: QQ, JJ, 77. Singleton: 2♠.
- Highest pair = QQ → **mid = JJ**. Bot = QQ + 77.
- **Play**: top=2♠, mid=J♥+J♣, bot=Q♥+Q♦+7♦+7♣.

**Example 4 — JJ highest, RB:** `J♥ J♦ T♥ T♣ 6♦ 6♣ 2♠`
- Three pairs: JJ, TT, 66. Singleton: 2♠.
- Highest pair = JJ → **mid = TT**. Bot = JJ + 66.
- **Play**: top=2♠, mid=T♥+T♣, bot=J♥+J♦+6♦+6♣.

**Example 5 — TT highest, RB:** `T♥ T♦ 9♥ 9♣ 5♦ 5♣ 2♠`
- Three pairs: TT, 99, 55. Singleton: 2♠.
- Highest pair = TT → **mid = 99**. Bot = TT + 55.
- **Play**: top=2♠, mid=9♥+9♣, bot=T♥+T♦+5♦+5♣. Even at TT (the lowest broadway pair), bot anchoring still wins.

**Example 6 — 99 highest, RA (boundary flips):** `9♥ 9♦ 5♥ 5♣ 3♦ 3♣ 2♠`
- Three pairs: 99, 55, 33. Singleton: 2♠.
- Highest pair = 99 → **mid = 99**. Bot = 55 + 33.
- **Play**: top=2♠, mid=9♥+9♦, bot=5♥+5♣+3♦+3♣. At 99, the high pair is no longer strong enough to anchor the bot — keep it in the mid for the Hold'em equity.

**Example 7 — 44 highest (lowest possible):** `4♥ 4♦ 3♥ 3♣ 2♦ 2♣ Q♠`
- Three pairs: 44, 33, 22. Singleton: Q♠.
- Highest pair = 44 → **mid = 44**. Bot = 33 + 22.
- **Play**: top=Q♠, mid=4♥+4♦, bot=3♥+3♣+2♦+2♣. Weak hand all around, but the Q on top scoops the top tier most of the time, and 44 mid is at least a real pair.

### Probe history

- **v33 (production before this ship)** picks top=singleton on 80.4% of three_pair hands (the right idea was already there) but picks the WRONG pair for mid most of the time: it puts the highest pair in mid 68% of the time, which is RA-aligned but actually the wrong default. The middle pair (RB) is the better default.
- **`verify_rule_X_v33_three_pair.py` (Session 41)** — full 114K three_pair population; tested 4 always-X candidates (RA, RB, RC, RD). RA: +$18.36/1000h whole-grid. RB: +$24.94. RC, RD: regress.
- **`probe_three_pair_boundary.py` (Session 41)** — full 286-cell (high, mid, low) breakdown. Boundary "RB if high ∈ {T,J,Q,K} else RA" lifts +$43.05/1000h whole-grid (60% of the +$71.18 per-cell oracle ceiling).
- **`grade_v37_rule7.py` (Session 41)** — full-grid head-to-head: v33 = $2,920/1000h (40.68% optimal); v37 = $2,920 − Δ (40.68% + Δpct optimal). Three_pair within-cat regret drops by 67%, pct_optimal jumps from 38.9% → 64.9%.

**Fires on:** 1.9% of all hands (~1 in 53). Lift over v33: **+$43/1000h whole-grid** (38% the size of Rule 6's +$112 lift, but on a smaller population).

### What this leaves on the table

The +$43 captures 60% of the per-cell oracle ceiling. The remaining ~$28/1000h is in:
- K-high cells with low low-pair (≤6) where some prefer RB despite being in the "RA" bucket — small carve-out
- Edge cells with very small RA-vs-RB differences (sample noise)
- Multi-feature signal (suits, singleton rank, interactions) — ML territory

A 2-condition rule was tested ("RB if high ∈ {T,J,Q,K} OR (high=A AND low ≤ 3)") and only adds $0.01/1000h. The simple 1-condition rule is at the natural simplicity plateau.

---

## Rule 8 — Composite quads_pair: put 2 of the 4 quads in mid (the non-pair-suit pair)

**Fires whenever you have a quad PLUS a pair (the rare 4+2+1 hand type).** ~0.057% of hands (~1 in 1,750 you're dealt). When it fires, it scoops up a tier-Bot DS configuration that v33 was leaving on the table.

### The setup (always)

- **Top = the singleton card** (the one card that's neither part of the quad nor part of the pair).
- **Mid = the 2 quad cards whose SUITS are NOT the pair's suits.**
- **Bot = the other 2 quad cards + both pair cards** (4 cards total, automatically double-suited).

### Why "non-pair-suit quads to mid"?

The structural insight: the 4 quad cards have all 4 suits (one each), and the 2 pair cards have 2 different suits. The pair's two suits are a subset of the quad's four suits. If you put the QUAD CARDS THAT MATCH THE PAIR'S SUITS into the bot (alongside the pair), you get a bot of "2 of suit X + 2 of suit Y" — a perfect double-suited Omaha hand. The remaining 2 quads (at the OTHER 2 suits) go to the mid.

The mid is a paired hand (2 of the quad rank). The bot is a double-suited 2-pair Omaha (the quad rank + the pair rank, perfectly suited). The top is the singleton.

### Worked examples

**Example 1 — AAAA + KK + 2:** `A♣ A♦ A♥ A♠ K♣ K♦ 2♠`
- Quads = AAAA, pair = KK, singleton = 2♠.
- Pair's suits: {♣, ♦}. Non-pair-suits: {♥, ♠}.
- **Play**: top = 2♠, mid = A♥ + A♠, bot = A♣ + A♦ + K♣ + K♦.
  Bot is "2 clubs + 2 diamonds" — perfectly double-suited.

**Example 2 — 9999 + 55 + 7:** `9♣ 9♦ 9♥ 9♠ 5♣ 5♦ 7♠`
- Quads = 9999, pair = 55, singleton = 7♠.
- Pair's suits: {♣, ♦}. Non-pair-suits: {♥, ♠}.
- **Play**: top = 7♠, mid = 9♥ + 9♠, bot = 9♣ + 9♦ + 5♣ + 5♦.

**Example 3 — 2222 + 77 + Q:** `2♣ 2♦ 2♥ 2♠ 7♥ 7♠ Q♣`
- Quads = 2222, pair = 77, singleton = Q♣.
- Pair's suits: {♥, ♠}. Non-pair-suits: {♣, ♦}.
- **Play**: top = Q♣, mid = 2♣ + 2♦, bot = 2♥ + 2♠ + 7♥ + 7♠.

### Why it works

- v33 (and v8_hybrid before it) was picking arbitrary suit configurations for these hands. The rule guarantees the bot is double-suited — a $1.13 EV/hand difference at the top end of the suit-choice spread.
- The mid as a pair-of-quad-rank is a strong Hold'em hand (better than mid = 2 mismatched cards), and the bot as a double-suited 2-pair Omaha gets two flush draws AND the made 2-pair.
- The unrestricted oracle's pick for these hands is sometimes a different shape entirely (e.g., quads-on-bot via splitting the pair), but the deterministic rule captures 100% of the WITHIN-quad-in-mid oracle and the residual gap to the unrestricted oracle is small.

### Probe history

- **`verify_rule_X_v33_composite.py` (Session 42)** — full 14,742 composite population walked. Per subtype: quads_pair 6,863 hands; other subtypes (quads_trip, two_trips, trips_two_pair) reported large oracle-ceiling lifts but their heuristic capture is still TBD.
- **Verification script** confirmed that the deterministic "non-pair-suit quads to mid" pick achieves regret = $604.9/1000h within-st = exactly the oracle-within-constraint regret. 100% heuristic capture.
- **`grade_v38_rule8.py` (Session 42)** — full grid: $2,877 → $2,868/1000h ($\Delta$ +$9/1000h). Prefix grid: $1,753 → $1,735 ($\Delta$ +$19/1000h). Both grids positive — first session where the both-grid-validation gate was a tight binding constraint and the rule passed.

**Fires on:** ~0.057% of all hands (~1 in 1,750). Lift over v37: **+$9.42/1000h whole-grid** (small in absolute terms because the population is tiny, but the within-subtype regret reduction is dramatic — composite quads_pair within-st drops from $17,101/1000h to $605/1000h).

---

## Rule 9 — Three sub-rules for the rare composite shapes (plain quads, TT, T2P)

**Fires across three uncommon-but-tractable hand shapes** that share the same structural family of "multiple same-rank cards make the suit-aware mid pick the right move":

### Rule 9a — Plain quads (4+1+1+1, ~0.24% of hands, ~1 in 420)

**Setup**: 1 quad + 3 singletons, no pair.

- **Top** = your highest singleton.
- **Mid** = the 2 quad cards whose **suits are NOT used by any of the 3 singletons.**
- **Bot** = the other 2 quad cards + the 2 lower singletons.

**Why it works**: with all 4 suits represented in the quad, picking the 2 quads at "non-singleton-suits" forces the bot to be perfectly double-suited. The bot Omaha hand has 2 quads (matching 2 of the 3 singleton-suits) + 2 lower singletons → 2-of-X + 2-of-Y suit pattern.

**Worked example:** `9♣ 9♦ 9♥ 9♠ A♣ K♥ 7♠`
- Quad = 9999. Singletons = A♣, K♥, 7♠. Singleton-suits = {♣, ♥, ♠}. Non-singleton-suit = {♦}.
- Hmm — only 1 non-singleton-suit means we can't pick 2 quads at non-sing-suits. Fall back: pick canonical first 2 quads (or whichever combo gives DS). In this fallback case, the rule degrades to pick-the-canonical, but the heuristic is rare to fully fail (most plain quad hands have ≤2 distinct singleton-suits).

**Worked example (typical):** `9♣ 9♦ 9♥ 9♠ A♣ K♣ 7♥`
- Quad = 9999. Singletons = A♣, K♣, 7♥. Singleton-suits = {♣, ♥}. Non-singleton-suits = {♦, ♠}.
- Mid = 9♦ + 9♠ (non-singleton-suits).
- Top = A♣ (highest singleton).
- Bot = 9♣ + 9♥ + K♣ + 7♥. Bot has 2 clubs + 2 hearts = double-suited.

**Lift over v38**: +$15.31/1000h whole-grid (full N=200) + +$11.78/1000h whole-prefix. Wins on ALL 13 quad-rank cells. Within-cat regret drops $9,670 → $3,235/1000h on full (66% reduction). pct_optimal jumps 9.5% → 45.9%.

### Rule 9b — Two trips (3+3+1, ~0.07% of hands, ~1 in 1,400)

**Setup**: 2 trips (different ranks) + 1 singleton.

- **Top** = a HIGH-trip card whose suit IS in the LOW-trip's suits (split the high trip to top).
- **Mid** = the FULL LOW-trip pair (2 of 3 low-trip cards).
- **Bot** = 2 high-trip cards + 1 low-trip card + the singleton (4 cards). Pick the L-bot card whose suit best maximizes bot DS (matches a remaining-H-suit + singleton's suit).

**Why it works**: splitting the high trip to top + keeping the low-trip-pair in mid + putting 2 high-trip cards on the bot creates an Omaha bot with strong pair-on-board potential AND a clean DS path through the suit-aware L-bot pick. The "top H-suit ∈ L-suits" heuristic ensures the leftover H-suits in the bot don't clash with the L-trip-card.

**Worked example:** `T♣ T♦ T♥ 5♣ 5♦ 5♥ K♠`
- High trip = TTT, low trip = 555, singleton = K♠.
- L-suits = {♣, ♦, ♥}.
- Top: pick a T-card at suit ∈ {♣, ♦, ♥}. T♣ (or T♦, T♥) all qualify; pick the canonical first → T♣.
- Mid = 5♦ + 5♥ (or some pair-of-5; the rule's 2 of 3 picked by suit-aware L-bot routing).
- L-bot: maximize DS-bot score given the remaining bot will be {T♦, T♥} + 1 of {5♣, 5♦, 5♥} + K♠. The 5♣ joining bot would give bot suits {♦, ♥, ♣, ♠} = rainbow. Better to put 5♦ or 5♥ in bot → bot has 2 of one suit. The DS-aware tiebreaker picks 5♣ for L-bot (matches a remaining-H-suit if it's ♦ or ♥? Actually ♣ doesn't match, so 5♣ scores 0; 5♦ scores 1 (matches T♦); 5♥ scores 1 (matches T♥)). Pick 5♦ or 5♥ → bot = {T♦, T♥, 5♦, K♠} = ♦×2, ♥×1, ♠×1 → SS bot. Best achievable.

**Lift over v38**: +$3.57/1000h whole-grid (full) + +$2.79/1000h whole-prefix. 60% of the +$5.98 oracle ceiling.

### Rule 9c — Trips + two pairs (3+2+2, ~0.11% of hands, ~1 in 875)

**Setup**: 1 trip + 2 pairs (no singleton). 7 cards = 3+2+2.

- **Top** = a trip-member at the suit NOT shared with either pair (suit-aware split).
- **If trip-rank ≤ 4**: mid = LOW pair, bot = 2 trip-leftovers + HIGH pair (4 cards = trips-on-bot via 2T + HIGH-pair-on-board via 2H).
- **Else (trip-rank ≥ 5)**: mid = HIGH pair, bot = 2 trip-leftovers + LOW pair.

**Why it works**: the bot is always "trip-on-board" via 2 trip-leftovers. The choice is which pair joins the bot. When the trip is very weak (≤4), the trip-on-board anchor is barely useful (low-rank trips lose to most Omaha completions); putting the HIGH pair on the bot creates a stronger 2-pair Omaha. When the trip is 5+, mid Hold'em strength of HH outweighs that bot benefit.

**Worked examples:**

`T♣ T♦ T♥ Q♣ Q♦ 8♥ 8♠` (trip=T, hi-pair=Q, lo-pair=8). T ≥ 5 → F2: mid = QQ, bot = 2T + 88. Top = T-member at suit ∉ {♣, ♦, ♥, ♠} — ♥ is shared with 8♥, ♠ with 8♠, ♣ and ♦ are pair-suits. No clean non-pair-suit. Fallback: top = T♣ (canonical first). **Play: top=T♣, mid=Q♣+Q♦, bot=T♦+T♥+8♥+8♠.**

`3♣ 3♦ 3♥ K♣ K♦ Q♥ Q♠` (trip=3, hi-pair=K, lo-pair=Q). T ≤ 4 → F3: mid = QQ (low pair), bot = 2 of trip + KK. Top = 3-member; non-pair-suits would be {♠} (since ♣, ♦, ♥ are all used by pairs/trip). Top = 3♥ (matching one of the L-pair's suits is OK as fallback). **Play: top=3♥, mid=Q♥+Q♠, bot=3♣+3♦+K♣+K♦.**

**Lift over v38**: +$2.81/1000h whole-grid (full) + +$13.48/1000h whole-prefix. The boundary at trip=4 was confirmed via 23-rule sweep as the cleanest split (vs T<=5: +$2.88/+$13.05; T<=6: +$2.93/+$12.65 — diminishing returns past T<=4).

---

## Rule 10 — J-low single-pair defensive (the FIRST defensive rule)

**Setup**: 1 pair (no trips, no quads, no second pair). Max card on the hand is **J or lower** (the "weak-hand defensive zone"). 342,720 hands total at this max-J zone — 5.7% of canonical.

**Gate** (production v40b): the rule fires only when ONE of these is true:
1. **Pair rank ≤ 6** (low pair: 22 / 33 / 44 / 55 / 66), OR
2. **Pair rank EQUALS max rank** (e.g., JJ on J-high body, TT on T-high body — the pair IS the highest card in the hand).

The gate excludes the "pair is high but not the max" zone (e.g., 99 on J-high, TT on J-high) where the per-cell drill data showed the rule regresses by $2-$8/cell.

**Setting (when fired):**
- **Top** = your **LOWEST** singleton. (Yes, lowest. This inverts the conventional top=highest reflex.)
- **Mid** = the pair (paired Hold'em mid).
- **Bot** = the 4 HIGHEST non-pair singletons.

**Simple variant (v40, retained as sister artifact for human-memorization fork):** same setting but with NO gate condition (fires on every J-low pair hand). Smaller lift (+$23 full vs the gated v40b's +$48), but only ONE condition to memorize ("max ≤ J AND pair"). Use when the pair-rank gate is too much cognitive load mid-game.

**Why it works**: When even your highest card cannot reliably win the top tier (any J-or-lower hand vs random opponent), the conventional "top=highest" play gives away kicker strength to the bot for 1 point per board of marginal top equity. By dumping the lowest singleton to top, you accept guaranteed top-tier loss but stack the strong cards into mid + bot — where they earn 2-3 points per board.

The math:
- Top tier: 1 point per board, max 2 across both boards.
- Mid: 2 per board, max 4.
- Bot: 3 per board, max 6.

When TOP equity is already <50% (any J-low hand), the opportunity cost of dumping the highest card to top is <1 point. The gain in bot+mid equity from upgrading the bot's 4-card Omaha kicker strength is >1 point (the bot's two-pair / pair-on-board / kicker chain matters a lot in Omaha).

The pair stays in mid because the pair is the structural anchor — even a weak pair like 33 wins ~30% of mid Hold'ems against a random hand; moving it to bot would weaken both tiers. Oracle confirms this: 60-85% of J-low pair cells have oracle's pick keeping mid=pair.

**Worked example 1 (J-high pair=5):**
`J♥ 9♣ 7♣ 5♦ 5♣ 3♥ 2♠`
- Pair = 55. Singletons (rank desc): J, 9, 7, 3, 2.
- Top = 2♠ (lowest).
- Mid = 5♦ + 5♣.
- Bot = J♥ + 9♣ + 7♣ + 3♥ (the 4 highest non-pair singletons).

The bot now has J-9-7-3 with 2 clubs (9♣ + 7♣) → SS bot. The mid is the 5-pair. Top = 2♠ — concedes the top tier (we'd lose to most random opponents anyway), but the bot's J-high Omaha is much stronger than v3's default bot of "5-3-2 plus a low kicker".

**Worked example 2 (T-high pair=2):**
`T♣ 8♦ 6♥ 5♣ 2♦ 2♠ 4♣`
- Pair = 22. Singletons (rank desc): T, 8, 6, 5, 4.
- Top = 4♣ (lowest).
- Mid = 2♦ + 2♠.
- Bot = T♣ + 8♦ + 6♥ + 5♣ (the 4 highest).

Bot is rainbow (one of each suit) — not great for Omaha flush draws, but the kicker strength is real (T-8-6-5 vs the v3 default of "T plus 2-pair + low kickers"). Top = 4♣ concedes 1 point per board.

**Worked example 3 (J-high pair=J — pair == max):**
`J♥ J♣ 9♦ 7♠ 5♣ 3♥ 2♦`
- Pair = JJ. Singletons (rank desc): 9, 7, 5, 3, 2.
- Top = 2♦ (lowest).
- Mid = J♥ + J♣ (paired-J mid is a STRONG Hold'em mid).
- Bot = 9♦ + 7♠ + 5♣ + 3♥.

Bot is rainbow + low kickers. The JJ in mid is the value driver here; top = 2 sacrificed because no high singleton beats JJ-as-mid in this body.

**When this rule does NOT fire:**
- Max card ≥ Q (Q-high, K-high, A-high pair hands): keep top=highest-singleton (oracle still picks top=hi 48%-96% on these).
- Two-pair, trips, three-pair, quads, trips-pair, no-pair: different categories, different rules.
- Hands where Rule 1 fires (single pair + Ace + balanced kickers + DS feasibility): Rule 1 takes precedence (but Rule 1 requires an Ace, which J-low pair can never have, so they don't actually conflict).

**Lift over v39 (gated v40b — production, grader-confirmed both grids):** **+$48/1000h whole-grid (full N=200) + +$37/1000h whole-grid (prefix N=1000)**. pct_opt full: 41.17% → 41.48% (+0.31%). v39 → v40b score: $2,846 → $2,798 full, $1,707 → $1,670 prefix.

**Lift of the simple v40 variant (no gate, sister artifact):** +$23/1000h full + +$37/1000h prefix. The simple variant fires on the localized regression cells (pair_rank ∈ (max-4, max-1)) where the rule loses; the gate avoids those cells. The gate's "pair == max" branch captures the JJ / TT / 99 / etc. cells where the pair IS the max rank (and oracle-favored top=lo even there).

**Why the gate works:** the per-cell drill (drill_low_pair_J_high_defense.py) showed that the structural-inversion mechanism breaks down in the narrow zone where the pair is high enough to anchor a strong mid (against random opponents) but not the max card. Examples: J-high pair=9 (Jh_p9, regresses −$5.76/cell), T-high pair=8 (Th_p8, −$1.33/cell). In those zones, the conventional top=highest still wins because the J/T high card has marginal but real top-tier equity AND the pair (9/8) gets value from BOT in the alternative configuration. The gate avoids precisely these cells.

**Mechanism connection (why this generalizes)**: The "weak-hand top inversion" is the mechanism. It applies most cleanly to the pair category (where Rule 10 captures it), partially to no-pair hands (where T-low has signal but J-high is multi-feature; Q5 deferred), and not at all to the two_pair category (Q4 confirmed all defensive variants regress; v33's adaptive splitting is genuine multi-feature ML routing, not a hidden defensive rule).

---

## Default (no rule fires)

For every hand not covered above — single pair outside the rule's gates, no-pair hands, plain quads (no second pair), and the rare composite shapes other than quads_pair — **play it the obvious way:**

- **Top** = your highest singleton card (especially an Ace if you have one)
- **Mid** = your strongest 2-card Hold'em combination from what's left (pair > broadway > suited connector)
- **Bot** = whatever's left, ideally with at least 2 of one suit for some Omaha equity

This is the v8_hybrid play. It's not optimal on every hand but it's adequate. The v34 ML champion captures meaningful additional EV here (especially on high_only, pair, two_pair, trips_pair, and the remaining composite subtypes), but no clean human-memorizable rule has been extracted for these categories yet.

Sessions 41–42 mapped the residual landscape for the rule-mining program:
- **high_only**: confirmed ML-only (Session 41). The X3 oracle ceiling of +$355/1000h whole-grid is unreachable by any single-feature heuristic.
- **two_pair**: a clean +$197/1000h boundary rule was found on the full grid in Session 42 but DEFERRED after a -$512/1000h prefix regression. v33's underlying logic adaptively splits pairs on weak hands and any forced-no-split rule loses there. ML territory unless a split-allowing variant is found.
- **composite**: heterogeneous (4 subtypes). quads_pair shipped in Session 42 (+$9.42/1000h via Rule 8). The other 3 subtypes (quads_trip, two_trips, trips_two_pair) have promising oracle-ceilings (+$7-8 each) but need heuristic-refinement drills before shipping.

---

## The common thread

The single insight running through all 4 rules:

> **The bottom tier is the most valuable, and double-suited (2+2) bots win against the realistic mixture by $5K-$15K per 1,000 hands.** Whenever a pair (or trip) can serve as a suit anchor for the bot — meaning the pair has two different suits, and your kickers can fill the DS structure — putting the pair in the bot is usually correct. The exceptions are mid pairs (6-9), which are strong enough in mid that the move isn't worth it, and KK/AA, which are valuable enough in mid that the trade flips back.

The mid tier is forgiving (Hold'em rules, can use 0/1/2 hole cards), so giving up a "pair in mid" for kickers in mid loses less than you'd think. The bot is unforgiving (Omaha 2+3 is rigid), so getting the bot to DS shape is high-value.

---

## One-paragraph cheat sheet

> Don't break pairs. With one pair + an Ace + balanced suits, put the
> Ace on top and the pair in a double-suited bot — except for pairs 6-9
> which stay in mid AND for KK / AA which always stay in mid. With two
> pairs, never split either; either both go to bot, or higher to mid +
> lower to bot, whichever makes the bot double-suited. With trips +
> pair, split the trips 2-and-1, keep the pair together, build a
> double-suited bot. With three pairs, top is the singleton; mid is the
> middle pair if your highest pair is T/J/Q/K, otherwise mid is the
> highest pair. With a quad PLUS a pair (4+2+1), top is the singleton;
> mid is the two quad cards at the suits that DON'T match the pair
> (this guarantees a double-suited bot). With plain quads + 3
> singletons, same idea: top is the highest singleton, mid is the two
> quad cards at the suits NOT used by the singletons. With two trips +
> a singleton, split the high trip to top (pick a high-trip card whose
> suit appears in the low trip), mid is the full low-trip pair, bot
> gets two high-trip cards plus one low-trip card chosen for DS bot.
> With one trip + two pairs, split the trip to top; if the trip is
> rank 4 or lower, mid is the LOW pair (high pair to bot for stronger
> Omaha anchor), otherwise mid is the HIGH pair (low pair to bot).
> **DEFENSIVE — when your max card is J-or-lower AND you have one pair
> (no trip / no second pair / no quad), AND the pair is rank-6-or-
> lower OR the pair IS your max card, INVERT the conventional top:
> top is the LOWEST singleton, mid is the pair, bot is the 4 highest
> non-pair singletons.** The mid-pair stays as the structural anchor;
> the top is sacrificed because a J-or-lower top is going to lose to
> most opponents anyway, and the strong cards earn more points in
> mid+bot than top. (For the simpler ungated variant — fire whenever
> max ≤ J and you have a pair — see v40_rule10.py; smaller lift but
> only one condition.) For any hand without a pair, play it the obvious
> way — high card on top, decent cards in mid.
