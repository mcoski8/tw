# Current: Sprint 8 — Session 59 NULL RESULT on v45_dt set up a methodology pivot. **Naive 4th-pass ML feature engineering on high_only has saturated** (depth=36 ml=1 + 2.25M leaves + S58's v44 already captures everything ho_v5 features encode), but the diagnostic drills (HO11/HO12/HO13) surfaced **measurable, localized EV gaps** that ML can't reach. Examples: at K × DS_NO_JOINT × best_top=Q × mid_h≥J (n=18,144), oracle picks the non-K-on-top route 67% while v44 picks it only 36% — a $9.76/1000h cell. Existing rules 14/15/16/17 cover high_only at the WHOLE-max-rank level but were never audited cell-by-cell. **Session 60+ pivots to a per-max-rank rule catalog with explicit rule testing** — for each max-rank's structural cells, write candidate deterministic rules, apply them to every hand in the cell, measure capture % against oracle ceiling, ship to v53 only when both catalog-worthy (≥40% gap closure within cell, +$3/1000h within-cell, statable in one sentence) AND production-worthy (≥$5/1000h whole-grid lift, zero non-target regression). Cells where no rule meets Threshold 1 are formally labeled **ML-only territory** in the catalog. The deliverable is `HIGH_ONLY_RULE_CATALOG.md` — a teachable per-cell strategy doc that the project has been pointing at since CLAUDE.md ("a condensed decision tree / hierarchy of rules that a human can memorize and apply in <30 seconds, matching the solver 95–99% of the time"). **Strategies of record UNCHANGED:** v52_full_high_only_handler ($2,498/$1,522), v44_dt ($1,081/$686). The two tracks diverge by $1,417/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 60): A-high cell-by-cell audit + build the test harness.**
>
>   A-high is the right starting zone because (a) it's the biggest high_only sub-population (660,660 hands; $182/1000h whole-grid residual), (b) Rule 14 is the oldest and most stress-tested rule at the whole-max-rank level (+$131/1000h whole-grid when shipped in S50 — the LARGEST single-rule lift in project history), (c) the cell-level gaps at A-high are the SMALLEST of any max-rank (oracle drops A off top only 6% in DS_NO_JOINT and 19% in DS_NO_MAXTOP), so if we can't even refine A-high the whole approach is suspect, and (d) the test harness built for A-high is reused for K/Q/J/T/9/8 — A-high pays for the scaffolding.
>
>   **5-PHASE PLAN (Session 60):**
>
>   **Phase 1 — Build the test harness.** Write `analysis/scripts/test_rule_catalog.py`. Interface:
>   ```python
>   test_rule_on_cell(
>       rule_fn,                  # hand → setting_index (or None to skip)
>       cell_predicate_fn,        # hand_id → bool (e.g., "max=A AND cell=DS_NO_JOINT")
>       oracle_grid,              # data/oracle_grid_full_realistic_n200.bin
>       canonical_hands,
>       baselines=[v52_fn, v44_fn],
>   ) → CatalogResult(
>       n_hands_in_cell,
>       rule_pct_optimal,         # % of cell hands where rule picks oracle's argmax
>       rule_mean_ev,
>       oracle_ceiling_ev,
>       capture_pct,              # (rule_ev - null_ev) / (oracle_ev - null_ev)
>       gap_closure_pct,          # vs v52: (rule_ev - v52_ev) / (oracle_ev - v52_ev)
>       lift_vs_v52_within_cell,  # $/1000h within cell population
>       lift_vs_v52_whole_grid,   # $/1000h scaled to whole 6M grid
>       lift_vs_v44_within_cell,
>       top_mismatch_classes,     # where rule disagrees with oracle, by EV loss
>   )
>   ```
>   The harness reuses `data/drill_ho_v44_per_hand_structural.parquet` for cell tags and the oracle grid for EV evaluation. Cell predicates are parameterized (max_rank × cell name).
>
>   **Phase 2 — Audit Rule 14 itself.** For each of A-high's 5 structural cells (JOINT_HIGH, JOINT_MED, JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY), measure: how much oracle ceiling does Rule 14 actually capture? Where does Rule 14 leak EV vs oracle? This is the baseline we're trying to improve.
>
>   **Phase 3 — Propose 2–4 candidate refinement rules per leaky cell.** For cells where Rule 14 leaks > $3/1000h within-cell, design candidate rules that handle the residual. Examples (TBD by data):
>   ```python
>   def rule_A_DS_NO_MAXTOP_drop_if_max_bot_pair_K(hand):
>       """If A-high AND DS_NO_MAXTOP AND best DS bot has A-pair, drop A to bot, take K top."""
>       ...
>   ```
>   Each candidate is one Python function with a one-sentence docstring summarizing the principle.
>
>   **Phase 4 — Test every candidate against every leaky cell.** For each cell, rank candidates by capture_pct + lift. Apply thresholds:
>   - **Catalog-worthy (Threshold 1):** ≥ 40% gap closure between v52 and oracle ceiling on the cell AND ≥ +$3/1000h within-cell vs v52 AND one-sentence statable.
>   - **Production ship (Threshold 2):** Threshold 1 met AND ≥ +$5/1000h whole-grid lift on full N=200 grid AND zero non-targeted regression.
>   - **ML-only acknowledgment (Threshold 3):** No candidate clears Threshold 1 → cell labeled "ML-only" in catalog. Document why (e.g., "oracle's pick depends on subtle suit-pair dynamics no simple rule captures").
>
>   **Phase 5 — Write `SESSION_60_A_HIGH_CATALOG.md`.** One-page-per-cell catalog of Rule 14's current capture + candidate rule test results + cell verdict. Ship Threshold-2-passing rules as Rules 18+ in v53. Repository pattern reused for S61 (K-high) through S65 (final aggregate).
>
>   **TIME BUDGET:** Session 60 is harness-heavy. Probably 2 hours: harness 45 min, Rule 14 audit 30 min, candidate testing 45 min, catalog doc 30 min. Subsequent sessions (K/Q/J/T/...) reuse the harness and run ~1 hour each.
>
>   **SUCCESS CRITERIA:**
>   - Test harness works on Rule 14 alone (sanity-check it reproduces v45_rule14's shipped +$131/1000h).
>   - At least one A-high cell has its Rule 14 capture % measured.
>   - Either ship at least one refinement rule (Threshold 2) OR honestly label at least one cell ML-only (Threshold 3).
>   - `SESSION_60_A_HIGH_CATALOG.md` produced as the first page of the catalog.

> **❌ NULL RESULT (Session 59 — for context):**
> 1. **v45_dt did NOT ship.** Full-grid lift = $0/1000h. v44_dt remains the ML champion.
> 2. The 4 ho_v5 features rank #66/#97/#106/#110 (sum 0.09% — LOWEST per-ship). Combined with **+9 leaves** vs v44's 2.248M, signals depth=36 ml=1 saturation.
> 3. The data signal is real (HO13 stratification: K × DS_NO_JOINT × best_top=Q × mid_h≥J is a $9.76/1000h cell with a 30.5% gap between oracle's pick rate and v44's). But it's not capturable by adding more DT features at current hyperparameters → motivates the catalog approach.

> **✅ ARTIFACTS to reuse from S58/S59:**
> 1. **`data/drill_ho_v44_per_hand_structural.parquet`** (15.0 MB) — per-hand v44 residual structure with cell tags. Foundation for Session 60+ catalog work.
> 2. **`data/drill_ho_v43_nonmax_joint.parquet`** (4.7 MB) — non-max joint achievability + best alt top/mid quality. Reusable.
> 3. **`data/oracle_grid_full_realistic_n200.bin`** (~2.5 GB) — ground-truth EV for all 6M hands × 105 settings. The arbiter.
> 4. **`SESSION_58_HIGH_ONLY_DECISION_MATRIX.md`** — per-max-rank × per-cell oracle TOP/BOT/MID profile. Use as the "what should the rule do?" reference when designing candidate rules.
> 5. **`SESSION_59_V45_DT_REPORT.md`** + `data/v45_dt_model.npz` — null-result artifacts kept for reference (Session 60+ does NOT use them).

> **📓 METHODOLOGY (Session 60+):**
> - **Capture % thresholds:**
>   - **Threshold 1 (Catalog-worthy):** ≥ 40% gap closure between v52 and oracle ceiling on the cell AND ≥ +$3/1000h within-cell AND one-sentence statable.
>   - **Threshold 2 (Production ship):** Threshold 1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression.
>   - **Threshold 3 (ML-only):** No candidate clears Threshold 1 → cell formally labeled ML-only.
> - **Cell decomposition (use the existing 6-cell scheme):** JOINT_HIGH, JOINT_MED, JOINT_LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY, NEITHER. Defined in `drill_high_only_v44_deepdive.py`.
> - **Audit existing rules FIRST.** Before proposing new candidates, measure how the current rule (14 for A, 15 for K, 16 for Q, 17/v52 defensive for J/T/9/8) performs cell-by-cell. The candidate rules REFINE within leaky cells; they don't replace the broader rule.
> - **Speed is not necessary — clarity and perfection is.** (User directive S59.) Each session covers one max-rank fully; the catalog accumulates over 5–6 sessions. End with a complete `HIGH_ONLY_RULE_CATALOG.md`.

> Updated: 2026-05-11 (Session 59 end — methodology pivot to catalog approach)

---

## Headline state at end of Session 59 (UNCHANGED from S58)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v52_full_high_only_handler** | **PRODUCTION rule chain** (17 rules; UNCHANGED since S53). $2,498 full / $1,522 prefix. | `analysis/scripts/strategy_v52_full_high_only_handler.py` |
| **v44_dt** | **PRODUCTION ML champion (UNCHANGED).** $1,081 full / $686 prefix; 2.25M leaves; 107 features. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |
| v45_dt (S59 NULL) | Trained but does NOT ship. 2.25M+9 leaves, 111 features. | `analysis/scripts/strategy_v45_dt.py` + `data/v45_dt_model.npz` |
| v43_dt | Predecessor ML champion (S57). | `analysis/scripts/strategy_v43_dt.py` + `data/v43_dt_model.npz` |
| v42_dt | S56 ML champion. | `analysis/scripts/strategy_v42_dt.py` + `data/v42_dt_model.npz` |
| v41_dt | S55 ML champion. | `analysis/scripts/strategy_v41_dt.py` + `data/v41_dt_model.npz` |
| v40_dt | S55 first ship; replaced within-session. | `analysis/scripts/strategy_v40_dt.py` + `data/v40_dt_model.npz` |
| v39_dt | S54 ML champion. | `analysis/scripts/strategy_v39_dt.py` + `data/v39_dt_model.npz` |
| v36_dt / v34_dt / v32_dt | Older ML baselines. | various |
| v45_rule14_Ahigh_DS (Rule 14 standalone) | Rule 14 fired against v44_rule13 baseline. Predecessor in chain. | `analysis/scripts/strategy_v45_rule14_Ahigh_DS.py` |
| v46_rule15_Khigh_DS / v47_rule16_Qhigh_DS | Predecessor rule chains. | various |
| v44_rule13_three_pair_DS / earlier | Predecessor rule chains. | various |

**Per-category residuals at end of S59 (UNCHANGED from S58):**

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

**high_only is STILL the dominant residual** ($755/1000h whole-grid = ~70% of v44's total regret). Session 60+ attacks it via the catalog methodology.

**Existing high_only rules and their whole-population shipped lifts:**

| Max-rank | Rule | Session | Whole-grid lift when shipped | Status entering S60 |
|---|---|---|---|---|
| A | Rule 14 | S50 | +$131 | Cell-level audit NOT done; refinement candidates TBD |
| K | Rule 15 | S51 | +$51 | Cell-level audit NOT done |
| Q | Rule 16 | S52 | +$19 | Cell-level audit NOT done |
| J/T/9/8 (defensive) | Rule 17 / v52 | S53 | +$17 | Cell-level audit NOT done |

**Two production tracks at end of S59 (UNCHANGED):** Rule chain $2,498; ML champion $1,081; diverge by $1,417/1000h.

---

## Session 60+ catalog sequence

| Session | Max-rank focus | Existing rule | Population | $/1000h wg residual |
|---|---|---|---|---|
| **60** | **A-high** | Rule 14 | **660,660 (53.8% of high_only)** | **$182.51** |
| 61 | K-high | Rule 15 | 330,330 (26.9%) | $110.94 |
| 62 | Q-high | Rule 16 | 150,150 (12.2%) | $55.24 |
| 63 | J-high | Rule 17 (HIMID branch) | 60,060 (4.9%) | $23.43 |
| 64 | T/9/8 combined | Rule 17 (defensive branch) | 25,740 (2.1%) | $9.29 |
| 65 | Aggregate + cross-cell rules | All | All high_only | All |

Total addressable via catalog audit: $381.41/1000h whole-grid (= v44's full high_only residual). Even capturing 30% of that via rules = ~$115/1000h on the rule chain, $0 on ML.

---

## Resume Prompt (Session 60 — A-high catalog audit + harness)

```
Resume Session 60 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S59 — methodology pivot to
  per-max-rank rule catalog with explicit testing)
- DECISIONS_LOG.md (latest: Decision 094 — v45_dt NULL result)
- SESSION_59_V45_DT_REPORT.md (the null-result context)
- SESSION_58_HIGH_ONLY_DECISION_MATRIX.md (per-max-rank × per-cell
  oracle TOP/BOT/MID profile — the reference for designing candidate rules)
- STRATEGY_GUIDE.md Part 1 — Session 59 NULL entry
- analysis/scripts/strategy_v52_full_high_only_handler.py — current
  rule chain (the v52 production rule chain to extend)
- analysis/scripts/strategy_v44_dt.py — ML champion (the cell-level
  benchmark; rule must close gap toward this, not necessarily beat it)
- analysis/scripts/strategy_v45_rule14_Ahigh_DS.py — Rule 14 standalone
  (the rule being audited cell-by-cell this session)
- analysis/scripts/drill_high_only_v44_deepdive.py — cell decomposition
  reference (JOINT_HIGH/MED/LOW, DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY,
  NEITHER classification)

State (end of Session 59):
- Rule chain production: v52_full_high_only_handler (17 rules; UNCHANGED
  since S53) at $2,498 full / $1,522 prefix.
- ML champion: v44_dt (UNCHANGED) at $1,081 full / $686 prefix;
  2.25M leaves at depth=36 ml=1; 107 features.
- S59 attempted a 4th ho_v5 pass; NULL ($0/1000h). v44 retained.
- high_only STILL dominant residual at $755/1000h whole-grid (~70%
  of v44's regret) but naive feature-augmentation has saturated at
  depth=36 ml=1.

USER DIRECTIVE (S59 close):
- The S58 decision matrix described oracle behavior per cell but never
  tested whether deterministic rules can actually capture it.
- Existing rules 14/15/16/17 cover high_only at the whole-max-rank
  level but were never audited cell-by-cell.
- Cell-level gaps are known and quantified (e.g., Rule 15 keeps K on
  top 100% but oracle drops K 34% in DS_NO_JOINT; Rule 14 keeps A on
  top 100% but oracle drops A 19% in DS_NO_MAXTOP).
- "Speed is not necessary — clarity and perfection is."

DIRECTION FOR SESSION 60 (A-high catalog audit + harness):

A-high is the right starting zone: biggest population (660K hands,
$182/1000h wg residual), oldest and most-tested rule (Rule 14 at +$131
shipped), smallest cell-level gaps (oracle drops A off top only 6% in
DS_NO_JOINT and 19% in DS_NO_MAXTOP — the cleanest test of whether
cell-level refinement is even worth the effort).

5-PHASE PLAN (Session 60):

Phase 1 — Build the test harness.
  Write `analysis/scripts/test_rule_catalog.py`. The harness takes a
  candidate rule function (hand → setting_index), a cell predicate
  (e.g., "max=A AND cell=DS_NO_JOINT"), the oracle grid, and a list
  of baselines (v52, v44, Rule 14 standalone). It returns:
    - n_hands_in_cell
    - rule_pct_optimal (% of cell where rule matches oracle argmax)
    - rule_mean_ev vs oracle_ceiling_ev
    - capture_pct = (rule_ev - null_pick_ev) / (oracle_ev - null_pick_ev)
    - gap_closure_pct = (rule_ev - v52_ev) / (oracle_ev - v52_ev)
    - lift_vs_v52_within_cell ($/1000h within cell)
    - lift_vs_v52_whole_grid ($/1000h scaled to 6M)
    - lift_vs_v44_within_cell
    - top_mismatch_classes (where rule disagrees with oracle, by $)
  Reuse data/drill_ho_v44_per_hand_structural.parquet for cell tags.

Phase 2 — Audit Rule 14 itself.
  For each of A-high's 5 cells (JOINT_HIGH, JOINT_MED, JOINT_LOW,
  DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY), run the harness against
  strategy_v45_rule14_Ahigh_DS. Measure capture_pct and gap_closure_pct
  per cell. Identify "leaky" cells (those where Rule 14 leaks > $3/1000h
  within-cell vs oracle).

Phase 3 — Propose 2-4 candidate refinement rules per leaky cell.
  For each leaky cell, design candidate rules guided by the S58 decision
  matrix (oracle's modal TOP/BOT/MID per cell). Each candidate is one
  Python function with a one-sentence principle. Examples (TBD by data):
    - rule_A_DS_NO_MAXTOP_drop_if_max_bot_pair_high(hand) — "drop A to
      bot when DS bot would contain A as suited pair"
    - rule_A_DS_NO_JOINT_mid_suited_priority(hand) — "if A on top + DS
      bot, prefer the (top=A, DS bot, ms mid) candidate where mid_high
      is highest"
  Keep candidates LOCAL to the cell — gating discipline.

Phase 4 — Test every candidate against every leaky cell.
  Apply 3 thresholds:
    Threshold 1 (Catalog-worthy):
      gap_closure_pct >= 40% AND lift_vs_v52_within_cell >= $3/1000h
      AND one-sentence statable.
    Threshold 2 (Production ship into v53):
      Threshold 1 + lift_vs_v52_whole_grid >= $5/1000h
      + zero non-A-high regression on full N=200 grid.
    Threshold 3 (ML-only):
      No candidate clears Threshold 1 → cell labeled ML-only.

Phase 5 — Write SESSION_60_A_HIGH_CATALOG.md.
  One section per A-high cell: oracle's modal pick, Rule 14's capture,
  candidate rule test results, verdict (ships / catalog-only / ML-only).
  If any rule meets Threshold 2: ship as Rule 18 (or Rule 14 v2) in
  v53_high_only_handler. Grade vs v52.

Time budget: ~2 hours. Harness 45 min, audit 30 min, candidates 45 min,
catalog doc 30 min.

ACCEPTANCE for Session 60:
- Harness validated (reproduces v45_rule14's known +$131/1000h whole-grid
  ship as sanity check).
- All 5 A-high cells audited; capture_pct + gap_closure_pct reported.
- At least one candidate rule tested in each leaky cell.
- Either ship at least one refinement rule (Threshold 2) OR honestly
  label at least one cell ML-only (Threshold 3).
- SESSION_60_A_HIGH_CATALOG.md produced as the first page of the
  HIGH_ONLY_RULE_CATALOG.md aggregate (built over S60-S65).

REMINDERS:
- Speed is NOT necessary — clarity and perfection IS.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Reuse data/drill_ho_v44_per_hand_structural.parquet for cell tags.
- Reuse data/oracle_grid_full_realistic_n200.bin for EV evaluation.
- Don't propose candidate rules without first auditing the existing
  rule (Rule 14) for that cell — refinements REFINE within leaky cells,
  they don't replace.
- Threshold 1 gates whether something enters the catalog; Threshold 2
  gates whether it ships to v53; Threshold 3 honestly labels ML-only.

OUTPUT for Session 65 (the endgame, 5-6 sessions away):
- HIGH_ONLY_RULE_CATALOG.md — complete A/K/Q/J/T/9/8 catalog with
  per-cell verdicts.
- v53_high_only_handler (rule chain successor to v52) — every cell
  refinement that ships.
- Honest documentation of which cells are ML-only (v44_dt's exclusive
  territory).
- This becomes the project's first user-facing strategy guide that
  matches the CLAUDE.md goal: "a condensed decision tree / hierarchy
  of rules that a human can memorize and apply in <30 seconds,
  matching the solver 95-99% of the time."
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
