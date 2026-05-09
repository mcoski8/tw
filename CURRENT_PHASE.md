# Current: Sprint 8 — Session 44 closes a methodology investigation triggered by user devil's-advocate questioning of Rule 10's bot construction. Ran two drills on the bot suit×connectivity priority hierarchy. The first (cross-product mean regret) showed surprising-but-confounded results (4-flush-run-4 outranking SS-run-4, contradicting Omaha first-principles). Consulted Gemini, who confirmed the **confounding hypothesis**: cross-class average regret is biased by hand-population differences. The second drill (within-hand pairwise) eliminated the confounder and produced a **definitive** suit×connectivity hierarchy: **suit dominates connectivity at every level** in the J-low no-pair zone. DS-scattered (worst DS) beats every non-DS class within-hand, including SS-run-4 (best SS) by +$1,603/1000h. The thinnest margin is DS-scattered vs SS-run-2+strays at +$111/1000h — basically tied but DS still wins. Within DS, connectivity matters but less than suit dominance: DS-run-4 vs DS-scattered = +$2,554, vs DS-vs-SS-at-run-4 = +$4,457. **No new rule shipped** — Session 44 invalidated the previous methodology rule "DS > SS > rainbow > 3+1 > 4-flush" (which came from trips territory) and replaced it with "suit dominates connectivity universally" via within-hand pairwise validation. v40b remains production. Surprising side-finding: **DS one-gap-4 beats DS run-4** by +$376/1000h within-hand — a missing internal rank creates a board-bridging straight bonus. Methodology lesson NEW: cross-class regret averaging is confounded by hand-population differences; within-hand pairwise comparison is the right methodology. Methodology lesson NEW: first-principles arguments must check payoff height in addition to probability — 4-flush-run-4 vs SS-run-4 was almost a wash because higher flush kicker compensates for lower flush probability.

