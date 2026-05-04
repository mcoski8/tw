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
> Last updated: 2026-05-04 (Session 30 — v20 ships).

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
| **v20** | **S30** | **30** | **5** | **43 gated** | **307,939** | **$1,982** | **$1,082** | **CURRENT CHAMPION** |

**Per-category breakdown** (full grid, N=200): how each category's
regret has dropped across the three flagship versions:

| Category | v14 | v16 | v18e | v20 | Δ v20 vs v14 |
|---|---:|---:|---:|---:|---:|
| high_only | $4,082 | $3,785 | $3,307 | $2,894 | −$1,188 |
| pair | $2,011 | $2,127 | $1,873 | $1,873 | −$138 |
| two_pair | $3,371 | $2,005 | $1,458 | $1,458 | −$1,913 |
| trips | $4,054 | $2,347 | $1,997 | $1,997 | −$2,057 |
| trips_pair | $5,417 | $2,438 | $1,608 | $1,608 | −$3,809 |
| three_pair | $4,529 | $1,975 | $1,653 | $1,653 | −$2,876 |
| quads | $9,670 | $2,233 | $724 | $724 | −$8,946 |
| composite | $10,883 | $5,260 | $2,100 | $2,100 | −$8,783 |

The v20 jump is concentrated in high_only (−$413 vs v18e); other
categories inherit v18e's numbers because gating zeroes the new
features for them.

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

| Hand type | Frequency | v14 $/1000h | v20 $/1000h | Status |
|---|---:|---:|---:|---|
| high_only | 20.4% | $4,082 | $2,894 | Largest absolute residual; gated suited features helped (Session 30) but a candidate **Rule 5** (suited middle for high_only) hasn't been codified yet. |
| trips (no pair) | 5.5% | $4,054 | $1,997 | No human rule yet. Multi-archetype. |
| three_pair | 1.9% | $4,529 | $1,653 | No human rule yet. |
| quads | 0.2% | $9,670 | $724 | v20 captures heavily but no human rule. |
| composite | 0.2% | $10,883 | $2,100 | Biggest per-hand bleed in v20. Candidate for a `composite_aug_gated` family in Session 31. |

**Candidate Rule 5 (not yet codified):** for no-pair high_only hands,
when there exists a same-suit pair of cards both ranked T+, prefer
routing them together to mid. The v20 DT has clearly learned this
pattern (the gated `max_suited_pair_high_rank_g` feature is in v20's
top-15 importance) but extracting it as a plain-English rule requires
Session 31's distillation of the v20 tree.

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
- Combined chain → `analysis/scripts/strategy_v14_combined.py`

**ML champion + baselines (newest first):**
- v20 (current) → `analysis/scripts/strategy_v20_dt.py` + `data/v20_dt_model.npz` (308K leaves)
- v18e → `data/v18e_dt_model.npz` (274K leaves)
- v18d → `data/v18d_dt_model.npz` (193K leaves)
- v18c → `analysis/scripts/strategy_v18c_dt.py` + `data/v18c_dt_model.npz` (125K leaves)
- v18 → `analysis/scripts/strategy_v18_dt.py` + `data/v18_dt_model.npz` (61K leaves)
- v16 → `analysis/scripts/strategy_v16_dt.py` + `data/v16_dt_model.npz` (29K leaves)

**Trainers:**
- v18 capacity trainer (37 features) → `analysis/scripts/train_v18_dt.py`
- v19_gated trainer (43 features incl. gated suited) → `analysis/scripts/train_v19_gated_dt.py`
- v16 trainer (legacy, recomputes features) → `analysis/scripts/train_v16_regression.py`

**Aug feature compute:**
- Gated suited (high_only) → `analysis/scripts/suited_aug_features_gated.py`
- Gated suited persist → `analysis/scripts/persist_suited_aug_gated.py`

**Analysis:**
- v16 distillation → `analysis/scripts/distill_v16_dt.py`
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

> Everything below this line is the active rule set as of Session 30.
> If you only read one section, read this one.
>
> **Human-memorizable strategy of record: v14_combined + Rule 4.**
> Four numbered rules plus a default play. Edge over v8_hybrid baseline:
> **+$1,014/1000h** at $10/EV-pt (measured on the N=1000 prefix).
>
> **ML champion (not human-memorizable): v20_dt** — 307,939-leaf
> DecisionTreeRegressor (depth=30, min_samples_leaf=5), 43 features
> including 6 gated suited-broadway features for high_only. Beats v14
> by **+$1,051/1000h** on the full grid and **+$955/1000h** on the
> prefix N=1000. Lives at `analysis/scripts/strategy_v20_dt.py` +
> `data/v20_dt_model.npz`.

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
| Trips (no pair) | 3 of one rank, no other pair | (no simple rule yet — multi-archetype) |
| Two pairs | 2 of one rank + 2 of another | **Rule 2** |
| One pair (KK or AA) | 2 Kings or 2 Aces | **Rule 4** |
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

## Default (no rule fires)

For every hand not covered above — single pair outside the rule's gates, no-pair hands, plain trips, three pairs, quads — **play it the obvious way:**

- **Top** = your highest singleton card (especially an Ace if you have one)
- **Mid** = your strongest 2-card Hold'em combination from what's left (pair > broadway > suited connector)
- **Bot** = whatever's left, ideally with at least 2 of one suit for some Omaha equity

This is the v8_hybrid play. It's not optimal on every hand but it's adequate. The v20 ML champion captures meaningful additional EV here (especially on high_only hands) but no clean human-memorizable rule has been extracted yet — Session 31 priority.

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
