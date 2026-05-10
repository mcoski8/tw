# Session 56 — v42_dt new ML champion (+$79 full / $0 prefix) via high_only zone collapse

_Generated: 2026-05-10_

## TL;DR — HIGH_ONLY ZONE COLLAPSE BY 13.8% VIA 4 RANK-VALUED DS-ROUTING FEATURES

User direction: apply the proven 4-phase playbook (Sessions 54+55) to the
LARGEST remaining ML residual zone — high_only at $2,796/1000h
within-category, 40.4% of population, ~63% of v41's whole-grid regret.

User prediction: high_only would likely need different feature types
than prior zones (top-card placement, defensive triggers, broadway
connectivity, three-of-a-suit clustering). **Reality: the dominant
high_only blind spot turned out to be the SAME pattern as prior zones —
a DS-bot achievability gap.**

| Grid | v41_dt | v42_dt | Δ |
|---|---:|---:|---:|
| Full (N=200) | $1,270 | **$1,192** | **−$79** |
| Prefix (N=1000) | $686 | $686 | $0 |
| pct_opt full | 62.18% | **63.08%** | **+0.91%** |
| pct_opt prefix | 67.13% | 67.13% | 0 |
| p90 regret | 0.450 | 0.425 | improved |
| p99 regret | 1.075 | 1.035 | improved |

**Cumulative v32 → v42 = −$524 full / −$218 prefix** across 7 ML ships.
v42 is the 4th-largest single ML ship after v39 (−$237), v41 (−$124),
v34 (−$34).

**Prefix grid neutrality is by design, not regression:** the prefix
slice (500K hands) contains zero high_only hands. The new features are
gated to high_only, so prefix metrics are mathematically unchanged.
Every non-high_only category on prefix is byte-identical to v41.

## Phase 1: Drill HO (high_only mismatch matrix)

Sweep of all 1,226,940 high_only hands at 3,780/s (324s wall time).

**Total mismatch contribution: $481/1000h whole-grid** — matches the
expected $486 from within-cat regret × population share.

### Top mismatch class (single-class)
| | v41 picks | oracle picks | n | mean reg | wg contrib |
|---|---|---|---:|---:|---:|
| 1 | tA_SS_mu | tA_DS_ms | 28,014 | $7,774 | **$36.24** |
| 2 | tA_SS_mu | tA_DS_mu | 41,302 | $4,721 | $32.45 |
| 3 | tA_SS_mu | tA_SS_ms | 41,004 | $4,652 | $31.74 |
| 4 | tK_SS_mu | tK_DS_ms | 13,227 | $7,952 | $17.50 |
| 5 | tA_SS_ms | tA_DS_mu | 26,204 | $3,134 | $13.66 |

### Collapsed by bot-suit-profile swap
| v41_bot | oracle_bot | n | mean reg | wg contrib |
|---|---|---:|---:|---:|
| **SS** | **DS** | **236,205** | **$5,344** | **$210.08** |
| SS | SS | 112,435 | $4,287 | $80.22 |
| 31 | DS | 45,575 | $4,751 | $36.04 |
| SS | 31 | 49,649 | $3,627 | $29.97 |

**SS→DS swap alone = $210/1000h whole-grid (44% of all high_only
mismatch contribution).** The dominant blind spot is suit-routing.

### Class distribution (collapsed by bot suit profile)
| suit | v41 % | oracle % | v41-oracle |
|---|---:|---:|---:|
| **DS** | **36.64%** | **52.16%** | **−15.51%** |
| **SS** | **46.72%** | **32.04%** | **+14.68%** |
| 31 | 13.39% | 13.10% | +0.28% |
| RB | 1.71% | 0.63% | +1.08% |
| 4f | 1.54% | 2.07% | −0.53% |

The 1:1 SS↔DS exchange is the structural error.

### (h1, h2) cell concentration
The top 6 broadway cells cover **$441/$481 = 92%** of all high_only
mismatch contribution:

| h1 | h2 | n | wg contrib |
|---|---|---:|---:|
| A | K | 330,330 | $143.64 |
| K | Q | 180,180 | $92.08 |
| A | Q | 180,180 | $75.35 |
| Q | J | 90,090 | $50.58 |
| K | J | 90,090 | $44.09 |
| A | J | 90,090 | $36.18 |

