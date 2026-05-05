# Current: Sprint 8 — Session 33 wrap. v26_dt is the new ML champion (gating template generalized to 5 categories: high_only, trips_pair, composite, pair, two_pair). Two_pair audit confirmed pre-existing 3 features were already strictly category-gated; 6 new two_pair-gated features (`t2p_*`) added. Hit and recovered from a naming-collision bug mid-session.

> **🎯 IMMEDIATE NEXT ACTION (Session 34):**
>   (A) **High_only round 2.** Now the biggest UNTOUCHED lever —
>       20.4% × $2,894 = **$590/1000h share**, untouched since v20
>       (Session 30). Distill v26 on high_only specifically; candidate
>       gated additions: `connectivity_high_g`, `n_broadway_in_2nd_suit_g`.
>       Train v27. RISK: high_only resisted Rule 5 extraction in Session 31
>       — could be intrinsically harder.
>   (B) **Pair second-pass diagnostic.** Pair is still largest residual
>       share at $825/1000h. Distill v26 on pair to see which v25-pair-gated
>       features did the heavy lifting and whether further pair feature
>       engineering (e.g. v3-mid quality, kicker gap encoding) is warranted.
>       Cheap (~10 min) — run as triage before committing to round 2.
>   (C) **trips_aug_gated.** Trips (no pair) is 5.5% × $1,997 = $110 share,
>       fully untouched. Smaller absolute lever but a clean new family.

> **✅ SHIPPED (Decision 060):** v26_dt — depth=30, ml=5, **459,209 leaves**,
> 65 features (59 v25 features + 6 GATED two_pair features, prefix `t2p_*`).
> Strictly dominates v25: **−$70/1000h on full** (two_pair drops $313),
> **−$52/1000h on prefix** (two_pair drops $126). 5th instance of the
> gating template and largest per-category gain since v20→high_only's $413.

> **✅ AUDIT RESULT (Session 33, 2026-05-04):** The 3 pre-existing two_pair
> aug features (`default_bot_is_ds_tp`, `n_routings_yielding_ds_bot_tp`,
> `swap_high_pair_to_bot_ds_compatible`) were verified STRICTLY zero on
> every non-two_pair canonical row. They are NOT the v19 leakage pattern;
> they've been category-gated since Session 19. Same shape as the Session
> 32 pair audit. Path taken: option B (design 6-feature gated extension).

> **🐛 BUG ENCOUNTERED + FIXED (Session 33):** v26 was first trained with
> the new 6 features named `tp_*`, colliding with the trips_pair gated
> family's prefix. Two columns shared names; training succeeded by index,
> but inference's `feature_columns.index(c)` returned the FIRST occurrence
> for both lookups → buggy v26 wrote two_pair values into trips_pair's
> column index and left the actual two_pair column uninitialized. **Result:
> $3,746/1000h on prefix** (vs v25's $1,054 — a $2,692 catastrophic
> regression, with two_pair AND trips_pair both blown up). Renamed all 6
> features to `t2p_*` prefix; re-persisted parquet (37s); re-trained
> (256s); re-graded — clean win as documented above. **Methodology rule
> added: each gated family must use a UNIQUE prefix.**

> Updated: 2026-05-04 (end of Session 33)

---

## Headline state at end of Session 33

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14_combined + Rule 4** | Human-memorizable rule chain (4 rules) | `STRATEGY_GUIDE.md` + `analysis/scripts/strategy_v14_combined.py` |
| **v26_dt** | ML champion (459,209 leaves, 65 feat: 37 base + 6 gated suited + 6 gated trips_pair + 4 gated composite + 6 gated pair + 6 gated two_pair, plus the 3 Session-17 pair aug booleans and 3 Session-19 two_pair aug booleans which were already category-gated) | `analysis/scripts/strategy_v26_dt.py` + `data/v26_dt_model.npz` |
| v25_dt | Predecessor (59 feat); kept as a comparison baseline | `analysis/scripts/strategy_v25_dt.py` + `data/v25_dt_model.npz` |
| v24 / v23 / v20 / v18e / ... / v16 | Superseded baselines; retained | `data/v*_dt_model.npz` |
| v20b (d=32) | ARCHIVED — capacity saturated, bit-identical to v20 | `data/v20b_dt_model.npz` |
| v19, v21, v22 | ARCHIVED (v19: prefix fail; v21/v22: Rule 5 rejected) | various |
| v26_buggy_tp_collision | NOT persisted — overwritten in same session by fixed v26 | gone |

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
| v25 | 30 | 5 | 59 (53+6 gated pair) | 390,626 | $1,929 | 48.43% | −$47 vs v24 |
| **v26** | **30** | **5** | **65 (59+6 gated t2p)** | **459,209** | **$1,859** | **49.21%** | **−$70 vs v25 (two_pair −$313)** |

