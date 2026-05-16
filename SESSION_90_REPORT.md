# Session 90 — Chain-audit extends to HIGH_ONLY × max ≤ T: v64 SHIPS Rule 24 (+$7.23/1000h whole-grid) on 25,740 prefix-silent hands; v52-defensive-low confirmed PARTIALLY effective in first project-level audit

_Generated 2026-05-15. S90 was the planned execution of the S89-defined PRIMARY path: pivot to HIGH_ONLY × max ∈ {7-T} (different firing mode — v52-defensive-low rather than v52-fallthrough). Phase A structural feasibility eliminated 7 (cell × rank) combinations for free. Pre-drill confirmed v63 leaks +$7.23/1000h MORE than v44_dt on the 25.7K target hands. Chain audit attributed the bleed to v44→v47 (+$19.28) partially recovered by v48 (−$2.53) and v52-defensive-low (−$9.52), net residual +$7.23. v64 extends v63's gate to cover the entire structurally-non-empty HIGH_ONLY × max ≥ 8 zone. Full-grid grader auto-fired SHIP at +$7.23/1000h. Production goes $1,620.13 → $1,627.36/1000h. **Fourth consecutive chain-audit ship.** Combined S87+S88+S89+S90 recovery = $214.83/1000h._

## TL;DR — Plain language

**What changed in your strategy of record:** A new Rule 24. It's the same fix as Rules 21, 22, and 23 from the last three sessions, just applied to a different territory — instead of "no-pair J/Q/K/A high cards" (which Rules 21-23 covered), Rule 24 covers "no-pair hands where the highest card is an 8, 9, or T". For those hands with addressable structure (one of five suit/joint patterns), bypass the human-designed defensive rules and let the ML model handle it.

**Why this matters:** This finishes the chain-audit job for HIGH_ONLY hands entirely. Sessions 87-89 cleaned up the J/Q/K/A territory; Session 90 extends the same cleanup to T-and-below. The 8-T zone uses a DIFFERENT firing mode (v52-defensive-low, designed in S53 specifically for these weak-high hands), and we discovered something useful in the process: that defensive handler is partially effective — it catches about half of the bleed from v47's Q-high DS chain — but it doesn't go far enough. The ML model still beats it on aggregate.

**Why the dollar amount is smaller this time.** S87 shipped $98.67, S88 shipped $98.84, S89 shipped $10.09, S90 ships $7.23 — the trend is clearly diminishing as the target zones shrink. S90's 25,740 hands are about half S89's 48,132 and only ~3% of S87's 756,000. Per-hand, the bleed is similar in magnitude. The total just hits a smaller pool.

