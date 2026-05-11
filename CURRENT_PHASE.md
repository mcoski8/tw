# Current: Sprint 8 — Session 59 NULL RESULT. The 4-phase playbook applied for the **4th consecutive time on the same high_only zone** does **NOT** ship: v45_dt grades at exactly $1,081/1000h (the same as v44_dt) on the full grid. The ho_v5 features (non-max joint mid_high quality, combined-quality scalar, max-in-bot-pair count, 4f topMax count) added only **+9 leaves** to v44's 2.248M-leaf tree — essentially no new splits. Drills HO11/HO12/HO13 confirmed the data signal is real and large (K × DS_NO_JOINT × best_top=Q × mid_h≥J: oracle picks non-max-route 67%, v44 only 36%, a $9.76/1000h cell) but the DT at depth=36 ml=1 has saturated: each leaf already covers ~2.7 training examples, and the new v5 signals are mathematically derivable from v4 features (best_combined_q = max_top_rank + max_mid_high; n_max_in_bot_pair is implied by n_configs + suit profile). v44_dt remains the ML champion. **Strategies of record unchanged:** v52_full_high_only_handler ($2,498/$1,522), v44_dt ($1,081/$686). The two tracks diverge by $1,417/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 60): Pivot away from naive feature-augmentation on high_only.** The S59 null result establishes that depth=36 ml=1 + 2.25M leaves is a hard ceiling for the current DT class on high_only. Three options, in priority order:
>
>   **Option C — Surgical rule on K × DS_NO_JOINT × best_top=Q × mid_h≥J cell ($9.76/1000h whole-grid).** HO13 isolated 18,144 hands where oracle routes to (top=Q, DS bot, ms mid) 67% of the time while v44 routes only 36%. A rule chain entry covering this single cell could lift the rule chain by an estimated $5–7/1000h (lift on rule chain depends on whether the rule fires inside the v52 trip/two_pair/pair handlers' jurisdiction). The rule chain hasn't been touched since v52 (S53); this is a clean attack vector. Implementation: write `rule_18_K_high_DS_NO_JOINT_route.py` + grade vs v52.
>
>   **Option B — Pivot to trips zone** ($1,194 within-cat × 4.6% share = $55/1000h whole-grid). The 4-phase playbook on a fresh zone may have room; trips_pair and three_pair were already touched, but trips itself was last attacked in S39's trips_v2 features. Estimated lift: $20–40/1000h if the playbook generalizes. Implementation: drill trips zone residuals on v44_dt; design 4 trips-gated features; train v45_dt_v2 (a fresh v45 number since v45_dt didn't ship).
>
>   **Option A — Try a different model class on high_only** (gradient-boosted trees / RF ensemble). Higher computational cost. The data signal is there ($9.76/1000h cell); the question is whether a non-DT model can capture it. Estimated lift: unknown; could be $30–60/1000h or $0.
>
>   **Recommendation: Option C first (surgical rule).** Fastest to implement (~30 min), bounded downside, addresses a precisely-identified residual. If it ships, we get a rule-chain entry and ML champion unchanged. If it doesn't, we still learn whether rules can attack the residual where ML can't.
>
>   **4-phase playbook for Option C:**
>
>   **Phase 1 — Drill RU18**: deep-dive the 18,144 hands in the K × DS_NO_JOINT × best_top=Q × mid_h≥J cell. What does oracle pick beyond just (Q on top)? Bot DS suit profile distribution? Bot pair high? Mid pair high? Is there a clean trigger condition that fires on >90% of the cell?
>
>   **Phase 1b — Hand-level**: inspect 50 hands. Confirm the trigger condition uniquely identifies the cell without false positives in other K-high subcategories.
>
>   **Phase 2 — Write rule_18_K_high_DS_NO_JOINT_route.py**: gated to `max_rank == K AND has_K_on_top_DS_bot achievable == False AND n_joint_topNonMax > 0 AND best_top_topNonMax == Q AND best_mid_high_topNonMax >= J`. Action: route to (top=Q, DS bot via [the rule's chosen suit pair], ms mid via [the rule's chosen suit]).
>
>   **Phase 3 — Train v53_rule_chain (rules 1..18) + grade** vs v52. Acceptance: ≥−$5/1000h full grid + non-K-high categories byte-identical.
>
>   **Time budget:** ~1 hour total (drill 15 min, rule 20 min, grade 25 min). Significantly cheaper than the v45 attempt.

> **❌ NULL RESULT (Session 59):**
> 1. **v45_dt did NOT ship.** Full-grid lift = $0/1000h. Prefix lift = $0/1000h (by design, high_only-gated). v44_dt remains the ML champion.
> 2. The 4 ho_v5 features rank #66/#97/#106/#110 (0.07%/0.01%/0.01%/0.00%) — the LOWEST per-ship in project history. Combined with **+9 leaves** vs v44's 2.248M (essentially zero new splits), this signals saturation.
> 3. The data signal is real and was empirically verified (HO13 stratification: K × DS_NO_JOINT × best_top=Q × mid_h≥J is a $9.76/1000h cell with a 30.5% gap between oracle's pick rate and v44's). But it's not capturable by adding more DT features at current hyperparameters.

