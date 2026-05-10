# Current: Sprint 8 — Session 56 ships **v42_dt as the new ML champion via the user-priority high_only zone collapse, applying the proven 4-phase playbook (drill → hand-level → 4 rank-valued conditional features → train) for the 4th consecutive session**. v41_dt → v42_dt: **$1,270 → $1,192 full / $686 → $686 prefix**. **High_only within-category $2,796 → $2,411 (−$385, −13.8%)**, pct_opt 29.0% → 33.4% (+4.4%). All 7 non-targeted categories byte-identical to v41 on both grids (surgical gating). Leaf count v42: 2.02M → 2.11M (+4.7%). Depth saturated at 36. Four new features: rank-valued `ho_v2_bot_DS_*_g` series mirroring pair_aug_v5 / trips_pair_v2 / two_pair_v2 — total 99 features (95 base + 4 ho_v2). Three of four ranked in top-32 importance (#26, #31, #32). Cumulative v32 → v42 = **−$524 full / −$218 prefix** (7 ML ships). Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). The ML champion now beats the rule chain by **$1,306/1000h** (more than half the rule-chain EV deficit). Phase 1b validation was the cleanest in the project: 100% of dominant-class (tA_SS_mu → tA_DS_ms) mismatches have max_top=A available in DS configs, AND 100% of oracle picks use it — the new feature shape captures the structural delta exactly. **User-prediction "different feature types needed" was partially correct, partially wrong**: the dominant high_only blind spot turned out to be the SAME DS-routing pattern as prior zones; only the bot suit profile differs in 100% of mismatches, not the top-card choice. Methodology validation: **the playbook is fully transferable to the largest population zone (40.4% of canonical hands) without modification.** Prefix-grid neutrality is by design — the prefix slice contains zero high_only hands, so gated features mathematically guarantee identical metrics; this is correct, not a regression.

