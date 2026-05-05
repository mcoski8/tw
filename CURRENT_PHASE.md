# Current: Sprint 8 — Session 32 wrap. v25_dt is the new ML champion (gating template generalized to 4 categories: high_only, trips_pair, composite, pair). Pair audit confirmed pre-existing 3 features were already strictly category-gated (not v19 leakage); 6 new pair-gated features added.

> **🎯 IMMEDIATE NEXT ACTION (Session 33):**
>   (A) **two_pair_aug_gated.** Now the biggest UNTOUCHED lever —
>       22.3% × $1,458 = **$325/1000h share**. Existing
>       `feature_table_two_pair_aug.parquet` is UNGATED (Session 19);
>       audit and rebuild as `two_pair_aug_gated`. Train v26.
>   (B) **High_only round 2.** $590/1000h share, second-biggest
>       remaining. v23/v24/v25 didn't add anything for high_only.
>       Distill v25 on high_only specifically; candidate gated additions:
>       `connectivity_high_g`, `n_broadway_in_2nd_suit_g`. Train v27.
>   (C) **Pair second-pass diagnostic.** With pair now at $1,771 (still
>       largest residual share at $824/1000h), distill v25 on pair to
>       see which v25-pair-gated features are doing the work and whether
>       further pair feature engineering is warranted.

> **✅ SHIPPED (Decision 059):** v25_dt — depth=30, ml=5,
> **390,626 leaves**, 59 features (53 v24 features + 6 GATED pair
> features). Strictly dominates v24: **−$47/1000h on full**
> (pair drops $102), **−$18/1000h on prefix** (pair drops $41).
> 4th and largest-share clean instance of the gating template
> (population share 46.6%, biggest absolute headline gain since v20).

> **✅ AUDIT RESULT (Session 32, 2026-05-04):** The 3 pre-existing pair
> aug features (`default_bot_is_ds`, `n_top_choices_yielding_ds_bot`,
> `pair_to_bot_alt_is_ds`) were verified STRICTLY zero on every
> non-pair canonical row. They are NOT the v19 leakage pattern despite
> the inconsistent naming (no `_g` suffix). They've been
> category-gated since Session 17. Path taken from the resume prompt's
> two-option fork: option B (design 6-feature gated extension), not
> option A (rebuild from scratch).

> Updated: 2026-05-04 (end of Session 32)

---

## Headline state at end of Session 32

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14_combined + Rule 4** | Human-memorizable rule chain (4 rules) | `STRATEGY_GUIDE.md` + `analysis/scripts/strategy_v14_combined.py` |
| **v25_dt** | ML champion (390,626 leaves, 59 feat: 37 base + 6 gated suited + 6 gated trips_pair + 4 gated composite + 6 gated pair, plus the 3 Session-17 pair aug booleans which were already category-gated) | `analysis/scripts/strategy_v25_dt.py` + `data/v25_dt_model.npz` |
| v24_dt | Predecessor (53 feat); kept as a comparison baseline | `analysis/scripts/strategy_v24_dt.py` + `data/v24_dt_model.npz` |
| v23 / v20 / v18e / v18d / v18c / v18b / v18 / v16 | Superseded baselines; retained | `data/v*_dt_model.npz` |
| v20b (d=32) | ARCHIVED — capacity saturated, bit-identical to v20 | `data/v20b_dt_model.npz` |
| v19, v21, v22 | ARCHIVED (v19: prefix fail; v21/v22: Rule 5 rejected) | various |

**Capacity + feature progression (full 6M grid, N=200):**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| v16_dt | 18 | 100 | 37 | 28,790 | $2,464 | 42.54% | — |
| v18_dt | 22 | 50 | 37 | 60,651 | $2,306 | 44.01% | −$158 |
| v18b | 24 | 30 | 37 | 96,409 | $2,217 | 45.04% | −$89 |
| v18c | 26 | 20 | 37 | 124,902 | $2,172 | 45.59% | −$45 |
| v18d | 28 | 10 | 37 | 193,365 | $2,108 | 46.45% | −$64 |
| v18e | 30 | 5 | 37 | 274,446 | $2,066 | 47.08% | −$42 |
| v20 | 30 | 5 | 43 (gated suited) | 307,939 | $1,982 | 47.81% | −$84 |
| v20b | 32 | 5 | 43 (gated suited) | 307,939 | $1,982 | 47.81% | $0 (saturated) |
| v23 | 30 | 5 | 49 (43+6 gated TP) | 314,705 | $1,977 | 47.89% | −$5 vs v20 |
| v24 | 30 | 5 | 53 (49+4 gated comp) | 314,759 | $1,977 | 47.89% | −$1 vs v23 |
| **v25** | **30** | **5** | **59 (53+6 gated pair)** | **390,626** | **$1,929** | **48.43%** | **−$47 vs v24 (pair −$102)** |

