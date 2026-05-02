# Current: Sprint 8 — Full Oracle Grid SHIPPED. Query Harness operational. Session 24 closed.

> **🎯 IMMEDIATE NEXT ACTION (Session 25):** Decide whether to (a) re-run Q2 at N=1000 on its 2.56M-hand subset for a tighter signal, (b) build the Strategy-Grading harness that scores any deterministic strategy function against the grid in seconds, or (c) investigate the Q4 B-wins cluster (906K hands where DS-bot-preservation beats pair-in-mid). User can also pose new poker-domain questions directly via `compare_setting_classes` against the grid.

> **✅ SHIPPED (Decision 044, Session 24):** `data/oracle_grid_full_realistic_n200.bin` — 2.55 GB, 6,009,159 canonical hands × 105 settings × N=200 MC samples vs the realistic 70/25/5 mixture. Compute wall: 12.37h on the M2 Mac. Integrity verified. Headline best-EV mean = +0.758/hand (player wins).

> **✅ SHIPPED:** Query Harness (`tw_analysis.query` + `tw_analysis.oracle_grid`) — vectorized per-setting feature extraction at ~115 µs/hand, filter primitives + combinators, `compare_setting_classes` for class-vs-class comparisons. ~10 min per question on the full 6M grid.

> Updated: 2026-05-02 (end of Session 24)

---

## Headline state at end of Session 24

**The methodology pivot from Session 23 has fully landed.** Heuristic mining is paused; the new substrate is the Full Oracle Grid + Query Harness. v8_hybrid remains the production strategy of record but is no longer the training target — strategies are now graded *against* the grid.

**Five user-locked questions answered on the full 6M-hand grid:**

| # | Comparison | A wins | B wins | mean Δ | $/1000h |
|---|---|---:|---:|---:|---:|
| Q1 | DS bot run≤2 vs rainbow bot run≥3 | 89.5% | 10.4% | +1.32 | **+$13,186** |
| Q2 | DS bot run≤2 vs SS bot run≥3 | 67.1% | 32.7% | +0.44 | **+$4,375** |
| Q3 | DS bot any vs rainbow bot any | 76.2% | 23.6% | +0.58 | **+$5,770** |
| Q4 | pair-in-mid + non-DS bot vs no-pair-mid + DS bot | 79.3% | 20.5% | +0.82 | **+$8,150** |
| Q5 | small pair (2-5) → mid vs small pair → bot | 81.2% | 18.6% | +0.79 | **+$7,922** |

**Interpretive headlines:**
- **Strong DS preference confirmed.** Across every connectivity comparison (Q1-Q3), DS bot beats rainbow / SS by clear margins. The user's intuition was right; we now have the dollar values.
- **Pair-to-mid usually beats DS preservation (Q4).** Breaking a pair to keep a DS bot is the wrong call ~80% of the time. But the 20.5% B-wins cluster (~906K hands) is a candidate for a "pair-to-mid blunder" rule.
- **Small pairs (2-5) belong in mid most of the time (Q5).** Session 22's "pair-to-bot fires 24-32% for low pairs" reframes as a minority play, not a rule. 81.2% of small-pair hands are best with the pair in mid.

---

## What was completed this session (Session 24)

### Step 1 — Implement the realistic-human profile + mixture (Rust)

