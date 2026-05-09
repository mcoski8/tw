# Session 43 — Weak-Hand Defensive Investigation

_Generated: 2026-05-09_

## TL;DR

The user's weak-hand defensive investigation (~14% of hands, J-or-lower) produced
**one shippable rule** that beats v39's combined Rule 9 ship by itself, plus
two confirmed-ML-territory zones.

| Finding | Population | Verdict | Lift (full / prefix) |
|---|---:|---|---:|
| **Rule 10: J-low single-pair defensive** | **342K (5.7%)** | **SHIPS as v40** | **+$23 full / +$37 prefix (grader-confirmed)** |
| Q1: A-high+weak (single Ace, low body) | 660K | Already optimized — no rule needed | n/a |
| Q4: J-low two_pair (re-examined defensively) | 262K | Confirmed ML territory | all candidates regress |
| Q5: J-high or weaker no-pair | 86K | Multi-feature signal but no clean rule | regresses on J-high; small full-only lift on T-low |

The J-low single-pair rule (Rule 10) is **the largest single-rule ship of the
project to date** by prefix lift (+$37/1000h), and clears the both-grid
validation gate decisively (prefix lift > full lift, the opposite of the
"prefix-regression" risk pattern).

The user's specific framing questions answered:

- **Q1** (single Ace + low body): "always Ace-on-top" mathematically validated.
  Oracle picks top=Ace 96.0% of the time on A-high+weak hands. v3's existing
  logic already does this — no rule needed.
- **Q2** (K/Q-high + weak body, "break the broadway for suit"): the
  high-card-to-bot-for-4-flush hypothesis **fails empirically** — every variant
  tested regressed by $10-$27/1000h. The high-card belongs on top. Subset of
  ~33-52% of K/Q-high hands prefer non-hi top, but no clean structural rule
  captures it.
- **Q3** (J-low + 1 pair): **YES**, there is a clean defensive rule.
  Top=lowest-singleton, mid=pair, bot=4-highest-non-pair. +$36.7/1000h prefix.
  Ships as Rule 10.
- **Q4** (J-low + 2 pairs, re-examined defensively): NO — all deterministic
  defensive candidates regress. v33's adaptive splitting was NOT a hidden
  defensive rule; it's genuine ML routing. Session 42's "two_pair is ML
  territory" verdict reaffirmed.
- **Q5** (J-high no-pair, "does suited-bot save anything"): NO. Building a
  4-flush bot at the cost of breaking the high-card is a losing trade.
  Naive "top=lowest" works on T-high or weaker no-pair hands (+$8/1000h
  whole-grid full-only) but regresses on J-high.

## Headline structural inversion (Q5/Q3 unifying signal)

The single biggest finding of Session 43 is the **weak-hand top-position
inversion**:

> When the highest card cannot reliably win the top tier, the GTO play is
> to **dump the lowest card on top** and stack the strong cards into mid + bot.

Oracle top-position frequencies on no-pair hands:

| Stratum | top=hi | top=lo | top=mid-rank | other |
|---|---:|---:|---:|---:|
| A-high+weak | **96.0%** | 2.1% | 0.4% | 1.5% |
| K-high+weak | 66.6% | 15.6% | 7.2% | 10.5% |
| Q-high+weak | 48.1% | 24.4% | 10.7% | 16.8% |
| **J-high** | 27.2% | **34.4%** | 14.6% | 23.8% |
| **T-high** | 14.6% | **42.0%** | 13.1% | 30.4% |
| **9-high** | 6.8% | **47.1%** | 10.5% | 35.6% |
| 8-high | 2.9% | 44.9% | 6.9% | 45.3% |

The crossover is between K-high (top=hi dominates) and T-high (top=lo
dominates). J-high is the boundary zone where neither top-pick alone wins.

For the pair zone, the same inversion holds but is even stronger because
the pair anchors mid Hold'em strength (so dumping the high card to top
reduces top-tier loss without sacrificing the mid).

## Rule 10 details

**Trigger:** category = pair (exactly one pair, no trip, no quad)
            AND max card rank ≤ J (= 11)

**Setting:**
- TOP = lowest singleton
- MID = the pair
- BOT = the 4 highest non-pair singletons

**Population:** 342,720 hands (5.703% of grid)

**Lift (grader-confirmed, both grids):**
- Full N=200: $2,846 → $2,824/1000h (−$22 mean regret, **+$23/1000h whole-grid lift**)
- Prefix N=1000: $1,707 → $1,670/1000h (−$37 mean regret, **+$37/1000h whole-grid lift**)
- Both numbers match the drill prediction (+$22.73 / +$36.70) within sampling noise
- Within-pair-category full-grid regret: $2,008 → $1,959/1000h ($49/h reduction × 46.6% share = $23)

**Why it works:**
The pair-mid Hold'em anchor stays (oracle prefers mid-pair 60-85% across
J-low pair cells). The CHANGE is the top: instead of putting the high
singleton on top (where it loses to most random opponents anyway),
sacrifice the lowest singleton to top-tier loss. The 4 highest non-pair
go to bot, giving the Omaha bot stronger kicker-strength.

The mathematical insight: top tier wins only 1 point per board (max 2
points across both boards), while mid wins 2 and bot wins 3. On a hand
where TOP equity is already <50% (any J-low hand vs random), the
opportunity cost of dumping the high card to top is <1 point, while the
gain in bot-tier equity from upgrading kickers is >1 point.

**Per-cell breakdown (drill data):**

