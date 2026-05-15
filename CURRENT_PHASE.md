# Current: Sprint 8 — Session 84 MIXED verdict on v58 (LOW × PMID_DS_MAXTOP); production stays at v57; S83 playbook is cell-dependent not universal; S85 picks the next under-covered cell with the lesson that small-residual cells are label-noise-sensitive

S84 extended S83's Option D-revised playbook (rule extraction on under-rule-covered weak-hand zones) to the second-largest under-covered LOW pair cell, **PMID_DS_MAXTOP**. The candidate Rule 21 ("when LOW pair × PMID_DS_MAXTOP × top_alt_rank ≥ gate, force PMID_tmax_DS") fired SHIP on the prefix grid (+$5.59/1000h prefix lift at gate=5) but NULL on the full grid (+$1.36/1000h whole-grid lift). The 4× grid disagreement at the SHIP threshold is itself the verdict: **MIXED**, by the S83 precedent that requires both grids to clear $5 for a clean SHIP.

The disagreement traces to a label-noise effect: same canonical hands, but N=200 (full grid) shows 30% swap-wrong rate vs N=1000 (prefix) at 12% swap-wrong rate. Per S82 Decision 114, this 18pp gap is consistent with N=200 disagreeing with N=1000 on ~32% of PAIR hands' argmax. For S83's cell (residual $59/1000h), the same label noise was negligible — the signal stood above it. For S84's cell (residual $7.24/1000h), label noise can flip the verdict.

**Production state: UNCHANGED.** v57_lo_pair_defensive remains the rule chain. v44_dt remains the ML champion. Rule count stays at 20. Two-track divergence stays at $332/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 85): try the next under-covered LOW pair cell — LOW × PMID_SS_MAXTOP**
>
> S77 ranked LOW pair cells by STRUCTURE leak:
>   1. PMID_DS_NOMAXTOP — $31.00 (S83 SHIPPED Rule 20)
>   2. PMID_DS_MAXTOP — $21.68 (S84 MIXED — did not ship)
>   3. PMID_SS_MAXTOP — $9.71 (S85 default target)
>   4. PMID_OTHER — $11.81 (S85 alternative)
>   5. PBOT_DS_PARTIAL — $4.31 (smaller residual; lower priority)
>   6. PBOT_DS_JOINT — $1.91 (already has Rule 19; mostly closed)
>
> **PMID_SS_MAXTOP** has the structure: bot is single-suited (2+1+1) with max on top — no DS-bot available. The structural choice is between PMID_tmax_SS (default) and possibly routing to PBOT/SPLIT for some subset. Lower a priori expected lift than PMID_DS_MAXTOP, but the population is smaller and potentially cleaner.
>
> **Warning from S84:** S77's headline leak is measured under v44_dt. Production v57 likely closes a significant fraction. Phase A should re-measure under v57 to set realistic expectations BEFORE designing a rule.
>
> ### What S85 should run (default — recipe established in S83, refined in S84)
>
> 1. **Phase A** — Verify cell choice. Inspect S77 cell_stats['LOW|PMID_SS_MAXTOP']. Confirm Rule 20 doesn't fire on this cell (Rule 20 requires PMID_DS achievable; SS_MAXTOP cell precondition is no PMID_DS achievable).
> 2. **Phase B** — Drill v57 on cell. Adapt `drill_v57_low_pmid_ds_maxtop_S84.py` → `drill_v57_low_pmid_ss_maxtop_S85.py`. Filter parquet to cell_idx == 4 (PMID_SS_MAXTOP) AND pair_rank ∈ {2-7}. Run v57. Aggregate (v57_class, oracle_class) mismatches and total leak. **First check: what is v57's residual leak under production? If it's already < $5/1000h, the rule has no ceiling to ship and S85 should pivot to another cell early.**
> 3. **Phase B+** — Discriminator drill. Adapt `drill_v57_pmid_ds_variant_discriminator_S84.py` with appropriate feature candidates for PMID_SS cell. Likely features: max_sing, second_max, bot_pair_high under PMID_SS, presence of PBOT_SS alternative.
> 4. **Phase C** — Write strategy_v58_alt or strategy_v59 with parametric gate; multi-gate grade on full grid + multi-gate grade on prefix (run both — S84 showed they can disagree). Pre-commit SHIP/NULL/MIXED thresholds in code BEFORE running. **Both grids should clear $5 to declare SHIP.**
> 5. **Phase D** — Session-end commit + push + decision + CURRENT_PHASE rewrite.
>
> ### Alternative S85 directions (lower priority)
>
> * **LOW × PMID_OTHER** (S77: $11.81 STRUCTURE / 137,808 hands) — catchall cell, may need richer feature set.
> * **MID pair (8-T) × PMID_DS_NOMAXTOP** — extend Rule 20 to higher pair tier. Test whether rule transfers with shifted max_sing gate.
> * **HIGH_ONLY × J-high and below** (S71: $14.47 + $4.31 STRUCTURE) — different category, same defensive archetype.
> * **Resolve S84 divergence** by running N=1000 labels on the full 128k cell hands (~3-5h compute). Higher diligence cost; lower information yield than testing a new cell. Defer unless multiple subsequent cells also produce small-residual MIXED outcomes.
> * **Headline-goal recalibration** — still available from S82 fork; with S84's MIXED, the question "do small-residual cells have any path to ship under the $5 threshold?" becomes sharper.

