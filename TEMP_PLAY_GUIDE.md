# Taiwanese Poker — Player Guide (TEMP / scratch read)

> **What this is:** a compact "run-through" version of the solver's
> human-memorizable rule set. Walk top-to-bottom for a brand-new hand,
> stop at the first rule that fires, do what it says.
>
> **Status:** scratch document for reading. NOT the canonical strategy
> guide (`STRATEGY_GUIDE.md`). Safe to delete or rewrite — nothing else
> depends on it.
>
> **Honesty disclosures up front:**
> 1. Three of the most important hand categories (**trips**, **two pair**,
>    and **single pair where a double-suited bot is reachable**) are
>    handled by an ML model in the production chain, not by a human-
>    runnable rule. For those, this guide gives you a "good-enough"
>    default to play at the table — the ML model captures another
>    $200–$700/1000h of edge that no rule has matched.
> 2. The production rule chain ranks ~$348/1000h behind the ML model on
>    the realistic mixture. So this guide gets you most of the way, but
>    not all the way, to the solver's best play.
> 3. Edge over the "naive obvious play" baseline (`v8_hybrid`):
>    **about +$1,015/1000h** when you apply Rules 1–6 cleanly.

---

## Step 0 — How to read your hand

Sort your 7 cards by rank (high to low) and look for the strongest
"shape." The categories are mutually exclusive — pick the one that
matches.

| Shape (look for the most specific match) | What you have |
|---|---|
| **Quads + pair** (4+2+1) | 4 of one rank + 2 of another + 1 leftover |
| **Plain quads** (4+1+1+1) | 4 of one rank + 3 different singletons |
| **Two trips** (3+3+1) | 3 of one rank + 3 of another + 1 leftover |
| **Trips + two pair** (3+2+2) | 3 of one rank + 2 of two different others |
| **Trips + pair** (3+2+1+1) | 3 of one rank + 2 of another + 2 leftovers |
| **Pure trips** (3+1+1+1+1) | 3 of one rank, no other multi |
| **Three pair** (2+2+2+1) | 3 different pairs + 1 singleton |
| **Two pair** (2+2+1+1+1) | 2 different pairs + 3 leftovers |
| **One pair** (2+1+1+1+1+1) | 1 pair + 5 leftovers |
| **No pair** | 7 distinct ranks |

Then jump to the matching rule below. There are 10 numbered rules,
plus a default for "no rule fires."

---

## The decision tree (first match wins)

```
Have quads + pair?           → Rule 8
Have plain quads?            → Rule 9a
Have two trips?              → Rule 9b
Have trips + two pair?       → Rule 9c
Have trips + pair?           → Rule 3
Have pure trips?             → Rule 6
Have three pair?             → Rule 7
Have two pair?               → "Two pair default" (Rule 2 idea — see notes)
Have one pair?
   • pair is KK or AA?       → Rule 4 (then check Rule 5 override)
   • pair-rank ≤ 6 OR pair == max-card AND max ≤ J?
                             → Rule 10 (defensive)
   • pair fits Rule 1's 4 gates?
                             → Rule 1
   • else                    → Default play
Have no pair?                → Default play
```

> **Tip:** if you ever feel stuck mid-hand, the **default play** at the
> bottom of this guide is always a legal fallback. It scores worse than
> the rules but better than random panic.

---

## Rule 1 — Single pair, pair-to-bot for double-suited

**Fires only when ALL of these are true:**

