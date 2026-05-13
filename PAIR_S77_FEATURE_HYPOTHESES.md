# PAIR_S77_FEATURE_HYPOTHESES — H6 / H7 / H8 feature candidates for v48_dt

_Generated: 2026-05-13 (Session 77 end)_

## TL;DR

S77 PHASE 2 ran `drill_v44_pair_S77.py` on the full 2,800,512 pair hands (10.2 min wall). The combined (pair_rank_tier × S66 cell × setting-rank bucket) lens partitions v44's $511.16/1000h pair leak into **STRUCTURE $116.04 / NOISE $206.73 / MID $188.38** and isolates **$84.56/1000h (72.9% of pair's STRUCTURE-bucket leak)** in the top 5 LOW-tier cells. The leak has a single dominant pattern: **v44 systematically over-routes LOW pairs (2-7) to SPLIT (or PBOT) when oracle keeps the pair in MID.**

Three new pair-gated features are hypothesized for S78 v48_dt retrain:

| H# | Feature | Type | Gate | Expected within-pair lift | Expected full-grid lift |
|---|---|---|---:|---:|---:|
| **H6** | `pair_pmid_ds_n_configs_g` | int8 0..5 | single-pair | $15-25 | $7-12 |
| **H7** | `pair_kicker_max_in_pair_suit_g` | bool 0/1 | single-pair | $10-18 | $5-9 |
| **H8** | `pair_low_pmid_safety_g` | int8 0..5 | LOW pair only | $20-35 | $10-17 |
| **H6+H7+H8 jointly (50% redundancy budget)** | | | | **$25-45** | **$12-22** |

Acceptance for S78: train v48_dt at depth=36 ml=1 (S73 regime LOCKED), grade vs v44 with prefix + full grader, apply +$10/1000h full-grid ship bar. With expected lifts above, the joint pack is BORDERLINE at the ship bar — but it's the cleanest fresh signal target identified by the drill.

---

## Drill summary (P_S77_OUT_1 + P_S77_OUT_2)

### Cross-tier × cell × bucket WG decomposition

| tier | cell | n | MATCH% | NOISE% | MID% | STR% | STR $/1000h |
|---|---|---:|---:|---:|---:|---:|---:|
| LOW | PBOT_DS_JOINT | 171,072 | 75.3% | 18.3% | 5.6% | 0.8% | $1.97 |
| LOW | PBOT_DS_PARTIAL | 541,728 | 65.4% | 22.9% | 10.2% | 1.5% | $10.36 |
| LOW | **PMID_DS_MAXTOP** | 128,304 | 78.5% | 12.2% | 4.0% | **5.3%** | **$21.68** |
| LOW | **PMID_DS_NOMAXTOP** | 228,096 | 50.0% | 30.9% | 13.9% | **5.2%** | **$31.00** |
| LOW | **PMID_SS_MAXTOP** | 85,536 | 55.8% | 25.9% | 13.1% | **5.2%** | **$9.71** |
| LOW | **PMID_OTHER** | 137,808 | 63.3% | 22.6% | 10.3% | **3.9%** | **$11.81** |
| MID | (all 6 cells) | 646,272 | 68.7% | — | — | — | $15.93 |
| HIGH | (all 6 cells) | 861,696 | 65.5% | — | — | — | $13.57 |

### Tier rollup

| tier | n | MATCH% | NOISE $ | MID $ | **STR $** | TOTAL $ |
|---|---:|---:|---:|---:|---:|---:|
| **LOW (22-77)** | 1,292,544 | 64.4% | $96.93 | $98.09 | **$86.54** | **$281.56** |
| MID (88-TT) | 646,272 | 68.7% | $44.44 | $36.02 | $15.93 | $96.39 |
| HIGH (JJ-AA) | 861,696 | 65.5% | $65.36 | $54.27 | $13.57 | $133.21 |

**Key finding: LOW pairs carry 74.6% of pair's STRUCTURE leak ($86.54/$116.04).**

### Top 5 STRUCTURE-bucket cells (the v48 target population)

