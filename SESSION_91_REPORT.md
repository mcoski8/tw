# Session 91 — Chain-audit pattern pivots to prefix-COVERED LOW pair cells: v44_RULE13 chain bleeds $182/1000h vs v44_dt, but v54 + Rule 29 already absorb 97% of it; residual sub-cell bleeds FAIL two-grid SHIP standard. **NULL ship; production v64 UNCHANGED.**

_Generated 2026-05-15. S91 was the planned execution of the S90-defined PRIMARY path: pivot to LOW pair (prefix-COVERED) cells using the chain-audit pattern. Pre-drill on all 1,292,544 LOW pair hands surfaced two architecturally important findings: (1) the rule-based **v44_RULE13** chain (= what the v52→v47→v46→v45 path falls through to) BLEEDS $182.28/1000h vs v44_dt on LOW pair — much larger than HIGH_ONLY's chain bleed; (2) v54's PBOT_DS→v44_dt hybrid routing + v57's Rule 29 already recover $195.63/1000h, leaving production v64 ahead of v44_dt by $13.36/1000h on prefix and $92.41/1000h on full. Three candidate v65 designs to extend gate-out to small residual sub-cell bleeds were graded against pre-committed two-grid thresholds; all three FAILED (one NULL, two MIXED) due to full-grid disagreement. **Production v64 remains. No new ship. First non-ship session of the chain-audit run (broke the S87→S88→S89→S90 streak of four).**_

## TL;DR — Plain language

**What changed in your strategy of record:** Nothing. v64 from last session remains production. Rule count stays at 24.

**Why we didn't ship:** Sessions 87-90 found and gated four chain regressions in the HIGH_ONLY zone (no-pair hands). Each one fit the same pattern: a layered rule-chain (v47→v48→v52) was actively bleeding EV vs v44_dt on a subset where the prefix grader couldn't see it. Session 91 pivoted to LOW pair hands — territory the prefix grader CAN see (= "prefix-COVERED"). That should have made the SHIP standard stronger (real two-grid check), but it also raised the bar: any candidate now has to win on BOTH grids, not just the full grid alone.

When we ran the audit, we discovered two new things:

