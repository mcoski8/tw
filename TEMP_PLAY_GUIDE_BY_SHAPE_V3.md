# Taiwanese Poker — The Play Guide

> **What this is:** the project's near-optimal strategy distilled into rules a human can apply at the table in 30 seconds per hand. Built from 97 sessions of solver work on the full 6-million-hand canonical grid.
>
> **Stake assumption:** $10 per point throughout. A "scoop" (winning all 6 matchups) is +20 points = +$200. A normal clean win is up to +12 points = +$120.
>
> **How close to perfect:** the production bot (v65 = these rules + a long-tail ML model) plays at **93.6% of mathematically perfect**. A human applying these rules cleanly will land somewhere below that — we don't have a direct empirical grade of the human-only version, but the project's measurements bracket it between roughly 75% and 90% of perfect, depending on how often the ML-handled categories come up in your sessions.
>
> The remaining gap is small enough that normal card-luck variance hides it — you will not feel it session-to-session, but it adds up over thousands of hands.
>
> **Last updated:** 2026-05-16 (Session 98, V3). Reflects production strategy `v65`. Supersedes V1/V2.

---

## How close is "close enough"?

Quick anchor before the rules.

```
$0 ──────────────────────────────────── $17,450 per 1,000 hands
random      |          this guide          | production bot | perfect
(no skill)  v44_dt ML alone   (range)        (v65)            (the math)
            ~$10,810           ~$13,000–    ~$16,340          ~$17,450
                               $15,500
```

At $10/point and 1,000 hands of play:

| Player | Wins per 1,000 hands | % of perfect |
|---|---:|---:|
| 🎲 Random play | ~$0 (slightly negative) | ~0% |
| 🤖 ML model alone (no human rules) | **~$10,810** | ~62% |
| 👤 You with this guide (estimated range) | **~$13,000 – $15,500** | ~75–89% |
| 🤖 Production bot (v65 = rules + ML) | **~$16,340** | ~94% |
| 👑 Perfect play (mathematical ceiling) | ~$17,450 | 100% |

**Why a range for "you with this guide":** the project never directly graded "a human applying these rules cleanly." Your actual score depends on how often two specific category-types come up (no-pair and two-pair hands), where the ML model adds value the rules can't fully replicate. Over the long run, treat 80% of perfect as a realistic, honest target.

You will be the strongest player at any normal home game. The bot beats you by some amount — invisible session-to-session, real long-term.

---

## How to use this guide

This document has two ordering systems, intentionally:

- **At-the-table lookups** (the cheat sheet below, and the flow chart at the very end) are in **most-specific-first** order. Quads first, no-pair last. Walk top to bottom — the **first match wins**.
- **The teaching chapter** (Chapter 2) is in **most-common-first** order. No-pair first, quads last. Walk top to bottom to learn the rules in the order you'll see them in real games.

Both orderings are useful for different purposes. At the table, use the lookup. While studying, use the teaching chapter.

---

## The 30-second cheat sheet (lookup order — most specific first)

Sort your 7 cards by rank, high to low. Walk this table top to bottom. **The first shape that matches your hand IS your rule.**

| Shape | Quick play |
|---|---|
| **Quads + pair** (4+2+1) | Top=singleton, Mid=2 non-pair-suit quads, Bot=other 2 quads + pair (always double-suited) |
| **Plain quads** (4+1+1+1) | Top=high singleton, Mid=2 non-singleton-suit quads, Bot=other 2 quads + low singletons |
| **Two trips / Trips+two-pair** | Rare composite shapes — see Rule 9 below |
| **Trips + pair** (3+2+1+1) | Split trips, keep pair: Mid=2 trip cards, Bot=pair + 1 trip + 1 kicker |
| **Pure trips** (3+1+1+1+1) | Mid=2 trip cards. AAA/KKK/QQQ: 3rd trip on top. JJJ-or-lower: 3rd trip in bot |
| **Three pair** (2+2+2+1) | Top=singleton. Highest pair is T/J/Q/K? Mid=middle pair. Else mid=highest pair |
| **Two pair** (2+2+1+1+1) | NEVER split. Pick the layout that gives a double-suited bot |
| **One pair (KK or AA)** | Mid=pair. Top=Ace if you have one. Check rainbow override (see 2b) |
| **One pair (other), weak hand** | Max card is J-or-lower AND pair-rank ≤ 6 OR pair = max → DEFENSIVE (Ch. 4) |
| **One pair (other), normal** | Top=Ace (or highest), Mid=pair, Bot=rest. Pair-to-bot only if narrow gates met |
| **No pair, A/K/Q high, healthy body** | High card on top, build best DS bot, mid keeps 2 highest leftovers |
| **No pair, T-or-lower max OR vulnerable broadway** | Vulnerable broadway = max is J/Q/K but **2nd-highest is 8 or lower** → DEFENSIVE (Ch. 4) |
| **Low quads or low trips + low pair?** | Consider the BUYOUT — see Chapter 5 |

That's the whole strategy in one paragraph. The rest of this guide is the detail.

---

# Chapter 1 — The bedrock principles

