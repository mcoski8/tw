# Current: Sprint 8 — Session 34 wrap. v27_dt is the new ML champion (gating template generalized to a 6th category: high_only). Marginal +$6/1000h headline gain — smallest gating-template ship to date — but a real and clean signal: all of v27's improvement is concentrated in the high_only category (+0.3pp pct_opt, −$31/1000h within-category), other categories bit-identical.

> **🎯 IMMEDIATE NEXT ACTION (Session 35):**
>   (A) **Pair second-pass diagnostic.** With v27 absorbing high_only's
>       biggest accessible signal, **pair is now the largest residual**
>       at 46.6% × $1,771 = **$825/1000h share**. Cheap (~10 min) distill
>       of v27 on pair-only hands to see which v25-pair-gated features
>       did the heavy lifting and whether further pair feature
>       engineering (e.g. v3-mid quality, kicker gap encoding) is
>       warranted. The KK/AA Rule-4 boundary probe that ran in Session
>       34 already shows promise: 28% of bds_avail KK/AA hands prefer
>       DS-bot over Rule-4 mid-pair, with $42/1000h whole-grid upper
>       bound — but v25's pair-gated features may already capture this.
>   (B) **trips_aug_gated.** Trips (no pair) is 5.5% × $1,997 = $110
>       share, fully untouched. Smaller but a clean new gating template
>       instance (would be the 7th).
>   (C) **High_only round 3.** v27's $31/1000h within-category gain
>       suggests significant residual remains ($2,863 still in high_only).
>       But the diagnostic-to-headline conversion ratio was poor
>       (within-leaf 0.34 EV separation → only $31/1000h on the full
>       category). Probably diminishing returns; revisit later.

> **✅ SHIPPED (Decision 061):** v27_dt — depth=30, ml=5, **460,375 leaves**
> (just +1,166 vs v26), 69 features (65 v26 features + 4 GATED high_only
> features, prefix `ho_*_g`). Marginal headline win:
> **−$6/1000h on full grid** (high_only drops $31), pct_optimal
> +0.06 pp (49.21% → 49.27%). Prefix grid is **uninformative** for v27
> because the canonical-id 0..500K subset contains zero high_only hands
> — full-grid is the only validation possible.

> **🔬 DIAGNOSTIC RAN (`distill_v26_high_only.py`):** Walked all 6M hands
> through v26's 459K-leaf tree, restricted analysis to the 1.23M
> high_only hands. Top miss leaves clustered on the path
> `n_broadway ∈ [3,4]` AND `n_broadway_in_largest_suit_g ≥ 2`. Stratifying
> within-leaf by the candidate feature `n_broadway_in_2nd_suit` showed
> 0.34-0.41 EV within-leaf separation (e.g. leaf 578474 went from
> reg=+0.773 to +0.359 by knowing this single bit). This was the
> strongest pre-train signal of any session. **However, v27's
> realization was much smaller**: only $31/1000h within-category and
> $6/1000h headline. Conversion ratio: ~10% of the within-leaf signal
> manifested in the full-grid grade.

> **📓 METHODOLOGY LESSON ADDED (Session 34):** Within-leaf EV
> separation in N=200-oracle distillation does NOT scale linearly to
> ML-realized headline gain. Reasons: (a) most hands in a "miss leaf"
> are tight already; the gain concentrates in a small subset where the
> new feature actually flips the pick; (b) DT regression criterion may
> partition before reaching the within-leaf signal threshold; (c)
> features can correlate strongly with existing ones (none of the 4
> new `ho_*_g` features placed in v27's top-25 importance, vs v26's
> 3/6 t2p_* in top-25 — sign that the DT mostly absorbed the signal
> through existing features). For future high-share categories,
> validate the diagnostic with a single-feature DT before committing
> to a full family.

> **🔬 PROBE RAN (`probe_kk_aa_ds_bot_vs_mid.py`):** Rule 4 boundary
> probe on 430,848 non-trips KK/AA hands. Rule 4 (mid-pair) is BR-
> optimal on 72.76%; bot-DS routing wins on **28.08% of hands where
> DS-bot is geometrically available** (55.1% of KK/AA), with mean
> +0.379 EV gain when it wins. Upper-bound oracle-perfect Rule-5*:
> **$42/1000h on whole grid** within KK/AA. This is the biggest
> remaining clean rule-extraction candidate — but v25/v26's pair-
> gated features may already capture some of it. Session 35 priority A
> (pair second-pass) should grade pair-only on KK/AA subset to see how
> much of this $42 v26 already gets vs how much remains.

