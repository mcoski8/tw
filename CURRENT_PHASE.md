# Current: Sprint 8 — Session 43 ships **Rule 10 (J-low single-pair defensive)** as v40. Single rule, single ship, **+$23/1000h whole-grid full lift + +$37/1000h prefix lift, both grader-confirmed** (drill predicted +$22.73 / +$36.70 — matches within sampling noise). The user's weak-hand defensive investigation (~14% of hands, max card ≤ J) yielded ONE clean structural rule: for pair hands with max ≤ J, set top=lowest-singleton, mid=pair, bot=4-highest-non-pair. Discovered in `drill_low_pair_J_high_defense.py`; aggregated +$22.73/1000h whole-grid (full N=200) + **+$36.70/1000h whole-grid (prefix N=1000)** across 342,720 J-low pair hands. Both grids strongly positive — passes the both-grid validation gate decisively (prefix lift > full lift, the OPPOSITE of the prefix-regression risk pattern). The other three weak-hand zones investigated: (Q1) A-high+weak — already optimized at 96% top=Ace; (Q4) J-low two_pair re-examined defensively — confirmed Session 42's "two_pair is ML territory" verdict (all 6 deterministic candidates regress, including v33's adaptive splitting which turned out to be genuine ML routing not a hidden defensive rule); (Q5) J-high or weaker no-pair — naive "top=lowest" works on T-low (~+$8/1000h full-only, no prefix coverage) but regresses on J-high. The high-card-to-bot-for-4-flush hypothesis (Q2 user instinct) FAILS empirically: every variant regressed by $10-$27/1000h. Methodology lesson NEW: high_only category has ZERO prefix coverage (all canonical IDs >500K); the both-grid gate is INAPPLICABLE for no-pair rules — they ship full-only or not at all. Methodology lesson NEW: the **weak-hand top inversion** is a unifying structural pattern — when the highest card cannot reliably win the top tier, the GTO play is to dump the LOWEST card on top and stack the strong cards into mid+bot. Oracle confirms this inverts at the K-high → T-high boundary (96% top=hi on A-high, 47% top=lo on 9-high).

> **🎯 IMMEDIATE NEXT ACTION (Session 44):**
>
>   (A) **v40 ML retrain** — feed v34_dt with v40 baseline. Rule 10 changes 5.7% of grid (J-low pair). Some marginal ML signal expected.
>
>   (B) **Q5 J-high no-pair deep-dive** — biggest unrealized oracle ceiling (+$54/1000h whole-grid on 60K hands) but requires multi-feature decomposition. Top-position split is non-binary (27% top=hi, 34% top=lo, 39% other). Likely ML territory but worth a focused drill.
>
>   (C) **T-low high_only naive top=lo rule** — ~+$8/1000h whole-grid full-only lift. Methodology question: should we ship rules that lack prefix coverage? The category is genuinely full-only by canonical-ID coincidence.
>
>   (D) **Round-3 within-trips features** (Session 42 carryover). Diagnose v34's $1,291/1000h within-trips residual.
>
>   (E) **Learned A-vs-C decision tree for Rule 6** (Sessions 38–40 carryover). $5–13/1000h whole-grid ML target.
>
>   (F) **Trips_pair G3 oracle exploration** (Session 42 finding, +$85/1000h ceiling). Multi-feature ML or drill.
>
>   (G) **KK/AA single-suited Rule-4-bot residual** ($37/1000h). Defer behind A-F.

> **✅ SHIPPED (Decision 076):** **v40_rule10** as the new production strategy of record. Replaces v39 in `STRATEGY_GUIDE.md` Part 5 + Part 6 + cheat sheet. Lives at `analysis/scripts/strategy_v40_rule10.py`. Production strategy chain is now 10 rules deep (Rules 1-9 unchanged + Rule 10 = J-low single-pair defensive). v40b_rule10_gated (the gated variant, "pair_rank ≤ 6 OR pair_rank == max_rank") graded as a sister candidate; the production runtime chooses simple v40 for human-memorability per Session 42 "diminishing returns at structural break" methodology rule.

> **🔬 ARTIFACTS (Session 43):**
> 1. **`analysis/scripts/drill_high_card_defense.py`** — Q1+Q2+Q5 high_only investigation; oracle distribution shows weak-hand top inversion (96% top=Ace on A-high → 47% top=lo on 9-high)
> 2. **`analysis/scripts/drill_low_pair_J_high_defense.py`** — Q3 J-low pair drill; produced the Rule 10 candidate (+$22.73 full / +$36.70 prefix)
> 3. **`analysis/scripts/drill_two_pair_J_high_revisit.py`** — Q4 J-low two_pair re-examination; confirmed all deterministic candidates regress (ML territory)
> 4. **`analysis/scripts/strategy_v40_rule10.py`** — NEW PRODUCTION STRATEGY (v40)
> 5. **`analysis/scripts/strategy_v40b_rule10_gated.py`** — gated variant (sister candidate)
> 6. **`analysis/scripts/grade_v40_rule10.py`** + **`grade_v40b_rule10_gated.py`** — graders for both variants
> 7. **`SESSION_43_DEFENSIVE_REPORT.md`** — repo-root standalone report

