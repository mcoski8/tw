# Methodology Review Request — Taiwanese Poker Solver, Sprint 3 Production

> **Copy-paste this entire document to Claude Desktop (Opus) for adversarial review before launching the full 6M-hand × 4-model cloud production run.**
>
> **Origin**: Claude Code session 06 (2026-04-18). Bug fixes applied + 50K-hand pilot complete. About to commit to the full production run on cloud (~2.5 days, $0 on DigitalOcean signup credit). This is the final review gate — if the methodology is wrong, it's cheaper to find out now than after 2.5 days of compute.
>
> **What you're reviewing**: how we compute the EV of every 7-card hand × every possible arrangement against 4 opponent archetypes, and whether the data we'll collect is the right raw material for Sprint 7 (pattern mining → human-usable GTO strategy).

---

## 0. What you're being asked to review

We're about to spend ~2.5 days of cloud compute (or ~10 days on a Mac Mini) producing 4 binary files, one per opponent model, each containing 6,009,159 records of the form:

```
(canonical_hand_id, best_setting_index, best_ev)
```

That's ~54 MB per file, ~216 MB total. This will be the raw solver output for the entire Taiwanese Poker variant we're solving.

Before we commit, please pressure-test:

1. **Is the EV calculation mathematically correct** given the game rules?
2. **Are the 4 opponent models sound** — do they collectively span the strategic space of realistic human opponents, or are there blind spots?
3. **Is N=1000 samples enough** for stable best-response ranking, or will noise corrupt the results?
4. **Is producing 4 SEPARATE files (deferring aggregation to Sprint 7) the right call**, or should we aggregate during production?
5. **Is the pilot data we already have (50K hands, 2 hours compute) enough evidence to proceed** to the full 6M?
6. **What known limitations should we document** so that Sprint 7 analysis doesn't over-claim?

---

## 1. Game mechanics (critical to get right before evaluating the EV calc)

This is a **simultaneous set-and-score game**, NOT a betting game. No folding, no bluffing, no information asymmetry.

### Deal
- 2 players (the solver always models the 2-player equilibrium; multiplayer reduces to pairwise sums).
- Each player dealt 7 cards privately.
- Two independent 5-card community boards are dealt AFTER both players set their hands.
- Each player knows their own 7 cards but not the opponent's cards, not the boards.

### Setting
Each player arranges their 7 cards into 3 tiers:

| Tier | Hole cards | Board cards | Rule | 5-card search space |
|------|------------|-------------|------|---------------------|
| Top | 1 | 5 | Hold'em (use 0 or 1 hole card) | C(6,5) = 6 |
| Middle | 2 | 5 | Hold'em (use 0, 1, or 2 hole cards) | C(7,5) = 21 |
| Bottom | 4 | 5 | **Omaha — exactly 2 of 4 hole + exactly 3 of 5 board** | C(4,2)×C(5,3) = 60 |

Each player has C(7,1) × C(6,2) = **105** possible settings.

### No fouling
Unlike standard Chinese Poker, tiers do NOT need to be ordered strongest-to-weakest. You can put KK on top and AA in bot if you want (usually bad, but legal).

### Scoring per matchup
For each tier on each board (6 matchups total):
- Compare player A's tier-hand against player B's tier-hand using standard high-only poker rankings (royal flush down to high card).
- Chop (equal ranks): 0 points each.
- Winner gets tier's weight; loser loses it:

| Tier | Weight |
|------|--------|
| Top | 1 |
| Middle | 2 |
| Bottom | 3 |

Per-board subtotal is 1+2+3 = 6 for the winning side if no chops. Non-scoop max per matchup = 12 (6 × 2 boards).

### Scoop
If one player wins ALL 6 matchups with ZERO chops, they get **+20 points** (opponent gets -20). Any single chop or loss invalidates the scoop — it reverts to 12 max.

### Net-points encoding (Decision 013)
Instead of gross points, we encode as **net**: `hero_net + opp_net == 0` exactly, always. So:
- Hero wins top, mid, bot on both boards with zero chops: hero_net = +20, opp_net = -20.
- Hero wins 4 of 6 matchups cleanly (e.g., wins 1 top + 1 mid + 2 bot), opp wins 2 (1 top + 1 mid): hero_net = +1+2+3+3 - 1-2 = +6, opp_net = -6.
- Full chops on all 6: hero_net = opp_net = 0.

