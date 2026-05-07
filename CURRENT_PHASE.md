# Current: Sprint 8 — Session 39 wrap. **One human-strategy ship: v35_rule6_v3 ships in STRATEGY_GUIDE.md Part 6 as the new human strategy of record (oracle-bound +$8.12/1000h whole-grid vs v33).** Production runtime stays at v33 because heuristic-A loses $4/1000h on the flipped cells (the bot-DS optimizer is the rate-limiting step, exactly as Session 38's sweep predicted). Two-track ship — methodology rule NEW: the human strategy guide can be sharper than the production heuristic when heuristic-A is the rate-limiting step. The Rule 6 prose was also rewritten in plain English (dropped A/C variant jargon) with 6 worked examples and a 2-step suit-matching procedure for "which trip joins bot" (priority: DS 2+2 > SS 2+1+1 > 3+1 avoid).

> **🎯 IMMEDIATE NEXT ACTION (Session 40):**
>   (A) **Always-X structural baseline probes for remaining categories** (deferred from Sessions 38–39). Apply the Rule 6 / `verify_rule6_v14_trips` template systematically:
>      - **three_pair** (UNTOUCHED by gating; $31/1000h whole-grid budget). Likely candidate: "always top = unpaired card; mid = highest pair; bot = 2 lower pairs (paired bot for trips/full-house equity)." Write `verify_rule_X_v33_three_pair.py`.
>      - **composite** ($3.4/1000h whole-grid; high per-category regret). Heterogeneous category — may need sub-stratification.
>      - **two_pair** ($218 share; heavily ML-engineered already). Candidate: "always split high pair to mid".
>      - **high_only** ($572 share — biggest residual). v3 already routes this in v8_hybrid; check if v3's structural decisions match the oracle.
>      Each probe writes `verify_rule_X_v33_<category>.py`, reports BOTH the oracle ceiling AND the closest heuristic-realizable headline (Session 38 lesson — heuristic ceilings are usually 30-95% smaller than oracle ceilings).
>
>   (B) **Round-3 within-trips features (or pair-r5 / two_pair-r2).** v34's trips category lifted to $1,291 within-cat — within-trips share is now 4.2% of grid. Write `distill_v34_trips.py` to find the within-trips structure that v34's 4 trips_v2 features still don't capture. If a structural baseline exists, feed it back into ML as a new gated feature family.
>
>   (C) **Learned A-vs-C decision tree for Rule 6.** Reframes Sessions 38–39's negative-heuristic results as an ML target: a small classification tree on `(trip_rank, max_kicker_rank, kicker suit profile)` trained against the oracle's A-or-C choice. **$5-13/1000h whole-grid ceiling per Session 39 (v35 human-ceiling captures $8.12, leaves ~$4.77 of the $12.89 Decision 070 oracle).** Could ship as new gated feature family `rule6_ac_*_g` → v35_dt or v36_dt ML candidate.
>
>   (D) **KK/AA single-suited Rule-4-bot residual** ($37/1000h below oracle, 52.9% of KK/AA, 1.95% of grid). Defer behind A, B, C. v31a's tight gating shipped only +$6 — needs a different angle (meta-classifier feature trained on probe data, or sub-tree dedicated to KK/AA).
>
>   (E) **Production v36_rule6_v3 candidate ship** — replace v33 with v35 in the production runtime IF a learned A-variant heuristic (priority C delivers it) closes the heuristic-A gap. Until then, production stays at v33; v35 is human-guide only.

