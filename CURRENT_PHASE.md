# Current: Sprint 7 Phase B+ shipped — buyout in trainer, two_pair refinements (v3 = 56.16%), self-play regret check, rule-grounded explain.py, v4 weight rebalance attempted (no gain). Rule chain at v3, considered Phase-B-final.

> Updated: 2026-04-26 (end of Session 14)
> Previous sprint status: Session 13 delivered the high_only refinement (+11.5pp on category) and the buyout module. Session 14 worked through the entire Phase B+ priority list, ending with v3 (56.16%) as the production rule chain. v4's weight rebalance had ~0 effect, confirming we're at the structural ceiling for opponent-agnostic rules.

---

## What was completed this session (Session 14)

### Priority 1 — Buyout signature wired into trainer (DELIVERED)
- `trainer/src/buyout_eval.py` — bridge module that converts trainer card-strings to engine bytes, calls `tw_analysis.buyout.buyout_signature_scalar`, and combines with the live MC `best_ev` to produce both the high-precision signature signal AND a softer per-profile "best play loses more than the buyout cost" signal (`BUYOUT_COST = 4.0`).
- `trainer/app.py` — `/api/score` now returns a `buyout` dict per request; `/api/compare` returns hand-level signature + per-row `buyout_soft` flags + `soft_profiles` list of which profiles trigger the soft signal.
- `trainer/static/index.html`, `app.js`, `style.css` — banner above the result panel renders red BUYOUT badge for signature hits, amber "consider buyout" hint for soft hits, plus per-row "buyout" tag in the compare table.
- Smoke-tested end-to-end: quad-2 hand fires signature (best_ev -7.76), AA broadway clean, trips-3+pair-2 fires signature with soft_profiles=[MFSA, TopDef].

### Priority 2 — Two_pair lower-pair-mid pattern (DELIVERED)
- `analysis/scripts/encode_rules.py::strategy_v3` — extends `refined_v2` with two_pair conditionals:
  * AAKK (high=14, low=13) → low pair (KK) → mid (60.9% of robust per probe_two_pair).
  * Low two_pair (high ≤ 5) → both pairs to bot, mid = highest 2 singletons (modal robust answer 41-56% on these cells).
  * All other two_pair → unchanged (high pair → mid).
- Result on full 6M: **two_pair 59.16% → 60.20% (+1.04pp); overall 55.93% → 56.16% (+0.23pp).**
- Adjacent high pairs (KKQQ, QQJJ etc.) deliberately NOT changed — high → mid still wins ~67-69% on those.

### Priority 3 — Self-play regret check (DELIVERED)
- `analysis/scripts/selfplay_check.py` — samples random hands, runs engine MC against all 4 production profiles, and reports per-profile `(mean v3 EV, mean best EV, mean gap, match%)`. Documents in its docstring that pure self-play under symmetry is trivially zero, and explains that the useful measurement is exploitability gap.
- Result on 200 hands × samples=1000:

  | profile        | mean v3 EV | mean best EV | mean gap  | match% |
  |----------------|------------|--------------|-----------|--------|
  | MFSuitAware    | +0.235     | +0.398       | +0.164    | 56.5%  |
  | OmahaFirst     | +1.627     | +2.027       | +0.400    | 47.5%  |
  | TopDefensive   | +0.128     | +0.359       | +0.231    | 47.5%  |
  | RandomWeighted | +1.252     | +1.389       | +0.137    | 62.5%  |

- Strategy_v3 BEATS every profile on average (mean EV positive) and the average gap to solver-optimal stays under 0.50 EV/hand (the "meaningful" threshold). Not Nash, but solidly competitive.

### Priority 4 — Rule-chain-grounded explain.py (DELIVERED)
- `trainer/src/explain.py` — full rewrite. Now does a three-way comparison: USER's setting vs CHAIN's setting (via `strategy_v3`) vs SOLVER's best.
- Findings cover all five three-way relationships (all-agree, user=chain≠best, user=best≠chain, chain=best≠user, all-different), each with category-level rule-chain accuracy as the prior ("matches the solver on X% of <category> hands").
- Per-tier diff finding identifies which tier(s) differ between user and solver in plain rank notation.
- Kept the Omaha bottom-suit detector from v1 as a supplementary structural observation; dropped split-pair / wrong-top / tier-swap detectors since the rule-chain comparison subsumes them.
- Verified end-to-end via curl on AAKK case: trainer correctly says "You followed the rule chain — this hand is one of its misses" with the solver's pick spelled out.

### Priority 5 — Reach for ≥60% shape-agreement (ATTEMPTED, NULL RESULT)
- `analysis/scripts/encode_rules.py::strategy_v4` — bumps bot weights in both `_score_top_choice_for_locked_mid` (DS 3→4, conn 1→2) and `_hi_only_pick` (conn 2→3) to enable bot DS / 4-rundown more aggressively.
- Result on full 6M: **v4 = 56.12%** (vs v3 = 56.16%, a -0.04pp regression). High_only category 31.01% → 30.84% — the rebalance shifts choices on a few thousand hands but the gains and losses approximately cancel.
- Per-profile breakdown for v3: against multiway-robust 56.16%; vs MFSuitAware 55.68%; vs OmahaFirst 45.87%; vs TopDefensive 46.32%; **vs RandomWeighted 62.05%**. Strategy_v3 already crosses 60% against the easiest opponent.
- **Conclusion: 60% multiway-robust is at or beyond the structural ceiling for an opponent-agnostic 7-rule chain.** Any further rule additions that improve one opponent profile likely degrade another. The proper path to >60% is per-profile rule overlays — kept v4 in the file as documented "tried it, didn't move" so future sessions don't re-do the experiment.

### Headlines (full 6M, end of session)

