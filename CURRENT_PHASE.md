# Current: Sprint 8 — Session 58 ships **v44_dt as the new ML champion via the user-priority high_only zone THIRD-PASS collapse, applying the 4-phase playbook (drill → hand-level → 4 rank-valued conditional features → train) for the 6th consecutive session and the 3rd time on the SAME zone**. v43_dt → v44_dt: **$1,123 → $1,081 full / $686 → $686 prefix**. **High_only within-category $2,075 → $1,868 (−$207, −10.0%)**, pct_opt 37.9% → 41.8% (+3.9%). All 7 non-targeted categories byte-identical to v43 on both grids (surgical gating). Leaf count v44: 2.18M → 2.25M (+3.2%). Depth saturated at 36. Four new features: `ho_v4_topMax_DS_max_bot_pair_high_g`, `ho_v4_topMax_4f_ms_max_mid_high_g`, `ho_v4_topNonMax_DS_ms_n_configs_g`, `ho_v4_topNonMax_DS_ms_max_top_rank_g` — total 107 features (95 base + 4 ho_v2 + 4 ho_v3 + 4 ho_v4). Feature importance #47/#80/#93/#95. Cumulative v32 → v44 = **−$634 full / −$218 prefix** (9 ML ships). Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). The ML champion now beats the rule chain by **$1,417/1000h** (more than half the rule-chain EV deficit). **Three-session high_only collapse (S55 → S58): $2,796 → $2,411 → $2,075 → $1,868 = −$928 within-cat (−33.2%)** — composing three conditional axes (ho_v2 DS-only + ho_v3 DS+ms-joint + ho_v4 DS-quality+non-max-joint+4f) compresses the same zone three times without surgical interference. **Five drills (HO5–HO10) on all 1.226M high_only hands surfaced THREE structural axes invisible to v43**: (1) `DS_NO_JOINT` cell is dominant at 62.9% × every max-rank, ~69% of high_only regret; v43 under-routes DS bot by 10–20% there. (2) within JOINT picks, oracle is mid-first (mean mid_pct 0.67–0.81 >> bot_pct 0.24–0.36); v43 already covers via ho_v3_max_mid_high. (3) joint take-rate collapses with lower max-rank (A:95% → 8:13%); 47.7% of high_only hands have a non-max-top joint achievable; v43 has no feature for this entire population. (4) at max=A, 4f+ms_mid is dominant alt (54% of A-alt picks). MUST-PRODUCE deliverable shipped: `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` at repo root — per-max-rank × per-cell oracle TOP/BOT/MID profile + trade-off rules — answering the user's S57 review independently of the ML ship. Methodology validation: **the 4-phase playbook is transferable to the SAME zone for a THIRD pass without modification; the decision matrix is a separable deliverable from the ML ship; "Omaha-first or Hold'em-first?" has a nuanced answer (mid-first within joint, bot-first outside joint at lower max-ranks).**

