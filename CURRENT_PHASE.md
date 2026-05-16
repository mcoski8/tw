# Current: Sprint 8 — Session 87 v61 SHIPS Rule 21 (chain gate-out fix on HIGH_ONLY × DS_NO_JOINT × {J-A}) — biggest single-rule production ship since S70 (+$98.67/1000h full grid); production v57 → v61 ($1,412.53 → $1,511.20); S88 default = expand chain-audit pattern to next-largest prefix-silent HIGH_ONLY zones (DS_NO_MAXTOP, MS_ONLY)

S87 began with the user reframing strategic priority at session start:
"easy hands are easy to play — bleeding lives on weak hands where damage
control is hard." Two Gemini-2.5-pro Socratic debates (methodology
debate, then pivot+heuristics debate) produced a gated-pivot plan:
pre-drill addressability of the user-prioritized weak-hand zone before
committing to Option C N=1000 oracle infrastructure.

The pre-drill (64s compute on 756,000 HIGH_ONLY × DS_NO_JOINT × {J-A}
hands) uncovered a **bombshell: v57 leaks $98.67/1000h MORE than
v44_dt** on this cell sub-population. v52's HIGH_ONLY handler had been
actively bleeding EV vs the realistic-mixture opponent for 33+ sessions,
undetected because prefix grader is structurally silent on these cells.

A layer-by-layer chain audit pinpointed v47 (Rules 13-16, Q-high DS
chain) as the dominant source (+$82/1000h on the fallthrough subset);
v52-J-HIMID added +$12.76 and v52-defensive-gated added +$3.84.

The fix (v61): surgical 30-line gate-out. For HIGH_ONLY × DS_NO_JOINT ×
max ∈ {J,Q,K,A}, bypass the v47→v48→v52 chain and return
strategy_v44_dt directly. Pre-committed grader auto-fired **SHIP at
+$98.67/1000h whole-grid lift**. Per-rank breakdown matches audit
prediction exactly. Out-of-cell sanity: 0 v57≠v61 disagreements on 50K
random sample.

**Production state: ADVANCED.** v61_high_only_ds_no_joint_fix is the new
rule chain ($1,511.20/1000h full / $776.88 prefix unchanged). v44_dt
remains ML champion. Rule count: 20 → 21. Two-track divergence: $332 →
$234 (−$98). Cumulative closure since pre-S68: 76% → 83% of original
$1,409.

> **🎯 IMMEDIATE NEXT ACTION (Session 88): expand the chain-audit pattern to next-largest prefix-silent HIGH_ONLY zones**
>
> Three workstreams identified for S88. Default order:
>
> 1. **PRIMARY** — expand chain audit to DS_NO_MAXTOP × {K, A} cells
>    (~$15/1000h combined v44 STRUCTURE), MS_ONLY × {J-A} (~$13), and
>    JOINT_HIGH × {K, A} (~$5). If v47/v52 also bleeds on these, another
>    $20-40/1000h is recoverable via the same gate-out pattern. Compute:
>    ~5-10 min per cell using the S87 audit script.
>
> 2. **SECONDARY** — build Option C N=1000 oracle generator
>    infrastructure (Rust `--id-list-file` option). ~30-60 min Rust mod
>    + test + launch. Required to retroactively validate the S86 v60
>    candidate (still UNSHIPPED, MIXED-by-methodology) and for any
>    future smaller-effect rule on prefix-silent cells.
>
> 3. **TERTIARY** — audit prefix-COVERED cells with the same pattern. It
>    is possible v47/v52 layers are net-negative on cells we thought were
>    fine. Low compute cost (existing per-hand parquets), high
>    information value.
>
> 4. **OPTIONAL** — LOW × PMID_OTHER drill (deferred from S87). The last
>    LOW pair cell. May still be worth running once audit work concludes.

