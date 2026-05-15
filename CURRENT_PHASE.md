# Current: Sprint 8 — Session 86 v60 candidate MIXED-by-methodology on MID × PMID_DS_NOMAXTOP (Rule 20 extension); full-grid SHIP at +$6.43/1000h but prefix grid is silent (zero applicable hands in canonical-id 0-499,999); two-grid SHIP standard cannot be applied; production stays at v57; S87 surfaces the prefix-coverage-gap policy question to user, default direction is LOW × PMID_OTHER if user defers

S86 extended S83/S84/S85's Option D-revised playbook to the fourth under-rule-
covered pair cell, **MID pair × PMID_DS_NOMAXTOP** — the natural extension of
S83's shipped Rule 20 pattern from LOW pair (rank 2-7) to MID pair (rank 8-T).
The candidate v60 ("when MID pair × PMID_DS_NOMAXTOP × max_sing ≤ Q × v57-
picks-PMID_tmax-style, force PMID_tnomax_DS") cleared full-grid SHIP at
**+$6.43/1000h whole-grid (62.0% swap-right, 32,304 fires)** at gate=Q.

But the prefix-grid grader fired **zero times across all five gates** because
canonical_id ordering places MID pair × PMID_DS_NOMAXTOP hands starting at
canonical_id 593,072 — entirely outside the prefix range (0-499,999). The
prefix grid is **structurally silent on this cell**, neither confirming nor
contradicting the full-grid signal.

By the S84 two-grid SHIP standard ("both grids ≥ $5"), full-grid SHIP alone
is not sufficient → **MIXED verdict**. Production stays at v57. S86's
session-meta discovery: the prefix-grid validation has a hand-rank coverage
limit affecting all MID+ pair cells and HIGH-pair cells.

The cell residual is large ($31.17/1000h under v57 vs S83's $59 under v56),
the direction-residual is dominant ($22.98 on PMID_tmax → PMID_tnomax_DS,
4.6× the SHIP ceiling), the discriminator (max_sing) is sharp (84% swap-
right at max=9, 75% at J, 65% at Q), and per-rank lift is positive on all
three pair_ranks (rank 8 +$4.14, rank 9 +$2.20, rank T +$0.09). The
full-grid signal is structurally robust — the verdict is methodology-bound,
not signal-bound.

**Production state: UNCHANGED.** v57_lo_pair_defensive remains the rule
chain. v44_dt remains the ML champion. Rule count stays at 20. Two-track
divergence stays at $332/1000h.

> **🎯 IMMEDIATE NEXT ACTION (Session 87): surface the prefix-coverage-gap question to user, then act on their decision**
>
> S86 surfaced a methodology question that warrants user input before further cell drilling:
>
> **The S84 two-grid SHIP standard cannot be applied to cells whose canonical_id
> range starts above 500K.** This includes MID-pair (rank 8-T) cells, HIGH-pair
> cells, and most HIGH_ONLY high-card cells. Future Option D-revised extensions
> beyond LOW pair will face the same coverage gap.
>
> S87 should EITHER:
>
> 1. **Surface the question to user up-front:** how to resolve. The three
>    policy options are:
>    (a) **Strict standard, accept coverage limit** — Option D-revised is
>        capped at LOW pair cells. Pivot to LOW × PMID_OTHER and any
>        remaining LOW cell. After LOW is exhausted, methodology track
>        ends.
>    (b) **Relax to "two-grid-when-applicable"** — full-grid SHIP suffices
>        when prefix is silent. Ship v60 retroactively as Rule 21. Apply
>        to any future MID+ pair extension that grades full-grid SHIP.
>    (c) **Generate per-cell N=1000 oracle subsets** to extend prefix
>        coverage as needed. ~few hours per cell. Most rigorous.
>
> 2. **If user defers / not available, default to pursuing Option A direction:**
>    Drill **LOW × PMID_OTHER** ($11.81 v44 STRUCTURE / 137,808 hands, prefix-
>    covered). Largest remaining LOW pair cell by hand count. Different rule
>    shape (no DS available — likely macro pair placement vs within-PMID variant).
>
> ### Plan A — if user picks "strict standard" (Option A) or defers
>
> 1. **Phase A** — Verify cell choice. Inspect S77 cell_stats for
>    LOW|PMID_OTHER (cell_idx=5, pair_rank∈{2-7}). Confirm canonical_id
>    coverage in prefix (per LOW pair pattern, should be ~17% prefix-covered).
> 2. **Phase B** — Drill v57 on cell. Adapt
>    `drill_v57_mid_pmid_ds_nomaxtop_S86.py` → `drill_v57_low_pmid_other_S87.py`.
>    Early-out: if v57 residual < $5/1000h whole-grid, pivot.
> 3. **Phase B+** — Discriminator drill. Note: the structural premise is
>    DIFFERENT from S83-S86 (no DS available; no SS_w_maxtop). Likely needs
>    a different discriminator surface; rule shape may be about pair placement
>    (PMID vs PBOT vs SPLIT) at macro level rather than within-PMID variant.
>    Apply addressable-direction-residual SHIP-ceiling check.
> 4. **Phase C** — Write strategy_v61 with parametric gate + v57-pick-restriction.
>    Multi-gate full + prefix; pre-commit thresholds. SHIP requires both grids ≥ $5.
> 5. **Phase D** — Session-end commit + push + DECISIONS_LOG + CURRENT_PHASE rewrite.
>
> ### Plan B — if user picks "relax standard" (Option B)
>
> 1. **Promote v60 to production.** Update strategy_v60 default gate to 12
>    (Q). Add Rule 21 to STRATEGY_GUIDE.md. Re-grade v57 → v60 transition
>    on full grid; expect new production v60 at ~$1,419/1000h full grid
>    (v57's $1,412.53 + $6.43 lift).
> 2. **Verify two-track divergence change.** Two-track widens by ~$6.43/1000h.
> 3. **Audit-trail update.** Document the policy clarification in DECISIONS_LOG.
> 4. **Move to next under-covered cell** — likely MID × PMID_DS_MAXTOP or
>    MID × PMID_SS_MAXTOP for full Rule 20-pattern coverage at MID tier.
>
> ### Plan C — if user picks "generate N=1000 oracle subset" (Option C)
>
> 1. **Design oracle batch job** for MID × PMID_DS_NOMAXTOP cell hands at
>    N=1000. ~few hours compute. Background.
> 2. **In parallel, drill an unrelated prefix-covered cell.**
> 3. **When oracle completes, re-grade v60 against N=1000 labels.** If lift
>    confirms ≥ $5, override the S86 MIXED verdict and ship v60. If lift
>    falls below $5, MIXED stands.
>
> **My recommendation if pressed:** Plan A (pivot to LOW × PMID_OTHER) is
> the safest. It maintains the strict two-grid standard and tests one more
> LOW pair cell. If LOW × PMID_OTHER also fails to ship (likely, given the
> structural premise is non-DS), the methodology question becomes more
> pressing organically.

> **📓 METHODOLOGY (Session 87+ — refined through S83/S84/S85/S86):**
>
> 1. **Re-measure cell leak under PRODUCTION before designing a rule** (S84/S85/S86 standard). v57 leak ≠ v44 leak.
>
> 2. **Pre-committed grader thresholds in code remain the standard.** Demonstrated again on S86's MIXED.
>
> 3. **Multi-gate grading on BOTH grids is the standard, with caveat:** if the cell has zero applicable hands in the prefix (canonical_id range starts above 500K), the prefix grade is *uninformative*, not NULL.
>
> 4. **S85 lesson — Phase B+ should compute "addressable-direction-residual" as a SHIP-ceiling check.** Already applied in S86, confirmed direction-residual $22.98 >> $5 ceiling.
>
> 5. **S85 lesson — Use v57-pick restriction by default for under-covered-cell rules.** Standardized in S86 v60; no v1→v2 iteration needed.
>
> 6. **NEW S86 lesson — Phase A should check canonical_id coverage of the cell against the prefix range (0-499,999).** If the cell's canonical_id range starts above 500K, surface the two-grid-standard limitation immediately. Add this to the Phase A checklist.
>
> 7. **NEW S86 lesson — Distinguish "prefix-NULL" from "prefix-silent" in grader output.** n_fired=0 across all gates indicates coverage gap, not NULL signal. Graders should emit canonical_id range metadata alongside lift values.
>
> 8. **NEW S86 lesson — the two-grid SHIP standard needs an explicit clause for prefix-silent cells.** Three options: strict (reject all MID+ pair extensions), relax (full-grid suffices for prefix-silent cells), or extend (N=1000 oracle subsets per-cell). User decision required.
>
> 9. **Ship-rate is now 1/4 across cells:** S83 SHIP, S84 MIXED (small), S85 NULL, S86 MIXED-by-methodology. The methodology is the constant; cell properties (and increasingly, methodology coverage) determine outcome.
>
> 10. **"Speed is not necessary — clarity and perfection is" — S86 reaffirms.** Running the prefix grader even when its coverage gap was predictable empirically confirmed the discovery and made the methodology lesson defensible.

> **✅ ARTIFACTS produced in S86:**
> 1. `analysis/scripts/drill_v57_mid_pmid_ds_nomaxtop_S86.py` — Phase B drill (NEW)
> 2. `analysis/scripts/drill_v57_mid_pmid_ds_swap_discriminator_S86.py` — Phase B+ discriminator (NEW)
> 3. `analysis/scripts/strategy_v60_mid_pair_ds_nomaxtop.py` — v60 candidate, MIXED-by-methodology (DID NOT SHIP)
> 4. `analysis/scripts/grade_v60_mid_pair_ds_nomaxtop_S86.py` — Phase C full-grid multi-gate grader (NEW)
> 5. `analysis/scripts/grade_v60_prefix_multigate_S86.py` — Phase C prefix multi-gate grader (NEW)
> 6. `data/session86/drill_v57_mid_pmid_ds_nomaxtop_summary.json` (gitignored)
> 7. `data/session86/drill_v57_mid_pmid_ds_swap_discriminator_summary.json` (gitignored)
> 8. `data/session86/grade_v60_summary.json` (gitignored)
> 9. `data/session86/grade_v60_prefix_multigate_summary.json` (gitignored)
> 10. `data/session86/*.log` for each phase
> 11. `SESSION_86_REPORT.md` — session report with plain-language TL;DR + methodology discovery (NEW)
> 12. `DECISIONS_LOG.md` — Decision 121 (MIXED + prefix-coverage methodology discovery) appended
> 13. `CURRENT_PHASE.md` — this file, rewritten for S87
> 14. `STRATEGY_GUIDE.md` — NOT updated (no production change)

> Updated: 2026-05-15 (Session 86 end — v60 candidate cleared full-grid SHIP at +$6.43/1000h on MID × PMID_DS_NOMAXTOP but prefix grid is structurally silent (zero applicable hands in canonical_id 0-499,999). Mechanical verdict: MIXED. Production stays at v57. S86 surfaces a methodology discovery: the S84 two-grid SHIP standard has a hand-rank coverage limit affecting MID+ pair cells and HIGH-pair cells. Decision required from user for S87: maintain strict standard (cap Option D-revised at LOW pair), relax to "two-grid-when-applicable" (ship v60 retroactively), or generate per-cell N=1000 oracle subsets (~hours per cell). Default direction if user defers: pivot to LOW × PMID_OTHER (prefix-covered) as S87 candidate. Ship rate now 1/4 across S83-S86; the recipe for STRICT SHIP is sharp discriminator × large residual × single direction × prefix coverage.)

---

## Headline state at end of Session 86 (UNCHANGED — no production change)

**Strategies of record (UNCHANGED — v60 candidate MIXED-by-methodology, did not ship):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v57_lo_pair_defensive** | PRODUCTION rule chain. $1,412.53/1000h full / **$776.88/1000h prefix**. (UNCHANGED since S83 ship) | `analysis/scripts/strategy_v57_lo_pair_defensive.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 15 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$332/1000h (unchanged from S83).** Cumulative since pre-S68: $1,077 = 76% of original $1,409.

**Total project rule count: 20** (unchanged — Rule 21 candidate v60 did not ship by strict two-grid standard).

**S86 candidate result (MIXED-by-methodology — did not ship, prefix coverage gap):**

| Candidate | Hyperparams | Full grid (best) | Prefix grid (best) | Verdict |
|---|---|---:|---:|---|
| v60_mid_pair_ds_nomaxtop | max_sing_gate = 12 (Q) | **+$6.43/1000h SHIP** | $0.00/1000h (0 fires — coverage gap) | **MIXED** by two-grid standard |

---

## Hypothesis cascade status (updated after S86)

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
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — not picked by user at end of S82/S83/S84/S85/S86. |
| Headline-goal recalibration | Concede 95% match% as unreachable | INCREASINGLY ATTRACTIVE — cumulative under-covered-cell potential is bounded. Worth strategic discussion in S87. |
| **Option D-revised cell #1 (S83)** | LOW × PMID_DS_NOMAXTOP | **SHIPPED — Rule 20 + $16.81 prefix (Decision 118).** |
| **Option D-revised cell #2 (S84)** | LOW × PMID_DS_MAXTOP | **MIXED — prefix +$5.59 vs full +$1.36 (Decision 119).** |
| **Option D-revised cell #3 (S85)** | LOW × PMID_SS_MAXTOP | **CLEAN NULL — full -$0.09, prefix $0.00; both grids agree (Decision 120).** |
| **Option D-revised cell #4 (S86)** | MID × PMID_DS_NOMAXTOP | **MIXED-BY-METHODOLOGY — full +$6.43 SHIP, prefix silent (coverage gap); two-grid standard inapplicable (Decision 121).** |
| Option D-revised continuation (S87+) | LOW × PMID_OTHER, OR resolve methodology question, OR generate N=1000 oracle subsets | ACTIVE — S87 default is LOW × PMID_OTHER if user defers; methodology question surfaced for decision. |
| **Prefix-coverage methodology question (S86)** | How to handle prefix-silent cells in two-grid SHIP standard | OPEN — user decision required. |

**Cascade verdict (updated post S86):** Two-track active but methodology-bound.

* **ML cascade:** EXHAUSTED at v44 saturating regime (features S78 NULL + labels S82 NULL; both ends of capacity lever swept).
* **Rule-layer cascade (Option D-revised):** ALIVE for LOW pair; methodology-bound for MID+ pair due to prefix-coverage gap. Ship rate 1/4 strict (S83 only); 1/4 + 1 MIXED-by-methodology if relaxation considered.

---

## Resume Prompt (Session 87 — surface prefix-coverage methodology question, then act)

```
Resume Session 87 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S86 — opens with the S87 prefix-coverage
  methodology question)
- DECISIONS_LOG.md (latest: Decision 121 — S86 v60 MIXED-BY-METHODOLOGY on
  MID × PMID_DS_NOMAXTOP; full-grid SHIP +$6.43 but prefix grid silent due
  to canonical-id coverage gap; introduces "prefix-coverage-gap" concept
  and surfaces methodology policy question for user)
- SESSION_86_REPORT.md (S86 MIXED-by-methodology verdict, plain-language
  TL;DR, methodology discovery, refined playbook for S87)

KEY DATA FILES (no new generation needed in S87 unless Option C chosen):
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_pair_v44_per_hand_structural.parquet — S77 per-hand parquet
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 15 sessions)

STATE (end of S86):
- Production rule chain UNCHANGED at v57_lo_pair_defensive ($1,412.53 full /
  $776.88 prefix). Last strategy-of-record change was S83 (14 sessions ago).
- ML champion v44_dt UNCHANGED.
- Two-track divergence: $332/1000h (unchanged).
- Rule count: 20 (unchanged — v60 MIXED-BY-METHODOLOGY, did not ship).
- Four Option D-revised cells tested:
    S83 LOW × PMID_DS_NOMAXTOP: SHIPPED Rule 20
    S84 LOW × PMID_DS_MAXTOP: MIXED (small lift)
    S85 LOW × PMID_SS_MAXTOP: NULL (fragmented residual)
    S86 MID × PMID_DS_NOMAXTOP: MIXED-BY-METHODOLOGY (full SHIP, prefix silent)
- S86 introduces a methodology question: the S84 two-grid SHIP standard has a
  prefix coverage gap (cells with canonical_id range starting above 500K are
  silent in prefix grader). Affects all MID+ pair cells, HIGH pair cells,
  most HIGH_ONLY cells.

USER DIRECTIVE:
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; any strategic discussion / session report must lead
  with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 87 — surface prefix-coverage question, then act:

  PRIMARY: Ask the user how to handle the prefix-coverage-gap discovery
  from S86. Three policy options:

    (a) STRICT — maintain two-grid SHIP standard as-is. Cap Option D-revised
        at LOW pair cells. Try LOW × PMID_OTHER next; after LOW is exhausted,
        end methodology track and discuss headline-goal recalibration.

    (b) RELAX — adopt "two-grid-when-applicable" standard. Full-grid SHIP
        suffices when prefix is silent. Ship v60 retroactively as Rule 21.
        Resume Option D-revised continuation across all pair tiers.

    (c) EXTEND — generate per-cell N=1000 oracle subsets on-demand
        (~hours per cell). Validate v60 rigorously; if confirmed, ship.
        Apply same approach to future MID+ pair cells.

  DEFAULT IF USER DEFERS: pursue Option (a) direction — drill LOW ×
  PMID_OTHER (S77: $11.81 v44 STRUCTURE / 137,808 hands, prefix-covered).

  PHASE A (~5 min) — Decision in hand:
    - If (a): proceed to S87 plan for LOW × PMID_OTHER (different cell shape;
      structural premise is "no DS, no SS_w_maxtop" — rule likely about pair
      placement at macro level).
    - If (b): no compute; promote v60 to production (Rule 21 added);
      pivot to MID × PMID_DS_MAXTOP or MID × PMID_SS_MAXTOP as next cell.
    - If (c): design oracle batch job; ~hours background; drill prefix-
      covered cell in parallel.

  PHASE B/B+/C — same playbook as S83-S86 with one Phase A addition:
    - CHECK canonical_id range of target cell vs prefix range (0-499,999).
      If cell starts above 500K, surface coverage limitation up-front.
    - Apply addressable-direction-residual SHIP-ceiling check in Phase B+.
    - Apply v57-pick-restriction in v61 design by default.

  PHASE D — Session-end commit + push + DECISIONS_LOG + CURRENT_PHASE rewrite.
  End with verbatim resume prompt.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged.
- v57_lo_pair_defensive is the production rule chain (unchanged since S83).
- The pre-committed-verdict pattern is project standard.
- SHIP requires BOTH grids ≥ $5 (S84 refinement).
- Re-measure cell leak under v57 in Phase B BEFORE designing a rule (S84/S85/S86 lesson).
- Addressable-direction-residual ceiling check in Phase B+ (S85 lesson).
- v57-pick-restriction as default for under-covered-cell rules (S85 lesson).
- NEW S86 — Phase A canonical-id coverage check + distinguish prefix-NULL from prefix-silent.
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR before numbers.

ALTERNATIVE DIRECTIONS (if user picks a non-default plan):
- Ship v60 retroactively (Option B): apply +$6.43 to production, document policy clarification.
- Generate N=1000 oracle subset (Option C): ~hours compute; rigorous validation.
- Headline-goal recalibration discussion: cumulative bounded reachable lift.
- Resolve S84 divergence with N=1000 labels on full PMID_DS_MAXTOP cell (~3-5h).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