> **🎯 IMMEDIATE NEXT ACTION (Session 59): Decide between (a) high_only 4th-pass focused on the K/Q × `DS_NO_JOINT` cells where the "max-off-top" residual is biggest, OR (b) pivot to trips ($1,194 within-cat × 4.6% share = $55/1000h whole-grid) for diversification.**
>
>   **Why pause and decide rather than auto-continue.** The high_only zone is still the dominant residual ($1,868 within-cat × 40.4% share = $755/1000h whole-grid = ~70% of v44's regret), so a 4th-pass is the highest-leverage option. The S58 decision matrix surfaced a clear 4th-pass target: at K/Q in `DS_NO_JOINT`, oracle drops max-rank off the top **34%/52% of the time** but v43 keeps it on top 87%/68% — the v44 features only partly capture this (the non-max joint count fires, but oracle's choice depends on a richer per-cell trade-off than v44 currently encodes). Estimated ho_v5 lift: **$50–80/1000h** if the right structural axis is found, similar magnitude to S57's ho_v3 ship. The trips zone alternative is ~$10–15/1000h max even in best case (trips is only 4.6% of population) — much smaller absolute return. **Recommendation: continue high_only 4th-pass.**
>
>   **The 4-phase playbook for Session 59 (if continuing high_only):**
>
>   **Phase 1 — Drill HO11**: per-(max_rank, cell) v44-vs-oracle mismatch matrix specifically inside `DS_NO_JOINT` at K/Q/J. Identify the dominant new mismatch class. Hypothesis (testable): the residual is now in the "max-off-top + DS bot routing choice" axis — oracle picks (top=2nd-highest, DS bot, ms mid) where v44 still picks (top=max, DS_mu) or (top=max, SS_ms). v44's `ho_v4_topNonMax_DS_ms_max_top_rank_g` exposes the BEST non-max top rank but not WHICH non-max top is best per (DS bot, mid suit) trade-off.
>
>   **Phase 1b — Drill HO12 (hand-level)**: inspect 50–100 hands of the dominant new mismatch class. Confirm structural delta. Most likely finding: when DS_pair_high = max_rank in non-max-top joints (e.g., a K-pair as the suited pair in the bot at max=K), oracle ALWAYS picks the non-max joint route; v44 partially routes to it but not fully because the choice between top=2nd-rank vs top=3rd-rank vs top=lower depends on mid_high quality at each top.
>
>   **Phase 2 v5 — design 4 features targeting the deepest residual axis**:
>     1. `ho_v5_topNonMax_DS_ms_max_mid_high_g` — best mid_high in non-max-top joints (the missing quality counterpart to v44's max_top_rank).
>     2. `ho_v5_topNonMax_DS_ms_best_combined_quality_g` — max(top_rank + mid_high) across non-max joints — the "joint quality" scalar.
>     3. `ho_v5_topNonMax_DS_ms_with_max_in_bot_pair_g` — count of non-max joints where max-rank is paired in the bot (the K-pair-in-bot signature for K-high).
>     4. `ho_v5_topMax_4f_ms_n_configs_g` (or similar) — augment the 4f route to give a count signal alongside ho_v4's max_mid_high.
>
>   **Phase 3 — train + ship v45_dt** at depth=36 ml=1, 111 features. Acceptance: −$30/1000h or better on full grid + all non-high_only categories byte-identical.
>
>   **Time budget:** ~1.5–2 hours of compute (similar to S58). Fully autonomous-friendly.

> **✅ NEW SHIPS (Session 58):**
> 1. **v44_dt** replaces v43_dt as ML champion. **+$42 full / $0 prefix.** High_only zone collapse from $2,075 → $1,868 (−10.0%). Prefix neutrality is by design — prefix slice has zero high_only hands and the new features are gated.
> 2. **`SESSION_58_HIGH_ONLY_DECISION_MATRIX.md`** — per-max-rank × per-cell decision matrix at repo root, answering the user's S57 review question independently of the ML ship.
> 3. **Cumulative session +$42 full / $0 prefix.** New feature suite fully orthogonal — surgical gating preserves all other categories byte-identical on both grids.

> **🔬 ARTIFACTS (Session 58):**
> 1. **`analysis/scripts/drill_high_only_v43_deepdive.py`** — Drill HO5+HO6+HO7 (consolidated: per-max-rank residual + structural cell cross-tab + oracle pick profile). Persists `data/drill_ho_v43_per_hand_structural.parquet` (15 MB) for downstream drill reuse.
> 2. **`analysis/scripts/drill_high_only_v43_bot_vs_mid.py`** — Drill HO8 (Omaha-first vs Hold'em-first vs joint per max-rank).
> 3. **`analysis/scripts/drill_high_only_v43_threshold.py`** — Drill HO9 (DS-vs-SS threshold; reads parquet from HO5+HO6+HO7).
> 4. **`analysis/scripts/drill_high_only_v43_nonmax_joint.py`** — Drill HO10 supplementary (non-max-top joint enumeration).
> 5. **`analysis/scripts/high_only_aug_v4_features_gated.py`** + persist — PRODUCTION rank-valued features for high_only structural axes.
> 6. **`analysis/scripts/train_v44_dt.py`** + `strategy_v44_dt.py` + `grade_v44_dt.py` — ship.
> 7. **`data/v44_dt_model.npz`** (1260 MB) — PRODUCTION ML champion.
> 8. **`data/feature_table_high_only_aug_v4_gated.parquet`** (19 MB) — persisted feature table.
> 9. **`SESSION_58_V44_DT_REPORT.md`** — repo-root standalone report.
> 10. **`SESSION_58_HIGH_ONLY_DECISION_MATRIX.md`** — repo-root decision matrix (the user-deliverable doc).

> **📓 METHODOLOGY LESSONS (Session 58 NEW):**
> - **The 4-phase playbook is transferable to the SAME zone for a THIRD pass without modification.** Re-drilling against the new champion (v43, post-S57 collapse) revealed the residual had shifted axis (DS+ms joint → DS bot quality + non-max-top joint + 4f route) without changing in zone. Same playbook applied without modification.
> - **A zone can be collapsed at least three times by stacking conditional feature axes.** Each session adds a NEW conditional axis to the same zone, and gains compound surgically: $2,796 → $1,868 (−$928, −33.2%) over S56→S58.
> - **The decision matrix is a separable deliverable from the ML ship.** `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` documents oracle's structural strategy across 7 max-ranks × 7 cells, answering the user's S57 review independently of whether v44 shipped.
> - **5 drills can run as 4 scripts sharing one sweep.** HO5+HO6+HO7 consolidated (~8 min, 2.5K hands/s incl. v43 strategy calls); HO8/HO9/HO10 standalone (or read the shared parquet). Total drill compute: ~10 min wall time.
> - **"Omaha first or Hold'em first?" has a nuanced answer.** Within joint, oracle is mid-first (mid_high preferred over bot pair_high). Outside joint at lower max-ranks, oracle becomes bot-first (max-rank moves into the bot to enable a stronger DS configuration with a lower top). Both behaviors are simultaneously true at different points in the structural cell space.

> Updated: 2026-05-11 (Session 58)

---

## Headline state at end of Session 58

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED from S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **NEW ML champion (Session 58).** 2.25M leaves, 107 features at depth=36 ml=1; +$42 full / $0 prefix vs v43_dt. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). 2.18M leaves, 103 features. | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v42_dt | S56 ML champion. 2.11M leaves, 99 features. | `analysis/scripts/strategy_v42_dt.py` + `data/v42_dt_model.npz` |
| v41_dt | S55 ML champion. 2.02M leaves, 95 features. | `analysis/scripts/strategy_v41_dt.py` + `data/v41_dt_model.npz` |
| v40_dt | S55 first ship; replaced within-session. 1.57M leaves, 91 features. | `analysis/scripts/strategy_v40_dt.py` + `data/v40_dt_model.npz` |
| v39_dt | S54 ML champion. 1.52M leaves, 87 features. | `analysis/scripts/strategy_v39_dt.py` + `data/v39_dt_model.npz` |
| v36_dt | Older ML champion (S53 overnight; 1.06M leaves; $1,649). | `analysis/scripts/strategy_v36_dt.py` + `data/v36_dt_model.npz` |
| v34_dt | Older ML champion (874K leaves; $1,681). | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v47_rule16_Qhigh_DS / v46_rule15_Khigh_DS / v45_rule14_Ahigh_DS | Predecessor rule chains. | various |
| v44_rule13_three_pair_DS / v43_rule12 / v42 / v41 / v40b | Earlier rule chains. | various |
| v32_dt | Older ML baseline. | various |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines. | various |

**Capacity + feature progression — NEW v44 ML champion:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h full | pct_opt full |
|---|---:|---:|---:|---:|---:|---:|
| v32 | 32 | 3 | 83 | 731,606 | $1,715 | 50.86% |
| v34 | 34 (33 actual) | 2 | 83 | 874,548 | $1,681 | 52.02% |
| v36 | 36 (33 actual) | 1 | 83 | 1,064,442 | $1,649 | 53.61% |
| v39 | 36 | 1 | 87 (83+4 pair_v5) | 1,518,368 | $1,412 | 57.88% |
| v40 | 36 | 1 | 91 (87+4 tp_v2) | 1,569,848 | $1,394 | 58.48% |
| v41 | 36 | 1 | 95 (91+4 t2p_v2) | 2,015,413 | $1,270 | 62.18% |
| v42 | 36 | 1 | 99 (95+4 ho_v2) | 2,109,330 | $1,192 | 63.08% |
| v43 | 36 | 1 | 103 (99+4 ho_v3) | 2,177,798 | $1,123 | 63.99% |
| **v44** | **36** | **1** | **107 (103+4 ho_v4)** | **2,248,173** | **$1,081** | **64.80%** |

**Cumulative ML arc (v32 → v44):** **−$634/1000h on full grid across 9 ships** (v34: −$34, v36: −$33, v39: −$237, v40: −$18, v41: −$124, v42: −$79, v43: −$69, v44: −$42).

**Per-category residuals (within-category, full grid) — END OF SESSION 58:**

| Category | n_hands | share | v44 within-cat | $/1000h whole-grid | Δ vs v43 |
|---|---:|---:|---:|---:|---:|
| **high_only** (S58 collapsed) | 1,226,940 | 40.4% | **$1,868** | $755 | **−$207** |
| pair | 2,800,512 | 36.2% | $1,097 | $396 | $0 |
| trips | 328,185 | 4.6% | $1,194 | $55 | $0 |
| two_pair | 1,338,480 | 14.5% | $363 | $52 | $0 |
| three_pair | 114,400 | 2.2% | $1,613 | $35 | $0 |
| trips_pair | 171,600 | 1.8% | $281 | $5 | $0 |
| composite | 14,742 | 0.2% | $960 | $2 | $0 |
| quads | 14,300 | 0.1% | $545 | $1 | $0 |

**high_only is STILL by far the dominant residual** ($755/1000h whole-grid = ~70% of total v44 regret). Session 59's highest-leverage target. Three-session high_only progression: $2,796 → $2,411 → $2,075 → $1,868 = **−$928 within-category (−33.2%)** over Sessions 56–58.

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

**The two production tracks now diverge by $1,417/1000h** (v52 rule chain at $2,498; v44_dt at $1,081). The ML champion beats the human-memorizable rule chain by more than half its EV deficit.

---

## What Session 58 produced

**Code:**
- 4 drills (HO5+HO6+HO7 consolidated, HO8 standalone, HO9 reads parquet, HO10 standalone supplementary)
- 1 feature module (high_only_v4) + 1 persistence script
- 1 trainer (v44) + 1 strategy + 1 grader

**Documentation:**
- `STRATEGY_GUIDE.md` — Part 1 Session 58 entry; Part 2 ML champion table updated (v44 row); front-matter "Last updated" line refreshed
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 093 appended
- `SESSION_58_V44_DT_REPORT.md` — repo-root standalone report
- `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` — repo-root decision matrix (the user-deliverable doc)

**Models persisted:**
- `data/v44_dt_model.npz` (PRODUCTION ML champion, 1260 MB)
- `data/feature_table_high_only_aug_v4_gated.parquet` (19.04 MB)
- `data/drill_ho_v43_per_hand_structural.parquet` (15.0 MB; reusable for future high_only drills)
- `data/drill_ho_v43_nonmax_joint.parquet` (4.7 MB; supplementary)

---

## Resume Prompt (Session 59 — overnight, autonomous)

```
Resume Session 59 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 58)
- DECISIONS_LOG.md (latest: Decision 093 — v44_dt new ML champion)
- SESSION_58_V44_DT_REPORT.md
- SESSION_58_HIGH_ONLY_DECISION_MATRIX.md
- STRATEGY_GUIDE.md (Session 58 entry in Part 1; updated ML champion
  table in Part 2)
- analysis/scripts/strategy_v44_dt.py — current ML champion
- analysis/scripts/high_only_aug_v4_features_gated.py — ho_v4 feature
  template (most-recent prior art)
- analysis/scripts/drill_high_only_v43_deepdive.py — drill consolidation
  template
- analysis/scripts/high_only_aug_v3_features_gated.py — ho_v3 JOINT
  feature template

State (end of Session 58):
- Rule chain production: v52_full_high_only_handler (17 rules; UNCHANGED)
  at $2,498 full / $1,522 prefix.
- ML champion: v44_dt (NEW) at $1,081 full / $686 prefix; 2.25M leaves
  at depth=36 ml=1; 107 features.
- Cumulative ML v32 → v44 = −$634 full / −$218 prefix (9 ML ships).
- High_only collapsed THREE times: $2,796 → $2,411 → $2,075 → $1,868
  (−$928 / −33.2%).
- High_only is STILL the dominant residual at $755/1000h whole-grid
  (~70% of v44's regret).

DIRECTION FOR SESSION 59 (autonomous overnight):

**High_only 4th-pass focused on the K/Q × `DS_NO_JOINT` cells where the
"max-off-top" residual is biggest.**

The S58 decision matrix surfaced the deepest unaddressed cell: at K/Q in
`DS_NO_JOINT`, oracle drops max-rank off the top 34%/52% of the time
but v44 keeps it on top 87%/68%. v44's ho_v4 features partly capture
this (the non-max joint count fires) but oracle's choice depends on a
richer per-cell trade-off than v44 currently encodes.

5-DRILL PLAN (overnight):

### Drill HO11 — per-max-rank residual stratification on v44_dt
Apply HO5 template to v44 (swap strategy_v43_dt → strategy_v44_dt; add
v44 fields). Verify the K/Q × DS_NO_JOINT cells are now the dominant
residual. Identify the new top mismatch class (likely tK_DS_mu →
t<12_DS_ms or similar non-max-top swap).

### Drill HO12 — hand-level inspection of the dominant new mismatch
Inspect 50–100 hands. Confirm structural delta. Hypothesis: when the
DS bot would contain the max-rank as a suited pair (K-pair-bot at
max=K), oracle ALWAYS prefers non-max-top joint route.

### Drill HO13 — non-max-top joint quality stratification
Stratify non-max-top joints by (best_top_rank, best_mid_high) tuples.
Identify which (top, mid) combinations oracle prefers. v44 has best_top
but not best_mid in non-max joints — this is the gap.

### Phase 2 v5 — design 4 features
1. ho_v5_topNonMax_DS_ms_max_mid_high_g — best mid_high in non-max
   joints (the missing quality counterpart to v44's max_top_rank).
2. ho_v5_topNonMax_DS_ms_best_combined_quality_g — max(top + mid_high)
   across non-max joints.
3. ho_v5_topNonMax_DS_ms_with_max_in_bot_pair_g — count of non-max
   joints where max-rank is paired in the bot suit.
4. ho_v5_topMax_4f_ms_n_configs_g — augment 4f route with count signal.

Pick the 4 features from drill outcomes; mirror v2/v3/v4 rank-valued
shape.

### Train + ship v45_dt
depth=36 ml=1, 111 features = 107 + 4 ho_v5. Same surgical-gating
discipline. Acceptance: −$30/1000h or better on full grid + all
non-high_only categories byte-identical.

Time budget: ~1.5–2 hours of compute. Fully autonomous-friendly.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Reuse `data/drill_ho_v43_per_hand_structural.parquet` from S58 if
  the residual structure is similar (saves the ~8 min sweep).
- Methodology rule (Session 58): the 4-phase playbook is transferable
  to the SAME zone for a THIRD pass — and presumably a 4th, 5th, etc.
  Each pass adds a NEW conditional axis; gains compound surgically.
- Methodology rule (Session 58): the decision matrix is a separable
  deliverable from the ML ship — even if v45 doesn't ship, document
  the per-cell trade-off rules.
- Methodology rule (Session 58): "Omaha-first or Hold'em-first?" has
  a nuanced answer — mid-first within joint, bot-first outside joint
  at lower max-ranks. Both true simultaneously in different cells.
- Methodology rule (Session 57): joint achievability is a distinct
  structural axis from single-axis achievability; joint features are
  NOT redundant with the components.
- Methodology rule (Session 57): importance can be low (#60+) and
  lift can still ship via surgical gating on a high-leverage subset.
- Methodology rule (Session 57): user predictions can be wrong about
  WHICH axis dominates even after one pass collapses one axis; the
  data dictates the axis.
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