| metric | NAIVE_104 | SIMPLE = REFINED | hi_only_search = refined_v2 | **v3 (production)** | v4 (no gain) |
|---|---|---|---|---|---|
| Overall LITERAL agreement | 20.09% | 49.06% | 51.41% | **51.64%** | 51.60% |
| **Overall SHAPE agreement** | **21.77%** | **53.58%** | **55.93%** | **56.16%** | **56.12%** |
| Unanimous slice (26.7%) | 30.13% | 82.93% | 83.70% | 83.73% | 83.70% |
| 3of4 (40.5%) | 22.44% | 57.89% | 60.60% | 60.97% | 60.94% |
| Quads | 23.14% | 79.20% | 79.20% | 79.20% | 79.20% |
| Three-pair | 17.90% | 72.88% | 72.88% | 72.88% | 72.88% |
| Pair | 19.09% | 65.02% | 65.02% | 65.02% | 65.03% |
| Two-pair | 26.12% | 59.16% | 59.16% | **60.20%** | 60.20% |
| Trips | 30.57% | 56.39% | 56.39% | 56.39% | 56.38% |
| Trips_pair | 32.64% | 46.16% | 46.16% | 46.12% | 46.12% |
| **High_only** | **19.50%** | **19.50%** | **31.01%** | **31.01%** | 30.84% |

### Per-profile shape-agreement (v3)

| target opponent           | v3 shape-agreement |
|---------------------------|---|
| multiway_robust (mode)    | 56.16% |
| MFSuitAware (modal)       | 55.68% |
| OmahaFirst                | 45.87% |
| TopDefensive              | 46.32% |
| RandomWeighted            | **62.05%** |

---

## Files touched this session

**Added:**
- `trainer/src/buyout_eval.py`
- `analysis/scripts/selfplay_check.py`

**Modified:**
- `trainer/app.py` — `/api/score` and `/api/compare` now include buyout
- `trainer/src/explain.py` — full rewrite, rule-chain-grounded
- `trainer/static/index.html` — buyout banner placeholders
- `trainer/static/app.js` — `renderBuyoutBanner`, per-row buyout tag
- `trainer/static/style.css` — buyout banner styles
- `analysis/scripts/encode_rules.py` — added `strategy_v3` + `strategy_v4` + per-profile measurement
- `CURRENT_PHASE.md` — this file (rewritten)
- `handoff/MASTER_HANDOFF_01.md` — Session 14 entry appended

**Verified end-to-end:**
- `cargo build --release` clean.
- `cargo test --release`: 88 + 15 + 15 + 6 = 124 tests pass.
- Python tests: features 24/24, settings 11/11, canonical 9/9.
- `encode_rules.py` full 6M run completes in ~5 minutes; 7 strategies scored.
- `selfplay_check.py --hands 200 --samples 1000` runs in ~50s; per-profile gap report renders cleanly.
- Trainer manual smoke: quad-2 hand fires BUYOUT badge, AAKK case shows rule-chain-vs-solver explanation.

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md` (Session 14 entry appended)

---

## Resume Prompt (next session)

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- DECISIONS_LOG.md
- handoff/MASTER_HANDOFF_01.md  (scan Sessions 12-14)
- analysis/scripts/encode_rules.py  (current rule chain — 7 strategies)
- trainer/src/explain.py            (rule-chain-grounded feedback)
- trainer/src/buyout_eval.py        (signature + soft buyout signals)

State of the project (end of Session 14):
- Production rule chain = `strategy_v3` (encode_rules.py).
  56.16% shape-agreement vs multiway-robust on full 6M.
  Per-profile: MFSA 55.7%, Omaha 45.9%, TopDef 46.3%, RandomWeighted 62.0%.
- Buyout signature shipped in trainer with both signature + soft signals.
- Self-play regret: v3 BEATS all 4 profiles on average; gap to solver-optimal
  is +0.14 to +0.40 EV/hand — solidly competitive, not Nash.
- explain.py rewritten to compare USER vs CHAIN vs SOLVER with category-
  level rule-chain accuracy framing.
- v4 weight rebalance attempted (DS/conn weights bumped) — no gain (-0.04pp).
  60% on multiway-robust appears at the ceiling for an opponent-agnostic
  7-rule chain; further gains require per-profile overlays.

Possible directions for Session 15:

1. **Per-profile rule overlays.** The biggest gap is OmahaFirst & TopDefensive
   (~46% each). Build a small rule chain SPECIFIC to each profile, surface in
   the trainer when the user picks that profile. Could reach 70%+ per-profile.

2. **Trainer accuracy tracking** (Sprint 5b). Persist user submissions, track
   accuracy by hand category, build a "drill weak categories" mode.

3. **Decision-tree extraction** for publication. The current rule chain is in
   Python; a published "GTO Taiwanese Poker strategy guide" needs the rules
   in a decision-tree format a human can memorize. Build a Markdown export
   from `encode_rules.py::strategy_v3`.

4. **Tighter buyout signature.** Current is precision 26%, recall 47%. Try
   adding new feature buckets (e.g., "very low quads + isolated high"
   doesn't fire current rule but is buyout 30% of the time?). Probe required.

5. **Rule chain unit tests.** Lock in the current strategy_v3 behavior with
   golden-hand tests so future sessions can refactor without regression risk.

PRIORITY FROM USER:
- 5-10 rules max. Compression non-negotiable.
- Current chain = 7 rules + 2 two_pair conditionals + buyout signature = 10
  rules. AT BUDGET. Adding more requires removing one.
- Use SHAPE agreement, NOT literal.

Suggested starting point: depends on user direction. Trainer UX → priority 2
(accuracy tracking). Publication-ready → priority 3 (decision-tree export).
Robustness against tougher opponents → priority 1 (per-profile overlays).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