> **🎯 IMMEDIATE NEXT ACTION (Session 57):**
>
>   **More high_only feature axes — high_only is STILL the dominant residual at $2,411/1000h within-cat × 40.4% share = $975/1000h whole-grid contribution (~82% of v42's total regret).**
>
>   The ho_v2 features collapsed only the DS-routing axis ($210/1000h whole-grid). The remaining $271/1000h of high_only mismatch contribution (post-v42 estimate) lives in:
>      - **Top-card placement at non-Ace ranks**: the SS→SS swap ($80/1000h pre-v42) and 31→DS swap ($36) classes
>      - **Broadway connectivity at non-Ace tops**: tK→tK and tQ→tQ mismatches (still ~$67 + $24 = $91/1000h pre-v42)
>      - **Defensive-pair triggers** (when 7 cards form a near-straight)
>      - **Three-of-a-suit clustering quality**
>
>   4-phase plan (Session 57):
>   Phase 1: Re-drill high_only against v42 (NEW residual matrix; the SS→DS class will be smaller; new dominant classes will emerge)
>   Phase 1b: Hand-level inspection of new top class
>   Phase 2 v3: Design 4 rank-valued conditional features (probably mid-suited vs mid-unsuited quality, top-rank kept tA-vs-tK, etc.)
>   Train v43_dt
>
>   Alternative targets: trips zone ($55/1000h whole-grid) or three_pair ($35/1000h) — much smaller potential lift but cleaner playbook fits.

> **✅ NEW SHIPS (Session 56):**
> 1. **v42_dt** replaces v41_dt as ML champion. **+$79 full / $0 prefix.** High_only zone collapse from $2,796 → $2,411 (−13.8%). Prefix neutrality is by design — prefix slice has zero high_only hands and the new features are gated.
> 2. **Cumulative session +$79 full / $0 prefix.** New feature suite fully orthogonal — surgical gating preserves all other categories byte-identical on both grids.

> **🔬 ARTIFACTS (Session 56):**
> 1. **`analysis/scripts/drill_high_only_zone_v41_diagnostic.py`** — Drill HO (Phase 1)
> 2. **`analysis/scripts/drill_high_only_v41_mismatch_handlevel.py`** — Drill HO2 (Phase 1b)
> 3. **`analysis/scripts/high_only_aug_v2_features_gated.py`** + persist — PRODUCTION rank-valued features for high_only
> 4. **`analysis/scripts/train_v42_dt.py`** + `strategy_v42_dt.py` + `grade_v42_dt.py` — ship
> 5. **`data/v42_dt_model.npz`** (1188 MB) — PRODUCTION ML champion
> 6. **`data/feature_table_high_only_aug_v2_gated.parquet`** (19.24 MB) — persisted feature table
> 7. **`SESSION_56_V42_DT_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 56 NEW):**
> - **The playbook is fully transferable to the largest population zone.** Zone size doesn't break the methodology. high_only at 40.4% of population collapsed via the same pipeline that handled trips_pair (1.8%) and two_pair (14.5%).
> - **Phase 1b can be a 100% confirmation, not just a 70-90% one.** Prior sessions had aggregates like "72% have suit overlap" or "85.7% have R2 routing." S56's "100% of mismatches have max_top=A AND 100% of oracle picks use it" is the strongest Phase 1b validation yet. When feature design exactly matches the structural delta, the percentages collapse to 100/0.
> - **Surgical gating means prefix-grid neutrality is correct, not suspect.** When new features are gated to a category absent from the prefix slice, prefix Δ = $0 by construction. Pre-flight "2× ratio" gates only apply when both grids contain the target population.
> - **User-prediction "different feature types needed" was partially correct, partially wrong.** User predicted top-card placement, defensive triggers, broadway connectivity. Reality: the DOMINANT blind spot was the same DS-routing pattern as prior zones — Ace-top is preserved in 100% of dominant-class mismatches; the structural error is purely the bot suit profile. **Generalizable lesson: when an existing feature family (DS-bot achievability) is missing entirely from a zone, that gap dominates even when other axes also exist.**
> - **Single-axis ships have predictable leaf growth.** v42's +4.7% leaves vs v41's +32% reflects: population × axis-count × info-content determines leaf expansion. high_only has 40% population but the single DS axis touches a narrower split surface than two_pair's Layout B/C asymmetry.
> - **Cumulative DT ML arc continues to compound.** v32 → v42 = −$524 across 7 ML ships at depth=36 ml=1 saturation. Feature engineering at saturation continues to ship — the asymptote is not yet visible.

> Updated: 2026-05-10 (Session 56)

---

## Headline state at end of Session 56

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED from S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v42_dt** | **NEW ML champion (Session 56).** 2.11M leaves, 99 features at depth=36 ml=1; +$79 full / $0 prefix vs v41_dt. | `analysis/scripts/strategy_v42_dt.py` + `data/v42_dt_model.npz` |
| v41_dt | Predecessor ML champion (S55). 2.02M leaves, 95 features. | `analysis/scripts/strategy_v41_dt.py` + `data/v41_dt_model.npz` |
| v40_dt | S55 first ship; replaced by v41 within-session. 1.57M leaves, 91 features. | `analysis/scripts/strategy_v40_dt.py` + `data/v40_dt_model.npz` |
| v39_dt | S54 ML champion. 1.52M leaves, 87 features. | `analysis/scripts/strategy_v39_dt.py` + `data/v39_dt_model.npz` |
| v36_dt | Older ML champion (S53 overnight; 1.06M leaves; $1,649). | `analysis/scripts/strategy_v36_dt.py` + `data/v36_dt_model.npz` |
| v34_dt | Older ML champion (874K leaves; $1,681). | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v47_rule16_Qhigh_DS / v46_rule15_Khigh_DS / v45_rule14_Ahigh_DS | Predecessor rule chains. | various |
| v44_rule13_three_pair_DS / v43_rule12 / v42 / v41 / v40b | Earlier rule chains. | various |
| v32_dt | Older ML baseline. | various |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines. | various |

**Capacity + feature progression — NEW v42 ML champion:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h full | pct_opt full |
|---|---:|---:|---:|---:|---:|---:|
| v32 | 32 | 3 | 83 | 731,606 | $1,715 | 50.86% |
| v34 | 34 (33 actual) | 2 | 83 | 874,548 | $1,681 | 52.02% |
| v36 | 36 (33 actual) | 1 | 83 | 1,064,442 | $1,649 | 53.61% |
| v39 | 36 | 1 | 87 (83+4 pair_v5) | 1,518,368 | $1,412 | 57.88% |
| v40 | 36 | 1 | 91 (87+4 tp_v2) | 1,569,848 | $1,394 | 58.48% |
| v41 | 36 | 1 | 95 (91+4 t2p_v2) | 2,015,413 | $1,270 | 62.18% |
| **v42** | **36** | **1** | **99 (95+4 ho_v2)** | **2,109,330** | **$1,192** | **63.08%** |

**Cumulative ML arc (v32 → v42):** **−$524/1000h on full grid across 7 ships** (v34: −$34, v36: −$33, v39: −$237, v40: −$18, v41: −$124, v42: −$79).

**Per-category residuals (within-category, full grid) — END OF SESSION 56:**

| Category | n_hands | share | v42 within-cat | $/1000h whole-grid |
|---|---:|---:|---:|---:|
| **high_only** (S56 collapsed) | 1,226,940 | 40.4% | **$2,411** | $975 |
| pair | 2,800,512 | 36.2% | $1,097 | $396 |
| trips | 328,185 | 4.6% | $1,194 | $55 |
| two_pair | 1,338,480 | 14.5% | $363 | $52 |
| three_pair | 114,400 | 2.2% | $1,613 | $35 |
| trips_pair | 171,600 | 1.8% | $281 | $5 |
| composite | 14,742 | 0.2% | $960 | $2 |
| quads | 14,300 | 0.1% | $545 | $1 |

**high_only is STILL by far the dominant residual** ($975/1000h whole-grid = ~82% of total v42 regret). Session 57's highest-leverage target — but now needs a SECOND axis (the DS-routing axis is collapsed; the residual lives in top-card placement at non-Ace ranks, broadway connectivity, etc.).

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

**The two production tracks now diverge by $1,306/1000h** (v52 rule chain at $2,498; v42_dt at $1,192). The ML champion beats the human-memorizable rule chain by more than half its EV deficit.

---

## What Session 56 produced

**Code:**
- 2 drills (1 Phase 1 + 1 Phase 1b)
- 1 feature module (high_only_v2) + 1 persistence script
- 1 trainer (v42) + 1 strategy + 1 grader

**Documentation:**
- `STRATEGY_GUIDE.md` — Part 1 Session 56 entry; Part 2 ML champion table updated
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 091 appended
- `SESSION_56_V42_DT_REPORT.md` — repo-root standalone report

**Models persisted:**
- `data/v42_dt_model.npz` (PRODUCTION ML champion)
- `data/feature_table_high_only_aug_v2_gated.parquet`

---

## Resume Prompt (Session 57)

```
Resume Session 57 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 56)
- DECISIONS_LOG.md (latest: Decision 091 — v42_dt new ML champion)
- SESSION_56_V42_DT_REPORT.md
- STRATEGY_GUIDE.md (Session 56 entry in Part 1; updated ML champion table in Part 2)
- analysis/scripts/strategy_v42_dt.py — current ML champion
- analysis/scripts/high_only_aug_v2_features_gated.py — template feature suite
- analysis/scripts/drill_high_only_zone_v41_diagnostic.py — Phase 1 drill template
- analysis/scripts/drill_high_only_v41_mismatch_handlevel.py — Phase 1b drill template

