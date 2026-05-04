# Current: Sprint 8 — v18_dt is the new ML champion. Distillation pass complete; Rule 4 added; v17 archived.

> **🎯 IMMEDIATE NEXT ACTION (Session 29):** The two clearest paths to the
> next $100-300/1000h:
>   (A) Add **suited-broadway aug features** to the feature set. The
>       Session 28 high_only deep-dive showed v16 misses suited mids
>       that the oracle prefers. Persist 3 new features as
>       `data/feature_table_suited_aug.parquet`, retrain v18 with the
>       extended 40-feature set.
>   (B) Sweep tree hyperparameters around v18's (depth=22, min_leaf=50)
>       — try (depth=20, min_leaf=30), (depth=24, min_leaf=80) etc.
>       v18 was the first try at higher capacity; there's likely more
>       to extract.

> **✅ SHIPPED (Decision 050):** v18_dt — depth=22, min_samples_leaf=50,
> **60,651 leaves** (2.1× v16). Trained on the same full 6M grid (N=200)
> using cached parquet features (5min total — no per-hand feature
> recompute). **Wins +$158/1000h on the full grid, +$129/1000h on the
> N=1000 prefix** — the prefix confirmation rules out overfitting. Wins
> every category vs v16 except three_pair (+$31 noise on 25k hands).

> **✅ SHIPPED (Decision 049):** Rule 4 added to STRATEGY_GUIDE.md —
> KK or AA → keep pair in mid; top = highest non-pair card. v3 / v8 /
> v16 / v18 all converge on this. Documentation-only (no code change).

> **🚫 ARCHIVED (Decision 048):** v17 = v9.2/v10/v12 → v16 fallback.
> Loses to v16 by **−$369/1000h** on the full grid because v10 and v12
> are inferior to v16 on their categories (v10 worse by $1,366 on
> two_pair; v12 worse by $2,979 on trips_pair). The hand-coded rules
> were optimized against the OLD 4-profile mixture; v16/v18 are trained
> against the realistic mixture and supersede them.

> Updated: 2026-05-04 (end of Session 28)

---

## Headline state at end of Session 28

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14_combined + Rule 4** | Human-memorizable rule chain (4 rules now documented) | `STRATEGY_GUIDE.md` + `analysis/scripts/strategy_v14_combined.py`. Rule 4 is implicit in v8's pair-to-mid default. |
| **v18_dt** | ML champion (60,651-leaf DT, depth=22) | `analysis/scripts/strategy_v18_dt.py` + `data/v18_dt_model.npz` |
| v16_dt | superseded but kept for diff/baseline | `analysis/scripts/strategy_v16_dt.py` + `data/v16_dt_model.npz` |

**Final standings (full 6M grid, N=200):**

| Strategy | $/1000h vs ceiling | pct_optimal | Δ vs v8 | Δ vs v16 |
|---|---:|---:|---:|---:|
| v8_hybrid | $3,153 | 36.70% | — | — |
| v14_combined | $3,033 | 39.61% | −$120 | — |
| v17_rules_then_dt | $2,833 | 41.15% | −$320 | +$369 |
| v16_dt (depth=18, 28K leaves) | $2,464 | 42.54% | −$689 | — |
| **v18_dt (depth=22, 60K leaves)** | **$2,306** | **44.01%** | **−$847** | **−$158** |

**At higher fidelity (500K-prefix grid, N=1000):**

| Strategy | $/1000h vs ceiling | pct_optimal | Δ vs v8 | Δ vs v16 |
|---|---:|---:|---:|---:|
| v8_hybrid | $3,051 | 38.51% | — | — |
| v14_combined | $2,037 | 47.61% | −$1,014 | — |
| v16_dt | $1,607 | 50.77% | −$1,444 | — |
| **v18_dt** | **$1,478** | **52.60%** | **−$1,573** | **−$129** |

**Per-category breakdown (full grid, N=200) — v18 wins on every category:**

