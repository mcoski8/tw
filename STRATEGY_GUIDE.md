# Taiwanese Poker — Strategy Guide

> The condensed decision tree, in plain English, validated against the
> Full Oracle Grid (6M canonical hands × 105 settings × N=200 MC samples
> vs the realistic 70/25/5 human mixture).
>
> **Human-memorizable strategy of record: v14_combined + Rule 4.**
> Four numbered rules + a default play. Edge over v8_hybrid baseline:
> **+$1,014 per 1,000 hands** at $10/EV-pt (measured on the N=1000
> prefix grid for tightest fidelity).
>
> **ML champion (not human-memorizable): v18_dt** — a 60,651-leaf
> DecisionTreeRegressor (depth=22, min_samples_leaf=50) trained on
> the full 6M-hand grid. Beats v14 by **+$727/1000h** on the full
> grid (N=200) and **+$559/1000h** on the prefix N=1000. Lives at
> `analysis/scripts/strategy_v18_dt.py` + `data/v18_dt_model.npz`.
> Supersedes v16_dt (28,790 leaves) which is kept as a baseline.
>
> Last updated: 2026-05-04 (Session 28 — v18 ships; Rule 4 added; distillation pass).

---

## How to use this guide

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
- **KK / AA**: keep in mid. They're too valuable in Hold'em to relocate (also matches the locked-profile expectation that real opponents follow).
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
  Q drops to bot. v3 / v8 / v16 all agree on this exact setting.

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
- The "highest non-pair to top" subrule is what v3/v8/v16 all converge
  on — when KK + A are present, the A naturally goes to top because
  it's the highest non-K (no special-case needed).
- `has_premium_pair` is the 5th-most-important feature in the v16 DT
  (4.5% of total feature importance) — the model discovered this
  population split on its own.

**Fires on:** 7.17% of all hands (KK 3.58% + AA 3.58%; verified against the canonical hand table).

---

## Default (no rule fires)

For every hand not covered above — single pair outside the rule's gates, no-pair hands, plain trips, three pairs, quads — **play it the obvious way:**

- **Top** = your highest singleton card (especially an Ace if you have one)
- **Mid** = your strongest 2-card Hold'em combination from what's left (pair > broadway > suited connector)
- **Bot** = whatever's left, ideally with at least 2 of one suit for some Omaha equity

This is the v8_hybrid play. It's not optimal on every hand but it's adequate.

---

## The common thread

The single insight running through all 3 rules:

> **The bottom tier is the most valuable, and double-suited (2+2) bots win against the realistic mixture by $5K-$15K per 1,000 hands.** Whenever a pair (or trip) can serve as a suit anchor for the bot — meaning the pair has two different suits, and your kickers can fill the DS structure — putting the pair in the bot is usually correct. The exception is mid pairs (6-9), which are strong enough in mid that the move isn't worth it.

The mid tier is forgiving (Hold'em rules, can use 0/1/2 hole cards), so giving up a "pair in mid" for kickers in mid loses less than you'd think. The bot is unforgiving (Omaha 2+3 is rigid), so getting the bot to DS shape is high-value.

---

## One-paragraph cheat sheet

> Don't break pairs. With one pair + an Ace + balanced suits, put the Ace
> on top and the pair in a double-suited bot — except for pairs 6-9 which
> stay in mid AND for KK / AA which always stay in mid. With two pairs,
> never split either; either both go to bot, or higher to mid + lower to
> bot, whichever makes the bot double-suited. With trips + pair, split
> the trips 2-and-1, keep the pair together, build a double-suited bot.
> For any hand without a pair, play it the obvious way — high card on top,
> decent cards in mid.

---

## What's NOT yet covered (next session targets)

- **High-only hands** (no pair, ~20% of all hands). v14 leaves $4,082/1000h; v18 captures it down to $3,489 (v16 was $3,785). Session 28's deep-dive (`high_only_v16_residual.py`) found the worst residual cluster is `suit_dist=3+2+1+1, n_broadway=3, has_ace_singleton=1`: 88K hands × $0.33 mean regret = 6.4% of all high_only bleed. The DT over-applies "default top=Ace, mid=mid-cards"; the oracle prefers a **suited middle** when one exists (e.g. with `2c 5d 6h 7s Ts Kd Ad`, oracle picks top=A♦, mid=5♦+K♦ (suited), bot=rest). The 37-feature DT can't see this — there's no feature for "two cards of the same suit, both rank ≥ T". Session 29's first task is to add suited-broadway aug features and retrain.
- **Trips without a pair** (~5% of all hands). v14 leaves $4,054/1000h; v18 captures it down to $2,241.
- **Three pairs / quads / composite** — v18 captures these heavily (quads $9,670 v14 → $1,474 v18). Composite remains the worst per-hand category at $4,623/1000h v18.
- **v17 hybrid attempt (rules-then-DT) was archived** — Session 28's grade showed v9.2/v10/v12 are inferior to v16 in their own categories. The hand-coded rules were optimized against the OLD 4-profile mixture; the DT is trained against the realistic mixture and supersedes them.

---

## Distillation insights (Session 28 — from v16 DT, full grid)

These are observations from walking the 28,790-leaf v16 tree against the
6M-hand oracle grid. They explain WHY the DT works the way it does, even
when no single split translates cleanly to a new rule.

### Feature importance (top 8, by population-weighted MSE reduction)

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
n_routings_yielding_ds_bot_*, etc.) collectively contribute **<0.4%** of
total importance. The DT solves the problem almost entirely with raw
body-strength features (broadway count, low count, third rank).