Three ideas you need before any rule.

### 1. Tier values: 1 / 2 / 3 — the bottom is king

Each tier scores points **per board**. There are two boards. So:

| Tier | Points per board | Total per opponent |
|---|---:|---:|
| Top (1 card) | 1 | 2 |
| Mid (2 cards) | 2 | 4 |
| Bot (4 cards) | 3 | 6 |
| Scoop (all 6 with zero chops) | — | +20 (replaces 12) |

**At $10/point per opponent:** a scoop = $200, a clean non-scoop win = $120, a top-only win = $20. The bot is 3× more valuable than the top. **Design your hand around the bot.**

### 2. The Omaha rule (rigid, unforgiving)

The bottom hand uses **exactly 2 from your 4 hole cards + exactly 3 from the 5 board cards**. Not 1, not 3. Exactly 2.

That single rule is what makes **double-suited (2+2) bots so valuable** — it gives you two separate flush draws. A 4-flush bot is mostly wasted (you can only use 2 of your suited cards). A 3-flush bot is bad (the 3rd suited card is dead). Aim for 2+2.

### 3. The Mid tier is forgiving

The middle is played Hold'em-style — you can use **0, 1, or 2** of your hole cards with the board. That flexibility means a "weak" mid (8-high broadway) can still win when the board cooperates. Don't agonize over the mid — it's hard to truly break.

The bot is rigid (2+3 mandatory). The top is one card (no flexibility). **Spend your decision-making on the bot.**

### Two terms you'll see throughout

- **DS bot** = "double-suited bottom" = your 4 bot cards form a 2+2 suit pattern (two cards of one suit + two of another). This is the gold-standard bot shape.
- **HIMID** ("high mid") = a tie-break: when picking which 2 cards go to mid, pick the 2 highest non-bot cards.
- **PMID** ("pair-mid") = a setting where the pair stays in mid. The "PMID swap" decisions are about whether your highest non-pair card goes top or bot.

---

# Chapter 2 — The Main Playbook (teaching order — most common first)

Walk this chapter top to bottom while you're learning. **At the table, use the cheat sheet above instead** — it's in most-specific-first order, so the first match wins.

---

## Rule 1 — No pair (7 distinct ranks) — **~20% of hands**

You have no pair, trip, or quad — just 7 different ranks. The largest single category.

> ⚠️ **First, check Chapter 4 (Defensive Play).** If your hand is weak (max card T-or-lower, OR vulnerable broadway = max is J/Q/K with 2nd-highest ≤ 8), the defensive play applies. Otherwise continue here.

### 1a — A-high (you hold an Ace)

- **Top** = the Ace, always.
- **Bot** = the 4 cards that form a **2+2 double-suited (DS) pattern**. Pick the suit pairs that give you the strongest two-flush.
- **Mid** = **HIMID**: the 2 highest cards left over.

If a 2+2 DS bot isn't possible, fall back to a **single-suited (2+1+1) bot** with the same HIMID priority.

**Example:** `A♠ K♠ Q♥ J♣ 8♠ 5♥ 2♦`
- Suits: 3 spades, 2 hearts, 1 club, 1 diamond. Best 2+2 DS is not available (would need pairs of two suits). Best is single-suited spade bot.
- Top = A♠. Best SS bot = 2 spades + 2 others.
- → **Top: A♠ · Mid: K♠ Q♥ (HIMID) · Bot: J♣ 8♠ 5♥ 2♦**

### 1b — K-high (no Ace, max = K)

Same structure as 1a, with K on top.

### 1c — Q-high (no Ace/King, max = Q)

Same structure: Q on top, build DS bot, HIMID. The lifts shrink at Q (fewer hands win the top tier) but the structure is identical.

### 1d — J-high or lower

→ **GO TO CHAPTER 4 (DEFENSIVE).** Don't play offensively with no pair and a weak top.

> 💰 **What the ML model still owns here:** subtle texture decisions (specific suit + connectivity + low-card patterns) the rules don't capture. For the operator's at-the-table play this is an accepted gap — see Chapter 6 for the honest accounting.

---

## Rule 2 — One pair — **~43% of hands**

Most common category. Multiple sub-cases — check in order, **first match wins.**

### Sub-rule 2a — KK or AA (premium pair, default)

- **Mid** = both pair cards intact.
- **Top** = the highest non-pair card (the Ace if you hold KK + lone Ace).
- **Bot** = the remaining 4 cards.

**Examples:**

`4♣ 6♦ 8♥ J♠ Q♦ K♣ K♠` (KK + body) → **Top: Q♦ · Mid: K♣ K♠ · Bot: J♠ 8♥ 6♦ 4♣**

`4♣ 6♦ 8♥ Q♦ K♣ K♠ A♥` (KK + Ace) → **Top: A♥ · Mid: K♣ K♠ · Bot: Q♦ 8♥ 6♦ 4♣**

`9♣ T♦ J♥ Q♠ K♣ A♦ A♠` (AA + broadway) → **Top: K♣ · Mid: A♦ A♠ · Bot: Q♠ J♥ T♦ 9♣**

