# Current: Sprint 7 Phase D — ceiling-curve executed, EV-loss baseline established, project goal RETIRED + reframed. Session 16 closed; data-driven feature mining begins next session.

> **🔥 IMMEDIATE NEXT ACTION (Session 17):** Begin category-specific miss-driven feature mining on **single-pair hands** (47% of v3 total EV-loss). Filter `data/feature_table.parquet` to `mode_count == 3 AND category == 'pair'`. Train depth=None DT on that slice with current 27 features. Mine impure leaves to discover what hand structures the features can't distinguish. Engineer 2-3 new interaction features from the patterns. Re-run 3-of-4 ceiling on augmented feature set; target lift from 70% → 80%+.

> **🚫 RETIRED (Decision 033):** "≥95% shape-agreement on multiway-robust target." Replaced with directional reduction below v3's 1.63 EV-loss baseline AND non-negative absolute mean EV against all 4 opponent profiles. Reportable metric: $/1000 hands at $10/EV-pt.

> Updated: 2026-04-27 (end of Session 16)

---

## Headline state at end of Session 16

**Project goal officially reframed.** Old: "5-10 rule chain ≥95% multiway-robust shape-agreement." New: "rule chain that achieves directional EV-loss reduction below v3's 1.63 baseline AND positive mean EV against all 4 opponent profiles." Discovery-phase framing — no hard percentages, dollar-grounded reporting at $10/EV-pt over 1000 hands.

### v3 production rule chain — the new full picture

| | Shape (legacy) | Mean EV-loss | **Absolute mean EV** | $/1000 hands at $10/pt |
|---|---|---|---|---|
| vs MFSuitAware | (n/a per profile) | 1.37 | **−0.78** | **−$7,779** ❌ |
| vs Omaha | | 1.15 | +1.01 | +$10,117 ✅ |
| vs TopDef | | 1.44 | **−0.89** | **−$8,846** ❌ |
| vs Weighted | | 1.22 | +0.38 | +$3,779 ✅ |
| Multiway-robust shape | **56.16%** | (1.63 mean) | (mixed) | (mixed) |

**v3 is profitable against weak opponents but LOSES money against strong ones.** 72% of hands v3 loses money on against MFSuitAware. BR (optimal solver play) is profitable vs all 4 (+0.55 to +2.16 mean EV).

### Phase D ceiling-curve results (the structural diagnosis)

| | Full 6M | 3-of-4 majority subset (2.43M) |
|---|---|---|
| Depth=None ceiling (full) | **61.74%** | **70.01%** |
| Depth=None ceiling (CV) | 57.24% | 65.86% |
| CV peak depth | 15 (cv_shape 59.57%) | 15 (cv_shape 67.48%) |

**The 27-feature set is structurally insufficient for the 95% target.** Even unbounded-depth trees with 151K leaves cap at 62% on full data and 70% on clear-majority hands. Feature engineering is the lever — depth alone cannot break through.

### What was tested and refuted this session

1. **Fall-through hypothesis** ("v3 falls through to setting 102/104 on blunders"): OR=1.09 across 666 blunders / 1334 non-blunders → **refuted by representative-sample odds ratio**. The visual pattern in worst-15 list was confirmation bias.
2. **+5 Ace-on-top bias is the surgical bug** (`_score_top_choice_for_locked_mid` line 480): empirically tested as `strategy_v3_no_top_bias`, **refuted** — net total EV-loss INCREASED +93 EV (3% worse). The +5 bonus is load-bearing for non-Ace pair hands. Surgical-patch path is dead.

### What was learned about miss patterns

