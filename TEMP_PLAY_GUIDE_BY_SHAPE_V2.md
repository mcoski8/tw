# Taiwanese Poker — The Play Guide

> **What this is:** the project's near-optimal strategy distilled into rules a human can apply at the table in 30 seconds per hand. Built from 97 sessions of solver work on the full 6-million-hand canonical grid.
>
> **Stake assumption:** $10 per point throughout. A "scoop" (winning all 6 matchups) is +20 points = +$200. A normal win is up to +12 points = +$120.
>
> **How close to perfect:** if you apply this guide cleanly, you play at about **85-90% of mathematically perfect**. The remaining 10-15% lives in a machine-learning model that no human can run at the table. That gap is small enough that normal card-luck variance hides it — you will not feel it.
>
> **Last updated:** 2026-05-16 (Session 98). Reflects production strategy `v65`.

---

## How close is "close enough"?

A quick anchor before you read 25 rules.

```
$0 ─────────────────────────────────── $1,745 per 1,000 hands
random    your guide       perfect play
(no skill)  (~$1,500)        (the math)
            ≈85-90%           100%
```

At $10/point and 1,000 hands of play:

| Player | Wins per 1,000 hands |
|---|---:|
| 🎲 Random play | ~$0 (slightly negative) |
| 👤 You with this guide | **~$15,000** |
| 🤖 The production bot (v65 = these rules + a long-tail ML model) | **~$16,340** |
| 👑 Perfect play (the mathematical ceiling) | ~$17,450 |
| 👤 A typical opponent who knows the game | losing money to all of the above |

You will be the strongest player at any normal home game. The bot beats you by about $1,300 per 1,000 hands — meaningful long-term, invisible session-to-session.

---

## The 30-second cheat sheet

Sort your 7 cards by rank, high to low. Look for the strongest shape. **First match wins.**

| Shape | Quick play |
|---|---|
| **Quads + pair** (4+2+1) | Top=singleton, Mid=2 non-pair-suit quads, Bot=other 2 quads + pair (always DS) |
| **Plain quads** (4+1+1+1) | Top=high singleton, Mid=2 non-singleton-suit quads, Bot=other 2 quads + low singletons |
| **Two trips / Trips+two-pair** | Rare, see Rule 9 below |
| **Trips + pair** (3+2+1+1) | Split trips, keep pair: Mid=paired trip, Bot=pair+1 trip+1 kicker |
| **Pure trips** (3+1+1+1+1) | Mid=2 trip cards. AAA/KKK/QQQ: third trip on top. JJJ-or-lower: third trip in bot |
| **Three pair** (2+2+2+1) | Top=singleton. Highest pair is T/J/Q/K? Mid=middle pair. Else mid=highest pair |
| **Two pair** (2+2+1+1+1) | NEVER split. Layout with double-suited bot wins |
| **One pair (KK or AA)** | Mid=pair. Top=Ace if you have one. (Check rainbow override) |
| **One pair (other), weak hand** | DEFENSIVE — see Chapter 4 below |
| **One pair (other), normal hand** | Top=Ace (or highest), Mid=pair, Bot=rest. Pair-to-bot only if narrow gates met |
| **No pair, A/K/Q high** | High card on top, build best DS bot, mid keeps 2 highest leftovers |
| **No pair, T-or-lower max OR vulnerable broadway** | DEFENSIVE — see Chapter 4 below |
| **Anything truly junk?** | Consider the BUYOUT — see Chapter 5 |

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

**At $10/point, a scoop = $200, a clean non-scoop win = $120, a top-only win = $20.** The bot is 3× more valuable than the top. Design your hand around the bot.

### 2. The Omaha rule (rigid, unforgiving)

The bottom hand uses **exactly 2 from your 4 hole cards + exactly 3 from the 5 board cards**. Not 1, not 3. Exactly 2.

That single rule is what makes **double-suited bots (2♠+2♥, etc.) so valuable** — it gives you two separate flush draws. A 4-flush bot is mostly wasted (you can only use 2 of your suited cards). A 3-flush bot is bad (the 3rd suited card is dead). Aim for 2+2.

