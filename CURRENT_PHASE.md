# Current: Sprint 8 — Session 40 wrap. **Rule 6 low-trips reference table (Trip T down to 2) appended to STRATEGY_GUIDE.md Part 6 as Examples 7–14.** Connectivity probe (`probe_low_trips_connectivity.py`) tested whether bot run-length should add a 4th tier to Step 2's suit-matching priority — verdict NO (connectivity is invariant across the 3 trip-to-bot picks on the same hand; the alt priority "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1" regresses $11/1000h whole-grid; the oracle picks rainbow 0% of the time when SS or DS is available). Per-cell A-vs-C oracle map cross-referenced — A wins ≥99% in every n≥5 cell at trip ≤ T, including low-max-kicker cells. **No production code change.** v33 stays in runtime; v35 stays in the human guide; v34_dt remains the ML champion.

> **🎯 IMMEDIATE NEXT ACTION (Session 41):**
>
>   (A) **Always-X structural baseline probes for remaining categories** (PRIMARY). Apply the Rule 6 / `verify_rule6_v14_trips` template systematically:
>      - **three_pair** (UNTOUCHED by gating; $31/1000h whole-grid budget). Likely candidate: "always top = unpaired card; mid = highest pair; bot = 2 lower pairs (paired bot for trips/full-house equity)." Write `verify_rule_X_v33_three_pair.py`.
>      - **composite** ($3.4/1000h whole-grid; high per-category regret). Heterogeneous category — may need sub-stratification.
>      - **two_pair** ($218 share; heavily ML-engineered already). Candidate: "always split high pair to mid".
>      - **high_only** ($572 share — biggest residual). v3 already routes this in v8_hybrid; check if v3's structural decisions match the oracle.
>      Each probe writes `verify_rule_X_v33_<category>.py`, reports BOTH the oracle ceiling AND the closest heuristic-realizable headline (Session 38 lesson — heuristic ceilings are usually 30-95% smaller than oracle ceilings).
>
>   (B) **Round-3 within-trips features (or pair-r5 / two_pair-r2).** v34's trips category lifted to $1,291 within-cat — within-trips share is now 4.2% of grid. Write `distill_v34_trips.py` to find the within-trips structure that v34's 4 trips_v2 features still don't capture. If a structural baseline exists, feed it back into ML as a new gated feature family.
>
>   (C) **Learned A-vs-C decision tree for Rule 6.** Reframes Sessions 38–39's negative-heuristic results as an ML target: a small classification tree on `(trip_rank, max_kicker_rank, kicker suit profile, kicker suit-sharing pattern)` trained against the oracle's A-or-C choice. **$5-13/1000h whole-grid ceiling.** Session 40's connectivity probe surfaced an additional within-SS disagreement signal ($1,212/1000h_within_low_trips, ≈$19.53/1000h whole-grid mean lift) that can also be input to this tree's training. Could ship as new gated feature family `rule6_ac_*_g` → v35_dt or v36_dt ML candidate.
>
>   (D) **KK/AA single-suited Rule-4-bot residual** ($37/1000h below oracle, 52.9% of KK/AA, 1.95% of grid). Defer behind A, B, C. v31a's tight gating shipped only +$6 — needs a different angle (meta-classifier feature trained on probe data, or sub-tree dedicated to KK/AA).
>
>   (E) **Production v36_rule6_v3 candidate ship** — replace v33 with v35 in the production runtime IF a learned A-variant heuristic (priority C delivers it) closes the heuristic-A gap. Until then, production stays at v33; v35 is human-guide only.

> **✅ SHIPPED THIS SESSION (no DECISIONS_LOG entry — additive documentation only):**
> 1. **STRATEGY_GUIDE.md Part 6**: 8 new worked examples (Examples 7–14, Trip T down to Trip 2) appended after the Trip-7 example. Each example illustrates a distinct teaching point (rainbow kickers + all-SS; two-and-one kickers + DS find; 3+1 trap; 4-run incidental bot; wheel-eligible incidental bot; weak-hand acceptance). All 8 examples verified against `strategy_v35_rule6_v3.py` to confirm pick correctness.
> 2. **STRATEGY_GUIDE.md Part 6 "Why it works" addendum**: documented Session 40's connectivity-tier finding so future readers know why Step 2 doesn't include a run/wheel tier.
> 3. **STRATEGY_GUIDE.md Part 1 Session 40 entry**: full session log with the two methodology lessons (connectivity invariance + selection-effect awareness).

