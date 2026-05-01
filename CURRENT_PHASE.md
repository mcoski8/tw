# Current: Sprint 7 Phase E — str-sort bug fixed, v8_hybrid is the new champion at +$478/1000h vs v3. Session 22 closed.

> **🔥 IMMEDIATE NEXT ACTION (Session 23):** Mine pair-to-bot trigger conditions for low-pair (rank ≤ 5) hands. The 50K oracle-grid showed pair-to-bot is EV-correct 24-32% of the time for pair_rank ≤ 5, but neither v3 nor v7 captures this routing. Build v9 with explicit pair-to-bot rule. Estimated headroom: **+$50-150/1000h on top of v8_hybrid's +$478**.

> **🚫 RETIRED (Decision 033, Session 16):** "≥95% shape-agreement on multiway-robust target." Dollar metric is the headline.

> **🚫 NULL RESULT (Decision 040, Session 21):** path A.2 per-profile DT ensemble.

> **🚫 BUGFIX (Decision 041, Session 22):** trainer/src/engine.py used Python str-sort instead of byte-sort for 21 sessions. Setting_index space differed between strategy callables (byte-sort) and engine MC (str-sort) for ~94% of hands. Sessions 16-21 EV claims invalidated; all four strategies re-run post-fix. Buggy records archived as `*_buggy.parquet`.

> **✅ NEW CHAMPION (Decision 042, Session 22):** **v8_hybrid is the best deterministic strategy at +$478/1000h vs v3** with balanced gains across all 4 opponent profiles (every cell ≥ +$438/1000h).

> Updated: 2026-05-01 (end of Session 22)

---

## Headline state at end of Session 22

**v8_hybrid is production-ready.** Tournament results on 50K hands × 4 profiles, post-bugfix:

| Strategy | mfsuitaware | omaha | topdef | weighted | grand mean | $/1000h vs v3 |
|----------|-------------|-------|--------|----------|------------|----------------|
| v3 | +0.350 | +1.713 | +0.241 | +1.390 | +0.924 | 0 |
| v5_dt | +0.378 | +1.510 | +0.312 | +1.357 | +0.889 | −$344 |
| v6_ensemble | +0.379 | +1.497 | +0.313 | +1.361 | +0.887 | −$363 |
| v7_regression | +0.389 | +1.775 | +0.307 | +1.401 | +0.968 | +$445 |
| **v8_hybrid** | **+0.398** | **+1.757** | **+0.289** | **+1.442** | **+0.971** | **+$478** |
| oracle_argmax_mean (hedge ceil) | +0.498 | +1.849 | +0.415 | +1.500 | +1.066 | +$1,421 |
| oracle_BR_per_profile (cheats) | +0.538 | +2.124 | +0.503 | +1.546 | +1.178 | +$2,542 |

**Headlines:**
- **v7_regression is the FIRST learned strategy to beat v3 since the project began** (post-bugfix).
- **v8_hybrid extends v7's win by +$33/1000h** by falling back to v3 for the simple cases v3 already handled well (high_only + one_pair categories).
- v8_hybrid captures **34% of the profile-blind oracle ceiling** ($478 of $1,421) and **19% of the omniscient ceiling** ($478 of $2,542).
- Best opponent for ALL strategies: omaha. Worst: topdef. This is a property of the GAME, not the model.
- vs the realistic-strong opponent (mfsuitaware), v8_hybrid wins +$477/1000h vs v3.

### Session 21 → Session 22 deltas

