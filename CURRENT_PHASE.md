# Current: Sprint 7 Phase A complete — feature table built, first encoded rule chain measured at 53.58% shape-agreement vs multiway-robust on 6M hands

> Updated: 2026-04-26 (end of Session 12)
> Previous sprint status: Session 11 finished cloud production (4 .bin files local, pod terminated), shipped first multiway hypothesis test (200K-sample). Session 12 unblocked Sprint 7 properly: built the hand-feature extractor + Parquet pipeline (priorities 1 from the resume prompt), did pattern probing (priorities 2), encoded rules as strategy functions and measured GTO-distance baseline. Pulled in the user's home-game **buyout option** as a new strategic dimension.

---

## What was completed this session (Session 12)

### Infrastructure (Sprint 7 P1)
- `analysis/src/tw_analysis/features.py` — scalar reference + numpy-vectorized batch extractor for hand-level (n_pairs, pair_ranks, top/2nd/3rd rank, suit profile, connectivity, n_broadway, n_low, category) and per-tier (top_rank, mid_is_pair/suited, bot_suit_max/DS/n_pairs/connectivity/...) features. Multiway-robust mode resolver. Scalar/batch parity gate (Decision 028 discipline).
- `analysis/scripts/test_features.py` — 24 tests, all green.
- `analysis/scripts/build_feature_table.py` — streams 6,009,159 canonical hands × 4 BR files → `data/feature_table.parquet` (208 MB, 51 cols). Includes hand features + per-profile BR settings + multiway-robust + agreement_class + per-profile EVs (added mid-session) + ev_mean / ev_min / ev_max derived. Agreement-class breakdown matches the 200K-sample numbers from Session 11 exactly (26.68% / 40.48% / 20.64% / 9.48% / 2.71%) — sample was representative.
- Updated `tw_analysis/__init__.py` to export feature module.

### Pattern mining (Sprint 7 P2)
- `analysis/scripts/probe_rules.py` — quick rule-by-rule applicability + agreement on 6M.
- `analysis/scripts/mine_patterns.py` — comprehensive 9-section miner: trips placement, full-house quadrant analysis, quads, three-pair, big-pair-to-bot, top-card cutoff, suits-vs-connectivity, garbage hands, **buyout +EV per profile + signature**.

### Rule encoding + GTO-baseline measurement
- `analysis/scripts/encode_rules.py` — encodes 7 candidate placement rules as `apply_rules(hand) → setting_index`. Three strategies: NAIVE_104, SIMPLE, REFINED. Scores literal + **shape** agreement (shape ignores suit-position tie-breaks — the measure that actually reflects rule correctness).

### Headlines

**Strong rules surfaced from mining (>90% agreement on relevant subsets):**
- 9+ pair → middle: 93.5% agreement (J-pair 94.6%, A-pair 99.65%)
- Pure trips → middle: 93.8% (low trips 81%, high trips 99%)
- Three-pair → highest pair to mid: 75.4% (mid is **always** a pair, 0% miss)
- Quads → split 2 mid + 2 bot: 80–95% by rank, dips at quad-A (73.6%)
- Top = highest UNPAIRED rank: 82.7% when applicable; 1.6% when highest IS paired (pair-preservation crushes the rule)
- Mid-locked-as-pair + DS-bot feasible: DS wins 1.8x over connectivity

**Buyout (NEW strategic layer added this session):**
- ev_mean across 4 profiles < −4 in only **0.09%** of hands (~5,600 of 6M).
- Per-profile rates: vs MFSA 0.37%, vs TopDef 0.37%, vs OmahaFirst 0.01% (never), vs RandomWeighted 0.05%.
- **Anti-intuitive signature:** NOT garbage hands. It's hands with HARMFUL pair structure: quads of 2-7 (lift 117x), pure low trips (8x), trips+low-pair (6.6x). Garbage hands average -0.98 EV — bad but not catastrophic.
- Total selective-buyout edge in 4-handed: ~0.56 points per 100 hands.

**First encoded rule chain baseline (`encode_rules.py` SIMPLE/REFINED, all 6M hands):**
| metric | NAIVE_104 | SIMPLE = REFINED |
|---|---|---|
| **Overall shape-agreement** | 21.77% | **53.58%** |
| Unanimous slice (26.7%) | 30.13% | 82.93% |
| Quads | 23.14% | 79.20% |
| Three-pair | 17.90% | 72.88% |
| Pair | 19.09% | 65.02% |
| **High-only (no pair)** | 19.50% | **19.50%** ← biggest gap |

The 7-rule chain is **2.5x better than naive** but leaves a real gap. The rule chain currently falls back to NAIVE_104 for `high_only` hands, which is wrong 80% of the time — that's where Phase B should start.

