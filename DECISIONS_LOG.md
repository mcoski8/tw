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
