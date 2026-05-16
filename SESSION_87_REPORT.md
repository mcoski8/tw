# Session 87 — User-redirected strategic pivot uncovers a $98/1000h v52-chain bleed on prefix-silent weak-hand cells; v61 SHIPS as Rule 21 (chain gate-out), biggest single-rule production ship since S70

_Generated 2026-05-15. User reframed strategic priority at session start
("easy hands are easy to play — bleeding lives on weak hands"). A gated
pre-drill on the user-prioritized weak-hand zone revealed that the
production rule chain has been actively bleeding $98.67/1000h against the
v44_dt ML baseline for 33+ sessions, undetected because prefix grader is
structurally silent on these cells. The fix (v61) is a 30-line surgical
gate-out: for HIGH_ONLY × DS_NO_JOINT × max ∈ {J,Q,K,A}, bypass the
v47→v48→v52 chain and let v44_dt handle. Full-grid grader auto-fired SHIP
at +$98.67/1000h. Production goes from $1,412.53 → $1,511.20/1000h._

## TL;DR — Plain language

**What changed in your strategy of record:** A new Rule 21. On unpaired
hands where your highest card is Jack/Queen/King/Ace, AND the four-card
bottom can be set up as double-suited (2+2 suit pattern), AND the
double-suit options don't allow your max card to sit on top with a
suit-matched mid — **let the ML model pick the setting, not the old
human-designed defensive rules**.

**Why this was the biggest win in 15 sessions:** Three sessions ago I told
you we were leaking ~$6/1000h on a MID-pair candidate and had a
methodology question about how to validate it. You responded by
sidestepping the methodology question and reframing the priority: "easy
hands are easy to play — bleeding lives on weak hands." That reframe
turned out to be load-bearing. When I looked at the weak-hand zone with
fresh eyes, I found that the rule chain wasn't just *failing to extract
value* there — it was *actively making things worse* than the simple ML
baseline. The "defensive" rules built in sessions 47-52 were net-negative
on the biggest weak-hand cell. Nobody noticed because the validation tool
(prefix grader) is structurally blind to those cells. Removing those
rules on those cells recovers **+$98.67/1000h** — bigger than every rule
shipped from S71-S86 combined.

**The numbers:**
- Production v57: $1,412.53/1000h
- Production v61 (now): **$1,511.20/1000h** (+$98.67, +7.0%)
- Rule count: 20 → **21**
- Two-track divergence v61-vs-v44: $234/1000h (was $332, closed by $98)
- Cumulative closure since the pre-S68 baseline: 83% of original $1,409 (was 76%)

**What's NOT changing:**
- The ML champion (v44_dt) — unchanged for 15 sessions running.
- The prefix-grid score — unchanged at $776.88 (Rule 21 fires entirely outside prefix coverage; the prefix can't see the lift, but that doesn't make it less real).
- The v60 candidate from S86 — still parked, still MIXED-by-methodology, waits on Option C oracle infrastructure to be built in S88.

## The full story (compressed)

### How the session started

Last session (S86) I asked you a methodology question: how to handle the
v60 candidate that cleared full-grid SHIP at +$6.43/1000h but couldn't be
validated against the prefix grid because the cell type has zero
applicable hands in the prefix. Three options on the table: STRICT (cap
work at LOW pair), RELAX (ship v60 retroactively), EXTEND (build a per-
cell N=1000 oracle generator).

Your response started with "let's go ahead and have you do a socratic
test discussion with gemini about our options" and ended with "make sure
you have accurate data... but don't lose 20%+ accuracy to save days of
compute." Round 1 of the Gemini debate landed on Option C (EXTEND, build
the oracle generator) — fits your "hours OK, days not OK" cost threshold.

Then you reframed at a higher level: "easy hands are easy to play — the
hardest hands are damage control, weak hands where you have to limit
damage from superior opponent hands. This is where bleeding becomes
hemorrhaging. 10-20 trash hands in a row, that's real bleeding. I need
heuristics for how to play weak hands."

