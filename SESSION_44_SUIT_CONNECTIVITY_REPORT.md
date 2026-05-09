# Session 44 — Bot Suit × Connectivity Priority (methodology investigation)

_Generated: 2026-05-09_

## TL;DR

User devil's-advocate questioning of Rule 10's bot construction (Session 43 ship)
exposed a methodology flaw in the project's existing "DS > SS > rainbow > 3+1 >
4-flush" priority claim. Session 44 ran two drills to investigate, the second of
which (within-hand pairwise) eliminated the confounder and produced a
**definitive priority hierarchy**:

> **Suit dominates connectivity at every level.** DS-scattered (worst DS)
> beats every non-DS class within-hand, including SS-run-4 (best SS).
> The closest non-DS class is SS-run-2+strays at +$111/1000h margin —
> essentially tied but DS still wins. There is **no tipping point** where
> non-DS suit beats DS within-hand.

Within DS, connectivity matters but less than suit dominance: DS-run-4 vs
DS-scattered = +$2.5K, while DS-vs-SS-at-run-4 = +$4.5K.

**No new rule shipped this session.** v40b remains production. The findings
inform a future "Rule 10 v2" that incorporates suit-aware bot construction —
queued for Session 45+ with the user's specific direction (apply suit
dominance to J-low pair and J-low two_pair, testing whether the pair anchor
should be broken to enable DS bot).

## What was tested

User raised two devil's-advocate challenges to Session 43's findings:

1. The shipped Rule 10 puts the pair in mid and the 4 highest singletons in
   bot — with NO suit-aware bot construction. Was suit-aware bot
   construction (e.g., picking different singletons to enable DS bot)
   leaving EV on the table?

2. The methodology rule "DS > SS > rainbow > 3+1 > 4-flush" came from the
   trips territory (Rule 6 Step 2 + Session 40 connectivity probe). It had
   never been head-to-head tested in J-low pair or J-low no-pair populations.
   Where do connectivity tiers (run-4, one-gap-4, run-3+stray, etc.) fit in
   the hierarchy?

## Drill #1: cross-product priority (CONFOUNDED)

`analysis/scripts/drill_bot_suit_run_priority.py` — for each hand, classified
each of the 105 settings by (suit_class × connectivity_class), found the best
EV per achievable class, aggregated mean regret across hands.

**5 suit classes:** DS (2+2), SS (2+1+1), Rainbow (1+1+1+1), 3+1, 4-flush (4+0)
**7 connectivity classes:** run-4, one-gap-4, two-gap-4, run-3+stray,
two-runs-2, run-2+strays, scattered (defined by adjacency-pattern partition
on the 4 sorted bot ranks)

Cross product = 35 base classes per population.

### Findings (preliminary, with caveats)

The drill produced a 5×7 matrix per population (J-low no-pair + J-low pair).
Headline cells from no-pair pop:

| Class | Mean regret ($/1000h) |
|---|---:|
| DS one-gap-4 | $1,942 |
| DS run-4 | $2,102 |
| DS run-2+strays | $2,418 |
| 4-flush run-4 | $3,778 (?) |
| DS scattered | $4,100 |
| SS run-2+strays | $4,107 |
| SS run-4 | $5,424 |
| Rainbow scattered | $13,472 |

