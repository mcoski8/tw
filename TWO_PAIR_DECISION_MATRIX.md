# Session 69 Phase 1+2 — Two_pair Decision Matrix (Oracle vs v44_dt + v54 audit)

*Generated 2026-05-12. Mirrors `PAIR_DECISION_MATRIX.md` (S66) for the
two_pair category (cat=2, n=1,338,480 canonical hands = 22.3% of
canonical-grid). Answers: "for every (hi_pair_rank × structural cell),
what does oracle pick (layout, top, bot suit), where does v44_dt diverge,
and where does v54 (the production rule chain inherited from
v8/v14/v52 era) leave catalog-shippable headroom?" Phase 1 builds the
descriptive oracle/v44 matrix; Phase 2 adds the v54 sweep and rule-coverage
audit; Phase 3 candidate work is deferred to S69 Phase 2 / S70.*

**KEY FINDING (Phase 2):** v54 leaves **$634/1000h WG** more two_pair
residual than v44 (canonical-equal framing) — concentrated **uniformly
across all cells** (no PMID-style anti-headroom). **Every single cell
favors v44 over v54.** This is qualitatively cleaner than pair (where
PMID cells favored v52 by $50 WG) and quantitatively much larger than
the pair v52→v44 gap of $341 WG. **A blanket Path-B hybrid extension
("if two_pair → v44_dt") would predict a $634 WG whole-grid full-grid
ship — ~1.7× S68's record $382.**

---

## TL;DR — what the data says (one sentence per hi_pair_rank, sorted by v54-v44 gap)

| hi_pair | v44 WG | v54 WG | v54-v44 | n | Headline |
|---:|---:|---:|---:|---:|---|
| **A** | $12.70 | $142.39 | **$129.69** ← peak | 205,920 | v44 captures 83% pct_opt while v54 captures 48%; the +$130 lift is the largest single-rank Path-B headroom |
| **Q** | $7.86 | $126.43 | **$118.57** | 171,600 | Q-hi-pair is structurally similar to Q-pair (S66): the layout-trade-off cell where v54's old rule chain catastrophically under-weights Layout C (Hbot+Lmid) |
| **K** | $11.50 | $126.56 | **$115.05** | 188,760 | Same pattern as A; A_DS layout under-utilization dominates |
| **J** | $8.16 | $85.24 | $77.08 | 154,440 | Smaller absolute gap; declining magnitude with hi_pair_rank below the Q peak |
| T | $8.40 | $60.98 | $52.59 | 137,280 | Starts to taper |
| 9 | $7.20 | $46.42 | $39.22 | 120,120 | |
| 8 | $6.28 | $35.72 | $29.44 | 102,960 | |
| 7 | $5.60 | $26.84 | $21.24 | 85,800 | |
| 6 | $5.10 | $22.26 | $17.16 | 68,640 | |
| 5 | $4.03 | $20.38 | $16.36 | 51,480 | |
| 4 | $2.64 | $14.43 | $11.79 | 34,320 | |
| 3 | $1.35 | $7.63 | $6.29 | 17,160 | |
| **TOTAL** | **$80.82** | **$715.29** | **$634.47** | **1,338,480** | **$634 WG full-grid whole-grid harness-predicted lift** |

**Headline single sentence:** v54 (= v52 = v8/v14 era rule chain on
two_pair) leaks $634 WG vs v44_dt in canonical-equal framing — uniformly
across all cells, concentrated 69% in the top 4 hi_pair_ranks (A, K, Q, J).
The dominant mismatch class is the same `B_SS ↔ C_SS` Hbot/Hmid layout
confusion that S55 surfaced and that v44's t2p_v2_* features partially
address. **The Path B hybrid extension ("two_pair → v44") would predict
$634 WG full-grid lift — 1.7× S68's record ship.**

---

## Method

* **Data:** All 1,338,480 canonical two_pair hands (cat=2), graded against
  `oracle_grid_full_realistic_n200.bin` (the realistic 70/25/5 mixture
  profile, S24 artifact).
* **Per-hi-pair-rank stratification:** 3 through A (12 ranks). Each
  hi_pair_rank gets a different number of canonical hands depending on
  rank-pair distribution (more hands at higher hi_pair_rank).
