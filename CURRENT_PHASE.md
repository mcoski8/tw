# Current: Sprint 8 — Session 36 wrap. v30_dt is the new ML champion. Smallest ML ship since v27: −$13/1000h on full grid (and −$15 on prefix). 8th gating-template instance (trips). v29 KK/AA single-suited Rule-4-bot leak quantified and queued for v31a candidate (overnight). Three v31 candidates running overnight.

> **🌙 OVERNIGHT IN PROGRESS (Session 36 → 37):**
> Three v31 candidates running sequentially via `analysis/scripts/overnight_v31_cascade.sh`:
>   - **v31a — pair_r4v3 KK/AA-tight** (4 features) targeting the single-suited Rule-4-bot stratum that v29 left open.
>   - **v31b — trips_v2 round 2** (4 features) targeting C_top_trip routing + finer B-DS quality.
>   - **v31c — v30 features at depth=32 ml=3** to test capacity ceiling.
>
> Morning summary at `/tmp/v31_overnight_summary.md`. Per-step logs at `/tmp/{persist,train,grade}_*.log`.

> **🎯 IMMEDIATE NEXT ACTION (Session 37 morning):**
>   (A) **Read `/tmp/v31_overnight_summary.md`.** Pick the best of v31a/b/c.
>       Tripwire methodology (Session 35): top-25/30 placement count
>       predicts headline magnitude. v31a expected to be highest-impact
>       if pair_r4v3 features place in top-30 (KK/AA stratum is finely
>       targeted). v31b is the lower-prior bet (trips already gated;
>       round 2 may have diminishing returns). v31c is a control —
>       tells us whether capacity is the binding constraint.
>   (B) **Ship the winning candidate as v31.** Write Decision 066,
>       update CURRENT_PHASE, commit + push.
>   (C) **If none of v31a/b/c clear the +$10 bar:** consider pivoting
>       to fresh-category exploration. Remaining untouched categories
>       at v30 are: three_pair (1.9% × $1,654 = $32 share), and
>       refinements of already-gated families. Or revisit Rule 6 ship
>       (always-A_paired_mid for trips on STRATEGY_GUIDE) — diagnostic
>       showed always-A captures $85 whole-grid for trips alone.

> **✅ SHIPPED (Decision 065):** v30_dt — depth=30, ml=5, **493,057 leaves**
> (+6,715 vs v29), 79 features (73 v29 + 6 GATED `trips_*` features).
> Strictly dominates v29: **−$13/1000h on full grid** (trips drops $239),
> **−$15/1000h on prefix** (trips drops $289). 8th gating-template instance.
> First ship where prefix gain > full-grid gain (full:prefix ratio 0.87:1).

> **🔬 DIAGNOSTIC + DESIGN CHAIN (Session 36):**
> 1. v29 KK/AA round-2 audit → KK/AA gap closed only $7 of $14 deficit;
>    single-suited Rule-4-bot stratum is $37 below oracle.
> 2. Pivoted to trips diagnostic.
> 3. **Trips diagnostic surfaced the largest gap-to-baseline ever:**
>    v29 is $85/1000h whole-grid WORSE than always-A_paired_mid on
>    trips. v29 picks A on 79.9% of trips; the 20.1% deviations are
>    systematically wrong, especially on low-rank trips (2-9 each leak
>    $7-8/rank-share).
> 4. Designed 6 trips_aug_gated features encoding A-vs-B-vs-C routing.
> 5. v30 trained — 0/6 in top-30 importance (tripwire predicts small
>    headline). Confirmed: $13 full / $15 prefix.
> 6. v30 is a clean ship despite tripwire warning. Tripwire predicts
>    CONVERSION rate, not absolute opportunity (5-15% capture on the
>    same subpopulation regardless of underlying gap size).

> **📓 METHODOLOGY LESSONS REINFORCED (Session 36):**
> - **Tripwire is now confirmed across 5 ships:** 5/6 → +$47, 3/6 → +$70,
>   0/4 → +$6, 3/4 → +$46, 0/6 → +$13. Top-25/30 placement count is a
>   reliable leading indicator of MAGNITUDE (not direction).
> - **Diagnostic-first design holds even when tripwire is bearish.**
>   v30 is a diagnostic-driven ship (designed from explicit competing
>   baseline + missing signal) but tripwire predicted small. Both
>   readings were correct: design produced a clean win, just a small one.
> - **Always-X structural baselines are powerful primitives.** The trips
>   diagnostic surfaced "Always A_paired_mid" as the analog of Rule 4
>   for trips. This is a Rule 6 candidate that could ship $85/1000h to
>   STRATEGY_GUIDE if it isn't already encoded by v14_combined. Future
>   sessions should systematically check if structural baselines exist
>   for each category — they may unlock human-memorizable rules.
> - **Categorical features can be too coarse.** v29's
>   `pair_r4_bot_suit_profile_g` treats single-suited as one bucket
>   but the single-suited stratum has substantial within-bucket
>   structure that needs finer encoding (which suit, what rank
>   composition). v31a tests this hypothesis directly.

