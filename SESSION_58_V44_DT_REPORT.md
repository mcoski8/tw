# Session 58 — v44_dt new ML champion (+$42 full / $0 prefix) via high_only zone THIRD-PASS collapse

_Generated: 2026-05-10_

## TL;DR — HIGH_ONLY ZONE COLLAPSED ANOTHER 10.0% VIA 4 STRUCTURAL-AXIS FEATURES

The 4-phase playbook (drill → hand-level → 4 rank-valued conditional features → train) was applied for the **6th consecutive session** and the **3rd time on the same zone (high_only)**. Result: another **+$42/1000h on full grid**, all 7 non-targeted categories byte-identical (surgical gating confirmed).

**v44_dt replaces v43_dt as the ML champion.**

| Metric | v43_dt | v44_dt | Δ |
|---|---:|---:|---:|
| Full grid mean regret | 0.1123 | 0.1081 | **−0.0042** |
| Full grid $/1000h | $1,123 | **$1,081** | **−$42** |
| Full grid pct_opt | 63.99% | 64.80% | **+0.81%** |
| Prefix grid $/1000h | $686 | $686 | **$0 (by design)** |
| Prefix grid pct_opt | 67.13% | 67.13% | **$0 (by design)** |
| Leaves | 2,177,798 | 2,248,173 | **+3.2%** |
| Features | 103 | 107 | **+4 ho_v4** |
| Depth | 36 | 36 | saturated |

**Cumulative ML arc (v32 → v44):** **−$634/1000h on full grid across 9 ships** (v34: −$34, v36: −$33, v39: −$237, v40: −$18, v41: −$124, v42: −$79, v43: −$69, v44: −$42).

The ML champion now beats the rule chain (v52 at $2,498) by **$1,417/1000h** — more than half the rule-chain EV deficit.

## High_only zone collapse (the targeted gain)

| Stage | high_only within-cat | high_only pct_opt | Δ within-cat |
|---|---:|---:|---:|
| v41_dt (S55) | $2,796 | 29.0% | — |
| v42_dt (S56) | $2,411 | 33.4% | −$385 (−13.8%) |
| v43_dt (S57) | $2,075 | 37.9% | −$336 (−13.9%) |
| **v44_dt (S58)** | **$1,868** | **41.8%** | **−$207 (−10.0%)** |

Three-session cumulative collapse: $2,796 → $1,868 = **−$928 (−33.2%)** within-category, **−$378/1000h whole-grid contribution**.

## Per-category residuals (v44_dt, full grid)

| Category | n_hands | share | v44 within-cat | v43 within-cat | Δ |
|---|---:|---:|---:|---:|---:|
| **high_only** (S58 collapsed) | 1,226,940 | 40.4% | **$1,868** | $2,075 | **−$207** |
| pair | 2,800,512 | 36.2% | $1,097 | $1,097 | $0 |
| trips | 328,185 | 4.6% | $1,194 | $1,194 | $0 |
| two_pair | 1,338,480 | 14.5% | $363 | $363 | $0 |
| three_pair | 114,400 | 2.2% | $1,613 | $1,613 | $0 |
| trips_pair | 171,600 | 1.8% | $281 | $281 | $0 |
| composite | 14,742 | 0.2% | $960 | $960 | $0 |
| quads | 14,300 | 0.1% | $545 | $545 | $0 |

**All 7 non-high_only categories are BYTE-IDENTICAL to v43** — surgical gating worked exactly as designed.

## What the deep-dive (HO5–HO10) revealed

The user's S57 review asked: "what does oracle pick for its Omaha hand vs its Hold'em mid hand across every max-rank × structural cell? does it optimize Omaha first or Hold'em first?"

5 drills (HO5–HO10) on all 1.226M high_only hands surfaced four cross-cutting findings:

### Finding 1 — `DS_NO_JOINT` is the dominant residual cell (62.9% × every max-rank)

