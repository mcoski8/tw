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

### Sessions 09–54 — covered in CURRENT_PHASE.md rewrites + DECISIONS_LOG.md (Decisions 029–088) + SESSION_NN_*.md reports

The ML champion + rule chain work between Session 09 (oracle grid foundation) and Session 54 (v39_dt ML champion via diagnostic-driven feature engineering) was logged in DECISIONS_LOG.md and per-session SESSION_NN reports rather than this file. See `DECISIONS_LOG.md` and the `SESSION_NN_*.md` files at the repo root for per-session details. STRATEGY_GUIDE.md Part 1 has the strategy-of-record narrative.

### Session 55 — 2026-05-10 — Two ML champions in one session via the S54 playbook transferred to trips_pair + two_pair zones

**Context:** Session 54 had shipped v39_dt by applying a diagnostic-driven feature engineering playbook to the pair zone (+$237/1000h), with the explicit hypothesis that the methodology would generalize. Session 55 tested that hypothesis on the next two largest within-category residuals: trips_pair ($909/1000h) and two_pair ($918/1000h). Both shipped.

**Completed:**

*Track A — trips_pair (v40_dt ships +$18 full / +$29 prefix):*
- `analysis/scripts/drill_trips_pair_zone_v39_diagnostic.py` (Drill TP, Phase 1)
- `analysis/scripts/drill_trips_pair_v39_mismatch_handlevel.py` (Drill TP2, Phase 1b)
- `analysis/scripts/trips_pair_aug_v2_features_gated.py` + persist
- `analysis/scripts/train_v40_dt.py` + `strategy_v40_dt.py` + `grade_v40_dt.py`
- `data/v40_dt_model.npz` (91 features, 1.57M leaves) + `data/feature_table_trips_pair_aug_v2_gated.parquet`
- **trips_pair within-cat $909 → $281 (−$628, −69%); pct_opt 64.2% → 85.1%**
- All other categories byte-identical to v39 (surgical gating)

*Track B — two_pair (v41_dt ships +$124 full / +$86 prefix; NEW ML CHAMPION):*
- `analysis/scripts/drill_two_pair_zone_v39_diagnostic.py` (Drill T2P, Phase 1)
- `analysis/scripts/drill_two_pair_v39_mismatch_handlevel.py` (Drill T2P2, Phase 1b)
- `analysis/scripts/two_pair_aug_v2_features_gated.py` + persist
- `analysis/scripts/train_v41_dt.py` + `strategy_v41_dt.py` + `grade_v41_dt.py`
- `data/v41_dt_model.npz` (95 features, 2.02M leaves) + `data/feature_table_two_pair_aug_v2_gated.parquet`
- **two_pair within-cat $918 → $363 (−$555, −60%); pct_opt 66.6% → 83.2%**
- 3 of 4 new features in top-30 importance (#24, #26, #30)
- All other categories byte-identical to v40 (surgical gating preserved trips_pair $281)

**Cumulative session arc:** v39 → v41 = −$142/1000h full / −$115 prefix. Second-largest combined ML session lift after S54's single +$237. Cumulative v32 → v41 = −$445 full / −$218 prefix (6 ML ships).

**Methodology lessons:**
- The S54 playbook is **transferable** across ML residual zones: same Phase 1 drill shape, same Phase 1b hand-level inspection shape, same 4-feature design (n_configs, max_top, min_top/auxiliary, max_mid_sum or DS-specific), same depth=36 ml=1 hyperparams.
- **Asymmetric existing features signal blind spots.** Two_pair had `t2p_n_layout_b_routings_ds_g` (Layout B DS feature) but no Layout C equivalent — that asymmetry pointed directly at the missing design. Audit existing features for missing-mirror gaps.
- **Low individual importance + surgical gating = real ship.** tp_v2 features ranked at #69-78 individually (0.02-0.04%), but v40 still shipped +$18. Population-weighted utility > individual importance for gated features.
- **Population size dominates leaf-growth potential.** v40's 4 features added +3.4% leaves (over a 2.86% zone); v41's 4 features added +32% leaves (over a 22.3% zone). Same feature shapes, very different leaf impact — driven by gated population size.

**Documentation:**
- `SESSION_55_V41_DT_REPORT.md` — repo-root standalone report
- `CURRENT_PHASE.md` — rewritten
- `DECISIONS_LOG.md` — Decisions 089 (v40_dt) + 090 (v41_dt)
- `STRATEGY_GUIDE.md` Part 1 — Session 55 entry; Part 2 ML champion table updated

**End-of-S55 state:**
- ML champion: **v41_dt** at $1,270/1000h full / $686 prefix
- Rule chain production: **v52_full_high_only_handler** at $2,498 full / $1,522 prefix (UNCHANGED)
- Two production tracks diverge by $1,228/1000h
- Largest remaining residual: **high_only** zone ($2,796 within-cat × 40.4% share = $1,131/1000h whole-grid = ~63% of v41's total regret) — Session 56's highest-leverage target.