- 33.3% of hands are blunders (max-loss > 2.0).
- **Ace-singleton accounts for 45.5% of total EV-loss** across all hand categories — every Ace-cohort has 30-86% higher mean loss than its non-Ace counterpart. Real signal but **structurally diffuse**.
- Category-specific densities (highest mean loss per hand among n≥30 cohorts):
  1. two_pair + ace: 2.90 EV/hand (98 hands, 8.7% of loss)
  2. trips + ace: 2.07 (32 hands, 2.0%)
  3. pair + ace: 1.83 (382 hands, **21.4%** of loss)
  4. trips_pair: 1.82 (34 hands, 1.9%)
  5. high_only + ace: 1.75 (235 hands, **12.6%** of loss)
- Single-pair hands are 47% of total loss by sheer count (987 hands, OR ~0.9 — at baseline rate). Largest cohort to attack.

---

## What was completed this session (Session 16)

### Phase D Step 1 — ceiling-curve

- `analysis/scripts/dt_phase1.py` ran cleanly (~5 min CPU). Produced full 6M ceiling: 61.74% / 57.24%.
- `analysis/scripts/dt_phase1_3of4.py` (NEW) — 3-of-4 majority subset (2,432,648 hands). Ceiling 70.01% / 65.86%.

### EV-loss baseline harness (NEW)

- `analysis/scripts/v3_evloss_baseline.py` — random-hand sampler, subprocess to `mc --tsv`, per-profile absolute EV + EV-loss + per-cohort distributions. Supports `--strategy` flag (v3, v3_no_top_bias) and `--save data/<name>_records.parquet`.
- `data/v3_evloss_records.parquet` — v3 ground-truth baseline (seed=42, N=2000). 197KB.
- `data/v3_no_top_bias_records.parquet` — refuted-patch comparison records.

### Blunder analysis (Gemini's 3-test methodology)