| rank | tier | cell | n_STR | STR $ | gap_2nd_med |
|---:|---|---|---:|---:|---:|
| 1 | LOW | PMID_DS_NOMAXTOP | 11,884 | $31.00 | 0.1800 |
| 2 | LOW | PMID_DS_MAXTOP | 6,760 | $21.68 | 0.3850 |
| 3 | LOW | PMID_OTHER | 5,355 | $11.81 | 0.1850 |
| 4 | LOW | PBOT_DS_PARTIAL | 7,977 | $10.36 | 0.1150 |
| 5 | LOW | PMID_SS_MAXTOP | 4,484 | $9.71 | 0.1650 |
| **sum** | | | **36,460** | **$84.56** | — |

Cells 1-3 and 5 share a single mismatch pattern (v44 SPLIT/PBOT → oracle PMID). Cell 4 is the EXCEPTION (v44 PMID → oracle PBOT_DS). **gap_2nd_med 0.39 for PMID_DS_MAXTOP** indicates a very sharp optimum — those misses are HIGH-confidence "v44 picked structurally wrong."

---

## Dominant mismatch pattern (P_S77_OUT_3)

### LOW × PMID_DS_MAXTOP — $21.68/1000h, SHARPEST optimum

The single largest mismatch class IN THE ENTIRE DRILL:

```
v44: SPLIT_tmax_SS_mu  →  oracle: PMID_tmax_DS    n=3,072  mean=$+21,459  wg=$+10.97/1000h
```

3,072 hands × $21,459 mean regret = **$10.97/1000h on ONE mismatch class** out of the $116 pair STR total. v44 splits the pair (one card to mid, one to bot) with max-sing on top and SS bot; oracle keeps the pair in mid with DS bot and max-sing on top. The PMID_DS_MAXTOP option is structurally available (definition of the cell) but v44 misses it.

Other large LOW × PMID_DS_MAXTOP mismatches (all same direction):
* `SPLIT_tmax_31_mu → PMID_tmax_DS` n=730, $2.48
* `SPLIT_tmax_SS_ms → PMID_tmax_DS` n=818, $2.48
* `SPLIT_tmax_DS_mu → PMID_tmax_DS` n=621, $1.70

### LOW × PMID_DS_NOMAXTOP — $31.00/1000h

```
v44: SPLIT_tmax_SS_mu  →  oracle: PMID_tmax_SS         n=1,430  $+4.17
v44: SPLIT_tmax_SS_mu  →  oracle: PMID_tnomax_DS       n=  782  $+2.48
v44: SPLIT_tmax_RB_mu  →  oracle: PMID_tmax_SS         n=  432  $+1.69
v44: SPLIT_tpair_DS_mu →  oracle: PMID_tnomax_DS       n=  477  $+1.39
v44: PBOT_tmax_RB_mu   →  oracle: PMID_tnomax_DS       n=  616  $+1.36
```

Same pattern: v44 SPLITs/PBOTs, oracle stays PMID. NOMAXTOP cell = max sing is forced into bot under PMID_DS routing, so the top is a non-max singleton. v44 reads "max sing not on top" as a signal to abandon PMID, but oracle says PMID with non-max top is still optimal.

### LOW × PBOT_DS_PARTIAL — $10.36/1000h (REVERSE direction)

```
v44: PMID_tmax_SS  →  oracle: PBOT_tnomax_DS_mu    n=389  $+0.42
v44: PMID_tmax_SS  →  oracle: PBOT_tnomax_DS_ms    n=296  $+0.37
```

This cell is the EXCEPTION: v44 stays PMID, oracle routes to PBOT_DS. PBOT_DS_PARTIAL = pair-bot DS achievable but no msmid+maxtop bonus. The CORRECT discriminator: **70% of LOW × PBOT_DS_PARTIAL STR-bucket hands have kicker_max IN pair_suits**, vs 32-34% in the PMID-target cells. Kicker_max-in-pair-suit alignment is a clean PBOT-vs-PMID signal.

---

## Structural fingerprint (P_S77_OUT_4)

### LOW × PMID_DS_NOMAXTOP STR-bucket fingerprint (n=11,884)

* non-pair suit profile (5 non-pair cards): 80% DS, 20% 32
* n_broadway (T-A among non-pair): 75% have ≥2
* kicker_max_rank: 80% have A/K/Q (28% A, 32% K, 20% Q)
* **kicker_max suit ∈ pair_suits: 32% TRUE, 68% FALSE** ← discriminator
* pair_rank: uniform 22..77 (16.7% each)