> **🎯 IMMEDIATE NEXT ACTION (Session 45 — USER PRIORITY):**
>
>   (A) **Apply suit-dominance findings to J-low PAIR hands.** Rule 10 currently puts the pair in mid (anchored Hold'em) and the 4 highest non-pair singletons in bot. Session 44's within-hand pairwise drill showed that suit dominance is universal in J-low no-pair — but Rule 10's pair population was NOT covered by the within-hand pairwise drill (the drill restricted pair pop to mid=pair settings, eliminating bot configurations that would break the pair). The user's direction: drill the J-low single-pair zone for **"DS-bot at cost of breaking the pair" vs "pair-in-mid + non-DS bot"** within-hand pairwise. If breaking the pair to enable DS-bot wins, Rule 10 v3 should allow pair-breaking when DS-bot is achievable.
>
>   (B) **Extend to J-low two_pair zone.** Same question: does DS-bot beat keeping both pairs intact? Drill the J-low two_pair zone within-hand pairwise comparing "DS-bot built by breaking one or both pairs" vs "RA/RB/RC keeping pairs intact". If DS-bot wins, the Session 42/43 "two_pair is ML territory" verdict may need re-examination through the suit-dominance lens.
>
>   (C) **DS one-gap-4 vs DS run-4 follow-up.** Confirm in trips and other categories that one-gap-4 truly beats run-4. If so, this is a generalizable structural finding (board-bridging straight bonus dominates consecutive-rank straight value).
>
>   (D) **Carryover from Session 43:**
>     - v40 ML retrain (feed v34_dt with v40 baseline)
>     - Q5 J-high no-pair multi-feature deep dive ($54/1000h ceiling)
>     - T-low high_only naive top=lo rule (~+$8 full-only — methodology question on shipping full-only rules)
>     - Round-3 within-trips features (S42 carryover)
>     - Learned A-vs-C decision tree for Rule 6 (S38-40 carryover)
>     - Trips_pair G3 oracle exploration (+$85 ceiling)
>     - KK/AA single-suited Rule-4-bot residual

> **✅ NO NEW SHIP (Session 44):** v40b remains the production strategy of record. Session 44 was a methodology investigation that produced a refined priority hierarchy but did not yet translate into a new rule. The findings inform Session 45's planned drills.

> **🔬 ARTIFACTS (Session 44):**
> 1. **`analysis/scripts/drill_bot_suit_run_priority.py`** — cross-product 5×7 (suit × connectivity) drill with mean regret per cell (CONFOUNDED — kept for diagnostic purposes; do not use for production decisions)
> 2. **`analysis/scripts/drill_bot_suit_run_pairwise.py`** — within-hand pairwise drill (DEFINITIVE — used to derive the priority hierarchy)
> 3. **`SESSION_44_SUIT_CONNECTIVITY_REPORT.md`** — repo-root standalone report with full findings and tipping-point analysis

> **📓 METHODOLOGY LESSONS (Session 44 NEW):**
> - **Cross-class average regret is confounded by hand-population differences.** "Mean best EV in class" averaged across hands where the class is achievable mixes hand-overall-EV variance into the per-class metric. Different classes have different achievability populations. Always validate cross-class comparisons via within-hand pairwise.
> - **Suit dominates connectivity at every level (J-low no-pair).** No tipping point exists where non-DS suit beats DS within-hand. DS-scattered ≥ all SS, 4-flush, 3+1, rainbow.
> - **First-principles arguments must check payoff height, not just probability.** The "4-flush has fewer deck outs → SS wins" argument was incomplete. 4-flush-run-4 ≈ SS-run-4 within-hand because flush HEIGHT compensates for flush probability.
> - **DS one-gap-4 ≥ DS run-4** (counterintuitive but real, +$376/1000h within-hand). A missing internal rank creates board-bridging straight value that beats consecutive-rank value.
> - **Original "DS > SS > rainbow > 3+1 > 4-flush" methodology rule was incomplete.** Refined: "DS > everything (suit dominates), then 4-flush ≈ SS at strong connectivity, 3+1 ≈ SS, all rainbow at the bottom." More importantly, the priority should be checked against BOT-level achievability per hand, not assumed universally.

> Updated: 2026-05-09 (Session 44)

---

## Headline state at end of Session 44

**Strategies of record (UNCHANGED from end of Session 43):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v40b_rule10_gated** | PRODUCTION strategy of record (10 rules: v39 + Rule 10 with gate "pair ≤ 6 OR pair == max"). +$48 full / +$37 prefix lift over v39. | `analysis/scripts/strategy_v40b_rule10_gated.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v40_rule10 | Simple variant of Rule 10 (no gate). +$23 full / +$37 prefix. Retained for human-strategy memorability fork. | `analysis/scripts/strategy_v40_rule10.py` |
| v39_rule9 | Predecessor production (Session 42 overnight ship) | `analysis/scripts/strategy_v39_rule9.py` |
| v38_rule8_qp | Predecessor production | `analysis/scripts/strategy_v38_rule8_qp.py` |
| v37_rule7_three_pair | Earlier production runtime | `analysis/scripts/strategy_v37_rule7_three_pair.py` |
| v35_rule6_v3 | Human strategy of record for trips (sharper Rule 6 boundary). NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` |
| v33_rule6_trips | Earlier production runtime | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v38_rule8_two_pair_DEFERRED | DEFERRED — Session 42 two_pair Rule 8 candidate. Confirmed ML-only twice (S42 overnight + S43 Q4). | `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` |
| v36_rule7_high_only | ARCHIVED — Session 41 failed Rule 7 attempt for high_only | `analysis/scripts/strategy_v36_rule7_high_only.py` |

**Capacity + feature progression — UNCHANGED:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| **v34** | **34 (33 actual)** | **2** | **83** | **874,548** | **$1,681** | **52.02%** | (latest) |

**Human-strategy progression (full grid, N=200) — production runtime UNCHANGED:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v28_rule5_rainbow (+ Rules 4 + 5) | $3,032 | 39.64% | −$1 |
| v33_rule6_trips (+ Rule 6 v1) | $2,920 | 40.68% | −$113 |
| v37_rule7_three_pair (+ Rule 7) | $2,877 | 41.02% | −$156 |
| v38_rule8_qp (+ Rule 8 quads_pair) | $2,868 | 41.07% | −$165 |
| v39_rule9 (+ Rule 9 a/b/c) | $2,846 | 41.17% | −$187 |
| v40_rule10 (+ Rule 10, simple variant) — sister candidate | $2,824 | 41.15% | −$209 |
| **v40b_rule10_gated (+ Rule 10 gated) — CURRENT PRODUCTION** | **$2,798** | **41.48%** | **−$235** |

---

## What Session 44 produced

**Code:**
- 2 new drill scripts (`drill_bot_suit_run_priority.py` confounded; `drill_bot_suit_run_pairwise.py` definitive)
- 0 new strategy candidates
- 0 new graders

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 44 entry (TODO during commit)
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 077 added
- `SESSION_44_SUIT_CONNECTIVITY_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 45)

```
Resume Session 45 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 44)
- DECISIONS_LOG.md (latest: Decision 077 — bot suit×connectivity priority,
  methodology investigation; no new ship)
- SESSION_44_SUIT_CONNECTIVITY_REPORT.md (standalone report on the
  within-hand pairwise drill that produced the definitive priority)
- SESSION_43_DEFENSIVE_REPORT.md (the Rule 10 ship that triggered
  this line of investigation)
