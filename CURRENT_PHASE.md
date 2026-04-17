# Current: Sprint 3 — Best Response Computation | IN PROGRESS (production run pending)

> Updated: 2026-04-17
> Previous sprint: S2 Monte Carlo Engine — **COMPLETED**
> Active session: 04 (this one) — pipeline built and validated end-to-end; production run NOT yet started.

---

## What Was Completed Last Session (2026-04-17, Session 04)

The complete Sprint 3 pipeline is built, tested, and validated end-to-end on a 10K-hand pilot at production sample count. Only the multi-day production run itself is left.

### New code

- `engine/src/bucketing.rs` (NEW) — suit canonicalization (Decision 006).
  - `canonicalize`, `is_canonical`, `enumerate_canonical_hands`, `count_canonical_hands` (rayon-parallel).
  - File I/O: `write_canonical_hands`, `read_canonical_hands` ("TWCH" magic + version + count + 7-byte records).
  - 9 unit tests including round-trip across all 24 suit permutations and a closed-subset enumeration check.
- `engine/src/best_response.rs` (NEW) — per-hand best-response computation + checkpointed binary output.
  - `BestResponseRecord` (9 bytes: u32 canonical_id, u8 setting_index, f32 ev).
  - `BrHeader` (32 bytes: "TWBR" magic, version, samples, base_seed, canonical_total, opp_model_tag).
  - `BrWriter::open_or_create` — append-only with crash-safe resume (offset = (filesize − 32) / 9).
  - `solve_one`, `solve_range` — outer-parallel rayon over canonical hands, serial `mc_evaluate_all_settings` inside (Decision 017).
  - 6 unit tests: record/header round-trip, writer create / resume / mismatch / truncated handling, end-to-end `solve_one`.
- `engine/src/lib.rs` — registered modules + re-exports.
- `engine/src/main.rs` — three new CLI subcommands:
  - `enumerate-canonical [--count-only] [--out PATH]`
  - `solve --canonical PATH --out PATH --samples N --seed S [--block-size B] [--limit L]`
  - `spot-check --canonical PATH --out PATH [--show N]`
- `engine/Cargo.toml` — `tempfile = "3"` as dev-dep for writer tests.

### Test totals: 105 tests, 0 failures (Sprint 2: 90 → +15 new).

### Empirical findings

**Canonical hand count = 6,009,159** (ratio 22.26× vs C(52,7) = 133,784,560).
Cross-checked against Burnside's lemma over S₄ — exact match:
- Identity: 133,784,560 fixed
- 6 transpositions × 1,723,176 fixed each = 10,339,056
- 3 double-transpositions × 0 fixed = 0 (parity blocks 7-card 2:2:n:m splits)
- 8 three-cycles × 12,025 fixed each = 96,200
- 6 four-cycles × 0 fixed = 0 (parity blocks even distribution of 7)
- Sum / 24 = 6,009,159 ✓

**Throughput at N=1000 (M-class Mac, release build, full rayon):**

| Run | Hands | Wall time | Per-hand | Notes |
|-----|-------|-----------|----------|-------|
| Pilot — N=100, 1K hands | 1,000 | 3.8 s | 3.8 ms | sanity-only |
| **Extended pilot — N=1000, 10K hands** | **10,000** | **373.3 s** | **37.3 ms** | **production cadence** |
| **Projected production — N=1000, 6.01M hands** | **6,009,159** | **~62.3 hr ≈ 2.6 days** | 37.3 ms | within 1-week target |

CPU usage during extended pilot: 3,366 s user / 373 s real = **9.0× parallel speedup**, 57 MB peak RSS.

### Spot-check results (six representative hands at N=1000 parallel)

| Hand | Best setting | EV | Sense |
|------|--------------|------|-------|
| Quad aces (AAAA + 2-3-4) | `2c \| AA \| AA34` | +3.53 | Splits aces 2/2 across mid+bot, junk top |
| Royal hole + 9-8 (AhKhQhJhTh + 9d 8c) | `Kh \| AhJh \| QhTh9d8c` | +3.13 | Suited broadway in mid, connectors in bot |
| Wheel + T9 (Ah2c3d4h5s + 9c Tc) | `Tc \| Ah4h \| 9c5s3d2c` | +0.16 | Marginal, ace stays in mid for Hold'em |
| AAKK + 7-4-2 | `7c \| KK \| AA42` | +4.96 | Classic AAKK pattern, premium hand |
| Rainbow gappers (2-4-6-8-T-Q-A) | `Qd \| Ac2c \| Th8s6h4d` | +1.98 | Suited Ac2c → mid; spread → bot |
| Trip kings + 88 (KKK 88 5 2) | `Kc \| 88 \| KK52` | +4.43 | Pocket KK → bottom (3pt weight) |

