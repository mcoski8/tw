# Current: Sprint 8 — Full Oracle Grid + Query Harness. Methodology pivot from heuristic mining. Session 23 closed.

> **🔥 IMMEDIATE NEXT ACTION (Session 24):** Build `mfsuit_top_locked` opponent profile in `engine/src/opp_models.rs`, define the 70/25/5 mixture profile (locked / topdef / omaha), implement suit canonicalization to reduce 133M deals → ~20M canonical hands, kick off the full Oracle Grid compute (estimated 12-30h overnight). Build the Query Harness scaffolding in parallel while compute runs.

> **🚫 RETIRED (Decision 043, Session 23):** Heuristic mining as the primary track. v9 pair-to-bot rule, v9' DT-distillation, v9-trips-broadway-top-routing — all paused (not deleted). v8_hybrid remains the production champion as a baseline reference; further heuristic improvements will be DERIVED from the Oracle Grid, not mined from intuition.

> **🚫 REJECTED (Decision 043, Session 23):** CFR + bucketed Nash equilibrium. Considered + dialogued with Gemini; verdict was that Nash is overkill for the user's actual goal (max EV vs realistic humans, not unexploitable-by-Nash-bot). CFR is misaligned with the simultaneous-move structure of this game (no betting rounds, single setting decision per hand).

> **✅ NEW APPROACH (Decision 043, Session 23):** Brute-force the **Full Oracle Grid** at canonical-hand scale (~20M hands × 105 settings × 1 realistic-human mixture profile), then build a **Query Harness** that lets the user pose poker-domain questions directly to the data (e.g., "double-suited unconnected vs connected unsuited bot — which makes more money long-term?").

> Updated: 2026-05-01 (end of Session 23)

---

## Headline state at end of Session 23

**Methodology pivot.** After 7 sprints of heuristic mining, we are switching tracks to brute-force ground-truth computation + interactive query.

**v8_hybrid is still champion** (+$478/1000h vs v3 against the 4-profile mixture). It is NOT being removed. It serves as the current production strategy and the baseline-to-beat for whatever the Oracle Grid eventually distills into rules. No new v9 was built this session.

**Pre-test of v3 bleed zones produced.** Script `analysis/scripts/pretest_v3_bleed_zones.py` + persisted records `data/v3_bleed_zones.parquet`. Findings remain valid as discovery inputs to the Oracle Grid track.

**User's actual goal re-clarified:** "the best way to play this game" against real humans, not against an optimal Nash adversary. Rules are downstream — they emerge from the data once we have the data. The user is a winning Hold'em + Omaha player but not a statistician; he hired Claude Code to architect the system, not to hand him a menu of rule candidates.

---

## What was completed this session (Session 23)

### Step 1 — Pre-test of v3 bleed zones (`pretest_v3_bleed_zones.py`)

For every hand in the 50K oracle grid, computed `Δ_global = EV(oracle_argmax_mean) - EV(v3)` averaged across the 4 opponent profiles. Sorted descending, characterized the top-5% slice.

Headline numbers:
- Total v3-vs-oracle gap: **$1,420.9/1000h** (matches the leaderboard ceiling — sanity check passes).
- v3 == oracle on **59% of hands** (already optimal).
- Top-5% of hands hold **34%** of all dollars left on the table; top-10% hold **54%**.
- v8_hybrid captures $478 of $1,420 = **34% of headroom**. **$942/1000h remains on the table.**

Bleed by hand category:

| Category | population | $/1000h (mean) | share of total bleed |
|----------|-----------|----------------|----------------------|
| **high_only** | 21% | $2,190 | **33%** |
| pair | 47% | $688 | 23% |
| two_pair | 22% | $1,103 | 17% |
| **trips** | 5% | $4,411 | **16%** |
| **trips_pair** | 2.5% | $5,198 | 9% |
| three_pair | 1.9% | $1,379 | 2% |
| quads | 0.2% | $4,533 | 0.5% |