> **✅ SHIPPED (Decision 071):** v35_rule6_v3 in `STRATEGY_GUIDE.md` Part 6 as the human strategy of record. Headline: oracle-bound human ceiling **+$8.12/1000h whole-grid vs v33** on the 30K trips probe (63% of Decision 070's $12.89 oracle ceiling). Sacrifices ~$4.77/1000h vs the per-cell-optimal map by simplifying noisy Trip J + low-kicker cells away.
>
> Per-trip-rank lifts (oracle-bound v35 vs v33):
>
> | Trip rank | Δ within-trips | Δ whole-grid |
> |---|---:|---:|
> | 6 | +$67 | +$0.28 |
> | 7 | +$78 | +$0.32 |
> | 8 | +$192 | +$0.81 |
> | 9 | +$374 | +$1.56 |
> | T | +$583 | +$2.40 |
> | J | +$603 | +$2.54 |
> | Q | +$48 | +$0.19 |
> | A, K, ≤5 | $0 | $0 |
> | **Total** | | **+$8.12/1000h whole-grid** |

> **🚫 NOT SHIPPED in production runtime:** v35 heuristic loses $4.06/1000h whole-grid on disagreement cells vs v33. Production still calls `strategy_v33_rule6_trips` for runtime decisions. v35 lives in `analysis/scripts/strategy_v35_rule6_v3.py` and is used only by `verify_rule6_v3_human.py`.

> **🔬 ARTIFACTS (Session 39):**
> 1. **`analysis/scripts/strategy_v35_rule6_v3.py`** — sharpened boundary in code form. Boundary helper `_v35_pick_c(trip_rank, kicker_ranks)` returns True iff the third trip card goes on TOP (C variant). The A-variant body keeps v33's (suit_profile, rank_sum, longest_run) heuristic for now.
> 2. **`analysis/scripts/verify_rule6_v3_human.py`** — head-to-head verification on the 30K trips probe. Reports v33-oracle-bound, v35-oracle-bound, v33-heuristic, v35-heuristic, and per-trip-rank lifts.
> 3. **STRATEGY_GUIDE.md Part 6 rewrite** — the trips section now reads in plain English with no A/C jargon. Step 1 = the per-trip-rank table (where third trip card goes). Step 2 = the suit-matching procedure (which trip joins bot, with three named bot shapes DS/SS/3+1 and three named kicker patterns two-and-one/rainbow/three-of-a-suit). Six worked examples.
> 4. **STRATEGY_GUIDE.md Part 5 rewrite** — separates production rule code path (`strategy_v33_rule6_trips.py`, runtime) from human-guide code path (`strategy_v35_rule6_v3.py`, ceiling-evaluator). Adds probe registry.

> **📓 METHODOLOGY LESSONS REINFORCED + NEW (Session 39):**
> - **NEW: The human strategy guide can be sharper than the production heuristic when heuristic-A is the rate-limiting step.** Sessions 38 and 39 together establish this. Session 38 archived v34_rule6_v2 because heuristic-A couldn't cash a sharper boundary (-$0.57/1000h max). Session 39 ships v35 in the GUIDE because a HUMAN reading the prose can pick the oracle-best A-variant pick within the cell — they aren't bound to the heuristic. The bot-level test conflated two decisions (which cell fires + within-A routing); the human can decouple them via worked examples.
> - **Two-track shipping is now in the methodology toolbox.** When the heuristic is the bottleneck, ship the sharper rule in the human guide and keep the simpler heuristic in production. Production catches up later via ML (Priority C).
> - **Per-cell oracle data unlocks human-friendly rules.** Session 38 mapped (trip_rank, max_kicker_rank); Session 39 translated that map into "if you have an A in your kickers, A goes on top". The data → rule pipeline is replicable for any category with multi-modal optimal-pick structure.
> - **Heuristic-realizable ceilings are still ~5-50% of oracle ceilings (Session 38 finding holds).** v35 captures 63% of the Decision 070 oracle ceiling because (a) the boundary IS most of the gain and (b) the per-cell map is fairly clean.

> Updated: 2026-05-07 (end of Session 39)

---

## Headline state at end of Session 39

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v34_dt** | ML champion (874K leaves, 83 features at depth=34 ml=2) | `analysis/scripts/strategy_v34_dt.py` + `data/v34_dt_model.npz` |
| **v35_rule6_v3** | NEW Session 39 — human strategy of record (Rule 6 sharpened boundary + suit-matching procedure). Used in `STRATEGY_GUIDE.md` Part 6. NOT used at runtime. | `analysis/scripts/strategy_v35_rule6_v3.py` + STRATEGY_GUIDE.md Part 6 |
| v33_rule6_trips | Production runtime Rule 6 path (Session 37 ship; +$112/1000h vs v28). Stays at runtime because v35 heuristic regresses. | `analysis/scripts/strategy_v33_rule6_trips.py` |
| v32_dt | Predecessor ML (731,606 leaves at depth=32 ml=3) | `analysis/scripts/strategy_v32_dt.py` + `data/v32_dt_model.npz` |
| v31_dt | 79 features at depth=32 ml=3 | `analysis/scripts/strategy_v31_dt.py` + `data/v31_dt_model.npz` |
| v30_dt / v29_dt / v27_dt / v26 / v25 / v24 / v23 / v20 / v18e / v16 | Older baselines; retained | `data/v*_dt_model.npz` |
| v34_rule6_v2 | ARCHIVED — Session 38 negative-result candidate (heuristic-bound) | `analysis/scripts/strategy_v34_rule6_v2.py` |
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

**Per-category breakdown (full grid, N=200):** unchanged from Session 38 — v34 ships within-trips $1,291 (5.5% share). The v35 human-strategy ship does not change runtime per-category EVs because production still calls v33.

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
| **v35 oracle-bound (NEW)** | reader picks best-A or best-C within v35 sharper boundary | **$-34.44/1000h** | **+$8.12** |
| Pure oracle | reader picks any A∪C cell freely | $-3.51/1000h | +$39.05 |

**Note:** the "oracle-bound" numbers are negative (and pure oracle is closest to zero) because they're average-EV-relative-to-zero across the trips sample, scaled by population share. The Δ figures are the relevant comparison — v35's Δ +$8.12 is the headline. Pure oracle's +$39.05 is the unrealizable upper bound (would require Decision 070's learned A-vs-C tree at minimum).

---