All settings agree with research findings (top card J+ ideal where possible, premium pair to bot for 3pt scoring weight, suited cards to mid for flush draws).

### Files produced

- `data/canonical_hands.bin` (42 MB, gitignored) — 6,009,159 sorted-ascending 7-card byte arrays.
- `data/best_response_pilot.bin` (8.8 KB) — N=100 over first 1000 canonical hands.
- `data/best_response_extpilot.bin` (88 KB) — N=1000 over first 10K canonical hands.

---

## What's Currently In Progress

**The full production run has NOT been kicked off.** Code, file formats, checkpoint/resume, parallelism, and spot-checks are all validated. The blocking decision is whether to dedicate the M-class machine to a 2.6-day background run; that's a user call and not safe to start unattended.

---

## What's Not Started Yet

- [ ] Production run: N=1000 samples on all 6,009,159 canonical hands. Est. 62 hours.
- [ ] Final summary statistics over the full output (EV distribution, setting-frequency histogram).
- [ ] (Sprint 4) Pattern mining + decision-tree extraction begins consuming this output.

---

## Blockers / Issues

**None blocking.** Items to be aware of:

1. **Production launch is a user gate.** Run-to-completion is ~2.6 days, ~9 cores pinned, ~0% disk I/O after warmup, ~57 MB RSS. Not destructive, but a meaningful resource commitment for a personal machine. See the launch recipe below.
2. **Single-pass at N=1000 (Decision 017).** Sprint plan called for an adaptive 3-pass scheme (quick scan → precision → final resolution) plus 25-of-105 setting pre-screening. The user's resume prompt simplified this to a single pass at N=1000 with no pre-screening. We followed the simplified path — projected runtime is well within the 1-week target so adaptive multi-pass would be premature. Adaptive can be re-introduced in a Sprint 3.5 if Sprint 4 reveals decision boundaries that need higher per-hand precision.
3. **Outer parallel / inner serial.** Per sprint prompt #5: rayon parallelizes the OUTER loop over canonical hands; the INNER `mc_evaluate_all_settings` runs serially inside each worker. Confirmed empirically: 9.0× speedup with 9–10 cores, no scheduler thrash. Trying to nest the inner parallel kernel would degrade throughput.

---

## Immediate Next Actions

### Launch the production run

From the project root:

```bash
cd engine
nohup ./target/release/tw-engine solve \
  --samples 1000 \
  --seed 12648430 \
  --block-size 5000 \
  --out ../data/best_response.bin \
  > ../data/best_response.log 2>&1 &
echo $! > ../data/best_response.pid
```

- Output stream: `data/best_response.log` — one line per block (5K hands ≈ 3 minutes), with ETA.
- Resume: just rerun the same command. The writer reads the existing file's record count and picks up at the next canonical_id. Header mismatch on `--samples` or `--seed` will refuse to append (safety).
- Stop cleanly: `kill $(cat ../data/best_response.pid)`. Records are flushed per block (every 5K hands), so at most one block of work is repeated on restart.
- Check progress mid-run:
  ```bash
  ./target/release/tw-engine spot-check \
    --out ../data/best_response.bin --show 5
  ```
  Will print header, current record count, sample records, EV distribution, and the top-10 most-frequent setting indices over what's been written so far.

### After production completes

1. Run a final `spot-check --show 50` for a global sanity glance.
2. Sample ~100 canonical hands at random, re-solve at N=10K via `mc`, and compare best-setting agreement (target ≥ 95%).
3. Hand off to Sprint 4: bucketing + CFR will consume `data/best_response.bin` + `data/canonical_hands.bin`.

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md`

---

## Resume Prompt

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- sprints/s3-best-response.md
- DECISIONS_LOG.md   (scan 006, 015, 017)

Sprint 3 pipeline is built and validated end-to-end (105 tests pass; 6,009,159
canonical hands enumerated; extended pilot at N=1000 × 10K hands hit 37.3 ms/hand
with 9× parallel speedup; six spot-checks all agree with research findings).
Production run was NOT started in the previous session.

Your job:
  1. Confirm whether to launch the production run now. Recipe is in
     CURRENT_PHASE.md → "Launch the production run". Total wall time ~2.6 days,
     ~9 cores, 57 MB RSS, fully resumable.
  2. While the run is in flight (or after it completes), draft the Sprint 4
     plan: pattern mining + bucketing + CFR over the best-response output.
     Update sprints/s4-bucketing-cfr.md with concrete first tasks.
  3. After the production file is complete, do a final agreement check:
     sample 100 random canonical hands, re-solve each at N=10000 via the `mc`
     subcommand, and confirm best-setting agreement is ≥ 95%.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
