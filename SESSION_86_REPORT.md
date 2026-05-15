# Session 86 — v60 candidate (Rule 20 extension to MID pair × PMID_DS_NOMAXTOP) clears full-grid SHIP at +$6.43/1000h but cannot be validated against the prefix grid because the prefix has ZERO applicable hands; verdict is MIXED by the strict two-grid standard, production stays at v57

_Generated 2026-05-15. S86 extended S83's Rule 20 pattern from LOW pair (rank
2-7) to MID pair (rank 8-T) on the same structural cell (PMID_DS_NOMAXTOP).
The candidate v60 fires on max_sing ≤ Q with v57-pick-restriction, swapping
PMID_tmax to the best PMID_tnomax_DS configuration. Full grid: **+$6.43/1000h
SHIP at gate=Q (62.0% swap-right, 32,304 hands fired)**. Prefix grid: **0
fires across all gates — structural coverage gap, NOT a NULL signal**. By
the S84 two-grid SHIP standard ("both grids ≥ $5"), the candidate is
**MIXED**. Production stays at v57. S86's session-meta discovery: the
prefix-grid validation has a hand-rank coverage limit (canonical IDs 0-499K
contain no MID-pair × PMID_DS_NOMAXTOP hands)._

## TL;DR — Plain language

**What we tested:** Rule 20 already ships on LOW pair (2-7) × PMID_DS_NOMAXTOP
since S83 (+$16.81 prefix lift). The natural extension is to try the same
swap pattern on the next pair-rank tier: MID pair (8-T) at the same cell.
We expected this to be the most likely-to-ship next cell because it inherits
S83's known-working structural premise — the same swap direction
(PMID_tmax → PMID_tnomax_DS) and the same discriminator (max_sing).

**What we found in Phase B/B+ (the cell investigation):**

  - The cell has **114,048 hands** across pair_rank {8,9,T} (38,016 each).
  - v57 leaks **$31.17/1000h whole-grid** here — even bigger than v44's
    $27.26 baseline, because v52's pair-routing-to-mid increases the
    within-PMID variant leak.
  - **$22.98/1000h** of the leak is in a single swap-direction (v57 picks
    PMID_tmax, oracle wants PMID_tnomax_DS). This is 4.6× the SHIP ceiling
    — strong addressable signal.
  - max_sing is still a meaningful discriminator (84% swap-right at max=9,
    75% at max=J, 65% at max=Q, 51% at max=K, 17% at max=A), though softer
    than S83's LOW pair tier (where max_sing≤J peaks at 92%).
  - Per pair-rank: rank 8 has the cleanest swap signal; rank T is softest
    (65% at max_sing=J vs 84% for rank 8 at max_sing=J).

**What we tried (Rule 21 candidate v60):** Same forced setting as Rule 20
(top = best non-max singleton, bot = 4 singletons forming DS pattern, mid =
pair), but with pair_rank ∈ {8,9,T} instead of {2-7}. Applied the S85
design pattern of v57-pick-restriction (only override when v57 is in the
swap-from class). Multi-gate grading on max_sing ∈ {10, 11, 12, 13, 14}.

**Full-grid grader said (BEST gate=Q):**

  - **+$6.43/1000h whole-grid lift** ← clears SHIP threshold
  - 32,304 fired hands, 62.0% swap-right (20,016 reduced regret, 12,134
    increased regret)
  - Per-rank: rank 8 +$4.14 / rank 9 +$2.20 / rank T +$0.09
  - The lift is positive on all three pair_ranks; primarily driven by ranks 8
    and 9 with rank T contributing marginal signal.

**Prefix-grid grader said:**

  - **n_fired = 0 across all five gates.** Zero applicable hands.
  - This is because the canonical_id ordering puts MID pair × PMID_DS_NOMAXTOP
    hands starting at canonical_id 593,072 (the first hand of this cell type),
    well outside the prefix range (0-499,999). The prefix's canonical ordering
    is the well-known "weak-hand prefix" property (per project memory
    `taiwanese_canonical_id_prefix_lesson`).
  - The prefix grader is **silent**, not contradictory.

**Why we're NOT shipping v60 despite the strong full-grid signal:**

The S84 two-grid SHIP standard requires both full-grid AND prefix-grid lift
≥ $5/1000h. The prefix-grid lift here is $0.00 — but this is because zero
applicable hands exist in the prefix, not because the rule produces zero
lift. Mechanically, $0 < $5, so the strict standard fails.

