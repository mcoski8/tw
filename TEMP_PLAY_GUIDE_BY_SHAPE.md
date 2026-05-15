# Taiwanese Poker — Player Guide (TEMP / by-shape order)

> **What this is:** the same rule set as `TEMP_PLAY_GUIDE.md`, but
> reorganized so you walk the document **in order** from the simplest
> hand shape to the most complex. Rules are renumbered so they match
> the flow: Rule 1 = no pair, Rule 2 = one pair, Rule 3 = two pair, and
> so on. No scrolling back to check a rule number.
>
> **How to use:** start at the top. The first section heading that
> matches your hand IS your rule. Stop there.
>
> **Status:** scratch document for reading. NOT the canonical strategy
> guide (`STRATEGY_GUIDE.md`).
>
> **Honesty disclosures up front:**
> 1. Three of the most important hand categories (**trips**, **two pair**,
>    and **single pair where a double-suited bot is reachable**) are
>    handled by an ML model in the production chain. For those, this
>    guide gives you a "good-enough" rule that scores well below what
>    the ML model finds — the ML edge is summarized in the table at
>    the bottom of this file.
> 2. The production rule chain ranks ~$348/1000h behind the ML model.
>    So this guide gets you most of the way, not all the way.
> 3. Edge over the "naive obvious play" baseline if you apply Rules
>    1–10 cleanly: **about +$1,015/1000h**.

---

## Step 0 — Sort your 7 cards and identify the shape

Sort by rank, high to low. Look for the strongest "shape." The
sections below are in the order you should check them — first match
wins.

```
Have no pair? (7 distinct ranks)              → Rule 1
Have one pair? (and no trips/quads)           → Rule 2 (sub-rules a–e inside)
Have two pair?                                → Rule 3
Have three pair?                              → Rule 4
Have pure trips? (no other pair, no quads)    → Rule 5
Have trips + pair? (3+2+1+1)                  → Rule 6
Have two trips? (3+3+1)                       → Rule 7
Have trips + two pair? (3+2+2)                → Rule 8
Have plain quads? (4+1+1+1)                   → Rule 9
Have quads + pair? (4+2+1)                    → Rule 10
```

You will scan top-to-bottom **once**. The matching section starts
right after this list — keep reading.

---

## Rule 1 — No pair (7 distinct ranks)

**Fires when** all 7 cards are different ranks.

This is the largest unsolved category in the project. There is no
clean human rule for it — the production chain falls back to a default
play, and the ML model captures another **~$355/1000h** of edge that
no rule has matched.

### The default play (use this at the table)

- **Top** = your highest card (Ace if you have one).
- **Mid** = your strongest 2-card Hold'em combo from what's left, in this priority:
  1. Two cards of the **same suit AND connected** (e.g. K♠ Q♠) — best.
  2. Two cards of the same suit (suited but disconnected) — good.
  3. Two **broadway** cards (T or higher) of different suits.
  4. Connected non-broadway (e.g. 9♦ 8♣).
  5. Anything left.
- **Bot** = the remaining 4 cards. Try to make sure at least 2 cards share a suit (gives you an Omaha flush draw).

**Worked example:** `A♠ K♠ Q♥ J♣ 8♠ 5♥ 2♦`
- Top = A♠ (highest).
- Mid: K♠ Q♥ (broadway pair) — but K♠ + 8♠ would be suited, weaker than KQ broadway. Pick K♠ Q♥.
- Bot = J♣ 8♠ 5♥ 2♦. (Mostly rainbow, no flush draw — accept it.)
- → **Top: A♠  ·  Mid: K♠ Q♥  ·  Bot: J♣ 8♠ 5♥ 2♦**

> ⚠️ The ML model would refine this picky-by-picky for hand-specific
> suit and connectivity patterns. The default play is conservative;
> it loses ~$355/1000h on this category vs the model.

**Fires on:** ~20% of hands.

---

## Rule 2 — One pair (no trips, no quads, no second pair)

**Fires when** you have exactly one pair and 5 different singletons.

This is the most-branched rule in the guide because one-pair hands have
several sub-cases. Check the sub-rules **in order**; first match wins.

### Sub-rule 2a — Premium pair KK or AA (default)

**Fires when** your pair is KK or AA.

- **Mid** = both pair cards (KK or AA), intact.
- **Top** = the highest non-pair card you hold (the Ace if KK + lone Ace; otherwise the next-highest singleton).
- **Bot** = the remaining 4 cards.

