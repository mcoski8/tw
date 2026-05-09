# Current: Sprint 8 — Session 42 overnight wrap. **Rule 9 (3 sub-rules: plain quads + TT + T2P) ships in production as v39.** Combined +$22/1000h whole-grid (full N=200) + +$28/1000h whole-prefix (N=1000) — both grids positive, the consistency check passed cleanly. Quads pct_optimal jumps 9.5% → 45.9% (within-cat regret −66%); composite pct_optimal 28.1% → 33.6% (within-cat regret −37%). Six investigations ran in the overnight rule-mining pipeline; three produced ship-able both-grid-positive rules (9a plain quads, 9b TT E3a, 9c T2P boundary), one confirmed two_pair as ML-only territory (no split-rule rescue available), one identified the pair Rule 1 extension as a future Session 43 priority (QQ has $2,833/h v33 loss with 50/50 oracle split), one found existing Rule 3 already near-optimal. Rule 9a is a clean mirror of Rule 8 QP — same suit-aware "non-other-suit" pattern generalizes. Rule 9b uses the inverse insight ("top H-trip at suit IN L-suits"). Rule 9c adds a trip-rank boundary (T<=4 → HIGH pair to bot for stronger anchor). Methodology lesson NEW: the suit-aware multi-same-rank pattern is the structural insight unifying Rules 8 + 9a + 9b — it's a single "rule family" expressed across multiple populations.

> **🎯 IMMEDIATE NEXT ACTION (Session 43):**
>
>   (A) **Weak-hand defensive play investigation (USER PRIORITY).** ~14% of hands are J-high or lower — a massive unmined territory. See `docs/SESSION_43_WEAK_HAND_DEFENSE.md` for the full scope, sub-bucket stats, and the user's specific framing questions. Key drills: high-card-to-top-vs-to-bot decision when bot can be 4-flush; defensive structural picks for J-high pair / two-pair / no-pair sub-populations; re-examine the J-high two_pair zone through a defensive lens (overlaps with the deferred Rule 8 territory — v33's adaptive splitting may have been correct defensive play). The key uncertainty: do clean defensive rules exist as structural patterns, or is it multi-feature ML?
>
>   (B) **Pair Rule 1 cleanup (deferred from S42).** Drop Q,J from existing Rule 1 gate + add no-Ace QQ/JJ extension → ~+$5/1000h whole-grid. Below standalone-ship threshold but cheap; bundle with weak-hand findings.
>
>   (C) **Round-3 within-trips features.** Diagnose v34's residual within-trips ($1,291) for new structural signal. Feed back into ML as new gated feature family if found.
>
>   (C) **Learned A-vs-C decision tree for Rule 6** (deferred from Sessions 38–40). $5–13/1000h whole-grid ML target.
>
>   (D) **Trips_pair G3 oracle exploration** (Session 42 overnight finding). G3 (top=K, mid=2-trip-leftovers paired) has +$85/1000h oracle ceiling but no clean heuristic; would need ML or multi-feature search.
>
>   (E) **KK/AA single-suited Rule-4-bot residual** ($37/1000h below oracle). Defer behind A, B, C.
>
>   (F) **v34_dt re-train on v39 baseline.** v39 changes 0.42% of grid (across plain quads, TT, T2P). Tiny incremental ML signal expected.

> **✅ SHIPPED (Decision 075):** **v39_rule9** as the new production strategy of record. Replaces v38 in `STRATEGY_GUIDE.md` Part 5 + Part 6 + cheat sheet. Lives at `analysis/scripts/strategy_v39_rule9.py`. Production strategy chain is now 9 rules deep (Rules 1-8 unchanged + Rule 9 = 9a plain quads + 9b TT split-trip-to-top + 9c T2P trip-rank-boundary).

> **🔬 ARTIFACTS (Session 42 overnight):**
> 1. **`analysis/scripts/drill_tt_two_trips_deterministic.py`** — initial TT structural drill (E1/E2/E3a/E3b oracle classes; "always E1" gave +$0.73 lift only)
> 2. **`analysis/scripts/drill_tt_e3a_heuristic_hunt.py`** — 12+ suit-aware heuristic combos for E3a; winner "top∈L-suits, L-bot=DS-aware" → +$3.57 full / +$2.79 prefix
> 3. **`analysis/scripts/drill_plain_quads_structural.py`** — Q1a deterministic ("non-singleton-suit quads to mid") wins +$15.31 full / +$11.78 prefix; biggest single rule of the night
> 4. **`analysis/scripts/drill_t2p_trips_two_pair_deterministic.py`** + **`drill_t2p_deeper_boundary.py`** — initial then 23-rule sweep; winner "F3 if T<=4 else F2" → +$2.81 full / +$13.48 prefix
> 5. **`analysis/scripts/drill_two_pair_split_investigation.py`** + **`drill_two_pair_oracle_picks_full.py`** — confirmed split never wins per cell (0/78); two_pair is genuinely ML territory
> 6. **`analysis/scripts/drill_pair_rule1_extension.py`** — profiled 100K pair hands; QQ/JJ have biggest v33 loss with 50/50 oracle splits → Session 43 priority
> 7. **`analysis/scripts/drill_trips_pair_refinement.py`** — confirmed existing Rule 3 already near-optimal; G3 oracle ceiling +$85 but no clean heuristic
> 8. **`analysis/scripts/strategy_v39_rule9.py`** — NEW PRODUCTION STRATEGY (v39); three sub-rules
> 9. **`analysis/scripts/grade_v39_rule9.py`** — full + prefix grader; confirmed +$22 full / +$28 prefix
> 10. **`analysis/scripts/overnight_session42_rule_hunt.sh`** — pipeline runner
> 11. **`analysis/scripts/generate_session42_summary.py`** — auto-summary generator
> 12. **`SESSION_42_OVERNIGHT_REPORT.md`** — repo-root report with full findings, rankings, diminishing-returns frontier

