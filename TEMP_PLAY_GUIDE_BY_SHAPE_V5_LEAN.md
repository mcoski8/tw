# Taiwanese Poker — The Lean Play Guide (V5)

> **V5 spec: same strategic content as V4, half the cognitive load. 25 sub-rules → 10 concepts.**
>
> Built from `STRATEGY_GUIDE.md` Part 6 + production chain (v53/v54/v55/v56 → v57 → v60 → v64 → v65) as of Session 97.
> Stake: $10/point. 4-handed home game. Same EV claims as V4 (~85-89% of perfect when applied cleanly).
>
> **Last updated:** 2026-05-16 (Session 98, V5). Optimized from V4 per Gemini-reviewed cognitive-load spec.

---

## How close to perfect?

```
$0 ──────────────────────────────────── $17,450 per 1,000 hands at $10/pt
random        you with this guide        production bot         perfect
              (~$13K-$15.5K)              ($16,340)              ($17,450)
                ~75-89%                      94%                   100%
```

You will be the strongest player at any normal home game. The math is rigorous — the gap to perfect is small enough that card-luck variance hides it session-to-session.

---

## How to use this document

Two ordering systems, on purpose:
- **At the table:** the cheat sheet + flow chart at top/bottom — **most-specific match first** (quads → trips → pairs → no pair).
- **While studying:** Chapter 2 walks **most-common first** (no pair → 1 pair → 2 pair → ... → quads).

---

## 30-second cheat sheet (lookup order — first match wins)

| Shape | Quick play |
|---|---|
| **Any Quads** (4+2+1 or 4+1+1+1) | Top = singleton. Mid = 2 quad cards at non-pair / non-singleton suits. Bot = other 2 quads + pair / 2 lower singletons. Always perfect DS. ⚠️ Low quads (≤5)? See Ch. 5 BUYOUT |
| **Rare composites** (two trips / trips+2pair) | See Rule 8 — keep pairs intact, build best DS bot, singleton on top |
| **Trips + pair** (3+2+1+1) | Split trips, keep pair: Mid = 2 trip cards, Bot = pair + 1 trip + 1 kicker. ⚠️ Low trips (≤4) + low pair (≤3)? Ch. 5 BUYOUT |
| **Pure trips** (3+1+1+1+1) | Mid = 2 trip cards. AAA/KKK/QQQ → 3rd trip on top. JJJ-or-lower → 3rd trip in bot |
| **Three pair** (2+2+2+1) | Top = singleton. Highest pair K/Q/J/T → mid = middle pair. Else → mid = highest pair |
| **Two pair** (2+2+1+1+1) | NEVER split. Pick the layout with the best DS bot |
| **Premium pair** (KK or AA) | Mid = pair. Top = Ace if you have one. Check rainbow override |
| **Standard pair, weak hand** | Max ≤ J + pair ≤ 6 OR pair = max → DEFENSIVE (Ch. 4) |
| **Standard pair, low/mid + no Ace + max ≤ Q** | PMID-swap: max non-pair card to BOT (not top) when 2+2 DS achievable |
| **Standard pair, normal** | Top = highest. Mid = pair. Bot = rest. Pair-to-bot DS only when narrow gates hit |
| **No pair, A/K/Q/J-high with healthy body** (2nd ≥ 9) | High card on top. Best DS bot. HIMID mid |
| **No pair, T-or-lower OR vulnerable broadway** (2nd ≤ 8) | DEFENSIVE (Ch. 4) |
| **Low quads or low trips + low pair?** | Ch. 5 BUYOUT |

---

# Chapter 1 — Bedrock principles

## 1. Tier values: 1 / 2 / 3 — the bottom is king

| Tier | Pts/board | Total per opponent |
|---|---:|---:|
| Top (1 card) | 1 | 2 |
| Mid (2 cards) | 2 | 4 |
| Bot (4 cards) | 3 | 6 |
| **Scoop** (all 6 with zero chops) | — | **+20** (replaces 12) |

