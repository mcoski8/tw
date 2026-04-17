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

---

## Decision 011 — Dual Compute Backend (CPU + CUDA)
**Date:** April 2026 (pre-build)
**Question:** Should we build CPU-only or also support GPU acceleration?
**Options:** CPU only (simpler) | GPU only (fastest but limits hardware) | Both via feature flags (flexible)
**Choice:** Both — CPU is default, CUDA is opt-in via cargo feature flag
**Why:** CPU-only (Rust + rayon) works everywhere and requires no special dependencies. CUDA requires an NVIDIA GPU and CUDA toolkit but offers 10-50x speedup for the Monte Carlo inner loop. Using Cargo feature flags (--features cuda), we compile the same codebase with or without GPU support. The CPU path is developed first and serves as the reference implementation. The CUDA path is added in a sub-sprint after CPU is validated. This lets the user choose: run locally on Mac Mini for free (CPU, 8-12 days), rent a cheap CPU cloud server ($15-25, 1-2 days), or rent a GPU ($3-10, 4-8 hours).