### LOW × PMID_DS_MAXTOP STR-bucket fingerprint (n=6,760)

* non-pair suit profile: 67% 32, 33% DS
* n_broadway: 83% have ≥2
* kicker_max_rank: 67% A/K (35% A, 32% K)
* **kicker_max suit ∈ pair_suits: 34% TRUE, 66% FALSE** ← discriminator

### LOW × PBOT_DS_PARTIAL STR-bucket fingerprint (n=7,977) — REVERSE-direction cell

* non-pair suit profile: 47% SS, 34% DS, 17% 31
* n_broadway: ~62% have ≥2
* kicker_max_rank: 26% K, 25% Q, 20% J (broader distribution)
* **kicker_max suit ∈ pair_suits: 70% TRUE, 30% FALSE** ← reverse alignment

The kicker_max-in-pair-suits discriminator runs in the EXPECTED direction: cells where v44 should choose PMID have kicker_max NOT in pair_suits 65-78%; the one cell where v44 should choose PBOT has kicker_max IN pair_suits 70%.

---

## Hypothesis H6 — `pair_pmid_ds_n_configs_g`

### Definition

For single-pair hands (n_pairs==1, n_trips==0, n_quads==0): the count of distinct top-singleton choices (out of the 5 non-pair singletons) such that the bot (= pair-in-mid + 4 non-top singletons) is double-suited (2+2). Values 0..5. Zero on all non-pair hands.

```python
def compute_pair_pmid_ds_n_configs(hand) -> int:
    # gated to single-pair hands
    pair_rank = ...
    sing_pos = [i for i in range(7) if ranks[i] != pair_rank]  # 5 sings
    n = 0
    for top_local in range(5):
        bot_locals = [k for k in range(5) if k != top_local]
        bot_suits = [suits[sing_pos[k]] for k in bot_locals]
        if Counter(bot_suits).most_common(2) == [(_, 2), (_, 2)]:
            n += 1
    return n
```

### Why v44 lacks this signal

v44 has `pair_r4_bot_suit_profile_g` = the suit profile of the DEFAULT-routing bot (= top=max singleton, bot=4 lowest). That single value tells the DT whether the default bot is DS, SS, 31, etc. It does NOT enumerate alternative top-choices.

v44 also has `pair_aug_v5_bot_DS_n_configs_g` — but that counts **PBOT_DS** routings (pair in bot), not **PMID_DS** routings.

The DT cannot derive H6 from existing features in <3 splits without effectively re-enumerating combinations.

### Expected within-cat lift

Direct target: LOW × PMID_DS_{MAXTOP, NOMAXTOP} cells, combined $52.68/1000h STR-bucket leak across 18,644 hands. If H6 lets v48 route these to PMID instead of v44's SPLIT/PBOT choice:
* Captures 30-50% of $52.68 → $15-26/1000h within pair
* Full-grid lift: $7-12/1000h

### Redundancy risk

* `pair_r4_bot_suit_profile_g == 3` (DS) implies n_configs ≥ 1 (default routing yields DS) — partial overlap on the binary "any-PMID-DS-possible" axis.
* But n_configs ∈ {2, 3, 4, 5} encode information v44 cannot recover from a single suit-profile lookup.
* The MAXTOP-vs-NOMAXTOP distinction (which separates $21.68 from $31.00 cells) requires knowing whether the "default" top (= max sing) is among the top choices yielding DS bot. H6 alone doesn't directly encode that — but pair_r4_bot_suit_profile_g effectively does (default routing IS top=max).
* **Risk: ~30% redundancy**. Worth testing.

---

## Hypothesis H7 — `pair_kicker_max_in_pair_suit_g`

### Definition

Boolean (0/1) gated to single-pair hands; zero elsewhere. 1 if the max-rank singleton's suit is one of the two pair-suits; 0 otherwise.

```python
def compute_pair_kicker_max_in_pair_suit(hand) -> int:
    # gated to single-pair hands
    pair_pos = [i for i in range(7) if ranks[i] == pair_rank]
    pair_suits = {suits[pair_pos[0]], suits[pair_pos[1]]}
    sing_pos = [i for i in range(7) if i not in pair_pos]
    max_sing_local = argmax([ranks[p] for p in sing_pos])
    max_sing_suit = suits[sing_pos[max_sing_local]]
    return int(max_sing_suit in pair_suits)
```