Added to `engine/src/opp_models.rs`:
- `opp_mfsuit_top_locked(hand)` — Decision 043 deterministic profile.
  - Highest pocket pair from {AA, KK, QQ} → mid (AA > KK > QQ priority, supported by Session 23's "AA-pair-to-mid is essentially universal" finding).
  - Ace singleton in remaining 5 → top.
  - Otherwise: top via `pick_top_from_rem5` (TopDefensive-style highest singleton).
  - Fallback (no pair anchor + no ace): delegates to `opp_omaha_first`.
- 10 unit tests covering AA/KK/QQ priority, KK+QQ both, trips of kings, no-ace optimization branch, deterministic invariance.

Added to `engine/src/monte_carlo.rs`:
- `OpponentModel::MfsuitTopLocked` and `OpponentModel::RealisticHumanMixture` enum variants.
- Mixture dispatch inside `opp_pick`: per MC sample, draws 70% locked / 25% topdef / 5% omaha.

CLI in `engine/src/main.rs`:
- New `Opp::Locked` and `Opp::Realistic` choices, wired through `resolve_opp` and `opp_tag_from_model` (tag 7 = locked, tag 8 = mixture).

### Step 2 — Oracle Grid file format + writer (Rust)

New module `engine/src/oracle_grid.rs`:
- Magic `TWOG`, version 1, 32-byte header, 424-byte records (canonical_id u32 + 105 × f32 EVs in setting-index order — NOT sorted by EV).
- `OgWriter::open_or_create` mirrors `BrWriter`'s resume semantics. File header pinned to (samples, base_seed, canonical_total, opp_model_tag) — re-opening with mismatched parameters raises `HeaderMismatch`.
- `solve_grid_one` per-hand seed scheme `base_seed + canonical_id × 0x9E37_79B9_7F4A_7C15` (matches `best_response::solve_one` so grid + BR runs share their RNG stream definition).
- `solve_grid_range` is rayon-parallel over canonical hands inside a block, serial-MC inside each hand. Block-flush + fsync on each block.
- 7 unit tests including a parity test: `solve_grid_one`'s argmax over the 105 EVs must equal `mc_evaluate_all_settings::best.setting` at the same seed.

CLI command `oracle-grid` in `engine/src/main.rs`:
- Default opponent: `realistic` (mixture).
- Default output path: `data/oracle_grid_full_realistic.bin`.
- Resumes from existing file if header matches.
- Reports per-block throughput, ETA, and rate.

### Step 3 — Pilot run + harness validation (100K hands at N=200)

`data/pilot/oracle_grid_pilot_n200_100k.bin` — 13.8 min wall, ~120 hands/s.
Validated end-to-end with `analysis/scripts/oracle_grid_pilot_validate.py`. Q1-Q3 produced consistent signals with the full-grid run (relative deltas matched within MC noise).

### Step 4 — Full Oracle Grid compute (6M hands at N=200)

Kicked off via `tw-engine oracle-grid --canonical data/canonical_hands.bin --out data/oracle_grid_full_realistic_n200.bin --samples 200 --opponent realistic --block-size 1000`. Ran in background; user "left be" overnight.

Wall: **44,539s = 12.37 hours**. Steady throughput: 134.9 hands/s. Output: 2.55 GB, 6,009,159 records, integrity all green.

### Step 5 — Python Query Harness

New `analysis/src/tw_analysis/oracle_grid.py`:
- Reader (`load` or `memmap` mode), header parse, integrity validation, `decode_opp_tag` extension.

New `analysis/src/tw_analysis/query.py`:
- Vectorized `setting_features_from_bytes(hand_bytes)` — uses a precomputed (105, 7) `SETTING_HAND_INDICES` table to compute all per-(hand, setting) features in pure numpy. ~115 µs/hand.
- Per-setting features: top_rank, mid_pair_rank, mid_is_pair, bot_suit_profile (DS / SS / rainbow / 3+1 / 4-flush), bot_longest_run, bot_high_count, bot_pair_rank, bot_has_ace, top_is_ace.
- Filter primitives + combinators (`all_of`, `any_of`, `not_`).
- `compare_setting_classes(grid, ch, filter_a, filter_b, ...)` — scans all hands, picks max-EV setting in each filter class per hand, aggregates Δ.
- Reference Python-object path `setting_features_for_hand` retained as a slow oracle; sanity test confirms vectorized output is byte-identical on all 105 settings of a sample hand.

### Step 6 — Run the user's locked-in questions

`analysis/scripts/oracle_grid_full_queries.py` runs Q1-Q5 on the full grid. Wall: 53.4 min for all 5 questions (~10 min each). Results table above.

### Step 7 — Documentation pivot

- `CURRENT_PHASE.md` rewritten (this file).
- Decision 044 appended to `DECISIONS_LOG.md`.
- Session 24 entry to be appended to `handoff/MASTER_HANDOFF_01.md`.
- Memory: `project_taiwanese_oracle_grid.md` written; `MEMORY.md` index updated.

---

## Files added this session

- `engine/src/oracle_grid.rs` — new module + tests.
- `analysis/src/tw_analysis/oracle_grid.py` — grid file reader.
- `analysis/src/tw_analysis/query.py` — Query Harness.
- `analysis/scripts/oracle_grid_pilot_validate.py` — pilot validation.
- `analysis/scripts/oracle_grid_full_queries.py` — full-grid Q1-Q5 runner.
- `data/oracle_grid_full_realistic_n200.bin` (gitignored) — 2.55 GB grid.
- `data/oracle_grid_full_queries.log` (gitignored) — Q1-Q5 results.
- `data/pilot/oracle_grid_pilot_n200_100k.bin` (gitignored) — 42 MB pilot.

## Files modified this session

- `engine/src/opp_models.rs` — added `opp_mfsuit_top_locked` + 10 tests.
- `engine/src/monte_carlo.rs` — added `MfsuitTopLocked` and `RealisticHumanMixture` variants + dispatch.
- `engine/src/main.rs` — new `oracle-grid` subcommand + `Opp::Locked` and `Opp::Realistic` CLI options.
- `engine/src/lib.rs` — re-export `oracle_grid` module.

## Verified

- Rust: `cargo test --release` 141 / 141 pass (124 baseline + 10 locked-profile + 7 oracle-grid).
- Python: vectorized features parity-check vs Python-object reference: identical on all 105 settings of `As Kh Qd Jc Ts 9h 2d`.
- Grid integrity: `validate_oracle_grid` passes on 6,009,159 records (canonical_id ordering, finite EVs, plausible range, no zero-row writes).
- End-to-end CLI: pilot at N=200/100K and full at N=200/6M both completed without resume errors.

## Gotchas + lessons

- **Throughput model in CURRENT_PHASE.md was off.** Predicted 12-30h for N=1000; reality is 12.4h for N=200, ~62h for N=1000 (5×). Realistic mixture dispatch overhead is ~30% vs Random — `opp_pick` makes one extra RNG call per sample to draw the sub-profile. The "12-30h at N=1000" estimate didn't account for the new opponent's dispatch cost.
- **Python stdout buffering through `tee` hides progress.** First full-grid query run was killed because `print()` was buffered behind `tee`. Use `python3 -u` or `PYTHONUNBUFFERED=1` for any long-running script piped to a file.
- **Validation pass on a 2.5 GB memmap takes ~30s** to read the full file once. Acceptable but adds latency to harness startup. Future: skip validation in production query scripts after the first run.
- **Vectorizing per-hand features was non-optional.** Python-object enumeration (`decode_setting` × 105) at ~10 ms/hand × 6M = 16 hours per question. Numpy vectorization at ~115 µs/hand brings it to ~10 min. Pre-built `SETTING_HAND_INDICES` (105, 7) table is the key trick.
- **The "best EV across hands" metric doesn't average to zero** (it's +0.758) because the player gets to optimize per-hand against a fixed strategy, while the opponent applies the realistic mixture blind. The 100K-hand pilot's apparent -1.885 mean was lex-prefix bias (low canonical IDs are low-card hands).

