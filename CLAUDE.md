# CLAUDE.md - Taiwanese Poker Solver Context File

> **Purpose:** Master context file for AI assistants (Claude Code, etc.) working on this codebase.
> Read this file FIRST before making any changes.

---

## Project Summary

**TW Poker Solver** is a computational engine that aims to find the Nash equilibrium (or near-optimal approximation) for Taiwanese Poker — a card-setting game derived from Open-Face Chinese Poker played with 7 cards, 3 tiers, and 2 community boards.

**Primary Goal:** Solve (or near-solve) Taiwanese Poker by computing the optimal hand-setting strategy for every possible 7-card deal, then extract the patterns into a human-usable decision tree that matches the solver 95%+ of the time.

**Secondary Goal:** Build a training tool where a user is dealt 7 cards, sets their hand, and receives immediate feedback on whether their setting matches the computed optimal.

**Critical Output:** The solver itself is a means, not the end. The END PRODUCT is:
1. A complete database of optimal settings for all 133M hands
2. Pattern analysis revealing WHY each setting is optimal (what features drive the decision)
3. A condensed decision tree / hierarchy of rules that a human can memorize and apply in <30 seconds
4. Validation proving the decision tree matches the solver for 95-99% of hands
5. The definitive GTO Taiwanese Poker strategy guide — backed by exhaustive computation, not heuristics

**What This Is:**
- A poker math engine that evaluates all 133M+ possible 7-card hands
- A Nash equilibrium approximation via Counterfactual Regret Minimization (CFR) or exhaustive best-response computation
- A training/quiz interface for improving Taiwanese Poker play

**What This Is NOT:**
- Not a real-time game server or multiplayer platform
- Not a bot that plays against humans online
- Not a general poker solver — it's specific to Taiwanese Poker rules

---

## Game Rules (Critical — Read Carefully)

### Setup
- Standard 52-card deck
- 2-5 players (solver focuses on 2-player equilibrium, extends to multiplayer)
- Each player is dealt 7 cards
- Two separate 5-card community boards are dealt after all players set their hands

