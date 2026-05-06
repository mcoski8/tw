# Current: Sprint 8 — Session 36 wrap (incl. overnight cascade). v31_dt is the new ML champion. Second-largest single ship in project history (after v26): −$58/1000h full, −$29/1000h prefix vs v30. ZERO new features — pure capacity expansion (depth=30→32, ml=5→3). v30 (gated trips, 8th gating template) shipped earlier same session.

> **🎯 IMMEDIATE NEXT ACTION (Session 37):**
>   (A) **v32 candidate: stack v31b features (trips_v2 round 2) on v31's
>       capacity config.** Train at depth=32 ml=3 with 83 features
>       (79 v31 + 4 trips_v2). Expected ~$15/1000h incremental on top
>       of v31's $58 — would make total v32 vs v30 = ~$73/1000h, tying
>       v26 as the largest single ship in project history. v31b's
>       trips_v2 features are already persisted at
>       `data/feature_table_trips_aug_v2_gated.parquet`. Just need a
>       new train_v32_dt.py that extends train_v30_dt to read trips_v2
>       parquet at higher capacity.
>   (B) **Rule 6 verification: does v14_combined already encode Always
>       A_paired_mid for trips?** Read `analysis/scripts/strategy_v14_combined.py`
>       and trace what it does on a single-trips hand. If it doesn't
>       always set 2-of-3 trips on mid, codify Rule 6 (the structural
>       analog of Rule 4 for trips, extended beyond KKK/AAA to all
>       trip ranks). Worth ~$85/1000h whole-grid if the rule is missing.
>   (C) **KK/AA single-suited Rule-4-bot residual** ($37/1000h below
>       oracle, 52.9% of KK/AA). v31a (pair_r4v3 KK/AA-tight) shipped
>       only +$6 — the categorical-coarseness hypothesis was correct
>       but the headline didn't materialize. A different angle is
>       needed: meta-classifier feature trained on probe data, OR a
>       sub-tree dedicated to KK/AA hands.

> **✅ SHIPPED (Decision 065 + 066):** Two ships in Session 36:
> - **v30_dt** — depth=30, ml=5, **493,057 leaves** (+6,715 vs v29),
>   79 features (73 v29 + 6 GATED `trips_*` features). 8th gating-
>   template instance. **−$13/1000h full, −$15/1000h prefix vs v29**
>   (trips drops $239 within-trips on full, $289 on prefix; all other
>   categories bit-identical).
> - **v31_dt** — depth=32, ml=3, **699,773 leaves** (+206,716 vs v30,
>   +42% capacity), same 79 features as v30. **−$58/1000h full, −$29
>   prefix vs v30** (ALL 8 categories improve simultaneously; biggest
>   gains on previously-gated categories: composite −$346, trips_pair
>   −$217, two_pair −$108).

> **🌙 OVERNIGHT CASCADE COMPLETED (Session 36 → 37):**
> Three v31 candidates ran sequentially via `analysis/scripts/overnight_v31_cascade.sh`:
>
> | Candidate | Approach | Full Δ vs v30 | Prefix Δ vs v30 | Status |
> |---|---|---:|---:|---|
> | v31a | pair_r4v3 KK/AA-tight (4 features) | +$6 | $0 | ARCHIVED |
> | v31b | trips_v2 round 2 (4 features) | +$15 | +$13 | ARCHIVED (slated for v32 stack) |
> | **v31** (was v31c) | **v30 features at depth=32 ml=3** | **+$58** | **+$29** | **SHIPPED** |
>
> Total cascade wall time ~80 min. Logs at `/tmp/{persist,train,grade}_v31{a,b,c}_*.log`.
> Summary at `/tmp/v31_overnight_summary.md`.

> **🔬 DIAGNOSTIC + DESIGN CHAIN (Session 36):**
> 1. **v29 KK/AA round-2 audit** (`distill_v29_pair.py`): v29 closed
>    only $7 of v27's $14 KK/AA Rule-4 deficit. Single-suited Rule-4-
>    bot stratum is $37/1000h below oracle (52.9% of KK/AA).
>    v29's `pair_r4_bot_suit_profile_g` categorical encoding is too
>    coarse — single-suited has substantial within-bucket structure.
> 2. **Pivoted to trips diagnostic** (`distill_v29_trips.py`): largest
>    gap-to-baseline ever measured. v29 was $85/1000h whole-grid
>    WORSE than always-A_paired_mid on trips. Diagnostic-prescribed
>    6 trips-gated features (`trips_*_g`).
> 3. **v30 trained**: 0/6 in top-30 importance (tripwire predicted
>    small headline). Confirmed: $13 full / $15 prefix.
> 4. **Overnight cascade tested 3 v31 hypotheses simultaneously.**
>    The CAPACITY hypothesis won decisively: 79 features had been
>    encoded since v30 but not fully expressed within the 493K-leaf
>    budget. depth=32 ml=3 grows to 700K leaves (+42%) and unlocks
>    $58/1000h of latent signal.
> 5. **v31 ships** with no new features. Methodological precedent
>    set: capacity expansion is an orthogonal axis to feature design;
>    when feature-count grows ≥40 above last capacity-saturation test,
>    RE-TEST capacity.