* **Structural cell:** 7 mutually-exclusive cells per hi_pair_rank (the
  taxonomy is **two_pair-specific** and is informed by v44's existing
  `t2p_v2_*` Layout-B/C feature family from S55):
  * `LAYOUT_A_DS` — Layout A is DS-bot (HH+LL pair-suits FULLY match;
    bot is "two pair DS" — strongest A play).
  * `LAYOUT_C_DS` — Not (1), Layout C DS achievable (≥1 of 3 C-routings
    yields 2+2 bot).
  * `LAYOUT_B_DS` — Not (1) or (2), Layout B DS achievable.
  * `LAYOUT_A_SS` — Not above, Layout A is SS-bot (HH and LL share
    exactly 1 suit; bot has 2+1+1).
  * `LAYOUT_C_SS_ONLY` — No DS layout, no Layout A SS; Layout C SS
    achievable.
  * `LAYOUT_B_SS_ONLY` — No DS, no A_SS, no C_SS; Layout B SS achievable.
  * `LAYOUT_OTHER` — Layout A is RB and B/C only have 31/RB routings
    (empirically EMPTY — every two_pair hand has at least one DS or SS
    layout achievable; this taxonomy partitions the entire population).
* **Cell population is canonical-symmetric:** every hi_pair_rank has the
  same cell distribution (the cell axis depends on suit patterns, which
  are hi_pair_rank-independent at the canonical level):
  * LAYOUT_A_DS: 19.2% · LAYOUT_C_DS: 23.1% · LAYOUT_B_DS: 17.3% ·
    LAYOUT_A_SS: 32.7% · LAYOUT_C_SS_ONLY: 6.7% · LAYOUT_B_SS_ONLY: 1.0% ·
    LAYOUT_OTHER: 0.0%
* **Oracle/v44 pick classification:**
  * `layout`: A (both pairs in bot) / B (Lo in bot, Hi in mid) / C (Hi in
    bot, Lo in mid) / SPLIT (pair cards split across tiers)
  * `bot_suit`: DS / SS / 31 / RB / 4f
  * `top_type`: SING_MAX / SING_MID / SING_LOW / PAIR
  * `mid_suited`: bool
  * Compact label: e.g. `C_SS_tmax_mu`, `B_DS_tlow_mu`, `A_SS_tmid_ms`,
    `SPLIT_DS_tpair`

---

## Big-picture aggregates

### Per-hi_pair-rank residual (v44_dt vs oracle, canonical-equal weighting)

| hi_pair | n_hands | v44 pct_opt | v44 mean_regret ($/hand) | v44 $/1000h WG |
|---:|---:|---:|---:|---:|
| A | 205,920 | 83.16% | $370.5 | $12.70 |
| K | 188,760 | 82.84% | $366.2 | $11.50 |
| Q | 171,600 | 85.58% | $275.2 | $7.86 |
| J | 154,440 | 83.97% | $317.6 | $8.16 |
| T | 137,280 | 82.68% | $367.6 | $8.40 |
| 9 | 120,120 | 83.10% | $360.4 | $7.20 |
| 8 | 102,960 | 82.95% | $366.3 | $6.28 |
| 7 | 85,800 | 82.02% | $392.3 | $5.60 |
| 6 | 68,640 | 80.28% | $446.7 | $5.10 |
| 5 | 51,480 | 79.76% | $470.4 | $4.03 |
| 4 | 34,320 | 80.32% | $461.4 | $2.64 |
| 3 | 17,160 | 80.62% | $471.8 | $1.35 |
| **TOTAL** | **1,338,480** | **82.84%** | **$363** | **$80.82** |

The catalog framing (canonical-equal) gives **$80.82/1000h WG** for
two_pair v44→oracle. CURRENT_PHASE quotes **$363** because that uses
share-weighting (1.34M / 6.0M = 22.3%); both numbers measure the same
gap on different scales.

**v44 pct_opt of 82-86% per hi_pair_rank is dramatically higher than
pair's 60-72%.** v44 handles two_pair quite well at the catalog level —
the per-hand mean regret of ~$363-470 is the lowest of any non-degenerate
category in v44's coverage.

### Cell-residual cross-tab (v44 vs oracle, $/1000h whole-grid by canonical-equal)

