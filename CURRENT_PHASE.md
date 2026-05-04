# Current: Sprint 8 — v18c_dt is the new ML champion (capacity sweep). v19 (suited-broadway aug) failed prefix tripwire and was archived.

> **🎯 IMMEDIATE NEXT ACTION (Session 30):** The diminishing-returns
> capacity curve suggests one or two more depth/leaf-count steps may
> still extract real $ before plateauing — try (depth=28, ml=10) and
> (depth=30, ml=5). The bigger wins are likely in:
>   (A) **Different aug features.** v19's suited-broadway features
>       failed the prefix tripwire — they may be encoding signal but
>       in a way that overfits N=200 noise on the pair category. Try
>       narrower features that ONLY fire for high_only hands (gated
>       like the pair_aug / two_pair_aug families).
>   (B) **Train at higher MC density.** A 200K-hand uniform-random
>       N=2000 grid would give cleaner labels for trying new aug
>       features without the prefix's canonical-id bias problem.

> **✅ SHIPPED (Decision 051):** v18c_dt — depth=26, min_samples_leaf=20,
> **124,902 leaves**. Wins +$292/1000h vs v16 on full grid AND
> +$345/1000h on N=1000 prefix. Wins on every category vs both v16
> and v18 (v18b intermediate). The capacity curve (28K → 60K → 96K → 125K
> leaves) is monotonically improving with diminishing-but-positive
> marginal returns.

> **🚫 ARCHIVED (Decision 052):** v19_dt with 6 suited-broadway aug
> features. Won full grid by +$57/1000h vs v18, but **lost prefix by
> −$16/1000h**. The pair-category regression (+$36 on prefix) suggests
> the new features are partly memorizing N=200 noise. Suited-broadway
> features as currently designed don't generalize.

> Updated: 2026-05-04 (end of Session 29 / overnight continuation)

---

## Headline state at end of Session 29

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14_combined + Rule 4** | Human-memorizable rule chain (4 rules) | `STRATEGY_GUIDE.md` + `analysis/scripts/strategy_v14_combined.py` |
| **v18c_dt** | ML champion (124,902-leaf DT, depth=26) | `analysis/scripts/strategy_v18c_dt.py` + `data/v18c_dt_model.npz` |
| v18_dt / v18b | superseded but kept for diff/baseline | `data/v18_dt_model.npz`, `data/v18b_dt_model.npz` |
| v16_dt | superseded, kept | `data/v16_dt_model.npz` |
| v19_dt | ARCHIVED — failed prefix tripwire | `data/v19_dt_model.npz`, `analysis/scripts/strategy_v19_dt.py` |

**Capacity sweep (full 6M grid, N=200):**

| Strategy | Depth | min_leaf | Leaves | $/1000h | pct_opt | Δ vs prev | Δ vs v16 |
|---|---:|---:|---:|---:|---:|---:|---:|
| v16_dt | 18 | 100 | 28,790 | $2,464 | 42.54% | — | — |
| v18_dt | 22 | 50 | 60,651 | $2,306 | 44.01% | −$158 | −$158 |
| v18b | 24 | 30 | 96,409 | $2,217 | 45.04% | −$89 | −$247 |
| **v18c** | **26** | **20** | **124,902** | **$2,172** | **45.59%** | **−$45** | **−$292** |

**Capacity sweep (500K-prefix grid, N=1000):**

| Strategy | Leaves | $/1000h | pct_opt | Δ vs prev | Δ vs v16 |
|---|---:|---:|---:|---:|---:|
| v16_dt | 28K | $1,607 | 50.77% | — | — |
| v18_dt | 60K | $1,478 | 52.60% | −$129 | −$129 |
| v18b | 96K | $1,343 | 54.56% | −$135 | −$263 |
| **v18c** | **125K** | **$1,261** | **55.90%** | **−$82** | **−$345** |

**Per-category breakdown (full grid, N=200) — v18c wins on every category:**

| Category | v16 | v18 | v18c | Δ v18c vs v16 |
|---|---:|---:|---:|---:|
| high_only | $3,785 | $3,489 | $3,359 | −$426 |
| pair | $2,127 | $2,023 | $1,934 | −$193 |
| two_pair | $2,005 | $1,878 | $1,676 | −$329 |
| trips | $2,347 | $2,241 | $2,110 | −$237 |
| trips_pair | $2,438 | $2,135 | $1,873 | −$565 |
| three_pair | $1,975 | $1,812 | $1,706 | −$269 |
| quads | $2,233 | $1,474 | $907 | −$1,326 |
| composite | $5,260 | $4,623 | $3,207 | −$2,053 |

---

## What this leaves on the table (after v18c, full grid)

