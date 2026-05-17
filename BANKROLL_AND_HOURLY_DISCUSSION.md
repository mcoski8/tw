# Taiwanese Poker — Bankroll & Hourly EV Discussion

> Documenting the project's economic analysis of the operator's home game.
>
> **Status:** the per-hand $ numbers are LOCKED by Session 98 MC (8 archetypes × 50K hands each).
> The **hands/hour estimate is TENTATIVE** — needs empirical measurement.
>
> **Created:** 2026-05-16 (Session 98 closure) · **Stake:** $10/point · **Format:** 4-handed home game

---

## The starting question

> *"$2-3 per hand × 3 opponents is not bad at all. That's $9-10 per hand, and you can probably net 15 hands per hour so $150/hr which is a really high hourly. The issue you run into is variance of course."*

The first part needed a correction (the $2-3 was already per-field, not per-opp), but the underlying intuition was right: **the per-hour math IS strong, but variance is the binding constraint.**

---

## What we know (locked from MC simulation)

### Per-hand expected value by opponent field

| Field composition | $/hand vs V4 player |
|---|---:|
| 3× Grid Oracle (theoretical ceiling, ~unbeatable composite) | $+0.41 |
| 3× Balanced Pro (mfsuitaware-style strong competent) | $+2.43 |
| 3× Reasonable Naïveté (decent casual home player) | $+3.04 |
| 3× Defensive Inversion Player (knows the defensive flip) | $+2.84 |
| 3× Hold'em-Mid Optimizer (breaks pairs for strong mid) | $+4.74 |
| **Mixed realistic** (1× Standardist + 1× Top-Greedy + 1× Balanced) | **$+17.58** |
| 3× Pair-First Standardist (rigid QQ-AA→mid rule-follower) | $+20.13 |
| 3× Top-Greedy Defender (highest card to top always) | $+33.56 |

### Per-hand variance

- **Stdev: $130 per hand** (≈ 13 points × $10)
- Range: −$200 (anti-scoop) to +$200 (scoop)
- Distribution is heavy-tailed because of scoop bonuses

### How to read this table

The $/hand depends entirely on opponent field composition. Your *actual* hourly is determined by who you're playing against. Three useful anchors:

- **Worst-case competent field:** 3× Balanced Pro = $2.43/hand. This is the floor if your home game has only strong opponents.
- **Realistic home game:** Mixed competent (one of each common archetype) = **$17.58/hand**. Most actual home games look something like this.
- **Best-case soft field:** 3× Top-Greedy = $33.56/hand. A table of casual loose players who all front-load their top card.

---

## The hands-per-hour question (UNRESOLVED)

### Tentative estimate: 15 hands/hour live

Reasoning: a Taiwanese hand requires deal (4 × 7 cards = 28 cards) + 2 community boards + setting decision time + scoring + payout. Estimated **4-5 minutes per hand** = 12-15 hands/hr.

### Why this is uncertain

