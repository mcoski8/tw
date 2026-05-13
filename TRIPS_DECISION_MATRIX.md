# Session 70 Phase 1+2 — Trips Decision Matrix (Oracle vs v44_dt + v55 audit)

*Generated 2026-05-12. Mirrors `TWO_PAIR_DECISION_MATRIX.md` (S69) and
`PAIR_DECISION_MATRIX.md` (S66) for the trips category (cat=3,
n=328,185 canonical hands = 5.46% of canonical-grid). Answers: "for every
(trip_rank × structural cell), what does oracle pick (layout, top, bot
suit), where does v44_dt diverge, and where does v55 (= v54 = v52 on
trips, since neither v55's two_pair gate nor v54's pair gate fires on
trips) leave catalog-shippable headroom?"*

**KEY FINDING (Phase 2):** v55 leaves **$44.61/1000h WG** more trips
residual than v44 (canonical-equal framing) — concentrated in
**B_DS_AVAIL_LKR** ($25.50 WG = 57% of gap) and **NO_BDS_AKDOM** ($15.57
WG = 35% of gap), with negligible counter-headroom of $0.75 WG at
B_DS_AVAIL_HKR (low trip_ranks 3,4,T,J,K). **A blanket Path-B hybrid
extension ("if trips → v44_dt") would predict a $44 WG whole-grid
full-grid ship — ~1/14th of S69's $634 record** (smaller because trips
is 5.5% of grid vs two_pair's 22.3%, AND v55's within-cat gap is much
smaller).

---

## TL;DR — what the data says (one sentence per trip_rank, sorted by trip_rank desc)

| trip | v44 WG | v55 WG | v55-v44 | n | Headline |
|---:|---:|---:|---:|---:|---|
| A | $2.07 | $3.52 | **+$1.46** | 25,245 | v55 picks C-layout 100% across cells; v44 picks A; oracle picks A:92% — v55 over-routes to C |
| K | $4.33 | $7.14 | **+$2.81** | 25,245 | Mixed A/C routing in v55 (57/43 in HKR, 73/27 in LKR); v44 stays on A — large within-A bot-suit lift |
| Q | $5.83 | $11.49 | **+$5.66** | 25,245 | Q-trips Q B_DS_AVAIL_LKR is largest absolute v55→v44 cell gap ($4.12 WG) |
| J | $6.16 | $11.60 | **+$5.44** | 25,245 | J B_DS_AVAIL_LKR contributes $3.95 WG (2nd largest cell) |
| T | $5.22 | $9.43 | **+$4.21** | 25,245 | T B_DS_AVAIL_LKR contributes $2.62 WG |
| 9 | $4.64 | $8.04 | **+$3.40** | 25,245 | |
| 8 | $4.72 | $7.65 | **+$2.93** | 25,245 | |
| 7 | $4.84 | $7.89 | **+$3.05** | 25,245 | |
| 6 | $4.39 | $7.72 | **+$3.33** | 25,245 | |
| 5 | $4.22 | $8.14 | **+$3.92** | 25,245 | |
| 4 | $6.82 | $8.52 | **+$1.70** | 25,245 | v55 BEATS v44 at B_DS_AVAIL_HKR by $0.50 (counter-headroom) |
| 3 | $6.93 | $8.90 | **+$1.97** | 25,245 | v55 BEATS v44 at B_DS_AVAIL_HKR by $0.18 |
| 2 | $5.01 | $9.74 | **+$4.73** | 25,245 | No counter-headroom; uniformly v44 wins |
| **TOTAL** | **$65.18** | **$109.79** | **+$44.61** | **328,185** | **$44 WG full-grid whole-grid harness-predicted lift** |

**Headline single sentence:** v55 (= v52 = v8/v14 era rule chain on
trips) leaks $44.61 WG vs v44_dt in canonical-equal framing — concentrated
57% in B_DS_AVAIL_LKR and 35% in NO_BDS_AKDOM, with tiny ($0.75 WG)
counter-headroom at B_DS_AVAIL_HKR for trip_ranks {K,J,T,4,3}. **The Path
B hybrid extension ("trips → v44") would predict $44 WG full-grid lift —
14× smaller than S69's ship and likely a single-ship cell-wise rule
alternative also exists.**

---

## Method