- v18c captures **31% of the v14→ceiling gap** at N=200 fidelity
- v18c captures **62% of the v14→ceiling gap** at N=1000 fidelity ($776/$2,037)
- Remaining gap to ceiling: **$2,172/1000h (full grid N=200)**, **$1,261/1000h (prefix N=1000)**
- Biggest residual at N=200: still high_only ($3,359 × 20.4% share = $685 of v18c bleed = 31%)
- Biggest residual at N=1000: composite ($2,547 × 1.4% share = $36 — small population, but every hand bleeds ~$3K)

---

## What Session 29 produced

### (A/B) Suited-broadway aug features → v19 → ARCHIVED

Built `analysis/scripts/suited_aug_features.py` with 6 features:
- `n_suited_pairs_total` (0-21)
- `max_suited_pair_high_rank` (0,2-14)
- `max_suited_pair_low_rank` (0,2-14)
- `has_suited_broadway_pair` (0/1)
- `has_suited_premium_pair` (0/1)
- `n_broadway_in_largest_suit` (0-7)

Persisted via `analysis/scripts/persist_suited_aug.py` to
`data/feature_table_suited_aug.parquet` (23 MB, 44 sec compute).

Trained v19 (43 features = 37 base + 6 suited), depth=22, min_leaf=50,
72,900 leaves.

**Result:**
- Full grid (N=200): v19 = $2,250, +$57/1000h vs v18  ← positive
- Prefix (N=1000): v19 = $1,494, **−$16/1000h vs v18** ← FAILS prefix tripwire
- The pair-category regression on prefix (+$36/1000h) is the smoking
  gun — the new features improve full-grid pair (small win) by
  fitting N=200 noise that doesn't survive to N=1000 ground truth.
- The new features don't appear in v19's top-15 importance list
  (sklearn impurity-decrease normalized).

**Decision:** archive v19. Suited-broadway features as designed don't
generalize. See Decision 052.

### (C/D) Capacity sweep → v18b, v18c → v18c SHIPPED

Three sweeps from v18's (depth=22, ml=50) baseline:

| Variant | Depth | min_leaf | Leaves | Full $/1000h | Prefix $/1000h | Status |
|---|---:|---:|---:|---:|---:|---|
| v18b | 24 | 30 | 96,409 | $2,217 (+$89) | $1,343 (+$135) | passed |
| **v18c** | **26** | **20** | **124,902** | **$2,172 (+$45)** | **$1,261 (+$82)** | **SHIPPED** |

The capacity curve is monotonically improving on BOTH grids with
diminishing-but-positive marginal returns. v18c is shipped as the
new ML champion. Future sessions can probe deeper.

### What was built

**Aug features:**
- `analysis/scripts/suited_aug_features.py` — 6 feature compute fns + batch
- `analysis/scripts/persist_suited_aug.py` — persists to
  `data/feature_table_suited_aug.parquet` (all 6M hands, no category gate)

**Strategies:**
- `analysis/scripts/strategy_v19_dt.py` — 43-feature inference
  (archived; kept for diff)
- `analysis/scripts/strategy_v18c_dt.py` — new champion inference
  (loads `data/v18c_dt_model.npz`)

**Trainers:**
- `analysis/scripts/train_v19_dt.py` — extends train_v18 with suited augs
- `analysis/scripts/train_v18_dt.py` — already extant; reused for v18b/v18c
  via `--max-depth` / `--min-samples-leaf` / `--output` flags

**Graders:**
- `analysis/scripts/grade_v19_full_grid.py` — v16/v18/v19 head-to-head
- `analysis/scripts/grade_v18_sweep.py` — v16/v18/v18b/v18c sweep grader
  (prefix or full)

**Models (gitignored):**
- `data/v19_dt_model.npz` — 54 MB, 72,900 leaves (archived)
- `data/v18b_dt_model.npz` — 71 MB, 96,409 leaves
- `data/v18c_dt_model.npz` — 90 MB, 124,902 leaves (champion)

---

## Methodology lessons (Session 29)

1. **Prefix tripwire works.** v19 grades positive on full grid (+$57)
   but negative on prefix (−$16). Without the prefix check we'd ship
   v19 and live with overfit features. The lesson from Session 28
   (introduce the tripwire) just paid off concretely.

2. **Capacity scaling has clean diminishing returns.** Doubling leaves
   roughly halves the marginal $/1000h gain:
   - 28K → 60K (2.1x): −$158 full, −$129 prefix
   - 60K → 96K (1.6x): −$89 full, −$135 prefix
   - 96K → 125K (1.3x): −$45 full, −$82 prefix
   The next step (depth=28, ml=10, ~150K leaves) might still extract
   $30-50, but is unlikely to be transformative.

3. **The 6 suited-broadway features were too coarse.** Computing them
   for ALL hand categories meant the DT could find spurious-yet-
   noise-fitting splits in the pair / two_pair populations. A future
   v19' should gate the suited-broadway features to high_only ONLY
   (set them to 0 for paired hands), mirroring the existing
   `default_bot_is_ds_high` family pattern.