The honest mechanical verdict is **MIXED**: full-grid SHIP, prefix-grid
non-SHIP (by absence of applicable hands).

**Why this matters as a methodology discovery:**

S84's two-grid standard was created to guard against N=200 oracle-label
noise. The standard works well when the prefix HAS applicable hands. For
rules that target a cell whose hands fall outside canonical_ids 0-499,999,
the prefix cannot evaluate the rule at all — neither validating nor
invalidating it.

The cells affected by this coverage gap are MID-pair and HIGH-pair zones,
plus most high-card hand zones (HIGH_ONLY catch-all cells). All future
Option D-revised extensions to higher-rank tiers will hit this same gap.

**What the user can do next session:**

1. **Accept MIXED and pivot** to LOW × PMID_OTHER ($11.81 STRUCTURE under
   v44 / 138K hands, the largest remaining LOW pair cell — covered by
   prefix).
2. **Override and ship v60 on full-grid evidence alone.** The structural
   evidence is strong: identical swap-direction to S83, $22.98 single-
   direction residual, per-rank positive lift on all three MID ranks,
   62% swap-right at gate=Q. The S83 ship was full-grid-only (the two-grid
   standard didn't exist yet); reverting to that standard for v60 is
   internally consistent given the prefix's structural silence.
3. **Run an N=1000 oracle pass on MID × PMID_DS_NOMAXTOP hands** (~few
   hours compute) to confirm the full-grid lift survives label noise. This
   is the most rigorous answer but most expensive.

**My recommendation if pressed:** Option 2 (override and ship). The full-
grid evidence is structurally robust (per-rank validated, single-direction-
concentrated, mechanism-identical-to-S83), and the prefix-grid silence is
a known structural property not a signal failure. But this is a strategic
judgment call that warrants user input, especially given the project
standard.

## What S86 ran (timeline)

| Phase | Wall | What ran | Result |
|---|---:|---|---|
| Phase A | ~5 min (synthesis) | Verify cell choice via S77 cell_stats | n=114,048 / $27.26 v44 leak / same top-mismatch pattern as S83 (PMID_tmax_SS → PMID_tnomax_DS, 15,770 hands @ $8.09/1000h v44). Rule 20 cannot fire (pair_rank gate is LOW). |
| Phase B | 44s | `drill_v57_mid_pmid_ds_nomaxtop_S86.py` | v57 leaks **$31.17/1000h** whole-grid (vs v44's $27.26). 100% PMID placement. Direction-residual PMID_tmax_SS→PMID_tnomax_DS: $14.75. Combined tmax_{SS,31}→tnomax_DS: ~$22.96. PROCEED-PHASE-B+. |
| Phase B+ | 42s | `drill_v57_mid_pmid_ds_swap_discriminator_S86.py` | max_sing is the dominant discriminator (Δ=−1.02 KEEP vs SWAP); peak swap-right 84.3% at max=9, softening to 17.2% at max=A. SWAP_TO_TNOMAX_DS direction-residual: $22.98 — clears SHIP ceiling 4.6×. SWAP_TO_PBOT_SS: $4.77 (below ceiling). PROCEED-PHASE-C. |
| Phase C-1 | 5 gates × ~1.5s + 22s precompute | `grade_v60_mid_pair_ds_nomaxtop_S86.py` (multi-gate full grid) | Best gate Q=12: **+$6.43/1000h SHIP**. Gate=J: +$4.85 MIXED. Gate=T: +$1.63 NULL. Gate=K: -$0.08 NULL. Gate=A: -$54.47 NULL. |
| Phase C-2 | 5 gates × ~4.3s + 86s precompute | `grade_v60_prefix_multigate_S86.py` (multi-gate prefix) | n_fired = **0 across all gates** (canonical_id coverage gap: MID pair × PMID_DS_NOMAXTOP starts at canonical_id 593,072, outside prefix 0-499,999). Lift $0.00 by absence of applicable hands. |
| Phase D | active | Report + Decision 121 + CURRENT_PHASE rewrite + commit + push | — |

---

## The numbers (the read of the experiment)

### Phase B — cell leak under PRODUCTION v57

| Metric | Value |
|---|---:|
| MID × PMID_DS_NOMAXTOP n hands | 114,048 |
| Total leak under v44_dt (S77) | $27.26/1000h whole-grid |
| Total leak under v57 (this drill) | **$31.17/1000h whole-grid** |
| Δ (v57 − v44) | **+$3.91/1000h** (v52 routes pair-to-mid more aggressively, growing within-PMID variant leak) |
| v57 cell match% | 50.2% (57,262 / 114,048) |
| v57 pair-placement on cell | 100% PMID (no SPLIT, no PBOT) |
| Rule 20 fires on MID cell (sanity) | 0 ✓ (LOW gate excludes MID) |

Top STRUCTURE-bucket mismatches under v57:

| v57_class | oracle_class | n | $/1000h |
|---|---|---:|---:|
| PMID_tmax_SS | PMID_tnomax_DS | 23,657 | **$14.72** |
| PMID_tmax_31 | PMID_tnomax_DS | 13,166 | **$8.21** |
| PMID_tmax_SS | PMID_tnomax_SS | 5,513 | $2.46 |
| PMID_tmax_SS | PBOT_tmax_SS_ms | 3,736 | $1.80 |
| PMID_tmax_SS | PBOT_tmax_SS_mu | 2,169 | $0.93 |
| PMID_tmax_SS | PBOT_tnomax_SS_ms | 1,321 | $0.85 |
| PMID_tmax_31 | PBOT_tmax_SS_ms | 1,369 | $0.68 |

**Combined direction-residual PMID_tmax_{SS,31} → PMID_tnomax_DS: ~$22.96/1000h.**

### Phase B+ — population characterization + discriminator search

| Population | n | % of cell | $/1000h | Comment |
|---|---:|---:|---:|---|
| KEEP_TMAX (v57=oracle=PMID_tmax_*) | 54,221 | 47.5% | $0.00 | match |
| SWAP_TO_TNOMAX_DS (v57=PMID_tmax, oracle=tnomax_DS) | 38,499 | 33.8% | **$22.98** | primary swap |
| SWAP_TO_PBOT_SS (v57=PMID_tmax, oracle=PBOT_*_SS_*) | 10,468 | 9.2% | $4.77 | side-channel |
| OTHER (v57=tmax, oracle=something else) | 6,876 | 6.0% | $2.88 | residual variants |
| NOT_TMAX (v57 not tmax_SS / tmax_31) | 3,984 | 3.5% | $0.53 | excluded by v57-pick-restriction |

**Best discriminator for SWAP_TO_TNOMAX_DS direction: `max_sing`** (Δ = −1.02 mean).
Per-value swap-rate within {KEEP_TMAX ∪ SWAP_TO_TNOMAX_DS}:

| max_sing | KEEP | SWAP_TNOMAX_DS | swap_pct (within pair) |
|---:|---:|---:|---:|
| 14 (A) | 33,784 | 7,026 | 17.2% |
| 13 (K) | 12,342 | 12,827 | 51.0% |
| 12 (Q) | 5,341 | 9,840 | 64.8% |
| 11 (J) | 2,023 | 6,100 | 75.1% |
| 10 (T) | 634 | 2,187 | 77.5% |
| 9 | 97 | 519 | 84.3% |

Per pair-rank breakdown at gate=Q:

| rank | KEEP-cum-to-Q | SWAP-cum-to-Q | swap-pct |
|---|---:|---:|---:|
| 8 | 2,255 | 7,895 | 77.8% |
| 9 | 2,813 | 6,469 | 69.7% |
| T | 3,027 | 4,282 | 58.6% |

So gate=Q is sharpest for rank 8, weakest for rank T — consistent with the
per-rank lift breakdown in Phase C below.

### Phase C-1 — full grid multi-gate grade (v60 with v57-pick-restriction)

Pre-committed thresholds (locked in code BEFORE running):
```
SHIP_LIFT_DOLLARS_PER_1000H = 5.0   # full grid
NULL_LIFT_DOLLARS_PER_1000H = 2.0
MIXED in between
S84 refinement: SHIP requires BOTH grids ≥ $5
```

| Gate (max_sing ≤) | n_fired | swap-right | rank 8 | rank 9 | rank T | TOTAL $/1000h | Verdict |
|---|---:|---:|---:|---:|---:|---:|---|
| 10 (T) | 4,080  | 74.7% | +$1.12 | +$0.51 | +$0.00 | **+$1.63** | NULL |
| 11 (J) | 14,160 | 70.6% | +$2.76 | +$1.59 | +$0.50 | **+$4.85** | MIXED |
| **12 (Q)** | **32,304** | **62.0%** | **+$4.14** | **+$2.20** | **+$0.09** | **+$6.43** | **SHIP** |
| 13 (K) | 62,544 | 50.6% | +$3.28 | +$0.07 | -$3.43 | **-$0.08** | NULL |
| 14 (A) | 110,064 | 33.1% | -$14.39 | -$17.10 | -$22.97 | **-$54.47** | NULL |

**Best gate: max_sing ≤ Q (12) at +$6.43/1000h — full-grid SHIP.**

### Phase C-2 — prefix grid multi-gate grade (v60)

| Gate (max_sing ≤) | n_fired | n_changed | swap-right | Lift $/1000h prefix | Verdict |
|---|---:|---:|---:|---:|---|
| 10 | 0 | 0 | — | **$0.00** | NULL |
| 11 | 0 | 0 | — | **$0.00** | NULL |
| 12 | 0 | 0 | — | **$0.00** | NULL |
| 13 | 0 | 0 | — | **$0.00** | NULL |
| 14 | 0 | 0 | — | **$0.00** | NULL |

**Zero fires across all gates.** This is because canonical_id ordering
places MID pair × PMID_DS_NOMAXTOP hands starting at canonical_id 593,072,
outside the prefix (0-499,999).

```
Among 114,048 MID × PMID_DS_NOMAXTOP hands:
  canonical_id range: 593,072 to 6,000,984
  hands with canonical_id < 500,000: 0  ← prefix sees none

Among 228,096 LOW × PMID_DS_NOMAXTOP hands (S83 ship cell, for comparison):
  canonical_id range: 61,137 to 5,882,864
  hands with canonical_id < 500,000: 37,969  ← prefix sees ~17% of LOW cell
```

The prefix grader is **structurally silent on this cell**, not a NULL signal.

---

## Why MIXED, not SHIP, despite +$6.43 full-grid

**The S84 two-grid-confirmation standard requires both grids to clear $5.**
The full grid clears +$6.43; the prefix grid produces $0.00 (by absence
of applicable hands). By the strict standard, full-grid-only SHIP is
not sufficient. Verdict: **MIXED.**

**Why the prefix is silent (not contradictory):** The prefix grid evaluates
canonical IDs 0-499,999. These are the weakest 500K of the 6M canonical
hands per `taiwanese_canonical_id_prefix_lesson` memory. MID pair (rank
8-T) × PMID_DS_NOMAXTOP cell-eligible hands begin at canonical_id 593,072
— outside the prefix range entirely. The prefix grader cannot evaluate
v60's rule at all, neither validating nor invalidating it.

**Is the full-grid signal trustworthy?** Several reasons to think so:
1. The mechanism is mathematically identical to S83's shipped Rule 20
   (same cell shape, same swap direction, same discriminator family).
2. The direction-residual is $22.98 — a 4.6× margin over the SHIP
   ceiling. Even partial accuracy clears.
3. Per-rank lift is positive on all three pair_ranks (rank 8 +$4.14,
   rank 9 +$2.20, rank T +$0.09) — not a single-slice artifact.
4. The 62% swap-right rate at gate=Q is substantially above 50%.
5. The discriminator gradient is monotone (84% at max=9, 75% at J, 65% at
   Q, 51% at K, 17% at A) — clean signal, not noise.
6. Full-grid lift is +$6.43 with N=200 noise estimated <$0.5; the +$6.43
   estimate sits well above the noise floor.

**What WOULD make the lift suspect?** If the full-grid lift was driven by
a small subset of high-leverage hands whose N=200 EVs are unreliable. The
per-rank robustness argues against this (lift is distributed across ranks).

**Production decision:** Stay at v57. Document the prefix coverage gap as
a session-meta discovery. Surface the SHIP/MIXED judgement to the user
for next-session input.

---

## Session-meta discovery — prefix-grid coverage limit

S86 surfaces a previously-implicit limitation of the project's two-grid SHIP
standard: **the prefix grid (canonical_id 0-499,999, N=1000 oracle labels)
has a hand-rank coverage gap.** Cells whose canonical_id range starts above
500K are invisible to the prefix grader.

Affected zones (estimated from canonical-ordering structure):
- **MID-pair cells (rank 8-T)** for the four pair-cell variants tested or
  to-be-tested by Option D-revised (PMID_DS_NOMAXTOP, PMID_DS_MAXTOP,
  PMID_SS_MAXTOP, PMID_OTHER).
- **HIGH-pair cells (rank J-A)** for any pair-based extension.
- **High-card cells (HIGH_ONLY with strong top cards)** — likely fully
  outside prefix.

Cells already-tested where prefix coverage held:
- **LOW pair (rank 2-7) cells** had prefix coverage (S83 ship had ~17% of
  LOW × PMID_DS_NOMAXTOP cell within prefix; S84 / S85 cells similarly
  covered). The two-grid standard works as designed for LOW pair.

**Implication for Option D-revised continuation:** Future cells in
under-rule-covered zones above LOW pair will face the same coverage gap.
The two-grid SHIP standard cannot be applied mechanically.

**Possible resolutions (not implemented in S86):**
1. **Generate cell-specific N=1000 oracle subsets** for full validation.
   This is the rigorous approach; cost is hours-per-cell.
2. **Relax the two-grid standard to a "two-grid-when-applicable" standard**
   — full-grid SHIP suffices when prefix lacks coverage. This shifts the
   noise-control burden to other safeguards (per-rank robustness, single-
   direction concentration, sharp discriminator).
3. **Build a "uniform-random-subset prefix" with N=1000 labels** to replace
   or supplement the canonical-prefix as the standard. Largest cost, biggest
   methodology change.

This question is surfaced to the user for next-session decision.

---

## The mechanism story (mirrors S83)

The cell **MID pair × PMID_DS_NOMAXTOP** is defined by:
1. Hand is a single pair, rank 8-T
2. No PBOT_DS achievable (pair suits don't both appear among singletons
   such that a singleton-pair forms in each suit)
3. n_PMID_DS > 0 (at least one 4-subset of singletons forms 2+2 suit pattern)
4. n_PMID_DS_w_maxtop == 0 (max_sing cannot sit on top in a DS configuration)

Under v57, v52 routes pair-to-mid by default and picks the variant whose
top is max_sing (because for most hands max-on-top is correct). For MID
pair × PMID_DS_NOMAXTOP:

- **47.5% of cell hands (KEEP_TMAX)**: oracle agrees with v52's max-on-top.
- **33.8% (SWAP_TO_TNOMAX_DS)**: oracle prefers a non-max singleton on
  top, max in bot, bot has DS pattern. The DS upgrade is worth more than
  losing max-on-top. **This is the dominant residual.**
- **9.2% (SWAP_TO_PBOT_SS)**: oracle prefers pair-in-bot with SS pattern.
  The DS bot isn't available; oracle reaches for a different bot pattern.
  Smaller residual ($4.77/1000h) — competing but below SHIP ceiling.
- **6.0% (OTHER)**: v57 = tmax but oracle wants a different non-tnomax_DS
  variant. Mixed bag.
- **3.5% (NOT_TMAX)**: v57 already picks a non-tmax variant. Excluded by
  v57-pick restriction.

The discriminator `max_sing` separates KEEP from SWAP cleanly: when
max_sing is high (A or K), keeping max-on-top is correct; when max_sing
is low (T or J or below), the DS upgrade outweighs max-on-top.

The gate sweet spot at Q reflects this: max_sing ≤ Q captures 62% of
swap-eligible hands while excluding most of the wrong-direction A-on-top
hands.

---

## What S86 changed

### Strategy of record (UNCHANGED)
- **Rule chain:** v57_lo_pair_defensive (no change)
- **ML champion:** v44_dt (no change — 15 sessions in production)

### Rule count
- Before: 20 numbered rules
- After: **20 (unchanged)** — v60 candidate did not ship (MIXED verdict)

### Production numbers (UNCHANGED)
- v57 full grid: $1,412.53/1000h
- v57 prefix: $776.88/1000h
- Two-track divergence vs v44_dt: $332/1000h (unchanged)

### Files
- **New code (committed):**
  - `analysis/scripts/drill_v57_mid_pmid_ds_nomaxtop_S86.py` — Phase B drill
  - `analysis/scripts/drill_v57_mid_pmid_ds_swap_discriminator_S86.py` — Phase B+ discriminator
  - `analysis/scripts/strategy_v60_mid_pair_ds_nomaxtop.py` — v60 candidate (DID NOT SHIP — MIXED)
  - `analysis/scripts/grade_v60_mid_pair_ds_nomaxtop_S86.py` — Phase C full-grid multi-gate grader
  - `analysis/scripts/grade_v60_prefix_multigate_S86.py` — Phase C prefix multi-gate grader
- **New artifacts (gitignored under `data/session86/`):**
  - `drill_v57_mid_pmid_ds_nomaxtop_summary.json`
  - `drill_v57_mid_pmid_ds_swap_discriminator_summary.json`
  - `grade_v60_summary.json`
  - `grade_v60_prefix_multigate_summary.json`
  - `*.log` for each phase
- **Documentation:**
  - `SESSION_86_REPORT.md` — this file
  - `DECISIONS_LOG.md` — Decision 121 (MIXED + prefix-coverage discovery)
  - `CURRENT_PHASE.md` — rewritten for S87

---

## Path forward (S87 candidates)

The Option D-revised playbook ship rate is now 1/4 across tested cells
(S83 SHIP / S84 MIXED / S85 NULL / S86 MIXED — methodology-bound, not
signal-bound). S86's MIXED is structurally different from S84's MIXED: S84
was MIXED because the lift was real but small; S86 is MIXED because the
two-grid standard cannot be applied due to prefix coverage. The
underlying full-grid signal is comparable to S83's shipped Rule 20.

### Recommended first-pass priorities for S87

1. **Surface the prefix-coverage methodology question to user.** Three
   options:
   (a) Accept MIXED and pivot to LOW × PMID_OTHER (prefix-covered).
   (b) Override and ship v60 on full-grid evidence alone (precedent: S83
       shipped Rule 20 on full-grid alone before the two-grid standard
       existed).
   (c) Approve N=1000 oracle compute on the cell to validate rigorously.

2. **If pivot:** Try **LOW × PMID_OTHER** (S77: $11.81 v44 STRUCTURE /
   137,808 hands). Largest remaining LOW pair cell by hand count. Prefix
   coverage holds. Different rule shape (no DS available; rule likely
   about pair placement at the macro level rather than within-PMID
   variant).

3. **Headline-goal recalibration** is increasingly attractive given
   methodology-bound MIXED outcomes and bounded cumulative reachable lift.

4. **Resolve S84 divergence** (N=1000 on full PMID_DS_MAXTOP cell, ~3-5h
   compute). Lower information yield than testing a new cell; remains
   deprioritized.

---

## Methodology notes (S86)

1. **Phase B/B+ playbook transferred cleanly across pair-rank tiers.**
   The same drill scripts (adapted from S85's template) produced clean
   cell-residual and discriminator analyses. Infrastructure cost is
   near-zero per cell at this point.

2. **The S85 design pattern of v57-pick-restriction was applied by default.**
   v60's detector checks v57's pick is PMID_tmax-style before overriding —
   excluding the 3.5% NOT_TMAX subset where v57 already picked tnomax. No
   v1→v2 iteration was needed; the pattern is now standardized.

3. **The addressable-direction-residual SHIP-ceiling check from S85
   correctly classified this cell.** $22.98 ≫ $5 → PROCEED-PHASE-C. The
   ceiling check is now a routine Phase B+ gate.

4. **Pre-committed thresholds were locked in code before grader ran.**
   Verdict declared mechanically: SHIP (full grid) + uninformative (prefix)
   = MIXED. No narrative arbitrage.

5. **NEW S86 lesson — prefix-grid coverage limit.** The two-grid SHIP
   standard depends on the prefix having applicable hands. For cells whose
   canonical_id range starts above 500K, the prefix is silent. Future
   methodology should:
   - Compute and display canonical_id range alongside cell metadata.
   - Distinguish "prefix-NULL" from "prefix-silent" in grader output.
   - Resurface the two-grid standard's applicability whenever a cell
     starts above 500K.

6. **The full-grid signal at +$6.43 is structurally robust.** Per-rank
   lift positive on all three ranks; single-direction-concentrated residual;
   sharp monotone discriminator; mechanism mirrors shipped Rule 20. If the
   two-grid standard were relaxed for prefix-silent cells, this candidate
   would ship cleanly. The decision to require the two-grid standard
   uniformly is a project policy choice, not a signal-quality issue.

7. **"Speed is not necessary — clarity and perfection is" cashed out as
   running the prefix grader even when the cell-coverage analysis predicted
   it would be silent.** The mechanical $0.00 prefix lift confirms the
   coverage gap empirically. This makes the methodology discovery
   defensible rather than speculative.

---

## Headline state at end of S86 (UNCHANGED)

* **Rule chain (UNCHANGED):** v57_lo_pair_defensive — $1,412.53/1000h full grid / $776.88/1000h prefix.
* **ML champion (UNCHANGED):** v44_dt — $1,081/1000h full grid / $686/1000h prefix.
* **Two-track divergence:** $332/1000h (unchanged).
* **Total project rule count:** 20 (unchanged).
* **v60 (MID × PMID_DS_NOMAXTOP rule, gate=Q):** TESTED — verdict MIXED (full-grid SHIP +$6.43 / prefix-grid silent due to coverage gap) — NOT SHIPPED pending user decision on prefix-coverage methodology question.