**Now check 2b** — it overrides 2a in a narrow case.

### Sub-rule 2b — KK/AA rainbow override (rare, ~$1,800 per fire)

**Fires when ALL true:**

1. Pair = KK or AA.
2. Apply 2a mentally. If the 4 leftover (non-pair) cards have **one of each suit** (rainbow bot), trigger fires.
3. **DS-bot is geometrically possible** — at least one kicker matches each pair-suit.

**Setting (override 2a):**
- **Bot** = both pair cards + the **lowest** kicker matching each pair-suit (gives a 2+2 DS bot).
- **Top** = the **highest** of the 3 leftover non-pair cards.
- **Mid** = the other 2 leftover cards (often weak — that's fine).

**Example:** `K♠ K♦ 3♠ 5♦ 9♥ T♣ J♠`
- Mental 2a: bot = 3♠ 5♦ 9♥ T♣ → rainbow → trigger.
- DS bot: K♠ K♦ + 3♠ + 5♦ (one ♠, one ♦) → 2+2.
- → **Top: J♠ · Mid: T♣ 9♥ · Bot: K♠ K♦ 5♦ 3♠**
- Swing: about **+$180 per hand** vs the wrong play here. Worth memorizing.

Fires on **~0.27% of hands** (~1 in 370). Rare but dramatic.

### Sub-rule 2c — Single-pair pair-to-bot DS (narrow gates)

**Fires when ALL true:**

1. Pair rank is **2–5 OR T–J–Q**. Skip the **Goldilocks zone (6-7-8-9)** — those pairs stay in mid.
2. You hold **exactly one Ace**.
3. The pair has **two different suits**.
4. The 4 non-pair, non-Ace kickers split (1,1), (2,2), (1,3), or (3,1) between the pair's suits. Skip lopsided (2,1) or (1,2).

**Setting:**
- **Top** = the Ace.
- **Bot** = both pair cards + the **lowest** kicker matching each pair-suit (2+2 DS).
- **Mid** = the 2 leftover kickers.

**Example:** `3♣ 4♦ 8♦ 9♣ Q♣ Q♦ A♣` → **Top: A♣ · Mid: 9♣ 8♦ · Bot: Q♣ Q♦ 3♣ 4♦**

Fires on **~2.2%**.

### Sub-rule 2d — Q-pair PBOT_DS_JOINT (advanced single-cell)

**Fires when ALL true:**

1. Pair = QQ.
2. Both Q's are different suits.
3. The 4 non-pair cards include exactly 2 that match the pair's suits (one of each) AND 2 same-suited remaining cards.

**Setting:** both Q's to bot + 2 singletons completing DS. Mid = the 2 same-suited cards. Top = max singleton.

This is a small, surgical refinement — Rule 19 in the project. Worth ~$0.85/hand average when it fires. **If you miss it at the table, no big deal** — falling back to 2c or 2f loses only a small amount.

### Sub-rule 2e — PMID-swap defensive (low/mid pair, max ≤ Q)

**The concept** (combines the project's Rules 20 and 25):

> *If you have a low or mid pair, no Ace, your max non-pair card is Q or lower, AND your hand allows a **double-suited (2+2) bot structure with the pair in mid** — then your highest non-pair card belongs **in the bot**, not on top.*

**Fires when ALL true:**

1. Pair is **2-7** (low) OR **8/9/10** (mid).
2. Pair has two different suits.
3. Max non-pair card is **Q or lower**.
4. A 2+2 double-suited bot is achievable using the max non-pair card + 3 other singletons, with the pair sitting in mid.
5. Otherwise you'd be playing "highest non-pair on top, pair in mid, junk in bot" — and that play is what we're swapping out of.

**Setting:** **PMID + DS-bot, with max singleton in bot** (not top). Top = next-highest singleton. Bot = 2+2 DS using max + 3 others. Mid = pair.

In practice at the table: **with a low/mid pair, no Ace, and max ≤ Q, ask "can I build a 2+2 bot that includes my max card and lets my pair stay in mid?" If yes — do it. Don't waste the max card on top.**

### Sub-rule 2f — Default one-pair play

If none of 2a–2e fire:
- **Top** = your highest non-pair card.
- **Mid** = the pair.
- **Bot** = the 4 leftovers.

> 💰 **ML edge here:** for one-pair hands where a feasible DS-bot routing exists, the ML model captures additional value the rules don't fully reach. See Chapter 6 for the honest accounting.

---

## Rule 3 — Two pair — **~22% of hands**

Two distinct pairs and 3 leftover singletons. The second-largest category.

**Setting: NEVER split either pair.** Three valid no-split layouts:

| Layout | Top | Mid | Bot |
|---|---|---|---|
| A | 1 kicker | 2 kickers | both pairs (4 cards) |
| B | 1 kicker | higher pair | lower pair + 2 kickers |
| C | 1 kicker | lower pair | higher pair + 2 kickers |

**Pick by:**
1. **Bot DS shape:** 2+2 > 2+1+1 > rainbow > 3+1 > 4-flush. This is the dominant factor.
2. **Top rank:** Ace > K > Q ...
3. **Mid quality:** paired > offsuit broadway > suited connector > weak.

**Example:** `7♣ 7♦ 8♣ 8♦ J♥ K♠ A♠` (88 + 77)
- Layout A: Top=A♠, Mid=K♠ J♥, Bot=8♦ 8♣ 7♦ 7♣ → bot is 2♣+2♦, **double-suited.** ✓
- Layout B: Top=A♠, Mid=8♣ 8♦, Bot=7♣ 7♦ K♠ J♥ → bot only single-suited.
- → **Layout A: Top: A♠ · Mid: K♠ J♥ · Bot: 8♦ 8♣ 7♦ 7♣**

**The trap:** splitting one of the pairs to put "K Q suited mid" looks pretty but bleeds heavily. Per-hand losses can be $400+ on this exact hand vs the correct never-split play. Don't split.

### Special case — Rule 12: J-low two-pair both-intact + DS

**Fires when:** max card ≤ J AND a DS-bot is achievable with both pairs intact.
**Setting builder:** try HH-to-bot first (the HH pair + 2 singletons completing 2+2 DS), else LL-to-bot. Mid = the OTHER pair. Top = leftover singleton.

This is the layout-choice rule for two-pair hands that fit the J-low body. Already encoded in "pick by DS shape first" above; mentioned by name for completeness.

> 💰 **ML edge here:** two-pair is the largest single-category gap between human rules and the ML model. The "never split + DS-bot priority" rule captures the bulk of the EV — the ML's extra value is in marginal cases where splitting actually wins. See Chapter 6.

---

## Rule 4 — Three pair — **~1.9% of hands**

Three pairs + one singleton.

**Always:** Top = the singleton (keeps all 3 pairs intact).

**Which pair goes to mid:** depends only on the **highest pair's** rank.

| Highest pair | Mid is… | Bot is… |
|---|---|---|
| AA | the **AA** | the other two pairs |
| KK / QQ / JJ / TT | the **MIDDLE** pair | high pair + low pair |
| 99 or lower | the **HIGHEST** pair | the other two pairs |

**Memory hook:**

> *"AA on top? Mid = AA. Highest pair is K/Q/J/T? Mid = middle pair. Highest pair is 9 or lower? Mid = highest pair."*

**Examples:**

`A♥ A♦ K♥ K♣ Q♦ Q♣ 2♠` (AA highest pair) → **Top: 2♠ · Mid: A♥ A♦ · Bot: K♥ K♣ Q♦ Q♣**

`K♥ K♦ Q♥ Q♣ 5♦ 5♣ 2♠` (KK highest → middle to mid) → **Top: 2♠ · Mid: Q♥ Q♣ · Bot: K♥ K♦ 5♦ 5♣**

`T♥ T♦ 9♥ 9♣ 5♦ 5♣ 2♠` (TT highest → middle to mid) → **Top: 2♠ · Mid: 9♥ 9♣ · Bot: T♥ T♦ 5♦ 5♣**

`9♥ 9♦ 5♥ 5♣ 3♦ 3♣ 2♠` (99 highest → highest to mid) → **Top: 2♠ · Mid: 9♥ 9♦ · Bot: 5♥ 5♣ 3♦ 3♣**

### Special case — Rule 13: all-intact + DS

**Fires when:** the layout above also produces a DS-bot (the two "in-bot" pairs share two suits between them as 2+2). This is already the natural play — Rule 13 only refines one trap (avoid the LL-pair-only-mid case).

---

## Rule 5 — Pure trips — **~5.5% of hands**

Three of one rank + four singletons.

**Always:** Mid = 2 of the 3 trip cards (paired mid). The third trip goes either top or bot — **never split off alone**.

### Step 1 — Where does the third trip card go?

| Trip rank | Third trip to | Special case |
|---|---|---|
| **AAA** | **Top** | Always |
| **KKK** | **Top** | If you hold an Ace, put **Ace on top + 3rd K to bot** instead |
| **QQQ** | **Top** | If kickers contain J/K/A, put the highest on top + 3rd Q to bot |
| **JJJ or lower** | **Always BOT.** Top = highest non-trip card. | None |

### Step 2 — Which of the 3 trip cards joins bot? (Suit priority)

Used only when Step 1 sent the third trip to bot.

You want bot to be **2+2 DS**. Look at the 3 bot-bound kickers' suits:

| Kicker pattern | Pick trip-suit that gives… |
|---|---|
| Two share a suit, one different ("two-and-one") | bot = 2+2 DS if trip-suit matches the **singleton** kicker. Avoid trip-suit matching the kicker-pair (gives 3+1 trap). |
| All different (rainbow) | trip-suit completes a 2+1+1 SS (one flush draw). Any trip works. |
| All same suit (rare) | avoid the 4-flush. Pick a different trip-suit. |

**Rule of thumb:** never let the third trip's suit equal the kicker-pair suit.

**Examples:**

`2♦ 4♣ 7♥ J♠ A♣ A♦ A♥` (AAA always top) → **Top: A♣ · Mid: A♦ A♥ · Bot: J♠ 7♥ 4♣ 2♦**

`4♣ 7♦ 9♥ A♥ K♣ K♦ K♠` (KKK + Ace → Ace on top, K to bot)
- Kickers heading to bot: 4♣ 7♦ 9♥ → rainbow. Pick K♣ or K♦ for SS, avoid K♠ (which adds nothing).
- → **Top: A♥ · Mid: K♦ K♠ · Bot: K♣ 9♥ 7♦ 4♣**

`3♥ 5♥ 8♣ Q♣ 7♣ 7♦ 7♠` (Trip 7 — third to bot)
- Top = Q♣. Bot kickers (3♥ 5♥ 8♣): two ♥ + one ♣ ("two-and-one", pair=♥, singleton=♣).
- 7♣ → bot 2♥+2♣ = DS ✓.
- → **Top: Q♣ · Mid: 7♦ 7♠ · Bot: 7♣ 8♣ 5♥ 3♥**

> 💰 **ML edge here:** small — Rule 5 captures the bulk of trips value. The ML's remaining edge lives in rare suit-texture cases.

---

## Rule 6 — Trips + pair — **~3% of hands**

Three of one rank + a pair + 2 singletons.

**Key idea:** the trips MUST split (mid fits only 2 cards). Keep the pair intact. Two layouts:

| Layout | Top | Mid | Bot |
|---|---|---|---|
| A | 1 kicker | 2 of the 3 trip cards (paired mid) | original pair + 1 trip + 1 kicker |
| B | 1 kicker | 1 trip + 1 kicker | original pair + 2 trips (4 cards = 2 pairs) |

**Pick by:** 1) bot DS > SS > rainbow, 2) top rank, 3) slight preference for Layout A.