- **str-sort bug (Decision 041):** discovered + fixed. v3 grand mean EV jumped from −0.068 (buggy) to +0.985 (correct). Apparent v3-to-BR-ceiling gap shrunk from $13,941/1000h to $2,542. The "v3 is a money-loser" narrative from Sessions 16-21 was largely an artifact.
- **v7_regression baseline (Decision 042 §A):** trained depth-15 multi-output regression DT on 50K-hand × 4-profile × 105-setting EV grid. 13,955 leaves. First learned strategy to beat v3 (+$445/1000h, balanced gains across all 4 profiles).
- **v8_hybrid (Decision 042 §B):** v7 + v3 fallback for high_only and one_pair categories + AAKK exception. Best deterministic strategy as of 2026-05-01.
- **Pair-to-bot pattern (open headroom):** mining 50K grid showed oracle routes pair→bot for 32% of 22-hands, 24% of 33-55-hands, dropping rapidly above pair_rank=6. None of v3/v5/v6/v7 captures this. Estimated +$50-150/1000h for v9.
- **Tournament harness:** `tournament_50k.py` evaluates any new strategy across all 4 profiles in ~12 seconds (no new MC; uses pre-computed 50K grid). Future strategies can be A/B tested against the existing leaderboard.

---

## What was completed this session (Session 22)

### Step 1 — User pushback drove bug discovery

User's poker intuition on hand `Ks Qs 8h 8d 7d 5h Ac` ("v3 should put Ac on top with KsQs in mid, not 88 in mid") forced a trace of strategy_v3, which revealed v3 was already picking what the user wanted — but the EV evaluation pipeline was scoring a different setting. Root cause: `evaluate_hand_cached(tuple(sorted(hand_strs)))` used Python str-sort while strategies use byte-sort.

### Step 2 — Bugfix + re-run

Fixed `trainer/src/engine.py` line 222 to sort by `_card_byte()` (commit 39a4528). Killed the running v7 overnight chain. Restarted with re-baseline of v3/v5_dt/v6 + new v7 train + v7 baseline. Total chain runtime: ~4.4 hours (re-baselines 25 min, 50K MC 3.5h, train 4s, v7 baseline 8.4 min, comparison reports).

### Step 3 — v7 wins

Post-fix `v7_regression` (depth-15 multi-output DT trained to predict per-setting × per-profile EV from 37 features, then argmax over 105 at inference) scored +0.968 grand mean vs v3's +0.924 = **+$445/1000h**. First learned strategy to beat v3.

Per-profile gains: mfsuit +$384, omaha +$618, topdef +$665, weighted +$113. Win across all 4 profiles.

### Step 4 — v7 inspection + distillation

