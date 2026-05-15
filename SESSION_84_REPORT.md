# Session 84 — v58 MIXED: rule ships on prefix (+$5.59/1000h) but full grid NULLs (+$1.36/1000h); grid disagreement is the verdict, not a clean SHIP

_Generated 2026-05-15. S83's Option D-revised playbook extended to the
next under-rule-covered LOW pair cell (PMID_DS_MAXTOP). The candidate
rule (force PMID_tmax_DS when top_alt_rank ≥ 5) clears the prefix-grid
SHIP threshold but fails the full-grid SHIP threshold by ~$4. By project
precedent (S83 shipped because BOTH grids cleared the threshold), this
is MIXED — no production change._

## TL;DR — Plain language

**What we tested:** Extend S83's playbook (which shipped Rule 20 last session) to the next-largest under-rule-covered LOW pair cell — PMID_DS_MAXTOP. S77 measured this cell at $21.68/1000h STRUCTURE leak under v44_dt and 128,304 hands.

**What we found:** Under PRODUCTION v57, this cell's leak is only $7.24/1000h whole-grid — much smaller than S77's v44-based headline. v52's routing (which v56/v57 inherit) already gets 81% of the cell exactly right; the residual is **bidirectional within-PMID-DS variant choice** (PMID_tmax_DS ↔ PMID_tnomax_DS), with weak discriminators.

**What we tried:** The strongest discriminator from Phase B+ is `top_alt_rank` — the rank of the singleton that would sit on top under the alternative (tnomax_DS) config. Rule 21 candidate: when LOW pair × PMID_DS_MAXTOP × top_alt_rank ≥ gate, force PMID_tmax_DS (max on top, pair in mid, best DS bot excluding max).

**What the data said:** The pre-committed multi-gate graders fired automatically. **The two grids disagree:**

  - **Full grid (N=200 labels):** All 6 gates fired NULL. Best gate (top_alt_rank ≥ 5): +$1.36/1000h whole-grid lift. NULL threshold is $2/1000h; ship threshold is $5.
  - **Prefix grid (N=1000 labels, 500K hands):** Best gate (top_alt_rank ≥ 5) fired SHIP at +$5.59/1000h prefix lift, barely clearing the $5 ship threshold. Adjacent gates 2/6/7 = MIXED, gates 8/9 = NULL.

**Why the disagreement matters:** The swap-right rate at gate=5 jumps from **69.7% on full grid** to **88.1% on prefix grid** — purely a label-noise effect since the underlying hands are identical (canonical_hands.bin rows 0-499,999). N=200 labels are noisier (per S82 Decision 114, they disagree with N=1000 on ~32% of PAIR hands), and the noise masks signal on the full grid that the cleaner labels reveal.

**Why we're NOT shipping v58:** S83's precedent for shipping was strict: both grids cleared $5 (full +$16.47, prefix +$16.81 — 1.02× ratio, near-perfect agreement). S84's grids disagree by 4× ratio. The prefix's SHIP relies on the cleaner-labels argument; the full-grid NULL says the broader 6M-hand picture doesn't show the lift. Shipping based on prefix alone would be over-trusting a single-grid signal that isn't robust across the population. The conservative read is **MIXED**: real signal is plausible but not robust enough for production.

**What this tells us about Option D-revised's continuation:** S83's success came from a cell with a sharp discriminator (`max_sing`, 90%+ swap-right) and a large leak ($31 STRUCTURE under v44, of which production v56 left $59.42 → after Rule 20: $42.99). S84's cell has a soft discriminator (peak 67% on full / 88% on prefix) and a small residual leak ($7.24 under v57). **The playbook does not transfer mechanically to every under-covered cell.** The 76% closure that v52 already delivers on this cell leaves the residual at a magnitude that's right at the project's noise floor.

**The methodology held up.** The pre-committed-verdict pattern produced an unambiguous answer ("verdicts disagree") rather than letting us narrate a SHIP into existence post-hoc. The right action on MIXED is to NOT ship, document the divergence, and decide where to go next.