> **📓 METHODOLOGY (Session 85+ — refined from S84):**
>
> 1. **Re-measure cell leak under PRODUCTION before designing a rule.** S77's headline uses v44_dt; v52 routing (inherited by v56/v57) differentially closes cells. S84's $21.68 v44 headline became $7.24 under v57 — much less ceiling than the headline suggested. **Phase B's first job is to verify the cell still has enough residual leak to clear the SHIP threshold AT ALL** (per-hand × n_hands × theoretical-ceiling ≥ $5+).
>
> 2. **Pre-committed grader thresholds in code remain the standard.** S84's MIXED outcome demonstrates the pattern's value: the verdict fired mechanically, preventing post-hoc rationalization of SHIP based on the more favorable grid. Continue hardcoding SHIP ≥ $5 / NULL < $2 in graders BEFORE running.
>
> 3. **Multi-gate grading on BOTH grids is the new standard for any candidate that survives Phase B.** S83 ran multi-gate full + single-gate prefix (sufficient when both agreed). S84 showed that grids can disagree at small-residual cells. Multi-gate on both grids costs ~3 min wall and removes ambiguity. Default to running both for any candidate with full-grid lift > $1/1000h.
>
> 4. **For SHIP, both grids must clear $5.** S83 precedent: full $16.47 + prefix $16.81 (ratio 1.02×, both clear). S84: full $1.36 + prefix $5.59 (ratio 4×, only prefix clears) → MIXED. The two-grid-confirmation rule is now project-standard. A prefix-only ship is too sensitive to the canonical-prefix-skew + label-quality interaction.
>
> 5. **The under-rule-covered map needs a production-leak column.** S77's cell ranking by v44 leak is misleading for ship potential. The ordering by **production residual** (= post-v57 leak) is:
>    * PMID_DS_NOMAXTOP: $59.42 under v56 → after Rule 20: ~$43 residual (S83)
>    * PMID_DS_MAXTOP: $7.24 under v57 (S84) — already mostly closed
>    * Others: unmeasured under v57; expect similar closure from v52 routing
>    **Update this column as each cell is drilled under production. Cells with production residual < $10/1000h are unlikely to ship via single-rule extraction.**
>
> 6. **Cell-level outcomes will vary; MIXED/NULL is part of the natural distribution.** Of S83 + S84 = 2 cells tried, 1 shipped and 1 went MIXED. Expect ~50% ship rate on remaining under-covered cells with similarly soft discriminators. **The methodology is the constant; the cell properties determine the outcome.**
>
> 7. **"Speed is not necessary — clarity and perfection is" — S84 reaffirms.** Both decisions in S84 (running multi-gate prefix on full NULL outcome; declaring MIXED instead of post-hoc SHIP) traded a few minutes of compute and a less-decisive-looking verdict for an honest, unambiguous answer. Future sessions should bias toward more grader runs and more honest verdicts over fewer-runs-cleaner-narrative.