### 3. The Mid tier is forgiving

The middle is played Hold'em-style — you can use **0, 1, or 2** of your hole cards with the board. That flexibility means a "weak" mid (8-high broadway) can still win when the board cooperates. Don't agonize over the mid — it's hard to truly break.

The bot is rigid (2+3 mandatory). The top is one card (no flexibility). **Spend your decision-making on the bot.**

---

# Chapter 2 — The Main Playbook (common → rare)

Walk top to bottom. The first section that matches your hand IS your rule.

---

## Rule 1 — No pair (7 distinct ranks) — **~20% of hands**

You have no pair, trip, or quad — just 7 different ranks. The largest single category.

> ⚠️ **First, check Chapter 4 (Defensive Play).** If your hand is weak (max card T-or-lower, OR vulnerable broadway), the defensive play applies. Otherwise continue here.

### 1a — A-high (you hold an Ace)

- **Top** = the Ace, always.
- **Bot** = the 4 cards that form a **2+2 double-suited** pattern. Pick the suit pairs that give you the strongest two-flush.
- **Mid** = the 2 highest cards left over (HIMID — "high mid").

If a 2+2 DS bot isn't possible, try **single-suited (2+1+1) bot** with the same HIMID priority.

**Example:** `A♠ K♠ Q♥ J♣ 8♠ 5♥ 2♦`
- Suits: 3 spades, 2 hearts, 1 club, 1 diamond. Best 2+2 is **not** available (would need pairs of two suits). Best is single-suited spade bot.
- Top = A♠. Best SS bot = 2 spades + 2 others. Take 8♠ + 2♦ + 5♥ + J♣ → bot has 2♠+1♦+1♥+1♣. Mid = K♠ Q♥ (HIMID).
- → **Top: A♠ · Mid: K♠ Q♥ · Bot: J♣ 8♠ 5♥ 2♦**

### 1b — K-high (no Ace, max = K)

Same structure as 1a, with K on top.

### 1c — Q-high (no Ace/King, max = Q)

Same structure: Q on top, build DS bot, HIMID. The lifts shrink at Q (fewer hands win the top tier) but the structure is identical.

### 1d — J-high or lower

→ **GO TO CHAPTER 4 (DEFENSIVE).** Don't play offensively with no pair and weak top.

> 💰 **What the ML model still owns here:** an extra ~$3,550 per 1,000 hands ($355/1000h-equivalent at $10/point) lives in subtle texture decisions for no-pair hands. The default play above is conservative; the ML refines per-hand. Accepted gap.

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

### Sub-rule 2b — KK/AA rainbow override (rare, $1,800 per fire)

**Fires when ALL true:**

1. Pair = KK or AA.
2. Apply 2a mentally. If the 4 leftover (non-pair) cards have **one of each suit** (rainbow bot), trigger fires.
3. **DS-bot is geometrically possible** — at least one kicker matches each pair-suit.

**Setting (override 2a):**
- **Bot** = both pair cards + the **lowest** kicker matching each pair-suit (2+2 DS).
- **Top** = the **highest** of the 3 leftover cards.
- **Mid** = the other 2 leftover cards (often weak — fine).

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

**Example:** `3♣ 4♦ 8♦ 9♣ Q♣ Q♦ A♣` → Top: A♣ · Mid: 9♣ 8♦ · Bot: Q♣ Q♦ 3♣ 4♦

Fires on **~2.2%**.

### Sub-rule 2d — Q-pair PBOT_DS_JOINT (advanced single-cell)

**Fires when ALL true:**

1. Pair = QQ.
2. Both Q's are different suits.
3. The 4 non-pair cards include exactly 2 that match the pair's suits (one of each) AND 2 same-suited remaining cards.

**Setting:** both Q's to bot + 2 singletons completing DS. Mid = 2 same-suited cards. Top = max singleton.

This is a small, surgical refinement — Rule 19 in the project. Worth ~$0.85/hand average. **If you don't catch it at the table, no big deal** — 2c or default play loses only a small EV.