| hi_pair | LAYOUT_A_DS | LAYOUT_C_DS | LAYOUT_B_DS | LAYOUT_A_SS | LAYOUT_C_SS_ONLY | LAYOUT_B_SS_ONLY | TOTAL |
|---:|---:|---:|---:|---:|---:|---:|---:|
| A | $1.97 | $1.37 | $2.09 | $5.43 | $1.81 | $0.04 | $12.70 |
| K | $1.74 | $0.70 | $2.31 | $4.90 | $1.83 | $0.03 | $11.50 |
| Q | $1.14 | $0.35 | $1.90 | $3.31 | $1.15 | $0.01 | $7.86 |
| J | $1.27 | $0.38 | $1.82 | $3.48 | $1.20 | $0.02 | $8.16 |
| T | $1.35 | $0.52 | $1.47 | $3.70 | $1.34 | $0.01 | $8.40 |
| 9 | $1.19 | $0.57 | $1.21 | $3.10 | $1.12 | $0.01 | $7.20 |
| 8 | $1.03 | $0.53 | $1.08 | $2.69 | $0.94 | $0.00 | $6.28 |
| 7 | $0.95 | $0.42 | $1.00 | $2.45 | $0.79 | $0.00 | $5.60 |
| 6 | $0.70 | $0.33 | $0.91 | $2.39 | $0.77 | $0.00 | $5.10 |
| 5 | $0.43 | $0.24 | $0.76 | $1.94 | $0.66 | $0.00 | $4.03 |
| 4 | $0.26 | $0.17 | $0.48 | $1.21 | $0.51 | $0.00 | $2.64 |
| 3 | $0.12 | $0.09 | $0.25 | $0.62 | $0.27 | $0.00 | $1.35 |
| **TOTAL** | **$12.13** | **$5.66** | **$15.28** | **$35.22** | **$12.38** | **$0.13** | **$80.82** |

**Cell totals across hi_pair_ranks:**
- **LAYOUT_A_SS: $35.22 (43.6%)** ← largest absolute cell, deepest per-hand ($481/hand)
- LAYOUT_B_DS: $15.28 (18.9%) — second largest
- LAYOUT_C_SS_ONLY: $12.38 (15.3%)
- LAYOUT_A_DS: $12.13 (15.0%)
- LAYOUT_C_DS: $5.66 (7.0%) ← smallest meaningful cell; v44 most accurate here (~91% pct_opt)
- LAYOUT_B_SS_ONLY: $0.13 (0.2%) — negligible

LAYOUT_A_SS dominates because it's the largest cell (32.7% of two_pair) AND v44's hardest cell — the structural ambiguity of "Layout A bot is SS but Layout B/C also achievable; choose carefully" is the core two_pair difficulty.

### Top mismatch patterns per hi_pair_rank

The dominant mismatch class is `B_SS_tmax_mu ↔ C_SS_tmax_mu` (= the
S55 Hbot_Lmid vs Hmid_Lbot SS-bot ambiguity). It appears in the top-3
mismatch class for EVERY hi_pair_rank:

| hi_pair | dominant mismatch | n | mean ($/hand) | WG | Description |
|---:|---|---:|---:|---:|---|
| A | `B_SS_tmax_mu → C_SS_tmax_mu` | 6,395 | $2,248 | $2.39 | v44 picks Layout B with SS bot, oracle picks Layout C |
| K | `C_SS_tmax_mu → B_SS_tmax_mu` | 5,211 | $2,259 | $1.96 | Same in reverse — direction varies by structural detail |
| Q | `C_SS_tmax_mu → B_SS_tmax_mu` | 4,030 | $1,981 | $1.33 | v44 picks C, oracle prefers B |
| J | `C_SS_tmax_mu → B_SS_tmax_mu` | 4,149 | $2,073 | $1.43 | |
| T | `C_SS_tmax_mu → B_SS_tmax_mu` | 4,021 | $2,161 | $1.45 | |
| 9 | `B_SS_tmax_mu → C_SS_tmax_mu` | 3,249 | $2,041 | $1.10 | |
| 8 | `B_SS_tmax_mu → C_SS_tmax_mu` | 2,825 | $2,028 | $0.95 | |
| 7 | `B_SS_tmax_mu → C_SS_tmax_mu` | 1,937 | $2,010 | $0.65 | |
| 6 | `B_SS_tmax_mu → C_SS_tmax_mu` | 1,083 | $2,117 | $0.38 | |

**The B_SS↔C_SS Hbot/Hmid layout-confusion class alone accounts for
$8-12 WG within v44's two_pair residual.** This is exactly the structural
hard-case S55 identified — and is the residual after S55's t2p_v2_*
features. v44 has improved to 80%+ pct_opt within these cells, but the
remaining 15-20% mismatch is genuinely hard.

