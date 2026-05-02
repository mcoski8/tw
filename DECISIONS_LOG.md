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