> **✅ ARTIFACTS (Session 59):**
> 1. **`analysis/scripts/drill_high_only_v44_deepdive.py`** — HO11+HO12+HO13 consolidated drill on v44_dt's residuals. Reusable for future v44-baseline drills.
> 2. **`analysis/scripts/drill_high_only_v44_nonmax_quality.py`** — HO13 follow-up: non-max joint quality stratification by (max_rank × best_top × best_mid bucket).
> 3. **`analysis/scripts/high_only_aug_v5_features_gated.py`** + persist + train + strategy + grade — full v5 chain wired up (kept as documented null attempt; useful when Session 60 considers Option A / Option D).
> 4. **`data/v45_dt_model.npz`** (1260.57 MB) — trained but NOT shipping; kept for reference.
> 5. **`data/drill_ho_v44_per_hand_structural.parquet`** (15.0 MB) — per-hand v44 residual structure; reusable.
> 6. **`SESSION_59_V45_DT_REPORT.md`** — null-result session report at repo root.

> **📓 METHODOLOGY LESSONS (Session 59 NEW):**
> - **The 4-phase playbook hits a saturation ceiling at depth=36 ml=1 + ~2.25M leaves on 6M rows.** Three passes on high_only worked. The 4th does not, despite the data signal being clear. Bottleneck is no longer feature design but DT capacity.
> - **Low importance AND no leaf growth is a stronger null signal than importance alone.** v44 had low importance (#47–#95) but +70K leaves; v45 has lower importance AND +9 leaves — the combination is the leading indicator.
> - **Mathematically redundant features don't help at saturation.** ho_v5 signals are linear combinations or derivations of ho_v4 + base features; the DT already exploits the underlying axis.
> - **Drill stratification can identify a residual gap that is not closeable with the current model class.** HO13 found a 30.5% gap on an $9.76/1000h cell — a real signal that ML can't capture but a rule could.
> - **Number of consecutive same-zone playbook passes ≤ 3 under current DT hyperparameters.** Beyond that, switch zones, switch model class, or switch lever (rules).

> Updated: 2026-05-11 (Session 59 — NULL)

---

## Headline state at end of Session 59 (UNCHANGED from S58)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion (UNCHANGED).** 2.25M leaves, 107 features at depth=36 ml=1; $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v45_dt (S59 NULL) | Trained but does NOT ship; kept for reference. 2.25M+9 leaves, 111 features. | `analysis/scripts/strategy_v45_dt.py` + `data/v45_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v42_dt | S56 ML champion. | `analysis/scripts/strategy_v42_dt.py` + `data/v42_dt_model.npz` |
| v41_dt | S55 ML champion. | `analysis/scripts/strategy_v41_dt.py` + `data/v41_dt_model.npz` |
| v40_dt | S55 first ship; replaced within-session. | `analysis/scripts/strategy_v40_dt.py` + `data/v40_dt_model.npz` |
| v39_dt | S54 ML champion. | `analysis/scripts/strategy_v39_dt.py` + `data/v39_dt_model.npz` |
| v36_dt | Older ML champion (S53 overnight; 1.06M leaves; $1,649). | `analysis/scripts/strategy_v36_dt.py` + `data/v36_dt_model.npz` |
| v34_dt | Older ML champion (874K leaves; $1,681). | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v47_rule16_Qhigh_DS / v46_rule15_Khigh_DS / v45_rule14_Ahigh_DS | Predecessor rule chains. | various |
| v44_rule13_three_pair_DS / v43_rule12 / v42 / v41 / v40b | Earlier rule chains. | various |
| v32_dt | Older ML baseline. | various |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines. | various |

**Capacity + feature progression (UNCHANGED — v44 still champion):**

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
| v45 (NULL) | 36 | 1 | 111 (107+4 ho_v5) | 2,248,182 (+9) | $1,081 (+$0) | 64.80% (+0.00%) |

**Cumulative ML arc (v32 → v44, UNCHANGED):** **−$634/1000h on full grid across 9 ships.** v45 attempt: $0 (does not ship).

**Per-category residuals (UNCHANGED from S58):**

| Category | n_hands | share | v44 within-cat | $/1000h whole-grid |
|---|---:|---:|---:|---:|
| **high_only** | 1,226,940 | 40.4% | $1,868 | $755 |
| pair | 2,800,512 | 36.2% | $1,097 | $396 |
| trips | 328,185 | 4.6% | $1,194 | $55 |
| two_pair | 1,338,480 | 14.5% | $363 | $52 |
| three_pair | 114,400 | 2.2% | $1,613 | $35 |
| trips_pair | 171,600 | 1.8% | $281 | $5 |
| composite | 14,742 | 0.2% | $960 | $2 |
| quads | 14,300 | 0.1% | $545 | $1 |

**high_only is STILL the dominant residual** at $755/1000h whole-grid (~70% of total v44 regret). But naive 4th-pass feature engineering can no longer attack it under current DT hyperparameters.

**Human-strategy progression — UNCHANGED from end of S53:**

(table omitted — see S58 CURRENT_PHASE.md; no change in S59)

**The two production tracks STILL diverge by $1,417/1000h** (v52 rule chain at $2,498; v44_dt at $1,081). UNCHANGED.

---

## What Session 59 produced

**Code:**
- 2 drills (HO11+HO12+HO13 consolidated, HO13 follow-up cross-tab)
- 1 feature module (high_only_v5) + 1 persistence script
- 1 trainer (v45) + 1 strategy + 1 grader

**Documentation:**
- `STRATEGY_GUIDE.md` — Part 1 Session 59 NULL entry (appended); Part 2 unchanged (v44 still champion)
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 094 (NULL) appended
- `SESSION_59_V45_DT_REPORT.md` — repo-root null-result report

**Models persisted (NOT shipping):**
- `data/v45_dt_model.npz` (1260.57 MB; kept for reference)
- `data/feature_table_high_only_aug_v5_gated.parquet` (19.21 MB)
- `data/drill_ho_v44_per_hand_structural.parquet` (15.0 MB; reusable for future v44 drills)

---

## Resume Prompt (Session 60)

```
Resume Session 60 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 59 — NULL result)
- DECISIONS_LOG.md (latest: Decision 094 — v45_dt NULL result)
- SESSION_59_V45_DT_REPORT.md (the null-result session report)
- STRATEGY_GUIDE.md (Session 59 NULL entry in Part 1; Part 2 unchanged)
- analysis/scripts/strategy_v44_dt.py — current ML champion
- analysis/scripts/strategy_v52_full_high_only_handler.py — production rule chain
- analysis/scripts/drill_high_only_v44_deepdive.py — drill template
- analysis/scripts/drill_high_only_v44_nonmax_quality.py — cross-tab template

State (end of Session 59 = end of Session 58, unchanged):
- Rule chain production: v52_full_high_only_handler (17 rules; UNCHANGED)
  at $2,498 full / $1,522 prefix.
- ML champion: v44_dt (UNCHANGED) at $1,081 full / $686 prefix; 2.25M
  leaves at depth=36 ml=1; 107 features.
- v45_dt attempt: NULL ($0/1000h lift, +9 leaves, lowest-importance
  features in project history). Kept on disk for reference.
- high_only STILL dominant residual at $755/1000h whole-grid (~70%
  of v44's regret) but no longer ML-attackable under current
  hyperparameters.

DIRECTION FOR SESSION 60 (recommended: Option C — surgical rule):

The S59 null established that the 4-phase ML-feature playbook is
saturated on high_only at depth=36 ml=1. HO13 surfaced a specific
$9.76/1000h cell (K × DS_NO_JOINT × best_top=Q × mid_h>=J)
that ML can't reach but a rule might.

Option C (recommended): Write rule_18_K_high_DS_NO_JOINT_route.py.

Phase 1 — Drill RU18: deep-dive the 18,144 hands in the cell. What
does oracle pick beyond just (Q on top)? Bot DS suit profile?
Bot pair high? Mid pair high?

Phase 1b — Hand-level: 50 hands. Confirm a clean trigger.

Phase 2 — Write rule_18_K_high_DS_NO_JOINT_route.py gated to:
  max_rank == K AND
  no joint with K on top (n_joint_topMax == 0) AND
  non-max joint exists (n_joint_topNonMax > 0) AND
  best non-max top == Q AND
  best non-max mid_high >= J(11)

Action: route to (top=Q, DS bot, ms mid) per the rule's analysis.

Phase 3 — Train v53_rule_chain (rules 1..18) + grade vs v52.
Acceptance: >=-$5/1000h full grid + non-K-high categories byte-identical.

Alternative options if Option C doesn't work:
- Option B: pivot to trips zone ($55/1000h whole-grid)
- Option A: try a different model class (gradient boosting / RF) on
  high_only
- Option D: increase DT training data via synthetic-hand augmentation

Time budget: ~1 hour for Option C.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Methodology rule (Session 59): the 4-phase playbook saturates at 3
  consecutive same-zone passes under depth=36 ml=1. Beyond that,
  switch zones / model / lever.
- Methodology rule (Session 59): low importance + no leaf growth is
  the leading indicator of a null ship.
- Methodology rule (Session 59): drill stratification can identify
  residual gaps that are not closeable with the current model class.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
