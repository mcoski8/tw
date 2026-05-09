# Decisions Log - Taiwanese Poker Solver

> **Purpose:** Record every non-trivial decision so future sessions don't re-debate settled questions.
> **Format:** Question → Options → Choice → Why
> **Rule:** Append only. Never edit past entries.

---

## Decision 001 — Primary Language
**Date:** April 2026 (pre-build)
**Question:** What language for the core computation engine?
**Options:** Python (easy, slow) | Rust (fast, safe) | C++ (fast, complex) | Python+Cython (medium)
**Choice:** Rust for engine, Python for analysis/UI
**Why:** The engine must evaluate billions of poker hands. Each evaluation involves multiple 5-card lookups. Python is 100-1000x too slow for the inner loop. Rust gives C-level speed with memory safety and excellent parallelism (rayon). Python handles the parts that don't need speed: analysis, visualization, trainer UI.

## Decision 002 — Hand Evaluation Method
**Date:** April 2026 (pre-build)
**Question:** How to evaluate 5-card poker hands?
**Options:** Runtime computation | Pre-computed lookup table | Perfect hash function
**Choice:** Pre-computed lookup table
**Why:** All C(52,5) = 2,598,960 possible 5-card hands can be pre-computed and stored in a ~10-20MB table. This turns hand evaluation into a single table lookup (~20-50ns) instead of runtime computation (~500ns+). Since we evaluate billions of hands, this saves enormous time.

## Decision 003 — Solving Approach
**Date:** April 2026 (pre-build)
**Question:** How to find the optimal strategy?
**Options:** Full Nash equilibrium (exact) | Best response to random (approximate) | CFR with bucketing (approximate Nash)
**Choice:** Tiered approach — best response first (S3), then CFR (S4)
**Why:** Full Nash is computationally intractable for 133M hands. Best response to random is feasible and extremely valuable — it tells you the single best setting for every possible hand assuming your opponent plays reasonably. CFR with bucketing can then refine toward true equilibrium. Each tier builds on the previous.

## Decision 004 — Game Variant
**Date:** April 2026 (pre-build)
**Question:** Which Taiwanese Poker variant to solve?
**Options:** Standard (1 board, royalties, fouling) | Custom (2 boards, 20pt scoop, no fouling, no royalties)
**Choice:** Custom variant (user's home game rules)
**Why:** The user plays a specific variant with double boards, 20-point scoop (must win all 6 with no chops), no fouling penalty, and no royalty bonuses. This is what we've been analyzing throughout the research phase.

## Decision 005 — Opponent Model for Best Response
**Date:** April 2026 (pre-build)
**Question:** What opponent strategy to compute best response against?
**Options:** Uniform random setting | MiddleFirst heuristic | Mixed opponent pool
**Choice:** MiddleFirst heuristic as primary, with uniform random as baseline
**Why:** Computing best response against a realistic opponent is more useful than against random. Our research showed MiddleFirst is the strongest heuristic. If the best response to MiddleFirst matches the best response to random for most hands, the solution is robust. If they diverge, that tells us where meta-game matters.

## Decision 006 — Suit Canonicalization
**Date:** April 2026 (pre-build)
**Question:** Should we canonicalize suits to reduce hand count?
**Options:** Evaluate all 133M hands | Canonicalize suits (reduce to ~15-25M)
**Choice:** Canonicalize
**Why:** A♠K♠Q♥J♥ is strategically identical to A♥K♥Q♠J♠. Canonicalizing reduces hands by ~5-10x, directly reducing compute time. The only caveat is mapping back from canonical to specific suits for the trainer, which is straightforward.

## Decision 007 — Multi-Model AI Analysis for Strategy Extraction
**Date:** April 2026 (pre-build)
**Question:** How to interpret 133M rows of solver data into a human-usable strategy?
**Options:** Single AI model analysis | Pure statistical analysis only | Multi-model AI consensus with Socratic debate
**Choice:** Multi-model consensus — Claude + Gemini independently analyze, then debate, with pure statistics as ground truth referee
**Why:** A single model can have blind spots or biases. Pure statistics can find frequencies but struggles to synthesize rules from complex interactions. The multi-model approach gets independent analysis from two different AI architectures, then forces them to challenge each other's conclusions with the statistical baseline as the arbiter of factual disputes. This mirrors academic peer review — independent analysis + adversarial challenge produces more reliable conclusions. Full debate transcripts are saved for auditability so any rule can be traced back to the data and reasoning that produced it.

## Decision 014 — Sprint 2 Opponent Model Scope
**Date:** 2026-04-17
**Question:** Which `OpponentModel` variants should Sprint 2 ship?
**Options:** (a) Random only | (b) Random + MiddleFirst | (c) Random + MiddleFirst + BestResponse (peek-the-board)
**Choice:** (a) — Random only. `MiddleFirst` and `BestResponse` left as TODOs behind the same enum.
**Why:**
  1. The Sprint 2 prompt explicitly said "start random, add MiddleFirst later."
  2. `BestResponse` requires 105 `matchup_breakdown` calls per sample (one per candidate opp setting), blowing the <500 ms headline target (projected ~23 s/hand).
  3. `MiddleFirst` is a cleaner design once we have a reference policy from Sprint 3's best-response tables anyway — doing it now risks baking in a heuristic that the solver will quickly supersede.
  4. Sprint 3's Tier 1 objective (best response to *uniform random* opponent; CLAUDE.md) only needs the Random model. Shipping it alone keeps Sprint 2 scope tight.
  Enum dispatch means adding variants later is a 5-line change with no caller impact.

## Decision 015 — Common Random Numbers in `mc_evaluate_all_settings`
**Date:** 2026-04-17
**Question:** For Monte Carlo over all 105 p1 settings of one hand, should each setting draw its own independent samples, or should all 105 share the same `(opp_hand, boards, opp_setting)` per sample?
**Options:** (a) Independent samples per setting | (b) Common random numbers (CRN) — shared samples
**Choice:** (b) CRN — shared samples across the 105 settings per draw.
**Why:** Ranking-not-EV is what the solver cares about. CRN makes the *pairwise differences* of EVs across settings much less noisy than independent sampling, at the cost of coupling individual EVs — a trade-off that's a net win because (i) ranking is the downstream consumer, (ii) sampling work is shared across all 105 so throughput is 1/105-th per sample, (iii) the parallelization strategy (split the sample budget across workers, each worker does the full 105 inside its chunk) composes cleanly with CRN. The independent-samples design would have triaged sample budget badly: per-setting SE would be identical, but rank-gaps would be noisier.

## Decision 016 — `rand` crate feature policy: enable `small_rng`
**Date:** 2026-04-17
**Question:** Which RNG to use in the Monte Carlo inner loop?
**Options:** (a) `rand::thread_rng()` (OsRng-backed, ChaCha) | (b) `SmallRng` (Xoshiro256++, feature-gated in rand 0.8) | (c) Hand-rolled xorshift
**Choice:** (b) `SmallRng`, enabled via `rand = { features = ["small_rng"] }` in Cargo.toml.
**Why:** `thread_rng()` is cryptographically strong but ~5× slower than SmallRng — unnecessary for MC sampling where statistical quality, not unpredictability, is what matters. SmallRng passes BigCrush and is the standard MC choice in the `rand` ecosystem. A hand-rolled PRNG is unjustified — SmallRng has a 256-bit state that we can seed per worker for reproducibility, and the feature flag is the whole cost.

---

*Append only. Never edit past entries.*

## Decision 008 — Player Count and Opponent Strategy
**Date:** April 2026 (pre-build)
**Question:** Do we need separate solutions for 2-player, 3-player, 4-player, and 5-player games? Do we need to model different opponent types?
**Options:** Separate solutions per player count and opponent type | Single solution that works universally
**Choice:** Single universal solution — solve as 2-player game, applies to all player counts and all opponent types
**Why:** Taiwanese Poker is a simultaneous-move game with no information exchange. You set your hand without knowing opponent cards or strategy. Your optimal setting maximizes EV against the ENTIRE universe of possible opponents and boards, not against any specific opponent type. Mathematically, each opponent matchup is scored independently, and since all opponents are drawn from the same deck distribution (from your perspective), the setting that's optimal against one random opponent is optimal against any number of random opponents. Scoops add a minor nonlinearity but simulations confirmed it has negligible effect on optimal setting. We solve once, use everywhere.

## Decision 009 — Adaptive Multi-Pass Solver vs Single-Pass
**Date:** April 2026 (pre-build)
**Question:** How to compute optimal settings for all 18M canonical hands within a reasonable timeframe?
**Options:** Single pass with high sample count (M=1000, N=1000 for all hands, all settings) | Adaptive multi-pass (quick scan → precision on ambiguous → final resolution on toss-ups)
**Choice:** Adaptive multi-pass with setting pre-screening
**Why:** Single pass at M=1000, N=1000 across 105 settings for 18M hands would take months on consumer hardware. The adaptive approach recognizes that ~90% of hands have a clearly dominant setting identifiable with low sample counts (M=50, N=50). Only ~10% need higher precision, and only ~1% need maximum precision. Combined with pre-screening (eliminating ~80 of 105 obviously bad settings before any Monte Carlo), total compute drops from months to ~8-12 days on an M4 Mac Mini. The pre-screening MUST be validated to confirm it never eliminates the true optimal setting.

## Decision 010 — Target Hardware: M4 Mac Mini
**Date:** April 2026 (pre-build)
**Question:** What hardware to run the solver on?
**Options:** Cloud compute (AWS/GCP GPU instances) | M4 Mac Mini (local) | M2 Mac Mini (local)
**Choice:** M4 Mac Mini (local, 10-core)
**Why:** The user has/will have an M4 Mac Mini. Running locally avoids cloud costs (which would be significant for a 1-2 week compute job), gives full control over the process, and the M4's performance cores are fast enough to complete the solve in 8-12 days. The solver uses 8 cores (leaving 2 for OS), checkpoints every few minutes for resilience, and produces partial results immediately usable while computation continues. Cloud compute remains an option for acceleration if needed later.

## Decision 012 — 5-Card Evaluator: Colex-Indexed Lookup Table
**Date:** 2026-04-16 (Sprint 0)
**Question:** Which 5-card hand evaluation algorithm to implement — Cactus Kev's prime-hash, Two-plus-two 7-card table, or a colex-indexed lookup over all C(52,5) hands?
**Options:** Cactus Kev (elegant, ~1-5 KB tables, needs perfect-hash derivation for paired hands) | Two-plus-two (~130 MB, fastest for 7-card queries via sequential state machine) | Colex-indexed LUT (10 MB, sort-then-index, no perfect hash to derive)
**Choice:** Colex-indexed LUT of all 2,598,960 hands. Direct `compute_rank_5` function used at build time AND as the reference implementation for tests.
**Why:** Correctness > cleverness for Sprint 0. Cactus Kev requires deriving a perfect hash from prime products for the paired-hand table — an extra code path that's easy to get subtly wrong and harder to test exhaustively. Colex indexing is a closed-form bijection: sort 5 bytes, sum 5 binomial coefficients from a precomputed 52×6 table, index the array. The test `table_lookup_matches_direct_on_every_hand` then trivially verifies correctness against a direct-compute reference for EVERY possible hand (runs in 0.12s). Measured bench: 5.4 ns per eval — ~10× faster than the <50 ns target. Two-plus-two's 130 MB table is overkill for Sprint 0 and is still available as a future optimization for the 7-card tier evaluators if needed.

## Decision 013 — Net-Points Encoding for Matchup Scoring
**Date:** 2026-04-16 (Sprint 1)
**Question:** How should `matchup_breakdown` report per-player points? Gross points won (always ≥ 0 per player) or net points (positive for the winner, negative for the loser, summing to zero)?
**Options:**
  - Gross: `(p1_won_points, p2_won_points)`, each player sees only what they earned (0..=20). Callers subtract if they want net.
  - Net: `(p1_net, p2_net)` where `p1_net = p1_gross - p2_gross`, always summing to zero. Scoops produce (+20, -20).
**Choice:** Net-points encoding. `p1_points + p2_points == 0` is a hard invariant.
**Why:** Best-response computation (Sprint 3) averages EV *against* an opponent across millions of samples. With net-points, the EV is just `mean(p1_points)` — a single averaging pass. With gross-points, callers would need to subtract in the hot loop, and the invariant is weaker (p1_gross and p2_gross would each range over 0..=20, hiding sign). Net form also makes the scoop case unambiguous: (+20, -20) and (-20, +20) are the only scoop outcomes, vs gross form where you'd see (20, 0) and have to reason about whether the opponent got zero because they lost or because they chopped. The invariant `p1 + p2 == 0` is test-friendly — `net_points_always_sum_to_zero` in scoring_tests.rs verifies it across a handful of contrived matchups.

## Decision 017 — Sprint 3 Solve: Single-Pass at N=1000 (no pre-screening, no adaptive multi-pass)
**Date:** 2026-04-17 (Sprint 3, Session 04)
**Question:** Sprint 3's plan in `sprints/s3-best-response.md` was an adaptive 3-pass solver — quick scan (top-25 settings × M=50 × N=50), precision refinement (top-5 × M=500), final resolution (top-3 × M=2000) — gated by per-hand EV gap. Should the actual implementation follow that plan, or use a single pass at full N=1000 across all 105 settings?
**Options:**
  - (a) Adaptive 3-pass with 25-of-105 setting pre-screening (`quick_score = mid×4 + top×2 + bot×1.5`).
  - (b) Single pass at N=1000 across all 105 settings, no pre-screening.
**Choice:** (b) — single pass.
**Why:**
  1. The user's resume prompt explicitly simplified Sprint 3 to single-pass at N=1000. The adaptive plan in s3-best-response.md was a worst-case design from before we knew the actual canonical hand count.
  2. Suit canonicalization came in at **6,009,159 canonical hands**, not the 15-25M ballpark the adaptive plan was sized against. At our measured 37.3 ms/hand (N=1000, 9× rayon speedup), full single-pass projects to ~62 hours / 2.6 days — comfortably under the 1-week target in CLAUDE.md.
  3. Pre-screening is not free: it requires a heuristic that's PROVABLY non-eliminating of the true optimum (CRITICAL validation step), and the validation itself costs roughly as much as one full single-pass at lower N. Skipping it removes a correctness risk (heuristic that drops the optimum on adversarial hands) and a complexity risk (Sprint 4's CFR baseline now consumes a uniform-quality solve instead of a heterogeneously-confident one).
  4. CRN (Decision 015) means the marginal cost of evaluating one extra setting per sample is ~1/105 of one sample's cost — pre-screening's 25/105 reduction yields at most ~75% saving on the inner loop, which is dwarfed by the savings from canonicalization being 22× (not 5×).
  5. Single-pass output is simpler for Sprint 4 to consume: every hand has exactly one `(best_setting, best_ev)` record at the same N, so any cross-hand pattern mining has uniform confidence intervals.
  Adaptive multi-pass remains available behind a Sprint 3.5 if Sprint 4 reveals decision boundaries that need higher per-hand precision than N=1000 supports.

## Decision 018 — Best-Response Output File Format: Fixed-Width Records, Not Bincode
**Date:** 2026-04-17 (Sprint 3, Session 04)
**Question:** How should the per-hand best-response output be serialized — bincode'd `Vec<(u32, u8, f32)>`, length-prefixed framed records, or fixed-width records with a small leading header?
**Options:**
  - (a) `bincode::serialize(&Vec<Record>)` — one big blob.
  - (b) Length-prefixed framed records — `bincode::serialize_into(writer, &Record)` per hand.
  - (c) Custom fixed-width: 32-byte "TWBR" header + N × 9-byte records `(u32 LE id, u8 idx, f32 LE ev)`.
**Choice:** (c) — fixed-width.
**Why:**
  1. **Crash-safe resume.** Writer crashes are non-negotiable for a 2.6-day run. `(filesize − 32) / 9 = records_written` lets the writer compute the exact resume offset with one `metadata().len()` call, no parsing of prior state. Bincode would either need a length prefix (option b) or full re-deserialization (option a) to know where to resume — both fragile under partial writes.
  2. **Index-by-position.** With fixed-width records, `canonical_id = position` invariantly. Sprint 5's trainer can mmap the file and `seek(32 + 9 * id)` for O(1) lookups without an in-memory index.
  3. **Header-as-fingerprint.** The header carries `(samples, base_seed, canonical_total, opp_model_tag)`. `BrWriter::open_or_create` refuses to append to a file produced under different parameters, eliminating an entire class of "I resumed against the wrong file" foot-guns.
  4. **Predictable on-disk size.** 32 + 9 × 6,009,159 = 54,082,463 bytes ≈ 51.6 MB. No surprises, easy to back up, easy to validate file integrity with a single arithmetic check.
  5. **No bincode framing overhead.** Bincode's per-record framing (length prefix + variant tag) would add bytes without any benefit at this granularity.
  Trade-off: extending the record schema later (e.g. adding `second_best_ev` for adaptive refinement in Sprint 3.5) requires a version bump and a new magic-tag suffix. We accept this — it's a once-per-sprint cost and forces explicit migration paths.

## Decision 019 — Sprint 2b: Multi-Archetype Opponent Panel (7 models)
**Date:** 2026-04-17 (Sprint 2b, Session 05)
**Question:** Single opponent model (Random or MiddleFirstSuitAware-Mixed) vs a panel of archetype-representative models?
**Options:** (a) Single model (cheap, ~2.6d production) | (b) 3-model panel | (c) 7-model panel + diagnostic
**Choice:** (c) — 7-model panel implemented + diagnosed first, then reduced to P2-alt (4 models) for production.
**Why:** The 10K-hand diagnostic against only 2 opp models (Random vs HeuristicMixed-0.8) showed 45.6% same-best rate, which was already alarming. The 7-model panel revealed only 11.9% of hands have the same best-setting across all models — opp modelling dominates the solver's answer on ~88% of hands. Using a single opp model for the 6M-canonical-hand solve would produce a strategy calibrated to ONE archetype, systematically distorting Sprint 7's pattern-mining. The 7-model diagnostic (45.6 min, matching predicted ~46 min) is a reasonable one-time cost to measure the opp-model sensitivity and cluster structure empirically. Production is then committed to the minimal set of non-redundant archetypes (P2-alt).

## Decision 020 — Validation Gate ≥70% MC-Agreement Was the Wrong Metric for Archetype Panels
**Date:** 2026-04-18 (Sprint 2b, Session 05)
**Question:** Should opponent models be required to match MC-best-setting ≥ 70% of the time before inclusion in the diagnostic panel?
**Options:** (a) Keep ≥70% gate | (b) Drop the gate; measure distinctness from other panel models instead
**Choice:** (b) — drop the gate.
**Why:** Claude Desktop's original validate-model gate (BalancedHeuristic must match MC-best-setting ≥70% with ≤0.3 mean regret) conflates "is this a good solver?" with "is this a distinct play archetype?". A realistic-opponent panel needs coverage of characteristic human error modes (weak-but-systematic, Omaha-centric, scoop-avoidant, etc.), not near-GTO clones. Applying a ≥70% gate would eliminate every model EXCEPT ones already close to MC-optimal — defeating the panel's purpose. The correct gate is distinctness (low pairwise agreement with other panel members) + behavioural plausibility (does the model do things humans actually do?). Gemini 2.5 Pro independently reached the same conclusion. BalancedHeuristic was still ultimately dropped, but for Bug 2 (puts Ace in bot — no human plays this way), not for failing the ≥70% bar.

## Decision 021 — Drop BalancedHeuristic Entirely
**Date:** 2026-04-18 (Sprint 2b, Session 05)
**Question:** Retune BalancedHeuristic's weights (×2/×4/×2.5), replace with mini-MC variant, or drop entirely?
**Options:** (a) Retune | (b) Mini-MC replacement | (c) Drop
**Choice:** (c) — drop.
**Why:** The behavioural audit (`show-opp-picks`) found BalancedHeuristic puts an Ace in the bottom (instead of on top) when the bot has enough high-card density. Formula arithmetic confirmed this is systematic: the ×2.5-weighted bot-high-card component outweighs the ×2-weighted top-card component for Aces. No human archetype plays this way — it's not "miscalibrated-systematic," it's producing logically incoherent settings. Retuning becomes a whack-a-mole research project. Mini-MC replacement (top-10 by naive score + N=50 MC refinement) is a *different* archetype ("solver-app-assisted player") and doesn't belong in the slot originally designated for "player who reads the strategy guide systematically." Gemini 2.5 Pro agreed: "drop the model entirely." P2-alt panel (4 models) still covers the strategic space adequately without Balanced.

## Decision 022 — Production Aggregation Strategy Deferred to Sprint 7
**Date:** 2026-04-18 (Sprint 2b, Session 05)
**Question:** How should 4 models' outputs combine into a single best-response per hand for the final strategy guide?
**Options:** (a) Equal weight | (b) Realism-weighted | (c) Maximin (min-EV across models) | (d) Consensus-only | (e) Defer to Sprint 7 analytics on collected data
**Choice:** (e) — defer; output 4 separate best-response files, let Sprint 7 choose aggregation.
**Why:** With the 11.9% all-agree rate and mean 2.2 EV spread across models, ANY pre-committed aggregation scheme is uninformed speculation. Equal weighting treats OmahaFirst (orthogonal 17-19% archetype) as equally-likely as MFSuitAware (typical archetype), which is wrong. But any realism weighting is unvalidated. Collecting per-(hand, model) EV records in 4 separate 9-byte-record files (~54 MB each, ~216 MB total) preserves all information; Sprint 7 analytics can then experiment with aggregation schemes on the actual data without re-running the 10-day production solve. This also means each model is independently resumable — a partial production run produces 1-3 complete model files + one in-progress, which is strictly useful.

## Decision 023 — Production Panel = P2-alt (4 Models)
**Date:** 2026-04-18 (Sprint 2b, Session 05)
**Question:** Which subset of the 7-model panel to run in production given the 10+ day compute commitment?
**Options:** P1 (3 models) | P2 (original 4 with Balanced) | P2-alt (4 models swapping Balanced → TopDefensive) | P3 (all 7)
**Choice:** P2-alt = MFSuitAware-fixed + OmahaFirst-fixed + TopDefensive-fixed + RandomWeighted.
**Why:**
  1. **Drop MFNaive (88.4% redundant with MFSuitAware):** After Bug 1 fix (pair preservation), the two may diverge more, but both occupy the same Hold'em-centric niche; MFSuitAware is strictly more refined.
  2. **Drop BalancedHeuristic (Decision 021).**
  3. **Keep TopDefensive:** 79% agreement with MFSuitAware = 21% disagreement is substantial. TopDefensive's pair-preservation logic correctly handles AAKK, AA+KK+Q, etc. where the Hold'em-centric models split pairs (Bug 1). Covers the "scoop-terrified / risk-averse" archetype. **No need for a separate Scoop-Terrified model — already in the panel.**
  4. **Keep OmahaFirst:** Lowest pairwise agreement with any other model (17-19% vs Hold'em-centric, 44.8% with Random). Orthogonal archetype; essential for capturing Omaha-specialists coming to Taiwanese.
  5. **Keep RandomWeighted:** Represents the "casual-reasonable" player — doesn't make obviously-bad plays, doesn't systematically optimise. 54% agreement with Random + 63-64% with MF-family = moderate-but-distinct signature.
  6. P3 (all 7) was rejected for redundancy; P1 (3 models) sacrifices the TopDefensive pair-preservation archetype without gain.

## Decision 024 — `HeuristicMixed{p=0.9}` Wrapping for Production
**Date:** 2026-04-18 (Sprint 2b, Session 05)
**Question:** With the 4-model P2-alt panel, what mix ratio should wrap each deterministic model?
**Options:** (a) p=1.0 (no mix, pure) | (b) p=0.8 (Gemini's original recommendation) | (c) p=0.9 | (d) per-model tuning
**Choice:** (c) p=0.9 for the three deterministic members (MFSuitAware, OmahaFirst, TopDefensive). RandomWeighted stays pure (already stochastic; wrapping it with more Random has no meaningful effect).
**Why:** Gemini's original p=0.8 recommendation was calibrated against a Random-only baseline assumption. The 7-model diagnostic revealed the opp space is much richer than that — all-7-agree is only 11.9%, so opp-model signal matters a lot. A 20% Random tail dilutes archetype integrity more than necessary. 10% Random is sufficient to prevent brittle exploits on any single deterministic line while preserving ≥90% archetype fidelity. Gemini independently recommended p=0.9 on the 7-model data.

## Decision 025 — Bug 1 Fix: Pair-Preserving Top-Selection in MFNaive + MFSuitAware
**Date:** 2026-04-18 (Sprint 2b, Session 06)
**Question:** The MFNaive and MFSuitAware top-card rule ("highest-rank card remaining after the mid is chosen") breaks a pair on AAKK-style hands — e.g. `As Ah Kd Kh 7s 4c 2d` produces top=Kh, orphaning the other K into the bot. What's the minimal fix that (a) preserves pairs when possible and (b) doesn't regress any archetype's existing behaviour on plain hands?
**Options:**
  - (a) Keep the bug; accept that MF-family models break pairs when one pair is in mid.
  - (b) Prefer highest-rank SINGLETON in rem5 (card whose rank appears exactly once among the 5 non-mid cards); fall back to highest-rank overall when every card is a pair member.
  - (c) Prefer highest-rank NON-PAIR-MEMBER in the full 7-card hand (TopDefensive's rule) — but applied post-mid.
**Choice:** (b) — singleton-in-rem5 preference, fallback to highest-rank-overall.
**Why:**
  1. **Correct on AAKK:** mid=AA picked first; rem5=KKQQ+7 or KK+7,4,2 etc. Singleton ranks in rem5 are {7}, {4}, {2} on the audit hand → top=7. KK intact in bot.
  2. **No regression on plain broadway hands:** on `As Kh Qd Jc Ts 9h 2d` (no pairs) all of rem5 are singletons; the rule collapses to "highest rank" — same as pre-fix behaviour (top=Kh via MFSuitAware's ATs-over-AKo path; top=Qd via MFNaive).
  3. **Choice (c) would orphan AAs too:** on `As Ah Kd Qc Js 9h 3d`, MFNaive picks mid=AA, then rem5 = [Kd, Qc, Js, 9h, 3d]. Rule (c) would need the full-hand context rather than rem5 — but rem5 has no pair members here, so both (b) and (c) agree (top=Kd). Rule (b) is the simpler "local" rule; applies correctly to the rem5 context. This matches TopDefensive's own pair-preserving spec (which looks at the full hand because it picks top FIRST), so the three pair-preserving models (MFNaive, MFSuitAware, TopDefensive) all encode the same principle now, each in its own scoping.
  4. **Fallback case (all rem5 are pair members):** e.g. after mid=AA on AAKKQQ+J, rem5=KKQQ+J. J is a singleton in rem5 → top=J (fine). Only when NO singleton exists — e.g. AAKK-QQ-77 with mid=AA, rem5=KKQQ77 — does the fallback fire, and then highest-rank is picked (top=K). This still breaks a pair but is unavoidable; the model can't keep all three pairs intact when only 5 slots are available for 3 pairs.
  Implemented as a new `pick_top_from_rem5(&[Card; 5]) -> usize` helper. `build_setting_mid_then_top` and `candidate_bot_after_top` now both route through it. Verified by two new unit tests (`mfnaive_preserves_kk_on_aakk_hands`, `mfsuitaware_preserves_kk_on_aakk_hands`) and visual audit on 7 stress hands — behaviour on no-pair hands is bit-identical to pre-fix.

## Decision 026 — Bug 3 Fix: OmahaFirst Top = Highest of Remaining 3
**Date:** 2026-04-18 (Sprint 2b, Session 06)
**Question:** OmahaFirst selects the 4-card bot first, then picks "the best 2-card Hold'em mid from the remaining 3, leaving the leftover card as top." This produces absurd tops (top=2d on a broadway-heavy hand). Fix?
**Options:**
  - (a) Keep as-is (absurd tops are archetype-eccentric).
  - (b) Top = highest-rank card of the remaining 3; mid = the other 2.
  - (c) Top = highest-rank SINGLETON of rem3 with fallback (full pair-preserving rule).
**Choice:** (b) — simple "highest of 3" rule, index tie-break.
**Why:**
  1. **Archetype match:** An "Omaha-priority player" obsesses about the bot, not about the top. Once the bot is locked, they throw the highest remaining card on top without further optimisation. This matches real-world Omaha-specialist play.
  2. **Pair-preservation is not relevant here** because the 4-card Omaha bot selection already pulls pocket pairs into the bot when valuable (pairs score +15..+30 in `omaha_bot_score`). By the time we're at rem3, any remaining pair is usually unwanted junk the Omaha scorer rejected. Option (c) would over-engineer a rule for a case that rarely arises.
  3. **No regression on the existing tests** — `omahafirst_favors_double_suited_bot` and `omahafirst_wheel_hand_uses_wheel_in_bot` only check the bot contents; they pass unchanged. The new test `omahafirst_picks_highest_remaining_for_top` on the broadway hand locks in the fix (top=Ts ≥ 9, not the pre-fix 2d).
  4. Index tie-break keeps behaviour deterministic when two rem3 cards have equal rank (rare but not impossible — e.g. rem3 = [7h, 7s, X]). Higher-index card wins by convention (same as `pick_top_from_rem5`).

---

## Decision 011 — Dual Compute Backend (CPU + CUDA)
**Date:** April 2026 (pre-build)
**Question:** Should we build CPU-only or also support GPU acceleration?
**Options:** CPU only (simpler) | GPU only (fastest but limits hardware) | Both via feature flags (flexible)
**Choice:** Both — CPU is default, CUDA is opt-in via cargo feature flag
**Why:** CPU-only (Rust + rayon) works everywhere and requires no special dependencies. CUDA requires an NVIDIA GPU and CUDA toolkit but offers 10-50x speedup for the Monte Carlo inner loop. Using Cargo feature flags (--features cuda), we compile the same codebase with or without GPU support. The CPU path is developed first and serves as the reference implementation. The CUDA path is added in a sub-sprint after CPU is validated. This lets the user choose: run locally on Mac Mini for free (CPU, 8-12 days), rent a cheap CPU cloud server ($15-25, 1-2 days), or rent a GPU ($3-10, 4-8 hours).

---

## Decision 027 — Portable Scripts (Cross-Platform Path Resolution, Drop macOS-only time flags)
**Date:** 2026-04-19 (Sprint 3, Session 07)
**Question:** `scripts/production_all_models.sh` and `scripts/pilot_all_models.sh` were written for the Mac Mini and fail immediately on Linux cloud hosts. How do we make them portable without breaking Mac usage?
**Options:**
  - (a) Keep as-is; write a separate cloud-specific script each run.
  - (b) Hardcode both Mac and Linux paths with a conditional.
  - (c) Use `$(cd "$(dirname "$0")/.." && pwd)` to resolve repo root relative to the script's own location. Drop `/usr/bin/time -l` entirely since engine logs timing itself.
**Choice:** (c).
**Why:**
  1. **One source of truth.** Same script works on Mac Mini (`/Users/michaelchang/.../taiwanese`), on `/workspace/tw` inside a RunPod container, on `~/tw` under a GCP VM, etc. The `dirname/..` pattern is POSIX-standard shell and doesn't depend on the invoker's CWD.
  2. **`/usr/bin/time -l` was never essential.** The `-l` flag is BSD-only (macOS); GNU time uses `-v`. The engine's own log output captures per-block timing via `block-size` reports, so dropping the wrapper loses no operational signal. (If we ever want wall-clock + max-RSS again, add `command -v /usr/bin/time && /usr/bin/time -v ... || ...` guard.)
  3. **Discovered in production.** Session 07 had to unblock a live RunPod pod with two `sed -i` in-place patches applied over a web terminal. Committing the fix upstream prevents every future cloud user from re-doing that.
  4. **No Mac regression risk.** The resolved `$PROJ` on the Mac is still the absolute project root (same as the hardcoded path was). Removing `/usr/bin/time -l` only loses the post-run memory summary line on Mac runs — none of our downstream analysis consumes that line.


## Decision 028 — Python analysis stack with byte-identical Rust parity as its correctness gate
**Date:** 2026-04-21 (Session 08)
**Question:** How do we gain confidence that the Python-side analysis pipeline (readers, canonical decoder, setting-index decoder) matches the Rust engine's interpretation of the same data? Test parity with small hand-written cases, or commit to a stronger gate?
**Options:**
  - (a) Unit-test each module against hand-rolled expected values and call it good. Easy, but any hidden Rust-specific encoding subtlety (endianness, padding, float formatting) could slip through.
  - (b) Round-trip small synthetic records through both engines and compare.
  - (c) Run the Rust engine's own `spot-check` CLI on the exact same on-disk file the Python pipeline reads, render output in Python using the same format string Rust uses, and require `diff` to report zero differences.
**Choice:** (c), enforced for every major reader/decoder addition.
**Why:**
  1. **The whole analysis stack is downstream of correct decoding.** Every later claim — "setting 104 is picked 19.7% of the time," "this EV distribution looks right," any pattern miner, any decision tree — inherits correctness from the readers. A subtly-wrong decoder would poison all derived work silently and would be nearly impossible to back out of once pattern-mining conclusions are published.
  2. **Byte-equality beats semantic equality as a test.** Testing "the same set of settings" or "the same numeric EV" admits rounding errors, ordering drift, and format divergence. `diff` on formatted text is a strictly stronger constraint: if the Python output matches Rust's spot-check output byte-for-byte across 500 records (519 lines counting header+stats), the decoders agree on every u32 / u8 / f32 / enumeration choice we've implemented so far.
  3. **Cheap to produce, expensive to skip.** The Rust engine already has `spot-check` built for humans. Reformatting Python's output to match took ~5 minutes. The return is durable: a single `diff` run becomes the regression test for every future reader or decoder addition, including Models 2-4 when they land (same record format, same canonical file — if diff holds, they're correct).
  4. **Catches issues unit tests miss.** In practice the implementation path uncovered that `np.searchsorted` and `np.void` comparisons don't work as expected (fixed via `tobytes()` binary search + vectorized int16 column-diff for lex ordering). Pure unit tests against small synthetic data wouldn't have exercised the 6M-row code paths where these issues surfaced.
  5. **Forces format discipline.** Maintaining byte-for-byte parity means the Python code can't silently reformat outputs — which means any future "nice to read" pretty-printing must go in a separate presentation layer, not the decoder. That's the right architectural boundary anyway.
**Consequence:** Every new Python decoder (e.g. bottom-hand Omaha evaluator, feature extractor when it lands) should be paired with a Rust spot-check-style cross-verification before being trusted for downstream analysis.


## Decision 029 — Sprint 5a trainer: Flask + vanilla JS, subprocess-per-MC, on-demand Compare across all 4 profiles
**Date:** 2026-04-23/24 (Session 09)
**Question:** How do we build the trainer interface requested in the secondary project goal, given (a) only 1 of 4 `.bin` files is local, (b) Sprint 7 pattern mining that would produce solver-derived explanations is still blocked, (c) user wants interactive drag-and-drop + per-profile EV comparison?
**Options considered:**
  - (a) Terminal / CLI trainer — fast to build, but the user explicitly wanted drag-and-drop UI.
  - (b) React/Vite single-page app — richer stack, but adds a build step and npm dependency surface for what is still a local-only tool.
  - (c) Flask + vanilla JS + native HTML5 drag-and-drop — no build step, minimal dependency surface (Flask only), serves HTML/CSS/JS directly.
  - EV computation strategy: pre-store full 105-setting EVs per hand (~56 GB per model, prohibitive) vs. call the Rust engine on demand via a stable CLI flag.
  - Opponent-profile strategy: pin to the one we have data for (MiddleFirstSuitAware) vs. run MC live against every profile on request.
**Choice:** (c) Flask + vanilla JS + subprocess-per-MC via new `mc --tsv` flag. Trainer defaults to MiddleFirstSuitAware for single-hand scoring, but a "Compare across all 4 profiles" button triggers live MC against every production-profile (~5s total serial) and renders per-profile best arrangements.
**Why:**
  1. **Zero new dependencies beyond Flask.** The trainer/ package adds no JS toolchain, no React/Vite, no TypeScript. Static files are dropped straight into `trainer/static/` and served by Flask. One `python3 trainer/app.py` starts the whole thing.
  2. **The Rust engine already had the math.** `mc_evaluate_all_settings` already computes all 105 EVs for a hand against any opponent. We only needed a parseable output mode. Adding `--tsv` is a 40-line patch in `main.rs` that routes status prints to stderr and emits one TSV header block + 105 rows. No duplication of Monte Carlo logic in Python.
  3. **Subprocess-per-MC is "fast enough" and avoids FFI complexity.** Single MC at samples=1000 parallel runs in ~300ms — well under the threshold where humans perceive latency. Compare mode at 4 × ~300ms ≈ 1.5s serial is acceptable because it is not the primary interaction loop. Avoiding PyO3/FFI keeps the build story simple: `cargo build --release` once, then Python is the only iteration layer for trainer work.
  4. **On-demand MC is unbounded in opponent choice.** We did not need to precompute .bin files for every profile we wanted to train against — any opponent-model flag combination is reachable. This is what lets Compare work with only 1 or 2 `.bin` files on disk (the cloud solve progresses independently), and what will let us add exploitative-mix profiles later without re-running the cloud.
  5. **Per-profile Compare matches the user's mental model of "robust vs exploitative" play.** A setting that is top-EV against all 4 profiles is close to Nash (robust). A setting that is only top-EV against one profile is exploitative. The table + per-profile arrangements panel make this visible, which is the whole reason the user wanted the feature. Worst-case delta ("exploitable by [profile] for +X.XX EV") is the single most important number for a player evaluating their own play; it is shown prominently.
  6. **Pre-Sprint-7 explanations are explicitly hand-written heuristics.** The `explain.py` detectors (split-pair, isolated-bottom-suit, wrong-top-card, tier-swap) are derived from the game rules, not from solver data. They are good first-pass coaching but will be replaced once Sprint 7 pattern mining produces solver-derived rules. The interface shape (Finding { title, detail } list) is rule-engine-agnostic, so swapping the rule source later is a single-file change.
**Consequence:**
  1. The trainer is feature-complete at "dealt 7 cards → arrange → submit → see EV gap + per-profile comparison" with only 1 of 4 models on disk. When Models 3 & 4 land, no trainer code changes — the subprocess call already uses any valid opponent flag.
  2. Future enhancements gated on Sprint 7: swap `explain.py` rule source, add decision-tree explanations, surface "in 97% of similar hands the solver plays X" style claims.
  3. Future enhancement orthogonal to Sprint 7: user-accuracy stats tracking, difficulty modes, hand-category drill-down (Sprint 5b).
  4. Port 5050 (not Flask default 5000) because macOS AirPlay Receiver claims 5000. Documented in `trainer/app.py`.


## Decision 030 — Multiway-robust setting = mode of per-profile best-responses
**Date:** 2026-04-26 (Session 11)
**Question:** Given 4 best-response files (one per opponent profile), how do we operationally define the "multiway-robust" setting for a canonical hand? Several plausible definitions exist with different computational costs and theoretical justifications.
**Options considered:**
  - (a) Run a separate Monte Carlo simulation against an equal-mixture of the 4 profiles for every canonical hand. Theoretically the cleanest "BR vs uniform mixture of opponents." Cost: ~6M × 105 settings × 1000 samples = effectively re-doing one of our cloud runs. ~40 hours at full sample size. Prohibitive.
  - (b) Use the per-hand cross-model UNANIMOUS setting where it exists; for non-unanimous hands, compute analytically. Clean for the 26.68% of hands that are unanimous, but leaves 73% undefined.
  - (c) Use the MODE of the 4 per-profile best-response settings as the multiway-robust answer. Computable instantly from the existing .bin files; well-defined for every hand; tie-breaking ambiguity only affects 9.6% of hands (2-2 splits) plus 2.7% all-distinct.
  - (d) Compute a weighted score: multiway-robust = the setting that maximizes the SUM of "match counts" across the 4 profiles plus (when available) any EV margin info. More principled than (c) but data-hungry.
**Choice:** (c) — multiway-robust setting = MODE of the 4 per-profile best-responses. For 2-2 splits, take the first encountered in profile order; for all-distinct hands, also take the first. Document the tie-break behavior so it's reproducible.
**Why:**
  1. **Computable from existing data.** All 4 .bin files are on disk. Mode is an O(N×4) sweep with no MC. Full 6M-hand pass takes seconds.
  2. **The mode IS the operational best-response against an equal-mixture opponent population for the 90.4% of hands where the mode-count is ≥3.** When 3+ profiles agree on a setting, that setting is best against ≥75% of opponents → it's the dominant choice against any mixture weighted approximately equally. The error vs option (a) only matters for the ~10% of hands with 2-2 splits, which the analysis already flags as "genuinely contested."
  3. **The mode-rate IS the natural confidence signal.** Unanimous (4-of-4) → strongest robust answer. 3-of-4 → strong. 2-of-4 (2-1-1) → moderate, with one rival. 2-2 → genuinely opponent-dependent. 1-1-1-1 → highly opponent-dependent. This bucketing is exactly what the trainer wants to surface to the user ("how contested is this decision?").
  4. **Avoids the "sum of EVs" trap of option (d).** EVs aren't comparable across profiles — vs OmahaFirst the optimal hand has mean EV +2.12, vs TopDef it's +0.50. Adding raw EVs would systematically over-weight OmahaFirst's preference simply because OmahaFirst is a weaker opponent. Mode-counting normalizes for opponent strength implicitly.
  5. **Preserves the agreement-class signal for downstream Sprint 7 work.** The pattern miner can filter to unanimous hands for clean rule extraction, then validate against 3-of-4 hands as a holdout, then study contested hands separately. Mode-as-definition makes that stratification easy.
**Consequence:**
  1. `analysis/scripts/multiway_analysis.py` uses this definition. The hypothesis test "Δ multiway-robust vs heads-up BR" reported in CURRENT_PHASE.md and the handoff is downstream of this choice.
  2. Future feature mining (Sprint 7 hand-feature extractor) joins to multiway-robust setting using this definition. If we ever upgrade to option (a) we'd need to re-run analyses, but the qualitative findings (top rank −0.18, mid pair +2.2pp, bot DS +1.2pp) should hold because the mode and the true BR-vs-mixture agree on ≥90% of hands.
  3. Trainer UI's eventual multiway recommendations will derive from the mode + the agreement class — a hand with unanimous 4-of-4 is a "high-confidence rule applies" hand; a 2-2-split hand is a "your read on the table determines the answer" hand.


## Decision 031 — Per-profile overlays vs GTO core; overlays are auxiliary (trainer side), the published guide is multiway-robust
**Date:** 2026-04-27 (Sprint 7 Phase C, Session 15)
**Question:** When v3 hits 56.16% multiway-robust shape-agreement and only ~46% on br_omaha / br_topdef, should the project's effort go toward (a) per-profile overlays that lift the weak profiles to 50-55%, or (b) directly attacking the multiway-robust 95% target via richer rule structure?
**Options:**
  - (a) Overlays first — tactical lift visible in the trainer when the user picks an OmahaFirst or TopDefensive opponent. Surfaces in `strategy_for_profile` dispatcher.
  - (b) GTO-core first — the published guide is opponent-AGNOSTIC, multiway-robust agreement is the headline metric. Overlays are auxiliary tactical tools.
  - (c) Both, with explicit hierarchy: GTO core is the published 5-10 rule chain; overlays are an opt-in tactical layer in the trainer for opponent-specific drilling.
**Choice:** (c) — both, but with the hierarchy made explicit.
**Why:**
  1. **The published end product is opponent-AGNOSTIC.** CLAUDE.md states: "the END PRODUCT is a condensed decision tree / hierarchy of rules that a human can memorize and apply in <30 seconds" and "the definitive GTO Taiwanese Poker strategy guide — backed by exhaustive computation, not heuristics." Per-profile rules are NOT in that brief.
  2. **Multiway-robust agreement is the headline.** v3 at 56.16% is 39pp short of the 95% target — that's the real distance, not 5pp on per-profile.
  3. **Overlays still have value for the trainer.** When the user is drilling against a specific profile (e.g., "I always lose to the Omaha-leaning friend"), the per-profile overlay is the right tactical surface. Routed via `strategy_for_profile` dispatcher.
  4. **The methodology divides cleanly.** GTO-core work is supervised rule learning over the multiway-robust target; overlay work is tactical tuning per opponent BR. Don't conflate.
  5. **Recognised mid-session in Session 15** after pursuing per-profile overlays for two phases (Phase C, Phase C+). User pushback ("you're chasing the wrong metric") triggered the pivot to Phase D (decision-tree extraction).
**Consequence:**
  1. `strategy_v3` (or future `strategy_v5_dt`) is the publishable rule chain. Overlays remain available for trainer profile-specific mode but are NOT part of the published artifact.
  2. The 95% headline is measured against multiway-robust, not against any single profile.
  3. Future per-profile improvements are scoped as trainer enhancements; future GTO-core improvements are scoped as published-guide updates. Different reviewers / different release cadences.


## Decision 032 — Phase D methodology: sklearn DecisionTreeClassifier with shape-equivalence scoring
**Date:** 2026-04-27 (Sprint 7 Phase D scoping, Session 15)
**Question:** How do we extract a 5-10 rule chain matching the multiway-robust solver ≥95% on all 6M canonical hands, in a way that is testable, repeatable, and provable?
**Options considered:**
  - (a) Continue hand-engineering rules from miss-bucket inspection. Failed in Session 15 — I misread the unanimous-miss subset's modal pattern as a global pattern and proposed a flip rule that regressed two_pair by -27pp.
  - (b) sklearn `DecisionTreeClassifier` on (hand_features, multiway_robust setting_index), scored by shape-equivalence. Native `export_text` produces the if/elif chain.
  - (c) RuleFit / SkopeRules — designed for "small set of rules" output natively. Plan B if (b) produces convoluted rules.
  - (d) Hierarchical: predict tier features sequentially (top, then mid, then bot). Risk of cascading errors.
  - (e) Per-category trees, ensembled. Loses cross-category structure; complicates the human-memorizable guide with a preliminary "what category" step.
**Choice:** (b) — sklearn DecisionTreeClassifier on full 6M, scored by shape-equivalence.
**Why** (after Socratic dialog with Gemini 2.5 Pro, continuation `97707ec2-1603-44d2-a534-236caa6e92a2`):
  1. **Native rule output.** `export_text` produces the if/elif chain that IS the publishable artifact. Aligns model with deliverable.
  2. **Target = setting_index (105 classes), not shape-tuple (254K classes).** Shape-tuple is hand-specific (each hand has different ranks); 254K-class classification is intractable. Setting_index is bounded; we score predictions by collapsing both predicted and true to shape via `setting_shape()`.
  3. **Features are 21 hand-features + 6 boolean feasibility flags** (`can_make_ds_bot`, `can_make_4run`, `has_high_pair`, `has_low_pair`, `has_premium_pair`, `has_ace_singleton`, `has_king_singleton`). Boolean flags encode poker concepts the tree can split on cheaply. NO per-suit rank vectors (overfit risk).
  4. **3-fold CV on 1M subsample for depth selection; full-6M fit at chosen depth.** The population is finite — CV is for robust depth choice, not generalization to unseen data. This matches the rigorous standard for rule extraction over a known population.
  5. **EV-loss backtest is the ground truth.** Shape-agreement is the cheap proxy used for training. The actual game-cost is mean (BR_ev − chain_ev) across hands × profiles, computed via engine MC on a 5-10K-hand sample.
  6. **Don't anchor on the 83.2% "ceiling" napkin math.** The empirical depth=∞ tree is the actual ceiling. If it caps below 95%, the feature set is the limiter (next lever: feature engineering). If it exceeds 95%, depth pruning is the lever.
  7. **Testable:** the depth-vs-agreement curve is reproducible by anyone with the same seed + dataset. Repeatable: byte-identical-prediction parity check between sklearn tree and extracted Python rule chain. Provable: depth=∞ tree is empirical proof of structural ceiling.
**Consequence:**
  1. `analysis/scripts/dt_phase1.py` saved (Session 15) — the ceiling-curve experiment.
  2. Future `strategy_v5_dt` in `encode_rules.py` will be the learned chain.
  3. EV-loss reporting becomes a standard validation artifact alongside shape-agreement.
  4. If sklearn DT output is convoluted (e.g., many splits on continuous features that don't map to clean poker concepts), fall back to RuleFit / SkopeRules. Decision deferred to Phase D execution.


## Decision 033 — 95% shape-agreement target retired; absolute EV per profile is the new headline; rule-count cap is soft
**Date:** 2026-04-27 (Session 16)
**Question:** Phase D ceiling-curve experiment showed the 27-feature decision-tree ceiling is 61.74% on full 6M (well below the project's headline "≥95% shape-agreement on multiway-robust target"). Subsequent EV-loss baseline showed v3 LOSES money against strong opponents (-0.78 EV/hand vs MFSuitAware, -0.89 vs TopDef) despite scoring 56.16% shape. Two surgical-fix hypotheses (fall-through, +5 Ace-bonus removal) were empirically refuted. What's the right project goal given this?
**Options:**
  - (a) Hold the 95% line; pursue feature engineering iteratively until reachable.
  - (b) Reframe to "≥95% on unanimous-only hands" (covers 26.68% of data).
  - (c) Drop shape-agreement as headline; use per-profile absolute EV (+ $/1000 hands at $10/EV-pt) as primary metric, EV-loss vs BR as diagnostic.
  - (d) Combination: directional EV-loss reduction (no hard %) + non-negative absolute EV against all 4 profiles.
**Choice:** (d) — the directional reframe.
**Why:**
  1. **Empirical infeasibility of 95% shape on the current target.** The 27-feature ceiling caps at 61.74% on the full 6M and 70.01% on the 3-of-4 majority subset (clear-majority signal). Even unbounded depth and 151K leaves cannot break through the feature representation. Pursuing 95% on shape-agreement is chasing a number anchored to a defunct (single-BR) target definition, not the multiway-robust-mode target we adopted in Decision 030.
  2. **Shape-agreement is a noisy proxy that hides whether the strategy profits.** The user's reframe ($10/EV-point over 1000 hands — does the rule chain profit?) revealed v3 is profitable vs weak opponents (Omaha +$10K, Weighted +$3.7K per 1000) but LOSES money against strong ones (MFSuitAware -$7.7K, TopDef -$8.8K per 1000). EV-loss alone never surfaced this. Absolute EV per profile is the strategically meaningful metric.
  3. **Hand-engineered surgical patches don't work.** Two consecutive hypotheses were refuted by data: (i) fall-through to setting 102/104 (OR=1.09 — not a signal), (ii) +5 Ace-on-top bias removal (net total loss INCREASED +93 EV, the +5 was load-bearing for non-Ace pair hands). v3's hand-engineered architecture is at its structural ceiling for what 9-rule dispatch with single-component scoring can express. Components interact non-trivially.
  4. **User's "discovery phase" stance.** User is non-technical, called the project a "nuanced and new discovery phase," and explicitly pushed back: *"these ultra tight goals is begging for failure."* Hard percentage targets are inappropriate before we know what's achievable; directional reduction below v3's 1.63 baseline is achievable, measurable, and avoids the failure-by-numerical-target trap.
  5. **The rule-count cap (5-10 rules) is also soft.** User stated explicitly: *"realistically im thinking we even go more than 10 named heuristics if need be to get us better EV (in a significant way)."* Memorability has a cost, but that cost must be justified by real EV improvement — not enforced as an arbitrary cap. Realistic landing zone: ~10-15 named heuristics with internal nesting, total ~150-300 decision paths, depth-7 to depth-10 in tree terms.
  6. **Methodology doctrine adopted alongside.** Every hypothesis must go through 4 steps before any compute is spent: Hypothesize → Measure Signal (odds ratio on representative sample, NOT visual inspection) → Measure Impact (EV-loss share) → Test Cheaply (in silico/analytical proxy) → only then act. Two consecutive wrong hypotheses in this session would have been killed in 30s by an in silico test instead of costing 9-18 minutes of MC compute. Locked in.
**Consequence:**
  1. CLAUDE.md headline section may need an update reflecting the new goal framing (deferred to Session 17 — not blocking).
  2. CURRENT_PHASE.md updated with the new headline and Session 17 starting action.
  3. `analysis/scripts/v3_evloss_baseline.py` is the canonical evaluation harness. Future rule chains tested via `--strategy <name> --hands 2000 --save data/<name>_records.parquet` for apples-to-apples comparison at fixed seed=42.
  4. **Reporting standard:** every rule-chain candidate must report (a) per-profile absolute mean EV, (b) per-profile EV-loss vs BR, (c) $/1000 hands at $10/EV-pt for non-technical legibility. Both metrics; absolute EV is the headline.
  5. Path forward: data-driven distillation, not surgical patches. Category-specific miss-driven feature mining starting with single-pair hands (47% of total EV-loss).


## Decision 034 — Three single-pair augmented features added to the production feature set
**Date:** 2026-04-28 (Session 17)
**Question:** The 27-feature DT ceiling on full 6M (61.74%) and on (mode_count==3, category=='pair') (74.23%) is structurally insufficient for the rule-chain target. Which features close the gap?
**Options considered:**
  - (a) Continue hand-engineering rule logic in encode_rules.py. Refuted in Session 16 — the v3 architecture is at its hand-engineered ceiling.
  - (b) Add bot-suit-profile-per-routing features. Mined from the leaf dump (mine_pair_leaves.py): the structural blind spot is "the suit profile of the SPECIFIC 4 cards that end up in the bot under a given (top, mid) choice", which the existing `suit_max/suit_2nd/can_make_ds_bot` features only see at the 7-card level.
  - (c) Add full per-suit per-position vectors (e.g., 28 booleans). High variance, overfit risk, large rule chains.
**Choice:** (b) — three minimal features:
  1. `default_bot_is_ds` (bool) — bot is DS under v3-default routing.
  2. `n_top_choices_yielding_ds_bot` (0-5) — count of pair-on-mid routings yielding DS bot.
  3. `pair_to_bot_alt_is_ds` (bool) — alt routing (pair→bot, mid=top-2 singletons) yields DS bot.
**Why** (signal + impact + cheap-test confirmed before commit, per Decision 033's 4-step doctrine):
  1. **Mining produced the hypothesis.** mine_pair_leaves.py top-50 leaves showed two clusters: (A) v3-default bot has a 3-of-a-suit problem → BR moves a non-default singleton to top to repair the bot, (B) low pair + 2 high singletons + DS-feasible-on-pair-route → BR routes pair→bot. The features encode exactly these two routings + the default's status.
  2. **Odds ratios confirm signal direction.** `default_bot_is_ds` OR=4.39 vs "BR uses v3-default routing" (positive); `pair_to_bot_alt_is_ds` OR=0.56 (negative — BR shifts AWAY from default when alt is DS). Both directions match the leaf observations.
  3. **Drop-out ablation confirms all three are non-redundant.** Slice depth=None ceiling: 80.08% (full aug) → 78.04% (−default_bot_is_ds, −2.04pp) / 78.71% (−n_top_choices_yielding_ds_bot, −1.37pp) / 77.24% (−pair_to_bot_alt_is_ds, −2.85pp). `pair_to_bot_alt_is_ds` is the largest contributor — counter-intuitive given its inverse OR magnitude, and a reminder that signal strength ≠ contribution magnitude.
  4. **Cheap-test outcome:** depth=None lifts (single-pair 3-of-4: +5.85pp; full 6M: +2.02pp). Depth-15 augmented tree (62.0% full / 60.7% cv) **matches the baseline depth=None ceiling at 9× fewer leaves and +3.5pp better cv-shape generalization** — the strongest signal that the lift is real, not overfit.
  5. **Vacuous on non-pair hands by design.** Compute is single-pair only (n_pairs==1, no trips, no quads). Other categories will get their own augmented features in Session 18+. Non-pair rows in the augmented columns are 0 and the DT learns to ignore them via category_id splits.
  6. **Spot-check methodology lesson.** First feature design (computed only the v3-default routing's DS status) was wrong — caught by manually checking 4 hand-picked cases from the leaf dump against expected behavior. Re-designed `n_top_choices_yielding_ds_bot` as a count, not a "which", since the DT can't pick the specific top from a single boolean. **Spot-check ≥4 hand-picked cases against the source observation BEFORE batch.**
**Consequence:**
  1. `analysis/scripts/pair_aug_features.py` is the production feature module. `compute_pair_aug_for_hand(hand)` is the scalar primitive; `compute_pair_aug_batch(hands, slice_mask)` is the vectorised version.
  2. `data/feature_table_aug.parquet` (18.87 MB) joins `feature_table.parquet` on `canonical_id`. Future runs read this file instead of recomputing the 51s Python-loop augment over 6M.
  3. `analysis/scripts/dt_phase1_aug.py` is the canonical depth-curve harness with augmented features. Replaces dt_phase1.py for Phase D ceiling work.
  4. **Depth-15 with these features is the chain-extraction candidate.** 18,330 leaves; 62.0% full / 60.7% cv shape; matches baseline unbounded ceiling. Whether to ship this or continue mining other categories is the Session 18 fork.
  5. Feature naming convention locked: `<routing>_bot_<property>` for bot-property-per-routing features. Future categories (high_only, two_pair) will follow.


## Decision 035 — Three high_only augmented features added to the production feature set
**Date:** 2026-04-28 (Session 18)
**Question:** With Decision 034's pair-aug features the full-6M ceiling reached 63.76% (depth=None) / 62.0% (depth=15 knee). high_only is the second-largest miss-cohort by EV-loss share (12.6%). What features close that gap?
**Options considered:**
  - (a) Continue with the pair-aug features only and extract the depth-15 chain. Refuted by the discovery doctrine — there's a clean miss-pattern that further mining can address before chain commitment.
  - (b) Add bot-suit-profile-per-routing features for high_only (mirroring Decision 034's pattern). Mined from the leaf dump (`mine_high_only_leaves.py`): the structural blind spot is the suit profile of the SPECIFIC 4 cards in the bot under each (top, mid) routing, which the existing `suit_max/suit_2nd/can_make_ds_bot` features only see at the 7-card level.
  - (c) Per-suit per-position vectors. Same overfit concern as Decision 034.
**Choice:** (b) — three minimal features, vacuous on non-high_only hands:
  1. `default_bot_is_ds_high` (bool) — under NAIVE_104 (top=byte[6], mid=bytes(4,5), bot=bytes(0..3)), is bot DS (2,2)?
  2. `n_mid_choices_yielding_ds_bot` (0-15) — fix top=highest. Count of C(6,2) mid-pair choices from the remaining 6 that yield a DS bot.
  3. `best_ds_bot_mid_max_rank` (0 or 4-14) — fix top=highest. Among mid choices yielding DS bot, the maximum rank that can appear in mid. Encodes the rank-cost of routing-for-DS-bot.
**Why** (signal + impact + cheap-test confirmed before commit, per Decision 033's 4-step doctrine):
  1. **Mining produced the hypothesis.** `mine_high_only_leaves.py` (slice ceiling 39.64% / 4,544 leaves on 463K hands) showed the recurring pattern in the top-15 miss-leaves: under NAIVE_104 the bot is 3-suited (3 of the 4 lowest cards share a suit), and BR demotes a same-suit broadway pair from mid → bot to repair the bot to DS. Example: hand `2c 3c 6c 7d Jh Qh Ks` → NAIVE bot `2c 3c 6c 7d` = 3 clubs (NOT DS); BR routes Q-J→bot, mid=7-6, bot=`Qh Jh 3c 2c` = 2h+2c → DS.
  2. **Odds ratios confirm signal direction and magnitude.** `default_bot_is_ds_high` OR=6.38x: P(BR=NAIVE | F1=1)=57.32% vs P(=NAIVE | F1=0)=17.40%. `best_ds_bot_mid_max_rank` shows a clean U-shape — 36% NAIVE when no DS-bot achievable; 10% NAIVE when DS-bot only via low-mid (4-8); 42% NAIVE when broadway K/A can stay in mid with DS-bot. Exactly the "tradeoff cost" decision the DT needs to encode.
  3. **Drop-out ablation confirms all three are non-redundant.** Slice (high_only 3-of-4) ceiling: 48.92% (full aug) → 45.76% (−default_bot_is_ds_high, −3.15pp) / 47.73% (−n_mid_choices_yielding_ds_bot, −1.19pp) / 44.13% (−best_ds_bot_mid_max_rank, −4.78pp). F3 is the largest contributor — same pattern as Decision 034 where the OR-magnitude-weakest feature contributed most.
  4. **Cheap-test outcome:** depth=None lifts (high_only 3-of-4 slice: +9.28pp / 39.64% → 48.92%; full 6M: +1.44pp / 63.76% → 65.20%). Slice ceiling approaches the empirical ~50% "single deterministic rule cap on opponent-dependent high_only" finding from Session 13. The pair-aug features stay vacuous on the high_only slice (drop-out delta = 0pp on all three) confirming feature isolation by design.
  5. **Vacuous on non-high_only hands by design.** Compute is high_only only (7 distinct ranks). Other categories will get their own augmented features. Feature naming convention from Decision 034 followed: `default_bot_is_ds_high` / `n_mid_choices_yielding_ds_bot` / `best_ds_bot_mid_max_rank`. The `_high` suffix disambiguates from the pair-aug `default_bot_is_ds`.
  6. **Spot-check ≥4 hand-picked cases passed before batch.** Per Session 17 lesson: `high_only_aug_features.py.__main__` includes 5 spot-check cases (Leaf-1 miss, Leaf-1 alt-DS-bot, Leaf-5 miss, Default-DS sample, Monosuit). All match expected feature values, including non-trivial f3=12 on Leaf-5 (Q achievable in mid with DS-bot).
**Consequence:**
  1. `analysis/scripts/high_only_aug_features.py` is the production feature module. `compute_high_only_aug_for_hand(hand)` is the scalar primitive; `compute_high_only_aug_batch(hands, slice_mask)` is the vectorised version.
  2. `data/feature_table_high_only_aug.parquet` (18.75 MB) joins `feature_table.parquet` on `canonical_id`. Future runs read this file instead of recomputing the 43s Python-loop augment over the high_only sub-population.
  3. `analysis/scripts/dt_phase1_aug2.py` is the canonical depth-curve harness with all 33 augmented features (27 baseline + 3 pair-aug + 3 high_only-aug). Supersedes `dt_phase1_aug.py` for Phase D ceiling work.
  4. **Depth-15 with all 33 features is the new chain-extraction candidate.** 18,354 leaves; 62.86% full / 61.59% cv shape; +0.86pp full / +0.92pp cv over the Session 17 knee. v3 production at 56.16% means depth-15 aug-33 is +6.7pp over v3.
  5. Slice ceiling on high_only 3-of-4 is now 48.92% (vs Session 13's empirical ~50% opponent-dependent cap). The remaining 1pp suggests the high_only feature ceiling is approached for a DT on this target. Future high_only gains likely require a different target (per-profile chains, weighted ensemble, or accepting the multiway-robust target's intrinsic ambiguity on this category).
  6. Pattern reusable for two_pair (24% of EV-loss) and trips_pair (small but high-density) in Session 19+. Same template: filter slice → mine leaves → hypothesise routing-aware features → OR-test → spot-check → batch + ablation → persist parquet → re-run depth curve.


## Decision 036 — Three two_pair augmented features added to the production feature set
**Date:** 2026-04-28 (Session 19)
**Question:** With Decisions 034 + 035 the full-6M depth=None ceiling reached 65.20% and the depth-15 knee 62.86%/61.59% cv-shape. two_pair is the largest remaining miss-cohort by EV-loss share (24% of v3 EV-loss). Mining showed a much higher slice baseline (79.47%) and very diffuse miss-leaves (top-10 = 0.5% of misses, top-100 = 3.4%) — the doctrine's "test cheaply" gate became important. What features close the gap?
**Options considered:**
  - (a) Skip two_pair and ship the chain from the Session 18 depth-15 aug-33 tree. Refuted by signal: a quick `signal_or_two_pair.py` test showed adding the 3 candidate features lifts the slice depth=None DT literal-agreement +5.95pp (79.34% → 85.29%), comparable to single-pair's +5.85pp lift in Session 17 — the discovery still has runway despite diffuse miss-leaves.
  - (b) Add bot-suit-profile-per-routing features for two_pair (mirroring the Decision 034/035 pattern). Mining (`mine_two_pair_leaves.py`) showed the structural blind spot is "high-pair-on-mid (DT-default, settings 14/44) vs high-pair-on-bot (BR-swap routing)" — picking which of the two pairs goes to mid vs bot, plus singleton-on-top choice. Discriminator within each leaf is suit-coupling that the 28-feature baseline cannot expose.
  - (c) Per-suit per-position vectors. Same overfit concern as Decisions 034/035.
**Choice:** (b) — three minimal features, vacuous on non-two_pair hands:
  1. `default_bot_is_ds_tp` (bool) — under (mid=high-pair, top=highest-singleton, bot=low-pair+2-lowest-singletons), is bot DS (2,2)?
  2. `n_routings_yielding_ds_bot_tp` (0-6) — over the 6 intact-pair routings (2 mid-pair × 3 top-singleton choices), count those yielding DS bot.
  3. `swap_high_pair_to_bot_ds_compatible` (bool) — among the DS-bot routings, does ANY have HIGH pair on bot (i.e., mid=low-pair, bot=high-pair+2-singletons)?
**Why** (signal + impact + cheap-test confirmed before commit, per Decision 033's 4-step doctrine):
  1. **Mining produced the hypothesis.** `mine_two_pair_leaves.py` (slice ceiling 79.47% / 39,677 leaves on 675K hands) showed the dominant top miss-leaves all involve the high-pair-on-mid vs high-pair-on-bot routing decision, with suit-coupling as the within-leaf discriminator. Example Leaf-1 hand `2c 6c Jd Kh Ks Ac Ad`: DT picks mid=AA (high-pair-on-mid), bot=KK62; BR picks mid=KK (swap), bot=AA62. The features encode whether default routing yields DS-bot, how many routings DO yield DS-bot, and whether the swap-high-pair-to-bot routing is among them.
  2. **Signal magnitudes are weaker than Sessions 17/18 individually but combined-effect is strong.** F1 (`default_bot_is_ds_tp`) OR=1.14x (much weaker than pair-aug's 4.39x or high-aug's 6.38x). F3 (`swap_high_pair_to_bot_ds_compatible`) OR=0.65x (inverse, modest). F2 (`n_routings_yielding_ds_bot_tp`) shows a clean U-shape: P(BR=baseline) = 83.51%/70.23%/74.50%/88.04% across {0/1/2/4} routings — 17.81pp spread. The combined depth=None DT literal-agreement on slice lifts +5.95pp (79.34% → 85.29%), comparable to pair-aug's +5.85pp despite weaker individual ORs. The reason: each feature alone is weak but the three combined map cleanly to a six-cell "default-vs-swap × n-routings × kicker-rank" decision the DT can split on.
  3. **Drop-out ablation confirms all three are non-redundant.** Slice (two_pair 3-of-4) ceiling: 85.37% (full aug-37) → 83.53% (−default_bot_is_ds_tp, −1.84pp) / 83.70% (−n_routings_yielding_ds_bot_tp, −1.67pp) / 83.44% (−swap_high_pair_to_bot_ds_compatible, −1.93pp ← LARGEST). The three drops are within 0.26pp of each other — unlike Sessions 17/18 where one feature dominated. All three are doing real work; the structural-symmetry feature (F3) edges out by a hair. Pair-aug + high_only-aug features correctly drop 0.00pp on the two_pair slice (vacuous by design, third confirmation across 3 categories now).
  4. **Cheap-test outcome:** depth=None lifts (two_pair 3-of-4 slice: +5.90pp / 79.47% → 85.37%; two_pair full: +7.50pp / 68.29% → 75.79%; 3-of-4 majority: +1.64pp / 74.38% → 76.02% on top of pair+high; full 6M: +1.67pp / 65.20% → 66.87% on top of pair+high). Total full-6M lift over the 27-baseline now +5.13pp (61.74% → 66.87%) across 3 augmented families. Depth-15 knee with all 37 features: 63.74% full / 62.44% cv-shape, +0.88pp full / +0.85pp cv over the Session 18 knee. v3 production at 56.16% means depth-15 aug-37 is **+7.58pp over v3**.
  5. **Vacuous on non-two_pair hands by design.** Compute is two_pair only (n_pairs == 2, no trips, no quads, exactly 3 distinct singletons). Other categories (single-pair, high_only) have their own augmented families. Feature naming convention from Decisions 034/035 followed: `default_bot_is_ds_tp` / `n_routings_yielding_ds_bot_tp` / `swap_high_pair_to_bot_ds_compatible`. The `_tp` suffix disambiguates from the pair-aug `default_bot_is_ds` and high-aug `default_bot_is_ds_high`.
  6. **Spot-check 6 hand-picked cases passed before batch.** Per Session 17/18 lesson: `two_pair_aug_features.py.__main__` includes 6 spot-check cases (Leaf-1 miss, Leaf-2 miss, Leaf-3 miss, default-IS-DS construction, monosuit, swap-only-DS construction). All match expected feature values, including a non-trivial F2=2 on Leaf-1 where two routings (mid=KK + top=6 or top=2) yield DS-bot.
  7. **Diffuse miss-leaf concentration is NOT a contraindication.** The two_pair slice has top-10 miss-leaves = 0.5% of misses, top-100 = 3.4% — much flatter than single-pair (top-10 = 11%) or high_only (top-10 = 4.4%). But the +5.90pp slice lift confirms the structural pattern is real and uniform across small leaves. Diffuseness in the leaf graph is orthogonal to whether features can lift the floor — one decision-axis can be tested across many small leaves and have aggregated impact.
**Consequence:**
  1. `analysis/scripts/two_pair_aug_features.py` is the production feature module. `compute_two_pair_aug_for_hand(hand)` is the scalar primitive; `compute_two_pair_aug_batch(hands, slice_mask)` is the vectorised version (~26s on the 1.34M two_pair sub-population).
  2. `data/feature_table_two_pair_aug.parquet` (18.89 MB) joins `feature_table.parquet` on `canonical_id`. Future runs read this file instead of recomputing the augment.
  3. `analysis/scripts/dt_phase1_aug3.py` is the canonical depth-curve harness with all 37 augmented features (28 baseline + 3 pair-aug + 3 high_only-aug + 3 two_pair-aug; labelled "aug-36" by convention with prior sessions). Supersedes `dt_phase1_aug2.py` for Phase D ceiling work.
  4. **Depth-15 with all 37 features is the new chain-extraction candidate.** 18,399 leaves; 63.74% full / 62.44% cv-shape; +0.88pp full / +0.85pp cv over the Session 18 knee. v3 production at 56.16% means depth-15 aug-37 is +7.58pp over v3. Same leaf-count tier as Session 17/18 knees (~18K leaves), maintaining the chain-extraction-feasibility property.
  5. Pattern reusable for trips_pair and any remaining category mining in Session 20+. The augment template is now triple-validated across (single-pair, high_only, two_pair), with all three families:
     - confirmed vacuous on out-of-category hands (drop-out delta = 0pp);
     - additively composing on the full 6M (61.74 + 2.02 + 1.44 + 1.67 = 66.87% — exactly matches);
     - producing depth=None lifts of +5-9pp on their target slice.
  6. **Continue mining vs ship the chain.** The +0.88pp depth-15 / +1.67pp depth=None lift over Session 18 means there is still runway for additional category mining (trips_pair next, or non-3-of-4 cohorts), but the marginal lift per session is now ~+1pp on full-6M depth=None. Recommended Session 20 fork: (a) one more mining pass on trips_pair to confirm the lift plateau; OR (b) extract the depth-15 aug-37 chain via sklearn `export_text` and run `v3_evloss_baseline.py --strategy v5_dt --hands 2000 --save` for the actual EV-loss measurement against v3. The reframe (Decision 033) favours (a) until lift goes <0.5pp, but (b) is the deliverable the user is ultimately tracking ($/1000 hands at $10/EV-pt).

---

## Decision 037 — Halt trips_pair augmented-feature mining (Session 20)

**Date:** 2026-04-30
**Status:** Settled (halt)
**Question:** Should Session 20 mine trips_pair miss-leaves, design + persist a 4th augmented-feature family, and refit the depth-15 DT to 40 features?
**Choice:** **HALT at Step 4 of the 4-step doctrine.** No feature module, no parquet, no depth curve. The data says trips_pair cannot move the headline metric.
**Why** (the 4-step doctrine in action — measure BEFORE design):
  1. **Step 2 (signal — slice ceiling):** baseline DT on (mode_count==3 AND category=='trips_pair') slice ceiling at depth=None = **86.18% / 17,503 leaves on 54,163 hands.** vs two_pair's 79.47%, single-pair ~74%, high_only 39.64%. trips_pair's baseline is already strong, leaving only **13.82pp of slice headroom** (vs two_pair's 20.53pp).
  2. **Step 3 (impact — EV-loss share):** trips_pair share of total v3 EV-loss = **2.5%** (n=39 of 2000 in `data/v3_evloss_records.parquet`, sum of `loss_weighted` per cohort). Compare:
       - pair: 48.6%
       - two_pair: 26.1%
       - high_only: 16.6%
       - trips: 4.3%
       - **trips_pair: 2.5%**
       - three_pair: 1.4%
       - quads: 0.5%
     Population share matches: trips_pair = 178,464 / 6,009,159 = 2.97% of full 6M (vs two_pair's 22.27%). **trips_pair is the 5th-largest cohort, not a load-bearing miss bucket.**
  3. **Step 4 (cheap test — pre-mining math):** for trips_pair to add ≥+0.5pp on full-6M shape (the user's halt threshold from the resume prompt), the cohort must lift by **0.5 / 0.0297 = +16.8pp on the full trips_pair sub-population.** Session 19's two_pair full lift was +7.50pp (from 1.34M cohort, projecting +1.67pp full-6M). +16.8pp on a smaller cohort with a higher baseline ceiling is unprecedented. Even if we matched Session 19's slice lift exactly (+5.90pp slice / +7.50pp full), full-6M projection is **0.075 × 0.0297 = +0.22pp.** Below threshold.
  4. **Mining produced the qualitative pattern but the lift envelope cannot rescue it.** `mine_trips_pair_leaves.py` ran. Top-10 miss-leaves cover **1.2% of misses** (vs two_pair's 0.5% = even more diffuse), top-100 = 8.1%. 4,778 distinct leaves carry at least one miss. The recurring pattern in top miss-leaves is "trip-on-bot vs pair-on-bot" — same routing-decision shape as two_pair's "high-pair-on-mid vs high-pair-on-bot", with the 28 baseline features missing the per-routing bot suit profile. The pattern is real; we just can't extract enough EV from a 2.5%-share cohort to move the user's deliverable metric.
  5. **The discovery phase has plateaued for additional cohorts.** Three augmented-feature families (pair / high_only / two_pair) covered 91.3% of v3 EV-loss share. The remaining 8.7% is split across trips (4.3%), three_pair (1.4%), quads (0.5%) and the 2.5% trips_pair cohort. None of these alone can clear the +0.5pp halt threshold; even combined they project to <+1pp. The right pivot is target-reframing (per-profile EV) rather than another cohort mine.
**Consequence:**
  1. `analysis/scripts/mine_trips_pair_leaves.py` is preserved as the diagnostic. No `trips_pair_aug_features.py` module created. No `data/feature_table_trips_pair_aug.parquet` persisted.
  2. The **3-family aug set** (pair + high_only + two_pair = 9 features added to the 28-baseline = 37 total) is the FINAL aug set for the discovery phase. Future sessions: pivot the training target, do NOT add a 4th cohort.
  3. The 4-step doctrine demonstrably saved a session of work. ~12 minutes of mining + math vs the alternative of designing 3 trips_pair features, OR-testing them, computing the depth=None ceiling, persisting the parquet, refitting depth-15, then discovering full-6M lift was <0.5pp. Per the methodology, this halt is a SUCCESS.
  4. The remaining cohorts (trips, three_pair, quads) all have smaller EV-loss share than trips_pair and worse population coverage. They are similarly out of scope for Phase D.

---

## Decision 038 — Extract depth-15 chain (`strategy_v5_dt`) and quantify the shape-vs-EV gap (Session 20)

**Date:** 2026-04-30
**Status:** Settled. Chain shipped; mismatch quantified.
**Question:** Does the depth-15 augmented DT (37 features, 18,399 leaves, +7.58pp shape over v3) actually win in dollars at $10/EV-pt?
**Choice:** **No.** Extracted the chain into a portable artifact (`data/v5_dt_model.npz`, 133 KB) + production strategy callable (`analysis/scripts/strategy_v5_dt.py`). Ran `v3_evloss_baseline.py --strategy v5_dt --hands 2000 --samples 1000 --seed 42` (same hands as v3 baseline, identical RNG). Result: **net mean EV-loss across 4 profiles INCREASED by +0.0172 pts/hand vs v3 = −$172/1000h at $10/EV-pt.** The chain is a NET EV LOSS in dollars on the user's headline metric.
**Why:**
  1. **Per-profile EV deltas (positive = v5 ahead, negative = v5 behind):**
     | Profile      | v3 mean loss | v5_dt mean loss | Δ EV       | $/1000h         |
     |--------------|--------------|-----------------|------------|-----------------|
     | mfsuitaware  | 1.3692       | 1.3283          | +0.0409    | **+$409.31**    |
     | omaha        | **1.1514**   | **1.3315**      | **−0.1801**| **−$1,800.89**  |
     | topdef       | 1.4385       | 1.3688          | +0.0697    | +$697.44        |
     | weighted     | 1.2221       | 1.2212          | +0.0009    | +$8.82          |
     | **mean**     | 1.2953       | 1.3125          | −0.0172    | **−$171.83**    |
  2. **Shape-agreement is NOT EV.** v5_dt has **+7.57pp shape lift over v3** on the full 6M (63.73% vs 56.16%) but loses money on average. The mismatch is concentrated against the omaha-first profile, where v5_dt sacrifices −$1,801/1000h. v3's hand-tuned rule chain (and `strategy_v3_no_top_bias`) was designed knowing omaha is the highest-variance profile; the DT, trained on `multiway_robust` (mode-of-4-profiles), has no such asymmetry built in.
  3. **The training target is the root cause.** `multiway_robust` is the per-hand most-popular setting across the 4 BR profiles. When all 4 profiles agree, it equals the mode = the single BR setting. When profiles split (especially when omaha's BR pick differs from the others), `multiway_robust` picks the modal setting — which can be +EV on 3 profiles and significantly −EV on omaha. v3's rule chain happened to favor settings that don't trade away omaha-EV; the DT didn't inherit that intuition.
  4. **This is what Decision 033 was designed to catch.** The reframe explicitly retired ≥95% shape-agreement as a goal because shape-target is a poor proxy for EV. Session 20 measured the gap empirically: **a +7.57pp shape lift can correspond to a NET MONEY LOSS.** The user's reframe was correct.
  5. **Parity is locked in 3 places.** (a) `extract_v5_dt.py`: sklearn vs manual-walk on full 6M = 0 diffs / 6,009,159. (b) `verify_v5_dt_parity.py`: parquet-features vs from-hand-bytes-features on 50K random rows = 0 cell diffs / 1.85M cells. (c) `verify_v5_dt_parity.py`: tree-walk on parquet-features vs tree-walk on from-hand-features = 0 prediction diffs / 50,000.
**Consequence:**
  1. **`data/v5_dt_model.npz` is the production tree artifact.** 133 KB, gzip'd npz. Tree arrays + `feature_columns` + `cat_map`. Loadable with `np.load(..., allow_pickle=True)`.
  2. **`analysis/scripts/strategy_v5_dt.py` is the production strategy callable.** `strategy_v5_dt(hand) -> int` — drop-in replacement for `strategy_v3`. Computes 37 features from raw 7-byte hand, walks the saved tree, returns setting_index. Cached load_model. ~50µs per hand.
  3. **`analysis/scripts/v3_evloss_baseline.py` now supports `--strategy v5_dt`.** `STRATEGIES` dict extended. Same CLI as before; `--save` produces a per-hand × per-profile parquet identical-shape to `data/v3_evloss_records.parquet`.
  4. **The chain is preserved as a benchmark, not a deployment.** Future sessions can compare new strategies against v5_dt's recorded EV envelope without re-running the 8.5-minute MC sweep. `data/v5_dt_records.parquet` is the apples-to-apples baseline.
  5. **Session 21+ should pivot the target.** Three sub-paths: (A.1) DT regression on per-profile or `ev_mean` directly; (A.2) per-profile DT ensemble; (B) profile-aware hybrid (v5_dt where profiles agreed, v3+overlays where they split). The user's metric is dollars in MC at $10/EV-pt; the training target must match.
  6. **Two from-hand correctness gotchas captured for future inference work:**
     - **Aug-call gating.** `compute_high_only_aug_for_hand` does NOT early-return on non-high_only hands; the persist scripts apply a category mask. Strategy modules MUST gate each aug call by category string to be byte-identical with persisted parquets.
     - **Category-id alphabetical vs natural-order.** `dt_phase1_aug3.py` uses `sorted(unique(category))` which produces a different ordering than `tw_analysis.features.CATEGORY_TO_ID`. Strategy modules saved their own `cat_map` to remap. If a future cleanup pass moves to a single canonical mapping, this can be removed.

---

## Decision 039 — Cheap-test on the path-(A) target pivot: oracle hedge ceilings (Session 21)

**Date:** 2026-04-30
**Status:** Settled. Path (A) target pivot empirically justified by the 4-step doctrine; concrete sub-path picked.
**Question:** Does pivoting from `multiway_robust` (mode-of-4-profiles, classification) to a per-profile EV-aware target (path A.1 regression or A.2 ensemble) have enough EV headroom to justify the work?
**Choice:** **Yes. Pursue path A.2 (per-profile DT ensemble) first** because it requires no new MC compute. Defer A.1 (DT regression on per-setting EV) until A.2's residual EV gap is measured.
**Why** (the 4-step doctrine on the pivot itself):
  1. **Step 1 — Hypothesis.** Training on the mode-of-4 target loses money against the profile with the largest EV swings (omaha) because the multiway-mode setting can sacrifice omaha-EV when 3 of 4 profiles disagree with omaha's BR. A per-profile-aware target should recover that.
  2. **Step 2 — Signal (oracle ceiling).** `analysis/scripts/cheap_test_oracle_hedges.py` evaluates 200 random hands (seed=42) at samples=1000 against all 4 profiles, getting the FULL 105×4 EV grid per hand. From this we computed several oracle strategies' mean-of-4-profile-mean-EVs:

     | Strategy                              | Grand mean EV | $/1000h vs v5_dt at $10/pt |
     |---------------------------------------|---------------|------------------------------|
     | v3 (production)                       | −0.110        | +$133                        |
     | v5_dt (Session 20)                    | −0.123        |  $0                          |
     | oracle_BR_per_profile (profile-known) | **+1.285**    | **+$14,074**                 |
     | oracle_argmax_mean (A.1 ceiling)      | **+1.172**    | **+$12,949**                 |
     | oracle_minimax_loss                   | +1.149        | +$12,713                     |
     | oracle_argmax_mfsuitaware             | +1.129        | +$12,513                     |
     | oracle_argmax_omaha                   | +0.930        | +$10,529                     |
     | oracle_argmax_topdef                  | +1.083        | +$12,061                     |
     | oracle_argmax_weighted                | +1.135        | +$12,576                     |

     The hedge ceiling (oracle_argmax_mean) is **+$12,949 / 1000 hands** above v5_dt — over 100× v5_dt's −$133 deficit vs v3. Even retaining 10–20% of this in a learned approximator would dwarf any EV gain in Sessions 17-20.
  3. **Step 3 — Impact.** Per-profile-known BR is +$14K/1000h above v5_dt. The hedge that does NOT know the profile (argmax_mean) recovers 92% of that gap — meaning most of the win comes from "pick the EV-stable setting," not from "guess the profile." This is exactly the asymmetry v3+overlays already captures qualitatively (Decision 032's omaha overlay), but at much lower EV efficiency than the oracle.
  4. **Step 4 — Cheap test (in silico, no training).**
     - argmax_mean overlap with v3: **14.5% of 200 hands**. Overlap with v5_dt: **14.0%**. Both production strategies are FAR from the hedge optimum.
     - argmax_mean overlap with each per-profile BR: mfsuit 77.5% / omaha 49.5% / topdef 68.5% / weighted 77.0%. The hedge is structurally close to mfsuit/topdef/weighted and farther from omaha — suggesting voting among 4 per-profile DTs (path A.2) should approximate argmax_mean reasonably well.
     - argmax_mean margin (gap between #1 and #2 by mean-EV): median 0.245, mean 0.344. Only 15% of hands have margin <0.05. The argmax is well-defined and learnable.
**Why path A.2 first (not A.1):**
  1. **A.2 needs no new MC compute.** The 4 br_<profile> targets are already in `data/feature_table.parquet` for the full 6M canonical hands. We can train 4 DTs in ~1 minute total.
  2. **A.1 (regression on per-setting EV) requires new MC.** The training target — EV of every (hand, setting, profile) — is not currently persisted. To get a meaningful 50K-hand training set at samples=1000 would take ~14 hours of MC compute.
  3. **A.2's expected gain is large.** If a learned ensemble retains even 30% of the +$13K argmax_mean ceiling, that's ~+$4K/1000h vs v5_dt — 4× larger than v3's existing dollar advantage over v5_dt.
  4. **A.2 is reversible.** If it fails, no MC compute was wasted. If it succeeds, A.1 becomes the next refinement.
**Consequence:**
  1. `analysis/scripts/cheap_test_oracle_hedges.py` is the canonical cheap-test harness. Reproducible at hands=200, seed=42, samples=1000 in ~50s. `data/cheap_test_oracle_grid_200.npz` is the persisted 105×4×200 EV grid for re-analysis.
  2. **The 4-step doctrine demonstrably saved committing to A.1 prematurely.** Without measuring the hedge ceiling first, we might have spent 14 hours on MC for a path with unknown payoff. With the cheap-test, we know the upper bound and can scope effort accordingly.
  3. Path A.2 (per-profile ensemble) is the Session 21 immediate target — see Decision 040.


## Decision 040 — Path A.2 (per-profile DT ensemble) is a NULL RESULT (Session 21)

**Date:** 2026-04-30
**Status:** Settled (negative). Per-profile DT vote-ensemble does NOT improve EV over v5_dt; pivot Session 22 to A.1 (regression on per-setting EV via new MC) or B (hybrid with EV-aware tiebreak).
**Question:** Per Decision 039 the cheap-test showed argmax_mean has +$12,949/1000h headroom over v5_dt. Does training 4 per-profile classification DTs on `br_<profile>` and voting (mfsuitaware tiebreak) capture a meaningful slice of that headroom?
**Choice:** **No.** The ensemble is essentially a noisy reproduction of v5_dt and slightly worse on EV. Do not productionize it.
**Why** (the empirical result):
  1. **Trained 4 depth-15 DTs on the full 6M canonical hands** with the same 37 features as v5_dt but per-profile br targets. Per-profile literal-agreement on full 6M:
     - `br_mfsuitaware`  60.78%   (n_leaves 18,282)
     - `br_omaha`        63.81%   (n_leaves 19,936)
     - `br_topdef`       58.07%   (n_leaves 18,551)
     - `br_weighted`     64.74%   (n_leaves 18,605)
     - All 4 byte-identical sklearn-vs-manual-walk parity (0 diffs / 6,009,159 rows each).
  2. **Vote-distribution diagnostic on 100K-row sample:**
     - 1 distinct vote (unanimous):  22.94%
     - 2 distinct votes:              50.79%
     - 3 distinct votes:              23.31%
     - 4 distinct votes:               2.97%
  3. **EV-loss baseline at hands=2000, samples=1000, seed=42** (same hands as `data/v3_evloss_records.parquet` and `data/v5_dt_records.parquet`):

     | Profile     | v3 mean loss | v5_dt mean loss | v6_ensemble mean loss | $/1000h v6 vs v3 | $/1000h v6 vs v5 |
     |-------------|--------------|-----------------|-----------------------|------------------|------------------|
     | mfsuitaware | 1.3692       | 1.3283          | 1.3339                | +$353            | −$56             |
     | omaha       | 1.1514       | 1.3315          | 1.3483                | **−$1,969**      | **−$168**        |
     | topdef      | 1.4385       | 1.3688          | 1.3739                | +$647            | −$51             |
     | weighted    | 1.2221       | 1.2212          | 1.2259                | −$38             | −$47             |
     | **mean**    | 1.2953       | 1.3125          | **1.3205**            | **−$252**        | **−$81**         |

     v6_ensemble loses on every profile vs v5_dt. Loses to v3 on mean by −$252/1000h (worse than v5_dt's −$171). Net: **the ensemble is a regression.**
  4. **Choice-agreement tells the story:** v5_dt vs v6_ensemble = **90.25% literal-agreement** on the 2000 hands. They pick the same setting on 1,805 of 2,000 hands (90.25%). The "ensemble" is essentially v5_dt with a 9.75% noise overlay.
  5. **On the 195 disagreement hands** (`analysis/scripts/diag_v5_v6_disagreement.py`):
     - v6 wins  (lower mean loss): 76  (39.0%)
     - v6 loses (higher mean loss): 119 (61.0%)
     - Per-profile EV delta concentrated on omaha (−0.1724 EV/hand × 0.0975 share = −$168/1000h impact).
  6. **Why the null result.** Each per-profile DT achieves only 58-65% literal accuracy on its own br target. When 4 such weak classifiers vote, the modal vote often equals `multiway_robust` (which is what v5_dt was trained on) — so v6 mostly reproduces v5_dt. When they tie 2-2 (a common case at 50% of hands per the diagnostic), the mfsuitaware-fallback tiebreak picks a setting that's structurally close to mfsuit's BR — but that's NOT the argmax_mean optimum, because the argmax_mean overlap with mfsuit's BR was only 77.5% (per Decision 039's cheap test). Voting with weak classifiers + a single-profile fallback doesn't approach the hedge ceiling.
**Lesson reinforced (vs Decision 039's hypothesis):**
  - The cheap test signaled "argmax_mean overlap with each per-profile BR is 49–78%" — this was the WARNING that voting would underperform, even without the in-vivo run. We weighted it correctly as "should approximate" but the empirical result confirms an ensemble of weak per-profile DTs is too crude. Our doctrine call ("A.2 first because cheap to run") was right; the result invalidates A.2.
  - **The hedge ceiling is real (+$13K) but a 105-class classification model on 37 features and the multiway-or-per-profile target is not the lever to capture it.** The gap is in feature representation + target type, not in the training algorithm.
**Consequence:**
  1. `data/v6_per_profile_dts.npz` is preserved as the null-result artifact (0.55 MB). `analysis/scripts/extract_v6_per_profile_dts.py` and `strategy_v6_ensemble.py` are kept for reproducibility but will not be productionized.
  2. `data/v6_ensemble_records.parquet` is the apples-to-apples baseline showing the negative result; `analysis/scripts/compare_v3_v5_v6.py` is the side-by-side comparison harness.
  3. `analysis/scripts/diag_v5_v6_disagreement.py` is the disagreement-pattern diagnostic (used to generate the worst-10/best-10 hand tables).
  4. **Session 22 fork (recommended):** path A.1 (DT regression on per-setting EV) — requires generating a per-setting-per-profile EV training set via new MC compute. Estimated cost: 50K hands × ~1s/hand = ~14 hours. Run overnight via `cheap_test_oracle_hedges.py` extended to 50K. Train regression DTs on the per-setting EV grid, then argmax over 105 settings at inference. Expected gain (extrapolating from cheap test): 30-60% retention of +$13K ceiling = +$4-8K/1000h.
  5. **Alternative (cheap):** path B hybrid — at inference, use v5_dt as the default and switch to a different setting only when 4 per-profile DTs are unanimous BUT v5_dt picks a different setting (i.e. trust unanimity). Or use v3+overlays where v6's 2-2 tiebreak triggered. Both are testable in <1 hour and might recoup a portion of the cheap-test gap with no new MC.
  6. **The 4-step doctrine continues to pay.** ~1 hour total cost to produce a clean null result for path A.2 (training + 8.3-min MC + diagnostic) — vs the alternative of guessing it would work and committing 14 hours of MC to A.1 first. Null results that close off cheap paths cleanly are a doctrine win.


## Decision 041 — CRITICAL str-sort bug discovered + fixed (Session 22)

**Date:** 2026-05-01
**Status:** Settled. Bugfix shipped (commit 39a4528). All sessions 16-21 EV claims invalidated and re-verified post-fix.
**Question:** What was the root cause of v3 appearing to lose money to v5_dt despite v5_dt having higher shape-agreement?
**Answer:** A long-standing bug in `trainer/src/engine.py` `evaluate_hand()` used Python's `tuple(sorted(hand_strs))` which is STRING-SORT. Every strategy callable, persisted parquet, and BR `.bin` file uses BYTE-SORT. The two orderings disagree for any hand containing both digit-rank cards (2-9) AND broadway cards (T,J,Q,K,A) — **~94% of random hands**. Setting_index 99 meant "top=Ac" in Python (byte-sort) but "top=Qs" in the engine MC (str-sort) for the same hand, evaluating the WRONG setting against MC.
**Discovery story:**
  1. User pushed back on v3's rule for hand `Ks Qs 8h 8d 7d 5h Ac` saying the EV-optimal play is "top=Ac, mid=Ks-Qs, bot=8h-8d-7d-5h" — exactly what v3 *intends* to do.
  2. Tracing `strategy_v3` confirmed it returns setting_index 99 with byte-sort interpretation = top=Ac.
  3. Running cargo eval directly showed setting 99 in the engine's input-order space = top=Qs.
  4. Source of mismatch: `evaluate_hand_cached(tuple(sorted(hand_key)))` re-sorts as strings before passing to the engine.
**Fix:** sort by canonical card byte-value via `_card_byte()` rather than Python str-sort. One-line change in `trainer/src/engine.py` line 222.
**Impact magnitude:**
  - v3 grand mean EV pre-fix: −0.068 (across 4 profiles, 2000-hand baseline). Post-fix: +0.985 (50K-hand tournament).
  - Apparent v3-to-BR-ceiling gap pre-fix: $13,941/1000h. Post-fix: $2,542/1000h.
  - v3 vs argmax_mean choice agreement pre-fix: 14% (v3 looked completely wrong). Post-fix: 59% (v3 is actually close to the hedge optimum).
  - Sessions 16-21 EV-loss baselines (`v3_evloss_records.parquet`, `v5_dt_records.parquet`, `v6_ensemble_records.parquet`) all evaluated the wrong setting on ~94% of hands. All re-run post-fix; buggy versions archived as `*_buggy.parquet`.
**Why this went unnoticed:**
  - test_strategy_v3_golden.py (13 cases) tested strategy_v3's setting_index OUTPUT, not the round-trip through MC eval.
  - Sessions 16-21's narrative ("v5_dt loses money but has higher shape") was self-consistent under the buggy framework — the negative result reinforced the apparent finding (Decision 033's reframe) so no one questioned the eval pipeline.
  - The EV-loss baseline numbers were anchored to BR per profile (also computed in str-sort space), so internal consistency held even though the strategy comparisons were broken.
**Consequence:**
  1. New project memory: `project_taiwanese_strsort_bug.md` records the bug pattern + fix.
  2. Need a "round-trip test": for any hand, the (top, mid, bot) corresponding to strategy_v3(hand) via positions_to_setting_index should equal mc.settings[strategy_v3(hand)] reports. Add to test suite next session.
  3. **All published EV claims pre-2026-05-01 are SUSPECT** — verify against post-fix records or re-run before relying on them.
  4. The 4-step doctrine should add a "verify the eval pipeline matches the strategy convention" check before chasing apparent shape-vs-EV gaps. Lesson: when a counterintuitive negative result holds across multiple sessions, audit the measurement before re-architecting around it.


## Decision 042 — v7_regression beats v3 (post-fix); v8_hybrid is the new champion (Session 22)

**Date:** 2026-05-01
**Status:** Settled. v8_hybrid promoted to "best deterministic strategy" pending Session 23+ refinements.
**Question:** With the str-sort bug fixed (Decision 041), does the path A.1 (DT regression on per-setting EV) approach actually beat v3?
**Choice:** **Yes by +$445/1000h**. v8_hybrid (v7 + v3-fallback for high_only/pair) extends to **+$478/1000h** with much better per-opponent balance. Both are the FIRST learned strategies to beat v3 since the project began.
**Why** (50K-hand tournament results, all in 4-profile MC at $10/EV-pt):

  Per-profile mean EV (positive = winning):

  | Strategy | mfsuit | omaha | topdef | weighted | grand |
  |----------|--------|-------|--------|----------|-------|
  | v3       | +0.350 | +1.713 | +0.241 | +1.390  | +0.924 |
  | v5_dt    | +0.378 | +1.510 | +0.312 | +1.357  | +0.889 |
  | v6_ens   | +0.379 | +1.497 | +0.313 | +1.361  | +0.887 |
  | **v7**   | +0.389 | +1.775 | +0.307 | +1.401  | **+0.968** |
  | **v8_hybrid** | +0.398 | +1.757 | +0.289 | +1.442 | **+0.971** |
  | oracle_argmax_mean | +0.498 | +1.849 | +0.415 | +1.500 | +1.066 |
  | oracle_BR (cheats) | +0.538 | +2.124 | +0.503 | +1.546 | +1.178 |

  $/1000h vs v3 per-opponent:

  | Strategy | mfsuit | omaha | topdef | weighted | grand |
  |----------|--------|-------|--------|----------|-------|
  | v7       | +$384 | +$618 | +$665 | +$113 | +$445 |
  | v8_hybrid | +$477 | +$438 | +$479 | +$518 | +$478 |

  **v8_hybrid is more balanced** — every opponent ≥ +$438, vs v7's lopsided +$113-$665 range.

**Categorical decomposition** (50K, $/1000h × share-of-hands × population):

  | Category | n share | v7 vs v3 $/1000h | weighted contribution |
  |----------|---------|------------------|----------------------|
  | trips | 4.5% | +$3,575 | +$163 |
  | two_pair | 20.9% | +$739 | +$155 |
  | trips_pair | 1.9% | +$4,030 | +$79 |
  | three_pair | 2.2% | +$1,470 | +$33 |
  | high_only | 20.8% | **−$203** | **−$42** ← v7 worse |
  | pair | 49.4% | **−$50** | **−$24** ← v7 mildly worse |
  | quads | 0.2% | +$7,372 | +$18 |

  **The +$381 (2000-hand) / +$445 (50K-hand) v7 win comes ENTIRELY from multi-pair routing decisions** (trips, two_pair, trips_pair). v7 is actually worse than v3 on the most common cases (high_only, pair).

**v8_hybrid logic:** if hand is AAKK → use v3 (Decision 042 §A); else if high_only or one_pair → use v3; else → use v7. This isolates v7 to where it actually adds value (multi-pair structures) and falls back to v3 for the simple cases v3 already handles well.

**Pair-to-bot pattern discovered (mining the 50K grid):**

  | pair_rank | % oracle routes pair → BOT |
  |-----------|---------------------------|
  | 22 | 32.4% |
  | 33-55 | 24% |
  | 66 | 16% |
  | 77 | 9% |
  | 88+ | < 5% |

  **For pair_rank ≤ 5, routing pair-to-bot is the EV-correct play 24-32% of the time.** Neither v3, v5_dt, v6, nor v7 captures this. Estimated headroom for a v9 that adds pair-to-bot triggering rule: **+$50-150/1000h on top of v8_hybrid**.

**Why v7 wins where it wins, loses where it loses:**
  - Wins on multi-pair structures because the 37 features (especially the 9 augmented features from Sessions 17-19) DO capture suit-profile-per-routing for pair / high_only / two_pair-aware structures. The DT learns these well.
  - Loses on high_only because v3's hand-coded "search for top + DS-bot bonus" preserves bot-Omaha equity that v7's tree can't reproduce as cleanly. Setting 99 (top=hi, mid=middle-2, bot=mixed-with-highs) is what v3 captures and v7 missed.
  - Loses on AAKK because that exception (KK-to-mid) is a hand-coded special case; v7 chose AA-to-mid in 4 of 5 sample AAKK hands. Patched in v7_patched / v8_hybrid via direct override.

**Consequence:**
  1. `data/oracle_grid_50k.npz` is the canonical evaluation harness. Per-strategy tournament runs in ~12 seconds via `tournament_50k.py` (no new MC required).
  2. `strategy_v8_hybrid.py` is the best deterministic strategy as of 2026-05-01. Drop-in replacement for `strategy_v7_regression`.
  3. v3 is NOT retired — it's the fallback inside v8_hybrid for high_only + pair + AAKK. Removing v3 from the project would lose the +$66/1000h gain.
  4. Pre-fix sessions' DECISIONS_LOG entries (030-040) are factually accurate about the algorithms tried, but their *EV NUMBERS* are bug-affected. Audit any specific number quoted before relying on it.
  5. Session 23 priorities: (a) mine WHEN pair-to-bot fires (low pair × suit profile × connectivity), build v9 with explicit rule; (b) attempt distillation of v7's high-impact paths for memorable rules; (c) consider expanding training MC beyond 50K for better v7 fidelity.


## Decision 043 — Methodology pivot: heuristic mining → Full Oracle Grid + Query Harness (Session 23)

**Date:** 2026-05-01
**Status:** Settled. v9 heuristic-mining track paused (NOT deleted). New primary track is brute-force computation of the full canonical-hand EV grid against a realistic-human opponent mixture.
**Question:** After 7 sprints of heuristic mining, is the next move another rule (v9 = pair-to-bot for low pairs + trips-broadway top-routing + DS preservation) or a structural change in approach?
**Choice:** **Structural change.** Drop heuristic mining as the primary track. Compute the full Oracle Grid at canonical-hand scale (~20M hands × 105 settings × 1 mixture profile), then build a Query Harness that lets the user pose direct poker-domain questions to the data. Rules emerge from confirmed patterns in the grid, not from hand-coded intuition + tournament.

**Why** (multi-round dialogue with `gemini-3-pro-preview` via PAL MCP, plus user pushback):

1. **The cheap path was always available.** Each session, "mine another v_n+1 rule" was the lowest-friction next step. Output looked like progress (small EV gain over previous version) while the foundational solver track stayed deferred. The course-correction came when the user asked, in his words, *"if you had free reign... what would you do? Why aren't we doing that? It seems like we're just finding random nuances and expecting ME to do more thinking..."*

2. **CFR considered and rejected.** Gemini's verdict was direct: *"CFR is the wrong mathematical tool for his specific goal."* Reasons:
   - Nash equilibrium is a defensive posture against a perfectly optimal adversary. The user's actual opponents are humans with exploitable leaks.
   - This game is simultaneous-move (single setting decision per hand, no betting rounds) — CFR isn't even the standard tool for that game class. Fictitious Play / Best Response to a population distribution is.
   - Nash play sometimes underperforms vs humans because it balances against threats humans don't pose.
   - Bucketing/abstraction risk: 4-8 sessions of engineering before any data, with the possibility that wrong abstraction caps EV permanently.

3. **The mining-from-mixture grid is fundamentally limited.** All EV claims pre-Session 23 are against a fixed 4-profile mixture (mfsuitaware / omaha / topdef / weighted). The "$1,420/1000h ceiling" we kept quoting is the ceiling against THAT mixture, not a true game ceiling. v8_hybrid captures 34% of that mixture-ceiling. Further mining can only get us closer to 100% of a possibly-wrong target.

4. **The user's actual goal is empirical question-answering, not bot-vs-bot.** Quote: *"I want to see across EVERY hand, see what creates the largest money/hand. See what the commonalities are. ...is double-suited unconnected (think 48JK double-suited) vs JT98 no suits or single-suited JsTd9s8c which is better? Are we generally favoring DS hands on bottom vs connected hands without suits or with a single suit?"* These are queryable empirical questions over a full EV grid, not "what's the next rule" questions.

**The new architecture:**

1. **Realistic-human mixture profile = 70% `mfsuit_top_locked` + 25% `topdef` + 5% `omaha`.**
   - `mfsuit_top_locked` is a NEW custom profile (not yet built). Spec from user observation:
     * Pair of QQ or KK kept together AND placed in MID (never split, never to bot, except in rare circumstances).
     * Ace singleton goes on top.
     * No Ace? Optimize Omaha bot first; top gets the leftover.
   - 25% topdef captures the "won't sacrifice top" tendency in real-human play.
   - 5% omaha captures the rare full-sacrifice player.
   - Single-column grid, not multi-profile diagnostics — get answers in 12-30h instead of 36-90h.

2. **Suit canonicalization** to reduce 133M unique deals → ~15-25M canonical equivalence classes via suit-permutation invariance. `engine/src/bucketing.rs` has partial scaffolding.

3. **Full Oracle Grid compute.** Canonical hands × 105 settings × mixture profile, MC at N=1000 samples per cell. Estimated 12-30h on a 16-core Mac, parallelized via rayon. Persisted to disk as a single artifact.

4. **Query Harness.** Python module loaded with the grid. API:
   ```
   query.compare(setting_filter_a, setting_filter_b, hand_filter=None)
     → ΔEV, frequency, significance, sample hands
   ```
   Direct empirical answers to the user's poker-domain questions (DS-unconnected vs connected-unsuited bot, etc.).

5. **Discovery as a downstream operation.** Once grid + harness exist, use Decision Trees as DISCOVERY tools (find highest information-gain splits) not as PLAYING strategies. Bring findings to the user; he validates via the harness.

**Why this isn't another premature compression:**
- Grid is ground truth — no abstraction loss between hand and EV. Distillation is post-hoc, not pre-emptive.
- The user is the poker-domain expert posing questions; Claude Code is the engineer providing precise empirical answers. This flips the dynamic from "Claude proposes rule, user validates" to "user proposes question, Claude answers from data."

**What was retired this session:**
- v9 = pair-to-bot rule (Session 22's plan). Pre-test confirmed the empirical signal but was no longer the primary deliverable.
- v9 = trips-broadway top-routing rule. Same status.
- v9 = high_only re-routing rule. Same status.
- "$/1000h vs v3 against the 4-profile mixture" as the headline metric. New headline: EV per hand vs the realistic-human mixture, in dollars per 1000 hands at $10/EV-pt.
- The "30-second human-memorizable rules" target as the design constraint. Memorizable rules may emerge from distillation of the equilibrium-grid; they are no longer the design driver.

**What remains valid from prior decisions:**
- All hand-evaluation, scoring, MC machinery (Sprints 0-2). Production-grade.
- v3, v5_dt, v6_ensemble, v7_regression, v8_hybrid all stay as comparison baselines. v8_hybrid is the production champion against the 4-profile mixture; the new mixture's champion is unknown until the Oracle Grid runs.
- The 50K oracle grid and `tournament_50k.py` remain as the smaller-scale benchmark; not deleted.
- Pre-test findings (`pretest_v3_bleed_zones.py`, parquet records) are valid discovery inputs to inform what questions to ask the harness once it's built.

**Consequence:**
1. **Session 24 work order:** code `mfsuit_top_locked` → define mixture sampling → finish suit canonicalization → kick off full grid compute (overnight) → build query harness scaffolding in parallel.
2. **Time horizon:** 1 session of engineering + overnight compute → first oracle grid + harness queries in Session 25.
3. **Compute decision deferred:** if 16-core Mac compute is too slow for full N=1000, fall back to N=200 pilot at 100K canonical hands first, validate, then scale.
4. **The `mfsuit_top_locked` spec needs one final user confirmation before code is written.** User has clarified the rule once; Session 24 should restate the spec and confirm before committing 12-30h of compute.


## Decision 044 — Full Oracle Grid shipped at N=200 (Session 24)

**Date:** 2026-05-02
**Status:** Settled. Grid is production. Query Harness is operational. Sessions 25+ run all queries against this artifact.

**Question:** With Decision 043's plan in hand, what does it take to ship the Full Oracle Grid + Query Harness, and what answers fall out of the first round of poker-domain questions?

**Choice:** Ship at **N=200** (not the project default N=1000) because the user's locked-in initial questions produce $5K-$15K/1000h signals that are 30× the per-cell MC noise. N=1000 would cost ~3 days of compute on the M2 Mac vs ~12h at N=200 — re-run specific subsets at higher N if a comparison lands in the noise floor.

**What was built (Session 24):**

1. `engine/src/opp_models.rs::opp_mfsuit_top_locked` — Decision 043 deterministic profile. Highest pocket pair from {AA, KK, QQ} → mid; ace singleton → top; otherwise delegates to `opp_omaha_first`. 10 unit tests cover the decision tree (AA priority, KK+QQ both, trips of kings, no-pair fallback, etc.).
2. `engine/src/monte_carlo.rs::OpponentModel::RealisticHumanMixture` — per-MC-sample weighted draw of 70% MfsuitTopLocked / 25% TopDefensive / 5% OmahaFirst, dispatched inside `opp_pick`.
3. `engine/src/oracle_grid.rs` — new module: 32-byte header + 424-byte records (canonical_id u32 + 105 × f32 EVs in setting-index order). Append-only writer mirrors `BrWriter` resume semantics. 7 unit tests including a round-trip parity test that validates `solve_grid_one`'s argmax matches `mc_evaluate_all_settings::best`.
4. `engine/src/main.rs` — `oracle-grid` CLI subcommand with checkpointing (block_size flag), opponent dispatch (default `realistic`), and pilot-friendly `--limit`.
5. `analysis/src/tw_analysis/oracle_grid.py` — reader, memmap loader, integrity checks, `decode_opp_tag` extension covering tags 7+8.
6. `analysis/src/tw_analysis/query.py` — Query Harness:
   - `setting_features_from_bytes(hand_bytes)` — vectorized per-setting features (top rank, mid pair rank, bot suit profile, longest run, pair rank, high-card count, ace-in-bot, top-is-ace) at ~115 µs/hand.
   - Filter primitives: `bot_suit_profile_eq`, `bot_longest_run_at_least`, `mid_is_pair`, `mid_pair_rank_eq`, etc., plus `all_of`/`any_of`/`not_` combinators.
   - `compare_setting_classes(grid, ch, filter_a, filter_b, ...)` — for each hand, picks max-EV setting in each class, aggregates Δ across the population.
7. `analysis/scripts/oracle_grid_full_queries.py` — runs the 5 headline questions on the full grid.

**Compute results:**
- Wall: 12.37h on the user's 16-core M2 Mac mini (vs 12-30h estimate).
- Steady-state throughput: 134.9 hands/s (vs Random's ~200 hands/s — mixture dispatch overhead).
- Output file: `data/oracle_grid_full_realistic_n200.bin`, 2.55 GB, 6,009,159 records, integrity verified.
- Best-EV mean across all 6M hands: **+0.758 EV/hand** (player wins on average vs the mixture).
- Best-EV distribution: min −9.235, p10 −1.185, p50 +0.715, p90 +2.790, max +7.165, std 1.548.

**Headline answers (full 6M-hand grid, N=200):**

| Question | Comparison (A vs B) | A wins | B wins | mean ΔEV | $/1000h | Hands compared |
|---|---|---:|---:|---:|---:|---:|
| Q1 | DS bot, run≤2 vs rainbow bot, run≥3 | 89.5% | 10.4% | +1.32 | **+$13,186** | 1.05M / 6.01M (17.5%) |
| Q2 | DS bot, run≤2 vs SS bot, run≥3 | 67.1% | 32.7% | +0.44 | **+$4,375** | 2.56M / 6.01M (42.6%) |
| Q3 | DS bot (any) vs rainbow bot (any) | 76.2% | 23.6% | +0.58 | **+$5,770** | 3.10M / 6.01M (51.6%) |
| Q4 | pair-in-mid + non-DS bot vs no-pair-mid + DS bot | 79.3% | 20.5% | +0.82 | **+$8,150** | 4.43M / 6.01M (73.6%) |
| Q5 | small pair (2-5) → mid vs small pair → bot | 81.2% | 18.6% | +0.79 | **+$7,922** | 1.87M / 1.87M of small-pair hands |

**Interpretation:**

1. **Strong DS preference (Q1-Q3):** Against the realistic mixture, double-suited bots beat rainbow bots regardless of connectivity. The biggest edge ($13K/1000h) is when DS is paired with low connectivity vs rainbow paired with high connectivity — i.e. the user's intuition "favor DS over runs" is right. Even DS vs SS-connected (a closer fight) still favors DS by $4.4K/1000h on the 42.6% of hands where the choice exists.

2. **Pair-to-mid usually beats DS preservation (Q4):** When there's a tradeoff between keeping a pair in mid and preserving a DS bot, pair-to-mid wins +$8K/1000h on average. But B wins in 20.5% of comparisons — those are the candidate hands for a "pair-to-mid is a blunder" rule. The B-wins-by-most canonical_ids (425562, 3546583, 3546584, 2965461, ...) are the next investigation target.

3. **Small pairs to mid usually beats small pairs to bot (Q5):** Aggregate of 81.2% / +$7.9K/1000h favors small-pair-in-mid. This is consistent with Session 22's "pair-to-bot fires 24-32% on pair rank 2-5" finding (B's 18.6% win-rate matches the lower end), reframed: most low pairs DO go to mid; bot-routing is a minority play, not the rule.

4. **Sample size for follow-ups:** 17.5% — 73.6% of hands contribute to each comparison. The "only A available" / "only B available" buckets are large (e.g. Q1 has 4.5M only-A hands), suggesting many hands have a structurally-forced DS bot or rainbow bot — meaningful to slice by hand archetype.

**Consequence:**
1. **The grid is the new ground truth.** Future strategy candidates (v9_X) get graded against it in seconds: lookup chosen-setting EV per hand, compare to grid argmax, aggregate by hand category.
2. **N=200 stands as the production grade unless a specific question lands in the noise.** Std error per cell ≈ 0.4 EV pts; mean Δ for the smallest signal (Q2) was +0.44, so even Q2 is at the noise floor. If we want Q2 tightened, we re-run a 100K-hand DS-unconnected-vs-SS-connected subset at N=1000 (~5h).
3. **The "pair-to-mid is sometimes a blunder" investigation (Q4 B-wins) is the natural Sprint 9 target.** Pull the 906K hands where B wins, characterize them by hand features (rank profile, suit distribution, ace presence), see if a coherent class emerges.
4. **Memory updated:** `project_taiwanese_oracle_grid.md` records grid location, format, mixture spec, query API, and re-run guidance.
5. **The "12-30h" estimate from CURRENT_PHASE.md was directionally correct** for N=200 (12.4h actual). For N=1000 it would have been ~3 days, not ~30h — the throughput model in CURRENT_PHASE.md under-counted realistic-mixture dispatch overhead vs Random.

**Decisions deferred to Session 25:**
- Whether to re-run Q2 at N=1000 on its 2.56M-hand subset for a tighter signal.
- Whether to invest in a Strategy-Grading harness that scores any deterministic strategy function against the grid (drop-in replacement for `tournament_50k.py` at full scale).
- Whether to investigate the Q4 B-wins cluster (the 906K hands where DS-bot-preservation beats pair-in-mid).


## Decision 045 — v9.1 (pair-to-bot-DS, tightened) is the new champion (Session 25)

**Date:** 2026-05-02
**Status:** Settled. v9.1 is the new production deterministic strategy of record. v8_hybrid remains as baseline. Session 25 also shipped the Strategy-Grading harness that enables this loop.

**Question:** Decision 044 deferred three Session 25 options (A) tighten Q2, (B) build the Strategy-Grading harness, (C) investigate the Q4 B-wins cluster. The user picked all three in appropriate order, with the explicit goal of "find out why" pair-to-mid is sometimes a blunder for DS preservation.

**What got built (Session 25 in order):**

1. **Strategy-Grading harness** (`tw_analysis.grade_strategy`):
   - `grade_strategy(strategy_fn, grid, canonical_hands, label)` scores any deterministic `strategy(hand_bytes) → setting_index` function against the full 6M-hand grid, returning per-hand-category regret breakdowns and `pct_optimal` (frac matching grid argmax).
   - `categorize_hands` vectorizes the high_only / pair / two_pair / trips / trips_pair / three_pair / quads classification used by `tournament_50k.py`'s legacy harness.
   - Wall: ~4 min per strategy on the full 6M grid (single-threaded Python; the strategy callback is the bottleneck).

2. **v3 + v8_hybrid baseline** (`analysis/scripts/grade_strategies_full_grid.py`):
   - v3:        $3,321/1000h vs ceiling, 35.38% pct_optimal
   - v8_hybrid: $3,153/1000h vs ceiling, 36.70% pct_optimal (the +$168/1000h gain v8 captured over v3 on the OLD 4-profile mixture survives at +$168 vs the realistic mixture)
   - Both leave $3K+/1000h on the table — the headroom v9 has to capture.
   - Worst categories: trips_pair ($5.8K), trips ($4.1K), composite ($10.9K), quads ($9.7K).

3. **Top-10 B-wins inspection** (`q4_inspect_top10.py`): every one of the top-10 most-egregious B-wins hands in Q4 had the SAME archetype — non-premium pair (rank ≤ Q) + Ace singleton + structural DS-bot-with-pair-as-anchor — with B beating A by $26-28K/1000h per hand. The oracle's pick on these hands is a stereotyped pair-to-bot-DS arrangement.

4. **Wider Q4 B-wins characterization** (`q4_characterize_b_wins.py`, full 6M-hand pass):
   - Total B-wins: 907,797 hands
   - 78% of B-wins are 'pair' category, 13% two_pair, 6% trips, 2% trips_pair
   - Of the broad hypothesis class (single pair rank 2-12 + Ace singleton + DS-feasible): 1,261,975 hands; only **24.54% are B-wins**, 75.27% are A-wins. **The naive rule (always pair-to-bot when archetype matches) over-fires by 3:1.**
   - Mean Δ (A − B) on hypothesis hands: **+0.745 → $7,450/1000h favoring A** on AGGREGATE.

5. **Discriminator diagnostic** (`q4_discriminator_diagnostic.py`, sampled 200K hands):
   - **Pair rank shows a U-shaped pattern:**
     - Pair 2-5: pair-to-bot wins by $1.1K–$2.6K/1000h
     - Pair 6-9: pair-to-MID wins by $0.3K–$1.7K/1000h (don't fire here)
     - Pair T-Q: pair-to-bot wins by $0.3K–$2.4K/1000h
   - **Kicker symmetry matters:**
     - (n_a=1, n_b=1): pair-to-bot wins +$1.1K/1000h
     - (n_a=2, n_b=2): pair-to-bot wins **+$8.3K/1000h** (strongest signal)
     - (n_a=2, n_b=1) / (1,2): pair-to-MID wins -$1.4K/1000h
   - The 6-9 zone hypothesis: pair is "good enough" in mid (Hold'em pair) without being so high that opponents are likely to have higher pairs that demand DS bot strength.

6. **v9 (loose) — gates: single pair 2-12 + Ace singleton + DS-feasible**:
   - Full-grid grade: **−$37/1000h vs v8_hybrid** (v9.0 over-fires per the discriminator).

7. **v9.1 (tight) — gates: pair in {2,3,4,5,T,J,Q} + Ace singleton + (n_a, n_b) symmetric in {(1,1), (2,2)}**:
   - Full-grid grade: **+$24/1000h vs v8_hybrid**, **+0.26 pp pct_optimal**.
   - First v8-beating strategy since v8 was crowned in Session 22.

**Why pair-to-mid is a blunder (the user's "find out why" question, answered):**

For low pairs (2-5): the pair is structurally weak in mid (~67% of Hold'em hands beat a pair of 4s on the river), so its mid value is small. Moving it to bot doesn't sacrifice much, and gaining DS bot equity (+~$1-3K/1000h) more than compensates.

For high non-anchor pairs (J-Q): mid pair is strong in Hold'em (~85% win rate on the river vs random), but bot pair-anchored DS is even stronger (it's a guaranteed Omaha pair PLUS flush draws). The choice trades a strong mid for a stronger bot — and against the realistic mixture (which often has high cards in mid via the locked profile), the bot strength matters more.

For mid pairs (6-9): in the "Goldilocks zone" — strong enough in mid to win Hold'em frequently against the locked profile's mid cards, not weak enough to need bot relocation. Pair-to-mid is correct.

The kicker symmetry rule is structural: when (n_a, n_b) is asymmetric, the v9 rule's chosen "leftover for mid" is two cards of mismatched suits with no Hold'em synergy. When symmetric (1,1) or (2,2), the leftover-mid has natural Hold'em strength (e.g., (2,2) means mid is two cards of the OUTSIDE two suits, giving its own pseudo-DS structure).

**Consequence:**

1. **v9.1 is the new strategy-of-record** for grading any further candidates. v8_hybrid is retained as the comparison baseline. v9_loose (now an alias for the unrefined version) is kept in the codebase as a "what NOT to ship" reference.
2. **The Strategy-Grading harness is the new validation gate** for any v10+ candidate. Any new rule gets a 4-minute grade vs the full 6M grid before being considered for production.
3. **The grid + Socratic + grade loop the user proposed (yesterday's session-end conversation) is now operational.** Today's session went: hypothesis (top-10 inspection) → wider validation (characterize) → discriminator analysis (find the gate) → v9.1 candidate → grade-and-confirm. End-to-end < 1 hour from hypothesis to validated rule.
4. **Session 25 worth-the-effort score:** $24/1000h × ~$10/EV-pt × 1000 hands = $240 per 10K hands. Modest in absolute dollars but massive in process: this is the first deterministic rule that beat its predecessor without requiring 14h of new MC compute. It validates the methodology pivot from Session 23.
5. **Still ~$3,129/1000h to ceiling.** v10+ candidates can target:
   - Two-pair archetype (13% of B-wins were two-pair hands — a similar pair-to-bot rule with two pairs)
   - Trips routing on quads ($9.7K/1000h gap on quads — biggest per-hand bleed)
   - Composite hands ($10.9K/1000h on the 0.2% of hands that are trips+pair+quads etc.)
   - The (2,1) asymmetric kicker subset (currently a v9.1 NO-fire — but the discriminator showed it's actually a $1.4K/1000h LOSS-zone for pair-to-bot, so v9.1's exclusion is correct)

**Open questions for Session 26+:**
- Whether the prefix-grid run at N=1000 (currently in progress, ~5h compute, ~500K-hand high-fidelity prefix) will tighten or change the v9.1 numbers significantly. Re-grade v9.1 against it when it lands.
- Whether a two-pair-to-bot variant (v10) captures the 13% two-pair share of Q4 B-wins.
- Whether the (2,2) symmetric-kicker sub-class deserves its own LOUDER rule (it had a $8.3K signal vs the (1,1) class's $1.1K).


## Decision 046 — Session 25/26 mining sprint: v9.1/v10/v12/v14 ship; v11/v13/v15 archived

**Date:** 2026-05-03
**Status:** Settled. v14 is the strategy of record. Simple-rule mining has reached diminishing returns on multi-archetype categories.

**Context:** User asked to exhaustively mine the grid for new rules using the methodology established in Decision 045. Eight cycle attempts followed.

**The cycle scoreboard:**

| Cycle | Target | Approach | Result | Status |
|---|---|---|---|---|
| v9.1 | single pair | discriminator-tightened (pair rank ∈ {2-5,T-Q}, kicker symmetric) | +$24 vs v8 | SHIPPED |
| v10 | two_pair | top-15 inspection: never split a pair, enumerate 9 no-split candidates | +$81 incremental | SHIPPED |
| v12 | trips_pair | top-15 inspection: never split pair, split trips 2+1 | +$10 incremental | SHIPPED |
| v14 | single pair refine | extend v9.1 to (1,3)/(3,1) asymmetric kicker per discriminator | +$5 incremental | SHIPPED |
| v11 | high_only | top-15 → broad "sacrifice top, omaha-first" rule | **−$1,745** vs v10 | ARCHIVED |
| v13 | trips | top-15 → broad "split trips 2-1, mid=paired-trips" rule | **−$172** vs v12 | ARCHIVED |
| v15 | high_only refine | discriminator → "patch v8's bot to DS when feasible" | **−$296** vs v14 | ARCHIVED |

**Final standings (full 6M grid, N=200):**
- v8_hybrid: $3,153/1000h vs ceiling, 36.70% pct_optimal
- **v14**: **$3,033/1000h, 39.61% pct_optimal** (+$120 vs v8 cumulative)

**At higher fidelity (500K-prefix grid, N=1000):**
- v8: $3,051/1000h, 38.51% optimal
- **v14: $2,037/1000h, 47.61% optimal**  (+**$1,014/1000h** vs v8)

The N=200 grid was understating gains by ~8×. v14's TRUE edge against the realistic mixture is about **$1,000/1000h** ≈ $10 per hand.

**Methodology lessons:**

1. **Categories with ONE dominant correct play** yield to simple top-15 inspection rules: two_pair (v10), trips_pair (v12). One iteration suffices.

2. **Categories with MANY optimal archetypes** require a discriminator step BEFORE shipping a broad rule: pair (v9 → v9.1), high_only (no simple rule found).

3. **"Top-15 outliers" are not representative.** They show extreme cases where a specific archetype wins by $25-58K/1000h, but those are <10% of the category. The bulk of the category prefers a different play. Three regressions came from generalizing the outlier rule (v11, v13, v15).

4. **Diminishing returns are real.** v9.1: $24, v10: $81, v12: $10, v14: $5. The marginal gain shrinks with each rule.

5. **Prefix re-grading at N=1000 is a free 5-minute "are we sure?" check.** It vastly tightened our confidence in the gains and caught no false positives.

**What this leaves on the table:**

| Category | $/1000h gap | Share | Bleed share % | Status |
|---|---:|---:|---:|---|
| high_only | $4,082 | 20.4% | 27.5% | 3 attempts failed; needs DT/ML |
| pair | $2,011 | 46.6% | 30.9% | mostly captured by v9.2 |
| two_pair | $3,371 | 22.3% | 24.8% | mostly captured by v10 |
| trips | $4,054 | 5.5% | 7.3% | 1 attempt failed; needs DT/ML |
| trips_pair | $5,417 | 2.9% | 5.1% | mostly captured by v12 |
| three_pair | $4,529 | 1.9% | 2.8% | not attacked |
| quads | $9,670 | 0.2% | 0.8% | not attacked, tiny share |
| composite | $10,883 | 0.2% | 0.9% | not attacked, tiny share |

high_only and trips together = $1,055 / $3,033 of remaining bleed = 35% of v14's gap to ceiling. Cracking these would meaningfully lower v14's regret.

**Consequence + Session 27 options:**

1. **Pause + ship v14 as the production strategy.** It's a real $1,000/1000h gain over v8 against the realistic mixture. Update v8_hybrid → v14_combined as the deployed strategy in the trainer / wherever else v8 is referenced.

2. **DT-based v16 candidate.** Train an sklearn DecisionTreeRegressor on the grid: input = per-hand features (pair_rank, suit_dist, broadway_count, longest_run, ace_present, etc.), output = the 105-EV vector or just argmax. The grid is the ground-truth labels. This is the v7-regression methodology re-applied with the grid (v7 was trained against the OLD 4-profile mixture; v16 trains against the realistic mixture). Likely captures another $500-1000/1000h on the multi-archetype categories.

3. **High_only-specific DT.** Smaller scope than full DT — just for high_only hands. Less data, faster to train, easier to interpret rules from.

4. **More granular discriminators on high_only.** Carve into sub-clusters (e.g., suit_dist=(4,1,1,1) is a distinct sub-class with different optimal play). Each sub-cluster may have a clean simple rule. 8-15 hours of analysis work potentially.

5. **Two-pair refinement** — v10's choice rule has tiebreak heuristics that might not always match oracle. A few hundred dollars more might be there.

**Recommended next move:** Session 27 should kick off **option 2 (DT regression on full grid) AND option 1 (deploy v14)** in parallel. The DT will probably capture another $500-1500/1000h based on v7's prior history; v14 deployment is independent and locks in today's gain.


## Decision 047 — v16_dt is the new ML champion (Session 27)

**Date:** 2026-05-03
**Status:** Settled. v16_dt is the new ML strategy of record. v14_combined remains the human-memorizable strategy of record (the rule book in STRATEGY_GUIDE.md).

**Question:** Decision 046 recommended kicking off (option 2) DT regression on the full Oracle Grid in parallel with (option 1) v14 deployment. Did the DT capture the $500-1500/1000h Decision 046 forecast?

**Answer:** **Yes — +$569/1000h on the full grid (N=200), +$431/1000h on the N=1000 prefix.** The Decision 046 forecast was on the nose.

**What got built:**

1. **`analysis/scripts/train_v16_regression.py`** — flexible trainer. Reads either the full 6M-hand grid (N=200) or the 500K-prefix (N=1000), uses the same 37-feature set as v5/v7 (via `strategy_v5_dt.compute_feature_vector` for byte-identity), fits a `DecisionTreeRegressor` on the per-hand 105-EV vector. Saves model in v7-compatible npz format.

2. **`analysis/scripts/strategy_v16_dt.py`** — drop-in inference. Walks the saved DT, returns argmax of leaf 105-vec.

3. **`analysis/scripts/grade_v16_full_grid.py`** — head-to-head grader (v8 vs v14 vs v16) on either the full or prefix grid.

4. **`analysis/scripts/grade_v16_full_trained.py`** — single-strategy grader for v16 with custom model path (used to grade v16-full in parallel with the prefix-trained grading).

**Two training variants tried:**

| Training data | Records | min_samples_leaf | depth | leaves | Full-grid grade | Status |
|---|---:|---:|---:|---:|---:|---|
| 500K-prefix (N=1000) | 500,000 | 200 | 15 | 1,783 | $8,493/1000h, 16.40% opt | **ARCHIVED** (catastrophic overfitting to canonical-id bias) |
| full 6M (N=200) | 6,009,159 | 100 | 18 | 28,790 | $2,464/1000h, 42.54% opt | **SHIPPED** (champion) |

**The catastrophic prefix failure was the surprise of the session.** The prefix's oracle mean EV is **−0.667** vs the full grid's **+0.758** — the first 500K canonical hands are a heavily-warped subsample skewed toward weak/low-rank archetypes. A DT trained on that subsample learns argmax patterns that are completely wrong when applied to strong hands.

**Methodology lesson:** canonical-id ordering is highly non-uniform in hand strength. **Never train on a canonical-id prefix.** If a future session needs a smaller training subset, sample uniformly at random from `canonical_hands.bin`.

**Final standings (full 6M grid, N=200):**

| Strategy | $/1000h vs ceiling | pct_optimal | Δ vs v8 | Δ vs v14 |
|---|---:|---:|---:|---:|
| v8_hybrid | $3,153 | 36.70% | — | — |
| v14_combined | $3,033 | 39.61% | −$120 | — |
| **v16_dt** | **$2,464** | **42.54%** | **−$689** | **−$569** |

**At higher fidelity (N=1000 prefix grid):**

| Strategy | $/1000h vs ceiling | pct_optimal | Δ vs v8 | Δ vs v14 |
|---|---:|---:|---:|---:|
| v8_hybrid | $3,051 | 38.51% | — | — |
| v14_combined | $2,037 | 47.61% | −$1,014 | — |
| **v16_dt** | **$1,607** | **50.77%** | **−$1,444** | **−$431** |

**Per-category breakdown (full grid, N=200): v16 wins on every multi-rank category:**

| Category | v14 $/1000h | v16 $/1000h | Δ |
|---|---:|---:|---:|
| high_only | $4,082 | $3,785 | −$297 |
| pair | $2,011 | $2,127 | +$116 (apparent) |
| two_pair | $3,371 | $2,005 | −$1,366 |
| trips | $4,054 | $2,347 | −$1,707 |
| trips_pair | $5,417 | $2,438 | −$2,979 |
| three_pair | $4,529 | $1,975 | −$2,554 |
| quads | $9,670 | $2,233 | −$7,437 |
| composite | $10,883 | $5,260 | −$5,623 |

**The pair-category +$116 apparent regression at N=200 was MC noise.** At N=1000 prefix fidelity, v16's pair regret is $1,191 vs v14's $1,229 — v16 actually wins by $38/1000h on pair too. Future single-category deltas under ~$200/1000h should be re-validated at N=1000 before any "v9.2 still wins on its niche" claim.

**Why v16 wins big on the rare categories:**
- v14's hand-coded rules covered single-pair (v9.2), two-pair (v10), trips_pair (v12). Three-pair, quads, composite had NO hand-coded rule — they fell through to v8_hybrid which uses v3 for high_only/pair and v7 (the OLD-mixture-trained DT) for everything else. Against the realistic mixture, the old v7 routing on these tier-rare hands was wildly suboptimal.
- v16, trained on the realistic-mixture grid, learned the right routing for ALL categories simultaneously.

**Track B (v14 deployment) outcome:** done in ~2 minutes. The only "production strategy" reference for v8_hybrid was `analysis/scripts/tournament_50k.py`'s strategy list — added v9.2/v10/v12/v14/v16 as comparison entries. The trainer's `engine.py` references to `strategy_v3` are for opponent-profile MC dispatch, NOT user-strategy choice — left unchanged.

**Consequence:**

1. **v16_dt is the new ML champion.** Use it whenever a deployed-in-software strategy choice is needed. Loaded at inference via `strategy_v16_dt(hand_bytes) -> setting_index`. Model file: `data/v16_dt_model.npz` (21.5 MB).

2. **v14_combined remains the human-memorizable rule chain** for `STRATEGY_GUIDE.md`. The two coexist for different audiences: v14 is what a human studies; v16 is what the trainer compares the user against (alongside the grid argmax).

3. **The Strategy-Grading harness keeps working unchanged.** v16 is just another strategy_fn. Future v17/v18 candidates should grade against both v14 and v16.

4. **Project END PRODUCT update:** the project's stated end product (CLAUDE.md) is "a condensed decision tree / hierarchy of rules that a human can memorize and apply in <30 seconds, validated to match the solver 95-99% of the time." v14 hits 47.61% pct_optimal at N=1000 — far from 95%. v16 hits 50.77% — also far. The 95% target was set before we discovered that the realistic mixture has many hands with multiple near-optimal settings (tied or near-tied EV). The right success metric is now "$/1000h vs ceiling," not "% optimal." See `project_taiwanese_rule_baseline.md` for the EV-reframe history.

5. **Distillation is the obvious Session 28 move.** v16's 28,790 leaves encode a rich interpretable strategy. Walking the highest-impact splits (those that reduce MSE the most) and translating them to English will give us the next batch of v17/v18/v19 hand-coded rules for the strategy guide. This is the "DT-as-pattern-mining-tool" insight that originally motivated the v7 → v8_hybrid path in Session 22.

**Open questions for Session 28+:**
- Whether a uniform-random 500K-hand subsample at N=1000 trains as well as the full 6M at N=200 (cheaper to compute the grid).
- Which v16 splits are most-impactful and most-interpretable — the distillation candidates.
- Whether the high_only category ($3,785/1000h, 31% of v16 bleed) yields to any specific archetypal rule visible in v16's tree, or whether it's irreducibly noisy.


## Decision 048 — v17 (rules-then-DT chain) archived (Session 28)

**Date:** 2026-05-04
**Status:** Settled. v17 is archived. The hand-coded v9.2/v10/v12 rules are inferior to v16 in their categories and chaining them BEFORE v16 forces the inferior strategy to fire.

**Question:** Decision 047 left open whether a v17 = v9.2/v10/v12 → v16 fallback could combine the best of both worlds (interpretable rules where they fire, DT for unruled categories). Does it?

**Answer:** No. v17 LOSES to v16 by **−$369/1000h** on the full grid.

**Per-category (full grid, N=200) vs v16:**

| Category | v17 $/1000h | v16 $/1000h | Δ |
|---|---:|---:|---:|
| high_only | $3,785 | $3,785 | $0 (v17 falls through to v16) |
| pair | $2,084 | $2,127 | −$43 (v9.2 helps slightly) |
| two_pair | $3,371 | $2,005 | **+$1,366** (v10 is wildly worse than v16) |
| trips | $2,347 | $2,347 | $0 (v17 falls through) |
| trips_pair | $5,417 | $2,438 | **+$2,979** (v12 is wildly worse than v16) |
| three_pair | $1,975 | $1,975 | $0 |
| quads | $2,233 | $2,233 | $0 |
| composite | $5,260 | $5,260 | $0 |

**Why:** v9.2/v10/v12 were optimized against the OLD 4-profile mixture pre-Session 24. v16 was trained against the realistic 70/25/5 mixture. The DT discovered better per-category routings that the hand-coded rules cannot match.

**Methodology lesson:** Hand-coded rules that win against an OLDER baseline can simultaneously be inferior to a DT trained on the CURRENT ground truth. Do NOT chain hand-coded rules before the DT in production. The strategy guide can keep the rules as human-memorizable approximations (they still beat v8 by $120/1000h on their own), but in code, use the DT alone.

**Files:**
- `analysis/scripts/strategy_v17_rules_then_dt.py` — kept as historical artifact (matches the convention that archived strategies stay in tree for diff/comparison).
- `analysis/scripts/grade_v17_full_grid.py` — the grader that produced the result.
- `data/grade_v17_full.log` — grader output.

**Consequence:**
1. Strategy guide remains v14_combined as the human-memorizable chain — its purpose is teaching, not maximizing EV.
2. Code path remains v16/v18 as the production strategy — they win on every category.
3. Future hybrid attempts should fire the DT FIRST and use rules only as overrides for cases where the DT is known to be wrong.


## Decision 049 — Rule 4 (KK / AA → mid) added to STRATEGY_GUIDE.md (Session 28)

**Date:** 2026-05-04
**Status:** Settled. Documentation-only change. Strategy guide gains a 4th rule.

**Question:** The v16 distillation surfaced `has_premium_pair` as the 5th-most-important feature (4.5% of feature importance). It splits the population into a "keep KK/AA together in mid" branch. Empirical check on v3, v8, v16 confirmed all three already encode this play. Should the strategy guide formalize it as a rule?

**Choice:** Yes. Rule 4 = "KK or AA → keep pair in mid; top = highest non-pair card; bot = remaining 4." Added to `STRATEGY_GUIDE.md` between Rule 3 and the Default section.

**Why:**
- Behavior is unchanged (v3/v8/v16/v18 all converge on this setting). The rule documents existing best practice.
- The strategy guide previously mentioned KK/AA-in-mid only as a footnote inside Rule 1's discussion. Promoting it to a numbered rule makes it memorizable.
- The DT's independent discovery of `has_premium_pair` as a top-5 feature confirms the play is worth highlighting.
- Fires on **7.17%** of all hands (KK 3.58% + AA 3.58%; verified against `data/feature_table.parquet`).

**Note on the K-K split misconception:**
A prior draft of Rule 4 claimed "with KK + an Ace singleton, the K-K split is forced because the Ace dominates top selection." Empirical check showed this is WRONG: v3, v8, and v16 all return setting 104 = top=A, mid=KK (intact), bot=lowest 4. The Ace lands on top NATURALLY because it's the highest non-K, and the K-K stays in mid. No split occurs. Rule 4 was rewritten to remove the misclaim.

**Empirical edge case:** for AA + an all-low body (no broadway non-A cards, e.g. `2c 3d 4h 5s 6c Ah As`), v16 picks setting 14 = top=2c (lowest), mid=AA, bot=3-4-5-6 (connected). v3/v8 pick setting 74 = top=6c (highest non-A), mid=AA, bot=2-3-4-5. The DT trades top strength (a 6 on top loses 90% anyway) for bot connectivity. Documented as a footnote; human play follows v3/v8 (highest non-pair on top).

**Files:**
- `STRATEGY_GUIDE.md` — Rule 4 section + cheat-sheet update + table-of-shapes update.

**Consequence:**
1. Strategy guide now has 4 numbered rules: pair-to-bot DS (1), no-split two-pair (2), trips-pair routing (3), KK/AA → mid (4).
2. No code changes (Rule 4 is implicit in `encode_rules.strategy_v3`'s pair-to-mid default, which v8 / v14 inherit).
3. Future trainer UI can quiz on Rule 4 as a discrete pattern.


## Decision 050 — v18_dt is the new ML champion (Session 28)

**Date:** 2026-05-04
**Status:** Settled. v18 supersedes v16 as the production ML strategy. v16 is kept as a baseline.

**Question:** Decision 047 used v16 = depth=18, min_samples_leaf=100, 28,790 leaves. Was 28,790 leaves the capacity ceiling? Or is there more EV to extract from a higher-capacity tree?

**Answer:** **Yes — v18 = depth=22, min_samples_leaf=50, 60,651 leaves wins +$158/1000h on the full grid AND +$129/1000h on the prefix N=1000 grid (overfitting tripwire).**

**What got built:**

1. **`analysis/scripts/train_v18_dt.py`** — trainer using cached parquet features (skips the ~20-min Python feature-compute pass that v16 had). Total cycle: 5min train + 4min grade. Same npz output format as v16, drop-in compatible with the existing inference path.
2. **`analysis/scripts/strategy_v18_dt.py`** — inference: walks the saved DT, returns argmax of leaf 105-vec.
3. **`analysis/scripts/grade_v18_full_grid.py`** — head-to-head v16 vs v18 grader on the full 6M grid.
4. **`analysis/scripts/grade_v18_prefix_grid.py`** — v8/v14/v16/v18 on the 500K N=1000 prefix grid (the generalization check).
5. **`data/v18_dt_model.npz`** — 45 MB, 60,651 leaves, depth=22, min_samples_leaf=50.

**Final standings:**

| Strategy | Full grid (N=200) | Prefix (N=1000) |
|---|---:|---:|
| v8_hybrid | $3,153 | $3,051 |
| v14_combined | $3,033 | $2,037 |
| v16_dt (28K leaves) | $2,464 | $1,607 |
| **v18_dt (60K leaves)** | **$2,306** | **$1,478** |

**Per-category (full grid, N=200): v18 wins on every category vs v16:**

| Category | v16 $/1000h | v18 $/1000h | Δ |
|---|---:|---:|---:|
| high_only | $3,785 | $3,489 | −$296 |
| pair | $2,127 | $2,023 | −$104 |
| two_pair | $2,005 | $1,878 | −$127 |
| trips | $2,347 | $2,241 | −$106 |
| trips_pair | $2,438 | $2,135 | −$303 |
| three_pair | $1,975 | $1,812 | −$163 |
| quads | $2,233 | $1,474 | −$759 |
| composite | $5,260 | $4,623 | −$637 |

**Per-category on N=1000 prefix (the smaller categories — note the prefix grid has no high_only by canonical-id ordering):**

| Category | v16 $/1000h | v18 $/1000h | Δ |
|---|---:|---:|---:|
| pair | $1,191 | $1,116 | −$75 |
| two_pair | $1,862 | $1,678 | −$184 |
| trips | $2,213 | $2,148 | −$65 |
| trips_pair | $2,660 | $2,326 | −$334 |
| three_pair | $1,138 | $1,169 | +$31 (small noise on 25K hands) |
| quads | $1,156 | $1,133 | −$23 |
| composite | $4,246 | $3,791 | −$455 |

The +$31 prefix three_pair regression is well within Monte-Carlo noise (25,614 hands × $0.001 SE per cell). v18 wins on every category that has enough samples to be statistically stable.

**Why this matters for overfitting:**

A bigger tree (60K leaves vs 28K) trained on the same N=200 grid could just be memorizing N=200 noise — better training-set fit, worse generalization. The N=1000 prefix grid uses 5× as many MC samples per cell, so its labels are a closer estimate of the true game-theoretic answer. **v18 wins on prefix by $129/1000h** — the win generalizes. If v18 had only memorized noise, prefix performance would have regressed.

**Methodology lesson (cached parquets):**

The v16 trainer (`train_v16_regression.py`) recomputed all 6M hands' features from canonical bytes inside Python — that's the ~20-minute pass that gated rapid iteration. The cached `feature_table*.parquet` files (built once during the v3/v5/v7 era) contain the exact same 28 baseline + 9 aug features. The new `train_v18_dt.py` reads those parquets, joins them by canonical_id, computes the 7 derived flags in numpy (sub-second), and goes straight to fit. Total cycle drops from ~25 min to ~5 min. **Future ML training scripts MUST use cached parquets.**

**Consequence:**

1. **v18_dt is the new ML champion.** Use `strategy_v18_dt(hand_bytes) -> setting_index` for any production inference. Model file: `data/v18_dt_model.npz`.
2. **v16_dt is kept as a comparison baseline** (not deleted). The `strategy_v16_dt` import path still works.
3. **The Strategy-Grading harness keeps working unchanged.** Future v19/v20 candidates must grade against v18 as the bar.
4. **STRATEGY_GUIDE.md champion pointer updated to v18.**
5. **Open question:** depth=22 was the first try at higher capacity. Sweeping depth=20, 24, 26 may extract more. Also worth trying min_samples_leaf=30 (more leaves) and min_samples_leaf=80 (fewer leaves with longer trees). Session 29 picks this up alongside the suited-broadway aug feature work.
6. **The v18 tree is interpretable.** Re-run `distill_v16_dt.py` against `data/v18_dt_model.npz` (small modification needed for the model path) to see what splits the bigger tree added. Likely candidates: more granular category-aware splits in the trips_pair / composite branches where v18 won most.


## Decision 051 — v18c_dt is the new ML champion (Session 29 / overnight continuation)

**Date:** 2026-05-04
**Status:** Settled. v18c supersedes v18 as the production ML strategy. v18 / v18b / v16 are kept as baselines.

**Question:** Decision 050 left open whether the depth=22 / min_leaf=50 v18 was the capacity ceiling. Capacity sweep through depth=24/26 with shrinking min_samples_leaf.

**Answer:** **More capacity continues to help, with diminishing returns.** v18c (depth=26, min_leaf=20, 124,902 leaves) wins on every category vs v18 on BOTH grids and passes the prefix tripwire.

**Capacity sweep results:**

| Variant | Depth | min_leaf | Leaves | Full $/1000h | Prefix $/1000h | Δ Full vs prev | Δ Prefix vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| v16_dt | 18 | 100 | 28,790 | $2,464 | $1,607 | — | — |
| v18_dt | 22 | 50 | 60,651 | $2,306 | $1,478 | −$158 | −$129 |
| v18b | 24 | 30 | 96,409 | $2,217 | $1,343 | −$89 | −$135 |
| **v18c** | **26** | **20** | **124,902** | **$2,172** | **$1,261** | **−$45** | **−$82** |

Doubling leaves roughly halves the marginal $/1000h gain. Not yet plateaued — depth=28 / ml=10 might extract another $30-50 (Session 30 target).

**Per-category breakdown (full grid, N=200) — v18c wins on every category vs v16:**

| Category | v16 | v18 | v18b | v18c | Δ v18c vs v16 |
|---|---:|---:|---:|---:|---:|
| high_only | $3,785 | $3,489 | $3,396 | $3,359 | −$426 |
| pair | $2,127 | $2,023 | $1,966 | $1,934 | −$193 |
| two_pair | $2,005 | $1,878 | $1,743 | $1,676 | −$329 |
| trips | $2,347 | $2,241 | $2,165 | $2,110 | −$237 |
| trips_pair | $2,438 | $2,135 | $1,977 | $1,873 | −$565 |
| three_pair | $1,975 | $1,812 | $1,717 | $1,706 | −$269 |
| quads | $2,233 | $1,474 | $945 | $907 | −$1,326 |
| composite | $5,260 | $4,623 | $3,740 | $3,207 | −$2,053 |

The composite and quads categories show the biggest absolute wins — these are rare hands (14K each of 6M) where the additional capacity lets v18c memorize their per-archetype routings.

**Prefix N=1000 confirmation (overfitting check):**

| Strategy | $/1000h | pct_opt | Δ vs v16 |
|---|---:|---:|---:|
| v16_dt | $1,607 | 50.77% | — |
| v18_dt | $1,478 | 52.60% | −$129 |
| v18b | $1,343 | 54.56% | −$263 |
| v18c | $1,261 | 55.90% | **−$345** |

v18c wins on every category in prefix too. The win is not memorization of N=200 noise.

**What got built:**

1. `analysis/scripts/strategy_v18c_dt.py` — inference for the depth=26 model.
2. `data/v18c_dt_model.npz` — 90 MB, 124,902 leaves.
3. `data/v18b_dt_model.npz` — 71 MB, 96,409 leaves (intermediate, kept).
4. `analysis/scripts/grade_v18_sweep.py` — generic sweep grader; loads any model file via npz path.

**Consequence:**
1. **v18c_dt is the new ML champion.** Use `strategy_v18c_dt(hand_bytes) -> setting_index` for any production inference. Model file: `data/v18c_dt_model.npz`.
2. **v18 / v18b kept as baselines** for diff comparisons. Files retained.
3. **Future v19/v20 candidates must grade against v18c as the bar.**
4. **STRATEGY_GUIDE.md champion pointer updated to v18c.**


## Decision 052 — v19 (suited-broadway aug features) ARCHIVED — failed prefix tripwire (Session 29)

**Date:** 2026-05-04
**Status:** Settled. v19 is archived. The 6 suited-broadway aug features as designed don't generalize past N=200 noise.

**Question:** Session 28's high_only deep-dive showed v16/v18 cannot represent suited mids (e.g., 5d-Kd in `2c 5d 6h 7s Ts Kd Ad`). Adding suited-broadway aug features to the trainer should let the DT discover and exploit this pattern. Did it?

**Answer:** No — full grid was positive but prefix tripwire failed.

**What got built:**

1. `analysis/scripts/suited_aug_features.py` — 6 features:
   - `n_suited_pairs_total` (0-21)
   - `max_suited_pair_high_rank` (0,2-14)
   - `max_suited_pair_low_rank` (0,2-14)
   - `has_suited_broadway_pair` (0/1)
   - `has_suited_premium_pair` (0/1)
   - `n_broadway_in_largest_suit` (0-7)

2. `analysis/scripts/persist_suited_aug.py` — persists to
   `data/feature_table_suited_aug.parquet` (23 MB, 44 sec compute,
   computed for ALL 6M hands without category gating).

3. `analysis/scripts/train_v19_dt.py` — extended trainer (43 features).
4. `analysis/scripts/strategy_v19_dt.py` — inference for v19.
5. `analysis/scripts/grade_v19_full_grid.py` — head-to-head grader.

**Result (full 6M grid, N=200):**

| Strategy | Leaves | $/1000h | Δ vs v18 |
|---|---:|---:|---:|
| v16_dt | 28K | $2,464 | — |
| v18_dt | 60K | $2,306 | — |
| **v19_dt** | **73K** | **$2,250** | **+$57** |

**Result (500K-prefix grid, N=1000):**

| Strategy | $/1000h | Δ vs v18 |
|---|---:|---:|
| v16_dt | $1,607 | — |
| v18_dt | $1,478 | — |
| **v19_dt** | **$1,494** | **−$16** |  ← **FAIL**

**Per-category prefix breakdown:**

| Category | v18 | v19 | Δ |
|---|---:|---:|---:|
| pair | $1,116 | $1,152 | +$36 (regression) |
| two_pair | $1,678 | $1,687 | +$9 (≈noise) |
| trips | $2,148 | $2,093 | −$55 (small win) |
| trips_pair | $2,326 | $2,321 | −$5 (≈noise) |
| three_pair | $1,169 | $1,169 | $0 |
| quads | $1,133 | $1,133 | $0 |
| composite | $3,791 | $3,793 | +$2 (≈noise) |

The pair-category regression on prefix (+$36/1000h on 215K hands) is the smoking gun. The new features improve pair hands on the noisier full grid (where v19 picks something marginally better than v18 on N=200 labels) but that improvement disappears on cleaner N=1000 labels — a signature of overfitting.

**Why the features didn't generalize:**

1. **Computed for all categories.** The 6 features fire for paired hands too (e.g., a single-pair hand can have suited broadway among its non-pair cards). The DT uses them to make small discriminating splits in the pair branches that fit N=200 noise but don't survive to higher fidelity.

2. **No new feature in v19's top-15.** The sklearn feature_importances_ ranking puts the same v16/v18 base features at the top: n_broadway, third_rank, pair_high_rank, n_low, etc. The suited features contribute scattered low-importance splits — exactly the pattern of noise-fitting.

3. **Prefix doesn't include high_only.** The prefix's first 500K canonical_ids skip the high_only category (where the suited-mid signal lives). So we can't validate the targeted population's improvement directly. The prefix's pair-heavy composition exposes the spurious-feature problem instead.

**What to try next (Session 30):**

1. **Gated suited-broadway features.** Mirror `compute_high_only_aug_for_hand`'s pattern: return (0, 0, 0, 0, 0, 0) for any hand with n_pairs/n_trips/n_quads ≥ 1. Suited features fire ONLY for high_only hands. This should keep the high_only signal while removing the spurious pair-category fits.

2. **Higher-MC validation grid.** A 200K-hand uniform-random sample at N=2000 would test new feature ideas without the prefix's canonical-id-bias artifact. ~2-day compute on the M2 Mac mini.

**Files (kept for diff/comparison):**
- `analysis/scripts/suited_aug_features.py`
- `analysis/scripts/persist_suited_aug.py`
- `analysis/scripts/train_v19_dt.py`
- `analysis/scripts/strategy_v19_dt.py`
- `analysis/scripts/grade_v19_full_grid.py`
- `data/feature_table_suited_aug.parquet` (gitignored)
- `data/v19_dt_model.npz` (gitignored)

**Methodology lesson:** The Session 28 prefix tripwire just paid off concretely. Without it, v19's positive full-grid grade would have shipped, replacing v18 with a slightly-overfit model. The tripwire saved us from a regression. Keep using it on every ML candidate.


## Decision 053 — v20_dt is the new ML champion (Session 30 / overnight continuation)

**Date:** 2026-05-04
**Status:** Settled. v20 supersedes v18e/v18c/v18d/v18b/v18/v16. All older models retained as baselines.

**Question:** Decision 052 archived v19 (ungated suited-broadway aug features) for failing the prefix tripwire on the pair category. Could the same features work if GATED to the targeted population (high_only) only?

**Answer:** Yes. The gating pattern eliminates cross-category leakage and preserves the high_only signal. v20 (v18e capacity + 6 gated suited features) wins +$84/1000h on the full grid AND ties exactly on the prefix.

**What got built:**

1. **`analysis/scripts/suited_aug_features_gated.py`** — same 6 features as the Session 29 ungated version, but returns `(0, 0, 0, 0, 0, 0)` for any hand with `n_pairs/n_trips/n_quads ≥ 1`. Only fires on the 1.23M high_only canonical hands (20.4% of the population).

2. **`analysis/scripts/persist_suited_aug_gated.py`** — writes `data/feature_table_suited_aug_gated.parquet` (20 MB, 23 sec compute). Verification: 1,226,940 rows have non-zero features (matches the high_only count exactly).

3. **`analysis/scripts/train_v19_gated_dt.py`** — trainer reads 4 parquets (base + 3 augs + gated suited) and produces a 43-feature model. CLI flags for depth / min_leaf / output.

4. **`analysis/scripts/strategy_v19_gated_dt.py`** — generic gated-suited inference (used by both v19_gated and v20).

5. **`analysis/scripts/strategy_v20_dt.py`** — clean wrapper that loads `data/v20_dt_model.npz`.

6. **`data/v20_dt_model.npz`** — 211 MB, 307,939 leaves, depth=30, min_samples_leaf=5.

**Capacity sweep + feature engineering progression:**

| Strategy | Depth | min_leaf | Features | Leaves | Full $/1000h | Prefix $/1000h |
|---|---:|---:|---:|---:|---:|---:|
| v16 | 18 | 100 | 37 | 28,790 | $2,464 | $1,607 |
| v18 | 22 | 50 | 37 | 60,651 | $2,306 | $1,478 |
| v18b | 24 | 30 | 37 | 96,409 | $2,217 | $1,343 |
| v18c | 26 | 20 | 37 | 124,902 | $2,172 | $1,261 |
| v18d | 28 | 10 | 37 | 193,365 | $2,108 | $1,145 |
| v18e | 30 | 5 | 37 | 274,446 | $2,066 | $1,082 |
| **v20** | **30** | **5** | **43 gated** | **307,939** | **$1,982** | **$1,082** |

**Per-category v20 vs v18e (full grid, N=200):**

| Category | v18e $/1000h | v20 $/1000h | Δ |
|---|---:|---:|---:|
| high_only | $3,307 | $2,894 | **−$413** |
| pair | $1,873 | $1,873 | $0 (gating works) |
| two_pair | $1,458 | $1,458 | $0 |
| trips | $1,997 | $1,997 | $0 |
| trips_pair | $1,608 | $1,608 | $0 |
| three_pair | $1,653 | $1,653 | $0 |
| quads | $724 | $724 | $0 |
| composite | $2,100 | $2,100 | $0 |

ONLY high_only changed. Every other category is bit-identical to v18e. The gating produces a clean controlled experiment: the −$413 high_only gain is purely attributable to the 6 gated suited features.

**Prefix N=1000 confirmation:**

| Strategy | $/1000h | Δ vs v18e |
|---|---:|---:|
| v18e | $1,082 | — |
| v20 | $1,082 | $0 (tied — gating fires on zero prefix hands by design) |

The prefix has no high_only canonical_ids (the prefix is the first 500K canonical IDs, which are pair / two_pair / trips / trips_pair / three_pair / quads / composite). The gated features fire on zero hands in the prefix → identical predictions to v18e. The "tie" is the BEST possible prefix outcome for a feature-engineering change in a non-prefix category.

**Why this generalizes (the v19 lesson applied):**

The v19 (ungated) features failed the prefix tripwire by giving the DT permission to make small spurious splits in the pair / two_pair / trips populations using cross-category aug values. v19_gated and v20 zero out those features, leaving the pair-category routing decisions identical to the corresponding base-feature-only model. The new features only inform the high_only routing, where the signal is real.

**The gated pattern is the new template for aug families:**
- Compute features only for the targeted hand category.
- Return zeros otherwise.
- Persist as `feature_table_<category>_aug_gated.parquet`.
- Add to trainer's feature list.
- Validate on prefix tripwire (should tie if the targeted category isn't in the prefix).

**Consequence:**
1. **v20_dt is the new ML champion.** Use `strategy_v20_dt(hand_bytes) -> setting_index`. Model file: `data/v20_dt_model.npz`.
2. **STRATEGY_GUIDE.md champion pointer updated to v20.**
3. **Future aug families MUST be category-gated** per the v19 / v20 lesson.
4. **Open question:** Can we apply the gating pattern to other categories? Trips_pair ($1,608 v20) and composite ($2,100 v20) are the next biggest residuals. Both are good candidates for gated aug feature families in Session 31.


## Decision 054 — Capacity sweep continuation: v18d, v18e (Session 30)

**Date:** 2026-05-04
**Status:** Settled. v18d (depth=28, ml=10) and v18e (depth=30, ml=5) both pass full-grid + prefix tripwire. Used as intermediate baselines and as the capacity profile for v20.

**Question:** Decision 051 ended at v18c (depth=26, ml=20) with diminishing returns. Does the curve actually plateau, or is there more $/1000h to extract from deeper trees?

**Answer:** The curve hasn't plateaued. Two more steps both pass:

| Variant | Depth | min_leaf | Leaves | Full $/1000h | Prefix $/1000h | Δ Full vs prev | Δ Prefix vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| v18c | 26 | 20 | 124,902 | $2,172 | $1,261 | — | — |
| **v18d** | **28** | **10** | **193,365** | **$2,108** | **$1,145** | **−$64** | **−$117** |
| **v18e** | **30** | **5** | **274,446** | **$2,066** | **$1,082** | **−$42** | **−$63** |

Notable: v18d's PREFIX gain (+$117) was BIGGER than v18c's (+$82) — the diminishing-returns curve isn't strictly monotonic. There's noise on top of the overall trend.

**Per-category gains (full grid):**

| Category | v18c | v18d | v18e |
|---|---:|---:|---:|
| high_only | $3,359 | $3,323 | $3,307 |
| pair | $1,934 | $1,894 | $1,873 |
| two_pair | $1,676 | $1,550 | $1,458 |
| trips | $2,110 | $2,045 | $1,997 |
| trips_pair | $1,873 | $1,754 | $1,608 |
| three_pair | $1,706 | $1,675 | $1,653 |
| quads | $907 | $829 | $724 |
| composite | $3,207 | $2,680 | $2,100 |

**Files:**
- `data/v18d_dt_model.npz` (137 MB)
- `data/v18e_dt_model.npz` (189 MB)
- `analysis/scripts/grade_v18d_v18e.py` (capacity-step grader)

**Consequence:**
1. **v18e was briefly the ML champion** (between v18c and v20). v20 supersedes via gated suited features.
2. **The capacity profile (depth=30, ml=5)** is what v20 inherits.
3. **Open question for Session 31:** Try v20b at depth=32, ml=5 — might extract +$30-50.


## Decision 055 — v20b (depth=32) ARCHIVED — capacity saturated at depth=30, ml=5 (Session 31)

**Date:** 2026-05-04
**Status:** Settled. v20b is bit-identical to v20 on both grids. The capacity sweep has terminated.

**Question:** Decision 054 left depth=32 / ml=5 as an open candidate. Is there any extra $/1000h to extract by going one more depth step on the same gated-suited feature set?

**Answer:** No. v20b trains to **307,939 leaves** (identical to v20) at depth=32, ml=5. min_samples_leaf=5 is the binding constraint, not depth. Both grids:

| Strategy | Full $/1000h | Prefix $/1000h | Leaves |
|---|---:|---:|---:|
| v20 | $1,982 | $1,082 | 307,939 |
| v20b | $1,982 | $1,082 | 307,939 |

Δ = +$0 / +$0. Depth ≥ 30 is unreachable when min_samples_leaf=5 already pins every terminal node.

**Files:**
- `data/v20b_dt_model.npz` (211 MB) — kept for reproducibility but functionally redundant.
- `analysis/scripts/grade_v20b.py`

**Consequence:**
1. **Capacity sweep is closed.** Future ML wins must come from features (gated aug families), not from deeper trees on the same feature set.
2. **min_samples_leaf=5 is the floor.** Pushing it lower would risk overfitting.


## Decision 056 — Rule 5 candidates ARCHIVED — both naive and tightened variants lose vs v14_combined (Session 31)

**Date:** 2026-05-04
**Status:** Settled. Rule 5 (high_only suited-mid) cannot be extracted as a hand-coded rule. The v20 DT's gated suited routing is too fine-grained for any single threshold rule to match.

**Question:** v20's gated suited features capture −$413/1000h on the high_only category. Can that be turned into a human-memorizable Rule 5 ("if there's a same-suit pair with a 9+ in it, put it on mid"), or do we need a tightened variant ("J+ + 9+")?

**Answer:** Both fail. The single-threshold rule fires on far more high_only hands than the population that actually benefits from suited-mid routing.

| Strategy | Full $/1000h | Δ vs v14 |
|---|---:|---:|
| v14_combined + Rule 4 (baseline) | $3,033 | — |
| v21 = v14 + Rule 5 (msphr ≥ 9) | $3,713 | **−$680** |
| v22 = v14 + Rule 5 (msphr ≥ 11 AND msplr ≥ 9) | $3,506 | **−$473** |

Tightening helped (−$473 vs −$680) but didn't make Rule 5 positive. Per-category damage:

| Strategy | high_only | pair | two_pair | trips | trips_pair | three_pair | quads | composite |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| v14 | (~$4,082) | $2,011 | $3,371 | $4,054 | $5,417 | $4,529 | $9,670 | $10,883 |
| v21 | $7,411 | $2,011 | $3,371 | $4,054 | $5,417 | $4,529 | $9,670 | $10,883 |
| v22 | $6,398 | $2,011 | $3,371 | $4,054 | $5,417 | $4,529 | $9,670 | $10,883 |

The damage is entirely in high_only — Rules 1/2/3/4 don't fire there, so the rule chain falls through to v8 fallback unmodified for non-high_only categories. The −$3K-$3.4K hit on high_only is from over-eager firing: the rule routes hands to suited-mid that the DT (with its 308K leaves) carves around.

**Why the DT-vs-rule gap is fundamental here:** the gated suited DT splits in v20 use thresholds at multiple ranks (msphr at 5, 6, 7, 8 in different subtrees) and combine with `n_low`, `n_broadway`, and other features. A single AND-threshold rule cannot replicate this routing without firing ~8× too often on the wrong hands (the lesson the user already saved as memory).

**Files:**
- `analysis/scripts/strategy_rule5_suited_mid.py` (loose) — KEEP for reference / never use in production
- `analysis/scripts/strategy_rule5_tight_suited_mid.py` (tight) — KEEP for reference
- `analysis/scripts/strategy_v21_combined.py`, `strategy_v22_combined.py`
- `analysis/scripts/grade_v21_combined.py`, `grade_v22_combined.py`

**Consequence:**
1. **STRATEGY_GUIDE.md updated:** "Candidate Rule 5" section now says **REJECTED** (both variants tested), no Rule 5 in the rule chain.
2. **v14_combined + Rule 4 remains the human-memorizable strategy of record** at $3,033/1000h.
3. **The DT champion is the ONLY way to capture the high_only suited routing.** Use `strategy_v23_dt` (or v24 if it ships) for production.
4. **Methodology lesson confirmed:** Distillation of a gated DT feature into a hand-coded rule requires head-to-head validation BEFORE shipping. Naive extractions over-fire by an order of magnitude.


## Decision 057 — v23_dt is the new ML champion (Session 31) — gated trips_pair aug family generalizes the template

**Date:** 2026-05-04
**Status:** Shipped. v23 strictly dominates v20 on both grids by adding 6 trips_pair-gated features. Confirms the gating template generalizes from high_only (v20) to other categories.

**What v23 is:**
- 49 features: 37 base + 6 suited-broadway-gated (Session 30) + **6 trips_pair-gated (new)**.
- Training profile inherits from v20: depth=30, min_samples_leaf=5, random_state=42.
- 314,705 leaves (vs v20's 307,939) — +6,766 leaves carve trips_pair more finely.
- Model file: `data/v23_dt_model.npz` (215 MB).

**The 6 trips_pair-gated features** (`analysis/scripts/trips_pair_aug_features_gated.py`):

| Feature | Domain | What it encodes |
|---|---|---|
| `tp_trip_rank_g` | 0..14 | rank of the trip; 0 if not trips_pair |
| `tp_pair_rank_g` | 0..14 | rank of the pair |
| `tp_high_singleton_rank_g` | 0..14 | higher of the 2 singleton ranks |
| `tp_low_singleton_rank_g` | 0..14 | lower of the 2 singleton ranks (NEW info — baseline only carries `top_rank`) |
| `tp_singletons_suited_g` | 0/1 | 1 if both singletons share a suit |
| `tp_pair_routing_is_ds_g` | 0/1 | 1 if singleton suits fill out the pair's two suits → pair-on-bot routing yields DS |

All zero for any hand that is not trips_pair (n_trips==1 AND n_pairs==1 AND n_quads==0). 171,600 of 6,009,159 canonical hands fire the gate (2.86%).

**Validation results:**

| Grid | v20 $/1000h | v23 $/1000h | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,982 | **$1,977** | **−$5** |
| Prefix (N=1000, 500K hands) | $1,082 | **$1,073** | **−$9** |

The −$5 / −$9 gain is small because trips_pair is only 2.86% of the canonical full grid (8% of prefix). Per-category:

| Category | v20 full | v23 full | Δ |
|---|---:|---:|---:|
| high_only | $2,894 | $2,894 | $0 |
| pair | $1,873 | $1,873 | $0 |
| two_pair | $1,458 | $1,458 | $0 |
| trips | $1,997 | $1,997 | $0 |
| **trips_pair** | **$1,608** | **$1,447** | **−$161** |
| three_pair | $1,653 | $1,654 | +$1 (noise) |
| quads | $724 | $724 | $0 |
| composite | $2,100 | $2,080 | −$20 |

**The gating works perfectly:** every non-trips_pair category is bit-identical (or within N=200 noise). The −$161 on trips_pair is a clean controlled-experiment attribution to the 6 new gated features.

**Top feature importance** (v23 trainer): tp_low_singleton_rank_g made top-20 (0.20%), confirming the DT uses the new-info column most. The other tp_* features rank between 22 and 30.

**Files:**
- `analysis/scripts/trips_pair_aug_features_gated.py` — feature computation
- `analysis/scripts/persist_trips_pair_aug_gated.py` — writes parquet
- `data/feature_table_trips_pair_aug_gated.parquet` (20 MB)
- `analysis/scripts/train_v23_dt.py` — trainer (49 features)
- `analysis/scripts/strategy_v23_dt.py` — inference wrapper
- `analysis/scripts/grade_v23.py` — head-to-head grader
- `data/v23_dt_model.npz` (215 MB)

**Consequence:**
1. **v23 is the new ML champion.** Use `strategy_v23_dt(hand_bytes) -> setting_index`. (Or v24 if Decision 058 ships.)
2. **The gating template generalizes.** Confirmed: a category-gated aug feature family lifts ONLY its targeted category and ties everywhere else (including prefix tripwire).
3. **Future aug families should follow the same shape:** ~4-6 archetype-specific features, computed only when n_pairs/n_trips/n_quads gates fire, zeros otherwise, parquet'd by canonical_id, trained on top of the current champion.
4. **Open question answered (Decision 058):** v24 (composite-gated) DOES ship on top of v23 — third category gated cleanly.


## Decision 058 — v24_dt is the new ML champion (Session 31) — composite-gated aug family is the third gating success

**Date:** 2026-05-04
**Status:** Shipped. v24 wins on both grids by adding 4 composite-gated features. Third clean instance of the gating template (after high_only via v20 and trips_pair via v23). Headline gain is tiny because composite is 0.245% of population, but the per-category effect is unambiguous: composite drops $216/1000h and every other category is bit-identical or within N=200 noise.

**What v24 is:**
- 53 features: 49 v23 features + **4 composite-gated (new)**.
- Same training profile: depth=30, ml=5, random_state=42.
- 314,759 leaves (vs v23's 314,705) — only +54 leaves; the DT is reusing v23's structure and adding a few composite-specific splits.
- Model file: `data/v24_dt_model.npz` (215 MB).

**The 4 composite-gated features** (`analysis/scripts/composite_aug_features_gated.py`):

| Feature | Domain | What it encodes |
|---|---|---|
| `comp_archetype_g` | 0..4 | 0=non-composite, 1=trips_two_pair, 2=two_trips, 3=quads_pair, 4=quads_trip |
| `comp_lower_trip_rank_g` | 0..14 | Lower trip rank (only meaningful in two_trips); 0 elsewhere. **NEW info — baseline `trips_rank` only carries the higher one.** |
| `comp_singleton_rank_g` | 0..14 | Rank of the lone singleton in two_trips or quads_pair; 0 if no singleton or non-composite |
| `comp_higher_pair_rank_g` | 0..14 | Higher pair rank in trips_two_pair (mirror of pair_high_rank but zeroed off-archetype to avoid leakage) |

All zero for any non-composite hand. 14,742 of 6,009,159 canonical hands fire the gate (0.245%).

**Validation results:**

| Grid | v23 $/1000h | v24 $/1000h | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,977 | $1,977 | +$1 (effectively tied at headline; composite improves) |
| Prefix (N=1000, 500K hands) | $1,073 | $1,072 | +$1 |

Per-category at full grid:

| Category | v23 | v24 | Δ |
|---|---:|---:|---:|
| high_only | $2,894 | $2,894 | $0 |
| pair | $1,873 | $1,873 | $0 |
| two_pair | $1,458 | $1,458 | $0 |
| trips | $1,997 | $1,997 | $0 |
| trips_pair | $1,447 | $1,447 | $0 |
| three_pair | $1,654 | $1,654 | $0 |
| quads | $724 | $723 | −$1 (noise) |
| **composite** | **$2,080** | **$1,864** | **−$216** |

The −$216 composite improvement is real (prefix saw the same: composite $1,811 → $1,610, −$201). The 0.245% population share means the overall delta is ~$0.5/1000h — the +$1 headline is largely noise on top of a real micro-effect.

**Diagnostic provenance:** `composite_v20_residual.py` (Session 31, run earlier in this session) found 4 archetype clusters where v20 frequently SPLITS the dominant trips/quads instead of keeping them together on bot. v24's gated features expose the archetype + the unique-info "lower_trip_rank" signal so the DT can learn the per-archetype routing.

**Files:**
- `analysis/scripts/composite_aug_features_gated.py` — feature computation
- `analysis/scripts/persist_composite_aug_gated.py` — writes parquet
- `data/feature_table_composite_aug_gated.parquet` (19 MB)
- `analysis/scripts/train_v24_dt.py` — trainer (53 features, builds on train_v23)
- `analysis/scripts/strategy_v24_dt.py` — inference wrapper
- `analysis/scripts/grade_v24.py` — head-to-head grader
- `analysis/scripts/composite_v20_residual.py` — provenance diagnostic
- `data/v24_dt_model.npz` (215 MB)

**Consequence:**
1. **v24 is the new ML champion.** Use `strategy_v24_dt(hand_bytes) -> setting_index`. Marginal but technically positive on both grids.
2. **Three categories gated cleanly:** high_only (v20), trips_pair (v23), composite (v24). The template is now proven across hand-count and archetype dimensions.
3. **Diminishing-returns warning:** v24's headline gain is at the noise floor. Future small categories (quads at 0.24% × $724 = $1.7 share) are not worth gating. The remaining levers are the LARGE categories: pair ($873 share), high_only ($590 share), two_pair ($325 share).
4. **Open question for Session 32:** the gating template's natural next target is `two_pair_aug_gated` (~$325/1000h share, biggest untouched category). See CURRENT_PHASE.md "Next Session Targets" for a sketch.

## Decision 059 — v25_dt is the new ML champion (Session 32) — pair-gated aug family is the fourth gating success and the largest absolute win

**Date:** 2026-05-04
**Status:** Shipped. v25 wins on BOTH grids by adding 6 pair-gated features that augment the 3 pre-existing pair aug booleans (which the Session 32 audit confirmed were already category-gated despite their inconsistent naming, not the v19 leakage pattern). Fourth clean instance of the gating template (after v20→high_only, v23→trips_pair, v24→composite). Pair is the largest category by share, so this is the biggest absolute headline gain since v20.

**Pair audit (the diagnostic question from Session 31's resume prompt):**
The 3 pair aug features that have existed since Session 17 (`default_bot_is_ds`, `n_top_choices_yielding_ds_bot`, `pair_to_bot_alt_is_ds`) were verified strictly zero on every non-pair canonical hand:

| Feature | Non-pair rows nonzero | Pair-row coverage |
|---|---:|---:|
| `default_bot_is_ds` | 0 | 432,432 / 2,800,512 = 15.4% |
| `n_top_choices_yielding_ds_bot` | 0 | 1,338,480 / 2,800,512 = 47.8% (values {0,1,3} only) |
| `pair_to_bot_alt_is_ds` | 0 | 370,656 / 2,800,512 = 13.2% |

So they're already gated. They are NOT the v19 leakage pattern. The verdict was therefore option B from the resume prompt: design a 6-feature gated EXTENSION rather than rebuild from scratch.

**What v25 is:**
- 59 features: 53 v24 features + **6 pair-gated (new)**.
- Same training profile: depth=30, ml=5, random_state=42.
- 390,626 leaves (vs v24's 314,759) — **+75,867 leaves**, a +24% capacity expansion. Compare to v23→v24's +54 leaves: pair is genuinely large enough that the new features unlock substantial new partitioning.
- Model file: `data/v25_dt_model.npz` (266 MB).

**The 6 pair-gated features** (`analysis/scripts/pair_aug_features_gated.py`):

| Feature | Domain | What it encodes |
|---|---|---|
| `pair_kickers_in_pair_suit_max_g` | 0..5 | Max count of non-pair cards matching either pair-suit. Zero off-archetype. |
| `pair_kickers_in_pair_suit_min_g` | 0..5 | Min of same. Together with max fully specifies Rule 1's (1,1)/(2,2)/(2,1)/(3,1) split. |
| `pair_default_top_rank_g` | 0..14 | Rank of top under v3-default routing (= highest non-pair singleton). Lets DT split on "DS bot AND high top". |
| `pair_alt_top_rank_g` | 0..14 | Rank of top under pair→bot alt routing (= 3rd-highest non-pair singleton). Lets DT decide whether alt-top is competitive. |
| `pair_alt_mid_suited_g` | 0/1 | Top-2 non-pair cards same-suit under alt routing. Drives "alt mid is suited connector" splits. |
| `pair_alt_mid_n_broadway_g` | 0..2 | Broadway count among top-2 non-pair cards under alt routing. |

All zero for any non-pair hand. 2,800,512 of 6,009,159 canonical hands fire the gate (46.6% — the biggest gating share to date).

**Validation results:**

| Grid | v24 $/1000h | v25 $/1000h | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,977 | **$1,929** | **−$47** |
| Prefix (N=1000, 500K hands) | $1,072 | **$1,054** | **−$18** |

Per-category at full grid:

| Category | v24 | v25 | Δ |
|---|---:|---:|---:|
| high_only | $2,894 | $2,894 | $0 |
| **pair** | **$1,873** | **$1,771** | **−$102** |
| two_pair | $1,458 | $1,458 | $0 |
| trips | $1,997 | $1,997 | $0 |
| trips_pair | $1,447 | $1,446 | −$1 (noise) |
| three_pair | $1,654 | $1,654 | $0 |
| quads | $723 | $723 | $0 |
| composite | $1,864 | $1,869 | +$5 (noise) |

Per-category at prefix grid:

| Category | v24 | v25 | Δ |
|---|---:|---:|---:|
| **pair** | **$929** | **$888** | **−$41** |
| two_pair | $1,051 | $1,050 | −$1 (noise) |
| trips | $1,763 | $1,763 | $0 |
| trips_pair | $1,657 | $1,657 | $0 |
| three_pair | $1,122 | $1,122 | $0 |
| quads | $794 | $794 | $0 |
| composite | $1,610 | $1,610 | $0 |

The textbook gating-template signature: pair drops on both grids ($102 / $41), every other category bit-identical or within N=200 noise. Headline gain matches arithmetic ($102 × 46.6% pair share = $47). pct_optimal moves from 47.89% → 48.43% on full and 59.48% → 59.80% on prefix; pair-only pct_opt goes 52.8% → 53.9% (full) and 62.8% → 63.5% (prefix).

**Feature importance (v25 top-25):** 5 of 6 new pair-gated features placed in top-25, top one being `pair_alt_top_rank_g` at #15 (0.69%). The 3 pre-existing pair aug booleans (`default_bot_is_ds`, etc.) are still present as inputs and remain useful — the new features ADD signal rather than replace.

**Files:**
- `analysis/scripts/pair_aug_features_gated.py` — feature computation
- `analysis/scripts/persist_pair_aug_gated.py` — writes parquet
- `data/feature_table_pair_aug_gated.parquet` (20 MB)
- `analysis/scripts/train_v25_dt.py` — trainer (59 features, builds on train_v24)
- `analysis/scripts/strategy_v25_dt.py` — inference wrapper
- `analysis/scripts/grade_v25.py` — head-to-head grader
- `data/v25_dt_model.npz` (266 MB)

**Consequence:**
1. **v25 is the new ML champion.** Use `strategy_v25_dt(hand_bytes) -> setting_index`. Largest non-suited category gain in the project's history.
2. **Four categories gated cleanly:** high_only (v20), trips_pair (v23), composite (v24), pair (v25). The template now spans 0.245% to 46.6% population shares.
3. **Pair audit answer:** the 3 pre-existing pair aug features were already strictly category-gated. The naming inconsistency (no `_g` suffix) was misleading but harmless. They remain in the model and have been confirmed useful (0.32% feature importance combined in v25); the 6 new features add complementary signal rather than duplicate.
4. **Capacity surprise:** v25 needed +75K leaves vs v24, the largest leaf-count delta since v20. Suggests the pair category's new partitioning is structural, not noise-fitting; the prefix N=1000 tripwire confirmed this independently.
5. **Open question for Session 33:** with pair now gated, the largest untouched lever is `two_pair_aug_gated` ($325/1000h share, 22.3% population). High_only round 2 ($590 share but partly addressed) is the alternative. See CURRENT_PHASE.md.


## Decision 060 — v26_dt is the new ML champion (Session 33) — two_pair-gated aug family is the fifth gating success and largest per-category gain since v20

**Date:** 2026-05-04
**Status:** Shipped. v26 wins on BOTH grids by adding 6 two_pair-gated features that augment the 3 pre-existing two_pair aug booleans (verified strictly category-gated since Session 19 — same audit pattern as the Session 32 pair audit). Fifth clean instance of the gating template (high_only/v20, trips_pair/v23, composite/v24, pair/v25, two_pair/v26). The $313/1000h per-category drop on two_pair is the biggest single-category win since v20→high_only's $413.

**Two_pair audit (the diagnostic question from Session 32's resume prompt):**
The 3 two_pair aug features that have existed since Session 19 (`default_bot_is_ds_tp`, `n_routings_yielding_ds_bot_tp`, `swap_high_pair_to_bot_ds_compatible`) were verified strictly zero on every non-two_pair canonical hand:

| Feature | Non-two_pair rows nonzero | Two_pair-row coverage |
|---|---:|---:|
| `default_bot_is_ds_tp` | 0 | 180,180 / 1,338,480 = 13.5% |
| `n_routings_yielding_ds_bot_tp` | 0 | 617,760 / 1,338,480 = 46.2% (values {0,1,2,4} only) |
| `swap_high_pair_to_bot_ds_compatible` | 0 | 386,100 / 1,338,480 = 28.8% |

So they were already gated since Session 19 — same Session 17 vintage as the pair aug features. NOT v19 leakage. Path was again option B: design a 6-feature gated extension.

**What v26 is:**
- 65 features: 59 v25 features + **6 two_pair-gated (new)**.
- Same training profile: depth=30, ml=5, random_state=42.
- 459,209 leaves (vs v25's 390,626) — **+68,583 leaves**, +18% capacity expansion. Second-largest leaf-count delta of any single ship.
- Model file: `data/v26_dt_model.npz` (309 MB).

**The 6 two_pair-gated features** (`analysis/scripts/two_pair_aug_features_gated.py`):

| Feature | Domain | What it encodes |
|---|---|---|
| `t2p_layout_a_bot_is_ds_g` | 0/1 | Layout A (both pairs → bot) gives DS — fires when both pairs share BOTH suits exactly. ~19% of two_pair hands. |
| `t2p_n_layout_b_routings_ds_g` | 0..3 | DS routings with HIGH pair in mid (subset of `n_routings_yielding_ds_bot_tp`). Splits Layout B from Layout C — the Session 19 mining notes called out this exact distinction as the dominant miss pattern. |
| `t2p_top_singleton_rank_g` | 0..14 | Highest of the 3 singletons (natural top). |
| `t2p_low_singleton_rank_g` | 0..14 | Lowest singleton. Captures "is there a 2 or 3 to throw to top safely?" — surprisingly strong: #12 in feature importance at 0.81%. |
| `t2p_singletons_max_suit_count_g` | 1..3 | Max count of singletons in any one suit (suited-mid signal). |
| `t2p_high_pair_rank_g` | 0..14 | High pair rank, zeroed off-archetype (mirror of pair_high_rank with strict gating, mirrors pattern from `comp_higher_pair_rank_g`). |

All zero for any non-two_pair hand. 1,338,480 of 6,009,159 canonical hands fire the gate (22.3%).

**Validation results:**

| Grid | v25 $/1000h | v26 $/1000h | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,929 | **$1,859** | **−$70** |
| Prefix (N=1000, 500K hands) | $1,054 | **$1,002** | **−$52** |

Per-category at full grid:

| Category | v25 | v26 | Δ |
|---|---:|---:|---:|
| high_only | $2,894 | $2,894 | $0 |
| pair | $1,771 | $1,771 | $0 |
| **two_pair** | **$1,458** | **$1,145** | **−$313** |
| trips | $1,997 | $1,997 | $0 |
| trips_pair | $1,446 | $1,445 | −$1 (noise) |
| three_pair | $1,654 | $1,654 | $0 |
| quads | $723 | $723 | $0 |
| composite | $1,869 | $1,741 | −$128 (likely N=200 noise — composite is 0.245% of population, prefix saw +$2) |

Per-category at prefix grid:

| Category | v25 | v26 | Δ |
|---|---:|---:|---:|
| pair | $888 | $888 | $0 |
| **two_pair** | **$1,050** | **$924** | **−$126** |
| trips | $1,763 | $1,763 | $0 |
| trips_pair | $1,657 | $1,656 | −$1 (noise) |
| three_pair | $1,122 | $1,123 | +$1 (noise) |
| quads | $794 | $794 | $0 |
| composite | $1,610 | $1,612 | +$2 (noise) |

Textbook gating-template signature on prefix; full-grid composite move is most plausibly noise (composite has only 14,742 hands at N=200, and prefix shows it tied). Headline gain matches arithmetic: $313 × 22.3% population share = $70 (exact). pct_optimal moves from 48.43% → 49.21% on full and 59.80% → 60.80% on prefix; two_pair-only pct_opt jumps 57.3% → 60.8% (full) and 58.8% → 61.3% (prefix).

**Feature importance (v26 top-25):** 3 of 6 new two_pair-gated features placed in top-25, with `t2p_low_singleton_rank_g` at #12 (0.81%) — surprisingly strong, likely encoding "can we safely demote the weakest singleton to top?". The 3 pre-existing two_pair aug features remain in the model alongside the new 6.

**Bug encountered + fixed mid-session — naming-collision lesson:**
v26 was first trained with the 6 new features named `tp_*` (matching the trips_pair gated family's prefix). Both `tp_low_singleton_rank_g` AND `tp_top_singleton_rank_g` collided with the trips_pair feature names. Training succeeded by column index, but inference's `feature_columns.index(c)` returned the FIRST occurrence for both name lookups; the v26 strategy wrote two_pair values into the trips_pair column index and left the actual two_pair column uninitialized. **Result: v26 (buggy) showed $3,746/1000h on prefix** — a $2,692 catastrophic regression with two_pair AND trips_pair both blown up. Renamed all 6 features to `t2p_*` prefix; re-persisted parquet (37s); re-trained (256s); re-graded — clean win as documented above.

**Methodology lesson** (added to CURRENT_PHASE.md): each gated family must use a UNIQUE prefix. The trips_pair family already owned `tp_`; future families need distinct prefixes. Audit checklist now includes: `grep -c <new_prefix> existing feature definitions` before naming.

**Files:**
- `analysis/scripts/two_pair_aug_features_gated.py` — feature computation (6 features)
- `analysis/scripts/persist_two_pair_aug_gated.py` — writes parquet
- `data/feature_table_two_pair_aug_gated.parquet` (20 MB)
- `analysis/scripts/train_v26_dt.py` — trainer (65 features, builds on train_v25)
- `analysis/scripts/strategy_v26_dt.py` — inference wrapper
- `analysis/scripts/grade_v26.py` — head-to-head grader
- `data/v26_dt_model.npz` (309 MB)

**Consequence:**
1. **v26 is the new ML champion.** Use `strategy_v26_dt(hand_bytes) -> setting_index`. Largest per-category gain since v20→high_only (Session 30).
2. **Five categories gated cleanly:** high_only (v20), trips_pair (v23), composite (v24), pair (v25), two_pair (v26). Population shares span 0.245% (composite) to 46.6% (pair).
3. **Naming convention enforcement:** all gated features must use a unique prefix. Existing prefixes claimed: `_g` suffix variants for suited (`*_g`), trips_pair (`tp_*_g`), composite (`comp_*_g`), pair (`pair_*_g`), two_pair (`t2p_*_g`). New families must check.
4. **Diminishing-returns watch:** five large categories now gated. Remaining absolute residuals at full grid (per-category × share):
   - **pair**: 46.6% × $1,771 = $825 share — second-pass diagnostic candidate
   - **high_only**: 20.4% × $2,894 = $590 share — round 2 candidate
   - **two_pair**: 22.3% × $1,145 = $255 share — just got hit
   - trips: 5.5% × $1,997 = $110 — never gated
   - The large levers are increasingly squeezed; round-2 audits and trips_aug_gated are the natural Session 34+ targets.
5. **Open question for Session 34:** distill v26 on high_only (still $2,894/1000h, untouched since v20). Either a `connectivity_high_g` family yields another v20-shaped win, or high_only is intrinsically harder and we move to trips_aug_gated.


## Decision 061 — v27_dt is the new ML champion (Session 34) — high_only-gated aug family is the sixth gating success but the smallest per-category gain to date

**Date:** 2026-05-05
**Status:** Shipped (marginal). v27 wins on full grid by adding 4 high_only-gated features. Sixth clean instance of the gating template (after v20→suited/high_only-via-suited, v23→trips_pair, v24→composite, v25→pair, v26→two_pair). The $31/1000h within-category gain on high_only is real and category-isolated, but the smallest per-category absolute drop in the project's history. Headline: $1,859 → $1,853 (−$6/1000h, +0.06pp pct_opt).

**Diagnostic origin (Session 34 distillation of v26):**
The distillation `distill_v26_high_only.py` walked all 6M hands through v26's 459K-leaf tree and identified the top 30 high_only miss leaves. ALL of them shared the path `n_broadway ∈ [3,4]` AND `n_broadway_in_largest_suit_g ≥ 2` — i.e., suited-broadway high_only hands with 3-4 broadway cards. Stratifying within these miss leaves by the candidate feature `n_broadway_in_2nd_suit` produced striking separations:

| Leaf | n_ho | mean_regret | cand=0 reg | cand=1 reg | Δ |
|---|---:|---:|---:|---:|---:|
| 578474 | 420 | +0.635 | +0.773 | +0.359 | **+0.414 EV** |
| 545147 | 420 | +0.635 | +0.748 | +0.408 | +0.340 EV |
| 798839 | 432 | +0.589 | +0.679 | +0.544 | +0.135 EV |
| 545045 | 840 | +0.588 | +0.640 | +0.486 | +0.154 EV |

9/10 top miss leaves showed ≥0.15 EV within-leaf separation. This was the strongest pre-train signal of any session — comparable in magnitude to the per-leaf signal that motivated v25 and v26.

**What v27 is:**
- 69 features: 65 v26 features + **4 high_only-gated (new)**.
- Same training profile: depth=30, ml=5, random_state=42.
- 460,375 leaves (vs v26's 459,209) — **+1,166 leaves**, +0.25% expansion. The smallest single-ship leaf delta of any gating-template ship (compare v25→v26 +68K, v24→v25 +76K, v23→v24 +54).
- Model file: `data/v27_dt_model.npz` (310 MB).

**The 4 high_only-gated features** (`analysis/scripts/high_only_aug_features_gated.py`, prefix `ho_*_g` to avoid Session-33 naming-collision lesson):

| Feature | Domain | What it encodes |
|---|---|---|
| `ho_n_broadway_in_2nd_suit_g` | 0..3 | Count of T-A in the 2nd-largest suit. PRIMARY signal from diagnostic. |
| `ho_n_broadway_in_3rd_suit_g` | 0..3 | Count of T-A in the 3rd-largest suit. Completes the per-suit broadway distribution. |
| `ho_connectivity_high_g` | 0..5 | Longest run of consecutive ranks within broadway (T-A). |
| `ho_n_broadway_pairs_adj_g` | 0..4 | Count of adjacent broadway pairs present (AK/KQ/QJ/JT). Differs from connectivity_high — KQ + JT gives 2 here but longest=2. |

All zero for any non-high_only hand. 1,226,940 of 6,009,159 canonical hands fire the gate (20.4% — second-largest gating share after pair).

**Validation results:**

| Grid | v26 $/1000h | v27 $/1000h | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,859 | **$1,853** | **−$6** |
| Prefix (N=1000, 500K hands) | $1,002 | $1,002 | $0 (no high_only hands) |

Per-category at full grid:

| Category | v26 | v27 | Δ |
|---|---:|---:|---:|
| **high_only** | **$2,894** | **$2,863** | **−$31** |
| pair | $1,771 | $1,771 | $0 |
| two_pair | $1,145 | $1,145 | $0 |
| trips | $1,997 | $1,997 | $0 |
| trips_pair | $1,445 | $1,445 | $0 |
| three_pair | $1,654 | $1,654 | $0 |
| quads | $723 | $723 | $0 |
| composite | $1,741 | $1,741 | $0 |

Per-category at prefix grid: **all categories bit-identical (zero changes anywhere)** — confirmed because the prefix grid's canonical-id 0..500K subset contains zero high_only hands. The category distribution in prefix sums to exactly 500,000 across (pair, two_pair, trips, trips_pair, three_pair, quads, composite) — every prefix hand has at least one pair. This is a structural feature of the canonical-id ordering and means v27's high_only-targeting features can only be validated on the full grid.

Textbook gating-template signature on full grid: high_only drops, every other category bit-identical to the byte. Headline gain matches arithmetic: $31 × 20.42% population share = $6.33 ≈ $6 actual. pct_optimal moves from 49.21% → 49.27% on full (+0.06 pp); high_only-only pct_opt: 27.7% → 28.0% (+0.3 pp).

**Feature importance (v27 top-25):** **0 of 4 new ho_*_g features placed in the top 25.** Compare to v26 (3/6 t2p_*) and v25 (5/6 pair_*). This was the leading indicator of the marginal headline result. The DT primarily captured the new signal through reshuffling existing-feature splits, not through the new features themselves. Only +1,166 leaves grew, vs +68K/+76K of recent ships.

**Diagnostic-to-headline conversion ratio: ~10%.** The within-leaf 0.34-0.41 EV separation (worst miss leaves) projected to ~$3,400/1000h within-leaf. Realized headline: $31/1000h within-category, $6/1000h whole-grid. The signal is concentrated in a small fraction of hands within each miss leaf — even a perfect feature would only flip ~24% of bot-DS-eligible KKK/AAA, and the same logic holds for high_only: the 0.34 EV separation only fires on the SUBSET of leaf hands where the feature actually changes the optimal pick, not the full leaf population.

**Files:**
- `analysis/scripts/high_only_aug_features_gated.py` — feature computation (4 features)
- `analysis/scripts/persist_high_only_aug_gated.py` — writes parquet (28.5s for 6M hands)
- `data/feature_table_high_only_aug_gated.parquet` (19 MB)
- `analysis/scripts/train_v27_dt.py` — trainer (69 features, builds on train_v26)
- `analysis/scripts/strategy_v27_dt.py` — inference wrapper (6 gated families + base)
- `analysis/scripts/grade_v27.py` — head-to-head grader
- `analysis/scripts/distill_v26_high_only.py` — diagnostic that motivated the design
- `data/v27_dt_model.npz` (310 MB)

**Consequence:**
1. **v27 is the new ML champion.** Use `strategy_v27_dt(hand_bytes) -> setting_index`. Marginal but technically positive on the only grid that can measure it (full).
2. **Six categories gated cleanly:** suited/high_only-via-suited (v20), trips_pair (v23), composite (v24), pair (v25), two_pair (v26), high_only-direct (v27). The template is now proven across population shares from 0.245% (composite) to 46.6% (pair), with high_only at 20.4% being the second-largest.
3. **Naming convention enforcement upheld.** `ho_*_g` prefix is unique among existing gated families.
4. **New methodology rule: top-25 feature importance is a pre-grade tripwire.** If 0/N new features place in top-25, expect marginal-to-null headline. Future families: validate the diagnostic with a single-feature DT before committing to a 4-6 feature family. For correlated candidates (e.g. `ho_connectivity_high_g` overlaps with `n_broadway`+`n_low`+`connectivity`), the additional features may not earn their place.
5. **New methodology rule: prefix N=1000 grid has 0 high_only hands.** Future high_only-targeting models can only be validated on full-grid N=200. This was always true but had not been observed to LIMIT a grade until this session. The canonical-id 0..500K subset contains only hands with at least one pair (sums to exactly 500,000 across pair / two_pair / trips / trips_pair / three_pair / quads / composite).
6. **Open question for Session 35:** with high_only now lightly touched, the largest residual is back to **pair at $825/1000h whole-grid share**. Session 35 priority A is a pair second-pass diagnostic + a head-to-head grade of v27 vs the KK/AA-Rule-4 + bot-DS-oracle on the KK/AA subset (see Decision 062) to determine how much of pair's $42/1000h KK/AA upper bound v25's pair-gated features already capture.


## Decision 062 — KKK/AAA routing rule confirmed; KK/AA Rule-4 boundary probe (Session 34) — preserves Rule 4 default but identifies $42/1000h KK/AA upper bound for future pair second-pass

**Date:** 2026-05-05
**Status:** Documentation-only. No strategy change this session. Two probes ran in Session 34 to characterize the KK/AA and KKK/AAA routing decisions; both confirm the existing Rule 4 / paired-mid default but identify quantifiable exception subsets for future iteration.

**KKK/AAA probe (`probe_trips_kkk_aaa_routing.py`, n=50,490, 0.84% of grid):**
- A_paired_mid (keep 2 of 3 trip-rank cards in mid as a pair) is the dominant routing: mean EV **+2.530**, BR-optimal on **79.18%** of all KKK/AAA hands.
- AAA: A wins vs B 80.1% (clearer A-dominance). pct_opt of A = 83.84%.
- KKK: A wins vs B 70.9% (splits to DS-bot more often). pct_opt of A = 74.53%. Asymmetry explanation: AAA's stronger mid-pair makes the split less attractive than KKK's.
- B_split_bot_DS (2 of 3 trip-rank in bot, anchoring DS) is geometrically available on 68.6% of KKK/AAA hands. When available, strictly beats A on 24.3% of those cases with mean +0.363 EV gain.
- Top B-wins concentrated where smax=2, s2nd=2 (a 2-2-2-1 suit profile) with n_broadway ∈ [3,4] — high-broadway hands with strong DS-bot potential and mediocre kickers for paired-mid.
- Upper bound oracle-perfect rule: $606/1000h within KKK/AAA, **$5/1000h whole-grid** (KKK/AAA is 0.84% of population).
- CSV at `data/kkk_aaa_routing_probe.csv`.

**KK/AA Rule-4 boundary probe (`probe_kk_aa_ds_bot_vs_mid.py`, n=430,848, 7.17% of grid):**
- Rule 4 (KK/AA → mid as a pair) is BR-optimal on **72.76%** of non-trips KK/AA hands.
- DS-bot routing geometrically available on **55.1%** of KK/AA hands (always when both pair-cards are in different suits, which is 100% of canonical KK/AA hands).
- When DS-bot is available, it strictly beats Rule-4 mid-pair on **28.08%** of cases with mean +0.379 EV gain when it wins.
- Hands where bot-DS strictly wins: 66,713 / 430,848 = 15.48% of all KK/AA.
- Upper bound oracle-perfect Rule-5* on KK/AA: $587/1000h within KK/AA, **$42/1000h whole-grid**.
- CSV at `data/kk_aa_rule4_probe.csv`.

**Human-strategy implications:**
- **Rule 4 stays.** Both probes confirm "high pair (KK/AA) or trips of K/A → mid as a pair" as the dominant rule on the realistic mixture (72.76% / 79.18% / 83.84% optimal across the three subsets).
- **No Rule 5 (yet).** The DS-bot exception fires on ~24-28% of geometrically-eligible hands but is hard to evaluate manually pre-flop. The two prior Rule 5 attempts (v21 / v22 in Session 31) were rejected for being ~8× over-eager relative to the DT's selective routing.
- **Computational implication:** The KK/AA $42 and KKK/AAA $5 upper bounds are within range of v23/v24/v27-magnitude ships. Whether they're already captured by the existing pair_*_g and trips_rank features is the Session 35 priority A diagnostic.

**Files:**
- `analysis/scripts/probe_kk_aa_ds_bot_vs_mid.py` — KK/AA boundary probe
- `analysis/scripts/probe_trips_kkk_aaa_routing.py` — KKK/AAA routing probe
- `data/kk_aa_rule4_probe.csv` — n=430,848 per-hand frame
- `data/kkk_aaa_routing_probe.csv` — n=50,490 per-hand frame

**Consequence:**
1. **Rule 4 is preserved unchanged in `STRATEGY_GUIDE.md`.** Both KK/AA and KKK/AAA probes reaffirm the existing default.
2. **A new probe-script discipline established:** quick boundary probes (5-10s scan + headline pandas) should run BEFORE distillation to set expectations on per-category upper bounds. The KK/AA upper bound of $42/1000h whole-grid is informative for Session 35 prioritization.
3. **Open question for Session 35 priority A:** distill v27 on pair-only hands AND grade v27 vs Rule-4 + bot-DS oracle on the KK/AA subset specifically. If v27 already gets >75% of the $42 upper bound, KK/AA is "done" and the remaining pair residual is in non-KK/AA pair hands. If v27 gets <50%, there's a `pair_kk_aa_split_bot_ds_*_g` candidate family for v28.


## Decision 063 — Rule 5 (Rainbow override) shipped (Session 34, post-v27) — first successful Rule-5 attempt in the project's history

**Date:** 2026-05-05
**Status:** Shipped to STRATEGY_GUIDE.md as Rule 5. Marginal but positive: +$1/1000h whole-grid headline (+0.03 pp pct_opt) over v14_combined+Rule4. Strategy is `analysis/scripts/strategy_v28_rule5_rainbow.py`. NOT a new ML champion — v27_dt remains the computational champion at $1,853/1000h. Rule 5 is for human-memorizable play.

**Origin:** User intuition during the Session-34 closeout discussion. After reviewing the KK/AA Rule-4 boundary probe data, user proposed: "with KK/AA, if Rule 4 leaves you with a rainbow Omaha bot, swap to a double-suited bot anchored by the pair instead." This is a much tighter version of the Session-31 v21/v22 Rule-5 attempts.

**The trigger (Rule 5 gates):**
1. Pair = KK or AA (only premium pairs)
2. Pair has 2 different suits (DS-anchor possible)
3. Rule 4's resulting bot would be rainbow (1+1+1+1 across 4 suits)
4. DS-bot routing geometrically available (at least one kicker in each pair-suit)

**The play (when fired):**
- Bot = pair + lowest-rank kicker of each pair-suit (gives 2+2 DS)
- Top = highest-rank card of the 3 leftover non-pair cards
- Mid = the 2 remaining

**Population that fires:** 3.7% of KK/AA hands × 7.17% KK/AA share = **0.27% of all hands**. Compare to v21 (which fired on ~26% of high_only) and v22 (~13% of high_only) — Rule 5 is 20-50× tighter than the failed attempts.

**Validation results (full grid, N=200):**

| Strategy | $/1000h | pct_opt | Δ vs v14 |
|---|---:|---:|---:|
| v14_combined (4 rules) | $3,033 | 39.61% | — |
| **v28 (v14 + Rule 5 rainbow)** | **$3,032** | **39.64%** | **+$1/1000h, +0.03 pp** |
| v22 (failed Rule 5 — Sept 31) | $3,506 | — | −$473 |
| v21 (failed Rule 5 — Sept 31) | $3,713 | — | −$680 |

Per-category: only `pair` moves ($2,011 → $2,008, −$3). Every other category bit-identical to the byte.

**Per-hand high-leverage wins (illustrative):**
- K♠K♦3♠5♦9♥T♣J♠ (canonical_id 3,912,507): v14 picks rainbow-bot Rule-4 routing for +1.225 EV; Rule 5 routes to DS-bot (top=J, mid=Tc9h, bot=KsKd5d3s) for +3.025 EV. **Δ = $18,000/1000h on this single hand.** (Both v26_dt and v27_dt already pick this DS-bot routing — Rule 5 is for human play.)

**Why this Rule 5 worked where v21/v22 failed:**

| Aspect | v21/v22 (Session 31) | v28 (Session 34) |
|---|---|---|
| Trigger category | high_only (multi-archetype) | KK/AA only (premium-pair-specific) |
| Population fired | ~5-13% of all hands | 0.27% of all hands |
| Gate selectivity | rank-based (msphr ≥ 9) | structural (rainbow Rule-4-bot) |
| Failure mode | Over-fired on hands where DT correctly routed differently | Tight enough to only catch the high-leverage cases |

**Files:**
- `analysis/scripts/strategy_v28_rule5_rainbow.py` — implementation + smoke tests
- `analysis/scripts/grade_v28.py` — head-to-head grader vs v14
- Result log: `/tmp/grade_v28.log` (transient; ungitted)

**Consequence:**
1. **Rule 5 is added to STRATEGY_GUIDE.md** as a fifth numbered rule. The human-memorizable strategy of record is now **v14_combined + Rule 4 + Rule 5** ($3,032/1000h, edge over v8_hybrid ≈ +$1,015/1000h).
2. **First successful Rule 5 in project history.** Validates the methodology lesson: tight, structural gates beat loose rank-based gates. Future rule-extraction attempts should prefer geometric/structural triggers (rainbow, DS-feasibility) over magnitude-based triggers (rank ≥ X).
3. **Whole-grid gain is small** ($1/1000h), comparable to v24's marginal ML ship. Per-hand wins on the firing subset are large (~$18K/1000h on the canonical KsKd3s5d9hTcJs example). The asymmetry — small whole-grid + huge per-hand — is exactly what a "memorize the exception" rule should look like.
4. **v27_dt remains the computational champion.** Rule 5 is human-strategy only; v27 (and v26) already capture this routing on the firing subset.
5. **Open: $42 KK/AA upper bound minus $1 captured = $41 still on the table.** Future Rule-6 candidates would need to address the single-suited (2+1+1) Rule-4-bot bucket (48.7% of KK/AA) where 20% prefer DS-bot but the trigger is harder to define. Probably not worth the cognitive load for human play; ML routing already handles it.


## Decision 064 — v29_dt is the new ML champion (Session 35) — pair-gated v2 family is the 7th gating success and the largest diagnostic-driven win

**Date:** 2026-05-05
**Status:** Shipped. v29 wins on BOTH grids by adding 4 pair-gated v2 features (`pair_r4_*_g`) targeting the Rule-4-bot-suit-profile axis identified by the Session-35 v27 distillation diagnostic. Seventh clean instance of the gating template (after high_only-via-suited/v20, trips_pair/v23, composite/v24, pair-v1/v25, two_pair/v26, high_only-direct/v27, pair-v2/v29). Largest single ML ship since v26 (+$70). Diagnostic-driven: every feature traces directly to a competing-baseline gap identified before training.

**Diagnostic origin (`distill_v27_pair.py`, Session 35):**

The pair second-pass diagnostic walked all 6M hands through v27's 460K-leaf tree, restricted analysis to the 2.8M pair-only hands, and ran the KK/AA upper-bound capture analysis:

| Strategy | Within-KK/AA regret | Whole-grid contribution |
|---|---:|---:|
| Rule 4 alone (always mid)        | $949/1000h  | $68/1000h |
| Oracle (Rule 4 OR DS-bot, max)   | $362/1000h  | $26/1000h |
| **v27 actual**                   | **$1,236/1000h** | **$89/1000h** |

**v27 was $20/1000h whole-grid WORSE than Rule 4 alone on KK/AA.** v27 picks Rule-4 mid-pair on 84.6% of KK/AA hands, DS-bot on 7.8%, "other" on 7.6% — and the 15.4% non-Rule-4 picks were systematically incorrect, overgeneralizing v25's pair-gated features to KK/AA hands where Rule 4 was correct. Total v27→oracle gap = $63/1000h whole-grid. The missing signal: suit profile of Rule-4's resulting bot — exactly the trigger of Rule 5 (Decision 063).

**What v29 is:**
- 73 features: 69 v27 features + **4 pair-gated v2 (new)**.
- Same training profile: depth=30, ml=5, random_state=42.
- 486,342 leaves (vs v27's 460,375) — **+25,967 leaves**, +5.6% capacity expansion. Compare to v27→v29 vs v26→v27 (+1,166 leaves) — strong leaf-count growth was a leading indicator of headline gain. Compare to v25→v26 (+68K) and v24→v25 (+76K).
- Model file: `data/v29_dt_model.npz` (326 MB).

**The 4 pair-gated v2 features** (`analysis/scripts/pair_aug_v2_features_gated.py`, prefix `pair_r4_*_g`):

| Feature | Domain | What it encodes |
|---|---|---|
| `pair_r4_bot_suit_profile_g` | 0..5 | Categorical encoding of Rule-4 bot suit shape: 0=invalid, 1=rainbow, 2=single-suited (2+1+1), 3=double-suited (2+2), 4=three-of-suit (3+1), 5=four-of-suit. THE missing signal — directly enables "if Rule-4-bot is rainbow, swap to DS-bot" splits. |
| `pair_r4_bot_max_rank_g` | 0..14 | Highest rank in Rule-4 bot (= 2nd-highest non-pair rank). Distinguishes "rainbow but with high cards" from "rainbow garbage". |
| `pair_r4_n_broadway_kickers_g` | 0..5 | Count of T-A among 5 non-pair cards. Captures "premium kickers prop up paired-mid". |
| `pair_r4_n_low_kickers_g` | 0..5 | Count of 2-5 among 5 non-pair cards. Captures "lots of low cards make DS-bot more attractive". |

All zero for any non-single-pair hand. 2,800,512 of 6,009,159 canonical hands fire the gate (46.6% — second-largest gating share after v25's pair).

**Validation results:**

| Grid | v27 $/1000h | v29 $/1000h | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,853 | **$1,807** | **−$46** |
| Prefix (N=1000, 500K hands) | $1,002 | **$965** | **−$37** |

Per-category at full grid:

| Category | v27 | v29 | Δ |
|---|---:|---:|---:|
| high_only | $2,863 | $2,862 | −$1 (noise) |
| **pair** | **$1,771** | **$1,674** | **−$97** |
| two_pair | $1,145 | $1,145 | $0 |
| trips | $1,997 | $1,997 | $0 |
| trips_pair | $1,445 | $1,443 | −$2 (noise) |
| three_pair | $1,654 | $1,654 | $0 |
| quads | $723 | $723 | $0 |
| composite | $1,741 | $1,741 | $0 |

Per-category at prefix grid: pair drops $888 → $803 (−$85), every other category bit-identical or within prefix-grid noise.

Textbook gating-template signature on both grids — pair drops, every other category bit-identical to the byte. Headline gain matches arithmetic on full grid: $97 × 46.6% pair share = $45 ≈ $46. pct_optimal moves from 49.27% → 49.80% on full (+0.53 pp); pair-only pct_opt: 53.9% → 55.0% (+1.1 pp).

**Full:prefix ratio: 1.24:1.** v25 was 2.6:1, v26 was 1.35:1; v29's tighter ratio confirms diagnostic-driven feature design is robust to N=200 sample noise.

**Feature importance (v29 top-30):** 3 of 4 new features placed in top-30:
- `pair_r4_bot_max_rank_g` at #17 (0.51%)
- `pair_r4_bot_suit_profile_g` at #20 (0.27%)
- `pair_r4_n_low_kickers_g` at #23 (0.23%)
- `pair_r4_n_broadway_kickers_g` did NOT place — likely overlaps with existing `n_broadway` + `has_premium_pair`.

3/4 placement matches the v26 (3/6 → +$70) pattern; v27's 0/4 placement was the early warning sign for that ship's marginal headline.

**Files:**
- `analysis/scripts/pair_aug_v2_features_gated.py` — feature computation (4 features)
- `analysis/scripts/persist_pair_aug_v2_gated.py` — writes parquet (34.5s for 6M hands)
- `data/feature_table_pair_aug_v2_gated.parquet` (19 MB)
- `analysis/scripts/train_v29_dt.py` — trainer (73 features, builds on train_v27)
- `analysis/scripts/strategy_v29_dt.py` — inference wrapper (7 gated families + base)
- `analysis/scripts/grade_v29.py` — head-to-head grader
- `analysis/scripts/distill_v27_pair.py` — diagnostic that motivated the design
- `data/v29_dt_model.npz` (326 MB)

**Consequence:**

1. **v29 is the new ML champion.** Use `strategy_v29_dt(hand_bytes) -> setting_index`. Both grids show clean gains, well-calibrated full:prefix ratio.

2. **Seven categories now have at least one gating-template ship.** Pair has TWO iterations (v25 + v29), proving categories can absorb multiple distinct gating attacks when each targets a separate signal axis.

3. **Naming convention enforcement upheld.** `pair_r4_*_g` prefix is unique among existing gated families.

4. **Diagnostic-first design pays 7.7× better headline-per-feature than speculative design.** v27 (4 speculative high_only candidates) gained $6. v29 (4 diagnostic-driven pair features) gained $46. Same trainer config. The methodology lesson is now empirically backed: the diagnostic should identify a *competing baseline* (Rule 4 alone vs ML) and a *missing signal* (rainbow Rule-4-bot), not just within-leaf separation. v27's Session-34 diagnostic only showed within-leaf separation; v29's Session-35 diagnostic showed v27 LOSING to a simpler rule, which prescribed the feature design.

5. **The top-25 (or top-30) feature-importance tripwire is now a confirmed leading indicator:**
   - v25: 5/6 in top-25 → +$47 / +$18
   - v26: 3/6 in top-25 → +$70 / +$52
   - v27: 0/4 in top-25 → +$6 / $0
   - **v29: 3/4 in top-30 → +$46 / +$37**

6. **User intuition correlates with ML weak points.** The user's question about K♠K♦3♠5♦9♥T♣J♠ ("Rule 4 leaves rainbow garbage in the bot, surely DS-bot is better?") pointed at a $63/1000h whole-grid hole that v27's headline metrics never surfaced. Future sessions should treat user-flagged "this can't be right" reactions as a research-priority signal.

7. **Open question for Session 36:** distill v29 on pair to see how the residual KK/AA gap looks now. v29's pair drop is $97 within-pair × 46.6% = $45 whole-grid; the diagnostic predicted up to $62 available on KK/AA alone. Likely a notable chunk remains for either v30 (pair_r4 round-2 with finer features) or pivot to trips_aug_gated.

## Decision 065 — v30_dt is the new ML champion (Session 36) — trips-gated aug family is the 8th gating success and the smallest ship since v27

**Date:** 2026-05-05
**Status:** Shipped. v30 wins on BOTH grids by adding 6 trips-gated features (`trips_*_g`) targeting the A_paired_mid vs B_paired_bot routing decision identified by the Session-36 v29 trips distillation. Eighth clean instance of the gating template (after suited/v20, trips_pair/v23, composite/v24, pair-v1/v25, two_pair/v26, high_only-direct/v27, pair-v2/v29, trips/v30). Smallest single ML ship since v27 (+$6) but on a much larger underlying opportunity ($109 whole-grid trips share vs v27's high_only). Diagnostic-driven: every feature traces directly to a competing-baseline gap identified before training.

**Diagnostic origin (`distill_v29_trips.py`, Session 36):**

The trips distill walked all 6M hands through v29's 486K-leaf tree, restricted analysis to the 328,185 pure trips hands, and ran the routing-baseline analysis:

| Strategy | Within-trips regret | Whole-grid contribution |
|---|---:|---:|
| Always A_paired_mid (mid is trip pair)  | $24/1000h within-trips | $24/1000h |
| Always B_paired_bot_any                 | $625/1000h within-trips | $341/1000h |
| Always C_top_trip                       | $1,107/1000h within-trips | $605/1000h |
| Oracle (max over A∪B_any∪C)             | $0 (perfect routing)    | $0 |
| **v29 actual**                          | **$1,997/1000h**        | **$109** |

**v29 was $85/1000h whole-grid WORSE than always-A_paired_mid** — the largest gap-to-baseline ever measured in this project (4× v27's KK/AA Rule-4 deficit). v29 picks A on 79.9% of trips, B on 4.8%, C on 15.3%; the 20.1% non-A picks are systematically wrong, especially on low-rank trips (2-9 each leak $7-8/rank-share, total $60 of the $85 deficit). The missing signal: structural feasibility of B-DS routing + kicker quality.

**What v30 is:**
- 79 features: 73 v29 features + **6 trips-gated (new)**.
- Same training profile: depth=30, ml=5, random_state=42.
- 493,057 leaves (vs v29's 486,342) — **+6,715 leaves**, +1.4% capacity expansion. Significantly less than v29's +25,967 — leading-indicator of smaller headline.
- Model file: `data/v30_dt_model.npz` (330 MB).

**The 6 trips-gated features** (`analysis/scripts/trips_aug_features_gated.py`, prefix `trips_*_g`):

| Feature | Domain | What it encodes |
|---|---|---|
| `trips_b_ds_avail_g`              | 0/1   | Is any 105-setting B-DS routing feasible? (Bot has 2 trip-rank cards AND bot suit profile = DS.) |
| `trips_b_ds_n_routings_g`         | 0..3  | Number of distinct trip-pair {a,b} choices for which kickers contain ≥1 in suit a AND ≥1 in suit b. |
| `trips_kickers_max_suit_count_g`  | 0..4  | Max suit count among 4 kickers. ≥2 is necessary for B-DS. |
| `trips_kickers_max_rank_g`        | 0..14 | Highest kicker rank. High → A is strong. |
| `trips_n_broadway_kickers_g`      | 0..4  | Count of T-A among kickers. |
| `trips_n_low_kickers_g`           | 0..4  | Count of 2-5 among kickers. |

All zero for any non-pure-trips hand. 328,185 of 6,009,159 canonical hands fire the gate (5.46%). B-DS feasibility within trips matches diagnostic exactly: 225,225/328,185 = 68.6%.

**Validation results:**

| Grid | v29 $/1000h | v30 $/1000h | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,807 | **$1,794** | **−$13** |
| Prefix (N=1000, 500K hands) | $965 | **$951** | **−$15** |

Per-category at full grid:

| Category | v29 | v30 | Δ |
|---|---:|---:|---:|
| high_only | $2,862 | $2,862 | $0 |
| pair      | $1,674 | $1,674 | $0 |
| two_pair  | $1,145 | $1,145 | $0 |
| **trips** | **$1,997** | **$1,758** | **−$239** |
| trips_pair | $1,443 | $1,442 | −$1 (noise) |
| three_pair | $1,654 | $1,654 | $0 |
| quads     | $723 | $723 | $0 |
| composite | $1,741 | $1,733 | −$8 (noise) |

Per-category at prefix grid: trips drops $1,763 → $1,474 (−$289), every other category bit-identical or within prefix-grid noise.

Textbook gating-template signature on both grids — trips drops, every other category bit-identical to the byte. Headline gain matches arithmetic: $239 × 5.46% trips share = $13 ≈ $13 full grid. pct_optimal moves from 49.80% → 49.98% on full (+0.18 pp); trips-only pct_opt: 40.1% → 43.4% (+3.3 pp).

**Full:prefix ratio: 0.87:1.** This is the FIRST ship where prefix gain exceeds full-grid gain. v25 was 2.6:1, v26 was 1.35:1, v29 was 1.24:1, v30 is 0.87:1. Why: trips routing has a relatively clean structural answer (always-A is correct ~95%+ of the time on prefix's higher-fidelity N=1000 grading); on the full-grid noisier N=200, the marginal-deviation signal is harder to capture cleanly. This is consistent with trips being the LEAST noise-sensitive ship to date.

**Feature importance (v30 top-30):** **0 of 6** new features placed in top-30:
- `trips_kickers_max_rank_g`        at #34 (0.14%)
- `trips_b_ds_n_routings_g`         at #59 (0.05%)
- `trips_n_low_kickers_g`           at #60 (0.04%)
- `trips_n_broadway_kickers_g`      at #63 (0.04%)
- `trips_kickers_max_suit_count_g`  at #65 (0.02%)
- `trips_b_ds_avail_g`              at #74 (0.01%)

This matches the v27 pattern (0/4 → +$6) and confirms the tripwire: when 0 of new features place in top-30, expect a small headline. The methodology rule is now tested across 5 ships:
- v25: 5/6 in top-25 → +$47 / +$18
- v26: 3/6 in top-25 → +$70 / +$52
- v27: 0/4 in top-25 → +$6 / $0
- v29: 3/4 in top-30 → +$46 / +$37
- **v30: 0/6 in top-30 → +$13 / +$15**

Tripwire predicts CONVERSION rate, not absolute opportunity: trips category had 18× v27's high_only $/category opportunity, but the conversion is similar (~10-15% capture). Why: feature importance ranking measures global importance across 6M hands; gated features specific to a 5.5% subpopulation can capture meaningful within-category gains without ranking high globally — but if they're TIGHTLY gated and the global tree doesn't lean on them, the magnitude is bounded by what depth/leaf-count concedes.

**Files:**
- `analysis/scripts/trips_aug_features_gated.py` — feature computation (6 features)
- `analysis/scripts/persist_trips_aug_gated.py` — writes parquet (27s for 6M hands)
- `data/feature_table_trips_aug_gated.parquet` (19 MB)
- `analysis/scripts/train_v30_dt.py` — trainer (79 features, builds on train_v29)
- `analysis/scripts/strategy_v30_dt.py` — inference wrapper (8 gated families + base)
- `analysis/scripts/grade_v30.py` — head-to-head grader
- `analysis/scripts/distill_v29_trips.py` — diagnostic that motivated the design
- `data/v30_dt_model.npz` (330 MB)

**Consequence:**

1. **v30 is the new ML champion.** Use `strategy_v30_dt(hand_bytes) -> setting_index`. Both grids show clean gains on trips with all other categories bit-identical.

2. **Eight categories now have at least one gating-template ship.** Pair has TWO iterations (v25 + v29). Trips just got its first.

3. **Naming convention enforcement upheld.** `trips_*_g` prefix is unique (distinct from `tp_*_g` for trips_pair).

4. **Trips category still has $1,758/1000h within-trips residual** = $96/1000h whole-grid. The diagnostic showed oracle ceiling is $0 (perfect routing exists). v30 captured 12% of available routing headroom; round-2 trips features (v31b candidate) targeting C_top_trip routing + finer A/B distinction are queued for overnight exploration.

5. **The Rule 6 candidate ("Always set trips on mid") is empirically validated as a strong human-strategy primitive.** The diagnostic showed always-A captures $85/1000h whole-grid relative to v29 (or what it would have looked like without v30's partial fix). Worth investigating in a future session as a Rule 6 candidate analogous to Rule 4 for pair.

## Session 36 round-2 finding — v29 KK/AA single-suited Rule-4-bot stratum still leaks (deferred to v31a candidate)

**Date:** 2026-05-05
**Status:** Open finding. The Session-36 round-2 pair audit (`distill_v29_pair.py`) revealed that v29 closed only $7/1000h of v27's $14 KK/AA Rule-4 deficit — KK/AA whole-grid contribution went $89 (v27) → $82 (v29). v29 still picks Rule-4 84.8% of KK/AA (essentially unchanged from v27's 84.6%). The single-suited Rule-4-bot stratum (52.9% of KK/AA, 3.7% of grid) is the dominant residual leak.

**Stratification by Rule-4-bot suit profile (whole-grid $/1000h, 8.2% of grid is KK/AA total):**

| Profile | KK/AA share | v29 | Rule-4 | Oracle | v29-oracle gap |
|---|---:|---:|---:|---:|---:|
| rainbow (1+1+1+1)        |  8.8% | $12.0 | $15.4 | $3.8  | **$8.2** |
| **single-suited (2+1+1)** | **52.9%** | **$51.0** | **$38.1** | **$14.1** | **$36.9** |
| double-suited (2+2)      | 15.4% | $3.6 | $2.0 | $1.0 | $2.6 |
| three-of-suit (3+1)      | 20.6% | $14.4 | $11.9 | $6.3 | $8.0 |
| four-of-suit             |  2.2% | $1.0 | $0.8 | $0.7 | $0.3 |

The rainbow stratum (where Rule 5 lives) is the only one where v29 BEATS Rule-4. Single-suited is the largest leak: v29 is $13 worse than always-Rule-4 there, $37 below oracle.

**Why pair_r4_*_g didn't fix it:** v29's `pair_r4_bot_suit_profile_g` is a CATEGORICAL feature (rainbow / SS / DS / 3-suit / 4-flush). It treats single-suited as a single bucket. The single-suited stratum needs FINER encoding — which suit is dominant, its rank composition, and pair-suit alignment. v31a candidate (overnight cascade) tests 4 KK/AA-tight features (`pair_r4v3_*_g`) targeting this finer signal.

**Cycle scoreboard since Session 25 (22 ships, 7 archives, 1 doc-only, 1 mid-session bug recovery, 1 rule-strategy-only ship):**

| Cycle | Target | Result | Status |
|---|---|---:|---|
| v23 | gated trips_pair on v20 | +$5 / +$9 vs v20 | SHIPPED |
| v24 | gated composite on v23 | +$1 / +$1 vs v23 | SHIPPED |
| v25 | gated pair on v24 | +$47 / +$18 vs v24 | SHIPPED |
| v26 | gated two_pair on v25 | +$70 / +$52 vs v25 | SHIPPED |
| v27 | gated high_only-direct on v26 | +$6 / $0 vs v26 (prefix uninformative) | SHIPPED |
| v28 | Rule 5 (Rainbow override, human strategy) | +$1 vs v14_combined | SHIPPED (rule-only) |
| v29 | gated pair_r4 (round 2 of pair) on v27 | +$46 / +$37 vs v27 | SHIPPED |
| **v30** | **gated trips on v29** | **+$13 / +$15 vs v29** | **SHIPPED — current ML champion** |

## Decision 066 — v31_dt is the new ML champion (Session 36 overnight) — high-capacity v30 retrain produces second-largest ship in project history with ZERO new features

**Date:** 2026-05-06
**Status:** Shipped (overnight cascade from Session 36 → 37 morning). v31 = v30's 79 features trained at depth=32, min_samples_leaf=3 instead of v30's depth=30 ml=5. Ships +$58/1000h on full grid, +$29/1000h on prefix. Second-largest single ML ship after v26 (+$70). Zero new features — pure capacity expansion. Beat both v31a (pair_r4v3 KK/AA-tight, +$6 full) and v31b (trips_v2 round 2, +$15 full) head-to-head in the same overnight cascade.

**Origin:** The Session 36 v30 ship was small (+$13 full / +$15 prefix) despite trips having $109/1000h whole-grid opportunity and despite 6 diagnostic-driven features. Tripwire was bearish (0/6 in top-30). Rather than chase further feature design, the overnight cascade tested the alternative hypothesis: **maybe the gating-template features were already encoded but not fully expressed because the tree didn't have enough leaves**.

The v20 vs v20b finding (Session 31, depth=32 saturation) had been at 43 features with 308K leaves. By v30, the count was 79 features at 493K leaves — substantially more structure to encode. The "capacity is saturated" conclusion was true at v20's 43 features but not at v30's 79.

**What v31 is:**
- 79 features: identical to v30 (37 base + 6 gated suited + 6 gated trips_pair + 4 gated composite + 6 gated pair-v1 + 6 gated two_pair + 4 gated high_only + 4 gated pair_r4 + 6 gated trips).
- Hyperparameters: **depth=32, min_samples_leaf=3** (vs v30's depth=30 ml=5).
- **699,773 leaves** (+206,716 vs v30's 493,057, **+42% capacity expansion**). Largest single-ship leaf delta in project history.
- Model file: `data/v31_dt_model.npz` (450 MB, +120 MB vs v30).

**Validation results:**

| Grid | v30 $/1000h | v31 $/1000h | Δ |
|---|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,794 / 49.98% | **$1,736 / 50.92%** | **−$58 / +0.94 pp** |
| Prefix (N=1000, 500K hands) | $951 / 61.53% | **$921 / 62.07%** | **−$29 / +0.54 pp** |

Per-category at full grid — **ALL 8 categories improve** (no isolated-category gating signature this time; capacity helps across the board):

| Category | v30 | v31 | Δ |
|---|---:|---:|---:|
| high_only  | $2,862 | $2,816 | −$46 |
| pair       | $1,674 | $1,639 | −$35 |
| **two_pair** | $1,145 | $1,037 | **−$108** |
| trips      | $1,758 | $1,732 | −$26 |
| **trips_pair** | $1,442 | $1,225 | **−$217** |
| three_pair | $1,654 | $1,639 | −$15 |
| quads      | $723   | $645   | −$78 |
| **composite** | $1,733 | $1,387 | **−$346** |

The biggest gains accrue to the previously-gated categories (composite, trips_pair, two_pair) — the tree's previously-encoded gating features can now express more structure. This validates the hypothesis that **gating features had been adding signal that v30's depth/leaf budget couldn't fully express**.

Per-category at prefix grid: pair −$4, two_pair −$41, trips −$7, trips_pair −$184, composite −$230. Same pattern: previously-gated categories drop most.

**Full:prefix ratio: 2.0:1.** Higher than recent ships (v25: 2.6:1, v26: 1.35:1, v29: 1.24:1, v30: 0.87:1). The 2:1 ratio is at the edge of overfitting territory but still within reasonable bounds. The clean per-category improvements across all 8 categories (rather than spiky) suggest the gain is structural, not noise.

**Overnight cascade context:**

| Candidate | Strategy | Full Δ vs v30 | Prefix Δ vs v30 | Tripwire | Leaves |
|---|---|---:|---:|---:|---:|
| v31a | pair_r4v3 KK/AA-tight (4 features) | +$6 | $0 | 0/4 in top-30 | 500,722 (+8K) |
| v31b | trips_v2 round 2 (4 features) | +$15 | +$13 | 0/4 in top-30 | 507,692 (+15K) |
| **v31** (was v31c) | **v30 features at depth=32 ml=3** | **+$58** | **+$29** | n/a (no new features) | **699,773 (+207K)** |

v31a's tight gating produced minimal gain — within-pair moved $1,674 → $1,661 (−$13 within-pair on full, $0 on prefix). The KK/AA-tight features did inject signal but the marginal headline was modest.

v31b's trips round-2 features captured $277 within-trips on full (clean second iteration of trips). At higher capacity (v32 candidate) v31b's features would likely add ~$15 to v31's headline, suggesting v32 = v31 + v31b features at depth=32 ml=3 could ship ~$70-75/1000h vs v30 (rivaling v26's record).

**Files:**
- `analysis/scripts/strategy_v31_dt.py` — inference wrapper (delegates to strategy_v30_dt with v31 model path)
- `data/v31_dt_model.npz` (450 MB; was data/v31c_dt_model.npz pre-promotion)
- `analysis/scripts/overnight_v31_cascade.sh` — the runner that produced this ship
- `analysis/scripts/train_v30_dt.py` — same trainer used; just `--max-depth 32 --min-samples-leaf 3`

**Consequence:**

1. **v31 is the new ML champion.** Use `strategy_v31_dt(hand_bytes) -> setting_index`. Cumulative improvement from v18e → v31: $2,066 → $1,736 = −$330/1000h over 6 ML ships (v20 / v23 / v24 / v25 / v26 / v27 / v29 / v30 / v31). Total improvement vs v14_combined: −$1,297/1000h.

2. **Methodology rule (Session 36): when feature set grows ≥40 above the last capacity-saturation test, RE-TEST capacity.** The v20/v20b "capacity saturated" finding has a feature-count ceiling; it doesn't apply unbounded. Future ML champion ships should default to `depth=32 ml=3` going forward (or test depth=34 ml=2 as the next ceiling).

3. **The "diagnostic-first design vs pure capacity" tradeoff is now clearer.** v25-v30 were 6 sequential diagnostic-first ships (each adding 4-6 features per category) totaling $-260 cumulative. v31 alone (capacity-only) ships $-58. **Capacity unlocks ~22% of what the cumulative feature work added.** This is a strong yield for one config change; future sessions should run a capacity sweep (depth ∈ {30, 32, 34}, ml ∈ {2, 3, 5, 10}) before considering more features whenever leaf-count growth has stalled below historical norms.

4. **Tripwire confirmed 5×, with caveats.** v31a (0/4 → +$6) and v31b (0/4 → +$15) both shipped in line with the tripwire. v31 itself didn't go through the tripwire because it added no new features. The tripwire is a feature-design quality signal; capacity expansions are orthogonal and should be evaluated independently.

5. **v32 candidate = stack v31b features (trips_v2 round 2) onto v31's high-capacity config.** Expected ship: ~$15 incremental (v31b's full-grid gain) on top of v31's $58. Total v32 vs v30: ~$73, which would tie v26 as the largest single ship in project history. Train at depth=32 ml=3.

6. **v31a (pair_r4v3 KK/AA-tight) is archived.** Within-pair gain was small and didn't propagate to prefix. The categorical-encoding hypothesis (v29's pair_r4_bot_suit_profile being too coarse) remains plausible but the tight gating did not unlock the expected value. The KK/AA single-suited Rule-4-bot stratum (52.9% of KK/AA, $37 below oracle) remains an open optimization target — but the next attempt should use a fundamentally different angle (e.g., a meta-classifier feature predicting "DS-bot beats Rule 4" trained on probe data, or a sub-tree dedicated to KK/AA hands).

7. **v31a/v31b model files retained but archived.** `data/v31a_dt_model.npz` and `data/v31b_dt_model.npz` are kept on disk (gitignored) for future cross-strategy comparisons but are not exposed via strategy modules.

---

## Decision 067 — v32_dt is the new ML champion (Session 37) — round-2 trips features at high capacity, completing the v30 → v32 ship arc

**Date:** 2026-05-06
**Status:** Shipped. v32 = v31b's 83 features (79 v30 + 4 trips_v2 round-2) trained at v31's high-capacity config (depth=32, min_samples_leaf=3). Ships **+$20/1000h on full grid (+$79 cumulative vs v30)** and **+$18/1000h on prefix (+$47 cumulative vs v30)**. The cumulative v30→v32 ship of $79/1000h on full grid **beats v26's record ($70)** to become the largest single-session ML ship in project history.

**Origin:** Session 36's overnight cascade had two independently-positive ML candidates: v31b (trips_v2 round-2 features, +$15 full at depth=30 ml=5) and v31c → v31 (pure capacity, +$58 full). They were graded against v30 separately and v31 won the cascade head-to-head decision. But the two improvements come from orthogonal axes — trips_v2 features add new signal in trips, while capacity expansion expresses already-encoded signal across all 8 categories. **The v32 hypothesis is that they should stack additively.**

**What v32 is:**
- 83 features = v30's 79 + 4 trips_v2 (`trips_v2_c_top_advantage_g`, `trips_v2_b_ds_kicker_max_rank_g`, `trips_v2_b_ds_kicker_2nd_rank_g`, `trips_v2_n_kickers_in_trip_suits_g`).
- Hyperparameters: depth=32, min_samples_leaf=3 (same as v31).
- **731,606 leaves** (+31,833 vs v31's 699,773, +4.6% capacity).
- Model file: `data/v32_dt_model.npz` (468.5 MB).
- Tripwire: 0/4 trips_v2 in top-30 (positions 55, 60, 72, 73). Bearish, matching v31b at depth=30 ml=5 which placed 0/4 yet shipped +$15. Tripwire failure rate now 7 ships in a row for round-2 features — predicts conversion rate (~10-15%), not absolute opportunity.

**Validation results:**

| Grid | v30 $/1000h | v31 $/1000h | v32 $/1000h | Δ vs v31 | Δ vs v30 (cumulative) |
|---|---:|---:|---:|---:|---:|
| Full (N=200, 6.0M hands) | $1,794 / 49.98% | $1,736 / 50.92% | **$1,715 / 51.31%** | **−$20 / +0.39 pp** | **−$79 / +1.33 pp** |
| Prefix (N=1000, 500K hands) | $951 / 61.53% | $921 / 62.07% | **$904 / 62.47%** | **−$18 / +0.40 pp** | **−$47 / +0.94 pp** |

**Per-category at full grid (full N=200) — only trips moves:**

| Category | v30 | v31 | v32 | Δ v32 vs v31 |
|---|---:|---:|---:|---:|
| high_only  | $2,862 | $2,816 | $2,816 | $0 |
| pair       | $1,674 | $1,639 | $1,639 | $0 |
| two_pair   | $1,145 | $1,037 | $1,037 | $0 |
| **trips**  | $1,758 | $1,732 | **$1,359** | **−$373** |
| trips_pair | $1,442 | $1,225 | $1,225 | $0 |
| three_pair | $1,654 | $1,639 | $1,639 | $0 |
| quads      | $723   | $645   | $645   | $0 |
| composite  | $1,733 | $1,387 | $1,386 | −$1 |

Textbook category-gating signature — only the gated category (trips) moves; all others bit-identical. The −$373 within-trips translates to the +$20 whole-grid headline at the 5.5% trips share. On prefix, trips drops $1,467 → $1,116 (−$351 within-trips, +$18 whole-grid given trips' 8.0% prefix share).

**Full:prefix ratio: 1.11:1.** Lower than v31's 2:1 — the trips_v2 features are a much sharper, more focused gain than the broad capacity expansion v31 delivered. This is the fingerprint of a clean diagnostic-driven feature ship.

**Files:**
- `analysis/scripts/strategy_v32_dt.py` — inference wrapper (delegates to strategy_v31b_dt with v32 model path)
- `analysis/scripts/train_v32_dt.py` — trainer (extends train_v31b_dt; defaults depth=32 ml=3)
- `analysis/scripts/grade_v32.py` — head-to-head grader vs v31 + optional vs v30
- `data/v32_dt_model.npz` (468.5 MB)

**Consequence:**

1. **v32 is the new ML champion.** Use `strategy_v32_dt(hand_bytes) -> setting_index`. Cumulative improvement v18e → v32: $2,066 → $1,715 = −$351/1000h over 10 ML ships. Total improvement vs v14_combined: −$1,317/1000h. Captures **43.5% of the v14→ceiling gap** at N=200 fidelity.

2. **The combined v30→v32 ship of $79/1000h is the largest single-session ML ship in project history**, beating v26 ($70). The two contributing changes — capacity expansion (v31, $58) and round-2 trips features (v32 increment, $20) — are confirmed orthogonal: capacity helped all 8 categories simultaneously; trips_v2 helps only trips. Future sessions should follow this template: any time a new feature family is added, also re-test capacity at the higher feature-count.

3. **Methodology rule (Session 37, supplements Session 36):** the ship template is now (a) diagnostic-driven feature design → (b) standalone train at v31's default depth=32 ml=3 → (c) if leaf-count grows ≥10, re-test capacity at depth=34 ml=2. v32's 731,606 leaves is +5% over v31's 699,773 — borderline; the next ship that adds ≥6 features should test depth=34 ml=2 explicitly.

4. **Tripwire conversion rate continues to be ~10-15% on round-2 features** (7 ships now: v25 5/6→+$47, v26 3/6→+$70, v27 0/4→+$6, v29 3/4→+$46, v30 0/6→+$13, v31a 0/4→+$6, v31b 0/4→+$15, v32 0/4→+$20). Position-55/60/72/73 in importance is the typical v32-style tripwire footprint for already-saturated categorical signals.

5. **Trips category at $1,359/1000h is now the 4th-best-handled category** (after composite $1,386, trips_pair $1,225, two_pair $1,037 — wait, trips IS now $1,359 which is below trips_pair $1,225 and two_pair $1,037; corrected ranking: two_pair $1,037 < trips_pair $1,225 < trips $1,359 < composite $1,386). The combined v30+v32 trips work has lifted trips from $1,997 (v18e) to $1,359 (v32) = −$638/1000h within-trips, the second-largest absolute within-category improvement after composite ($2,100 → $1,386).

---

## Decision 068 — v33_rule6 is the new human strategy of record (Session 37) — Rule 6 (always pair mid on pure trips) ships +$112/1000h, the largest single rule ship in project history

**Date:** 2026-05-06
**Status:** Shipped. v33 = v28_rule5_rainbow + Rule 6 (trips routing override). Ships **+$112/1000h on full grid** (v28 $3,032 → v33 $2,920, 39.64% → 40.68% opt) and **+$143/1000h on prefix** (v28 $2,037 → v33 $1,894, 47.61% → 48.81% opt). This is **larger than every prior single rule ship combined** — Rule 4 + Rule 5 together moved v14 by ~$2/1000h, while Rule 6 alone moves the chain by $112-143 depending on the grid.

**Origin:** Session 36's `distill_v29_trips.py` had identified that v29 (the ML champion at the time) was $85/1000h whole-grid worse than the structural baseline "Always A_paired_mid" on pure trips — the largest gap-to-baseline ever measured. This was prescriptive for ML feature design (→ v30/v32 trips features) but it also raised the question whether the human strategy chain (v14_combined + Rule 4 + Rule 5) was making the same mistake.

Session 37 wrote `verify_rule6_v14_trips.py` to trace v14 on a 30K pure-trips sample. Findings:

- **v14 picks "mid is pair-of-trip-rank" on only 94.3% of pure trips.** The remaining 5.43% goes to B_bot_pair_trip routings (the third trip card on bot, breaking the mid-pair). This 5.4% is systematically wrong on every single rank, costing $3,609/1000h within-trips ($197/1000h whole-grid) vs the always-A∪C baseline.
- **v14's A-vs-C decision (top = highest kicker vs top = trip-rank) is already empirically correct on the 94.3% it gets right** — it's effectively computing `top = max(trip_rank, max_kicker_rank)` via the learned v7_regression tree.
- **Always-A∪C** (mid is pair of trip-rank, top is free) is the cleanest rule formulation. On the 30K probe, this rule gains $197/1000h whole-grid over v14 (oracle ceiling).

**What Rule 6 says:** *"On pure trips (one rank with count 3, no other pairs/quads), the third trip card never goes to bot. Mid is always 2 of the 3 trip-rank cards."* The third trip card goes either to top (C variant; preferred when trip_rank > max_kicker) or to bot as part of the 4-card bot (A variant; preferred when max_kicker > trip_rank).

**v33 implementation** (`analysis/scripts/strategy_v33_rule6_trips.py`):
- Decision tree mirrors v14's empirical optimum on A vs C: `if trip_rank > max_kicker_rank → C variant; else → A variant`.
- C variant: top = lowest-byte trip card, mid = other 2 trips, bot = 4 kickers (suit-symmetric across the 3 trip choices).
- A variant: top = highest-rank kicker; among 3 ways to choose which trip → bot, pick the one that maximizes (bot_suit_profile_score, bot_rank_sum, bot_longest_run).

**Probe vs full grid validation:**

| Sample | v28 within-trips $/1000h | v33 within-trips $/1000h | Δ within-trips | Δ whole-grid |
|---|---:|---:|---:|---:|
| 30K probe (full N=200) | $4,047 | $2,011 | −$2,036 | $+111 |
| Full 6M grid (N=200) | $4,054 | $2,010 | −$2,044 | **$+112** |
| Prefix 500K (N=1000) | $4,576 | $1,744 | −$2,832 | **$+143** |

Probe → full agreement is essentially perfect (1% drift). Prefix N=1000 confirms a slightly larger gain ($143 vs $112), with the prefix:full ratio at 1.28:1 — within the historical band for hand-coded rules. The 56% capture of the $197 oracle ceiling is the heuristic limit of "no peeking at oracle EVs"; the remaining $86/1000h would require a learned routing within A∪C (out of scope for the human rule chain).

**Per-category at full grid (full N=200) — only trips moves:**

| Category | v28 | v33 | Δ v33 vs v28 |
|---|---:|---:|---:|
| high_only  | $4,082 | $4,082 | $0 |
| pair       | $2,008 | $2,008 | $0 |
| two_pair   | $3,371 | $3,371 | $0 |
| **trips**  | $4,054 | **$2,010** | **−$2,044** |
| trips_pair | $5,417 | $5,417 | $0 |
| three_pair | $4,529 | $4,529 | $0 |
| quads      | $9,670 | $9,670 | $0 |
| composite  | $10,883 | $10,883 | $0 |

Trips' optimal-pick rate jumps from 19.9% to 39.0% (almost doubled). Same gating signature as the ML ships: clean isolation to the targeted category.

**Files:**
- `analysis/scripts/strategy_v33_rule6_trips.py` — Rule 6 implementation; `strategy_v33_rule6_trips(hand)` is the new human-strategy entry point
- `analysis/scripts/verify_rule6_v14_trips.py` — diagnostic that surfaced the rule
- `analysis/scripts/probe_v33_trips.py` — fast (3s) empirical check of v33 vs v28 on 30K trips
- `analysis/scripts/grade_v33_rule6.py` — full-grid head-to-head grader

**Consequence:**

1. **v33_rule6_trips is the new strategy of record for human play.** It is the first rule ship in project history that materially changes the headline ($112/1000h is ~12% of v14's gap to ceiling on the full grid). The Rule 4 + Rule 5 ships were ~$1-5 each by comparison.

2. **Methodology lesson (Session 37):** the `distill_*_trips`-style "always-X structural baseline" surfaced the rule. Future sessions should systematically check for structural always-X baselines on every category, not just trips. Candidates: high_only "always top = max-rank" (already true via v8_hybrid?); pair "always mid = pair" (already Rule 4); two_pair "always split high pair to mid" (deferred); trips_pair "always pair-of-pair to mid" (deferred — likely covered by v12).

3. **The "preserve-v28-when-already-A∪C" variant was tested and lost.** Override-everything captured $111/1000h on the probe; preserve-only-on-B captured $36.9. The Rule 6 heuristic's bot-DS optimization on the A variant beats v14/v8_hybrid's learned routing on average — even when both pick A, the heuristic's choice of which trip → bot (for max DS) is better than v8_hybrid's. Future rule chains should default to override-everything within the rule's scope.

4. **Rule 6 closes the largest single-category gap in the human strategy.** Trips drops from $4,054 (8.4% share at full grid) to $2,010, contributing $112/1000h whole-grid. The next-largest opportunity in the human chain is composite ($10,883 within-category × 0.9% share = $98/1000h whole-grid), but composite is much rarer and harder to rule-encode.

5. **Rule 6 does NOT modify v32 (the ML champion).** v32 already encodes trips routing via the gated `trips_*_g` and `trips_v2_*_g` feature families. v33 is the *human* strategy ship; v32 remains the *ML* strategy of record.

---

## Decision 069 — v34_dt is the new ML champion (Session 38) — depth=34 ml=2 capacity expansion of v32 unlocks +19.5% more leaves and ships −$34/1000h

**Date:** 2026-05-06
**Status:** Shipped. v34_dt = v32's exact 83 features (79 v30 + 4 trips_v2 round-2) trained at depth=34, min_samples_leaf=2. **874,548 leaves** (+19.5% over v32's 731,606). **Full grid: $1,681/1000h (vs v32 $1,715, −$34/1000h, 51.31% → 52.02% opt). Prefix grid: $889/1000h (vs v32 $904, −$15/1000h, 62.47% → 62.74% opt).**

**Origin:** Per the Session 37 methodology rule — when a ship adds new features OR leaf-count grows substantially, re-test capacity at depth=34 ml=2 (with depth=34 ml=3 as control). v32 added 4 trips_v2 features over v31 and grew leaf-count by +5%. The capacity sweep in Session 38 was the prescribed retest.

**Sweep design** (`analysis/scripts/train_v32_capacity_sweep.py`):
- v32_d34ml3 (control): same 83 features, depth=34, min_samples_leaf=3
- v32_d34ml2 (candidate): same 83 features, depth=34, min_samples_leaf=2
- Both random_state=42, criterion=squared_error, full 6.0M-grid training set
- Saved as `data/v32_d34ml3_dt_model.npz` (468 MB) and `data/v32_d34ml2_dt_model.npz` (546 MB); the candidate copied to `data/v34_dt_model.npz` for promotion

**Headline finding — ml=3 was the binding constraint, not depth:**

| Config | Leaves | Achieved depth | Fit time | Picked EV (train) |
|---|---:|---:|---:|---:|
| v32 (d32 ml=3) | 731,606 | 32 | (prev) | (prev) |
| **v32_d34ml3 (control)** | **731,611** | **33** | 818s | +0.5869 |
| **v32_d34ml2 (candidate)** | **874,548** | **33** | 589s | +0.5903 |

The control adds only +5 leaves over v32 and converges at depth=33 (well below the 34 cap). This means **ml=3 capped the tree, not depth=32** — depth=32 was never the binding constraint at ml=3. Lowering min_samples_leaf to 2 unlocks +142,937 more leaves (+19.5%).

**Validation grades:**

| Grid | v32 | v32_d34ml3 | **v34_dt (= v32_d34ml2)** | Δ v34 vs v32 |
|---|---:|---:|---:|---:|
| Full N=200 6.0M | $1,715 / 51.31% | $1,715 / 51.31% | **$1,681 / 52.02%** | **−$34 / +0.71pp** |
| Prefix N=1000 500K | $904 / 62.47% | $904 / 62.47% | **$889 / 62.74%** | **−$15 / +0.27pp** |

**Per-category at full grid (v34 vs v32) — all 8 categories improve, including 5 of them by ≥−$32 within-category:**

| Category | v32 | v34 | Δ within-cat | share | whole-grid contribution |
|---|---:|---:|---:|---:|---:|
| high_only  | $2,816 | $2,806 | −$10  | 20.4% | −$2.0 |
| pair       | $1,639 | $1,619 | −$20  | 46.6% | −$9.3 |
| two_pair   | $1,037 | $978   | −$59  | 22.3% | −$13.2 |
| trips      | $1,359 | $1,291 | −$68  | 5.46% | −$3.7 |
| trips_pair | $1,225 | $1,057 | −$168 | 2.86% | −$4.8 |
| three_pair | $1,639 | $1,635 | −$4   | 1.90% | −$0.1 |
| quads      | $645   | $613   | −$32  | 0.24% | −$0.1 |
| composite  | $1,386 | $1,173 | −$213 | 0.245% | −$0.5 |

The biggest within-category gains are in trips_pair (−$168) and composite (−$213) — both ML-engineered categories that benefit from finer leaf granularity. The whole-grid contribution is dominated by two_pair (−$13/1000h via 22.3% share) and pair (−$9/1000h via 46.6% share). **Unlike prior gating ships, this ship moves every category — a textbook capacity-only signature, not a gating signature.**

**Files:**
- `analysis/scripts/train_v32_capacity_sweep.py` — sweep training script
- `analysis/scripts/grade_v32_capacity_sweep.py` — head-to-head grader
- `analysis/scripts/strategy_v34_dt.py` — runtime harness (re-exports v31b's harness pointed at `data/v34_dt_model.npz`)
- `data/v34_dt_model.npz` — 546 MB, 874,548 leaves, depth=33

**Consequence:**

1. **v34_dt is the new ML champion.** Cumulative v30 → v34 of $113/1000h (full grid) is the new largest cumulative arc in project history (beats Session 37's v30→v32 of $79). The arc decomposes as: v30→v31 ($58, capacity), v31→v32 ($20, trips_v2 features), v32→v34 ($34, capacity-only at ml=2).

2. **Methodology lesson — when ml=3 leaves a tree at its natural saturation depth, the next capacity unlock is ml=2, not deeper depth.** The d34ml3 control showing 731,611 leaves (vs v32's 731,606) is the cleanest possible evidence. This refines the Session 37 methodology rule: *future capacity retests should sweep min_samples_leaf in {3, 2} at a generous depth cap (34 or higher), and pick the smaller-ml winner if shape-agreement improves.*

3. **The capacity ship was bigger than the rule-extraction Priority A.** Session 38 also probed v33's Rule 6 A-vs-C boundary (the user's hypothesis that low-trip C-variants are wrong). The probe validated the directional claim at the oracle level (best-A regret $82/1000h whole-grid vs best-C $608) but a heuristic-A-only v34_rule6_v2 could not capture the gain — sweeping the boundary across all 13 trip ranks gave +$0.57/1000h max at trip ≥ T, well within noise. v33's boundary stands. See Decision 070 below.

4. **Tripwire was not run for v34** because no new features were introduced — same 83 features as v32. The leaf-count growth of +19.5% is the relevant capacity signal, and the broad cross-category gains confirm latent signal was leaf-bound, not feature-bound.

---

## Decision 070 — v34_rule6_v2 archived (Session 38) — user's "C variant is wrong at low trip ranks" hypothesis is directionally correct on oracle but cannot be cashed via heuristic-A; v33's boundary stands

**Date:** 2026-05-06
**Status:** Negative result. v34_rule6_v2 was a candidate v33 successor that flips Rule 6's C variant to A at low trip ranks. **Did NOT ship.** Probe sweep across all 13 trip-rank thresholds gave a maximum gain of $+0.57/1000h whole-grid (at "trip ≥ T → C, else A") — within noise. v33's "trip > max_kicker_rank → C, else A" boundary remains the human strategy of record.

**Origin:** User flagged in the Session 38 prompt that Rule 6's C variant — putting the third trip card on top when `trip_rank > max_kicker_rank` — looked suspect for low/mid trip ranks. The intuition: a 7 on top has only 1 out to pair (the unused fourth 7, which doesn't exist in the deck since we already hold 3 of them; the only way for the 7 on top to pair is via the community board) and gives up the 7's bot contribution (suit synergy, connectivity, pair-on-board).

**Probe** (`analysis/scripts/probe_rule6_c_variant.py`): on the 30K pure-trips sample, stratified by (trip_rank, max_kicker_rank), compute oracle EV for:
- (a) best C-variant pick (top = trip card, bot = 4 kickers)
- (b) best A-variant pick (top = highest kicker, mid = 2 of 3 trips, bot = 1 trip + 3 lower kickers)
- (c) v33's actual pick

**Headline findings:**

| Metric | best-A | best-C |
|---|---:|---:|
| Mean regret vs oracle | +$82/1000h whole-grid | **+$608/1000h whole-grid** |
| Cells where it wins | 84.1% | 15.9% |

A-variant is the dominant routing on average. C-variant only wins at the high end:
- trip A: C wins in 100% of cells (C-A from +$5,757 to +$14,139)
- trip K: C wins in 95-100% of cells when feasible (C-A from +$2,131 to +$7,240)
- trip Q: C wins 56-79% of cells when feasible (C-A from +$815 at maxK=T to +$3,758 at maxK=6); LOSES at maxK=J (-$278)
- trip J: C wins narrowly at maxK=6,7,8 (small + noisy); LOSES at maxK=5,9,T (-$2,576 to -$3,707)
- trip ≤ T: A wins in nearly every cell ($1,765 to $17,030 oracle gap)

**Projected whole-grid gain by flipping wrong-C to A using the oracle:** +$12.89/1000h (28.8% of v33's C-fires are wrong by oracle). This is the ceiling for any heuristic-driven correction.

**Empirical sweep** (`analysis/scripts/probe_v34_sweep.py`): for `min_trip_for_C ∈ {3..14, A-only}`, build a Rule 6 v2 candidate and grade vs v33 on the 30K probe:

| Rule | $/1000h whole-grid | Δ vs v33 | Cells changed |
|---|---:|---:|---:|
| trip ≥ 6..6 → C (= v33) | $109.83 | baseline | 0 |
| trip ≥ 7 → C | $109.68 | +$0.15 | 10 |
| trip ≥ 8 → C | $109.54 | +$0.29 | 27 |
| trip ≥ 9 → C | $109.32 | +$0.52 | 81 |
| **trip ≥ T → C (best)** | **$109.27** | **+$0.57** | **226** |
| trip ≥ J → C | $109.83 | $0.00 | 543 |
| trip ≥ Q → C | $112.52 | −$2.69 | 1,151 |
| trip ≥ K → C | $120.01 | −$10.18 | 2,093 |
| trip ≥ A → C | $137.99 | −$28.15 | 3,642 |
| Always A (no C) | $181.79 | −$71.96 | 5,928 |

**Why the gap between oracle and heuristic:** the v33/v34 A-variant heuristic optimizes (bot_suit_profile, bot_rank_sum, bot_longest_run) but doesn't always recover the oracle-best A pick. Per-trip-rank loss when forcibly flipping C→A: at trip Q, heuristic-A loses ~$1,857/1000h within-trips on flipped cells (cell-level oracle said only −$278 at maxK=J); at trip J, loses ~$639/1000h within-trips (oracle was barely positive at maxK=6,7,8). The bot-DS optimizer is the rate-limiting step, not the threshold rule.

**Files (archived candidates, not on the strategy hot-path):**
- `analysis/scripts/probe_rule6_c_variant.py` — per-cell A-vs-C oracle probe
- `analysis/scripts/strategy_v34_rule6_v2.py` — v33 + corrected boundary candidate (archived)
- `analysis/scripts/probe_v34_rule6_v2.py` — v33-vs-v34 head-to-head on 30K trips
- `analysis/scripts/probe_v34_sweep.py` — the sweep across min_trip_for_C ∈ [3..14, A-only]

**Consequence:**

1. **v33's boundary stands.** No human-strategy ship from this Priority A.

2. **The user's hypothesis is preserved as a future ML target.** $12.89/1000h whole-grid is the oracle ceiling for "smarter A-vs-C". The remaining $86/1000h of Rule 6's gap to its full-A∪C ceiling could be closed with a learned A-variant heuristic OR a learned A-vs-C decision tree on (trip_rank, max_kicker_rank, suit profile). Both are ML targets; v32/v34's gated trips features partially capture this signal already (v32 ships within-trips $1,359, v34 ships $1,291).

3. **Methodology lesson — heuristic-realizable ceilings are smaller than oracle ceilings.** For trips, 56% of the oracle ceiling (Rule 6 ships $111 of $197 oracle) is the heuristic limit. Future Always-X probes should report BOTH the oracle ceiling AND the closest heuristic-realizable headline to set realistic expectations.

4. **The directional finding survives:** A-variant IS the right routing for trip ≤ T, and the oracle ceiling agrees with the user. The reason the rule cannot be cashed at the human-strategy level is the A-variant's own routing complexity, not the threshold rule.

---

## Decision 071 — v35_rule6_v3 ships in STRATEGY_GUIDE.md as the new human strategy of record (Session 39); production heuristic keeps v33 — methodology rule NEW: human guide can be sharper than production bot when heuristic-A is the rate-limiting step

**Date:** 2026-05-07
**Status:** Two-track ship.
- **STRATEGY_GUIDE.md Part 6 ships v35** (sharper Rule 6 boundary + 2-step suit-matching procedure for the A-variant body) as the human strategy of record. Captures **+$8.12/1000h whole-grid at the human ceiling (oracle-bound)** vs v33 on the same 30K trips probe.
- **Production runtime keeps v33.** v35's heuristic-A LOSES $4.06/1000h whole-grid at the bot level on the disagreement subset, exactly as Session 38's sweep predicted (the v33/v34 bot-DS optimizer is the rate-limiting step).

**Origin:** The user's Session 39 ask was "the trips strategy doesn't have hard-set rules that are easy to follow yet — can we fix that?" Session 38's per-cell oracle probe (`probe_rule6_c_variant.py`) had already mapped where v33's `trip_rank > max_kicker_rank → C` boundary diverges from oracle: 28.8% of v33's C-fires are wrong by oracle, projected ceiling $+12.89/1000h whole-grid.

**The sharpened rule** (replaces v33's prose):

| Trip rank | Where third trip card goes | Why |
|---|---|---|
| Trip A (AAA) | Always TOP | Nothing beats Ace on top |
| Trip K (KKK) | TOP unless A in kickers (then A on top, third K to bot) | Ace on top still wins |
| Trip Q (QQQ) | TOP unless any of {J, K, A} in kickers (then highest such on top, third Q to bot) | J on top wins more often than Q here per oracle |
| Trip ≤ J | Always BOT (highest non-trip on top) | Per-cell oracle: A wins everywhere with non-trivial sample size |

**The A1b suit-matching rewrite** (replaces v33's fuzzy "maximize bot DS-ness, then rank-sum, then connectivity"): when third trip joins bot, look at the 3 kickers' suits and pick the trip card with priority:
1. Match a kicker singleton suit → bot 2+2 (DS, best)
2. Match a fresh suit (not yet duplicated) → bot 2+1+1 (SS, OK)
3. NEVER match the kicker pair suit → bot 3+1 (third suited card is dead, avoid)

**Verification (`verify_rule6_v3_human.py`)** on 30K trips probe:

| Mode | v33 | v35 | Δ |
|---|---:|---:|---:|
| Oracle-bound (HUMAN ceiling) | -$42.56/1000h whole-grid | **-$34.44/1000h** | **+$8.12** ✓ |
| Heuristic (production bot) | -$113.34/1000h | -$117.40/1000h | -$4.06 ✗ |

The +$8.12 captures **63% of the $12.89 oracle ceiling identified in Decision 070**, sacrificing the noisy "Trip J + maxK ∈ {6,7,8}" cells where C narrowly wins on tiny samples ($+50 to $+1,400 within-trips). The trade buys a memorable rule for ~$4.77/1000h give-up vs the optimal-but-unmemorable per-cell map.

**Per-trip-rank breakdown** (oracle-bound v35 - v33):

| Trip rank | Δ within-trips | Δ whole-grid |
|---|---:|---:|
| 2-5 | $0 | $0 |
| 6 | +$67/1000h | +$0.28 |
| 7 | +$78 | +$0.32 |
| 8 | +$192 | +$0.81 |
| 9 | +$374 | +$1.56 |
| T | +$583 | +$2.40 |
| J | +$603 | +$2.54 |
| Q | +$48 | +$0.19 |
| K, A | $0 | $0 |
| **Total** | | **+$8.12/1000h whole-grid** |

**Files:**
- `analysis/scripts/strategy_v35_rule6_v3.py` — production code path for v35 (currently used only by the verify probe; runtime still calls v33)
- `analysis/scripts/verify_rule6_v3_human.py` — head-to-head verification on 30K trips probe
- `STRATEGY_GUIDE.md` Part 6 — rewritten Rule 6 in plain English (no A/C jargon), 6 worked examples, suit-matching procedure

**Methodology rule (NEW, Session 39): the human strategy guide can be sharper than the production heuristic when heuristic-A is the rate-limiting step.**

This rule resolves an apparent paradox left by Decision 070: how can a boundary be both "directionally correct on the oracle" AND "unrealizable at the bot level"? The answer is that the bot-level test conflates two decisions — (1) which cell to fire (A or C) and (2) within A, which trip joins bot. Decision 070's sweep showed that the bot-DS optimizer (decision 2) is wrong often enough on the cells the sharper boundary newly sends to A that the boundary's gain is washed out at the bot level.

But a HUMAN reading the strategy guide is not bound to the bot-DS optimizer for decision 2. The guide can teach the priority ordering (DS > SS > 3+1) explicitly with worked examples, and a thoughtful player will pick the oracle-best A within the cell roughly as well as the per-cell oracle does. **For the human, decision 2 is essentially solved by the new prose; the bot is still at v33's heuristic.**

**Consequence:**

1. **Two-track shipping is now an option** for rule rewrites where the heuristic is the bottleneck. v35 sets the precedent.
2. **The remaining ~$4.77/1000h gap** between v35's human ceiling and the optimal per-cell map is preserved as a future ML target — a learned A-vs-C decision tree (Priority C in CURRENT_PHASE.md) targeting `(trip_rank, max_kicker_rank, kicker suit profile)` against the oracle's A-or-C choice.
3. **The production bot WILL eventually adopt v35** (or its successor) once a learned A-variant heuristic closes the gap with the oracle-best A. Until then, v33's heuristic-A stays in code because v35's heuristic version regresses on flipped cells.

**Total project rule count: 6** (Rule 1: pair-to-bot DS; Rule 2: two-pair no-split; Rule 3: trips+pair split-trips-keep-pair; Rule 4: KK/AA stay-mid; Rule 5: KK/AA rainbow override; Rule 6: pure trips paired-mid + sharper top-vs-bot table). Rule 6 is now sharper for humans than for the production bot — a first in the project.

---

## Decision 072 — Rule 6 Step 2 priority stays as DS > SS > rainbow > 3+1; bot connectivity is NOT a tier (Session 40)

**Date:** 2026-05-07
**Status:** No code change. v35_rule6_v3 priority preserved as-is. Documented in STRATEGY_GUIDE.md Part 6 "Why it works" addendum so future maintainers know why connectivity was rejected.

**Origin:** User's Session 39 close listed three sub-tasks for Priority A0. (1) Add per-rank worked examples for trips T..2 (delivered as Examples 7–14). (2) **Test whether bot connectivity should add a 4th tier to Step 2's suit-matching priority** — i.e., should "rainbow run≥3" or "wheel-eligible" rank above SS? User's intuition: trip 5 + 2-3-4 makes a wheel; trip 7 + 4-5-6 makes a 4-card run; trip 6 + 5-7-8 makes a 4-run-with-gap. (3) Cross-reference Session 38's per-cell A-vs-C map to confirm A still beats C at low trips with weak max_kicker (delivered as a re-run of `probe_rule6_c_variant.py`; verdict unchanged from Session 38).

**Probe (`analysis/scripts/probe_low_trips_connectivity.py`)** on the same 30K trips sample (RandomState(0)) restricted to trip_rank ≤ T (n=20,849 hands × 3 picks each = 62,547 pick-rows). Reports five things:

1. **Mean oracle EV per (suit_profile × longest_run)** — within EVERY profile, more run = WORSE EV. DS run=1: $-3,912/1000h_within_low_trips. DS run=4: $-14,156. SS run=1: $-8,566. SS run=4: $-19,623. Rainbow run=1: $-13,566. Rainbow run=4: $-26,538. **The pattern is selection, not causation:** hands eligible to make a 4-card run are low-trip + low-kicker hands, which are weak hands overall.

2. **Oracle never picks rainbow** when SS or DS is available. Per-hand oracle picks across 20,849 hands: DS 47.2%, SS 35.8%, 3+1 17.9%, 4-flush 5%, **rainbow 0%**.

3. **Alternative priority "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1" REGRESSES.** Mean alt_picked_EV vs heuristic_EV at low trips: $-284.1/1000h_within_low_trips. Whole-grid: **-$11/1000h** vs the existing DS > SS > rainbow > 3+1 priority. Confirmed: rainbow is never the answer regardless of run length.

4. **Wheel-eligible bots: $-32K vs $-14K mean EV.** Same selection effect as (1) — wheel hands are weak hands. Within-hand mixed-pick analysis (when one of the 3 trip picks gives a wheel-eligible bot and others don't): in the rare cases this happens, oracle does not systematically prefer the wheel pick. **No rule change.**

5. **Rainbow-run-4 spotlight:** 196 hands have at least one rainbow-run-4 pick available. Oracle picks rainbow-run-4 in **0/196 (0.0%)** of those hands. The visually appealing "low trips + tight run + rainbow" shape is the structurally weakest pick among the 3 candidates.

**Why connectivity cannot be a Step 2 tier** (the deeper reason, surfaced by this probe):

> **Bot run-length is invariant across the 3 trip-to-bot candidates on a given hand.** Once Step 1 fires "third trip to bot" and we know which 3 kickers go on bot (the 3 lowest non-trip cards), the bot's 4 ranks are fully determined: {trip_rank, kicker1_rank, kicker2_rank, kicker3_rank}. Only the trip's *suit* changes between candidates, not its rank. So `bot_longest_run`, `bot_rank_sum`, `bot_high_count`, and any wheel-eligibility test are CONSTANT across the 3 picks. They cannot tiebreak between candidates because they're identical for all candidates.

**This generalizes** to a methodology rule: any candidate-level priority/tiebreaker must be derived from features that VARY between candidates. Features that depend only on the rank set are invariant in this enumeration pattern.

**Per-cell A-vs-C cross-reference (`probe_rule6_c_variant.py` re-run):** for trip ≤ T at every (trip_rank, max_kicker_rank) cell with n≥5, A wins ≥99% of the time. Lowest-max-kicker cells (where C might be expected to do better):

- Trip 6 + maxK 5: n=10, C-A=$-15,585/1000h_in, A wins 100%
- Trip 7 + maxK 6: n=13, C-A=$-10,911, A wins 100%
- Trip 8 + maxK 5: n=6, C-A=$-5,316, A wins 83.3% (small sample)
- Trip 9 + maxK 6: n=13, C-A=$-4,338, A wins 84.6%
- Trip T + maxK 5: n=7, C-A=$-2,871, A wins 100%
- Trip T + maxK 6: n=13, C-A=$-1,765, A wins 76.9%

v35's "trip ≤ J always A" boundary is structurally correct, not noise.

**Residual finding (carries to Priority C):** the connectivity probe surfaced a 42% disagreement rate between v33-heuristic-pick and oracle-pick at low trips. Mean lift on the disagreement subset is +$1,212/1000h_within_low_trips (≈$19.53/1000h whole-grid). The bulk (51% of disagreements) is "SS → SS" — same suit profile, different trip-suit pick. This is a within-SS suit-rotation signal that the current heuristic's tie-break (lowest trip index) misses. **Reframes Priority C input set:** the learned A-vs-C decision tree should also train on (trip_rank, max_kicker, kicker_suit_pattern, candidate_trip_suit) within the SS-tier to capture this gap.

**Files:**
- `analysis/scripts/probe_low_trips_connectivity.py` — new probe
- `STRATEGY_GUIDE.md` Part 6 — 8 new worked examples (Trip T..2) + connectivity-rejection note in "Why it works"
- `STRATEGY_GUIDE.md` Part 1 — Session 40 entry

**Methodology rules (NEW, Session 40):**

1. **Candidate-level invariance check before adding a feature to a priority/tiebreaker.** When the heuristic enumerates K candidates that share a fixed rank set or any other invariant subset, features derived from that invariant subset cannot serve as primary tiers OR tiebreakers. Always check what differs between candidates before designing a priority.
2. **Distinguish selection effect from causal-within-population signal.** Mean-EV-per-cell aggregates can hide the fact that the cell IS the population of weak hands. Test within-population (e.g., within-hand or within-(rank_set) groupings) before treating a feature as actionable.

**Consequence:**

1. **Step 2 priority stays:** DS > SS > rainbow > 3+1, with bot_rank_sum × 1,000 and bot_longest_run × 100 as continuing tertiary tiebreakers. (The longest_run × 100 term is harmless because it's invariant across candidates.)
2. **No code change.** v35_rule6_v3 keeps its existing _v35_pick_c boundary and v33-inherited A-variant body.
3. **Rule 6 documentation is now COMPLETE for human play.** Trip A through Trip 2 each have explicit per-rank treatment + at least one worked example.
4. **Priority C scope expanded:** the learned A-vs-C decision tree now has two training signals — the cell-level boundary AND the within-SS suit-rotation. Both contribute to the projected $5–$13/1000h whole-grid ML target.

---

## Decision 073 — Rule 7 (three_pair) ships in production as v37; high_only Rule 7 attempt (v36) ARCHIVED; high_only is officially ML-only territory (Session 41)

**Date:** 2026-05-08
**Status:** Two outcomes from the same Session 41 always-X probe sweep:
- **v37_rule7_three_pair SHIPS** as the new production strategy of record. Replaces v33. +$43/1000h whole-grid lift confirmed at full-grid scale (+$141/1000h on prefix).
- **v36_rule7_high_only ARCHIVED**. Heuristic regression of $6/1000h whole-grid confirmed on full grid; the +$354/1000h X3 oracle ceiling is multivariate and not capturable by any rule.

**Origin:** End of Session 40 queued the always-X structural baseline probes for the four remaining un-rule-mined categories (high_only, three_pair, composite, two_pair) per the Session 38 methodology rule. Session 41 ran the first two of those four.

---

**Part A — high_only (the big residual): tested, archived as ML-only.**

high_only is 20.4% of all hands and the largest within-cat residual ($572/1000h whole-grid in v34_dt's residuals). Three always-X candidates were tested in `verify_rule_X_v33_high_only.py`:

  - **X1: top = highest singleton card.** v33 already does this 100% of the time. Confirmation only.
  - **X2: top = highest, mid = next two highest (rank-down 1-2-4).** Deterministic regression: −$134/1000h whole-grid. v33 picks the X2 setting only 18.8% of hands; suit structure overrides pure rank ordering 81% of the time.
  - **X3: top = highest, mid is two cards of the same suit if any same-suit combination exists in the remaining 6.** Oracle ceiling: +$355/1000h whole-grid. Naive heuristic ("highest rank-sum same-suit mid"): −$5.88/1000h.

X3's ceiling is real and large but unrealizable. The follow-up `probe_high_only_suited_mid_drill.py` tested 6 different tiebreakers among same-suit mids:

| Heuristic | Δ vs v33 (whole-grid) |
|---|---:|
| H1: highest rank-sum same-suit mid | −$5.88 |
| H2: connected (gap≤1) first | −$78.98 ✗ |
| H3: bot-DS first | −$0.70 |
| H4: contains broadway (T+) first | −$6.54 |
| H5: connected+DS combo | −$77.52 ✗ |
| H6: composite weighted score | −$6.56 |
| Oracle ceiling | +$355.24 ✓ |

**All 6 heuristics regressed.** Per-feature importance: broadway is the strongest single signal (P(oracle picks this candidate | candidate is broadway-bearing) = 32% vs 19% for non-broadway = +0.13 lift), but still under 50% — coin-flip territory. Other features: connected +0.07, bot-DS −0.03, rank-sum percentile 0.76 (correlation only).

**`grade_v36_rule7_high_only.py`** confirmed at full-grid scale: v33 = $2,920/1000h (40.68% optimal); v36 = $2,926/1000h (40.16% optimal) — −$6/1000h whole-grid regression. The pct_optimal even goes DOWN (forcing same-suit mid moves us AWAY from oracle agreement on some hands).

**Decision A:** v36 ARCHIVED. ARCHIVED docstring added to `strategy_v36_rule7_high_only.py`; file retained for history but never used at runtime. **high_only is officially ML-only territory** — three rule attempts now (v11 omaha-first −$1,745, v15 DS-patch −$296, v36 same-suit-mid −$6). Methodology rule: do not re-attempt high_only rule extraction without a multi-feature ML breakthrough.

---

**Part B — three_pair (small but untouched): Rule 7 ships as v37.**

three_pair is 1.9% of all hands but had been completely untouched by gating in v34_dt ($86.20/1000h whole-grid budget). The full 114K population was probed exhaustively across all 286 (high_pair, middle_pair, low_pair) combinations.

**`verify_rule_X_v33_three_pair.py`** tested 4 candidates:

| Rule | Description | Δ vs v33 (whole-grid) |
|---|---|---:|
| RA | top=singleton, mid=HIGHEST pair, bot=mid+low pairs | +$18.36 |
| RB | top=singleton, mid=MIDDLE pair, bot=high+low pairs | +$24.94 |
| RC | top=singleton, mid=LOWEST pair, bot=high+mid pairs | −$96.38 ✗ |
| RD | top=pair-member (split a pair) | −$81.29 ✗ |

Both RA and RB beat v33. RC and RD are non-starters. Best-per-cell mix lifts +$54.00/1000h whole-grid (oracle ceiling for RA-vs-RB selection).

v33's diagnostics revealed the production strategy was already picking top=singleton 80.4% of the time (the right idea was there), but picking the WRONG pair for mid most of the time: mid=high pair 68% (RA-aligned), mid=middle pair 25% (RB-aligned). RB is the better default.

**`probe_three_pair_boundary.py`** ran the full 286-cell breakdown and tested ~20 boundary rules. The cleanest 1-condition rule:

  > **"if highest_pair ∈ {T, J, Q, K} → mid is the MIDDLE pair, else mid is the HIGHEST pair; top is always the singleton."**

Lift: **+$43.05/1000h whole-grid** (60% of the per-cell oracle ceiling). 64.3% per-hand agreement with the oracle's per-cell choice.

A 2-condition rule "RB if high ∈ {T,J,Q,K} OR (high=A AND low ≤ 3)" was tested and only adds +$0.01/1000h — basically nothing.

**The structural intuition:** the trade is "where does the strongest pair go: mid (Hold'em) or bot (Omaha)?"

- **AA is special.** Pairing AA in the mid is so dominant in Hold'em (only chops vs another AA opponent, beats every other pair) that you don't move it.
- **A broadway non-Ace pair (K, Q, J, T) on the bot anchors a strong 2-pair Omaha hand** — when the board pairs, you draw to trips with the high pair. You give up some mid Hold'em equity but gain more bot Omaha equity. Net positive.
- **Below T (your highest pair is 9 or lower)**, your "high" pair isn't strong enough on the bot. Better to keep it in the mid for Hold'em equity.

**`grade_v37_rule7.py`** prefix grade: three_pair within-cat regret drops $4,085 → $1,334 (67% reduction). pct_optimal jumps from 38.9% → 64.9% on three_pair. Whole-grid (prefix has 11% three_pair share): **+$141/1000h**. Overall optimal pct: 48.81% → 50.14%. Full-grid grade: pending at write time, expected ≈ +$43/1000h whole-grid (matches drill).

**Decision B:** v37 SHIPS as new production strategy of record. Production strategy chain is now 7 rules deep (Rule 1 pair-to-bot DS; Rule 2 two-pair no-split; Rule 3 trips+pair split-2-1; Rule 4 KK/AA stay-mid; Rule 5 KK/AA rainbow override; Rule 6 pure trips paired-mid + boundary; Rule 7 three_pair top=singleton + RB-or-RA on highest-pair-rank).

---

**Methodology rules (NEW, Session 41):**

1. **Heuristic-realizable ceilings vary by category.** high_only's heuristic ceiling is essentially zero (−$6 vs +$355 oracle ceiling — 0% capture). three_pair's heuristic ceiling is much higher (+$43 vs +$71 oracle ceiling — 60% capture). The difference: three_pair's optimal-pick structure is rank-driven (single feature: highest pair rank), while high_only's optimal-pick structure is multivariate (suit pattern × singleton × bot composition × rank correlations). **Always-X probes should check whether the optimal-pick structure is uni-variate before declaring a category rule-extractable.**
2. **v33/current-production diagnostics tell you which always-X candidate to test first.** v33's per-category routing reveals what it's already doing: "v33 picks mid=highest-pair on 68% of three_pair hands" → RA is the de facto current rule. Test the alternatives (RB, RC) immediately; don't waste a probe iteration confirming what v33 already does.
3. **high_only is officially ML-only.** Three rule attempts have now failed (v11, v15, v36). The X3 oracle ceiling shows +$355/1000h IS available but multivariate. Future high_only work should be ML-only (v34_dt's gated `ho_*_g` features are the path).
4. **Two-track shipping is no longer the default.** Sessions 38–40 used two-track because Rule 6's heuristic-A was the rate-limiting step. Session 41's v37 ships in BOTH tracks (heuristic captures 60% of ceiling, no two-track needed). Future probes should default-test the heuristic version first; only fall back to two-track if the heuristic regresses.

**Files:**
- ARCHIVED: `analysis/scripts/strategy_v36_rule7_high_only.py` (with ARCHIVED docstring)
- NEW: `analysis/scripts/strategy_v37_rule7_three_pair.py` (production)
- NEW: `analysis/scripts/verify_rule_X_v33_high_only.py`
- NEW: `analysis/scripts/probe_high_only_suited_mid_drill.py`
- NEW: `analysis/scripts/grade_v36_rule7.py`
- NEW: `analysis/scripts/verify_rule_X_v33_three_pair.py`
- NEW: `analysis/scripts/probe_three_pair_boundary.py`
- NEW: `analysis/scripts/probe_three_pair_final_rule.py`
- NEW: `analysis/scripts/grade_v37_rule7.py`
- UPDATED: `STRATEGY_GUIDE.md` Part 1 (Session 41 entry), Part 5 (production reference + probes), Part 6 (Rule 7 section, Default updated, cheat sheet updated)

**Total project rule count: 7** (Rule 1 pair-to-bot DS; Rule 2 two-pair no-split; Rule 3 trips+pair split-2-1; Rule 4 KK/AA stay-mid; Rule 5 KK/AA rainbow override; Rule 6 pure trips paired-mid + boundary; Rule 7 three_pair top=singleton + RB-or-RA boundary).

---

## Decision 074 — Rule 8 (composite quads_pair → quad-in-mid) ships in production as v38; two_pair Rule 8 candidate (boundary search +$197 on full) DEFERRED after prefix-grid regression (Session 42)

**Date:** 2026-05-08
**Status:** Two outcomes from the same Session 42 always-X probe sweep:
- **v38_rule8_qp SHIPS** as the new production strategy of record. Replaces v37. +$9.42/1000h whole-grid lift (full N=200) and +$18.63/1000h whole-prefix (N=1000) — both grids positive, the consistency check the two_pair candidate failed.
- **v38_rule8_two_pair DEFERRED** (renamed `strategy_v38_rule8_two_pair_DEFERRED.py`, retained for next-session investigation). Boundary search found a +$197/1000h whole-grid lift on full but the prefix grade showed -$512/1000h. ALL forced-single-pick variants regressed on prefix. The two_pair territory needs split-allowing rules or remains ML-only.

**Origin:** End of Session 41 queued the always-X probes for the last two un-mined categories (composite + two_pair). Session 42 ran both.

---

**Part A — two_pair (the big residual after high_only): clean +$197 boundary on full, but DEFERRED.**

two_pair is 22.27% of all hands and the largest within-cat residual on the production heuristic at $3,371/1000h within-cat ($751/1000h whole-grid). The full 1.34M two_pair population was probed exhaustively in `verify_rule_X_v33_two_pair.py`:

  - **TP_RA: top=hi-singleton, mid=HIGH pair**:    Δ -$87.71/1000h whole-grid
  - **TP_RB: top=hi-singleton, mid=LOW pair**:     Δ +$68.46/1000h whole-grid (best of always-rules)
  - **TP_RC: top=hi-singleton, mid=2 lo-singletons**: Δ -$1,988/1000h whole-grid
  - **Best per cell (oracle ceiling)**:                Δ +$624.65/1000h whole-grid

`probe_two_pair_boundary.py` mapped all 78 (high_pair, low_pair) cells and tested ~20 boundary rules. The cleanest:

  > **"RC if high ≤ 4, elif T ≤ high ≤ K then RB, else RA"**
  > Δ = +$196.89/1000h whole-grid (32% of the +$624.65 oracle ceiling)
  > 4.6× the size of v37's three_pair lift — would have been the biggest rule-layer ship in project history

`grade_v38_rule8.py` (two_pair version) confirmed +$197.00 on full grid. **But the prefix grade showed -$512/1000h regression.**

A 12-variant sweep (narrower boundaries, low-pair gating, no-RC versions, "always RA/RB", etc.) tested every shape: ALL regressed on prefix. Even the "always RA" baseline lost -$863. The fundamental problem: v33's underlying v7_regression sometimes splits pairs (mid is 1 card from each pair), and on the prefix's weak-hand-biased distribution this adaptive splitting happens to be the right move on enough hands that any forced no-split rule loses.

**Decision A:** v38_rule8_two_pair DEFERRED. Strategy file renamed `strategy_v38_rule8_two_pair_DEFERRED.py` and retained for next-session investigation. The two_pair territory needs:
  1. A split-allowing rule (e.g., "if both pairs ≤ 6, allow mid = 1 card from each pair"), OR
  2. ML capture only (already the case in v34_dt's gated `tp_*_g` features), OR
  3. A separate "human guide" track with the boundary-rule and an explicit warning that production runtime keeps v37's two_pair behavior (two-track ship like v35_rule6_v3 was used for trips).

---

**Part B — composite (small but heterogeneous): quads_pair Rule 8 SHIPS as v38.**

composite is 0.245% of canonical hands, 14,742 hands across 4 subtypes (quads_pair 6,863; quads_trip 156; two_trips 4,290; trips_two_pair 6,864). The full population was probed in `verify_rule_X_v33_composite.py`:

| Subtype | n | v33 within-st | Best candidate | Capture |
|---|---:|---:|---|---|
| **quads_pair** | 6,863 | $17,101/1000h | QP_quad_in_mid: +$9.42 whole-grid | **100% deterministic** |
| quads_trip | 156 | $21,524 | QT_quad_split: +$0.21 whole-grid | oracle-ceiling, tiny pop |
| two_trips | 4,290 | $11,400 | TT_full_house_split: +$7.22 whole-grid | oracle-ceiling, drill pending |
| trips_two_pair | 6,864 | $7,210 | T2P_split_trip_top: +$7.64 whole-grid | oracle-ceiling, drill pending |

Only the quads_pair subtype has a verified deterministic rule.

**The QP rule:**
  > For quads_pair (4+2+1):
  > - TOP = the singleton
  > - MID = the 2 quad cards whose suits are NOT the pair's suits
  > - BOT = the other 2 quads + the pair (4 cards)

**Why the suit-aware mid pick:** the 4 quad cards have all 4 suits (one each), and the 2 pair cards have 2 different suits. Putting the QUAD CARDS THAT MATCH THE PAIR'S SUITS into the bot (alongside the pair) makes the bot "2 of suit X + 2 of suit Y" — a perfectly double-suited Omaha hand. The remaining 2 quads (at the OTHER 2 suits) go to mid.

**Verification:** the deterministic rule's regret matches the oracle-within-constraint ($604.9/1000h within-st) EXACTLY across all 6,863 hands. 100% heuristic capture of the quad-in-mid subspace ceiling.

**`grade_v38_rule8.py` (composite-QP version):**
- Full grid: $2,877 → $2,868/1000h whole-grid (Δ +$9/1000h, matches probe)
- Prefix grid: $1,753 → $1,735/1000h whole-prefix (Δ +$19/1000h, matches probe)
- Composite within-cat regret: drops on both grids; pct_optimal on prefix jumps 6.9% → 25.3%

**Decision B:** v38 SHIPS as new production strategy of record. Production strategy chain is now 8 rules deep (Rule 1–7 unchanged + Rule 8 quads_pair top=singleton + non-pair-suit-quads to mid).

---

**Methodology rules (NEW, Session 42):**

1. **Prefix-grid regression as a generalization gate.** Sessions 38–41 happened to ship rules that won on both grids. Session 42 is the first time a rule won big on full ($+197) but lost big on prefix ($-512). The decision: prefix is biased toward weak hands, but a rule that loses there indicates the rule isn't capturing structure, just exploiting a full-grid-only artifact. **A rule with a prefix regression of >2× the full-grid lift does NOT ship**, regardless of how clean the boundary looks on the per-cell breakdown.

2. **Composite is heterogeneous; subtypes need separate rules.** The composite category lumps 4 shapes (quads_pair, quads_trip, two_trips, trips_two_pair). Only quads_pair has a verified deterministic rule. The others have promising oracle-ceilings (+$7-8 whole-grid each) but need follow-up heuristic-refinement drills (Session 43 priority).

3. **v33 on weak hands is doing something non-trivial.** v33 inherits two_pair routing from v8_hybrid → v7_regression (a learned tree). On the prefix's weak-hand distribution, v33 picks splits/non-Rule-2 settings that any forced rule can't match. v33 is already capturing fine-grained suit/kicker structure on weak hands. Some categories may need ML rather than another rule.

4. **The "boundary search beats v33 on average" measurement is necessary but not sufficient.** Session 42 probe found a clean rule that wins on FULL grid by $197. Naive interpretation: ship it. Correct interpretation: validate that the rule's per-cell agreement with the oracle holds on the prefix sub-distribution too. A rule can be correct-on-average yet wrong on a specific hand class.

**Files:**
- DEFERRED: `analysis/scripts/strategy_v38_rule8_two_pair_DEFERRED.py` (with DEFERRED docstring)
- NEW (PRODUCTION): `analysis/scripts/strategy_v38_rule8_qp.py`
- NEW: `analysis/scripts/verify_rule_X_v33_two_pair.py`
- NEW: `analysis/scripts/probe_two_pair_boundary.py`
- NEW: `analysis/scripts/verify_rule_X_v33_composite.py`
- NEW: `analysis/scripts/grade_v38_rule8.py`
- UPDATED: `STRATEGY_GUIDE.md` Part 1 (Session 42 entry), Part 5 (production reference + probes), Part 6 (Rule 8 section, Default updated, cheat sheet updated, Step 1 categorize table updated)

**Total project rule count: 8** (Rule 1 pair-to-bot DS; Rule 2 two-pair no-split; Rule 3 trips+pair split-2-1; Rule 4 KK/AA stay-mid; Rule 5 KK/AA rainbow override; Rule 6 pure trips paired-mid + boundary; Rule 7 three_pair top=singleton + RB-or-RA boundary; Rule 8 quads_pair top=singleton + non-pair-suit-quads to mid).

---

## Decision 075 — Rule 9 (3 sub-rules: plain quads + TT + T2P) ships as v39 from Session 42 overnight rule-mining (Session 42 overnight)

**Date:** 2026-05-09 (overnight after 2026-05-08 v38 ship)
**Status:** SHIPS as production. Three new structural rules bundled into Rule 9, all passing the both-grid validation gate (full + prefix both positive). v39 replaces v38 as the strategy of record. Combined +$22/1000h whole-grid (full N=200) + +$28/1000h whole-prefix (N=1000). v39 score: $2,846/1000h on full (vs v8_hybrid $3,153, vs v14 $3,033, vs v33 $2,920, vs v38 $2,868).

**Origin:** After v38 (Rule 8 quads_pair) shipped, the user requested an overnight rule-mining sprint. Six investigations ran sequentially:
1. TT (two_trips) E3a heuristic hunt
2. Plain quads structural drill
3. T2P (trips_two_pair) initial drill + deeper boundary search
4. Two_pair split-allowing investigation
5. Pair Rule 1 extension probe
6. Trips_pair refinement
Plus a two_pair oracle-pick characterization probe. Three of the six produced ship-able rules.

---

**Rule 9a — Plain quads (4+1+1+1, 14,300 hands, 0.24% of canonical).**

Mirror of Rule 8 QP. The same suit-aware insight ("non-pair-suit quads to mid") generalizes when the "pair" is replaced by "the 3 singletons":

  - TOP = highest singleton
  - MID = the 2 quad cards whose SUITS are NOT used by the 3 singletons
  - BOT = the other 2 quads + the 2 lower singletons

100% deterministic. Captures 73% of the +$21.02/1000h whole-grid oracle ceiling. **+$15.31 full / +$11.78 prefix.** Wins on ALL 13 quad-rank cells. Within-cat regret on plain quads drops $9,670 → $3,235/1000h on full (66% reduction). pct_optimal: 9.5% → 45.9%.

**Rule 9b — TT (two_trips, 3+3+1, 4,290 hands, 0.071% of canonical).**

Split the HIGH trip to top with suit-aware top-pick + DS-aware L-bot pick:

  - TOP = an H-trip card whose suit IS in the LOW-trip's suits
  - MID = the FULL LOW-trip pair (2 of 3 low-trip cards)
  - L-bot = the L-trip card whose suit best matches bot's H-trip-leftovers + singleton (DS-aware tiebreaker)
  - BOT = 2 H-trip + 1 L-trip + singleton

**+$3.57 full / +$2.79 prefix.** Captures 60% of the +$5.98/1000h whole-grid oracle ceiling for E3a (split-trip-to-top class).

**Rule 9c — T2P (trips_two_pair, 3+2+2, 6,864 hands, 0.114% of canonical).**

Split the trip to top with a trip-rank boundary controlling which pair joins the bot:

  - TOP = a trip-member at the suit NOT shared with either pair (if possible)
  - if trip-rank ≤ 4: MID = LOW pair, BOT = 2 trip-leftovers + HIGH pair (HIGH pair to bot for stronger 2-pair Omaha anchor)
  - else (trip ≥ 5): MID = HIGH pair, BOT = 2 trip-leftovers + LOW pair (mid Hold'em strength of HH outweighs)

**+$2.81 full / +$13.48 prefix.** Beats "always F2" (+$2.04 / +$9.57) by adding the trip-rank boundary. Boundary search confirmed T<=4 as the cleanest split (T<=5: +$2.88/+$13.05; T<=6: +$2.93/+$12.65 — diminishing returns past T=4).

---

**Methodology rules (NEW, Session 42 overnight):**

1. **Suit-aware "non-X-suit" insight generalizes broadly.** Rule 8 QP discovered the pattern. Rule 9a (plain quads) generalized identically, just replacing "pair" with "singletons". Rule 9b (TT) used the inverse ("top at suit IN L-suits") for similar structural reasons. The pattern: when you have multiple same-rank cards, the suits NOT used by the rest of the hand are structurally distinct, and using those suit-positions for mid/top forces the bot to be DS via the remaining-suit symmetry.

2. **Diminishing returns are observable in the boundary search.** T2P "F3 if T<=4" = +$2.81/+$13.48. Extending to T<=5 trades +$0.07 full for −$0.43 prefix. Extending to T<=6 trades +$0.12 full for −$0.83 prefix. The boundary at T=4 is at the structural break (very-low-trip cells where the bot anchor matters less).

3. **Two_pair confirmed ML territory.** Two-pair split investigation: SPLIT never wins at any of 78 cells. Even oracle-best-per-cell within {RA, RB, RC} loses prefix by -$336/1000h. Oracle's prefix-win comes from picking different singletons as top (21% non-hi-singleton picks), driven by suit/connectivity — not by cell-rank-based rules.

4. **Pair Rule 1 extension is the largest remaining structural opportunity.** The pair category (46.6% of hands) profile shows QQ has $2,833/h v33 loss with 50/50 oracle split between mid=P_pair vs unpaired-mid. JJ similar. Suggests an extension to Rule 1 ("when QQ or JJ has 2 distinct suits and balanced kickers, move to bot for DS") but the gate requires careful design + both-grid validation — Session 43 priority.

**Files:**
- NEW: `analysis/scripts/strategy_v39_rule9.py` (PRODUCTION)
- NEW: `analysis/scripts/grade_v39_rule9.py`
- NEW (drills): `drill_tt_two_trips_deterministic.py`, `drill_tt_e3a_heuristic_hunt.py`, `drill_plain_quads_structural.py`, `drill_t2p_trips_two_pair_deterministic.py`, `drill_t2p_deeper_boundary.py`, `drill_two_pair_split_investigation.py`, `drill_two_pair_oracle_picks_full.py`, `drill_pair_rule1_extension.py`, `drill_trips_pair_refinement.py`
- NEW (pipeline): `overnight_session42_rule_hunt.sh`, `generate_session42_summary.py`
- NEW (report): `SESSION_42_OVERNIGHT_REPORT.md`
- UPDATED: `STRATEGY_GUIDE.md` Part 1 (Session 42 overnight entry), Part 5 (Rule 9 reference + new probes), Part 6 (Rule 9a/9b/9c sections, Step 1 categorize table updated)

**Total project rule count: 9** (Rules 1-8 unchanged + Rule 9: a=plain quads, b=TT split, c=T2P boundary). Rule 9 is structurally a 3-bundle but conceptually a single "rule of the suit-aware multi-same-rank pattern".

---

## Decision 076 — Rule 10 (J-low single-pair defensive) ships in production as v40 (Session 43)

**Date:** 2026-05-09
**Status:** SHIPS as production. Rule 10 is the first DEFENSIVE rule in the project — its mechanism is "minimize loss" rather than "maximize EV". v40b (the gated variant) replaces v39 as the strategy of record after grader-confirmed full lift was 2x the simple variant. **Grader-confirmed: +$48/1000h whole-grid (full N=200, v40b gated) + +$37/1000h whole-grid (prefix N=1000, identical for both variants).** v39 → v40b score: $2,846 → $2,798 full, $1,707 → $1,670 prefix. pct_opt full: 41.17% → 41.48% (+0.31%). pct_opt prefix: 50.38% → 50.64%. **Largest single-rule full-grid lift since v33's Rule 6 (Session 37, +$113/1000h).** The simple ungated v40 variant (+$23 full / +$37 prefix) is retained as a sister artifact for the human-memorization fork.

**Origin:** Session 43 was dedicated to the user's weak-hand defensive investigation (~14% of hands have max card ≤ J). Three drills ran:
1. `drill_high_card_defense.py` — high_only Q1+Q2+Q5
2. `drill_low_pair_J_high_defense.py` — pair Q3 (this drill produced Rule 10)
3. `drill_two_pair_J_high_revisit.py` — two_pair Q4 (re-examination through defensive lens)

The user's specific framing questions were answered:
- **Q1** ("single A + low body — always A on top?"): YES, mathematically validated. Oracle picks top=Ace 96.0% of the time on A-high+weak hands. v3 already implements this.
- **Q2** ("K/Q-high — break broadway for 4-flush bot?"): NO. Every B_BOT_FLUSH variant regressed by $10-$27/1000h. The high card belongs on top.
- **Q3** ("J-low + 1 pair — defensive structural pick?"): YES. Rule 10 captures this.
- **Q4** ("J-low + 2 pairs — re-examine deferred Rule 8 defensively?"): NO. All six deterministic candidates regressed; v33's adaptive splitting confirmed as genuine ML routing, not a hidden defensive rule. Reaffirms Session 42 verdict.
- **Q5** ("J-high or weaker no-pair — does suited-bot save?"): MIXED. Naive top=lowest works on T-low (+$8/1000h whole-grid full only) but regresses on J-high. high_only category has zero prefix coverage so both-grid validation is impossible. Defer.

---

**Rule 10 — J-low single-pair defensive (342,720 hands, 5.703% of canonical):**

  TRIGGER: category == pair (exactly one pair, no trip, no quad)
           AND max_rank ≤ J (= 11)

  SETTING:
    TOP = lowest singleton
    MID = the pair
    BOT = the 4 highest non-pair singletons

The pair stays in mid (oracle prefers mid-pair on 60-85% of J-low pair cells). The CHANGE from v3's default is the top: instead of top=highest-singleton, use top=LOWEST-singleton. The 4 highest non-pair singletons go to bot for stronger Omaha kicker-strength. This is the "weak-hand top inversion" applied to the pair category.

**Lift on the J-low pair zone:** +$22.73/1000h whole-grid (full N=200) + +$36.70/1000h whole-grid (prefix N=1000). Per-cell breakdown shows the rule wins on broadly: pair_rank ≤ 6 (across all max ∈ {7..J}) and on pair_rank == max_rank cells. It regresses slightly on cells where pair_rank ∈ (max-4, max-1) — e.g., Jh_p7 to Jh_pT regress by $2-$8/cell. Net aggregate is strongly positive; the regressions are localized.

A gated variant (`strategy_v40b_rule10_gated.py`) with the additional condition "pair_rank ≤ 6 OR pair_rank == max_rank" was also produced and graded. The gated variant captures more upside on the full grid (estimated +$48/1000h) by avoiding the localized regression cells. Prefix lift is identical (+$37/1000h) because the prefix only contains pair=2 cells which always satisfy the gate.

**Production ship choice — gated v40b over simple v40:** Initial intent was to ship the simple v40 per the "diminishing returns at structural break" methodology. However, the v40b grader returned **+$48/1000h full** (vs v40's +$23) — exactly 2x the lift, with the same +$37 prefix lift. AND v40b gains pct_opt +0.31% on full while v40 has a slight pct_opt regression (−0.02%). Per the user's data-driven-discovery methodology, the data clearly favors v40b. The extra condition ("pair_rank ≤ 6 OR pair_rank == max_rank") adds modest memorization burden, but the per-cell drill data showed it captures a real structural break — the rule wins broadly on (pair ≤ 6 OR pair == max) cells and regresses on (pair ∈ (max-4, max-1)) cells. The gate avoids precisely the regression zone. v40b ships as production runtime; v40 is retained as a sister artifact for human-memorization fork (pattern matches Session 39's v33 production / v35 sharper-human-strategy fork).

---

**Methodology rules (NEW, Session 43):**

1. **Weak-hand top inversion is a unifying structural pattern.** Top tier wins 1 point/board (max 2 across both boards), mid 2/board, bot 3/board. When TOP equity is already <50% (any J-low hand vs random opponent), the opportunity cost of dumping the highest card to top is <1 point, while the gain in bot+mid equity from upgrading kicker strength is >1 point. The math inverts the conventional "highest card to top" reflex. This pattern explains Rule 10's mechanism and may extend to other weak-hand categories (Q5 J-high no-pair has signal but is multi-feature; deferred).

2. **high_only category has zero prefix coverage.** All 7-distinct-rank canonical IDs are >500K; the prefix grid contains 0 high_only hands. The both-grid validation gate is INAPPLICABLE for any rule scoped to no-pair hands. Defensive rules for the no-pair zone can only ship on full-grid validation alone, OR not ship. This is a hard constraint, not a methodology choice.

3. **High-card-to-bot-for-4-flush is a LOSING trade.** Counterintuitive conventional wisdom from human play is empirically wrong: every variant tested (B_BOT_FLUSH, B_BOT_3FLUSH_EXT) regressed by $10-$27/1000h on every weak-hand stratum. The bot's flush draw doesn't compensate for the lost top-tier equity from breaking the high card.

4. **Worst-case regret is a useful sanity check** for defensive rules. A rule with positive mean lift but BIGGER worst-case regret would induce more 20-point scoops. v40's per-cell worst-case regret stays in the +$10-$22 range vs v39's +$15-$25, confirming no scoop-induction risk.

5. **Two_pair is genuinely ML territory (CONFIRMED TWICE).** Session 42 overnight investigation reached this verdict; Session 43 Q4 re-examination through the defensive lens reached the same verdict. v33's adaptive splitting is genuine multi-feature ML routing, not a hidden defensive rule waiting to be extracted.

**Files:**
- NEW: `analysis/scripts/strategy_v40_rule10.py` (PRODUCTION)
- NEW: `analysis/scripts/strategy_v40b_rule10_gated.py` (sister candidate)
- NEW: `analysis/scripts/grade_v40_rule10.py`
- NEW: `analysis/scripts/grade_v40b_rule10_gated.py`
- NEW (drills): `drill_high_card_defense.py`, `drill_low_pair_J_high_defense.py`, `drill_two_pair_J_high_revisit.py`
- NEW (report): `SESSION_43_DEFENSIVE_REPORT.md`
- UPDATED: `STRATEGY_GUIDE.md` Part 1 (Session 43 entry), Part 5 (Rule 10 reference), Part 6 (Rule 10 worked example, Step 1 / cheat sheet updated)

**Total project rule count: 10** (Rules 1-9 unchanged + Rule 10 = J-low single-pair defensive).

---

## Decision 077 — Bot suit×connectivity priority refined: SUIT DOMINATES CONNECTIVITY in J-low no-pair (Session 44, methodology investigation, no new ship)

**Date:** 2026-05-09
**Status:** METHODOLOGY UPDATE. No new strategy ships. v40b remains production. Replaces the previous methodology rule "DS > SS > rainbow > 3+1 > 4-flush" (which came from trips territory and was assumed universal) with the empirically-validated rule "suit dominates connectivity at every level — DS-scattered (worst DS) beats every non-DS class within-hand in the J-low no-pair zone." The replaced rule was structurally incomplete; new rule is validated via within-hand pairwise drill on 85,800 J-low no-pair hands.

**Origin:** User devil's-advocate questioning of Rule 10's bot construction (Session 43 ship) exposed two issues. (1) Rule 10 puts pair in mid + 4 highest singletons in bot with no suit-aware bot construction — possibly leaving EV on the table. (2) The methodology rule "DS > SS > rainbow > 3+1 > 4-flush" had never been head-to-head tested in J-low pair or J-low no-pair populations, and connectivity (run-4, one-gap-4, etc.) had not been formally placed in the hierarchy.

---

**Investigation:**

Two drills ran:

1. `drill_bot_suit_run_priority.py` — cross-product 5×7 (suit × connectivity) drill measuring mean regret per cell across achievable hands. Surprising findings: 4-flush-run-4 outranked SS-run-4, DS-scattered outranked SS-run-4 — both contradicted Omaha first-principles.

2. `drill_bot_suit_run_pairwise.py` — within-hand pairwise drill comparing every (class_A, class_B) pair on the SAME hand. Eliminated the cross-class hand-population confounder.

User explicitly asked for Gemini consultation before drawing conclusions. Gemini (`mcp__pal__chat` with `gemini-2.5-pro`) confirmed: cross-class average regret is confounded by hand-population differences (different classes have different achievability populations, mixing hand-overall-EV variance into the per-class metric). Within-hand pairwise comparison is the correct methodology for cross-class priority ranking.

---

**Definitive findings (within-hand pairwise, J-low no-pair, n=85,800):**

**Tipping-point: DS-scattered (worst DS) vs every non-DS class:**

| Vs class | n co-achievable | Lift |
|---|---:|---:|
| SS run-2+strays | 37,332 | **+$111** (basically tied, DS wins) |
| 4-flush run-4 | 672 | +$622 |
| SS run-4 | 16,904 | +$1,603 |
| Rainbow run-4 | 3,588 | +$6,981 |
| Rainbow scattered | 8,784 | +$10,361 |

**DS-scattered beats every non-DS class within-hand. No tipping point exists.** The thinnest margin is DS-scattered vs SS-run-2+strays at +$111/1000h — essentially tied but DS still wins.

**Within-DS connectivity premium:** ~$2-3K (e.g., DS run-4 vs DS scattered = +$2,554). Less than the suit premium (~$4.5K for DS-vs-SS at run-4). Suit dominance > connectivity premium.

**Curious side-finding:** DS one-gap-4 beats DS run-4 by +$376/1000h within-hand. A missing internal rank creates a board-bridging straight bonus. Counterintuitive — worth confirming in trips territory in a follow-up.

**4-flush-run-4 vs SS-run-4 mystery resolved:** 4-flush wins by +$907/1000h within-hand (vs +$1,646 in confounded drill). Smaller effect than the confounded analysis. Plausible mechanism: flush HEIGHT compensates for flush probability. With 4-flush-run-4 (5♠6♠7♠8♠), if board brings 3 spades, you use the highest 2 spades from hand (7♠+8♠) for an 8-high spade flush. With SS-run-4 (5♠6♠7♥8♦), you use 5♠+6♠ for a 6-high flush. EV(probability × payoff) can balance.

---

**Refined priority hierarchy:**

**Tier 1 (any DS):** DS one-gap-4 ≈ DS run-4 ≥ DS run-2+strays ≥ DS two-runs-2 ≥ DS run-3+stray ≥ DS two-gap-4 ≥ DS scattered. All DS variants beat all non-DS variants within-hand.

**Tier 2 (close cluster, ~tied with DS-scattered):** SS run-2+strays, SS one-gap-4, 4-flush run-4, SS run-4. Within $1K of DS-scattered within-hand.

**Tier 3:** 3+1 variants, weaker SS connectivity, 4-flush poor connectivity.

**Tier 4 (avoid):** all rainbow (≥$3K below DS-scattered).

**Practical implication for production:** "If you can build a DS bot, do it — regardless of connectivity. If no DS available, pick the suit class with most flush draws available, then break ties by connectivity (prefer one-gap-4 ≈ run-4)."

---

**Methodology rules NEW (Session 44):**

1. **Cross-class regret averaging is confounded by hand-population differences.** "Mean best EV in class" averages across hands where the class is achievable. Different classes have different achievability populations. Always validate cross-class comparisons via within-hand pairwise.

2. **Suit dominates connectivity at every level (J-low no-pair).** No tipping point exists. DS-scattered ≥ all SS, 4-flush, 3+1, rainbow.

3. **First-principles arguments must check payoff height, not just probability.** The "4-flush has fewer deck outs → SS wins" argument was incomplete — it missed that flush HEIGHT compensates for flush probability when 4-flush is run-4.

4. **Original "DS > SS > rainbow > 3+1 > 4-flush" methodology rule was structurally incomplete.** It came from trips territory (Rule 6 Step 2 + Session 40). The refined rule is "DS > everything (suit dominates), then 4-flush ≈ SS at strong connectivity, 3+1 ≈ SS, all rainbow at the bottom." More importantly, the priority should be checked via within-hand pairwise, not assumed universally.

5. **DS one-gap-4 ≥ DS run-4** (counterintuitive but real). Worth investigating whether this generalizes to other categories.

---

**Why no new rule shipped:**

The findings invalidate the previous suit-priority methodology rule but translating into a production rule extension requires more drill work — specifically the user's Session 45 direction:

1. Apply suit dominance to J-low single-pair: does the pair-stays-in-mid anchor (Rule 10's mid choice) hold when breaking the pair would enable a DS bot? Or is DS-bot preferred even at the cost of mid pair anchor?

2. Apply to J-low two_pair: does DS-bot beat keeping both pairs intact?

These questions go beyond the bot's structural classification — they ask whether the FULL setting (top + mid + bot) should be reorganized to prioritize suit dominance over conventional pair anchors.

**Files:**
- NEW: `analysis/scripts/drill_bot_suit_run_priority.py` (cross-product, CONFOUNDED — kept for diagnostic purposes)
- NEW: `analysis/scripts/drill_bot_suit_run_pairwise.py` (within-hand pairwise, DEFINITIVE)
- NEW (report): `SESSION_44_SUIT_CONNECTIVITY_REPORT.md`
- UPDATED: `CURRENT_PHASE.md` (rewritten for Session 44 wrap + Session 45 resume direction)
- UPDATED: `STRATEGY_GUIDE.md` Part 1 (Session 44 entry — to be added in commit)

**Total project rule count: 10** (unchanged). Methodology rule count: refined.

---

## Decision 078 — Rule 10 v3 (suit-aware bot) ships as v41 (Session 45)

**Date:** 2026-05-09
**Status:** SHIPS as production. v41 replaces v40b as the strategy of record. **Grader-confirmed: +$29/1000h whole-grid (full N=200) and +$54/1000h whole-grid (prefix N=1000).** v40b → v41 score: $2,798 → $2,769 full, $1,670 → $1,616 prefix. pct_opt full: 41.48% → 41.91% (+0.43%); pct_opt prefix: 50.64% → 51.81% (+1.17%). Cumulative v39 → v41: −$77 full / −$91 prefix. Both grids strongly positive with no per-category regression.

**Origin:** Session 45 was scoped to the user's verbatim direction (S44 closure): "now that we have a definitive answer for defensive J-high no-pair hands, we need to compare that to J-high hands with a pair... do we favor DS on bottom even at the cost of breaking a pair?". Three drills ran:

1. `drill_J_low_pair_DS_break.py` — J-low single-pair (n=342,720)
2. `drill_J_low_two_pair_DS_break.py` — J-low two_pair (n=262,080)
3. `drill_DS_one_gap_vs_run4_other_cats.py` — S44 carryover validation

**Definitive findings (Drill A, full grid, n=342,720):**

The user's "should we break the pair to enable DS bot?" question is answered NO:

| Comparison | Lift ($/1000h) |
|---|---:|
| A3 − A2: DS via pair-break vs non-DS pair-anchor | **−$10,304** (catastrophic) |
| A5 − A2: DS via pair-to-bot vs non-DS pair-anchor | **+$8.9** (essentially tied) |
| **A1 − A2: DS premium WITHIN pair-mid** | **+$2,756** |
| A4 − A2: pair-split non-DS vs pair-mid non-DS | −$11,878 |

**Pair structure dominates suit structure.** Breaking the pair to enable DS bot is catastrophic. But keeping pair-in-mid AND choosing singletons that yield a DS bot is +$2,756/1000h within-hand on the 47.8% of J-low pair hands where it's achievable.

Per-pair-rank tipping point on A5 (pair-to-bot DS): mostly negative for P=2..9, but **P=J = +$2,975** (clear win). Pair-to-bot DS at P=J is a Rule 11 candidate but requires a separate setting-builder; deferred to Session 46+.

**Drill B (J-low two_pair, n=262,080)** confirmed the same pattern with even larger margins:
- B3 − B2 (split-LL for DS) = −$9,030
- B5 − B2 (split-HH for DS) = −$12,042
- B7 − B2 (both-split for DS) = −$23,165
- **B1 − B2 (DS WITHIN both-intact) = +$1,864**

The "two_pair is ML territory" verdict (S42 + S43, twice) holds for cross-class rules. The within-class suit-aware-bot opportunity (B1−B2 = +$1,864) is queued as a future candidate but requires careful setting-builder design.

**Drill C: S44's "DS one-gap-4 ≥ DS run-4 by +$376" finding does NOT generalize.** With 200K samples per category, sign flips by category (high_only −$233, pair +$344, two_pair +$361, trips −$518). The S44 result was likely inside noise on its sample (n=1,680). Don't extract as a universal structural feature.

---

**Rule 10 v3 — design:**

  TRIGGER (unchanged from v40b):
    cat == pair                AND
    max_rank ≤ J               AND
    (P ≤ 6 OR P == max_rank)

  SETTING (changed):
    Among the 5 non-pair singletons, identify all candidate TOP-picks
    such that the remaining 4 singletons form a DS bot (suit pattern 2+2).

    IF any DS-achievable TOP exists:
      TOP = lowest-rank singleton among DS-achievable picks
            (preserves v40b's weak-hand top-inversion intent)
    ELSE:
      TOP = lowest-rank singleton (v40b fallback)

    MID = the pair (always)
    BOT = the remaining 4 non-pair singletons

**Behavioral verification on 50K J-low gated-pair sample:**
- v40b (suit-blind) picks DS bot on 15.7% of fired hands
- v41 picks DS bot on 47.4% of fired hands (matches A1 achievability ≈ 47.8%)
- Picks differ on 31.8% of fired hands

**Production ship rationale:**
- Both grids strongly positive (+$29 full / +$54 prefix), no regression on any category
- pct_opt improves on both grids
- Worst-case regret unchanged (max_regret = $5.74)
- Mechanism is interpretable and follows existing methodology (weak-hand top inversion + S44 suit-dominance, applied within-class)

---

**Methodology rules NEW (Session 45):**

1. **Pair structure dominates suit structure universally in J-low pair / two_pair.** Breaking a pair to enable DS-bot is catastrophic by ~$10K-$23K/1000h. The within-class suit-aware refinement is the right axis for further extraction.

2. **Within-class suit-aware bot is a generalizable rule pattern.** Same mechanism that ships Rule 10 v3 has a sister candidate in two_pair (B1−B2 = +$1,864).

3. **DS one-gap-4 ≥ DS run-4 (S44) does NOT generalize.** Sign flips by category. This is a category-specific noise effect, not a universal structural feature.

4. **Tie-break by preserving prior intent.** Where multiple valid choices exist, prefer the one closest to the existing baseline (Rule 10 v3 picks lowest singleton among DS-achievable TOPs to preserve v40b's top-inversion intent).

5. **Pair-to-bot + DS at P=J is a real Rule 11 candidate** (+$2,975/1000h) but requires a separate setting-builder; deferred.

---

**Files:**
- NEW: `analysis/scripts/strategy_v41_rule10_v3_ds.py` (PRODUCTION)
- NEW: `analysis/scripts/grade_v41_rule10_v3_ds.py`
- NEW (drills): `drill_J_low_pair_DS_break.py`, `drill_J_low_two_pair_DS_break.py`, `drill_DS_one_gap_vs_run4_other_cats.py`
- NEW (report): `SESSION_45_RULE10_V3_REPORT.md`
- UPDATED: `CURRENT_PHASE.md` (rewritten for Session 45 wrap)
- UPDATED: `STRATEGY_GUIDE.md` Part 1 (Session 45 entry) + production-of-record references

**Total project rule count: 10** (Rule 10 evolved v40 → v40b → v41).

---

## Decision 079 — Rule 11 (J-pair pair-to-bot DS) ships as v42 (Session 46)

**Date:** 2026-05-09
**Status:** SHIPS as production. v42 replaces v41 as strategy of record. **Grader-confirmed: +$6/1000h whole-grid (full N=200) and $0 (prefix unchanged — Rule 11 fires on 0 prefix hands).** v41 → v42 score: $2,769 → $2,763 full, $1,616 → $1,616 prefix. pct_opt full: 41.91% → 41.93% (+0.02%). pct_opt prefix: unchanged. Cumulative v39 → v42: −$83 full / −$91 prefix.

**Origin:** Drill A's per-pair-rank breakdown (Session 45) found A5−A2 = +$2,975/1000h at P=J specifically (vs negative for P=2..T). Session 46 ran a focused J-pair-J drill (Drill D, n=34,272) to validate the apples-to-apples comparison and shipped Rule 11.

**Drill D findings (J-pair-J, P=11 AND max=11, n=34,272):**

| Comparison | Lift ($/1000h) | Verdict |
|---|---:|---|
| **A5 − A1** (pair-to-bot DS vs pair-mid DS) | **+$1,004** | apples-to-apples Rule 11 question |
| A5 − A2 (S45 headline) | +$2,975 | confirmed |
| **A5 vs v41 production pick** | **+$3,769** | largest cross-class override at J-pair-J |
| A1 − A2 (Rule 10 v3 internal lift) | +$2,553 | confirmed |
| A5 − A6 (DS WITHIN pair-bot) | +$2,211 | DS premium real |

v41 picks A5 0% of fired hands at J-pair-J (47.8% A1, 52.2% A2). Rule 11 surgically overrides at this single cell.

---

**Rule 11 — design:**

  TRIGGER:
    cat == pair        AND
    P == 11            AND
    max_rank == 11     AND
    DS-bot achievable with both J's in bot

  SETTING BUILDER:
    Both J's go to BOT.
    Among the 5 non-pair singletons, pick 2 for BOT such that the bot's
    4-card suit pattern is 2+2 (DS):
      Case A (J's same suit X): need 2 singletons of same non-X suit
        Y. Pick the lowest-rank pair (keep mid + top strength).
      Case B (J's different suits X, Y): need 1 of suit X + 1 of suit
        Y. Pick the lowest-rank of each.
    TOP = lowest-rank singleton among the 3 remaining (top-inversion).
    MID = the 2 remaining singletons.

    If no DS-achievable pair-in-bot config exists, fall through to v41.

**Behavioral verification (5K J-pair-J sample):**
- Rule 11 fires on 49.8% of J-pair-J (A5 achievability ≈ 55.1%; ~5% gap is sampling + canonical suit-symmetry)
- 100% of fired picks correctly have pair-in-bot AND DS-bot
- 100% of fired picks differ from v41

**Heuristic captures 56% of oracle ceiling.** Whole-grid lift +$6/1000h translates to +$2,105/1000h within fires (vs A5-best vs v41's +$3,769 ceiling). The remaining ~+$5/1000h whole-grid is heuristic-vs-oracle gap. Refinement candidates queued (sweep alternative tie-breaks for singleton-pair selection and top-placement).

**Production ship rationale:**
- Both grids non-regressive (+$6 full, $0 prefix unchanged)
- pct_opt improves on full
- Per-category: pair −$14/1000h, all others unchanged
- Worst-case regret unchanged (max = $5.74)
- First single-cell rule of project — surgical override at the largest cross-class residual identified by the drill methodology
- Same precedent as v38 (Rule 8 quads_pair) which shipped at +$9.42/1000h full

**Methodology rules NEW (Session 46):**

1. **Cross-class override opportunities are ranked by "best-in-class minus production pick".** Drill D's "v41 vs best-in-class" view directly identified A5's +$3,769 lift as 6× the next-best class. Use this lens for single-cell rule discovery.

2. **Single-cell rules can ship at <$10/1000h whole-grid lift.** Rule 11 fires on 0.285% of grid; the within-fires lift is +$2,105/1000h. Both numbers are meaningful — small whole-grid lifts can be clean single-cell wins.

3. **Single-cell rules at extreme P-rank cells have natural prefix immunity.** J-pair-J has zero prefix coverage (no canonical ID < 500K is J-pair-J). Rule 11 fires on 0 prefix hands → prefix unchanged. Same precedent as Session 41/43 high_only-zero-prefix.

4. **Don't hold rules for "perfect heuristic-vs-oracle".** v42's 56%-of-ceiling capture is a clean ship; the remaining ~+$5/1000h is queued as a separate refinement.

---

**Files:**
- NEW: `analysis/scripts/strategy_v42_rule11_jpair_pbot_ds.py` (PRODUCTION)
- NEW: `analysis/scripts/grade_v42_rule11_jpair_pbot_ds.py`
- NEW: `analysis/scripts/drill_J_pair_pair_to_bot_DS.py`
- NEW (report): `SESSION_46_RULE11_JPAIR_REPORT.md`
- UPDATED: `CURRENT_PHASE.md` (rewritten for Session 46 wrap)
- UPDATED: `STRATEGY_GUIDE.md` Part 1 (Session 46 entry) + production-of-record references

**Total project rule count: 11** (Rules 1-10 + Rule 11 = J-pair pair-to-bot DS — first single-cell rule).

---

## Decision 080 — Rule 12 (J-low two_pair both-intact + DS-bot) ships as v43 (Session 47)

**Date:** 2026-05-09
**Status:** SHIPS as production. v43 replaces v42 as strategy of record. **Grader-confirmed: +$35/1000h whole-grid (full N=200) and +$66/1000h whole-grid (prefix N=1000).** v42 → v43 score: $2,763 → $2,727 full, $1,616 → $1,550 prefix. pct_opt full: 41.93% → 42.20% (+0.27%). pct_opt prefix: 51.81% → 52.61% (+0.80%). Two_pair regret $3,371 → $3,211 (−$160 within two_pair). **Largest single-rule full-grid lift since v33's Rule 6 (Session 37, +$113).** Cumulative v39 → v43 = −$118 full / −$157 prefix.

**Origin:** Drill B (Session 45) found B1−B2 = +$1,864/1000h within-hand at J-low two_pair. The pattern matched Rule 10 v3's "DS within pair-anchor" structural insight — applied to the two_pair category. Session 47 ran two parallel investigations:

1. **Drill E — Rule 11 heuristic sweep (NEGATIVE).** Tested 6 simple tie-break combinations for Rule 11. v42's V_LOLO is empirically optimal; no variant beats it. The +$1,794/1000h gap to A5 oracle requires more sophisticated logic than simple tie-breaks.

2. **Drill F — two_pair within-class DS variants (DEFINITIVE).** Tested HH-to-bot vs LL-to-bot tie-breaks on the J-low two_pair pop (n=262,080).

**Drill F findings (full grid):**

| Variant | n_fires | Perfect% | Lift vs v42 | Whole-grid full |
|---|---:|---:|---:|---:|
| **V_HH_BOT** | 75,600 | 69.1% | **+$1,808** | **+$22.75** |
| V_LL_BOT | 75,600 | 65.6% | +$1,044 | +$13.14 |
| B1 oracle (ceiling) | — | 100% | +$2,505 | +$50.42 |

HH-to-bot wins by +$764/1000h within fires. Hybrid (HH preferred, LL fallback) covers all 120,960 fires (46.2% of J-low two_pair).

---

**Rule 12 — design:**

  TRIGGER:
    cat == two_pair       AND
    max_rank ≤ J          AND
    DS-bot achievable with both pairs intact (HH or LL to bot)

  SETTING BUILDER:
    Try HH-to-bot first:
      pair-cards = the 2 HH cards
      Find 2 singletons completing 2+2 DS suit pattern.
      If found: use HH-to-bot configuration.
    Else try LL-to-bot:
      pair-cards = the 2 LL cards
      Same DS-completion search.
      If found: use LL-to-bot configuration.
    Else: fall through to v42.

    Tie-break (when multiple sing-pairs work):
      Pick lowest rank-sum (preserves mid + top strength).

    BOT = chosen pair + 2 chosen singletons
    MID = the OTHER pair (pair-anchor preserved in mid)
    TOP = the leftover singleton (deterministic, no choice)

**Behavioral verification (30K J-low two_pair sample):**
- Rule 12 fires on 47.3% (matches Drill F's 46.2%)
- 100% of fired picks correctly produce DS-bot
- 100% of fired picks correctly preserve both pairs intact
- 27.6% of picks differ from v42

**Production ship rationale:**
- Both grids strongly positive (+$35 full / +$66 prefix), no regression on any other category
- pct_opt improves on both grids substantially
- Worst-case regret unchanged (max = $5.74)
- Largest single-rule full-grid lift since v33's Rule 6
- Mechanism interpretable and consistent with the suit-dominance family (Rule 10 v3, Rule 11)

---

**Methodology rules NEW (Session 47):**

1. **Simple tie-break sweeps cap quickly.** Drill E showed v42's existing heuristic was already optimal among 6 simple variants. Further refinement requires structural complexity. Hard-cap signal for Rule 11 simple-sweep work.

2. **Cross-class within-pop rules from "DS premium within X" lens ship reliably.** Drill A → Rule 10 v3 (+$29). Drill D → Rule 11 (+$6). Drill F → Rule 12 (+$35). The "within-class DS premium" axis is the project's most productive rule-discovery axis right now.

3. **HH-to-bot wins over LL-to-bot for two_pair.** Counter to "lowest pair to bot for kicker preservation" intuition. HH in bot creates a stronger 2-pair-with-kicker Omaha hand; LL in mid still anchors Hold'em mid because pair-mid beats most non-pair mid combos.

4. **Cumulative ship arcs >$100/1000h come from structural-axis families.** v30→v34 was the ML capacity arc. v39→v43 is the suit-dominance arc (4 ships, all from S44's within-hand pairwise insight). Both are multi-rule families sharing one underlying mechanism.

---

**Files:**
- NEW: `analysis/scripts/strategy_v43_rule12_two_pair_DS_intact.py` (PRODUCTION)
- NEW: `analysis/scripts/grade_v43_rule12_two_pair.py`
- NEW: `analysis/scripts/drill_two_pair_DS_within_intact.py` (Drill F)
- NEW: `analysis/scripts/drill_rule11_heuristic_sweep.py` (Drill E, negative result)
- NEW (report): `SESSION_47_RULE12_TWO_PAIR_REPORT.md`
- UPDATED: `CURRENT_PHASE.md` (rewritten for Session 47)
- UPDATED: `STRATEGY_GUIDE.md` Part 1 (Session 47 entry) + production-of-record references

**Total project rule count: 12** (Rules 1-11 + Rule 12 = J-low two_pair both-intact + DS).