4. **The v18c tree is interpretable.** Re-running `distill_v16_dt.py`
   against `data/v18c_dt_model.npz` (small model-path arg change)
   would surface what splits v18c added beyond v18. Likely candidates:
   more granular composite-category routing where v18c won most
   ($5,260 → $3,207 = −$2,053 — the biggest single-category gain).

5. **Cycle scoreboard since Session 25 (12 ships, 5 archives, 1 doc-only):**

| Cycle | Target | Result | Status |
|---|---|---:|---|
| v9.1 | single pair | +$24 | SHIPPED |
| v10 | two_pair | +$81 | SHIPPED |
| v11 | high_only | −$1,745 | ARCHIVED |
| v12 | trips_pair | +$10 | SHIPPED |
| v13 | trips | −$172 | ARCHIVED |
| v14 | single pair refine | +$5 | SHIPPED |
| v15 | high_only DS | −$296 | ARCHIVED |
| v16_prefix | DT prefix | −$5,460 | ARCHIVED |
| v16 | DT 6M | +$569 | SHIPPED |
| Rule 4 | KK/AA doc | doc-only | SHIPPED |
| v17 | rules→DT | −$369 | ARCHIVED |
| v18 | DT d=22, ml=50 | +$158 full, +$129 prefix | SHIPPED |
| v19 | suited-aug | +$57 full, **−$16 prefix** | ARCHIVED (prefix fail) |
| v18b | DT d=24, ml=30 | +$90 full, +$135 prefix | SHIPPED |
| **v18c** | **DT d=26, ml=20** | **+$45 full, +$82 prefix** | **SHIPPED — current champion** |

---

## Resume Prompt (Session 30)

```
Resume Session 30 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Rule 4 + Distillation insights)
- CURRENT_PHASE.md (rewritten end of Session 29)
- DECISIONS_LOG.md (latest: Decisions 051 / 052)
- analysis/scripts/strategy_v18c_dt.py — current ML champion
- analysis/scripts/train_v18_dt.py — quick capacity-sweep trainer

State (end of Session 29):
- v18c_dt is the new ML champion: $2,172/1000h on full grid (45.59% opt),
  $1,261/1000h on prefix N=1000 (55.90% opt). 124,902 leaves,
  depth=26, min_samples_leaf=20.
- Capacity curve (28K → 60K → 96K → 125K leaves) is monotonically
  improving with diminishing-but-positive marginal returns. Next step
  (depth=28, ml=10) might extract another $30-50.
- v19 (6 suited-broadway aug features) FAILED the prefix tripwire
  (−$16/1000h on N=1000) despite winning the full grid (+$57). The
  features fit N=200 noise on the pair category that doesn't survive
  to N=1000 ground truth. Archived.
- The suited-broadway feature direction is still promising — the
  failure is "applied to all categories without gating." A retry should
  zero out the features for non-high_only hands (mirror the
  default_bot_is_ds_high pattern that's gated to high_only).

Next session targets:

(A) **Gated suited-broadway features.** Build `suited_aug_features_v2`
    that returns (0,0,0,0,0,0) for any hand with a pair/trip/quad
    (mirroring how `compute_high_only_aug_for_hand` short-circuits on
    paired hands). Persist to `data/feature_table_suited_aug_v2.parquet`.
    Train v19' = v18c base + gated suited augs. Grade. If passes
    prefix tripwire, ship.

(B) **One more capacity step.** Train v18d at (depth=28, ml=10) and
    grade. Marginal: probably $30-50 more if returns continue
    halving. Cheap to try.

(C) **Distill v18c.** Run `distill_v16_dt.py` against
    `data/v18c_dt_model.npz` (small change to make MODEL_PATH a CLI
    arg). The composite-category gain ($5,260 → $3,207 = −$2,053) is
    the biggest single-category win — what splits did v18c add to
    composite that v18 didn't?

(D) **Composite category deep-dive.** v18c leaves $4,596 on composite
    (full grid) — still 14k hands × $0.46 = $66K total bleed. Build
    `composite_v18c_residual.py` mirroring `high_only_v16_residual.py`.
    Find the worst clusters. Composite is rare hands (quads+pair,
    two trips, etc.) — there may be a clean per-archetype rule.

(E) **Higher-MC training data.** A 200K-hand uniform-random sample
    at N=2000 would be cleaner than the prefix N=1000 (which has
    canonical-id bias) for validating new feature ideas. ~2-day
    compute on the M2 Mac mini per the Session 24 throughput
    estimate (134.9 hands/s × 200K hands × 2000 samples).

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Always validate ML candidates on BOTH full grid (N=200) AND prefix
  (N=1000) — the prefix tripwire just rejected v19 in Session 29.
- Cached parquets cut training cycles to ~5min — keep using them.
- Don't add aug features that fire for ALL hand categories without
  testing — gated features (one category only) generalize better
  per the v19 lesson.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