### Sub-rule 2e — Single-pair defensive (PMID swap)

**Fires when ALL true:**

1. Pair is **8, 9, or T** (the "MID pair" zone) — OR — pair is **2-7** (the "LOW pair" zone).
2. Pair has two different suits.
3. The board structure allows a "PMID double-suited" setting (pair in mid + 2+2 suited bot), AND the max singleton would otherwise have gone on top.
4. Max non-pair singleton is **Q or lower**.

**Setting:** swap to **PMID + DS-bot, with max singleton in bot** (not top). Top = next-highest singleton. Bot = 2+2 DS using max + 3 others. Mid = pair.

This is a defensive-style swap for one-pair hands where keeping the highest card on top wastes a flush draw. Two specific cell-level rules (Rule 20 for LOW pair, Rule 25 for MID pair) capture this; they're identical in spirit.

In practice at the table: **if you have a low/mid pair, no Ace, and a strong bot suit structure with max card Q or lower — the highest non-pair card belongs in the bot, not on top.**

### Sub-rule 2f — Default one-pair play

If none of 2a–2e fire:
- **Top** = your highest non-pair card.
- **Mid** = the pair.
- **Bot** = the 4 leftovers.

> 💰 **ML edge here:** ~$2,150 per 1,000 hands ($215/1000h) in the "pair with feasible DS-bot routing" cases. The default is the safe table play.

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

**The trap:** splitting one of the pairs to put "K Q suited mid" looks pretty but bleeds ~**$4,600 per 1,000 hands** ($460/1000h) on this exact hand. Never split.

### Special case — Rule 12: J-low two-pair both-intact + DS

**Fires when:** max card ≤ J AND a DS-bot is achievable with both pairs intact.
**Setting builder:** try HH-to-bot first (HH-suit + 2 singletons completing 2+2 DS), else LL-to-bot. Mid = the OTHER pair. Top = leftover singleton.

This is the layout-choice rule for two-pair hands that fit the J-low body. Already encoded in "pick by DS shape first" above; mentioned by name for completeness.

> 💰 **ML edge here:** ~$6,340 per 1,000 hands ($634/1000h). Two-pair is the largest single-category gap between human rules and the ML model. The "never split + DS-bot priority" rule still captures most of the EV — the ML's edge is in marginal cases where splitting actually wins.

---

## Rule 4 — Three pair — **~1.9% of hands**

Three pairs + one singleton.

**Always:** Top = the singleton (keeps all 3 pairs intact).

**Which pair goes to mid:** depends only on the **highest pair's** rank.

| Highest pair | Mid is… | Bot is… |
|---|---|---|
| AA | the AA | the other two pairs |
| KK / QQ / JJ / TT | the **MIDDLE** pair | high pair + low pair |
| 99 or lower | the **HIGHEST** pair | the other two pairs |

**Memory hook:** *"Highest pair K/Q/J/T → middle to mid. Else → highest to mid."*

**Examples:**

`A♥ A♦ K♥ K♣ Q♦ Q♣ 2♠` (AAA) → **Top: 2♠ · Mid: A♥ A♦ · Bot: K♥ K♣ Q♦ Q♣**

`K♥ K♦ Q♥ Q♣ 5♦ 5♣ 2♠` (KK → middle) → **Top: 2♠ · Mid: Q♥ Q♣ · Bot: K♥ K♦ 5♦ 5♣**

`9♥ 9♦ 5♥ 5♣ 3♦ 3♣ 2♠` (99 → highest) → **Top: 2♠ · Mid: 9♥ 9♦ · Bot: 5♥ 5♣ 3♦ 3♣**

### Special case — Rule 13: all-intact + DS

**Fires when:** the layout above also produces a DS-bot (the two "in-bot" pairs share two suits between them as 2+2). Already the natural play — Rule 13 only refines the LL-to-mid-only trap (avoid that case).

---

## Rule 5 — Pure trips — **~5.5% of hands**

Three of one rank + four singletons.

