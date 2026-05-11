# Current: Sprint 8 — Session 57 ships **v43_dt as the new ML champion via the user-priority high_only zone SECOND-PASS collapse, applying the proven 4-phase playbook (drill → hand-level → 4 rank-valued conditional features → train) for the 5th consecutive session and the 2nd time on the SAME zone**. v42_dt → v43_dt: **$1,192 → $1,123 full / $686 → $686 prefix**. **High_only within-category $2,411 → $2,075 (−$336, −13.9%)**, pct_opt 33.4% → 37.9% (+4.5%). All 7 non-targeted categories byte-identical to v42 on both grids (surgical gating). Leaf count v43: 2.11M → 2.18M (+3.2%). Depth saturated at 36. Four new features: rank-valued `ho_v3_topMax_DS_ms_*_g` series encoding JOINT (DS bot + ms mid) achievability + quality conditional on top=max-rank-of-hand — total 103 features (95 base + 4 ho_v2 + 4 ho_v3). All 4 features at LOW individual importance: #63 min_mid_high (0.07%), #64 max_mid_sum (0.07%), #100 max_mid_high (0.01%), #102 n_configs (0.00%) — **lowest-importance-per-ship in project**. Cumulative v32 → v43 = **−$592 full / −$218 prefix** (8 ML ships). Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). The ML champion now beats the rule chain by **$1,375/1000h** (more than half the rule-chain EV deficit). **Two-session high_only collapse (S55 → S57): $2,796 → $2,411 → $2,075 = −$721 within-cat (−25.8%)** — composing two conditional axes (ho_v2 DS-only + ho_v3 DS+ms-joint) compresses the same zone twice without surgical interference. Phase 1 surfaced the counterintuitive finding: after S56 the SAME SS→DS pattern STILL dominates the residual, just with a NEW dimension (mid suiting); user-prediction axes (defensive K/Q triggers, T-9-8 top choice, broadway connectivity) were NOT confirmed. Phase 1b confirmed 100% of dominant-class mismatches have a (DS bot + ms mid) joint config achievable WITH the Ace on top. Methodology validation: **the playbook is transferable to the SAME zone for a SECOND pass, and joint-achievability features are a distinct structural axis from single-axis achievability features.** Surgical gating mathematically guarantees prefix-grid neutrality when the prefix slice contains zero target-zone hands.

