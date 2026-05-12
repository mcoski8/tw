# Session 66 Phase 1+2 — Pair Decision Matrix (Oracle vs v44_dt + v52 audit)

*Generated 2026-05-12. Mirrors `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` for the pair category (cat=1, n=2,800,512 canonical hands = 46.6% of canonical-grid). Answers: "for every (pair_rank × structural cell), what does oracle pick (placement, top, bot, mid), where does v44_dt diverge, and where does v52 (the production rule chain) leave catalog-shippable headroom?" Phase 1 builds the descriptive oracle/v44 matrix; Phase 2 adds the v52 sweep and rule-coverage audit; Phase 3 candidate work is deferred to S67+.*

**KEY FINDING (Phase 2):** v52 leaves $341/1000h WG more pair residual than v44, concentrated entirely in PBOT cells ($391 WG gap) where six pair_ranks (A, K, 6, 7, 8, 9) have ZERO PBOT routing. See "Phase 2" section below for catalog-shippable rule candidates worth $30-90/1000h WG each.

---

## TL;DR — what the data says (one sentence per pair_rank, sorted by within-cat WG residual)

| pair_rank | WG residual ($/1000h) | Oracle's headline behavior | v44's biggest miss |
|---:|---:|---|---|
| **3** | **$70.28** ← peak | **Keep pair in mid 70%; PMID's PBOT under-routing accounts for residual; v44 SPLIT-mistake costs $5.16/1000h alone** | **`SPLIT_tmax_SS_mu → PMID_tmax_DS`** $5.16/1000h (v44 splits low pair into top+other; oracle keeps pair-in-mid + DS bot) |
| **4** | **$68.08** | Same pattern as 3 (PMID 68%, oracle prefers PMID-with-DS-bot) | **`SPLIT_tmax_SS_mu → PMID_tmax_SS`** $3.53/1000h (same SPLIT error class) |
| **7** | **$51.61** | PMID 78%; v44 over-PMIDs on the 22% where oracle moves to PBOT | `SPLIT_tmax_SS_mu → PMID_tmax_DS` $3.20/1000h + `PMID_tnomax_SS → PMID_tnomax_DS` $2.85/1000h |
| **8** | **$39.20** | PMID 81% (oracle keeps pair in mid most of the time at 8-pair) | `PMID_tmax_SS → PMID_tnomax_DS` $3.60/1000h (drop max off top + upgrade bot SS→DS) |
| **Q** | **$38.07** | **PBOT 53%** ← flip; oracle moves Q-pair to BOT more often than not | `PMID_tmax_SS → PBOT_tmax_SS_ms` $3.04/1000h (v44 keeps Q in mid; oracle moves to bot with ms_mid) |
| **J** | **$37.84** | PBOT 49% (near tie); oracle splits 50/50 on pair-to-bot | `PMID_tmax_SS → PBOT_tmax_SS_ms` $3.53/1000h (largest PBOT-under-route mismatch across all ranks) |
| **K** | **$33.09** | PMID 63%; oracle does PBOT on 37% of K-pair | `PMID_tmax_SS → PMID_tnomax_DS` $2.44 + `PMID_tmax_SS → PBOT_tmax_SS_ms` $2.38 (tied) |
| **5** | **$31.58** | PMID 65%; same drop-max-off-top + bot upgrade pattern | `PMID_tnomax_SS → PMID_tnomax_DS` $2.63/1000h |
| **T** | **$30.71** | PMID 68%; oracle drops max off top + DS bot upgrade dominates | `PMID_tmax_SS → PMID_tnomax_DS` $2.98/1000h |
| **6** | **$30.24** | PMID 71%; same pattern | `PMID_tmax_SS → PMID_tnomax_DS` $3.07 + `PMID_tnomax_SS → PMID_tnomax_DS` $3.06 |
| **2** | **$29.77** | PMID 65%; same pattern, slightly more PBOT (34%) | `PMID_tmax_SS → PMID_tnomax_DS` $2.60/1000h |
| **9** | **$26.48** | PMID 78%; oracle does drop-max-defensive on PMID variant | `PMID_tmax_SS → PMID_tnomax_DS` $3.64/1000h |
| **A** | **$24.21** ← lowest | PMID 82% (highest oracle PMID rate); drop-max-defensive within PMID is the leak | `PMID_tmax_SS → PMID_tnomax_DS` $3.76/1000h |

**Headline single sentence:** Oracle's pair-placement preference is **non-monotonic in pair_rank** — PMID dominates at A (82%) and 9-pair (78%), drops to a 47% MINIMUM at Q-pair (where oracle PBOTS 53%), and partially recovers at low pairs (68% PMID at 3-pair). v44_dt systematically under-routes to PBOT (= pair-to-bot DS plays) at mid pairs (Q/J/T/K) by 7–11%, AND simultaneously over-picks SPLIT (1-pair-on-top) at low pairs (3, 4) where oracle near-never splits. **The two largest absolute residuals (pair=3 $70 and pair=4 $68) are dominated by v44's SPLIT mistakes — $20K+/hand mean regret on a small population.**

---

## Method