Across **every** max-rank, the `DS_NO_JOINT` cell (DS bot achievable with max-on-top, but no joint config exists with mid-suited) accounts for 62.9% of hands and roughly $293/1000h whole-grid summed (~69% of all high_only regret). Oracle picks DS bot 52–68% of the time in this cell; v43 picks SS bot 41–51% — a systematic **−10–20% under-routing of DS bot** in the largest cell.

The top mismatch class in the entire grid lives here:
* `tA_SS_mu → tA_DS_mu`: n=34,726 hands @ $4,336 mean = **$25.06/1000h whole-grid**.
* `tA_SS_mu → tA_SS_ms`: $23.07/1000h.
* `tA_SS_ms → tA_DS_mu`: $13.83/1000h.

### Finding 2 — Within JOINT picks, MID-FIRST dominates (mean mid_pct 0.67–0.81 >> bot_pct 0.24–0.36)

HO8 ranked oracle's chosen joint config among all candidate joint configs by bot pair_high (descending) and mid_high (descending) separately. Oracle's mean rank-percentile is consistently higher in the mid_high ordering than the bot_pair_high ordering — and the gap **widens at lower max-ranks** (A: gap 0.31; 8: gap 0.56). Oracle is mid-first within joint at every max-rank. v43 has `ho_v3_max_mid_high` already; the residual is in feature compositions, not new signals here.

### Finding 3 — Joint take-rate **collapses** at lower max-ranks (A:95% → 8:13%)

Oracle's joint take-rate (when joint is achievable):

| max | A | K | Q | J | T | 9 | 8 |
|---|---:|---:|---:|---:|---:|---:|---:|
| % takes joint | 94.8% | 85.9% | 75.7% | 53.8% | 35.9% | 22.3% | 13.3% |

At J/T/9/8, oracle increasingly chooses to **abandon joint** in favor of (top != max, DS bot, ms mid) configs — pushing the max-rank into the bot or mid as a suited pair, taking a low-rank top. v43's ho_v3 features only count joints with `top=max`, so this entire route is **invisible** to the model. HO10 found 47.7% of high_only hands have at least one such non-max-top joint achievable (consistent across every max-rank by suit symmetry).

### Finding 4 — At max=A, 4-flush + ms mid is the dominant alternative

When oracle skips joint at max=A (only 5% of joint-avail hands), 54% of those alts are `tmax_4f_ms` — top=A, 4-flush bot, suited mid. This is a structural axis with no v43 feature.

## The 4 new ho_v4 features (each gated to high_only)

```python
# analysis/scripts/high_only_aug_v4_features_gated.py
ho_v4_topMax_DS_max_bot_pair_high_g  0..13  # best higher-of-suited-pair
                                              # in DS bot when top=max
                                              # (DS_NO_JOINT discrimination)
ho_v4_topMax_4f_ms_max_mid_high_g    0..13  # best mid_high in (top=max,
                                              # 4-flush bot, ms mid) configs
                                              # (Ace-high 4f route)
ho_v4_topNonMax_DS_ms_n_configs_g    0..30  # count of (top!=max, DS bot,
                                              # ms mid) joint configs where
                                              # max-rank is in bot or mid
ho_v4_topNonMax_DS_ms_max_top_rank_g 0..13  # best non-max top rank
                                              # achievable in those joints
```

Each targets a distinct structural axis surfaced by HO5–HO10 (Finding 1, 4, 3, 3).

## Feature importance — LOW BUT SHIPPING (5th consecutive session)

| Rank | Feature | Importance |
|---:|---|---:|
| #47 | `ho_v4_topNonMax_DS_ms_max_top_rank_g` | 0.13% |
| #80 | `ho_v4_topMax_DS_max_bot_pair_high_g` | 0.04% |
| #93 | `ho_v4_topMax_4f_ms_max_mid_high_g` | 0.01% |
| #95 | `ho_v4_topNonMax_DS_ms_n_configs_g` | 0.01% |

The non-max-top joint *quality* feature (`max_top_rank_g`) ranked notably higher than the count feature — suggesting the DT splits on "how strong the alternative top can be" more than "how many alternative joints exist." This matches Finding 3's intuition that route quality, not abundance, drives the swap.