---

## Phase 2 — v54 (rule chain) sweep on two_pair category

To validate the "v54 underperforms v44 on two_pair" claim, a separate
sweep computed `strategy_v52_full_high_only_handler` (the v54 fall-through
target for non-pair non-high-only categories — Rule 19 in v53 is
single-pair-only, so v54 == v52 on two_pair) picks for all 1,338,480
two_pair hands and measured the v54→oracle gap per (hi_pair_rank × cell).
Output: `data/drill_two_pair_v54_per_hand.parquet` +
`data/drill_two_pair_v54_summary.json`.

### Headline finding — v54 leaves $634/1000h MORE two_pair residual than v44

| Metric | v44_dt (ML champion) | v54 (rule chain) | Δ (v54 − v44) |
|---|---:|---:|---:|
| Total two_pair WG residual | **$80.82** | **$715.29** | **+$634.47** |
| Within-cat pct_opt | 82.84% | 44.00% (avg) | −38.84 pp |

**v54 underperforms v44 on two_pair by $634/1000h whole-grid** — nearly
2× the pair v52→v44 gap of $341. The two_pair category is now the
**largest two-track-divergence contributor** in the codebase, exceeding
both pair (post-S68) and high_only.

### Per-hi_pair-rank v54 vs v44 ($/1000h WG)

| hi_pair | n_hands | v44_wg | v54_wg | v54-v44 | v44_pct_opt | v54_pct_opt |
|---:|---:|---:|---:|---:|---:|---:|
| A | 205,920 | $12.70 | $142.39 | **+$129.69** ← peak | 83.2% | 47.6% |
| K | 188,760 | $11.50 | $126.56 | **+$115.05** | 82.8% | 40.9% |
| Q | 171,600 | $7.86 | $126.43 | **+$118.57** | 85.6% | 35.0% |
| J | 154,440 | $8.16 | $85.24 | +$77.08 | 84.0% | 40.4% |
| T | 137,280 | $8.40 | $60.98 | +$52.59 | 82.7% | 45.2% |
| 9 | 120,120 | $7.20 | $46.42 | +$39.22 | 83.1% | 48.5% |
| 8 | 102,960 | $6.28 | $35.72 | +$29.44 | 83.0% | 49.7% |
| 7 | 85,800 | $5.60 | $26.84 | +$21.24 | 82.0% | 49.9% |
| 6 | 68,640 | $5.10 | $22.26 | +$17.16 | 80.3% | 46.7% |
| 5 | 51,480 | $4.03 | $20.38 | +$16.36 | 79.8% | 41.7% |
| 4 | 34,320 | $2.64 | $14.43 | +$11.79 | 80.3% | 40.6% |
| 3 | 17,160 | $1.35 | $7.63 | +$6.29 | 80.6% | 40.0% |
| **TOTAL** | **1,338,480** | **$80.82** | **$715.29** | **+$634.47** | **82.8%** | **44.0%** |

**Two facts emerge:**
1. **v54 loses to v44 at EVERY hi_pair_rank.** No exceptions. (Compare
   pair: v52 beat v44 at pair=3, 4 by $5-11 WG; v54 has no such relief
   here.)
2. **v54's within-cat pct_opt of 44% is dramatically below v44's 83%.**
   The rule chain matches oracle on less than half of two_pair hands.

### Per-cell aggregate v54 vs v44 (across all 12 hi_pair_ranks, $/1000h WG)

| cell | n | v44_wg | v54_wg | v54-v44 | Hypothesis |
|---|---:|---:|---:|---:|---|
| **LAYOUT_A_DS** | 257,400 | $12.13 | $273.53 | **+$261.40** ← largest | v54 picks Layout A on 85% but oracle disagrees on 80% — the v8/v14 era handler doesn't tune A_DS layout selection |
| **LAYOUT_A_SS** | 437,580 | $35.22 | $221.37 | **+$186.15** | The largest cell × big gap = #2 contributor; v54 over-routes to Layout B |
| **LAYOUT_C_DS** | 308,880 | $5.66 | $92.61 | **+$86.95** | C_DS layout favored by oracle but v54 splits B/C 42/54 instead of going C |
| LAYOUT_B_DS | 231,660 | $15.28 | $79.06 | +$63.78 | Smaller relative gap; v54 mostly picks B correctly here |
| LAYOUT_C_SS_ONLY | 90,090 | $12.38 | $41.80 | +$29.42 | Smaller cell |
| LAYOUT_B_SS_ONLY | 12,870 | $0.13 | $6.92 | +$6.78 | Tiny cell |
| **TOTAL** | **1,338,480** | **$80.82** | **$715.29** | **+$634.47** | |