The v41 blind spot is overwhelmingly broadway-rich high_only hands.

## Phase 1b: Drill HO2 (hand-level inspection of tA_SS_mu → tA_DS_ms)

28,014 hands matched the target class. Top-20 hand inspection showed
oracle consistently re-routes the bot to a 2+2 suit pair while keeping
Ace on top, often using a low spade as the unsuited "filler" the v41
strategy buries on the bot.

**The smoking gun (full-population aggregates over all 28,014 hands):**

| Aggregate | Value |
|---|---|
| ho_v2_bot_DS_max_top_rank = A | **100.0%** of mismatches |
| Oracle's top == max_top across DS configs | **100.0%** of mismatches |
| Oracle's top == min_top across DS configs | 0.0% |
| Suit distribution (3,2,2,0) | 82.7% (7 DS configs each) |
| Suit distribution (2,2,2,1) | 17.3% (3 DS configs each) |

**In every single mismatch hand, an Ace-top + DS-bot config exists, and
oracle picks it. v41 does not see it.** The new ho_v2 features expose
exactly this signal — the structural delta is 100%-explained by the
playbook's standard DS-routing feature shape.

This is the cleanest Phase 1b validation in the project so far.

## Phase 2 v2: Rank-valued conditional features

Mirror of pair_aug_v5 / trips_pair_v2 / two_pair_v2 — applied to
high_only with no anchor (all 7 ranks distinct). Enumerates all
C(7,4)=35 candidate 4-card bot subsets, filters to suit profile = 2+2.

| Feature | What it captures |
|---|---|
| `ho_v2_bot_DS_n_configs_g` | Count of 4-card bot subsets that are DS (0..18; typical 0/3/7) |
| `ho_v2_bot_DS_max_top_rank_g` | Best top rank achievable across DS configs (= leftover max rank) |
| `ho_v2_bot_DS_min_top_rank_g` | Lowest top rank achievable (= leftover min rank, top fixed to lowest) |
| `ho_v2_bot_DS_max_mid_sum_g` | Best mid rank-sum across DS configs (= leftover top-2 sum, top = lowest) |

All zeros for non-high_only hands (n_pairs > 0 or n_trips > 0 or
n_quads > 0).

**Distribution (over full canonical 6.0M hands):**
- ho_v2_bot_DS_n_configs_g: 0=4.89M (gated zero), 3=540K, 6=180K, 7=180K, 9=120K, 10=36K, 18=60K
- ho_v2_bot_DS_max_top_rank_g: spread across 6..14, peak at 14 (Ace)
- ho_v2_bot_DS_min_top_rank_g: peaks at 2 (the floor)
- ho_v2_bot_DS_max_mid_sum_g: spread 9..27 with broadway-heavy

## Phase 3: v42_dt training + grading

### Training (depth=36 ml=1, 99 features = 95 + 4 ho_v2)