> **📓 METHODOLOGY (Session 88+ — refined through S87):**
>
> 1. **PIVOT GATE pattern (NEW S87)** — before committing expensive
>    infrastructure (e.g., Option C oracle gen), spend ≤5 min on a
>    focused diagnostic that could falsify the premise. S87's pre-drill
>    took 64s and rerouted the entire session.
>
> 2. **CHAIN AUDIT pattern (NEW S87)** — layer-by-layer attribution
>    against a baseline strategy (v44_dt). The transition that
>    introduces the regression is the bad rule layer. Took 2 min compute
>    and uncovered a 33-session-old regression. Apply to every
>    prefix-silent zone where the rule chain has overrides.
>
> 3. **EFFECT-SIZE-DOMINANCE rule (NEW S87)** — when effect ≫ noise
>    floor by 20×+ AND the rule is a gate-out (not an addition), bypass
>    the two-grid SHIP standard with explicit documentation. Below the
>    threshold the standard still rules. v61 ships under this exception.
>
> 4. **USER STRATEGIC REDIRECT as first-class input** — listen for
>    priority reframes from the user, not just methodology answers. The
>    S87 reframe was load-bearing; none of S86's three options would
>    have surfaced the v52 bleed.
>
> 5. **Pre-committed grader thresholds in code** — locked SHIP/NULL
>    thresholds before grader runs. Mechanical verdict, no narrative
>    arbitrage. Now standard.
>
> 6. **Re-measure cell leak under PRODUCTION before designing a rule**
>    (S84/S85/S86 standard, reconfirmed S87).
>
> 7. **Multi-gate grading on BOTH grids is the standard**, with caveat:
>    prefix-silent cells use the EFFECT-SIZE-DOMINANCE rule. v61 shipped
>    under this; v60 (smaller effect, MIXED) still needs N=1000.
>
> 8. **"Speed is not necessary — clarity and perfection is" — S87
>    reaffirms.** Running the chain-audit drill even when the headline
>    bleed result was clear from the pre-drill pinpointed v47 as the
>    actual source (not just blaming "the chain"). Made the fix
>    surgical.

> **✅ ARTIFACTS produced in S87:**
> 1. `analysis/scripts/drill_v57_high_only_addressability_S87.py` — pre-drill (NEW)
> 2. `analysis/scripts/audit_v52_chain_bleed_S87.py` — chain audit (NEW)
> 3. `analysis/scripts/strategy_v61_high_only_ds_no_joint_fix.py` — Rule 21 SHIPPED (NEW)
> 4. `analysis/scripts/grade_v61_full_grid_S87.py` — full-grid grader with pre-committed thresholds (NEW)
> 5. `data/session87/drill_v57_high_only_addressability.log`
> 6. `data/session87/audit_v52_chain_bleed.log`
> 7. `data/session87/grade_v61_full_grid.log`
> 8. `SESSION_87_REPORT.md` — session report with plain-language TL;DR (NEW)
> 9. `DECISIONS_LOG.md` — Decision 122 (ship + methodology) appended
> 10. `CURRENT_PHASE.md` — this file, rewritten for S88
> 11. `STRATEGY_GUIDE.md` — Part 1 Session 87 entry added; Part 6 current standard updated; front-matter rewritten
> 12. Memory file `project_taiwanese_damage_control_priority.md` — user's load-bearing strategic priority captured