This is important because the solver's objective is `argmax_S E[p1_net]` — the zero-sum structure means we're literally maximizing hero's expected winnings.

### Rules authority
`modules/game-rules.md` in the repo is the canonical rules reference, cross-verified against Wikipedia. All rules above are enforced in the evaluator, which exhaustively matches a direct-compute reference on every possible 5-card hand (2,598,960 hands verified in the test suite).

---

## 2. The EV calculation, formally

### Notation
- `H` = hero's 7-card hand (fixed, what we're solving for)
- `S` = hero's setting (one of 105 arrangements of H)
- `O` = opponent's 7-card hand (drawn from the remaining 45 cards)
- `B1, B2` = the two 5-card boards (drawn from the 38 cards remaining after O)
- `M` = opponent model (a function that maps (O, RNG) → opponent_setting)
- `score(S, S_opp, B1, B2)` = net points for hero when hero plays setting S vs opp setting S_opp on boards B1, B2

### Definition
Hero's expected value for setting S on hand H against opponent model M is:

```
EV(H, S, M) = E_{O, B1, B2}[ score(S, M(O), B1, B2) ]
```

The expectation is taken over:
- Uniform random choice of O from C(45, 7) possibilities
- Uniform random choice of B1 from the remaining 38 cards (C(38, 5) ways)
- Uniform random choice of B2 from the remaining 33 cards (C(33, 5) ways)

Because this is a simultaneous game with no information exchange, hero's EV depends only on O's CARD distribution, not on whether opp plays optimally against hero's hand (opp can't react to hero's setting — they set first too).

### Best response
For a given (H, M), the solver finds:

```
S*(H, M) = argmax_{S in all_105_settings(H)} EV(H, S, M)
best_ev(H, M) = EV(H, S*(H, M), M)
```

This is the **best response against opponent model M**, given hand H. It is NOT the Nash equilibrium; it assumes the opponent plays exactly according to M, and hero plays best-response. If opp is actually a Nash player (GTO), hero's best-response-to-M would be exploitable. In practice, this is desired — we want to know how to exploit each archetype.

### Monte Carlo estimator
Closed-form EV is intractable (the expectation is over 45 choose 7 × 38 choose 5 × 33 choose 5 ≈ 10^15 combinations). We Monte Carlo it:

```
EV_hat(H, S, M; N) = (1/N) * sum_{i=1..N} score(S, M(O_i), B1_i, B2_i)
```

where `(O_i, B1_i, B2_i)` are N i.i.d. samples of the (opp cards, boards) joint distribution.

### Common random numbers (CRN) — Decision 015
**Critical optimization**: for a fixed (H, M), instead of running N samples per setting (which would be 105 × N = 105,000 samples per hand at N=1000), we generate ONE sample of `(O, B1, B2, M(O))` and score ALL 105 settings against it simultaneously. That gives us N = 1000 shared samples.

Formally:
```
for sample i in 1..N:
    draw (O_i, B1_i, B2_i)
    S_opp_i = M(O_i, RNG_i)      // depends on M being stochastic or not
    for each setting s in all_settings(H):
        accumulate score(s, S_opp_i, B1_i, B2_i) into sums[s]
```

This shares the sampling cost across 105 settings (cost ~1/105 per-setting) AND reduces the VARIANCE of the ranking (since all settings are scored under the same shocks). The downside is that individual EVs are correlated across settings; we don't care because we only need the argmax.

### Suit canonicalization — Decision 006
Under the symmetric group S_4 acting on suits, many 7-card hands are strategically identical. Example: `A♠ K♠ Q♥ J♥ 9♦ 8♣ 4♦` has the same strategic properties as `A♥ K♥ Q♠ J♠ 9♣ 8♦ 4♣` (just relabeled suits). The orbit size under S_4 is at most 24; hands with repeated suit patterns have smaller orbits.