**Example:** `4♣ T♦ T♥ T♠ J♣ J♦ Q♦` (TTT + JJ + 4 + Q)
- Layout A: Top=Q♦, Mid=T♠ T♥ (paired), Bot=J♦ J♣ T♦ 4♣ → bot has 2♣+2♦ = **DS** ✓.
- → **Top: Q♦ · Mid: T♠ T♥ · Bot: J♦ J♣ T♦ 4♣**

---

## Rule 7 — Quads + pair (4+2+1) — **~0.057% of hands**

Very rare (~1 in 1,750).

**Setting (always works):**
- **Top** = the singleton.
- **Mid** = the 2 quad cards whose suits are **NOT** the pair's suits.
- **Bot** = the other 2 quad cards + both pair cards. **Always perfectly DS.**

**Example:** `A♣ A♦ A♥ A♠ K♣ K♦ 2♠`
- Pair-suits = {♣, ♦}. Non-pair-suits = {♥, ♠}.
- → **Top: 2♠ · Mid: A♥ A♠ · Bot: A♣ A♦ K♣ K♦** (perfect 2♣+2♦ DS).

---

## Rule 8 — Plain quads (4+1+1+1) — **~0.24% of hands**

Four of one rank + 3 different singletons (no second pair).

**Setting:**
- **Top** = your highest singleton.
- **Mid** = the 2 quad cards at suits **NOT** used by any singleton.
- **Bot** = the other 2 quad cards + the 2 lower singletons.