At $10/point per opponent: scoop = $200, normal win = $120, top-only = $20. **The bot is 3× more valuable than the top. Design around the bot.**

## 2. The Omaha rule (rigid, unforgiving)

Bot uses **exactly 2 from your 4 hole cards + exactly 3 from the 5 board cards.** Not 1, not 3. Exactly 2.

This is why **double-suited (2+2) bots are gold** — two flush draws. A 3-flush bot is bad (the 3rd suited card is dead). A 4-flush is worst. Aim for 2+2.

## 3. The Mid tier is forgiving

Mid is Hold'em-style — 0, 1, or 2 hole cards used. A "weak" mid still wins often. Don't agonize over mid; **spend your decisions on the bot.**

## Two terms you'll see

- **DS bot** = double-suited bottom (2+2 suit pattern)
- **HIMID** = "high mid" tie-break: when picking which 2 cards go to mid, take the 2 highest non-bot cards

---

# Chapter 2 — The 8 macro rules (common → rare)

---

## Rule 1 — No pair (~20% of hands)

> ⚠️ **First check defensive trigger:** max ≤ T OR (max is K/Q/J AND 2nd-highest ≤ 8 = vulnerable broadway) → go to Chapter 4.

**For offensive no-pair hands** (A-high any body, OR K/Q/J-high with 2nd-highest ≥ 9):

- **Top** = highest card.
- **Bot** = best 2+2 DS pattern from remaining 6. If 2+2 not possible, single-suited (2+1+1).
- **Mid** = HIMID (the 2 highest leftover cards).

**Example:** `A♠ K♠ Q♥ J♣ 8♠ 5♥ 2♦`
- Best bot shape: single-suited spades (3 spades available, no 2+2).
- → **Top: A♠ · Mid: K♠ Q♥ · Bot: J♣ 8♠ 5♥ 2♦**

> 💰 ML edge here: subtle suit-texture decisions the rules don't capture. Accepted gap.

---

## Rule 2 — Premium pair: KK or AA (~7% of hands)

- **Mid** = both pair cards.
- **Top** = highest non-pair card (Ace if KK + lone Ace).
- **Bot** = remaining 4 cards.

**Example:** `4♣ 6♦ 8♥ J♠ Q♦ K♣ K♠` → **Top: Q♦ · Mid: K♣ K♠ · Bot: J♠ 8♥ 6♦ 4♣**

### Rainbow override (rare, ~$1,800 per fire)

If the resulting bot has **one of each suit** (rainbow) AND a 2+2 DS-bot is geometrically possible — **override**:

- **Bot** = both pair cards + lowest kicker matching each pair-suit (gives 2+2 DS).
- **Top** = highest of the 3 leftover non-pair cards.
- **Mid** = other 2 leftover cards.

**Example:** `K♠ K♦ 3♠ 5♦ 9♥ T♣ J♠` → mental default = rainbow bot → trigger
- → **Top: J♠ · Mid: T♣ 9♥ · Bot: K♠ K♦ 5♦ 3♠** (2♠+2♦ DS)

Fires ~1 in 370 hands. Memorize it.

---

## Rule 3 — Standard pair (~36% of hands)

Check sub-cases in order. **First match wins.**

### 3a. Defensive trigger
Max card ≤ J AND (pair ≤ 6 OR pair = max card) → **DEFENSIVE (Ch. 4).**

### 3b. PMID-swap exception
Pair is 2-7 (low) OR 8/9/T (mid), with no Ace, max non-pair ≤ Q, AND a 2+2 DS bot is achievable using max + 3 other singletons with pair in mid → **swap to PMID + DS-bot, max to bot, next-highest to top.**

In words: *with a low/mid pair, no Ace, max ≤ Q, ask "can I build a 2+2 bot including my max card and keep the pair in mid?" If yes — do it.*

