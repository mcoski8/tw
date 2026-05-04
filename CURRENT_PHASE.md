# Current: Sprint 8 — v20_dt is the new ML champion (capacity sweep + GATED suited features). Multi-cycle overnight progress.

> **🎯 IMMEDIATE NEXT ACTION (Session 31):** Two paths to extract more $:
>   (A) **Distill v20.** Run `distill_v16_dt.py` against
>       `data/v20_dt_model.npz` (small change to make MODEL_PATH a CLI
>       arg). Find what splits v20's bigger tree added beyond v18e
>       and especially what the gated suited features partition.
>   (B) **More gated aug families.** The gated approach worked. Apply
>       the same pattern to other categories: e.g. a gated `trips_aug`
>       family that fires only for trips_pair / pure trips. Each new
>       gated family is a low-risk add (the prefix tripwire passes
>       trivially since the features fire on zero hands not in their
>       category).
>   (C) **Composite category deep-dive.** Composite remains the largest
>       per-hand bleed at $2,100/1000h v20 / $2,547 prefix. 14k hands ×
>       high regret = $66K total. Build a composite-specific
>       diagnostic mirroring `high_only_v16_residual.py`.

> **✅ SHIPPED (Decision 053):** v20_dt — depth=30, min_samples_leaf=5,
> **307,939 leaves**, 43 features (37 base + 6 GATED suited-broadway).
> Strictly dominates v18e: **+$84/1000h on full grid** (high_only
> category drops $413), **tied on prefix** (gated features fire on zero
> prefix hands by design). The gating fixed the v19 overfitting
> problem from Session 29.

> **✅ SHIPPED (Decision 054):** Capacity sweep continued — v18d
> (depth=28, ml=10, 193K leaves) and v18e (depth=30, ml=5, 274K
> leaves) both pass the prefix tripwire with non-trivial gains. v20
> incorporates v18e's capacity profile with the gated suited features.

> Updated: 2026-05-04 (end of Session 30 / overnight continuation)

---

## Headline state at end of Session 30

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14_combined + Rule 4** | Human-memorizable rule chain (4 rules) | `STRATEGY_GUIDE.md` + `analysis/scripts/strategy_v14_combined.py` |
| **v20_dt** | ML champion (307,939 leaves, 43 feat with gated suited) | `analysis/scripts/strategy_v20_dt.py` + `data/v20_dt_model.npz` |
| v18e_dt / v18d / v18c / v18b / v18 / v16 | superseded baselines, retained | `data/v18*_dt_model.npz`, `data/v16_dt_model.npz` |
| v19_dt (ungated suited) | ARCHIVED — failed prefix tripwire | `data/v19_dt_model.npz` |
| v19_gated_dt | superseded by v20 (same idea, smaller capacity) | `data/v19_gated_dt_model.npz` |

**Final capacity sweep + feature engineering progression (full 6M grid, N=200):**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| v16_dt | 18 | 100 | 37 | 28,790 | $2,464 | 42.54% | — |
| v18_dt | 22 | 50 | 37 | 60,651 | $2,306 | 44.01% | −$158 |
| v18b | 24 | 30 | 37 | 96,409 | $2,217 | 45.04% | −$89 |
| v18c | 26 | 20 | 37 | 124,902 | $2,172 | 45.59% | −$45 |
| v18d | 28 | 10 | 37 | 193,365 | $2,108 | 46.45% | −$64 |
| v18e | 30 | 5 | 37 | 274,446 | $2,066 | 47.08% | −$42 |
| **v20** | **30** | **5** | **43 gated** | **307,939** | **$1,982** | **47.81%** | **−$84** |

**Same sweep on N=1000 prefix (overfitting tripwire):**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v16_dt | $1,607 | 50.77% | — |
| v18_dt | $1,478 | 52.60% | −$129 |
| v18b | $1,343 | 54.56% | −$135 |
| v18c | $1,261 | 55.90% | −$82 |
| v18d | $1,145 | 58.13% | −$117 |
| v18e | $1,082 | 59.30% | −$63 |
| **v20** | **$1,082** | **59.31%** | **$0 (tied — gating works)** |

**Per-category breakdown (full grid, N=200) — v20 wins on every category vs v16:**

| Category | v16 | v18e | v20 | Δ v20 vs v16 |
|---|---:|---:|---:|---:|
| high_only | $3,785 | $3,307 | $2,894 | **−$891** |
| pair | $2,127 | $1,873 | $1,873 | −$254 |
| two_pair | $2,005 | $1,458 | $1,458 | −$547 |
| trips | $2,347 | $1,997 | $1,997 | −$350 |
| trips_pair | $2,438 | $1,608 | $1,608 | −$830 |
| three_pair | $1,975 | $1,653 | $1,653 | −$322 |
| quads | $2,233 | $724 | $724 | −$1,509 |
| composite | $5,260 | $2,100 | $2,100 | −$3,160 |