> **📓 METHODOLOGY LESSONS (Session 42 overnight):**
> - **NEW: Suit-aware "non-X-suit" insight is a generalizable rule family.** Rule 8 QP (quads_pair) → Rule 9a (plain quads) is the same insight, different population. Rule 9b TT uses the inverse ("top at suit IN L-suits") for similar structural reasons. The pattern: when a hand has multiple same-rank cards (4 quads, 3 trips, 2 pairs), the suits of those cards interact with the suits of the rest of the hand. The structural pick uses one or another suit-overlap to force the bot to be DS.
> - **NEW: Diminishing returns are observable in boundary search.** T2P "F3 if T<=4 else F2" beats T<=5 by +$0.07 full / -$0.43 prefix; beats T<=6 by +$0.12 full / -$0.83 prefix. The boundary at the structural break (T=4 = "very low trip with no Omaha leverage") is the natural plateau.
> - **NEW: The both-grid validation gate works as a rule-quality filter.** 3 of 6 overnight investigations produced rules that passed both grids. 1 (two_pair split) confirmed ML-only. 1 (pair extension) showed promise but needs more gate-design work. 1 (trips_pair) found nothing improvable. The gate cleanly distinguishes generalize-able structural insights from full-grid-only artifacts.
> - **REINFORCED: human-strategy human-memorability frontier sits around 8-9 rules for routine memorization, +1-2 sub-rules per "rule" if they share a common pattern.** Rule 9 has 3 sub-rules but they all share the "split-the-multi-same-rank, suit-aware mid pick" pattern — memorization burden is 1.5× a base rule, not 3×.

> Updated: 2026-05-09 (overnight after end of Session 42 main work)

---

## Headline state at end of Session 42 (incl. overnight)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v39_rule9** | NEW PRODUCTION strategy of record (9 rules: v38 + Rule 9 a/b/c) | `analysis/scripts/strategy_v39_rule9.py` |
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| v38_rule8_qp | Prior production runtime (Session 42 morning ship; superseded by v39 same session overnight) | `analysis/scripts/strategy_v38_rule8_qp.py` |
| v37_rule7_three_pair | Predecessor production (Session 41 ship) | `analysis/scripts/strategy_v37_rule7_three_pair.py` |
| v35_rule6_v3 | Human strategy of record for trips (sharper Rule 6 boundary). NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` |
| v33_rule6_trips | Earlier production runtime | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v38_rule8_two_pair_DEFERRED | DEFERRED — Session 42 two_pair Rule 8 candidate. Confirmed ML-only by S42 overnight investigation. | `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` |
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
| **v39_rule9 (+ Rule 9 a/b/c) — CURRENT PRODUCTION** | **$2,846** | **41.17%** | **−$187** |

**Same on prefix:**

| Strategy | Prefix $/1000h | Δ vs v8_hybrid prefix |
|---|---:|---:|
| v8_hybrid (prefix) | $3,051 | baseline |
| v37 (prefix) | $1,753 | −$1,298 |
| v38 (prefix) | $1,735 | −$1,316 |
| **v39 (prefix) — CURRENT PRODUCTION** | **$1,707** | **−$1,344** |

---

## What this leaves on the table (UPDATED Session 42 overnight)

- **For human play (oracle-bound):** Rule 9 captures the suit-aware multi-same-rank pattern across 3 populations. ~$56K/1000h within-cat oracle ceilings remain on TT (E3a not fully captured) and T2P (deeper boundary plateau). Whole-grid contribution is small (~$5/1000h) — not worth more rules.
- **For human play (open opportunities):** pair Rule 1 extension on QQ/JJ is the biggest remaining structural opportunity (~$2,800/h within-cat × 0.466 share × 4 ranks of "broadway non-A" → potentially $50-100/1000h whole-grid if a clean rule exists). Session 43 priority.
- **For ML champion:** v34 unchanged. Biggest remaining residuals (full grid):
  - **high_only**: $572 share — OFFICIALLY ML-ONLY (Session 41)
  - **pair**: $754 share — KK/AA single-suited Rule-4-bot is the largest sub-stratum; QQ/JJ-to-bot extension also open
  - **two_pair**: $218 share — ML-only confirmed by S42 overnight
  - **trips**: $71 share — round-3 needs new diagnostic angles
  - **trips_pair**: $30 (already gated; G3 oracle +$85 ceiling open for ML exploration)
  - three_pair: ~$28 share (after v37 ship)
  - **composite**: ~$10 share total **after v39 ships** (~$30 left across remaining subtypes mostly via TT/T2P heuristic-vs-oracle gaps)
  - quads: ~$5 share **after v39 ships** (down from $23/1000h)

---

## What Session 42 overnight produced

**Code (drills + production):**
- 7 new drill scripts (TT initial + E3a, plain quads, T2P initial + deeper, two_pair split + oracle picks, pair Rule 1 extension, trips_pair refinement)
- 1 production strategy: `strategy_v39_rule9.py`
- 1 grader: `grade_v39_rule9.py`
- 2 pipeline scripts: `overnight_session42_rule_hunt.sh`, `generate_session42_summary.py`

**Documentation:**
- `STRATEGY_GUIDE.md` Part 1 — Session 42 overnight entry
- `STRATEGY_GUIDE.md` Part 5 — Rule 9 reference + new probes
- `STRATEGY_GUIDE.md` Part 6 — Rule 9a/9b/9c sections with worked examples; Step 1 categorize table updated; cheat sheet updated
- `STRATEGY_GUIDE.md` header — bumped Last updated to 2026-05-09 with overnight summary
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decision 075 added
- `SESSION_42_OVERNIGHT_REPORT.md` — repo-root standalone report

---

## Resume Prompt (Session 43)

```
Resume Session 43 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Session 42 overnight entry in Part 1; Part 5 lists v39 as
  current production; Part 6 has Rule 9a/9b/9c with worked examples)
