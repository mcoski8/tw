# Session 85 — v59 candidate NULL on LOW × PMID_SS_MAXTOP; second consecutive cell where Option D-revised playbook generates a clean candidate but the candidate does not ship

_Generated 2026-05-15. S83's Option D-revised playbook extended to the third
under-rule-covered LOW pair cell (PMID_SS_MAXTOP). The candidate rule
(force PMID_tnomax_best when max_sing ≤ gate and v57 picked PMID_tmax_SS)
auto-fires NULL on both the full grid and the prefix grid across all six
gates. No two-grid disagreement; the verdict is unambiguous. **Production
stays at v57. Rule count stays at 20. Two-track divergence unchanged.**_

## TL;DR — Plain language

**What we tested:** The third in our series of "extend Rule 20 to the next
under-covered LOW pair cell" tries. S77 ranks the under-covered cells by
pre-production leak; we already shipped Rule 20 on cell #1 (PMID_DS_NOMAXTOP,
S83), MIXED on cell #2 (PMID_DS_MAXTOP, S84), and this session tried cell
#3: PMID_SS_MAXTOP (85,536 hands, $9.71/1000h whole-grid STRUCTURE leak under
v44_dt).

**What we found about the cell:** Under PRODUCTION v57 this cell has
$15.33/1000h residual leak — *much more than we expected*. The previous cell
(PMID_DS_MAXTOP) only had $7.24 residual; v52's pair-routing had closed 78%
of v44's leak. Here v52 closes only 39%, leaving $15.33 — a bigger pie than
v44's S77-headline $9.71 STRUCTURE alone suggested (the full v44 cell leak
was $25.16; the structure subset is the easier-to-extract slice). That was a
positive surprise.

**But the residual is fragmented across three different swap-directions:**
  - $6.98/1000h would want pair-in-bot (PBOT_SS variants) — 17.5% of cell
  - $4.36/1000h would want different non-max top (PMID_tnomax variants) — 13.1% of cell
  - $3.99/1000h is in OTHER (v57 already picks a non-tmax_SS config, oracle differs) — 15.2% of cell

No single direction holds enough leak to clear $5 SHIP with realistic
selectivity. The cell is *correct* about being under-rule-covered, but the
residual is structurally diverse.

**What we tried (Rule 21 candidate v59):** Target the tnomax direction
because `max_sing` is the cleanest discriminator (peak swap-right 65.9% at
max_sing ≤ 11, vs S83's Rule 20 max_sing peak of 92.8% at max_sing ≤ J — much
softer here). Rule: when LOW pair × PMID_SS_MAXTOP × max_sing ≤ gate × v57
currently picks PMID_tmax_SS, force the best PMID_tnomax (highest
bot_pair_high, ties broken by top-rank then suit-pattern).

**What the graders said:** The pre-committed multi-gate graders fired.
**Both grids agree on NULL across all gates.** No divergence story this time.

  - **Full grid (N=200 labels):** Best gate (max_sing ≤ 9) lift: -$0.09/1000h
    whole-grid. NULL threshold is $2. Best swap-right rate: 27.5%. All other
    gates progressively worse.
  - **Prefix grid (N=1000 labels):** Gates 9-11 fire 0 times (prefix's first
    500K canonical hands skew toward weak hands and contain few qualifying
    cell hands at low max_sing). Gates 12-14 fire on 2K-12K hands with large
    NEGATIVE lift (-$12.81 to -$131.27/1000h prefix). Best gate: 9 at $0.00
    (no fires). NULL by absence of signal.

**Why both grids fire NULL together (no divergence):**

1. The cell's structure-bucket residual ($9.71 v44 / part of $15.33 v57) is
   *distributed across direction-conflicting populations*. Targeting the
   tnomax direction means firing on hands the rule helps (SWAP_TO_PMID_TNOMAX,
   $4.36 potential) but also on hands the rule hurts (KEEP_PMID_TMAX +
   SWAP_TO_PBOT_SS). The hurt populations are bigger than the help, even at
   the most-selective gate.