- STRATEGY_GUIDE.md (Session 44 entry in Part 1)
- analysis/scripts/strategy_v40b_rule10_gated.py — current production
- analysis/scripts/drill_bot_suit_run_pairwise.py — the definitive S44 drill
- analysis/scripts/drill_low_pair_J_high_defense.py — Rule 10's underlying drill

State (end of Session 44):
- Production unchanged: v40b_rule10_gated (Rule 10, J-low pair defensive,
  gated by "pair ≤ 6 OR pair == max"). +$48 full / +$37 prefix vs v39.
- Session 44 produced no new ship — it was a methodology investigation
  triggered by user devil's-advocate questioning of Rule 10.
- Definitive finding: SUIT DOMINATES CONNECTIVITY in J-low no-pair
  bot construction. DS-scattered (worst DS) beats every non-DS class
  within-hand. No tipping point exists.
- Surprising side-finding: DS one-gap-4 ≥ DS run-4 (+$376/1000h within
  hand) — a missing internal rank creates a board-bridging straight bonus.

USER-PRIORITY DIRECTION FOR SESSION 45 (verbatim):
"Now that we have a definitive answer for defensive J-high no-pair
hands, we need to compare that to J-high hands with a pair and see how
to play these. Do we favor the pair in the middle still? What about if
it breaks double-suited on bottom? Does that mean DS on bottom even at
the cost of breaking a pair is our best option? And then this can flow
into J-high with two pair, do we favor DS on bottom STILL? What if it
means breaking our two pair? Etc."

Translation into drills:

(A) drill_J_low_pair_DS_break.py — for J-low single-pair hands, drill
    "best DS-bot config" vs "best non-DS-bot config with pair-in-mid"
    within-hand pairwise. Categories of comparison:
      A1: pair-in-mid + DS-bot achievable (rare; hand has 2+2 suit
          pattern across 4 non-pair singletons) — Rule 10 baseline
      A2: pair-in-mid + non-DS-bot (Rule 10's typical case)
      A3: pair-split (one pair-member to bot, the other to mid or top)
          + DS-bot achievable
      A4: pair-to-bot (both pair-members in bot) + DS-bot achievable
    Find the lift of A3/A4 over A1/A2 within-hand. If positive,
    Rule 10 v3 should allow pair-breaking when DS-bot is achievable.

(B) drill_J_low_two_pair_DS_break.py — same question for two_pair:
    B1: both-pairs-intact + best-bot
    B2: split one pair (one member moved out) + DS-bot
    B3: both pairs split + DS-bot
    Within-hand pairwise lift of B2/B3 over B1. If positive, the
    Session 42/43 "two_pair is ML territory" verdict needs revisiting
    through the suit-dominance lens.

(C) Validate findings on FULL grid (N=200) AND PREFIX grid (N=1000).
    J-low pair has prefix coverage (~10% of prefix is J-low pair=2
    cells); J-low two_pair has prefix coverage too.

(D) If suit-dominance-over-pair-anchor pattern holds: design Rule 10 v3
    (or new Rule 11) that conditionally breaks pairs for DS-bot.
    If pattern doesn't hold (pair-anchor is more important): document
    the boundary and refine the human-strategy guide.

Carryover from Session 44 (lower priority):
- DS one-gap-4 vs DS run-4 follow-up: confirm in trips category
- v40 ML retrain
- Q5 J-high no-pair multi-feature deep dive
- T-low high_only naive top=lo rule
- Round-3 within-trips features
- Learned A-vs-C decision tree for Rule 6
- Trips_pair G3 oracle exploration
- KK/AA single-suited Rule-4-bot residual

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ALL rules on BOTH full grid (N=200) AND prefix (N=1000)
  WHEN PREFIX COVERAGE EXISTS. high_only category has ZERO prefix.
- Methodology rule (Session 44 NEW): cross-class regret averaging is
  confounded by hand-population differences. Always validate cross-class
  comparisons via within-hand pairwise.
- Methodology rule (Session 44 NEW): suit dominates connectivity at every
  level (J-low no-pair). No tipping point.
- Methodology rule (Session 44 NEW): first-principles arguments need to
  check payoff height in addition to probability.
- Methodology rule (Session 43 NEW): weak-hand top inversion.
- Methodology rule (Session 43 NEW): high_only zero prefix coverage.
- Methodology rule (Session 43 NEW): high-card-to-bot-for-flush is
  a losing trade.
- Methodology rule (Session 42 NEW): a rule with prefix regression
  >2× the full-grid lift does NOT ship.
- Methodology rule (Session 42 overnight NEW): suit-aware "non-X-suit"
  insight is a generalizable rule family.
- Methodology rule (Session 42 overnight NEW): two_pair was previously
  declared ML territory (twice — S42 overnight + S43 Q4) but Session 45's
  pair-breaking-for-DS drill may revisit this through the suit-dominance lens.
- Methodology rule (Session 38): default ML champion ships use depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
