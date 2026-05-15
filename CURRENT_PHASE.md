# Current: Sprint 8 — Session 85 NULL verdict on v59 (LOW × PMID_SS_MAXTOP); both grids agree, production stays at v57; Option D-revised ship rate now 1/3 across three tested cells; S86 default target is MID pair × PMID_DS_NOMAXTOP (Rule 20 extension)

S85 extended S83/S84's Option D-revised playbook to the third under-rule-covered LOW pair cell, **PMID_SS_MAXTOP**. The candidate Rule 21 ("when LOW pair × PMID_SS_MAXTOP × max_sing ≤ gate × v57-picks-PMID_tmax_SS, force PMID_tnomax_best") auto-fired NULL on the full grid (best gate=9: −$0.09/1000h) AND NULL on the prefix grid (best gate=9-11: $0.00/1000h with zero fires; gates 12-14 progressively negative to −$131.27/1000h). **No two-grid disagreement; verdict is decisively NULL.**

The cell residual is real ($15.33/1000h whole-grid under v57, the largest of the three cells tested), but it is *distributed across three direction-conflicting populations*: PBOT-route ($6.98/1000h, 17.5% of cell), within-PMID tnomax variant ($4.36/1000h, 13.1% of cell), and OTHER ($3.99/1000h, 15.2% of cell). No single-direction rule clears SHIP by ceiling argument — even an idealized rule with perfect accuracy on SWAP_TO_PMID_TNOMAX would yield $4.36/1000h, below the $5 SHIP threshold.

The v59 candidate iterated v1 → v2 within Phase C: v1 fired on all cell hands at max_sing ≤ gate (overriding v57's correct picks); v2 restricted firing to hands where v57 picked PMID_tmax_SS (the swap-from class). v2 is architecturally correct; both versions NULLed but v2's numbers are cleaner.

**Production state: UNCHANGED.** v57_lo_pair_defensive remains the rule chain. v44_dt remains the ML champion. Rule count stays at 20. Two-track divergence stays at $332/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 86): try MID pair (rank 8-T) × PMID_DS_NOMAXTOP — the most likely-to-ship next cell because it inherits Rule 20's known-working structural premise**
>
> Rule 20 (S83) shipped on **LOW** pair (rank 2-7) × PMID_DS_NOMAXTOP at +$16.81/1000h prefix lift. The natural extension is the same cell shape at the next pair-rank tier: MID pair (8-T) × PMID_DS_NOMAXTOP. The structural premise is identical (PMID with DS bot achievable but max-on-top not achievable; swap direction is PMID_tmax_SS → PMID_tnomax_DS). The discriminator (max_sing) likely shifts — when pair is higher rank (e.g., 9-9), the relative value of max-on-top changes, so the max_sing gate may shift from Q to K or similar.
>
> ### What S86 should run (default — established playbook, refined methodology)
>
> 1. **Phase A** — Verify cell choice. Inspect S77 cell_stats for MID|PMID_DS_NOMAXTOP. Confirm Rule 20 currently fires 0 times on MID pair (its pair_rank gate is 2-7).
> 2. **Phase B** — Drill v57 on cell. Adapt `drill_v57_low_pmid_ss_maxtop_S85.py` → `drill_v57_mid_pmid_ds_nomaxtop_S86.py`. Filter parquet to cell_idx == 3 (PMID_DS_NOMAXTOP) AND pair_rank ∈ {8, 9, T}. Run v57. Aggregate (v57_class, oracle_class) mismatches and total leak. **Phase B ceiling check: if v57 residual < $5/1000h whole-grid, pivot.**
> 3. **Phase B+** — Discriminator drill. Adapt S83's discriminator script (it's the cleanest template since this cell shape matches). Verify whether `max_sing` retains discriminative power at MID pair tier, and whether the gate shifts.
> 4. **Phase C** — Write `strategy_v60_mid_pair_ds_nomaxtop.py` extending Rule 20's logic to pair_rank ∈ {8,9,T}; multi-gate full + multi-gate prefix; pre-commit thresholds. **SHIP requires both grids ≥ $5.**
> 5. **Phase D** — Session-end commit + push + decision + CURRENT_PHASE rewrite.
>
> ### Alternative S86 directions (lower priority)
>
> * **LOW × PMID_OTHER** (S77: $11.81 STRUCTURE / 137,808 hands) — largest remaining LOW cell by hand count. Structural premise is "no PBOT_DS, no PMID_DS, no PMID_SS_w_maxtop" — these are weak hands with no bot upgrade available. Rule would likely be about pair placement at the macro level (PMID vs PBOT vs SPLIT), not within-PMID variant. Different rule shape; uncharacterized discriminator surface.
> * **HIGH_ONLY × J-high and below** (S71: $14.47 + $4.31 STRUCTURE / 14k hands) — different category but similar defensive-routing archetype. v52's existing rules for max ≤ T may already capture much of it.
> * **Headline-goal recalibration** — increasingly attractive. With S83 SHIP + S84 MIXED + S85 NULL across three tested cells (ship rate 1/3), the cumulative under-covered-cell potential is bounded. If MID pair × PMID_DS_NOMAXTOP also ships, we'd be at 2/4 ship rate with one more LOW catchall + one HIGH_ONLY cell remaining; the ~$30-60/1000h cumulative reachable lift is below the ~$300+ gap to a 95% match% goal. Worth a strategic discussion at end of S86 regardless of outcome.
> * **Resolve S84 divergence** by running N=1000 labels on full PMID_DS_MAXTOP cell (~3-5h compute). Lower information yield than testing a new cell; deprioritized further given S85's clean NULL doesn't depend on resolving S84.

