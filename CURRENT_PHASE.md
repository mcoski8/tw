# Current: Sprint 8 — Session 83 SHIPS v57 (Rule 20: LOW pair defensive PMID-DS swap); first production change in 12 sessions; Option D-revised (user-redirected) playbook validated; S84 extends playbook to adjacent under-rule-covered cells

S83 executed the user-redirected Option D (under-rule-covered weak-hand zones, not just S77's specific LOW pair finding). Phase A synthesized coverage from existing S76/S77/S71 drills (no new compute). Phase B drilled the top under-covered cell — LOW pair × PMID_DS_NOMAXTOP — under PRODUCTION v56 (not v44_dt) and found that v56's leak structure differs from v44's: v56 doesn't SPLIT low pair at all (100% PMID), but it picks the wrong PMID variant (max-on-top + SS bot instead of drop-max + DS bot). Phase B+ identified `max_sing` (rank of largest non-pair card) as a razor-sharp discriminator: swap is right 89-93% at max_sing ≤ J, right 77% at Q, right 54% at K, and WRONG 86% at A. Phase C wrote v57 with a max_sing gate parameter and ran a multi-gate grader with **pre-committed SHIP/NULL/MIXED thresholds in code**: Q gate auto-fired SHIP on both full grid (+$16.47/1000h) and prefix (+$16.81/1000h, 84s wall, 6,048 picks changed of 12,096 fires).

**Production state CHANGED for the first time in 12 sessions.** Rule chain advances from v56 to v57_lo_pair_defensive. ML champion v44_dt UNCHANGED.

> **🎯 IMMEDIATE NEXT ACTION (Session 84): extend the S83 playbook to LOW pair × PMID_DS_MAXTOP**
>
> S83 demonstrated the playbook for Option D-revised on a single cell. The same playbook applies to adjacent under-rule-covered LOW pair cells. The next-highest under-covered cell is **LOW × PMID_DS_MAXTOP** (S77 measured $21.68/1000h STRUCTURE leak on 128,304 hands; structural sister of PMID_DS_NOMAXTOP where DS bot is achievable WITH max-on-top).
>
> ### What S84 should run (default — recipe established in S83)
>
> 1. **Phase B** — Adapt `drill_v56_low_pmid_ds_nomaxtop_S83.py` → `drill_v56_low_pmid_ds_maxtop_S84.py`. Filter parquet to `cell_idx == 2` (PMID_DS_MAXTOP) AND pair_rank ∈ {2-7}. Run v56 on the 128,304 cell hands. Aggregate (v56_class, oracle_class) mismatches.
> 2. **Phase B+** — Identify the discriminator. Hypothesis: `max_sing` is again the signal, but with a different sign/cutoff because the cell already has DS-with-max-on-top available — so v56's tmax_DS pick may be CORRECT more often than in PMID_DS_NOMAXTOP. The swap target might instead be PBOT or a different within-PMID variant. Run the same KEEP/SWAP/OTHER population analysis.
> 3. **Phase C** — Write `strategy_v58_*` with parametric gate; multi-gate grade with pre-committed SHIP/NULL/MIXED thresholds in code.
> 4. **Phase D** — Session-end commit + push + decision + CURRENT_PHASE rewrite.
>
> ### Alternative S84 directions (lower priority)
>
> * **LOW × PMID_SS_MAXTOP** (S77: $9.71 STRUCTURE / 85,536 hands) — third-largest under-covered LOW cell. Smaller, but may have cleaner pattern.
> * **LOW × PMID_OTHER** (S77: $11.81 STRUCTURE / 137,808 hands) — catchall cell; may need richer feature than `max_sing`.
> * **MID pair (8-T) × PMID_DS_NOMAXTOP** (S77: ~$8/1000h STRUCTURE) — same cell type as S83 but different pair_rank tier. Test whether the rule transfers with shifted gate.
> * **HIGH_ONLY × J-high and below** (S71: $14.47 STRUCTURE J-high + $4.31 T-high; v52 has defensive rules already for max ≤ T, J-high uses 2nd-high ≤ 8 gate). Investigate residual under-coverage if v52's gate misses cases.
>
> ### Why default to PMID_DS_MAXTOP rather than another option
>
> Of the 4 remaining LOW pair cells, PMID_DS_MAXTOP has:
> * The next-largest STRUCTURE leak ($21.68 — second only to PMID_DS_NOMAXTOP's $31.00)
> * The same fundamental structure (DS achievable, PMID dominant) so the playbook transfers cleanly
> * Existing per-hand classification in S77's parquet (no taxonomy rebuild needed)
>
> Once PMID_DS_MAXTOP ships (or NULLs), the same playbook extends to PMID_SS_MAXTOP and PMID_OTHER. After all four LOW pair cells are processed, the natural next step is MID pair × PMID_DS_NOMAXTOP (extending the rule family one tier up) or HIGH_ONLY LOW (different category, same defensive archetype).

> **📓 METHODOLOGY (Session 84+):**
>
> 1. **Always grade the PRODUCTION strategy on the candidate cell first.** S82 measured leak under v44_dt; v56 routes most of PAIR through v52 and has a different leak profile. Phase B's first job is to characterize v56's behavior on the cell, NOT to trust prior v44-based drills.
>
> 2. **Pre-committed grader thresholds in code are project-standard.** Both `grade_v57_lo_pair_defensive_S83.py` (full) and `grade_v57_prefix_S83.py` (prefix) auto-fire SHIP/NULL/MIXED based on thresholds hardcoded BEFORE the data lands. This pattern transferred cleanly from S81/S82's NULL pattern.
>
> 3. **Multi-gate grading is the right resolution for parametric rules.** Phase C grades the rule at multiple gate values, not just one. The lift surface has structure (J: +$3.69, Q: +$16.47, K: +$12.94, A: −$88.95); single-gate would miss the structure.
>
> 4. **The S83 playbook compresses to ~3-4 hours per cell.** Reuse S77's parquet + S66's pair_structural + S66's pick classifier + S83's pre-committed grader templates. New code per cell: ~2 short Python files (drill + grader). Wall: ~2 min compute (Phase B 77s + Phase C 17s + Phase C-prefix 84s).
>
> 5. **Rule-layer track is alive while ML-cascade track is exhausted.** S78 features NULL + S82 labels NULL at v44 capacity established the bottleneck. S83's first rule extraction in the under-covered zone shipped on first attempt. Future Option D extractions are the priority path.
>
> 6. **"Speed is not necessary — clarity and perfection is."** Multi-gate grade with pre-committed verdicts; reuse-of-prior-drill data over rebuild; cell-level focus over whole-grid sweeps. Every speed-vs-clarity trade in S83 chose clarity.

> **✅ ARTIFACTS produced in S83:**
> 1. `analysis/scripts/strategy_v57_lo_pair_defensive.py` — Rule 20 + chain composition (NEW PRODUCTION).
> 2. `analysis/scripts/drill_v56_low_pmid_ds_nomaxtop_S83.py` — Phase B drill.
> 3. `analysis/scripts/drill_v56_pmid_swap_discriminator_S83.py` — Phase B+ discriminator drill.
> 4. `analysis/scripts/grade_v57_lo_pair_defensive_S83.py` — Phase C full-grid multi-gate grader with pre-committed verdicts.
> 5. `analysis/scripts/grade_v57_prefix_S83.py` — Phase C prefix-grid grader with pre-committed verdicts.
> 6. `data/session83/drill_v56_low_pmid_ds_nomaxtop_summary.json` (gitignored).
> 7. `data/session83/drill_v56_pmid_swap_discriminator_summary.json` (gitignored).
> 8. `data/session83/grade_v57_summary.json` (gitignored).
> 9. `data/session83/grade_v57_prefix_summary.json` (gitignored).
> 10. `SESSION_83_REPORT.md` — session report with plain-language TL;DR.
> 11. `DECISIONS_LOG.md` — Decision 118 (SHIP verdict + methodology).
> 12. `CURRENT_PHASE.md` — this file, rewritten for S84.
> 13. `STRATEGY_GUIDE.md` — Part 1 S83 entry appended; Part 6 production-rule-chain block updated; front matter Last updated.

> Updated: 2026-05-15 (Session 83 end — v57_lo_pair_defensive SHIPS. Pre-committed grader auto-fired SHIP on both grids: +$16.47/1000h whole-grid (v56 $1,429 → v57 $1,412.53), +$16.81/1000h prefix (v56 $794 → v57 $776.88). Production strategy of record CHANGES for the first time in 12 sessions; previous change was v56 in S70. Rule 20 = "LOW pair (rank 2-7) + PMID_DS_NOMAXTOP cell + max_sing ≤ Q → force PMID with DS-bot (= max in bot) and non-max singleton on top." Mechanism: v56 (= v52 for this cell) over-routes to max-kicker-on-top + single-suited bot when oracle wants drop-max + double-suited bot; the LOW pair has no offensive top potential so the DS-bot trade is the real value. Discriminator `max_sing` is razor-sharp: ≤J swap-right 89-93%, =Q swap-right 77%, =K swap-right 54%, =A swap-WRONG 86%. Multi-gate grade showed Q is the lift maximum ($16.47 full); K still ships at $12.94 but smaller; A is catastrophic NULL (−$89). User's strategic redirect at end of S82 — "stop min-maxing well-covered areas, focus on under-rule-covered weak-hand zones" — was the load-bearing decision that made the ship possible. Rule count: 19 → 20. Two-track divergence: $348 → $332 (cumulative closure since pre-S68: 76% of original $1,409). The Option D rule-layer track is formally validated as alive while the ML-cascade track remains exhausted at v44 saturating regime per Decisions 113 + 117. S84 default plan: apply the S83 playbook to LOW pair × PMID_DS_MAXTOP (next-largest under-covered cell at $21.68/1000h STRUCTURE leak).)

---

## Headline state at end of Session 83

**Strategies of record (CHANGED — rule chain advances, ML champion unchanged):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v57_lo_pair_defensive** | **PRODUCTION rule chain (NEW).** $1,412.53/1000h full / **$776.88/1000h prefix**. Adds Rule 20 over v56. | `analysis/scripts/strategy_v57_lo_pair_defensive.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 12 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$332/1000h** (closed −$16 in S83; cumulative since pre-S68: $1,077 = 76% of original $1,409 divergence closed).

**Total project rule count: 20** (Rule 20 = LOW pair defensive PMID-DS swap, S83).

**S83 candidate result (SHIPPED):**

| Candidate | Hyperparams | Verdict |
|---|---|---|
| v57_lo_pair_defensive | max_sing gate = Q (12); fires on 12,096 prefix hands (changes 6,048) | **SHIP** — full +$16.47, prefix +$16.81, both > $5 ship threshold |

---

## Hypothesis cascade status (updated after S83)

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
| A2 (S81/S82) | Targeted N=1000 expansion on two_pair + trips_pair + held-out validation | CLEAN NULL — Lens-3 held-out 63.74% < 72.0% floor; A1's S80 lift confirmed as memorization (Decision 117). |
| A-path (oracle-label-quality lever) | All variants tested at v44 capacity | FORMALLY CLOSED at v44 regime (Decision 117). |
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — surfaced in S83 fork; not picked by user. |
| Headline-goal recalibration | Concede 95% match% as unreachable; pick new metric | DEFERRED — surfaced in S83 fork; not picked by user; still available as future option. |
| **Option D-revised (S83)** | **Rule-chain extension on under-rule-covered weak-hand zones** | **SHIPPED — Rule 20 (LOW pair × PMID_DS_NOMAXTOP × max_sing ≤ Q) +$16.81 prefix (Decision 118).** |
| Option D-revised continuation (S84+) | Apply S83 playbook to adjacent under-covered cells | ACTIVE — default S84 target is LOW × PMID_DS_MAXTOP ($21.68 STRUCTURE leak). |

**Cascade verdict (updated post S83):** The cascade now has TWO active tracks. ML cascade is exhausted at v44 saturating regime per Decisions 113 + 117 (both ends — features S78 NULL, labels S82 NULL — produced zero signal). **Rule-layer cascade (Option D-revised) is alive** — first cell-level extraction in the under-covered zone shipped on first attempt at +$16.81 prefix. S84+ extends the playbook to adjacent cells.

---

## Resume Prompt (Session 84 — extend Option D playbook to LOW pair × PMID_DS_MAXTOP)

```
Resume Session 84 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S83 — opens with S84 default target)
- DECISIONS_LOG.md (latest: Decision 118 — S83 v57 SHIP +$16.81/1000h prefix
  on Rule 20 LOW pair defensive PMID-DS swap; first production change in
  12 sessions)
- SESSION_83_REPORT.md (S83 SHIP verdict, plain-language TL;DR, methodology,
  the playbook to replicate)

KEY DATA FILES (no new generation needed in S84):
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_pair_v44_per_hand_structural.parquet — S77 per-hand parquet
  (canonical_id, pair_rank, cell_idx, v44_idx, oracle_idx, regret, etc.)
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 12 sessions)

STATE (end of S83):
- Production rule chain ADVANCED to v57_lo_pair_defensive ($1,412.53 full /
  $776.88 prefix). First strategy-of-record change in 12 sessions (since v56
  in S70).
- ML champion v44_dt UNCHANGED ($1,081 full / $686 prefix).
- Two-track divergence: $332/1000h (cumulative 76% closure since pre-S68).
- Rule count: 20 (Rule 20 = LOW pair × PMID_DS_NOMAXTOP × max_sing ≤ Q → force
  PMID with DS-bot and non-max top).
- Option D-revised (user-redirected rule-layer track) FORMALLY VALIDATED as
  alive. ML-cascade track FORMALLY CLOSED at v44 capacity (Decisions 113 + 117).
- Pre-committed grader pattern (verdicts hardcoded in code BEFORE data lands)
  is now project standard for any ship-or-null experiment.

USER DIRECTIVE:
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; any strategic discussion / session report must lead
  with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 84 — extend the S83 playbook to the next under-rule-
covered cell:

  DEFAULT TARGET: LOW pair × PMID_DS_MAXTOP (S77: $21.68/1000h STRUCTURE
                  leak across 128,304 hands; structural sister cell where
                  DS bot is achievable WITH max-on-top — opposite of S83's
                  cell where DS requires max in bot).

  PHASE A (~5 min) — Verify cell choice is correct. Sanity-check S77's
  cell_stats for LOW × PMID_DS_MAXTOP; confirm cell is still under-rule-
  covered after Rule 20 ship (Rule 20 should NOT fire on this cell by
  construction — the cell has DS-with-maxtop available, so the
  PMID_DS_NOMAXTOP trigger condition n_PMID_DS_w_maxtop == 0 fails).

  PHASE B (~10 min, ~80s compute) — Drill the cell under PRODUCTION v57
  (not v56 — important since v57 is now production). Write
  `drill_v57_low_pmid_ds_maxtop_S84.py`. Filter parquet to cell_idx == 2
  AND pair_rank ∈ {2-7}. Run v57 on each hand. Aggregate (v57_class,
  oracle_class) mismatches and total leak $.

  PHASE B+ (~10 min, ~80s compute) — Discriminator drill. Hypothesis: the
  swap target is different from PMID_DS_NOMAXTOP because the cell already
  has DS-with-maxtop. May be PBOT-routing (oracle wants pair-to-bot) or a
  different within-PMID variant. Use the same KEEP/SWAP/OTHER population
  analysis from S83.

  PHASE C (~5 min, ~few seconds compute) — Write strategy_v58_* with
  parametric gate; multi-gate grade on full grid (cell hands only,
  fast) + prefix grid. Pre-commit SHIP/NULL/MIXED thresholds in code
  BEFORE running (SHIP ≥ $5 prefix, NULL < $2 prefix).

  PHASE D — Session-end commit + push + DECISIONS_LOG + CURRENT_PHASE
  rewrite. End with verbatim resume prompt.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged.
- v57_lo_pair_defensive is the new production rule chain (not v56).
- The pre-committed-verdict pattern is project standard.
- "Speed is not necessary — clarity and perfection is."
- The user is non-technical; session reports open with plain-language TL;DR
  before numbers.
- If S84's Phase B finds the leak structure is materially different from
  S83's, adapt the discriminator search. Don't force the S83 pattern onto
  a cell where it doesn't fit.

ALTERNATIVE DIRECTIONS (if user redirects):
- LOW × PMID_SS_MAXTOP (S77: $9.71 STRUCTURE / 85k hands) — smaller cell.
- LOW × PMID_OTHER (S77: $11.81 STRUCTURE / 138k hands) — catchall.
- MID pair (8-T) × PMID_DS_NOMAXTOP — extend Rule 20 to higher pair tier.
- HIGH_ONLY × J-high (S71: $14.47 STRUCTURE / 14k hands) — different category.
- Headline-goal recalibration (still available from S82 fork).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