**Always:** Mid = 2 of the 3 trip cards (paired mid). The third trip goes either top or bot — **never split off alone**.

### Step 1 — Where does the third trip card go?

| Trip rank | Third trip to | Special case |
|---|---|---|
| **AAA** | **Top** | Always |
| **KKK** | **Top** | If you hold an Ace, put **Ace on top + 3rd K to bot** instead |
| **QQQ** | **Top** | If kickers contain J/K/A, put highest on top + 3rd Q to bot |
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

> 💰 **ML edge here:** ~$450 per 1,000 hands ($45/1000h). Modest. Rule 5 captures the bulk.

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

These together fire on <0.2% of hands. Worth knowing exists; don't sweat them.

### Rule 9a — Two trips (3+3+1) — ~0.07%

- **Top** = a HIGH-trip card whose suit ALSO appears in the LOW trip's suits.
- **Mid** = 2 of the 3 LOW-trip cards (paired mid).
- **Bot** = 2 remaining HIGH-trip cards + 1 LOW-trip + singleton. Pick the LOW card whose suit best builds DS.

**Example:** `T♣ T♦ T♥ 5♣ 5♦ 5♥ K♠` → Top: T♣ · Mid: 5♦ 5♥ · Bot: T♦ T♥ 5♣ K♠

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

> *Easy hands are easy to play. Hard hands are where money is lost. This section is intentionally short.*

## The one idea

When you're holding a weak hand, **invert your instinct**. Don't put your highest card on top — put your **lowest** card on top.

**Why:** Top is worth 1 point per board. Bot is 3× that. If you're going to lose a tier anyway, lose the **cheapest** one. Stacking your strong cards into Mid and Bot — even when "strong" just means a small pair or 8-high broadway — turns a 12-point disaster (~$120) into a 4-point loss (~$40). **You earn $80 by playing it correctly.**

## When to go defensive — three red flags

Pick the **first** flag that matches. If none match, play offensively per Chapter 2.

| Flag | The hand | What you're spotting |
|---|---|---|
| 🚩 **1. No pair, weak max** | Max card is **T or lower** — OR — max is J/Q/K but **2nd-highest ≤ 8** | "Tall but hollow" — no second card to back up the top |
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

❌ *The trap:* Top=T♣, Mid=8♦ 6♥, Bot=5♣ 4♣ 3♦ 2♠ — T-high top loses 90%+, bot is rainbow junk. Loss ~9-12 points = **~$90-120**.

✅ *Defensive:* Top=**2♠**, Mid=**T♣ 8♦**, Bot=**6♥ 5♣ 4♣ 3♦** (2♣+1♥+1♦) — concede the top deliberately, T-high mid wins a fair share, 6-high bot with a 2-club draw is real. Loss ~3-6 points = **~$30-60**. **You save $40-90 every time you play this correctly.**

**Example B — Weak pair, J-high body**

Hand: `J♥ 9♣ 7♣ 5♦ 5♣ 3♥ 2♠`

❌ *The trap:* Top=J♥, Mid=5♦ 5♣, Bot=9♣ 7♣ 3♥ 2♠ — J-on-top gets chopped or beaten, bot is weak. Loss ~6-9 points = **~$60-90**.

✅ *Defensive:* Top=**2♠**, Mid=**5♦ 5♣** (pair stays), Bot=**J♥ 9♣ 7♣ 3♥** (J-high + 2-club draw) — 2 on top concedes cleanly, pair-mid unchanged, bot is dramatically stronger. Loss ~3-5 points = **~$30-50**. **You save $30-60.**

## One thing to remember

> Top is 1 point per board. Bottom is 3 points per board. If you have to lose, lose your cheapest tier first.

---

# Chapter 5 — Managing Difficult Hands: The Buyout Option

> Variant rule: a player can offer to pay **4 points (= $40 at our stake) per willing opponent** to fold the hand entirely and avoid playing it. Each opponent independently accepts or declines. If they accept, you pay them $40 and the hand is over for that pair. If they decline, you must play.

## The single counterintuitive idea

