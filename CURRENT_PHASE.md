# Current: Sprint 7 Phase B in progress — high_only refinement +11.5pp, REFINED extended via search-based mid/bot scoring, buyout signature deployed. Rule chain at 55.93% shape-agreement on 6M.

> Updated: 2026-04-26 (end of Session 13)
> Previous sprint status: Session 12 delivered the feature pipeline + first encoded rule chain at 53.58% shape-agreement; Session 13 attacked Phase B priorities 1-4 (high_only gap, REFINED conditionals, unanimous-miss diagnostic, buyout pre-step). Rule chain now 55.93% — modest but evidence-based gain. Buyout classifier shipped as a separate `tw_analysis.buyout` module.

---

## What was completed this session (Session 13)

### Priority 1 — Close the high_only gap (DELIVERED, partial)
- `analysis/scripts/mine_high_only.py` — 8-section deep miner over the 1.23M no-pair hand subset. Headlines:
  - Robust top == hand top_rank (highest singleton): **83.05%**.
  - Robust mid is suited 58.40%, connected 85.13%; mid = (second, third) only **20.37%** — naive_104's mid choice is wrong 80% of the time.
  - Robust bot DS rate when feasible (suit_2nd ≥ 2): **55.44%**.
  - Naive_104 shape-agreement on high_only: 19.50%, with 79% of misses coming from MID, only 21% from TOP.
- `analysis/scripts/diag_high_only_misses.py` — sample-based confusion analysis. Discovered my first heuristic over-DS'd the bot (77% vs robust's 49%) and under-suited the mid (37% vs 58%). Iterated on weight schemes.
- `analysis/scripts/diag_high_only_ceiling.py` — measured **inter-profile shape-agreement on high_only is only 22-67%** (avg ~36%). Only 8.62% of high_only hands are unanimous. **Theoretical ceiling for any single rule against multiway-robust on high_only is ~50%.**
- `encode_rules.py::strategy_hi_only_search` — search-based fallback for no-pair hands. Final weights (mid-first):
  - mid suited+connected +6, suited only +4, connected (gap≤2) +2
  - bot DS +5, bot connectivity ≥4 +2, bot ≥2 broadway +1
  - mid rank-sum/100 (final tiebreak)
  - **High_only shape-agreement: 19.50% → 31.01%** (+11.5pp; capacity well below the ~50% ceiling).

### Priority 2 — Make REFINED actually different from SIMPLE (DELIVERED, no-op gain)
- `encode_rules.py::strategy_refined_v2` — extends search-based top selection to pair / two_pair / trips_pair / quads via `_best_top_for_locked_mid` (composite: top=highest-singleton +5, bot DS +3, bot conn≥4 +1, top rank/100).
- Result: **0pp delta vs hi_only_search.** Investigated — `top = highest singleton` is already correct in 77%+ of pair-based hands; the +5 preference dominates the +3 DS bonus, and forcing a different top would reduce overall accuracy. The existing rule IS the refined rule for top selection on locked-mid hands.

### Priority 3 — UNANIMOUS misses investigation (DELIVERED, surfaced new pattern)
- `analysis/scripts/diag_unanimous_misses.py` — bucketed 273K unanimous misses by category and inspected 30 examples. Major discovery: for `two_pair` hands, **robust often picks the LOWER pair → mid** (not higher), counter to SIMPLE. Examples include AAKK → KK in mid (60.9%), 2-2/3-3 hands, 5-5/6-6 hands.
- `analysis/scripts/probe_two_pair.py` — full stratification by (high_pair, low_pair) rank. Confirmed:
  - Low two_pair (high ≤ 5): mid is "no pair at all" 30-50% (both pairs to bot, mid = singleton-pair).
  - Adjacent high pairs (gap=1, both ≥ 9): lower → mid is 30-40% — significant counter-pattern.
  - **AAKK (14, 13): lower → mid 60.9%** (the strongest case).
- DECISION: Did NOT encode these refinements yet. Each only adds <1pp, requires complex conditional logic, and the user prioritises 5-10 rules. Documented in handoff as candidate Phase B+ work if 70% target is hard-required.

### Priority 4 — Buyout pre-step (DELIVERED)
- `analysis/src/tw_analysis/buyout.py` — module with both scalar and batch APIs. Tightened signature for high precision:
  - **Quads of rank ≤ 5** → BUYOUT
  - **Trips ≤ 4 + pair ≤ 3** (low full-house shape) → BUYOUT
- Validated on full 6M hands (`buyout_signature.py`):
  - Precision 26.30%, Recall 46.56%, F1 33.6% vs ground truth (ev_mean < -4).
  - Catches 1,945 of 1,956 (99.4%) low-quads buyout cases; misses pure-trips category which is too noisy as a single-feature signature (recall only 47% overall as a result).
- Exported via `tw_analysis` package — trainer can now call `buyout_signature_scalar(...)` for the BUYOUT badge.
- Trainer integration deferred to next session.

### Headlines (full 6M)

| metric | NAIVE_104 | SIMPLE = REFINED | hi_only_search = refined_v2 |
|---|---|---|---|
| Overall LITERAL agreement | 20.09% | 49.06% | **51.41%** |
| **Overall SHAPE agreement** | **21.77%** | **53.58%** | **55.93%** |
| Unanimous slice (26.7%) | 30.13% | 82.93% | 83.70% |
| 3of4 (40.5%) | 22.44% | 57.89% | 60.60% |
| Quads | 23.14% | 79.20% | 79.20% |
| Three-pair | 17.90% | 72.88% | 72.88% |
| Pair | 19.09% | 65.02% | 65.02% |
| Two-pair | 26.12% | 59.16% | 59.16% |
| Trips | 30.57% | 56.39% | 56.39% |
| Trips_pair | 32.64% | 46.16% | 46.16% |
| **High_only** | **19.50%** | **19.50%** | **31.01%** |