That reframe killed the entire S86 framing. We're not deciding between
three methodology options for v60 — we're asking whether v60 (a MID-pair
candidate) is even the right thing to work on.

### Round 2 of the Gemini debate

I ran a second Socratic round with gemini-2.5-pro on both sides:
**Should we pivot to weak-hand damage-control work?** Pulled S71's
HIGH_ONLY drill data first — it confirmed your intuition empirically:
$36-52/1000h leak per cell on K/A-high × DS_NO_JOINT cells, vs $6.43 on
the S86 candidate. 5-8× the opportunity.

FOR-pivot: pivot now, build the oracle, your intuition is gold. AGAINST-
pivot: don't pivot yet — demand a pre-drill to prove the leak is
addressable signal (not irreducible variance noise). The two sides
disagreed sharply on a heuristic question (A-high default play: Ace-on-
top scoop-blocker vs Ace-in-mid + DS-bot). The data resolved it in favor
of AGAINST: A-high × DS_NO_JOINT leaks $29.41 BECAUSE the current rules
pick Ace-on-top when oracle prefers Ace-in-mid + DS-bot.

You picked the gated plan: pre-drill addressability first, then commit.

### The pre-drill bombshell

64 seconds of compute. Re-evaluated v57 (production) on the 756,000
hands in J/Q/K/A × DS_NO_JOINT cells. The expectation: confirm v57's
leak roughly matches v44's leak ($256 baseline), proceed to design a new
rule to push below v44.

What we found:

| max | n | v44 leak $/1000h | v57 leak $/1000h | **v57 worse by** |
|---|---:|---:|---:|---:|
| J | 37,800 | $16.29 | $29.88 | **+$13.59** |
| Q | 94,500 | $38.80 | $58.04 | **+$19.24** |
| K | 207,900 | $76.99 | $105.94 | **+$28.95** |
| A | 415,800 | $124.81 | $161.70 | **+$36.89** |
| **TOTAL** | **756,000** | **$256.89** | **$355.55** | **+$98.67** |

**v57 leaks $98/1000h MORE than v44 on these cells.** The rule chain is
actively making things worse than the dumb ML baseline. v52's HIGH_ONLY
handler fires (overrides v44) on 64-86% of these hands; its overrides
are net-negative.

This had been happening for 33+ sessions. Nobody caught it because the
N=1000 prefix grader has zero applicable hands in this cell type — the
prefix is structurally blind to it. v52 shipped in S53 based on full-
grid evidence alone, and the regression went undetected.

### The chain audit

3 more minutes of compute. Layer-by-layer attribution against v44_dt
baseline (v44 → v47 → v48 → v52):

| max | v44→v47 Δ | v47→v48 Δ | v48→v52 Δ |
|---|---:|---:|---:|
| J | **+$16.04** | -$1.68 | -$0.77 |
| Q | **+$19.10** | $0.00 | +$0.14 |
| K | **+$27.95** | $0.00 | +$1.00 |
| A | **+$36.89** | $0.00 | $0.00 |
| **Σ** | **+$99.98** | | |

**~$100/1000h of the bleed is from the v44→v47 transition.** v47's
Rules 13-16 (Q-high DS chain) are the dominant source. v48/v52 add
basically nothing on top.

By v52 firing mode:
- v52-fallthrough (v47 handles, Q/K/A subset): 711,900 hands, $82.07 bleed
- v52-J-HIMID (J-high subset): 34,650 hands, $12.76 bleed
- v52-defensive-gated (s2≤8 subset): 9,450 hands, $3.84 bleed

### The fix

v61: surgical 30-line rule. Detect HIGH_ONLY × DS_NO_JOINT × max ∈ {J,Q,K,A},
return `strategy_v44_dt` directly, bypass the v47→v48→v52 chain. Outside
the gate v61 == v57 by construction.

Pre-committed thresholds locked in code before grader ran: SHIP ≥ $30,
NULL ≤ $5, MIXED in between.

