# Sprint 7: Analytics Pipeline + GTO Strategy Extraction

> **Phase:** Phase 4 - Analytics & Final Output
> **Status:** NOT STARTED

---

## Sprint Goals

This is the MOST IMPORTANT sprint. The solver produces data. This sprint turns data into the solved strategy.

1. Export solver results with full feature extraction
2. Run pattern mining across all hand categories
3. Build the decision tree from solver data
4. Validate decision tree against solver (target: 95%+ agreement)
5. Identify and catalog edge cases where simple rules fail
6. Quantify EV gain of perfect play vs heuristic play
7. Generate the final GTO strategy document

---

## Tasks

### Data Export & Feature Extraction
| Task | Status | Notes |
|------|--------|-------|
| Read binary solver output into Python | Pending | Use reader.py |
| Extract hand features for all hands (pair count, ranks, suits, connectivity) | Pending | See analytics-pipeline.md |
| Extract setting features (mid type, top rank, bot suitedness) | Pending | |
| Store in Parquet or SQLite for fast querying | Pending | ~2-4GB |
| Verify: sample 1000 hands, manually check features are correct | Pending | |

### Pattern Mining
| Task | Status | Notes |
|------|--------|-------|
| By hand category: what % put pair in mid? | Pending | |
| By pair rank: at what rank does pair-in-mid stop being dominant? | Pending | |
| Two pair analysis: which pair goes mid, which goes bot? | Pending | Cross-tab by rank |
| Trips analysis: does third card ever go top? | Pending | Verify our "never" rule |
| Unpaired analysis: what 2-card combo goes mid? | Pending | Highest 2 vs connected? |
| Suitedness analysis: EV of DS vs SS vs rainbow bottom | Pending | By hand type |
| When does optimal deviate from MiddleFirst? | Pending | Categorize all deviations |
| Top card analysis: EV by rank across all hands | Pending | |

### Decision Tree Construction
| Task | Status | Notes |
|------|--------|-------|
| Define tree structure: category → rank → suitedness → action | Pending | |
| Build tree rules from pattern data | Pending | |
| Implement tree as code (JSON rules engine) | Pending | |
| Test tree on 100K random hands vs solver | Pending | Target 95%+ match |
| Iterate: add branches for disagreement cases | Pending | |
| Iterate until 98%+ agreement or diminishing returns | Pending | |

### Validation & Comparison
| Task | Status | Notes |
|------|--------|-------|
| Agreement rate: decision tree vs solver | Pending | Target 95-99% |
| Average EV loss when tree disagrees with solver | Pending | Target <$0.10 |
| Comparison: heuristic MiddleFirst vs solver | Pending | Quantify improvement |
| Comparison: pre-solver strategy guide vs solver | Pending | Were we right? |
| Identify top 100 "most surprising" solver decisions | Pending | Hands where intuition is wrong |
| Catalog: hands where solver says OmahaFirst is correct | Pending | If any exist |

### Final Output Generation
| Task | Status | Notes |
|------|--------|-------|
| One-page flowchart (decision tree visual) | Pending | |
| Detailed rules per hand category with solver numbers | Pending | |
| Edge case catalog with examples | Pending | |
| EV benchmark table by hand type | Pending | |
| Common mistakes ranked by EV cost | Pending | |
| "Was our heuristic right?" comparison report | Pending | |
| Generate final HTML strategy guide (updated from pre-solver version) | Pending | |

### AI Consensus Engine (Multi-Model Analysis)
| Task | Status | Notes |
|------|--------|-------|
| Prepare data packages from solver output | Pending | See ai-consensus-engine.md |
| Compute statistical baseline (pure math, no AI) | Pending | Ground truth for debate |
| Run independent Claude analysis on solver data | Pending | Anthropic API |
| Run independent Gemini analysis on solver data | Pending | Google API |
| Round 2: Each model challenges the other's findings | Pending | |
| Round 3: Each model defends against challenges | Pending | |
| Round 4: Consensus — produce agreed decision tree | Pending | |
| Flag disputed rules with confidence levels | Pending | |
| Human review of consensus strategy | Pending | Player gut-check |
| Final iteration if human flags issues | Pending | |
| Save full debate transcript for auditability | Pending | |
| Output structured strategy JSON with rules + confidence | Pending | |

---

## Key Success Metrics

| Metric | Target | Meaning |
|--------|--------|---------|
| Decision tree agreement | 95-99% | Tree matches solver for nearly all hands |
| Avg EV loss on disagreements | <$0.10 | When tree is wrong, it's barely wrong |
| Heuristic vs solver EV gap | Measured | How much our pre-solver guide leaves on the table |
| Perfect play vs MiddleFirst | Measured | The true value of solving the game |
| Edge cases cataloged | 100% | Every disagreement is explained |

---

## Session Log