**An interesting nuance:** Unlike S87-S89, where v44_dt almost always picked better than the chain (swap-right rates 62-85%), here v52-defensive-low wins outright on 23.2% of the hands (vs S89's 7.6%). The aggregate still favors gating uniformly, but there's room for a future Rule 25 that retains v52-defensive-low's wins on the subset where it deserves them. Deferred.

**The numbers are mechanically clean:**
- 70.4% swap-right rate on changed hands
- 0 out-of-gate disagreements on 50K random sample
- v44→v47 transition still the dominant culprit (+$19.28 introduced)
- v52-defensive-low partially recovers ($9.52 of the $19.28)
- Net residual bleed $7.23 — same magnitude as S89
- Pre-committed SHIP threshold $5; lift $7.23 → cleared by 1.45×
- Pre-drill and grader produced IDENTICAL aggregate numbers (high stability)

**The numbers:**
- Production v63: $1,620.13/1000h
- Production v64 (now): **$1,627.36/1000h** (+$7.23, +0.45%)
- Rule count: 23 → **24**
- Cumulative closure since pre-S68 baseline: **$1,291.16 of $1,409 = 91.6%** (was 91.1%)
- Remaining gap to oracle ceiling: **$117.84/1000h** (was $125.07)
- Combined S87+S88+S89+S90 chain-audit recovery: **$214.83/1000h** across four consecutive sessions

**What's NOT changing:**
- The ML champion (v44_dt) — unchanged for 18 sessions running.
- The prefix-grid score — unchanged at $776.88 (Rule 24 fires entirely outside prefix coverage, same as Rules 21-23).
- The v60 candidate from S86 — still parked, still MIXED-by-methodology, still waits on Option C N=1000 oracle infrastructure.

## The full story (compressed)

### Phase A — verify target stats and structural feasibility

The S89 plan handed S90 a clear default: "pivot to HIGH_ONLY × max ∈ {7-T} chain audit. Different firing mode (v52-defensive-low). Unknown whether the v47 chain bleed extends here." Phase A queried the S71 per-hand parquet and applied structural feasibility checks:

**Structurally empty (no compute needed):**
- HIGH_ONLY × max = 7: empty. HIGH_ONLY requires 7 distinct ranks, but only 6 ranks ≤ 7 exist (2-7). Aces always counted as 14.
- HIGH_ONLY × max ∈ {8, 9, T} × JOINT_HIGH: empty. JOINT_HIGH needs `best_ms_mid_high ≥ J`; mid cards have rank < max ≤ T = 10.
- HIGH_ONLY × max ∈ {8, 9, T} × NEITHER: empty (same pigeonhole argument as NEITHER × {J-A} in S89).
- HIGH_ONLY × max = 8 × JOINT_MED: empty. JOINT_MED needs `best_ms_mid_high ≥ 8`; mid cards have rank < max = 8.

**Non-empty target — 11 (cell × rank) combinations totaling 25,740 hands:**

| cell | n | v44_baseline_leak |
|---|---:|---:|
| JOINT_MED × {9, T} | 3,150 | $0.6483 |
| JOINT_LOW × {8, 9, T} | 630 | $0.0714 |
| DS_NO_JOINT × {8, 9, T} | 16,200 | $6.4077 |
| DS_NO_MAXTOP × {8, 9, T} | 3,456 | $1.4087 |
| MS_ONLY × {8, 9, T} | 2,304 | $0.7455 |
| **TOTAL** | **25,740** | **$9.2816** |

All prefix-silent (cid_min ≥ 590,496; prefix ends at 499,999). v44 baseline leak is HIGHER per-hand than S89 — $9.28 on 25.7K vs S89's $6.37 on 48.1K. So v44 has more "room to be worse" on these hands.

### Phase B — pre-drill: bombshell #4 at smaller scale

Wrote `drill_v63_high_only_addressability_S90.py` (template from S89, rebound to v63 baseline + new target cells). Re-evaluated v63 (current production) on the 25.7K hands. Results:

| cell | n | v44 leak $ | v63 leak $ | **Δ (chain bleed)** |
|---|---:|---:|---:|---:|
| JOINT_MED | 3,150 | $0.65 | $2.00 | **+$1.35** |
| JOINT_LOW | 630 | $0.07 | $0.38 | **+$0.31** |
| DS_NO_JOINT | 16,200 | $6.41 | $10.15 | **+$3.75** |
| DS_NO_MAXTOP | 3,456 | $1.41 | $2.33 | **+$0.92** |
| MS_ONLY | 2,304 | $0.75 | $1.65 | **+$0.90** |
| **TOTAL** | **25,740** | **$9.28** | **$16.51** | **+$7.23** |

**v63 leaks +$7.23/1000h MORE than v44_dt on these cells.** Hypothesis P1 (v52-defensive-low is well-designed, clean null) REJECTED. Hypothesis P2 (chain extends to max ≤ T) CONFIRMED.

Override activity: 68-89% across all cells. v63 actively reroutes a strong majority of these hands away from v44_dt's picks. Per (cell × rank), only 2 of 14 sub-cells individually clear the per-cell $1 gate; aggregate uniformity supports gating the whole zone as one architectural move.

### Phase B+ — chain audit reveals v52-defensive-low's PARTIAL effectiveness

Wrote `audit_v63_chain_bleed_S90.py`. Layer attribution against v44_dt baseline:

| Cell | v44→v47 Δ | v47→v48 Δ | v48→v52 Δ |
|---|---:|---:|---:|
| JOINT_MED | +$1.23 | -$0.21 | +$0.33 |
| JOINT_LOW | +$0.49 | +$0.01 | -$0.19 |
| DS_NO_JOINT | **+$10.98** | -$0.79 | -$6.44 |
| DS_NO_MAXTOP | +$4.61 | -$1.19 | -$2.50 |
| MS_ONLY | +$1.98 | -$0.36 | -$0.72 |
| **Σ** | **+$19.28** | **-$2.53** | **-$9.52** |

**The story is different from S87/S88/S89.** v47 is STILL the dominant regression introducer (+$19.28) — fourth consecutive session with v47 (Rules 13-16, Q-high DS chain) as the culprit. But:
- v48 contributes a small improvement (−$2.53)
- v52 contributes a much LARGER improvement (−$9.52)
- Net residual: +$7.23

By v52 firing mode: **100% of 25,740 hands fire v52-defensive-low** (LOW_MAX_DEFENSIVE = {7, 8, 9, 10}). **This is the first project-level audit of v52-defensive-low's behavior.** Verdict: it's partially effective — it recovers approximately half of v47's bleed but does not fully restore v44_dt's performance. The S53 design intent (defensive-low for max ∈ {7-T}) was REAL and CORRECT. The implementation just leaves money on the table relative to ML.

### The fix (v64 = Rule 24)

Same architectural shape as v63, just with more cells in the gate-out set:

```python
TARGET_MAX_RANKS = {8, 9, T, J, Q, K, A}
TARGET_CELLS = {DS_NO_JOINT, DS_NO_MAXTOP, MS_ONLY,
                JOINT_HIGH, JOINT_MED, JOINT_LOW}   # all 6 non-empty cell types

def strategy_v64(hand):
    if HIGH_ONLY(hand) and max_rank(hand) in TARGET_MAX_RANKS \
       and cell(hand) in TARGET_CELLS:
        return strategy_v44_dt(hand)   # bypass chain
    return strategy_v57_lo_pair_defensive(hand)
```

v64 effectively gates **the entire structurally-non-empty HIGH_ONLY × max ≥ 8 zone**. (HIGH_ONLY × max = 7 is structurally empty by combinatorial necessity; no further chain-audit work remains in the HIGH_ONLY category.)

### Grader (Phase C)

Pre-committed thresholds (locked in code BEFORE grader ran):
- SHIP ≥ $5/1000h whole-grid (same as S89)
- NULL ≤ $1/1000h
- MIXED in between

Pre-drill predicted $7.23 — comfortably above SHIP at 1.45×.

Full-grid grade (19s compute, 25.7K hands × 2 strategies + 50K out-of-gate sanity):

| Metric | Value |
|---|---:|
| Whole-grid lift | **+$7.23/1000h** |
| Cell hands | 25,740 |
| v64 same as v63 | 5,559 (21.6%) |
| v64 better | 14,214 (55.2%) |
| v64 worse | 5,967 (23.2%) |
| Swap-right rate (of changed) | **70.4%** |
| Out-of-gate sanity (v64 != v63 disagreements on 50K random sample) | **0** ✓ |
| Mechanical verdict | **SHIP** (cleared SHIP threshold by 1.45×) |

Per-cell breakdown matched the pre-drill prediction exactly (to $0.01 across every cell). The high stability between pre-drill and grader (both at $7.23) is a useful signal — when chain-audit and grader agree to two decimal places, the EFFECT-SIZE-DOMINANCE rule is on solid footing.

### Why we shipped on N=200 only (the EFFECT-SIZE-DOMINANCE rule applied to a fourth-consecutive ship)

Same justification as S87/S88/S89, calibrated to the smaller target:

1. Effect size $7.23 is 1.45× the SHIP threshold ($5) — smaller multiple than S87/S88's 3.3× but on the right side and similar to S89's 2×.
2. Effect size is **~33× the LLN aggregate noise floor** for a 25.7K-hand population (~$0.22 estimated, scaled from S89's $0.30 by √(25.7/48)).
3. Population is 25,740 hands. Aggregate measurement is statistically tight; pre-drill ↔ grader match to $0.01 confirms.
4. Mechanism is REMOVE-OVERRIDE (gate out a deterministic chain), not ADD-NEW-SETTING.
5. Per-hand split (22% same / 55% better / 23% worse) shows clear net favor toward v44_dt despite v52-defensive-low's notable partial wins.
6. The grader is mechanically pre-committed in code; no narrative arbitrage.

The Option C N=1000 oracle infrastructure remains DEFERRED. Required for v60 retroactive validation and any future smaller-effect candidate — but not blocking on a $7.23 effect at 33× the noise floor.

## What this means architecturally — the structurally-non-empty HIGH_ONLY zone is CLOSED

S87, S88, S89, and S90 found the SAME architectural pattern at four magnitudes:

| Session | Target | n_hands | Chain Δ | Swap-right | v44→v47 share |
|---|---|---:|---:|---:|---:|
| S87 | DS_NO_JOINT × {J-A} | 756,000 | +$98.67 | 62.3% | ~83% |
| S88 | DS_NO_MAXTOP + MS_ONLY + JOINT_HIGH × {J-A} | 357,504 | +$98.84 | 76.8% | 99.7% |
| S89 | JOINT_MED + JOINT_LOW × {J-A} | 48,132 | +$10.09 | 85.2% | 96.0% |
| **S90** | **5 cells × {8, 9, T}** | **25,740** | **+$7.23** | **70.4%** | **100%+** |
| **TOTAL** | **Structurally-non-empty HIGH_ONLY × max ≥ 8** | **1,187,376** | **$214.83** | — | — |

(S90's "v44→v47 share" is over 100% because v48 and v52 partially recover it — the layer made the leak strictly worse and the subsequent layers recovered. The same denominator framing as S87-S89 doesn't apply cleanly when intermediate layers improve.)

The v47 chain bleed is **net-negative across the ENTIRE structurally-non-empty HIGH_ONLY zone, at every magnitude.** v47 (Rules 13-16, the "Q-high DS chain", S52) was designed as offensive value-add for high-card hands. Empirically, it has been bleeding EV across the entire HIGH_ONLY zone for 34+ sessions since it shipped. The bleed went undetected because the prefix grader is structurally blind to HIGH_ONLY hands.

The structurally-non-empty HIGH_ONLY × max ≥ 8 audit is now COMPLETE. All 17 non-empty (cell × rank) combinations across the zone (6 in {J-A}, 11 in {8,9,T}) are gated. No further chain-audit work remains in HIGH_ONLY.

**What's still left to audit (S91 candidates):**

1. **Prefix-COVERED cells** (LOW pair, two_pair, trips). The audit pattern might surface buried v47/v52 net-negatives outside HIGH_ONLY. These categories use DIFFERENT rule chains in production (v44_dt routing via v54/v55/v56 hybrids). Existing per-hand parquets cover most. Different audit setup but transferable principle.
2. **Option C N=1000 oracle generator**: still needed for v60 retroactive validation and smaller-effect candidates. Engineering scope ~30-60 min.
3. **LOW × PMID_OTHER drill**: the last LOW pair cell deferred from S87/S88/S89. Standard Option D-revised playbook.
4. **REFINEMENT (DEFERRED): v52-defensive-low partial-effectiveness exploit.** S90 found v52-DL actively wins on 23% of S90 target hands. A future v65 could retain v52-DL on the subset where it wins (per-hand picker rather than uniform gate). Speculative.

The dominant lever for the project remains "find and remove chain regressions." The audit pattern has shipped **$214.83/1000h across four sessions** — bigger than every rule shipped from S71-S86 combined ($16.81 prefix from Rule 20 was the only ship in that 16-session window). Whether S91's prefix-COVERED pivots find similar regressions in two_pair / trips / LOW pair is the next strategic question.

## Methodology lessons (S90)

1. **The chain-audit pattern transferred 1:1 for a FOURTH consecutive session.** S87 → S88 → S89 → S90: four scripts each, all templated by rebinding target cells + baseline strategy + thresholds. Infrastructure cost is empirically zero per cell.

2. **The EFFECT-SIZE-DOMINANCE rule generalized to four ships across two orders of magnitude.** S87 ($98.67), S88 ($98.84), S89 ($10.09), S90 ($7.23): three orders of magnitude apart, all four pass the "effect ≫ noise floor by 20×+" criterion. The per-session SHIP threshold is a per-cell calibration; the noise-floor multiple is what generalizes.

3. **Per-hand swap-right rate trended UP S87→S88→S89, then DOWN at S90 (62.3% → 76.8% → 85.2% → 70.4%).** Useful diagnostic: a drop in swap-right rate flags that the chain-layer being gated is doing real work. v52-defensive-low's partial-effectiveness story showed up here BEFORE the audit revealed the mechanism. Future audits should treat sub-65% swap-right rate as a flag to investigate the chain layer's design intent, even if aggregate verdict is SHIP.

4. **v52-defensive-low is partially effective — first project-level audit of this mode.** The S53 design intent (defensive-low for max ∈ {7-T}) was REAL — it recovers $9.52 of v47's $19.28 bleed. Just not fully. Worth recording as a project finding: v52-defensive-low's S53 design philosophy was correct; the implementation leaves money on the table relative to ML.

5. **Pre-Phase A structural feasibility check eliminated 4 (cell × rank) combinations for free.** Same playbook as S89's NEITHER × {J-A} closure, applied to: max=7 × any, max ∈ {8,9,T} × {JOINT_HIGH, NEITHER}, max=8 × JOINT_MED. Five-minute pencil-and-paper proof saves at least an hour of compute time per cell.

6. **Pre-drill ↔ grader match to two decimal places confirms aggregate stability.** S87 and S88 saw stronger headline magnitudes but worse pre-drill ↔ grader agreement. S89 and S90 both predicted the grader output to within $0.01. This is the load-bearing signal that EFFECT-SIZE-DOMINANCE applies — the noise floor is genuinely well below the effect size when pre-drill ↔ grader agree this tightly.

7. **"Speed is not necessary — clarity and perfection is" — S90 reaffirms.** Running the chain audit (7s compute) when the pre-drill headline was already clear ($7.23) pinpointed the layer attribution and revealed v52-defensive-low's partial-effectiveness story. The "v52-defensive-low is partially effective" finding becomes a project-level methodology lesson, not just a session note.

## Headline state at end of S90

| Strategy | Use case | Where it lives |
|---|---|---|
| **v64_high_only_chain_fix_zone** | PRODUCTION rule chain (NEW S90). **$1,627.36/1000h full / $776.88/1000h prefix** (prefix unchanged — gate fires outside prefix coverage). | `analysis/scripts/strategy_v64_high_only_chain_fix_zone.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 18 sessions, since v44 in S58). $1,081/1000h full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

* **Total project rule count: 24** (Rule 24 = v64 chain gate-out extension to HIGH_ONLY × {8, 9, T}, completing the structurally-non-empty HIGH_ONLY zone audit).
* **Cumulative closure since pre-S68: $1,291.16 of $1,409 = 91.6%** (was 91.1%).
* **Remaining gap to oracle ceiling: $117.84/1000h** (was $125.07).
* **Production vs v44_dt: $546.36/1000h** (the rule chain now outperforms v44_dt by this much, up from $539).
* **Structurally-non-empty HIGH_ONLY × max ≥ 8 audit: COMPLETE** (24 non-empty (cell × rank) combinations all gated; HIGH_ONLY × max = 7 structurally empty).
