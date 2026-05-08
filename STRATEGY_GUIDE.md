# Taiwanese Poker — Strategy Guide

> The condensed decision tree, in plain English, validated against the
> Full Oracle Grid (6M canonical hands × 105 settings × N=200 MC samples
> vs the realistic 70/25/5 human mixture).
>
> **Structure of this file:**
> 1. Strategy evolution (chronological — what we learned and when)
> 2. ML champion progression (every model version + score)
> 3. Distillation insights (what features matter, what the DT does)
> 4. What's still on the table (residuals + open questions)
> 5. Where each rule + model lives in code
> 6. **The Current Standard** (at the bottom — the rules to memorize, the model to call)
>
> Last updated: 2026-05-07 (Session 40 — Rule 6 low-trips reference table (Trip T..2) appended to Part 6 as 8 worked examples. Connectivity probe (`probe_low_trips_connectivity.py`) confirmed bot run-length is NOT a valid Step-2 tier: the alt priority "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1" regresses $11/1000h whole-grid vs current DS > SS > rainbow > 3+1. Per-cell A-vs-C oracle map cross-referenced (A wins in every n≥5 cell at trip ≤ T). No code change to `strategy_v35_rule6_v3.py`; production v33 unchanged. Methodology rule NEW: connectivity is invariant across the 3 trip-to-bot picks on a given hand, so it cannot serve as a tiebreaker.)

---

# Part 1 — Strategy Evolution

This section is APPEND-ONLY. Every entry is a snapshot of what was true at the
end of that session. Reading top-to-bottom gives you the full history of
how the strategy got to where it is.

## Pre-mining baseline (v3 / v8 / v8_hybrid)

**Before any pattern mining**, the strategy was a hand-coded chain:
- `strategy_v3` (`encode_rules.py`) handled all categories with a single
  routine: highest pair to mid, search for best top, remainder to bot.
- `strategy_v7_regression` (a DT trained on the OLD 4-profile mixture)
  handled three_pair / quads / composite via learned splits.
- `strategy_v8_hybrid` combined v3 (for high_only and pair) with v7 (for
  everything else). This was the production strategy through Session 24.

**Score: $3,153/1000h on the realistic mixture (full grid, N=200).**
That's the baseline every later improvement is measured against.

The v3 chain implicitly encodes "KK/AA → mid" (both pair cards stay
together; top searches over remaining singletons → naturally picks the
A on top when present). This was not yet documented as a rule — it
becomes Rule 4 in Session 28.

## Sessions 25–26: Rule mining sprint (Rules 1, 2, 3 discovered)

The first wave of pattern mining against the new realistic-mixture
Oracle Grid produced three numbered rules:

- **Rule 1 — Single pair: pair-to-bot for double-suited.**
  Discovered via `strategy_v9_pair_to_bot_ds.py` mining. Refined to v9.1
  (tighter gates) then v9.2 (added (1,3)/(3,1) kicker patterns). Fires
  on 2.19% of hands.
  Improvement: +$24/1000h N=200 (within its niche).

- **Rule 2 — Two pairs: never split either pair.**
  `strategy_v10_two_pair_no_split.py`. Replaces v3's "split both pairs
  to bot" default. Fires on every two_pair hand (~22%).
  Improvement: +$81/1000h.

- **Rule 3 — Trips + pair: split the trips 2-and-1, keep the pair.**
  `strategy_v12_trips_pair.py`. Fires on every trips_pair hand (~3%).
  Improvement: +$10/1000h.

**Combined into `strategy_v14_combined`** (v12 → v10 → v9.2 → v8 fallback).

**Score: $3,033/1000h. Improvement: −$120 vs v8_hybrid.**

Several other mining attempts archived in this window:
- v11 (high_only Omaha-first): −$1,745, ARCHIVED.
- v13 (trips no-pair): −$172, ARCHIVED.
- v15 (high_only DS-patch): −$296, ARCHIVED.

The high_only and trips categories resisted hand-coded rules — they
became the targets for the ML approach in Session 27.

## Session 27: First ML champion — v16_dt

A regression DT trained on the full 6M oracle grid. 37 features (28
baseline + 9 hand-engineered "aug" features for pair / high_only /
two_pair routings).

- **v16_full** (depth=18, min_samples_leaf=100, **28,790 leaves**)
  trained on the full 6M grid. Wins on every category vs v14.
  **Score: $2,464/1000h. Improvement: −$569 vs v14, −$689 vs v8.**

A failed sibling (v16_prefix, trained on the 500K canonical-id prefix)
scored $8,493/1000h and was archived. The lesson: canonical-id ordering
is highly non-uniform in hand strength; never train on a canonical-id
prefix subset. Sample uniformly at random instead.

## Session 28: Distillation, Rule 4, v18 capacity

**Distillation of v16's tree.** Walked all 6M hands through v16's
tree, computed population-weighted MSE reduction at every internal
node. Top finding: `n_broadway` alone explains 44.9% of total feature
importance. The 9 hand-engineered "aug" features collectively
contribute <0.4% — the DT solves the problem almost entirely with raw
body-strength features.

**Rule 4 added — Premium pair (KK or AA) → keep pair in mid.**
v3 / v8 / v16 all already converge on this play. Rule 4 formalizes it
for human memorization. No code change. Fires on 7.17% of hands.

**v17 attempt (rules-then-DT chain) ARCHIVED.** Wrapping
v9.2/v10/v12 in front of v16 as a "use rules where they fire, DT for
everything else" hybrid LOSES by $369/1000h on the full grid. v10 and
v12 are inferior to v16 on their own categories ($1,366 worse on
two_pair, $2,979 worse on trips_pair). Hand-coded rules optimized
against the OLD 4-profile mixture cannot beat a DT trained on the
realistic-mixture grid.

**v18 ships.** Same 37 features as v16, more capacity (depth=22,
min_samples_leaf=50, **60,651 leaves** — 2.1× v16). Trained via a new
`train_v18_dt.py` that reads the cached parquet feature tables — total
training cycle drops from ~25min to ~5min.
**Score: $2,306/1000h. Improvement: −$158 vs v16, validated on prefix
(+$129 vs v16).**

The prefix grid (500K hands × N=1000) becomes the new
"overfitting tripwire" — any future ML candidate must improve on
both the noisy full grid and the cleaner prefix.

## Session 29: Capacity sweep + v19 archived

**Capacity sweep continued.** Two more steps from v18's baseline:
- **v18b** (depth=24, ml=30, **96,409 leaves**):
  $2,217 / $1,343 (full / prefix). +$89 / +$135 vs v18.
- **v18c** (depth=26, ml=20, **124,902 leaves**):
  $2,172 / $1,261. +$45 / +$82 vs v18b.

Diminishing-but-positive marginal returns on both grids. v18c ships as
the new champion.
**v18c improvement: −$292 vs v16, −$345 vs v16 on prefix.**

**v19 attempted — suited-broadway aug features.** The Session 28
distillation showed the DT can't represent "two cards of the same suit
with one or both being broadway." Built 6 new features
(`n_suited_pairs_total`, `max_suited_pair_high_rank`,
`max_suited_pair_low_rank`, `has_suited_broadway_pair`,
`has_suited_premium_pair`, `n_broadway_in_largest_suit`) computed for
ALL 6M hands without category gating.

v19 (43 features, depth=22, ml=50, 73K leaves):
- Full grid: +$57/1000h vs v18 ✓
- **Prefix: −$16/1000h vs v18 ✗** — FAILS the prefix tripwire.
- Pair-category prefix regression (+$36/1000h on 215K hands) is the
  smoking gun: the new features fit N=200 noise on hands they
  shouldn't matter for.

**v19 ARCHIVED.** The prefix tripwire just paid off concretely —
without it, v19's positive full-grid grade would have shipped a
slightly-overfit model. The features were real signal in the wrong
container.

## Session 30: Gated suited features + v20 (current champion)

**Diagnosis of v19 failure.** The 6 ungated suited features fired
across all hand categories, giving the DT permission to make small
spurious splits in the pair / two_pair / trips populations. Fix:
**gate the features to high_only hands only**.

**`suited_aug_features_gated.py`** mirrors the existing
`high_only_aug_features.py` pattern — returns `(0, 0, 0, 0, 0, 0)` for
any hand with `n_pairs/n_trips/n_quads ≥ 1`. The features only fire on
the 1.23M high_only canonical hands (20.4% of the population).

**Capacity sweep extended further:**
- **v18d** (depth=28, ml=10, **193,365 leaves**): $2,108 / $1,145.
  +$64 / +$117 vs v18c. (Notably, the prefix gain went UP from
  v18b→v18c's $82 — diminishing returns isn't strictly monotonic.)
- **v18e** (depth=30, ml=5, **274,446 leaves**): $2,066 / $1,082.
  +$42 / +$63 vs v18d.

**v19_gated** (gated features, depth=28, ml=10, 216K leaves):
- Full grid: +$73 vs v18d (high_only category drops $356).
- Prefix: tied exactly ($0 change — gated features fire on zero
  prefix hands by design).

**v20 ships** — the combination of v18e capacity (depth=30, ml=5)
with the gated suited features (43 features total, **307,939 leaves**).
- Full grid: +$84 vs v18e. ONLY high_only category changes ($3,307 →
  $2,894, a $413 gain). Every other category is bit-identical to v18e
  — clean controlled experiment.
- Prefix: tied exactly with v18e ($1,082 / $1,082).

**Score: $1,982/1000h on full grid. Improvement: −$482 vs v16, −$1,051 vs v14.**

**The gating pattern is now the template** for all future aug families:
fire only in the targeted hand category, leave others bit-identical,
prefix tripwire passes trivially. This is the single biggest
methodology lesson of Sessions 28-30.

## Session 31: Two ships (v23 trips_pair, v24 composite); v20b archived; Rule 5 rejected

This was an "all 4 targets" sprint per the user's request: distill v20,
new gated aug families, composite deep-dive, v20b capacity step.

**v20b at depth=32 (capacity probe).** Bit-identical to v20 (same
307,939 leaves). `min_samples_leaf=5` is the binding constraint at
depth=30; pushing to depth=32 changes nothing. **ARCHIVED.** The
trainer-flag-level capacity sweep is now CLOSED — future gains are
feature-engineering, not raw capacity.

**Distill v20 → Rule 5 candidates → REJECTED.** Walked v20's tree on
the high_only category. Top splits all standard features (n_broadway,
third_rank, pair_high_rank); the 6 gated suited features cluster around
msphr thresholds 5.5–8.5 in deep subtrees. Two candidate Rule 5 variants
(loose `msphr ≥ 9` and tight `msphr ≥ 11 AND msplr ≥ 9`) tested
head-to-head against v14_combined:
- **v21 = v14 + Rule 5 (loose):** $3,713/1000h, **−$680 vs v14.**
- **v22 = v14 + Rule 5 (tight):** $3,506/1000h, **−$473 vs v14.**

Both **REJECTED**. Both fire on ~8× more high_only hands than the DT's
selective routing actually wants. The DT's gated splits use 4+ rank
thresholds combined with `n_low`/`n_broadway` that no single AND-rule
can replicate. **For the human chain: stop at Rule 4. For computational
play: use the DT champion.**

**v23 ships — gated trips_pair aug family.** 6 new features
(`tp_trip_rank_g`, `tp_pair_rank_g`, `tp_high_singleton_rank_g`,
`tp_low_singleton_rank_g`, `tp_singletons_suited_g`,
`tp_pair_routing_is_ds_g`), zeros for non-trips_pair. 49 features total
(43 v20 + 6 trips_pair-gated), depth=30 ml=5, **314,705 leaves**.
- Full grid: $1,977/1000h. **+$5 vs v20** (trips_pair drops $1,608 → $1,447, **−$161**).
- Prefix: $1,073/1000h. **+$9 vs v20** (trips_pair drops $1,657 → $1,478, **−$179**).
- Every other category bit-identical or within N=200 noise. 2nd clean instance of the gating template after v20→high_only.

**v24 ships — gated composite aug family.** 4 new features
(`comp_archetype_g`, `comp_lower_trip_rank_g`, `comp_singleton_rank_g`,
`comp_higher_pair_rank_g`), zeros for non-composite. Composite is rare
(0.245% of population) but the largest per-hand bleed at $2,080 on v23.
The `composite_v20_residual` diagnostic identified 4 archetype clusters
(trips_two_pair, two_trips, quads_pair, quads_trip) where v20 frequently
SPLITS the dominant trips/quads instead of keeping them together on bot.
The 4 gated features expose archetype + the unique-info "lower_trip_rank"
signal. 53 features total (49 v23 + 4 composite-gated), depth=30 ml=5,
**314,759 leaves** (only +54 over v23).
- Full grid: $1,977/1000h. **+$1 vs v23** at the headline (composite drops $2,080 → $1,864, **−$216**).
- Prefix: $1,072/1000h. **+$1 vs v23** (composite drops $1,811 → $1,610, **−$201**).
- Headline is at the noise floor because composite is 0.245% of population, but per-category effect is unambiguous. 3rd clean instance of the gating template.

**Score: v23 $1,977/1000h, v24 $1,977/1000h. v24 is the new ML champion.
Improvement: −$487 vs v16, −$1,056 vs v14.**

**Methodology lesson — the gating template is now proven across THREE
categories** (high_only, trips_pair, composite). Each upgrade lifted
ONLY its targeted category and kept every other category bit-identical
or within N=200 noise. Population shares span 0.245% to 20.4%. Future
aug families should follow the same shape: 4-6 archetype-specific
features, zero for off-archetype hands, persisted by canonical_id,
trained on top of the current champion.

**Methodology lesson — distilled rules need head-to-head validation
BEFORE shipping.** Both Rule 5 variants looked good in distillation but
lost to v14 by hundreds of $/1000h. Naive rule extraction is ~8×
over-eager relative to the DT's selective routing.

## Session 32: v25 ships (gated pair) — 4th gating success, largest population share

**Pair audit — answers the diagnostic question from Session 31's
resume prompt.** The 3 pre-existing pair aug features
(`default_bot_is_ds`, `n_top_choices_yielding_ds_bot`,
`pair_to_bot_alt_is_ds`) were verified STRICTLY zero on every non-pair
canonical row. They've been category-gated since Session 17 — the
naming inconsistency (no `_g` suffix) was misleading but harmless. They
are NOT the v19 leakage pattern.

Path forked: option B (design 6-feature gated EXTENSION alongside the
existing 3 booleans), not option A (rebuild from scratch).

**v25 ships — 6 new pair-gated features.** The existing 3 features
answered "is the bot DS under this routing?" (booleans / 0-3 buckets).
The new 6 add rank- and mid-quality signal:
- `pair_kickers_in_pair_suit_max_g` (0..5)
- `pair_kickers_in_pair_suit_min_g` (0..5)
- `pair_default_top_rank_g` (0..14)
- `pair_alt_top_rank_g` (0..14)
- `pair_alt_mid_suited_g` (0/1)
- `pair_alt_mid_n_broadway_g` (0..2)

59 features total (53 v24 + 6 pair-gated), depth=30 ml=5,
**390,626 leaves** (+75K vs v24 — biggest single-ship leaf delta since
v20). Prefix tripwire confirmed the new partitioning is structural, not
noise-fitting.

- Full grid: $1,929/1000h. **−$47 vs v24** (pair drops $1,873 → $1,771, **−$102**).
- Prefix: $1,054/1000h. **−$18 vs v24** (pair drops $929 → $888, **−$41**).
- Every other category bit-identical or within N=200 noise. pct_optimal
  jumps 47.89% → 48.43% (full) and 59.48% → 59.80% (prefix). Pair-only
  pct_opt: 52.8% → 53.9% (full), 62.8% → 63.5% (prefix).

**Score: $1,929/1000h on full grid. Improvement: −$535 vs v16, −$1,104 vs v14.**

**Methodology lesson — population share matters more than per-hand
bleed for picking next targets.** Pair has only $1,873/1000h regret
(modest) but 46.6% population share, so its absolute share is $873/1000h
— biggest residual. v25's $102 per-category gain × 46.6% = $47 headline,
the largest gating gain since v20. Compare composite (0.245% × $216 =
$0.5/1000h headline despite a comparable per-category effect).