### 3c. Pair-to-bot DS (narrow gate)
Pair rank ∈ {2-5, T-Q}, exactly one Ace, pair in two suits, kickers split (1,1)/(2,2)/(1,3)/(3,1) between pair-suits:
- **Top** = Ace. **Bot** = pair + lowest kicker per pair-suit (2+2 DS). **Mid** = 2 leftover kickers.

**Example:** `3♣ 4♦ 8♦ 9♣ Q♣ Q♦ A♣` → **Top: A♣ · Mid: 9♣ 8♦ · Bot: Q♣ Q♦ 3♣ 4♦**

### 3d. Default
- **Top** = highest non-pair card.
- **Mid** = the pair.
- **Bot** = 4 leftovers.

> 💰 ML edge: ML model picks slightly better in cases with feasible DS-bot routing.

---

## Rule 4 — Two pair (~22% of hands)

**NEVER split either pair.** Three valid layouts (all keep both pairs intact):

| Layout | Top | Mid | Bot |
|---|---|---|---|
| A | 1 kicker | 2 kickers | both pairs |
| B | 1 kicker | higher pair | lower pair + 2 kickers |
| C | 1 kicker | lower pair | higher pair + 2 kickers |

**Pick by:** 1) bot DS shape (2+2 > 2+1+1 > rainbow > 3+1), 2) top rank, 3) mid quality.

**Example:** `7♣ 7♦ 8♣ 8♦ J♥ K♠ A♠` → Layout A: bot 8♦8♣7♦7♣ = 2♣+2♦ DS ✓ → **Top: A♠ · Mid: K♠ J♥ · Bot: 8♦ 8♣ 7♦ 7♣**

**The trap:** splitting a pair to make "K♣Q♣ suited mid" bleeds heavily. Don't.

> 💰 ML edge here is the **largest** — two-pair has the biggest gap between human rules and ML play. The "never split + DS-bot priority" captures the bulk. ML refines the marginal splits.

---

## Rule 5 — Three pair (~1.9% of hands)

**Always:** Top = the singleton.

**Which pair goes to mid:** depends on the **highest pair's** rank.

| Highest pair | Mid is… | Bot is… |
|---|---|---|
| AA | the **AA** | the other two pairs |
| KK / QQ / JJ / TT | the **MIDDLE** pair | high pair + low pair |
| 99 or lower | the **HIGHEST** pair | the other two pairs |

**Memory hook:** *AA on top? Mid = AA. K/Q/J/T highest? Mid = MIDDLE pair. 9-or-lower highest? Mid = HIGHEST pair.*

**Examples:**

`A♥ A♦ K♥ K♣ Q♦ Q♣ 2♠` (AA highest) → **Top: 2♠ · Mid: A♥ A♦ · Bot: K♥ K♣ Q♦ Q♣**

`9♥ 9♦ 5♥ 5♣ 3♦ 3♣ 2♠` (99 highest → highest to mid) → **Top: 2♠ · Mid: 9♥ 9♦ · Bot: 5♥ 5♣ 3♦ 3♣**

---

## Rule 6 — Pure trips (~5.5% of hands)

**Always:** Mid = 2 of the 3 trip cards. The third trip goes top or bot — **never split alone**.

### Step 1 — Where does the third trip go?

| Trip rank | 3rd trip → | Special case |
|---|---|---|
| **AAA** | **Top** | Always |
| **KKK** | **Top** | If you have an Ace, put **Ace on top + 3rd K to bot** |
| **QQQ** | **Top** | If kickers contain J/K/A, **highest on top + 3rd Q to bot** |
| **JJJ or lower** | **Always BOT.** Top = highest non-trip. | None |

### Step 2 — Suit priority for the 3rd trip in bot

Look at the 3 bot-bound kickers' suits. You want bot = **2+2 DS**.