* **Data:** All 328,185 canonical trips hands (cat=3), graded against
  `oracle_grid_full_realistic_n200.bin` (the realistic 70/25/5 mixture
  profile, S24 artifact).
* **Per-trip-rank stratification:** 2 through A (13 ranks). 25,245
  canonical hands per rank (uniform — canonical symmetry across ranks
  for trips).
* **Structural cell:** 4 mutually-exclusive cells per trip_rank (the
  taxonomy is **trips-specific** and is informed by v44's existing
  `trips_*_g` and `trips_v2_*_g` feature families from S36):
  * `B_DS_AVAIL_HKR` — B-DS layout achievable AND best B-DS bot's
    2nd-rank in-trip-suit kicker ≥ T (broadway anchor for B routing).
  * `B_DS_AVAIL_LKR` — B-DS achievable AND best 2nd-kicker < T (mid/low
    anchor).
  * `NO_BDS_CTOP` — B-DS NOT achievable AND trip_rank > max_kicker_rank
    (C-top advantage cell — C layout's top trumps all kickers).
  * `NO_BDS_AKDOM` — B-DS NOT achievable AND max_kicker_rank ≥ trip_rank
    (A's top is competitive — kicker outranks trip).
* **Cell population is canonical-symmetric for ranks 9 and below:**
  - **High ranks (A, K, Q, J, T):** all 4 cells populated (NO_BDS_CTOP
    distribution varies with trip_rank).
  - **Mid ranks (9, 8, 7, 6):** NO_BDS_CTOP shrinks dramatically (60..16
    hands).
  - **Low ranks (5, 4, 3, 2):** NO_BDS_CTOP is empty (trip_rank cannot
    exceed all 4 kickers when trip ≤ 5; max_kicker ≥ 6 always).
  Across all ranks the cell ratios converge to roughly: HKR ≈ 18.9%, LKR
  ≈ 49.7%, NO_BDS_AKDOM ≈ 25.1%, NO_BDS_CTOP ≈ 6.3%.

* **Oracle/v44/v55 pick classification:**
  * `layout`: A_paired_mid / B_paired_bot / C_top_trip / SPLIT
    (A: top=kicker, mid=2 trips, bot=1 trip + 3 kickers;
    B: bot=2 trips + 2 kickers;
    C: top=trip, mid=2 trips, bot=4 kickers;
    SPLIT: otherwise — rare)
  * `bot_suit`: DS / SS / 31 / RB / 4f
  * `top_type`: TRIP / KICKER_MAX / KICKER_MID / KICKER_LOW
  * Compact label: e.g. `A_DS_tkmax`, `B_DS_ttrip`, `C_RB_ttrip`

---

## Big-picture aggregates

### Per-trip-rank residual (v44_dt vs oracle, canonical-equal weighting)

| trip | n_hands | v44 pct_opt | v44 mean_regret ($/hand) | v44 $/1000h WG |
|---:|---:|---:|---:|---:|
| A | 25,245 | 53.26% | $492.5 | $2.07 |
| K | 25,245 | 50.60% | $1,030.6 | $4.33 |
| Q | 25,245 | 50.54% | $1,388.1 | $5.83 |
| J | 25,245 | 52.66% | $1,465.5 | $6.16 |
| T | 25,245 | 57.95% | $1,242.3 | $5.22 |
| 9 | 25,245 | 60.39% | $1,103.8 | $4.64 |
| 8 | 25,245 | 60.42% | $1,124.0 | $4.72 |
| 7 | 25,245 | 59.41% | $1,152.0 | $4.84 |
| 6 | 25,245 | 61.69% | $1,045.1 | $4.39 |
| 5 | 25,245 | 63.46% | $1,005.2 | $4.22 |
| 4 | 25,245 | 54.63% | $1,623.2 | $6.82 |
| 3 | 25,245 | 55.76% | $1,650.3 | $6.93 |
| 2 | 25,245 | 61.22% | $1,193.6 | $5.01 |
| **TOTAL** | **328,185** | **57.07%** | **$1,194** | **$65.18** |

v44 pct_opt of 50-63% per trip_rank is intermediate between two_pair
(82%+) and pair (60-72%). The trips residual is dominated by
within-Layout-A bot-suit selection errors (A_31 vs A_SS vs A_DS),
not by gross layout mistakes.

### Cell-residual cross-tab (v44 vs oracle, $/1000h whole-grid by canonical-equal)

| trip | B_DS_AVAIL_HKR | B_DS_AVAIL_LKR | NO_BDS_CTOP | NO_BDS_AKDOM | TOTAL |
|---:|---:|---:|---:|---:|---:|
| A | $0.36 | $1.50 | $0.20 | — | $2.07 |
| K | $0.89 | $3.00 | $0.26 | $0.18 | $4.33 |
| Q | $1.20 | $3.93 | $0.33 | $0.38 | $5.83 |
| J | $1.09 | $4.41 | $0.25 | $0.40 | $6.16 |
| T | $0.88 | $3.90 | $0.11 | $0.33 | $5.22 |
| 9 | $1.24 | $3.04 | $0.05 | $0.31 | $4.64 |
| 8 | $1.39 | $2.95 | $0.01 | $0.37 | $4.72 |
| 7 | $1.55 | $2.88 | $0.00 | $0.41 | $4.84 |
| 6 | $1.22 | $2.87 | $0.00 | $0.31 | $4.39 |
| 5 | $1.21 | $2.76 | — | $0.25 | $4.22 |
| 4 | $2.19 | $3.97 | — | $0.66 | $6.82 |
| 3 | $2.02 | $4.28 | — | $0.63 | $6.93 |
| 2 | $1.61 | $3.12 | — | $0.28 | $5.01 |
| **TOTAL** | **$16.85** | **$42.61** | **$1.21** | **$4.52** | **$65.18** |

**Cell totals (within-v44):**
- **B_DS_AVAIL_LKR: $42.61 (65.4%)** ← largest absolute cell; the
  "B-DS feasible but kicker quality mediocre" decision.
- B_DS_AVAIL_HKR: $16.85 (25.8%)
- NO_BDS_AKDOM: $4.52 (6.9%)
- NO_BDS_CTOP: $1.21 (1.9%) — v44 nearly perfect here at low ranks.

### Top mismatch patterns per trip_rank

The dominant mismatch class is **`A_31_tkmax → A_DS_tkmax`** (= v44
picks Layout-A with 3-1 bot suit, oracle picks Layout-A with DS bot —
within-A bot-suit selection error). Variants `A_SS_tkmax → A_DS_tkmax`
and `A_SS_tkmax → A_DS_tkmid` also appear. **All major mismatches are
within-A-layout**; oracle and v44 mostly agree on Layout A.

| trip | dominant mismatch | n | mean ($/hand) | WG | Description |
|---:|---|---:|---:|---:|---|
| A | `C_SS_ttrip → B_DS_ttrip` | 1,119 | $2,811 | $0.52 | C/B routing conflict on top trip rank (rare; trips=A is special) |
| K | `A_31_tkmax → A_DS_tkmax` | (top) | — | $0.85 | Within-A bot-suit selection |
| Q | `A_31_tkmax → A_DS_tkmax` | (top) | — | $0.85 | Within-A bot-suit selection |
| ... | `A_31_tkmax → A_DS_tkmax` is the dominant mismatch class across all ranks 2-T |

**The within-A bot-suit class alone accounts for the bulk of v44's
trips residual.** v44 has improved trips substantially via the
`trips_b_ds_*_g` features (S36) but the remaining 15-20% mismatch in
B_DS_AVAIL cells is genuinely hard — picking the BEST DS-bot configuration
when several singleton kickers could complete it.

---

## Phase 2 — v55 (rule chain) sweep on trips category

To validate the "v55 underperforms v44 on trips" claim, a separate
sweep computed `strategy_v55_two_pair_hybrid` picks for all 328,185
trips hands. For trips, v55 falls through (its two_pair gate doesn't
fire) to v54 (whose pair gate doesn't fire), to v53 (whose Rule 19 is
single-pair-only), to v52 — so v55 == v52 on trips. Output:
`data/drill_trips_v55_per_hand.parquet` +
`data/drill_trips_v55_summary.json`.

### Headline finding — v55 leaves $44.61/1000h MORE trips residual than v44

| Metric | v44_dt (ML champion) | v55 (rule chain) | Δ (v55 − v44) |
|---|---:|---:|---:|
| Total trips WG residual | **$65.18** | **$109.79** | **+$44.61** |
| Within-cat pct_opt | 57.07% | 36.71% (avg) | −20.36 pp |

**v55 underperforms v44 on trips by $44.61/1000h whole-grid** — much
smaller than the pair v52→v44 gap of $341 or two_pair's $634 WG, but
still ML-only-dominant.

### Per-trip-rank v55 vs v44 ($/1000h WG)

| trip | n_hands | v44_wg | v55_wg | v55-v44 | v55_pct_opt |
|---:|---:|---:|---:|---:|---:|
| A | 25,245 | $2.07 | $3.52 | **+$1.46** | 39.5% |
| K | 25,245 | $4.33 | $7.14 | **+$2.81** | 32.1% |
| Q | 25,245 | $5.83 | $11.49 | **+$5.66** | 28.5% |
| J | 25,245 | $6.16 | $11.60 | **+$5.44** | 32.7% |
| T | 25,245 | $5.22 | $9.43 | **+$4.21** | 38.2% |
| 9 | 25,245 | $4.64 | $8.04 | **+$3.40** | 41.5% |
| 8 | 25,245 | $4.72 | $7.65 | **+$2.93** | 43.4% |
| 7 | 25,245 | $4.84 | $7.89 | **+$3.05** | 41.5% |
| 6 | 25,245 | $4.39 | $7.72 | **+$3.33** | 41.5% |
| 5 | 25,245 | $4.22 | $8.14 | **+$3.92** | 39.6% |
| 4 | 25,245 | $6.82 | $8.52 | **+$1.70** | 39.5% |
| 3 | 25,245 | $6.93 | $8.90 | **+$1.97** | 39.6% |
| 2 | 25,245 | $5.01 | $9.74 | **+$4.73** | 37.6% |
| **TOTAL** | **328,185** | **$65.18** | **$109.79** | **+$44.61** | **36.7%** |

**v55 loses to v44 at EVERY trip_rank overall.** Within-cell exceptions
exist (see counter-headroom below), but at the rank-aggregate level
v55 is uniformly worse.

### Per-cell aggregate v55 vs v44 (across all 13 trip_ranks, $/1000h WG)

| cell | n | v44_wg | v55_wg | v55-v44 | Hypothesis |
|---|---:|---:|---:|---:|---|
| **B_DS_AVAIL_LKR** | 163,170 | $42.61 | $68.11 | **+$25.50** ← largest | v55 picks SS bot 56% (oracle prefers DS 70%); v55 over-picks SS-bot under B-DS feasibility |
| **NO_BDS_AKDOM** | 82,368 | $4.52 | $20.09 | **+$15.57** | v55 picks SS:38% / DS:38% / 31:25% (oracle DS:52% / 31:28%); v55's bot-suit distribution is misaligned |
| **NO_BDS_CTOP** | 20,592 | $1.21 | $3.91 | **+$2.70** | Small cell; v55 picks C:100% with 31:50%/DS:38% (oracle agrees C-layout but picks DS more) |
| **B_DS_AVAIL_HKR** | 62,055 | $16.85 | $17.69 | **+$0.84** | v55 nearly EQUALS v44 (gap is 5% of within-cell); v55 has tiny counter-headroom at low trip_ranks |
| **TOTAL** | **328,185** | **$65.18** | **$109.79** | **+$44.61** | |

**Crystal-clear pattern: v55 underperforms v44 EVERYWHERE at the cell
aggregate.** Counter-headroom at the cell level is $0.84 WG (B_DS_AVAIL_HKR)
which is dominated by the $43+ WG that v55 loses in other cells. **A
blanket "trips → v44" hybrid extension captures $44.61 WG with only
$0.75 WG of within-cell offsetting losses** (at trip_ranks {K,J,T,4,3}
× B_DS_AVAIL_HKR).

### Per-cell × trip-rank counter-headroom audit (cells where v55 < v44)

| trip | cell | v44_wg | v55_wg | v55-v44 |
|---:|---|---:|---:|---:|
| K | B_DS_AVAIL_HKR | $0.89 | $0.89 | **−$0.00** ← tied |
| J | B_DS_AVAIL_HKR | $1.09 | $1.04 | **−$0.05** |
| T | B_DS_AVAIL_HKR | $0.88 | $0.85 | **−$0.02** |
| 4 | B_DS_AVAIL_HKR | $2.19 | $1.68 | **−$0.50** ← largest |
| 3 | B_DS_AVAIL_HKR | $2.02 | $1.84 | **−$0.18** |
| **TOTAL counter** | | **$7.07** | **$6.31** | **−$0.75** |

The B_DS_AVAIL_HKR counter-headroom is real but tiny — $0.75 WG total,
1.7% of the v55→v44 gap. A blanket hybrid forfeits this $0.75 in exchange
for the $44.61. **Net gain: +$43.86 WG** if blanket; selective hybrid
(retain v55 on the 5 counter-headroom cells) could recover the $0.75
at the cost of gate complexity.

### Phase 2 conclusion — Path B hybrid is favored, but at smaller scale than S69

The v55→v44 gap on trips decomposes as:
- **All 4 cells favor v44** at the aggregate.
- **B_DS_AVAIL_LKR contributes 57%** of the gap, NO_BDS_AKDOM 35%.
- **Cells favoring v55 at trip-rank granularity**: 5 cells totaling $0.75 WG (1.7% of gap). Concentrated in B_DS_AVAIL_HKR at low/mid trip_ranks.

**This is structurally similar to S69 two_pair** — v55 is ML-only at
catalog granularity. Catalog rules CANNOT capture this gap; the headroom
is v44's selective per-hand decisions on within-A bot-suit selection.

**Per S69 methodology lesson: always test "lift vs v44" alongside
"lift vs baseline".** Any catalog candidate that ships against v55
baseline but loses to v44 is dominated by the hybrid extension.

---

## Recommendation for Session 70 Phase 3

**The trips category is ML-only at catalog granularity. The Path B
hybrid ship is favored, though smaller in absolute terms than S68/S69.**

### Path B (RECOMMENDED PRIMARY) — v56_trips_hybrid: blanket trips → v44

**Design (single binary gate):**
> If hand is trips (exactly_one_trip AND n_pairs == 0 AND n_quads == 0)
> → route to `strategy_v44_dt`. Else → route to
> `strategy_v55_two_pair_hybrid`.

This subsumes v55's full behavior (since `strategy_v55_two_pair_hybrid`
remains the fall-through, all two_pair + pair hybrid logic is preserved).
The new gate adds trips → v44 routing on top.

**Expected impact (from harness Phase 2 sweep):**
- Within-trips full-grid lift: **$44.61 WG canonical-equal framing**
  (predicted, blanket). Selective could recover ~$0.75 more.
- This IS the whole-grid lift since canonical-equal already accounts for
  category share.
- Predicted v56 vs v55 lift: **$44 WG full-grid, ~$20 WG prefix-grid**
  (assuming similar prefix:full ratio as S68/S69: ~47%).
- Within-trips pct_opt: 36.7% → 57.1% (+20.4 pp).
- **NOT a new project record** — but cleanly extends the methodology
  arc to the smallest remaining residual category. After this ship,
  trips joins high_only/pair/two_pair as CLOSED.

**Routing implementation simplicity:**
```python
def _is_trips(hand_bytes):
    ranks = (hand_bytes // 4) + 2
    rc = np.bincount(ranks, minlength=15)
    return (
        int((rc == 4).sum()) == 0 and
        int((rc == 3).sum()) == 1 and
        int((rc == 2).sum()) == 0
    )

def strategy_v56_trips_hybrid(hand):
    if _is_trips(hand):
        return strategy_v44_dt(hand)
    return strategy_v55_two_pair_hybrid(hand)
```

**Routing fire rate:** 5.46% of canonical grid (= trips share). Combined
with v55's two_pair (22.3%) and pair PBOT (12.9%), v56 routes ~40% of
the grid through v44_dt.

**Architectural note:** v56 stacks atop v55 cleanly. v55 handles
two_pair → v44. v54 handles pair PBOT → v44. v56 adds trips → v44.
Three gates structurally disjoint (different rank-count signatures);
zero conflict risk.

### Path A (FALLBACK / COMPLEMENTARY) — Catalog rule attempts

For S70 acceptance criteria (3+ candidate verdicts), test ~3-5 catalog
candidates targeting B_DS_AVAIL_LKR (the largest cell at $25.50 WG gap)
and NO_BDS_AKDOM ($15.57 WG gap). **Expected outcome: most T3
(ML-only)** based on within-A bot-suit selectivity that's hard to
encode as a deterministic rule.

Suggested candidates (priority by cell-WG):
1. **C_TR_1: "Prefer A-DS bot when B_DS available and best DS bot is
   top-anchored"** — target B_DS_AVAIL_LKR + B_DS_AVAIL_HKR. Rule: in
   trips with B-DS feasible AND max kicker (DS-pair kicker) ≥ Q AND
   trip_rank ≥ T → take Layout A with the DS-bot configuration.
   - Cell ceiling (B_DS_AVAIL): ~$25 WG combined; v44 captures ~70%
     within this cell, so catalog ceiling is ~$8 WG max.
2. **C_TR_2: "Prefer A-DS bot in NO_BDS_AKDOM with high max kicker"** —
   target NO_BDS_AKDOM at high trip_ranks. Likely T3 (v55 already picks
   A:100% — the question is bot-suit selectivity, which is the
   ML-residual).
3. **C_TR_3: "Top to be max kicker for trip_rank ≤ T AND max_kicker ≥ Q"**
   — narrow rule targeting v55's TOP_TYPE distribution leak (v55 picks
   KICKER_MID:14% where oracle picks KICKER_MAX more).