> **📓 METHODOLOGY (Session 86+ — refined through S83/S84/S85):**
>
> 1. **Re-measure cell leak under PRODUCTION before designing a rule** (S84/S85 lesson, project standard). S77's leak is under v44_dt; v52 routing closes a differential fraction per cell.
>
> 2. **Pre-committed grader thresholds in code remain the standard.** S85 demonstrated value on a CLEAN NULL: pre-committed thresholds removed all interpretive ambiguity.
>
> 3. **Multi-gate grading on BOTH grids is the standard for any candidate that survives Phase B** (S84 standard, S85 confirmed). For SHIP, both grids must clear $5.
>
> 4. **NEW S85 lesson — Phase B+ "within-population swap-rate" is an UPPER BOUND on rule swap-rate.** The discriminator measures direction-relevant power, but rule fires on broader population including direction-conflicting populations. Don't extrapolate Phase B+ peak swap-rates to expected rule swap-rates — Phase C grader is the ground truth.
>
> 5. **NEW S85 lesson — Phase B+ should compute "addressable-direction-residual" as a SHIP-ceiling check.** If the residual within the rule's swap direction (NOT the total cell residual) is below $5/1000h, the rule cannot SHIP regardless of discriminator quality. Make this an explicit Phase B+ gate alongside the Phase B cell-residual check.
>
> 6. **NEW S85 lesson — Use v57-pick restriction by default for under-covered-cell rules.** Only fire the rule when v57's pick is in the swap-from class; never override v57 when v57 already picks something different. S85's v1 → v2 iteration documented the architecturally clean pattern.
>
> 7. **Cell-level outcomes vary; ship rate is converging to ~1/3.** S83 SHIP, S84 MIXED, S85 NULL. The methodology is the constant; cell properties determine outcome. Recipe: **sharp discriminator (≥85% swap-right) × large residual (≥$30/1000h whole-grid) × single dominant swap direction.** Cells missing any of these tend to MIXED or NULL.
>
> 8. **"Speed is not necessary — clarity and perfection is" — S85 reaffirms.** The v1 → v2 iteration within Phase C was the right call (cleaner numbers, robust verdict, documented design pattern) over single-pass v1 NULL declaration.

> **✅ ARTIFACTS produced in S85:**
> 1. `analysis/scripts/drill_v57_low_pmid_ss_maxtop_S85.py` — Phase B drill (NEW)
> 2. `analysis/scripts/drill_v57_pmid_ss_swap_discriminator_S85.py` — Phase B+ discriminator (NEW)
> 3. `analysis/scripts/strategy_v59_lo_pair_ss_tnomax.py` — v59 candidate, v1 → v2 iteration (DID NOT SHIP)
> 4. `analysis/scripts/grade_v59_lo_pair_ss_tnomax_S85.py` — Phase C full-grid multi-gate grader (NEW)
> 5. `analysis/scripts/grade_v59_prefix_multigate_S85.py` — Phase C prefix multi-gate grader (NEW)
> 6. `data/session85/drill_v57_low_pmid_ss_maxtop_summary.json` (gitignored)
> 7. `data/session85/drill_v57_pmid_ss_swap_discriminator_summary.json` (gitignored)
> 8. `data/session85/grade_v59_summary.json` (gitignored)
> 9. `data/session85/grade_v59_prefix_multigate_summary.json` (gitignored)
> 10. `data/session85/*.log` for each phase
> 11. `SESSION_85_REPORT.md` — session report with plain-language TL;DR (NEW)
> 12. `DECISIONS_LOG.md` — Decision 120 (NULL verdict + methodology lessons) appended
> 13. `CURRENT_PHASE.md` — this file, rewritten for S86
> 14. `STRATEGY_GUIDE.md` — NOT updated (no production change)