We enumerate one canonical representative per orbit. Count: **6,009,159 canonical hands** (Burnside-verified: 133,784,560 / 24 for most hands, plus smaller orbits from suit-symmetric cases). This is a ~22× reduction vs the raw 133M.

Solve is done only over canonical hands. For any actual hand encountered at inference time (e.g., in the trainer UI), we canonicalize it first and look up the canonical answer.

### Per-hand RNG seeding
For reproducibility, each canonical hand gets a deterministic seed derived from its ID:

```
per_hand_seed = base_seed XOR (canonical_id * 0x9E37_79B9_7F4A_7C15)
```

(The multiplier is φ * 2^64 for stream separation.) This means the solve is fully reproducible: given the same code + same base_seed, every hand's best_ev comes out bit-identical.

### Output format (Decision 018)
Per canonical hand, one 9-byte record:
```
canonical_id:          u32 little-endian  (4 bytes) — index into the canonical list
best_setting_index:    u8                 (1 byte)  — index into all_settings(hand) [0..105)
best_ev:               f32 little-endian  (4 bytes) — net points per matchup
```

File = 32-byte header ("TWBR" magic + version + samples + base_seed + canonical_total + opp_model_tag) + N × 9-byte records. No compression; the format is mmap-able for O(1) seek-by-canonical-id from the Sprint 7 analysis code.

**One file per opponent model**, 4 files total.

---

## 3. The 4 opponent models (P2-alt panel)

These were chosen after the Session 05 7-model diagnostic (10K hands × 7 models) revealed that only 11.9% of hands have the same best setting across all 7 models. In other words: **opp modelling matters for 88% of hands**. A single-model solve would bake in one archetype's assumption.

After Socratic review with Gemini 2.5 Pro and Claude Desktop (Session 05), we pruned to 4 models: MFSuitAware, OmahaFirst, TopDefensive, RandomWeighted. MFNaive was dropped (88% redundant with MFSuitAware). BalancedHeuristic was dropped (Bug 2 — formula puts Aces in bot instead of on top, which is a logically incoherent play; no real player does this).

Three of the four are wrapped in `HeuristicMixed{p_heuristic: 0.9}` — 90% of samples use the deterministic heuristic, 10% draw uniformly from 105 settings. This 10% Random tail prevents the solver from finding brittle exploits against any single deterministic line.

### Model 1: MFSuitAware-mixed-0.9

**Archetype**: the thoughtful Hold'em-centric player. Someone who's played a lot of Hold'em and applies Hold'em intuitions ("mid is the biggest tier for equity, put your best 2-card Hold'em hand there") but also notices when the Omaha bot has a bad suit structure and adjusts.