> **📓 METHODOLOGY LESSONS (Session 43):**
> - **NEW: Weak-hand top inversion is a unifying structural pattern.** Top tier wins 1 point/board (max 2 across two boards), mid 2/board, bot 3/board. When TOP equity is already <50% (any J-low hand vs a random opponent), the opportunity cost of dumping the highest card to top is <1 point, while the gain in bot+mid equity from upgrading kicker strength is >1 point. The math inverts the conventional "highest card to top" reflex.
> - **NEW: high_only category has zero prefix coverage** (all 7-distinct-rank canonical IDs are >500K). The both-grid validation gate is INAPPLICABLE for no-pair rules. Defensive rules for the no-pair zone can only ship on full-grid validation alone, OR not ship.
> - **REINFORCED: Two_pair is genuinely ML territory.** Q4's defensive re-examination confirmed Session 42's verdict — all six deterministic candidates (RA, RB, RC, RA_TOP_LO, RC_TOP_LO, F_SPLIT) regressed materially on both grids. v33's adaptive splitting on prefix is genuine multi-feature ML routing, not a hidden defensive rule.
> - **NEW: High-card-to-bot-for-4-flush is a LOSING trade.** Counterintuitive conventional wisdom — building a 4-flush bot at the cost of breaking the high card regressed by $10-$27/1000h on every weak-hand stratum tested. The bot's flush draw doesn't compensate for the lost top-tier equity.
> - **NEW: Worst-case regret is a useful sanity check** for defensive rules. A rule with positive mean lift but BIGGER worst-case regret would induce more 20-point scoops. v40's per-cell worst-case regret stays in the +$10-$22 range (compared to v39's +$15-$25), confirming no scoop-induction risk.

> Updated: 2026-05-09 (Session 43)

---

## Headline state at end of Session 43

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v40_rule10** | NEW PRODUCTION strategy of record (10 rules: v39 + Rule 10) | `analysis/scripts/strategy_v40_rule10.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v40b_rule10_gated | Gated variant of Rule 10 (pair_rank ≤ 6 OR pair_rank == max); same prefix lift, full lift TBD | `analysis/scripts/strategy_v40b_rule10_gated.py` |
| v39_rule9 | Predecessor production (Session 42 overnight ship) | `analysis/scripts/strategy_v39_rule9.py` |
| v38_rule8_qp | Predecessor production | `analysis/scripts/strategy_v38_rule8_qp.py` |
| v37_rule7_three_pair | Earlier production runtime | `analysis/scripts/strategy_v37_rule7_three_pair.py` |
| v35_rule6_v3 | Human strategy of record for trips (sharper Rule 6 boundary). NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` |
| v33_rule6_trips | Earlier production runtime | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v38_rule8_two_pair_DEFERRED | DEFERRED — Session 42 two_pair Rule 8 candidate. Confirmed ML-only twice (S42 overnight + S43 Q4). | `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` |
| v36_rule7_high_only | ARCHIVED — Session 41 failed Rule 7 attempt for high_only | `analysis/scripts/strategy_v36_rule7_high_only.py` |

**Capacity + feature progression (full 6M grid, N=200) — UNCHANGED from Session 41:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| **v34** | **34 (33 actual)** | **2** | **83** | **874,548** | **$1,681** | **52.02%** | (latest) |

**Same sweep on N=1000 prefix:** unchanged from Session 38 — v34 at $889/1000h / 62.74%.

**Human-strategy progression (full grid, N=200) — production runtime:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v28_rule5_rainbow (+ Rules 4 + 5) | $3,032 | 39.64% | −$1 |
| v33_rule6_trips (+ Rule 6 v1) | $2,920 | 40.68% | −$113 |
| v37_rule7_three_pair (+ Rule 7) | $2,877 | 41.02% | −$156 |
| v38_rule8_qp (+ Rule 8 quads_pair) | $2,868 | 41.07% | −$165 |
| v39_rule9 (+ Rule 9 a/b/c) | $2,846 | 41.17% | −$187 |
| **v40_rule10 (+ Rule 10 J-low pair) — CURRENT PRODUCTION** | **$2,824** | **41.15%** | **−$209** |

**Same on prefix:**

| Strategy | Prefix $/1000h | Δ vs v8_hybrid prefix |
|---|---:|---:|
| v8_hybrid (prefix) | $3,051 | baseline |
| v37 (prefix) | $1,753 | −$1,298 |
| v38 (prefix) | $1,735 | −$1,316 |
| v39 (prefix) | $1,707 | −$1,344 |
| **v40 (prefix) — CURRENT PRODUCTION** | **$1,670** | **−$1,381** |

---

## What this leaves on the table (UPDATED Session 43)