2. The `max_sing` discriminator was measured at 65.9% swap-right within the
   isolated population of {KEEP_PMID_TMAX ∪ SWAP_TO_PMID_TNOMAX}, but the
   real rule fires on a broader population that includes SWAP_TO_PBOT_SS
   (where oracle prefers PBOT, not tnomax). Within the broader population,
   the swap-right rate falls to 27%.

3. The "best PMID_tnomax" heuristic in v59 also doesn't perfectly match
   oracle preferences (oracle prefers PMID_tnomax_31 60% / PMID_tnomax_SS 40%
   on SWAP hands; v59 prefers SS on bot_pair_high ties). Even when the rule
   correctly fires on a swap-eligible hand, the chosen variant may be wrong.

**Why we're NOT shipping v59:** Both grids agree NULL. Full-grid lift is
literally $-0.09 (negative) at best — there is no signal to chase. Even an
idealized rule with 100% accuracy on SWAP_TO_PMID_TNOMAX would yield at most
$4.36/1000h — below the $5 SHIP threshold. The cell's structural composition
makes a single-direction rule structurally unable to ship.

**What this tells us about Option D-revised continuation:** Of 3 cells now
tested:
  - Cell #1 (PMID_DS_NOMAXTOP, S83): **SHIPPED** — sharp discriminator (max_sing,
    92.8% peak), large residual leak ($59.42/1000h whole-grid under v56), single
    dominant swap direction (PMID_tmax_SS → PMID_tnomax_DS).
  - Cell #2 (PMID_DS_MAXTOP, S84): **MIXED** — soft discriminator (top_alt_rank,
    67% peak), small residual ($7.24/1000h), bidirectional within-PMID-DS swap.
  - Cell #3 (PMID_SS_MAXTOP, S85): **NULL** — moderate residual ($15.33/1000h)
    but split across 3 competing directions (PBOT, tnomax, OTHER). No single
    direction large enough to clear SHIP.

**Pattern:** S83's success required (sharp discriminator) × (large residual)
× (single dominant direction). Cells missing any of these tend to MIXED or NULL.

**The methodology held up.** The pre-committed-verdict pattern produced an
unambiguous NULL on both grids — no narrative gap to exploit. The v1 → v2
iteration within Phase C (adding the v57-pick restriction) demonstrates the
pattern's value: v1's rule had a structural bug (overrode v57 on populations
where v57 was already correct), and the grader exposed it bluntly (best
full-grid lift -$1.51). The fix narrowed scope but the cell still fails
ceiling; the verdict is robust to rule-design quality.

**What's still alive on Option D-revised:**
  - **LOW × PMID_OTHER** ($11.81 v44 STRUCTURE / 137,808 hands, catchall —
    likely similar issue: structurally diverse residual, may need feature-
    intersection rule rather than single feature).
  - **MID pair (8-T) × PMID_DS_NOMAXTOP** — extend Rule 20 to higher pair tier;
    may transfer if Rule 20's pattern holds for mid pairs (likely the cleanest
    remaining option).
  - **HIGH_ONLY × J-high and below** ($14.47 + $4.31 STRUCTURE under v44) —
    different category but similar archetype; defensive routing already in v52
    for max ≤ T.
  - **Resolve S84 divergence** by running N=1000 labels on the full 128k PMID_DS_MAXTOP
    cell (~3-5h compute). Lower information yield than testing a new cell;
    deprioritized.
  - **Headline-goal recalibration** — still on the table. With S83 SHIP + S84
    MIXED + S85 NULL, we're at 1/3 ship rate on tested cells. If the remaining
    cells continue at this rate, the cumulative under-covered-cell ceiling is
    smaller than the gap to a 95% match% goal would require.

## What S85 ran (timeline)

