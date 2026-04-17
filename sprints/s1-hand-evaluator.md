# Sprint 1: Hand Evaluator (Hold'em + Omaha)

> **Phase:** Phase 1 - Engine Core
> **Status:** NOT STARTED

---

## Sprint Goals

Build the tier-specific evaluators on top of the 5-card lookup table:
1. Top tier evaluator: best 5 of 6 cards (1 hole + 5 board)
2. Middle tier evaluator: best 5 of 7 cards (2 hole + 5 board) — standard Hold'em
3. Bottom tier evaluator: Omaha — MUST use exactly 2 from 4 hole + 3 from 5 board
4. Full scoring system: compare two players' settings across two boards
5. Scoop detection (all 6 matchups won, zero chops)

---

## Tasks

### Top Tier Evaluator
| Task | Status | Notes |
|------|--------|-------|
| Implement `eval_top(card: Card, board: [Card;5]) -> HandRank` | Pending | Best 5 of 6, try dropping each of 6 |
| Test: A with board KQJT2 = broadway straight | Pending | |
| Test: 7 with board 77KQ3 = trips | Pending | |
| Benchmark: target <100ns | Pending | 6 lookups |

### Middle Tier Evaluator
| Task | Status | Notes |
|------|--------|-------|
| Implement `eval_middle(hole: [Card;2], board: [Card;5]) -> HandRank` | Pending | Best 5 of 7, C(7,5)=21 combos |
| Test: AA with board KQJ32 = pair of aces | Pending | |
| Test: 87s with board 654AK = straight | Pending | |
| Benchmark: target <200ns | Pending | 21 lookups |

### Bottom Tier (Omaha) Evaluator
| Task | Status | Notes |
|------|--------|-------|
| Implement `eval_omaha(hole: [Card;4], board: [Card;5]) -> HandRank` | Pending | C(4,2)×C(5,3) = 60 combos |
| **CRITICAL:** Verify exactly 2 from hand + 3 from board | Pending | Must NOT use 1 or 3 from hand |
| Test: AAKK with board A2345 = three aces (use AA from hand + A23 or A34 etc from board) | Pending | |
| Test: 4 spades in hand with 3 spades on board = flush ONLY if 2 hand spades + 3 board spades | Pending | |
| Test: 4 spades in hand with 4 spades on board = flush uses 2 hand spades + 3 board (one board spade unused) | Pending | |
| Benchmark: target <500ns | Pending | 60 lookups |

### Scoring System
| Task | Status | Notes |
|------|--------|-------|
| Implement `score_matchup(p1: HandSetting, p2: HandSetting, board1: [Card;5], board2: [Card;5]) -> (i32, i32)` | Pending | Returns points for each player |
| Implement scoop detection: all 6 wins, 0 chops → 20 points | Pending | |
| Implement chop handling: equal ranks → 0 points for that matchup | Pending | |
| Test: known hands with known board, verify correct scores | Pending | |
| Test: scoop scenario (one player dominates all 6) | Pending | |
| Test: full chop scenario (identical settings somehow) | Pending | |

---

## Session Log