> Updated: 2026-05-05 (end of Session 34)

---

## Headline state at end of Session 34

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14_combined + Rule 4** | Human-memorizable rule chain (4 rules) | `STRATEGY_GUIDE.md` + `analysis/scripts/strategy_v14_combined.py` |
| **v27_dt** | ML champion (460,375 leaves, 69 feat: 37 base + 6 gated suited + 6 gated trips_pair + 4 gated composite + 6 gated pair + 6 gated two_pair + 4 gated high_only, plus the 3 Session-17 pair aug booleans and 3 Session-19 two_pair aug booleans which were category-gated) | `analysis/scripts/strategy_v27_dt.py` + `data/v27_dt_model.npz` |
| v26_dt | Predecessor (65 feat); kept as a comparison baseline | `analysis/scripts/strategy_v26_dt.py` + `data/v26_dt_model.npz` |
| v25 / v24 / v23 / v20 / v18e / ... / v16 | Superseded baselines; retained | `data/v*_dt_model.npz` |
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
| v25 | 30 | 5 | 59 (53+6 gated pair) | 390,626 | $1,929 | 48.43% | −$47 vs v24 |
| v26 | 30 | 5 | 65 (59+6 gated t2p) | 459,209 | $1,859 | 49.21% | −$70 vs v25 |
| **v27** | **30** | **5** | **69 (65+4 gated ho)** | **460,375** | **$1,853** | **49.27%** | **−$6 vs v26 (high_only −$31)** |

