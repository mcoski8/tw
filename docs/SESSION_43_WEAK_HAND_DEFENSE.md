# Session 43+ Investigation: Weak-Hand Defensive Play

> **Owner:** user-driven priority (raised end of Session 42 overnight)
> **Status:** scoped, not started
> **Scope size:** large — touches ~14% of all hands, the second-biggest unmined territory after the high-card rules

## Why this matters

So far the rule chain optimizes for hands that have *something to win with* — a pair high enough to anchor a mid, suit pattern good enough to build DS bot, etc. **The "weak hand" territory has been almost entirely ignored.** These are the hands where the question isn't "how do I scoop?" but "how do I lose the LEAST?"

A scoop gives the opponent +20 points; a 12-point loss is the next-worst outcome. The difference between "lose 12" and "lose 20" on a single hand is massive — and weak hands are exactly where that difference hinges on top-tier choice and suit-coordination.

**14.13% of canonical hands are J-high or lower.** That's nearly 1 in 7 hands dealt. We have no defensive rules for any of them.

## The territory by the numbers

(Computed end of Session 42 overnight, from the full 6,009,159-hand canonical population.)

### Total defensive territory (max card = J or lower)

| Threshold (max card ≤) | Count | % of all hands |
|---|---:|---:|
| **J (≤11) — primary defensive zone** | **849,270** | **14.13%** |
| T (≤10) | 376,398 | 6.26% |
| 9 (≤9) | 151,936 | 2.53% |
| 8 (≤8) | 53,334 | 0.89% |
| 7 (≤7) | 15,402 | 0.26% |
| 6 (≤6) | 3,295 | 0.05% |
| 5 (≤5) — wheel territory | 400 | 0.01% |

### Defensive zone broken out by category (max card ≤ J)

| Category | Hands | % of grid | % of defensive zone |
|---|---:|---:|---:|
| pair | 342,720 | 5.70% | **40.4%** ← biggest sub-territory |
| two_pair | 262,080 | 4.36% | **30.9%** |
| high_only (no pair) | 85,800 | 1.43% | 10.1% |
| trips | 64,260 | 1.07% | 7.6% |
| trips_pair | 50,400 | 0.84% | 5.9% |
| three_pair | 33,600 | 0.56% | 4.0% |
| composite (rare) | 6,210 | 0.10% | 0.7% |
| quads | 4,200 | 0.07% | 0.5% |

**Critical overlap:** the J-high two_pair zone (262K hands, 4.36% of grid) is the *same population* where Session 42's two_pair Rule 8 candidate showed +$197 full / -$512 prefix — and where the prefix grade tanked. **v33's adaptive splitting on those hands may have been correct DEFENSIVE play that I dismissed as "ML-only".** This is worth re-examining through a defensive lens.

### J-high pair sub-stratification (where's the pair?)

J-high pair hands skew LOW — when the highest card is J, the pair tends to be small.

| Pair rank | Share of J-high-pair |
|---|---:|
| 2 | 34.27% |
| 3 | 19.04% |
| 4 | 9.52% |
| 5 | 5.52% |
| 6 | 5.52% |
| 7 | 5.52% |
| 8 | 5.16% |
| 9 | 5.16% |
| T | 5.15% |
| J | 5.14% |

The bottom of the table is the *worst-of-the-worst*: pair=2 with junk J-high body. The top of the table (JJ-with-T-9-8-7-x body) is much better — JJ in mid is still a meaningful Hold'em hand.

### J-high no-pair (no other multiples) suit patterns

| Suit pattern | Share | Bot DS achievable? |
|---|---:|---|
| 3+2+1+1 (rainbow-ish) | 28.6% | maybe — depends on rank distribution |
| 4+2+1 | 15.1% | yes — 4-flush available for bot |
| 3+2+2 (DS-like) | 14.8% | yes — natural DS |
| 2+2+2+1 | 14.0% | yes — natural DS |
| 3+3+1 | 10.0% | no — 3-flush in single suit wastes |
| 4+3 | 5.2% | no — 4-flush + 3-flush both waste |
| 4+1+1+1 | 4.9% | yes if 4-flush split correctly |
| 5+2 | 3.1% | no — 5-flush is mostly wasted |
| 5+1+1 | 3.1% | no |
| 6+1 | 1.1% | no — extreme flush waste |
| 7 (one-suit hand!) | 0.2% | totally wasted suit |

## User questions to investigate (Session 43 priority)

These are the user's specific framings — drill scripts should test each.

### Q1: Single Ace with low body — always Ace-on-top?

Example: `A♠ 9♥ 7♣ 5♦ 4♣ 3♠ 2♦` (A-high, 7 distinct ranks, rainbow-ish).

The Ace is the only "winner" we have. Conventional wisdom: A on top, scrape together a mid + bot. The mid will be a 9-7 or 9-5 or similar (loses to most pairs), and the bot will be "5+4+3+2 + something" with nominal flush draw if any.

**Question:** is there ever a case where keeping the Ace down is right? Maybe when the Ace's suit is the only one that could anchor a 4-flush bot?

### Q2: K-high or Q-high with a single body — break the broadway for suit?

Example: `K♣ 8♦ 7♣ 5♣ 4♥ 3♣ 2♦` (K-high, K matches a 4-flush in clubs).