> **🎯 IMMEDIATE NEXT ACTION (Session 58): EXHAUSTIVE high_only deep-dive — characterize WHAT oracle picks for Omaha (bot) vs Hold'em (mid) across EVERY max-rank × structural-achievability cell, then design ho_v4 from the deepest residual axis revealed.**
>
>   **Why this — the user's S57 review.** The S57 ship (ho_v3 joint features) is real lift but only at the *aggregate* level — it tells the DT "there exists a way to do DS-bot AND ms-mid with the Ace on top." It does NOT explain *what oracle is actually optimizing for* in each (top, bot, mid) configuration. Specifically the user wants to know:
>   1. **When v43 picks `DS+ms` correctly, what is it actually choosing for the bot vs the mid?** Does it pick the highest-rank suited mid pair? The most-connected bot? Both? What about *trade-offs* between bot strength and mid strength when the joint config exists but at uneven quality?
>   2. **Does oracle optimize Omaha (bot) FIRST and then take whatever mid is left? Or Hold'em (mid) FIRST and then take whatever bot is left? Or jointly?** If it's joint, what's the implicit *exchange rate* between bot rank/connectivity and mid rank/connectivity?
>   3. **Does oracle prioritize HIGHER cards in the bot, or HIGHER connectivity in the bot?** (Omaha values both, but they're competing in many 7-card hands — when forced to choose, which wins?)
>   4. **What about edge cases**: Ace-high hands where DS is achievable BUT mid would be "random crap" (low max_mid_high) — does oracle still take DS+ms, or fall back to SS_ms (single-suit bot but a strong suited mid), or DS_mu (DS bot, mid unsuited but high)?
>   5. **Same exhaustive analysis for K-high, Q-high, J-high, T-high, 9-high, 8-high.** Each max-rank class likely has its own optimization trade-off — defensive triggers, mid-vs-bot priority, connectivity weights — and we have NO unified picture of what those are.
>
>   **The deep-dive plan (5 drills, 1 feature module, 1 ship; should take an overnight session at most):**
>
>   ### Drill HO5 — per-max-rank residual stratification
>
>   Sweep all 1,226,940 high_only hands. For each max_rank ∈ {A, K, Q, J, T, 9, 8}:
>   - Total v43 vs oracle mismatch contribution ($/1000h whole-grid).
>   - Top-10 mismatch classes (v43_pick → oracle_pick).
>   - Distribution of v43 picks (top×bot×mid) vs oracle picks.
>   - pct_opt within max-rank class.
>
>   Expected output: a per-max-rank table that shows where the residual concentrates after v43. Likely K-high and Q-high move up the ranking now that A-high SS→DS is compressed.
>
>   ### Drill HO6 — full structural achievability cross-tabulation
>
>   For each high_only hand, compute these 8 boolean/count signals:
>   1. `n_DS_bot_configs` (count of 4-card subsets of all 7 that are 2+2)
>   2. `n_DS_bot_with_max_on_top` (DS configs where max-rank is in leftover, not bot)
>   3. `n_ms_mid_configs` (count of (top, mid_pair) splits where mid 2 cards share suit)
>   4. `n_ms_mid_with_max_on_top` (subset with max-rank as top)
>   5. `n_joint_DS_ms_max_top_configs` (the ho_v3 count: all three together)
>   6. `best_DS_bot_pair_high` (max higher-card-of-suited-pair across DS configs)
>   7. `best_ms_mid_high` (max higher-card-of-suited-mid across ms-mid configs)
>   8. `bot_mid_quality_corr` (in joint configs, does best_bot_pair coincide with best_mid_pair? or are they competing?)
>
>   Stratify by max_rank. Cross-tabulate. Identify cells where the joint is achievable but at *uneven* quality (high bot, low mid, OR low bot, high mid — the trade-off cases).
>
>   ### Drill HO7 — what oracle ACTUALLY picks (per max_rank × structural cell)
>
>   For each (max_rank × structural-achievability) cell from Drill HO6, characterize the oracle's pick:
>   - **TOP**: rank distribution (always max? sometimes 2-on-top defensive? second-highest?)
>   - **BOT**: ranks present (sum, max, min), suit profile (DS/SS/RB/31/4f), connectivity (longest run within the bot's 4 cards), suit-pair high cards.
>   - **MID**: ranks present (sum, max, min), suit-match (ms/mu), connectivity.
>
>   Then compare against v43's pick per-cell. The DELTA between oracle and v43 in bot vs mid choices reveals what v43 is missing.
>
>   ### Drill HO8 — Omaha-first vs Hold'em-first vs joint
>
>   The discriminating question: when oracle picks (bot, mid), is it:
>   - **Omaha-first**: pick the strongest possible bot (DS + highest pair-high + best connectivity); take whatever mid + top are left.
>   - **Hold'em-first**: pick the strongest possible mid (suited + highest pair); take whatever bot is left.
>   - **Joint-optimal**: balance bot strength against mid strength via some implicit rate.
>
>   Test by:
>   1. For each oracle-picked hand, enumerate ALL alternative (bot, mid) splits with the same top.
>   2. Rank by bot strength only, by mid strength only, and by an EV-weighted joint.
>   3. Where does oracle's pick fall? Top of bot-only ranking? Top of mid-only? Top of joint?
>
>   Hypothesis: oracle is closer to "bot-first" than "mid-first" because Omaha pays 3 points/board vs Hold'em mid 2 points/board. But the magnitude matters and may flip in specific cells (e.g., low-rank bot with high-rank suited mid).
>
>   ### Drill HO9 — edge-case "trade-off" enumeration
>
>   The user's specific question: when DS is achievable BUT mid is crap, what does oracle pick?
>   - Stratify hands where best_ms_mid_high (in joint configs) ≤ T (i.e., the suited mid would be a low pair).
>   - Compare: oracle DS+low_ms_mid vs SS_ms+higher_mid vs DS_mu+highest_mid vs other.
>   - Per max-rank, quantify the break-even point: at what mid_high threshold does oracle switch from DS+ms to SS+ms?
>
>   Same for: when SS is achievable but mid would be high suited vs DS achievable but mid is low suited — at what point does the bot upgrade matter more than the mid downgrade?
>
>   ### Phase 2 v4 design — based on Drill HO5–HO9 findings
>
>   Most likely outcomes (rank by probability):
>   1. **Trade-off-aware joint feature**: 4 features that encode "DS+ms achievable AND mid_high ≥ threshold" + "SS+ms with mid_high ≥ threshold" + "second-best joint config quality" — explicit alternative-comparison features.
>   2. **Per-max-rank-class joint features**: 4 features that fire only at K/Q/J max-rank and encode the same joint pattern as ho_v3 but with different trade-off weights.
>   3. **Bot-vs-mid priority signal**: a feature like "ratio of best_DS_bot_quality to best_ms_mid_quality" that exposes the trade-off directly.
>   4. **Defensive-2-on-top features**: if Drill HO5 reveals defensive-top mismatches dominate at K/Q max, build features that encode "defensive top achievable + with what bot/mid quality."
>
>   Pick the 4 features that target the LARGEST residual cell from the drills.
>
>   ### Train v44_dt
>
>   depth=36 ml=1, 107 features = 103 + 4 ho_v4. Same surgical-gating discipline. Acceptance: −$30/1000h or better on full grid + all non-high_only categories byte-identical.
>
>   **Alternative if Drill HO5–HO9 reveal nothing actionable** (unlikely given 75% of regret is still in high_only): trips zone ($55/1000h whole-grid) or three_pair ($35/1000h). But high_only should still have real lift — the analysis itself will reveal the next axis.
>
>   **Time budget**: this is a 5-drill investigation. Each drill is ~6 min on the full grid (per Session 57's drills). Total drill time ≈ 30 min + analysis between phases. Feature design + persist + train + grade ≈ 30 min. Total session ≈ 1.5–2 hours of compute, plus thinking time. Suitable for an overnight session.
>
>   **Diagnostic deliverable** (regardless of whether v44_dt ships): produce a **per-max-rank decision matrix** showing what oracle picks for top, bot (Omaha), and mid (Hold'em) under every structural-achievability cell. This is the "exhaustive characterization" the user wants AND it directly informs all future high_only feature work.

> **✅ NEW SHIPS (Session 57):**
> 1. **v43_dt** replaces v42_dt as ML champion. **+$69 full / $0 prefix.** High_only zone collapse from $2,411 → $2,075 (−13.9%). Prefix neutrality is by design — prefix slice has zero high_only hands and the new features are gated.
> 2. **Cumulative session +$69 full / $0 prefix.** New feature suite fully orthogonal — surgical gating preserves all other categories byte-identical on both grids.

> **🔬 ARTIFACTS (Session 57):**
> 1. **`analysis/scripts/drill_high_only_zone_v42_diagnostic.py`** — Drill HO3 (Phase 1)
> 2. **`analysis/scripts/drill_high_only_v42_mismatch_handlevel.py`** — Drill HO4 (Phase 1b)
> 3. **`analysis/scripts/high_only_aug_v3_features_gated.py`** + persist — PRODUCTION rank-valued JOINT features for high_only
> 4. **`analysis/scripts/train_v43_dt.py`** + `strategy_v43_dt.py` + `grade_v43_dt.py` — ship
> 5. **`data/v43_dt_model.npz`** (1224 MB) — PRODUCTION ML champion
> 6. **`data/feature_table_high_only_aug_v3_gated.parquet`** (18.72 MB) — persisted feature table
> 7. **`SESSION_57_V43_DT_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 57 NEW):**
> - **The 4-phase playbook is transferable to the SAME zone for a SECOND pass.** Re-drilling against the new champion (v42, post-S56 collapse) revealed the residual had shifted in axis (DS-only → joint DS+ms) without changing in dominant top-rank or zone. Same playbook applied without modification.
> - **A zone can be collapsed multiple times by stacking conditional feature axes.** Two-session high_only collapse: $2,796 → $2,411 → $2,075 = −$721 within-cat (−25.8%). Each pass adds a NEW conditional axis; gains compound surgically because the gating keeps non-targeted categories untouched.
> - **Joint achievability is a distinct structural axis from single-axis achievability.** ho_v2 exposes "is DS bot achievable" but the DT couldn't compose "DS bot AND mid suited" from existing features alone. Joint features are NOT redundant with the components — they expose joint structure invisible when only individual axes are exposed.
> - **Importance can be low and lift can still ship.** v43's 4 features at #63/#64/#100/#102 individual importance is the lowest-per-ship on record, yet they ship +$69. Importance ≠ impact when features fire on a narrow but high-leverage subset (3.0% of full grid for ho_v3).
> - **User predictions can be wrong about WHICH axis dominates, even after one pass collapses one axis.** The user predicted K/Q defensive triggers, T-9-8 top choice, and broadway connectivity for S57. Reality: the dominant residual was STILL on the SS→DS axis, just with a NEW conditional dimension (mid suiting). The data dictates the axis, not the human intuition.

> Updated: 2026-05-10 (Session 57)

---

## Headline state at end of Session 57

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED from S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v43_dt** | **NEW ML champion (Session 57).** 2.18M leaves, 103 features at depth=36 ml=1; +$69 full / $0 prefix vs v42_dt. | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v42_dt | Predecessor ML champion (S56). 2.11M leaves, 99 features. | `analysis/scripts/strategy_v42_dt.py` + `data/v42_dt_model.npz` |
| v41_dt | S55 ML champion. 2.02M leaves, 95 features. | `analysis/scripts/strategy_v41_dt.py` + `data/v41_dt_model.npz` |
| v40_dt | S55 first ship; replaced within-session. 1.57M leaves, 91 features. | `analysis/scripts/strategy_v40_dt.py` + `data/v40_dt_model.npz` |
| v39_dt | S54 ML champion. 1.52M leaves, 87 features. | `analysis/scripts/strategy_v39_dt.py` + `data/v39_dt_model.npz` |
| v36_dt | Older ML champion (S53 overnight; 1.06M leaves; $1,649). | `analysis/scripts/strategy_v36_dt.py` + `data/v36_dt_model.npz` |
| v34_dt | Older ML champion (874K leaves; $1,681). | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v47_rule16_Qhigh_DS / v46_rule15_Khigh_DS / v45_rule14_Ahigh_DS | Predecessor rule chains. | various |
| v44_rule13_three_pair_DS / v43_rule12 / v42 / v41 / v40b | Earlier rule chains. | various |
| v32_dt | Older ML baseline. | various |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines. | various |

**Capacity + feature progression — NEW v43 ML champion:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h full | pct_opt full |
|---|---:|---:|---:|---:|---:|---:|
| v32 | 32 | 3 | 83 | 731,606 | $1,715 | 50.86% |
| v34 | 34 (33 actual) | 2 | 83 | 874,548 | $1,681 | 52.02% |
| v36 | 36 (33 actual) | 1 | 83 | 1,064,442 | $1,649 | 53.61% |
| v39 | 36 | 1 | 87 (83+4 pair_v5) | 1,518,368 | $1,412 | 57.88% |
| v40 | 36 | 1 | 91 (87+4 tp_v2) | 1,569,848 | $1,394 | 58.48% |
| v41 | 36 | 1 | 95 (91+4 t2p_v2) | 2,015,413 | $1,270 | 62.18% |
| v42 | 36 | 1 | 99 (95+4 ho_v2) | 2,109,330 | $1,192 | 63.08% |
| **v43** | **36** | **1** | **103 (99+4 ho_v3)** | **2,177,798** | **$1,123** | **63.99%** |

**Cumulative ML arc (v32 → v43):** **−$592/1000h on full grid across 8 ships** (v34: −$34, v36: −$33, v39: −$237, v40: −$18, v41: −$124, v42: −$79, v43: −$69).

**Per-category residuals (within-category, full grid) — END OF SESSION 57:**

| Category | n_hands | share | v43 within-cat | $/1000h whole-grid | Δ vs v42 |
|---|---:|---:|---:|---:|---:|
| **high_only** (S57 collapsed) | 1,226,940 | 40.4% | **$2,075** | $838 | **−$336** |
| pair | 2,800,512 | 36.2% | $1,097 | $396 | $0 |
| trips | 328,185 | 4.6% | $1,194 | $55 | $0 |
| two_pair | 1,338,480 | 14.5% | $363 | $52 | $0 |
| three_pair | 114,400 | 2.2% | $1,613 | $35 | $0 |
| trips_pair | 171,600 | 1.8% | $281 | $5 | $0 |
| composite | 14,742 | 0.2% | $960 | $2 | $0 |
| quads | 14,300 | 0.1% | $545 | $1 | $0 |

**high_only is STILL by far the dominant residual** ($838/1000h whole-grid = ~75% of total v43 regret). Session 58's highest-leverage target — but now needs a THIRD axis (DS-only and DS+ms-joint axes are both collapsed; the residual lives in K/Q-top mismatches, mid-suit-only at non-Ace ranks, defensive triggers, broadway connectivity, etc.).

**Two-session high_only progression:** $2,796 → $2,411 → $2,075 = −$721 within-category (−25.8%) over Sessions 56–57. Each session compressed the zone via a different conditional axis.

**Human-strategy progression — UNCHANGED from end of S53:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v33_rule6_trips (+ Rule 6 v1) | $2,920 | 40.68% | −$113 |
| v37_rule7_three_pair (+ Rule 7) | $2,877 | 41.02% | −$156 |
| v38_rule8_qp (+ Rule 8) | $2,868 | 41.07% | −$165 |
| v39_rule9 (+ Rule 9 a/b/c) | $2,846 | 41.17% | −$187 |
| v40b_rule10_gated (+ Rule 10) | $2,798 | 41.48% | −$235 |
| v41_rule10_v3_ds (+ Rule 10 v3) | $2,769 | 41.91% | −$264 |
| v42_rule11_jpair_pbot_ds (+ Rule 11) | $2,763 | 41.93% | −$270 |
| v43_rule12_two_pair_DS_intact (+ Rule 12) | $2,727 | 42.20% | −$306 |
| v44_rule13_three_pair_DS (+ Rule 13) | $2,717 | 42.34% | −$316 |
| v45_rule14_Ahigh_DS (+ Rule 14) | $2,585 | 43.05% | −$448 |
| v46_rule15_Khigh_DS (+ Rule 15) | $2,534 | 43.24% | −$499 |
| v47_rule16_Qhigh_DS (+ Rule 16) | $2,515 | 43.30% | −$518 |
| **v52_full_high_only_handler (+ Rule 17) — CURRENT PRODUCTION** | **$2,498** | **43.34%** | **−$535** |

**The two production tracks now diverge by $1,375/1000h** (v52 rule chain at $2,498; v43_dt at $1,123). The ML champion beats the human-memorizable rule chain by more than half its EV deficit.

---

## What Session 57 produced

**Code:**
- 2 drills (1 Phase 1 + 1 Phase 1b)
- 1 feature module (high_only_v3) + 1 persistence script
- 1 trainer (v43) + 1 strategy + 1 grader

**Documentation:**
- `STRATEGY_GUIDE.md` — Part 1 Session 57 entry; Part 2 ML champion table updated; Part 6 ML champion paragraph updated; front-matter "Last updated" line refreshed
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 092 appended
- `SESSION_57_V43_DT_REPORT.md` — repo-root standalone report

**Models persisted:**
- `data/v43_dt_model.npz` (PRODUCTION ML champion)
- `data/feature_table_high_only_aug_v3_gated.parquet`

---

## Resume Prompt (Session 58 — overnight, autonomous)

```
Resume Session 58 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 57)
- DECISIONS_LOG.md (latest: Decision 092 — v43_dt new ML champion)
- SESSION_57_V43_DT_REPORT.md
- STRATEGY_GUIDE.md (Session 57 entry in Part 1; updated ML champion
  table in Part 2)
- analysis/scripts/strategy_v43_dt.py — current ML champion
- analysis/scripts/high_only_aug_v3_features_gated.py — ho_v3 JOINT
  feature template (most-relevant prior art)
- analysis/scripts/drill_high_only_zone_v42_diagnostic.py — Phase 1
  drill template (per-cell mismatch matrix)
- analysis/scripts/drill_high_only_v42_mismatch_handlevel.py — Phase 1b
  drill template (hand-level inspection)
- analysis/scripts/high_only_aug_v2_features_gated.py — ho_v2 single-axis
  template (DS-only)

State (end of Session 57):
- Rule chain production: v52_full_high_only_handler (17 rules; UNCHANGED)
  at $2,498 full / $1,522 prefix.
- ML champion: v43_dt (NEW) at $1,123 full / $686 prefix; 2.18M leaves
  at depth=36 ml=1; 103 features (95 base + 4 ho_v2 + 4 ho_v3 JOINT).
- Cumulative ML v32 → v43 = −$592 full / −$218 prefix (8 ML ships).
- High_only collapsed twice: $2,796 → $2,411 → $2,075 (−$721 / −25.8%).
- High_only is STILL the dominant residual at $838/1000h whole-grid
  (~75% of v43's regret).

USER-PRIORITY DIRECTION FOR SESSION 58 (autonomous overnight):

**EXHAUSTIVE high_only deep-dive — characterize WHAT oracle picks for
the Omaha (bot) hand vs the Hold'em (mid) hand across EVERY max-rank ×
structural-achievability cell, then design ho_v4 from the deepest
residual axis revealed.**

The user reviewed Session 57's ship and said:
"your findings are great and at first glance its nice to see that it
didnt know it had the option of splitting the remaining 6 cards into
suited chunks - but be specific, what does it choose for its omaha hand
double suited vs its mid hand - what is it looking for in each? does it
optimize the omaha FIRST before holdem or vice versa? does it care
about high(er) cards for one vs the other or does it look solely at
connectedness for the omaha? and what about situations that are 1) Ace
high still but dont have 3 possible suited combinations, lets say it
can do DS but then its mid is random crap, or lets say it can do a
single suit and the other stuff suffers 2) work this same logic for K
high, Q high, so on so forth until its exhaustive across all
combinations."

**Deliverable regardless of whether v44_dt ships:** a per-max-rank ×
per-structural-achievability decision matrix showing what oracle picks
for top, bot, mid under every cell. This is the documentation the user
wants, AND it directly informs all future high_only feature work.

**5-DRILL PLAN (overnight):**

### Drill HO5 — per-max-rank residual stratification (~7 min)
Sweep all 1,226,940 high_only hands. For each max_rank ∈
{A, K, Q, J, T, 9, 8}:
  - Total v43 vs oracle mismatch contribution ($/1000h whole-grid).
  - Top-10 mismatch classes (v43_pick → oracle_pick).
  - Distribution of v43 picks (top×bot×mid) vs oracle picks.
  - pct_opt within max-rank class.
Adapt drill_high_only_zone_v42_diagnostic.py — swap to v43, add
max_rank dimension to the cell stratification.

### Drill HO6 — full structural achievability cross-tabulation (~7 min)
For each high_only hand, compute these signals (most are derivable
from existing scripts; aggregate them):
  1. n_DS_bot_configs (count of 4-card subsets that are 2+2)
  2. n_DS_bot_with_max_on_top (DS configs where max-rank is leftover)
  3. n_ms_mid_configs (count of (top, mid_pair) splits with mid suited)
  4. n_ms_mid_with_max_on_top (subset with max-rank as top)
  5. n_joint_DS_ms_max_top_configs (the ho_v3 count)
  6. best_DS_bot_pair_high (max higher-card-of-suited-pair across DS)
  7. best_ms_mid_high (max higher-card-of-suited-mid across ms-mid)
  8. bot_mid_quality_gap (in joint configs: best_bot vs best_mid rank
     difference — captures trade-off magnitude)
Stratify by max_rank. Cross-tabulate. Identify cells where joint is
achievable but at uneven quality (high bot + low mid, OR vice versa —
the trade-off cases that ho_v3 cannot distinguish).

### Drill HO7 — what oracle ACTUALLY picks per cell (~10 min)
For each (max_rank × structural-achievability) cell from Drill HO6:
  - TOP: rank distribution (always max? sometimes 2-on-top defensive?
    second-highest?).
  - BOT: ranks present (sum, max, min), suit profile, longest-run
    connectivity within the bot's 4 cards, suit-pair high cards.
  - MID: ranks present (sum, max, min), suit-match status,
    connectivity.
Then compare against v43's pick per-cell. The DELTA between oracle
and v43 in bot vs mid choices reveals what v43 is missing.

### Drill HO8 — Omaha-first vs Hold'em-first vs joint (~10 min)
The user's discriminating question. For each oracle-picked hand:
  1. Enumerate ALL alternative (bot, mid) splits with the same top.
  2. Rank by bot strength only, by mid strength only, by joint EV.
  3. Where does oracle's pick fall in each ranking?
Hypothesis to test: oracle is closer to "bot-first" than "mid-first"
because Omaha pays 3 points/board vs Hold'em mid 2 points/board. But
the ratio matters and may flip in specific cells. Quantify the
implicit exchange rate per max-rank.

### Drill HO9 — edge-case "trade-off" enumeration (~10 min)
The user's specific question: when DS is achievable BUT mid is crap,
what does oracle pick?
  - Stratify hands where best_ms_mid_high (in joint configs) ≤ T
    (suited mid would be a low pair).
  - Compare oracle picks: DS+low_ms_mid vs SS_ms+higher_mid vs
    DS_mu+highest_mid vs other.
  - Per max-rank, quantify the break-even threshold: at what mid_high
    does oracle switch from DS+ms to SS+ms?
Same for the inverse: when SS is achievable with strong suited mid
but DS would force a weak mid, at what point does the bot upgrade
matter more than the mid downgrade?

### Phase 2 v4 — design 4 features from drill findings
Most likely candidates (rank by likelihood after drill data):
  1. Trade-off-aware joint feature: encode "DS+ms achievable AND
     mid_high ≥ threshold" + "SS+ms with mid_high ≥ threshold" +
     second-best joint quality — explicit alternative-comparison.
  2. Per-max-rank-class joint features: fire only at K/Q/J max-rank
     and encode the same joint pattern as ho_v3 but with different
     trade-off weights.
  3. Bot-vs-mid priority signal: e.g., "ratio of best_DS_bot_quality
     to best_ms_mid_quality" that exposes the trade-off directly.
  4. Defensive-2-on-top features: if Drill HO5 reveals defensive-top
     mismatches dominate at K/Q max.

Pick the 4 features that target the LARGEST residual cell from the
drills, mirroring the v2/v3/v5 rank-valued conditional shape.

### Train + ship v44_dt
depth=36 ml=1, 107 features = 103 + 4 ho_v4. Same surgical-gating
discipline. Acceptance: −$30/1000h or better on full grid + all
non-high_only categories byte-identical.

### MUST-PRODUCE deliverable (regardless of whether v44 ships)
A per-max-rank decision matrix saved to
`SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` at repo root, covering
A/K/Q/J/T/9/8 max-rank classes, with per-cell:
  - Oracle's TOP pick (always-max? sometimes defensive?)
  - Oracle's BOT pick (suit profile, rank profile, connectivity)
  - Oracle's MID pick (suit profile, rank profile, connectivity)
  - Trade-off rule (e.g., "at K-high, oracle switches from DS+ms to
    SS+ms when best_ms_mid_high ≤ 9").
  - v43's mistake pattern in this cell.

This deliverable IS the answer to the user's review question even
if no new ML ship results.

Time budget: ~30 min of drills + ~30 min of feature design + persist
+ train + grade (~6 min train, ~14 min full-grid grade) = ~1.5–2
hours of compute. Plus thinking time. Fully autonomous-friendly.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Run drills in parallel where independent (HO5/HO6/HO7/HO8/HO9 can
  often share a single sweep — consolidate into 1-2 scripts if
  possible to save wall time).
- Don't re-implement what already exists — reuse setting_features_from_bytes,
  SETTING_HAND_INDICES, SUIT_PROFILE_* constants from
  tw_analysis.query.
- Methodology rule (Session 57): the 4-phase playbook is transferable
  to the SAME zone for a SECOND pass without modification.
- Methodology rule (Session 57): a zone can be collapsed multiple
  times by stacking conditional feature axes; gains compound
  surgically.
- Methodology rule (Session 57): joint achievability is a distinct
  structural axis from single-axis achievability; joint features are
  NOT redundant with the components.
- Methodology rule (Session 57): importance can be low (#60+) and
  lift can still ship via surgical gating on a high-leverage subset.
- Methodology rule (Session 57): user predictions can be wrong about
  WHICH axis dominates even after one pass collapses one axis; the
  data dictates the axis, not the human intuition.
- Methodology rule (Session 56): when feature design exactly matches
  the structural delta, Phase 1b confirmation collapses to 100/0.
- Methodology rule (Session 56): surgical-gating means prefix-grid
  neutrality is correct (not suspect) when the prefix slice doesn't
  contain the targeted population.
- Methodology rule (Session 55): asymmetric existing features signal
  blind spots.
- Methodology rule (Session 55): low individual feature importance
  can still ship lift via surgical gating.
- Methodology rule (Session 54): diagnostic-first feature engineering
  works at saturation.
- Methodology rule (Session 54): boolean features are redundant at
  ml=1 saturation.
- Methodology rule (Session 54): rank-valued conditional features
  describing ALTERNATIVE configurations unlock saturation.
- Methodology rule (Session 54): feature design beats hyperparameter
  tuning at saturation.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
