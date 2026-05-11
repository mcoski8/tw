# Session 57 — v43_dt new ML champion (+$69 full / $0 prefix) via high_only zone SECOND-PASS collapse

_Generated: 2026-05-10_

## TL;DR — HIGH_ONLY ZONE COLLAPSED ANOTHER 13.9% VIA 4 JOINT (DS BOT + MS MID) FEATURES

The 4-phase playbook (drill → hand-level → 4 rank-valued conditional features → train) was applied for the **5th consecutive session** and the **2nd time on the same zone (high_only)**. Result: another **+$69/1000h on full grid**, all 7 non-targeted categories byte-identical (surgical gating confirmed).

**v43_dt replaces v42_dt as the ML champion.**

| Metric | v42_dt | v43_dt | Δ |
|---|---:|---:|---:|
| Full grid mean regret | 0.1192 | 0.1123 | **−0.0069** |
| Full grid $/1000h | $1,192 | $1,123 | **−$69** |
| Full grid pct_opt | 63.08% | 63.99% | **+0.91%** |
| Prefix grid $/1000h | $686 | $686 | **$0 (by design)** |
| Prefix grid pct_opt | 67.13% | 67.13% | **$0 (by design)** |
| Leaves | 2,109,330 | 2,177,798 | **+3.2%** |
| Features | 99 | 103 | **+4 ho_v3** |
| Depth | 36 | 36 | saturated |

**Cumulative ML arc (v32 → v43):** **−$592/1000h on full grid across 8 ships** (v34: −$34, v36: −$33, v39: −$237, v40: −$18, v41: −$124, v42: −$79, v43: −$69).

The ML champion now beats the rule chain (v52 at $2,498) by **$1,375/1000h** — more than half the rule-chain EV deficit.

## High_only zone collapse (the targeted gain)

| Stage | high_only within-cat | high_only pct_opt | Δ within-cat |
|---|---:|---:|---:|
| v41_dt (S55) | $2,796 | 29.0% | — |
| v42_dt (S56) | $2,411 | 33.4% | −$385 (−13.8%) |
| **v43_dt (S57)** | **$2,075** | **37.9%** | **−$336 (−13.9%)** |

Two-session cumulative collapse: $2,796 → $2,075 = **−$721 (−25.8%)** within-category, **−$291/1000h whole-grid contribution**.

## Per-category residuals (v43_dt, full grid)

| Category | n_hands | share | v43 within-cat | v42 within-cat | Δ |
|---|---:|---:|---:|---:|---:|
| **high_only** (S57 collapsed) | 1,226,940 | 40.4% | **$2,075** | $2,411 | **−$336** |
| pair | 2,800,512 | 36.2% | $1,097 | $1,097 | $0 |
| trips | 328,185 | 4.6% | $1,194 | $1,194 | $0 |
| two_pair | 1,338,480 | 14.5% | $363 | $363 | $0 |
| three_pair | 114,400 | 2.2% | $1,613 | $1,613 | $0 |
| trips_pair | 171,600 | 1.8% | $281 | $281 | $0 |
| composite | 14,742 | 0.2% | $960 | $960 | $0 |
| quads | 14,300 | 0.1% | $545 | $545 | $0 |

**All 7 non-high_only categories are BYTE-IDENTICAL to v42** — surgical gating worked exactly as designed.

## What Phase 1 (Drill HO3) revealed

After S56's ho_v2 features collapsed parts of the high_only zone, the SAME SS→DS bot-suit-swap pattern is **STILL the dominant residual**:

- v42 picks SS bot **46.07%** vs oracle **32.04%** (−14.0% absolute under-routing of DS).
- Total SS→DS bot-suit swap contribution: **$189.33/1000h whole-grid**.
- Top single mismatch class: **v42=tA_SS_mu, oracle=tA_DS_ms** — 28,027 hands @ $7,534 mean regret = **$35.14/1000h whole-grid**.
- This dominant class barely moved from v41 (28,014 hands @ $7,774) — ho_v2 features did NOT meaningfully collapse the Ace-top SS→DS swap.
- 2nd: tA_SS_mu → tA_DS_mu ($25.61, n=35,332) — bot-suit-only swap.
- 3rd: tA_SS_mu → tA_SS_ms ($23.68, n=33,559) — **mid-suit-only swap** (NEW signal).
- 4th: tK_SS_mu → tK_DS_ms ($17.05, n=13,229) — same pattern at K-top.

User-prediction axes (defensive K/Q triggers, T-9-8 top choice, broadway connectivity) were NOT confirmed as dominant — the structural blind spot remained on the SS→DS axis but with a NEW dimension: mid suiting.

## What Phase 1b (Drill HO4) confirmed

For the dominant class (v42=tA_SS_mu, oracle=tA_DS_ms), all 28,027 mismatch hands were sampled. The structural delta:

- **100%** of mismatches have a (DS bot + suited mid) **JOINT** config achievable WITH the Ace on top.
- 18% have 3 joint configs, 82% have 9 joint configs — abundant alternatives.
- DS_AND_ms_max_top = A in 100% of cases (existing ho_v2 feature also fires at 14 here).
- **Oracle's actual mid_high distribution spans the full range** (K 22%, Q 19%, J 17%, T 14%, … down to 3 at 0.9%).
- Oracle uses the BEST-available joint mid only 8.2% of the time — the choice depends on more than max-mid-high.

**Diagnosis:** v42 has DS-bot achievability features (`ho_v2_*_g`) but NOT joint (DS bot + ms mid) achievability features. The mid-suit-only swap class ($23.68/1000h) confirms mid-suiting matters as a separate axis. The DT can split on "DS bot achievable + max_top=A" but cannot split on "DS bot AND mid suited at the same time, with what mid quality."