> **📓 METHODOLOGY LESSONS REINFORCED (Session 36):**
> - **Tripwire confirmed 5×** (v25 5/6→+$47, v26 3/6→+$70, v27 0/4→+$6,
>   v29 3/4→+$46, v30 0/6→+$13, v31a 0/4→+$6, v31b 0/4→+$15). Tripwire
>   predicts CONVERSION rate (~10-15%), not absolute opportunity.
> - **Capacity expansion is orthogonal to feature design.** v25-v30's
>   6 cumulative ships totaled −$260; v31 alone (capacity-only) ships
>   −$58 = 22% of cumulative feature work. Whenever a ship has a
>   bearish tripwire AND leaf-count gain ≤10K, run a capacity sweep
>   BEFORE adding more features.
> - **The v20/v20b "capacity saturated" finding doesn't generalize
>   unbounded.** It was at 43 features with 308K leaves. By v30
>   (79 features, 493K leaves), depth=32 unlocks $58. Re-test capacity
>   whenever feature count grows substantially.
> - **Categorical features can be too coarse, but tighter gating
>   doesn't always help.** v31a's KK/AA-tight gating shipped only
>   +$6 despite being well-targeted. The KK/AA single-suited stratum
>   needs a fundamentally different angle, not just finer features.
> - **"Always-X" structural baselines surface Rule-N candidates.**
>   The trips diagnostic surfaced "Always A_paired_mid" as a Rule 6
>   candidate worth $85/1000h. Future sessions should systematically
>   check for structural always-X baselines for each category.

> Updated: 2026-05-06 (end of Session 36 + overnight cascade)

---

