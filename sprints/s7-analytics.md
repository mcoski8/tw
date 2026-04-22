# Sprint 7: Analytics Pipeline + GTO Strategy Extraction

> **Phase:** Phase 4 - Analytics & Final Output
> **Status:** FOUNDATIONAL INFRASTRUCTURE COMPLETE (readers + decoders + Rust parity gate — Session 08); pattern mining and decision-tree work deferred until all 4 cloud `.bin` files land (~2026-04-26)

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
| Read binary solver output into Python | **Done (S08)** | `tw_analysis.br_reader` — numpy structured dtype, load + memmap, full validation |
| Read canonical-hand file into Python | **Done (S08)** | `tw_analysis.canonical` — `CanonicalHands.hand_cards(id)` for id→7-cards |
| Setting-index decoder | **Done (S08)** | `tw_analysis.settings.decode_setting` — byte-identical to Rust `all_settings` |
| Byte-identical Rust parity gate | **Done (S08)** | Decision 028 — `diff` passes across 519-line `spot-check` output |
| Python canonicalize + is_canonical | **Done (S08)** | Mirror of `engine/src/bucketing.rs`, 24-perm suit group |
| Inverse lookup (hand → canonical_id) | **Done (S08)** | Binary search via `tobytes()` comparison |
| Extract hand features for all hands (pair count, ranks, suits, connectivity) | Pending | Deferred to after all 4 `.bin` files are local |
| Extract setting features (mid type, top rank, bot suitedness) | Pending | |
| Store in Parquet or SQLite for fast querying | Pending | ~2-4GB |
| Verify: sample 1000 hands, manually check features are correct | Pending | Parity gate from S08 means decode is trustworthy; feature correctness still needs its own check |

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

### Session 08 — 2026-04-20 to 2026-04-21 — Python analysis stack + byte-identical Rust parity gate

**Context:** Sprint 3 cloud production still running on RunPod (Model 1 done and downloaded mid-session, Model 2 at ~35% at session end). Rather than idle for ~5 more days, built the Sprint 7 foundation: Python readers + decoders that can ingest the `.bin` outputs as they land, verified byte-for-byte against the Rust engine.

**Completed:**
- `analysis/src/tw_analysis/br_reader.py` — reads best-response `.bin` (header + 9-byte records), `load` and `memmap` modes, full validation (magic, version, canonical_id ordering, setting-index bounds, finite EV, plausible EV range).
- `analysis/src/tw_analysis/settings.py` — `Card`, `HandSetting`, `parse_hand`, `decode_setting`, `all_settings`. Mirrors `engine/src/setting.rs` enumeration: outer top 0..7 × inner `(a<b)` on the remaining 6 cards, mid/bot sorted desc by packed card index.
- `analysis/src/tw_analysis/canonical.py` — reads `canonical_hands.bin` (`TWCH` magic + 32-byte header + N × 7 uint8 rows). Includes `canonicalize()`, `is_canonical()`, `CanonicalHands.hand_cards(id)`, `CanonicalHands.find(hand) → canonical_id`.
- `analysis/scripts/inspect_br.py` — CLI inspector (header + validation + stats + head).
- `analysis/scripts/test_settings.py` — 11 unit tests, all green.
- `analysis/scripts/test_canonical.py` — 9 unit tests, all green.
- **Byte-identical cross-verify against Rust `tw-engine spot-check --show 500`:** 519-line output rendered from Python via the decoder pipeline matches Rust's output with zero `diff` differences. Decision 028 elevates this to a standing correctness gate for all future readers/decoders.

**Real-data validation against Model 1:**
- 6,009,159 records; canonical_id strictly 0..N-1 in order; all setting indices ∈ [0,104]; all EVs finite; header opponent tag `1_002_090` correctly decoded as `HeuristicMixed(MiddleFirstSuitAware, p=0.90)`.
- Top-5 most-chosen setting indices on Model 1: 104 (19.7%), 102 (10.6%), 74 (10.3%), 99 (9.5%), 90 (9.3%). Several of these share the "low-card top" pattern but conclusions deferred until Models 2-4 can be compared.
- `canonical_hands.bin` full-file lex ordering verified; 500-hand `is_canonical` spot-check all true; cross-checked `br.header.canonical_total == len(canonical_hands) == 6,009,159`.

**Gotchas:**
- `np.searchsorted`, `<=`, and `!=` do not work on `np.void` structured dtypes (no ufunc loop). Initial draft of `CanonicalHands.find()` and the adjacent-pair lex-ordering check both broke on this; replaced with `tobytes()`-based binary search and vectorized int16 column-diff (`argmax` of first non-zero column across 7 columns) respectively.
- RunPod auto-provisions SSH keys on pod CREATION only, not when keys are added to a running pod. Had to manually append public key to the pod's `~/.ssh/authorized_keys` via web terminal. Web terminal's single-quote line wrapping does NOT break the key — Base64 data stayed on one line, trailing comment orphaned on a second line (ignored by OpenSSH).

**Deliberate non-action:**
- Did NOT start single-model pattern mining or feature extraction. The 4 models exist specifically to compare strategy shifts under different opponent assumptions; any pattern conclusion from Model 1 alone would mislead and likely need to be re-derived once all 4 are in. That's also why the hand-feature extractor is pending — easier to design with four files in hand.