> Updated: 2026-05-15 (Session 85 end — v59 candidate CLEAN NULL on both full and prefix grids across all six gates. The cell residual ($15.33/1000h whole-grid) is real but fragmented across PBOT-route ($6.98), within-PMID tnomax ($4.36), and OTHER ($3.99). No single-direction rule can clear the $5 SHIP threshold by ceiling argument. The v59 iterated v1 → v2 within Phase C as a documented design refinement (v57-pick restriction). Three cells tested across S83/S84/S85: ship rate 1/3 (S83 SHIP / S84 MIXED / S85 NULL). The recipe for SHIP is now characterised: sharp discriminator (≥85% swap-right) × large residual (≥$30/1000h whole-grid) × single dominant swap direction. S86 default: MID pair × PMID_DS_NOMAXTOP — inherits Rule 20's known-working structural premise; most likely-to-ship next cell. Expect ~half of remaining cells to MIXED/NULL given the soft-discriminator + multi-direction pattern S85 demonstrated.)

---

## Headline state at end of Session 85 (UNCHANGED — no production change)

**Strategies of record (UNCHANGED — v59 candidate did not ship):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v57_lo_pair_defensive** | PRODUCTION rule chain. $1,412.53/1000h full / **$776.88/1000h prefix**. (UNCHANGED since S83 ship) | `analysis/scripts/strategy_v57_lo_pair_defensive.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 14 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$332/1000h (unchanged from S83).** Cumulative since pre-S68: $1,077 = 76% of original $1,409.

**Total project rule count: 20** (unchanged — Rule 21 candidate v59 did not ship).

**S85 candidate result (NULL — did not ship, both grids agree):**

| Candidate | Hyperparams | Full grid (best) | Prefix grid (best) | Verdict |
|---|---|---:|---:|---|
| v59_lo_pair_ss_tnomax (v2) | max_sing_gate = 9 | −$0.09/1000h NULL | $0.00/1000h NULL | **NULL** — both grids agree |

---

## Hypothesis cascade status (updated after S85)

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
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — not picked by user at end of S82/S83/S84/S85. |
| Headline-goal recalibration | Concede 95% match% as unreachable | INCREASINGLY ATTRACTIVE — S83/S84/S85 results imply bounded cumulative under-covered-cell potential. Worth strategic discussion at end of S86. |
| **Option D-revised cell #1 (S83)** | LOW × PMID_DS_NOMAXTOP | **SHIPPED — Rule 20 + $16.81 prefix (Decision 118).** |
| **Option D-revised cell #2 (S84)** | LOW × PMID_DS_MAXTOP | **MIXED — prefix +$5.59 vs full +$1.36; production stays at v57 (Decision 119).** |
| **Option D-revised cell #3 (S85)** | LOW × PMID_SS_MAXTOP | **CLEAN NULL — full -$0.09, prefix $0.00; both grids agree; production stays at v57 (Decision 120).** |
| Option D-revised continuation (S86+) | MID pair × PMID_DS_NOMAXTOP (Rule 20 extension), LOW × PMID_OTHER, HIGH_ONLY × J-low | ACTIVE — S86 default target is MID pair × PMID_DS_NOMAXTOP. Expected ship rate ~1/3 based on S83/S84/S85 trend. |

**Cascade verdict (updated post S85):** Two-track active but converging.

* **ML cascade:** EXHAUSTED at v44 saturating regime (features S78 NULL + labels S82 NULL; both ends of capacity lever swept).
* **Rule-layer cascade (Option D-revised):** ALIVE but ship rate converging to ~1/3 across tested cells. The SHIP recipe is now characterized: **sharp discriminator (≥85% swap-right) × large residual (≥$30/1000h whole-grid) × single dominant swap direction.** Cells missing any of these tend to MIXED/NULL.

---

## Resume Prompt (Session 86 — extend Option D playbook to MID pair × PMID_DS_NOMAXTOP, with established methodology)

```
Resume Session 86 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S85 — opens with S86 default target)
- DECISIONS_LOG.md (latest: Decision 120 — S85 v59 CLEAN NULL on LOW ×
  PMID_SS_MAXTOP; both grids agree; introduces "addressable-direction-
  residual" SHIP-ceiling check and v57-pick-restriction pattern)
- SESSION_85_REPORT.md (S85 NULL verdict, plain-language TL;DR, methodology
  lessons, the further-refined playbook to use in S86)

KEY DATA FILES (no new generation needed in S86):
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_pair_v44_per_hand_structural.parquet — S77 per-hand parquet
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 14 sessions)