Trap-zone hypothesis empirically confirmed: in the top-5% bleed slice, **58% are "trap zone" hands** (v3's mid choice locally looked fine, the cascade into bot is what bled).

The mechanism of the bleed: **67% of top-5% bleed involves v3 leaving a worse bot suit profile than oracle does**. Specifically: single_suited→double_suited (24%), rainbow→double_suited (19%), rainbow→single_suited (16%), 3-suited→double_suited (5%). v3 repeatedly breaks DS bots to satisfy its tier-greedy mid pick.

Top routing-change archetypes in the top-5% slice:
- trips14_2mid_1bot → trips14_2mid_1top (10.5% of top-5% bleed) — v3 puts an ace in bot when it should be on top
- trips13/12 versions of same archetype (5.6% + 2.0%)
- pair2/3/4/5_to_mid → pair_to_bot (combined 7%) — Session 22 finding fully reproduced

The pair-rank gradient is monotonic and clean:

| pair rank | % oracle → bot | v3 → bot |
|-----------|---------------|----------|
| 2 | 32% | 0% |
| 3-5 | ~24% | 0% |
| 6 | 16% | 0% |
| 7 | 8.6% | 0% |
| 8 | 5% | 0% |
| 9 | 3.9% | 0% |
| T-Q | <1.2% | 0% |
| K | 0% | 0% |
| **A** | **0.3%** | 0% |

**AA-to-mid is essentially universal (oracle agrees with v3 on AA-pair-routing 99.7% of the time).** When AA hands disagree (~20%), it's about top/bot composition, not pair routing.

### Step 2 — Methodology dialogue with Gemini (PAL MCP)

Three rounds of Socratic + direct dialogue with `gemini-3-pro-preview`. Topics:
- Whether the "30-second human-memorizable rules" target was premature compression.
- Whether "discover first, distill last" was a real new paradigm or retroactive narrative.
- The trap-zone hypothesis (small Δ_local + large Δ_global) refinement.
- Methodology choice: CFR vs full-grid brute-force.

**Final verdict (Gemini, direct):** "CFR is the wrong mathematical tool for his specific goal." Nash equilibrium is defensive against optimal adversaries; humans have huge exploitable leaks. Best response to a realistic-human distribution is what maximizes win rate. Plus this game is simultaneous-move (no betting rounds) so CFR isn't even the standard tool — Fictitious Play / pure BR to a population is.

### Step 3 — User's empirical observation about real-human play

User provided the opponent-profile spec from his actual playing population:
- **Most players use mfsuit-style with top defense.**
- **Pair of Q's or K's is NEVER broken up** — kept together, almost always placed in MID (rare exceptions: extreme bot opportunities).
- **Ace singleton always goes on top.**
- **No Ace? Player optimizes Omaha bot first; top gets the leftover.**
- AA-to-bot: extremely rare, only when DS + decent pair available for top tier.
- Full top/mid sacrifice (e.g., 3 on top + 5s2s in mid for KKJT-DS bot): extremely rare, ~5% of population at most.

This rules out the existing `mfsuitaware` profile as a stand-in: it doesn't enforce the "high pair stays together in mid" or "Ace always to top" constraints, so its EV outputs would simulate phantom opponent behavior the user's actual humans don't exhibit.

### Step 4 — Mixture decision (Session 24 spec)

**Final mixture: 70% `mfsuit_top_locked` + 25% `topdef` + 5% `omaha`.**

Rationale:
- 70% locked = the dominant style with the high-pair + Ace-to-top hard rules.
- 25% topdef = real humans' strong top-defense tendency.
- 5% omaha = capture the rare full-sacrifice player; without this tail the Oracle would assume the bot is always weak.

Single-column grid (one mixture profile, not multi-column). Get answers in 12-30h instead of 36-90h. Multi-column diagnostics can be re-run later if a rule is suspected of being mixture-specific.

### Step 5 — Documentation pivot

This file (CURRENT_PHASE.md) rewritten. Decision 043 appended to DECISIONS_LOG.md. Session 23 entry appended to MASTER_HANDOFF_01.md. New script `analysis/scripts/pretest_v3_bleed_zones.py` committed.

---

## Files added this session

- `analysis/scripts/pretest_v3_bleed_zones.py` — bleed-zone analysis + parquet emitter.
- `data/v3_bleed_zones.parquet` (gitignored) — 50K-hand per-hand records with v3 / oracle picks, bleed magnitude, routing changes, bot-suit-profile changes.

## Files modified this session

- `CURRENT_PHASE.md` — rewritten (this file).
- `DECISIONS_LOG.md` — appended Decision 043 (methodology pivot).
- `handoff/MASTER_HANDOFF_01.md` — appended Session 23 entry.

## Verified

- Rust: `cargo test --release` 124 / 124 pass.
- Python: 74 / 74 pass.

## Gotchas + lessons

- **Heuristic mining was a 7-sprint detour because the cheap path was always available.** Each session looked like progress (new rule, new EV gain) while the foundational solver track stayed deferred. The course-correction came from a user push: "you keep asking ME for the next rule — I hired you to build the system."
- **CFR is not always the right answer to "build the optimal solver."** For a vs-human game with simultaneous-move structure, best-response to a realistic population distribution is the right primitive. CFR's defensive Nash is overkill and may even underperform vs humans because it balances against threats they don't pose.
- **Domain calls genuinely need the user.** Encoding `mfsuit_top_locked` requires the user's "humans never break QQ/KK" observation; no amount of code-tracing produces that fact. Future sessions should ask poker-domain questions explicitly and reserve plumbing-verification for code-tracing.

---

## Resume Prompt (Session 24)

```
Resume Session 24 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md (rewritten end of Session 23)
- modules/game-rules.md (MANDATORY)
- DECISIONS_LOG.md (latest: Decision 043 — methodology pivot to Oracle Grid)
- handoff/MASTER_HANDOFF_01.md (Session 23 entry just added)
- engine/src/opp_models.rs (where the new mfsuit_top_locked profile goes)
- engine/src/bucketing.rs (partial suit-canonicalization scaffolding)
- engine/src/main.rs (CLI entry point)
- analysis/scripts/pretest_v3_bleed_zones.py (Session 23 reference)

State of the project (end of Session 23):
- Methodology pivoted from heuristic mining (Sprints 1-7) to full-grid brute-force +
  query harness. CFR considered and rejected.
- v8_hybrid (+$478/1000h vs v3) remains the production champion. No v9 was built.
- Pre-test confirmed: 67% of top-5% v3 bleed is bot suit-profile breakage. Trap-zone
  hypothesis (small local Δ, large global Δ) is empirically supported (58% of top-5%
  slice).
- AA-pair-to-mid is universal (99.7% per oracle). Pair-rank gradient is monotonic
  with inflection at pair-rank 7-8.
- 124 Rust + 74 Python tests pass.

User-confirmed opponent profile spec for the new mfsuit_top_locked:
- Pair of QQ or KK kept together AND placed in MID (never split, never to bot
  except in extremely rare circumstances).
- Ace singleton goes on top.
- No Ace? Player optimizes Omaha bot first; top gets the leftover.

User-confirmed mixture for the Oracle Grid: 70% mfsuit_top_locked + 25% topdef + 5% omaha.

IMMEDIATE NEXT ACTIONS (Session 24, ordered):

(1) Code mfsuit_top_locked in engine/src/opp_models.rs. Either:
    (a) New variant of OpponentModel enum + new strategy_for_profile branch in
        analysis/scripts/encode_rules.py, OR
    (b) Wrapper that calls mfsuitaware then post-processes to enforce the
        QQ+/Ace constraints.
    Choice (a) is cleaner; (b) is faster. Defer the (a)-vs-(b) call to your
    judgement after seeing the existing opp_models.rs structure.

(2) Define the mixture profile. Per-MC-sample, draw which sub-profile the
    opponent uses (0.70 / 0.25 / 0.05 weighted). Add this as either a
    composite OpponentModel or a sampling helper that wraps an existing one.

(3) Suit canonicalization. engine/src/bucketing.rs has partial scaffolding —
    review it, finish if usable, build fresh if not. Goal: collapse the
    133M unique 7-card hands to ~15-25M canonical equivalence classes via
    suit-permutation invariance. Add tests verifying canonical output is
    suit-invariant.

(4) Full Oracle Grid compute kickoff:
    - Iterate over all canonical hands.
    - For each, compute EV per setting (105 values) against the
      70/25/5 mixture profile, N MC samples per setting.
    - Persist to disk as oracle_grid_full_realistic.{npz, parquet, or .bin —
      pick based on file size; estimated 6-15GB).
    - Estimated 12-30h on the user's Mac (16+ cores, rayon parallelism).
    - Run as background process via Bash run_in_background or as a
      cargo command. Decide based on resilience needs (checkpoint to disk
      every N hands so a crash doesn't lose all progress).

(5) Query Harness scaffolding (build in parallel while compute runs).
    Python module that loads the grid and exposes:
      query.compare(setting_filter_a, setting_filter_b, hand_filter=None)
        → ΔEV, frequency, significance, sample hands
    Filter spec: high-level poker primitives — bot_suit_profile,
    bot_connectivity, has_pair_at_rank_K, has_singleton_at_rank_R,
    pair_position (top/mid/bot), etc.
    User's locked-in initial questions:
      - DS unconnected (e.g., 48JK-DS) vs connected unsuited (e.g., JT98) bot
      - DS unconnected vs single-suited connected (JsTd9s8c) bot
      - Generally favoring DS over connectivity?
      - When does pair-to-mid become a blunder for bot DS preservation?

(6) Validation metrics: report headline as EV per hand against the mixture
    profile (in dollars per 1000 hands at $10/EV-pt, matching the
    project convention). Include scoop rate and frequency-of-disagreement
    with v3/v8_hybrid for context.

REMINDERS:
- Auto mode is on; minimize interruptions. Make reasonable engineering
  judgement calls without pause-points unless they're poker-domain calls.
- Use python3, not python.
- venv at trainer/venv/ (or wherever it lives) — activate before running
  Python scripts.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol mandatory: commit + push to origin/main per
  session-end-prompt.md. Push is pre-authorized per persistent memory.

Open question to confirm with user once before kicking off the long compute:
- N MC samples per (hand, setting) cell? Project default is 1000. Higher
  N reduces noise; lower N speeds the run. 1000 is the right default;
  flag if a smaller pilot (N=200, 100K hands) before the full N=1000 run
  is preferred for sanity check.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
