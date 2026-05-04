# Current: Sprint 8 — Session 31 wrap. v24_dt is the new ML champion (gating template generalized to 3 categories: high_only, trips_pair, composite). v20b ARCHIVED, Rule 5 candidates ARCHIVED.

> **🎯 IMMEDIATE NEXT ACTION (Session 32):**
>   (A) **two_pair_aug_gated.** Biggest UNTOUCHED lever after pair —
>       22.3% × $1,458 = **$325/1000h share**. Existing
>       `feature_table_two_pair_aug.parquet` is UNGATED (Session 19);
>       audit and rebuild as `two_pair_aug_gated`. Train v25.
>   (B) **Pair category audit.** Pair is the SINGLE biggest residual
>       (46.6% × $1,873 = **$873/1000h share**). Already has 3 ungated
>       aug features. Diagnostic question: are they cross-category
>       leakage (the v19 lesson) or genuine help? If leakage, replace
>       with proper gated versions; if genuine, design a 6-feature
>       `pair_aug_gated` v2.
>   (C) **High_only round 2.** v23/v24 didn't add anything for high_only.
>       It remains $2,894/1000h (3rd-biggest share at $590). Distill v24
>       on high_only specifically; candidate gated additions:
>       `connectivity_high_g`, `n_broadway_in_2nd_suit_g`.

> **✅ SHIPPED (Decision 058):** v24_dt — depth=30, ml=5,
> **314,759 leaves**, 53 features (49 v23 features + 4 GATED composite
> features). Strictly dominates v23: **+$1/1000h on full**
> (composite drops $216), **+$1/1000h on prefix** (composite drops $201).
> Headline gain at noise floor because composite is 0.245% of population,
> but the per-category effect is unambiguous: 3rd clean instance of the
> gating template.

> **✅ SHIPPED (Decision 057):** v23_dt — depth=30, ml=5,
> **314,705 leaves**, 49 features (43 v20 features + 6 GATED trips_pair
> features). Beat v20: **+$5/1000h full**, **+$9/1000h prefix**
> (trips_pair drops $161 / $179). 2nd instance of the gating template
> after v20→high_only.

> **❌ ARCHIVED (Decision 055):** v20b (depth=32, ml=5) — bit-identical
> to v20. min_samples_leaf=5 is the binding constraint at depth=30;
> capacity sweep is closed.

> **❌ REJECTED (Decision 056):** Rule 5 candidates (suited-mid for
> high_only). Both naive (msphr ≥ 9, v21) and tightened (msphr ≥ 11
> AND msplr ≥ 9, v22) variants LOSE head-to-head against v14_combined:
> v21 = −$680/1000h, v22 = −$473/1000h. Stop at Rule 4 for the human
> chain.

> Updated: 2026-05-04 (end of Session 31)

---

## Headline state at end of Session 31

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14_combined + Rule 4** | Human-memorizable rule chain (4 rules) | `STRATEGY_GUIDE.md` + `analysis/scripts/strategy_v14_combined.py` |
| **v24_dt** | ML champion (314,759 leaves, 53 feat: 37 base + 6 gated suited + 6 gated trips_pair + 4 gated composite) | `analysis/scripts/strategy_v24_dt.py` + `data/v24_dt_model.npz` |
| v23_dt | Predecessor (49 feat); kept as a comparison baseline | `analysis/scripts/strategy_v23_dt.py` + `data/v23_dt_model.npz` |
| v20 / v18e / v18d / v18c / v18b / v18 / v16 | Superseded baselines; retained | `data/v*_dt_model.npz` |
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
| **v24** | **30** | **5** | **53 (49+4 gated comp)** | **314,759** | **$1,977** | **47.89%** | **−$1 vs v23 (composite −$216)** |

**Same sweep on N=1000 prefix (overfitting tripwire):**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v18e | $1,082 | 59.30% | — |
| v20 | $1,082 | 59.31% | $0 |
| v20b | $1,082 | 59.31% | $0 |
| v23 | $1,073 | 59.47% | −$9 vs v20 |
| **v24** | **$1,072** | **59.48%** | **−$1 vs v23 (composite −$201)** |