STATE (end of S85):
- Production rule chain UNCHANGED at v57_lo_pair_defensive ($1,412.53 full /
  $776.88 prefix). Last strategy-of-record change was S83 (13 sessions ago
  including S84 + S85).
- ML champion v44_dt UNCHANGED.
- Two-track divergence: $332/1000h (unchanged).
- Rule count: 20 (unchanged — Rule 21 candidate v59 NULL, did not ship).
- Three Option D-revised cells tested: SHIP / MIXED / NULL (ship rate 1/3).
- The SHIP recipe is now characterized: sharp discriminator (≥85% swap-right) ×
  large residual (≥$30/1000h whole-grid) × single dominant swap direction.
- S85 introduces two methodology refinements:
  (a) addressable-direction-residual SHIP-ceiling check in Phase B+
  (b) v57-pick-restriction as default for under-covered-cell rules

USER DIRECTIVE:
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; any strategic discussion / session report must lead
  with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 86 — extend Rule 20's known-working pattern to the
next pair-rank tier:

  DEFAULT TARGET: MID pair (rank 8-T) × PMID_DS_NOMAXTOP. Inherits S83's
                  Rule 20 structural premise (PMID with DS bot achievable
                  but max-on-top not achievable; swap direction is
                  PMID_tmax_SS → PMID_tnomax_DS). The max_sing gate likely
                  shifts (from Q to K or similar) because pair-rank tier
                  changes the relative value of max-on-top.

  PHASE A (~5 min) — Verify cell choice. Inspect S77 cell_stats for
  MID|PMID_DS_NOMAXTOP (cell_idx=3, pair_rank∈{8,9,T}). Confirm Rule 20
  currently fires 0 times on this cell (its pair_rank gate is 2-7).

  PHASE B (~10 min, ~50s compute) — Drill the cell under PRODUCTION v57.
  Adapt drill_v57_low_pmid_ss_maxtop_S85.py → drill_v57_mid_pmid_ds_nomaxtop_S86.py.
  Filter parquet to cell_idx == 3 (PMID_DS_NOMAXTOP) AND pair_rank ∈ {8,9,10}.

  ** EARLY-OUT CHECK: If v57's residual leak on this cell is < $5/1000h
     whole-grid, no rule can ship by ceiling argument. Pivot to LOW ×
     PMID_OTHER or HIGH_ONLY × J-low. Do not waste Phase B+/C compute on a
     ceiling-NULL cell. **

  PHASE B+ (~10 min, ~50s compute) — Discriminator drill. Adapt
  drill_v56_pmid_swap_discriminator_S83.py (S83's template for the same
  cell shape). Check whether max_sing retains discriminative power at MID
  pair tier; if so, identify the gate (likely K based on pair-rank shift).

  ** NEW S85 CEILING CHECK: compute addressable-direction-residual (the
  subset of cell residual within the rule's swap direction). If this is
  < $5/1000h whole-grid, even perfect rule accuracy cannot SHIP. Pivot. **

  PHASE C (~5 min, ~3 min compute) — Write strategy_v60_mid_pair_ds_nomaxtop
  with parametric gate. Apply v57-pick-restriction (only fire when v57 picked
  PMID_tmax_SS). Run BOTH multi-gate full-grid grader AND multi-gate prefix
  grader. Pre-commit SHIP/NULL/MIXED thresholds in code BEFORE running. SHIP
  requires BOTH grids cleared $5; otherwise MIXED or NULL.

  PHASE D — Session-end commit + push + DECISIONS_LOG + CURRENT_PHASE rewrite.
  End with verbatim resume prompt.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged.
- v57_lo_pair_defensive is the production rule chain (unchanged since S83).
- The pre-committed-verdict pattern is project standard.
- SHIP requires BOTH grids ≥ $5 (S84 refinement).
- Re-measure cell leak under v57 in Phase B BEFORE designing a rule
  (S84 + S85 lesson).
- Addressable-direction-residual ceiling check in Phase B+ (NEW S85 lesson).
- v57-pick-restriction as default for under-covered-cell rules
  (NEW S85 design pattern).
- "Speed is not necessary — clarity and perfection is."
- The user is non-technical; session reports open with plain-language TL;DR
  before numbers.

ALTERNATIVE DIRECTIONS (if user redirects, or if MID × PMID_DS_NOMAXTOP
ceiling-NULLs in Phase B):
- LOW × PMID_OTHER (S77: $11.81 STRUCTURE / 138k hands) — catchall, biggest
  remaining LOW cell.
- HIGH_ONLY × J-high and below (S71: $14.47 STRUCTURE / 14k hands) —
  different category.
- Headline-goal recalibration — increasingly attractive given ship rate trend.
- Resolve S84 divergence with N=1000 full-cell labels (~3-5h compute).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