**Same sweep on N=1000 prefix (overfitting tripwire):**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v18e | $1,082 | 59.30% | — |
| v20 | $1,082 | 59.31% | $0 |
| v23 | $1,073 | 59.47% | −$9 vs v20 |
| v24 | $1,072 | 59.48% | −$1 vs v23 |
| **v25** | **$1,054** | **59.80%** | **−$18 vs v24 (pair −$41)** |

**Per-category breakdown (full grid, N=200) — four gating wins visible:**

| Category | v18e (37 feat) | v20 (+suited) | v23 (+TP) | v24 (+comp) | v25 (+pair) | Δ v25 vs v18e |
|---|---:|---:|---:|---:|---:|---:|
| high_only | $3,307 | $2,894 | $2,894 | $2,894 | $2,894 | **−$413** (v20 win) |
| pair | $1,873 | $1,873 | $1,873 | $1,873 | $1,771 | **−$102** (v25 win) |
| two_pair | $1,458 | $1,458 | $1,458 | $1,458 | $1,458 | $0 |
| trips | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $0 |
| trips_pair | $1,608 | $1,608 | $1,447 | $1,447 | $1,446 | **−$162** (v23 win) |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | +$1 (noise) |
| quads | $724 | $724 | $724 | $723 | $723 | −$1 (noise) |
| composite | $2,100 | $2,100 | $2,080 | $1,864 | $1,869 | **−$231** (v24 win + small carryover) |

**The gating template is proven across 4 categories now.** Each champion
upgrade lifts ONLY its targeted category and keeps everything else
bit-identical (or within N=200 noise). Population shares span four
orders of magnitude: 0.245% (composite) up to 46.6% (pair). The pair
upgrade is the largest absolute headline gain since v20 because pair has
the biggest population share by far.

---

## What this leaves on the table

- v25 captures **36% of the v14→ceiling gap** at N=200 fidelity ($1,104/$3,033 vs v14)
- v25 captures **63% of the v14→ceiling gap** at N=1000 fidelity ($983/$2,037)
- Remaining gap to ceiling: **$1,929/1000h (full grid N=200)**, **$1,054/1000h (prefix N=1000)**
- Biggest residuals at full grid (per-category × share):
  - **pair**: 46.6% × $1,771 = **$824 share** — STILL the single biggest residual after v25's $102 win, but now harder to extract further; second-pass diagnostic recommended before more pair feature engineering
  - **high_only**: 20.4% × $2,894 = **$590 share** — second-biggest remaining lever; round 2 is a Session 33 candidate
  - **two_pair**: 22.3% × $1,458 = **$325 share** — biggest fully-untouched category and the cleanest Session 33 target
  - trips: 5.5% × $1,997 = $110, three_pair: 1.9% × $1,654 = $32
  - trips_pair: 2.86% × $1,447 = $41 (already gated)
  - composite: 0.245% × $1,869 = $4.6 (already gated)
- Per-category prioritization for Session 33: two_pair_aug_gated > high_only round 2 > pair second-pass

---

## What Session 32 produced

### Pair audit + v25 ship in one session

User asked for the pair audit from Session 31's resume prompt and let auto-mode run end-to-end:

- **Pair audit** → confirmed all 3 pre-existing pair aug features (`default_bot_is_ds`, `n_top_choices_yielding_ds_bot`, `pair_to_bot_alt_is_ds`) are STRICTLY zero on every non-pair canonical hand. They've been category-gated since Session 17, just without the `_g` naming convention. They are not the v19 leakage pattern. Path forked to "design 6-feature gated extension" (resume-prompt option B), not "rebuild gated from scratch" (option A).

- **6 new pair-gated features designed** (`pair_aug_features_gated.py`). The existing 3 features answered "is the bot DS under this routing?" (booleans / 0-3 bucket). The new 6 add rank- and mid-quality signal:
  - `pair_kickers_in_pair_suit_max_g` (0..5)
  - `pair_kickers_in_pair_suit_min_g` (0..5)
  - `pair_default_top_rank_g` (0..14)
  - `pair_alt_top_rank_g` (0..14)
  - `pair_alt_mid_suited_g` (0/1)
  - `pair_alt_mid_n_broadway_g` (0..2)

  Persistence took 35s for all 6M canonical hands → `data/feature_table_pair_aug_gated.parquet` (20 MB).

