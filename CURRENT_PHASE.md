# Current: Sprint 8 — Session 57 ships **v43_dt as the new ML champion via the user-priority high_only zone SECOND-PASS collapse, applying the proven 4-phase playbook (drill → hand-level → 4 rank-valued conditional features → train) for the 5th consecutive session and the 2nd time on the SAME zone**. v42_dt → v43_dt: **$1,192 → $1,123 full / $686 → $686 prefix**. **High_only within-category $2,411 → $2,075 (−$336, −13.9%)**, pct_opt 33.4% → 37.9% (+4.5%). All 7 non-targeted categories byte-identical to v42 on both grids (surgical gating). Leaf count v43: 2.11M → 2.18M (+3.2%). Depth saturated at 36. Four new features: rank-valued `ho_v3_topMax_DS_ms_*_g` series encoding JOINT (DS bot + ms mid) achievability + quality conditional on top=max-rank-of-hand — total 103 features (95 base + 4 ho_v2 + 4 ho_v3). All 4 features at LOW individual importance: #63 min_mid_high (0.07%), #64 max_mid_sum (0.07%), #100 max_mid_high (0.01%), #102 n_configs (0.00%) — **lowest-importance-per-ship in project**. Cumulative v32 → v43 = **−$592 full / −$218 prefix** (8 ML ships). Rule chain unchanged at v52 ($2,498 full / $1,522 prefix). The ML champion now beats the rule chain by **$1,375/1000h** (more than half the rule-chain EV deficit). **Two-session high_only collapse (S55 → S57): $2,796 → $2,411 → $2,075 = −$721 within-cat (−25.8%)** — composing two conditional axes (ho_v2 DS-only + ho_v3 DS+ms-joint) compresses the same zone twice without surgical interference. Phase 1 surfaced the counterintuitive finding: after S56 the SAME SS→DS pattern STILL dominates the residual, just with a NEW dimension (mid suiting); user-prediction axes (defensive K/Q triggers, T-9-8 top choice, broadway connectivity) were NOT confirmed. Phase 1b confirmed 100% of dominant-class mismatches have a (DS bot + ms mid) joint config achievable WITH the Ace on top. Methodology validation: **the playbook is transferable to the SAME zone for a SECOND pass, and joint-achievability features are a distinct structural axis from single-axis achievability features.** Surgical gating mathematically guarantees prefix-grid neutrality when the prefix slice contains zero target-zone hands.