**Methodology lesson — leakage check is a one-shot pyarrow read.**
The pair audit was a single ~5-second pandas script (count nonzero rows
by category for each suspect feature). Should be the first step of every
audit going forward; 3 sessions of "is this gated?" diagnostics
collapses into one query.

## Session 33: v26 ships (gated two_pair) — 5th gating success, biggest per-category gain since v20

**Two_pair audit (same pattern as Session 32).** The 3 pre-existing
two_pair aug features (`default_bot_is_ds_tp`,
`n_routings_yielding_ds_bot_tp`, `swap_high_pair_to_bot_ds_compatible`)
were verified strictly zero on every non-two_pair canonical row.
Already gated since Session 19. NOT v19 leakage. Path: option B (extend
with 6 new features alongside the existing 3).

**v26 ships — 6 new two_pair-gated features.** The Session 19 mining
notes had flagged "high-pair-on-mid (DT default) vs high-pair-on-bot
(BR swap)" as the dominant miss pattern; the existing
`n_routings_yielding_ds_bot_tp` lumps Layout B and Layout C together.
The 6 new features SPLIT B from C and add rank/suit info:
- `t2p_layout_a_bot_is_ds_g` (0/1) — Layout A bot DS, fires when both
  pairs share BOTH suits exactly (~19% of two_pair hands)
- `t2p_n_layout_b_routings_ds_g` (0..3) — Layout B subset of total DS
  routings (the long-flagged distinction)
- `t2p_top_singleton_rank_g` (0..14)
- `t2p_low_singleton_rank_g` (0..14) — surprisingly strong, #12 in
  feature importance
- `t2p_singletons_max_suit_count_g` (1..3)
- `t2p_high_pair_rank_g` (0..14)

