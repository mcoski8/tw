# Module: Compute Pipeline — Adaptive Multi-Pass Solver

## Purpose

Computing the optimal setting for all ~18M canonical hands is the core workload. A naive approach (all 105 settings × high sample count × all hands) would take months. This module defines the optimized multi-pass pipeline that completes the solve in 1-2 weeks on an M4 Mac Mini.

---

## Key Optimizations

### 1. Setting Pre-Screening

Of the 105 possible settings for any 7-card hand, most are obviously terrible. A hand like A♠ K♥ Q♦ J♣ T♠ 9♥ 2♦ has 105 possible settings, but putting the 2 in the middle with the 9 while the Ace goes to bottom is clearly suboptimal.

**Pre-screen heuristic (runs in microseconds, no Monte Carlo needed):**
```
For each of 105 settings, compute a quick score:
    mid_score:
        pair → 40 + pair_rank × 2
        suited broadway → 25 + high_rank + low_rank
        offsuit broadway → 20 + high_rank + low_rank
        suited connector → 15 + high_rank
        junk → high_rank
    
    top_score:
        rank of top card (2-14)
    
    bot_score:
        pair_bonus + connectivity_bonus + double_suited_bonus
    
    quick_total = mid_score × 4 + top_score × 2 + bot_score × 1.5
```

**Keep only the top 20-25 settings** (by quick_total) for Monte Carlo evaluation. This eliminates ~80% of settings instantly.

**Verification:** During development, run a sample of 10,000 hands with ALL 105 settings and confirm the pre-screened top-25 always contains the true optimal. If not, widen the screen or adjust scoring weights.

### 2. Adaptive Multi-Pass Computation

**Pass 1 — Quick Scan (identifies ~90% of optimal settings)**
- Settings evaluated: top 25 (pre-screened)
- Opponent samples (M): 50
- Board samples (N): 50
- Samples per setting: 2,500
- Standard error: ±0.24 EV
- Purpose: identify hands where one setting clearly dominates (EV gap > 0.5)

**Pass 2 — Precision on Ambiguous Hands (~5-10% of hands)**
- Trigger: any hand where EV gap between rank 1 and rank 2 setting is < 0.5
- Settings evaluated: top 5 from Pass 1
- Opponent samples: 500
- Board samples: 500
- Samples per setting: 250,000
- Standard error: ±0.024 EV
- Purpose: resolve close decisions with 10x precision

**Pass 3 — Final Resolution on Toss-Up Hands (~0.5-1% of hands)**
- Trigger: EV gap still < 0.10 after Pass 2
- Settings evaluated: top 3 from Pass 2
- Opponent samples: 2,000
- Board samples: 2,000
- Samples per setting: 4,000,000
- Standard error: ±0.006 EV
- Purpose: definitively resolve the closest decisions

**Hands that remain within 0.05 EV after Pass 3** are genuinely equivalent — either setting is optimal. Flag these as "either works" in the output.

### 3. Partial Result Caching

Each evaluation (our setting vs one opponent hand vs one board pair) produces intermediate data. Cache:
- The opponent's optimal setting (looked up from prior computation or heuristic)
- Pre-computed 2-card Omaha combinations for our 4 bottom cards (6 combos, computed once per setting)
- Pre-computed 2-card combos for opponent's bottom (6 combos, computed once per opponent)

This avoids redundant work when evaluating the same setting against different boards.

### 4. Lookup Table Optimization

Use the Two-Plus-Two style evaluator (7-card lookup table, ~130MB in memory):
- 5-card evaluation: ~10-15ns (hash lookup)
- Eliminates the need to enumerate C(n,5) combinations in some cases

For Omaha specifically, pre-build a table of all C(4,2) = 6 two-card combos for each 4-card holding, so the inner loop only iterates over C(5,3) = 10 board combos × 6 pre-built hand combos = 60 lookups.

---

## Time Estimates