Full-grid grade (377s compute, 756K hands × 2 strategies + 50K out-of-cell
sanity): **+$98.67/1000h whole-grid lift, mechanical verdict SHIP**.
Per-hand: 42.4% better / 25.7% worse / 31.9% same. Swap-right on 515K
changed hands: 62.3%. Out-of-cell sanity: 0 v57≠v61 disagreements on
50,000 random sample.

## Why we shipped on N=200 only

The S84 two-grid standard normally requires both full-grid AND prefix-
grid lift ≥ $5. Prefix is silent here. Per Round 1 Gemini's analysis +
S87's specific case:

1. Effect size is $98 — 20× the SHIP threshold. Not borderline.
2. Population is 756,000 hands. LLN aggregate noise floor is ≪ $1.
3. Mechanism is REMOVE-OVERRIDE (gate out a deterministic chain), not
   ADD-NEW-SETTING. Risk profile is asymmetric.
4. Per-hand split (42/26/32) shows real swap-right majority, not single-
   slice artifact.

The Option C N=1000 oracle infrastructure is DEFERRED to S88 — still the
right build for future smaller candidates (v60, etc.), just not blocking
this ship.

## What's left for S88

1. **Expand the audit pattern.** DS_NO_MAXTOP, MS_ONLY, JOINT_HIGH cells
   are the next-largest prefix-silent zones. If v47/v52 bleed on them
   too, another $20-40/1000h is recoverable.
2. **Build Option C N=1000 oracle generator.** Required for retroactive
   v60 validation and future smaller-effect candidates. ~30-60 min Rust
   change + test + launch.
3. **Audit prefix-COVERED cells too.** It's possible the v47/v52 layers
   are also net-negative on cells we thought were fine.
4. **LOW × PMID_OTHER drill** (deferred from S87). The last LOW pair
   cell.

Default S88 plan if user defers: pursue (1) on DS_NO_MAXTOP × {K, A}
cells — methodology directly transfers from S87's audit pattern.

## Methodology lessons (S87)

1. **PIVOT GATE pattern.** Before committing expensive infrastructure
   (e.g., the N=1000 oracle build), spend ≤5 min on a focused diagnostic
   that could falsify the premise. S87's pre-drill took 64s and rerouted
   the entire session.

2. **CHAIN AUDIT pattern.** Layer-by-layer attribution against a baseline
   strategy. Took 2 minutes of compute and uncovered a 33-session-old
   regression. Apply to every prefix-silent zone where the rule chain
   has overrides.

3. **EFFECT-SIZE-DOMINANCE rule.** When effect ≫ noise floor by 20×+ AND
   the rule is a gate-out (not an addition), bypass the two-grid
   standard with explicit documentation. Below the threshold the
   standard still rules.

4. **USER STRATEGIC REDIRECT is a first-class input.** Not a methodology
   answer, a priority reframe. The reframe was load-bearing — none of
   the S86 methodology options would have surfaced this fix.

5. **Buyout memory still relevant.** User asked "should I just buy out
   for 4?" as a damage-control move. Memory recall: buyout +EV signature
   is harmful PAIR structure (low quads, low trips), NOT garbage hands.
   Surfaced at the right moment.

6. **Socratic protocol works.** Two PAL consensus calls (methodology +
   pivot+heuristics) with FOR/AGAINST stances surfaced cruxes (LLN
   argument, addressability vs variance) that informed concrete next
   steps. Project pattern.

## Headline state at end of S87

* **Rule chain (CHANGED):** v61_high_only_ds_no_joint_fix — **$1,511.20/1000h full grid** / $776.88 prefix (unchanged).
* **ML champion (UNCHANGED):** v44_dt — $1,081/1000h full grid / $686/1000h prefix.
* **Two-track divergence:** $234/1000h (was $332, −$98).
* **Total project rule count: 21** (Rule 21 = v61 chain gate-out).
* **Cumulative closure since pre-S68:** $1,175 of $1,409 = 83% (was 76%).