**Same sweep on N=1000 prefix (overfitting tripwire):**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v18e | $1,082 | 59.30% | — |
| v20 | $1,082 | 59.31% | $0 |
| v23 | $1,073 | 59.47% | −$9 vs v20 |
| v24 | $1,072 | 59.48% | −$1 vs v23 |
| v25 | $1,054 | 59.80% | −$18 vs v24 |
| **v26** | **$1,002** | **60.80%** | **−$52 vs v25 (two_pair −$126)** |

**Per-category breakdown (full grid, N=200) — five gating wins visible:**

| Category | v18e (37 feat) | v20 (+suited) | v23 (+TP) | v24 (+comp) | v25 (+pair) | v26 (+t2p) | Δ v26 vs v18e |
|---|---:|---:|---:|---:|---:|---:|---:|
| high_only | $3,307 | $2,894 | $2,894 | $2,894 | $2,894 | $2,894 | **−$413** (v20 win) |
| pair | $1,873 | $1,873 | $1,873 | $1,873 | $1,771 | $1,771 | **−$102** (v25 win) |
| two_pair | $1,458 | $1,458 | $1,458 | $1,458 | $1,458 | $1,145 | **−$313** (v26 win) |
| trips | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $0 |
| trips_pair | $1,608 | $1,608 | $1,447 | $1,447 | $1,446 | $1,445 | **−$163** (v23 win) |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | +$1 (noise) |
| quads | $724 | $724 | $724 | $723 | $723 | $723 | −$1 (noise) |
| composite | $2,100 | $2,100 | $2,080 | $1,864 | $1,869 | $1,741 | **−$359** (v24 win + v26 carryover; prefix shows tied so likely noise) |

**The gating template is now proven across 5 categories.** Each champion
upgrade lifted ONLY its targeted category and kept everything else
bit-identical (or within N=200 noise) — except v26 also showed a $128
composite swing on full grid, but the prefix shows composite tied, so
this is most plausibly N=200 noise (composite has only 14,742 hands).

---

## What this leaves on the table

- v26 captures **39% of the v14→ceiling gap** at N=200 fidelity ($1,174/$3,033 vs v14)
- v26 captures **66% of the v14→ceiling gap** at N=1000 fidelity ($1,035/$2,037)
- Remaining gap to ceiling: **$1,859/1000h (full grid N=200)**, **$1,002/1000h (prefix N=1000)**
- Biggest residuals at full grid (per-category × share):
  - **pair**: 46.6% × $1,771 = **$825 share** — STILL the single biggest residual; second-pass diagnostic candidate
  - **high_only**: 20.4% × $2,894 = **$590 share** — second-biggest, untouched since v20
  - **two_pair**: 22.3% × $1,145 = **$255 share** — just got hit
  - trips: 5.5% × $1,997 = $110 — never gated (fully untouched)
  - three_pair: 1.9% × $1,654 = $32
  - trips_pair: 2.86% × $1,445 = $41 (already gated)
  - composite: 0.245% × $1,741 = $4.3 (already gated)
- Per-category prioritization for Session 34: high_only round 2 > pair second-pass > trips_aug_gated

---

## What Session 33 produced

### Two_pair audit + v26 ship + bug recovery in one session

User redirected to two_pair as Session 33's priority A and let auto-mode run end-to-end:

- **Two_pair audit** → confirmed all 3 pre-existing two_pair aug features are STRICTLY zero on every non-two_pair canonical hand. They've been category-gated since Session 19. Same Session-32-pair-audit pattern.

- **6 new two_pair-gated features designed** (`two_pair_aug_features_gated.py`). The Session 19 mining diagnostic flagged "high-pair-on-mid (DT default) vs high-pair-on-bot (BR swap)" as the dominant miss pattern; the existing `n_routings_yielding_ds_bot_tp` lumps Layout B and Layout C together. The 6 new features split B from C and add rank/suit info:
  - `t2p_layout_a_bot_is_ds_g` (0/1) — ~19% of two_pair hands fire
  - `t2p_n_layout_b_routings_ds_g` (0..3) — Layout B subset of total DS routings
  - `t2p_top_singleton_rank_g` (0..14)
  - `t2p_low_singleton_rank_g` (0..14) — surprisingly strong, #12 in feature importance
  - `t2p_singletons_max_suit_count_g` (1..3)
  - `t2p_high_pair_rank_g` (0..14)

  Persistence took 38s for all 6M canonical hands → `data/feature_table_two_pair_aug_gated.parquet` (20 MB).