> **✅ ARTIFACTS produced in S84:**
> 1. `analysis/scripts/drill_v57_low_pmid_ds_maxtop_S84.py` — Phase B drill (NEW)
> 2. `analysis/scripts/drill_v57_pmid_ds_variant_discriminator_S84.py` — Phase B+ discriminator (NEW)
> 3. `analysis/scripts/strategy_v58_lo_pair_ds_maxtop.py` — v58 candidate (DID NOT SHIP)
> 4. `analysis/scripts/grade_v58_lo_pair_ds_maxtop_S84.py` — Phase C full-grid multi-gate grader (NEW)
> 5. `analysis/scripts/grade_v58_prefix_S84.py` — Phase C single-gate prefix grader (NEW)
> 6. `analysis/scripts/grade_v58_prefix_multigate_S84.py` — Phase C multi-gate prefix grader (NEW)
> 7. `data/session84/drill_v57_low_pmid_ds_maxtop_summary.json` (gitignored)
> 8. `data/session84/drill_v57_pmid_ds_variant_discriminator_summary.json` (gitignored)
> 9. `data/session84/grade_v58_summary.json` (gitignored)
> 10. `data/session84/grade_v58_prefix_summary.json` (gitignored)
> 11. `data/session84/grade_v58_prefix_multigate_summary.json` (gitignored)
> 12. `SESSION_84_REPORT.md` — session report with plain-language TL;DR (NEW)
> 13. `DECISIONS_LOG.md` — Decision 119 (MIXED verdict + methodology lessons) appended
> 14. `CURRENT_PHASE.md` — this file, rewritten for S85
> 15. `STRATEGY_GUIDE.md` — NOT updated (no production change)