- CURRENT_PHASE.md (rewritten end of Session 42 overnight)
- DECISIONS_LOG.md (latest: Decision 075 — v39 Rule 9 ships)
- SESSION_42_OVERNIGHT_REPORT.md (standalone overnight report)
- analysis/scripts/strategy_v39_rule9.py — current production
- analysis/scripts/strategy_v34_dt.py — ML champion

State (end of Session 42 overnight):
- Production strategy of record is now **v39_rule9** (9 rules, 3 sub-rules
  in Rule 9). Combined +$22/1000h whole-grid (full) + +$28/1000h prefix.
  Quads within-cat regret −66%; composite −37%.
- Two_pair confirmed genuinely ML territory (no split-rule rescue
  available; v33's prefix-wins come from suit/connectivity-driven
  non-hi-singleton tops).
- Pair Rule 1 extension (QQ/JJ to bot) is the biggest remaining
  structural opportunity, but requires careful gate design + both-grid
  validation. Drill artifact: drill_pair_rule1_extension.py.
- v34_dt remains the ML champion. v39 doesn't change ML champion;
  it's a rule-layer ship across 3 small populations (0.42% combined).

Next session targets (priority order):

(A) Weak-hand defensive play (USER PRIORITY). ~14% of hands are
    J-high or lower — biggest unmined territory. See
    docs/SESSION_43_WEAK_HAND_DEFENSE.md for the full scope. Key
    drill: high-card-to-top-vs-to-bot when bot can be made 4-flush.

(B) Pair Rule 1 cleanup (deferred from S42). Drop Q,J from existing
    Rule 1 gate + add no-Ace QQ/JJ extension → ~+$5/1000h. Bundle
    with weak-hand findings.

(C) Round-3 within-trips features. Diagnose v34's residual within-trips
    ($1,291) for new structural signal.

(C) Learned A-vs-C decision tree for Rule 6 (deferred from S38–40).
    $5–13/1000h whole-grid ML target.

(D) Trips_pair G3 oracle exploration (+$85/1000h ceiling).

(E) KK/AA single-suited Rule-4-bot residual.

(F) v34_dt re-train on v39 baseline.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ALL rules on BOTH full grid (N=200) AND prefix (N=1000).
- Methodology rule (Session 42 NEW): a rule with prefix regression
  >2× the full-grid lift does NOT ship.
- Methodology rule (Session 42 overnight NEW): suit-aware "non-X-suit"
  insight is a generalizable rule family. Rule 8 QP / Rule 9a plain
  quads / Rule 9b TT all use it. Watch for opportunities to apply.
- Methodology rule (Session 42 overnight NEW): diminishing returns are
  observable in boundary search; the structural break is the natural
  plateau.
- Methodology rule (Session 42 overnight NEW): two_pair is ML territory.
- Methodology rule (Session 41): heuristic-realizable ceilings vary
  by category; high_only is officially ML-only.
- Methodology rule (Session 38): default ML champion ships use
  depth=34 ml=2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