1. **The chain machinery for pair hands is a totally different beast.** For HIGH_ONLY hands, the chain layers were v47→v48→v52 (the layers we'd been gating). Those layers have guards that EXIT on pair hands. For LOW pair, the chain falls through all the way to a completely separate rule-based strategy called **v44_RULE13** — which is NOT v44_dt (our ML champion). v44_RULE13 has its own rule chain (v44_rule13_three_pair_DS → v43_rule12_two_pair → v42_rule11_jpair_pbot_ds → …). This was always known but never named in chain-audit context until this session.

2. **v44_RULE13 BLEEDS MASSIVELY vs v44_dt on LOW pair — $182/1000h.** Almost 30× the bleed S90 found on HIGH_ONLY × {8,9,T}. The good news: production already largely fixes this through v54's "if pair has PBOT_DS achievable → route to v44_dt" hybrid (absorbs $178.82) plus Rule 29 (absorbs $16.81). Production is genuinely working as designed — it just turns out the underlying chain it patches over is far worse than we'd realized.

**What we tried:** Three candidate "extend the gate-out" rules to capture residual sub-cell bleeds the prefix grader still showed (PMID_DS_NOMAXTOP × max_sing=K, PMID × max_sing=J non-DS_NOMAXTOP cells, and a combined version). Pre-committed grader auto-fired NULL/MIXED on all three because the FULL grid disagreed with the prefix grid on direction.

**Why the grids disagreed:** This is the methodologically important finding. For prefix-COVERED LOW pair cells, the prefix grid (N=1000) and full grid (N=200) measure DIFFERENT canonical_id populations within the same nominal sub-cell (the prefix is just the first 500K canonical IDs — a non-random lower-cid slice). When the per-hand effect is small ($0.04-$0.40/hand) and the chain machinery's hand-level behavior varies across the canonical_id range, the two grids legitimately diverge in their per-sub-cell aggregate Δ. Not winner's curse on the oracle — population divergence on the strategy.

**The audit closes cleanly with a NULL.** No regression to fix that survives the two-grid test. Honest result.

**Why this is still valuable:**
- The "v44_RULE13 bleeds $182" finding is a project-level architectural snapshot.
- The methodology lesson — "chain-audit pattern in prefix-COVERED zones runs into population-divergence noise on residual sub-cell bleeds" — is a real refinement of the S87-S90 playbook.
- Saved compute: didn't ship a $4 lift that would have lost $7 on the other grid.

**The numbers:**
- Production v64: $1,627.36/1000h full / $776.88 prefix (UNCHANGED from S90)
- Rule count: 24 (UNCHANGED)
- v44_dt: $1,081 full / $686 prefix (UNCHANGED for 19 sessions)
- v44_RULE13 chain on LOW pair: $438.38/1000h prefix leak (= **+$182.28** worse than v44_dt — massive bleed)
- v54's pair_hybrid routing recovers $178.82 of that
- v57's Rule 29 recovers another $16.81
- Net production: $13.36/1000h LIFT over v44_dt on LOW pair prefix
- Combined S87+S88+S89+S90+S91 chain-audit recovery: $214.83/1000h (S91 contributes $0)

**What's NOT changing:** Production, ML champion, rule count, prefix score, full score. v60 from S86 still parked. The streak of four consecutive chain-audit ships ends here, and that's OK — the audit confirmed there isn't a clean ship to make on this territory.

## The full story (compressed)

### Phase A — identify LOW pair target cells

Used `drill_pair_v44_per_hand_structural.parquet` (S66 drill output). All 6 LOW pair cells (PBOT_DS_JOINT, PBOT_DS_PARTIAL, PMID_DS_MAXTOP, PMID_DS_NOMAXTOP, PMID_SS_MAXTOP, PMID_OTHER) × pair_rank ∈ {2..7} are **prefix-COVERED** (cid_min between 61,085 and 62,041; well below the 500K prefix boundary).

Total LOW pair hands: 1,292,544 across the full grid; 215,162 within the prefix subset.

v44_dt baseline leak vs oracle (per cell, full grid):

| cell | n | v44 leak |
|---|---:|---:|
| PBOT_DS_JOINT | 171,072 | $19.32 |
| PBOT_DS_PARTIAL | 541,728 | $83.58 |
| PMID_DS_MAXTOP | 128,304 | $33.16 |
| PMID_DS_NOMAXTOP | 228,096 | $87.32 |
| PMID_SS_MAXTOP | 85,536 | $25.16 |
| PMID_OTHER | 137,808 | $33.03 |
| **TOTAL** | **1,292,544** | **$281.56** |

LOW pair has $281/1000h of v44_dt residual leak vs oracle on the full grid. PBOT_DS_PARTIAL and PMID_DS_NOMAXTOP are the largest cells with the largest leaks.

### Phase B — addressability pre-drill (v64 vs v44_dt)

`drill_v64_lo_pair_addressability_S91.py` evaluated v64 (current production) on all 1.29M LOW pair hands (4 min compute at ~5,300 hands/sec).

**Headline finding (per cell, full grid):**

| cell | v44=v64 % | v44 leak | v64 leak | Δ (v64−v44) |
|---|---:|---:|---:|---:|
| PBOT_DS_JOINT | 100.0% | $19.32 | $19.32 | **$+0.00** |
| PBOT_DS_PARTIAL | 100.0% | $83.58 | $83.58 | **$+0.00** |
| PMID_DS_MAXTOP | 82.7% | $33.16 | $7.24 | **$-25.92** |
| PMID_DS_NOMAXTOP | 58.6% | $87.32 | $42.95 | **$-44.37** |
| PMID_SS_MAXTOP | 74.6% | $25.16 | $15.33 | **$-9.83** |
| PMID_OTHER | 71.8% | $33.03 | $20.73 | **$-12.30** |
| **TOTAL** | | $281.56 | $189.15 | **$-92.41** |

Production v64 LIFTS $92.41/1000h over v44_dt on LOW pair full grid. PBOT cells are byte-identical (v54 routes both to v44_dt). PMID cells where the chain handles things show large lifts — production is doing useful work.

**Prefix grid version (215,162 prefix LOW pair hands):**

| cell | v44 prefix | v64 prefix | Δ prefix |
|---|---:|---:|---:|
| PBOT_DS_JOINT | $46.62 | $46.62 | $+0.00 |
| PBOT_DS_PARTIAL | $125.51 | $125.51 | $+0.00 |
| PMID_DS_MAXTOP | $3.79 | $8.09 | $+4.30 |
| PMID_DS_NOMAXTOP | $58.52 | $38.39 | $-20.13 |
| PMID_SS_MAXTOP | $8.33 | $9.64 | $+1.31 |
| PMID_OTHER | $13.32 | $14.49 | $+1.17 |

Two-grid disagreement on **PMID_DS_MAXTOP** (full -$25.92 LIFT vs prefix +$4.30 BLEED), **PMID_SS_MAXTOP** (full -$9.83 vs prefix +$1.31), **PMID_OTHER** (full -$12.30 vs prefix +$1.17). PMID_DS_NOMAXTOP agrees on direction (Rule 29 confirmed as a real lift).

### Phase B+ — chain audit (layer attribution on prefix grid)

`audit_v64_lo_pair_chain_S91.py` ran v44_dt, v44_RULE13 (= strategy_v44_rule13_three_pair_DS), v54, v57, v64 on every prefix LOW pair hand (215,162 × 5 strategies × 138s compute).

**Layer transitions, prefix totals:**

| layer | total leak ($/1000h) | Δ vs prior |
|---|---:|---:|
| v44_dt | $+256.11 | — |
| v44_RULE13 chain | $+438.38 | **+$182.28** (chain BLEEDS) |
| v54 (PBOT_DS routing) | $+259.56 | **-$178.82** (recovers most) |
| v57 (+ Rule 29) | $+242.75 | **-$16.81** (Rule 29 confirmed) |
| v64 (production) | $+242.75 | $+0.00 (HIGH_ONLY gates don't fire on pair) |

**This is the load-bearing finding of S91.** The rule-based v44_RULE13 chain — the fallthrough at the bottom of every chain layer in the project — bleeds **$182.28/1000h** vs v44_dt on LOW pair. Bigger than every chain bleed S87-S90 found by ~2-25×. But production v64 absorbs ~107% of it via v54 + Rule 29. Net production is $13.36/1000h ahead of v44_dt on prefix and $92.41/1000h ahead on full.

**Per-sub-cell residual:** the per-cell × max_sing breakdown identified five sub-cells where v44_RULE13 still bleeds vs v44_dt on prefix AFTER v54's routing (the "audit residual"):

| cell | max_sing | n_prefix | v44_dt $ | v44_RULE $ | Δ (chain bleed) |
|---|---:|---:|---:|---:|---:|
| PMID_DS_NOMAXTOP | 13 (K) | 10,080 | $15.32 | $20.14 | **+$4.82** |
| PMID_DS_MAXTOP | 11 (J) | 1,890 | $1.22 | $5.16 | +$3.95 |
| PMID_OTHER | 11 (J) | 2,030 | $2.29 | $5.53 | +$3.24 |
| PMID_SS_MAXTOP | 11 (J) | 1,260 | $1.22 | $2.59 | +$1.37 |
| PMID_DS_MAXTOP | 10 (T) | 945 | $0.99 | $1.85 | +$0.86 |

Combined residual: **$14.24/1000h prefix bleed**. But:

### Phase C — pre-committed grader

`grade_v65_lo_pair_chain_candidates_S91.py` locked thresholds:
- **SHIP**: prefix lift ≥ $5 AND full lift ≥ $5 (both grids clear, same direction).
- **MIXED**: one grid clears, the other doesn't.
- **NULL**: neither clears OR grids disagree direction.

Three candidates evaluated:

| candidate | predicted prefix lift | predicted full lift | mechanical verdict |
|---|---:|---:|---|
| A: route LOW × PMID_DS_NOMAXTOP × max_sing=K → v44_dt | +$4.82 | **-$6.85** | **NULL (grid negative)** |
| B: route LOW × {DS_MAXTOP, SS_MAXTOP, OTHER} × max_sing=J → v44_dt | +$8.56 | **-$1.35** | **MIXED (grids disagree)** |
| C: combined — all 5 sub-cells | +$14.24 | ~-$10.00 | **MIXED (grids disagree)** |

**Aggregate S91 verdict: NULL. No candidate ships. Production v64 unchanged.**

### Why the grids disagreed — the methodology finding

For prefix-COVERED LOW pair cells, the prefix grid (N=1000) and full grid (N=200) evaluate **different canonical_id populations within the same nominal sub-cell**. The prefix subset is the first 500,000 canonical hands — a non-random *lower-cid slice* of the structurally identical sub-cell.

The v44_RULE13 chain's hand-level behavior varies across the canonical_id range (it triggers different rule branches depending on subtle hand features that correlate with canonical_id ordering). When the per-hand effect is small ($0.04-$0.40 per hand), the prefix and full per-sub-cell Δ can legitimately diverge by **direction**, not just magnitude.

This is NOT winner's curse on the oracle (the standard "max of noisy estimates is biased upward" pitfall flagged in Decisions 114-117). The cause is **strategy-level**: the two strategies (v44_dt vs v64) interact with the prefix vs full canonical-id populations differently. The two grids are honest measurements on different populations — no methodology fix can collapse them.

**Project-level lesson:** The chain-audit pattern (S87-S90) was most productive on HIGH_ONLY × {J-A,8-T} because (a) prefix-silent → EFFECT-SIZE-DOMINANCE exception applies, AND (b) per-sub-cell bleeds were $7-99/1000h, large enough to dominate any population-divergence noise. On prefix-COVERED LOW pair, neither condition holds: the prefix grid is real (so we can't claim EFFECT-SIZE-DOMINANCE), and the per-sub-cell bleeds are $1-5/1000h (small enough that population-divergence noise dominates).

### What this answers about the cascade

1. **The v44_RULE13 rule-based chain is the project's biggest hidden net-negative layer** — bleeds $182/1000h vs v44_dt on LOW pair alone. But it's already largely contained by v54 + Rule 29. The audit confirmed this is the right architecture.

2. **The chain-audit pattern (find-a-net-negative-layer, gate it out)** does NOT scale arbitrarily — it works when the residual bleeds are LARGE relative to grid noise OR when prefix-silence permits the EFFECT-SIZE-DOMINANCE exception. On LOW pair PMID residuals, neither applies.

3. **Rule 29 (S83's $16.81 ship) is independently re-confirmed** via the audit's layer attribution. Δ_v57_vs_v54 = exactly -$16.81 on the prefix grid, concentrated entirely in PMID_DS_NOMAXTOP × max_sing=12 (the cell × gate Rule 29 was designed for).

4. **v54's PBOT_DS hybrid routing is independently re-confirmed.** Δ_v54_vs_v44_RULE13 = -$178.82 on prefix; without it, the project would be bleeding $182/1000h vs v44_dt on LOW pair. v54 is the load-bearing pair-handling architecture.

5. **HIGH_ONLY gate-outs (v61/v62/v63/v64) don't fire on pair hands.** Δ_v64_vs_v57 = exactly $0.00 across all LOW pair sub-cells, confirming the gates are scoped correctly.

### Methodology lessons (Session 91)

1. **Two-grid SHIP standard is the right test for prefix-COVERED audits.** S87-S90 used EFFECT-SIZE-DOMINANCE on prefix-SILENT cells; S91 is the first session to apply the proper two-grid standard. Both candidates that "would have shipped" on prefix alone failed when the full grid was checked — exactly the kind of false ship the two-grid standard is meant to prevent.

2. **Prefix and full grids evaluate DIFFERENT canonical_id populations within the same nominal sub-cell.** The prefix subset is the first 500K canonical IDs — a non-random lower-cid slice. Per-sub-cell aggregate Δ on the two grids can legitimately diverge in DIRECTION when (a) per-hand effects are small, and (b) the strategy's per-hand picks correlate with canonical_id ordering. This is "population-divergence noise" — distinct from oracle winner's curse.

3. **The CHAIN AUDIT pattern applicability test:** the pattern is most productive when EITHER (i) the target cells are prefix-SILENT (Effect-Size-Dominance applies) OR (ii) per-sub-cell residual bleeds are ≥$5/1000h on BOTH grids (so population-divergence noise doesn't dominate). On LOW pair PMID cells, neither condition holds — explaining the NULL.

4. **Pre-committed-threshold pattern is critical for honest verdicts.** Without locking $5 thresholds in code before evaluation, the temptation to ship the $4.82 prefix bleed in Candidate A would have been real. The mechanical NULL verdict is the right call.

5. **A NULL audit session is still a complete chain-audit cycle.** S87/S88/S89/S90 each shipped; S91 doesn't. The methodology produced an honest answer — no candidate clears the SHIP bar. Worth the session.

6. **The v44_RULE13 chain bleed scale ($182/1000h) is a project-level architectural snapshot** worth documenting. Future sessions should approach this number aware that the v54/v55/v56 hybrid + Rule 29 are doing $195 of recovery work — they are load-bearing, not optional.

## Headline state at end of S91 (UNCHANGED from S90)

| Strategy | Use case | Where it lives |
|---|---|---|
| **v64_high_only_chain_fix_zone** | PRODUCTION rule chain. **$1,627.36/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v64_high_only_chain_fix_zone.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 19 sessions, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

* **Total project rule count: 24** (UNCHANGED).
* **Cumulative closure since pre-S68: $1,291.16 of $1,409 = 91.6%** (UNCHANGED).
* **Remaining gap to oracle ceiling: $117.84/1000h** (UNCHANGED).
* **Production vs v44_dt: $546.36/1000h** (UNCHANGED).
* **First non-ship session in the chain-audit run.** S87/S88/S89/S90 shipped Rules 21/22/23/24 (HIGH_ONLY chain gate-outs); S91 NULLs cleanly with documented methodology lesson.

## What's still on the table (S92 candidates)

1. **PRIMARY — audit two_pair cells with the chain-audit pattern.** v55_two_pair_hybrid is the dedicated chain layer for two_pair. Existing per-hand parquet `drill_two_pair_v44_per_hand_structural.parquet` (1.34M hands, 7-cell taxonomy) is ready. Audit setup: compare v44_dt to v55-routed strategy and v44_RULE13 chain on each cell × hi_pair × max_sing. Same two-grid SHIP standard. Predictable outcome if S91 pattern holds: v55's hybrid routing absorbs most of the chain bleed, residual sub-cell candidates fail two-grid standard. Worth testing once to confirm.

2. **SECONDARY — audit trips cells with the same pattern.** Smaller drill (only 2.97M-row parquet vs 23.9M for pair). Similar setup to two_pair.

3. **TERTIARY — Option C N=1000 oracle generator.** Still required for v60 from S86. Engineering scope ~30-60 min Rust mod. Deprioritized vs new audits because PRIMARY uses existing infra.

4. **REFINEMENT (DEFERRED) — v52-defensive-low partial-effectiveness exploit from S90.** Still on the books as a possible future v65 design. Speculative.

5. **HYPOTHESIS — extend Rule 29 to gate=K with a v52-defensive-low-style construction.** Not investigated this session. Could be worth one drill in S92+ if PRIMARY/SECONDARY don't produce a ship.

The dominant lever for the project remains "find and remove chain regressions." But the audit on prefix-COVERED LOW pair shows this lever has limits: when residual bleeds are small AND prefix-grader is active, the two-grid standard correctly NULLs candidates that would have shipped on prefix alone. Future audits should approach prefix-COVERED zones aware of this constraint.