**What's still alive on Option D-revised:** Three other under-rule-covered cells remain (LOW × PMID_SS_MAXTOP, LOW × PMID_OTHER, MID pair × PMID_DS_NOMAXTOP) plus HIGH_ONLY × J-high and below. The S83 playbook applies cell-by-cell; expect some cells to ship (sharp discriminator, large leak) and others to NULL/MIXED (soft discriminator, small leak). S84 is the first of the latter.

## What S84 ran (timeline)

| Phase | Wall | What ran | Result |
|---|---:|---|---|
| Phase A | ~5 min (synthesis) | Verified cell choice via S77 cell_stats | $33.16 v44 leak / $21.68 STRUCTURE / 128k hands. Rule 20 cannot fire (by construction). |
| Phase B | 49s + analysis | `drill_v57_low_pmid_ds_maxtop_S84.py` | v57 leaks $7.24 whole-grid (vs v44's $33.16); 100% PMID placement; bidirectional within-PMID-DS variant mismatches |
| Phase B+ | 46s + analysis | `drill_v57_pmid_ds_variant_discriminator_S84.py` | Best discriminator `top_alt_rank` Δ=+1.18 for SWAP_TO_TMAX, peak 67% swap-right at top_alt=9 |
| Phase C-1 | 6×3s | `grade_v58_lo_pair_ds_maxtop_S84.py` (full grid, 6 gates) | ALL gates NULL. Best gate=5: +$1.36/1000h whole-grid |
| Phase C-2 | 89s | `grade_v58_prefix_S84.py` (prefix, single gate=5) | UNEXPECTED SHIP +$5.59/1000h prefix |
| Phase C-3 | 6×5s | `grade_v58_prefix_multigate_S84.py` (prefix, 6 gates) | Gate=5 SHIP $5.59; gates 2/6/7 MIXED; gates 8/9 NULL |
| Phase D | active | Report + Decision 119 + CURRENT_PHASE rewrite + commit + push | — |

---

## The numbers (the read of the experiment)

### Phase B — cell leak under PRODUCTION v57

| Metric | Value |
|---|---:|
| LOW × PMID_DS_MAXTOP n hands | 128,304 |
| Total leak under v44_dt (S77) | $33.16/1000h whole-grid |
| Total leak under v57 (this drill) | **$7.24/1000h whole-grid** |
| Δ (v57 − v44) | **−$25.92/1000h** (v52 routing closes most of v44's leak) |
| v57 cell match% (MATCH bucket) | 84.8% (108,856 / 128,304) |
| v57 pair-placement on cell | 100% PMID (no SPLIT, no PBOT) |
| Rule 20 fires on cell (sanity) | 0 ✓ (by construction; cell precondition is n_PMID_DS_w_maxtop > 0) |

Top STRUCTURE-bucket mismatches under v57:

| v57_class | oracle_class | n | $/1000h |
|---|---|---:|---:|
| PMID_tnomax_DS | PMID_tmax_DS | 4,312 | $2.41 |
| PMID_tmax_DS | PMID_tnomax_DS | 6,054 | $2.05 |
| PMID_tmax_DS | PBOT_tmax_SS_ms | 1,733 | $0.53 |
| PMID_tnomax_DS | PMID_tnomax_DS (config tiebreak) | 1,276 | $0.53 |

**Within-PMID-DS variant ceiling:** $2.41 + $2.05 = **$4.46/1000h whole-grid bidirectional.** PBOT side-channel: ~$1.50. Total cell ceiling at perfect routing: **~$6/1000h whole-grid**, which is itself only marginally above the $5 SHIP threshold.

### Phase B+ — discriminator search

Four target populations (within the cell):

| Population | n | % of cell | $/1000h |
|---|---:|---:|---:|
| KEEP_TMAX (v57=tmax_DS, oracle=tmax_DS) | 104,317 | 81.3% | $0.00 |
| KEEP_TNOMAX (v57=tnomax_DS, oracle=tnomax_DS) | 5,727 | 4.5% | $0.54 |
| SWAP_TO_TMAX (v57=tnomax_DS, oracle=tmax_DS) | 4,563 | 3.6% | $2.42 |
| SWAP_TO_TNOMAX (v57=tmax_DS, oracle=tnomax_DS) | 6,674 | 5.2% | $2.06 |
| OTHER | 7,023 | 5.5% | $2.22 |

Top discriminators (mean of feature within each pop):

| Feature | KEEP_TMAX | KEEP_TNOMAX | SWAP_TO_TMAX | SWAP_TO_TNOMAX |
|---|---:|---:|---:|---:|
| max_sing | 13.17 | 10.18 | 10.53 | 12.19 |
| **top_alt_rank** | 2.95 | 3.71 | **4.89** | 4.47 |
| best_bph_tnomax | 7.86 | 10.18 | 10.53 | 12.19 |
| bph_advantage | −3.05 | +1.52 | +1.88 | +1.80 |

**`top_alt_rank` per-value swap-right within (KEEP_TNOMAX, SWAP_TO_TMAX):**

| top_alt_rank | KEEP_TNOMAX | SWAP_TO_TMAX | swap_pct |
|---:|---:|---:|---:|
| 2 | 1,813 | 568 | 23.9% |
| 3 | 1,383 | 683 | 33.1% |
| 4 | 980 | 773 | 44.1% |
| 5 | 624 | 802 | 56.2% |
| 6 | 389 | 717 | 64.8% |
| 7 | 292 | 580 | 66.5% |
| 8 | 181 | 307 | 62.9% |
| 9 | 65 | 133 | 67.2% |

Peaks at 67.2% — much softer than S83's `max_sing` discriminator (which hit 92.8% at value 8 / 88.8% at value J).

### Phase C-1 — full grid multi-gate grade (auto-fired verdicts)

```
SHIP rule:   lift >= $5/1000h whole-grid
NULL rule:   lift  < $2/1000h whole-grid
MIXED:       in between
```

| Gate (top_alt_rank ≥) | n_fired | n_changed | swap-right | Δ EV | Lift $/1000h whole-grid | Verdict |
|---|---:|---:|---:|---:|---:|---|
| 2 (always) | 85,536 | 11,358 | 50.8% | +55.16 | **+$0.09** | NULL |
| 5 | 45,306 | 4,725 | 69.7% | +815.94 | **+$1.36** | NULL |
| 6 | 34,776 | 3,150 | 72.5% | +624.73 | **+$1.04** | NULL |
| 7 | 25,683 | 1,890 | 74.1% | +397.69 | **+$0.66** | NULL |
| 8 | 18,018 | 825 | 74.4% | +173.23 | **+$0.29** | NULL |
| 9 | 10,908 | 225 | 77.8% | +48.79 | **+$0.08** | NULL |

**Best gate: top_alt_rank ≥ 5 at +$1.36/1000h whole-grid — NULL by $0.64 (below $2 NULL threshold).**

### Phase C-2/3 — prefix grid multi-gate grade (auto-fired verdicts)

```
SHIP rule:   lift >= $5/1000h prefix
NULL rule:   lift  < $2/1000h prefix
MIXED:       in between
```

| Gate (top_alt_rank ≥) | n_fired | n_changed | swap-right | Δ match% | Lift $/1000h prefix | Verdict |
|---|---:|---:|---:|---:|---:|---|
| 2 (always) | 14,238 | 2,268 | 63.9% | +0.12pp | **+$4.33** | MIXED |
| **5** | 8,658 | 1,113 | **88.1%** | +0.16pp | **+$5.59** | **SHIP** |
| 6 | 6,408 | 693 | 93.2% | +0.11pp | **+$4.11** | MIXED |
| 7 | 4,518 | 378 | 94.4% | +0.06pp | **+$2.31** | MIXED |
| 8 | 2,985 | 165 | 91.5% | +0.03pp | **+$0.78** | NULL |
| 9 | 1,800 | 45 | 93.3% | +0.01pp | **+$0.22** | NULL |

**Best gate: top_alt_rank ≥ 5 at +$5.59/1000h prefix — SHIP by $0.59 (above $5 SHIP threshold).**

### The divergence

| Metric | Full grid (N=200) | Prefix (N=1000) | Ratio (prefix/full) |
|---|---:|---:|---:|
| Gate=5 lift | +$1.36/1000h whole-grid | +$5.59/1000h prefix | — (different normalizers) |
| Gate=5 n_fired | 45,306 | 8,658 | — (different populations) |
| Gate=5 n_changed | 4,725 | 1,113 | 0.236 |
| Gate=5 **swap-right rate** | **69.7%** | **88.1%** | **+18.4pp** |
| Gate=5 swap-wrong rate | 30.3% | 11.7% | −18.4pp |
| Gate=5 net EV gain per changed hand | 0.17 EV | 0.25 EV | 1.5× |

**The 18pp swap-right gap is purely a label-noise effect.** The underlying hands are identical (the prefix evaluates canonical hands 0-499,999 — same hands as in the full grid's prefix region). The only difference is the labels used to compute regret and oracle pick: N=200 Monte Carlo samples per setting vs N=1000.

Per S82 Decision 114: N=200 disagrees with N=1000 on ~32% of PAIR hands' argmax. For this rule's fired-and-changed population, ~30% wrong on N=200 vs ~12% wrong on N=1000 is directionally consistent — roughly half of the 32% disagreement rate flips our specific rule's verdict on that hand.

---

## Why MIXED instead of SHIP

**S83 precedent:** shipped because BOTH grids cleared the threshold (full +$16.47, prefix +$16.81, ratio 1.02×, near-perfect agreement). The two-grid agreement was load-bearing for the SHIP verdict; it provided confidence that the signal wasn't a grid artifact.

**S84 situation:** full +$1.36 (NULL), prefix +$5.59 (SHIP). Ratio 4×. The grids materially disagree.

**Two possible interpretations of the disagreement:**

1. **Label-noise-masks-real-signal (favors SHIP):** N=200 labels are noisier; the prefix's cleaner labels reveal real signal that the full grid is undercounting. The 18pp swap-right gap is consistent with this. Per S82 Decision 114, label noise on PAIR is significant.

2. **Prefix-subset-not-representative (against SHIP):** The first 500K canonical hands skew toward weak hands (per the [[taiwanese_canonical_id_prefix_lesson]] memory). The cell hands in the prefix may be enriched relative to the full grid, AND the cleaner labels happen to favor our rule's effect more than the truth would. The full grid (whole population) is the authoritative view.

**Either interpretation argues for caution.** Even on the most favorable read (label noise masks real signal), the prefix's lift is right at the SHIP threshold ($5.59 vs $5.00 — only +$0.59 of buffer). On the most pessimistic read (population artifact), shipping would introduce a regression in the broader population.

**The right action on this signal magnitude with this grid disagreement is to NOT ship.** The pre-committed-verdict pattern's strength is that it removes interpretive arbitrage; declaring SHIP here based on the prefix grade alone would be the kind of post-hoc rationalization the pattern is designed to prevent.

**Decision: VERDICT = MIXED. Production rule chain stays at v57. v58 is documented as a tested-and-MIXED candidate.**

---

## The mechanism story (preserved for future work)

The cell **LOW pair × PMID_DS_MAXTOP** is defined by:
1. Hand is a single pair, rank 2-7
2. No PBOT_DS achievable (no pair-suit singleton joining)
3. At least one PMID_DS config has max-singleton on top (n_PMID_DS_w_maxtop > 0)

Under production v57, v52's routing already puts pair-in-mid 100% of the time on this cell. The choice that remains is between two PMID-DS variants:

- **PMID_tmax_DS** — max on top, pair in mid, DS bot of the 4 other singletons (excluding max).
- **PMID_tnomax_DS** — a non-max singleton on top, pair in mid, DS bot of 4 singletons INCLUDING max.

Both are valid double-suited-bot configurations. The trade is:
- tmax_DS keeps the strong max on top (typically A or K — a real win on the top tier).
- tnomax_DS sacrifices the top tier (a weaker singleton there) for a stronger bot configuration where max anchors a suited pair in bot.

**`top_alt_rank` is the cleanest discriminator** (Δ = +1.18 mean between SWAP_TO_TMAX and KEEP_TNOMAX) but tops out at 67% swap-right within (KEEP_TNOMAX ∪ SWAP_TO_TMAX). The intuition: when the alternative top (top_alt_rank) is itself a high-rank singleton, you can afford to use it on top and put max in bot — but at top_alt ≥ 7 the oracle says "actually max on top is still better, take the tmax_DS." The signal is real but soft.

**Why the cell is structurally hard:**
- Both variants are DS (vs S83's NOMAXTOP cell, where the trade was DS vs SS — a much sharper structural difference).
- v52 already gets 81% right — the lever is small.
- The residual signal lives in a feature combination (top_alt_rank, max_sing, bph_advantage) that no single rule can cleanly capture without breaking the dominant KEEP_TMAX population.

---

## What S84 changed

### Strategy of record (UNCHANGED)
- **Rule chain:** v57_lo_pair_defensive (no change)
- **ML champion:** v44_dt (no change — 13 sessions in production)

### Rule count
- Before: 20 numbered rules (Rules 1-20)
- After: **20 (unchanged)** — v58 candidate did not ship

### Production numbers (UNCHANGED)
- v57 full grid: $1,412.53/1000h
- v57 prefix: $776.88/1000h
- Two-track divergence vs v44_dt: $332/1000h (unchanged)

### Files
- **New code (committed):**
  - `analysis/scripts/drill_v57_low_pmid_ds_maxtop_S84.py` — Phase B drill
  - `analysis/scripts/drill_v57_pmid_ds_variant_discriminator_S84.py` — Phase B+ discriminator
  - `analysis/scripts/strategy_v58_lo_pair_ds_maxtop.py` — v58 candidate (DID NOT SHIP)
  - `analysis/scripts/grade_v58_lo_pair_ds_maxtop_S84.py` — Phase C full-grid multi-gate grader
  - `analysis/scripts/grade_v58_prefix_S84.py` — single-gate prefix grader
  - `analysis/scripts/grade_v58_prefix_multigate_S84.py` — multi-gate prefix grader
- **New artifacts (gitignored under `data/session84/`):**
  - `drill_v57_low_pmid_ds_maxtop_summary.json` — Phase B
  - `drill_v57_pmid_ds_variant_discriminator_summary.json` — Phase B+
  - `grade_v58_summary.json` — Phase C-1 full grid
  - `grade_v58_prefix_summary.json` — Phase C-2 prefix single-gate
  - `grade_v58_prefix_multigate_summary.json` — Phase C-3 prefix multi-gate
  - `*.log` files for each phase
- **Documentation:**
  - `SESSION_84_REPORT.md` — this file
  - `DECISIONS_LOG.md` — Decision 119 (MIXED + methodology lesson)
  - `CURRENT_PHASE.md` — rewritten for S85

---

## Path forward (S85 candidates)

The Option D-revised playbook remains alive, but S84 shows it does not transfer to every cell. The cell-level closure under v52 already varies (e.g., PMID_DS_NOMAXTOP: $59 leak; PMID_DS_MAXTOP: $7 leak). Adjacent under-covered cells to test:

### Default priority — try one or two more cells before reassessing

1. **LOW × PMID_SS_MAXTOP** (S77: $9.71 STRUCTURE leak, 85,536 hands). Smaller cell. Differs from PMID_DS_MAXTOP in that no DS-bot is achievable — the bot is single-suited. The structural question may be: should this hand sometimes route to PBOT_SS or stay PMID_tmax_SS? Lower a priori expected lift but cleaner population.
2. **LOW × PMID_OTHER** (S77: $11.81 STRUCTURE leak, 137,808 hands). Catchall — no PBOT_DS, no PMID_DS, no PMID_SS_w_maxtop. These are "weak hand, no structural bot upgrade available" — the rule may be about whether to keep PMID at all or sometimes route to SPLIT.
3. **MID pair (8-T) × PMID_DS_NOMAXTOP** (S77: ~$8/1000h STRUCTURE). Extend Rule 20 to a higher pair tier. Rule 20 currently gates on `pair_rank ∈ {2-7}`; testing whether `pair_rank ∈ {8,9,T}` ships with a shifted max_sing gate (perhaps K instead of Q).

### Alternative direction — resolve the S84 divergence

4. **Run N=1000 labels on the full LOW × PMID_DS_MAXTOP cell** (128k hands × 105 settings × N=1000 = 13.4M evals, est. ~3-5h compute). This would replace the prefix-vs-full divergence with a single cleaner-label measurement on the entire cell. If the cleaner labels confirm the prefix's $5.59 signal across the full cell, v58 could be re-graded for SHIP. **Higher diligence cost** but resolves the ambiguity definitively.
5. **Run held-out OOS validation** at gate=5 on cell hands not in the prefix (i.e., canonical IDs 500K-2.8M cell hands). This would test whether the prefix's signal generalizes. **Lower cost** (~1h compute) but only validates one direction.

### Lower priority

6. **HIGH_ONLY × J-high and below** (S71: $14.47 + $4.31 STRUCTURE). Different category but same defensive-routing archetype. v52's existing rules for max ≤ T may already capture most of it.

**Default S85 plan: try LOW × PMID_SS_MAXTOP using the S84 playbook (with the lesson that the cell may be more closed than S77 headline suggests). Pre-commit ship thresholds in code before the grade.**

---

## Methodology notes (S84)

1. **The pre-committed-verdict pattern proved its value on a MIXED outcome.** Both graders fired their verdicts mechanically. Had the pattern not been in place, the temptation to declare SHIP based on the prefix's +$5.59 (and rationalize away the full grid's $1.36 as label noise) would have been substantial. The mechanical verdict + the project precedent of "both grids must clear" made MIXED the unambiguous reading.

2. **S77's headline leak under v44_dt was misleading for the production system.** v44 said $33.16 total / $21.68 STRUCTURE on this cell; production v57 said $7.24 total. The 4.6× compression came purely from v52's pair-routing logic — which was shipped before S77 measured leak. **Always re-measure under production before targeting a cell.** S83 made this same observation; S84 confirms the lesson generalizes.

3. **S83's playbook is cell-dependent, not universal.** S83's success came from a cell with a sharp discriminator (max_sing, 90%+ swap-right) and a large residual leak ($31 STRUCTURE under v44 → $59.42 under v56). S84's cell has neither — soft discriminator (peak 67% full / 88% prefix) and small residual leak ($7.24 under v57). The same compute and methodology produced MIXED instead of SHIP. **Expect cell-level outcomes to vary; null/mixed cells are part of the natural distribution, not a methodology failure.**

4. **The grid-divergence phenomenon may recur on future small-signal cells.** Cells where the under-v57 leak is in the $5-10 range will be sensitive to N=200 vs N=1000 label noise. Future Phase C graders may want to default to N=1000 prefix as the primary verdict and use full-grid as a sanity check, OR plan compute to expand N=1000 labels to the cell-specific population before grading. The current "both grids must clear $5" precedent is robust but pessimistic.

5. **The discriminator surface (per-gate prefix lift) has internal consistency** — gate=5 peaks, neighbors are MIXED, far gates NULL. This shape suggests a real signal of some magnitude, not noise. The question is whether the magnitude is large enough; on prefix it barely clears, on full it doesn't.

6. **"Speed is not necessary — clarity and perfection is" cashed out as running multi-gate prefix.** A single-gate prefix grade at gate=5 would have left ambiguity ("maybe gate=5 is a fluke; maybe other gates would ship too"). The multi-gate prefix grade ($5.7s × 6 = 34s wall) showed the surface and grounded the MIXED verdict in a coherent shape.

7. **Three new graders (full-multi-gate, prefix-single-gate, prefix-multi-gate) are reusable templates.** Subsequent under-rule-covered cells can adapt the same pattern: drill under production, find discriminator, write parametric strategy, run multi-gate full + multi-gate prefix, let pre-committed verdicts fire. The infrastructure cost amortizes across cells.

---

## Headline state at end of S84 (UNCHANGED)

* **Rule chain (UNCHANGED):** v57_lo_pair_defensive — $1,412.53/1000h full grid / $776.88/1000h prefix.
* **ML champion (UNCHANGED):** v44_dt — $1,081/1000h full grid / $686/1000h prefix.
* **Two-track divergence:** $332/1000h (unchanged).
* **Total project rule count:** 20 (unchanged).
* **v58 (LOW × PMID_DS_MAXTOP rule):** TESTED — verdict MIXED — NOT SHIPPED. Documented as a candidate that cleared prefix SHIP gate but failed full-grid SHIP gate; production stays at v57.