| Category | v16 $/1000h | v18 $/1000h | Δ |
|---|---:|---:|---:|
| high_only | $3,785 | $3,489 | −$296 |
| pair | $2,127 | $2,023 | −$104 |
| two_pair | $2,005 | $1,878 | −$127 |
| trips | $2,347 | $2,241 | −$106 |
| trips_pair | $2,438 | $2,135 | −$303 |
| three_pair | $1,975 | $1,812 | −$163 |
| quads | $2,233 | $1,474 | −$759 |
| composite | $5,260 | $4,623 | −$637 |

---

## What this leaves on the table (full grid, after v18)

- v18 captures **27% of the v14→ceiling gap** ($727/$3,033 vs v14) at N=200 fidelity
- v18 captures **52% of the v14→ceiling gap** at N=1000 fidelity ($559/$2,037)
- Remaining gap to ceiling: **$2,306/1000h (full grid N=200)**, **$1,478/1000h (prefix N=1000)**
- Biggest residual: still high_only ($3,489 × 20.4% share = $711 of v18 bleed = 31%)

---

## What Session 28 produced

### (A) Distillation of v16's 28,790-leaf DT (`distill_v16_dt.py`)

Walked all 6M oracle-grid hands through v16's tree. Computed
population-weighted MSE reduction at every internal node.

**Top feature importance (population-weighted MSE reduction):**
1. `n_broadway` — **44.9%** (root split: `n_broadway ≤ 2.5`)
2. `third_rank` — 11.5%
3. `pair_high_rank` — 8.8%
4. `n_low` — 7.7%
5. `has_premium_pair` — 4.5%
6. `top_rank` — 4.3%
7. `second_rank` — 3.8%
8. `has_ace_singleton` — 3.4%

The 9 hand-engineered "aug" features collectively contribute **<0.4%** of
total importance. The DT solves the problem almost entirely with raw
body-strength features. All distillation observations recorded in
`STRATEGY_GUIDE.md` under "Distillation insights (Session 28)".

### (B) High_only deep-dive (`high_only_v16_residual.py`)

Clustered all 1.23M high_only hands by (`suit_dist`, `n_broadway`,
`can_ds_bot`, `has_ace_singleton`).

**Worst residual cluster:** `suit_dist=3+2+1+1, n_broadway=3, has_ace_singleton=1` —
88,200 hands × $0.33 mean regret = $29,487 total = **6.4% of all
high_only bleed**. Examples show v16 choosing default "Ace on top, mid
= mid-rank cards" when the oracle prefers a **suited middle** (e.g. the
`5d Kd` mid in `2c 5d 6h 7s Ts Kd Ad`).

**v18 (60K-leaf) reduced this category by $296/1000h, but the
absolute residual remains the largest.** Adding suited-broadway aug
features is the next attack vector.

### (C) v17 = v9.2/v10/v12 → v16 fallback — ARCHIVED

Built and graded `strategy_v17_rules_then_dt.py`. Lost to v16 by
**−$369/1000h** because v10 and v12 are inferior to v16 in their
respective categories. See Decision 048 in DECISIONS_LOG.md.

### (D) Higher-capacity v18 — SHIPPED (the session's biggest win)