## What this leaves on the table

- **For human play (oracle-bound):** v35 captures 63% of the Decision 070 oracle ceiling. The remaining 37% (~$4.77/1000h) is in the noisy Trip J + low-kicker cells the user simplified out for memorability. Reframed as Priority C (learned A-vs-C tree).
- **For production runtime:** v33 still misses $86/1000h of Rule 6's full-A∪C oracle ceiling (Decision 068 finding). The v33→v35 boundary sharpening doesn't help at runtime because heuristic-A is the bottleneck (Decision 070 finding). Closing this gap requires a learned A-variant heuristic (Priority C).
- **For ML champion:** v34 captures 44.6% of the v14→ceiling gap at N=200, 71% at N=1000. Biggest residuals at full grid:
  - **high_only**: 20.4% × $2,806 = **$572 share** — largest residual
  - **pair**: 46.6% × $1,619 = **$754 share** — KK/AA single-suited Rule-4-bot is the largest sub-stratum (open)
  - **two_pair**: 22.3% × $978 = **$218 share** — capacity-improved at v34
  - **trips**: 5.46% × $1,291 = **$71 share** — v30, v32, v34 have all shipped; round-3 needs new diagnostic angles
  - three_pair: 1.9% × $1,635 = $31 (untouched by gating)
  - trips_pair: 2.86% × $1,057 = $30 (already gated; v34 capacity expansion)
  - composite: 0.245% × $1,173 = $2.9 (already gated; v34 capacity expansion)

---

## What Session 39 produced

**1. v35_rule6_v3 strategy** (`analysis/scripts/strategy_v35_rule6_v3.py`):
- New boundary helper `_v35_pick_c` encodes the per-trip-rank rule (A always C; K only if no A; Q only if no J/K/A; J or lower never).
- A-variant body inherits v33's (suit_profile, rank_sum, longest_run) bot-DS optimizer for now.
- Smoke tests confirm: diverges from v33 on exactly 4 of 11 named cases, all matching the oracle-cell-level direction.

**2. Verification probe** (`analysis/scripts/verify_rule6_v3_human.py`):
- Same 30K trips sample as Sessions 37–38 (RandomState(0)).
- Reports v33/v35 in BOTH oracle-bound (human ceiling) and heuristic (production bot) modes.
- Per-trip-rank breakdown shows the lift is concentrated in trips 8–J.
- Disagreement subset analysis confirms the boundary delta (1,535/30K = 5.12% of trips, +$2,904/1000h within-trips at the human ceiling).

**3. STRATEGY_GUIDE.md rewrite:**
- Part 6 Rule 6 fully rewritten in plain English (no A/C variant terminology). Two-step structure: (1) per-trip-rank table for top-vs-bot of the third trip card, (2) suit-matching procedure for "which trip joins bot" with three named cases × three named bot shapes. Six worked examples covering all major cases.
- Part 1 Session 39 entry added.
- Part 2 unchanged (production strategies' per-grid scores haven't changed).
- Part 5 split production code path (v33) from human-guide code path (v35), added probe registry.
- Header date bumped to 2026-05-07.

**4. Decision 071** added to DECISIONS_LOG.md codifying the two-track ship + the new methodology rule.

---

## Resume Prompt (Session 40)

```
Resume Session 40 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Session 39 entry in Part 1; Part 2 has v34_dt as
  current ML champion; Part 6 has REWRITTEN Rule 6 with sharper
  boundary table + suit-matching procedure)
- CURRENT_PHASE.md (rewritten end of Session 39)
- DECISIONS_LOG.md (latest: Decision 071 — v35_rule6_v3 ships in
  the human strategy guide; production keeps v33)
- analysis/scripts/strategy_v35_rule6_v3.py — human strategy of record
- analysis/scripts/strategy_v33_rule6_trips.py — production heuristic
- analysis/scripts/verify_rule6_v3_human.py — Session 39 verification probe

State (end of Session 39):
- v35_rule6_v3 ships in STRATEGY_GUIDE.md as the human strategy of record:
  +$8.12/1000h whole-grid at the human ceiling (oracle-bound) vs v33.
  Production runtime stays at v33 because v35 heuristic regresses
  ($-4.06/1000h on flipped cells).
- Methodology rule NEW: human guide can be sharper than production bot
  when heuristic-A is the rate-limiting step.

Next session targets (priority order — UNCHANGED from Session 39 carry-over):

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

(C) Learned A-vs-C decision tree for Rule 6. Reframes Sessions 38–39's
    negative-heuristic results: a small classification tree on
    (trip_rank, max_kicker_rank, kicker suit profile) trained against
    oracle's A-or-C choice. $5-13/1000h ML target. Could finally close
    Rule 6's heuristic-A gap and let production adopt v35.

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
- Methodology rule (Session 39 NEW): the human strategy guide can be
  sharper than the production heuristic when heuristic-A is the
  rate-limiting step. Two-track ship (guide ships, runtime stays).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
