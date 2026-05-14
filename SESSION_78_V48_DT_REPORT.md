# Session 78 — v48_dt: H6+H7+H8 pair-feature pack — CLEAN NULL ship at prefix grade

_Generated 2026-05-13 (Session 78 end)._

## TL;DR

S77 queued three pair-gated feature hypotheses (H6/H7/H8) for v48_dt
retrain at the S73 regime (depth=36, ml=1). Phase 1-4 executed as
planned: feature files implemented with sanity tests, gated parquet
packs persisted with zero-on-non-pair verification, smoke train passed
the rank-<80 abort gate, full train completed in 578s wall producing a
2.29M-leaf 1,285 MB model.

**Phase 5 prefix grade returned Δ = +$2/1000h (v44 $686 → v48 $684).**
Within-pair lift was +$5/1000h ($595 → $590) on the 215,162 prefix pair
hands — a small fraction of S77's predicted $30-45/1000h within-pair
lift. Per the CURRENT_PHASE directive (`prefix Δ < +$5 → NULL ship`),
Phase 6 (full grade) was skipped. Production state UNCHANGED for the
seventh consecutive session.

**Verdict: CLEAN NULL ship.** The structural-redundancy hypothesis (S74
codified: features derivable in <few splits from existing v44 features
get zero or near-zero lift at v44's saturating regime) is empirically
confirmed for H6/H7/H8 — the saturated 2.25M-leaf tree absorbs the new
pair signal via existing splits rather than via the new features.

## Phase results

### Phase 1 — Feature files (PASS)

Three new pair-gated feature files implemented at
`analysis/scripts/`:

* `pair_pmid_ds_features_gated.py` — H6: `pair_pmid_ds_n_configs_g`
  (int8 0..5, single-pair gated).
* `pair_kicker_align_features_gated.py` — H7:
  `pair_kicker_max_in_pair_suit_g` (bool 0/1, single-pair gated).
* `pair_low_pmid_safety_features_gated.py` — H8:
  `pair_low_pmid_safety_g` (int8 0..5, LOW-pair-only gated).

H8's inline `_pair_cell_for_low()` cell-taxonomy logic was
cross-validated against S66's gold-standard `compute_pair_structural`
+ `cell_for_pair_hand` on 23,377 random single-pair canonical hands:
**zero disagreements.**

All sanity tests passed (8/8 H6, 9/9 H7, 12/12 H8) including the
gate-out cases for trips, two-pair, quads, no-pair, and MID/HIGH pair
hands.

### Phase 2 — Persist gated parquets (PASS)

Persists ran in parallel; each verified zero-on-non-gated:

| Feature | Output | Size | Distribution |
|---|---|---:|---|
| H6 | `data/feature_table_pair_pmid_ds_gated.parquet` | 18.69 MB | 0:4.67M, 1:927K, 3:412K |
| H7 | `data/feature_table_pair_kicker_align_gated.parquet` | 18.64 MB | 0:4.61M, 1:1.40M |
| H8 | `data/feature_table_pair_low_pmid_safety_gated.parquet` | 18.60 MB | 0:4.72M, 1:128K, 2:228K, 3:86K, 4:138K, 5:713K |

**Observation: H6 values only reach {0, 1, 3} — the deck structure for
5 non-pair singletons across 4 suits admits exactly 0, 1, or 3
PMID_DS-yielding top choices** (from suit profiles 2+2+1 → 1 config,
3+2 → 3 configs, all others → 0). The 0..5 range in the original H6
spec was unreachable. H6 is still informative (it cleanly tags the
"PMID_DS feasible / many-feasible / infeasible" trichotomy) but the
top-rank achievable value cap reduces partitioning surface vs the
hypothesis.

H8's level-5 (PBOT_DS) count of 712,800 matches S77 drill totals
exactly (PBOT_DS_JOINT 171,072 + PBOT_DS_PARTIAL 541,728), confirming
the cell logic is consistent with the drill.

### Phase 3 — Smoke train, 100K rows (PASS-with-caveat)

Smoke train at depth=36 ml=1 completed in 2.5s wall, producing 63,226
leaves at depth 28. Feature importance placements:

| Feature | Smoke rank | Smoke importance |
|---|---:|---:|
| `pair_kicker_max_in_pair_suit_g` (H7) | **#51** | 0.19% |
| `pair_low_pmid_safety_g` (H8) | **#69** | 0.07% |
| `pair_pmid_ds_n_configs_g` (H6) | **#73** | 0.07% |

None reached the top-30 ideal target but all cleared the **rank ≥80 =
abort** threshold from the S78 directive. Proceeded to full train per
the strict reading of the abort gate.

### Phase 4 — Full train, 4.8M rows (PASS)

| Metric | v44_dt | v48_dt | Δ |
|---|---:|---:|---:|
| Wall time | ~30 min | **9.6 min** (578s) | — |
| Features | 107 | **110** | +3 |
| Leaves | 2,250,000 | **2,294,001** | +44,001 (+1.96%) |
| Depth | 36 | 36 | — |
| Model size | 1,253 MB | **1,285 MB** | +32 MB |

Top-30 dominated by base + suited + pair_r4 + pair_aug_v5 + t2p_v2
features (same as v44). H6/H7/H8 placement at full scale:

| Feature | Full rank | Full importance |
|---|---:|---:|
| H7 `pair_kicker_max_in_pair_suit_g` | **#43** | 0.1416% |
| H8 `pair_low_pmid_safety_g` | **#57** | 0.0812% |
| H6 `pair_pmid_ds_n_configs_g` | **#68** | 0.0623% |

All three moved up vs smoke (51→43, 69→57, 73→68). The DT did use the
new features; they just contributed less partitioning surface than the
hypothesis predicted.

### Phase 5 — Prefix grade (CLEAN NULL ship)

500K-hand prefix grid (oracle_grid_prefix500k_n1000.bin).

```
strategy                    pct_opt   mean_regret   $/1000h   p90    wall
v44_dt (baseline)            67.13%   0.0686        $686      0.264   67s
v48_dt (+ H6/H7/H8)          67.19%   0.0684        $684      0.263   78s

v48_dt vs v44_dt: +0.0002  ≈ $+2/1000h
```

Per-category breakdown:

| category | n_hands | v44 $/1000h | v48 $/1000h | Δ |
|---|---:|---:|---:|---:|
| **pair** | 215,162 | **$595** | **$590** | **−$5 (within-cat)** |
| two_pair | 204,275 | $663 | $663 | — |
| trips | 25,245 | $1,086 | $1,086 | — |
| trips_pair | 25,943 | $727 | $727 | — |
| three_pair | 25,614 | $1,143 | $1,143 | — |
| quads | 1,100 | $783 | $783 | — |
| composite | 2,661 | $1,226 | $1,226 | — |

**The H6/H7/H8 pack lifts ONLY pair, by $5/1000h within pair on
prefix.** All other categories are byte-identical (v48 picks the same
setting as v44 outside pair) — the new gated features correctly do not
affect non-pair routing.

Per the CURRENT_PHASE Phase 5 directive (`prefix Δ < +$5 → NULL ship;
document the within-pair lift; consider pair-only sub-strategy
alternative`), Phase 6 (full grade) was skipped.

### Phase 6 — Full grade (SKIPPED per directive)

The S78 plan explicitly conditioned Phase 6 on prefix Δ ≥ +$5. With
prefix Δ = +$2 the full-grid run was skipped to conserve cluster time
and respect the user directive. Prefix and full track each other
within ±$5-15 historically; the +$10 ship bar would require prefix
≈ +$7+ to be achievable.

## Why the predicted lift didn't land — structural-redundancy NULL

S77's hypothesis pack expected:

| Hypothesis | Predicted within-pair $ | Observed within-pair $ | Hit ratio |
|---|---:|---:|---:|
| H6+H7+H8 (joint, 50% redundancy budget) | $30-45 | **$5 (combined)** | ~10-17% |

The S77 PAIR_S77_FEATURE_HYPOTHESES.md assessed redundancy at H6 ~30%,
H7 ~40%, H8 ~50%. **Observed redundancy is materially higher** —
closer to 85-90% (saturated DT recovers most of H6/H7/H8's signal
through existing splits). Three contributing factors:

1. **H6 only emits {0, 1, 3}**, not {0..5} — its partitioning surface
   is ~3 bits, not the 6 hypothesized.
2. **H7 is a 1-bit signal** that a saturated DT can often approximate
   via `pair_kickers_in_pair_suit_max_g ≥ 1 AND
   pair_default_top_rank_g == kicker_max` (2-split derivation).
3. **H8 is a 5-split cell synthesis** but at v44's 2.25M-leaf
   saturation, the DT has the capacity to construct the cell labels
   from `n_PBOT_DS` (via `pair_aug_v5_bot_DS_n_configs_g`),
   `pair_r4_bot_suit_profile_g`, and `pair_kickers_in_pair_suit_*_g`
   with only 3-4 splits per relevant leaf.

This empirically confirms the **S74 + S77 redundancy doctrine**: at
v44's saturating regime, features the DT can derive in 2-4 splits from
existing features capture zero-to-negligible incremental signal. The
S77 50%-redundancy budget proved insufficiently pessimistic. The
saturated DT's effective redundancy ceiling on derived pair features
appears to be in the 85-90% range.

## What WAS achieved on pair

* +$5/1000h within-pair on prefix = ~0.8% relative lift on pair's
  ($595→$590) prefix contribution.
* Pair `pct_optimal` improved 69.2% → 69.3% (+0.1 pp on 215K hands).
* The H6/H7/H8 pack DID slightly nudge pair routing in the predicted
  direction (more PMID-target picks, fewer SPLIT/PBOT mispicks). The
  lift is real but tiny.
* Two-track divergence UNCHANGED at $348/1000h (no full grade run).

## Pair-only sub-strategy alternative (deferred)

The CURRENT_PHASE directive mentions a pair-only sub-strategy as a
fallback. Given v48 captures only $5/1000h within pair on prefix and
pair contributes $511/1000h to v44's full-grid leak (1% capture), a
pair-only hybrid (route pair hands through v48, all else through v44)
would lift the production stack by at most $2/1000h full-grid.
**That's below the +$10 ship bar.** No pair-only sub-strategy is
worth shipping.

## Where this leaves the ML feature track

Single-model ML at v44's saturating regime appears to be at its
empirical ceiling:

| Track | Sessions | Outcome |
|---|---|---|
| H1 (ho_v6) | S71-S73 | PARTIAL POSITIVE / NULL ship at +$5 |
| H2 (route-tradeoff) | S74 | CLEAN NULL at +$0 |
| Boosting (depth=6, n_est=200) | S75 | DECISIVE NULL at −$1,392 |
| Diagnostic re-aim to pair | S76 | SHIPPED diagnostic |
| Pair deep-drill + H6/H7/H8 pack | S77-S78 | **CLEAN NULL at +$2 prefix** |

The redundancy ceiling is the dominant constraint, not the diagnostic
quality. S77 produced the cleanest feature-engineering hypothesis in
the project's history; the saturated DT still absorbed it.

## Files (Session 78)

**New code:**

* `analysis/scripts/pair_pmid_ds_features_gated.py` (H6)
* `analysis/scripts/pair_kicker_align_features_gated.py` (H7)
* `analysis/scripts/pair_low_pmid_safety_features_gated.py` (H8)
* `analysis/scripts/persist_pair_pmid_ds_gated.py`
* `analysis/scripts/persist_pair_kicker_align_gated.py`
* `analysis/scripts/persist_pair_low_pmid_safety_gated.py`
* `analysis/scripts/train_v48_dt.py`
* `analysis/scripts/strategy_v48_dt.py`
* `analysis/scripts/grade_v48_dt.py`

**Data (gitignored, local-only):**

* `data/feature_table_pair_pmid_ds_gated.parquet` (18.69 MB)
* `data/feature_table_pair_kicker_align_gated.parquet` (18.64 MB)
* `data/feature_table_pair_low_pmid_safety_gated.parquet` (18.60 MB)
* `data/v48_dt_smoke.npz` (32.90 MB) — 100K-row smoke model
* `data/v48_dt_model.npz` (1,285 MB) — full v48 DT (kept for audit)
* `data/session78/persist_pair_*.log` — persist logs
* `data/session78/train_v48_smoke.log` — smoke train log
* `data/session78/train_v48_full.log` — full train log
* `data/session78/grade_v48_prefix.log` — prefix grade log

**Documentation:**

* `SESSION_78_V48_DT_REPORT.md` — this file.
* `DECISIONS_LOG.md` — Decision 113 (S78 v48 CLEAN NULL).
* `CURRENT_PHASE.md` — rewritten for S79.
* `STRATEGY_GUIDE.md` — front-matter date refresh (no strategy of
  record changed).

## Production state at end of S78 (UNCHANGED for the seventh
consecutive session)

* Rule chain: **v56_trips_hybrid** ($1,429 full / $794 prefix). Grader-confirmed.
* ML champion: **v44_dt** ($1,081 full / $686 prefix).
* Two-track divergence: $348/1000h (no change).
* Total project rule count: 18 (UNCHANGED).
* Hypothesis cascade: H1=NULL-at-bar, H2=NULL, Boosting=NULL,
  H6/H7/H8=**NULL**.