Shape-agreement up by **+2.35pp overall** (53.58% → 55.93%). Half the gap on high_only is closed. Remaining gap to 70% target (~14pp) is dominated by structurally contested categories where inter-profile disagreement caps single-rule accuracy.

### Honest take on the 70% target
Diagnostic work this session showed the gap to 70% is NOT primarily a rule-mining problem. It's an opponent-modelling problem:
  * On high_only, the 4 production profiles agree on the answer for only 8.6% of hands (vs 26.7% unanimous overall). Inter-profile shape-agreement averages 36%.
  * **A single deterministic rule cannot exceed ~50% on high_only** because the right answer genuinely depends on opponent type.
  * This generalises: the more contested a category, the lower the rule-chain ceiling. The rule chain is meant to capture the OPPONENT-INDEPENDENT decisions; opponent-dependent decisions belong in a separate "exploit layer" the trainer surfaces.

Path forward suggestion: rather than chasing 70% on multiway-robust, accept the rule chain at ~60% as the "robust core strategy" and build separate per-profile guidance for contested cases.

---

## Files touched this session

**Added:**
- `analysis/scripts/mine_high_only.py`
- `analysis/scripts/diag_high_only_misses.py`
- `analysis/scripts/diag_high_only_ceiling.py`
- `analysis/scripts/diag_unanimous_misses.py`
- `analysis/scripts/probe_pair.py`
- `analysis/scripts/probe_two_pair.py`
- `analysis/scripts/buyout_signature.py`
- `analysis/src/tw_analysis/buyout.py`

**Modified:**
- `analysis/scripts/encode_rules.py` — added `strategy_hi_only_search` and `strategy_refined_v2`
- `analysis/src/tw_analysis/__init__.py` — exports for buyout module
- `CURRENT_PHASE.md` — this file (rewritten)

**Verified end-to-end:**
- `cargo build --release` — clean.
- `cargo test --release` — all tests pass (omaha/scoring/hand_eval/integration).
- `analysis/scripts/test_features.py` — 24/24 pass.
- `encode_rules.py` full 6M run completes in ~5 minutes; 4 strategies scored.
- `buyout_signature.py` full 6M validation runs cleanly.

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md` (Session 13 entry to be appended)

---

## Resume Prompt (next session — Sprint 7 Phase B continuation)

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- DECISIONS_LOG.md
- handoff/MASTER_HANDOFF_01.md  (scan Sessions 12-13)
- analysis/scripts/encode_rules.py  (current rule chain — 4 strategies)
- analysis/src/tw_analysis/buyout.py  (buyout signature)

State of the project:
- Rule chain at 55.93% shape-agreement on 6M (best: hi_only_search /
  refined_v2). Up from 53.58% baseline (+2.35pp).
- High_only at 31.01% (was 19.50%) — but ~50% ceiling per inter-profile
  agreement diagnostic (only 8.6% of high_only hands are unanimous).
- Buyout signature shipped as `tw_analysis.buyout` module.
  Precision 26%, Recall 47% vs ev_mean < -4 ground truth. Trainer wiring
  pending.
- DECISIONS_LOG.md unchanged this session (no new architectural decisions).

Sprint 7 Phase B+ PRIORITIES:

1. **Wire buyout into the trainer (`trainer/app.py`).**
   On hand-deal, call `buyout_signature_scalar(...)` and surface a "BUYOUT"
   badge if True. Additionally, look up the hand's `ev_mean` from
   feature_table.parquet and surface a softer "consider buyout vs [profile]"
   for the borderline cases the signature misses.

2. **Encode the two_pair lower-pair-mid pattern.** Specifically:
   - AAKK (high=14, low=13): force LOW pair → mid (60.9% of robust).
   - Adjacent high pairs (gap=1, low ≥ 9): consider lower → mid
     conditionally; check it doesn't regress the dominant case.
   - Low two_pair (high ≤ 5): consider "both pairs to bot, mid is
     singleton-pair" pattern (30-50% of robust).
   Each is a small absolute gain (~0.1-0.5pp); decide if pursuing.

3. **Self-play break-even Nash check (Sprint 7 P3).** Now that the chain
   has a stable handle (55.9%), encode `strategy_hi_only_search` as both
   players in 100K self-play hands. Mean EV ≈ 0 measures Nash distance.
   This is the ultimate sanity check before publishing the rule chain.

4. **Trainer's explain.py update.** Swap from hand-written heuristics to
   reasoning grounded in the encoded rules: "in 84% of similar unanimous
   hands the rule chain matches solver; in this case yours diverged from
   the rule chain on the mid tier" etc.

5. **(Lower priority) Reach for ≥60%.** If the user wants further rule
   refinements, the candidate moves are:
   - Add bot-rundown detection (4-card straight) as separate from connectivity.
   - Encode "low pair → bot" rule for pair hands with pair_high ≤ 5.
   - Rebalance hi_only_search weights against per-profile MFSA only
     (the modal opponent) instead of multiway-robust.

DEFERRED:
- Per-tier EV decomposition (engine matchup_breakdown exposure)
- Naive-distance metric
- Category bucketing fix (trips+trips, quads+pair) — affects <0.5%

PRIORITY FROM USER:
- 5-10 rules max. Compression non-negotiable.
- The current chain is 7 rules + buyout signature = 8 rules. Within budget.
- Use SHAPE agreement, NOT literal.

Suggested starting point for next session: depends on user direction.
If 70% is hard-required → priority 5 (more refinements). If trainer UX
is the goal → priority 1 (buyout wire-up). If publication-ready strategy
is the goal → priority 3 (self-play Nash check).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