---

## Resume Prompt (Session 25)

```
Resume Session 25 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 24)
- DECISIONS_LOG.md (latest: Decision 044 — Full Oracle Grid shipped)
- handoff/MASTER_HANDOFF_01.md (Session 24 entry just added)
- analysis/src/tw_analysis/oracle_grid.py
- analysis/src/tw_analysis/query.py
- analysis/scripts/oracle_grid_full_queries.py

State of the project (end of Session 24):
- Full Oracle Grid is shipped at data/oracle_grid_full_realistic_n200.bin
  (2.55 GB, 6,009,159 records × 105 EVs vs realistic 70/25/5 mixture).
- Query Harness operational; 5 headline questions answered.
- v8_hybrid is still the production deterministic strategy. Sprint 7's
  v9_X heuristic mining track remains paused; future strategies will
  derive from grid queries, not from intuition.
- 141 Rust + (74) Python tests pass.

Three reasonable Session 25 options (user's call):

(A) **Tighten Q2's signal at N=1000.** Q2 (DS-unconnected vs SS-connected
    bot) had the smallest mean Δ (+0.44) — close to the per-cell noise
    floor at N=200. Re-run a 100K-hand DS-unconn-vs-SS-connected subset
    at N=1000 to confirm. Cost: ~5h on the M2.

(B) **Build the Strategy-Grading harness.** A drop-in replacement for
    tournament_50k.py that grades any strategy(hand) → setting_index
    function against the full 6M-hand grid in seconds. This makes
    iterating on rules cheap and enables a "user proposes strategy →
    Gemini Socratic → grid validate" loop.

(C) **Investigate the Q4 B-wins cluster.** 906K hands where breaking a
    pair to preserve a DS bot is the EV-correct play. Pull those hands,
    characterize by features (rank profile, suit distribution, ace
    presence, hand category), see if a coherent "pair-to-mid is a
    blunder" archetype emerges. This was Decision 043's framing of "rules
    emerge from data, not intuition."

(D) **The user proposes a new poker-domain question.** Any "is X bot
    better than Y bot?" / "when does Z setting dominate?" comparison
    can be answered with `compare_setting_classes` against the grid in
    ~10 min. The Q4 B-wins canonical_ids
    (425562, 3546583, 3546584, 2965461, ...) are concrete starting points.

REMINDERS:
- Auto mode is on; minimize interruptions. Make reasonable engineering
  judgement calls without pause-points unless they're poker-domain calls.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol mandatory: commit + push to origin/main per
  session-end-prompt.md. Push is pre-authorized per persistent memory.
- The grid is large (2.55 GB) — load via memmap, not load mode, in
  scripts that don't need to mutate the data.
- For long Python scripts that pipe output, use python3 -u or
  PYTHONUNBUFFERED=1 (Session 24 lesson).
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