> **🔬 ARTIFACTS (Session 40):**
> 1. **`analysis/scripts/probe_low_trips_connectivity.py`** — new probe, 30K trips × low-trip subset (20,849 hands × 3 picks each = 62,547 pick-rows). Reports mean oracle EV per (suit_profile × longest_run), per-hand heuristic-vs-oracle disagreements, alt-priority head-to-head, wheel-eligible bonus test, rainbow-run-4 spotlight.
> 2. **Per-cell map confirmation** — re-ran `probe_rule6_c_variant.py` against the same 30K trips sample. Verdict unchanged from Session 38: A wins in every n≥5 cell at trip ≤ T, including the lowest max-kicker rows (Trip 6+5: C-A=$-15,585 within-trips; Trip T+5: $-2,871).

> **📓 METHODOLOGY LESSONS (Session 40):**
> - **NEW: Candidate-level invariance is a prerequisite for any candidate-level priority.** Step 2's priority orders K candidates that share a fixed rank set (the bot's 4 ranks are determined the moment Step 1 fires). Any feature derived from ranks alone (longest_run, rank_sum, broadway_count, wheel-eligibility) is invariant across the K candidates. Only features that vary between candidates (here, suit assignment) can serve as primary tiers OR tiebreakers. **Future Step-2-style probes should check candidate-level invariance before adding a feature to the priority.** Wasted effort otherwise.
> - **NEW: When a probe's mean-EV-per-cell shows a "feature predicts bad outcomes", check for selection effects before drawing rule-shaping conclusions.** "Wheel-eligible bots have $-32K mean EV vs $-14K for non-wheel" looks like the wheel is bad; in reality, the population that produces wheel-eligible bots is the population of weak hands. Always test whether the feature is correlating with the population (selection effect) or with within-population settings (true causal signal) before treating it as actionable.
> - **REINFORCED (Session 38–39): heuristic-realizable ceilings are still ~5–50% of oracle ceilings.** Session 40's $1,212/1000h within-SS disagreement gap is the kind of residual that learned ML (not heuristics) can capture. Reframes Priority C: the learned A-vs-C tree can absorb both the cell-level boundary signal AND the within-SS suit-pick signal in one tree.

> Updated: 2026-05-07 (end of Session 40)

---

## Headline state at end of Session 40

**Strategies of record (UNCHANGED from Session 39):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| **v35_rule6_v3** | Human strategy of record (Rule 6 sharpened boundary + suit-matching procedure + Session 40 reference table). Used in `STRATEGY_GUIDE.md` Part 6. NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` + STRATEGY_GUIDE.md Part 6 |
| v33_rule6_trips | Production runtime Rule 6 path (Session 37 ship). Stays at runtime because v35 heuristic regresses. | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` + `data/v32_dt_model.npz` |
| v31_dt | 79 features at depth=32 ml=3 | `analysis/scripts/strategy_v31_dt.py` + `data/v31_dt_model.npz` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v34_rule6_v2 | ARCHIVED — Session 38 negative-result candidate | `analysis/scripts/strategy_v34_rule6_v2.py` |
| v32_d34ml3 | ARCHIVED — Session 38 control retrain | `data/v32_d34ml3_dt_model.npz` |
| v28_rule5_rainbow | Predecessor human chain (v14 + Rule 4 + Rule 5) | `analysis/scripts/strategy_v28_rule5_rainbow.py` |
| v31a / v31b / v20b / v19 / v21 / v22 | ARCHIVED candidates | various |

**Capacity + feature progression (full 6M grid, N=200) — UNCHANGED from Session 38:**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| v18e | 30 | 5 | 37 | 274,446 | $2,066 | 47.08% | — |
| v20 | 30 | 5 | 43 (gated suited) | 307,939 | $1,982 | 47.81% | −$84 |
| v23 | 30 | 5 | 49 (43+6 gated TP) | 314,705 | $1,977 | 47.89% | −$5 vs v20 |
| v24 | 30 | 5 | 53 (49+4 gated comp) | 314,759 | $1,977 | 47.89% | −$1 vs v23 |
| v25 | 30 | 5 | 59 (53+6 gated pair) | 390,626 | $1,929 | 48.43% | −$47 vs v24 |
| v26 | 30 | 5 | 65 (59+6 gated t2p) | 459,209 | $1,859 | 49.21% | −$70 vs v25 |
| v27 | 30 | 5 | 69 (65+4 gated ho) | 460,375 | $1,853 | 49.27% | −$6 vs v26 |
| v29 | 30 | 5 | 73 (69+4 gated pair_r4) | 486,342 | $1,807 | 49.80% | −$46 vs v27 |
| v30 | 30 | 5 | 79 (73+6 gated trips) | 493,057 | $1,794 | 49.98% | −$13 vs v29 |
| v31 | 32 | 3 | 79 (same as v30) | 699,773 | $1,736 | 50.92% | −$58 vs v30 (capacity-only) |
| v32 | 32 | 3 | 83 (79 + 4 trips_v2) | 731,606 | $1,715 | 51.31% | −$20 vs v31 |
| **v34** | **34 (33 actual)** | **2** | **83 (same as v32)** | **874,548** | **$1,681** | **52.02%** | **−$34 vs v32** |

