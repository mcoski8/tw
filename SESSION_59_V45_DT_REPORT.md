# Session 59 — v45_dt NULL RESULT: high_only 4th-pass hit ceiling at depth=36 ml=1

_Generated: 2026-05-11_

## TL;DR — v45_dt SHIPS $0/1000h vs v44_dt; does NOT replace ML champion

The 4-phase playbook (drill → hand-level → 4 rank-valued conditional features → train) was applied for the **7th consecutive session** and the **4th time on the same zone (high_only)**. Drills HO11–HO13 on v44_dt confirmed the S58 prediction: at K/Q × DS_NO_JOINT, v44 keeps max-rank on top 19–18% too often and under-routes suited mid 12–15%. The 4 new ho_v5 features (non-max joint mid_high, combined quality, max-in-bot-pair count, 4f topMax count) were designed from the HO13 stratification.

**v45_dt training:** depth=36, ml=1, 111 features → **2,248,182 leaves (only +9 over v44's 2,248,173)**. **v5 feature importance: #66 (0.07%), #97 (0.01%), #106 (0.01%), #110 (0.00%) — the lowest per-ship in project history.**

**v45_dt grade:** full-grid mean_regret 0.1081, $/1000h = $1,081, pct_opt 64.80% — **byte-identical to v44_dt across all 8 categories** (high_only pct_opt 41.83% → 41.94%, +0.11% absolute; mean_regret rounds to the same 0.1868 within-cat). **Lift: $0/1000h. v45 does NOT ship.**

| Metric | v44_dt | v45_dt | Δ |
|---|---:|---:|---:|
| Full grid mean regret | 0.1081 | 0.1081 | **+0.0000** |
| Full grid $/1000h | $1,081 | $1,081 | **$0** |
| Full grid pct_opt | 64.80% | 64.80% | **+0.00%** (+8 hands matched, n=3,893,731 → 3,893,739) |
| Prefix grid $/1000h | $686 | $686 | $0 (by design) |
| Prefix grid pct_opt | 67.13% | 67.13% | $0 (by design) |
| Leaves | 2,248,173 | 2,248,182 | **+9 (negligible)** |
| Features | 107 | 111 | +4 ho_v5 |
| Depth | 36 | 36 | saturated |
| Training time | TBD | 508s | — |

**v44_dt remains the ML champion. The high_only zone has hit a saturation ceiling at depth=36 ml=1.**

## Why v45 didn't ship — the saturation hypothesis

v44_dt at depth=36 ml=1 has 2.25M leaves on 6M training rows — each leaf covers ~2.7 training examples on average, and many leaves cover just 1. The DT has essentially memorized the training distribution.

Adding new features can split a leaf only if:
1. The leaf currently contains training rows with **different** target argmax (otherwise no impurity to reduce), AND
2. The new feature value distinguishes those rows, AND
3. No existing feature already provides an equivalent split.

ho_v5 features are mostly DERIVED from v4 signals:
- `ho_v5_max_mid_high_nonmax` is bounded by `ho_v4_max_top_rank_nonmax` (both signal "non-max joint quality")
- `ho_v5_best_combined_q` = `ho_v4_max_top_rank` + `ho_v5_max_mid_high` (linear combination)
- `ho_v5_max_in_bot_pair_n` is implied by `ho_v4_n_configs` × suit_profile counts
- `ho_v5_n_4f_ms_topmax` was already captured indirectly via ho_v4's `max_mid_high_4f`

So at depth=36, ml=1 saturation, the new features are mathematically redundant with v4's signals. The DT chooses one or the other for splitting; either yields the same leaf assignment.

## What HO11–HO13 still verified

Even though v5 didn't ship, the drills produced useful diagnostic artifacts:

**HO11 — per-max-rank residual stratification on v44_dt:**

| max | n hands | pct_opt | mean_reg | wg_contrib | Δ vs v43 (S58) |
|---|---:|---:|---:|---:|---:|
| A | 660,660 | 44.5% | $1,660 | $182.51 | −$18.80 |
| K | 330,330 | 38.9% | $2,018 | $110.94 | −$12.36 |
| Q | 150,150 | 36.7% | $2,211 | $55.24 | −$6.77 |
| J | 60,060 | 35.1% | $2,344 | $23.43 | −$3.00 |
| T | 20,020 | 38.0% | $2,181 | $7.27 | −$1.06 |
| 9 | 5,005 | 42.7% | $2,087 | $1.74 | −$0.29 |
| 8 | 715 | 40.6% | $2,338 | $0.28 | −$0.04 |
| **all** | 1,226,940 | 41.8% | $1,868 | **$381.41** | **−$42.32** |

A/K/Q together = 92% of high_only's whole-grid regret. ✓ Consistent with S58 ship.

**HO12 — DS_NO_JOINT is STILL the dominant cell** at every max-rank (62.9% by structural design × all max-ranks = $267/1000h whole-grid summed, ~70% of v44's high_only regret).

**HO13 follow-up (`drill_high_only_v44_nonmax_quality.py`) — non-max joint quality stratification:**

At max=K × DS_NO_JOINT × best_top=Q × best_mid_high=high(J+):
- n=18,144 hands
- Oracle picks non-max route 66.6%
- v44 picks non-max route **only 36.1%** — a +30.5% gap, **$9.76/1000h cell**

At max=K × best_top=J × mid_high>=J: n=15,624, oracle 44.1%, v44 11.8% — $7.53/1000h.

The gap is real and the signal is in the features. But the DT cannot exploit it at depth=36 ml=1.

## Methodology lessons (Session 59)

1. **The 4-phase playbook hits a saturation ceiling at depth=36 ml=1 + ~2.25M leaves on 6M rows.** Three passes on high_only worked (S56/57/58 each shipped). The 4th pass does NOT, despite the data signal being clear. The bottleneck is no longer feature design but DT capacity / training-data coverage.

2. **Low feature importance (+ negligible leaf growth) is the leading indicator of a null ship.** v44's ho_v4 ranked #47/#80/#93/#95 (0.13%/0.04%/0.01%/0.01%) and shipped −$42. v45's ho_v5 ranks #66/#97/#106/#110 (0.07%/0.01%/0.01%/0.00%) AND leaves grew only +9 (vs v44's +70K). The combination of low importance AND no leaf growth is a stronger null signal than importance alone.

3. **Mathematically redundant features don't help at saturation, even if the underlying axis is real.** ho_v5's signals are derivable from ho_v4 + base features via small linear combinations. The DT already has enough info to split correctly; what's missing is more rows / a different model class.

4. **The decision matrix prediction (S58 "high_only 4th-pass is the highest-leverage option") was empirically wrong.** The leverage exists at the population level ($755/1000h whole-grid in high_only) but is not capturable by adding more DT features. Future high_only attacks need a different lever.

5. **Drill HO13's stratification revealed the gap but not the path.** The (max_rank × best_top × mid_h_bucket) cross-tab pinpointed $9.76/1000h cells where v44 routes wrong. But knowing the gap doesn't mean it's closeable with the current model class.

## What this means for Session 60

The high_only zone may have plateaued under the current ML approach. Options:

**Option A — try a different model class** (gradient boosting / RF ensemble / increased depth/ml relaxation). Boosting can correct residuals in a way single-tree fitting can't.

**Option B — pivot to trips** ($1,194 within-cat × 4.6% share = $55/1000h whole-grid). The 4-phase playbook on a fresh zone may have room. trips_pair and three_pair are already collapsed; trips is the highest unattacked residual.

**Option C — examine RESIDUAL high_only hands directly** (e.g. the K × DS_NO_JOINT × best_top=Q × mid_h>=J cell from HO13) and design a RULE that fires only on that surgical cell. This would add a rule chain entry (no longer ML-only). v52 rule chain hasn't been touched since S53.

**Option D — increase training data / augment with grid-evaluated synthetic hands** — push past the depth=36 ml=1 wall by giving the DT more rows to learn from.

**Recommended:** Option C (rule on the largest residual cell) for fastest lift, OR Option B (trips) for diversification.

## Files (Session 59)

**Drills (produced):**
- `analysis/scripts/drill_high_only_v44_deepdive.py` (HO11+HO12+HO13 consolidated)
- `analysis/scripts/drill_high_only_v44_nonmax_quality.py` (HO13 follow-up cross-tab)

**Features (designed, persisted, but null-ship):**
- `analysis/scripts/high_only_aug_v5_features_gated.py`
- `analysis/scripts/persist_high_only_aug_v5_gated.py`

**Training + grading (executed, null result):**
- `analysis/scripts/train_v45_dt.py`
- `analysis/scripts/strategy_v45_dt.py`
- `analysis/scripts/grade_v45_dt.py`

**Models (persisted but NOT shipping):**
- `data/v45_dt_model.npz` (1260.57 MB — kept for reference but NOT the production champion)
- `data/feature_table_high_only_aug_v5_gated.parquet` (19.21 MB)
- `data/drill_ho_v44_per_hand_structural.parquet` (15.0 MB — reusable for future v44 residual drills)

**Documentation:**
- `SESSION_59_V45_DT_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` — Part 1 Session 59 NULL entry; Part 2 unchanged (v44 remains ML champion)
- `CURRENT_PHASE.md` — rewritten with next-session direction
- `DECISIONS_LOG.md` — Decision 094 (NULL result) appended

**Production state at end of S59:** UNCHANGED from S58.
- Rule chain: **v52_full_high_only_handler** ($2,498 full / $1,522 prefix)
- ML champion: **v44_dt** ($1,081 full / $686 prefix)
- The two tracks diverge by $1,417/1000h.

## Methodology validation summary

| Session | Playbook applied | Outcome |
|---|---|---|
| S54 | pair zone (1st pass) | +$237 SHIP |
| S55 (a) | trips_pair zone (1st pass) | +$18 SHIP |
| S55 (b) | two_pair zone (1st pass) | +$124 SHIP |
| S56 | high_only zone (1st pass) | +$79 SHIP |
| S57 | high_only zone (2nd pass) | +$69 SHIP |
| S58 | high_only zone (3rd pass) | +$42 SHIP |
| **S59** | **high_only zone (4th pass)** | **$0 NULL** |

The playbook ships on first pass at every zone. It ships on 2nd and 3rd pass at high_only (where the residual is uniquely large). But at the 4th pass on the same zone, depth=36 ml=1 saturation prevents further DT-only gains.

**Lesson:** Number of consecutive same-zone passes ≤ 3 under current DT hyperparameters. Beyond that, switch zones, switch model class, or switch lever (rules).