State (end of Session 56):
- Rule chain production: v52_full_high_only_handler (17 rules; UNCHANGED) at
  $2,498 full / $1,522 prefix.
- ML champion: v42_dt (NEW) at $1,192 full / $686 prefix; 2.11M leaves at
  depth=36 ml=1; 99 features (95 + 4 ho_v2).
- Cumulative ML v32 → v42 = −$524 full / −$218 prefix (7 ML ships).
- High_only zone gap collapsed from $2,796 → $2,411 (−$385, −13.8%).

USER-PRIORITY DIRECTION FOR SESSION 57:

Continue compressing the high_only zone — STILL the dominant residual at
$2,411/1000h within-cat × 40.4% share = $975/1000h whole-grid (~82% of
v42's total regret).

The ho_v2 features collapsed the DS-routing axis. The remaining residual
lives in:
- Top-card placement at non-Ace ranks (tK→tK and tQ→tQ mismatches were
  $67 and $24 pre-v42 — what's left after v42 collapsed the SS→DS slice
  of those?)
- Broadway connectivity at non-Ace tops
- Defensive-pair triggers and three-of-a-suit clustering

4-phase plan:
Phase 1: Re-drill high_only against v42_dt (NEW residual matrix; the
         SS→DS class will be smaller; new dominant classes will emerge)
Phase 1b: Hand-level inspection of the new top class
Phase 2 v3: Design 4 rank-valued conditional features for the
            highest-leverage NEW axis (likely mid-suited quality OR
            broadway-when-not-Ace OR something else the drill reveals)
Train v43_dt

Alternative targets: trips zone ($55/1000h whole-grid) or three_pair
($35/1000h) — much smaller potential lift but cleaner playbook fit.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Methodology rule (Session 56 NEW): the 4-phase playbook is fully
  transferable to the largest population zone without modification.
- Methodology rule (Session 56 NEW): when feature design exactly matches
  the structural delta, Phase 1b confirmation collapses to 100/0.
- Methodology rule (Session 56 NEW): surgical-gating means prefix-grid
  neutrality is correct (not suspect) when the prefix slice doesn't
  contain the targeted population.
- Methodology rule (Session 55): the playbook is TRANSFERABLE.
  Same shape works across zones.
- Methodology rule (Session 55): asymmetric existing features signal
  blind spots.
- Methodology rule (Session 55): low individual feature importance can
  still ship lift via surgical gating.
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