> Updated: 2026-05-15 (Session 87 end — STRATEGY OF RECORD CHANGED: v57 → v61_high_only_ds_no_joint_fix. User-redirected strategic pivot to weak-hand damage-control work surfaced a 33-session-old $98/1000h v52-chain bleed on HIGH_ONLY × DS_NO_JOINT × {J-A} cells. Surgical gate-out (return v44_dt directly on those cells) shipped at +$98.67/1000h whole-grid via pre-committed SHIP threshold. v52's HIGH_ONLY handler shipped in S53 with full-grid evidence only; prefix grader is structurally silent for HIGH_ONLY cells (canonical_id ≥ 590,512; prefix ends at 499,999), so the regression went undetected for 33+ sessions. Rule count 20 → 21. Production $1,412.53 → $1,511.20/1000h. Two-track divergence v61-vs-v44: $234/1000h (was $332). Cumulative closure since pre-S68: 83% of original $1,409 (was 76%). Decision 122 records ship + methodology lessons (PIVOT GATE pattern, CHAIN AUDIT pattern, EFFECT-SIZE-DOMINANCE rule, USER STRATEGIC REDIRECT as first-class input). v60 from S86 remains UNSHIPPED, MIXED-by-methodology, pending Option C N=1000 oracle generator build (S88 secondary). S88 default plan: expand chain-audit pattern to DS_NO_MAXTOP × {K, A} cells using S87 audit script template.)

---

## Headline state at end of Session 87 (CHANGED — STRATEGY OF RECORD ADVANCED)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v61_high_only_ds_no_joint_fix** | PRODUCTION rule chain (NEW S87). $1,511.20/1000h full / $776.88/1000h prefix (unchanged). | `analysis/scripts/strategy_v61_high_only_ds_no_joint_fix.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 15 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

Two-track divergence: **$234/1000h (was $332; −$98 this session).** Cumulative closure since pre-S68: $1,175 = 83% of original $1,409 (was 76%).

**Total project rule count: 21** (Rule 21 added — v61 chain gate-out fix for the $98/1000h v52-chain bleed on HIGH_ONLY × DS_NO_JOINT × {J-A}).

**S87 candidate result (SHIP):**

| Candidate | Mechanism | Whole-grid lift | Verdict |
|---|---|---:|---|
| v61_high_only_ds_no_joint_fix | Gate-out v47→v48→v52 chain on HIGH_ONLY × DS_NO_JOINT × {J,Q,K,A}; return strategy_v44_dt | **+$98.67/1000h SHIP** | **SHIP** |

---

## Hypothesis cascade status (updated after S87)

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
| A3 | Full 6M-hand N=1000 grid | DEPRIORITIZED — not picked by user. |
| Headline-goal recalibration | Concede 95% match% as unreachable | OPEN but less urgent post-S87 (extraction track suddenly more productive). |
| Option D-revised cell #1 (S83) | LOW × PMID_DS_NOMAXTOP | SHIPPED — Rule 20 + $16.81 prefix (Decision 118). |
| Option D-revised cell #2 (S84) | LOW × PMID_DS_MAXTOP | MIXED — prefix +$5.59 vs full +$1.36 (Decision 119). |
| Option D-revised cell #3 (S85) | LOW × PMID_SS_MAXTOP | CLEAN NULL — full -$0.09, prefix $0.00 (Decision 120). |
| Option D-revised cell #4 (S86) | MID × PMID_DS_NOMAXTOP | MIXED-BY-METHODOLOGY — full +$6.43 SHIP, prefix silent; v60 still UNSHIPPED (Decision 121). |
| **DAMAGE-CONTROL chain audit (S87)** | HIGH_ONLY × DS_NO_JOINT × {J-A} v52-chain regression | **SHIPPED — Rule 21 + $98.67 full-grid (Decision 122).** |
| Prefix-coverage methodology question (S86) | How to handle prefix-silent cells in two-grid SHIP standard | PARTIALLY RESOLVED — EFFECT-SIZE-DOMINANCE rule defined; Option C infra still needed for smaller candidates |
| **Chain-audit expansion (S88+)** | DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH cells under v44/v47/v52 attribution | OPEN — primary S88 direction |

**Cascade verdict (post S87):** Two-track active and accelerating.

* **ML cascade:** EXHAUSTED at v44 saturating regime.
* **Rule-layer cascade:** Originally focused on under-rule-covered cells via Option D-revised playbook. S87 added a NEW PATTERN: chain-audit for buried regressions on prefix-silent cells. The chain-audit pattern is now the dominant lever — bigger expected lift per session than incremental value extraction.

---

## Resume Prompt (Session 88 — expand chain-audit pattern to next-largest prefix-silent HIGH_ONLY zones)

```
Resume Session 88 of the Taiwanese Poker Solver project at
/Users/michaelchang/CODE/taiwanese.

Read these files for context (in this order):
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of S87 — opens with the S88 chain-audit
  expansion plan)
- DECISIONS_LOG.md (latest: Decision 122 — S87 v61 SHIPS Rule 21 at
  +$98.67/1000h on HIGH_ONLY × DS_NO_JOINT × {J-A}; the chain-audit
  pattern uncovered a 33-session-old v52-chain regression; methodology
  introduced EFFECT-SIZE-DOMINANCE rule + PIVOT GATE pattern + CHAIN AUDIT
  pattern)
- SESSION_87_REPORT.md (S87 SHIP verdict, plain-language TL;DR, audit
  methodology, refined playbook for S88)

KEY DATA FILES:
- data/oracle_grid_full_realistic_n200.bin — 6M × 105 at N=200
- data/oracle_grid_prefix500k_n1000.bin — 500K × 105 at N=1000
- data/drill_v44_high_only_S71_per_hand.parquet — per-hand HIGH_ONLY drill
  data, includes canonical_id + max_rank + cell_idx + v44/oracle picks +
  gap metrics. THIS IS THE SUBSTRATE FOR FUTURE CHAIN-AUDIT EXPANSIONS.
- data/v44_dt_model.npz — production ML champion (UNCHANGED for 16 sessions)
- data/session87/*.log — S87 drill + audit + grader logs

STATE (end of S87):
- Production rule chain ADVANCED to v61_high_only_ds_no_joint_fix
  ($1,511.20 full / $776.88 prefix). Last strategy-of-record change was
  THIS SESSION (was previously S83, 4 sessions ago).
- ML champion v44_dt UNCHANGED.
- Two-track divergence: $234/1000h (was $332; −$98).
- Rule count: 21 (Rule 21 added — v61 chain gate-out).
- Cumulative closure: 83% of original $1,409 (was 76%).
- v60 from S86 STILL UNSHIPPED, MIXED-by-methodology; waits on Option C
  N=1000 oracle generator (S88 secondary build).
- v52 HIGH_ONLY handler regression DOCUMENTED but only PARTIALLY FIXED —
  Rule 21 covers DS_NO_JOINT × {J-A} only. DS_NO_MAXTOP, MS_ONLY,
  JOINT_HIGH cells may have similar regressions.

USER DIRECTIVES (persistent):
- "Speed is not necessary — clarity and perfection is."
- "Easy hands are easy to play — bleeding lives on weak hands where
  damage control is hard." (Strategic priority anchor — see memory
  project_taiwanese_damage_control_priority.md.)
- User is non-technical; any strategic discussion / session report must
  lead with plain-language framing of trade-offs.
- Session-end commit + push is pre-authorized for this project (see
  feedback_taiwanese_commits memory).

DIRECTION FOR SESSION 88 — expand chain-audit pattern to next-largest
prefix-silent HIGH_ONLY zones:

  PRIMARY (S88 default plan):
  Apply the S87 PIVOT GATE + CHAIN AUDIT pattern to the next-largest
  prefix-silent HIGH_ONLY zones. Use S87 scripts as templates:
    drill_v57_high_only_addressability_S87.py  (template for pre-drill)
    audit_v52_chain_bleed_S87.py               (template for chain audit)
    grade_v61_full_grid_S87.py                 (template for grader)

  Target cells (in descending leak order, all prefix-silent):
    - HIGH_ONLY × DS_NO_MAXTOP × {K, A}: ~$15.30 v44 STRUCTURE combined
    - HIGH_ONLY × MS_ONLY × {J-A}: ~$13.53 v44 STRUCTURE combined
    - HIGH_ONLY × JOINT_HIGH × {K, A}: ~$5/1000h smaller

  Combined potential: another $20-40/1000h if audit positive across all.

  PHASE A (~5 min): query S71 cell stats for target cells. Check that
    v44 STRUCTURE leak survives under v61 (production now). Verify
    cells are still prefix-silent.
  PHASE B (~3-5 min): pre-drill — re-evaluate v61 (production) on each
    target cell. Identify v61 vs v44 delta.
  PHASE B+ (~3 min): chain audit — layer-by-layer attribution. Identify
    which rule layer introduces any regression.
  PHASE C: design v62 = v61 + extended gate-out on confirmed
    regressions. Pre-committed thresholds (SHIP ≥ $15 whole-grid since
    these cells are smaller individually; aggregate could still be
    large).
  PHASE D: session-end commit + push + DECISIONS_LOG + CURRENT_PHASE
    rewrite. End with verbatim resume prompt.

  ALTERNATIVE DIRECTIONS:

  (a) Build Option C N=1000 oracle generator infrastructure.
      Engineering scope: modify engine/src/main.rs to add --id-list-file
      option (read canonical IDs from a file, only process those).
      ~30-60 min Rust mod + ~10 min test + launch background K-high
      run for v60 retroactive validation. Required for any future
      smaller-effect rule on prefix-silent cells.

  (b) Audit prefix-COVERED cells with the chain-audit pattern. LOW pair,
      two_pair, trips. Existing per-hand parquets cover most. Low compute,
      potentially high information value if buried regressions exist
      outside HIGH_ONLY too.

  (c) LOW × PMID_OTHER drill (deferred from S87). Last LOW pair cell,
      methodology question is the standard Option D-revised playbook.

REMINDERS:
- Use python3, not python.
- cargo at ~/.cargo/bin/cargo.
- v44_dt model + features remain unchanged.
- v61_high_only_ds_no_joint_fix is the production rule chain.
- The pre-committed-verdict pattern is project standard.
- The EFFECT-SIZE-DOMINANCE exception for prefix-silent cells:
  effect ≫ noise floor by 20×+ AND rule is a gate-out → bypass two-grid
  standard with documentation. Below threshold: two-grid standard rules.
- The CHAIN AUDIT pattern (NEW S87): layer-by-layer attribution against
  v44_dt baseline; identify the regression-introducing transition.
- The PIVOT GATE pattern (NEW S87): cheap pre-drill (≤5 min) BEFORE
  committing to expensive infrastructure or pivots.
- "Speed is not necessary — clarity and perfection is."
- User is non-technical; session reports open with plain-language TL;DR
  before numbers.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