**Worked examples:**

`4♣ 6♦ 8♥ J♠ Q♦ K♣ K♠` (KK with lower body)
→ **Top: Q♦  ·  Mid: K♣ K♠  ·  Bot: J♠ 8♥ 6♦ 4♣**

`4♣ 6♦ 8♥ Q♦ K♣ K♠ A♥` (KK with lone Ace)
→ **Top: A♥  ·  Mid: K♣ K♠  ·  Bot: Q♦ 8♥ 6♦ 4♣**

`9♣ T♦ J♥ Q♠ K♣ A♦ A♠` (AA + broadway body)
→ **Top: K♣  ·  Mid: A♦ A♠  ·  Bot: Q♠ J♥ T♦ 9♣**

> Then **immediately check Sub-rule 2b** — it overrides 2a in a narrow case.

**Fires on:** ~7.2% of hands (KK 3.6% + AA 3.6%).

### Sub-rule 2b — KK/AA rainbow override (very rare, big win)

**Fires only when ALL of these are true:**

1. Pair = KK or AA (we're already inside 2a).
2. **Apply Sub-rule 2a mentally**, then look at the resulting bot. If the 4 leftover cards span all 4 suits → bot is **rainbow**.
3. **DS-bot is geometrically possible:** at least one kicker matches each pair-suit (one ♠ + one ♦ if pair is K♠ K♦, etc.).

**Setting (when fired):** override 2a — put the pair in **bot**.
- **Bot** = both pair cards + the **lowest-rank** kicker matching each pair-suit (gives a 2+2 DS bot).
- **Top** = the **highest-rank** card of the 3 leftover non-pair cards.
- **Mid** = the other 2 leftover cards (often weak — that's OK).

**Worked example:** `K♠ K♦ 3♠ 5♦ 9♥ T♣ J♠`
- Pair = KK ✓, two pair-suits (♠ + ♦) ✓.
- Mental 2a: top=J♠, mid=K♠ K♦, bot=3♠ 5♦ 9♥ T♣ — bot has one of each suit → **rainbow** → trigger.
- DS-bot available: 3♠ matches ♠, 5♦ matches ♦ ✓.
- → **Top: J♠  ·  Mid: T♣ 9♥  ·  Bot: K♠ K♦ 5♦ 3♠** (2♠ + 2♦, DS).
- This swing is worth ~$18K/1000h on this exact hand.

**Fires on:** ~0.27% of hands (~1 in 370). Rare but the per-hand win is dramatic.

### Sub-rule 2c — Pair-to-bot for double-suited (gates)

**Fires only when ALL of these are true** AND you didn't fire 2a/2b:

1. Pair rank is **2–5** OR **T–J–Q** (skip 6-7-8-9 "Goldilocks" — those stay in mid).
2. You hold **exactly one Ace** (no AA, no second pair of any rank).
3. The pair has **two different suits** (e.g. Q♣ + Q♦).
4. **Kickers split balanced** between the pair's two suits. Of the 4 non-pair, non-Ace cards, count how many match each pair-suit. Acceptable: **(1,1), (2,2), (1,3), (3,1)**. Skip lopsided **(2,1) / (1,2)**.

**Setting (when fired):**
- **Top** = the Ace.
- **Bot** = both pair cards + the **lowest** kicker matching each pair-suit (2+2 DS).
- **Mid** = the 2 leftover kickers.

**Worked example:** `3♣ 4♦ 8♦ 9♣ Q♣ Q♦ A♣`
- Pair = QQ ✓, one Ace ✓, two pair-suits ✓.
- Kickers split: clubs {3♣, 9♣} = 2; diamonds {4♦, 8♦} = 2 → (2,2) balanced ✓.
- Lowest club kicker = 3♣; lowest diamond kicker = 4♦.
- → **Top: A♣  ·  Mid: 9♣ 8♦  ·  Bot: Q♣ Q♦ 3♣ 4♦**

**Counter-example (don't fire):** `Q♣ Q♦ A♥ 3♣ 5♣ 4♦ 9♠`
- Kickers: clubs = 2, diamonds = 1, spade = 0 → **(2,1) lopsided** → don't fire 2c. Fall through to 2d / 2e.

**Fires on:** ~2.2% of hands (~1 in 45).

### Sub-rule 2d — J-low defensive (top inversion)

**Fires when ALL of these are true** AND you didn't fire 2a/2b/2c:

1. Max card in the entire hand is **J or lower** (the "weak hand" zone).
2. **Pair rank ≤ 6** OR **pair rank EQUALS the max-card rank**. (Mid-range pairs that are not the max — like 99 in a J-high body — are excluded.)

**Setting (when fired):**
- **Top** = your **LOWEST** singleton (yes, lowest — this inverts the conventional "top = highest" reflex).
- **Mid** = the pair.
- **Bot** = the **4 HIGHEST** non-pair singletons.

**Worked examples:**

`J♥ 9♣ 7♣ 5♦ 5♣ 3♥ 2♠` (J-high, pair = 55)
→ **Top: 2♠  ·  Mid: 5♦ 5♣  ·  Bot: J♥ 9♣ 7♣ 3♥** (bot has 2♣)

`T♣ 8♦ 6♥ 5♣ 4♣ 2♦ 2♠` (T-high, pair = 22)
→ **Top: 4♣  ·  Mid: 2♦ 2♠  ·  Bot: T♣ 8♦ 6♥ 5♣**

`J♥ J♣ 9♦ 7♠ 5♣ 3♥ 2♦` (J-high, pair = JJ — pair == max)
→ **Top: 2♦  ·  Mid: J♥ J♣  ·  Bot: 9♦ 7♠ 5♣ 3♥**

**Why it works:** with max card J-or-lower you'll lose the top tier
most of the time anyway. Conceding top with your weakest card stacks
strong cards into mid + bot, where they earn 2× and 3× the points.

**Fires on:** ~5.7% of hands.

### Sub-rule 2e — Default one-pair play

**Fires when** none of 2a / 2b / 2c / 2d match.

- **Top** = your highest singleton (especially an Ace).
- **Mid** = the pair.
- **Bot** = the remaining 4 singletons.

> ⚠️ The ML model would refine this per-hand for the "single pair with
> a feasible double-suited bot" cases, capturing another ~$215/1000h.
> The default is the safe table play.

**Worked example:** `A♠ Q♣ T♥ 9♣ 8♣ 8♦ 3♠`
- Pair = 88 (Goldilocks zone — stays in mid). 2c excluded (pair rank 8 not in 2-5/T-J-Q list).
- → **Top: A♠  ·  Mid: 8♣ 8♦  ·  Bot: Q♣ T♥ 9♣ 3♠**

**One-pair total:** ~43% of hands across all sub-rules.

---

## Rule 3 — Two pair (never split either pair)

**Fires when** you have exactly two pairs (and no trips, no quads).

**Setting:** never break either pair. Pick from the 3 valid no-split layouts:

| Layout | Top | Mid | Bot |
|---|---|---|---|
| A | 1 kicker | 2 kickers | both pairs (4 cards) |
| B | 1 kicker | higher pair | lower pair + 2 kickers |
| C | 1 kicker | lower pair | higher pair + 2 kickers |

**Pick the layout that maximizes (in this priority order):**
1. Bot is double-suited (2+2) > single-suited (2+1+1) > rainbow > 3+1 > 4-flush.
2. Top rank (Ace > K > Q ...).
3. Mid is paired > offsuit broadway > suited connector > anything else.

**Worked example:** `7♣ 7♦ 8♣ 8♦ J♥ K♠ A♠`
- Two pairs: 88 and 77.
- The naive "suited connector mid + split both pairs" play (top K, mid 8♣ 7♦, bot A J 8 7) **bleeds about $46K/1000h**.
- **Layout A** wins: **Top: A♠  ·  Mid: K♠ J♥  ·  Bot: 8♦ 8♣ 7♦ 7♣** (bot has 2♦ + 2♣, double-suited).

> ⚠️ The ML model captures another **~$634/1000h** on two-pair beyond
> what Rule 3 alone gets. Rule 3 is what to play at the table without
> a computer.

**Fires on:** ~22% of hands.

---

## Rule 4 — Three pair (top = singleton, then one rank check picks mid)

**Fires when** you have exactly three pairs + one singleton.

**Setup (always):** **Top = the singleton.** That keeps all 3 pairs intact.

**Which pair goes to mid?** The decision depends only on your **highest pair's rank**:

| Highest pair | Mid is… | Bot is… |
|---|---|---|
| **AA** | the **AA** (high pair) | the other two pairs |
| **KK / QQ / JJ / TT** | the **MIDDLE pair** | the high pair + the lowest pair |
| **99 or lower** | the **highest pair** | the other two pairs |

**One-line memory hook:** "Is your highest pair K, Q, J, or T? → mid is the **middle** pair. Otherwise → mid is the **highest** pair."

**Worked examples:**

`A♥ A♦ K♥ K♣ Q♦ Q♣ 2♠` (AAA highest)
→ **Top: 2♠  ·  Mid: A♥ A♦  ·  Bot: K♥ K♣ Q♦ Q♣**

`K♥ K♦ Q♥ Q♣ 5♦ 5♣ 2♠` (KK highest → mid = middle pair)
→ **Top: 2♠  ·  Mid: Q♥ Q♣  ·  Bot: K♥ K♦ 5♦ 5♣**

`T♥ T♦ 9♥ 9♣ 5♦ 5♣ 2♠` (TT highest → mid = middle pair)
→ **Top: 2♠  ·  Mid: 9♥ 9♣  ·  Bot: T♥ T♦ 5♦ 5♣**

`9♥ 9♦ 5♥ 5♣ 3♦ 3♣ 2♠` (99 highest → boundary flips: mid = highest)
→ **Top: 2♠  ·  Mid: 9♥ 9♦  ·  Bot: 5♥ 5♣ 3♦ 3♣**

**Fires on:** ~1.9% of hands.

---

## Rule 5 — Pure trips (3 of one rank, no other pair, no quads)

**Fires when** you have trips of any rank and no second pair.

**Setup (always):**
- **Mid** = 2 of the 3 trip cards (paired mid).
- The third trip card goes to **either top or bot** — never split out alone.
- The 4 non-trip cards are your kickers.

### Step 1 — Where does the third trip card go?

| Trip rank | Third trip goes to | Special case |
|---|---|---|
| **AAA** | **Top** | None — always top |
| **KKK** | **Top** | If you also have an Ace, put **Ace on top + third K to bot** |
| **QQQ** | **Top** | If you have **J, K, or A in kickers**, put the highest such card on top + third Q to bot |
| **Trip J or lower** | **Always BOT.** Highest non-trip card goes on top. | None |

### Step 2 — Which trip joins bot? (suit priority)

Used only when Step 1 sent the third trip to bot.

You're aiming for the bot to be **2+2 double-suited**. Look at the 3 kickers heading to bot:

| Kicker pattern | What it means |
|---|---|
| **Two share a suit, one different** | "two-and-one" (most common) |
| **All different suits** | "rainbow kickers" |
| **All same suit** (rare) | gives a 4-flush trap if not careful |

**Then pick the trip card whose suit gives the best bot:**

| Bot shape | When you get it | Quality |
|---|---|---|
| **2+2 DS** ✓ best | Trip suit matches the **lone (singleton)** kicker | two flush draws |
| **2+1+1 SS** OK | Trip suit fills out a rainbow-kicker spot | one flush draw |
| **3+1** ✗ avoid | Trip suit matches the **kicker pair suit** | third suited card is dead |

**Rule of thumb:** **never let the third trip's suit equal the kicker-pair suit.** When in doubt, pick the trip whose suit appears **least often** in the kickers.

### Worked examples (one per case)

**AAA always top:** `2♦ 4♣ 7♥ J♠ A♣ A♦ A♥`
→ **Top: A♣  ·  Mid: A♦ A♥  ·  Bot: J♠ 7♥ 4♣ 2♦**

**KKK no Ace → third K on top:** `4♣ 7♦ 9♥ Q♠ K♣ K♦ K♠`
→ **Top: K♣  ·  Mid: K♦ K♠  ·  Bot: Q♠ 9♥ 7♦ 4♣**

**KKK with Ace → Ace on top, K to bot:** `4♣ 7♦ 9♥ A♥ K♣ K♦ K♠`
- Top = A♥. Bot kickers (4♣ 7♦ 9♥) are rainbow. Pick K♣ (or K♦) — both give SS. K♠ gives rainbow (worst).
- → **Top: A♥  ·  Mid: K♦ K♠  ·  Bot: K♣ 9♥ 7♦ 4♣**

**QQQ with J kicker → J on top:** `2♥ 4♣ 7♦ J♠ Q♣ Q♦ Q♥`
→ **Top: J♠  ·  Mid: Q♦ Q♥  ·  Bot: Q♣ 7♦ 4♣ 2♥**

**Trip 7, finds a 2+2:** `3♥ 5♥ 8♣ Q♣ 7♣ 7♦ 7♠`
- Top = Q♣. Bot kickers (3♥ 5♥ 8♣): suits ♥♥♣ → "two-and-one" (pair=♥, singleton=♣).
- 7♣ → bot 2♥ + 2♣ = **DS** ✓. 7♦ / 7♠ → SS.
- → **Top: Q♣  ·  Mid: 7♦ 7♠  ·  Bot: 7♣ 8♣ 5♥ 3♥**

**Trip J, low kickers (no DS available):** `2♣ 4♣ 6♥ 9♦ J♣ J♦ J♠`
- Top = 9♦. Bot kickers (2♣ 4♣ 6♥): suits ♣♣♥ → "two-and-one" (pair=♣, singleton=♥).
- J♣ → 3+1 ✗ (third club is dead). J♦ → SS. J♠ → SS.
- → **Top: 9♦  ·  Mid: J♣ J♠  ·  Bot: J♦ 6♥ 4♣ 2♣**

> ⚠️ The ML model captures another **~$45/1000h** on trips beyond
> Rule 5. Smaller gap than two-pair / pair, but real.

**Fires on:** ~5.5% of hands.

---

## Rule 6 — Trips + pair (split the trips, keep the pair)

**Fires when** you have 3 of one rank + 2 of another + 2 leftover kickers.

**Key idea:** the trips MUST split (mid only fits 2 cards). Keep the pair intact. Two sane layouts:

| Layout | Top | Mid | Bot |
|---|---|---|---|
| A | 1 kicker | 2 of the 3 trip cards (paired mid) | original pair + 1 trip + 1 kicker |
| B | 1 kicker | 1 trip + 1 kicker | original pair + 2 trips (4 cards = 2 pairs) |

**Pick by:** 1) bot DS > SS > rainbow, 2) top rank, 3) slight preference for Layout A (paired mid is robust).