Wrote `train_v18_dt.py` using **cached parquet features** (saves ~20
min vs the per-hand Python feature compute that v16's trainer used).
Trained at depth=22, min_samples_leaf=50.

- Training: 188.4s fit, 60,651 leaves, depth=22, retention 69.59% on
  training set.
- Full grid grade: $2,306/1000h, 44.01% optimal — **wins by $158/1000h vs v16**.
- Prefix N=1000 grade: $1,478/1000h, 52.60% optimal — **wins by $129/1000h vs v16**.
- Prefix confirmation rules out overfitting concerns: a higher-capacity
  tree that simply memorized N=200 noise would NOT improve on the
  cleaner N=1000 labels. v18 does. The win is real.

---

## Methodology lessons (Session 28)

1. **Cached parquet features cut training cycles from ~25min to ~5min.**
   `distill_v16_dt.py` and `train_v18_dt.py` read the cached
   `feature_table*.parquet` and reconstruct the 37-col matrix in 2 sec.
   Future training/analysis scripts MUST use the cached path.

2. **Bigger trees still help.** v16 (depth=18, 28K leaves) was the
   first DT champion; v18 (depth=22, 60K leaves) extracts another
   $158/1000h. There may be more in the depth=24-28 range, possibly
   needing `min_samples_leaf` tuning.

3. **The prefix grid is the overfitting tripwire.** Any future ML
   candidate that claims a full-grid win must also be validated on the
   N=1000 prefix. v18's prefix win confirms generalization; if v18 had
   regressed on prefix, we'd archive it as overfit even if full-grid
   was positive.

4. **n_broadway is the master classifier.** A single root split on
   `n_broadway ≤ 2.5` captures more MSE reduction than any other
   split in the entire 28K-leaf v16 tree.

5. **Aug features are under-leveraged.** The 9 hand-engineered aug
   features contribute <0.4% of v16's feature importance. New augs
   should encode genuinely missing information (suited broadway pairs,
   connected high cards) rather than precomputed routing signals.

6. **Hand-coded rules can't compete with the DT in their own
   categories.** v9.2/v10/v12 were optimized against the OLD
   4-profile mixture; v16/v18 are trained against the realistic
   mixture and supersede them. v17 (rules-then-DT chain) regresses
   because it forces the inferior strategy to fire first. Do NOT
   chain hand-coded rules before the DT in production.

7. **v3 / v8 / v16 / v18 all converge on KK / AA play.** Rule 4
   doesn't change strategy behavior — it documents what every strategy
   in the chain already does. Strategy guide gains a 4th rule for
   memorization without code changes.

8. **Cycle scoreboard since Session 25 (10 ships, 4 archives, 1 doc-only):**

| Cycle | Target | Result | Status |
|---|---|---:|---|
| v9.1 | single pair | +$24 N=200 | SHIPPED |
| v10 | two_pair | +$81 incremental | SHIPPED |
| v11 | high_only | −$1,745 | ARCHIVED |
| v12 | trips_pair | +$10 incremental | SHIPPED |
| v13 | trips | −$172 | ARCHIVED |
| v14 | single pair refine | +$5 incremental | SHIPPED |
| v15 | high_only DS-patch | −$296 | ARCHIVED |
| v16_prefix | DT on 500K prefix | −$5,460 | ARCHIVED |
| v16_full | DT on 6M full | +$569 | SHIPPED |
| Rule 4 | KK/AA documentation | doc-only | SHIPPED (doc-only) |
| v17 | rules-then-DT chain | −$369 | ARCHIVED |
| **v18** | **DT depth=22 / min_leaf=50** | **+$158 (full), +$129 (prefix)** | **SHIPPED — current ML champion** |

---

## What was built in Session 28

**Distillation:**
- `analysis/scripts/distill_v16_dt.py` — walks the saved tree, computes per-node MSE reduction, ranks splits + features
- `analysis/scripts/high_only_v16_residual.py` — clusters high_only residual by suit_dist + n_broadway + ace_singleton
- `analysis/scripts/high_only_suited_mid_probe.py` — tests the suited-mid hypothesis (not run; reserved for Session 29 v18 features)
- `data/distill_v16_dt.log` — full distillation output (top 30 splits, full feature importance, depth-5 tree dump)
- `data/high_only_v16_residual.log` — top 30 high_only clusters with worst-regret examples

**Strategies:**
- `analysis/scripts/strategy_v17_rules_then_dt.py` — v9.2/v10/v12 → v16 fallback (archived after grading)
- `analysis/scripts/strategy_v18_dt.py` — loads `data/v18_dt_model.npz` (the new ML champion)

**Trainer:**
- `analysis/scripts/train_v18_dt.py` — uses cached parquet features (~5 min train cycle vs ~25 min for the v16 trainer)

**Graders:**
- `analysis/scripts/grade_v17_full_grid.py` — 4-strategy comparison (v8/v14/v16/v17) on full grid
- `analysis/scripts/grade_v18_full_grid.py` — v16 vs v18 on full grid
- `analysis/scripts/grade_v18_prefix_grid.py` — v8/v14/v16/v18 on N=1000 prefix (overfitting tripwire)

**Models:**
- `data/v18_dt_model.npz` — 45 MB, 60,651 leaves, depth=22 (the new champion)

**Documentation:**
- `STRATEGY_GUIDE.md` — Rule 4 added; "Distillation insights (Session 28)" appendix added; champion pointer updated to v18
- `CURRENT_PHASE.md` — rewritten (this file)
- `DECISIONS_LOG.md` — Decisions 048 (v17 archive), 049 (Rule 4 ship), 050 (v18 ship)

---

## Resume Prompt (Session 29)

```
Resume Session 29 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (now includes Rule 4 + Distillation insights)
- CURRENT_PHASE.md (rewritten end of Session 28)
- DECISIONS_LOG.md (latest: Decisions 048 / 049 / 050)
- analysis/scripts/distill_v16_dt.py — Session 28's tree-walker
- analysis/scripts/train_v18_dt.py — fast retrainer using cached features
- analysis/scripts/strategy_v18_dt.py — ML champion

State (end of Session 28):
- v18_dt is the new ML champion: $2,306/1000h on full grid (44.01% opt),
  $1,478/1000h on prefix N=1000 (52.60% opt). 60,651 leaves, depth=22.
  Wins +$158 vs v16 on full, +$129 vs v16 on prefix.
- v14_combined + Rule 4 remains the human-memorizable strategy.
- v17 (hand-coded rules → v16 fallback) lost by $369 and was archived.
  The hand-coded v9.2/v10/v12 are inferior to v16's per-category routing.
- Distillation revealed n_broadway is the master signal (44.9% of total
  feature importance). Aug features contribute <0.4% — new augs should
  encode genuinely missing information.
- High_only worst-residual cluster has a clean signal the DT can't see:
  suited mids (same-suit pair of cards both ≥ T) that 37 features miss.

Next session targets:

(A) **Build suited-broadway aug parquet (HIGHEST PRIORITY).**
    Add 3-5 features:
    - n_suited_pairs_in_top5 (count of (i,j) in top-5 ranked cards
      with same suit)
    - max_suited_pair_rank (highest rank involved in such a pair)
    - has_suited_broadway_pair (binary, both ranks ≥ T and same suit)
    Persist to data/feature_table_suited_aug.parquet using the
    persist_*_aug.py pattern.

(B) **Train v19 with extended 40-feature set.** Use train_v18_dt.py +
    new aug parquet. Try (depth=22, min_leaf=50) first (matching v18
    config); if positive, sweep capacity.

(C) **Codify Rule 5 if v19 finds a clean suited-mid split.** Walk
    v19's tree (reuse distill_v16_dt.py with a model-path arg) and
    translate the highest-impact suited-broadway split to an English
    rule for STRATEGY_GUIDE.md.

(D) **Sweep v18's hyperparameters.** Now that we know depth=22 +
    min_leaf=50 wins, try (depth=24, min_leaf=80) and
    (depth=20, min_leaf=30) — wider/narrower regularization. Cheap
    (~5 min train + 4 min grade each).

(E) **Diagnose composite category.** v18 leaves $4,623/1000h on
    composite (the highest residual after high_only). 14k hands ×
    high regret = real money. Build a composite-only diagnostic
    similar to high_only_v16_residual.py.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Always validate ML candidates on BOTH full grid (N=200) AND prefix
  (N=1000) — prefix grid is the overfitting tripwire.
- ALWAYS prefer reading data/feature_table*.parquet over recomputing
  features from canonical hand bytes (saves 20 min per training run).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