> Updated: 2026-05-15 (Session 84 end — v58 candidate MIXED, production unchanged. The Option D-revised playbook is cell-dependent: S83's PMID_DS_NOMAXTOP cell shipped at +$16.81/1000h prefix because the discriminator (max_sing) was sharp (92.8% swap-right) and the residual leak under v56 was large ($59.42). S84's PMID_DS_MAXTOP cell did NOT ship because the discriminator (top_alt_rank) was soft (peak 67% full / 88% prefix) and the residual leak under v57 was small ($7.24 — v52 already closed 78% of v44's headline). The grids disagreed at the threshold (full +$1.36 NULL vs prefix +$5.59 SHIP) due to N=200 vs N=1000 label-noise sensitivity at this small magnitude. By the new two-grid-confirmation standard (both grids must clear $5), the candidate is MIXED. S85 default: try LOW × PMID_SS_MAXTOP using the refined playbook (Phase B re-measures leak under v57 before designing a rule; both grids graded; both must clear $5 to ship). Expect roughly half the remaining under-covered cells to MIXED/NULL given soft discriminators + small residuals.)

---

## Headline state at end of Session 84 (UNCHANGED — no production change)

**Strategies of record (UNCHANGED — v58 candidate did not ship):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v57_lo_pair_defensive** | PRODUCTION rule chain. $1,412.53/1000h full / **$776.88/1000h prefix**. (UNCHANGED since S83 ship) | `analysis/scripts/strategy_v57_lo_pair_defensive.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 13 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$332/1000h (unchanged from S83).** Cumulative since pre-S68: $1,077 = 76% of original $1,409.

**Total project rule count: 20** (unchanged — Rule 21 candidate did not ship).

**S84 candidate result (MIXED — did not ship):**

| Candidate | Hyperparams | Full grid | Prefix grid | Verdict |
|---|---|---:|---:|---|
| v58_lo_pair_ds_maxtop (Rule 21) | top_alt_rank_gate = 5 (J) | +$1.36/1000h NULL | +$5.59/1000h SHIP | **MIXED** — grids disagree; precedent requires both to clear $5 |

---

## Hypothesis cascade status (updated after S84)

| Hypothesis | Description | Status |
|---|---|---|
| H1 | high_only SS+ms route quality | NULL ship +$5 (S73). |
| H2 | high_only route-tradeoff | CLEAN NULL +$0 (S74). |
| Option B (S75) | Gradient boosting at depth=6 / n_est=200 | DECISIVE NULL −$1,392/1000h. |
| S76 / S77 diagnostics | Cross-cat → pair drill | Shipped diagnostics; identified H6/H7/H8 + LOW pair under-coverage. |
| H6 / H7 / H8 (S78) | Pair gated features | CLEAN NULL +$2 prefix. |
| Single-model ML feature-engineering track | At v44 saturating regime | FORMALLY CLOSED (Decision 113). |
| S79 label-noise measurement | Existing N=1000 prefix vs N=200 full | MIXED — 32% oracle disagreement reveals criterion blind spot (Decision 114). |
| A1 (S80) | Retrain v44 DT on N=1000 prefix labels | LIFTS +13.15pp on N=1000 match rate; in-sample evaluation caveat (Decision 115). |
| C2 (S80) | Regularize v44 DT (max_leaf_nodes=500K, ml=5) | NULL −2.13pp on N=1000, −12.24pp on N=200 (Decision 115). |
| A2 (S81/S82) | Targeted N=1000 expansion on two_pair + trips_pair + held-out validation | CLEAN NULL — Lens-3 held-out 63.74% < 72.0% floor (Decision 117). |
| A-path (oracle-label-quality lever) | All variants tested at v44 capacity | FORMALLY CLOSED at v44 regime (Decision 117). |
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — not picked by user at end of S82/S83. |
| Headline-goal recalibration | Concede 95% match% as unreachable | DEFERRED — still available; S84 MIXED makes this slightly more attractive. |
| **Option D-revised (S83)** | Rule-chain extension on under-rule-covered weak-hand zones | **CELL #1 SHIPPED — Rule 20 + $16.81 prefix (S83 / Decision 118).** |
| **Option D-revised cell #2 (S84)** | LOW × PMID_DS_MAXTOP | **MIXED — prefix +$5.59 SHIP but full +$1.36 NULL; production stays at v57 (Decision 119).** |
| Option D-revised continuation (S85+) | Apply playbook to PMID_SS_MAXTOP, PMID_OTHER, MID pair, HIGH_ONLY | ACTIVE — default S85 target is LOW × PMID_SS_MAXTOP ($9.71 v44 STRUCTURE; expect smaller residual under v57). |

**Cascade verdict (updated post S84):** Two-track active.

* **ML cascade:** EXHAUSTED at v44 saturating regime (features S78 NULL + labels S82 NULL; both ends of capacity lever swept).
* **Rule-layer cascade (Option D-revised):** ALIVE with variable cell-level outcomes — S83 SHIP, S84 MIXED. ~50% ship rate is the working assumption on remaining cells. Continue cell-by-cell with refined methodology (re-measure under production first; multi-gate on both grids; pre-committed thresholds; require both grids to clear $5 for SHIP).

---

## Resume Prompt (Session 85 — extend Option D playbook to LOW × PMID_SS_MAXTOP, with refined methodology from S84)

```
Resume Session 85 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S84 — opens with S85 default target)
- DECISIONS_LOG.md (latest: Decision 119 — S84 v58 MIXED on LOW × PMID_DS_MAXTOP;
  production stays at v57; introduces the two-grid-confirmation standard for
  SHIP and the production-leak overlay for the under-covered map)
- SESSION_84_REPORT.md (S84 MIXED verdict, plain-language TL;DR, methodology
  lessons, the refined playbook to use in S85)

KEY DATA FILES (no new generation needed in S85):
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_pair_v44_per_hand_structural.parquet — S77 per-hand parquet
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 13 sessions)

STATE (end of S84):
- Production rule chain UNCHANGED at v57_lo_pair_defensive ($1,412.53 full /
  $776.88 prefix). Last strategy-of-record change was S83 (12 sessions ago
  including S84).