> Updated: 2026-05-05 (end of Session 36)

---

## Headline state at end of Session 36

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14 + Rule 4 + Rule 5** (5 numbered rules) | Human-memorizable strategy | `STRATEGY_GUIDE.md` Part 6 + `analysis/scripts/strategy_v28_rule5_rainbow.py` |
| **v30_dt** | ML champion (493,057 leaves, 79 feat: 37 base + 6 gated suited + 6 gated trips_pair + 4 gated composite + 6 gated pair + 6 gated two_pair + 4 gated high_only + 4 gated pair_r4 + 6 gated trips) | `analysis/scripts/strategy_v30_dt.py` + `data/v30_dt_model.npz` |
| v29_dt | Predecessor (73 feat); kept as comparison baseline | `analysis/scripts/strategy_v29_dt.py` + `data/v29_dt_model.npz` |
| v27_dt | Older baseline (69 feat); kept | `data/v27_dt_model.npz` |
| v26 / v25 / v24 / v23 / v20 / v18e / v16 | Superseded baselines; retained | `data/v*_dt_model.npz` |
| v20b (d=32) | ARCHIVED — capacity saturated, bit-identical to v20 | `data/v20b_dt_model.npz` |
| v19, v21, v22 | ARCHIVED (v19: prefix fail; v21/v22: Rule 5 attempts rejected) | various |
| v28_rule5_rainbow | Human-strategy chain (NOT an ML model) — ships +$1/1000h vs v14 | `analysis/scripts/strategy_v28_rule5_rainbow.py` |

**Capacity + feature progression (full 6M grid, N=200):**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| v18e | 30 | 5 | 37 | 274,446 | $2,066 | 47.08% | — |
| v20 | 30 | 5 | 43 (gated suited) | 307,939 | $1,982 | 47.81% | −$84 |
| v23 | 30 | 5 | 49 (43+6 gated TP) | 314,705 | $1,977 | 47.89% | −$5 vs v20 |
| v24 | 30 | 5 | 53 (49+4 gated comp) | 314,759 | $1,977 | 47.89% | −$1 vs v23 |
| v25 | 30 | 5 | 59 (53+6 gated pair) | 390,626 | $1,929 | 48.43% | −$47 vs v24 |
| v26 | 30 | 5 | 65 (59+6 gated t2p) | 459,209 | $1,859 | 49.21% | −$70 vs v25 |
| v27 | 30 | 5 | 69 (65+4 gated ho) | 460,375 | $1,853 | 49.27% | −$6 vs v26 |
| v29 | 30 | 5 | 73 (69+4 gated pair_r4) | 486,342 | $1,807 | 49.80% | −$46 vs v27 |
| **v30** | **30** | **5** | **79 (73+6 gated trips)** | **493,057** | **$1,794** | **49.98%** | **−$13 vs v29 (trips −$239 within-trips)** |

**Same sweep on N=1000 prefix:**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v18e | $1,082 | 59.30% | — |
| v25 | $1,054 | 59.80% | −$28 |
| v26 | $1,002 | 60.80% | −$52 |
| v27 | $1,002 | 60.80% | $0 |
| v29 | $965 | 61.32% | −$37 vs v27 |
| **v30** | **$951** | **61.53%** | **−$15 vs v29 (trips −$289 within-trips)** |

**Per-category breakdown (full grid, N=200) — eight gating wins now visible:**

| Category | v18e | v20 | v23 | v24 | v25 | v26 | v27 | v29 | v30 | Δ v30 vs v18e |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high_only  | $3,307 | $2,894 | $2,894 | $2,894 | $2,894 | $2,894 | $2,863 | $2,862 | $2,862 | **−$445** (v20+v27) |
| pair       | $1,873 | $1,873 | $1,873 | $1,873 | $1,771 | $1,771 | $1,771 | $1,674 | $1,674 | **−$199** (v25+v29) |
| two_pair   | $1,458 | $1,458 | $1,458 | $1,458 | $1,458 | $1,145 | $1,145 | $1,145 | $1,145 | −$313 (v26) |
| **trips**  | **$1,997** | **$1,997** | **$1,997** | **$1,997** | **$1,997** | **$1,997** | **$1,997** | **$1,997** | **$1,758** | **−$239** (v30) |
| trips_pair | $1,608 | $1,608 | $1,447 | $1,447 | $1,446 | $1,445 | $1,445 | $1,443 | $1,442 | −$166 (v23) |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | $+1 (noise) |
| quads      | $724 | $724 | $724 | $723 | $723 | $723 | $723 | $723 | $723 | −$1 (noise) |
| composite  | $2,100 | $2,100 | $2,080 | $1,864 | $1,869 | $1,741 | $1,741 | $1,741 | $1,733 | −$367 (v24+v26+v30 noise) |

