# Taiwanese Poker — Strategy Guide

> The condensed decision tree, in plain English, validated against the
> Full Oracle Grid (6M canonical hands × 105 settings × N=200 MC samples
> vs the realistic 70/25/5 human mixture).
>
> Strategy of record: **v14_combined**.
> Edge over v8_hybrid baseline: **+$1,014 per 1,000 hands** at $10/EV-pt
> (measured on the N=1000 prefix grid for tightest fidelity).
> Last updated: 2026-05-03 (Session 26).

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
| One pair | 2 of one rank, no other multiples | **Rule 1** (gates apply) |
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
> stay in mid. With two pairs, never split either; either both go to bot,
> or higher to mid + lower to bot, whichever makes the bot double-suited.
> With trips + pair, split the trips 2-and-1, keep the pair together,
> build a double-suited bot. For any hand without a pair, play it the
> obvious way — high card on top, decent cards in mid.

---

## What's NOT yet covered (next session targets)

- **High-only hands** (no pair, ~20% of all hands, $4,082/1000h on the table). Tried 3 simple rules; all regressed. The oracle plays these too variably for a single hand-coded rule. Decision-tree-trained-on-the-grid (planned Session 27 v16) is the likely fix.
- **Trips without a pair** (~5% of all hands, $4,054/1000h on the table). Same issue.
- **Three pairs / quads / composite** — small share, not yet attacked.

Together these account for ~$1,055 of v14's $3,033/1000h gap to perfect play. Cracking them via DT regression is the single biggest remaining opportunity.

---

## Where each rule lives in code

- Rule 1 → `analysis/scripts/strategy_v9_2_pair_to_bot_ds.py`
- Rule 2 → `analysis/scripts/strategy_v10_two_pair_no_split.py`
- Rule 3 → `analysis/scripts/strategy_v12_trips_pair.py`
- Combined chain → `analysis/scripts/strategy_v14_combined.py`
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