**Same sweep on N=1000 prefix:** unchanged from Session 38 — v34 at $889/1000h / 62.74%.

**Per-category breakdown (full grid, N=200):** unchanged from Session 38. Session 40 made no production code change, so the per-category EVs are identical.

**Human-strategy progression (full grid, N=200) — production runtime:**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v8_hybrid (pre-Rule chain) | $3,153 | — | — |
| v14_combined (Rules 1-3) | $3,033 | 39.5% | baseline |
| v28_rule5_rainbow (+ Rule 4 + Rule 5) | $3,032 | 39.64% | −$1 |
| **v33_rule6_trips (+ Rule 6 v1 — current production)** | **$2,920** | **40.68%** | **−$113** |

**Human-strategy ceiling (oracle-bound, what a thoughtful reader of the guide can in principle achieve):**

| Strategy | Mode | $/1000h whole-grid (lower is better) | Δ vs v33 oracle-bound |
|---|---|---:|---:|
| v33 oracle-bound | reader picks best-A or best-C within v33 boundary | $-42.56/1000h | baseline |
| **v35 oracle-bound** | reader picks best-A or best-C within v35 sharper boundary | **$-34.44/1000h** | **+$8.12** |
| Pure oracle | reader picks any A∪C cell freely | $-3.51/1000h | +$39.05 |

**Note:** Session 40 did NOT change v35's boundary or any score. The new examples in Part 6 are an additive teaching aid — the underlying strategy is identical. The connectivity probe confirmed Step 2's priority is correct, so no rule change.

---

## What this leaves on the table (UNCHANGED from Session 39)

- **For human play (oracle-bound):** v35 captures 63% of the Decision 070 oracle ceiling. The remaining 37% (~$4.77/1000h) is in the noisy Trip J + low-kicker cells the user simplified out for memorability. Reframed as Priority C (learned A-vs-C tree).
- **For production runtime:** v33 still misses $86/1000h of Rule 6's full-A∪C oracle ceiling. The v33→v35 boundary sharpening doesn't help at runtime because heuristic-A is the bottleneck. Closing this gap requires a learned A-variant heuristic (Priority C). **NEW in Session 40:** the connectivity probe surfaced a $19.53/1000h within-SS suit-pick disagreement signal that's another input for Priority C's training data.
- **For ML champion:** v34 captures 44.6% of the v14→ceiling gap at N=200, 71% at N=1000. Biggest residuals at full grid: high_only $572, pair $754, two_pair $218, trips $71, three_pair $31, trips_pair $30, composite $2.9.

---

## What Session 40 produced

**1. `analysis/scripts/probe_low_trips_connectivity.py`** — new probe (~250 lines). Scope: trip_rank ≤ T A-variant hands. For each hand, enumerates all 3 trip-to-bot picks; computes (suit_profile, longest_run, oracle_ev) per pick; reports per-hand heuristic-vs-oracle disagreement, alt-priority head-to-head, wheel-bonus test, rainbow-run-4 spotlight. Run output saved to `/tmp/probe_low_trips_connectivity.log` (not committed; can be re-run).

**2. STRATEGY_GUIDE.md Part 6 — 8 new worked examples (Examples 7–14)**:
- Example 7 — Trip T (rainbow kickers, all SS)
- Example 8 — Trip 9 (DS find via two-and-one)
- Example 9 — Trip 8 (3+1 trap visible)
- Example 10 — Trip 6 (4-run bot, illustrates connectivity is incidental)
- Example 11 — Trip 5 (wheel-eligible bot, same point)
- Example 12 — Trip 4 (rainbow, simple SS, weak-hand acceptance)
- Example 13 — Trip 3 (rainbow, simple SS)
- Example 14 — Trip 2 (rainbow, simple SS, lowest possible)

All 8 verified against `strategy_v35_rule6_v3.py`.

**3. STRATEGY_GUIDE.md Part 6 "Why it works" addendum**: documents Session 40's connectivity-tier rejection so future readers/maintainers see why Step 2's priority intentionally excludes run-length.