**The gating template is now proven across 8 categories.** Pair has had two distinct gating-template iterations (v25 + v29). Trips just got its first (v30).

---

## What this leaves on the table

- v30 captures **40.9% of the v14→ceiling gap** at N=200 fidelity ($1,239/$3,033 vs v14)
- v30 captures **68.4% of the v14→ceiling gap** at N=1000 fidelity ($1,086/$2,037)
- Remaining gap to ceiling: **$1,794/1000h (full grid N=200)**, **$951/1000h (prefix N=1000)**
- Biggest residuals at full grid (per-category × share):
  - **high_only**: 20.4% × $2,862 = **$584 share** — largest residual
  - **pair**: 46.6% × $1,674 = **$781 share** — KK/AA single-suited Rule-4-bot is the largest sub-stratum (v31a target)
  - **two_pair**: 22.3% × $1,145 = **$255 share** — gated in v26
  - **trips**: 5.5% × $1,758 = **$96** — v30 captured $13; round 2 = v31b target
  - three_pair: 1.9% × $1,654 = $32 (untouched)
  - trips_pair: 2.86% × $1,445 = $41 (already gated)
  - composite: 0.245% × $1,733 = $4.3 (already gated)

---

## What Session 36 produced

### v30 ship + v29 KK/AA round-2 audit + overnight cascade kicked off

**1. v29 round-2 pair audit completed.** `distill_v29_pair.py` showed v29 closed only $7/1000h of v27's $14 KK/AA Rule-4 deficit. v29 still picks Rule-4 84.8% of KK/AA. Single-suited Rule-4-bot stratum (52.9% of KK/AA) is the largest residual leak: v29 is $13 worse than always-Rule-4 there, $37 below oracle. Categorical encoding of `pair_r4_bot_suit_profile_g` is too coarse for this stratum — finer features needed.

**2. Trips diagnostic surfaced massive gap-to-baseline.** `distill_v29_trips.py` showed v29 is $85/1000h whole-grid WORSE than always-A_paired_mid on trips — the largest competing-baseline deficit ever measured. v29 picks A 79.9%, B 4.8%, C 15.3%. Per-rank: low trips (2-9) leak $7-8/rank-share each.

**3. v30 designed and shipped — 6-feature `trips_*_g` family** (`trips_aug_features_gated.py`):

- `trips_b_ds_avail_g` (0/1) — is B-DS routing structurally feasible?
- `trips_b_ds_n_routings_g` (0..3) — count of distinct {a,b} trip-suit pairs that admit B-DS
- `trips_kickers_max_suit_count_g` (0..4) — max suit count in 4 kickers
- `trips_kickers_max_rank_g` (0..14) — highest kicker rank
- `trips_n_broadway_kickers_g` (0..4) — count of T-A among kickers
- `trips_n_low_kickers_g` (0..4) — count of 2-5 among kickers

Persistence: 27s for all 6M canonical hands → `data/feature_table_trips_aug_gated.parquet` (19 MB). B-DS feasibility rate matches diagnostic exactly: 225,225/328,185 = 68.6%.