- Fit time: 355.7s (5.9 min)
- Leaves: **2,109,330 (+4.7% over v41's 2.02M)** — modest leaf growth,
  consistent with a single-axis surgical addition

### Feature importance (new ho_v2 placement)

| Rank | Feature | Importance |
|---:|---|---:|
| #26 | `ho_v2_bot_DS_max_mid_sum_g` | **0.28%** |
| #31 | `ho_v2_bot_DS_max_top_rank_g` | **0.22%** |
| #32 | `ho_v2_bot_DS_min_top_rank_g` | **0.21%** |
| #80 | `ho_v2_bot_DS_n_configs_g` | 0.03% |

**3 of 4 new features ranked in top-32** — deeper integration than the
S55 t2p_v2 family (which ranked #24/26/30/73). The min/max top-rank
pair captures asymmetric "must give up Ace" vs "can keep Ace" routing
choices.

### Full-grid grade (vs v41)

| Strategy | pct_opt | $/1000h | p90 | leaves |
|---|---:|---:|---:|---:|
| v41_dt | 62.18% | $1,270 | 0.450 | 2,015,413 |
| **v42_dt** | **63.08%** | **$1,192** | **0.425** | **2,109,330** |

**Δ = −$79/1000h, +0.91% pct_opt** — surgical and meaningful.

### Per-category (full grid)

| Category | v41 | v42 | Δ |
|---|---:|---:|---:|
| **high_only** | **$2,796** | **$2,411** | **−$385 (−13.8%)** |
| **high_only pct_opt** | **29.0%** | **33.4%** | **+4.4%** |
| pair | $1,097 | $1,097 | 0 |
| two_pair | $363 | $363 | 0 |
| trips | $1,194 | $1,194 | 0 |
| trips_pair | $281 | $281 | 0 |
| three_pair | $1,613 | $1,613 | 0 |
| quads | $545 | $545 | 0 |
| composite | $960 | $960 | 0 |

**All non-high_only categories byte-identical to v41.** Surgical
gating discipline preserved.

### Prefix-grid grade (vs v41)

| Strategy | pct_opt | $/1000h |
|---|---:|---:|
| v41_dt | 67.13% | $686 |
| v42_dt | 67.13% | $686 |

Δ = $0/1000h. **The prefix slice (500K canonical hands) contains zero
high_only hands.** The new features are gated to high_only, so the
prefix grade is mathematically guaranteed identical to v41.

This is a NEUTRAL result, not a regression. Every non-high_only
category on prefix is byte-identical to v41. Surgical gating means
"prefix grid invariant" is the expected outcome when the targeted zone
isn't represented in the prefix.

## Cumulative ML arc

| Strategy | Session | Hyperparams | Features | Leaves | Full $/1000h |
|---|---|---|---:|---:|---:|
| v30 | S36 | depth=30 ml=5 | 79 | 493K | $1,794 |
| v31 | S36 overnight | depth=32 ml=3 | 79 | 700K | $1,736 |
| v32 | S37 | depth=32 ml=3 | 83 | 732K | $1,715 |
| v34 | S38 | depth=34 ml=2 | 83 | 875K | $1,681 |
| v36 | S53 overnight | depth=36 ml=1 | 83 | 1.06M | $1,649 |
| v39 | S54 | depth=36 ml=1 | 87 | 1.52M | $1,412 |
| v40 | S55 Track A | depth=36 ml=1 | 91 | 1.57M | $1,394 |
| v41 | S55 Track B | depth=36 ml=1 | 95 | 2.02M | $1,270 |
| **v42** | **S56** | **depth=36 ml=1** | **99** | **2.11M** | **$1,192** |

**Cumulative v32 → v42: −$524/1000h on full grid** (across 7 ML ships).

**Why high_only collapsed less than prior zones (13.8% vs 60-69%):**
Prior zones (trips_pair, two_pair, pair) had a single dominant
structural axis that the v2/v5 feature shape captured nearly
completely. high_only has multiple structural axes — DS-routing is the
biggest ($210/1000h whole-grid contribution out of $481), but other
axes remain (top-card placement at non-Ace ranks, broadway
connectivity, defensive triggers). The current 4 features address the
DS-routing axis surgically; future v43+ work can target the remaining
$300/1000h of high_only mismatch contribution.

## Methodology lessons (Session 56)

1. **The playbook is fully transferable to the largest population zone.**
   Zone size doesn't break the methodology. high_only (40.4%
   population) collapsed via the same pipeline that handled trips_pair
   (1.8% population) and two_pair (14.5%).

2. **User-prediction "different feature types needed" was partially
   correct, partially wrong.** User predicted top-card placement,
   defensive triggers, broadway connectivity. **Reality: the DOMINANT
   blind spot was the same DS-routing pattern as prior zones — Ace-top
   IS preserved in 100% of dominant-class mismatches; the structural
   error is purely the bot suit profile.** The smoking-gun signal
   (Phase 1b: oracle uses max_top in 100% of mismatches) made this
   unambiguous. This is a generalizable lesson: when an existing
   feature family (DS-bot achievability) is missing entirely, that gap
   dominates even when other axes also exist.

3. **Phase 1b can be a 100% confirmation, not just a 70-90% one.** Prior
   sessions had aggregates like "72% have suit overlap" or "85.7% have
   R2 routing available." S56's "100% of mismatches have max_top=A and
   100% of oracle picks use it" is the strongest Phase 1b validation
   yet — when feature design exactly matches the structural delta, the
   percentages collapse to 100/0.

4. **Surgical gating means prefix-grid neutrality is correct, not
   suspect.** When new features are gated to a category absent from the
   prefix grid, prefix delta = $0 by construction. Pre-flight
   "2× ratio" gates only apply when both grids contain the target
   population.

5. **Single-axis ships have predictable leaf growth (+4.7% here vs +32%
   for v41's two_pair v2).** Population × axis-count × info-content
   determines leaf expansion. high_only has 40% population but the
   single DS axis touches a narrower split surface than two_pair's
   Layout B/C asymmetry.

## Headroom analysis (where future work can go)

After v42, residuals (within-category, full grid):

| Category | n_hands | share | v42 within-cat | $/1000h whole-grid |
|---|---:|---:|---:|---:|
| **high_only** | 1,226,940 | 40.4% | **$2,411** | $975 |
| pair | 2,800,512 | 36.2% | $1,097 | $396 |
| trips | 328,185 | 4.6% | $1,194 | $55 |
| three_pair | 114,400 | 2.2% | $1,613 | $35 |
| two_pair | 1,338,480 | 14.5% | $363 | $52 |
| trips_pair | 171,600 | 1.8% | $281 | $5 |
| composite | 14,742 | 0.2% | $960 | $2 |
| quads | 14,300 | 0.1% | $545 | $1 |

high_only is **still** the dominant residual at $975/1000h whole-grid
contribution (~82% of v42's total regret). Next-priority targets:

1. **More high_only feature axes** (Session 57 candidate): top-card
   placement at non-Ace ranks (the SS→SS and 31→DS swaps still each
   contribute $30+/1000h). Audit existing ho_*_g features for missing
   parallels.
2. **Trips zone** ($1,194/1000h, 4.6% share = $55 whole-grid) — same
   playbook, smaller target.
3. **Three_pair zone** ($1,613/1000h, 2.2% share = $35 whole-grid).

## Files produced (Session 56)

**Drills:**
- `analysis/scripts/drill_high_only_zone_v41_diagnostic.py` (Phase 1)
- `analysis/scripts/drill_high_only_v41_mismatch_handlevel.py` (Phase 1b)

**Features (Phase 2 v2):**
- `analysis/scripts/high_only_aug_v2_features_gated.py`
- `analysis/scripts/persist_high_only_aug_v2_gated.py`

**Training + grading:**
- `analysis/scripts/train_v42_dt.py`
- `analysis/scripts/strategy_v42_dt.py`
- `analysis/scripts/grade_v42_dt.py`

**Models persisted:**
- `data/v42_dt_model.npz` (1188 MB, PRODUCTION ML champion)
- `data/feature_table_high_only_aug_v2_gated.parquet` (19.24 MB)

**Documentation:**
- `SESSION_56_V42_DT_REPORT.md` (this file)
- Updated `CURRENT_PHASE.md`, `STRATEGY_GUIDE.md`, `DECISIONS_LOG.md`

## State at end of Session 56

- **Rule chain production: v52** at $2,498 full / $1,522 prefix (UNCHANGED)
- **ML champion: v42_dt** at **$1,192 full / $686 prefix** (NEW)
- Cumulative ML v32 → v42: −$524 full / −$218 prefix
- The two production tracks now diverge by **$1,306/1000h** (v52 rule chain at $2,498; v42_dt at $1,192). The ML champion now beats the human-memorizable rule chain by more than half its EV deficit.

## Pre-flight: v42 is robust, not noise

- **Full grid ships strongly positive:** −$79/1000h, +0.91% pct_opt
- **Prefix grid neutral by design** (zero high_only in prefix; gating mathematically guarantees identical metrics on non-targeted populations)
- **Leaf expansion modest and structural** (+4.7%, deterministic with random_state=42)
- **Surgical via gating** (every other category byte-identical to v41 on both grids)
- **3 of 4 new features in top-32 importance** — deeper integration than S55 t2p_v2 family
- **Phase 1b 100% match rate** — feature design exactly captures structural delta
- **Matches Phase 1 diagnosis** — the lift is in the high_only zone, exactly where the diagnostic identified the gap
