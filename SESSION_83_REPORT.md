# Session 83 — v57 SHIPS: Rule 20 (LOW pair defensive PMID-DS swap) — first production ship in 12 sessions

_Generated 2026-05-15. End of S82 surfaced a user-owned strategic fork; user picked Option D (rule-chain extension) with a refinement: focus on under-rule-covered weak-hand zones rather than min-maxing well-covered areas. S83 executed the refined Option D and shipped v57 with **+$16.81/1000h prefix-grid lift** vs v56._

## TL;DR — Plain language

**What we shipped today:** A new defensive rule (Rule 20) for the production rule chain. v56 → v57. The new strategy of record is `strategy_v57_lo_pair_defensive` at $1,412.53/1000h full grid / **$776.88/1000h prefix** (down from v56's $794 prefix).

**The strategy of record CHANGED for the first time in 12 sessions** (since v56 in S70). All of S71-S82's ML cascade work (feature engineering null in S78, label-quality null in S82) produced zero production change. This session's rule-layer work shipped a clean +$16.81/1000h prefix lift on the very first attempt — confirming that the bottleneck has moved from "ML feature/label space at v44 capacity" to "rule-layer real estate the cascade hadn't touched."

**Your strategic redirect was the load-bearing decision of this session.** S82's fork offered three options: A3 (5× compute on the same lever the data already disfavored), recalibration (concede the 95% match target), or Option D (rule-chain extension on S77's LOW pair finding). You picked Option D **with a refinement** — focus on under-rule-covered weak-hand zones (where there are NO existing rules), not just S77's specific LOW-pair-PMID-DS hint. That reframe is what made the ship possible:

  - **Phase A diagnostic confirmed the under-coverage map:** PAIR has $511/1000h total residual leak under v44 but only ONE rule covering it (Rule 19 on Q-pair PBOT_DS_JOINT, +$8.50). HIGH_ONLY has $381 total leak but THREE rules (A/K/Q-high) plus the defensive Rule 17 generalized handler. **PAIR was strikingly under-covered.**
  - **Phase B drill on v56 (not just v44) found the leak structure had shifted:** S77's headline "LOW pair SPLIT mistake" was a v44_dt phenomenon — production v56 (which routes these hands to v52, not v44) doesn't split LOW pair at all. v56 picks PMID 100% of the time on LOW × PMID_DS_NOMAXTOP. The leak is instead about WHICH PMID variant: v56 picks max-on-top + single-suited bot when oracle wants drop-max + double-suited bot.
  - **Phase B+ found a razor-sharp discriminator:** `max_sing` (the rank of the largest non-pair card). When max_sing ≤ J, the swap to DS-bot is right 89-93% of the time. When max_sing = A, the swap is WRONG 86% of the time. Q is the inflection (77% swap-right); K is 54%.
  - **Phase C graded the rule at multiple gates with pre-committed SHIP/NULL/MIXED thresholds in code:** Q gate (+$16.47 full / +$16.81 prefix) >> $5 ship threshold. Decisive SHIP.

**Plain-language Rule 20:** "If your pair is a small one (rank 2 through 7), AND you have no flush-draw potential with the pair (no card matching either pair-suit), AND a double-suited bottom is achievable BUT only if your max kicker goes in the bottom, AND your max kicker is Queen or lower — then *give up* putting max kicker on top. Take the double-suited bottom (which forces max into bottom) and put a smaller singleton on top. You're losing top anyway; the DS bottom is the real win."

**Why this is exactly the "weak hand defensive routing" you described:** A LOW pair with a non-A/non-K max kicker is a weak hand. The choice "max on top" looks offensive but it's not — the J / T / 9 / 8 / 7 on top can't actually win or chop top against the opponent's likely top card. Oracle (the solver) says: stop pretending the kicker is offensive, take the defensive DS-bot instead. The rule extracts exactly this defensive trade.

**What this means for the cascade:** S82's two adjacent zero-signal levers (features NULL in S78, labels NULL in S82) correctly identified the bottleneck as "ML at v44 capacity." The rule-layer operates OUTSIDE that capacity — and the very first rule extraction in the under-covered zone produced a clean ship. **The Option D path is alive.** Plenty more weak-hand cells remain (LOW pair × PMID_DS_MAXTOP, PMID_SS_MAXTOP, PMID_OTHER; J-high and below HIGH_ONLY) where the same playbook can be applied.

