# Sprint 2: Monte Carlo Engine

> **Phase:** Phase 1 - Engine Core
> **Status:** NOT STARTED

---

## Sprint Goals

Build the Monte Carlo simulation engine that evaluates a hand setting's expected value by sampling random opponents and random boards.

1. Single-hand evaluator: given a setting, sample N random opponents + boards, compute average score
2. All-settings evaluator: for a 7-card hand, evaluate all 105 settings, return ranked list
3. Parallelization with rayon for multi-threaded simulation
4. Progress reporting for long-running computations
5. Convergence testing: verify EV estimates stabilize as N increases

---

## Tasks

### Core Monte Carlo
| Task | Status | Notes |
|------|--------|-------|
| Implement `mc_evaluate_setting(setting, hand, num_samples) -> f64` | Pending | Returns average EV |
| For each sample: deal random opponent 7 cards from remaining deck | Pending | |
| For each sample: opponent sets hand using MiddleFirst heuristic | Pending | Realistic opponent |
| For each sample: deal 2 boards from remaining cards | Pending | |
| For each sample: score the matchup, accumulate points | Pending | |
| Return: average points per hand (EV) | Pending | |

### Opponent Modeling
| Task | Status | Notes |
|------|--------|-------|
| Implement MiddleFirst opponent strategy | Pending | Based on our research |
| Implement Random opponent strategy | Pending | For baseline comparison |
| Implement TopDefense opponent strategy | Pending | Alternative |
| Config: select opponent model for simulation | Pending | |

### All-Settings Evaluation
| Task | Status | Notes |
|------|--------|-------|
| Implement `mc_evaluate_all_settings(hand, num_samples) -> Vec<(HandSetting, f64)>` | Pending | |
| Sort by EV descending | Pending | |
| Report best setting and its EV | Pending | |
| Report EV gap between best and second-best | Pending | |
| Report EV of worst setting for comparison | Pending | |

### Parallelization
| Task | Status | Notes |
|------|--------|-------|
| Parallelize samples within one setting (rayon) | Pending | |
| Parallelize across settings for one hand | Pending | |
| Thread-safe random number generation (per-thread RNG) | Pending | |
| Configurable thread count via env var | Pending | |

### Convergence & Validation
| Task | Status | Notes |
|------|--------|-------|
| Test: run same hand at N=100, 500, 1000, 5000, 10000 | Pending | |
| Verify: EV estimates converge (standard error decreases) | Pending | |
| Compute confidence intervals for EV estimates | Pending | |
| Determine minimum N for <0.1 EV standard error | Pending | |

### CLI Interface
| Task | Status | Notes |
|------|--------|-------|
| `cargo run -- eval --hand "As Kh Qd Jc Ts 9h 2d" --samples 1000` | Pending | |
| Display: all 105 settings ranked by EV | Pending | Top 10 at minimum |
| Display: best setting with tier breakdown (top/mid/bot EV) | Pending | |
| Display: computation time | Pending | |

---

## Performance Targets

| Operation | Target |
|-----------|--------|
| 1 hand, 1 setting, 1000 samples | <5ms |
| 1 hand, 105 settings, 1000 samples | <500ms |
| 1 hand, 105 settings, 10000 samples | <5 seconds |

---

## Session Log

---

## Optional: CUDA Backend (Sprint 2b)

If GPU acceleration is desired, add after CPU Monte Carlo is validated:

| Task | Status | Notes |
|------|--------|-------|
| Add `cuda` feature flag to Cargo.toml | Pending | cust + cuda-sys |
| Write CUDA kernel for sample evaluation | Pending | One thread = one full sample |
| Load lookup table into GPU global memory | Pending | ~20MB, fits easily |
| Batch settings → GPU, collect results | Pending | |
| Benchmark: A100 vs 8-core CPU throughput | Pending | Target: 10-50x speedup |
| Verify: GPU results match CPU results exactly | Pending | CRITICAL |
| Test on Vast.ai or RunPod rental | Pending | |

The CPU backend is the reference. GPU results MUST match CPU results for identical inputs (same seed, same samples). Any divergence is a bug.