**Algorithm** (pure deterministic, then mix-wrapped):
1. For each of the 21 possible 2-card middles:
   - Compute `tier` (pocket pair > suited broadway > offsuit broadway > suited-ace/connector > other).
   - Compute `naive_mid_score` (Hold'em-equity ladder: pairs = 200+rank*2, non-pairs = 3·high+2·low + suitedness + connectivity + ace bonuses).
   - Compute the hypothetical bot that results (remaining 5 − top = 4 cards), score its suit structure (DS > SS > rainbow > 3+1 > 4-flush).
2. Pick the middle with the lex-max key `(tier, bot_suit_score, naive_mid_score, <index tiebreak>)`.
3. Top card: **highest-rank SINGLETON** among the 5 non-mid cards (Bug 1 fix, Decision 025 — preserves pocket pairs in the bot on AAKK-style hands). Falls back to highest-rank overall if all 5 cards are pair members.
4. Bot = the remaining 4.

**Wrapping**: 90% of samples use this deterministic output; 10% use `random_setting()` (uniform over 105).

**Known archetype trait**: prefers suited broadway over offsuit broadway — so on `As Kh Qd Jc Ts 9h 2d`, it picks mid=As+Ts (suited) over mid=As+Kh (higher-value offsuit). Real Hold'em players usually pick AK over AT-suited; we noted this as an archetype tendency ("overvalues suitedness") rather than a bug.

### Model 2: OmahaFirst-mixed-0.9

**Archetype**: the Omaha specialist coming to Taiwanese Poker. Obsesses about the bottom tier (where Omaha rules apply) and thinks of top/mid as afterthoughts.

**Algorithm**:
1. Enumerate all C(7,4) = 35 possible bottoms. For each, compute `omaha_bot_score`:
   - High-card bonus: each card > 8 adds (rank − 8) × 2.
   - Pair / trip / quad bonuses.
   - Connectivity: length of longest run of distinct consecutive ranks × 8.
   - Wheel draw: +3 if 2+ of {A,2,3,4,5}, +6 if 3+.
   - Suit bonus: DS +14, SS +7, rainbow 0, 3+1 −4, 4-flush −8.
2. Pick the 4-card bottom with highest score (lex tiebreak on indices).
3. Top = **highest-rank** of the 3 remaining cards (Bug 3 fix, Decision 026 — pre-fix picked the leftover of a mid selection, producing absurd deuces on top).
4. Mid = the other 2.

**Wrapping**: 90% heuristic, 10% uniform Random.

### Model 3: TopDefensive-mixed-0.9

**Archetype**: the scoop-terrified / risk-averse player. Defensive strategy — refuses to put a pair member on top even when it would be correct (preserves pair potential at the cost of tier strength).

**Algorithm**:
1. Top = highest-rank **non-pair-member** card (singleton rank appears once in hand). If every rank in the hand appears ≥ 2x (e.g., AAKKQQ + J), fall back to highest-rank overall.
2. From remaining 6: pick best 2-card mid by `naive_mid_score` (same function MFNaive uses).
3. Bot = remaining 4.

**Wrapping**: 90% heuristic, 10% uniform Random.

**Known archetype eccentricity (Bug 4, deferred)**: on trip hands like JJJ + 9 7 5 3, this model splits the trips (top = 9, mid = JJ, bot = J + 7+5+3) when the correct play is usually top = J, mid = JJ, bot = 9+7+5+3. We accepted this as a trait of the archetype ("player who treats a J on top as 'breaking the pair'") rather than fixing, because it's a legitimate behaviour some real players exhibit. If production data shows this systematically underperforms vs MFSuitAware, we'll revisit.

### Model 4: RandomWeighted (pure, no mix wrapper)

**Archetype**: the casual-reasonable player. No systematic strategy; applies basic filters ("don't put a deuce on top if I have higher cards; pairs should probably go together"); within the filter, picks randomly.

**Algorithm**:
1. Compute the 3 highest distinct ranks in the hand. Call this `top_ranks`.
2. Filter 105 settings down to those where:
   - top card's rank is in `top_ranks`, AND
   - mid is either a pocket pair OR both cards are broadway (≥10).
3. If the filter yields ≥ 3 settings: uniform random pick.
4. Else relax: only require top-in-top_ranks. If ≥ 3 settings: uniform random pick.
5. Else: uniform random over all 105.

**No wrapping**: the model is already stochastic; wrapping it with another 10% Random would just add noise without changing archetype meaning.

### Why these 4 specifically

**Coverage argument** (from the 7-model diagnostic):
- MFSuitAware covers the "good Hold'em-centric player" archetype.
- OmahaFirst is the ONLY model with <50% agreement with the Hold'em-centric cluster; it's structurally orthogonal.
- TopDefensive covers the "pair-preserving defensive player" and does not cluster tightly with MF (77% agreement, 23% disagreement = meaningful archetype distance).
- RandomWeighted covers "casual play"; sits between MF and Random in agreement rate, representing the non-systematic-but-not-crazy player.

**Non-coverage limitations we're aware of**:
- A "weak-tight" player who over-folds — N/A in our game (no folding).
- A "solver-app-assisted" player who runs a mini-MC themselves — deferred to possible Sprint 3b.
- A "Nash-level" opponent — we're not solving for Nash in Sprint 3; that's Sprint 4 (CFR with bucketing). Until then, "Nash" isn't in the panel.

---

## 4. Validation evidence so far

### Test suite
- **124 unit + integration tests** passing, including:
  - 5 tests covering the 2+3 Omaha rule's most common bug patterns.
  - Exhaustive LUT-vs-direct check on all 2,598,960 five-card hands.
  - Per-opponent-model archetype tests (pair preservation on AAKK, wheel hands, double-suited bots, etc.).

### Stress audit
Ran `show-opp-picks` on 7 stress hands (AAKK, broadway, TT+junk, JJJ+junk, 9876-straight-draw, 55+KJ9, A55+junk). All 4 production models produce archetype-consistent settings. Full log: `data/session06/stress_audit_postfix.log`.

### 5K-hand post-fix diagnostic
After Bug 1 + 3 fixes:
- All-7-models agree: 11.9% → **14.4%** (expected — Bug 3 makes OmahaFirst less pathologically isolated).
- OmahaFirst vs Hold'em-centric: 17-19% → **29-36%** (Bug 3 empirically validated; ~2× increase).
- MFNaive↔MFSuitAware: 88.4% → 89.0% (expected — both got same fix).
- **No pair ≥ 95%** — 4-model panel remains meaningfully distinct. No cluster collapse.

Full log: `data/session06/diagnostic_5k_postfix.log`.

### 50K-hand pilot (4 models × 50K hands × N=1000)
Complete as of 2026-04-18 01:37. Key findings:

- **Headers verified**: opp_model_tag = 1002090 / 1003090 / 1004090 / 6. File sizes exactly 450,032 bytes each.
- **Per-model wall-clock**: 30-31 minutes per model (sequential, 9× rayon parallel on M4 Mac Mini).
- **Per-hand rate at N=1000**: 31.4 ms/hand with mixed-opp wrapper (slightly faster than pure-Random's 37.3 ms/hand because the heuristic branch skips `random_setting` 90% of the time).
- **EV distributions archetype-consistent**:
  - MFSuitAware-mixed-0.9: mean EV = **-2.89** (toughest opp → hero loses most on these weak hands)
  - TopDefensive-mixed-0.9: mean EV = **-2.89** (similarly tough)
  - RandomWeighted: mean EV = **-1.66** (medium)
  - OmahaFirst-mixed-0.9: mean EV = **-1.02** (weakest at Hold'em tiers → hero loses least)
- **The mean EV being negative is a SAMPLE artifact, not a solver bug**: the pilot scanned canonical ids 0–49,999, which are the lowest-card-rank canonical hands (all 2s, 3s, 4s, 5s, occasional 6-8). Over the full 6M canonical range, mean EV should approach 0 against Random and slightly positive against the heuristics (since heuristics are exploitable).

### Pilot top-10 and bottom-10 per opponent
(Full tables in `data/session06/pilot_top10_per_opponent.md` and `pilot_bottom10_per_opponent.md`.)

**Top hands** cluster at canonical ids 40k-46k (the high end of the 50K sample) and share a structural pattern: **3 pairs + 1 high singleton**, e.g., `2c 2d 3c 3d Kh Ks Ah`. The solver's chosen play is consistent: high singleton on top, premium pair in mid, low pairs in bot. Against OmahaFirst (weakest opp), peak EV hits +3.75; against MFSuitAware/TopDefensive, peak is +3.1.

**Bottom hands** are all quads-of-2s with low trash kickers, e.g., `2c 2d 2h 2s 3c 4c 5c`. Quads in hole are useless (Omaha caps at 2-from-hand). The solver picks the "least-bad" arrangement: lowest EV is -9.84 on `2c 2d 2h 3c 3d 3h 3s` (quads 3s + trips 2s) against MFSuitAware. Neither tier can win on its own when the opp has random cards (almost always higher-ranked).

### Meta-finding: same hand → different settings for different opponents
On `2c 2d 2h 2s 3c 3d 3h` (quads of 2s + trips of 3s), the solver picks:
- vs MFSuitAware: `top=2s, mid=[3h 2h], bot=[3d 3c 2d 2c]` (give up top, play for chops)
- vs OmahaFirst: `top=3d, mid=[2s 2d], bot=[3h 3c 2h 2c]` (try to scoop the bot with 2-pair Omaha)
- vs TopDefensive: same as MFSuitAware
- vs RandomWeighted: same as OmahaFirst

This is the core empirical proof that opp modelling matters. A single-model solve would bake in the wrong answer on 85%+ of hands.

---

## 5. Aggregation question — explicit, unresolved

After the 4 files are produced, we have 4 "best settings" per canonical hand, potentially all different. Sprint 7 needs to collapse this into a single playable strategy. Candidate aggregation schemes:

- **Equal weight**: average the 4 EVs; pick the setting that's best on average. Assumes opp archetype is uniform-random across real-world pool.
- **Realism-weighted**: weights based on empirical opp-archetype frequency. We don't have this data; would need to be elicited.
- **Maximin**: pick the setting that minimizes hero's worst-case EV across the 4 opps. Defensive; ignores that we might actually be playing OmahaFirst archetype (easier opp).
- **Consensus-only**: only play moves that ≥3 of 4 models' best responses agree on; fall back to MFSuitAware (toughest) for disagreements.
- **Archetype-conditional**: produce 4 strategy documents, one per archetype. Only useful if hero can identify opponent's archetype in advance.

**Our current position (Decision 022)**: DEFER aggregation to Sprint 7 analytics, which will have all the data and can experiment with schemes. Production simply produces 4 files.

**Claude Desktop, please push back on this if you think production should aggregate instead.** The cost of deferring is 4× the disk space (216 MB vs 54 MB) and one extra analysis step; the benefit is that we don't bake in an uninformed aggregation choice.

---

## 6. Known limitations we're documenting now

Before Sprint 7 analysis over-claims, these caveats apply to the production output:

1. **Not Nash**: the solver output is best-response-to-heuristic, not Nash equilibrium. Against a Nash-level opponent, our solver's picks may be exploitable. Sprint 4 (CFR) addresses this.
2. **Opponent card distribution is uniform**: the model assumes opp's 7 cards are uniformly drawn from the remaining 45. In our game this is correct (no folding = no hand-selection bias). In a betting variant, it would be wrong.
3. **Canonical sampling ≠ uniform over actual hands**: the production covers the 6M canonical orbits, not all 133M hands with multiplicity. For aggregate statistics weighted by orbit size, Sprint 7 analysis must multiply by each canonical's multiplicity.
4. **N=1000 precision**: at N=1000, the standard error of per-setting EV is ~0.1 points (for a variance of ~10 on hero_net). Best-setting ranking is stable across N=1000 vs N=10000 in our convergence tests (Session 02), but marginal hands with close 1st/2nd settings may flip. Sprint 7 might re-solve ambiguous-decision-boundary hands at higher N if needed.
5. **4 archetypes don't span every real opponent**: solver-assisted play, Nash, tilt-induced deviations are out of panel. Extending the panel is Sprint 3b (~+2.6 days per model).

---

## 7. What specifically to pressure-test

Please challenge each of these:

### A. EV calculation
Is the MC estimator for `EV(H, S, M)` unbiased and correct given the game's simultaneous-move structure? Are we missing any expectation term (e.g., something that should integrate over opp's setting ALSO being uncertain given the heuristic)? Specifically: for stochastic heuristics like RandomWeighted, we draw a single opp_setting per sample and score all 105 hero settings against it. Is this the right way to handle the stochasticity, or should each sample re-draw opp_setting multiple times?

### B. Common Random Numbers
CRN reduces variance of the RANKING of settings but correlates their EV estimates. Is this the right trade-off for the "find argmax" problem? Are there cases where CRN could bias the argmax (e.g., a setting looks better because of a lucky board set rather than true EV superiority)?

### C. Opponent panel completeness
Given 4 archetypes (MFSuitAware, OmahaFirst, TopDefensive, RandomWeighted) and the empirical finding that they span 29-77% pairwise agreement, does this panel adequately represent the opponent space for a recreational / home-game opponent pool? What archetype is missing?

### D. Opponent panel validity
For EACH of the 4 archetypes, is the algorithm a reasonable caricature of that archetype, or is it silly? Specifically:
- MFSuitAware's "ATs over AKo" preference — is that a realistic Hold'em-player trait or a bug?
- TopDefensive's trip-split on JJJ hands — deferrable archetype eccentricity or an actual bug that makes the archetype uninterpretable?
- OmahaFirst's scoring formula (high-cards + pairs + connectivity + suit + wheel) — does it capture "Omaha-first thinking" or just encode an arbitrary linear combination?
- RandomWeighted's top-3-ranks + pair/broadway-mid filter — does "casual but not stupid" play really follow this rule, or should the filter be tighter/looser?

### E. HeuristicMixed{p=0.9}
Why 0.9 specifically? Gemini originally suggested 0.8 but we raised to 0.9 because the 7-model diagnostic showed opp-model signal is much richer than a Random-only baseline would suggest — a 20% Random tail dilutes archetype fidelity more than necessary. Is 0.9 the right point on the "archetype fidelity vs exploit-robustness" trade-off curve?

### F. Aggregation deferral
Is `Decision 022 — defer aggregation to Sprint 7` the right call, or should production aggregate using (e.g.) equal weight and save disk space? The downside of aggregating now is that we commit to a scheme; the downside of deferring is 216 MB of output instead of 54 MB and an extra Sprint 7 step.

### G. N=1000 adequacy
At N=1000 samples per hand × 105 settings = 105,000 score evaluations per canonical hand. Is this enough for stable argmax? Should we use N=500 for most hands and escalate to N=5000 for "close calls" (top-1 EV within some epsilon of top-2)? Our Session 04 convergence tests showed N=1000 vs N=10000 top-1 is stable for the hand `As Kh Qd Jc Ts 9h 2d`; is that evidence sufficient to assume N=1000 is adequate across all 6M canonical hands?

### H. Pilot-to-production extrapolation
The pilot covered canonical ids 0–49,999 (lowest-card hands). Their EV distributions are heavily skewed negative because those hands can't win. Do we have enough evidence from this slice to trust that the full 6M run will behave correctly, or should we run a BETTER pilot that samples uniformly across the canonical range (e.g., every 120th canonical id to get 50K samples spanning the full range)?

### I. Validation plan post-production
Once the 4 production files are produced, how should we validate them BEFORE Sprint 7 analysis? Current plan (Session 04 carry-forward): sample 100 random canonical hands, re-solve each at N=10,000, and check best-setting agreement is ≥ 95%. Is that the right gate?

### J. Anything else
Anything we're not thinking about that should be fixed BEFORE we commit to 2.5 days of cloud compute?

---

## 8. Meta: what Claude Desktop should decide

At the end of your review, please state one of:

1. **PROCEED AS-IS**: methodology is sound, launch the cloud production run as planned.
2. **PROCEED WITH SPECIFIC FIX**: identify the change, rationale, and expected time-to-fix. Then re-review.
3. **DO NOT PROCEED — RETHINK**: identify the fundamental issue, propose an alternative approach.

For options (2) and (3), we'll integrate your feedback and re-propose in the next session before launching.

---

## Reference: relevant code + data files in the repo

- **Game rules**: `modules/game-rules.md` (authoritative)
- **Hand evaluator**: `engine/src/hand_eval.rs`, `engine/src/holdem_eval.rs`, `engine/src/omaha_eval.rs`
- **Scoring**: `engine/src/scoring.rs` (net-points encoding)
- **Setting enumeration**: `engine/src/setting.rs` (all_settings returns 105 arrangements)
- **Monte Carlo**: `engine/src/monte_carlo.rs` (CRN + rayon parallelism)
- **Opponent models**: `engine/src/opp_models.rs` (all 7 heuristics + helpers)
- **Best-response pipeline**: `engine/src/best_response.rs` (9-byte fixed records, crash-safe writer)
- **Canonicalization**: `engine/src/bucketing.rs` (suit permutation reduction to 6M canonical hands)
- **Decisions**: `DECISIONS_LOG.md` (entries 001–026, chronologically)
- **Session history**: `handoff/MASTER_HANDOFF_01.md` (sessions 01–06)
- **Pilot outputs**: `data/pilot/*.bin` (50K × 4 models, gitignored)
- **Pilot logs**: `data/session06/pilot_*.log`
- **Top/bottom hand docs**: `data/session06/pilot_{top10,bottom10}_per_opponent.md`
- **5K diagnostic**: `data/session06/diagnostic_5k_postfix.log`
- **Stress audit**: `data/session06/stress_audit_postfix.log`

All of these are on `github.com/mcoski8/tw@main` at HEAD as of commit `24bdd7b` (2026-04-18).