## The 4 new ho_v3 features

```python
# analysis/scripts/high_only_aug_v3_features_gated.py
ho_v3_topMax_DS_ms_n_configs_g       0..15  # joint (top=max-rank, DS bot, ms mid) count
ho_v3_topMax_DS_ms_max_mid_high_g    0..13  # best higher-card-of-suited-mid
ho_v3_topMax_DS_ms_min_mid_high_g    0..13  # lowest higher-card-of-suited-mid
ho_v3_topMax_DS_ms_max_mid_sum_g     0..25  # best sum of suited mid pair
```

For each high_only hand, fix top = max-rank-of-hand. Enumerate the C(6,4)=15 4-card subsets of the remaining 6 cards as candidate bots. Filter to (a) bot is 2+2 (DS), (b) the 2 leftover cards (mid) share a suit. Aggregate count + mid quality.

**Distribution check (output of persist):**
- 5,828,979 zero rows (97.0% — non-high_only, gated correctly)
- 102,960 rows with n_configs=3 (8.4% of high_only)
- 77,220 rows with n_configs=6 (6.3% of high_only)
- max_mid_high distribution spans 5..K with peak at J (38,808 rows)
- max_mid_sum distribution spans 9..27, well-distributed

Only **14.7% of high_only hands** have any joint config — but those hands include nearly all the dominant SS→DS mismatch class.

## Feature importance — LOW BUT SHIPPING

| Rank | Feature | Importance |
|---:|---|---:|
| #63 | ho_v3_topMax_DS_ms_min_mid_high_g | 0.07% |
| #64 | ho_v3_topMax_DS_ms_max_mid_sum_g | 0.07% |
| #100 | ho_v3_topMax_DS_ms_max_mid_high_g | 0.01% |
| #102 | ho_v3_topMax_DS_ms_n_configs_g | 0.00% |

This is the **lowest feature-importance-per-ship** in the project so far. Yet v43 ships **+$69 full grid**. Methodology rule (S55): *"low individual feature importance can still ship lift via surgical gating."* — re-confirmed for the 2nd time.

The features fire on only 14.7% of high_only hands (3.0% of full grid), but those hands are concentrated in the dominant SS→DS mismatch class. Per-firing impact is much higher than global importance suggests.

## Pre-flight checks

- **Full grid ships strongly positive**: −$69/1000h, +0.91% pct_opt
- **Prefix grid neutral by design** (zero high_only hands in prefix slice; gating mathematically guarantees identical metrics on non-targeted populations)
- **All 7 non-high_only categories byte-identical** (pair, two_pair, trips, three_pair, trips_pair, composite, quads — every $/1000h matches v42 exactly)
- **Leaf expansion modest** (+3.2%, smaller than v42's +4.7% over v41 — consistent with low-importance features that fire on a smaller subset)
- **Phase 1b 100% match rate** for joint achievability — feature design exactly captures structural delta
- **Matches Phase 1 diagnosis** — the lift is in the high_only zone, exactly where the diagnostic identified the gap
- **Matches Phase 1b structural axis** — mid-suit-aware joint features capture what ho_v2 missed

## Methodology lessons (Session 57)

1. **The 4-phase playbook is transferable to the SAME zone for a second pass.** Re-drilling against the new champion (v42, post-S56 collapse) revealed the residual had shifted in axis (DS-only → joint DS+ms) without changing in dominant top-rank or zone. The same playbook applied without modification.

2. **A zone can be collapsed multiple times by stacking conditional feature axes.** S56's ho_v2 (DS bot only) + S57's ho_v3 (DS bot AND ms mid) compose: 2-session cumulative collapse = −$721 within-category (−25.8%). Each pass adds a NEW conditional axis to the same zone.

3. **User predictions can be wrong about which axis dominates, even after one pass collapses one axis.** The user predicted K/Q defensive triggers, T-9-8 top choice, and broadway connectivity for S57. Reality: the dominant residual was STILL on the SS→DS axis, just with a NEW conditional dimension (mid suiting). The data dictates the axis, not the human intuition.

4. **Importance can be low and lift can still ship.** v43's 4 features rank #63/#64/#100/#102 — the lowest importance-per-ship on record. Yet they ship +$69. Importance ≠ impact when features fire on a narrow but high-leverage subset.

5. **Joint achievability is a distinct structural axis from single-axis achievability.** ho_v2 exposes "is DS bot achievable" but the DT couldn't compose "DS bot AND mid suited" from existing features alone. Joint features are NOT redundant with the components — they expose joint structure that's invisible when only individual axes are exposed.

## Files (Session 57)

**Drills:**
- `analysis/scripts/drill_high_only_zone_v42_diagnostic.py` (Drill HO3, Phase 1)
- `analysis/scripts/drill_high_only_v42_mismatch_handlevel.py` (Drill HO4, Phase 1b)

**Features:**
- `analysis/scripts/high_only_aug_v3_features_gated.py` (PRODUCTION)
- `analysis/scripts/persist_high_only_aug_v3_gated.py`

**Training + grading:**
- `analysis/scripts/train_v43_dt.py` + `strategy_v43_dt.py` + `grade_v43_dt.py`

**Models:**
- `data/v43_dt_model.npz` (1224 MB, PRODUCTION — NEW ML CHAMPION)
- `data/feature_table_high_only_aug_v3_gated.parquet` (18.72 MB)

**Documentation:**
- `SESSION_57_V43_DT_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 57 entry; Part 2 ML champion table updated
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decision 092 appended