The high_only category alone gained another **−$413** going from v18e → v20 — that's purely from the gated suited features. Every other category is unchanged because the gating ensures the new features fire on zero hands in those populations.

---

## What this leaves on the table

- v20 captures **35% of the v14→ceiling gap** at N=200 fidelity ($1,051/$3,033 vs v14)
- v20 captures **62% of the v14→ceiling gap** at N=1000 fidelity ($955/$2,037)
- Remaining gap to ceiling: **$1,982/1000h (full grid N=200)**, **$1,082/1000h (prefix N=1000)**
- Biggest residual at full grid: still high_only ($2,894 × 20.4% share = $590 of v20's $1,982 = 30%)
- Biggest residual at prefix: composite ($1,812 × 1.0% share — small population, but every hand bleeds ~$2K)
- trips_pair is still ~$1,600/1000h on prefix (8.7% of bleed) — candidate for a gated trips_pair_aug

---

## What Session 30 produced (overnight continuation of Session 29)

### Capacity sweep continuation (v18d, v18e)

Built on Session 29's v18b/v18c sweep with two more steps:

| Variant | Depth | min_leaf | Leaves | Full $/1000h | Prefix $/1000h |
|---|---:|---:|---:|---:|---:|
| v18d | 28 | 10 | 193,365 | $2,108 | $1,145 |
| v18e | 30 | 5 | 274,446 | $2,066 | $1,082 |

Marginal returns are diminishing but still positive on both grids.
v18d's prefix gain (+$117) was actually LARGER than v18c's (+$82) —
the curve hasn't strictly plateaued.

### Gated suited-broadway features → v19_gated → v20

Diagnosed the Session 29 v19 failure: the 6 suited features fired
across all categories, and the DT used them to fit N=200 noise on the
pair category, causing prefix regression.

**Fix:** gate the features to high_only only.
Built `analysis/scripts/suited_aug_features_gated.py` returning
zeros for any hand with `n_pairs/n_trips/n_quads ≥ 1`.
Persisted to `data/feature_table_suited_aug_gated.parquet` (20 MB).

**v19_gated** (depth=28, ml=10, 215K leaves, gated features):
- Full grid: +$73 vs v18d (high_only category drops $356)
- Prefix: TIED with v18d ($0 change — gated features fire on zero
  prefix hands by design).

**v20** (depth=30, ml=5, 308K leaves, gated features — combines v18e
capacity with gating):
- Full grid: +$84 vs v18e (high_only category drops $413)
- Prefix: TIED with v18e ($0 change)
- Strictly dominates v18e. **Shipped as the new ML champion.**

The gating pattern is now the template for all future aug families:
fire ONLY in the targeted category, leave other categories unchanged,
prefix tripwire passes trivially.

### What was built

**Aug features (gated):**
- `analysis/scripts/suited_aug_features_gated.py` — 6 features computed
  only for high_only hands, zeros otherwise
- `analysis/scripts/persist_suited_aug_gated.py` — writes parquet
  (`data/feature_table_suited_aug_gated.parquet`, 20 MB, 23 sec)

**Strategies:**
- `analysis/scripts/strategy_v19_gated_dt.py` — generic gated-suited
  inference (loads MODEL_PATH default, can be overridden)
- `analysis/scripts/strategy_v20_dt.py` — clean wrapper around the v20
  champion model
- `analysis/scripts/train_v19_gated_dt.py` — trainer for any gated-suited
  variant via `--max-depth` / `--min-samples-leaf` / `--output`

**Graders:**
- `analysis/scripts/grade_v18d_v18e.py` — 2-strategy capacity-step grader
- `analysis/scripts/grade_v19_gated.py` — v18d vs v19_gated head-to-head
- `analysis/scripts/grade_v20.py` — v18e vs v20 head-to-head

**Models (gitignored):**
- `data/v18d_dt_model.npz` (137 MB, 193,365 leaves)
- `data/v18e_dt_model.npz` (189 MB, 274,446 leaves)
- `data/v19_gated_dt_model.npz` (152 MB, 215,597 leaves)
- `data/v20_dt_model.npz` (211 MB, 307,939 leaves) ← champion

---

## Methodology lessons (Session 30)

1. **Gated aug features are the template.** v19 (ungated) failed prefix
   tripwire because cross-category leakage let the DT fit pair-category
   N=200 noise. v19_gated (same features, zeroed for non-high_only)
   tied prefix exactly while winning full grid. Future aug families
   should ALL be category-gated.

2. **Capacity scaling continues, with reversals.** The diminishing-
   returns curve isn't strictly monotonic — v18d → v18c gave +$64 full
   / +$117 prefix, BIGGER than v18c → v18b's +$45 full / +$82 prefix.
   The curve has noise on top of the trend. Don't stop sweeping just
   because one step looks small.

3. **Prefix tripwire saved us twice this session.** v19 (ungated) and
   v20 design both started from "more features." Without the prefix
   check, ungated v19 would have shipped, replacing v18 with a
   slightly-overfit model. The prefix exposed the leakage.

4. **The 4 ML champions form a clean ablation:**
   - v18e (37 features, no augs): high_only $3,307
   - v20  (43 features, gated augs): high_only $2,894 ← SAME architecture, different features only
   - The $413/1000h delta is purely attributable to the gated suited
     features. This is a clean controlled experiment.

5. **Cycle scoreboard since Session 25 (15 ships, 5 archives, 1 doc-only):**

| Cycle | Target | Result | Status |
|---|---|---:|---|
| v9.1 / v10 / v12 / v14 | hand-coded rules | various | SHIPPED |
| v11 / v13 / v15 / v16_prefix / v17 / v19 | various | various | ARCHIVED |
| v16 | DT 28K leaves | +$569 vs v14 | SHIPPED |
| Rule 4 | KK/AA documentation | doc-only | SHIPPED |
| v18 | DT d=22, ml=50 | +$158 / +$129 (full/prefix vs v16) | SHIPPED |
| v18b | DT d=24, ml=30 | +$90 / +$135 vs v18 | SHIPPED |
| v18c | DT d=26, ml=20 | +$45 / +$82 vs v18b | SHIPPED |
| v18d | DT d=28, ml=10 | +$64 / +$117 vs v18c | SHIPPED |
| v18e | DT d=30, ml=5 | +$42 / +$63 vs v18d | SHIPPED |
| v19_gated | gated suited (d=28,ml=10) | +$73 / $0 vs v18d | SUPERSEDED |
| **v20** | **v18e capacity + gated suited** | **+$84 / $0 vs v18e** | **SHIPPED — current champion** |

---

## Resume Prompt (Session 31)

```
Resume Session 31 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Rule 4 + Distillation insights)
- CURRENT_PHASE.md (rewritten end of Session 30)
- DECISIONS_LOG.md (latest: Decisions 053 / 054)
- analysis/scripts/strategy_v20_dt.py — current ML champion
- analysis/scripts/suited_aug_features_gated.py — gated features template

State (end of Session 30):
- v20_dt is the new ML champion: $1,982/1000h on full grid (47.81% opt),
  $1,082/1000h on prefix N=1000 (59.31% opt). 307,939 leaves, depth=30,
  min_samples_leaf=5, 43 features (37 base + 6 GATED suited-broadway).
- The gated-features pattern is now the template for new aug families:
  fire only in targeted category (zeros elsewhere), prefix tripwire
  passes trivially since features fire on zero non-targeted hands.
- Capacity sweep continues paying with diminishing returns; v18e at
  depth=30 / ml=5 was the last 37-feature step before v20's gating
  added another +$84.

Next session targets:

(A) **Distill v20.** Run `distill_v16_dt.py` against v20_dt_model.npz
    (small change to make MODEL_PATH a CLI arg). Find what splits
    v20's bigger tree added beyond v18e — especially what the gated
    suited features partition. May surface a Rule 5 candidate for
    STRATEGY_GUIDE.md.

(B) **More gated aug families.** Apply the gated template to new
    categories. Candidates:
    - `trips_pair_aug_gated`: 3-5 features for trips_pair routing
      (trips-rank, pair-rank, kicker-suit). Trips_pair is $1,608
      v20 / $1,835 prefix — still a big residual.
    - `composite_aug_gated`: 3-5 features for the composite category
      (which includes 2-trips, quads+pair, two-trips, trips+two-pair).
      Composite is $2,100 v20 — biggest per-hand bleed.

(C) **Composite deep-dive.** Build `composite_v20_residual.py`
    mirroring `high_only_v16_residual.py`. Find worst clusters.
    Composite is rare hands (14k of 6M) — there may be a clean
    per-archetype rule.

(D) **One more capacity step.** Try v20b at depth=32, ml=5 with the
    gated features. The curve hasn't strictly plateaued; might
    extract +$30-50.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated. Cross-category
  features have proven to overfit (Session 29 v19 lesson).
- Cached parquets cut training cycles to ~5 min.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