## Headline state at end of Session 36 (incl. overnight)

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14 + Rule 4 + Rule 5** (5 numbered rules) | Human-memorizable strategy | `STRATEGY_GUIDE.md` Part 6 + `analysis/scripts/strategy_v28_rule5_rainbow.py` |
| **v31_dt** | ML champion (699,773 leaves, 79 features at depth=32 ml=3 — 37 base + 8 gated families: 6 suited + 6 trips_pair + 4 composite + 6 pair v1 + 6 two_pair + 4 high_only + 4 pair_r4 + 6 trips) | `analysis/scripts/strategy_v31_dt.py` + `data/v31_dt_model.npz` |
| v30_dt | Predecessor at depth=30 ml=5 (493K leaves, same 79 features) | `analysis/scripts/strategy_v30_dt.py` + `data/v30_dt_model.npz` |
| v29_dt | Older baseline (73 feat); kept as comparison | `analysis/scripts/strategy_v29_dt.py` + `data/v29_dt_model.npz` |
| v27_dt | Older baseline (69 feat); kept | `data/v27_dt_model.npz` |
| v26 / v25 / v24 / v23 / v20 / v18e / v16 | Superseded baselines; retained | `data/v*_dt_model.npz` |
| v20b (d=32) | ARCHIVED — capacity saturated at 43 features (true at the time, but doesn't generalize to 79 features) | `data/v20b_dt_model.npz` |
| v31a / v31b | ARCHIVED candidates from overnight cascade — lost to v31c (depth=32 ml=3 capacity retrain) | `data/v31{a,b}_dt_model.npz` |
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
| v30 | 30 | 5 | 79 (73+6 gated trips) | 493,057 | $1,794 | 49.98% | −$13 vs v29 |
| **v31** | **32** | **3** | **79 (same as v30)** | **699,773** | **$1,736** | **50.92%** | **−$58 vs v30 (capacity-only)** |

**Same sweep on N=1000 prefix:**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v18e | $1,082 | 59.30% | — |
| v25 | $1,054 | 59.80% | −$28 |
| v26 | $1,002 | 60.80% | −$52 |
| v27 | $1,002 | 60.80% | $0 |
| v29 | $965 | 61.32% | −$37 vs v27 |
| v30 | $951 | 61.53% | −$15 vs v29 |
| **v31** | **$921** | **62.07%** | **−$29 vs v30** |

**Per-category breakdown (full grid, N=200):**

| Category | v18e | v20 | v25 | v26 | v27 | v29 | v30 | v31 | Δ v31 vs v18e |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high_only  | $3,307 | $2,894 | $2,894 | $2,894 | $2,863 | $2,862 | $2,862 | **$2,816** | **−$491** |
| pair       | $1,873 | $1,873 | $1,771 | $1,771 | $1,771 | $1,674 | $1,674 | **$1,639** | **−$234** |
| two_pair   | $1,458 | $1,458 | $1,458 | $1,145 | $1,145 | $1,145 | $1,145 | **$1,037** | **−$421** |
| trips      | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,758 | **$1,732** | **−$265** |
| trips_pair | $1,608 | $1,608 | $1,446 | $1,445 | $1,445 | $1,443 | $1,442 | **$1,225** | **−$383** |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | **$1,639** | **−$14** |
| quads      | $724 | $724 | $723 | $723 | $723 | $723 | $723 | **$645** | **−$79** |
| composite  | $2,100 | $2,100 | $1,869 | $1,741 | $1,741 | $1,741 | $1,733 | **$1,387** | **−$713** |

**Eight category-gated wins now visible** plus one capacity-only ship (v31). The capacity ship's biggest gains are on previously-gated categories — confirms gating-template features had been adding signal that v30's leaf budget couldn't fully express.

---

## What this leaves on the table

- v31 captures **42.8% of the v14→ceiling gap** at N=200 fidelity ($1,297/$3,033 vs v14)
- v31 captures **70.2% of the v14→ceiling gap** at N=1000 fidelity ($1,116/$2,037)
- Remaining gap to ceiling: **$1,736/1000h (full grid N=200)**, **$921/1000h (prefix N=1000)**
- Biggest residuals at full grid (per-category × share):
  - **high_only**: 20.4% × $2,816 = **$574 share** — largest residual
  - **pair**: 46.6% × $1,639 = **$764 share** — KK/AA single-suited Rule-4-bot is the largest sub-stratum (open for v32+)
  - **two_pair**: 22.3% × $1,037 = **$231 share** — already gated + capacity-improved
  - **trips**: 5.5% × $1,732 = **$95** — v30 captured $13, v31 capacity adds $26; v32 round-2 (v31b features at v31's capacity) candidate
  - three_pair: 1.9% × $1,639 = $31 (untouched by gating)
  - trips_pair: 2.86% × $1,225 = $35 (already gated, capacity adds substantial)
  - composite: 0.245% × $1,387 = $3.4 (already gated, biggest within-category capacity gain)

---

## What Session 36 (incl. overnight) produced

### v30 ship + v29 KK/AA round-2 audit + overnight v31 cascade

**1. v29 round-2 pair audit** (`distill_v29_pair.py`): v29 closed only $7/1000h of v27's $14 KK/AA Rule-4 deficit. Stratification by Rule-4-bot suit profile localized the residual to the single-suited stratum (52.9% of KK/AA, $37/1000h below oracle). v29's categorical `pair_r4_bot_suit_profile_g` is too coarse for this stratum.

**2. Trips diagnostic** (`distill_v29_trips.py`): largest gap-to-baseline ever measured. v29 was $85/1000h whole-grid WORSE than always-A_paired_mid. v29 picks A on 79.9% of trips; the 20.1% deviations are systematically wrong, especially on low-rank trips.

**3. v30 designed and shipped** — 6-feature `trips_*_g` family. 79 features total, depth=30 ml=5, 493,057 leaves. **−$13 full / −$15 prefix vs v29.** All categories except trips bit-identical (textbook gating signature). 8th gating-template instance.

**4. Overnight v31 cascade** ran 3 candidates:
- **v31a** (pair_r4v3 KK/AA-tight, 4 features): +$6 full / $0 prefix. Within-pair −$13 on full. Modest.
- **v31b** (trips_v2 round 2, 4 features for C_top + finer A/B): +$15 full / +$13 prefix. Within-trips −$277 on full. Solid round-2 ship.
- **v31** (was v31c — v30 features at depth=32 ml=3): **+$58 full / +$29 prefix.** All 8 categories improve. Second-largest single ML ship.

**5. v31 promoted to ML champion** — model file renamed `data/v31_dt_model.npz`, strategy module at `analysis/scripts/strategy_v31_dt.py`. Decision 066 written.

### Methodology lessons reinforced (Session 36)

1. **Capacity expansion is an orthogonal axis to feature design.** v31's $58 ship is 22% of v25-v30's cumulative $260 feature-design work. Capacity unlocks signal already encoded but not expressed.

2. **Re-test capacity when feature-count grows substantially.** v20/v20b at 43 features showed depth=32 saturated. At v30's 79 features, depth=32 ml=3 unlocks $58. The "capacity saturated" conclusion has a feature-count ceiling.

3. **Tripwire confirmed across 7 ships now** (incl. v31a/b). 0/N → small, 3+/N → big. v31 itself didn't go through the tripwire (no new features); capacity is orthogonal.

4. **Tighter gating doesn't always help.** v31a's KK/AA-tight gating shipped only +$6. The categorical-coarseness hypothesis was correct but the headline didn't materialize via tighter gating alone. Different angle needed.

5. **Always-X structural baselines surface Rule-N candidates.** Always A_paired_mid for trips = Rule 6 candidate worth $85/1000h. Verify against v14_combined.

---

## Resume Prompt (Session 37)

```
Resume Session 37 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (last updated end of Session 36 — Session 36 entry
  in Part 1 covers BOTH v30 and v31 ships)
- CURRENT_PHASE.md (rewritten end of Session 36)
- DECISIONS_LOG.md (latest: Decision 066 — v31 capacity-only ship)
- analysis/scripts/strategy_v31_dt.py — current ML champion
- analysis/scripts/strategy_v30_dt.py — predecessor (same 79 features
  at depth=30 ml=5 instead of depth=32 ml=3)
- analysis/scripts/distill_v29_trips.py — v30 origin diagnostic
- analysis/scripts/distill_v29_pair.py — v29 KK/AA round-2 audit
  (single-suited Rule-4-bot stratum still leaks $37/1000h, deferred)

State (end of Session 36 + overnight):
- v31_dt is the new ML champion: $1,736/1000h on full grid (50.92% opt),
  $921/1000h on prefix N=1000 (62.07% opt). 699,773 leaves, depth=32,
  min_samples_leaf=3, 79 features (same as v30).
- Second-largest single ML ship in project history (−$58/1000h full,
  −$29 prefix vs v30) achieved with ZERO new features. Pure capacity
  expansion (depth=30→32, ml=5→3, +207K leaves = +42%).
- v30 (gated trips, 8th gating-template instance) shipped earlier
  same session: −$13 full / −$15 prefix vs v29.
- All 8 categories improve under v31; biggest gains on previously-
  gated categories (composite −$346, trips_pair −$217, two_pair −$108).

Next session targets (priority order):

(A) v32 candidate: stack v31b features (trips_v2 round 2, 4 features
    for C_top_trip + finer A/B routing) on v31's high-capacity config.
    Train at depth=32 ml=3 with 83 features (79 v31 + 4 trips_v2).
    Expected ~$15 incremental on top of v31's $58 = total v32 vs v30
    around $73, would tie v26 as largest single ship.
    v31b features already persisted at
    `data/feature_table_trips_aug_v2_gated.parquet`. Just need
    train_v32_dt.py extending train_v30_dt at higher capacity.

(B) Rule 6 verification: does v14_combined already encode Always
    A_paired_mid for trips? Read strategy_v14_combined.py and trace
    on a single-trips hand. If missing, codify Rule 6 (structural
    analog of Rule 4 for trips, extended beyond KKK/AAA to all trip
    ranks). Worth ~$85/1000h whole-grid if rule isn't already there.

(C) KK/AA single-suited Rule-4-bot stratum ($37/1000h below oracle).
    v31a's KK/AA-tight features shipped only +$6 — different angle
    needed. Options: (i) meta-classifier feature trained on probe
    data, (ii) sub-tree dedicated to KK/AA hands, (iii) leave it
    open and revisit after v32.

(D) After v32, consider depth=34 ml=2 capacity test as the next
    capacity ceiling. Pattern: re-test capacity whenever feature-
    count grows ≥10 above last sweep.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts: PYTHONUNBUFFERED=1 or python3 -u.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated and use a UNIQUE
  prefix. Claimed: `_g` (suited), `tp_*_g` (trips_pair), `comp_*_g`
  (composite), `pair_*_g` (pair v1), `t2p_*_g` (two_pair), `ho_*_g`
  (high_only), `pair_r4_*_g` (pair v2), `trips_*_g` (trips), and
  archived: `pair_r4v3_*_g` (KK/AA-tight) + `trips_v2_*_g` (trips
  round 2, slated for v32).
- Methodology rule (Session 36): default future ML champion ships
  to depth=32 ml=3. Re-test capacity (depth=34 ml=2) when feature
  count grows substantially.
- Methodology rule (Session 36): tripwire predicts conversion rate
  (~10-15%), not absolute opportunity.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