### Hand Setting
Each player arranges their 7 cards into 3 tiers:
- **Top:** 1 card (played as Hold'em — best 5 of 6 using the 1 card + 5 board cards)
- **Middle:** 2 cards (played as Hold'em — best 5 of 7 using the 2 cards + 5 board cards)
- **Bottom:** 4 cards (played as Omaha — MUST use exactly 2 from hand + 3 from board)

**CRITICAL OMAHA RULE:** The bottom hand MUST use exactly 2 cards from the player's 4-card holding and exactly 3 from the 5-card board. This is NOT optional. A player cannot use 1 or 3 or 4 from their hand.

**NO FOULING RULE:** Unlike traditional Chinese Poker, there is NO fouling in this variant. Players can set their hands in any configuration — the top does NOT need to be weaker than the middle, etc.

### Scoring (Per Opponent Matchup)
Each tier is evaluated independently on EACH of the two boards:

| Tier | Points Per Board | Total Possible |
|------|-----------------|----------------|
| Top | 1 point | 2 points (1 × 2 boards) |
| Middle | 2 points | 4 points (2 × 2 boards) |
| Bottom | 3 points | 6 points (3 × 2 boards) |
| **Non-scoop max** | | **12 points** |

**Scoop:** If a player wins ALL 6 individual matchups (3 tiers × 2 boards) with ZERO chops, the total is 20 points (not 12). Any single chop or loss on any matchup invalidates the scoop.

**Chops:** When both players' hands evaluate to the same rank on a given tier+board, neither player earns points for that matchup. Chops are common, especially on the top tier when both players have similar high cards.

### Suitedness in Omaha (Critical)
- **Double suited (2+2):** Two cards of one suit + two of another. BEST configuration. Two separate flush draws.
- **Single suited (2+1+1):** One flush draw. Decent.
- **Three of a suit:** BAD. You can only use 2 from hand, so the third suited card wastes an out.
- **Four of a suit:** WORST. Same problem amplified. Removes 4 of 13 suited cards from deck for no benefit.
- **Rainbow (1+1+1+1):** No flush draws. Weakest for flush equity but no wasted cards.

### Hand Evaluation Notes
- Standard poker hand rankings apply (royal flush > straight flush > quads > full house > flush > straight > trips > two pair > pair > high card)
- For Top tier: best 5 of 6 cards (1 hole + 5 board)
- For Middle tier: best 5 of 7 cards (2 hole + 5 board), standard Hold'em rules
- For Bottom tier: Omaha rules — MUST use exactly 2 from 4-card holding + exactly 3 from board. C(4,2) × C(5,3) = 60 combinations to check per hand.
- The Wheel (A-2-3-4-5) is the lowest straight

---

## Computational Scope

### Problem Size
- Unique 7-card hands from 52 cards: C(52,7) = **133,784,560**
- Possible settings per hand: C(7,1) × C(6,2) = 7 × 15 = **105**
- Total hand-setting combinations: ~**14.05 billion**
- For 2 players: opponent has C(45,7) = 45,379,620 possible hands
- Board runouts from remaining cards: C(38,10) for two 5-card boards (but order within boards doesn't matter, boards are distinguishable)
- Full 2-player game tree: astronomically large (~10^30 states)

### Solving Approach — Tiered Strategy

**Tier 1 — Best Response Tables (Feasible, High Value)**
For each of the 133M possible 7-card hands, compute the expected value of all 105 possible settings against a uniform random opponent distribution using Monte Carlo simulation. This gives us the "best response to a random opponent" — which is what our strategy guide approximates heuristically.

Compute requirements:
- 133M hands × 105 settings × N board samples = total evaluations
- At N=100 samples per setting: ~1.4 trillion evaluations
- At N=1000 samples per setting: ~14 trillion evaluations
- Each evaluation involves: dealing opponent cards, dealing 2 boards, evaluating 3 tiers on each board
- Estimated time: weeks on a single machine, hours on a GPU cluster

**Tier 2 — Hand Bucketing + CFR (Challenging, Higher Value)**
Group similar hands into ~1,000-10,000 buckets based on hand features (pair rank, suitedness, connectivity, high card). Run Counterfactual Regret Minimization between buckets to converge on Nash equilibrium. This is how commercial poker solvers work.

Compute requirements:
- Depends heavily on bucket granularity
- 1,000 buckets × 105 settings × 1,000 iterations = manageable
- 10,000 buckets × 105 settings × 10,000 iterations = heavy but feasible

**Tier 3 — Full Nash Equilibrium (Extremely Difficult)**
True Nash over all 133M hands without bucketing. Likely intractable without massive distributed compute. Not our initial goal.

### Recommended Path
Start with Tier 1 (best response tables). This alone would be the most comprehensive Taiwanese Poker strategy ever computed. Then layer on Tier 2 (CFR with bucketing) to refine toward true equilibrium.

---

## Key Architectural Decisions

### 1. Language: Rust (Core Engine) + Python (Analysis/UI)
The evaluation engine MUST be fast. Each hand evaluation involves:
- Omaha evaluation: C(4,2) × C(5,3) = 60 five-card combinations
- Hold'em evaluation: C(7,5) = 21 combinations for middle, C(6,5) = 6 for top
- These run billions of times

Rust for the core engine (hand evaluation, Monte Carlo, CFR loops). Python for analysis, visualization, and the trainer UI.

**Alternative:** C++ or even optimized Python with NumPy/Cython. But Rust offers safety + speed. Decision can be revisited based on developer preference.

### 2. Hand Evaluation via Lookup Tables
Pre-compute a lookup table for all C(52,5) = 2,598,960 possible 5-card hands. Map each to a hand rank integer. This turns hand evaluation from a computation into a table lookup — orders of magnitude faster.

Multiple established libraries exist:
- `phf` hand evaluator (perfect hash)
- Two-plus-two evaluator (7-card lookup)
- Cactus Kev's evaluator

### 3. Hand Canonicalization
Many 7-card hands are equivalent up to suit permutation. A♠K♠Q♥J♥9♦8♣4♦ is strategically identical to A♥K♥Q♠J♠9♣8♦4♣. Canonicalizing suits reduces the 133M hands significantly (estimated ~5-10x reduction).

### 4. Parallelization
Monte Carlo simulation is embarrassingly parallel. Each hand can be evaluated independently. Use:
- Multi-threaded Rust (rayon) for CPU parallelism
- Optional GPU compute (CUDA) for massive throughput
- Distributed across multiple machines if available

### 5. Storage Format
Results stored in compressed binary format:
- For each canonical hand: the optimal setting (1 byte for top index, 1 byte for mid combo index) + EV (4 bytes float)
- Total storage for 133M hands: ~800MB uncompressed, ~200MB compressed
- Can also store full 105-setting EV arrays for analysis: ~56GB uncompressed

### 6. Trainer Interface
Web-based (React or simple HTML/JS) or CLI-based:
- Deal random 7-card hand
- User sets their hand (top/mid/bot)
- Compare against computed optimal
- Show EV difference and explain why optimal is better
- Track user accuracy over time

---

## Code Quality Standards

### Comment Requirements
This is a computational/mathematical project. Comments should focus on:
- WHY a particular algorithm or optimization was chosen
- Mathematical formulas and their derivations
- Performance-critical code sections and their bottlenecks
- Correctness proofs for hand evaluation (Omaha 2+3 rule, etc.)
- Lookup table construction and verification

### Naming Conventions
```
Rust modules:        snake_case       hand_evaluator.rs
Rust structs:        PascalCase       struct HandSetting
Rust functions:      snake_case       fn evaluate_omaha()
Rust constants:      SCREAMING_CASE   const NUM_SETTINGS: usize = 105
Python modules:      snake_case       analysis.py
Python classes:      PascalCase       class TrainerSession
Config keys:         SCREAMING_CASE   NUM_MONTE_CARLO_SAMPLES
```

### Testing Standards
- Hand evaluation MUST be verified against known poker hands
- Omaha evaluation MUST enforce exactly-2-from-hand rule
- Monte Carlo convergence MUST be validated (run at N=100, N=1000, N=10000 and verify EV estimates converge)
- Regression tests for edge cases: wheel straights, suited boards, split pots

---

## File Structure Overview

```
taiwanese-solver/
├── docs/                           # All documentation
│   ├── CLAUDE.md                   # You are here
│   ├── CURRENT_PHASE.md
│   ├── DECISIONS_LOG.md
│   ├── checklist.md
│   ├── session-end-prompt.md
│   ├── handoff/
│   │   └── MASTER_HANDOFF_01.md
│   ├── sprints/
│   │   ├── SPRINT_INDEX.md
│   │   ├── s0-foundation.md
│   │   ├── s1-hand-evaluator.md
│   │   ├── s2-monte-carlo.md
│   │   ├── s3-best-response.md
│   │   ├── s4-bucketing-cfr.md
│   │   ├── s5-trainer.md
│   │   └── s6-validation.md
│   └── modules/
│       ├── hand-evaluation.md
│       ├── monte-carlo-engine.md
│       ├── scoring-system.md
│       ├── hand-bucketing.md
│       ├── cfr-algorithm.md
│       └── trainer-ui.md
│
├── engine/                         # Rust core engine
│   ├── Cargo.toml
│   ├── src/
│   │   ├── main.rs
│   │   ├── lib.rs
│   │   ├── card.rs                # Card, Deck, Suit, Rank types
│   │   ├── hand_eval.rs           # 5-card hand evaluator + lookup table
│   │   ├── holdem_eval.rs         # Top tier (1+5) and Middle tier (2+5) evaluation
│   │   ├── omaha_eval.rs          # Bottom tier: exactly 2 from hand + 3 from board
│   │   ├── setting.rs             # HandSetting: top(1) + mid(2) + bot(4) from 7 cards
│   │   ├── scoring.rs             # Score two settings against two boards
│   │   ├── monte_carlo.rs         # Monte Carlo simulation engine
│   │   ├── best_response.rs       # Compute best setting for each hand vs random
│   │   ├── bucketing.rs           # Hand canonicalization and bucketing
│   │   ├── cfr.rs                 # Counterfactual Regret Minimization
│   │   └── lookup/
│   │       ├── mod.rs
│   │       └── tables.rs          # Pre-computed hand rank lookup tables
│   ├── benches/                   # Performance benchmarks
│   │   ├── eval_bench.rs
│   │   └── monte_carlo_bench.rs
│   └── tests/
│       ├── hand_eval_tests.rs
│       ├── omaha_tests.rs
│       ├── scoring_tests.rs
│       └── integration_tests.rs
│
├── analysis/                       # Python analysis + visualization
│   ├── pyproject.toml
│   ├── src/
│   │   ├── __init__.py
│   │   ├── reader.py              # Read Rust output files
│   │   ├── features.py            # Extract hand + setting features from raw data
│   │   ├── patterns.py            # Pattern mining across hand categories
│   │   ├── decision_tree.py       # Build decision tree from solver data
│   │   ├── validate.py            # Test decision tree vs solver agreement
│   │   ├── stats.py               # Statistical analysis of results
│   │   ├── visualize.py           # Charts and graphs
│   │   ├── compare.py             # Compare heuristic vs computed optimal
│   │   └── strategy_gen.py        # Generate final strategy document from solver data
│   └── notebooks/
│       ├── exploration.ipynb
│       ├── pattern_analysis.ipynb  # Deep dive into pattern mining
│       ├── decision_tree.ipynb     # Decision tree construction + validation
│       └── results.ipynb
│
├── consensus/                      # AI multi-model analysis engine
│   ├── pyproject.toml
│   ├── src/
│   │   ├── __init__.py
│   │   ├── data_prep.py           # Prepare data packages for AI models
│   │   ├── baseline.py            # Statistical baseline (pure math, no AI)
│   │   ├── claude_analyst.py      # Anthropic API — independent analysis
│   │   ├── gemini_analyst.py      # Google API — independent analysis
│   │   ├── debate.py              # Orchestrate Socratic debate rounds
│   │   ├── consensus.py           # Extract consensus from debate
│   │   └── output.py              # Generate structured strategy JSON
│   └── transcripts/               # Full debate logs (append-only)
│       └── .gitkeep
│
├── trainer/                        # Training/quiz application
│   ├── pyproject.toml
│   ├── src/
│   │   ├── __init__.py
│   │   ├── app.py                 # Main trainer application
│   │   ├── dealer.py              # Deal random hands
│   │   ├── evaluator.py           # Check user's setting vs optimal
│   │   ├── display.py             # Terminal or web display
│   │   └── stats.py               # Track user performance
│   └── data/
│       └── optimal_settings.bin   # Computed optimal settings (from engine)
│
├── data/                           # Generated data files
│   ├── lookup_table.bin           # 5-card hand rank lookup table
│   ├── best_response/             # Best response results per hand bucket
│   └── cfr/                       # CFR convergence data
│
├── scripts/
│   ├── build.sh                   # Build Rust engine
│   ├── run_solver.sh              # Run full solve pipeline
│   ├── run_trainer.sh             # Launch trainer
│   └── benchmark.sh               # Run performance benchmarks
│
├── .gitignore
└── README.md
```

---

## Performance Targets

| Operation | Target | Notes |
|-----------|--------|-------|
| 5-card hand evaluation | <50 nanoseconds | Via lookup table |
| Single Omaha evaluation (4 hole + 5 board) | <500 nanoseconds | 60 lookups |
| Single Middle evaluation (2 hole + 5 board) | <200 nanoseconds | 21 lookups |
| Single Top evaluation (1 hole + 5 board) | <50 nanoseconds | 6 lookups |
| Full setting evaluation (3 tiers × 2 boards) | <2 microseconds | |
| Monte Carlo: 1 hand, 1 setting, 1000 samples | <5 milliseconds | |
| Monte Carlo: 1 hand, all 105 settings, 1000 samples | <500 milliseconds | |
| Full best-response solve (133M hands) | <1 week (single machine) | With parallelism |
| Full best-response solve (133M hands) | <24 hours (cluster) | 32+ cores |

---

## Environment Variables

```bash
# Engine Configuration
TW_NUM_THREADS=8                    # Parallel threads for Monte Carlo
TW_MONTE_CARLO_SAMPLES=1000        # Samples per setting per hand (adjustable)
TW_OUTPUT_DIR=./data/results        # Where to write results
TW_LOOKUP_TABLE=./data/lookup_table.bin

# Trainer Configuration
TW_OPTIMAL_DATA=./data/best_response/optimal.bin
TW_TRAINER_PORT=8080                # Web trainer port (if web-based)

# Debug
TW_LOG_LEVEL=info                   # trace, debug, info, warn, error
TW_PROGRESS_INTERVAL=100000        # Print progress every N hands

# AI Consensus Engine (Sprint 7)
ANTHROPIC_API_KEY=sk-ant-...        # For Claude analysis
ANTHROPIC_MODEL=claude-sonnet-4-20250514
GOOGLE_API_KEY=AI...                # For Gemini analysis
GEMINI_MODEL=gemini-2.5-pro
DEBATE_ROUNDS=4                     # Socratic debate rounds
CONFIDENCE_THRESHOLD=0.95           # Min agreement for "settled" rules
```

---

## Useful Commands

```bash
# Build
cd engine && cargo build --release

# Run benchmarks
cargo bench

# Run tests
cargo test

# Run full solver (all 133M hands, will take days)
cargo run --release -- solve --samples 1000 --threads 8 --output ../data/best_response/

# Run solver on a subset (for testing)
cargo run --release -- solve --subset 10000 --samples 100 --threads 4

# Evaluate a single hand
cargo run --release -- eval --hand "As Kh Qd Jc Ts 9h 2d"

# Run trainer
cd trainer && python src/app.py

# Analysis
cd analysis && jupyter notebook notebooks/results.ipynb
```

---

## After Reading This File

**Read these next, in order:**
1. `docs/CURRENT_PHASE.md` — what's happening right now
2. The active sprint file referenced in CURRENT_PHASE.md
3. `docs/modules/hand-evaluation.md` — the core algorithm
4. `docs/modules/scoring-system.md` — how scoring works

---

*Last updated: April 2026 (pre-build)*