> **🎯 IMMEDIATE NEXT ACTION (Session 58): THIRD pass on high_only — push further into the headroom.**
>
>   **high_only is STILL the dominant residual at $2,075/1000h within-cat × 40.4% share = $838/1000h whole-grid (~75% of v43's total regret).** S56 ho_v2 + S57 ho_v3 collapsed two axes (DS-only achievability, then DS+ms joint achievability). The next session should:
>
>   **Step 1**: Re-drill HO5 (`drill_high_only_zone_v43_diagnostic.py`) against v43_dt — the residual matrix will have shifted again; new dominant classes will emerge. Likely candidates:
>   - K-top mismatches (the tK_SS_mu → tK_DS_ms class at $17.05/1000h pre-v43 may shift up the ranking).
>   - Mid-suit-only at non-Ace ranks (tK_SS_mu → tK_SS_ms at $7.59/1000h pre-v43).
>   - A-top defensive sub-axes (tA→tK and tA→tQ swaps).
>   - The user-predicted axes (defensive K/Q, T-9-8 top, broadway connectivity) might finally surface as dominant after the SS→DS axis is compressed further.
>
>   **Step 2**: If the new dominant class is a JOINT-axis variant (e.g., ho_v3 generalized to non-Ace tops, or 3-way joint of DS+ms+top-rank), build ho_v4. If a genuinely new axis (defensive top, broadway connectivity, mid-ranks-on-bot), pivot the feature design.
>
>   **Step 3**: Train v44_dt at depth=36 ml=1, 107 features = 103 + 4 ho_v4. Acceptance: −$30/1000h or better on full grid + surgical (all non-high_only categories byte-identical).
>
>   **Alternative targets** if Session 58's drill reveals nothing actionable in high_only: trips zone ($55/1000h whole-grid) or three_pair ($35/1000h) — same drill + 4-feature shape applies. Recommend high_only first since the upside is much larger AND the playbook is now proven for SECOND passes.
>
>   **Methodology candidates worth testing** (from S57's lowest-importance-per-ship ship):
>   - Are joint-achievability features ALWAYS the right design after a single-axis collapse, or did the high_only zone happen to have an unusually rich joint structure?
>   - Can the playbook handle a zone where Phase 1b reveals NO further single-axis structural delta (i.e., the residual is irreducibly multi-axis noise)?

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

## Resume Prompt (Session 58)

```
Resume Session 58 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 57)
- DECISIONS_LOG.md (latest: Decision 092 — v43_dt new ML champion)
- SESSION_57_V43_DT_REPORT.md
- STRATEGY_GUIDE.md (Session 57 entry in Part 1; updated ML champion table in Part 2)
- analysis/scripts/strategy_v43_dt.py — current ML champion
- analysis/scripts/high_only_aug_v3_features_gated.py — template feature suite (ho_v3 JOINT)
- analysis/scripts/drill_high_only_zone_v42_diagnostic.py — Phase 1 drill template
- analysis/scripts/drill_high_only_v42_mismatch_handlevel.py — Phase 1b drill template

State (end of Session 57):
- Rule chain production: v52_full_high_only_handler (17 rules; UNCHANGED) at
  $2,498 full / $1,522 prefix.
- ML champion: v43_dt (NEW) at $1,123 full / $686 prefix; 2.18M leaves at
  depth=36 ml=1; 103 features (99 + 4 ho_v3 JOINT).
- Cumulative ML v32 → v43 = −$592 full / −$218 prefix (8 ML ships).
- High_only zone gap collapsed twice: $2,796 → $2,411 → $2,075 (−$721 / −25.8%).

USER-PRIORITY DIRECTION FOR SESSION 58:

**THIRD pass on high_only — push further into the headroom.**

high_only is STILL the dominant residual at $2,075/1000h within-cat ×
40.4% share = $838/1000h whole-grid (~75% of v43's total regret).
S56 ho_v2 collapsed the DS-only axis; S57 ho_v3 collapsed the DS+ms-joint
axis. The remaining residual likely lives in:

  Axis A: K-top SS→DS mismatches (tK_SS_mu → tK_DS_ms was $17.05/1000h
          pre-v43; may shift up after S57).
  Axis B: Mid-suit-only at non-Ace ranks (tK_SS_mu → tK_SS_ms etc.).
  Axis C: A-top alternative-rank mismatches (tA→tK $13.77, tA→tQ $4.82
          pre-v43).
  Axis D: Defensive triggers, T-9-8 top choice, broadway connectivity
          (the user's S57 predictions that didn't dominate then but
          might surface now after SS→DS is further compressed).

4-phase plan:
Phase 1: Re-drill high_only against v43_dt (NEW residual matrix; the
         A-top SS→DS class will be smaller; new dominant classes will
         emerge — most likely K/Q-top SS→DS or non-Ace mid-suit-only).
Phase 1b: Hand-level inspection of the new top class — identify which
          structural axis it represents.
Phase 2 v4: Design 4 rank-valued conditional features for the
          highest-leverage NEW axis.
Train v44_dt (depth=36 ml=1, 107 features = 103 + 4 ho_v4).

Acceptance: −$30/1000h or better on full grid + surgical (all
non-high_only categories byte-identical).

Alternative targets if Session 58's drill reveals nothing actionable:
trips zone ($55/1000h whole-grid) or three_pair ($35/1000h) — same
drill + 4-feature shape applies. Recommend high_only first since the
upside is much larger AND the playbook is now proven for SECOND passes.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Methodology rule (Session 57 NEW): the 4-phase playbook is transferable
  to the SAME zone for a SECOND pass without modification.
- Methodology rule (Session 57 NEW): a zone can be collapsed multiple
  times by stacking conditional feature axes; gains compound surgically.
- Methodology rule (Session 57 NEW): joint achievability is a distinct
  structural axis from single-axis achievability; joint features are NOT
  redundant with the components.
- Methodology rule (Session 57 NEW): importance can be low (#60+) and
  lift can still ship via surgical gating on a high-leverage subset.
- Methodology rule (Session 57 NEW): user predictions can be wrong about
  WHICH axis dominates even after one pass collapses one axis; the data
  dictates the axis, not the human intuition.
- Methodology rule (Session 56): the 4-phase playbook is fully
  transferable to the largest population zone without modification.
- Methodology rule (Session 56): when feature design exactly matches
  the structural delta, Phase 1b confirmation collapses to 100/0.
- Methodology rule (Session 56): surgical-gating means prefix-grid
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