### Key insight: `n_broadway` is the master signal

The root split is `n_broadway ≤ 2.5` and that single split alone
accounts for $4M of the total $11M MSE reduction in the tree. Every
strategy decision flows downstream of "how many T-J-Q-K-A cards do I
have?"

| n_broadway | What the DT does (root branch) |
|---:|---|
| 0–2 | Bias toward placing the few high cards in bot or mid; default plays well |
| 3 | Mixed — splits further on premium-pair / ace-singleton |
| 4–7 | Premium pair → mid (Rule 4); else default |

The strategy guide already implicitly captures this through "play it the
obvious way" for low-broadway hands and the special rules for paired
hands. The DT confirms there's no hidden transformation needed for
broadway-heavy hands beyond the existing rules.

### What the DT does NOT see

The DT keys on rank-and-suit-count features but does NOT know about:
- **Suited pairs of broadway cards** (e.g. K♦Q♦ together) — there is no
  feature for "do I have a same-suit pair of cards both ≥ T".
- **Connected high cards** (e.g. J-Q-K) — captured only via
  `connectivity` (longest run) which lumps low and high runs together.

These are the most likely sources of the remaining gap to oracle. A v18
training run that adds `n_suited_pairs_in_top5` and
`max_pair_rank_in_suited` aug features could close the high_only
residual.

### What survives from earlier rules

The v9.2 / v10 / v12 hand-coded rules predate the DT. The DT's existence
doesn't invalidate them — they're how a human applies the same logic.
The DT's `pair_high_rank` and `has_premium_pair` splits at the top of
its tree mirror Rule 1's gating on pair rank. The DT's category-specific
behavior on two_pair and trips_pair mirrors Rules 2 and 3. The wins
come from hundreds of small per-cell adjustments the DT makes that no
human-readable rule could match.

---

---

## Where each rule lives in code

- Rule 1 → `analysis/scripts/strategy_v9_2_pair_to_bot_ds.py`
- Rule 2 → `analysis/scripts/strategy_v10_two_pair_no_split.py`
- Rule 3 → `analysis/scripts/strategy_v12_trips_pair.py`
- Rule 4 → encoded implicitly in `analysis/scripts/strategy_v8_hybrid.py` (via
  `encode_rules.strategy_v3`'s pair-to-mid default). v3 / v8 / v16 all
  agree on the canonical KK and AA play; Rule 4 is documentation, not a
  separate code path.
- Combined human-memorizable chain → `analysis/scripts/strategy_v14_combined.py`
- ML champion (Session 28) → `analysis/scripts/strategy_v18_dt.py` + `data/v18_dt_model.npz` (60,651 leaves, depth=22)
- v16 baseline (Session 27) → `analysis/scripts/strategy_v16_dt.py` + `data/v16_dt_model.npz` (28,790 leaves, depth=18)
- v18 trainer (cached parquets, ~5min cycle) → `analysis/scripts/train_v18_dt.py`
- v16 trainer (legacy, recomputes features) → `analysis/scripts/train_v16_regression.py`
- v16 distillation analysis → `analysis/scripts/distill_v16_dt.py` + `analysis/scripts/high_only_v16_residual.py` (Session 28)
- Grading harness → `analysis/src/tw_analysis/grade_strategy.py`
- Full ground-truth grid → `data/oracle_grid_full_realistic_n200.bin` (gitignored, 2.55 GB)

To validate any new rule against the grid in ~4 minutes:
```python
from tw_analysis.canonical import read_canonical_hands
from tw_analysis.grade_strategy import grade_strategy
from tw_analysis.oracle_grid import read_oracle_grid

grid = read_oracle_grid("data/oracle_grid_full_realistic_n200.bin", mode="memmap")
ch = read_canonical_hands("data/canonical_hands.bin", mode="memmap")
result = grade_strategy(my_strategy_fn, grid, ch, label="my_strategy")
print(result.summary())
```