**Crystal-clear pattern: v54 underperforms v44 EVERYWHERE.** Unlike pair
(where PMID cells favored v52 by $50 WG total), two_pair has NO
counter-headroom cells. **A blanket "two_pair → v44" hybrid extension
captures the entire $634 WG with no offsetting losses.**

This is qualitatively different from S68's pair hybrid (which had to
preserve PMID → v53 routing to keep the +$49 WG PMID-cell catch). Here,
the routing logic simplifies to a single binary: "is hand two_pair?
→ route to v44_dt".

### Phase 2 conclusion — Path B hybrid is overwhelmingly favored

The v54→v44 gap on two_pair decomposes by cell as:
- **All cells favor v44** by $7-261 WG. No v54-favoring cell exists.
- **Largest individual cell gap**: LAYOUT_A_DS at $261 WG. This single
  cell is bigger than the entire pair v52→v44 PMID anti-headroom ($50 WG).
- **Per-rank concentration**: top 4 hi_pair_ranks (A, K, Q, J) account
  for $440 of $634 = 69% of the gap.

**This is structurally analogous to the high_only S60-S64 outcome** — v54
is ML-only at catalog granularity. **Catalog rules CANNOT capture this
gap; the headroom is the v44 ML's selective per-hand decisions.** Just
like high_only S60-S64, the dominant lift mechanism here is hybrid
delegation, not catalog rules.

---

## Recommendation for Session 69 Phase 2 / S70 direction

**The two_pair category is ML-only at catalog granularity. The Path B
hybrid ship is overwhelmingly favored. Recommended path:**

### Path B (RECOMMENDED PRIMARY) — v55_two_pair_hybrid: blanket two_pair → v44

**Design (single binary gate):**
> If hand is two_pair (n_pairs == 2 AND n_trips == 0 AND n_quads == 0)
> → route to `strategy_v44_dt`. Else → route to `strategy_v54_pair_hybrid`.

This subsumes v54's pair-routing behavior (since `strategy_v54_pair_hybrid`
is the fall-through, all pair hybrid logic is preserved). The new gate
adds two_pair → v44 routing on top.

**Expected impact (from harness Phase 2 sweep):**
- Within-two_pair full-grid lift: **$634 WG canonical-equal framing**
- This IS the whole-grid lift since canonical-equal already accounts for
  category share (drill formula: `reg * 10 * 1000 / N_TOTAL_GRID`).
- Predicted v55 vs v54 lift: **$634 WG full-grid, ~$300 WG prefix-grid**
  (assuming similar prefix:full ratio as S68's v54: 179 prefix / 382 full
  = 47%).
- Within-two_pair pct_opt: 44% → 83% (+39 pp).
- **NEW PROJECT RECORD:** 1.7× S68's v54 ship of $382.

**Routing implementation simplicity:**
```python
def _is_two_pair(hand_bytes):
    ranks = (hand_bytes // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    return (
        int((rc == 4).sum()) == 0 and
        int((rc == 3).sum()) == 0 and
        int((rc == 2).sum()) == 2
    )

def strategy_v55_two_pair_hybrid(hand):
    if _is_two_pair(hand):
        return strategy_v44_dt(hand)
    return strategy_v54_pair_hybrid(hand)
```

**Routing fire rate:** 22.3% of canonical grid (= two_pair share). Combined
with v54's pair PBOT routing (12.9%), v55 routes ~35% of the grid through
v44_dt.

**Architectural note:** v55 stacks atop v54 cleanly (v54 handles
non-two_pair → v53 → v52 → ...). The two_pair gate is structurally
disjoint from the pair gate, so there's zero risk of conflicting routing.

### Path A (FALLBACK / COMPLEMENTARY) — Catalog rule attempts

For S69 acceptance criteria (3+ candidate verdicts), test ~5 catalog
candidates targeting the largest cells. **Expected outcome: all T3
(ML-only)** based on v54's per-cell pct_opt of 20-50%.