Two surprising results: **4-flush run-4 outranked SS run-4** (counterintuitive
given Omaha first-principles — 4-flush leaves 9 deck spades vs SS's 11), and
**DS scattered outranked SS run-4** (DS-no-connectivity beats SS-best-connectivity).

User correctly challenged: this contradicts hypergeometric flush probability.
A 4-flush hand like J♠T♠9♠8♠ should be strictly worse for flush equity than
J♠T♠9♦8♣.

## Methodology check via Gemini consultation

`mcp__pal__chat` with `gemini-2.5-pro`, full drill code shared. Gemini
confirmed the hypothesis: **the cross-class comparison is confounded** because
"mean regret per class" is averaged over different hand populations per class.
Hands that achieve 4-flush-run-4 bots (rare, structurally rigid, 2.1% of pop)
are not the same hands that achieve SS-run-4 bots (44% of pop). Different
oracle ceilings inflate or deflate the per-class mean.

Gemini's recommendation matched the user's intuition: **within-hand pairwise
comparison** controls for the confounder. For each hand that can achieve BOTH
class A and class B, compute EV(best in A) − EV(best in B). Average across
hands where both achievable. The same-hand comparison eliminates the
hand-population bias.

## Drill #2: within-hand pairwise (DEFINITIVE)

`analysis/scripts/drill_bot_suit_run_pairwise.py` — same scope, but for each
hand builds a 35-vector of best-EV-per-achievable-class, then computes the
35×35 pairwise lift matrix and accumulates across hands.

### Definitive findings (J-low no-pair pop, full data, n=85,800 hands)

**Tipping-point analysis: DS-scattered (worst DS) vs every other class:**

| Vs class | n co-achievable | Lift (DS-scat wins by) |
|---|---:|---:|
| SS run-2+strays | 37,332 | **+$111** (basically tied, DS wins) |
| 4-flush one-gap-4 | 1,400 | +$412 |
| 3+1 one-gap-4 | 15,794 | +$619 |
| 4-flush run-4 | 672 | +$622 |
| SS one-gap-4 | 29,418 | +$846 |
| 3+1 run-4 | 7,540 | +$873 |
| **SS run-4** | 16,904 | **+$1,603** |
| 3+1 run-2+strays | 36,046 | +$1,614 |
| SS run-3+stray | 34,270 | +$2,634 |
| SS two-runs-2 | 26,364 | +$2,904 |
| SS scattered | 35,380 | +$3,166 |
| SS two-gap-4 | 16,218 | +$3,414 |
| **Rainbow run-4** | 3,588 | **+$6,981** |
| Rainbow scattered | 8,784 | +$10,361 |

**Conclusion: DS-scattered beats EVERY non-DS class within-hand.** No
tipping point exists. The thinnest margin is DS-scattered vs SS-run-2+strays
at +$111 — essentially tied but DS still wins.

**4-flush vs SS at run-4** (Omaha first-principles re-test):
- 4-flush run-4 vs SS run-4: 4-flush wins by **+$907** (n=176, smaller
  effect than the confounded drill's +$1,646 but still positive)

The user's prediction (SS > 4-flush at run-4) was directionally wrong but
the gap is much smaller than the confounded drill suggested. Plausible
mechanism: flush HEIGHT compensates for flush probability. With 4♠ run-4
in hand, when board brings 3 spades you use the highest 2 spades from
hand (e.g., 7♠+8♠) for an 8-high spade flush. With SS run-4, you use
5♠+6♠ for a 6-high flush. EV(prob × payoff) can balance.

**Within-DS connectivity premium:**

| Comparison | n | Lift |
|---|---:|---:|
| DS one-gap-4 vs DS scattered | 14,412 | +$2,717 |
| DS run-4 vs DS scattered | 5,468 | +$2,554 |
| DS run-2+strays vs DS scattered | 40,328 | +$1,896 |
| DS one-gap-4 vs DS run-4 | 1,680 | +$376 (one-gap-4 actually wins!) |

Connectivity premium WITHIN DS is ~$2-3K. Suit premium DS-vs-SS is ~$4.5K
at run-4. Suit dominance > connectivity premium.

Curious finding: **DS one-gap-4 beats DS run-4** by +$376/1000h. A missing
internal rank slightly outperforms perfect consecutive — likely because the
gap creates a board-bridging straight equity bonus when the board brings
the missing rank. Worth a Session 45+ follow-up.

### Refined priority hierarchy

**Tier 1 (any DS):** DS one-gap-4 ≈ DS run-4 ≥ DS run-2+strays ≥ DS two-runs-2
≥ DS run-3+stray ≥ DS two-gap-4 ≥ DS scattered. All DS variants beat all
non-DS variants within-hand.

**Tier 2 (close cluster, ~tied with DS-scattered):** SS run-2+strays,
SS one-gap-4, 4-flush run-4, SS run-4. These are within $1K of DS-scattered
within-hand.

**Tier 3:** 3+1 variants, weaker SS connectivity, 4-flush poor connectivity.

**Tier 4 (avoid):** all rainbow (≥$3K below DS-scattered).

**Practical rule for production (Rule 10 v2 candidate):** "If you can build
a DS bot, do it — regardless of connectivity. If no DS available, pick the
suit class with most flush draws available, then break ties by connectivity
(prefer one-gap-4 ≈ run-4)."

## Methodology lessons (Session 44 NEW)

1. **Cross-class average regret is confounded by hand-population differences.**
   Mean regret per class averages over hands where the class is achievable —
   different classes have different achievability populations. Apples-to-oranges.
   Within-hand pairwise comparison eliminates this confounder.

2. **Suit dominates connectivity at every level (J-low no-pair).** No
   tipping point exists. DS-scattered ≥ all SS, 4-flush, 3+1, rainbow.

3. **First-principles arguments must check payoff height, not just
   probability.** The "4-flush has fewer deck outs" argument missed that
   when the flush DOES land, the flush height is structurally higher with
   4-flush than SS. Both factors matter.

4. **DS one-gap-4 ≥ DS run-4.** A missing internal rank in the bot creates
   a board-bridging straight bonus that beats the consecutive-rank case.
   Counterintuitive — worth confirming in trips territory too.

## Files produced

**Drills (2):**
- `analysis/scripts/drill_bot_suit_run_priority.py` — cross-product (confounded)
- `analysis/scripts/drill_bot_suit_run_pairwise.py` — within-hand pairwise (definitive)

**Documentation:**
- `SESSION_44_SUIT_CONNECTIVITY_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` Part 1 — Session 44 entry
- `CURRENT_PHASE.md` — rewritten for Session 44 wrap + Session 45 resume
- `DECISIONS_LOG.md` — Decision 077 added (methodology + suit-dominance finding)

## Why no new rule shipped

The findings invalidate the previous suit-priority methodology rule
(`DS > SS > rainbow > 3+1 > 4-flush`) and replace it with "suit dominates
connectivity universally." But translating this into a production rule
extension requires more drill work — specifically the user's Session 45
direction:

1. Apply suit dominance to J-low single-pair: does the pair-stays-in-mid
   anchor (Rule 10's mid choice) hold when breaking the pair would enable
   a DS bot? Or is DS-bot preferred even at the cost of mid pair anchor?

2. Apply to J-low two_pair: does DS-bot beat keeping both pairs intact?

These questions go beyond the bot's structural classification — they ask
whether the FULL setting (top + mid + bot) should be reorganized to
prioritize suit dominance over the conventional pair anchors. Major
structural question, queued for Session 45.

## Next session priorities (Session 45)

The user's verbatim direction: now that we have a definitive answer for
defensive J-high no-pair hands, we need to compare that to J-high hands
with a pair and see how to play these. Do we favor the pair in the middle
still? What about if it breaks double-suited on bottom? Does that mean DS
on bottom even at the cost of breaking a pair is our best option? And
then this can flow into J-high with two pair, do we favor DS on bottom
STILL? What if it means breaking our two pair?

Session 45 will:
1. Drill the J-low single-pair zone for "DS-bot at cost of breaking the
   pair" vs "pair-in-mid + non-DS bot" — within-hand pairwise.
2. Then extend to J-low two_pair zone for "DS-bot at cost of breaking
   both pairs" — within-hand pairwise.
3. If the suit-dominance-over-pair-anchor pattern holds, design a
   "Rule 10 v3" that allows pair-breaking when DS-bot is achievable.
4. Validate on full + prefix grids.