### Per-Evaluation Cost (Optimized)
| Operation | Time |
|-----------|------|
| 5-card lookup | 10-15ns |
| Top eval (6 lookups) | ~80ns |
| Middle eval (21 lookups) | ~250ns |
| Omaha eval (60 lookups) | ~700ns |
| Full matchup (2 players × 3 tiers × 2 boards) | ~2.0μs |
| Scoring + scoop check | ~50ns |
| **Total per sample** | **~2.1μs** |

### Per-Hand Cost by Pass
| Pass | Settings | Samples/Setting | Time/Hand | Total Time (18M hands, 8 cores) |
|------|----------|----------------|-----------|--------------------------------|
| Pass 1 | 25 | 2,500 | 131ms | **~66 hours (2.7 days)** |
| Pass 2 | 5 (on ~1.5M hands) | 250,000 | 2.6s | **~136 hours (5.7 days)** |
| Pass 3 | 3 (on ~100K hands) | 4,000,000 | 25.2s | **~88 hours (3.7 days)** |
| **Total** | | | | **~290 hours (~12 days)** |

### By Hardware
| Hardware | Effective Cores (leaving 2 for OS) | Est. Total Time |
|----------|-----------------------------------|-----------------|
| M2 Mac Mini (8-core) | 6 | 16-20 days |
| M2 Pro Mac Mini (12-core) | 10 | 10-13 days |
| M4 Mac Mini (10-core) | 8 (faster per-core) | 8-12 days |
| M4 Pro Mac Mini (14-core) | 12 (faster per-core) | 5-8 days |

---

## Checkpoint System

The solver MUST checkpoint regularly. A 2-week computation cannot be restarted from scratch.

```
Checkpoint format:
    checkpoint_YYYYMMDD_HHMMSS.bin
    
    Contains:
    - pass_number: which pass is running
    - hands_completed: count of hands finished in current pass
    - last_hand_index: resume point
    - results_so_far: Vec<(hand_index, best_setting, ev)>
    - ambiguous_hands: Vec<hand_index> (for next pass)
    
    Checkpoint interval: every 100,000 hands (~every 3-4 minutes in Pass 1)
```

On restart, the solver:
1. Finds latest checkpoint file
2. Loads completed results
3. Resumes from last_hand_index + 1
4. Continues as if never interrupted

---

## Progress Reporting

During computation, print to stdout:

```
[Pass 1] 1,234,567 / 18,000,000 hands (6.9%) | 2.7 days elapsed | ETA: 36.6 days
         Current hand: Ks Qh Jd Td 8s 5c 3h → Best: K top | QJ mid | Td8s5c3h bot (EV: +1.23)
         Ambiguous so far: 89,432 (7.2%)
         Checkpoint: checkpoint_20260420_143022.bin
```

---

## Memory Requirements

| Component | Size |
|-----------|------|
| 5-card lookup table | 10-20MB (or 130MB for 7-card two-plus-two) |
| Working memory per thread | ~1MB (deck, RNG state, temp arrays) |
| Results accumulator | ~200MB (18M hands × ~12 bytes each) |
| Ambiguous hand list | ~50MB max |
| **Total** | **~400MB** (well within any Mac Mini's RAM) |

---

## Output Format

### Per-Hand Result
```rust
struct HandResult {
    hand_index: u32,        // canonical hand identifier
    best_setting: u8,       // index into the 105 possible settings (0-104)
    best_ev: f32,           // expected value of best setting
    second_best_ev: f32,    // EV of second-best (to show confidence margin)
    pass_resolved: u8,      // which pass determined this (1, 2, or 3)
}
```

### Summary Output
```
Total hands solved: 18,234,567
Resolved in Pass 1: 16,411,110 (90.0%)
Resolved in Pass 2: 1,641,111 (9.0%)
Resolved in Pass 3: 164,111 (0.9%)
Genuinely equivalent (gap < 0.05): 18,235 (0.1%)

Average EV gap (best vs second): 1.34
Median EV gap: 0.87
Min EV gap (excluding equivalent): 0.051

Most common optimal setting pattern:
  1. Pair mid + highest remaining top: 62.3% of hands
  2. Best broadway mid + A/K top: 18.7% of hands
  3. [etc]
```