**Buyouts are NOT for garbage hands. They are for structurally-trapped strong-shape hands.**

This is the most-missed insight in the game. Most players assume you buy out when your hand looks awful. The math says the opposite:

| Hand type | Buy out? | Why |
|---|---|---|
| **Quad 3s** (`3♣ 3♦ 3♥ 3♠ + low junk`) | **YES — buy out** | Quads of 3s are locked into bot. They lose to any pair the board makes for the opponent. Your "strong" hand is actually crushed structurally. Expected loss > $40. |
| **Garbage** (`Q♣ 8♦ 5♥ 4♠ 3♦ 2♣ + nothing`) | **NO — play it** | Bad expected EV (~−$10 to −$15) but **not worth $40 to fold.** You'll lose 1-2 points, not 5+. Just play and lose small. |
| **Low trips + low pair** (`333 + 22`) | **YES — buy out** | Same structural trap as quads. The board pairs up beats you. Expected loss > $40. |
| **Mid trips** (`555 + medium kickers`) | **NO — play it** | The bot has real strength. You'll often win the bot, sometimes the mid. Play. |

## When to OFFER a buyout (you initiate)

These are the empirically-validated +EV signatures from the solver. **Offer when your hand fits one of these:**

| Signature | Hand pattern | Average loss without buyout (per opponent) |
|---|---|---|
| 🎯 **Strong** | Quads of rank **5 or lower** (2222 / 3333 / 4444 / 5555) | ~−$50 to −$80 |
| 🎯 **Strong** | Trips of rank **4 or lower + low pair (rank ≤ 3)** (e.g. 333 + 22) | ~−$50 to −$70 |
| 📊 **Worth considering** | Quads of rank 6 or 7 (6666 / 7777) | ~−$30 to −$50 |
| 📊 **Worth considering** | Pure trips of rank ≤ 5, no pair (e.g. 555 + 5 high junk singletons) | ~−$30 to −$45 |

**At $40/opponent**, the "Strong" signatures are clear-money +EV. The "Worth considering" tier depends on the specific opponent — if you read them as a player who will accept (a tighter player who values certainty), offer. If they always decline, don't bother.

**Hands you might think to buy out but SHOULDN'T:**

- ❌ **No pair, low max** (7♣ 5♦ 4♥ 3♠ 2♣ ... ) — losing $5-15, not worth paying $40.
- ❌ **Single low pair** (2♣ 2♦ + junk) — losing $5-10, not worth $40.
- ❌ **Trips above 7** (888+, 999+, etc.) — likely net winners, never buy out.

## When to ACCEPT an opponent's buyout offer (they initiate)

**The information matters.** When someone offers you $40 to fold, they're telling you their hand is structurally weak — likely in the buyout signature zone (low quads / low trips + low pair).

**Decision tree when offered $40:**

1. **Does my hand likely beat their "buyout zone" range?** A medium pair (88-JJ in mid) or better usually beats low quads + structurally-trapped junk. If YES → **DECLINE** their offer. You'll extract more than $40 from the hand.

2. **Is my hand also weak (J-low body, no pair, weak pair)?** If YES → **ACCEPT.** Free $40. You probably weren't going to win much from them anyway, and now you do without playing.

3. **Is my hand strong (premium pair, trips, two-pair, etc.)?** **DECLINE** without hesitation. You're going to win much more than $40 by playing.

**Quick heuristic:** *if your hand wouldn't be in a buyout signature, decline. They're trying to escape; don't let them.*

## A worked buyout example

You hold: `3♣ 3♦ 3♥ 3♠ K♠ Q♣ J♦` — quads of 3s with K/Q/J kickers.

This looks like a monster. It's not.