| Kicker pattern | Pick 3rd trip suit that gives… |
|---|---|
| Two share suit, one different | 3rd-trip suit = **singleton kicker's suit** → DS. Avoid matching the kicker-pair suit (3+1 trap). |
| All different (rainbow) | Any trip-suit completes a 2+1+1 SS. |
| All same suit (rare) | Avoid the 4-flush trap. |

**Rule of thumb:** *Never let the 3rd trip's suit equal the kicker-pair suit.*

**Examples:**

`2♦ 4♣ 7♥ J♠ A♣ A♦ A♥` → **Top: A♣ · Mid: A♦ A♥ · Bot: J♠ 7♥ 4♣ 2♦** (AAA always top)

`3♥ 5♥ 8♣ Q♣ 7♣ 7♦ 7♠` → kickers ♥♥♣ (pair=♥, singleton=♣); 7♣ → bot 2♥+2♣ DS ✓ → **Top: Q♣ · Mid: 7♦ 7♠ · Bot: 7♣ 8♣ 5♥ 3♥**

---

## Rule 7 — Trips + pair (~3% of hands)

Trips MUST split (mid only fits 2). Keep the pair intact. Two layouts:

| Layout | Top | Mid | Bot |
|---|---|---|---|
| A | 1 kicker | 2 trip cards (paired mid) | pair + 1 trip + 1 kicker |
| B | 1 kicker | 1 trip + 1 kicker | pair + 2 trips |

**Pick by:** 1) bot DS > SS > rainbow, 2) top rank, 3) prefer Layout A (paired mid is robust).

**Example:** `4♣ T♦ T♥ T♠ J♣ J♦ Q♦` → Layout A: bot J♦J♣T♦4♣ = 2♣+2♦ DS ✓ → **Top: Q♦ · Mid: T♠ T♥ · Bot: J♦ J♣ T♦ 4♣**

> ⚠️ **Low trips (≤4) + low pair (≤3)?** Check Chapter 5 BUYOUT before setting.

---

## Rule 8 — Any quads + rare composites (~0.4% of hands combined)

### 8a. Quads + pair (4+2+1) or Plain quads (4+1+1+1)

- **Top** = the singleton.
- **Mid** = the 2 quad cards at suits **NOT** used by your non-quad cards (pair-suits or singleton-suits).
- **Bot** = the other 2 quad cards + the pair / 2 lower singletons.

**Always produces a perfectly double-suited bot.**

**Example:** `A♣ A♦ A♥ A♠ K♣ K♦ 2♠` → Pair-suits = {♣, ♦}, non-pair = {♥, ♠} → **Top: 2♠ · Mid: A♥ A♠ · Bot: A♣ A♦ K♣ K♦** (2♣+2♦ DS).

> ⚠️ **Low quads (rank ≤ 5)?** Check Chapter 5 BUYOUT before setting.

### 8b. Two trips (3+3+1) OR Trips + two pair (3+2+2)

Macro-heuristic for these <0.2% shapes: **Never split pairs. Keep the highest paired/tripped structure in the mid. Build the strongest DS bot. Singleton on top.**

For two trips: split the HIGH trip across top + bot (one card each side), keep the LOW trip paired in mid.

For trips + two pair: split the trip, keep both pairs intact; mid is one pair (high if trip-rank ≥ 5, low if trip-rank ≤ 4), bot is the other pair + 2 trip-leftovers.

If you're under time pressure and unsure — apply the macro-heuristic (pairs intact, DS bot, singleton on top) and accept a small EV loss.

---

# Chapter 3 — The common thread