### Gemini 2.5 Pro Socratic dialogue (continuation_id ec08b754-69f3-479d-bb5a-c15fee965876)
- Pushback: "encode-then-measure" risks rediscovering the need for feasibility flags + category fixes. Strongest argument: section-5 mining showed high-pair-to-bot correlates with `bot_is_double_suited` 62% — encoding without the flag would be incomplete.
- Synthesis: hybrid Phase A — derive feasibility from existing columns (`can_make_ds_bot ≡ suit_2nd ≥ 2`, `can_make_4run_bot ≡ connectivity ≥ 4`) instead of extending features.py; encode multiple competing rule strategies; let the gap measurement tell us whether refinement helps.
- Result confirmed Gemini was partially right: SIMPLE = REFINED at 53.58% because REFINED doesn't yet add anything beyond SIMPLE. Phase B needs ACTUAL conditional refinement, not just renamed strategies.

---

## Files touched this session

**Added:**
- `analysis/src/tw_analysis/features.py`
- `analysis/scripts/test_features.py`
- `analysis/scripts/build_feature_table.py`
- `analysis/scripts/probe_rules.py`
- `analysis/scripts/mine_patterns.py`
- `analysis/scripts/encode_rules.py`
- `data/feature_table.parquet` (208 MB, gitignored)
- `data/mine_patterns_session12.txt` (9 KB session output for posterity)

**Modified:**
- `analysis/src/tw_analysis/__init__.py` — exports for features module
- `CURRENT_PHASE.md` — this file (rewritten)

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md` (Session 12 entry appended)

---

## Resume Prompt (next session — Sprint 7 Phase B)

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- DECISIONS_LOG.md  (latest is Decision 030)
- handoff/MASTER_HANDOFF_01.md  (scan Session 12)
- analysis/src/tw_analysis/features.py  (the feature extractor)
- analysis/scripts/encode_rules.py  (the encoded rule chain)
- data/mine_patterns_session12.txt  (Session 12 mining output)

State of the project:
- All 4 production .bin files at data/best_response_cloud/. Pod terminated.
- data/feature_table.parquet built (6,009,159 hands × 51 cols). EV columns
  included (per-profile + ev_mean/min/max).
- 7-rule chain encoded as encode_rules.py strategies SIMPLE / REFINED.
  Both produce identical output: 53.58% shape-agreement vs multiway-robust
  on 6M hands. NAIVE_104 baseline is 21.77%. So the rules are 2.5x better
  than naive — but 46% of hands still mismatch.
- Use SHAPE agreement, NOT literal. Literal scores include suit-tie-break
  artifacts and grossly under-report rule correctness.

Sprint 7 Phase B PRIORITIES IN ORDER:

1. **Close the high_only gap.** 35% of all rule misses are no-pair hands;
   miss rate is 80.5% within that category. The rule chain falls back to
   NAIVE_104 there, but multiway-robust isn't 104 for ~80% of high_only
   hands. Mine these specifically:
     - Run the same probing on the high_only subset only.
     - Look at top-card distribution, mid-card composition (do robust
       answers prefer suited/connected mid pairs?), bot-DS preference.
     - Hypothesize candidate rules; encode them; re-measure.
   Expected payoff: closing this fully would push the rule chain from
   53.58% to ~70%.

2. **Make REFINED actually refined.** Currently SIMPLE == REFINED. The
   conditionals to add (driven by mining):
     - "9+ pair → mid UNLESS trips present OR a higher pair exists" (this
       captures the 6.5% high-pair-to-bot cases as 19% trips + 29% higher pair).
     - "When mid locked as a high pair AND can_make_ds_bot, optimize bot
       for DS" (1.8x preference observed).
     - "trips_low + pair_high: pair displaces trips from mid 36.5% of the
       time" — encode as a tunable conditional and measure.

3. **Investigate the 17.1% miss rate on UNANIMOUS hands.** These are hands
   where ALL 4 profiles agree on the answer but my rule chain disagrees.
   Pure rule-logic failures, not opponent-dependent. ~273K hands. Likely
   reveals one or two missing rules.

4. **Buyout integration.** Add a buyout pre-step to the rule chain:
   "if ev_mean < -4 vs the actual opponent type, recommend buyout."
   Trainer surfaces a "BUYOUT" badge. Confirm signature: low quads,
   pure low trips, trips+low-pair (per project memory).

5. **(Lower priority) Self-play break-even Nash check** (Sprint 7 P3).
   Once the rule chain hits ~75-80% shape-agreement, encode it as both
   players in 100K self-play hands. Mean EV should be ≈ 0; deviation
   measures Nash distance.

DEFERRED (don't do unless rule mining is exhausted):
- Per-tier EV decomposition (engine matchup_breakdown exposure) — for
  trainer COACHING, not rule mining
- Naive-distance metric — diagnostic only
- Category bucketing fix (trips+trips, quads+pair) — affects <0.5% of
  hands, low leverage

PRIORITY FROM USER:
- 5-10 rules max. Compression non-negotiable.
- Brainstormed coverage: trips, trips+pair quadrants, quads, three-pair,
  big pair on bot, top-card cutoff, suits vs connectivity, garbage,
  buyout. ALL are now empirically measured (see mine_patterns_session12.txt).

Suggested starting point for next session: build a high_only-focused
miner, hypothesize 2-3 rules, encode, re-measure. Goal: rule chain to
≥70% shape-agreement.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