- Best you can build: Top=K♠, Mid=Q♣ J♦, Bot=3♣ 3♦ 3♥ 3♠ (the four 3s).
- **The bot:** quads of 3s on the bot uses 2 threes from your hole + 3 board cards. If the board has ANY pair higher than 3 (i.e., any pair at all that's 4+), the opponent's pair-on-board likely beats your single-pair-3 from the available 2-card combo. Quad rank matters in showdowns where you can use all 4 quads, but Omaha forces you to use exactly 2 from hand — so your "quads" are functionally only **pair of 3s** in most scoring scenarios.
- **Average loss against the field:** ~5-7 points = ~$50-70 per opponent.

**Decision:** offer the buyout to each opponent. Each $40 paid SAVES you ~$10-30. Multiply by 3-4 opponents and you save $30-120 net.

If anyone declines, they're either misreading (good for you long-term) or holding their own strong hand (rare but happens). Either way, accept the table's individual choices.

## What the project knows empirically

From `analysis/scripts/buyout_signature.py` against the full 6M-hand grid:
- The signature above fires on **0.09% of hands** (~1 in 1,100).
- When it fires, the hand truly is structurally trapped 26% of the time (high precision).
- The signature misses about 53% of true-buyout hands (lower recall) — there's a softer signal in `trainer/src/buyout_eval.py` for "consider buyout vs *this specific opponent*" that we haven't ported into rules yet.
- **Garbage hands have an average EV of only −$10 — much less than the $40 buyout cost.** This is the empirical proof that the "buy out on junk" instinct is wrong.

---

# Chapter 6 — Appendix: What This Guide Leaves on the Table

Four hand shapes are handled in the production bot by a machine-learning model (`v44_dt` — a decision tree with about 2.25 million leaves). The model captures patterns no human can apply at the table. Here's how much EV you're leaving behind by using this guide alone:

| Shape | This guide uses | ML's extra edge (per 1,000 hands at $10/point) |
|---|---|---:|
| No pair (Rule 1) | Default play + Rules 1a-c + Chapter 4 defensive | **~$3,550** |
| One pair, "feasible DS-bot" cases (Sub-rule 2f) | Default play | **~$2,150** |
| Two pair (Rule 3) | Never-split + DS-priority | **~$6,340** |
| Pure trips (Rule 5) | Step 1 + Step 2 | **~$450** |
| **Total un-captured by humans** | | **~$12,490 per 1,000 hands** |

The production bot also includes a "blanket routing" layer: for the categories above, the bot does NOT apply human rules at all — it routes the hand to the ML model directly. The ML earns the extra ~$12,490 per 1,000 hands above purely by handling these per-hand instead of via boundary rules.

**The honest math:** you with this guide ≈ $15,000/1000h. The bot ≈ $16,340/1000h. Gap ≈ $1,340/1000h.

That's the cost of being human. At normal play volumes, it's invisible.

---

## At the table — the 30-second flow chart

```
1. Sort your 7 cards.
2. Spot the shape (most specific match wins).
3. Quad? → Rule 7 or 8.
4. Trip + pair? → Rule 6.
5. Pure trips? → Rule 5.
6. Three pair? → Rule 4.
7. Two pair? → Rule 3 (never split, prioritize DS bot).
8. One pair?
   - KK or AA?           → Rule 2a (then check 2b rainbow override)
   - Other pair, weak hand? → CHAPTER 4 DEFENSIVE
   - Other pair, normal? → 2c (gates) or 2f (default)
9. No pair?
   - Max ≤ T or vulnerable? → CHAPTER 4 DEFENSIVE
   - A/K/Q-high?        → Rule 1a/1b/1c
10. About to play a low-quad or low-trips+low-pair? → CHAPTER 5 BUYOUT
11. Set and ship.
```

That's the strategy. Read it twice, play 100 hands, you'll have it.

---

*Built from `STRATEGY_GUIDE.md` Part 6 + the production chain (v53/v54/v55/v56 architectural routing → v57 → v60 → v64 → v65) as of Session 97 (2026-05-16). Reflects all 25 production rules in their human-applicable form. Buyout signature from `analysis/scripts/buyout_signature.py`. ML model = `v44_dt` (unchanged since Session 58, 25 consecutive sessions).*

*This is a scratch teaching document. The canonical engineering reference remains `STRATEGY_GUIDE.md`. Update when production strategy changes.*