### Why v44 lacks this signal

v44 has `pair_kickers_in_pair_suit_max_g` and `_min_g` — those are the MAX and MIN of (count of kickers in pair-suit-A, count in pair-suit-B). They count HOW MANY kickers align with each pair-suit, not WHICH SPECIFIC kicker (the max-rank one) does.

The discrimination "kicker_max IS in pair_suits" vs "is NOT" is a 1-bit signal that requires looking at the ranks AND the suits together. v44's features expose them independently.

### Expected within-cat lift

This is the cleanest PBOT-vs-PMID discriminator the drill surfaced:
* When TRUE (kicker_max ∈ pair_suits): PBOT_DS structurally tempting because pair + max-sing form 3 cards in pair-suits, easy to complete DS bot with 1 more kicker.
* When FALSE: PBOT_DS requires sacrificing the max-sing to bot OR using lesser-rank kickers, weakening the position.

Target: LOW × PMID-target cells where v44 over-routes to SPLIT/PBOT. ~$70/1000h of LOW STRUCTURE leak in cells with 65-78% FALSE alignment. If H7 lets v48 route those to PMID:
* Captures 20-30% → $14-21/1000h within pair
* Full-grid lift: $7-10/1000h

Could also fire in the REVERSE direction for LOW × PBOT_DS_PARTIAL (70% TRUE alignment) — letting v48 keep the existing PBOT_DS pick instead of (incorrectly) over-correcting to PMID. Net: $5-9/1000h full-grid.

### Redundancy risk

* `pair_kickers_in_pair_suit_max_g` ≥ 1 implies the max KICKERS count in a pair-suit is at least 1 — but doesn't say which RANK kicker is in that suit.
* The DT could approximate H7 by combining `pair_kickers_in_pair_suit_max_g ≥ 1` AND `pair_default_top_rank_g == max_sing_rank` (always true since default routing puts max on top). Effective 2-3 split derivation; partial redundancy at saturation.
* **Risk: ~40% redundancy** but the 1-bit "max sing is in a pair-suit" signal is a HIGH-information single feature for the DT to split on.

---

## Hypothesis H8 — `pair_low_pmid_safety_g`

### Definition

Categorical (int8 0..5) gated to LOW pairs (pair_rank ∈ {2,3,4,5,6,7}). Zero on all non-pair hands AND on MID/HIGH pairs. For LOW pairs, encodes the S66 cell in priority order:

```
0: not a LOW pair  (= not single-pair OR pair_rank >= 8)
1: LOW pair AND cell == PMID_DS_MAXTOP
2: LOW pair AND cell == PMID_DS_NOMAXTOP
3: LOW pair AND cell == PMID_SS_MAXTOP
4: LOW pair AND cell == PMID_OTHER
5: LOW pair AND cell ∈ {PBOT_DS_JOINT, PBOT_DS_PARTIAL}
```

The 6 levels are NOT linearly ordered by EV; they're a clean categorical that the DT splits on directly. Levels 1-4 are "v44 over-routes to SPLIT/PBOT, oracle keeps PMID" cells; level 5 is the "v44 may stay PMID, oracle routes to PBOT_DS" exception cell.

```python
def compute_pair_low_pmid_safety(hand) -> int:
    if not is_single_pair(hand): return 0
    if pair_rank >= 8: return 0
    cell = cell_for_pair_hand(compute_pair_structural(hand))
    return {"PMID_DS_MAXTOP": 1, "PMID_DS_NOMAXTOP": 2,
            "PMID_SS_MAXTOP": 3, "PMID_OTHER": 4,
            "PBOT_DS_JOINT": 5, "PBOT_DS_PARTIAL": 5}[cell]
```

### Why v44 lacks this signal

v44 has the CONSTITUENT counts (n_PBOT_DS via v5, pair_r4_bot_suit_profile for default-PMID-bot shape) but NOT the cell synthesis. The cell taxonomy is a CASCADE of AND-NOT logic:

