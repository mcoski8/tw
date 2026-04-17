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

## Decision 011 — Dual Compute Backend (CPU + CUDA)
**Date:** April 2026 (pre-build)
**Question:** Should we build CPU-only or also support GPU acceleration?
**Options:** CPU only (simpler) | GPU only (fastest but limits hardware) | Both via feature flags (flexible)
**Choice:** Both — CPU is default, CUDA is opt-in via cargo feature flag
**Why:** CPU-only (Rust + rayon) works everywhere and requires no special dependencies. CUDA requires an NVIDIA GPU and CUDA toolkit but offers 10-50x speedup for the Monte Carlo inner loop. Using Cargo feature flags (--features cuda), we compile the same codebase with or without GPU support. The CPU path is developed first and serves as the reference implementation. The CUDA path is added in a sub-sprint after CPU is validated. This lets the user choose: run locally on Mac Mini for free (CPU, 8-12 days), rent a cheap CPU cloud server ($15-25, 1-2 days), or rent a GPU ($3-10, 4-8 hours).