- **Naming-collision bug** — first attempt named the 6 features `tp_*` (matching trips_pair's prefix). The DT trained without errors but inference produced **$3,746/1000h on prefix** (catastrophic regression with two_pair AND trips_pair both blown up). Diagnosed in 1 round-trip from the per-category breakdown showing the cross-category blowup pattern; fixed by renaming all 6 features to `t2p_*` everywhere, re-persist + retrain + re-grade.

- **v26 trained** (depth=30, ml=5) — 459,209 leaves (+68K vs v25). Second-largest single-ship leaf delta after v25.

- **v26 graded on both grids** — full $70/1000h, prefix $52/1000h. Two_pair drops $313 / $126. Largest per-category gain since v20→high_only.

### Methodology lessons (Session 33)

1. **Each gated family must use a UNIQUE prefix.** Existing claims:
   - `*_g` suffix variants (suited): `n_suited_pairs_total_g`, `max_suited_pair_high_rank_g`, etc.
   - `tp_*_g` (trips_pair, Session 31)
   - `comp_*_g` (composite, Session 31)
   - `pair_*_g` (pair, Session 32)
   - `t2p_*_g` (two_pair, Session 33)

   New families must check existing prefixes BEFORE picking a name. The collision bug cost ~10 minutes (re-persist + retrain + re-grade) but could have been worse if it had only failed on the prefix tripwire (we'd have shipped a "tied" model that was actually broken). The per-category blowup signature was the diagnostic giveaway.

2. **Cross-category blowup is the diagnostic for column-name collisions.** If a "gated for category X" feature change regresses category X AND some other category Y simultaneously, suspect a column-name collision between the new family's prefix and an existing one.

3. **Two_pair routing was richer than expected.** $313/1000h gain is 3× larger than expected from the share-based extrapolation (which predicted ~$70-150 based on v25's pair gain). The diffuse-miss pattern from Session 19 was actually well-suited to the gating template — the existing 3 features captured "is bot DS?" but not "WHICH layout?". Splitting the layouts unlocked substantial new routing decisions.

4. **The prefix tripwire scales.** v25 (pair) had $18/1000h prefix gain; v26 (two_pair) had $52/1000h. Larger prefix gains correlate with larger full-grid gains AND stronger overfitting protection — the prefix shape-agreement jumped from 59.80% to 60.80% (+1.0 pp), the biggest single-ship pct_opt jump on the prefix.

5. **Cycle scoreboard since Session 25 (19 ships, 7 archives, 1 doc-only, 1 mid-session bug recovery):**

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
| v25 | gated pair on v24 | +$47 / +$18 vs v24 | SHIPPED |
| v26_buggy | gated two_pair (`tp_*` collision) | −$2,692 prefix | RECOVERED IN-SESSION |
| **v26** | **gated two_pair (`t2p_*` rename) on v25** | **+$70 / +$52 vs v25** | **SHIPPED — current champion** |

---

## Resume Prompt (Session 34)

```
Resume Session 34 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (v26 champion section)
- CURRENT_PHASE.md (rewritten end of Session 33)
- DECISIONS_LOG.md (latest: Decision 060)
- analysis/scripts/strategy_v26_dt.py — current ML champion
- analysis/scripts/two_pair_aug_features_gated.py — newest gated family
  (fifth instance after suited / trips_pair / composite / pair)

State (end of Session 33):
- v26_dt is the new ML champion: $1,859/1000h on full grid (49.21% opt),
  $1,002/1000h on prefix N=1000 (60.80% opt). 459,209 leaves, depth=30,
  min_samples_leaf=5, 65 features (37 base + 6 gated suited + 6 gated
  trips_pair + 4 gated composite + 6 gated pair + 6 gated two_pair, plus
  the 3 Session-17 pair aug booleans and 3 Session-19 two_pair aug
  booleans which were verified strictly category-gated).
- The gating template is now PROVEN across 5 categories spanning four
  orders of magnitude in population share (0.245% to 46.6%).
- Capacity sweep CLOSED at the trainer-flag level — adding gated features
  expands leaf count organically (v25: +75K; v26: +68K leaves).

Next session targets (priority order by absolute share):

(A) **High_only round 2.** $590/1000h share, biggest untouched lever
    since v20 (Session 30). Distill v26 on high_only specifically;
    candidate gated additions: `connectivity_high_g`,
    `n_broadway_in_2nd_suit_g`, `top_3_broadway_n_g`. Train v27.
    RISK: high_only resisted Rule 5 extraction (Session 31) — could
    be intrinsically harder than the four already-gated categories.

(B) **Pair second-pass diagnostic.** Pair is still the largest
    residual share at $825/1000h. Distill v26 on pair to see which
    of v25's pair-gated features are doing the work and whether
    further pair feature engineering (e.g. v3-mid quality, kicker
    gap encoding) is warranted before declaring pair "done".

(C) **trips_aug_gated.** Trips (no pair) is 5.5% × $1,997 = $110
    share, fully untouched. Smaller absolute lever but a clean new
    family — would be the 6th gating template instance.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000).
- ALL new aug feature families MUST be category-gated. Gating template
  is now proven 5× and is the default.
- ALL new aug families MUST use a UNIQUE PREFIX. Claimed: `_g` suffix
  (suited), `tp_*_g` (trips_pair), `comp_*_g` (composite),
  `pair_*_g` (pair), `t2p_*_g` (two_pair). Check before naming!
- Cached parquets cut training cycles to ~5 min.
- Capacity sweep is closed at the trainer-flag level — gated features
  expand leaves organically.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