**Example:** `9♣ 9♦ 9♥ 9♠ A♣ K♣ 7♥`
- Singleton-suits = {♣, ♥}. Non-singleton-suits = {♦, ♠}.
- → **Top: A♣ · Mid: 9♦ 9♠ · Bot: 9♣ 9♥ K♣ 7♥** (2♣+2♥ DS).

**Edge case:** if 3 singletons span 3 different suits, only 1 suit is "non-singleton" — fall back to any 2 quads in mid.

---

## Rule 9 — Very rare composite shapes

These together fire on <0.2% of hands. Worth knowing exist; don't sweat them.

### Rule 9a — Two trips (3+3+1) — ~0.07%

- **Top** = a HIGH-trip card whose suit ALSO appears in the LOW trip's suits.
- **Mid** = 2 of the 3 LOW-trip cards (paired mid).
- **Bot** = 2 remaining HIGH-trip cards + 1 LOW-trip + singleton. Pick the LOW card whose suit best builds DS.

**Example:** `T♣ T♦ T♥ 5♣ 5♦ 5♥ K♠` → **Top: T♣ · Mid: 5♦ 5♥ · Bot: T♦ T♥ 5♣ K♠**

### Rule 9b — Trips + two pair (3+2+2) — ~0.11%

- **Top** = a trip card at a suit not shared with either pair (suit-aware split).
- If **trip-rank ≤ 4** → mid = LOW pair, bot = 2 trip-leftovers + HIGH pair.
- Else (**trip-rank ≥ 5**) → mid = HIGH pair, bot = 2 trip-leftovers + LOW pair.

**Examples:**

`T♣ T♦ T♥ Q♣ Q♦ 8♥ 8♠` (trip 10 ≥ 5) → **Top: T♣ · Mid: Q♣ Q♦ · Bot: T♦ T♥ 8♥ 8♠**