65 features total (59 v25 + 6 two_pair-gated), depth=30 ml=5,
**459,209 leaves** (+68K vs v25, second-largest single-ship leaf delta
after v25's +75K).

- Full grid: $1,859/1000h. **−$70 vs v25** (two_pair drops $1,458 → $1,145, **−$313**).
- Prefix: $1,002/1000h. **−$52 vs v25** (two_pair drops $1,050 → $924, **−$126**).
- Every other category bit-identical or within N=200 noise. pct_optimal
  jumps 48.43% → 49.21% (full) and 59.80% → 60.80% (prefix). Two_pair
  pct_opt: 57.3% → 60.8% (full), 58.8% → 61.3% (prefix).
- **Largest per-category gain since v20→high_only ($413).**

**Score: $1,859/1000h on full grid. Improvement: −$605 vs v16, −$1,174 vs v14.**

**Bug recovery mid-session — naming collision.** First v26 attempt named
the new features `tp_*`, colliding with the trips_pair gated family's
prefix. Both `tp_low_singleton_rank_g` AND `tp_top_singleton_rank_g`
existed in two different feature definitions. Training succeeded by
column index, but inference's `feature_columns.index(c)` returned the
FIRST occurrence for both name lookups — the v26 strategy wrote
two_pair values into the trips_pair column index and left the actual
two_pair column uninitialized. **Buggy v26 output: $3,746/1000h on
prefix** ($2,692 catastrophic regression with two_pair AND trips_pair
both blown up). Diagnosed in 1 round-trip from the cross-category
blowup pattern; renamed all 6 features to `t2p_*`, re-persisted parquet
(38s), retrained (256s), regraded — clean win as documented above.

**Methodology lesson — each gated family must use a UNIQUE prefix.**
Existing claims: `_g` suffix variants (suited), `tp_*_g` (trips_pair),
`comp_*_g` (composite), `pair_*_g` (pair), `t2p_*_g` (two_pair). New
families must check existing prefixes BEFORE picking a name. Cross-
category blowup (regressing both the targeted category AND another) is
the diagnostic signature for column-name collisions.

**Methodology lesson — the gating template is now proven across FIVE
categories** (high_only, trips_pair, composite, pair, two_pair).
Population shares span 0.245% (composite) to 46.6% (pair). Per-category
gains: high_only $413, two_pair $313, composite $216, trips_pair $161,
pair $102. The template works at every scale tried; the question is no
longer "does it work?" but "which category next, and what features?".

## Session 34: v27 ships (gated high_only-direct) — 6th gating success but smallest per-category gain to date; KK/AA + KKK/AAA boundary probes confirm Rule 4

**Diagnostic-first design.** Session opened by running the
`distill_v26_high_only.py` diagnostic that had been drafted but never
run in Session 33. Walked all 6M hands through v26's 459K-leaf tree
restricted to the 1.23M high_only hands. Top 30 miss leaves all
shared the path `n_broadway ∈ [3,4]` AND `n_broadway_in_largest_suit_g ≥ 2` —
suited-broadway high_only hands. Stratifying these leaves by the
candidate feature `n_broadway_in_2nd_suit` produced striking
within-leaf separations: 9/10 top miss leaves showed ≥0.15 EV split,
with the strongest (leaf 578474, n_ho=420) showing **+0.414 EV
within-leaf separation** by knowing this single bit. This was the
strongest pre-train signal of any session.

**v27 ships — 4 new high_only-gated features.** Naming used the new
unique prefix `ho_*_g` (Session 33 collision lesson upheld):

- `ho_n_broadway_in_2nd_suit_g` (0..3) — primary diagnostic signal
- `ho_n_broadway_in_3rd_suit_g` (0..3) — completes per-suit broadway distribution
- `ho_connectivity_high_g` (0..5) — longest run T-A
- `ho_n_broadway_pairs_adj_g` (0..4) — count of {AK, KQ, QJ, JT}

69 features total (65 v26 + 4 high_only-gated), depth=30 ml=5,
**460,375 leaves** (only **+1,166 vs v26** — the smallest single-ship
leaf delta of any gating-template ship; compare v25→v26 +68K, v24→v25 +76K).

- Full grid: $1,853/1000h. **−$6 vs v26** (high_only drops $2,894 → $2,863, **−$31**).
- Prefix: $1,002/1000h. **$0 vs v26** — but the prefix grid contains **zero high_only hands** (canonical-id 0..500K covers only categories with at least one pair). The "$0" is structural, not informative.
- Every other category bit-identical. pct_optimal moves 49.21% → 49.27% (full, +0.06pp). High_only-only pct_opt: 27.7% → 28.0% (+0.3pp).

**Score: $1,853/1000h on full grid. Improvement: −$611 vs v16, −$1,180 vs v14.**

**Diagnostic-to-headline conversion ratio: ~10%.** The within-leaf 0.34
EV separation projected to ~$3,400/1000h within-leaf — but realized
only $31/1000h within-category and $6/1000h whole-grid. The signal is
concentrated in a small fraction of hands within each miss leaf, not
the full leaf population. **0/4 new features placed in v27's top-25
importance** (vs 3/6 t2p_* in v26 and 5/6 pair_* in v25) — leading
indicator of the marginal headline result.

**KKK/AAA routing probe (`probe_trips_kkk_aaa_routing.py`):** Ran
fresh in Session 34. 50,490 hands (0.84% of grid). **A_paired_mid
(keep 2 of 3 trip-rank in mid as a pair) is BR-optimal on 79.18% of
KKK/AAA hands** — confirms the Rule 4 default extends naturally to
trips of K/A. AAA→A wins 80.1% vs B; KKK→A wins 70.9% (KKK splits to
DS-bot more often because AAA's mid-pair is structurally stronger).
B_split_bot_DS is geometrically available on 68.6% of hands; when
available, strictly beats A on 24.3% with mean +0.363 EV gain. Upper
bound: $5/1000h whole-grid if rule perfectly switches. CSV at
`data/kkk_aaa_routing_probe.csv`.

**KK/AA Rule-4 boundary probe (`probe_kk_aa_ds_bot_vs_mid.py`):**
Pulled headline from existing CSV (probe ran in Session 33-34
staging). 430,848 non-trips KK/AA hands. **Rule 4 (mid-pair) is BR-
optimal on 72.76%.** DS-bot routing geometrically available on 55.1%;
when available, strictly beats mid-pair on 28.08% with mean +0.379 EV
gain. Upper bound: $42/1000h whole-grid if rule perfectly switches —
**comparable magnitude to v23/v24/v27 ships and the largest remaining
clean rule-extraction candidate**.

**Methodology lesson — within-leaf EV separation does NOT scale
linearly to ML headline gain.** Conversion ratio observed: ~10%.
Reasons: (a) most hands in a "miss leaf" are tight already; the gain
concentrates in the subset where the new feature actually flips the
pick; (b) DT regression criterion may partition before reaching the
within-leaf signal threshold; (c) features can correlate strongly
with existing ones — `ho_connectivity_high_g` overlaps with
`n_broadway`+`n_low`+`connectivity`. For future high-share
categories, validate the diagnostic with a **single-feature DT**
before committing to a 4-6 feature family.

**Methodology lesson — top-25 feature importance is a pre-grade
tripwire.** v25 had 5/6 new features in top-25 (gained $47 / $18);
v26 had 3/6 in top-25 (gained $70 / $52); v27 had 0/4 in top-25
(gained $6 / $0). The placement count weakly predicts headline gain
magnitude. Future families with 0/N placement should be archived
without grading.

**Methodology lesson — prefix N=1000 grid has zero high_only hands.**
Future high_only-targeting models can only be validated on the full
grid. The canonical-id 0..500K subset contains only categories with
at least one pair (sums to exactly 500,000 across pair, two_pair,
trips, trips_pair, three_pair, quads, composite). This was always
true but had not been observed to limit a grade until v27.

**Methodology lesson — Rule 4 holds for KK, AA, KKK, and AAA.** Both
boundary probes confirm "mid-as-pair" as the dominant routing on the
realistic mixture (72.76% / 79.18% / 83.84% optimal across the three
subsets). The DS-bot exception is +EV ~24-28% of geometrically-
eligible hands but has historically been hard to extract as a clean
rule (v21 / v22 attempts were ~8× over-eager). For human play: stop
at Rule 4. For computational play: use v27 (or v26 — they're nearly
identical on the KK/AA and KKK/AAA subsets since neither was the
target of v27's high_only features).

## Session 35: v29 ships (gated pair_r4) — 7th gating success and largest diagnostic-driven win

**The chain:** This session was driven entirely by user intuition + diagnostic-first design. The trail:

1. **User question (Session 34 close):** "What about KK/AA where leftover bot is rainbow? Shouldn't we move KK/AA to bot for DS?" Per-hand probe of K♠K♦3♠5♦9♥T♣J♠ confirmed: Rule 4 picks rainbow bot for +1.225 EV; oracle BR is DS-bot for +3.025 EV (Δ = $18,000/1000h on this single hand).

2. **Rule 5 (Rainbow override) shipped to STRATEGY_GUIDE** as the user-intuited human rule (Decision 063). v28 = v14 + Rule 5 = $3,032/1000h on full grid, +$1 vs v14_combined. **First successful Rule 5 in project history** (v21/v22 lost $473-$680). Tight structural trigger (KK/AA + Rule-4-bot rainbow + DS feasibility) fires on 0.27% of all hands. Per-hand wins on the firing subset are dramatic ($15-18K/1000h on canonical examples).

3. **`distill_v27_pair.py` ran the KK/AA capture analysis** to quantify how much of the boundary-probe $42/1000h upper bound v27 already captures. Surprising finding: **v27 is $20/1000h whole-grid WORSE than Rule 4 alone on KK/AA** (regret 0.1236 vs 0.0949 EV/hand). v27 picks Rule-4 84.6% of KK/AA, but the 15.4% non-Rule-4 picks are systematically incorrect — overgeneralizing v25's pair-gated features. Total v27→oracle gap on KK/AA: $63/1000h whole-grid.

4. **The missing signal: suit profile of Rule-4's resulting bot.** v25's existing `pair_*_g` features encode kickers-in-pair-suit and alt-routing rank quality but NOT the SHAPE of the leftover bot. The rainbow trigger that drives Rule 5 is the same axis the ML champion was missing.

**v29 ships — 4 new pair-gated v2 features** (prefix `pair_r4_*_g` to avoid collision with v25's `pair_*_g`):

- `pair_r4_bot_suit_profile_g` (0..5) — encoded Rule-4 bot suit shape. THE missing signal.
- `pair_r4_bot_max_rank_g` (0..14) — highest rank in Rule-4 bot
- `pair_r4_n_broadway_kickers_g` (0..5) — count of T-A among 5 non-pair cards
- `pair_r4_n_low_kickers_g` (0..5) — count of 2-5 among 5 non-pair cards

73 features total (69 v27 + 4 pair_r4-gated), depth=30 ml=5,
**486,342 leaves** (+25,967 vs v27, +5.6% capacity expansion).
3 of 4 new features placed in top-30 importance (#17, #20, #23) —
strong pre-grade tripwire signal.

- Full grid: $1,807/1000h. **−$46 vs v27** (pair drops $1,771 → $1,674, **−$97 within-pair**).
- Prefix: $965/1000h. **−$37 vs v27** (pair drops $888 → $803, **−$85 within-pair**).
- Every other category bit-identical or within N=200 noise. pct_optimal moves 49.27% → 49.80% (full, +0.53 pp) and 60.80% → 61.32% (prefix, +0.52 pp).
- Full:prefix ratio 1.24:1 — well-calibrated, low overfitting risk.

**Score: $1,807/1000h on full grid. Improvement: −$657 vs v16, −$1,226 vs v14.**

**Methodology lesson — diagnostic-first design produces 7.7× better headline-per-feature than speculative design.** v27 (4 speculative high_only candidates) gained $6/1000h. v29 (4 diagnostic-driven pair features) gained $46/1000h. Same trainer config, same gating template. The difference: v29's diagnostic explicitly compared v27 vs Rule 4 alone and discovered v27 was *losing* — that's the kind of finding that prescribes feature design rather than just suggesting candidates.

**Methodology lesson — diagnostic should identify a competing baseline.** Future feature engineering should explicitly ask: "What rule-based or simpler-ML alternative am I beating, and where is the ML champion underperforming it?" That comparison surfaces the *missing signal* directly. Within-leaf separation (Session-34 high_only) is necessary but not sufficient; you need the baseline comparison to know whether the signal will translate to ML capacity.

**Methodology lesson — user intuition correlates with ML weak points.** The user-flagged hand pattern (KK/AA + rainbow Rule-4-bot) revealed a $63/1000h whole-grid weakness that v27's headline metrics never surfaced. When a domain expert says "this can't be right" at the table, treat that as a high-prior research signal.

**Methodology lesson — categories can absorb multiple gating-template iterations.** Pair has now seen TWO independent ships:
- v25: 6 features encoding kickers-in-pair-suit + alt-routing quality (-$102 within-pair)
- v29: 4 features encoding Rule-4-bot suit profile + body-card distribution (-$97 within-pair)

Total pair improvement since v18e: **−$199/1000h within-pair**. Each iteration targeted a distinct signal axis; neither superseded the other (v29 BUILDS ON v25, doesn't replace).

## Session 36: v30 ships (gated trips, 8th gating) + v31 ships (capacity expansion, 2nd-largest ship in project history)

This session produced TWO ships back-to-back: a gating-template ship (v30, trips) followed overnight by a CAPACITY-ONLY ship (v31). The pair sets a methodological precedent worth recording in detail.

**Part A — v29 KK/AA round-2 audit + v30 trips ship.**

The session opened with `distill_v29_pair.py` running the round-2 KK/AA audit on the v29 champion. v29 closed only $7/1000h of v27's $14 KK/AA Rule-4 deficit. Stratification by Rule-4-bot suit profile revealed:

| Rule-4-bot profile | KK/AA share | v29 | Rule-4 alone | Oracle | v29-oracle gap |
|---|---:|---:|---:|---:|---:|
| rainbow (1+1+1+1)        |  8.8% | $12.0 | $15.4 | $3.8  | **$8.2** |
| **single-suited (2+1+1)** | **52.9%** | **$51.0** | **$38.1** | **$14.1** | **$36.9** |
| double-suited (2+2)      | 15.4% | $3.6 | $2.0 | $1.0 | $2.6 |
| three-of-suit (3+1)      | 20.6% | $14.4 | $11.9 | $6.3 | $8.0 |
| four-of-suit             |  2.2% | $1.0 | $0.8 | $0.7 | $0.3 |

v29's `pair_r4_bot_suit_profile_g` (categorical 0..5) treats single-suited as one bucket — but the single-suited stratum (52.9% of KK/AA, 3.7% of grid) needs FINER encoding (which suit, dominant-suit max rank, pair-suit alignment). Rainbow is captured well because Rule 5 fires there; single-suited is the dominant residual leak. **Deferred** to v31a candidate (overnight cascade).

The session pivoted to a fresh diagnostic: `distill_v29_trips.py`. The trips category (5.46% of grid, $109/1000h whole-grid contribution) had been entirely untouched by gating. The diagnostic produced the **largest gap-to-baseline ever measured in this project**:

| Strategy | Within-trips regret | Whole-grid contribution |
|---|---:|---:|
| Always A_paired_mid (mid is trip pair)  | $24/1000h | $24/1000h |
| Always B_paired_bot_any                 | $625/1000h | $341/1000h |
| Always C_top_trip                       | $1,107/1000h | $605/1000h |
| Oracle (max over A∪B_any∪C)             | $0 (perfect routing exists) | $0 |
| **v29 actual**                          | **$1,997/1000h** | **$109** |

**v29 was $85/1000h whole-grid WORSE than always-A_paired_mid** — the analog of "v27 was $20 worse than Rule 4 on KK/AA" but 4× larger. v29 picks A on 79.9% of trips, B on 4.8%, C on 15.3%; the 20.1% non-A picks are systematically wrong, especially on low-rank trips (2-9 each leak $7-8/rank-share, totaling ~$60 of the $85 deficit).

**v30 ships — 6 new trips-gated features** (prefix `trips_*_g`, distinct from v23's `tp_*_g` which is trips_pair):

- `trips_b_ds_avail_g` (0/1) — is B-DS routing structurally feasible (≥1 kicker in each of 2 trip-suits)?
- `trips_b_ds_n_routings_g` (0..3) — count of {a,b} trip-suit pairs admitting B-DS
- `trips_kickers_max_suit_count_g` (0..4) — max suit count among 4 kickers
- `trips_kickers_max_rank_g` (0..14) — highest kicker rank
- `trips_n_broadway_kickers_g` (0..4) — count of T-A among kickers
- `trips_n_low_kickers_g` (0..4) — count of 2-5 among kickers

79 features total (73 v29 + 6 trips-gated), depth=30 ml=5, **493,057 leaves** (+6,715 vs v29, +1.4% capacity expansion). **0/6 new features placed in top-30 importance** — tripwire predicted small headline.

- Full grid: $1,794/1000h. **−$13 vs v29** (trips drops $1,997 → $1,758, **−$239 within-trips**).
- Prefix: $951/1000h. **−$15 vs v29** (trips drops $1,763 → $1,474, **−$289 within-trips**).
- All other categories bit-identical or within N=200 noise. pct_optimal moves 49.80% → 49.98% (full, +0.18 pp) and 61.32% → 61.53% (prefix, +0.21 pp).
- **Full:prefix ratio 0.87:1** — first ship where prefix gain exceeds full-grid gain. Trips routing has cleaner answers under higher-fidelity grading.

**Part B — overnight v31 cascade: capacity-only retrain produces second-largest ship.**

Three v31 candidates ran sequentially (~80 min total) via `analysis/scripts/overnight_v31_cascade.sh`:

| Candidate | Approach | Full Δ vs v30 | Prefix Δ vs v30 | Tripwire | Leaves |
|---|---|---:|---:|---:|---:|
| v31a | pair_r4v3 KK/AA-tight (4 features) | +$6 | $0 | 0/4 in top-30 | 500,722 (+8K) |
| v31b | trips_v2 round 2 (4 features for C_top + finer A/B) | +$15 | +$13 | 0/4 in top-30 | 507,692 (+15K) |
| **v31 (was v31c)** | **v30 features at depth=32 ml=3** | **+$58** | **+$29** | n/a (no new features) | **699,773 (+207K)** |

**v31 ships — depth=32, min_samples_leaf=3, 79 features (identical to v30), 699,773 leaves** (+206,716 vs v30 = +42% capacity expansion, the largest single-ship leaf delta in project history).

Per-category at full grid — **ALL 8 categories improve** (no isolated-category gating signature; capacity helps across the board):

| Category | v30 | v31 | Δ |
|---|---:|---:|---:|
| high_only  | $2,862 | $2,816 | −$46 |
| pair       | $1,674 | $1,639 | −$35 |
| **two_pair** | $1,145 | $1,037 | **−$108** |
| trips      | $1,758 | $1,732 | −$26 |
| **trips_pair** | $1,442 | $1,225 | **−$217** |
| three_pair | $1,654 | $1,639 | −$15 |
| quads      | $723   | $645   | −$78 |
| **composite** | $1,733 | $1,387 | **−$346** |

The biggest gains accrue to PREVIOUSLY-GATED categories (composite, trips_pair, two_pair). Capacity expansion lets the existing gating-template features express more structure. Previously-untouched categories (high_only, three_pair, quads) also improve, just less dramatically.

- Full grid: $1,736/1000h. **−$58 vs v30** (second-largest single ship after v26's −$70). pct_opt 49.98% → 50.92% (+0.94 pp).
- Prefix: $921/1000h. **−$29 vs v30**. pct_opt 61.53% → 62.07% (+0.54 pp).
- Full:prefix ratio 2.0:1 — at edge of overfitting territory but clean per-category structure rules out pure noise.

**Score: $1,736/1000h on full grid. Improvement: −$728 vs v16, −$1,297 vs v14.**

**Methodology lesson — when feature set grows ≥40 above last capacity-saturation test, RE-TEST capacity.** The v20 vs v20b finding (Session 31, depth=32 produced bit-identical results as depth=30 ml=5) was at 43 features with 308K leaves. That conclusion didn't generalize: at v30's 79 features and 493K leaves, depth=32 ml=3 unlocks $58/1000h of latent signal. Future ML champion sessions should default to **depth=32 ml=3** going forward, and re-test capacity (depth=34 ml=2 as the next ceiling) whenever leaf-count growth stalls below historical norms (~30K leaves per gating-template ship).

**Methodology lesson — diagnostic-first feature design and capacity expansion are orthogonal axes.** v25-v30 were 6 sequential diagnostic-first ships (each adding 4-6 features per category) totaling −$260/1000h cumulative. v31 alone (capacity-only, zero new features) ships −$58. Capacity unlocks ~22% of what the cumulative feature work had added but couldn't fully express. Future sessions should run a capacity sweep BEFORE considering more features whenever a ship has a bearish tripwire AND a leaf-count gain ≤10K — because that pattern signals "feature was added but tree couldn't express it" rather than "feature wasn't useful."

**Methodology lesson — categorical features can be too coarse, but tighter gating doesn't always help.** v31a's pair_r4v3 features were KK/AA-tight (zero outside KK/AA). The hypothesis was that v29's `pair_r4_bot_suit_profile_g` was too coarse for the single-suited stratum. The candidate shipped only +$6 full / $0 prefix. Tight gating did inject signal (within-pair −$13 on full) but the headline was modest. The KK/AA single-suited Rule-4-bot stratum remains an open optimization target ($37 below oracle) but a fundamentally different angle is needed (e.g., meta-classifier feature trained on probe data, or a sub-tree dedicated to KK/AA hands).

**Methodology lesson — "always-X" structural baselines surface Rule-N candidates.** The trips diagnostic surfaced "Always A_paired_mid" as the structural analog of Rule 4 for trips. The Session 34 KK/AA Rule-4 boundary probe surfaced Rule 5 (Rainbow override). Future sessions should systematically check whether each category has a structural always-X baseline that the human strategy could codify — even if it's already implicit in v14_combined, naming it explicitly preserves the strategy chain's coherence.

**Methodology lesson — the gating template now has 8 instances; pair has 2 iterations.** Suited (v20) / trips_pair (v23) / composite (v24) / pair v1 (v25) / two_pair (v26) / high_only (v27) / pair v2 (v29) / trips (v30). v31 is NOT a 9th gating-template instance — it's a capacity-only retrain. The template is established; the capacity dimension is the orthogonal axis going forward.

---

## Session 37: v32 ships (round-2 trips at high capacity, completing v30→v32 arc, beats v26 record); v33_rule6 is largest single rule ship in project history

This session executed the v32 hypothesis from Session 36 (stack v31b's round-2 trips features onto v31's high-capacity config) AND surfaced/codified Rule 6 — the structural analog of Rule 4 for trips, which delivers the largest single rule ship the project has ever seen.

**Part A — v32 ships (the v30→v32 ship arc).**

Session 36's overnight cascade produced two independently-positive ML candidates: v31b (trips_v2 round-2 features at depth=30 ml=5, +$15 full / +$13 prefix vs v30) and v31c → v31 (pure capacity expansion, +$58 full / +$29 prefix vs v30). They were graded as alternatives, and the cascade picked v31. But the two improvements come from orthogonal axes: **trips_v2 features add new signal in trips, while capacity expansion expresses already-encoded signal across all 8 categories.** Stacking them should deliver both gains.

v32 = 83 features (79 v30 + 4 trips_v2 round-2) at depth=32, min_samples_leaf=3. Trained at v31's high-capacity config. **731,606 leaves** (+31,833 vs v31, +4.6% capacity).

| Grid | v30 → v31 | v31 → v32 | v30 → v32 (cumulative) |
|---|---:|---:|---:|
| Full (N=200) | $1,794 → $1,736 (−$58) | $1,736 → $1,715 (**−$20**) | **−$79** |
| Prefix (N=1000) | $951 → $921 (−$29) | $921 → $904 (**−$18**) | **−$47** |

**The cumulative v30→v32 ship of $79/1000h on full grid beats v26's record of $70 to become the largest single-session ML ship in project history.**

Per-category at full grid — only trips moves vs v31 (textbook gating signature):

| Category | v30 | v31 | v32 | Δ v32 vs v31 |
|---|---:|---:|---:|---:|
| high_only  | $2,862 | $2,816 | $2,816 | $0 |
| pair       | $1,674 | $1,639 | $1,639 | $0 |
| two_pair   | $1,145 | $1,037 | $1,037 | $0 |
| **trips**  | $1,758 | $1,732 | **$1,359** | **−$373** |
| trips_pair | $1,442 | $1,225 | $1,225 | $0 |
| three_pair | $1,654 | $1,639 | $1,639 | $0 |
| quads      | $723   | $645   | $645   | $0 |
| composite  | $1,733 | $1,387 | $1,386 | −$1 |

**Score: $1,715/1000h on full grid. Improvement: −$351 vs v18e, −$1,317 vs v14_combined. v32 captures 43.5% of the v14→ceiling gap.**

Tripwire footprint for v32: 0/4 trips_v2 in top-30 (positions 55, 60, 72, 73). Bearish, matching v31b at depth=30 ml=5 which placed 0/4 yet shipped +$15. **7 ships now confirm tripwire predicts conversion rate (~10-15%), not absolute opportunity.**

**Part B — Rule 6 verification + v33_rule6 ships (the largest single rule ship in project history).**

Session 36's `distill_v29_trips.py` had identified that v29 was $85/1000h whole-grid worse than the structural baseline "Always A_paired_mid" on pure trips. Session 37 wrote `verify_rule6_v14_trips.py` to trace the same baseline against the human strategy chain (v14_combined + Rule 4 + Rule 5 = v28).

The probe surfaced three findings on a 30K pure-trips sample:

1. **v14 picks "mid is pair-of-trip-rank" (A or C variant) on only 94.3% of pure trips.** The remaining 5.43% goes to B_bot_pair_trip routings (the 3rd trip card on bot, breaking the mid-pair). 0.24% goes to other archetypes.
2. **v14's A-vs-C decision is empirically correct on the 94.3% it gets right** — equivalent to `top = max(trip_rank, max_kicker_rank)`. The bug is purely in the 5.4% B-bleed.
3. **The cleanest rule: "On pure trips, the third trip card never goes to bot."** This is "always A∪C" (mid is pair of trip-rank, top free). The oracle ceiling for this rule is **$197/1000h whole-grid over v14** — bigger than any prior rule ship combined.

**Rule 6 statement:** *"With pure trips (one rank with count 3, no other pairs/quads), mid is always 2 of the 3 trip-rank cards. The third trip card goes to top (when trip_rank > max_kicker_rank, i.e. the C variant) or to bot (otherwise, the A variant). Within the A variant, choose which trip → bot to maximize bot DS-ness."*

**v33_rule6_trips ships:**

| Grid | v28 (current human champ) | v33 | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $3,032 / 39.64% | **$2,920 / 40.68%** | **−$112 / +1.04 pp** |
| Prefix (N=1000, 500K hands) | $2,037 / 47.61% | **$1,894 / 48.81%** | **−$143 / +1.20 pp** |

The trips category alone drops $4,054 → $2,010 within-trips on the full grid (almost halved), with 19.9% → 39.0% optimal-pick rate. Probe → full agreement is essentially perfect (1% drift).

**The 56% capture of the $197 oracle ceiling** is the heuristic's limit (no peeking at oracle EVs). Override-everything beat preserve-A∪C-when-already-good ($111 vs $37 on the probe) — the heuristic's bot-DS optimization on the A variant beats v14/v8_hybrid's learned routing on average, even when both pick A.

**Methodology lesson — "always-X" structural baselines surface Rule-N candidates worth shipping.** The trips diagnostic surfaced Rule 6 worth $112-143/1000h whole-grid; the Session 34 Rule 4 boundary probe surfaced Rule 5. **Future sessions should systematically probe each category for an always-X baseline** — every category with a learned ML feature family should have its rule-chain analog tested. Candidates: high_only "always top = max-rank" (likely already true via v8_hybrid); two_pair "always split high pair to mid" (deferred); trips_pair "always pair-of-pair to mid" (probably already covered by v12 detect logic but worth verifying).

**Methodology lesson — orthogonal axis stacking works (v32 confirms).** v31's capacity expansion ($58) and v31b's trips_v2 features ($15) stacked additively to v32's $79 cumulative (with a small extra $6 from interaction). The template for future ships: **standalone diagnostic-driven feature design at v31's default depth=32 ml=3, then re-test capacity at depth=34 ml=2 if leaf-count grows substantially.**

**Methodology lesson — rule chain ships should default to override-everything within the rule's scope.** The "preserve v14 when already-A∪C" variant of Rule 6 captured only $37/1000h vs the override-everything $112. Rule heuristics should fully replace the learned strategy within their gate, not just patch its mistakes — because the heuristic's structural reasoning often beats the learned strategy's fine-grained choices.

---

## Session 38: v34_dt ships (capacity-only ml=2 retrain at v32 features); Rule 6 A-vs-C boundary probe validates the user hypothesis at the oracle but cannot be cashed via heuristic-A

This session pursued two priority targets from Session 37's wrap and surfaced one shipping result and one informative negative.

**Part A — v34_dt ships (depth=34 ml=2 capacity expansion).**

Per the Session 37 methodology rule (when feature count grows OR leaf-count grows ≥+5%, retest capacity), Session 38 retrained v32's exact 83 features at depth=34 with two `min_samples_leaf` settings:

- **v32_d34ml3 (control):** 731,611 leaves at achieved depth 33. Exactly +5 leaves vs v32's 731,606. **Result: $1,715/1000h full / $904/1000h prefix — bit-identical to v32.** This proves **ml=3 was the binding constraint, not depth=32** — the natural saturation depth at ml=3 is 33, well below the 34 cap, so depth=32 was never the bottleneck.

- **v32_d34ml2 (candidate, promoted to v34_dt):** 874,548 leaves at achieved depth 33. **+19.5% capacity over v32.** Lowering ml from 3 to 2 unlocks +142,937 more splits.

**Validation grades (full + prefix):**

| Grid | v32 | v32_d34ml3 | **v34_dt** | Δ v34 vs v32 |
|---|---:|---:|---:|---:|
| Full N=200 6.0M | $1,715 / 51.31% | $1,715 / 51.31% | **$1,681 / 52.02%** | **−$34 / +0.71pp** |
| Prefix N=1000 500K | $904 / 62.47% | $904 / 62.47% | **$889 / 62.74%** | **−$15 / +0.27pp** |

**Per-category v34 vs v32 (full grid):** every category improves. Within-category headlines:

| Category | v32 | v34 | Δ within | share | whole-grid |
|---|---:|---:|---:|---:|---:|
| high_only  | $2,816 | $2,806 | −$10  | 20.4% | −$2.0 |
| pair       | $1,639 | $1,619 | −$20  | 46.6% | −$9.3 |
| two_pair   | $1,037 | $978   | −$59  | 22.3% | −$13.2 |
| trips      | $1,359 | $1,291 | −$68  | 5.46% | −$3.7 |
| trips_pair | $1,225 | $1,057 | −$168 | 2.86% | −$4.8 |
| three_pair | $1,639 | $1,635 | −$4   | 1.90% | −$0.1 |
| quads      | $645   | $613   | −$32  | 0.24% | −$0.1 |
| composite  | $1,386 | $1,173 | −$213 | 0.245% | −$0.5 |

The biggest within-category gains are in trips_pair (−$168) and composite (−$213) — both ML-engineered categories that benefit from finer leaf granularity. Whole-grid contribution is dominated by two_pair (−$13/1000h via 22.3% share) and pair (−$9/1000h via 46.6% share). **Unlike prior gating ships, this ship moves every category — a textbook capacity-only signature.**

**Cumulative v30 → v34 of $113/1000h (full grid) is the new largest cumulative arc in project history**, beating Session 37's v30→v32 of $79. The arc decomposes as: v30→v31 ($58, capacity), v31→v32 ($20, trips_v2 features), v32→v34 ($34, capacity-only at ml=2).

**Part B — Rule 6 A-vs-C boundary probe (negative result, archived as v34_rule6_v2).**

Following the user's hypothesis that Rule 6's C variant (3rd trip card on top when `trip_rank > max_kicker_rank`) is suspect at low/mid trip ranks, Session 38 wrote `probe_rule6_c_variant.py` to compute oracle EVs for the best A and best C settings stratified by `(trip_rank, max_kicker_rank)`.

**Oracle-level findings strongly validated the user's hypothesis:**

| Variant | Mean regret vs oracle (whole-grid) | Cells where it wins |
|---|---:|---:|
| best-A (top = highest kicker) | $+82/1000h | 84.1% |
| best-C (top = trip card) | $+608/1000h | 15.9% |

C wins overwhelmingly only at trip A (100% of cells, +$5,757 to +$14,139 over A) and trip K (88-100%, +$2,131 to +$7,240); narrowly at trip Q (mixed); LOSES at trip ≤ J (-$1,765 to -$17,030). The user was directionally right: C is dominated below trip Q.

**But heuristic-realizable gain is ~95% smaller than the oracle ceiling.** A boundary sweep across `min_trip_for_C ∈ {3..14, A-only}` produced max gain of **+$0.57/1000h whole-grid at trip ≥ T**. The 95% gap arises because the v33/v34 A-variant heuristic (bot suit profile → rank sum → run) underperforms relative to v33's "mechanical C" pick on the cells that flip — at trip Q, the heuristic-A loses ~$1,857/1000h within-trips on flipped cells (oracle said only −$278 was even achievable). The bot-DS optimizer is the rate-limiting step, not the threshold rule.

**Sweep table:**

| Rule | $/1000h whole-grid | Δ vs v33 | Cells changed |
|---|---:|---:|---:|
| v33 (trip > maxK → C) | $109.83 | baseline | 0 |
| trip ≥ 9 → C | $109.32 | +$0.52 | 81 |
| **trip ≥ T → C (best)** | **$109.27** | **+$0.57** | **226** |
| trip ≥ J → C | $109.83 | $0.00 | 543 |
| trip ≥ Q → C | $112.52 | −$2.69 | 1,151 |
| trip ≥ K → C | $120.01 | −$10.18 | 2,093 |
| Always A | $181.79 | −$71.96 | 5,928 |

**v33's boundary stands as the human strategy of record.** v34_rule6_v2 is archived. The remaining ~$5-13/1000h of unrealized A-vs-C oracle gain is now reframed as a future ML target: a learned A-variant heuristic OR a learned A-vs-C decision tree on (trip_rank, max_kicker_rank, suit profile). v32/v34's gated trips features partially capture this signal already.

**Methodology lessons reinforced (Session 38):**

1. **`min_samples_leaf=2` can unlock more capacity than depth.** When a `ml=3` tree saturates below its depth cap (control: depth=33 actual at depth=34 cap), the next capacity unlock is `ml=2`, NOT deeper depth. **Refines Session 37's rule:** future capacity retests should sweep `min_samples_leaf ∈ {3, 2}` at a generous depth cap, and pick the smaller-ml winner if shape-agreement improves.

2. **Heuristic-realizable ceilings are smaller than oracle ceilings.** Rule 6's heuristic captured 56% of its $197 oracle ceiling (Session 37 finding); Rule 6 v2's would capture only ~5% of its $13 oracle ceiling because the A-heuristic's quality is the rate-limiting step. **Future Always-X probes should report BOTH the oracle ceiling AND the closest heuristic-realizable headline** to set realistic expectations.

3. **Capacity ships are not gating ships.** v34's per-category footprint moves every category simultaneously (textbook capacity signature). Gating ships move ONE category and leave the others bit-identical. This distinction now has 2 instances on each side: capacity-only (v31, v34) vs single-category gating (v20, v23, v24, v25, v26, v27, v29, v30, v32 round-2).

4. **Tripwire was not run for v34 because no new features were introduced.** Same 83 features as v32. The leaf-count growth of +19.5% is the relevant capacity signal, and broad cross-category gains confirm latent signal was leaf-bound, not feature-bound. Tripwire is a feature-design diagnostic; capacity ships use leaf-count + per-category coverage instead.

---

## Session 39: Rule 6 boundary tightening + suit-matching rewrite (v35_rule6_v3 ships in the strategy guide; production heuristic keeps v33)

The user's headline ask was: "the trips strategy doesn't have hard-set rules that are easy to follow yet — can we fix that?" This session rewrote Rule 6 around two human-friendly artifacts:

1. **A sharper boundary table** that maps directly onto Session 38's per-cell oracle data, replacing the `trip_rank vs max_kicker_rank` comparison with an explicit per-trip-rank decision (Trip A always third-on-top; Trip K third-on-top unless an Ace; Trip Q third-on-top unless J/K/A; Trip ≤ J always third-to-bot).
2. **A 2-step suit-matching procedure** for "which trip joins bot" that replaces the prior fuzzy "maximize bot DS-ness" instruction with priority-ordered cases (match a singleton kicker → 2+2 DS, match a fresh suit → 2+1+1 SS, never match the kicker pair → avoid 3+1).

**Verification (`verify_rule6_v3_human.py`)** on the same 30K trips probe:

| Mode | v33 (boundary trip > maxK) | v35 (sharpened) | Δ |
|---|---:|---:|---:|
| **Oracle-bound (HUMAN ceiling)** | -$42.56/1000h whole-grid | **-$34.44/1000h** | **+$8.12** ✓ |
| Heuristic (production bot) | -$113.34/1000h | -$117.40/1000h | -$4.06 ✗ |

v35 captures **63% of the $12.89/1000h oracle ceiling identified in Decision 070**, sacrificing the remaining 37% by simplifying the noisy "Trip J + low-kicker" cells (where C narrowly wins by $50–$1,400 within-trips on small samples). The trade keeps the rule memorable and only loses ~$4.77/1000h vs the optimal-but-unmemorable boundary.

**Per-trip-rank breakdown** (oracle-bound):

| Trip rank | v33 → v35 lift | Driver |
|---|---:|---|
| A, K, 2-5 | $0 | v33 already optimal here |
| 6-Q | +$0.19 to +$2.54/1000h | Sharpened cells flip C → A correctly |
| 8 | +$0.81 | Trip 8 + low kickers |
| 9 | +$1.56 | Same |
| T | +$2.40 | Trip T + low kickers |
| J | +$2.54 | Largest lift — Trip J + maxK low cells |

**Methodology rule (NEW Session 39): the human strategy guide can be sharper than the production heuristic when heuristic-A is the rate-limiting step.** Decision 070 archived v34_rule6_v2 because the heuristic-A bot-DS optimizer couldn't cash a sharper boundary. But the same boundary IS realizable for a thoughtful human, who can pick the oracle-best A-variant pick in any cell (the cell-level A-vs-C choice is the gain; the within-A-routing is what the production heuristic stumbles on). v35 ships in `STRATEGY_GUIDE.md` Part 6 as the human strategy of record. The production bot keeps v33 because runtime evaluation shows the heuristic-A loses $4/1000h on the flipped cells (matching Session 38's sweep finding).

**Decision 071** records this two-track ship.

**A1b — Suit-matching rule for "which trip joins bot"**: replaces v33's fuzzy "maximize bot DS-ness, then rank-sum, then connectivity" with three named cases (kickers two-and-one, kickers rainbow, kickers three-of-a-suit) and three named bot shapes (DS 2+2, SS 2+1+1, 3+1 to avoid). Five worked examples in the Part 6 rewrite. The production heuristic-A is structurally the same procedure (suit_profile dominates the score), so the prose change does not modify production behavior.

**What did NOT happen this session**: Always-X probes for `three_pair`, `composite`, `two_pair`, `high_only` (deferred Priority A2). Round-3 within-trips diagnostic (Priority B). Learned A-vs-C decision tree (Priority C). KK/AA single-suited Rule-4-bot residual (Priority D). All carried into Session 40.

---

## Session 40: Rule 6 low-trips reference table (Trip T..2 worked examples) + connectivity tier rejected

User's Session-39-close ask: "Trip A/K/Q/J got explicit per-rank treatment + worked examples. Trip T..2 got lumped as 'always third trip to bot' — spell out per-rank treatment too." This session delivered three artifacts, all additive (no production code change, no DECISIONS_LOG entry needed).

**A0.1 — Eight new worked examples appended to Part 6.** One per rank from T down to 2 (Examples 7–14), filling in the gap between the existing Trip J (Example 5) and Trip 7 (Example 6). Each example shows a different teaching point: Trip T's rainbow-kickers-all-SS case (no DS available); Trip 9's two-and-one-kickers DS find (the canonical "good" Step 2 outcome); Trip 8's 3+1 trap (where your trip is the kicker-pair suit); Trip 6's 4-card-run bot (illustrating connectivity is incidental); Trip 5's wheel-eligible bot (same point, more dramatic); Trips 4/3/2's plain SS picks on weak hands (illustrating the rule keeps working even when the cards don't). All 8 examples were verified against `strategy_v35_rule6_v3.py` to confirm the picks match the narrative.

**A0.2 — Connectivity tier rejected (`probe_low_trips_connectivity.py`).** Tested the hypothesis that a 4-card run on bot (e.g., trip 5 + 2-3-4 wheel; trip 7 + 4-5-6) should add a connectivity tier between SS and rainbow in Step 2's priority. Three findings:

1. **Connectivity is invariant across the 3 trip-to-bot picks on a given hand.** Within one hand, the bot's longest run is determined by the kicker ranks (which are fixed) plus the trip rank (also fixed) — only suits change between picks. So run-length cannot serve as a tiebreaker; it's identical across candidates.
2. **Mean oracle EV by (suit_profile × longest_run) shows MORE run = WORSE EV inside every profile.** This is selection: hands eligible to make 4-runs are low-trip + low-kicker hands, which are weak overall. Mean EV at "DS run=4" is $-14,156/1000h_within_low_trips vs "DS run=1" at $-3,912 — the run is a signal of weak cards, not of strong settings.
3. **The alt priority "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1" regresses $11/1000h whole-grid versus the existing DS > SS > rainbow > 3+1.** And the oracle picks rainbow 0% of the time when SS or DS is available; rainbow-run-4 picks are oracle-preferred 0/196 (0%) of hands where they exist.

The probe also surfaced a **42% disagreement rate** between v33-heuristic-pick and oracle-pick at low trips. Mean lift on the disagreement subset is +$1,212/1000h_within_low_trips (≈$19.53/1000h whole-grid). The bulk (51% of disagreements) is "SS → SS" — same suit profile, different trip-suit pick. This residual gap is real but is **not** a connectivity story; it would take a finer-grained suit/rank correlation feature to capture (note for Priority C — the learned A-vs-C decision tree could absorb this).

**A0.3 — Per-cell A-vs-C oracle map cross-referenced.** Re-ran `probe_rule6_c_variant.py` on the 30K trips probe (same RandomState(0)). For trip ≤ T at every cell with n≥5, A wins ≥99% of the time and the within-cell C-A delta is structurally negative ($-1,765 to $-15,585/1000h_in even at the lowest max-kicker cells). Confirms v35's "Trip ≤ J always A" boundary is structurally correct, not a noise artifact.

**Score impact:** $0/1000h. This session was additive documentation (the strategy guide) plus a probe whose verdict was "no rule change needed". No new ship.

**Methodology lesson — connectivity in same-rank-set picks is invariant; cannot be a tiebreaker.** A general rule that applies whenever a heuristic enumerates K candidates that share a fixed rank set: features that depend only on ranks (run length, rank-sum, broadway count) are constant across candidates. The only signal worth scoring is what differs (here, suit assignment). Future Step-2-style probes should check candidate-level invariance before adding a feature to the priority.

**Methodology lesson — when a probe's mean-EV-per-cell shows a "feature predicts bad outcomes", check for selection effects.** "Wheel-eligible bots have $-32K mean EV vs $-14K for non-wheel" looks like the wheel is bad; in reality, wheel-eligible hands ARE bad hands. Always read selection effects before drawing rule-shaping conclusions from cross-cell aggregates.

**What did NOT happen this session**: Always-X probes for `three_pair`, `composite`, `two_pair`, `high_only` (Priority A still pending). Round-3 within-trips diagnostic (Priority B). Learned A-vs-C decision tree (Priority C — but the within-SS disagreement signal from this session's connectivity probe makes a useful input to that tree's training). KK/AA single-suited Rule-4-bot residual (Priority D). All carry into Session 41.

---

# Part 2 — ML champion progression (the full table)

Every model trained, side-by-side, on both validation grids:

| Strategy | Session | Depth | min_leaf | Features | Leaves | Full $/1000h | Prefix $/1000h | Status |
|---|---:|---:|---:|---:|---:|---:|---:|---|
| v8_hybrid | pre-S25 | n/a | n/a | n/a | n/a | $3,153 | $3,051 | superseded |
| v14_combined | S26 | n/a | n/a | n/a | n/a | $3,033 | $2,037 | human chain (still useful) |
| v16_prefix | S27 | 15 | 200 | 37 | 1,783 | $8,493 | n/a | ARCHIVED (prefix bias) |
| v16_dt | S27 | 18 | 100 | 37 | 28,790 | $2,464 | $1,607 | superseded |
| v17_rules_then_dt | S28 | n/a | n/a | n/a | n/a | $2,833 | n/a | ARCHIVED |
| v18_dt | S28 | 22 | 50 | 37 | 60,651 | $2,306 | $1,478 | superseded |
| v18b | S29 | 24 | 30 | 37 | 96,409 | $2,217 | $1,343 | superseded |
| v18c | S29 | 26 | 20 | 37 | 124,902 | $2,172 | $1,261 | superseded |
| v19 (ungated suited) | S29 | 22 | 50 | 43 | 72,900 | $2,250 | $1,494 | ARCHIVED (prefix fail) |
| v18d | S30 | 28 | 10 | 37 | 193,365 | $2,108 | $1,145 | superseded |
| v18e | S30 | 30 | 5 | 37 | 274,446 | $2,066 | $1,082 | superseded |
| v19_gated | S30 | 28 | 10 | 43 gated | 215,597 | $2,036 | $1,145 | superseded |
| v20 | S30 | 30 | 5 | 43 gated | 307,939 | $1,982 | $1,082 | superseded by v23 |
| v20b | S31 | 32 | 5 | 43 gated | 307,939 | $1,982 | $1,082 | ARCHIVED (capacity saturated) |
| v21 / v22 | S31 | n/a | n/a | n/a | n/a | $3,713 / $3,506 | n/a | ARCHIVED (Rule 5 attempts vs v14) |
| v23 | S31 | 30 | 5 | 49 (43+6 trips_pair) | 314,705 | $1,977 | $1,073 | superseded by v24 |
| v24 | S31 | 30 | 5 | 53 (49+4 composite) | 314,759 | $1,977 | $1,072 | superseded by v25 |
| v25 | S32 | 30 | 5 | 59 (53+6 pair-gated) | 390,626 | $1,929 | $1,054 | superseded by v26 |
| v26 | S33 | 30 | 5 | 65 (59+6 two_pair-gated) | 459,209 | $1,859 | $1,002 | superseded by v27 |
| v27 | S34 | 30 | 5 | 69 (65+4 high_only-gated) | 460,375 | $1,853 | $1,002 | superseded by v29 (prefix unchanged because prefix has no high_only hands) |
| v29 | S35 | 30 | 5 | 73 (69+4 pair_r4-gated) | 486,342 | $1,807 | $965 | superseded by v30 |
| v30 | S36 | 30 | 5 | 79 (73+6 trips-gated) | 493,057 | $1,794 | $951 | superseded by v31 |
| v31a | S36-overnight | 30 | 5 | 83 (79+4 pair_r4v3 KK/AA-tight) | 500,722 | $1,788 | $951 | ARCHIVED — minimal headline gain ($6 full / $0 prefix) |
| v31b | S36-overnight | 30 | 5 | 83 (79+4 trips_v2 round 2) | 507,692 | $1,779 | $938 | ARCHIVED — solid trips round-2 ($15 full / $13 prefix) but lost vs v31 in cascade |
| v31 | S36-overnight | 32 | 3 | 79 (same as v30) | 699,773 | $1,736 | $921 | superseded by v32 — capacity-only retrain shipped second-largest ship (after v26) with zero new features |
| v32 | S37 | 32 | 3 | 83 (79 v30 + 4 trips_v2 round 2) | 731,606 | $1,715 | $904 | superseded by v34 — stacks trips_v2 round-2 features on v31's high-capacity config; held the ML record briefly between Session 37 and 38 |
| v32_d34ml3 | S38 | 34 | 3 | 83 (same as v32) | 731,611 | $1,715 | $904 | ARCHIVED — control retrain at depth=34 ml=3; +5 leaves vs v32 (depth=33 actual saturation) confirms ml=3 was the binding constraint |
| **v34_dt** | **S38** | **34** | **2** | **83 (same as v32)** | **874,548** | **$1,681** | **$889** | **CURRENT ML CHAMPION** — capacity-only retrain at depth=34 ml=2; +19.5% leaves over v32; ships −$34 full / −$15 prefix and lifts every category. Cumulative v30 → v34 of $113/1000h is the new largest cumulative arc in project history |

**Per-category breakdown** (full grid, N=200): how each category's
regret has dropped across the flagship versions:

| Category | v14 | v16 | v18e | v20 | v25 | v26 | v27 | v29 | v30 | v31 | v32 | v34 | Δ v34 vs v14 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high_only | $4,082 | $3,785 | $3,307 | $2,894 | $2,894 | $2,894 | $2,863 | $2,862 | $2,862 | $2,816 | $2,816 | **$2,806** | **−$1,276** |
| pair | $2,011 | $2,127 | $1,873 | $1,873 | $1,771 | $1,771 | $1,771 | $1,674 | $1,674 | $1,639 | $1,639 | **$1,619** | **−$392** |
| two_pair | $3,371 | $2,005 | $1,458 | $1,458 | $1,458 | $1,145 | $1,145 | $1,145 | $1,145 | $1,037 | $1,037 | **$978** | **−$2,393** |
| trips | $4,054 | $2,347 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,758 | $1,732 | $1,359 | **$1,291** | **−$2,763** |
| trips_pair | $5,417 | $2,438 | $1,608 | $1,608 | $1,446 | $1,445 | $1,445 | $1,443 | $1,442 | $1,225 | $1,225 | **$1,057** | **−$4,360** |
| three_pair | $4,529 | $1,975 | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | $1,639 | $1,639 | **$1,635** | **−$2,894** |
| quads | $9,670 | $2,233 | $724 | $724 | $723 | $723 | $723 | $723 | $723 | $645 | $645 | **$613** | **−$9,057** |
| composite | $10,883 | $5,260 | $2,100 | $2,100 | $1,869 | $1,741 | $1,741 | $1,741 | $1,733 | $1,387 | $1,386 | **$1,173** | **−$9,710** |

Eight category-gated wins are now visible across the v18e → v31
progression, plus one capacity-only ship (v31):
- **v20 → high_only-via-suited:** −$413 vs v18e (6 gated suited features).
- **v23 → trips_pair:** −$161 vs v20 (6 gated trips_pair features).
- **v24 → composite:** −$216 vs v23 (4 gated composite features).
- **v25 → pair (v1):** −$102 vs v24 (6 gated pair features).
- **v26 → two_pair:** −$313 vs v25 (6 gated two_pair features). Largest
  per-category gain since v20→high_only.
- **v27 → high_only-direct:** −$31 vs v26 (4 gated high_only features).
  Smallest per-category gain to date — diagnostic was speculative.
- **v29 → pair (v2):** −$97 vs v27 (4 gated pair_r4 features).
  **First successful within-category iteration — pair has now seen
  TWO independent gating-template ships, totaling −$199 within-pair
  vs v18e.** Diagnostic-driven from `distill_v27_pair.py`'s
  competing-baseline analysis — the most prescriptive feature design
  in project history.
- **v30 → trips:** −$239 vs v29 (6 gated trips features). 8th gating-
  template instance. First trips-category gating ship.
- **v32 → trips round-2:** −$373 vs v31 (4 gated trips_v2 features stacked
  on v31's capacity config). 9th gating-template instance and the FIRST
  within-trips iteration; same template-second-iteration pattern as v25→v29
  for pair.
- **v34 → capacity-only at ml=2:** −$34 whole-grid vs v32 (zero new features;
  874K leaves vs v32's 731K). 2nd capacity-only ship (after v31); per-category
  shape moves every category, with biggest gains in the previously-gated
  composite (−$213 within-cat) and trips_pair (−$168). The control retrain
  at depth=34 ml=3 reproduced v32 exactly, proving ml=3 was the leaf-binding
  constraint, not depth.

Each gating upgrade lifted ONLY its targeted category and kept every other
category bit-identical (or within N=200 noise) — the cleanest possible
controlled-experiment shape for feature engineering. Every change also
trivially passes the prefix N=1000 tripwire because the new features
fire on zero off-archetype hands by design.

**v31 is the exception to the per-category controlled-experiment shape.**
It's a CAPACITY-ONLY retrain (depth=32 ml=3 vs v30's depth=30 ml=5,
identical 79 features). All 8 categories improve simultaneously. The
biggest gains accrue to PREVIOUSLY-GATED categories (composite −$346,
trips_pair −$217, two_pair −$108, quads −$78), confirming the
hypothesis that v25-v30's gating features had been encoded but not
fully expressed within v30's leaf budget. **+42% leaf-count expansion
(493K → 700K) unlocks $58/1000h whole-grid in one config change** —
22% of what the cumulative 6-ship gating-template work added.

---

# Part 3 — Distillation insights (Session 28, from v16's tree)

Walked all 6M oracle-grid hands through v16's 28,790-leaf tree. These
findings still hold — they're about how the DT thinks, which is roughly
the same in v18 and v20 (the bigger trees just have more partition
detail).

## Feature importance (top 8, population-weighted MSE reduction)

| Rank | Feature | % of total | What it captures |
|---:|---|---:|---|
| 1 | `n_broadway` | 44.9% | Count of T-J-Q-K-A cards (0..7) |
| 2 | `third_rank` | 11.5% | Rank of 3rd-highest distinct rank (body strength) |
| 3 | `pair_high_rank` | 8.8% | Rank of highest pair (0 if none) |
| 4 | `n_low` | 7.7% | Count of 2-5 cards |
| 5 | `has_premium_pair` | 4.5% | KK or AA flag |
| 6 | `top_rank` | 4.3% | Highest rank in hand |
| 7 | `second_rank` | 3.8% | 2nd-highest distinct rank |
| 8 | `has_ace_singleton` | 3.4% | A in hand, no A-pair/trip/quad |

The 9 hand-engineered "aug" features (default_bot_is_ds_*,
n_routings_yielding_ds_bot_*, etc.) collectively contribute **<0.4%**
of total importance. The DT solves the problem almost entirely with
raw body-strength features.

## Key insight: `n_broadway` is the master signal

The root split is `n_broadway ≤ 2.5` and that single split alone
accounts for $4M of the total $11M MSE reduction in the tree.

| n_broadway | What the DT does |
|---:|---|
| 0–2 | Bias toward placing the few high cards in bot or mid; default plays well |
| 3 | Mixed — splits further on premium-pair / ace-singleton |
| 4–7 | Premium pair → mid (Rule 4); else default |

## What the v16 DT does NOT see

- **Suited pairs of broadway cards** (e.g. K♦Q♦ together) — there is
  no feature for "do I have a same-suit pair of cards both ≥ T"
- **Connected high cards** (e.g. J-Q-K) — captured only via
  `connectivity` (longest run) which lumps low and high runs together

The first of these was addressed in Session 30 by the gated
suited-broadway features → v20's $413/1000h gain on high_only. The
second is still open — a `connectivity_high` feature (longest run
restricted to broadway ranks) is a Session 31+ candidate.

## v20's biggest tree-shape changes (informal)

v20 has 307K leaves vs v16's 28K (10.9× more). Most of the new
partitions are in the composite category (where v16 was $5,260/1000h
and v20 is $2,100). v20 has not been formally distilled yet — Session
31 priority A.

---

# Part 4 — What's NOT yet covered

| Hand type | Frequency | v14 $/1000h | Latest $/1000h | Status |
|---|---:|---:|---:|---|
| high_only | 20.4% | $4,082 | $2,816 (v31) | v27 (Session 34) added 4 high_only-gated features (`ho_n_broadway_in_2nd_suit_g` and 3 others); −$31/1000h on the category. v31 (Session 36 capacity-only retrain) brings it to $2,816 (−$46 vs v30 from depth=32 ml=3 capacity expansion). Smallest gating gain to date but capacity-aware retraining unlocks more. A naive **Rule 5** (suited middle for high_only) was tested both ways in Session 31 and **REJECTED** — see below. |
| pair | 46.6% | $2,011 | $1,639 (v31) | TWO gating ships: v25 (Session 32) added 6 features encoding kickers-in-pair-suit / alt-routing rank quality (−$102 within-pair); v29 (Session 35) added 4 features encoding Rule-4-bot suit profile + body-card distribution (−$97 within-pair). v31 (Session 36 capacity retrain) brings within-pair to $1,639 (−$35 vs v30). v29 was diagnostic-driven from `distill_v27_pair.py`'s competing-baseline analysis (v27 was actually $20/1000h whole-grid WORSE than Rule 4 alone on KK/AA — overgeneralizing v25's features). **Rule 5 (Rainbow override) ships to STRATEGY_GUIDE for human play (Decision 063).** Open: KK/AA single-suited Rule-4-bot stratum (52.9% of KK/AA, $37/1000h below oracle within-stratum). v31a candidate (KK/AA-tight features) tried Session 36 overnight, shipped only +$6 — different angle needed (e.g., meta-classifier or sub-tree dedicated to KK/AA). |
| trips (no pair) | 5.5% | $4,054 | $1,732 (v31) | v30 (Session 36) added 6 trips-gated features (`trips_*_g`) — first trips gating ship. −$239 within-trips on full grid. Diagnostic surfaced the largest gap-to-baseline in project history: v29 was $85/1000h whole-grid WORSE than always-A_paired_mid. v31 capacity retrain adds another −$26 within-trips. v32 candidate = v31b's trips_v2 round-2 features (C_top + finer A/B routing) at v31's high-capacity config, expected ~$15-20 incremental. **Always-A_paired_mid** is a Rule 6 candidate worth investigating for STRATEGY_GUIDE — captures $85/1000h whole-grid relative to v29's deviations. Likely already implicit in v14_combined; needs verification. |
| trips_pair | 2.9% | $5,417 | $1,225 (v31) | v23 (Session 31) added 6 trips_pair-gated features; −$161/1000h on the category. v31 capacity retrain adds **another −$217 within-trips_pair** — the SECOND-largest single-category drop from a non-gating ship. The trips_pair gating from v23 had been adding signal but v30's leaf budget couldn't fully express it; capacity unlocks the latent value. No hand-coded rule extracted; the DT routing is multi-axis. |
| three_pair | 1.9% | $4,529 | $1,639 (v31) | No human rule yet. v31 capacity retrain adds −$15 within-three_pair. Untouched by gating. |
| two_pair | 22.3% | $3,371 | $1,037 (v31) | v26 (Session 33) added 6 two_pair-gated features alongside the 3 pre-existing two_pair aug booleans; −$313/1000h on the category. v31 capacity retrain adds another −$108 within-two_pair. The 6 features split Layout B (high pair → mid) from Layout C (low pair → mid) which the existing 3 features lumped together. |
| quads | 0.2% | $9,670 | $645 (v31) | v20 captures heavily; v31 capacity retrain adds −$78 within-quads. No human rule. Below noise floor for further gating. |
| composite | 0.2% | $10,883 | $1,387 (v31) | v24 (Session 31) added 4 composite-gated features for archetype-specific routing. v31 capacity retrain adds **−$346 within-composite** — the LARGEST single-category drop from any non-gating ship. The composite gating from v24 had been substantially under-expressed; capacity unlocks the latent value. Composite is also the smallest population share (0.245%) so this $346 within-category translates to only $1/1000h whole-grid contribution change. |

**Rule 5 candidates — REJECTED (Session 31):** Two attempts to extract a
suited-mid rule from v20's gated features both lost head-to-head against
v14_combined:

| Strategy | Full $/1000h | Δ vs v14 |
|---|---:|---:|
| v14_combined + Rule 4 | $3,033 | — |
| v21 = v14 + Rule 5 (msphr ≥ 9, "any high suited pair") | $3,713 | −$680 |
| v22 = v14 + Rule 5 (msphr ≥ 11 AND msplr ≥ 9, tightened) | $3,506 | −$473 |

Both variants fire on far more high_only hands than the population that
actually benefits from suited-mid routing (the rule is ~8× over-eager
relative to the DT's selective routing). The DT's gated splits use 4+
distinct rank thresholds combined with `n_low` / `n_broadway` that no
single AND-rule can replicate. **For the human strategy: stop at Rule 4.
For computational play: use the DT champion (v23 or v24).** See
Decision 056 in DECISIONS_LOG.md.

**v17 hybrid attempt (rules-then-DT) was archived in Session 28.**
Hand-coded rules can be inferior to the DT in their own categories.
Don't chain them in front of the DT in production code; the strategy
guide can keep them as human-memorizable approximations.

---

# Part 5 — Where each rule + model lives in code

**Human rules:**
- Rule 1 → `analysis/scripts/strategy_v9_2_pair_to_bot_ds.py`
- Rule 2 → `analysis/scripts/strategy_v10_two_pair_no_split.py`
- Rule 3 → `analysis/scripts/strategy_v12_trips_pair.py`
- Rule 4 → encoded implicitly in `analysis/scripts/strategy_v8_hybrid.py`
  (via `encode_rules.strategy_v3`'s pair-to-mid default). v3 / v8 /
  v16 / v18 / v20 all agree on the canonical KK and AA play; Rule 4
  is documentation, not a separate code path.
- Rule 5 (KK/AA rainbow override) → `analysis/scripts/strategy_v28_rule5_rainbow.py`
- Rule 6 v1 (production heuristic, Session 37) → `analysis/scripts/strategy_v33_rule6_trips.py` — boundary `trip_rank > max_kicker_rank → C, else A`. Production runtime stays here.
- Rule 6 v3 (sharper human boundary, Session 39) → `analysis/scripts/strategy_v35_rule6_v3.py` — explicit per-trip-rank table (Trip A always third-on-top; K only if no Ace; Q only if no J/K/A; J or lower never). Strategy guide ceiling +$8.12/1000h whole-grid vs v33 oracle-bound; production heuristic-A loses at runtime, so used for human-play guidance only.
- Combined chain (4 rules) → `analysis/scripts/strategy_v14_combined.py`
- Combined chain (5 rules) → `analysis/scripts/strategy_v28_rule5_rainbow.py` (wraps v14 with Rule 5)
- Combined chain (6 rules, current production) → `analysis/scripts/strategy_v33_rule6_trips.py` (wraps v28 with Rule 6 v1)
- Combined chain (6 rules, current human-guide) → `analysis/scripts/strategy_v35_rule6_v3.py` (wraps v28 with Rule 6 v3)

**Probes:**
- Per-cell A-vs-C oracle map (Session 38) → `analysis/scripts/probe_rule6_c_variant.py`
- v33→v34 boundary sweep (Session 38) → `analysis/scripts/probe_v34_sweep.py`
- v35 human-decision verification (Session 39) → `analysis/scripts/verify_rule6_v3_human.py`

**ML champion + baselines (newest first):**
- v31 (CURRENT CHAMPION) → `analysis/scripts/strategy_v31_dt.py` + `data/v31_dt_model.npz` (700K leaves, 79 features, depth=32 ml=3 — capacity-only retrain of v30)
- v30 → `analysis/scripts/strategy_v30_dt.py` + `data/v30_dt_model.npz` (493K leaves, 79 features, depth=30 ml=5)
- v29 → `analysis/scripts/strategy_v29_dt.py` + `data/v29_dt_model.npz` (486K leaves, 73 features)
- v27 → `analysis/scripts/strategy_v27_dt.py` + `data/v27_dt_model.npz` (460K leaves, 69 features)
- v26 → `analysis/scripts/strategy_v26_dt.py` + `data/v26_dt_model.npz` (459K leaves, 65 features)
- v25 → `analysis/scripts/strategy_v25_dt.py` + `data/v25_dt_model.npz` (391K leaves, 59 features)
- v24 → `analysis/scripts/strategy_v24_dt.py` + `data/v24_dt_model.npz` (315K leaves, 53 features)
- v23 → `analysis/scripts/strategy_v23_dt.py` + `data/v23_dt_model.npz` (315K leaves, 49 features)
- v20 → `analysis/scripts/strategy_v20_dt.py` + `data/v20_dt_model.npz` (308K leaves)
- v18e → `data/v18e_dt_model.npz` (274K leaves)
- v18d → `data/v18d_dt_model.npz` (193K leaves)
- v18c → `analysis/scripts/strategy_v18c_dt.py` + `data/v18c_dt_model.npz` (125K leaves)
- v18 → `analysis/scripts/strategy_v18_dt.py` + `data/v18_dt_model.npz` (61K leaves)
- v16 → `analysis/scripts/strategy_v16_dt.py` + `data/v16_dt_model.npz` (29K leaves)

**Trainers:**
- v31 trainer = v30 trainer with `--max-depth 32 --min-samples-leaf 3` → `analysis/scripts/train_v30_dt.py` (no separate train_v31 file; v31 differs only in hyperparameters)
- v30 trainer (79 features incl. all 8 gated families) → `analysis/scripts/train_v30_dt.py`
- v29 trainer (73 features incl. 7 gated families) → `analysis/scripts/train_v29_dt.py`
- v27 trainer (69 features incl. 6 gated families) → `analysis/scripts/train_v27_dt.py`
- v26 trainer (65 features incl. 5 gated families + 3 pre-existing pair-gated booleans + 3 pre-existing two_pair-gated booleans) → `analysis/scripts/train_v26_dt.py`
- v25 trainer (59 features incl. 4 gated families + 3 pre-existing pair-gated booleans) → `analysis/scripts/train_v25_dt.py`
- v24 trainer (53 features incl. 3 gated families + 3 pre-existing pair-gated booleans) → `analysis/scripts/train_v24_dt.py`
- v23 trainer (49 features incl. gated suited + gated trips_pair) → `analysis/scripts/train_v23_dt.py`
- v18 capacity trainer (37 features) → `analysis/scripts/train_v18_dt.py`
- v19_gated trainer (43 features incl. gated suited) → `analysis/scripts/train_v19_gated_dt.py`
- v16 trainer (legacy, recomputes features) → `analysis/scripts/train_v16_regression.py`

**Aug feature compute:**
- Pair (3 pre-existing, already category-gated since Session 17 despite no `_g` suffix) → `analysis/scripts/pair_aug_features.py`
- Pair persist → `analysis/scripts/persist_aug_features.py` → `data/feature_table_aug.parquet`
- Gated pair (Session 32, 6 new features) → `analysis/scripts/pair_aug_features_gated.py`
- Gated pair persist → `analysis/scripts/persist_pair_aug_gated.py` → `data/feature_table_pair_aug_gated.parquet`
- Two_pair (3 pre-existing, already category-gated since Session 19) → `analysis/scripts/two_pair_aug_features.py` → `data/feature_table_two_pair_aug.parquet`
- Gated two_pair (Session 33, 6 new features, prefix `t2p_*`) → `analysis/scripts/two_pair_aug_features_gated.py`
- Gated two_pair persist → `analysis/scripts/persist_two_pair_aug_gated.py` → `data/feature_table_two_pair_aug_gated.parquet`
- Gated high_only-direct (Session 34, 4 new features, prefix `ho_*`) → `analysis/scripts/high_only_aug_features_gated.py`
- Gated high_only-direct persist → `analysis/scripts/persist_high_only_aug_gated.py` → `data/feature_table_high_only_aug_gated.parquet`
- Gated pair_r4 (Session 35, 4 new features, prefix `pair_r4_*`) → `analysis/scripts/pair_aug_v2_features_gated.py`
- Gated pair_r4 persist → `analysis/scripts/persist_pair_aug_v2_gated.py` → `data/feature_table_pair_aug_v2_gated.parquet`
- Gated trips (Session 36, 6 new features, prefix `trips_*` — NOT `tp_*` which is trips_pair) → `analysis/scripts/trips_aug_features_gated.py`
- Gated trips persist → `analysis/scripts/persist_trips_aug_gated.py` → `data/feature_table_trips_aug_gated.parquet`
- Gated pair_r4v3 (Session 36 overnight, 4 KK/AA-tight features, prefix `pair_r4v3_*` — ARCHIVED, candidate v31a) → `analysis/scripts/pair_aug_v3_features_gated.py`
- Gated trips_v2 (Session 36 overnight, 4 round-2 features, prefix `trips_v2_*` — ARCHIVED for now, candidate v31b; SLATED for v32 stack on top of v31's high-capacity config) → `analysis/scripts/trips_aug_v2_features_gated.py`
- Gated suited (high_only-via-suited, Session 30) → `analysis/scripts/suited_aug_features_gated.py`
- Gated suited persist → `analysis/scripts/persist_suited_aug_gated.py`
- Gated trips_pair → `analysis/scripts/trips_pair_aug_features_gated.py`
- Gated trips_pair persist → `analysis/scripts/persist_trips_pair_aug_gated.py`
- Gated composite → `analysis/scripts/composite_aug_features_gated.py`
- Gated composite persist → `analysis/scripts/persist_composite_aug_gated.py`

**Analysis:**
- v16 distillation → `analysis/scripts/distill_v16_dt.py`
- v26 high_only distillation (Session 34) → `analysis/scripts/distill_v26_high_only.py`
- v27 pair distillation + KK/AA capture analysis (Session 35) → `analysis/scripts/distill_v27_pair.py`
- v29 pair distillation round-2 + KK/AA round-2 audit (Session 36) → `analysis/scripts/distill_v29_pair.py`
- v29 trips distillation + routing-baseline analysis (Session 36) → `analysis/scripts/distill_v29_trips.py`
- KK/AA Rule-4 boundary probe (Session 34) → `analysis/scripts/probe_kk_aa_ds_bot_vs_mid.py` + `data/kk_aa_rule4_probe.csv`
- KKK/AAA routing probe (Session 34) → `analysis/scripts/probe_trips_kkk_aaa_routing.py` + `data/kkk_aaa_routing_probe.csv`
- Overnight v31 cascade runner (Session 36 → 37) → `analysis/scripts/overnight_v31_cascade.sh`
- High_only residual diagnostic → `analysis/scripts/high_only_v16_residual.py`
- Multi-strategy sweep grader → `analysis/scripts/grade_v18_sweep.py`

**Ground-truth grids (gitignored, large):**
- Full 6M × N=200 → `data/oracle_grid_full_realistic_n200.bin` (2.55 GB)
- Prefix 500K × N=1000 → `data/oracle_grid_prefix500k_n1000.bin`

**To validate any new rule against the grid in ~4 minutes:**
```python
from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid

grid = read_oracle_grid("data/oracle_grid_full_realistic_n200.bin", mode="memmap")
ch = read_canonical_hands("data/canonical_hands.bin", mode="memmap")
result = grade_strategy(my_strategy_fn, grid, ch, label="my_strategy")
print(result.summary())
```

---

# Part 6 — THE CURRENT STANDARD

> Everything below this line is the active rule set as of Session 37.
> If you only read one section, read this one.
>
> **Human-memorizable strategy of record: v14_combined + Rule 4 + Rule 5.**
> Five numbered rules plus a default play. Edge over v8_hybrid baseline:
> **+$1,015/1000h** at $10/EV-pt (full grid, N=200). A naive Rule 5
> (suited-mid for high_only) was tested in Session 31 in two flavors and
> **REJECTED**; the Rule 5 here (KK/AA Rainbow override, Session 34) is
> a much tighter structural rule that fires on only 0.27% of hands and
> is the **first successful Rule 5 in project history** — see Decision
> 063 in DECISIONS_LOG.md.
>
> **Rule 4 extends to KKK and AAA.** The Session 34 probe
> `probe_trips_kkk_aaa_routing.py` confirms that "keep 2 of 3 trip-rank
> cards in mid as a pair" is BR-optimal on **79.18%** of KKK/AAA hands
> (83.84% for AAA, 74.53% for KKK). The DS-bot-split exception (~24%
> of geometrically-eligible cases) is hard to apply manually pre-flop;
> for human play, treat KKK and AAA the same as KK and AA — pair in mid.
> See Decision 062.
>
> **Open Rule 6 candidate (Session 36 finding, not yet codified):**
> The trips diagnostic (`distill_v29_trips.py`) showed that **Always
> A_paired_mid** (set 2 of 3 trip-rank cards in mid as a pair) captures
> $85/1000h whole-grid relative to v29's 80%-A / 20%-deviation pattern.
> This is the structural analog of Rule 4 for trips, EXTENDED beyond
> KKK/AAA to all trip ranks. v14_combined likely already encodes this
> implicitly via its v3 default; needs verification before formal Rule 6
> codification. The per-rank deviation cost from v29 is highest on low
> trips (2-9 each leak $7-8/rank-share). See Decision 065 and 066.
>
> **ML champion (not human-memorizable): v31_dt** — 699,773-leaf
> DecisionTreeRegressor (depth=32, min_samples_leaf=3), 79 features
> including 6 gated suited-broadway (high_only-via-suited), 6 gated
> trips_pair, 4 gated composite, 6 gated pair (v1), 6 gated two_pair,
> 4 gated high_only-direct, 4 gated pair_r4 (Session 35), and 6 gated
> trips (Session 36). Beats v14 by **+$1,297/1000h** on the full grid
> and **+$1,116/1000h** on the prefix N=1000. Lives at
> `analysis/scripts/strategy_v31_dt.py` + `data/v31_dt_model.npz`.
> (v30 — the predecessor at depth=30 ml=5 with the same 79 features —
> remains useful as a "smaller model" reference; v29 if you need a
> 73-feature comparison; v27 for the 69-feature baseline before pair_r4.)
>
> **v31 is a CAPACITY-ONLY ship — zero new features vs v30.** This is
> the second-largest single ML ship in project history (after v26's
> +$70). The methodological lesson: when feature-count grows substantially
> beyond the last capacity-saturation test, RE-TEST capacity. Future ML
> champion ships should default to `depth=32 ml=3` going forward.

---

## How to use this guide (current standard)

Walk through Step 1, then apply the matching rule from Step 2.
For hand types not covered, play it the obvious way (highest card on top,
suited cards together in mid, rest to bot) — that's what v8 does and it's
adequate on the un-ruled categories.

---

## Step 1 — Categorize your 7 cards

Look for the strongest "shape" in your hand:

| Shape | Cards | Apply rule |
|---|---|---|
| Quads | 4 of one rank | (no rule yet — rare, ~0.2% of hands) |
| Trips + pair | 3 of one rank + 2 of another | **Rule 3** |
| Trips (any rank, no other pair) | 3 of one rank, no other pair | **Rule 6** — mid is always 2 of the 3 trip cards |
| Two pairs | 2 of one rank + 2 of another | **Rule 2** |
| One pair (KK or AA) | 2 Kings or 2 Aces | **Rule 4** (default), check **Rule 5** for rainbow override |
| One pair (other ranks) | 2 of one rank, no other multiples | **Rule 1** (gates apply) |
| No pair | 7 distinct ranks | (no simple rule yet — multi-archetype) |

---

## Rule 1 — Single pair: pair-to-bot for double-suited

**Fires only if ALL of these are true:**

1. **Pair rank is 2-5 OR T-J-Q.** Skip 6-7-8-9 (Goldilocks zone — pair stays in mid).
2. **Exactly one Ace** in the hand. No pair of Aces, no second pair of any rank.
3. **The pair has two different suits** (e.g., Q♣ + Q♦). Same-suit pairs can't anchor a double-suited bot.
4. **Kickers are balanced between the pair's two suits.** Count the 4 non-pair, non-Ace cards. Of those, count how many match each pair-suit. Must be **(1,1), (2,2), (1,3), or (3,1)**. Skip lopsided **(2,1) or (1,2)**.

**The play (when fired):**
- **Top** = the Ace
- **Bot** = both pair-cards + the LOWEST kicker of each pair-suit (gives a 2+2 double-suited bot)
- **Mid** = the 2 leftover kickers

**Worked example:** `3♣ 4♦ 8♦ 9♣ Q♣ Q♦ A♣`
- Pair = QQ ✓ (rank 12), one Ace ✓, two pair-suits ✓
- Kickers split: clubs {3♣, 9♣} = 2, diamonds {4♦, 8♦} = 2 → (2,2) balanced ✓
- Lowest club kicker = 3♣, lowest diamond kicker = 4♦
- → **Top = A♣, Mid = 9♣ + 8♦, Bot = Q♣ + Q♦ + 3♣ + 4♦**

**Counter-example (don't fire):** `Q♣ Q♦ A♥ 3♣ 5♣ 4♦ 9♠`
- Kickers: 3♣, 5♣ are clubs (matching Q♣) = 2; 4♦ is diamond (matching Q♦) = 1; 9♠ is spade = 0
- (n_clubs, n_diamonds) = (2, 1) → lopsided, **don't fire**
- Play it the v8 way (pair in mid).

**Why it works:**
- **Low pairs (2-5)**: weak in mid (a pair of 4s loses Hold'em to almost any pair). Better to use the pair as a bot suit-anchor for a DS flush draw.
- **High non-anchor pairs (J-Q)**: strong in mid, but bot-pair-with-DS is even stronger — you keep the pair value AND gain two flush draws.
- **Mid pairs (6-9)**: Goldilocks zone. Strong enough in mid (wins Hold'em often) and not strong enough that bot help is needed. Leave them in mid.
- **KK / AA**: keep in mid (see Rule 4).
- **Asymmetric kickers**: when (n_a, n_b) is (2,1) or (1,2), the leftover-mid is two cards of mismatched suits with no Hold'em synergy — a weak mid. Symmetric kickers preserve mid strength.

**Fires on:** 2.19% of all hands (~1 in 45 you'll be dealt).

---

## Rule 2 — Two pairs: never split either pair

**Fires whenever you have exactly two pairs** (and no trips/quads).

**The play:** never break either pair. There are exactly 3 valid no-split layouts:

| Layout | Mid | Bot | Top |
|---|---|---|---|
| A | 2 kickers | both pairs (4 cards) | 1 kicker |
| B | higher pair | lower pair + 2 kickers | 1 kicker |
| C | lower pair | higher pair + 2 kickers | 1 kicker |

**Pick the layout that maximizes (in order):**
1. Bot is double-suited (2+2) > single-suited (2+1+1) > rainbow > 3+1 > 4-flush
2. Top rank (Ace > K > Q ...)
3. Mid is paired > offsuit broadway > suited connector > other

**Worked example:** `7♣ 7♦ 8♣ 8♦ J♥ K♠ A♠`
- Two pairs: 88 and 77.
- **What v8 wrongly does**: top=K, mid=8♣+7♦ (suited connector), bot=A+J+8+7 (rainbow with both pairs split). Bleeds **$46K/1000h**.
- **What Rule 2 does**: Layout A — top=A♠, mid=K♠+J♥ (offsuit broadway), bot=8♦+8♣+7♦+7♣ (both pairs intact, double-suited).

**Why it works:**
- Two pairs as a unit in the bot give you a guaranteed Omaha 2-pair AND two flush draws.
- v8's "suited connector mid" trade gives up a much stronger bot for a moderately stronger mid — the tier-importance ratio (bot:mid:top = 3:2:1) means bot wins.
- The pair that joins the bot uses ITS suits as the bot's DS anchors.

**Fires on:** every two_pair hand (~22% of all hands you'll be dealt).

---

## Rule 3 — Trips + pair: split the trips, keep the pair

**Fires when you have 3 of one rank + 2 of another + 2 kickers.**

**The play:** the trips MUST split (3 of them can't fit in mid; mid only holds 2). Keep the pair intact. Two valid layouts:

| Layout | Mid | Bot | Top |
|---|---|---|---|
| A | 2 of the 3 trip-cards (paired mid) | original pair + 1 trip-overflow + 1 kicker | 1 kicker |
| B | 1 trip + 1 kicker | original pair + 2 trip-cards (4 cards = 2 pairs) | 1 kicker |

**Pick by priority:**
1. Bot is double-suited > SS > rainbow
2. Top rank
3. Slight preference for Layout A (paired mid is robust)

**Worked example:** `4♣ T♦ T♥ T♠ J♣ J♦ Q♦`
- Trips = TTT, pair = JJ, kickers = 4♣ + Q♦.
- **What v10 wrongly does**: top=J, mid=Q+J, bot=T+T+T+4 (rainbow, breaks the trips weirdly). Bleeds **$50K/1000h**.
- **What Rule 3 does**: Layout A — top=Q♦, mid=T♠+T♥ (paired mid), bot=J♦+J♣+T♦+4♣ (DS).

**Why it works:**
- A paired-mid (2 of the 3 trip cards) is roughly as strong as the original pair-in-mid would be.
- The bot gets the original pair + 1 trip-card + 1 kicker — that's TWO PAIRS in the bot with DS anchors. Much stronger than v8's "all 3 trips in bot, no pair structure."

**Fires on:** every trips_pair hand (~3% of all hands).

---

## Rule 4 — Premium pair (KK or AA): pair stays intact in mid

**Fires whenever your pair is KK or AA** (and you don't have quads).

This rule formalizes what `strategy_v8_hybrid` (and therefore the v14
fallback) already does, and the v16 DT confirms is correct. It's been
implicit in the codebase since v3; making it explicit here so a human
memorizing the strategy doesn't accidentally split the pair.

**The play:**
- **Mid** = both pair cards (KK or AA), intact
- **Top** = the highest non-pair card you hold (the Ace if KK + lone Ace;
  otherwise the next-highest singleton)
- **Bot** = the remaining 4 cards

**Worked example (KK with lower body):** `4♣ 6♦ 8♥ J♠ Q♦ K♣ K♠`
- Pair = KK. Highest non-pair = Q♦.
- **Play**: top=Q♦, mid=K♣+K♠ (intact), bot=4♣+6♦+8♥+J♠.

**Worked example (KK with Ace singleton):** `4♣ 6♦ 8♥ Q♦ K♣ K♠ A♥`
- Pair = KK plus an A♥ singleton. Highest non-pair = A♥.
- **Play**: top=A♥, mid=K♣+K♠ (intact), bot=4♣+6♦+8♥+Q♦.
- *No K split occurs* — the Ace becomes top, the KK stays in mid, the
  Q drops to bot. v3 / v8 / v16 / v20 all agree on this exact setting.

**Worked example (AA + broadway body):** `9♣ T♦ J♥ Q♠ K♣ A♦ A♠`
- Pair = AA. Highest non-pair = K♣.
- **Play**: top=K♣, mid=A♦+A♠ (intact), bot=9♣+T♦+J♥+Q♠.

**AA-with-low-body edge case:** `2♣ 3♦ 4♥ 5♠ 6♣ A♥ A♠`
- Pair = AA, body is all 2-6. v3/v8 pick top=6♣ (highest non-A).
- v16 picks **top=2♣ (lowest), mid=A♥+A♠, bot=3♦+4♥+5♠+6♣**. The DT is
  trading top strength (a 6 on top loses 90% anyway) for a slightly
  stronger bot (3-4-5-6 connected, gives a wheel-style straight draw).
- For human play, follow Rule 4 as stated (top = highest non-pair). The
  edge case is a small EV refinement ($0.01-0.05/hand) that requires
  computing 105 EVs to justify and doesn't generalize cleanly.

**Why it works:**
- KK and AA are the strongest mid-tier Hold'em holdings (win ~80% of
  unpaired-board matchups). Splitting them throws away most of that
  value for marginal top upside.
- The "highest non-pair to top" subrule is what v3/v8/v16/v20 all
  converge on — when KK + A are present, the A naturally goes to top
  because it's the highest non-K (no special-case needed).
- `has_premium_pair` is the 5th-most-important feature in the v16 DT
  (4.5% of total feature importance) — the model discovered this
  population split on its own.

**Fires on:** 7.17% of all hands (KK 3.58% + AA 3.58%).

---

## Rule 5 — KK/AA Rainbow override: swap to DS-bot when Rule 4 leaves a rainbow Omaha hand

**Fires only when ALL of these are true** (very narrow trigger — fires on ~0.27% of all hands):

1. **Pair = KK or AA** (Rule 4 territory)
2. **Pair has two different suits** (e.g., K♠+K♦ — DS-anchor possible)
3. **Apply Rule 4 mentally and look at the resulting bot.** If the 4 leftover cards (after putting the highest non-pair card on top and the pair in mid) span all 4 suits → **bot is rainbow**.
4. **DS-bot is geometrically possible:** at least one kicker matches each pair-suit.

**The play (when fired):** Override Rule 4 — put the pair in bot.
- **Bot** = both pair-cards + the lowest-rank kicker matching each pair-suit (gives a 2+2 double-suited bot)
- **Top** = the highest-rank card of the 3 leftover non-pair cards
- **Mid** = the other 2 leftover cards (will often be off-suit and weak — that's OK)

**Worked example (the canonical case):** `K♠K♦ 3♠ 5♦ 9♥ T♣ J♠`
- Pair = KK ✓, two different suits (♠+♦) ✓
- Rule 4 routing: top=J♠, mid=K♠K♦, bot=3♠5♦9♥T♣ — bot has 1 of each suit → **rainbow**, trigger fires.
- DS-bot available: 3♠ matches ♠, 5♦ matches ♦ ✓
- Rule 5 play: **bot = K♠K♦5♦3♠** (2 ♠ + 2 ♦, double-suited), **top = J♠** (highest leftover), **mid = T♣9♥**
- EV result: Rule 5 routing scores **+3.025 EV** vs Rule 4's +1.225 EV — **the override wins by 1.80 EV ($18,000/1000h on this single hand)**.

**Why it works:**
- A rainbow Omaha bot is essentially dead — you can't make any flush or strong-suited play. Whatever's in mid (a pair of Kings) is also limited to Hold'em equity only.
- A 2-2 DS bot anchored by KK retains the pair-on-board strength (set draws, two-pair) AND gains two flush draws. The trade is: give up KK-as-pair in mid (worth ~+0.4 EV) for a 2-2 DS bot anchored by KK (worth ~+1.4 EV vs rainbow). Net ~+1.0 EV swing.
- The "mid is weak" cost is small in TW Poker — a random 2-card mid loses to opponent's mid by maybe 0.5 EV. The gain from a live bot dwarfs the mid loss.

**Why the gates are this narrow:**
- **Premium pair only:** lower pairs (Q and below) generally do better in mid because their kickers play well alongside (e.g., QQ + AKxx in mid + bot has more options).
- **Two pair-suits:** if KK is K♠+K♠... wait that's impossible. The pair always has two different suits given a 52-card deck. Actually, this gate is structurally automatic for KK/AA — but stated for completeness.
- **Rainbow Rule-4-bot:** this is the strongest signal that Rule 4 is leaving value on the table. When Rule-4-bot is single-suited or DS, Rule 4 is correct most of the time.
- **DS feasibility:** without one kicker in each pair-suit, you can't even build the DS bot.

**Why earlier Rule 5 attempts (v21, v22) failed:** Both v21 and v22 (Session 31) attempted Rule 5 by firing on ~5-13% of all hands — much too eager. They lost $473-$680/1000h vs v14. v28's Rule 5 (this rule) fires on 0.27% of all hands — 20-50× tighter. The structural rainbow trigger is far more selective than the rank-based triggers (msphr ≥ 9, etc.) those attempts used. **First successful Rule 5 in the project's history** (Session 34, Decision 063).

**Fires on:** 0.27% of all hands (~1 in 370 you're dealt). Rare, but the per-hand wins are dramatic.

**Empirical lift over v14_combined:** +$1/1000h whole-grid (small but POSITIVE — comparable to v24's marginal ML ship). The whole-grid number is small because the rule fires rarely; the per-hand wins on the firing subset are large ($15K-$18K/1000h on hands like the worked example).

---

## Rule 6 — Pure trips: 2 of the 3 trip cards always go to mid (the third NEVER goes to bot)

**Fires whenever you have trips of any rank (and no second pair, no quads).**
This rule supersedes the prior Rule 4 (extended), which covered only KKK/AAA.
The principle is simple — **mid is paired with the trip rank** — and the only
remaining decision is whether the third trip card goes on **top** or joins **bot**.
The rest of this section is a hand-traceable answer to that question.

### The setup (always)

- **Mid** = 2 of the 3 trip cards (paired mid, ~80% Hold'em equity).
- The third trip card goes to **either top or bot** — never split out separately, never two-trips-on-bot.
- The 4 non-trip cards (your **kickers**) fill the rest.

### Step 1 — Where does the third trip card go (top or bot)?

The decision depends only on your **trip rank** and what kickers are in your hand:

| Trip rank | Where the third trip card goes | Why |
|---|---|---|
| **Trip A (AAA)** | **Always TOP.** | Nothing beats Ace on top. |
| **Trip K (KKK)** | **TOP**, unless you also hold an **A** in kickers (then put the A on top, third K to bot). | An Ace on top still beats your K. |
| **Trip Q (QQQ)** | **TOP**, unless you hold a **J, K, or A** in kickers (then put the highest such card on top, third Q to bot). | Even a J on top beats Q on top *more often than you'd think* — see "Why" below. |
| **Trip J or lower** | **Always BOT.** Highest non-trip card goes on top. | At J or below, every kicker layout makes "third trip in bot + best singleton on top" the better setting. |

When the third trip card goes to **bot**, the bot becomes 1 trip + 3 lowest non-trip cards, and the next two steps decide which trip that is.

### Step 2 — Which of the 3 trip cards joins bot? (Suit-matching, no math)

Used only when Step 1 sent the third trip to bot — i.e., trip rank ≤ J, **or** trip Q with J/K/A kicker, **or** trip K with A kicker.

You're trying to make the bot **double-suited (2+2)** — two cards each of two different suits — because DS bots dominate the Omaha bot equity. Look at the 3 kickers heading to the bot.

**Look at your 3 kickers' suits and identify the pattern:**

- **Two kickers share a suit, one is different** ("two-and-one") — the most common case.
- **All three kickers different suits** ("rainbow kickers").
- **All three kickers same suit** (rare).

**Then pick the trip card whose suit gives the best bot in this priority:**

| Bot shape | How to spot it | Quality |
|---|---|---|
| **2+2 (DS)** ✓ best | Trip suit matches the **lone (singleton)** kicker — making 2 of *that* suit and 2 of the kicker-pair suit | Two flush draws, dominant Omaha shape |
| **2+1+1 (SS)** OK | Trip suit matches a kicker that wasn't already paired in kickers (i.e., a fresh second of an existing kicker suit, or fills out a rainbow) | One flush draw |
| **3+1** ✗ avoid | Trip suit matches the **kicker pair suit** (now you have 3 of one suit on bot) | Third suited card is dead — only 2 from hand can be used |
| **4-flush** ✗ never | All 4 bot cards same suit | Worst Omaha shape |

**Rule of thumb**: **never let the third trip suit equal the kicker pair suit** (that's the 3+1 trap). When in doubt, pick the trip whose suit appears **least often** in the kickers.

### Worked examples

**Example 1 — Trip A (always top):** `2♦ 4♣ 7♥ J♠ A♣ A♦ A♥`
- Trip A → third A on top, no exceptions.
- Top = A♣ (any A — they're suit-symmetric on top). Mid = A♦ + A♥. Bot = J♠ + 7♥ + 4♣ + 2♦.
- **Play**: top=A♣, mid=A♦+A♥, bot=J♠+7♥+4♣+2♦.

**Example 2 — Trip K, no Ace:** `4♣ 7♦ 9♥ Q♠ K♣ K♦ K♠`
- Trip K, no A in kickers → third K on top.
- Top = K♣. Mid = K♦ + K♠. Bot = Q♠ + 9♥ + 7♦ + 4♣.
- **Play**: top=K♣, mid=K♦+K♠, bot=Q♠+9♥+7♦+4♣.

**Example 3 — Trip K, with Ace (third K to bot):** `4♣ 7♦ 9♥ A♥ K♣ K♦ K♠`
- Trip K, A in kickers → A goes on top, third K joins bot.
- Top = A♥. Bot kickers = 4♣, 7♦, 9♥ — rainbow (3 different suits).
- Step 2: rainbow kickers + trip K's suits {♣, ♦, ♠}. Match to a kicker suit: K♣ → 2♣ in bot; K♦ → 2♦ in bot. K♠ → still rainbow (♠ not in kickers). Both K♣ and K♦ give 2+1+1 (SS). K♠ gives rainbow.
- Pick K♣ or K♦ (either is fine — same SS shape). Mid = the other 2 K's plus K♠ on... wait, mid is 2 K's. Pick K♣ to bot, mid = K♦ + K♠.
- **Play**: top=A♥, mid=K♦+K♠, bot=K♣+9♥+7♦+4♣.

**Example 4 — Trip Q, with J kicker (third Q to bot, sharper than v14/v33):** `2♥ 4♣ 7♦ J♠ Q♣ Q♦ Q♥`
- Trip Q, J in kickers → J goes on top, third Q joins bot. (This is the case where v33's old "trip > max kicker" boundary picked C and put a Q on top — the sharper rule says J on top.)
- Top = J♠. Bot kickers = 2♥, 4♣, 7♦ — rainbow. Trip suits = {♣, ♦, ♥}, all match a kicker → any pick gives 2+1+1.
- Pick Q♣ for bot (matches 4♣). Mid = Q♦ + Q♥.
- **Play**: top=J♠, mid=Q♦+Q♥, bot=Q♣+7♦+4♣+2♥.

**Example 5 — Trip J, low kickers (always third J to bot):** `2♣ 4♣ 6♥ 9♦ J♣ J♦ J♠`
- Trip J → third J always on bot (trip rank ≤ J).
- Top = 9♦ (highest kicker). Bot kickers = 2♣, 4♣, 6♥. Suits: ♣, ♣, ♥ → "two-and-one" (♣♣♥).
- Step 2: kicker pair = ♣, kicker singleton = ♥. Trip suits = {♣, ♦, ♠}.
  - J♣ → bot 3♣+1♥ = **3+1 ✗ avoid** (third club is dead).
  - J♦ → bot 2♣+1♥+1♦ = 2+1+1 (SS).
  - J♠ → bot 2♣+1♥+1♠ = 2+1+1 (SS).
  - (No J♥, so the perfect 2+2 is unavailable.)
- Pick J♦ or J♠ (either SS — equivalent). Mid = J♣ + the other.
- **Play**: top=9♦, mid=J♣+J♠, bot=J♦+6♥+4♣+2♣.

**Example 6 — Trip 7, finds a 2+2:** `3♥ 5♥ 8♣ Q♣ 7♣ 7♦ 7♠`
- Trip 7 → third 7 always to bot. Top = Q♣ (highest non-trip). Bot kickers = 3♥, 5♥, 8♣.
- Suits: ♥♥♣ → "two-and-one" (pair=♥, singleton=♣). Trip suits = {♣, ♦, ♠}.
  - 7♣ → bot 1♣+1♣+2♥ = 2+2 (DS) ✓ — wait, that's 2♣ (3♥+5♥+8♣+7♣) = 2♥+2♣. Yes 2+2.
  - 7♦ → bot 2♥+1♣+1♦ = 2+1+1 (SS).
  - 7♠ → bot 2♥+1♣+1♠ = 2+1+1 (SS).
- Pick 7♣ — **2+2 double-suited bot**. Mid = 7♦ + 7♠.
- **Play**: top=Q♣, mid=7♦+7♠, bot=7♣+8♣+5♥+3♥.

### Trips ≤ J reference table — one worked example per rank

Trip A, K, Q are covered above (Examples 1–4). Trip J and Trip 7 are also covered (Examples 5–6). The 8 examples below fill in **every remaining rank from T down to 2**. The procedure is mechanical at every rank — only the suit layout changes — but seeing one hand at each rank makes it easier to recognize at the table.

Three things to notice as you scan these:

1. **The procedure is the same every time.** Step 1 always sends the third trip to bot (trip ≤ J). Step 2 always uses the suit-matching priority to pick which of the 3 trips joins bot. There is no "different rule for low trips."
2. **Connectivity (4-card runs, wheel structures) is incidental, not a tier.** Trip 6 with kickers 4-5-7 makes a 4-card run on bot (4-5-6-7); Trip 5 with kickers 2-3-4 makes the wheel-eligible bot 2-3-4-5. In both cases, **every** trip-to-bot pick gives the same run length, so the run is not a tiebreaker. Step 2 still picks by suit. (Confirmed by Session 40 connectivity probe — 0/196 hands where rainbow-run-4 is available does the oracle pick it; an alt tier "DS > rainbow run≥3 > SS" regresses $11/1000h whole-grid.)
3. **Hand strength drops fast as trip rank drops.** Trip 5 with low kickers is structurally weak no matter how you set it. The rule still tells you the right answer; it just can't make a low-trip hand into a strong hand.

In the suit notation below, "trip suits {♣, ♦, ♥}" means your three trip cards are clubs, diamonds, hearts (no spade). Bot-shape codes: **DS** = 2+2 double-suited, **SS** = 2+1+1 single-suited, **3+1** = three-of-a-suit (avoid), **rainbow** = 1+1+1+1.

**Example 7 — Trip T:** `7♦ 8♣ 9♥ T♣ T♦ T♥ J♠`
- Trip T → third T to bot (trip ≤ J). Top = J♠. Bot kickers below: 9♥, 8♣, 7♦ — suits ♥♣♦, **rainbow**.
- Trip suits {♣, ♦, ♥} (no ♠ in trip).
- T♣ → bot ♣♥♣♦ = SS (♣♣). T♦ → SS (♦♦). T♥ → SS (♥♥). All three give SS — kickers are rainbow, so any trip suit pairs with a kicker suit. **No DS available.**
- Pick any (they're equivalent). **Play**: top=J♠, mid=T♦+T♥, bot=T♣+9♥+8♣+7♦.

**Example 8 — Trip 9, find a DS:** `2♣ 5♥ 8♥ 9♣ 9♦ 9♥ Q♠`
- Trip 9 → third 9 to bot. Top = Q♠. Bot kickers: 8♥, 5♥, 2♣ — suits ♥♥♣, **two-and-one** (pair=♥, singleton=♣).
- Trip suits {♣, ♦, ♥}.
  - 9♣ → bot ♣♥♥♣ = **DS (2♣+2♥) ✓**
  - 9♦ → bot ♦♥♥♣ = SS (♥♥)
  - 9♥ → bot ♥♥♥♣ = **3+1 ✗ avoid** (third heart is dead)
- Pick **9♣**. **Play**: top=Q♠, mid=9♦+9♥, bot=9♣+8♥+5♥+2♣.

**Example 9 — Trip 8, 3+1 trap visible:** `2♥ 5♣ 7♣ 8♣ 8♦ 8♠ Q♣` (note: trip suits are ♣♦♠, no ♥)
- Trip 8 → third 8 to bot. Top = Q♣. Bot kickers: 7♣, 5♣, 2♥ — suits ♣♣♥, **two-and-one** (pair=♣, singleton=♥).
- Trip suits {♣, ♦, ♠} (no ♥ available, so the 2+2 DS that would need a ♥-trip is impossible).
  - 8♣ → bot ♣♣♣♥ = **3+1 ✗ avoid**
  - 8♦ → bot ♦♣♣♥ = SS (♣♣) ✓
  - 8♠ → bot ♠♣♣♥ = SS (♣♣) ✓
- Both 8♦ and 8♠ give SS — equivalent, pick either. The takeaway: when no 2+2 is available because your trip is missing the singleton's suit, you settle for SS but **never let your trip be the kicker-pair suit** (8♣ here). **Play**: top=Q♣, mid=8♣+8♠, bot=8♦+7♣+5♣+2♥.

**Example 10 — Trip 6, 4-run bot:** `4♦ 5♣ 6♣ 6♦ 6♥ 7♥ T♠`
- Trip 6 → third 6 to bot. Top = T♠. Bot kickers: 7♥, 5♣, 4♦ — suits ♥♣♦, **rainbow**.
- Bot ranks once a trip joins: {6, 7, 5, 4} — that's **4-5-6-7, a 4-card run**. Looks juicy, but the run is the same regardless of which 6 you pick.
- Trip suits {♣, ♦, ♥}. With rainbow kickers, every trip suit gives SS (no DS available).
  - 6♣ → SS (♣♣). 6♦ → SS (♦♦). 6♥ → SS (♥♥).
- Pick any. **Play**: top=T♠, mid=6♦+6♥, bot=6♣+7♥+5♣+4♦. Bot has a 4-card straight draw; that's just a bonus.

**Example 11 — Trip 5, wheel-eligible bot:** `2♦ 3♣ 4♥ 5♣ 5♦ 5♥ K♠`
- Trip 5 → third 5 to bot. Top = K♠. Bot kickers: 4♥, 3♣, 2♦ — suits ♥♣♦, **rainbow**.
- Bot ranks once a trip joins: {5, 4, 3, 2} — **wheel-eligible** (with an Ace on the board, 2-3-4-5-A is a straight, the wheel). Same wheel structure regardless of which 5 you pick.
- Trip suits {♣, ♦, ♥}. Rainbow kickers + any trip suit = SS.
  - 5♣, 5♦, 5♥ all give SS (each pairs with a kicker suit).
- Pick any. **Play**: top=K♠, mid=5♦+5♥, bot=5♣+4♥+3♣+2♦. The wheel structure adds a real chunk of bot equity, but it's structural — Step 2 didn't have to "find" it.

**Example 12 — Trip 4, weak hand, simple SS:** `2♦ 4♣ 4♦ 4♥ 7♥ 9♣ A♠`
- Trip 4 → third 4 to bot. Top = A♠ (highest non-trip — your Ace is your one strong card). Bot kickers: 9♣, 7♥, 2♦ — suits ♣♥♦, **rainbow**.
- Trip suits {♣, ♦, ♥}. Rainbow + any → SS.
- Pick any. **Play**: top=A♠, mid=4♦+4♥, bot=4♣+9♣+7♥+2♦. Hand is weak overall — Ace scoops top, but mid (a pair of 4s) and bot (low cards) lose to most opponent settings. The rule is doing its job; the cards aren't.

**Example 13 — Trip 3:** `3♣ 3♦ 3♥ 5♦ 8♥ T♣ K♠`
- Trip 3 → third 3 to bot. Top = K♠. Bot kickers: T♣, 8♥, 5♦ — suits ♣♥♦, **rainbow**.
- Trip suits {♣, ♦, ♥}. Rainbow + any → SS.
- Pick any. **Play**: top=K♠, mid=3♦+3♥, bot=3♣+T♣+8♥+5♦.

**Example 14 — Trip 2, lowest possible:** `2♣ 2♦ 2♥ 4♦ 7♥ J♣ A♠`
- Trip 2 → third 2 to bot. Top = A♠. Bot kickers: J♣, 7♥, 4♦ — suits ♣♥♦, **rainbow**.
- Trip suits {♣, ♦, ♥}. Rainbow + any → SS.
- Pick any. **Play**: top=A♠, mid=2♦+2♥, bot=2♣+J♣+7♥+4♦. Trip 2s are about as weak as trips get; the Ace on top is the only material part of the hand.

### Why it works

- **Mid is paired** (2 trips together) — Hold'em equity ~80% on unpaired boards (same as KK/AA stay-in-mid logic from Rule 4).
- **Never put the third trip on bot AS THE ONLY trip there** — that would split the paired mid. Either both extra trips stay in mid (third on top) or one trip joins bot (paired mid is preserved).
- **The boundary in Step 1** comes from the oracle: the per-cell map of best-A vs best-C across (trip rank × max kicker rank) shows that A wins on average for **trip ≤ J in every cell**, **trip Q whenever J/K/A is present**, **trip K only when an Ace is present**, and **trip A never**. Earlier versions of this guide used the simpler boundary "trip > max kicker → top is the trip card" (v33), which is right at the high end (Trip A, K-without-A, Q-with-T-or-lower) but **picks the wrong top in three places**: Trip Q + J kicker, Trip J + low kickers, and Trip T + low kickers. Sharpening these is +$8/1000h whole-grid at the human ceiling (oracle-bound).
- **Connectivity is not a Step 2 tier (Session 40 confirmation).** Bot 4-card runs and wheel-eligible bots happen incidentally on low-trip + low-kicker hands, but every trip-to-bot pick on the same hand gives the same run length, so connectivity is invariant across the 3 candidates. The Session 40 probe (`probe_low_trips_connectivity.py`) tested the alternative "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1" tier and found it regresses $11/1000h whole-grid versus the existing DS > SS > rainbow > 3+1 priority. The oracle picks rainbow 0% of the time when SS or DS is available; rainbow-run-4 picks are oracle-preferred 0/196 (0%) of the hands where they exist.

### Probe history

- **v14 picks "mid is paired" on only 94.3% of pure trips.** The 5.4% routing the 3rd trip to bot **alone** loses $197/1000h whole-grid vs the always-paired-mid baseline (Session 37 verify_rule6_v14_trips probe).
- **v33 (Session 37 ship)** locked in "third trip never bot-only" + "trip > max kicker → top is trip rank, else top is max kicker". That ships **+$112/1000h whole-grid full grid / +$143/1000h prefix** vs v28 — the largest single rule ship in project history.
- **v33 boundary's heuristic ceiling**: 56% of the $197 always-A∪C oracle ceiling. The remaining 44% gap is explained by an under-optimized A-variant heuristic for "which trip joins bot" (Session 38 sweep, `probe_v34_sweep.py`).
- **Session 38's per-cell oracle probe** (`probe_rule6_c_variant.py`) showed v33's boundary is wrong on 28.8% of "v33 picks C" cells — projected oracle ceiling of $+12.89/1000h whole-grid by flipping those cells to A.
- **v35 boundary (this section, Session 39)** captures **+$8.12/1000h whole-grid at the human ceiling** (oracle-bound) on the same 30K probe, while sacrificing the noisy/marginal trip-J + low-kicker cells the user simplified out for memorability. **Decision 071** ships v35 as the strategy of record for human play; the production heuristic bot keeps v33 because heuristic-A still cannot cash the sharper boundary (-$4/1000h grid at the bot level — the bot-DS optimizer is the rate-limiting step).

**Fires on:** 5.46% of all hands (~1 in 18 you're dealt). Pure trips covers all 13 trip ranks; the headline gain over v14 is concentrated on low trips (2-9) where the third-trip-to-bot bleed is largest.

**Subsumes Rule 4 (extended):** the prior KKK/AAA rule was a special case. KKK with no Ace → third K on top (matches v35). KKK with Ace → A on top (matches v35). AAA → always third A on top (matches v35). Rule 6 generalizes cleanly to all 13 trip ranks.

---

## Default (no rule fires)

For every hand not covered above — single pair outside the rule's gates, no-pair hands, three pairs, quads — **play it the obvious way:**

- **Top** = your highest singleton card (especially an Ace if you have one)
- **Mid** = your strongest 2-card Hold'em combination from what's left (pair > broadway > suited connector)
- **Bot** = whatever's left, ideally with at least 2 of one suit for some Omaha equity

This is the v8_hybrid play. It's not optimal on every hand but it's adequate. The v32 ML champion captures meaningful additional EV here (especially on high_only, pair, two_pair, trips_pair, and composite hands), but no clean human-memorizable rule has been extracted yet. Two boundary probes (Session 34) confirmed Rule 4 holds for KK, AA, KKK, and AAA but identified an exception (~24-28% of DS-bot-eligible hands prefer split-bot) that has consistently resisted clean rule extraction. Session 37's Rule 6 closed the trips category gap with the largest single rule ship in project history; the next-largest opportunity in the human chain is composite (~$98/1000h whole-grid) but composite is much rarer and harder to rule-encode.

---

## The common thread

The single insight running through all 4 rules:

> **The bottom tier is the most valuable, and double-suited (2+2) bots win against the realistic mixture by $5K-$15K per 1,000 hands.** Whenever a pair (or trip) can serve as a suit anchor for the bot — meaning the pair has two different suits, and your kickers can fill the DS structure — putting the pair in the bot is usually correct. The exceptions are mid pairs (6-9), which are strong enough in mid that the move isn't worth it, and KK/AA, which are valuable enough in mid that the trade flips back.

The mid tier is forgiving (Hold'em rules, can use 0/1/2 hole cards), so giving up a "pair in mid" for kickers in mid loses less than you'd think. The bot is unforgiving (Omaha 2+3 is rigid), so getting the bot to DS shape is high-value.

---

## One-paragraph cheat sheet

> Don't break pairs. With one pair + an Ace + balanced suits, put the
> Ace on top and the pair in a double-suited bot — except for pairs 6-9
> which stay in mid AND for KK / AA which always stay in mid. With two
> pairs, never split either; either both go to bot, or higher to mid +
> lower to bot, whichever makes the bot double-suited. With trips +
> pair, split the trips 2-and-1, keep the pair together, build a
> double-suited bot. For any hand without a pair, play it the obvious
> way — high card on top, decent cards in mid.