| Phase | Wall | What ran | Result |
|---|---:|---|---|
| Phase A | ~5 min (synthesis) | Verified cell choice via S77 cell_stats | n=85,536 / $25.16 v44 total / $9.71 STRUCTURE / Rule 20 cannot fire (by construction). |
| Phase B | 34s | `drill_v57_low_pmid_ss_maxtop_S85.py` | v57 leaks **$15.33/1000h** whole-grid (vs v44's $25.16); 100% PMID placement; dominant residual is PMID→PBOT_SS swaps ($5.63 combined) + within-PMID variant swaps ($4.34). PASSED early-out ceiling check ($5). |
| Phase B+ | 35s | `drill_v57_pmid_ss_swap_discriminator_S85.py` | Best discriminator for SWAP_TO_PMID_TNOMAX: `max_sing` (Δ = −1.09), peak swap-right 65.9% at max_sing ≤ 11. Best for SWAP_TO_PBOT_SS: `best_pbot_ss_bph_tmax_ms` (Δ = +0.83), peak 45.9%. Both substantially softer than S83's 92.8%. |
| Phase C-1a | 6×1s | `grade_v59_lo_pair_ss_tnomax_S85.py` (v1, full grid) | All 6 gates NULL. Best gate=9: -$1.51/1000h. 12% swap-right (rule fires on OTHER & PBOT populations and overrides v57's correct picks). |
| Phase C-1b (revision) | — | strategy_v59 → v2 (restrict to v57-picks-PMID_tmax_SS) | Re-graded full grid. |
| Phase C-1c | 6×1s | re-run full grid with v59_v2 | All 6 gates NULL. Best gate=9: -$0.09/1000h. 27.5% swap-right. |
| Phase C-2 | 6×5s + 89s precompute | `grade_v59_prefix_multigate_S85.py` (v2, prefix) | All 6 gates NULL. Gates 9-11 fire 0 times. Gates 12-14 fire with progressively negative lift (-$12.81 / -$41.36 / -$131.27/1000h prefix). |
| Phase D | active | Report + Decision 120 + CURRENT_PHASE rewrite + commit + push | — |

---

## The numbers (the read of the experiment)

### Phase B — cell leak under PRODUCTION v57

| Metric | Value |
|---|---:|
| LOW × PMID_SS_MAXTOP n hands | 85,536 |
| Total leak under v44_dt (S77) | $25.16/1000h whole-grid |
| Total leak under v57 (this drill) | **$15.33/1000h whole-grid** |
| Δ (v57 − v44) | **−$9.83/1000h** (v52 closes 39% of v44's leak) |
| v57 cell match% | 59.4% (50,801 / 85,536) |
| v57 pair-placement on cell | 100% PMID (no SPLIT, no PBOT) |
| Rule 20 fires on cell (sanity) | 0 ✓ (cell precondition n_PMID_DS == 0) |

Top STRUCTURE-bucket mismatches under v57:

| v57_class | oracle_class | n | $/1000h |
|---|---|---:|---:|
| PMID_tmax_SS | PBOT_tmax_SS_mu | 6,508 | $2.84 |
| PMID_tmax_SS | PBOT_tmax_SS_ms | 5,566 | $2.79 |
| PMID_tmax_SS | PMID_tnomax_31 | 6,295 | $2.64 |
| PMID_tmax_SS | PMID_tnomax_SS | 4,130 | $1.70 |
| PMID_tmax_SS | PBOT_tnomax_SS_ms | 2,044 | $1.22 |
| PMID_tnomax_31 | PBOT_tnomax_SS_ms | 821 | $0.50 |
| PMID_tnomax_SS | PMID_tmax_SS | 941 | $0.49 |

**Cell ceilings by direction:** PBOT-route $6.85 (combined PMID→PBOT_SS swaps).
Within-PMID variant $4.34. Other $4.14. Total ceiling: ~$15.33.

### Phase B+ — population characterization + discriminator search

| Population | n | % of cell | $/1000h | Comment |
|---|---:|---:|---:|---|
| KEEP_PMID_TMAX (v57=oracle=PMID_tmax_SS) | 46,280 | 54.1% | $0.00 | match |
| SWAP_TO_PBOT_SS (v57=PMID_tmax_SS, oracle wants PBOT_*_SS_*) | 14,994 | 17.5% | $6.98 | swap |
| SWAP_TO_PMID_TNOMAX (v57=PMID_tmax_SS, oracle wants PMID_tnomax_*) | 11,227 | 13.1% | $4.36 | swap |
| OTHER (v57 != PMID_tmax_SS) | 13,035 | 15.2% | $3.99 | v57 disagrees with oracle on tnomax variant |

PBOT sub-distribution (oracle classes within SWAP_TO_PBOT_SS):
  - PBOT_tmax_SS_mu: 6,852
  - PBOT_tmax_SS_ms: 5,810
  - PBOT_tnomax_SS_ms: 2,130
  - PBOT_tnomax_SS_mu: 202

PMID_tnomax sub-distribution (oracle classes within SWAP_TO_PMID_TNOMAX):
  - PMID_tnomax_31: 6,754 (60%)
  - PMID_tnomax_SS: 4,473 (40%)

**Best discriminator for SWAP_TO_PMID_TNOMAX direction: `max_sing`** (Δ = -1.09).
Per-value swap-rate within {KEEP_PMID_TMAX ∪ SWAP_TO_PMID_TNOMAX}:

| max_sing | KEEP_TMAX | SWAP_TNOMAX | swap_pct (within pair) |
|---:|---:|---:|---:|
| 14 (A) | 26,482 | 757 | 2.8% |
| 13 (K) | 13,580 | 4,104 | 23.2% |
| 12 (Q) | 5,644 | 5,197 | 47.9% |
| 11 (J) | 331 | 664 | 66.7% |
| 10 (T) | 146 | 323 | 68.9% |
| 9 | 70 | 135 | 65.9% |
| 8 | 27 | 47 | 63.5% |

**Best discriminator for SWAP_TO_PBOT_SS direction: `best_pbot_ss_bph_tmax_ms`**
(Δ = +0.83), peak 45.9% swap-rate at val=5 — much softer.

### Phase C-1 — full grid multi-gate grade (v59_v2)

Pre-committed thresholds (locked in code BEFORE running):
```
SHIP_LIFT_DOLLARS_PER_1000H = 5.0   # full grid (project convention)
NULL_LIFT_DOLLARS_PER_1000H = 2.0   # below this = no signal
MIXED in between
```

| Gate (max_sing ≤) | n_fired | n_changed | swap-right | Δ EV | Lift $/1000h whole-grid | Verdict |
|---|---:|---:|---:|---:|---:|---|
| 9  |   360  |   360  | 27.5% |   −56.98  | **−$0.09** | NULL |
| 10 |   990  |   990  | 29.0% |  −144.37  | **−$0.24** | NULL |
| 11 | 2,250  | 2,250  | 30.6% |  −312.23  | **−$0.52** | NULL |
| 12 | 15,858 | 15,858 | 22.6% | −3,897.75 | **−$6.49** | NULL |
| 13 | 38,538 | 38,538 | 18.2% | −12,181.27 | **−$20.27** | NULL |
| 14 | 74,178 | 74,178 | 11.0% | −37,527.44 | **−$62.45** | NULL |

**Best gate: max_sing ≤ 9 at −$0.09/1000h — NULL by $2.09 (below $2 NULL threshold by more than the entire NULL gap, with a NEGATIVE sign).**

### Phase C-2 — prefix grid multi-gate grade (v59_v2)

| Gate (max_sing ≤) | n_fired | n_changed | swap-right | Lift $/1000h prefix | Verdict |
|---|---:|---:|---:|---:|---|
| 9  |      0 |      0 |   —    | **+$0.00**  | NULL |
| 10 |      0 |      0 |   —    | **+$0.00**  | NULL |
| 11 |      0 |      0 |   —    | **+$0.00**  | NULL |
| 12 |  2,268 |  2,268 | 10.6% | **−$12.81** | NULL |
| 13 |  6,048 |  6,048 |  7.6% | **−$41.36** | NULL |
| 14 | 11,970 | 11,970 |  3.9% | **−$131.27**| NULL |

**Both grids NULL. No two-grid divergence.** The prefix has 0 fires at gates ≤ 11
because canonical IDs 0-499,999 skew toward weak hands (per
[[taiwanese_canonical_id_prefix_lesson]]) and contain few qualifying PMID_SS_MAXTOP
cell hands at low max_sing.

---

## Why NULL (not MIXED, not SHIP)

**Both grids agree:** Full-grid best lift -$0.09 (NULL), prefix-grid best lift
$0.00 (NULL — no fires) or progressively negative. Neither grid shows any sign
of a salvageable signal; the verdict is robust.

**Two-grid agreement is what makes this clean.** S84's MIXED came from
$1.36 vs $5.59 grid disagreement at a small-residual cell. Here both grids
are tight on NULL — no question of "which to trust." The cell residual exists
($15.33 is real), but the addressable subset by any single PMID_tnomax-direction
rule is bounded above by $4.36 — already below the $5 SHIP threshold even
with perfect rule accuracy.

**The methodology gave us a clean verdict despite a structurally weak hypothesis.**
Phase B+ showed soft discriminators on both swap directions; an honest read
of those numbers (peak 65.9% / 45.9% vs S83's 92.8%) predicted NULL/MIXED.
The grader confirmed. No room for narrative arbitrage.

---

## The mechanism story (preserved for future work)

The cell **LOW pair × PMID_SS_MAXTOP** is defined by:
1. Hand is a single pair, rank 2-7
2. No PBOT_DS achievable (no singleton matches each of the pair's two suits)
3. No PMID_DS achievable (no 4-subset of singletons has 2+2 suit pattern)
4. n_PMID_SS_w_maxtop > 0 (at least one PMID config has max-on-top + SS bot)

Under v57, v52's pair-routing puts pair-in-mid 100% of the time on this cell.
v57's PMID variant choice is **mostly** correct (KEEP_PMID_TMAX = 54.1% of cell)
but has three failure modes:

1. **PBOT side-channel (17.5% of cell, $6.98 leak):** Oracle sometimes prefers
   pair-in-bot with SS bot (PBOT_*_SS_*). The condition is hand-dependent and
   involves the suit overlap between pair and singletons. The best feature
   we found (`best_pbot_ss_bph_tmax_ms`) peaked at 45.9% swap-rate — too soft
   for a clean rule. The pair-in-bot route would build a flush draw using the
   pair's suit + a matching singleton-pair, but only when the suit pattern
   aligns AND the singleton ranks are right.

2. **Within-PMID tnomax variant (13.1% of cell, $4.36 leak):** Oracle wants
   non-max on top, max in bot. `max_sing` discriminates softly (peak 65.9% at
   max_sing ≤ 11). The decision is hand-specific (depends on whether max
   anchors a stronger suited-pair in bot vs sits alone on top), and a single
   gate doesn't separate cleanly.

3. **OTHER (15.2% of cell, $3.99 leak):** v57 already picks a non-tmax_SS
   variant (most likely PMID_tnomax_31 or PMID_tnomax_SS), but oracle wants
   yet a different variant. The choice is finer-grained than a single rule
   can capture without an ML-grade decision boundary.

**Why no clean rule exists:** The residual is real ($15.33) but distributed
across three direction-conflicting populations. A rule targeting any one
direction harms the other two (and the KEEP_TMAX dominant population), and
no feature isolates a single direction sharply. Combined-feature rules
(e.g., max_sing ≤ 11 AND best_pmid_ss_bph_tmax ≤ 6) might shave a sub-rule,
but the cell-ceiling for any direction is already below $5 — even perfect
accuracy on tnomax ($4.36) won't clear SHIP. The cell asks for a
multi-direction structural rule (or ML routing), not a heuristic gate.

---

## What S85 changed

### Strategy of record (UNCHANGED)
- **Rule chain:** v57_lo_pair_defensive (no change)
- **ML champion:** v44_dt (no change — 14 sessions in production)

### Rule count
- Before: 20 numbered rules
- After: **20 (unchanged)** — v59 candidate did not ship

### Production numbers (UNCHANGED)
- v57 full grid: $1,412.53/1000h
- v57 prefix: $776.88/1000h
- Two-track divergence vs v44_dt: $332/1000h (unchanged)

### Files
- **New code (committed):**
  - `analysis/scripts/drill_v57_low_pmid_ss_maxtop_S85.py` — Phase B drill
  - `analysis/scripts/drill_v57_pmid_ss_swap_discriminator_S85.py` — Phase B+ discriminator
  - `analysis/scripts/strategy_v59_lo_pair_ss_tnomax.py` — v59 candidate (DID NOT SHIP; iterated v1 → v2 within Phase C)
  - `analysis/scripts/grade_v59_lo_pair_ss_tnomax_S85.py` — Phase C full-grid multi-gate grader
  - `analysis/scripts/grade_v59_prefix_multigate_S85.py` — Phase C prefix multi-gate grader
- **New artifacts (gitignored under `data/session85/`):**
  - `drill_v57_low_pmid_ss_maxtop_summary.json` — Phase B
  - `drill_v57_pmid_ss_swap_discriminator_summary.json` — Phase B+
  - `grade_v59_summary.json` — Phase C-1 (v2)
  - `grade_v59_prefix_multigate_summary.json` — Phase C-2
  - `*.log` files for each phase
- **Documentation:**
  - `SESSION_85_REPORT.md` — this file
  - `DECISIONS_LOG.md` — Decision 120 (NULL + methodology lessons)
  - `CURRENT_PHASE.md` — rewritten for S86

---

## Path forward (S86 candidates)

The Option D-revised playbook ship rate is now 1/3 (S83 SHIP / S84 MIXED /
S85 NULL). The methodology produces clean candidates and clean verdicts
in all three cases; the verdict is determined by cell properties, not by
methodology quality. The question for S86 is which adjacent cell offers
the cleanest setup.

### Default priority — try one more cell type before reassessing

1. **MID pair (rank 8-T) × PMID_DS_NOMAXTOP.** Rule 20 already ships at LOW
   pair tier; testing whether the same pattern extends to MID pair (8-T) is
   the natural extension. Rule 20's structural premise (sharp max_sing
   discriminator, single dominant direction) may or may not transfer. The
   max_sing gate likely shifts (Q→K possibly) because mid pairs alter the
   relative-strength calculus. **This is the most likely-to-ship next cell**
   because it inherits a known-working pattern.

2. **LOW × PMID_OTHER** ($11.81 v44 STRUCTURE / 137,808 hands). Largest
   remaining LOW pair cell by hand count. The "OTHER" cell precondition is
   "no PBOT_DS, no PMID_DS, no PMID_SS_w_maxtop" — these are weak hands
   with no structural bot upgrade available. The rule there would likely
   be about pair placement (mid vs bot vs split) rather than within-PMID
   variant; the discriminator surface is unknown.

3. **HIGH_ONLY × J-high and below** (S71: $14.47 + $4.31 STRUCTURE / 14k
   hands). Different category but same defensive-routing archetype.
   v52's existing rules for max ≤ T may already capture most of it.

### Strategic-fork direction (lower priority)

4. **Headline-goal recalibration.** With S83 SHIP + S84 MIXED + S85 NULL,
   the cumulative ship potential of the remaining under-covered cells is
   bounded. Resolving the gap to 95% match% by under-covered-cell extraction
   alone looks increasingly unlikely.

5. **Resolve S84 divergence** (N=1000 on full PMID_DS_MAXTOP cell, ~3-5h).
   Lower information yield than testing a new cell; deprioritized further
   given S85's NULL doesn't depend on resolving S84.

**Default S86 plan: try MID pair × PMID_DS_NOMAXTOP — the most likely
shipper because it inherits a known-working pattern (Rule 20 extension).
Use the same playbook with refined methodology (re-measure under production
in Phase B; both grids in Phase C; pre-committed thresholds).**

---

## Methodology notes (S85)

1. **The pre-committed-verdict pattern produced a clean NULL on a structurally
   weak candidate.** Phase B+ already suggested NULL/MIXED (soft discriminators
   + diverse residual). The grader confirmed mechanically. No narrative
   arbitrage was possible — both grids agreed NULL.

2. **The v1 → v2 iteration within Phase C demonstrates a useful refinement:
   "check v57's actual pick before overriding."** The v1 rule overrode v57
   on populations where v57 was already correct (OTHER, where v57 picks a
   tnomax variant). v2's restriction (only fire when v57 picks PMID_tmax_SS)
   narrowed the scope. Both NULL, but v2 is the right design pattern for
   future under-covered-cell rules — *don't override v57 unless v57 is in
   the wrong-pick population*.

3. **Phase B+ swap-rate within isolated populations is an UPPER BOUND on
   rule swap-rate.** The "within {KEEP ∪ SWAP}" framing measures the
   discriminator's discriminative power on the direction-relevant population,
   but the actual rule fires on a broader population including
   direction-conflicting populations (PBOT in our case). The real rule
   swap-rate is lower. *Phase C grader is the ground truth; Phase B+ is a
   feasibility check.*

4. **Cell residual is necessary but not sufficient for SHIP.** S85's
   $15.33/1000h cell residual is the largest of the three cells tested
   (S83 was $59 under v56; S84 was $7 under v57; S85 is $15 under v57), yet
   S85 NULLed while S83 shipped. Residual must be concentrated in a single
   addressable direction with a sharp discriminator. S85 fails the
   "single addressable direction" test (residual splits across PBOT,
   PMID-tnomax, OTHER).

5. **Ship rate on under-covered cells is now 1/3.** Across S83 + S84 + S85,
   we've tested 3 cells and shipped 1. If this rate holds for the remaining
   3-4 cells, the cumulative additional Rule-20-style ships is bounded
   around 1-2 more rules. **This is a useful prior for the headline-goal
   recalibration question** — Option D-revised is alive but saturating.

6. **"Speed is not necessary — clarity and perfection is" cashed out as the
   v1 → v2 restriction iteration.** The v1 grade was negative but only -$1.51;
   one could narrate "the rule has SOME merit but needs refinement." The v2
   restriction was the right refinement (architecturally cleaner), and the
   re-grade gave -$0.09 — even cleaner NULL. The honesty of the iteration
   matters more than the speed; v1's clear-failure result motivated the
   structural fix rather than a parameter-sweep workaround.

7. **The reusable grader template is now amortized across 3 cells.** Each
   new cell adapts: `drill_v57_<cell>_S<n>.py`, `drill_v57_<cell>_discriminator_S<n>.py`,
   `strategy_v<n>_<rule_name>.py`, `grade_v<n>_<cell>_S<n>.py`,
   `grade_v<n>_prefix_multigate_S<n>.py`. Infrastructure cost is now near-zero
   per cell.

---

## Headline state at end of S85 (UNCHANGED)

* **Rule chain (UNCHANGED):** v57_lo_pair_defensive — $1,412.53/1000h full grid / $776.88/1000h prefix.
* **ML champion (UNCHANGED):** v44_dt — $1,081/1000h full grid / $686/1000h prefix.
* **Two-track divergence:** $332/1000h (unchanged).
* **Total project rule count:** 20 (unchanged).
* **v59 (LOW × PMID_SS_MAXTOP rule):** TESTED — verdict NULL — NOT SHIPPED. Documented as a candidate that produced clean NULL on both grids; production stays at v57.
