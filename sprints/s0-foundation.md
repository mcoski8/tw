# Sprint 0: Foundation + Lookup Tables

> **Phase:** Phase 1 - Engine Core
> **Status:** NOT STARTED
> **Sprint File:** `docs/sprints/s0-foundation.md`

---

## Sprint Goals

1. Initialize Rust project with proper dependency management
2. Define core types: Card, Rank, Suit, Deck
3. Build 5-card hand evaluator with lookup table generation
4. Verify hand evaluator correctness against known hand rankings
5. Benchmark hand evaluation speed (target: <50ns per eval)
6. Define HandSetting type (top=1, mid=2, bot=4 from 7 cards)
7. Enumerate all 105 possible settings for a 7-card hand
8. First working binary that evaluates a hand from CLI
9. Initialize Python analysis project structure
10. Initialize documentation

---

## Tasks

### Rust Project Setup
| Task | Status | Notes |
|------|--------|-------|
| Create `engine/Cargo.toml` with dependencies | Pending | rayon, rand, serde, clap |
| Define Card type (rank: u8, suit: u8) | Pending | Compact representation |
| Define Rank enum (2-14, A=14) | Pending | |
| Define Suit enum (0-3) | Pending | |
| Implement Deck: new(), shuffle(), deal() | Pending | |
| Implement Display traits for cards | Pending | "As", "Kh", "2d" format |
| Parse cards from string ("As Kh Qd") | Pending | CLI input |

### 5-Card Hand Evaluator
| Task | Status | Notes |
|------|--------|-------|
| Choose evaluation algorithm | Pending | Cactus Kev, Two-plus-two, or custom PHF |
| Implement 5-card hand rank computation | Pending | Returns comparable integer |
| Generate lookup table for all C(52,5) = 2,598,960 hands | Pending | |
| Serialize lookup table to binary file | Pending | ~10-20MB |
| Load lookup table from file on startup | Pending | Memory-mapped or direct load |
| Verify: Royal flush > straight flush > quads > ... > high card | Pending | |
| Verify: A-2-3-4-5 is lowest straight (wheel) | Pending | |
| Verify: Same hand ranks compare by kickers correctly | Pending | |
| Benchmark: target <50ns per evaluation | Pending | |

### Hand Setting Type
| Task | Status | Notes |
|------|--------|-------|
| Define HandSetting struct: top(Card), mid([Card;2]), bot([Card;4]) | Pending | |
| Implement `all_settings(hand: [Card;7]) -> Vec<HandSetting>` | Pending | Returns 105 settings |
| Verify: all 105 settings use all 7 cards exactly once | Pending | |
| Implement Display for HandSetting | Pending | |

### Project Infrastructure
| Task | Status | Notes |
|------|--------|-------|
| Create .gitignore | Pending | target/, data/*.bin, .env |
| Create README.md | Pending | |
| Create scripts/build.sh | Pending | |
| Initialize Python analysis project | Pending | pyproject.toml |
| Verify all docs/ files in place | Pending | |
| First git commit | Pending | |

---

## Acceptance Criteria

- [ ] `cargo test` passes with all hand evaluation tests green
- [ ] `cargo bench` shows <50ns per 5-card evaluation
- [ ] CLI can parse "As Kh Qd Jc Ts 9h 2d" and display all 105 settings
- [ ] Lookup table generates and loads correctly
- [ ] Documentation complete

---

## Session Log

*(Sessions appended here as they occur)*