- Setting decision time varies enormously by hand complexity
- A V4-trained player aims for ≤30 seconds per hand (per the guide's cheat sheet) — but newer players may take 1-2 min
- The other 3 players' speed matters — slowest player bottlenecks the table
- Reveal + scoring + payout = ~1 min per hand
- Buyout decisions (~0.09% of hands) add minor delay

### Possible ranges

| Conditions | Hands/hr estimate |
|---|---:|
| Fast play, all experienced, no delays | 25-30 |
| **Typical home game pace** | **15-20** |
| Slow players, lots of discussion | 8-12 |
| Online single-table | 50-80 |
| Online 4-tabling | 200-300 |

### Action item

The operator should measure this at the next home session. Specifically:
- Set a timer for one hour of play
- Count hands dealt (count starts and finished hands)
- Repeat across 2-3 sessions for stability
- Update this document with the empirical number

---

## Hourly EV under different hands/hour assumptions

Multiplying the per-hand $/hand by hands/hr:

| Field | $/hand | @ 10 h/hr | @ 15 h/hr | @ 20 h/hr | @ 25 h/hr |
|---|---:|---:|---:|---:|---:|
| 3× Balanced Pro | $2.43 | $24 | $36 | $49 | $61 |
| 3× Reasonable Naïveté | $3.04 | $30 | $46 | $61 | $76 |
| 3× Hold'em-Mid Optimizer | $4.74 | $47 | $71 | $95 | $119 |
| **Mixed competent (realistic)** | **$17.58** | **$176** | **$264** | **$352** | **$440** |
| 3× Pair-First Standardist | $20.13 | $201 | $302 | $403 | $503 |
| 3× Top-Greedy Defender | $33.56 | $336 | $503 | $671 | $839 |

### Honest mid-point

At a typical home game with 15 hands/hr against a mixed competent field: **~$250-300/hour is the realistic expectation.**

---

## Variance reality — the binding constraint

### Per-hour variance

- At 15 hands/hr: per-hour stdev ≈ **±$504**
- At 25 hands/hr: per-hour stdev ≈ **±$650**

This means in ANY given hour:
- ±$500 from expected is "normal" (1σ swing)
- ±$1,000 from expected is "uncomfortable but expected" (2σ swing — happens ~5% of hours)
- ±$1,500+ is "bad night" (3σ — happens ~0.3% of hours)

### Sample size to confidently detect your edge

How long do you need to play before your actual results are statistically distinguishable from "lucky"?

| Real edge ($/hand) | Hands needed for 95% confidence | Live time @ 15h/hr | Online time @ 100h/hr |
|---|---:|---:|---:|
| $20/hand (loose field) | ~170 hands | **~11 hours** | ~2 hours |
| $9/hand (mixed competent) | ~840 hands | **~56 hours** | ~9 hours |
| $3/hand (tough field) | ~7,500 hands | **~500 hours** | ~75 hours |
| $0.5/hand (Grid Oracle approach) | ~270,000 hands | unrealistic | ~2,700 hours |

### What this means practically

- **Soft field (Top-Greedy / Standardist heavy):** you'll feel the edge within 10-15 hours of play. One good month of home games will show real winnings.
- **Mixed competent field:** you'll need 50+ hours to be statistically sure. About 3-6 months of weekly home games.
- **Tough field:** you may not feel the edge at all live; the variance band swallows it. Online is the only practical way to verify.

---

## Bankroll guidance

### Maximum risk per hand

- Worst single-hand outcome: anti-scoop = **−20 points × 3 opponents × $10 = −$600**
- Realistic worst-case for one tough hand: −12 points × 3 = **−$360**
- Typical bad-hand loss: **−$80 to −$120**

### Recommended bankroll by experience level

| Phase | Recommended bankroll | Why |
|---|---|---|
| First 50 hands (learning execution) | **$1,000-2,000** | Possible execution errors → realized edge may be lower than expected |
| Comfortable application of V4 | **$3,000-5,000** | Standard 20-30 buy-in cushion against normal variance |
| Long-term sustainable play | **$5,000-10,000** | Absorbs occasional 3σ downswings (~$1,500 bad nights) |
| Aggressive volume player | **$10,000+** | If playing 50+ hours/month, variance accumulation is real |

### Bankroll math sanity check

At the realistic mixed-competent field ($264/hr expected, ±$504/hr stdev):
- **Monthly expectation (20 hours/month):** $5,280 expected, with ~$2,250 stdev
- **Risk of losing month even with edge:** ~1% (assuming ~$5K bankroll)
- **Risk of losing 6 consecutive months:** essentially impossible given the edge

### The kicker — execution variance is the real risk

The V4 guide's 85-89% performance claim assumes **clean execution**. In early sessions:
- Cognitive load is high (visualizing Omaha 2+2 patterns + tier evaluations)
- Pressure of real money may cause mistakes
- Operator should expect 60-75% performance for the first 100-200 hands

This means **early-session realized edge may be 40-50% of theoretical**, not 85-89%. The bankroll should be sized to absorb this learning curve.

---

## Online play — the missing piece

### Why online would be transformational

| Metric | Live | Online single | Online 4-table |
|---|---:|---:|---:|
| Hands/hour | 15 | 60 | 240 |
| Hours to detect $9/hand edge | 56 | 14 | 4 |
| Hours to detect $3/hand edge | 500 | 125 | 31 |
| Sessions/month to play 1,000 hands | 16.7 | 4.2 | 1.0 |

### Current status — availability unknown

As of 2026-05, Taiwanese Poker is not known to be available on any commercial poker platform (PokerStars, GGPoker, etc.). It's primarily a home-game variant.

### Possible paths to online play

1. **Private friends-only app** — build a 4-player web app using the existing scorer/strategy infrastructure. Invite friends to play. Tracks data.
2. **Discord-bot dealer** — host the game logic in a Discord bot. Friends bring their own cards.
3. **Specific Asian poker apps** — Taiwanese variants may exist on regional platforms (untested by this project).

### If online play opens up

- Bankroll requirements shift toward "online standard" — typically 30-50 buy-ins
- Verification timeline compresses dramatically
- Can multi-table to accelerate edge realization

---

## Open questions to revisit

1. **Hands per hour empirical measurement** — operator to time during next 2-3 sessions
2. **Actual home-game opponent mix** — does the field actually look like "1× Standardist + 1× Top-Greedy + 1× Balanced", or different?
3. **Online platform availability** — is there a Taiwanese variant we don't know about?
4. **Execution-variance measurement** — track actual performance vs theoretical over first 200 hands

When any of these resolve, update this document and the corresponding hourly/bankroll numbers.

---

## TL;DR for someone reading this 6 months later

- **You probably win $200-400/hour** at a typical $10/point home game (15 hands/hr × $15-20/hand realistic mixed field)
- **Variance is brutal** — single-session swings of ±$1,000 are normal
- **Bankroll of $5K-10K is appropriate** for sustained play
- **Live verification takes months** of consistent play
- **Online would be the empirical proof** but Taiwanese isn't widely available
- **Early sessions will underperform** while execution becomes muscle memory

The MC says the math works. The variance reality says it'll feel random in the short term. Both are true.

---

*Last updated 2026-05-16 (end of Session 98). Update the hands/hour estimate once the operator measures it in real play.*