**Worked example:** `4♣ T♦ T♥ T♠ J♣ J♦ Q♦`
- Trips = TTT, pair = JJ, kickers = 4♣ + Q♦.
- **Layout A**: **Top: Q♦  ·  Mid: T♠ T♥ (paired mid)  ·  Bot: J♦ J♣ T♦ 4♣** (bot has 2♦ + 2♣, JJ + T as 2-pair anchor).

**Fires on:** ~3% of hands.

---

## Rule 7 — Two trips (3+3+1)

**Fires when** you have 3 of one rank + 3 of another + 1 singleton. ~0.07% of hands (~1 in 1,400).

**Setting:**
- **Top** = a **HIGH-trip** card whose suit also appears in the **LOW** trip's suits.
- **Mid** = 2 of the 3 LOW-trip cards (paired mid).
- **Bot** = the 2 remaining HIGH-trip cards + 1 LOW-trip card + the singleton. Pick the LOW card whose suit best builds DS.

**Worked example:** `T♣ T♦ T♥ 5♣ 5♦ 5♥ K♠`
- High = TTT, low = 555, singleton = K♠. L-suits = {♣, ♦, ♥}.
- Top = T♣ (any T qualifies — pick canonical).
- Mid = 5♦ + 5♥. Bot = T♦ T♥ + 5♣ + K♠ (pick to maximize DS).
- → **Top: T♣  ·  Mid: 5♦ 5♥  ·  Bot: T♦ T♥ 5♣ K♠**