**Same sweep on N=1000 prefix (overfitting tripwire):**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v18e | $1,082 | 59.30% | — |
| v20 | $1,082 | 59.31% | $0 |
| v23 | $1,073 | 59.47% | −$9 vs v20 |
| v24 | $1,072 | 59.48% | −$1 vs v23 |
| v25 | $1,054 | 59.80% | −$18 vs v24 |
| v26 | $1,002 | 60.80% | −$52 vs v25 |
| **v27** | **$1,002** | **60.80%** | **$0 vs v26** (prefix has 0 high_only hands; the canonical-id 0..500K subset contains only categories with at least one pair, so v27's high_only-gated features cannot fire on this grid) |

**Per-category breakdown (full grid, N=200) — six gating wins now visible:**

| Category | v18e (37 feat) | v20 (+suited) | v23 (+TP) | v24 (+comp) | v25 (+pair) | v26 (+t2p) | v27 (+ho) | Δ v27 vs v18e |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| high_only | $3,307 | $2,894 | $2,894 | $2,894 | $2,894 | $2,894 | $2,863 | **−$444** (v20 + v27 wins) |
| pair | $1,873 | $1,873 | $1,873 | $1,873 | $1,771 | $1,771 | $1,771 | −$102 (v25 win) |
| two_pair | $1,458 | $1,458 | $1,458 | $1,458 | $1,458 | $1,145 | $1,145 | −$313 (v26 win) |
| trips | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $0 |
| trips_pair | $1,608 | $1,608 | $1,447 | $1,447 | $1,446 | $1,445 | $1,445 | −$163 (v23 win) |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | +$1 (noise) |
| quads | $724 | $724 | $724 | $723 | $723 | $723 | $723 | −$1 (noise) |
| composite | $2,100 | $2,100 | $2,080 | $1,864 | $1,869 | $1,741 | $1,741 | −$359 (v24+v26) |

**The gating template is now proven across 6 categories** spanning 0.245% (composite) to 46.6% (pair) population shares. v27's high_only is the smallest per-category gain to date (−$31), but extends the template to its 6th instance and validates that the diagnostic-driven feature design pipeline still produces non-negative results.

---

## What this leaves on the table

- v27 captures **39% of the v14→ceiling gap** at N=200 fidelity ($1,180/$3,033 vs v14)
- v27 captures **66% of the v14→ceiling gap** at N=1000 fidelity ($1,035/$2,037)
- Remaining gap to ceiling: **$1,853/1000h (full grid N=200)**, **$1,002/1000h (prefix N=1000)**
- Biggest residuals at full grid (per-category × share):
  - **pair**: 46.6% × $1,771 = **$825 share** — STILL the single biggest residual; second-pass diagnostic candidate (Session 35 priority A)
  - **high_only**: 20.4% × $2,863 = **$584 share** — just got hit but most of it remains
  - **two_pair**: 22.3% × $1,145 = **$255 share** — gated in v26
  - trips: 5.5% × $1,997 = **$110** — never gated (fully untouched, candidate for v28)
  - three_pair: 1.9% × $1,654 = $32
  - trips_pair: 2.86% × $1,445 = $41 (already gated)
  - composite: 0.245% × $1,741 = $4.3 (already gated)
- Per-category prioritization for Session 35: pair second-pass > trips_aug_gated > high_only round 3

---

## What Session 34 produced

### v27 ship + KK/AA boundary probe data + methodology lesson

Session opened by re-running existing untracked-from-Session-33 probe scripts. Three artefacts existed at session start:
- `analysis/scripts/distill_v26_high_only.py` (drafted, never run)
- `analysis/scripts/probe_kk_aa_ds_bot_vs_mid.py` (run; CSV exists at `data/kk_aa_rule4_probe.csv`)
- `analysis/scripts/probe_trips_kkk_aaa_routing.py` (drafted, never run)

**0. KKK/AAA trips routing probe** (`probe_trips_kkk_aaa_routing.py`) — ran fresh in Session 34:

- 50,490 KKK/AAA hands (0.84% of grid). KKK = AAA = 25,245 each.
- **A_paired_mid (keep 2 of 3 trip-rank in mid)** is the dominant routing: mean EV +2.530, BR-optimal on 79.18% of all KKK/AAA hands.
- **B_split_bot_DS** (2 of 3 trip-rank in bot, anchoring DS) is geometrically available on 68.6% of hands. When available, **strictly beats A on 24.3% of those cases** with mean +0.363 EV gain.
- **AAA vs KKK asymmetry**: AAA → A wins vs B 80.1% (clearer A-dominance); KKK → A wins 70.9% (KKK splits to DS-bot more often). AAA's stronger mid-pair makes the split less attractive than KKK's.
- Top B-wins are concentrated where smax=2, s2nd=2 (a 2-2-2-1 suit profile) with n_broadway ∈ [3,4] — high-broadway hands with strong DS-bot potential and mediocre kickers for paired-mid.
- **Upper bound**: $606/1000h within KKK/AAA, **$5/1000h whole-grid** if rule perfectly switches. Comparable magnitude to v23/v27 ships.
- **Human rule for KKK/AAA**: default to A_paired_mid (keep 2-of-3 in mid as a pair, like Rule 4). The DS-bot split is +EV ~24% of the time but hard to evaluate manually pre-flop. For computational play, the DT (v25/v26/v27) already routes correctly on the majority of these via existing trips_rank + suit features. CSV at `data/kkk_aaa_routing_probe.csv` (n=50,490).

**1. KK/AA Rule-4 boundary probe analysis** — pulled headline from existing CSV:

- 430,848 non-trips KK/AA hands; Rule-4 (mid-pair) BR-optimal on 72.76%.
- DS-bot routing geometrically available on 55.1% of KK/AA hands.
- When DS-bot is available, it strictly beats mid-pair on 28.08% of cases with mean gain +0.379 EV.
- Hands where bot-DS strictly wins: 66,713 / 430,848 = 15.48% of all KK/AA.
- Upper-bound oracle-perfect Rule-5* on KK/AA: $42/1000h on whole grid.
- This is the biggest remaining clean rule-extraction candidate. v25/v26's pair-gated features may already capture some of it; Session 35 priority A is the diagnostic to find out.

**2. v26 high_only distillation** — ran `distill_v26_high_only.py` (~5 min for the 6M-hand walk):

- High_only baseline: 20.4% × $2,894 = $590/1000h whole-grid share. Mean within-category regret $2,894/1000h, pct_opt 27.7%.
- Top miss leaves clustered on path `n_broadway ∈ [3,4]` AND `n_broadway_in_largest_suit_g ≥ 2`. Each top-30 miss leaf was bleeding +0.5 to +0.65 EV/hand on 300-840 hands.
- Stratifying these leaves by the candidate feature `n_broadway_in_2nd_suit`:
  - Leaf 578474 (n_ho=420, mean_regret +0.635): cand=0 reg=+0.773, cand=1 reg=+0.359 → **Δ +0.414 EV**
  - Leaf 545147: Δ +0.340 EV
  - Leaf 798839: Δ +0.135 EV
  - 9/10 top miss leaves showed ≥ 0.15 EV separation by this single bit
- v26's tree feature-importance restricted to high_only: `n_broadway` 62.7%, `n_low` 11.8%, `top_rank` 6.2%, `third_rank` 5.4% — existing features dominate.

**3. v27 designed and trained** — 4-feature high_only-gated family (prefix `ho_*_g`):

- `ho_n_broadway_in_2nd_suit_g` (0..3) — primary signal from diagnostic
- `ho_n_broadway_in_3rd_suit_g` (0..3)
- `ho_connectivity_high_g` (0..5) — longest run T..A
- `ho_n_broadway_pairs_adj_g` (0..4)

Persistence: 28.5s for all 6M canonical hands → `data/feature_table_high_only_aug_gated.parquet` (19 MB).

Training: 296s for depth=30 ml=5; 460,375 leaves (+1,166 vs v26 — much smaller capacity expansion than v25→v26's +68K or v24→v25's +76K).

**4. v27 graded on both grids:**

- Full grid: $1,859 → $1,853 (**−$6/1000h**); pct_opt 49.21% → 49.27% (+0.06 pp)
- Prefix: $1,002 → $1,002 ($0); prefix has 0 high_only hands so the change can't manifest
- High_only category: $2,894 → $2,863 (**−$31/1000h**); pct_opt 27.7% → 28.0% (+0.3 pp)
- All other categories bit-identical

### Diagnostic-to-headline conversion ratio

The within-leaf 0.34-0.41 EV separation at the worst miss leaves promised a much bigger lift than realized. Conversion ratio: roughly **10% of the within-leaf-projected signal** manifested in the full-grid headline. Reasons identified:

1. **0/4 new features placed in v27's top-25 importance** — vs v26 (3/6 t2p_*) and v25 (5/6 pair_*). The DT mostly captured the signal through existing feature combinations rather than the new bits.
2. **Tiny capacity expansion (+1,166 leaves)** — vs the +68K/+76K of recent ships. Suggests the 4 new features are highly correlated with existing ones (especially `ho_connectivity_high_g` overlapping with `n_broadway`+`n_low`+`connectivity`).
3. **Within-leaf signal is concentrated in a small fraction of hands per leaf** — the 30-30 split in regret means even an oracle-perfect feature would only flip ~half the leaf's picks, and the leaves themselves are a small slice of the 1.23M high_only population.

### Methodology lessons (Session 34)

1. **Within-leaf EV separation in N=200-oracle distillation does NOT scale linearly to ML-realized headline gain.** Conversion ratio observed: ~10%. For future high-share categories, validate the diagnostic with a single-feature DT (or a 2-feature minimum) before committing to a full 4-6 feature family. The "more candidates is safer" intuition was wrong here — extra correlated features add complexity without proportional signal.

2. **Top-25 feature importance is a useful pre-grade tripwire.** v25 had 5/6 new features in top-25; v26 had 3/6; v27 had 0/4. The placement count weakly predicts headline gain magnitude. A v28 design where 0/N new features are in top-25 should be archived without grading.

3. **Prefix N=1000 grid does not contain high_only hands.** The canonical-id 0..500K range covers only hands with at least one pair (categories pair / two_pair / trips / trips_pair / three_pair / quads / composite — exactly summing to 500K). Future high_only-targeting models can only be validated on the full grid. This is a known consequence of the canonical-id ordering noted in the project memory `taiwanese_canonical_id_prefix_lesson` but had not previously been observed to LIMIT a grade.

4. **Diagnostic discovery > brute force.** The diagnostic correctly identified `n_broadway_in_2nd_suit` as the strongest within-leaf separator. The headline gain was small but POSITIVE on both grids' available signals. The methodology pipeline (distill → identify candidate → design family → train → grade on both grids) is sound; the LESSON is in setting expectations: small wins on top of a 5×-gated 65-feature model are themselves a victory.

5. **Cycle scoreboard since Session 25 (20 ships, 7 archives, 1 doc-only, 1 mid-session bug recovery):**

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
| v26 | gated two_pair (`t2p_*` rename) on v25 | +$70 / +$52 vs v25 | SHIPPED |
| **v27** | **gated high_only on v26** | **+$6 / $0 vs v26 (prefix uninformative)** | **SHIPPED — current champion (marginal)** |

---

## Resume Prompt (Session 35)

```
Resume Session 35 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (v27 champion section)
- CURRENT_PHASE.md (rewritten end of Session 34)
- DECISIONS_LOG.md (latest: Decision 061)
- analysis/scripts/strategy_v27_dt.py — current ML champion
- analysis/scripts/high_only_aug_features_gated.py — newest gated family
  (sixth instance after suited / trips_pair / composite / pair / two_pair)

State (end of Session 34):
- v27_dt is the new ML champion: $1,853/1000h on full grid (49.27% opt),
  $1,002/1000h on prefix N=1000 (60.80% opt — UNCHANGED from v26 because
  prefix has zero high_only hands). 460,375 leaves, depth=30,
  min_samples_leaf=5, 69 features (65 v26 + 4 gated high_only).
- Marginal +$6/1000h headline gain (smallest gating-template ship to
  date), but real and category-isolated: high_only −$31/1000h, +0.3pp
  pct_opt; every other category bit-identical.
- The gating template is now PROVEN across 6 categories spanning four
  orders of magnitude in population share (0.245% to 46.6%).
- Capacity sweep CLOSED at the trainer-flag level — adding gated
  features expands leaf count organically (v27: only +1,166 leaves,
  smallest single-ship leaf delta since v23/v24's +6/+54).
- KK/AA Rule-4 boundary probe ran (data/kk_aa_rule4_probe.csv): 28% of
  KK/AA hands with DS-bot available prefer DS-bot over Rule-4 mid-pair;
  upper bound $42/1000h whole-grid. Open question: how much of this
  does v25/v26's pair-gated already capture?

Next session targets (priority order by expected value):

(A) **Pair second-pass diagnostic.** Pair is now the largest residual
    at 46.6% × $1,771 = $825/1000h share. Distill v27 on pair-only
    hands. Specifically: (i) which v25-pair-gated features are doing
    the heavy lifting; (ii) is there room for a v3-mid-quality or
    kicker-gap-encoding family; (iii) on the KK/AA subset specifically,
    grade v26 vs Rule-4 vs the bot-DS oracle to determine how much of
    the $42/1000h KK/AA upper bound is already captured.

(B) **trips_aug_gated.** Trips (no pair) is 5.5% × $1,997 = $110
    share, fully untouched. Smaller absolute lever but a clean new
    family — would be the 7th gating template instance. Note: probe
    script `probe_trips_kkk_aaa_routing.py` exists in tree (Session
    33-34 staging) but was never run; would inform feature design.

(C) **High_only round 3.** v27's $31/1000h within-category gain
    leaves $2,863 still in high_only — most of the residual remains.
    But the diagnostic-to-headline conversion ratio was poor (~10%).
    Probably diminishing returns; revisit after pair second-pass.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000)
  WHEN APPLICABLE — note: prefix has zero high_only hands, so
  high_only-targeting models can only be validated on the full grid.
- ALL new aug feature families MUST be category-gated. Gating template
  is now proven 6× and is the default.
- ALL new aug families MUST use a UNIQUE PREFIX. Claimed: `_g` suffix
  (suited), `tp_*_g` (trips_pair), `comp_*_g` (composite),
  `pair_*_g` (pair), `t2p_*_g` (two_pair), `ho_*_g` (high_only). Check
  before naming!
- Cached parquets cut training cycles to ~5 min.
- Capacity sweep is closed at the trainer-flag level — gated features
  expand leaves organically.
- New methodology rule (Session 34): top-25 feature importance is a
  pre-grade tripwire. If 0/N new features place in top-25, expect
  marginal-to-null headline gain. Validate diagnostic with a single-
  feature DT before committing to a 4-6 feature family.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