The rule wins on broadly: pair_rank ≤ 6 (across all max ∈ {7..J}) and
on pair_rank == max_rank cells. It regresses slightly on cells where
pair_rank is in the (max-4, max-1) zone — e.g., Jh_p7 to Jh_pT
regress by $2-$8/cell. Net aggregate is +$22.73/1000h full; the
regressions are localized.

A gated variant ("pair_rank ≤ 6 OR pair_rank == max_rank") would
capture more of the upside (estimated +$48/1000h full) by skipping the
regression cells, at the cost of an extra condition. Per Session 42's
"diminishing returns / structural break" methodology rule, the simple
unrestricted version is preferred for human memorization, with the
gated variant available as v40b for production.

## What was tried but did not ship

### Q1 — Always Ace-on-top
Oracle confirmed at 96.0%. v3 already implements this. No new rule needed.

### Q2 — K/Q-high "break the broadway for suit"
Tested variants:
- B_BOT_FLUSH (high card in bot anchoring 4-flush): -$10 to -$27/1000h
- B_BOT_3FLUSH_EXT (3-suit + 1 extra in bot): -$15 to -$27/1000h
- C_TOP_2ND (split high to mid): -$26 to -$59/1000h
- D_TOP_LO (top=lowest): -$25 to -$44/1000h
All regress materially. The user's "break the broadway" hypothesis is
empirically wrong — top=hi remains right ~50-67% of the time on K/Q-high.

### Q4 — J-low two_pair defensive split
Six candidates tested:
- RA / RB / RC (top=hi-sing variants): all regress
- RA_TOP_LO / RC_TOP_LO (top=lo variants): regress more
- F_SPLIT (split-pair mid): catastrophic regression (-$1,287 full)
None positive. v33's adaptive routing on this zone is genuine ML
behavior, not a hidden defensive rule.

### Q5 — J-high no-pair top=lowest
Naive D_TOP_LO regresses on J-high (-$5/1000h) but wins on T-high
(+$5.29) and 9-high (+$2.70). Combined T-low high_only lift: ~+$8/1000h
whole-grid (full only — high_only category has zero prefix coverage).

This is below the both-grid validation threshold and is deferred. A
follow-up Session 44 drill could investigate the J-high no-pair zone
more carefully (it has the BIGGEST oracle ceiling of all defensive
strata at +$54/1000h whole-grid) but the rule extraction requires
multi-feature signal that didn't reduce to a clean structural pick.

## Methodology lessons (Session 43 NEW)

1. **Prefix coverage is non-uniform across categories.** high_only
   has ZERO prefix coverage (all canonical IDs >500K). This means
   the both-grid validation gate is INAPPLICABLE for high_only rules.
   Defensive rules for the no-pair zone can only be validated on full.
   Conversely, the pair category has strong prefix coverage (43% of
   prefix is pair, skewed toward low pairs).

2. **Worst-case regret is a useful sanity check.** All shipped rules
   need to NOT make a 20-point scoop more likely on any hand. v40's
   per-cell worst_full numbers stay in the +$10 to +$22 range
   (compared to v39's +$15 to +$25), confirming the rule trades a
   small mean improvement for slightly worse worst-case in some
   cells but no scoop-induction risk.

3. **The "weak-hand top inversion" is a generalizable pattern.**
   Across all weak-hand strata (no-pair AND pair), the structural
   feature is "highest card cannot reliably win top tier → invert
   the conventional top-pick". This is a unifying lens that explains
   Rule 10's mechanism. A future Session 44 might extend the same
   pattern to two-pair (Q4 disconfirmed at this level, but a smarter
   gate might find a sub-zone) or to broader weak-hand zones.

4. **High-card-to-bot for flush is a LOSING trade.** Counterintuitive
   conventional wisdom — "build a 4-flush bot at the cost of the high
   card" regressed by $10-$27/1000h on every weak-hand stratum tested.
   The bot's flush draw doesn't compensate for the lost top-tier
   equity from breaking the high card.

## Files produced

**Drills (3):**
- `analysis/scripts/drill_high_card_defense.py` — Q1+Q2+Q5 (high_only)
- `analysis/scripts/drill_low_pair_J_high_defense.py` — Q3 (J-low pair)
- `analysis/scripts/drill_two_pair_J_high_revisit.py` — Q4 (J-low two_pair)

**Strategies + graders (4):**
- `analysis/scripts/strategy_v40_rule10.py` — production candidate (simple)
- `analysis/scripts/strategy_v40b_rule10_gated.py` — gated variant
- `analysis/scripts/grade_v40_rule10.py`
- `analysis/scripts/grade_v40b_rule10_gated.py`

**Documentation:**
- `SESSION_43_DEFENSIVE_REPORT.md` (this file)
- `STRATEGY_GUIDE.md` updated (Part 1 entry, Part 6 Rule 10 reference)
- `CURRENT_PHASE.md` rewritten
- `DECISIONS_LOG.md` Decision 076 added

## Next session priorities

1. **v40 ML retrain** — feed v34_dt with v40 baseline. Marginal.
2. **Q5 deep-dive (J-high no-pair)** — biggest unrealized ceiling
   (+$54/1000h) but requires multi-feature decomposition. Likely ML.
3. **T-low high_only naive Rule 10b** — ship "top=lowest" for max ≤ T
   no-pair? +$8/1000h full-only (no prefix validation). Methodology
   question: ship full-only rules?
4. **Round-3 within-trips features** (Session 42 carryover).
5. **Learned A-vs-C decision tree for Rule 6** (Session 38-40 carryover).