`inspect_v7_tree.py` revealed v7's structure:
- Root split: `n_broadway ≤ 2.5` (count of T-J-Q-K-A in hand). v7's first question is "how many high cards do you have?"
- Top features by usage: `suit_max` (10.7%), `connectivity` (9.1%), `second_rank` (8.6%), `third_rank` (8.5%), `suit_3rd` (8.2%) — ~36% of splits are about suit profile + connectivity (matches user's Session 22 critique that v3 underweights these).
- Coverage: v7 uses 78 of 105 settings. Top 6 cover 92% of leaves: settings 104 / 74 / 102 / 99 / 90 / 95 (plus rare specialty settings).
- 13,955 leaves at depth 15. Not memorable.

`distill_v7.py` (knowledge distillation) showed:
- Depth-3 distillation: 8 leaves, 45.6% v7-agreement.
- Depth-4: 16 leaves, 50.6% v7-agreement.
- Depth-5: 32 leaves, 56.6% v7-agreement.
- v7's behavior is NOT compressible into a memorable chain without losing significant accuracy.

### Step 5 — Where v7 wins, where v7 loses

`where_v7_beats_v3.py` (per-category × per-profile breakdown):

| Category | n share | $/1000h v7-vs-v3 | weighted contribution |
|----------|---------|------------------|----------------------|
| trips | 4.5% | +$3,575 | +$163 |
| two_pair | 20.9% | +$739 | +$155 |
| trips_pair | 1.9% | +$4,030 | +$79 |
| three_pair | 2.2% | +$1,470 | +$33 |
| **high_only** | **20.8%** | **−$203** | **−$42** |
| **pair** | **49.4%** | **−$50** | **−$24** |
| quads | 0.2% | +$7,372 | +$18 |

**v7's gain comes entirely from multi-pair routing.** v7 LOSES to v3 on high_only and one_pair (the most common categories). Reason: v3's hand-coded "search for top + DS-bot bonus + 4-run-bonus" preserves bot-Omaha equity that v7's tree can't reproduce on these simpler structures.

### Step 6 — v8_hybrid + AAKK patch

`strategy_v7_patched.py`: v7 + v3 hand-coded AAKK exception. AAKK is rare (~0.2%) so total impact at 50K scale is noise (−$4/1000h vs v7).

`strategy_v8_hybrid.py`: v7 + v3 fallback for high_only AND one_pair AND AAKK. Eliminates the −$42 + −$24 v7 was costing on those categories. Net result: **+$478/1000h vs v3** (vs v7's +$445), and much more balanced per-opponent profile.

### Step 7 — Pair-to-bot pattern mining (open headroom)

`mine_pair_to_bot_50k.py` over the 50K oracle grid:

| pair_rank | n one-pair hands | % oracle routes pair → BOT |
|-----------|------------------|----------------------------|
| 22 | 1,819 | **32.4%** |
| 33 | 1,791 | 24.0% |
| 44 | 1,878 | 24.5% |
| 55 | 1,849 | 24.1% |
| 66 | 1,787 | 16.1% |
| 77 | 1,729 | 8.6% |
| 88-AA | varies | < 5% |

Targeted probes confirmed the pattern empirically:
- `Jd Td 9c 4h 2c 2d 6s` (22 + JT9 connector + 64 junk):
  - v3 / v7 / v8: top=Jd, mid=22, bot=T-9-6-4 → mean EV −1.732
  - oracle: top=Jd, **mid=6-4 (junk)**, **bot=T-9-2-2** → mean EV **−1.395** (+$3,360 better)
- `Ah Kc Td 8s 5h 2c 2d` (22 + AK + T8 + 5):
  - v3 / v7 / v8: top=Ah, mid=22, bot=K-T-8-5 → mean EV +0.13
  - oracle: top=Ah, **mid=8-5 (junk)**, **bot=K-T-2-2** → +$4,124 better

The mid is "wasted" with junk but the bot becomes a pair-with-connectors that has high Omaha 2+3 equity. Neither v3 nor v7 captures this routing because both default to "pair → mid".

### Step 8 — High_only diagnostic

`probe_high_only_misses.py` showed: on the top-10 hands where v7 loses to v3 on high_only, v7 picks setting 104 (top=hi, mid=top-2, bot=lo-4) but v3 picks setting 99 (top=hi, mid=middle-2, bot=hi+lo mix). Setting 99 keeps the high cards in bot for Omaha equity — the routing v3's hand-coded "DS-bot bonus + run-bonus" preserves but v7's tree didn't reproduce. v8_hybrid fixes by falling back to v3 here.

### Step 9 — Tests + commit

- Rust: `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass.
- Commits:
  - `39a4528`: str-sort bugfix
  - `40f60b0`: Session 22 analytical work (11 new files, 1144 insertions)

---

## Files added this session

**Strategy callables (production-grade):**
- `analysis/scripts/strategy_v7_patched.py` — v7 + v3 AAKK exception
- `analysis/scripts/strategy_v8_hybrid.py` — **v8_hybrid champion**
- `data/v7_regression_model.npz` — frozen v7 tree

**Analysis & exploration:**
- `analysis/scripts/cheap_test_oracle_hedges.py` (Session 21, but persisted in Session 22 50K run)
- `analysis/scripts/tournament_50k.py` — fast leaderboard across all strategies × profiles
- `analysis/scripts/inspect_v7_tree.py` — v7 tree structure inspection
- `analysis/scripts/distill_v7.py` — shallow distillation experiments
- `analysis/scripts/where_v7_beats_v3.py` — per-category breakdown
- `analysis/scripts/mine_pair_to_bot_50k.py` — pair-rank-vs-pair-to-bot table
- `analysis/scripts/probe_high_only_misses.py` — high_only diagnostic
- `analysis/scripts/probe_low_pair_vs_connectors.py` — Q2B targeted MC

**Data:**
- `data/oracle_grid_50k.npz` (post-fix) — 50K hands × 4 profiles × 105 settings
- `data/v7_regression_records.parquet` — 2000-hand baseline
- `data/v3_evloss_records.parquet`, `data/v5_dt_records.parquet`, `data/v6_ensemble_records.parquet` — all re-run post-fix
- `data/cheap_test_oracle_grid_1000.npz` — 1000-hand verification at fix time

**Archived (buggy):**
- `data/v3_evloss_records_buggy.parquet`, `data/v5_dt_records_buggy.parquet`, `data/v6_ensemble_records_buggy.parquet`
- `data/cheap_test_oracle_grid_200_buggy.npz`, `data/cheap_test_oracle_grid_1000_buggy.npz`

## Files modified this session

- `trainer/src/engine.py` — str-sort BUGFIX (canonical sort by byte-value via `_card_byte()`)
- `analysis/scripts/v3_evloss_baseline.py` — registered v7_regression, v7_patched, v8_high_only_only, v8_hybrid in STRATEGIES dict
- `analysis/scripts/probe_user_hand.py` — extended to include v7
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — appended Decisions 041 + 042
- `handoff/MASTER_HANDOFF_01.md` — appended Session 22 entry

## Verified

- Rust: `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass.
- Tournament `tournament_50k.py`: deterministic, ~12 sec wall time. v8_hybrid +$478/1000h vs v3 reproducible.

## Gotchas + lessons

- **str-sort bug went unnoticed because the negative result reinforced the project's narrative.** When a counterintuitive negative result holds across multiple sessions (e.g., "newer ML strategy loses to hand-coded v3"), audit the EVAL PIPELINE before re-architecting. The 4-step doctrine should add this verification step.
- **Distillation of v7 isn't viable for memorable rules.** v7's behavior is structurally non-compressible — depth-5 distillation only captures 57% of v7's decisions. To get a human-memorable strategy, we'd have to accept significant lossy compression. Better path: extract the HIGH-IMPACT specific patterns v7 learned (multi-pair routings) and add them as new explicit rules to v3.
- **Hybrid > pure-learned model.** v8_hybrid wins by combining v7's strength (multi-pair routing) with v3's strength (high_only + one_pair). Pure ML is not the right answer here.
- **AAKK is a real exception, but rare (0.2% of hands).** v3's hand-coded rule ties the oracle. v7 missed it. Patch is correct but doesn't move the headline metric.
- **Oracle ceilings are smaller than the bug-era numbers suggested.** Real BR-omniscient gap above v3 is +$2,542/1000h (was reported as $13,941). Real argmax_mean ceiling is +$1,421 (was $12,816). Still meaningful, but not the "huge upside" the bug-era hedge ceiling implied.

---

## Resume Prompt (Session 23)

```
Resume Session 23 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 22)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decisions 041 + 042 — str-sort bugfix + v7/v8 results)
- handoff/MASTER_HANDOFF_01.md (Session 22 entry just added)
- analysis/scripts/strategy_v8_hybrid.py (current champion)
- analysis/scripts/strategy_v7_regression.py (the learned tree)
- analysis/scripts/tournament_50k.py (fast 50K-hand × 4-profile leaderboard)
- analysis/scripts/mine_pair_to_bot_50k.py (the pair-rank → pair-to-bot table)
- data/oracle_grid_50k.npz (50K-hand × 4-profile × 105-setting EV grid)
- data/v7_regression_model.npz (frozen v7 tree)

State of the project (end of Session 22):
- v8_hybrid is the best deterministic strategy at +$478/1000h vs v3.
  Per-opponent ($/1000h vs v3): mfsuit +$477, omaha +$438, topdef +$479,
  weighted +$518 (every opponent ≥ +$438 — well-balanced).
- v7_regression: +$445/1000h vs v3, slightly less balanced.
- Captures 34% of profile-blind oracle ceiling, 19% of omniscient ceiling.
- str-sort bug in trainer/src/engine.py fixed (commit 39a4528). Sessions
  16-21 EV claims invalidated; all strategies re-run post-fix.
- 124 Rust + 74 Python tests pass.

User priorities (re-confirmed Session 22):
- Discovery mode, not production commitment.
- Data drives discovery — let the leaves speak.
- Track $/1000h PER OPPONENT TYPE, not just grand mean (per Session 22 user
  feedback). Each opponent column matters; mfsuitaware is the most
  realistic-strong human profile.
- User's poker-domain critiques are accurate and drive the work — connectivity
  has multiple forms (consecutive, 1-gap, 2-gap), suit profile matters more
  than v3's chain captures, routing should be flexible (pair-to-bot,
  trips-to-bot, top-sacrifice are all real options v3 ignores).

IMMEDIATE NEXT ACTIONS (pick one):

(A) Mine pair-to-bot trigger conditions for low-pair hands.
    The 50K oracle grid showed pair_rank ≤ 5 routes pair→bot 24-32% of
    the time, but v3/v5/v6/v7 never do. Build the discriminator:
      1. From the 50K grid, slice hands with pair_rank ≤ 5 where oracle
         picks pair-to-bot (~3,200 hands).
      2. Compute features for each. Find the OR / decision rule that
         separates "oracle picks pair-to-bot" from "oracle picks pair-to-mid".
         Likely candidates: suit profile of the 4 non-pair cards
         (DS-able? 3-suited?), connectivity of the bot under each routing,
         broadway count, suited-mid-availability.
      3. Build v9 = v8_hybrid + explicit pair-to-bot rule for pair_rank ≤ 5.
      4. Tournament test: how much of the +$50-150/1000h headroom does v9 capture?

(B) Distill v7's HIGH-IMPACT paths into new explicit rules.
    Don't try to compress v7 wholesale (depth-5 distillation only 57%
    agreement). Instead: identify the leaves where v7 wins MOST against
    v3, extract the path constraints for those leaves, translate to plain
    English rules. Add 5-10 such rules to v3's chain to make a
    rule-augmented v9'.

(C) Multi-pair routing fine-tuning.
    v7 contributes +$163 from trips, +$155 from two_pair, +$79 from
    trips_pair. The oracle gap on these categories is much larger
    (estimated +$300-1000 headroom on multi-pair structures alone).
    Mining specifically: for trips_pair hands, what discriminates
    "trips→mid" vs "pair→mid (inverse routing)"? For two_pair, when does
    the swap-high-pair-to-bot routing win?

(D) Bigger MC sweep (100K-200K hands) to get tighter ceiling estimates
    and bigger training set for v7. If the 50K-trained v7 has overfit
    leaves (3.6 hands/leaf average), a 100K sweep would halve that.
    Cost: ~7 hours overnight. Marginal v7 gain estimate: +$50-100/1000h.

The user has previously chosen (A)-style targeted mining. The pair-to-bot
pattern is the highest-confidence next win since (a) we have direct empirical
evidence of the gap on probe hands, (b) it covers ~12% of all hands × ~25%
where the rule fires = ~3% of hands with $1-4K per-hand swings, (c) builds
on v8_hybrid's clean foundation.

Apply the 4-step doctrine for any hypothesis BEFORE running new MC:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample)
3. Measure Impact (EV-loss share)
4. Test Cheaply (in silico / analytical proxy)
Then act.

Session-end protocol (mandatory): commit + push to origin/main per
session-end-prompt.md. Push is pre-authorized per persistent memory.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