Training: 398s for depth=30 ml=5; **493,057 leaves (+6,715 vs v29)**, +1.4% capacity expansion. Tripwire FAILED: 0/6 new features in top-30 (best is `trips_kickers_max_rank_g` at #34, 0.14%). Predicted small headline.

**4. v30 graded:**

| Grid | v29 | v30 | Δ |
|---|---:|---:|---:|
| Full N=200 | $1,807 / 49.80% | **$1,794 / 49.98%** | **−$13/1000h, +0.18 pp** |
| Prefix N=1000 | $965 / 61.32% | **$951 / 61.53%** | **−$15/1000h, +0.21 pp** |

Per-category at full grid: trips drops $1,997 → $1,758 (**−$239/1000h within-trips**). pct_opt on trips: 40.1% → 43.4% (+3.3 pp). All other categories bit-identical to within-N=200-noise.

**Full:prefix ratio: 0.87:1** — first ship where prefix > full-grid gain. Trips routing has cleaner answers under higher-fidelity grading.

### Methodology lessons reinforced (Session 36)

1. **Tripwire confirmed 5×.** 0/N in top-30 → small ship; 3+/N → big ship. v30 (0/6) ships +$13, matching v27 (0/4) ships +$6.

2. **Tripwire predicts conversion rate, not opportunity size.** Trips had 18× v27's high_only opportunity but the conversion rate was similar (~10-15%). The gating template's headline ceiling is bounded by leaf-count expansion, not subpopulation share.

3. **Categorical features can be too coarse.** v29's pair_r4 used a 6-bucket categorical for suit profile; the single-suited bucket houses 52.9% of KK/AA but has substantial within-bucket structure. v31a's pair_r4v3 features test finer encoding.

4. **Always-X baselines are Rule-N candidates.** Trips diagnostic surfaced "Always A_paired_mid" as the structural analog of Rule 4 for trips. If v14_combined doesn't already encode it, this could be a Rule 6 ship to STRATEGY_GUIDE worth ~$85/1000h whole-grid.

---

## Resume Prompt (Session 37)

```
Resume Session 37 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

The overnight v31 cascade ran 3 candidates while you were away.
Read first: /tmp/v31_overnight_summary.md (head-to-head deltas, per-
category tables, tripwire feature placement).

Then read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 36)
- DECISIONS_LOG.md (latest: Decision 065 — v30 ship, plus the v29
  KK/AA round-2 finding)
- analysis/scripts/strategy_v30_dt.py — current ML champion
- analysis/scripts/{train,strategy,grade}_v31{a,b,c}_dt.py — overnight
  candidates' wrappers
- analysis/scripts/{pair_aug_v3,trips_aug_v2}_features_gated.py — new
  candidate feature modules
- analysis/scripts/distill_v29_trips.py — Session 36 trips diagnostic

State (end of Session 36):
- v30_dt is the new ML champion: $1,794/1000h on full grid (49.98% opt),
  $951/1000h on prefix N=1000 (61.53% opt). 493,057 leaves, depth=30,
  min_samples_leaf=5, 79 features (73 v29 + 6 gated trips).
- 8th gating-template instance. Trips category drops $239 within-trips
  (40.1% → 43.4% pct_opt).
- Smallest ML ship since v27 ($13 vs $6) but on a much larger underlying
  opportunity ($109 whole-grid trips share vs v27's $43 high_only).
- Tripwire 0/6 in top-30 predicted (and confirmed) small headline.
- Three v31 candidates running overnight: v31a (pair_r4v3 KK/AA-tight),
  v31b (trips_v2 round 2), v31c (v30 features at depth=32 ml=3).

Decision matrix for picking v31 winner:
- If v31a ships ≥+$10 with ≥1/4 features in top-30 → ship as v31, write
  Decision 066, pair has had 3 gating-template iterations.
- If v31b ships ≥+$10 → ship as v31, trips has had 2 iterations.
- If v31c ships ≥+$10 → THIS IS A SIGNAL: capacity is still binding;
  consider raising default depth/ml for future trains.
- If multiple ship: pick the largest, archive the others.
- If NONE ship ≥+$10: pivot. Options:
  (a) Rule 6 ship — codify "Always A_paired_mid" for trips to
      STRATEGY_GUIDE, ~$85/1000h whole-grid if v14 doesn't already.
  (b) Fresh diagnostic on v30 across all 7 residual categories to
      find next-priority leak.
  (c) Higher-fidelity oracle grid (N=200 → N=400 or N=500) — multi-
      hour compute investment for cleaner training signal.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000)
  WHEN APPLICABLE.
- ALL new aug feature families MUST be category-gated. Gating template
  is now proven 8× and is the default.
- ALL new aug families MUST use a UNIQUE PREFIX. Claimed: `_g` suffix
  (suited), `tp_*_g` (trips_pair), `comp_*_g` (composite),
  `pair_*_g` (pair v1), `t2p_*_g` (two_pair), `ho_*_g` (high_only),
  `pair_r4_*_g` (pair v2), `trips_*_g` (trips), `pair_r4v3_*_g`
  (pair v3 — overnight), `trips_v2_*_g` (trips v2 — overnight).
- Cached parquets cut training cycles to ~5 min.
- Methodology rule (Session 35-36): top-25/30 feature importance is a
  pre-grade tripwire confirmed across 5 ships:
    v25 5/6 → +$47, v26 3/6 → +$70, v27 0/4 → +$6, v29 3/4 → +$46,
    v30 0/6 → +$13. Placement count predicts magnitude.
- Methodology rule (Session 36): tripwire predicts conversion rate
  (~10-15%), not absolute opportunity. A 0/N tripwire on a $200
  category opportunity → ~$20 ship; on a $20 category → ~$2.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