These candidates are sanity-checks. The expected ship is v56 hybrid.

### Path C (LOWER PRIORITY) — ML retrain v45_dt+

After v56 ships, the residuals are three_pair ($32 WG), trips_pair ($5
WG, already collapsed S55a), composite + quads (negligible). At this
point, ML retrain to reduce v44's residuals further is the natural next
direction. Given hybrids now route ~40% of grid through v44, any v44
improvement compounds across hybrids.

### Acceptance summary

**Phase 2 data supports Path B with the smallest ship of the methodology
arc.** v55 underperforms v44 by $44.61/1000h on trips, concentrated in
B_DS_AVAIL_LKR (57%) and NO_BDS_AKDOM (35%). Counter-headroom is $0.75
WG (1.7%) at B_DS_AVAIL_HKR for ranks {K,J,T,4,3}. **A blanket trips →
v44_dt routing should ship at the predicted $44 WG full-grid lift with
$0.75 WG offsetting losses.**

---

## Reusable artifacts

| Artifact | Path | Purpose |
|---|---|---|
| **Phase 1 — v44 sweep** | | |
| Per-hand parquet | `data/drill_trips_v44_per_hand_structural.parquet` | 2.83 MB; per-hand structural cell tag + v44/oracle picks. |
| Summary JSON | `data/drill_trips_v44_summary.json` | 224 KB; aggregate stats keyed by (trip_rank, cell). |
| Sweep log | `data/session70/drill_trips_v44_S70.log` | Console output. |
| Sweep script | `analysis/scripts/drill_trips_v44_S70.py` | Trips-specific deep-dive; mirrors `drill_two_pair_v44_S69.py`. |
| **Phase 2 — v55 sweep** | | |
| v55 per-hand parquet | `data/drill_trips_v55_per_hand.parquet` | 1.78 MB; per-hand v55_idx + regret. |
| v55 summary JSON | `data/drill_trips_v55_summary.json` | 32 KB; per-(trip_rank, cell) aggregates with v55-v44 deltas. |
| v55 sweep script | `analysis/scripts/sweep_v55_on_trips_S70.py` | Reads trips parquet, computes v55 picks, aggregates by (trip_rank, cell). |
| Cell taxonomy | This document | 4-cell trips-specific scheme. Reused by any Phase 3 audit. |

---

## Threshold definitions (reused from S60-S69)

| Threshold | Definition | Use |
|---|---|---|
| **T1 (Catalog-worthy)** | ≥ 40% gap closure within cell AND ≥ +$3/1000h within-cell AND one-sentence statable | Identifies candidates that "really fit" the cell |
| **T2 (Production ship)** | T1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression | Production-shipping gate |
| **T3 (ML-only)** | No candidate clears T1 | Formal "this cell is ML-only at catalog granularity" verdict |

These thresholds apply unchanged to the trips Phase 3 audit.

**S69 lesson reinforced:** A T2 verdict against the v55 baseline is
**not** sufficient evidence to ship a rule when the hybrid option exists.
Always also test "lift vs v44" — if negative, the candidate is dominated.

---

*This document is the Session 70 Phase 1+2 deliverable. The cell-by-cell
descriptive matrix per trip_rank is canonical; cross-cutting
observations are value-added synthesis. Phase 3 (candidate sweep + v56
hybrid build + grade) is the next S70 step — see Recommendation above.*