* **Data:** All 2,800,512 canonical pair hands (cat=1), graded against `oracle_grid_full_realistic_n200.bin` (the realistic 70/25/5 mixture profile, Session 24 artifact).
* **Per-pair-rank stratification:** 2 through A (13 ranks). Each pair_rank has exactly 215,424 canonical hands.
* **Structural cell:** 6 mutually-exclusive cells per pair_rank. The taxonomy is **pair-specific** (S58's 6 cells assume 7 distinct ranks and are not applicable):
  * `PBOT_DS_JOINT` — pair-to-bot DS achievable AND ms_mid achievable AND max non-pair singleton on top achievable (the "joint pair-to-bot": pair+kickers in bot, ms_mid from 2 remaining singletons, max sing on top)
  * `PBOT_DS_PARTIAL` — pair-to-bot DS achievable but no ms_mid+maxtop combo
  * `PMID_DS_MAXTOP` — Not PBOT_DS AND PMID + DS bot from singletons + max sing on top achievable
  * `PMID_DS_NOMAXTOP` — Not PBOT_DS AND PMID DS achievable only with max sing in bot
  * `PMID_SS_MAXTOP` — Not PBOT_DS AND no PMID DS AND PMID + SS bot + max sing on top achievable
  * `PMID_OTHER` — None of the above (PMID with only 31/RB/4f bot achievable)
* **Cell population is canonical-symmetric:** every pair_rank has the same cell distribution (the cell axis depends on singleton suit patterns, which are pair-rank-independent at the canonical level):
  * PBOT_DS_JOINT: 28,512 (13.2%) · PBOT_DS_PARTIAL: 90,288 (41.9%) · PMID_DS_MAXTOP: 21,384 (9.9%) · PMID_DS_NOMAXTOP: 38,016 (17.6%) · PMID_SS_MAXTOP: 14,256 (6.6%) · PMID_OTHER: 22,968 (10.7%)
* **Oracle pick classification:**
  * `pair_placement` — PMID (both pair cards in mid) / PBOT (both in bot) / SPLIT (pair split across two tiers)
  * `top_type` — PAIR (top is a pair card) / SING_MAX (top is the max non-pair singleton) / SING_NOMAX (top is a non-max singleton)
  * `bot_suit_profile` — DS / SS / 31 / RB / 4f
  * `mid_suited` — bool (NOTE: PMID picks always `mid_suited=False` since the two pair cards have different suits by construction)
  * Compact label: e.g. `PMID_tmax_SS`, `PBOT_tmax_DS_ms`, `SPLIT_tmax_SS_mu`

---

## Big-picture aggregates

### Per-pair-rank residual (v44_dt vs oracle, canonical-equal weighting)

| pair_rank | n_hands | pct_opt | mean_regret ($/hand) | $/1000h whole-grid |
|---:|---:|---:|---:|---:|
| A | 215,424 | 71.98% | $675.3 | $24.21 |
| K | 215,424 | 65.55% | $923.0 | $33.09 |
| Q | 215,424 | 61.62% | $1,061.9 | $38.07 |
| J | 215,424 | 61.59% | $1,055.5 | $37.84 |
| T | 215,424 | 66.98% | $856.6 | $30.71 |
| 9 | 215,424 | 70.28% | $738.7 | $26.48 |
| 8 | 215,424 | 67.73% | $1,093.5 | $39.20 |
| 7 | 215,424 | 64.35% | $1,439.7 | $51.61 |
| 6 | 215,424 | 66.94% | $843.7 | $30.24 |
| 5 | 215,424 | 66.09% | $880.9 | $31.58 |
| **4** | **215,424** | **60.43%** | **$1,899.1** | **$68.08** |
| **3** | **215,424** | **60.25%** | **$1,960.4** | **$70.28** ← peak |
| 2 | 215,424 | 66.99% | $830.3 | $29.77 |
| **TOTAL** | **2,800,512** | **65.55%** | **$1,103** | **$511.16** |

The catalog framing (canonical-equal) gives **$511/1000h WG** for pair v44→oracle. This differs from CURRENT_PHASE's quoted **$396** because CURRENT_PHASE uses a different weighting (36.2% "share" instead of 46.6% canonical-population share); the two framings agree to the same multiplier convention used by HIGH_ONLY_RULE_CATALOG.md ($615 catalog framing vs $755 CURRENT_PHASE framing for high_only). **Both numbers measure the same gap; only the per-1000h scale differs.**

The peak at pair=3,4 — $138 WG combined, 27% of the pair WG residual concentrated on 15% of the pair population — is the biggest finding of this matrix. The mean-regret-per-hand at pair=3,4 ($1,900+) is nearly 3× any other pair_rank.

### Oracle pick distribution per pair_rank (placement, across all cells)

| pair_rank | or_PMID | or_PBOT | or_SPLIT | v44_PMID | v44_PBOT | v44_SPLIT | placement Δ vs oracle |
|---:|---:|---:|---:|---:|---:|---:|---|
| A | 82.2% | 17.8% | 0.0% | 88.5% | 11.5% | 0.0% | +6.3 PMID |
| K | 62.9% | 37.1% | 0.0% | 71.3% | 28.7% | 0.0% | +8.4 PMID |
| **Q** | **46.8%** | **53.2%** ← peak | 0.0% | 53.6% | 46.4% | 0.0% | +6.8 PMID (under-PBOT) |
| J | 50.6% | 49.4% | 0.0% | 61.1% | 38.9% | 0.0% | +10.5 PMID (under-PBOT) |
| T | 67.6% | 32.4% | 0.0% | 78.9% | 21.1% | 0.0% | +11.3 PMID |
| 9 | 77.6% | 22.4% | 0.0% | 86.6% | 13.4% | 0.0% | +9.0 PMID |
| 8 | 80.7% | 19.3% | 0.0% | 84.3% | 14.5% | 1.1% | +3.6 PMID |
| 7 | 78.2% | 21.7% | 0.0% | 77.9% | 20.2% | 1.9% | −0.3 PMID (+1.9 SPLIT) |
| 6 | 70.8% | 29.1% | 0.1% | 80.1% | 19.8% | 0.0% | +9.3 PMID |
| 5 | 65.0% | 34.7% | 0.3% | 74.6% | 25.3% | 0.1% | +9.6 PMID |
| **4** | **68.4%** | 31.1% | 0.4% | 62.1% | 33.7% | **4.2%** | **−6.3 PMID, +3.8 SPLIT** |
| **3** | **69.6%** | 29.7% | 0.7% | 62.6% | 33.0% | **4.4%** | **−7.0 PMID, +3.7 SPLIT** |
| 2 | 64.6% | 34.3% | 1.1% | 75.0% | 24.5% | 0.5% | +10.4 PMID |

**Three structural patterns visible:**
1. **Oracle's PBOT rate is non-monotonic in pair_rank.** Minimum at pair=A (18%), maximum at pair=Q (53%), partial recovery to mid-30% at 2-5 (LOW pairs). The Q-peak is the structural inflection: Q-pair on bot beats Q-pair in mid for the strongest pair-to-bot rate of any pair_rank.
2. **v44_dt under-routes PBOT at every mid pair_rank (K, Q, J, T) by 7–11%.** This is the largest systematic v44 error pattern on pair hands.
3. **v44_dt over-picks SPLIT at pair=3, 4 (4.2%-4.4%) — oracle never picks SPLIT meaningfully there (~0.5%).** The SPLIT picks at low pairs are catastrophic ($16K-$24K/hand mean regret); these alone account for most of the pair=3, pair=4 WG residual spike.

### Cell residual cross-tab (v44 vs oracle, $/1000h whole-grid by canonical-equal)

| pair_rank | PBOT_DS_JOINT | PBOT_DS_PARTIAL | PMID_DS_MAXTOP | PMID_DS_NOMAXTOP | PMID_SS_MAXTOP | PMID_OTHER | TOTAL |
|---:|---:|---:|---:|---:|---:|---:|---:|
| A | $2.53 | $9.89 | $0.64 | $7.67 | $1.62 | $1.87 | $24.21 |
| K | $3.25 | $12.91 | $1.13 | $9.24 | $3.02 | $3.53 | $33.09 |
| Q | $3.40 | $13.61 | $1.66 | $11.01 | $3.86 | $4.52 | $38.07 |
| J | $3.53 | $14.41 | $1.33 | $10.33 | $3.74 | $4.51 | $37.84 |
| T | $3.58 | $13.50 | $0.61 | $7.89 | $2.29 | $2.84 | $30.71 |
| 9 | $3.15 | $11.27 | $0.53 | $7.73 | $1.75 | $2.05 | $26.48 |
| 8 | $3.64 | $13.93 | $3.09 | $11.64 | $2.97 | $3.93 | $39.20 |
| 7 | $3.76 | $16.34 | $5.74 | $15.61 | $4.38 | $5.78 | $51.61 |
| 6 | $2.80 | $12.32 | $1.02 | $9.15 | $2.26 | $2.69 | $30.24 |
| 5 | $2.79 | $12.90 | $1.30 | $9.12 | $2.55 | $2.92 | $31.58 |
| **4** | $3.51 | $14.62 | **$11.60** | **$22.30** | **$6.70** | **$9.35** | **$68.08** |
| **3** | $3.43 | $13.93 | **$12.66** | **$23.28** | **$7.12** | **$9.85** | **$70.28** |
| 2 | $3.04 | $13.47 | $0.83 | $7.85 | $2.15 | $2.44 | $29.77 |
| **TOTAL** | **$42.40** | **$173.09** | **$42.14** | **$152.82** | **$44.42** | **$56.28** | **$511.16** |

**Cell totals across pair_ranks:**
- **PBOT_DS_PARTIAL: $173.09 (33.9%)** ← largest absolute cell, but small per-hand ($886/hand)
- **PMID_DS_NOMAXTOP: $152.82 (29.9%)** ← second largest, deepest per-hand ($1,858/hand)
- PMID_OTHER: $56.28 (11.0%)
- PMID_SS_MAXTOP: $44.42 (8.7%)
- PBOT_DS_JOINT: $42.40 (8.3%)
- PMID_DS_MAXTOP: $42.14 (8.2%)

**The pair=3,4 SPIKE is concentrated in the four PMID variants** (NOT in PBOT cells). PBOT cells are uniform-ish across pair_rank; PMID cells explode at low pair. The spike is consistent with the SPLIT-mistake pattern: when oracle's correct play is PMID + best-DS-bot and v44 instead picks SPLIT-pair-in-top, the regret lands in the cells where PMID is the correct placement.

### v44 within-cell pct_opt (= how often v44 matches oracle within cell)

| pair_rank | PBOT_DS_JOINT | PBOT_DS_PARTIAL | PMID_DS_MAXTOP | PMID_DS_NOMAXTOP | PMID_SS_MAXTOP | PMID_OTHER |
|---:|---:|---:|---:|---:|---:|---:|
| A | 77.2% | 72.1% | 89.8% | 56.5% | 68.7% | 76.3% |
| K | 73.4% | 65.6% | 84.7% | 52.9% | 56.3% | 64.4% |
| Q | 73.3% | 62.9% | 79.5% | 47.1% | 48.4% | 57.7% |
| J | 73.1% | 61.6% | 82.4% | 48.1% | 49.2% | 58.0% |
| T | 71.9% | 64.9% | 89.8% | 56.0% | 61.6% | 69.3% |
| 9 | 73.6% | 69.4% | 90.8% | 57.3% | 66.4% | 74.6% |
| 8 | 72.7% | 67.6% | 86.7% | 54.1% | 62.8% | 69.9% |
| 7 | 73.3% | 65.0% | **81.7%** | 49.8% | 56.4% | 63.7% |
| 6 | 76.2% | 66.4% | 85.2% | 52.5% | 60.4% | 68.7% |
| 5 | 76.9% | 65.3% | 82.6% | 52.8% | 58.1% | 67.3% |
| **4** | 74.5% | 64.6% | **66.6%** ← | **44.0%** ← | **49.1%** | **55.2%** |
| **3** | 74.3% | 65.2% | **66.4%** ← | **43.4%** ← | **47.9%** | **53.1%** |
| 2 | 75.5% | 64.2% | 87.2% | 55.8% | 61.5% | 70.3% |

**Two cells stand out:**
- **PMID_DS_NOMAXTOP** is the lowest pct_opt cell at EVERY pair_rank (range 43-58%). v44 cannot reliably handle "PMID + DS bot but max must go in bot" decisions.
- **PMID_DS_MAXTOP at pair=4, 3** drops sharply from the 80-90% norm to ~66%. v44 mismanages low-pair PMID cells specifically — consistent with the SPLIT mistake.

---

## Top mismatch patterns per pair_rank (aggregated, $/1000h WG)

Each row: v44's pick class → oracle's pick class. Showing the largest $-magnitude mismatch per pair_rank.

| pair | dominant mismatch | n | mean ($/hand) | WG | What's happening |
|---:|---|---:|---:|---:|---|
| A | `PMID_tmax_SS → PMID_tnomax_DS` | 8,156 | $2,772 | $3.76 | Drop max off top, upgrade SS→DS bot |
| K | `PMID_tmax_SS → PMID_tnomax_DS` | 5,041 | $2,907 | $2.44 | Same drop-max-defensive + DS |
| Q | `PMID_tmax_SS → PBOT_tmax_SS_ms` | 5,661 | $3,229 | $3.04 | **Move Q-pair from mid to bot** (the under-PBOT pattern) |
| J | `PMID_tmax_SS → PBOT_tmax_SS_ms` | 6,852 | $3,097 | $3.53 | **Same Q-pattern at J** — largest under-PBOT mismatch in the matrix |
| T | `PMID_tmax_SS → PMID_tnomax_DS` | 6,113 | $2,933 | $2.98 | Drop max + DS within PMID |
| 9 | `PMID_tmax_SS → PMID_tnomax_DS` | 7,448 | $2,937 | $3.64 | Same pattern |
| 8 | `PMID_tmax_SS → PMID_tnomax_DS` | 7,316 | $2,959 | $3.60 | Same pattern |
| 7 | **`SPLIT_tmax_SS_mu → PMID_tmax_DS`** | 793 | **$24,226** | $3.20 | **v44 SPLITs the pair; oracle keeps in mid + DS bot** |
| 6 | `PMID_tmax_SS → PMID_tnomax_DS` | 6,473 | $2,846 | $3.07 | Drop max + DS within PMID |
| 5 | `PMID_tnomax_SS → PMID_tnomax_DS` | 4,146 | $3,810 | $2.63 | Within PMID drop-max, upgrade SS→DS |
| **4** | **`SPLIT_tmax_SS_mu → PMID_tmax_SS`** | 1,287 | **$16,465** | $3.53 | **v44 SPLITs low pair; oracle keeps in mid** |
| **3** | **`SPLIT_tmax_SS_mu → PMID_tmax_DS`** | 1,518 | **$20,422** | **$5.16** ← largest single mismatch class | **v44 SPLITs low pair; oracle keeps in mid + DS bot** |
| 2 | `PMID_tmax_SS → PMID_tnomax_DS` | 5,483 | $2,852 | $2.60 | Same drop-max pattern as high pairs |

**Three dominant mismatch signatures:**

1. **`PMID_tmax_SS → PMID_tnomax_DS` (drop-max-defensive + DS bot upgrade)** — Universal pattern at pair ranks 2/5/6/9/T/8/9/A/K (i.e., everywhere except Q/J where PBOT dominates, and 3/4 where SPLIT mistake dominates). Each pair_rank loses $2-4 WG to this pattern. Aggregate ≈ $25-30 WG across the matrix.

2. **`PMID_tmax_SS → PBOT_tmax_SS_ms` (pair-to-bot with suited-mid + max-on-top)** — Concentrated at Q/J/K/T. The "under-PBOT" pattern. Aggregate Q+J+K+T ≈ $10 WG.

3. **`SPLIT_tmax_X_mu → PMID_tmax_X` (low-pair anti-SPLIT)** — v44 chooses a SPLIT setting (one pair card on top + one in mid or bot) when oracle clearly says "keep pair together in mid". Catastrophic per-hand cost ($16K-$24K). Concentrated at pair=3, 4, with a smaller tail at pair=7, 8. Aggregate ≈ $12-15 WG.

---

## Cross-cutting observations

### Observation 1 — The Q-pair PBOT peak is the central structural finding

At pair_rank = Q, oracle picks PBOT (pair-to-bot) on **53% of hands** — the only pair_rank where PBOT exceeds PMID. The pattern is:

| pair_rank | Oracle PBOT% | v44 PBOT% |
|---:|---:|---:|
| A | 17.8% | 11.5% |
| K | 37.1% | 28.7% |
| **Q** | **53.2%** ← peak | 46.4% |
| J | 49.4% | 38.9% |
| T | 32.4% | 21.1% |
| 9 | 22.4% | 13.4% |

**Mechanism:** Q-pair is the "sweet spot" for pair-to-bot because (a) Q is high enough that QQ-on-bot dominates many opposing 4-card bot hands, but (b) Q is low enough that QQ-in-mid loses to A-pair or K-pair in mid frequently. K-pair and A-pair benefit more from mid-anchor strength (high pair on mid Hold'em); pair ≤ J benefits less from in-mid strength but the singletons typically aren't strong enough to substitute. Q is the inflection where (b) - (a) flips sign.

**v44 under-shoots PBOT at every pair_rank K, Q, J, T, 9, 8 by 7-11%.** This is a clean, systematic, refining-target error.

### Observation 2 — The pair=3,4 spike is a v44 SPLIT-pick bug

The two largest per-pair-rank residuals (pair=3: $70 WG, pair=4: $68 WG) are dominated by v44 picking SPLIT settings (top = 1 pair card; mid + bot contain the other pair card separated). The mean regret on these SPLIT picks is $16K-$24K/hand — order-of-magnitude larger than the typical pair-hand regret of $1K-$3K.

Oracle near-never picks SPLIT (0.5% across all pair_ranks; max 1.1% at pair=2). v44 picks SPLIT 4.2% at pair=4 and 4.4% at pair=3. **The SPLIT class is a v44 anti-pattern at low pairs specifically — the ML model has not learned "pair stays together" as a hard constraint at pair_rank ≤ 4.**

**Phase 2 implication:** a single rule of the form *"if pair_rank ∈ {3, 4} AND v44 would pick a SPLIT setting, force the best PMID + DS-bot + max-on-top alternative"* could capture an estimated $10-15/1000h WG with very high specificity (fires <5% of pair=3,4 = <0.6% of pair = <0.2% of canonical). This would meet T2's $5 raw WG bar AND likely T1's 40% capture bar within the SPLIT-mistake sub-cell. **The rule is high-priority for Phase 3 candidate work.**

### Observation 3 — PMID_DS_NOMAXTOP is the deepest cell at every pair_rank

Across all 13 pair_ranks, PMID_DS_NOMAXTOP (n=494,208 = 17.6% of pair-population) has the deepest within-cell mean regret ($1,858/hand) and the lowest pct_opt (43-58%). The cell is structurally: "pair stays in mid + DS bot achievable + but max non-pair singleton must go INTO the bot pair to make DS work."

Oracle's pick distribution in PMID_DS_NOMAXTOP (averaged across pair_ranks):
- PLACEMENT: PMID 75-90% (consistent with cell definition)
- TOP_TYPE: SING_MAX 50-60% (oracle is willing to put max in top even when DS bot trade-off requires max in bot — i.e., oracle abandons DS in favor of max-on-top)
- BOT_suit: SS 50-65%, DS 15-30% (oracle frequently DOESN'T take the DS option)

**v44's pick in same cell:**
- PLACEMENT: PMID 95-99%
- TOP_TYPE: SING_MAX 60-70%
- BOT_suit: SS 70-85%, DS 8-15% (v44 takes DS even less than oracle)

The cell is structurally a *suit-trade* decision: do you sacrifice your highest singleton to bot to get DS, or keep the highest on top with a weaker bot? v44 mostly does the conservative "keep max on top + weak bot" choice. Oracle is more willing to make the trade — but only on ~30% of the cell, not all. v44 misses the WHICH 30%.

**This is structurally analogous to the high_only DS_NO_JOINT cell** (S58 Observation 1) — a within-cell quality-trade-off where the rule "always take DS" or "never take DS" both fail.

### Observation 4 — PBOT_DS_PARTIAL is the largest cell but shallowest per-hand

PBOT_DS_PARTIAL (n=1,173,744 = 41.9% of pair) is the largest cell by population AND the largest WG residual contributor ($173/1000h). But its per-hand mean regret is only $886 — among the SHALLOWEST cells. The cell contributes to total WG mainly through its size.

Oracle's pick distribution in PBOT_DS_PARTIAL:
- PLACEMENT: PMID 55-70%, PBOT 30-45% (oracle splits roughly evenly)
- v44 PLACEMENT: PMID 70-85% (over-PMID by 10-15%)

**The pattern:** PBOT_DS_PARTIAL means "pair-to-bot DS is achievable, but you can't ALSO get ms_mid + max-on-top from the remaining singletons." Oracle chooses PBOT when the bot is strong enough; PMID otherwise. v44 defaults to PMID more often. This is the cell-version of the systematic under-PBOT bias from Observation 1.

**A rule "if pair_rank ∈ {Q, J} AND cell == PBOT_DS_PARTIAL AND PBOT bot pair_high ≥ 10 → pick the best PBOT setting"** is a candidate worth Phase 3 testing. Estimated capture: $5-15 WG (within Q+J PBOT_DS_PARTIAL = $28 WG total residual).

### Observation 5 — PBOT_DS_JOINT cell is consistently easy for v44 (pct_opt 71-77%)

The "joint pair-to-bot" cell (pair-to-bot DS + ms_mid + max-on-top all achievable) is where v44 hits its highest pct_opt within PBOT plays. Oracle's pick here is overwhelmingly the obvious one (top=max singleton, pair-to-bot DS, ms_mid). v44 matches oracle on ~3/4 of hands.

**The PBOT_DS_JOINT cell offers only $42/1000h total WG headroom across all 13 pair_ranks** — small target. Not a primary catalog focus.

### Observation 6 — Existing pair rules (Rules 5, 10, 11, v9_2) cover narrow zones; six pair_ranks have ZERO PBOT routing

The pair-handling rules in v52 are:
- **Rule 5 (v28):** KK/AA + bot rainbow → suit-aware adjustment. Fires on a narrow sub-cell (rainbow bot only).
- **Rule 10 (v41):** pair_rank ≤ J AND max_rank ≤ J → defensive (lowest singleton on top + pair in mid + 4 high singletons in bot).
- **Rule 11 (v42):** pair_rank = J AND max_rank = J → pair-to-bot DS specifically.
- **v9_2 (in v14_combined → v8_hybrid):** pair_rank ∈ {2-5, T-J-Q} AND single Ace + DS-bot-with-pair-in-bot achievable → pair-to-bot DS.

**Empirical coverage** (from Phase 2 v52 placement sweep on PBOT_DS_JOINT cells): pair_ranks A, K, 6, 7, 8, 9 produce v52 PMID-pick 100% of the time in PBOT cells — NO PBOT routing rule fires for these six ranks (= 46% of pair population). Within the 7 covered ranks (Q, J, T, 5, 4, 3, 2), v52 picks PBOT only 42-58% of PBOT_DS_JOINT, gated by v9_2's "single-Ace + suit-pattern" predicate. Rule 11 fires uniquely on J-pair-J (~2% of pair).

**The dominant catalog gap is the 6-rank PBOT-uncovered zone** (pair=A, K, 6, 7, 8, 9). At those ranks, oracle picks PBOT 12-37% (per the placement distribution table in the big-picture aggregates) but v52 picks PBOT 0%. Quantitative impact: see Phase 2 below.

---

## Phase 2 — v52 (rule chain) sweep on pair category

To validate the "existing pair rules leave headroom" hypothesis, a separate sweep computed `strategy_v52_full_high_only_handler` picks for all 2,800,512 pair hands and measured the v52→oracle gap per (pair_rank × cell). Output: `data/drill_pair_v52_per_hand.parquet` + `data/drill_pair_v52_summary.json`.

### Headline finding — v52 leaves $341/1000h more pair residual than v44

| Metric | v44_dt (ML champion) | v52 (rule chain) | Δ (v52 − v44) |
|---|---:|---:|---:|
| Total pair WG residual | $511.16 | **$852.48** | **+$341.33** |
| Within-cat pct_opt | 65.55% | 51.94% | −13.61 pp |

**v52 underperforms v44 on pair by $341/1000h whole-grid** — comparable in magnitude to high_only's $381/1000h ML-only residual. The pair category is the **second-largest two-track-divergence contributor** in the codebase, after high_only.

### Per-pair-rank v52 vs v44 ($/1000h WG)

| pair_rank | v44 WG | v52 WG | v52 − v44 | v44 pct_opt | v52 pct_opt |
|---:|---:|---:|---:|---:|---:|
| A | $24.21 | $57.78 | **+$33.57** | 71.98% | 57.81% |
| K | $33.09 | $75.46 | **+$42.37** | 65.55% | 47.86% |
| **Q** | $38.07 | $102.09 | **+$64.02** ← peak | 61.62% | 38.95% |
| J | $37.84 | $79.04 | **+$41.20** | 61.59% | 43.70% |
| T | $30.71 | $60.42 | +$29.71 | 66.98% | 53.10% |
| 9 | $26.48 | $51.36 | +$24.88 | 70.28% | 57.60% |
| 8 | $39.20 | $52.10 | +$12.90 | 67.73% | 57.61% |
| 7 | $51.61 | $57.59 | +$5.98 | 64.35% | 55.13% |
| 6 | $30.24 | $61.76 | +$31.51 | 66.94% | 51.51% |
| 5 | $31.58 | $70.53 | +$38.96 | 66.09% | 48.14% |
| **4** | $68.08 | $63.34 | **−$4.74** | 60.43% | 51.11% |
| **3** | $70.28 | $59.23 | **−$11.05** | 60.25% | 52.95% |
| 2 | $29.77 | $61.78 | +$32.01 | 66.99% | 50.89% |
| **TOTAL** | **$511.16** | **$852.48** | **+$341.33** | **65.55%** | **51.94%** |

**Two facts emerge:**
1. **v52 loses to v44 at every pair_rank EXCEPT pair=3, 4** — where v52 beats v44 by $5-11/1000h WG. Reason: v52 has v3's "pair stays in mid" default, which is correct at low pairs; v44 makes catastrophic SPLIT picks there (per Observation 2). The peak v52-LOSS is at **Q-pair (+$64 WG)**, exactly where oracle most prefers PBOT and v52 has no rule routing to it.
2. **v52's within-cat pct_opt of 51.94% is dramatically below v44's 65.55%** — the rule chain matches oracle on only ~52% of pair hands.

### Per-cell aggregate v52 vs v44 (across all 13 pair_ranks, $/1000h WG)

| cell | v44 WG | v52 WG | v52 − v44 | Hypothesis |
|---|---:|---:|---:|---|
| **PBOT_DS_JOINT** | $42.40 | $150.51 | **+$108.11** | v52 has no general PBOT-take rule; existing rules cover <50% of cell at most pair_ranks |
| **PBOT_DS_PARTIAL** | $173.09 | $455.82 | **+$282.73** ← largest | Same as above; dominant uncovered cell |
| PMID_DS_MAXTOP | $42.14 | $15.16 | −$26.98 | **v52 beats v44** — v3 default + Rule 10 (low-pair defensive) handles this cell tightly |
| PMID_DS_NOMAXTOP | $152.82 | $142.28 | −$10.55 | v52 slightly ahead; Rule 10 fires on the low-pair sub-zone where v44 fails |
| PMID_SS_MAXTOP | $44.42 | $38.11 | −$6.31 | v52 slightly ahead |
| PMID_OTHER | $56.28 | $50.60 | −$5.68 | v52 slightly ahead |
| **PBOT subtotal** | **$215.49** | **$606.33** | **+$390.84** | v52's PBOT under-routing is the dominant catalog gap |
| **PMID subtotal** | **$295.66** | **$246.15** | **−$49.51** | v52 beats v44 at PMID overall |

**Crystal-clear pattern:** v52 (rule chain) is **systematically worse than v44 (ML) at PBOT cells** by $391/1000h — and **slightly better at PMID cells** by $50/1000h.

### Existing pair-rule fire-region check (v52 placement distribution in PBOT cells)

To identify which existing rules cover which sub-zones, v52's placement choice was inspected in PBOT cells:

| pair_rank | v52 % PMID in PBOT_DS_JOINT | v52 % PBOT in PBOT_DS_JOINT | Routing rule |
|---:|---:|---:|---|
| A | 100.0% | 0.0% | (no PBOT rule fires) |
| K | 100.0% | 0.0% | (no PBOT rule fires) |
| Q | 58.3% | 41.7% | **v9_2** fires (pair_rank Q + Ace + DS feasibility) |
| J | 42.4% | 57.6% | **Rule 11** fires (J-pair + max=J only — narrow!) |
| T | 58.3% | 41.7% | **v9_2** fires |
| 9 | 100.0% | 0.0% | (no PBOT rule) |
| 8 | 100.0% | 0.0% | (no PBOT rule) |
| 7 | 100.0% | 0.0% | (no PBOT rule) |
| 6 | 100.0% | 0.0% | (no PBOT rule) |
| 5 | 58.3% | 41.7% | **v9_2** fires |
| 4 | 58.3% | 41.7% | **v9_2** fires |
| 3 | 58.3% | 41.7% | **v9_2** fires |
| 2 | 58.3% | 41.7% | **v9_2** fires |

**Six pair ranks (A, K, 6, 7, 8, 9) have ZERO PBOT routing in v52** even when PBOT_DS is achievable. v9_2's predicate excludes these ranks (it requires pair_rank ∈ {2-5, T-J-Q} + a single Ace). Rule 11 fires only on J-pair-J (narrow).

**Within v9_2-covered ranks (Q/T/5/4/3/2), v52 picks PBOT only 42% even in PBOT_DS_JOINT.** This is the structural Ace-and-suit-pattern gate — when those conditions aren't met, v9_2 doesn't fire.

### Phase 2 conclusion — catalog headroom is large and CLEAN

The v52→v44 gap on pair decomposes by cell as:
- **PBOT cells (combined $391 WG headroom)** — catalog-shippable. Rule space: extend PBOT-take rules to cover the 6 uncovered pair_ranks (A, K, 6, 7, 8, 9) and broaden v9_2's gate beyond the "single Ace" predicate.
- **PMID cells (combined $50 WG anti-headroom)** — v52 already beats v44; the catalog-correct strategy for PMID cells is the existing rule chain.

This contrasts sharply with high_only's Phase-5 outcome (ALL CELLS ML-only at catalog granularity per `HIGH_ONLY_RULE_CATALOG.md`). **Pair has substantial rule-shaped headroom** in PBOT cells specifically, and the diagnostic axis (PMID-vs-PBOT placement) is human-statable.

---

## Recommendation for Session 67+ direction (REVISED with Phase 2 data)

**The pair category is NOT ML-only at catalog granularity. The PBOT-cell story is rich with catalog-shippable headroom. Recommended path:**

### Path A (RECOMMENDED) — PBOT-rule extension sweep

**Phase 3 candidates in priority order, with v52 baseline residuals as upper-bound ship targets:**

1. **C_PAIR_1: Generalized PBOT-take for K-pair** (highest priority)
   - Fire region: pair_rank = K AND PBOT_DS achievable (cells PBOT_DS_JOINT + PBOT_DS_PARTIAL = 13.2% + 41.9% = 55.1% of K-pair = ~118.8K hands)
   - v52 residual in fire region: $14.62 + $37.15 = $51.77 WG (within K-pair)
   - v44 residual in fire region: $3.25 + $12.91 = $16.16 WG
   - Catalog-shippable ceiling: $51.77 − $16.16 = **$35.61 WG within K-pair**, scaling to **~$36/1000h whole-grid lift** if rule captures 100% of v44's catch
   - Rule: *"if pair_rank == K AND PBOT_DS achievable AND PBOT bot_pair_high ≥ T → take PBOT-HIMID setting"*
   - Clears T2 ($5 WG) by >7×. Expected production-ship candidate.

2. **C_PAIR_2: Generalized PBOT-take for A-pair**
   - Fire region: pair_rank = A AND PBOT_DS achievable (~118.8K hands)
   - v52 residual: $8.54 + $32.27 = $40.81 WG
   - v44 residual: $2.53 + $9.89 = $12.42 WG
   - Catalog ceiling: **$28.39 WG within A-pair = ~$28/1000h WG lift** at full capture
   - Same structural rule template as C_PAIR_1.

3. **C_PAIR_3: PBOT-take for 6/7/8/9-pair (uncovered v9_2 zone)**
   - Fire region: pair_rank ∈ {6, 7, 8, 9} AND PBOT_DS achievable (~475K hands)
   - v52 combined residual: ($11.60 + $33.22) + ($12.87 + $38.07 — wait wrong ranks, let me recompute):
     - 6: PBOT_DS_JOINT $11.60 + PBOT_DS_PARTIAL $33.22 = $44.82
     - 7: $9.98 + $29.37 = $39.35
     - 8: $8.84 + $26.63 = $35.47
     - 9: $9.30 + $26.98 = $36.28
     - Sum = $155.92 WG
   - v44 same: $2.80+$12.32+$3.76+$16.34+$3.64+$13.93+$3.15+$11.27 = $67.21 WG
   - Catalog ceiling: $155.92 − $67.21 = **$88.71 WG combined lift** across the 4 ranks
   - Per-rank lifts: 6 ≈ $26, 7 ≈ $24, 8 ≈ $21, 9 ≈ $18 — each clears T2 by 4-5×.

4. **C_PAIR_4: Broaden v9_2 to drop "single Ace" predicate**
   - Currently v9_2 fires only when an Ace is present alongside pair_rank ∈ {2-5, T-J-Q}.
   - The Ace predicate excludes ~70% of structurally-eligible hands within v9_2's pair_rank set.
   - Removing the Ace predicate would broaden v9_2's fire region 3×; expected lift estimate **$30-50/1000h WG**.
   - This is the smallest implementation change with substantial expected payoff.

5. **C_PAIR_5: Q-pair PBOT-take (v9_2 gating refinement)**
   - v52 leaves Q-pair PBOT_DS_PARTIAL $54.81 WG (largest single-cell residual); v44 catches $13.61.
   - Catalog-shippable: **$41.20 WG** at full capture — single-cell ship would be a project-record single rule lift.
   - Within v9_2's existing fire-region; refinement to take PBOT more often within PBOT_DS_PARTIAL when bot pair quality is high.

**Estimated Phase 3 cumulative ship value:** $200-300/1000h WG if 3-4 of the above candidates ship at 40-60% capture rates. **Bigger than high_only's S50-S53 era ($131+$51+$19+$17 = $218/1000h WG)** in cumulative shipped lift.

### Path B (FALLBACK) — Hybrid chain v52-PMID + v44-PBOT routing

If Phase 3 candidates fail catalog ship thresholds, the natural fallback is a **cell-routed hybrid**: route pair hands to v52 when cell ∈ PMID_*, route to v44 when cell ∈ PBOT_*. Expected combined residual:
- Hybrid total = v44_PBOT ($215) + v52_PMID ($246) = $462 WG
- vs v52 alone ($852): **$390 WG improvement on pair**
- vs v44 alone ($511): **$49 WG improvement on pair**

This is implementationally simple (gate is the structural cell taxonomy already defined) and captures most of the two-track-divergence on pair.

### Path C (LOWEST PRIORITY) — Trips/two_pair/three_pair audit

After pair Phase 3 ships, the next category targets per `HIGH_ONLY_RULE_CATALOG.md` Part 4.2: trips ($55 WG), two_pair ($52), three_pair ($35). Smaller absolute targets but cleaner candidates.

### Acceptance summary

**Phase 2 data DECISIVELY supports Path A over the original "anti-SPLIT" framing.** The v52 rule chain underperforms v44 by $341/1000h on pair, concentrated entirely in PBOT cells, and concentrated specifically at pair_ranks NOT covered by v9_2 or Rule 11. The structural-axis gate (PBOT_DS_achievable + pair_rank-specific rules) is the highest-EV catalog target in the project: **PBOT-take rules for K, A, 6-9 pairs alone could ship $100-150/1000h cumulative WG with high specificity.**

---

## Reusable artifacts

| Artifact | Path | Purpose |
|---|---|---|
| **Phase 1 — v44 sweep** | | |
| Per-hand parquet | `data/drill_pair_v44_per_hand_structural.parquet` | 22.8 MB; per-hand structural cell tag + v44/oracle picks. Reusable for Phase 3 catalog harness. |
| Summary JSON | `data/drill_pair_v44_summary.json` | 390 KB; aggregate stats keyed by (pair_rank, cell). Source for Phase 1 tables. |
| Sweep log | `data/session66/drill_pair_v44_S66.log` | 1,872 lines; PAIR1/PAIR2/PAIR3 console output. |
| Sweep script | `analysis/scripts/drill_pair_v44_S66.py` | Pair-specific deep-dive; mirrors `drill_high_only_v44_deepdive.py`. |
| **Phase 2 — v52 sweep** | | |
| v52 per-hand parquet | `data/drill_pair_v52_per_hand.parquet` | 12.0 MB; v52_idx, v52_regret, placement/top_type joined on canonical_id. |
| v52 summary JSON | `data/drill_pair_v52_summary.json` | 45 KB; v52 per-(pair, cell) aggregates. Source for Phase 2 tables. |
| v52 sweep script | `analysis/scripts/sweep_v52_on_pair_S66.py` | Reads pair parquet, computes v52 picks, aggregates by (pair_rank, cell). |
| Cell taxonomy | This document | 6-cell pair-specific scheme. Reused by any pair Phase 3 rule audit. |

---

## Threshold definitions (reused from S60-S64)

| Threshold | Definition | Use |
|---|---|---|
| **T1 (Catalog-worthy)** | ≥ 40% gap closure within cell AND ≥ +$3/1000h within-cell AND one-sentence statable | Identifies candidates that "really fit" the cell |
| **T2 (Production ship)** | T1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression | Production-shipping gate |
| **T3 (ML-only)** | No candidate clears T1 | Formal "this cell is ML-only at catalog granularity" verdict |

These thresholds apply unchanged to the pair Phase 2/3 audit.

---

*This document is the Session 66 Phase 1 deliverable. The cell-by-cell descriptive matrix per pair_rank is canonical; cross-cutting observations are value-added synthesis. Phase 2 (audit existing pair rules) and Phase 3 (candidate sweep) are deferred to Session 67+.*