- `analysis/scripts/v3_blunder_analysis.py` — Tests 1/2/3 + bonus EV-loss share computation + worst-15 dump. Used to refute fall-through hypothesis and quantify multi-pair-with-Ace cluster (9.5% of loss only, not the dominant pattern I'd suggested).

### Ace-bias patch experiment

- `strategy_v3_no_top_bias` added to `encode_rules.py` (lines ~626-720). Drops the `+5` highest-singleton bonus while keeping the `-10` pair-breaking penalty. Empirically refuted; left in tree as cautionary marker.

### Methodology doctrine locked in

- 4-step process for any hypothesis: **Signal (OR) → Impact (EV-loss share) → in silico → only then run new MC.** Two consecutive wrong hypotheses in this session would have been killed in 30s by an in silico instead of 18 min of MC compute.

### Goal reframe (Decision 033)

- 95% shape-agreement target retired.
- Absolute EV per profile is the new headline.
- Rule-count cap is soft (>10 named heuristics OK if EV gain is significant).
- $/1000 hands at $10/EV-pt for non-technical legibility.

---

## Files added this session

- `analysis/scripts/dt_phase1_3of4.py`
- `analysis/scripts/v3_evloss_baseline.py`
- `analysis/scripts/v3_blunder_analysis.py`
- `data/v3_evloss_records.parquet` (197KB)
- `data/v3_no_top_bias_records.parquet`

## Files modified this session

- `analysis/scripts/encode_rules.py` — added experimental `_score_top_choice_no_top_bias`, `_best_top_for_locked_mid_no_bias`, `strategy_v3_no_top_bias` (refuted variant; left in tree)
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — appended Decision 033
- `handoff/MASTER_HANDOFF_01.md` — appended Session 16 entry

## Verified

- Rust: `cargo build --release` clean. `cargo test --release` 124/124 pass.
- Python: 74/74 tests pass (24 features + 11 settings + 9 canonical + 9 cross_model + 13 v3_golden + 8 overlays_golden).

## Gotchas + lessons

- **Confirmation bias from worst-list inspection cost 9 min of MC.** The visible pattern in 15 worst hands (all setting 104) didn't generalize — OR was 1.09 across the full blunder population. **Always odds ratio over a representative sample, never eyeball the tail.**
- **Single-component patches don't work in v3.** `_score_top_choice_for_locked_mid` has interacting components (-10 pair penalty, +5 highest-singleton, +3 bot DS, +1 bot conn, rank/100). Tweaking one breaks others. Architecture is at its hand-engineered ceiling.
- **EV-loss alone hides whether a strategy profits.** Always report absolute EV per profile alongside EV-loss vs BR. The user's $10/point reframe surfaced that v3 actively loses money vs strong opponents — a fact the loss-only view obscured.
- **Decision 030 had a small numerical error.** It claimed mode_count ≥ 3 = 90.4%. Actual: 67.16% (4-of-4 = 26.68%, 3-of-4 = 40.48%). The genuinely-arbitrary tie-break pool (2-2 + 1-1-1-1) is 12.19%, not 73% as my earlier framing implied. Doesn't change strategic conclusions — just numerical precision.

## Resume Prompt (Session 17)

```
Resume Session 17 of the Taiwanese Poker Solver project.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 16)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 033 — 95% target retired)
- handoff/MASTER_HANDOFF_01.md (scan Sessions 13-16; Session 16 is the most consequential)
- analysis/scripts/encode_rules.py (current rule chain — strategy_v3 is production)
- analysis/scripts/v3_evloss_baseline.py (canonical evaluation harness)
- analysis/scripts/v3_blunder_analysis.py (3-test methodology + EV-loss share)
- data/v3_evloss_records.parquet (ground-truth baseline records, seed=42)

State of the project (end of Session 16):
- 95% shape-agreement target RETIRED (Decision 033).
- New headline: per-profile absolute EV (does v3 profit?) AND mean EV-loss reduction below v3 baseline 1.63.
- v3 LOSES money vs strong opponents (MFSA −0.78, TopDef −0.89), profits vs weak (Omaha +1.01, Weighted +0.38).
- 27-feature DT ceiling: 61.74% on full 6M, 70.01% on 3-of-4 majority. Features ARE the bottleneck.
- Two surgical-fix hypotheses tested and refuted (fall-through OR=1.09; +5 Ace-bonus removal: net loss +93 EV).
- 124 Rust + 74 Python tests green.

User priorities (re-confirmed Session 16):
- Discovery mode, not production commitment. Don't set ultra-tight goals.
- Data/ML/AI drives discovery — user's example heuristics are arbitrary illustrations, NOT constraints or features to encode literally.
- Rule-count cap is soft — more than 10 named heuristics OK if EV gain is significant.
- Track results as $/1000 hands at $10/EV-point — non-technical-friendly framing.

IMMEDIATE NEXT ACTION:
Begin category-specific miss-driven feature mining on single-pair hands (47% of v3 EV-loss).
Steps:
1. Filter feature_table.parquet to (mode_count == 3) AND (category == 'pair') — should be ~1.2M hands.
2. Train depth=None DT on that slice with current 27 features. Report shape ceiling on this slice.
3. Inspect the 50 most-impure leaves of the depth=None tree. Dump the cards in those leaves. What hand structures cluster there?
4. Engineer 2-3 new interaction features from the visible patterns; don't speculate.
5. Re-run 3-of-4 ceiling with augmented feature set. Target lift toward 80%+.
6. If lift is real, train depth-10 to depth-15 DT on FULL 6M with augmented features, extract via export_text → Python if/elif → byte-identical parity check.
7. Re-baseline EV-loss with v3_evloss_baseline.py --strategy <new_chain>. Compare absolute EV per profile to v3.

Apply the 4-step methodology doctrine for any hypothesis:
1. Hypothesize (qualitative observation)
2. Measure Signal (odds ratio on representative sample — NOT eyeballing worst-list)
3. Measure Impact (EV-loss share — does the pattern matter in aggregate?)
4. Test Cheaply (in silico / analytical proxy BEFORE running new MC)
Then act.

Don't repeat session 16's mistake of jumping from "Ace-singleton 45% of loss" to "+5 bonus is the bug" without an in silico — that cost 9 min of MC for a refuted hypothesis.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
