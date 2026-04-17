# Sprint 3: Best Response Computation (Multi-Pass Adaptive Solver)

> **Phase:** Phase 2 - Solving
> **Status:** NOT STARTED

---

## Sprint Goals

Compute the optimal setting for every possible 7-card hand using the adaptive multi-pass pipeline. This is THE sprint that solves the game.

1. Implement setting pre-screening (reduce 105 → ~25 viable settings per hand)
2. Implement 3-pass adaptive solver (quick scan → precision → final resolution)
3. Implement suit canonicalization to reduce ~133M hands to ~18M
4. Implement checkpoint/resume system for multi-week computation
5. Implement progress reporting with ETA
6. Run Pass 1 (~3 days), analyze results, run Passes 2-3 (~7-10 days)
7. Validate output against Monte Carlo spot-checks

See `docs/modules/compute-pipeline.md` for full technical spec including time estimates, memory requirements, and output format.

---

## Tasks

### Setting Pre-Screening
| Task | Status | Notes |
|------|--------|-------|
| Implement quick_score() for any HandSetting | Pending | Mid×4 + Top×2 + Bot×1.5 |
| Implement pre_screen(hand) → top 25 settings by quick_score | Pending | |
| Validate: sample 10K hands, confirm true optimal is always in top 25 | Pending | CRITICAL |
| If validation fails: widen to top 30-35 or adjust weights | Pending | |

### Hand Canonicalization
| Task | Status | Notes |
|------|--------|-------|
| Implement suit permutation canonicalization | Pending | |
| Build canonical_index → hand mapping | Pending | |
| Build hand → canonical_index mapping | Pending | |
| Count total canonical hands (expect ~15-20M) | Pending | |
| Verify: all suit permutations of a hand map to same canonical | Pending | |

### Pass 1 — Quick Scan
| Task | Status | Notes |
|------|--------|-------|
| Implement Pass 1 loop: 25 settings × M=50 × N=50 per hand | Pending | |
| Record: best_setting, best_ev, second_ev, ev_gap per hand | Pending | |
| Flag ambiguous hands (ev_gap < 0.5) for Pass 2 | Pending | |
| Checkpoint every 100K hands | Pending | |
| Progress reporting with ETA | Pending | |
| Run on all canonical hands | Pending | Est: 2-3 days on M4 Mini |
| Analyze results: what % resolved? Distribution of EV gaps? | Pending | |

### Pass 2 — Precision
| Task | Status | Notes |
|------|--------|-------|
| Read ambiguous hand list from Pass 1 | Pending | |
| Run: top 5 settings × M=500 × N=500 per ambiguous hand | Pending | |
| Re-flag: hands still within 0.10 EV for Pass 3 | Pending | |
| Checkpoint every 50K hands | Pending | |
| Run | Pending | Est: 4-6 days on M4 Mini |

### Pass 3 — Final Resolution
| Task | Status | Notes |
|------|--------|-------|
| Run: top 3 settings × M=2000 × N=2000 per remaining hand | Pending | |
| Flag hands within 0.05 EV as "genuinely equivalent" | Pending | |
| Run | Pending | Est: 2-4 days on M4 Mini |

### Output & Validation
| Task | Status | Notes |
|------|--------|-------|
| Write final results to binary file | Pending | |
| Generate summary statistics | Pending | |
| Spot-check: pick 100 random hands, verify vs fresh Monte Carlo with M=10K N=10K | Pending | |
| Spot-check: pick 50 hands where solver disagrees with MiddleFirst heuristic, verify manually | Pending | |

---

## Compute Budget (M4 Mac Mini, 8 effective cores)

| Pass | Hands | Time Estimate |
|------|-------|---------------|
| Pass 1 | ~18M | 2-3 days |
| Pass 2 | ~1-2M | 4-6 days |
| Pass 3 | ~100K | 2-4 days |
| **Total** | | **8-12 days** |

---

## Session Log