**Per-category breakdown (full grid, N=200) — three gating wins visible:**

| Category | v18e (37 feat) | v20 (+suited) | v23 (+TP) | v24 (+comp) | Δ v24 vs v18e |
|---|---:|---:|---:|---:|---:|
| high_only | $3,307 | $2,894 | $2,894 | $2,894 | **−$413** (v20 win) |
| pair | $1,873 | $1,873 | $1,873 | $1,873 | $0 |
| two_pair | $1,458 | $1,458 | $1,458 | $1,458 | $0 |
| trips | $1,997 | $1,997 | $1,997 | $1,997 | $0 |
| trips_pair | $1,608 | $1,608 | $1,447 | $1,447 | **−$161** (v23 win) |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | +$1 (noise) |
| quads | $724 | $724 | $724 | $723 | −$1 (noise) |
| composite | $2,100 | $2,100 | $2,080 | $1,864 | **−$236** (v24 win + small carryover) |

**The gating template is proven across 3 categories.** Each champion
upgrade lifts ONLY its targeted category and keeps everything else
bit-identical (or within N=200 noise). This is the cleanest possible
controlled-experiment shape for a feature-engineering change.

---

## What this leaves on the table

- v24 captures **35% of the v14→ceiling gap** at N=200 fidelity ($1,056/$3,033 vs v14)
- v24 captures **62% of the v14→ceiling gap** at N=1000 fidelity ($965/$2,037)
- Remaining gap to ceiling: **$1,977/1000h (full grid N=200)**, **$1,072/1000h (prefix N=1000)**
- Biggest residuals at full grid (per-category × share):
  - **pair**: 46.6% × $1,873 = **$873 share** — single biggest untapped lever
  - **high_only**: 20.4% × $2,894 = **$590 share** — partly addressed; round 2 candidate
  - **two_pair**: 22.3% × $1,458 = **$325 share** — biggest fully-untouched category
  - trips: 5.5% × $1,997 = $110, three_pair: 1.9% × $1,654 = $32
  - trips_pair: 2.86% × $1,447 = $41 (already gated)
  - composite: 0.245% × $1,864 = $4.6 (already gated)
- Per-category prioritization: pair > high_only_round2 > two_pair > trips > three_pair

---

## What Session 31 produced

### Session 31 was an "all 4 targets" sprint

User requested all four queued items get done: (A) distill v20, (B) new
gated aug families, (C) composite deep-dive, (D) v20b capacity step.
All four executed. Outcomes:

- **(A) distill v20** → produced detailed split breakdown
  (`data/distill_v20_dt.log`). Top splits all standard features
  (n_broadway, third_rank, pair_high_rank). The 6 gated suited features
  cluster around msphr thresholds 5.5–8.5, mostly in deep subtrees.
  Distillation surfaced **2 candidate Rule 5 variants** (loose msphr ≥ 9
  and tight msphr ≥ 11 AND msplr ≥ 9), both **REJECTED** in head-to-head
  vs v14 (Decision 056).

- **(B) new gated aug families** → built two:
  - **trips_pair_aug_gated** (6 features): SHIPPED as v23 (Decision 057,
    +$5/1000h full, +$9/1000h prefix; trips_pair −$161 on category).
  - **composite_aug_gated** (4 features): SHIPPED as v24 (Decision 058,
    +$1/1000h full, +$1/1000h prefix; composite −$216 on category).

- **(C) composite_v20_residual diagnostic** → identified 4 clean
  archetypes (trips_two_pair, two_trips, quads_pair, quads_trip) with
  the pattern: v20 frequently SPLITS the dominant trips/quads instead of
  keeping them together on bot. Informed the design of v24's 4
  composite-gated features.