Suggested candidates (priority by cell-WG):
1. **C_T2P_1: Layout-A-DS preference rule** — "if hi_pair_rank ≥ T AND
   LAYOUT_A_DS achievable AND lo_pair_rank ≥ 9 → take Layout A with both
   pairs in bot, top = max sing"
   - Fire region: ~80K hands across hi_pair ∈ {T, J, Q, K, A}
   - Catalog ceiling: $73 WG in the cell, but v44's selectivity within
     the cell suggests <30% capture → likely T3.
2. **C_T2P_2: Layout-C-DS preference for Q-pair-hi** — "if hi_pair_rank=Q
   AND LAYOUT_C_DS achievable → take Layout C, max sing on top, ms_mid"
   - Fire region: ~40K hands.
   - Catalog ceiling: $19 WG; v54 already picks C 54% so the marginal
     capture is small.
3. **C_T2P_3: Anti-Layout-B for A_SS cells** — "if LAYOUT_A_SS AND
   hi_pair_rank ≥ Q → prefer Layout C over Layout B (oracle preference
   pattern)"
   - Fire region: ~150K hands.
   - The B↔C class is structurally hard; rule unlikely to beat v44's
     selective pick.
4. **C_T2P_4: Q-pair-low pair B-routing rule** — narrow rule on
   hi_pair=Q × lo_pair ≤ 5 × LAYOUT_B_DS → take Layout B.
5. **C_T2P_5: 2-pair-low cell (3,4 hi_pair)** — small per-rank lift
   (<$2 WG) but maybe high capture %.

**These candidates are sanity-checks, not ship vehicles.** The expected
ship is v55 hybrid.

### Path C (LOWER PRIORITY) — Trips audit (S70+)

After v55 ships, the remaining residuals are trips ($55 v44, $110 v54),
three_pair ($35), trips_pair ($5). Smaller absolute targets.

### Acceptance summary

**Phase 2 data DECISIVELY supports Path B over Path A.** v54
underperforms v44 by $634/1000h on two_pair, concentrated uniformly
across all cells with no counter-headroom anywhere. The structural-axis
gate (n_pairs == 2 + no trips/quads) is the cleanest catalog routing in
the project: **a blanket two_pair → v44_dt routing should ship at the
predicted $634 WG full-grid lift with ZERO offsetting losses.**

---

## Reusable artifacts

| Artifact | Path | Purpose |
|---|---|---|
| **Phase 1 — v44 sweep** | | |
| Per-hand parquet | `data/drill_two_pair_v44_per_hand_structural.parquet` | 10.4 MB; per-hand structural cell tag + v44/oracle picks. Reusable for Phase 2 catalog harness. |
| Summary JSON | `data/drill_two_pair_v44_summary.json` | 355 KB; aggregate stats keyed by (hi_pair, cell). |
| Sweep log | `data/session69/drill_two_pair_v44_S69.log` | Console output. |
| Sweep script | `analysis/scripts/drill_two_pair_v44_S69.py` | Two_pair-specific deep-dive; mirrors `drill_pair_v44_S66.py`. |
| **Phase 2 — v54 sweep** | | |
| v54 per-hand parquet | `data/drill_two_pair_v54_per_hand.parquet` | per-hand v54_idx + regret. |
| v54 summary JSON | `data/drill_two_pair_v54_summary.json` | per-(hi_pair, cell) aggregates with v54-v44 deltas. |
| v54 sweep script | `analysis/scripts/sweep_v54_on_two_pair_S69.py` | Reads two_pair parquet, computes v54 picks, aggregates by (hi_pair, cell). |
| Cell taxonomy | This document | 7-cell two_pair-specific scheme. Reused by any Phase 3 audit. |

---

## Threshold definitions (reused from S60-S68)

| Threshold | Definition | Use |
|---|---|---|
| **T1 (Catalog-worthy)** | ≥ 40% gap closure within cell AND ≥ +$3/1000h within-cell AND one-sentence statable | Identifies candidates that "really fit" the cell |
| **T2 (Production ship)** | T1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression | Production-shipping gate |
| **T3 (ML-only)** | No candidate clears T1 | Formal "this cell is ML-only at catalog granularity" verdict |

These thresholds apply unchanged to the two_pair Phase 2/3 audit.

---

*This document is the Session 69 Phase 1+2 deliverable. The cell-by-cell
descriptive matrix per hi_pair_rank is canonical; cross-cutting
observations are value-added synthesis. Phase 3 (candidate sweep + v55
hybrid build + grade) is the next S69 step — see Recommendation above.*