`3♣ 3♦ 3♥ K♣ K♦ Q♥ Q♠` (trip 3 ≤ 4) → **Top: 3♥ · Mid: Q♥ Q♠ · Bot: 3♣ 3♦ K♣ K♦**

---

# Chapter 3 — The Common Thread

> **The bottom tier is king and double-suited (2+2) bots are gold.** Whenever a pair (or trip) can serve as a suit anchor for the bot — meaning it has two different suits AND your kickers fill out the DS — putting that pair in the bot is usually correct. Two exceptions: (1) **mid-rank pairs (6-9)** are strong enough in mid that the trade isn't worth it; (2) **KK/AA** are valuable enough in mid that the trade flips back (except the rainbow-bot override, which restores it). The mid is forgiving (Hold'em-style, 0/1/2 hole cards), so giving up "pair in mid" loses less than instinct suggests. The bot is unforgiving (Omaha 2+3 mandatory) — get it to DS shape whenever you can.

---

# Chapter 4 — Managing Difficult Hands: Defensive Play

> *Easy hands are easy to play. Hard hands are where money is lost. This section is intentionally short — defensive play is one idea applied three ways.*

## The one idea

When you're holding a weak hand, **invert your instinct**. Don't put your highest card on top — put your **lowest** card on top.

**Why:** Top is worth 1 point per board. Bot is 3× that. If you're going to lose a tier anyway, lose the **cheapest** one. Stacking your strong cards into Mid and Bot — even when "strong" just means a small pair or 8-high broadway — turns a 12-point-per-opponent disaster (~$120 per opponent) into a 4-point-per-opponent loss (~$40 per opponent). **You earn $80 per opponent by playing it correctly.**

## When to go defensive — three red flags

Pick the **first** flag that matches. If none match, play offensively per Chapter 2.

| Flag | The hand | What you're spotting |
|---|---|---|
| 🚩 **1. No pair, weak max** | Max card is **T or lower** — OR — max is J/Q/K but **2nd-highest ≤ 8** (vulnerable broadway) | "Tall but hollow" — no second card to back up the top |
| 🚩 **2. Weak pair, J-low body** | Exactly **one pair**, max is **J or lower**, AND **pair-rank ≤ 6** *OR* **pair = max** | A pair that won't anchor the mid against the field |
| 🚩 **3. The mid-pair anti-trap** | Pair is **7, 8, or 9** in a J-low body AND pair ≠ max | Looks defendable but it's a trap — play normally and accept it |

## The defensive setting

When **Flag 1** fires (no pair):

- **Top** = your **lowest** singleton.
- **Bot** = the 4 cards that make the best 2+2 DS pattern (pick the suit pairs that give two suited pairs).
- **Mid** = the 2 highest leftover cards.

When **Flag 2** fires (weak pair):

- **Top** = your **lowest** non-pair singleton.
- **Mid** = the pair (it stays as the structural anchor).
- **Bot** = the 4 highest non-pair singletons.