- ML champion v44_dt UNCHANGED.
- Two-track divergence: $332/1000h (unchanged).
- Rule count: 20 (unchanged — Rule 21 candidate MIXED, did not ship).
- S84 introduces the two-grid-confirmation standard: SHIP requires both
  full-grid lift ≥ $5 AND prefix-grid lift ≥ $5. Prefix-only SHIP is
  insufficient evidence given canonical-prefix-skew + label-noise
  sensitivity at small residuals.
- The under-covered map's true ordering is by PRODUCTION residual (not v44
  leak per S77). PMID_DS_NOMAXTOP had $59 production residual under v56;
  PMID_DS_MAXTOP had $7 under v57. Smaller-residual cells are label-noise-
  sensitive and may MIXED.

USER DIRECTIVE:
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; any strategic discussion / session report must lead
  with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 85 — extend the (now-refined) S83/S84 playbook to the
next under-rule-covered cell:

  DEFAULT TARGET: LOW × PMID_SS_MAXTOP (S77: $9.71/1000h STRUCTURE leak
                  across 85,536 hands under v44_dt; expected residual under
                  v57 may be significantly smaller).

  PHASE A (~5 min) — Verify cell choice. Sanity-check S77's cell_stats for
  LOW × PMID_SS_MAXTOP; confirm cell is still under-rule-covered after
  Rule 20 ship (Rule 20 won't fire by construction since PMID_SS_MAXTOP
  cell requires no PMID_DS achievable). The cell structure: bot is
  single-suited (2+1+1), max on top is the n_PMID_SS_w_maxtop config.

  PHASE B (~10 min, ~50s compute) — Drill the cell under PRODUCTION v57.
  Adapt drill_v57_low_pmid_ds_maxtop_S84.py → drill_v57_low_pmid_ss_maxtop_S85.py.
  Filter parquet to cell_idx == 4 (PMID_SS_MAXTOP) AND pair_rank ∈ {2-7}.
  Run v57 on each hand. Aggregate mismatches and total leak $.

  ** EARLY-OUT CHECK: If v57's residual leak on this cell is < $5/1000h
     whole-grid, no rule can ship by ceiling argument. Pivot to LOW ×
     PMID_OTHER or MID pair extension instead. Do not waste Phase B+/C
     compute on a ceiling-NULL cell. **

  PHASE B+ (~10 min, ~50s compute) — Discriminator drill (if Phase B
  passes the ceiling check). Identify the dominant mismatch class and
  candidate discriminator features for that cell's structural choice
  space (likely PMID_tmax_SS vs PBOT_tmax_SS_ms, or similar).

  PHASE C (~5 min, ~3 min compute) — Write strategy_v58_alt_* (or v59 if
  this lands a clean SHIP) with parametric gate. Run BOTH multi-gate
  full-grid grader AND multi-gate prefix grader. Pre-commit SHIP/NULL/
  MIXED thresholds in code BEFORE running. SHIP requires BOTH grids
  cleared $5; otherwise MIXED or NULL.

  PHASE D — Session-end commit + push + DECISIONS_LOG + CURRENT_PHASE
  rewrite. End with verbatim resume prompt.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged.
- v57_lo_pair_defensive is the production rule chain (unchanged in S84).
- The pre-committed-verdict pattern is project standard.
- SHIP now requires BOTH grids ≥ $5 (S84 refinement).
- Re-measure cell leak under v57 in Phase B BEFORE designing a rule —
  S77's v44-based headlines overstate ceiling on cells v52 already routes
  well.
- "Speed is not necessary — clarity and perfection is."
- The user is non-technical; session reports open with plain-language TL;DR
  before numbers.

ALTERNATIVE DIRECTIONS (if user redirects, or if PMID_SS_MAXTOP ceiling-
NULLs in Phase B):
- LOW × PMID_OTHER (S77: $11.81 STRUCTURE / 138k hands) — catchall.
- MID pair (8-T) × PMID_DS_NOMAXTOP — extend Rule 20 to higher pair tier.
- HIGH_ONLY × J-high (S71: $14.47 STRUCTURE / 14k hands) — different category.
- Resolve S84 divergence with N=1000 full-cell labels (~3-5h compute).
- Headline-goal recalibration (still available from S82 fork).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