Two structural choices:
- **K-on-top, mid = some 8-7 / 8-5 combo, bot = 4-flush in clubs minus K** = bot has K's suit but no K, weaker bot. Top is K (might chop with K-high-top opponent, or lose to A-high).
- **K-in-bot, top = the next-highest singleton (8?), mid = 7+5 or similar, bot = K♣+7♣+5♣+3♣ = 4 clubs!** Bot is now a flush in Omaha (use 2 from hand + 3 from board, board has 1 club → flush of K-high). Top is dramatically weaker (8 on top loses everything).

Likely the right answer depends on whether the K's suit-flush is achievable AND whether the loss-on-top is recoverable. Drill needed.

### Q3: J-high (or lower) + 1 pair — defensive framework?

Example A: `J♥ 9♠ 7♣ 5♦ 5♣ 3♥ 2♠` (J-high, pair of 5s).
Example B: `9♥ 8♠ 7♣ 6♦ 4♣ 2♥ 2♠` (9-high, pair of 2s).

The pair is too weak to anchor a strong mid; the high card is too weak to scoop. Question: is there a "minimize damage" structural pick?

### Q4: J-high (or lower) + 2 pairs — same territory as the deferred Rule 8

Example: `J♥ 9♠ 7♣ 5♦ 5♣ 3♥ 3♠` (J-high, two pair 55+33).

This is the J-high two_pair territory where Session 42's deferred Rule 8 candidate broke. Re-examining through defensive lens: maybe v33's adaptive splitting IS the defensive answer here. Drill needed.

### Q5: J-high or lower + no pair — does suited-bot save anything?

Example: `J♥ 9♣ 7♣ 5♣ 4♣ 3♥ 2♦` (J-high no-pair, 4-flush in clubs).

7-card no-pair hand. The 4-flush in clubs is the only redeeming feature. Bot construction: do we use J as top + bot = clubs (bot has 4 clubs, can play flush in Omaha if board has any clubs), or different?

## Methodological notes for the drill

1. **Frame as "minimize loss" not "maximize EV"**: weak hands have predominantly negative EV against any random opponent. The goal is the LEAST-NEGATIVE EV, not positive EV. Different objective function — but the oracle grid already encodes this.

2. **Compare to v37/v33's actual picks specifically**: the v33 routing for these hands is almost entirely v8_hybrid → v3 fallback (since none of Rules 1-9 fire on most weak hands). What does v3 actually do? Profile it.

3. **Suit-coordination signal is paramount**: weak hands have NO rank strength, so the only structural lever is suit pattern. Specifically the "is the bot 4-flush, 4-suited (DS), or rainbow" decision dominates.

4. **High-card on top vs in-bot**: this is the single biggest defensive decision and we have no rule for it. The user's instinct (sometimes break the high card for suited bot) needs empirical testing.

5. **Split the investigation by max-card threshold**: the right rule for J-high might be wrong for 8-high. Don't lump.

6. **Watch the both-grid validation gate**: the prefix grid is HEAVILY weighted toward weak hands (recall pair-Rule-1-extension found 0 QQ/JJ in prefix; weak-hand investigations will be the OPPOSITE — high prefix density). A defensive rule that wins on both grids is the target.

## Drill plan (Session 43 starting points)

| Drill | Population | Goal |
|---|---|---|
| `drill_high_card_defense.py` | 85,800 J-high no-pair hands | Q1, Q2, Q5 — when does high-card-to-bot beat high-card-to-top? |
| `drill_low_pair_J_high_defense.py` | 342,720 J-high pair hands | Q3 — defensive structural picks for J-high pair |
| `drill_two_pair_J_high_revisit.py` | 262,080 J-high two_pair hands | Q4 — re-examine the deferred Rule 8 territory through defensive lens |
| `drill_t_high_followup.py` | 376K T-high-or-lower hands | extension if J-high yields rules |

## Key uncertainty going in

Whether "defensive rules" exist as clean structural patterns at all. Three possible outcomes:

1. **Clean rule(s) exist**: e.g., "always put highest card on top UNLESS the highest card is K-or-lower AND the bot can be made 4-flush with that suit" — would ship as Rule 10.
2. **Multi-feature ML territory**: the defensive choice depends on suit×rank×kicker-pattern interactions that don't compress into 1-2 conditions.
3. **v33 already does this implicitly via v3 / v8_hybrid**: the existing "obvious play" might already be near-optimal for weak hands, in which case the residual is small.

The data we'll need to disambiguate is per-cell oracle pick distributions stratified by (max_card, category, suit_pattern, kicker_distribution). Same toolkit as the Session 42 drills.

---

## Stretch Q from user (file under "exotic structural"):

> "What if that K or Q is the one suit that could match up — do you break it in favor of single up top vs suitedness down low?"

This is the central tension of weak-hand defensive play. The drill must directly compare:
- TOP-K config: top=K, mid+bot built from rest, bot's suit pattern depends on what's left.
- BOT-K config: top=highest-other-singleton, mid built from middle ranks, bot=K + 3 same-suited cards (if available) for 4-flush bot.

Per-hand EV comparison + per-cell aggregation will tell us when each config wins. This is **the** key drill of the defensive investigation.