---

## Rule 8 — Trips + two pairs (3+2+2)

**Fires when** you have 1 trip + 2 different pairs. ~0.11% of hands (~1 in 875).

**Setting:**
- **Top** = a trip-card at a suit not shared with either pair (suit-aware split). If no such suit exists, pick the canonical first.
- If **trip-rank ≤ 4** → mid = LOW pair, bot = 2 trip-leftovers + HIGH pair.
- Else (**trip-rank ≥ 5**) → mid = HIGH pair, bot = 2 trip-leftovers + LOW pair.

**Worked example (trip ≥ 5):** `T♣ T♦ T♥ Q♣ Q♦ 8♥ 8♠`
→ **Top: T♣  ·  Mid: Q♣ Q♦  ·  Bot: T♦ T♥ 8♥ 8♠**

**Worked example (trip ≤ 4):** `3♣ 3♦ 3♥ K♣ K♦ Q♥ Q♠`
→ **Top: 3♥  ·  Mid: Q♥ Q♠  ·  Bot: 3♣ 3♦ K♣ K♦**

---

## Rule 9 — Plain quads (4+1+1+1)

**Fires when** you have 4 of one rank + 3 different singletons (no second pair). ~0.24% of hands (~1 in 420).

**Setting:**
- **Top** = your highest singleton.
- **Mid** = the 2 quad cards at suits **NOT used by any singleton**.
- **Bot** = the other 2 quad cards + the 2 lower singletons.