```
cell = PBOT_DS_JOINT if n_PBOT_DS_w_msmid_maxtop > 0
       else PBOT_DS_PARTIAL if n_PBOT_DS > 0
       else PMID_DS_MAXTOP if n_PMID_DS_w_maxtop > 0
       else PMID_DS_NOMAXTOP if n_PMID_DS > 0
       else PMID_SS_MAXTOP if n_PMID_SS_w_maxtop > 0
       else PMID_OTHER
```

A saturated DT at 2.7 rows/leaf cannot reliably reach this cell synthesis through a feature cascade — it would consume 5+ splits in priority order at every relevant subtree. A direct categorical short-circuits the synthesis into a single split.

The LOW-pair gating is intentional: 74.6% of pair STRUCTURE leak is in LOW; the signal is noisy/diluted for MID/HIGH pairs (where strong pair-rank dominates routing decisions). Gating tightens the feature against the right population.

### Expected within-cat lift

Direct target: ALL of LOW STRUCTURE-bucket leak ($86.54/1000h within 36,460 hands across 5 cells). If H8 lets v48 cleanly partition LOW pair hands by cell:
* Captures 25-40% of $86.54 → $22-35/1000h within pair
* Full-grid lift: $10-17/1000h

### Redundancy risk

H8 IS the most aggressive feature and the most "derivable" in principle. The S74 H2 lesson: a feature that's a 2-split combination of existing features gets zero lift at saturation. H8 is a 5-split combination (the cell cascade) — more deeply hidden, less likely to be directly derivable in <3 splits.

**Risk: ~50% redundancy** but worth testing precisely because the cell cascade is too long for a saturated DT to compute consistently.

### LOW-only gating decision

Gating to LOW pairs is justified by drill data:
* LOW STR leak: $86.54 / LOW total $281.56 = 30.7% of LOW pair leak
* MID STR leak: $15.93 / MID total $96.39 = 16.5%
* HIGH STR leak: $13.57 / HIGH total $133.21 = 10.2%

The signal-to-noise is 3× better for LOW than HIGH. Wider gating dilutes the feature; tighter gating concentrates it.

---

## Combined H6+H7+H8 expected behavior

| Hypothesis | Expected within-pair $ | Expected full-grid $ | Independent? |
|---|---:|---:|---|
| H6 alone | $15-26 | $7-12 | mostly |
| H7 alone | $14-21 | $5-10 | partial overlap with H6 |
| H8 alone | $22-35 | $10-17 | overlaps with H6+H7 |
| **H6+H7 (overlap-budgeted)** | $20-30 | $10-15 | |
| **H6+H7+H8 (overlap-budgeted)** | $30-45 | $14-22 | |

Assuming 50% redundancy budget on overlapping signal, the joint pack expects to clear the **+$10/1000h full-grid ship bar** with moderate margin. The fingerprint is structurally distinct from the v44 H1/H2 axes — no shared lineage with the high_only H1-H5 cascade.

### Methodology guard rails

1. **S73 regime LOCKED** for v48 training: depth=36, ml=1, criterion=squared_error. No re-sweep.
2. **+$10 ship bar canonical** (S73 codified, held S74-S76). If full-grid Δ < $10, NULL ship regardless of within-pair lift.
3. **Capacity matters**: v44 has 2.25M leaves on 4.8M rows. New features must add NEW partition surfaces, not refine existing ones. H6, H7, H8 are designed to expose pair-routing structure the DT cannot derive in <3 splits.
4. **Smoke before full**: train v48_dt on 100K rows first; verify feature importance places H6/H7/H8 in top-30 before committing to full retrain.

---

## Acceptance status (Session 77 PHASE 3)

✅ Pair structural cell taxonomy designed and validated (`drill_v44_pair_S77.py` shipped).
✅ Top 3-5 STRUCTURE-bucket cells identified (top 5 = LOW × {PMID_DS_NOMAXTOP, PMID_DS_MAXTOP, PMID_OTHER, PBOT_DS_PARTIAL, PMID_SS_MAXTOP}, totaling $84.56/1000h).
✅ Three feature hypotheses (H6, H7, H8) with expected within-pair lift ≥$30/1000h on the joint pack.
✅ Decision 112 pending PHASE 4.

S78 next steps: implement H6+H7+H8 feature pack (~3 new gated feature files), persist gated parquet, retrain v48_dt at depth=36 ml=1, prefix + full grade vs v44.
