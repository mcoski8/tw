# Taiwanese Poker Solver

A computational engine that solves (or near-solves) Taiwanese Poker — a card-setting
variant played with 7-card hands, 3 tiers (top=1 card, middle=2 cards, bottom=4 cards),
and two 5-card community boards. The bottom tier plays as Omaha (exactly 2 from hand +
3 from board), middle and top play as Hold'em. Scoring: 1/2/3 points per tier per
board (12 max), 20-point scoop for winning all 6 matchups with zero chops.

## Project Structure

```
taiwanese/
├── CLAUDE.md, CURRENT_PHASE.md, ...   # Master project docs
├── modules/                           # Module specs (hand eval, scoring, compute pipeline, ...)
├── sprints/                           # Per-sprint task lists
├── engine/                            # Rust core engine
├── analysis/                          # Python analysis + pattern mining (later sprints)
├── consensus/                         # AI multi-model analysis (Sprint 7)
├── trainer/                           # Training/quiz app (Sprint 5)
├── data/                              # Generated tables + solver output
└── scripts/                           # Build + run helpers
```

Read `CLAUDE.md` first for full project context, game rules, and architectural decisions.

## Getting Started

### Prerequisites
- Rust (stable, 1.75+)
- Python 3.11+ (needed only for analysis/trainer in later sprints)

### Build

```
./scripts/build.sh
```

### Run the hand-setting enumerator (Sprint 0 capability)

```
cd engine
cargo run --release -- eval --hand "As Kh Qd Jc Ts 9h 2d"
```

Outputs all 105 possible top/middle/bottom settings for the 7-card hand. EV computation
comes online in Sprint 2 (Monte Carlo).

### Tests and benchmarks

```
cd engine
cargo test --release   # 15 tests, including a full 2,598,960-hand table vs direct-compute roundtrip
cargo bench            # eval_5 ~5 ns (target <50 ns)
```

## Current Status

Sprint 0 — Foundation + Lookup Tables. See `CURRENT_PHASE.md`.