## What S83 ran (timeline)

| Phase | Wall | What ran | Result |
|---|---:|---|---|
| Phase A | ~5 min (synthesis) | Analyzed existing S76/S77/S71 outputs | Coverage map: PAIR LOW > HIGH_ONLY LOW for under-rule-covered leak |
| Phase B | 77s + analysis | `drill_v56_low_pmid_ds_nomaxtop_S83.py` on 228,096 hands | v56 leaks $59.42/1000h on cell (vs v44's $87.32); 100% PMID; dominant mismatch is within-PMID variant |
| Phase B+ | 77s + analysis | `drill_v56_pmid_swap_discriminator_S83.py` on same hands | `max_sing` is razor-sharp discriminator: ≤J swap-right 89-93%, =A swap-wrong 86% |
| Phase C-1 | 4×4s | `grade_v57_lo_pair_defensive_S83.py` at 4 gates on full grid | Q gate WINS: +$16.47/1000h whole-grid SHIP |
| Phase C-2 | 84s | `grade_v57_prefix_S83.py` on prefix N=1000 (500K hands) | Q gate confirmed: +$16.81/1000h prefix SHIP (>> $5 threshold) |
| Phase D | active | This report + Decision 118 + CURRENT_PHASE rewrite + STRATEGY_GUIDE update + commit + push | — |

---

## The numbers (the read of the experiment)

### Multi-gate grade on full grid (auto-fired ship verdicts)

```
SHIP rule:   lift >= $5/1000h  (project standard, S78 convention)
NULL rule:   lift < $2/1000h
MIXED:       in between
```

| Gate | n_fired | n_changed | swap-right rate | Δ EV | Lift $/1000h whole-grid | Verdict |
|---|---:|---:|---:|---:|---:|---|
| J (≤11)  | 36,288 | 6,000 | 85.0% | +2,219 | **+$3.69** | MIXED |
| **Q (≤12)** | **72,576** | **42,288** | **72.8%** | **+9,899** | **+$16.47** | **SHIP** |
| K (≤13)  | 133,056 | 102,768 | 56.9% | +7,779 | +$12.94 | SHIP (but smaller than Q) |
| A (≤14)  | 228,096 | 197,808 | 33.6% | −53,454 | **−$88.95** | **NULL (catastrophic)** |

**Q gate is the maximum-lift ship-eligible candidate.** K still ships at +$12.94 but loses $3.53 vs Q's +$16.47 (introduces more KEEP-wrong fires than it adds K-max swap-right hands).

### Prefix-grid grade at Q gate (500K hands × N=1000 labels)

| Metric | v56 (production) | v57 (Q gate) | Δ |
|---|---:|---:|---:|
| Match% (vs N=1000 argmax) | 66.07% | 66.49% | **+0.42pp** |
| Mean regret $/1000h | $793.69 | $776.88 | **−$16.81** |
| n_rule_fires (prefix) | — | 12,096 | — |
| n_picks_changed (prefix) | — | 6,048 | — |

**The pre-committed grader auto-fired SHIP** ($16.81 > $5 ship threshold; $16.81 > $2 null threshold).

### Two-track divergence

| Session | rule-chain vs v44_dt full-grid divergence | Δ this session |
|---|---:|---:|
| Pre-S68 | $1,409 | baseline |
| Post-S68 (v54) | $1,027 | −$382 (S68) |
| Post-S69 (v55) | $393 | −$634 (S69) |
| Post-S70 (v56) | $348 | −$45 (S70) |
| Post-S82 (v56 unchanged for 12 sessions) | $348 | $0 |
| **Post-S83 (v57)** | **$332** | **−$16** (S83) |

The divergence remains because v44_dt's $1,081 full-grid leak is mostly orthogonal to v57's gains (v44's leak is concentrated in categories where v57 doesn't fire). Closing more of this divergence requires either more rule-layer extractions (the Option D path is now demonstrated) or an ML retrain that lifts v44 itself.

---

## The mechanism (why Rule 20 works)

The cell **LOW pair × PMID_DS_NOMAXTOP** is defined by:
1. Hand is a single pair, rank 2-7
2. Neither pair suit is represented among the 5 non-pair singletons (so PBOT_DS is impossible — there's no way to put pair-in-bot with a double-suited bottom)
3. A double-suited (2+2 suit pattern) configuration of 4 of the 5 singletons IS achievable, but ONLY when max_sing is one of the 4 (i.e., max_sing must be in bot)

**v52 (which v56 routes here) defaults to "max kicker on top, take whatever bot suit comes out" — typically single-suited (SS) or three-of-a-suit (31) bot.** This is the safe-looking play: A or K on top, pair in mid, rest in bot.

**Oracle disagrees in a specific way.** When max_sing ≤ Q (≤ 12), the "safe" top isn't safe at all — a Q or J on top almost always loses or chops against the opponent's top card. Oracle says: stop spending the max kicker on top, take the DS bot (which captures real points via the bot's two flush draws), and put a non-max singleton on top (which loses the same as max would).

**The 77% swap-right rate at Q gate decomposes as:**
- 72,576 hands fire under the gate
- 42,288 of those have v57's pick ≠ v56's pick (the remaining 30,288 are "rule fires but v56 already happened to pick PMID_tnomax_DS")
- Of the 42,288 changed: 30,800 (72.8%) get strictly closer to oracle; 11,313 (27%) get strictly farther; rest tie
- Net per-hand EV: +0.234 ($2.34 per fired-and-changed hand)
- Whole-grid average: +$16.47/1000h

---

## What S83 changed

### Strategy of record
- **Rule chain:** v56_trips_hybrid → **v57_lo_pair_defensive** (NEW)
- **ML champion:** v44_dt (UNCHANGED — 12 sessions in production)

### Rule count
- Before: 19 numbered rules (Rules 1-19; Rules 22-28 are defensive high_only sub-rules consolidated into Rule 17)
- After: **20 numbered rules** (Rule 20 = LOW pair defensive PMID-DS swap)

### Production numbers
- v56 → v57 full grid: $1,429 → **$1,412.53** (−$16.47)
- v56 → v57 prefix: $794 → **$776.88** (−$16.81)

### Files
- **New code (committed):**
  - `analysis/scripts/strategy_v57_lo_pair_defensive.py` — the rule + chain composition with v56
  - `analysis/scripts/drill_v56_low_pmid_ds_nomaxtop_S83.py` — Phase B drill
  - `analysis/scripts/drill_v56_pmid_swap_discriminator_S83.py` — Phase B+ discriminator drill
  - `analysis/scripts/grade_v57_lo_pair_defensive_S83.py` — multi-gate full-grid grader with pre-committed verdict
  - `analysis/scripts/grade_v57_prefix_S83.py` — prefix-grid grader with pre-committed verdict
- **New artifacts (gitignored under `data/session83/`):**
  - `drill_v56_low_pmid_ds_nomaxtop_summary.json` — Phase B cell stats
  - `drill_v56_pmid_swap_discriminator_summary.json` — discriminator tables
  - `grade_v57_summary.json` — multi-gate full-grid verdicts
  - `grade_v57_prefix_summary.json` — prefix-grid verdict
- **Documentation:**
  - `SESSION_83_REPORT.md` — this file
  - `DECISIONS_LOG.md` — Decision 118 appended
  - `CURRENT_PHASE.md` — rewritten for S84
  - `STRATEGY_GUIDE.md` — Part 1 entry for S83, Part 6 production-rule-chain block updated

---

## Path forward (S84 candidates)

S83's playbook (cell-level drill → discriminator → gated rule → multi-gate grade with pre-committed verdict) is the new template. Adjacent under-covered cells where the same approach likely transfers:

1. **LOW pair × PMID_DS_MAXTOP** (S77: $21.68 STRUCTURE leak, 128k cell hands). The cell has DS-with-max-on-top achievable — opposite of S83's cell. Expected pattern: v56 picks max-on-top with non-DS bot when DS-with-max-on-top is achievable; rule forces DS-with-max-on-top.
2. **LOW pair × PMID_SS_MAXTOP / PMID_OTHER** ($9.71 + $11.81 STRUCTURE leak). Smaller cells but still untouched.
3. **HIGH_ONLY × J-high and below** ($14.47 + $4.31 STRUCTURE leak). Different category but same "under-rule-covered defensive routing" archetype. v52 has defensive rules for max ≤ T already (Rules 22-28); J-high may have residual signal not captured by the 2nd-high ≤ 8 gate.
4. **MID pair × PMID_DS_NOMAXTOP** (S77: ~$8/1000h STRUCTURE leak; pair ranks 8-10). The same mechanism may apply but with shifted gate (max_sing ≤ K or J instead of Q).
5. **Re-grade v44_dt + downstream chain to check for cascade effects.** v57 doesn't touch v44_dt directly, but if subsequent rules ship, v44's contribution to the chain may need re-evaluation.

**Default S84 plan: drill LOW pair × PMID_DS_MAXTOP using the S83 playbook. Pre-commit ship thresholds in code before the grade. Expected lift if pattern transfers: +$10-15/1000h prefix (smaller cell + similar swap-right discrimination).**

---

## Methodology notes (S83)

1. **The user's redirect is the load-bearing decision.** Option D was originally framed as "implement S77's specific LOW pair kicker_max-in-pair-suit discriminator" — a narrow rule extraction. User's reframe ("focus on under-rule-covered weak-hand zones broadly, not just well-trodden areas") changed the scope and made it possible to identify the bigger leak structure under v56. Without the reframe, S83 would have re-drilled v44's SPLIT mistake (which v56 doesn't make).

2. **Always grade the PRODUCTION strategy, not just the diagnostic baseline.** S77 measured leak under v44_dt. Production v56 routes these hands through v52, not v44. Phase B's first finding was that v56 leaks LESS than v44 on this cell ($59.42 vs $87.32) AND for a different reason. Had I trusted S77's "SPLIT mistake" headline without re-measuring on v56, the rule would have targeted the wrong pattern.

3. **Pre-committed grader thresholds in code are now the project standard.** Both `grade_v57_lo_pair_defensive_S83.py` (full grid) and `grade_v57_prefix_S83.py` (prefix) have SHIP/NULL/MIXED thresholds hardcoded. The grader prints the verdict next to the numbers automatically. No interpretation arbitrage when the data lands. This matches the S81/S82 pattern from the A2 NULL.

4. **The discriminator's "max_sing" finding is methodologically beautiful.** A single feature (highest non-pair card rank) separates KEEP (oracle agrees with v52) from SWAP (oracle wants DS-bot) with sharp cutoffs: 89-93% at ≤ J, 77% at Q, 54% at K, 14% at A. Two clean inflection points — Q (where the swap becomes a coin-flip's-worth majority) and A (where the swap becomes wrong). Multi-gate grading turned the per-value swap-right histogram into a ship-eligible candidate.

5. **The under-coverage map is the right framing for Option D's continuation.** Pair has $511 total leak with one rule; high_only has $381 with three rules (plus defensive). Cells × rule-routing × leak is the right table to maintain going forward. Each row is a potential rule. After S83 ships, PAIR × LOW × PMID_DS_NOMAXTOP becomes a "rule-routed" cell; the next rule extractions populate the remaining LOW pair cells.

6. **"Speed is not necessary — clarity and perfection is" cashed out here as multi-gate grading.** Single-gate grade would have shipped Q at +$16.47 but missed that K at +$12.94 also ships (worse than Q) and A is catastrophic (−$89). Multi-gate gives us confidence we picked the right gate AND mapped the full lift surface. Same compute footprint, much higher information output.

7. **The same playbook applies to adjacent cells.** S83 used: (a) S77's existing drill data to identify the candidate cell, (b) reused S66's pair_structural + classify_pick_pair taxonomy (no re-derivation), (c) ran v56 on cell hands to confirm leak, (d) discriminator drill to find gate, (e) multi-gate grade with pre-committed verdicts. Steps a-e compress to ~3 hours per cell once templates are in place. S84+ can run multiple cells per session.

---

## Headline state at end of S83 (CHANGED — strategy of record advances)

* **Rule chain (NEW):** v57_lo_pair_defensive — **$1,412.53/1000h full grid / $776.88/1000h prefix**. Grader-confirmed both grids with pre-committed verdicts.
* **ML champion (UNCHANGED):** v44_dt — $1,081/1000h full grid / $686/1000h prefix.
* **Two-track divergence:** $332/1000h (was $348; closed −$16 this session).
* **Total project rule count:** 20 (was 19; new Rule 20 = LOW pair defensive PMID-DS swap).
* **Cumulative two-track-divergence closure:** $1,077/1000h closed of original $1,409 = **76%** (was 75%).
* **First production ship in 12 sessions.** v56 had held since S70.