- **(D) v20b at depth=32** → bit-identical to v20 (same 307,939 leaves).
  ARCHIVED. Capacity sweep is closed; min_samples_leaf=5 is the binding
  constraint.

### Methodology lessons (Session 31)

1. **The gating template generalizes across 3 categories now.** v20
   (high_only), v23 (trips_pair), v24 (composite). Future aug families
   should follow the same shape: 4-6 archetype-specific features, zero
   for off-archetype hands, persisted by canonical_id, trained on top of
   the current champion.

2. **Distilled rules need head-to-head validation BEFORE shipping.**
   Both Rule 5 variants looked good in distillation but lost to
   v14_combined by hundreds of $/1000h. The DT's gated routing is too
   selective for any single AND-rule to replicate. Naive rule extraction
   is ~8× over-eager.

3. **Capacity sweeps have a floor.** min_samples_leaf=5 caps depth-30
   leaves at 307,939 (v20). Going to depth=32 changes nothing. Future
   gains are feature-engineering, not capacity.

4. **Diminishing returns on small categories.** v24 added composite
   gating for a ~$0.5/1000h overall lift. Quads (0.24% × $724 = $1.7
   share) is below the noise floor and not worth gating. Future work
   should focus on LARGE categories: pair, high_only round 2, two_pair.

5. **Cycle scoreboard since Session 25 (17 ships, 7 archives, 1 doc-only):**

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
| **v24** | **gated composite on v23** | **+$1 / +$1 vs v23** | **SHIPPED — current champion** |

---

## Resume Prompt (Session 32)

```
Resume Session 32 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (Rule 5 archived, v24 champion section)
- CURRENT_PHASE.md (rewritten end of Session 31)
- DECISIONS_LOG.md (latest: Decisions 055 / 056 / 057 / 058)
- analysis/scripts/strategy_v24_dt.py — current ML champion
- analysis/scripts/composite_aug_features_gated.py — gated template
  (third instance after suited and trips_pair)

State (end of Session 31):
- v24_dt is the new ML champion: $1,977/1000h on full grid (47.89% opt),
  $1,072/1000h on prefix N=1000 (59.48% opt). 314,759 leaves, depth=30,
  min_samples_leaf=5, 53 features (37 base + 6 gated suited + 6 gated
  trips_pair + 4 gated composite).
- The gating template is now PROVEN across 3 categories
  (high_only/v20, trips_pair/v23, composite/v24). Future aug families
  should follow same shape.
- Capacity sweep CLOSED — min_samples_leaf=5 saturates at depth=30.
- Rule 5 (suited-mid for high_only) REJECTED in both variants.
  STRATEGY_GUIDE.md "Rule 5 candidate" section now reads "REJECTED".

Next session targets (priority order by absolute share):

(A) **Pair category audit.** Pair = $873/1000h share — single biggest
    residual. Already has 3 ungated aug features
    (`default_bot_is_ds`, `n_top_choices_yielding_ds_bot`,
    `pair_to_bot_alt_is_ds`). Diagnostic question: are they
    cross-category leakage (the v19 lesson in reverse) or genuine
    help? If leakage, replace with proper `pair_aug_gated`. If
    genuine, design a 6-feature gated extension.

(B) **two_pair_aug_gated.** Biggest fully-untouched category at
    $325/1000h share. Existing `feature_table_two_pair_aug.parquet`
    (Session 19) is UNGATED. Audit and rebuild as
    `two_pair_aug_gated`. Likely 6 features for "which pair goes
    top", "singleton position", "DS-bot reachability" routing
    decisions. Train v25.

(C) **High_only round 2.** $590/1000h share, third lever. v20→v24
    didn't add anything for high_only beyond Session 30. Distill v24
    on high_only specifically; candidate additional gated features:
    `connectivity_high_g`, `n_broadway_in_2nd_suit_g`. Train v26.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated. Gating template
  is now proven 3× and is the default.
- Cached parquets cut training cycles to ~5 min.
- Capacity sweep is closed — don't burn cycles increasing depth/ml.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