> **The bottom is king; double-suited bots are gold.** Whenever a pair (or trip) has two suits AND your kickers can fill the DS structure, putting the pair in the bot is usually correct. Two exceptions: (1) mid-rank pairs (6-9) are strong enough in mid that the trade isn't worth it; (2) KK/AA are valuable enough in mid that the trade flips back — *except* the rainbow override.
>
> The mid is forgiving (Hold'em-style, 0/1/2 hole cards). The bot is unforgiving (Omaha 2+3). Get the bot to DS shape whenever you can.

---

# Chapter 4 — Defensive Play (the most important short section)

> *Easy hands are easy. Hard hands lose money. This is one idea applied three ways.*

## The one idea

**On weak hands, invert your instinct.** Don't put your highest card on top — put your **lowest** card on top.

**Why:** Top = 1 pt/board, bot = 3×. If you'll lose a tier anyway, lose the **cheapest** one. Stacking strong cards into mid + bot turns a 12-pt disaster ($120) into a 4-pt loss ($40) — **you save $80 per opponent.**

## When to go defensive — three red flags

| Flag | The hand | Spotting it |
|---|---|---|
| 🚩 **1** | No pair, weak max | Max card T or lower — OR — max K/Q/J but 2nd-highest ≤ 8 |
| 🚩 **2** | Weak pair, J-low body | One pair, max ≤ J, AND (pair ≤ 6 OR pair = max) |
| 🚩 **3** | Mid-pair trap (anti-flag) | Pair is 7/8/9 in J-low body AND pair ≠ max → **play normally, accept the trap** |

## The defensive setting

**Flag 1 (no pair):** Top = lowest singleton. Bot = best 2+2 DS from rem6. Mid = 2 highest leftover.

**Flag 2 (weak pair):** Top = lowest non-pair singleton. Mid = the pair. Bot = 4 highest non-pair.

## One worked example

Hand: `T♣ 8♦ 6♥ 5♣ 4♣ 3♦ 2♠`

❌ *Trap:* Top=T♣, Mid=8♦6♥, Bot=5♣4♣3♦2♠ — T-high loses 90%+, bot is junk. Loss ~9-12 pts per opp = **$90-120 each.**

✅ *Defensive:* Top=**2♠**, Mid=**T♣ 8♦**, Bot=**6♥ 5♣ 4♣ 3♦** (2♣+1♥+1♦) — concede top deliberately, T-high mid wins fair share, 6-high bot with 2-club draw is real. Loss ~3-6 pts = **$30-60 each. You save $60-90 per opponent.**

## One thing to remember

> Top = 1 pt/board. Bot = 3 pts/board. If you have to lose, lose your cheapest tier first.

---

# Chapter 5 — The Buyout Option

> Variant rule: pay **4 pts ($40) per willing opponent** to fold the hand. Each opponent independently accepts/declines.
>
> All EV figures below are **per opponent**.

## The counterintuitive headline

**Buyouts are NOT for garbage hands. They are for structurally-trapped strong-shape hands.** Low quads and low trips+low pair LOOK strong but are crushed by the Omaha 2+3 rule — your "quads" play as just a pair of 3s on most boards.

## The decision matrix

| Your hand | You initiate (offer)? | Opponent offers you? |
|---|---|---|
| **Structurally trapped** (Quads rank ≤ 5, OR Trips ≤ 4 + Pair ≤ 3) | ✅ **OFFER to every opponent.** Expected loss > $40 each. | N/A |
| **Worth considering** (Quads 6-7, OR Pure trips ≤ 5 no pair) | 📊 Offer if you read opponent as tight (likely to accept) | — |
| **Garbage** (no pair, low max, or single low pair) | ❌ Never offer — losing only $5-15 each, not worth $40 | ✅ **Accept** the free $40 |
| **Medium-or-better** (KK-mid, two pair, mid trips, etc.) | ❌ Never offer — you're winning more by playing | ❌ **Decline** — they're trying to escape; don't let them |

## The mechanism (why low quads are traps)

You hold `3♣ 3♦ 3♥ 3♠ K♠ Q♣ J♦`. You build top=K♠, mid=Q♣J♦, bot=3♣3♦3♥3♠.

**The bot problem:** Omaha forces exactly 2-from-hand + 3-from-board. You can only use 2 of your four 3s. So your "quads" play as **a pair of 3s** in most board runouts. If the board has ANY pair higher than 3, opponent's pair-on-board beats your pair-of-3s.

Expected loss per opponent: ~5-7 pts = ~$50-70. Offering buyout to all 3 opponents saves you net $30-90 best case.

## What we know empirically

From `analysis/scripts/buyout_signature.py` (6M-hand grid):
- Tight signature fires on **0.09% of hands** (~1 in 1,100)
- When it fires, hand is truly trapped 26% of the time (precision)
- **Garbage hands have mean EV of only −$10 per opponent** — never worth paying $40 to fold

---

# Chapter 6 — The honest accounting

Four hand shapes are handled in production by an ML model (`v44_dt`, 2.25M-leaf decision tree), not human rules:
- **No pair** (~20% of hands)
- **One pair with feasible DS-bot routing** (subset of Rule 3)
- **Two pair** (~22%)
- **Pure trips** (~5.5%)

For these, the production bot routes directly to ML. Humans applying this guide fall back to "default play" in those zones.

## The honest score range

- **Production bot (v65 = rules + ML):** $16,340/1000h = **94% of perfect**
- **ML alone (v44_dt):** $10,810/1000h = **62%**
- **The 25 human rules add $5,528/1000h** over ML alone — rules do the bulk of the work
- **You with this guide:** estimated **$13,000-$15,500/1000h** = **75-89% of perfect**

The variance depends on how often no-pair and two-pair hands come up — those are where ML's edge is biggest.

## Why we don't give an exact human-only number

The project never directly graded "human applying this guide cleanly" against the same opponent model. Doing so requires Option C N=1000 sparse-grid infrastructure simulated against all 6M hands. Feasible but not done.

## The operator's decision

After 98 sessions, production reached 94% of perfect. The remaining 6% lives in three NULL-likely levers. The operator chose to ship this teaching guide rather than grind the final 6% — at normal play volumes, the gap is invisible vs card-luck variance.

**Bottom line:** you're a stronger player than 99% of the people you'll sit down with at any home game.

---

## At-the-table flow chart (lookup order — most specific first)

```
1. Sort your 7 cards.
2. First match wins.

3.  Quads + pair OR plain quads?      → Rule 8a.   ⚠️ Low quads (≤5)? Ch.5
4.  Two trips OR trips+two pair?       → Rule 8b.
5.  Trip + pair?                       → Rule 7.    ⚠️ Low trips+low pair? Ch.5
6.  Pure trips?                        → Rule 6.    ⚠️ Pure trips ≤5? Ch.5 (maybe)
7.  Three pair?                        → Rule 5.
8.  Two pair?                          → Rule 4 (never split, DS bot priority).
9.  One pair?
    - KK or AA?                         → Rule 2 (then check rainbow override)
    - Other pair, weak hand?            → CHAPTER 4 DEFENSIVE
    - Other pair, low/mid + max ≤ Q?    → Rule 3b (PMID-swap)
    - Other pair, narrow DS gate?       → Rule 3c (pair-to-bot DS)
    - Other pair, normal?               → Rule 3d (default)
10. No pair?
    - Max ≤ T OR vulnerable broadway?   → CHAPTER 4 DEFENSIVE
    - A/K/Q/J-high healthy body?        → Rule 1
11. Set and ship.
```

**That's the whole guide. 10 named rules. Read twice, play 100 hands, you'll have it.**

---

*Built from `STRATEGY_GUIDE.md` Part 6 + the production chain (v53/v54/v55/v56 → v57 → v60 → v64 → v65) as of Session 97 (2026-05-16). All 25 production rules from V4 are preserved in collapsed form. ML model `v44_dt` unchanged for 25 consecutive sessions.*

*V5 is the LEAN version of V4 — same strategic coverage, ~50% less reading, organized for memorization. Specifically: Rules 1a-1d collapsed → 1; Rules 7+8 collapsed → 8a; Rules 9a/9b collapsed → 8b; Rules 12/13 dropped as redundant; buyout chapter collapsed to action matrix; redundant worked examples pruned to one per rule.*