- **For human play (open opportunities):** Q5 J-high no-pair has the biggest remaining oracle ceiling (+$54/1000h whole-grid on 60K hands) but requires multi-feature decomposition; top-position split is 3-way (27% hi, 34% lo, 39% other). Likely ML territory but worth a Session 44 deep-dive. T-low high_only naive top=lo rule (~+$8/1000h full-only) is below the both-grid threshold but cheap if we accept full-only validation.
- **For ML champion:** v34 unchanged. Biggest remaining residuals (full grid):
  - **high_only**: $572 share — OFFICIALLY ML-ONLY (Session 41); Session 43 confirmed top-pick is the structural lever but no clean rule
  - **pair**: $754 share — Rule 10 captures J-low subset; KK/AA single-suited Rule-4-bot residual remains
  - **two_pair**: $218 share — confirmed ML territory TWICE (Session 42 overnight + Session 43 Q4)
  - **trips**: $71 share — round-3 needs new diagnostic angles
  - **trips_pair**: $30 (already gated; G3 oracle +$85 ceiling open for ML exploration)
  - three_pair: ~$28 share (after v37 ship)
  - **composite**: ~$10 share total **after v39 ships** (~$30 left across remaining subtypes mostly via TT/T2P heuristic-vs-oracle gaps)
  - quads: ~$5 share **after v39 ships** (down from $23/1000h)

---

## What Session 43 produced

**Code (drills + production):**
- 3 new drill scripts (high_only Q1+Q2+Q5; J-low pair Q3; J-low two_pair Q4 revisit)
- 2 production strategies: `strategy_v40_rule10.py` (simple) + `strategy_v40b_rule10_gated.py` (gated variant)
- 2 graders: `grade_v40_rule10.py`, `grade_v40b_rule10_gated.py`

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 43 entry (TODO during session-end commit)
- `STRATEGY_GUIDE.md` Part 5 — Rule 10 reference (TODO)
- `STRATEGY_GUIDE.md` Part 6 — Rule 10 worked example + cheat sheet update (TODO)
- `STRATEGY_GUIDE.md` header — bumped Last updated (TODO)
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 076 added
- `SESSION_43_DEFENSIVE_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 44)

```
Resume Session 44 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Session 43 entry in Part 1; Part 5 lists v40 as
  current production; Part 6 has Rule 10 with worked example)
- CURRENT_PHASE.md (rewritten end of Session 43)
- DECISIONS_LOG.md (latest: Decision 076 — v40 Rule 10 ships)
- SESSION_43_DEFENSIVE_REPORT.md (standalone weak-hand defensive report)
- analysis/scripts/strategy_v40_rule10.py — current production
- analysis/scripts/strategy_v34_dt.py — ML champion

State (end of Session 43):
- Production strategy of record is now **v40_rule10** (10 rules: v39 +
  Rule 10 J-low pair defensive). +$37/1000h prefix lift confirmed
  (full grade pending; drill predicted +$22.73 full / +$36.70 prefix).
- Q4 (J-low two_pair re-examination) confirmed Session 42's "two_pair
  is ML territory" verdict. v33's adaptive splitting is genuine ML
  routing, not a hidden defensive rule.
- Q1 already-optimized; Q2/Q5 high-card-to-bot-for-flush hypothesis
  FAILED empirically.
- v34_dt remains ML champion. v40 changes 5.7% of grid (the J-low
  pair zone); some marginal ML signal expected from a v34 retrain.

Next session targets (priority order):

(A) v40 ML retrain — feed v34_dt with v40 baseline.

(B) Q5 J-high no-pair deep-dive — biggest unrealized oracle ceiling
    (+$54/1000h on 60K hands) but multi-feature; likely ML.

(C) T-low high_only naive top=lo rule (~+$8/1000h full-only).
    Methodology question: ship rules without prefix coverage?

(D) Round-3 within-trips features (Session 42 carryover).

(E) Learned A-vs-C decision tree for Rule 6 (Sessions 38-40 carryover).

(F) Trips_pair G3 oracle exploration.

(G) KK/AA single-suited Rule-4-bot residual.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ALL rules on BOTH full grid (N=200) AND prefix (N=1000)
  WHEN PREFIX COVERAGE EXISTS. high_only category has ZERO prefix
  coverage — full-only validation only.
- Methodology rule (Session 43 NEW): weak-hand top inversion is a
  unifying structural pattern. When highest card can't win top tier,
  dump LOWEST card to top and stack mid+bot.
- Methodology rule (Session 43 NEW): high_only category has zero
  prefix coverage; both-grid gate is INAPPLICABLE.
- Methodology rule (Session 43 NEW): high-card-to-bot-for-flush is
  a losing trade. Don't propose it.
- Methodology rule (Session 42 NEW): a rule with prefix regression
  >2× the full-grid lift does NOT ship.
- Methodology rule (Session 42 overnight NEW): suit-aware "non-X-suit"
  insight is a generalizable rule family. Watch for opportunities.
- Methodology rule (Session 42 overnight NEW): two_pair is ML territory
  (confirmed twice now — S42 overnight + S43 Q4).
- Methodology rule (Session 38): default ML champion ships use
  depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