**Worked example:** `9♣ 9♦ 9♥ 9♠ A♣ K♣ 7♥`
- Singleton-suits = {♣, ♥}. Non-singleton-suits = {♦, ♠}.
- → **Top: A♣  ·  Mid: 9♦ 9♠  ·  Bot: 9♣ 9♥ K♣ 7♥** (2♣ + 2♥ DS).

> Edge case: if 3 singletons span 3 different suits, only 1 suit is
> "non-singleton" — you can't pick 2 quads at non-singleton suits.
> Fall back to any 2 quads in mid. The rare case where the rule
> doesn't cleanly apply.

---

## Rule 10 — Quads + pair (4+2+1)

**Fires when** you have a quad PLUS a pair. ~0.057% of hands (~1 in 1,750).

**Setting:**
- **Top** = the singleton (the one card that's neither part of the quad nor the pair).
- **Mid** = the 2 quad cards whose **suits are NOT the pair's suits.**
- **Bot** = the other 2 quad cards + both pair cards (perfectly double-suited).

**Worked example:** `A♣ A♦ A♥ A♠ K♣ K♦ 2♠`
- Pair-suits = {♣, ♦}. Non-pair-suits = {♥, ♠}.
- → **Top: 2♠  ·  Mid: A♥ A♠  ·  Bot: A♣ A♦ K♣ K♦** (2♣ + 2♦ DS).

---

## The common thread (one paragraph)

> **The bottom tier is the most valuable, and double-suited (2+2) bots
> win against the realistic mixture by $5K–$15K per 1,000 hands.**
> Whenever a pair (or trip) can serve as a suit anchor for the bot —
> meaning the pair has two different suits AND your kickers can fill
> the DS structure — putting that pair in the bot is usually correct.
> Exceptions: mid pairs (6-9), which are strong enough in mid that the
> move isn't worth it; and KK / AA, which are valuable enough in mid
> that the trade flips back. The mid tier is forgiving (Hold'em rules,
> can use 0/1/2 hole cards), so giving up a "pair in mid" loses less
> than you'd think. The bot is unforgiving (Omaha 2+3 is rigid), so
> getting the bot to DS shape is high-value.

---

## What this guide leaves on the table

These four shapes are handled by an ML decision tree (`v44_dt`) in the
production rule chain — a model with ~2.25 million leaves that no
human can apply at the table. For these, the rule above gives you a
"good-enough" play; the ML model captures additional edge.

| Shape | This guide uses | ML edge over this guide | Why no rule yet |
|---|---|---:|---|
| No pair (Rule 1) | Default play | **~$355/1000h** | Multi-feature signal — no single boundary |
| One pair, default cases (Rule 2e) | Default play | **~$215/1000h** | Per-hand cell routing needs 107 features |
| Two pair (Rule 3) | Never-split heuristic | **~$634/1000h** | Adaptive split logic resists single-rule capture |
| Pure trips (Rule 5) | Step 1+2 heuristic | **~$45/1000h** | Diminishing returns past Rule 5 |

The ongoing project work is targeting these gaps. Currently waiting
on a 15-hour oracle run that will determine whether a new model
(`v49_a2`) ships as the next champion.

---

*Built from `STRATEGY_GUIDE.md` Part 6 (the canonical rule set,
Sessions 24–42 ship history) and the production chain
`strategy_v56_trips_hybrid.py` → `v55` → `v54` → `v53` → `v52`.
Same content as `TEMP_PLAY_GUIDE.md`, reorganized in shape order
(no pair → 1 pair → ... → quads + pair) so the document reads
top-to-bottom without back-references. Safe to delete or rewrite.*