**4. STRATEGY_GUIDE.md Part 1 Session 40 entry**: full session log with two new methodology lessons.

**5. CURRENT_PHASE.md** rewritten (this file).

---

## Resume Prompt (Session 41)

```
Resume Session 41 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Part 1 Session 40 entry; Part 2 v34_dt is current ML
  champion; Part 6 has Rule 6 with full Trip A..2 reference table now)
- CURRENT_PHASE.md (rewritten end of Session 40)
- DECISIONS_LOG.md (latest: Decision 071 — v35_rule6_v3 ships in
  the human strategy guide; production keeps v33; no Session 40 decision)
- analysis/scripts/probe_low_trips_connectivity.py — Session 40 probe
- analysis/scripts/strategy_v35_rule6_v3.py — human strategy of record
- analysis/scripts/strategy_v33_rule6_trips.py — production heuristic

State (end of Session 40):
- Rule 6 reference table for trips T..2 shipped to STRATEGY_GUIDE.md Part 6
  as 8 new worked examples (Examples 7–14). Connectivity-tier hypothesis
  was tested and rejected (`probe_low_trips_connectivity.py`): the alt
  priority "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1" regresses
  $11/1000h whole-grid; rainbow is oracle-preferred 0% of the time when
  SS or DS is available; bot run-length is invariant across the 3
  trip-to-bot picks on a given hand so cannot be a tiebreaker.
- A0 work for Rule 6 is now COMPLETE. Trip A through Trip 2 each have
  explicit per-rank treatment + at least one worked example.
- Production v33 unchanged. v34_dt unchanged. v35 unchanged (only its
  documentation deepened).
- Methodology rule (Session 40 NEW): Candidate-level invariance is a
  prerequisite for any candidate-level priority/tiebreaker. Check
  before adding features.
- Methodology rule (Session 40 NEW): Mean-EV-per-cell aggregates can hide
  selection effects. Always confirm whether a feature's correlation with
  poor outcomes is causal-within-population vs population-of-weak-hands.

Next session targets (priority order):

(A) Always-X structural baseline probes for remaining categories.
    - three_pair (untouched by gating, 1.9% share)
    - composite (high per-category regret, tiny share)
    - two_pair (heavily ML-engineered already)
    - high_only (largest residual share, 20.4%)
    Each probe writes verify_rule_X_v33_<category>.py; report BOTH
    oracle ceiling AND heuristic-realizable headline.

(B) Round-3 within-trips features. Diagnose v34's residual within-trips
    ($1,291) for new structural signal. Feed back into ML as a new
    gated feature family if found.

(C) Learned A-vs-C decision tree for Rule 6. Two training signals:
    (1) the cell-level A-vs-C boundary (Sessions 38–39 oracle map).
    (2) the within-SS suit-pick disagreement (Session 40 connectivity
        probe — $19.53/1000h whole-grid mean lift on disagreement
        subset, dominantly SS→SS suit-rotation). $5-13/1000h whole-grid
        target. Could finally close Rule 6's heuristic-A gap and let
        production adopt v35.

(D) KK/AA single-suited Rule-4-bot residual ($37/1000h below oracle).

(E) Production v36_rule6_v3 candidate ship — replace v33 with v35 in
    runtime IF Priority C delivers a learned A-variant heuristic that
    closes the heuristic-A gap.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated and use a UNIQUE
  prefix. Claimed: `_g` (suited), `tp_*_g` (trips_pair), `comp_*_g`
  (composite), `pair_*_g` (pair v1), `t2p_*_g` (two_pair), `ho_*_g`
  (high_only), `pair_r4_*_g` (pair v2), `trips_*_g` (trips), and
  `trips_v2_*_g` (trips round 2). For Priority C: claim
  `rule6_ac_*_g` for the learned A-vs-C tree.
- Methodology rule (Session 38): default ML champion ships now use
  depth=34 ml=2. Capacity sweeps: ml ∈ {3, 2} at depth=34+. Capacity
  ships skip tripwire.
- Methodology rule (Session 38): always-X probes must report BOTH
  oracle ceiling AND heuristic-realizable headline.
- Methodology rule (Session 39): the human strategy guide can be
  sharper than the production heuristic when heuristic-A is the
  rate-limiting step. Two-track ship (guide ships, runtime stays).
- Methodology rule (Session 40 NEW): Candidate-level invariance is a
  prerequisite for any candidate-level priority/tiebreaker.
- Methodology rule (Session 40 NEW): Mean-EV-per-cell aggregates can
  hide selection effects.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