The 4f and DS bot pair_high features rank low globally (target narrower populations) but contribute via surgical routing on the high-leverage `DS_NO_JOINT` cell. Methodology rule (S55) confirmed for the 5th time: **low individual importance can still ship lift via surgical gating on high-leverage subsets**.

## Pre-flight checks

- **Full grid ships strongly positive**: −$42/1000h, +0.81% pct_opt
- **Prefix grid neutral by design** (zero high_only hands in prefix slice; gating mathematically guarantees identical metrics on non-targeted populations)
- **All 7 non-high_only categories byte-identical** (pair, two_pair, trips, three_pair, trips_pair, quads, composite — every $/1000h matches v43 exactly)
- **Leaf expansion modest** (+3.2%, similar to v43's +3.2% over v42)
- **High_only pct_opt jumps +3.9%** (37.9% → 41.8%) — the targeted population improved
- **Decision matrix delivered** (`SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` at repo root) — answers the user's S57 review question independent of whether v44 shipped

## Methodology lessons (Session 58)

1. **The 4-phase playbook is transferable to the SAME zone for a THIRD pass.** Re-drilling against the new champion (v43, post-S57 collapse) revealed the residual had shifted in axis (DS+ms joint → DS bot quality + non-max-top joint + 4f route) without changing in dominant zone. Same playbook applied without modification.

2. **A zone can be collapsed at least three times by stacking conditional feature axes.** S56 (ho_v2 DS-only) + S57 (ho_v3 DS+ms joint) + S58 (ho_v4 DS quality + non-max joint + 4f) compose: 3-session cumulative collapse = −$928 within-category (−33.2%). Each pass adds a NEW conditional axis to the same zone.

3. **Decision matrix is a separable deliverable from the ML ship.** Even if v44 had not shipped, the `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` would document Oracle's structural strategy across 7 max-ranks × 7 structural cells — answering the user's review question on its own terms.

4. **Drills can share the per-hand sweep.** HO5+HO6+HO7 ran as one consolidated script (482s total, 2.5K hands/s). HO8 ran independently (24s, structural-only). HO10 ran independently (55s, pure enumeration). HO9 read the parquet from HO5+HO6+HO7. Total drill compute: ~10 min wall time across 5 drills — well within the overnight budget.

5. **Mid-first within joint is a robust pattern; bot-first becomes correct OUTSIDE joint at lower max-ranks.** The user's question "Omaha first or Hold'em first?" has a nuanced answer: WITHIN joint, oracle is mid-first (mid_high preferred over bot pair_high); OUTSIDE joint at lower max-ranks, oracle becomes bot-first (puts max-rank into the bot for a stronger DS configuration with a lower top).

## Files (Session 58)

**Drills:**
- `analysis/scripts/drill_high_only_v43_deepdive.py` (HO5+HO6+HO7 consolidated)
- `analysis/scripts/drill_high_only_v43_bot_vs_mid.py` (HO8)
- `analysis/scripts/drill_high_only_v43_threshold.py` (HO9)
- `analysis/scripts/drill_high_only_v43_nonmax_joint.py` (HO10 supplementary)

**Features:**
- `analysis/scripts/high_only_aug_v4_features_gated.py` (PRODUCTION)
- `analysis/scripts/persist_high_only_aug_v4_gated.py`

**Training + grading:**
- `analysis/scripts/train_v44_dt.py` + `strategy_v44_dt.py` + `grade_v44_dt.py`

**Models:**
- `data/v44_dt_model.npz` (1260 MB, PRODUCTION — NEW ML CHAMPION)
- `data/feature_table_high_only_aug_v4_gated.parquet` (19.04 MB)
- `data/drill_ho_v43_per_hand_structural.parquet` (15.0 MB; reusable for future high_only drills)
- `data/drill_ho_v43_nonmax_joint.parquet` (4.7 MB; supplementary)

**Documentation:**
- `SESSION_58_V44_DT_REPORT.md` (this file)
- `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` (per-max-rank × per-cell oracle decision rules; the user's S57 review answer)
- `STRATEGY_GUIDE.md` Part 1 — Session 58 entry; Part 2 ML champion table updated
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 093 appended