1. Pair rank is **2–5** OR **T–J–Q** (skip the 6-7-8-9 "Goldilocks" zone — those stay in mid).
2. You hold **exactly one Ace** (no AA, no second pair of any rank).
3. The pair has **two different suits** (e.g. Q♣ + Q♦, not Q♣ + Q♣ — same-suit pairs can't anchor a DS bot).
4. **Kickers split balanced** between the pair's two suits. Of the 4 non-pair, non-Ace cards, count how many match each pair-suit. Acceptable splits: **(1,1), (2,2), (1,3), (3,1)**. Skip lopsided **(2,1) / (1,2)**.

**Setting (when fired):**
- **Top** = the Ace
- **Bot** = both pair cards + the **lowest** kicker matching each pair-suit (gives a 2+2 DS bot)
- **Mid** = the 2 leftover kickers

**Worked example:** `3♣ 4♦ 8♦ 9♣ Q♣ Q♦ A♣`
- Pair = QQ ✓, one Ace ✓, two pair-suits ✓.
- Kickers split: clubs {3♣, 9♣} = 2; diamonds {4♦, 8♦} = 2 → **(2,2) balanced** ✓.
- Lowest club kicker = 3♣; lowest diamond kicker = 4♦.
- → **Top: A♣  ·  Mid: 9♣ 8♦  ·  Bot: Q♣ Q♦ 3♣ 4♦** (bot is 2♣ + 2♦, double-suited).

**Counter-example (DON'T fire):** `Q♣ Q♦ A♥ 3♣ 5♣ 4♦ 9♠`
- Kickers: clubs {3♣, 5♣} = 2; diamond {4♦} = 1; spade {9♠} = 0 → **(2,1) lopsided** → don't fire.
- Fall back to default play (pair in mid).

**Fires on:** ~2.2% of hands (~1 in 45).

---

## Rule 2 — Two pairs: never split either pair

**Fires whenever you have exactly two pairs** (no trips, no quads).

**Setting:** never break either pair. Three valid layouts:

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
- The naive "suited connector mid + split both pairs" play (top K, mid 8♣7♦, bot A J 8 7) **bleeds about $46K/1000h** on this exact hand.
- **Layout A** wins: **Top: A♠  ·  Mid: K♠ J♥  ·  Bot: 8♦ 8♣ 7♦ 7♣** (bot has 2♦+2♣, double-suited, both pairs intact).

> ⚠️ **Note on production:** the latest research shows the two-pair
> category gains another **~$634/1000h** when you let an ML model pick
> per-hand instead of using Rule 2 alone. Rule 2 is what to play at the
> table without a computer; the ML model lives in `strategy_v44_dt.py`
> and is the production champion for this category.

**Fires on:** ~22% of hands.

---

## Rule 3 — Trips + pair: split the trips, keep the pair

**Fires when you have 3 of one rank + 2 of another + 2 leftover kickers.**

**Key idea:** the trips MUST split (mid only fits 2 cards). Keep the pair intact. Two sane layouts:

| Layout | Top | Mid | Bot |
|---|---|---|---|
| A | 1 kicker | 2 of the 3 trip cards (paired mid) | original pair + 1 trip + 1 kicker |
| B | 1 kicker | 1 trip + 1 kicker | original pair + 2 trips (4 cards = 2 pairs) |

**Pick by:** 1) bot DS > SS > rainbow, 2) top rank, 3) slight preference for Layout A (paired mid is robust).

**Worked example:** `4♣ T♦ T♥ T♠ J♣ J♦ Q♦`
- Trips = TTT, pair = JJ, kickers = 4♣ + Q♦.
- **Layout A**: **Top: Q♦  ·  Mid: T♠ T♥ (paired mid)  ·  Bot: J♦ J♣ T♦ 4♣** (bot is 2♦+2♣, double-suited, JJ + T as 2-pair anchor).

**Fires on:** ~3% of hands.

---

## Rule 4 — Premium pair (KK or AA): pair stays in mid