- **v25 trained** (depth=30, ml=5) — 390,626 leaves (vs v24's 314,759). The +75K-leaf delta is the largest since v20 and signals that the pair category genuinely had unmet partitioning need, not noise-fitting (the prefix tripwire confirms this).

- **v25 graded on both grids** — wins by $47/1000h (full) and $18/1000h (prefix). Pair category drops by $102/$41. Every other category bit-identical or within N=200 noise. Textbook gating-template signature.

### Methodology lessons (Session 32)

1. **The "is it leakage?" diagnostic should be a one-shot pyarrow read.** The audit (verifying that 3 features are zero on non-pair rows) was a single 5-second pandas script — should be the first step of every category audit going forward.

2. **Naming conventions catch up over time.** The 3 pair aug features lack the `_g` suffix because they predate the convention (Session 17 vs Session 30). They are still effectively gated. Don't conflate naming inconsistency with leakage; verify with the data.

3. **Population share matters more than per-hand bleed for picking next targets.** Pair has only $1,873/1000h regret (modest) but 46.6% share, so its absolute share is $873. v25's $102 per-category gain × 46.6% = $47 headline — by far the largest gating gain since v20. Compare composite (0.245% × $216 = $0.5).

4. **Capacity expansion is not always proportional to category size.** v25 used 75,867 more leaves than v24 (24% capacity expansion) for a 46.6% population share. The ratio is below proportional but well above v23/v24's ~6 leaves per pair-share-percent. The new pair features unlocked structural partitioning, not noise.

5. **Cycle scoreboard since Session 25 (18 ships, 7 archives, 1 doc-only):**

| Cycle | Target | Result | Status |
|---|---|---:|---|
| v9.1 / v10 / v12 / v14 | hand-coded rules | various | SHIPPED |
| v11 / v13 / v15 / v16_prefix / v17 / v19 | various | various | ARCHIVED |
| v16 | DT 28K leaves | +$569 vs v14 | SHIPPED |
| Rule 4 | KK/AA documentation | doc-only | SHIPPED |
| v18 / v18b / v18c / v18d / v18e | DT capacity sweep | various | SHIPPED |
| v19_gated | gated suited (d=28,ml=10) | +$73 / $0 vs v18d | SUPERSEDED |
| v20 | v18e capacity + gated suited | +$84 / $0 vs v18e | SHIPPED |
| v20b | DT d=32, ml=5 | $0 / $0 (saturated) | ARCHIVED |
| v21 / v22 | Rule 5 attempts | −$680 / −$473 vs v14 | ARCHIVED |
| v23 | gated trips_pair on v20 | +$5 / +$9 vs v20 | SHIPPED |
| v24 | gated composite on v23 | +$1 / +$1 vs v23 | SHIPPED |
| **v25** | **gated pair on v24** | **+$47 / +$18 vs v24** | **SHIPPED — current champion** |

---

## Resume Prompt (Session 33)

```
Resume Session 33 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (v25 champion section)
- CURRENT_PHASE.md (rewritten end of Session 32)
- DECISIONS_LOG.md (latest: Decision 059)
- analysis/scripts/strategy_v25_dt.py — current ML champion
- analysis/scripts/pair_aug_features_gated.py — newest gated family
  (fourth instance after suited / trips_pair / composite)

State (end of Session 32):
- v25_dt is the new ML champion: $1,929/1000h on full grid (48.43% opt),
  $1,054/1000h on prefix N=1000 (59.80% opt). 390,626 leaves, depth=30,
  min_samples_leaf=5, 59 features (37 base + 6 gated suited + 6 gated
  trips_pair + 4 gated composite + 6 gated pair, plus the 3 pre-Session-30
  pair aug booleans which were verified strictly category-gated).
- The gating template is now PROVEN across 4 categories spanning four
  orders of magnitude in population share (0.245% to 46.6%).
- Capacity sweep CLOSED — min_samples_leaf=5 saturates at depth=30.
  However, adding gated features expands leaf count (v25 has +75K leaves
  vs v24); the ml=5/d=30 ceiling is in feature-engineering, not raw capacity.

Next session targets (priority order by absolute share):

(A) **two_pair_aug_gated.** Biggest fully-untouched category at
    $325/1000h share. Existing `feature_table_two_pair_aug.parquet`
    (Session 19) is UNGATED. Audit and rebuild as
    `two_pair_aug_gated`. Likely 6 features for "which pair goes
    top", "singleton position", "DS-bot reachability" routing
    decisions. Train v26.

(B) **High_only round 2.** $590/1000h share, second-biggest
    remaining. v23/v24/v25 didn't add anything for high_only beyond
    Session 30. Distill v25 on high_only specifically; candidate
    additional gated features: `connectivity_high_g`,
    `n_broadway_in_2nd_suit_g`. Train v27.

(C) **Pair second-pass diagnostic.** Pair is still the largest
    residual share at $824/1000h. Distill v25 on pair to see which
    of v25's pair-gated features are doing the work and whether
    further pair feature engineering (e.g. v3-mid quality, kicker
    gap encoding) is warranted before declaring pair "done".

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated. Gating template
  is now proven 4× and is the default. Naming convention is `_g` suffix.
- Cached parquets cut training cycles to ~5 min.
- Capacity sweep is closed at the trainer-flag level — don't burn cycles
  increasing depth/ml. New features can still expand leaves organically.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