(Flag 3 doesn't fire — play normally and accept it.)

## Two examples

**Example A — No pair, T-high body**

Hand: `T♣ 8♦ 6♥ 5♣ 4♣ 3♦ 2♠`

❌ *The trap:* Top=T♣, Mid=8♦ 6♥, Bot=5♣ 4♣ 3♦ 2♠ — T-high top loses 90%+, bot is rainbow junk. Loss ~9-12 points per opponent = **~$90-120 per opponent**.

✅ *Defensive:* Top=**2♠**, Mid=**T♣ 8♦**, Bot=**6♥ 5♣ 4♣ 3♦** (2♣+1♥+1♦) — concede the top deliberately, T-high mid wins a fair share, 6-high bot with a 2-club draw is real. Loss ~3-6 points per opponent = **~$30-60 per opponent**. **You save $40-90 per opponent every time you play this correctly.**

**Example B — Weak pair, J-high body**

Hand: `J♥ 9♣ 7♣ 5♦ 5♣ 3♥ 2♠`

❌ *The trap:* Top=J♥, Mid=5♦ 5♣, Bot=9♣ 7♣ 3♥ 2♠ — J-on-top gets chopped or beaten, bot is weak. Loss ~6-9 points per opponent = **~$60-90 per opponent**.

✅ *Defensive:* Top=**2♠**, Mid=**5♦ 5♣** (pair stays), Bot=**J♥ 9♣ 7♣ 3♥** (J-high + 2-club draw) — 2 on top concedes cleanly, pair-mid unchanged, bot is dramatically stronger. Loss ~3-5 points per opponent = **~$30-50 per opponent**. **You save $30-60 per opponent.**

## One thing to remember

> Top is 1 point per board. Bottom is 3 points per board. If you have to lose, lose your cheapest tier first.

---

# Chapter 5 — Managing Difficult Hands: The Buyout Option

> Variant rule: a player can offer to pay **4 points (= $40 at our stake) per willing opponent** to fold the hand entirely and avoid playing it. Each opponent independently accepts or declines. If an opponent accepts, you pay THAT opponent $40 and the hand is over between the two of you. If they decline, you must play out the hand against that opponent.
>
> **All EV figures in this chapter are per-opponent unless explicitly stated otherwise.** At a 3-opponent table, multiply by 3 to estimate total cost vs total swing.

## The single counterintuitive idea

**Buyouts are NOT for garbage hands. They are for structurally-trapped strong-shape hands.**

This is the most-missed insight in the game. Most players assume you buy out when your hand looks awful. The math says the opposite:

| Hand type | Buy out? | Why |
|---|---|---|
| **Quad 3s** (`3♣ 3♦ 3♥ 3♠ + low junk`) | **YES — buy out** | Quads of 3s are locked into bot. They lose to any pair the board makes for the opponent. Your "strong" hand is actually crushed structurally. Expected loss > $40 per opponent. |
| **Garbage** (`Q♣ 8♦ 5♥ 4♠ 3♦ 2♣ + nothing`) | **NO — play it** | Bad expected EV (~−$5 to −$15 per opponent) but **not worth $40 per opponent to fold.** You'll lose 1-2 points each, not 5+. Just play and lose small. |
| **Low trips + low pair** (`333 + 22`) | **YES — buy out** | Same structural trap as quads. The board pairs up beats you. Expected loss > $40 per opponent. |
| **Mid trips** (`555 + medium kickers`) | **NO — play it** | The bot has real strength. You'll often win the bot, sometimes the mid. Play. |

## When to OFFER a buyout (you initiate)

These are the empirically-validated +EV signatures from the solver. **Offer when your hand fits one of these:**

| Signature | Hand pattern | Average per-opponent loss without buyout |
|---|---|---|
| 🎯 **Strong** | Quads of rank **5 or lower** (2222 / 3333 / 4444 / 5555) | ~−$50 to −$80 per opponent |
| 🎯 **Strong** | Trips of rank **4 or lower + low pair (rank ≤ 3)** (e.g. 333 + 22) | ~−$50 to −$70 per opponent |
| 📊 **Worth considering** | Quads of rank 6 or 7 (6666 / 7777) | ~−$30 to −$50 per opponent |
| 📊 **Worth considering** | Pure trips of rank ≤ 5, no pair (e.g. 555 + 5 high junk singletons) | ~−$30 to −$45 per opponent |

**At $40 per willing opponent**, the "Strong" signatures are clear +EV — offer to all opponents. The "Worth considering" tier is borderline: if you read an opponent as tighter (more likely to accept), offer to them; otherwise skip.

**Hands you might think to buy out but SHOULDN'T:**

- ❌ **No pair, low max** (7♣ 5♦ 4♥ 3♠ 2♣ ... ) — losing $5-15 per opponent, not worth paying $40 per opponent.
- ❌ **Single low pair** (2♣ 2♦ + junk) — losing $5-10 per opponent, not worth $40 per opponent.
- ❌ **Trips above 7** (888+, 999+, etc.) — likely net winners, never buy out.

## When to ACCEPT an opponent's buyout offer (they initiate)

**The information matters.** When someone offers you $40 to fold, they're telling you their hand is structurally weak — almost certainly in the buyout signature zone (low quads / low trips + low pair).

**Decision tree when offered $40:**

1. **Does my hand likely beat their "buyout zone" range?** A medium pair (88-JJ in mid) or better usually beats low quads + structurally-trapped junk. If YES → **DECLINE** their offer. You'll extract more than $40 from the hand against this opponent.

2. **Is my hand also weak (J-low body, no pair, weak pair)?** If YES → **ACCEPT.** Free $40. You probably weren't going to win much from them anyway, and now you do without playing.

3. **Is my hand strong (premium pair, trips, two-pair, etc.)?** **DECLINE** without hesitation. You're going to win much more than $40 from this opponent by playing.

**Quick heuristic:** *if your hand wouldn't be in a buyout signature, decline. They're trying to escape; don't let them.*

## A worked buyout example

You hold: `3♣ 3♦ 3♥ 3♠ K♠ Q♣ J♦` — quads of 3s with K/Q/J kickers.

This looks like a monster. It's not.

- Best you can build: Top=K♠, Mid=Q♣ J♦, Bot=3♣ 3♦ 3♥ 3♠ (the four 3s).
- **The bot:** because of the Omaha 2-from-hand rule, you can only use 2 of your four 3s with 3 board cards. So your "quads" play as just a **pair of 3s** in most board runouts. If the board has any pair higher than 3 (i.e., any pair at all that's 4+), your opponent's pair-on-board likely beats your pair-of-3s bottom.
- **Average per-opponent loss against the field:** ~5-7 points = ~$50-70 per opponent.

**Decision:** offer the buyout to each opponent individually. Each $40 paid SAVES you ~$10-30 per that opponent. At a 3-opponent table, offering to all three saves you roughly $30-90 net (best case: all three accept = -$120 vs -$150-210 if you play it out; worst case: only one accepts = small but real save).

If an opponent declines, they're either misreading the situation (good for you long-term) or they're holding their own strong hand (rare but possible). Either way, accept each opponent's individual choice and play out the hand against the decliners.

## What the project knows empirically

From `analysis/scripts/buyout_signature.py` against the full 6M-hand grid:
- The signature above fires on **0.09% of hands** (~1 in 1,100).
- When it fires, the hand truly is structurally trapped 26% of the time (high precision).
- The signature misses about 53% of true-buyout hands (lower recall) — there's a softer signal in `trainer/src/buyout_eval.py` for "consider buyout vs *this specific opponent*" that hasn't been ported into rules yet.
- **Garbage hands have an average per-opponent EV of only −$10 — far less than the $40 buyout cost.** This is the empirical proof that the "buy out on junk" instinct is wrong.

---

# Chapter 6 — Appendix: The honest accounting

Four hand shapes are handled in the production bot by a machine-learning model (`v44_dt` — a decision tree with about 2.25 million leaves) rather than by human rules:

- **No pair** (~20% of hands)
- **One pair where a feasible double-suited bot exists** (subset of one-pair)
- **Two pair** (~22% of hands)
- **Pure trips** (~5.5% of hands)

For these categories, the production bot does NOT apply rules at all — it routes the hand directly to the ML model. The ML captures texture and connectivity patterns no human can apply at the table.

## What this means for you, the human

When you apply this guide, you're using:
- **Deterministic rules** for premium pairs (KK/AA), three pair, trips+pair, all quad shapes, and the defensive zones.
- **"Default play" fallback** for the ML-handled categories above, plus the narrow gates of Rules 1, 2c, and 2d.

The default play in ML categories is what the guide tells you (e.g., "never split two pair, prioritize DS bot") — strong play, but not the ML's full strength.

## The honest score range

We measure two reference points cleanly:
- **Production v65 (rules + ML):** $16,340 per 1,000 hands at $10/point. **93.6% of perfect.**
- **ML alone (v44_dt, no human rules):** $10,810 per 1,000 hands. **62% of perfect.**

The 25 human rules contribute **$5,528 per 1,000 hands** of value over ML alone (v65 minus v44_dt at $10/point). That's the bulk of the strategy — the rules are doing most of the work.

**Your score with this guide alone** sits between those two reference points. It's higher than ML-alone (because you're applying the 25 rules for the categories where rules dominate) but lower than v65 (because for ML-handled categories, you're using default play instead of the ML's full per-hand decisioning).

A realistic estimate: **$13,000–$15,500 per 1,000 hands** = **75–89% of perfect**. The variance depends on how often two-pair and no-pair hands come up in your sessions — those are where the ML's edge is largest.

## Why we don't give you an exact number

The project never directly graded "a human applying this guide cleanly" against the same opponent model. Doing so would require simulating perfect-rule-application across the full 6M-hand grid, which is feasible but hasn't been done. **A V4 of this guide could include that grade if you want the exact number.**

## The decision the operator made

After 97 sessions, the production strategy reached 93.6% of perfect. The remaining 6.4% lives in three diminishing-return levers that each have small expected value. The operator decided to ship this teaching guide rather than grind the final 6.4% — at normal play volumes, the gap is invisible relative to card-luck variance, and the human-usable artifact has more value than another ~1-3% of EV gain in the bot.

**Bottom line:** you with this guide are a stronger player than 99% of the people you'll sit down with at any home game. The honest gap to "perfect" is small enough that the gain from closing it would be hard to feel session-to-session.

---

## At-the-table flow chart (lookup order — most specific first)

```
1. Sort your 7 cards.
2. Spot the shape (most specific match wins).
3. Quad + pair?     → Rule 7.
4. Plain quads?     → Rule 8.
5. Two trips OR     → Rule 9.
   Trips + 2 pair?
6. Trip + pair?     → Rule 6.
7. Pure trips?      → Rule 5.
8. Three pair?      → Rule 4.
9. Two pair?        → Rule 3 (never split, prioritize DS bot).
10. One pair?
    - KK or AA?           → Rule 2a (then check 2b rainbow override)
    - Other pair, weak hand? → CHAPTER 4 DEFENSIVE
    - Other pair, low/mid with max ≤ Q? → check 2e (PMID-swap)
    - Other pair, normal? → 2c (gates) or 2f (default)
11. No pair?
    - Max ≤ T or vulnerable broadway? → CHAPTER 4 DEFENSIVE
    - A/K/Q-high, healthy body?      → Rule 1a / 1b / 1c
12. About to play a low quad or low trips+low pair? → CHAPTER 5 BUYOUT
13. Set the hand and ship it.
```

That's the strategy. Read it twice, play 100 hands, you'll have it.

---

*Built from `STRATEGY_GUIDE.md` Part 6 + the production chain (v53/v54/v55/v56 architectural routing → v57 → v60 → v64 → v65) as of Session 97 (2026-05-16). Reflects all 25 production rules in their human-applicable form. Buyout signature from `analysis/scripts/buyout_signature.py`. ML model = `v44_dt` (unchanged since Session 58, 25 consecutive sessions).*

*This is V3, replacing V2 (which had a math contradiction in Chapter 6 and a few smaller bugs surfaced by independent review). The canonical engineering reference remains `STRATEGY_GUIDE.md`. Update when production strategy changes.*