**Fires whenever your pair is KK or AA** (and you don't have quads).

**Setting:**
- **Mid** = both pair cards (KK or AA), intact
- **Top** = the highest non-pair card you hold (the Ace if KK + lone Ace; otherwise the next-highest singleton)
- **Bot** = the remaining 4 cards

**Worked examples:**

`4♣ 6♦ 8♥ J♠ Q♦ K♣ K♠` (KK with lower body)
- → **Top: Q♦  ·  Mid: K♣ K♠  ·  Bot: J♠ 8♥ 6♦ 4♣**

`4♣ 6♦ 8♥ Q♦ K♣ K♠ A♥` (KK with lone Ace)
- → **Top: A♥  ·  Mid: K♣ K♠  ·  Bot: Q♦ 8♥ 6♦ 4♣**

`9♣ T♦ J♥ Q♠ K♣ A♦ A♠` (AA + broadway body)
- → **Top: K♣  ·  Mid: A♦ A♠  ·  Bot: Q♠ J♥ T♦ 9♣**

> ⚠️ **AA-with-low-body edge case** (e.g. `2♣ 3♦ 4♥ 5♠ 6♣ A♥ A♠`): the
> ML model picks `top=2♣` to give the bot a wheel-style straight draw.
> For human play, follow Rule 4 as written — the EV difference is small.

**Then check Rule 5 immediately** — it overrides Rule 4 in a narrow case.

**Fires on:** ~7.2% of hands (KK 3.6% + AA 3.6%).

---

## Rule 5 — KK/AA Rainbow override (very rare, big win when it fires)

**Fires only when ALL of these are true:**

1. Pair = KK or AA (we're already inside Rule 4 territory).
2. The pair has two different suits (always true for KK / AA — stated for completeness).
3. **Apply Rule 4 mentally**, then look at the resulting bot. If the 4 leftover cards span all 4 suits → bot is **rainbow**.
4. **DS-bot is geometrically possible:** at least one kicker matches each pair-suit.

**Setting (when fired):** override Rule 4 — put the pair in **bot**.
- **Bot** = both pair cards + the **lowest-rank** kicker matching each pair-suit (2+2 DS)
- **Top** = the **highest-rank** card of the 3 leftover non-pair cards
- **Mid** = the other 2 leftover cards (often weak — that's OK)

**Worked example:** `K♠ K♦ 3♠ 5♦ 9♥ T♣ J♠`
- Pair = KK ✓, two pair-suits (♠ + ♦) ✓.
- Mental Rule 4: top=J♠, mid=K♠ K♦, bot=3♠ 5♦ 9♥ T♣ — bot has one of each suit → **rainbow** → trigger.
- DS-bot available: 3♠ matches ♠, 5♦ matches ♦ ✓.
- → **Top: J♠  ·  Mid: T♣ 9♥  ·  Bot: K♠ K♦ 5♦ 3♠** (2♠ + 2♦, DS).
- This swing is worth ~$18K/1000h on this single hand.

**Fires on:** ~0.27% of hands (~1 in 370). Rare but the per-hand wins are dramatic.

---

## Rule 6 — Pure trips: 2 of the 3 trip cards always go to mid

**Fires whenever you have trips of any rank (and no second pair, no quads).**

**The Setup (always):**
- **Mid** = 2 of the 3 trip cards (paired mid).
- The third trip card goes to **either top or bot** — never split out alone.
- The 4 non-trip cards (your kickers) fill the rest.

### Step 1 — Where does the third trip go?

| Trip rank | Third trip goes to | Special case |
|---|---|---|
| **AAA** | **Top** | None — always top |
| **KKK** | **Top** | If you also have an Ace, put **Ace on top + third K to bot** |
| **QQQ** | **Top** | If you have **J, K, or A in kickers**, put the highest such card on top + third Q to bot |
| **Trip J or lower** | **Always BOT.** Highest non-trip card goes on top. | None |

### Step 2 — Which of the 3 trip cards joins bot? (Suit priority)

(Used only when Step 1 sent the third trip to bot.)

You're trying to make the bot **2+2 double-suited**. Look at the 3 kickers heading to bot:

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

### Worked examples (one per trip-rank "case")

**AAA always top:** `2♦ 4♣ 7♥ J♠ A♣ A♦ A♥`
→ **Top: A♣  ·  Mid: A♦ A♥  ·  Bot: J♠ 7♥ 4♣ 2♦**

**KKK no Ace → third K on top:** `4♣ 7♦ 9♥ Q♠ K♣ K♦ K♠`
→ **Top: K♣  ·  Mid: K♦ K♠  ·  Bot: Q♠ 9♥ 7♦ 4♣**

**KKK with Ace → Ace on top, K to bot:** `4♣ 7♦ 9♥ A♥ K♣ K♦ K♠`
- Top = A♥. Bot kickers (4♣ 7♦ 9♥) are rainbow.
- Pick K♣ (or K♦) — both give SS. K♠ gives rainbow (worst).
- → **Top: A♥  ·  Mid: K♦ K♠  ·  Bot: K♣ 9♥ 7♦ 4♣**

**QQQ with J kicker → J on top:** `2♥ 4♣ 7♦ J♠ Q♣ Q♦ Q♥`
→ **Top: J♠  ·  Mid: Q♦ Q♥  ·  Bot: Q♣ 7♦ 4♣ 2♥**

**Trip 7, finds a 2+2:** `3♥ 5♥ 8♣ Q♣ 7♣ 7♦ 7♠`
- Top = Q♣ (highest non-trip). Bot kickers (3♥ 5♥ 8♣): suits ♥♥♣ → "two-and-one" (pair=♥, singleton=♣).
- 7♣ → bot 2♥ + 2♣ = **DS** ✓. 7♦ / 7♠ → SS.
- → **Top: Q♣  ·  Mid: 7♦ 7♠  ·  Bot: 7♣ 8♣ 5♥ 3♥**

**Trip J, low kickers (no DS available):** `2♣ 4♣ 6♥ 9♦ J♣ J♦ J♠`
- Top = 9♦. Bot kickers (2♣ 4♣ 6♥): suits ♣♣♥ → "two-and-one" (pair=♣, singleton=♥).
- J♣ → 3+1 ✗ (third club is dead). J♦ → SS. J♠ → SS.
- → **Top: 9♦  ·  Mid: J♣ J♠  ·  Bot: J♦ 6♥ 4♣ 2♣**

**Fires on:** ~5.5% of hands.

---

## Rule 7 — Three pair: top = singleton, then one rank check picks mid

**Fires whenever you have exactly three pairs + one singleton.**

**Setup (always):** **Top = the singleton.** That keeps all 3 pairs intact.

### Which pair goes to mid?

The decision depends only on your **highest pair's rank**:

| Highest pair | Mid is… | Bot is… |
|---|---|---|
| **AA** | the **AA** (high pair) | the other two pairs |
| **KK / QQ / JJ / TT** | the **MIDDLE pair** | the high pair + the lowest pair |
| **99 or lower** | the **highest pair** | the other two pairs |

**One-line memory hook:** "Is your highest pair K, Q, J, or T? → mid is the **middle** pair. Otherwise → mid is the **highest** pair."

### Worked examples

`A♥ A♦ K♥ K♣ Q♦ Q♣ 2♠` (AAA highest)
→ **Top: 2♠  ·  Mid: A♥ A♦  ·  Bot: K♥ K♣ Q♦ Q♣**

`K♥ K♦ Q♥ Q♣ 5♦ 5♣ 2♠` (KK highest → mid = middle pair)
→ **Top: 2♠  ·  Mid: Q♥ Q♣  ·  Bot: K♥ K♦ 5♦ 5♣**

`T♥ T♦ 9♥ 9♣ 5♦ 5♣ 2♠` (TT highest → mid = middle pair)
→ **Top: 2♠  ·  Mid: 9♥ 9♣  ·  Bot: T♥ T♦ 5♦ 5♣**

`9♥ 9♦ 5♥ 5♣ 3♦ 3♣ 2♠` (99 highest → boundary flips: mid = highest)
→ **Top: 2♠  ·  Mid: 9♥ 9♦  ·  Bot: 5♥ 5♣ 3♦ 3♣**

**Fires on:** ~1.9% of hands. Lift over the prior heuristic: **+$43/1000h**.

---

## Rule 8 — Quads + pair: non-pair-suit quads to mid

**Fires whenever you have a quad PLUS a pair (4+2+1).** ~0.057% of hands (~1 in 1,750).

**Setup:**
- **Top** = the singleton.
- **Mid** = the 2 quad cards whose **suits are NOT the pair's suits.**
- **Bot** = the other 2 quad cards + both pair cards (perfectly double-suited).

**Worked example:** `A♣ A♦ A♥ A♠ K♣ K♦ 2♠`
- Pair-suits = {♣, ♦}. Non-pair-suits = {♥, ♠}.
- → **Top: 2♠  ·  Mid: A♥ A♠  ·  Bot: A♣ A♦ K♣ K♦** (2♣ + 2♦, perfect DS).

---

## Rule 9 — Three sub-rules for rare composite shapes

### Rule 9a — Plain quads (4+1+1+1)

**Setup:**
- **Top** = your highest singleton.
- **Mid** = the 2 quad cards at suits **NOT used by any singleton.**
- **Bot** = the other 2 quad cards + the 2 lower singletons.

**Example:** `9♣ 9♦ 9♥ 9♠ A♣ K♣ 7♥` — singleton-suits = {♣, ♥}. Non-singleton-suits = {♦, ♠}.
→ **Top: A♣  ·  Mid: 9♦ 9♠  ·  Bot: 9♣ 9♥ K♣ 7♥** (2♣ + 2♥ DS).

> Edge case: if all 3 singletons have different suits AND the quad's
> 4th suit is "missing" from singletons (1 non-sing-suit only), you
> can't make a clean DS — fall back to any 2 quads in mid.

### Rule 9b — Two trips (3+3+1, ~0.07% of hands)

**Setup:**
- **Top** = a **HIGH-trip** card whose suit also appears in the **LOW** trip's suits.
- **Mid** = 2 of the 3 LOW-trip cards (paired mid).
- **Bot** = the 2 remaining HIGH-trip cards + 1 LOW-trip card + the singleton. Pick the LOW card whose suit best builds DS.

**Example:** `T♣ T♦ T♥ 5♣ 5♦ 5♥ K♠` — high = TTT, low = 555, singleton = K♠.
- L-suits = {♣, ♦, ♥}. Top = T♣ (any T qualifies — pick canonical).
- Mid = 5♦ + 5♥. Bot = T♦ T♥ + 5♣ + K♠ (pick to maximize DS).
- → **Top: T♣  ·  Mid: 5♦ 5♥  ·  Bot: T♦ T♥ 5♣ K♠**

### Rule 9c — Trips + two pairs (3+2+2, ~0.11%)

**Setup:**
- **Top** = a trip-card at the suit not shared with either pair (suit-aware split).
- If **trip-rank ≤ 4** → mid = LOW pair, bot = 2 trip-leftovers + HIGH pair.
- Else (**trip-rank ≥ 5**) → mid = HIGH pair, bot = 2 trip-leftovers + LOW pair.

**Example (trip ≥ 5):** `T♣ T♦ T♥ Q♣ Q♦ 8♥ 8♠`
→ **Top: T♣  ·  Mid: Q♣ Q♦  ·  Bot: T♦ T♥ 8♥ 8♠**

**Example (trip ≤ 4):** `3♣ 3♦ 3♥ K♣ K♦ Q♥ Q♠`
→ **Top: 3♥  ·  Mid: Q♥ Q♠  ·  Bot: 3♣ 3♦ K♣ K♦**

---

## Rule 10 — J-low single-pair defensive (top inversion)

**Fires when ALL of these are true:**

1. You have exactly one pair (no trips, no quads, no second pair).
2. **Max card in the entire hand is J or lower** (the "weak hand" zone).
3. **Pair rank ≤ 6** OR **pair rank EQUALS the max-card rank**. (The middle zone — pair high but not max — is excluded.)

**Setting (when fired):**
- **Top** = your **LOWEST** singleton (yes, lowest — this inverts the conventional "top = highest" reflex)
- **Mid** = the pair
- **Bot** = the **4 HIGHEST** non-pair singletons

**Worked examples:**

`J♥ 9♣ 7♣ 5♦ 5♣ 3♥ 2♠` (J-high, pair = 55)
→ **Top: 2♠  ·  Mid: 5♦ 5♣  ·  Bot: J♥ 9♣ 7♣ 3♥** (bot has 2♣)

`T♣ 8♦ 6♥ 5♣ 4♣ 2♦ 2♠` (T-high, pair = 22)
→ **Top: 4♣  ·  Mid: 2♦ 2♠  ·  Bot: T♣ 8♦ 6♥ 5♣**

`J♥ J♣ 9♦ 7♠ 5♣ 3♥ 2♦` (J-high, pair = JJ — pair == max)
→ **Top: 2♦  ·  Mid: J♥ J♣  ·  Bot: 9♦ 7♠ 5♣ 3♥**

**Why it works:** if the highest card you hold is a J or lower, you'll
lose the top tier most of the time anyway. Conceding the top with your
weakest card stacks the strong cards into mid + bot, where they earn
2× and 3× the points. The pair stays in mid as the structural anchor.

**Fires on:** ~5.7% of hands. Lift over the prior heuristic: **+$48/1000h**.

---

## Default — when no rule fires

For every hand not covered above (single pair outside Rules 1/4/5/10 gates, no-pair "high-only" hands, and a few rare composite shapes other than quads-pair):

- **Top** = your highest singleton (especially an Ace if you have one)
- **Mid** = your strongest 2-card Hold'em combo from what remains (pair > broadway > suited connector)
- **Bot** = the rest, ideally with at least 2 of one suit for an Omaha flush draw

This is the "obvious" play. It loses to the ML model on these hand
types — high_only by ~$355/1000h, two_pair by ~$634/1000h, single
pair (PBOT-DS feasible) by ~$215/1000h, trips by ~$45/1000h — but
it's a clean, safe fallback at the table.

---

## The one-paragraph cheat sheet

> **Don't break pairs.** With one pair + an Ace + balanced suits + a
> low or T-J-Q pair, put the Ace on top and the pair in a double-suited
> bot — except KK / AA which always stay in mid (then check the
> rare rainbow override, where you drop KK/AA to the bot for a 2+2 DS
> instead). With two pairs, never split either; pick the layout that
> double-suits the bot. With trips + a pair, split the trips 2-and-1
> and keep the original pair intact. With pure trips, two of the three
> trip cards always pair the mid — the third goes top for trip A/K/Q
> (with Q only if no J/K/A in kickers, and K only if no Ace) and bot
> for trip J or lower; when it goes bot, pick the trip-suit that
> avoids the 3+1 trap and ideally hits 2+2 DS. With three pairs, top
> is the singleton; mid is the **middle** pair if your highest pair is
> T/J/Q/K, otherwise mid is the **highest** pair. With quads + pair,
> top is the singleton, mid is the quad cards at the non-pair suits
> (this guarantees a DS bot). With plain quads + 3 singletons, same
> idea — mid is the quad cards at non-singleton suits.
> **DEFENSIVE — when your max card is J-or-lower AND you have exactly
> one pair AND the pair is rank-6-or-lower OR the pair IS your max
> card, INVERT the top: top is the LOWEST singleton, mid is the pair,
> bot is the 4 highest non-pair singletons.** For everything else,
> high card on top, decent cards in mid, rest to bot — and accept that
> you're leaving some EV on the table that only the ML model can find.

---

## What this guide does NOT cover

These categories are handled by an ML decision tree (`v44_dt`) in the
production rule chain — a model with ~2.25 million leaves that no
human can apply at the table. For those, the default play above is
your best bet without a computer.

| Category | Model edge over default | Why no rule yet |
|---|---:|---|
| **High-only (no pair)** | ~$355/1000h | Multi-feature signal — no single boundary |
| **Two pair** | ~$634/1000h | Adaptive split logic resists single-rule capture |
| **Single pair (PBOT-DS feasible)** | ~$215/1000h | Per-hand cell routing needs 107 features |
| **Pure trips** | ~$45/1000h | Diminishing returns past Rule 6 |
| **Trips + pair** | ~$10–20/1000h | Rule 3 captures most of it |

The ongoing project work is targeting these gaps. Currently waiting
on a 15-hour oracle run that will determine whether a new model
(`v49_a2`) ships as the next champion.

---

*Built from `STRATEGY_GUIDE.md` Part 6 (the canonical rule set,
Sessions 24–42 ship history) and the production chain
`strategy_v56_trips_hybrid.py` → `v55` → `v54` → `v53` → `v52`. This
is a temp scratch file — safe to delete or rewrite.*
