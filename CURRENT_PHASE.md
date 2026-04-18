# Current: Sprint 3 — Production launch pending (USER-LAUNCHED ON CLOUD)

> Updated: 2026-04-18 (end of Session 06)
> Previous sprint status: Sprint 2b complete, bug fixes applied, diagnostic re-validated, pilot running. Mac-Mini production is OFF the table (user veto); cloud launch awaits user.

---

## What Was Completed This Session (Session 06)

### Bug fixes (Claude Desktop approved, Decisions 025 + 026)

- **Bug 1 fix** — pair-preserving top-card selection in MFNaive + MFSuitAware via new `pick_top_from_rem5` helper. Routes `build_setting_mid_then_top` and `candidate_bot_after_top` through the helper.
- **Bug 3 fix** — OmahaFirst top = highest-rank of the 3 cards not in the bot (was leftover-of-mid-selection, which produced deuce-on-top absurdities).
- **Bug 4 deferred** (TopDefensive trip-split kept as archetype eccentricity).
- **BalancedHeuristic dropped** from production panel (Bug 2, Decision 021) — kept in codebase for audit reproducibility.

### Tests

- 5 new unit tests added (MFNaive KK preservation, MFSuitAware KK preservation, TopDefensive AAKK redux, OmahaFirst highest-of-rem3 + stress variant).
- **124 tests passing**, 0 failures (119 pre-session + 5 new).

### Empirical validation

- **Stress-test audit** via `show-opp-picks` on 7 stress hands: all 4 production models produce archetype-correct settings. Output saved to `data/session06/stress_audit_postfix.log`.
- **5K-hand post-fix diagnostic** (1389 s wall):
  - All-7 agree: 11.9% → **14.4%** (as expected — Bug 3 fix reduces OmahaFirst's isolation).
  - OmahaFirst vs Hold'em-centric models: 17-19% → **29-36%** (~2× increase — Bug 3 empirically validated).
  - MFNaive↔MFSuitAware: 88.4% → 89.0% (~same — expected because both got identical fix).
  - No pair ≥ 95% — 4-model P2-alt panel remains fully justified; no cluster collapse.
- Output: `data/session06/diagnostic_5k_postfix.log` + `diagnostic_5k_postfix.json` (JSON gitignored).

### Cloud production plan (new this session — user pivoted from Mac Mini)

- **User vetoed** the 10-day Mac Mini production plan mid-session; asked for cloud alternative.
- After two Socratic rounds with **Gemini 3 Pro** via PAL MCP, top 3 cloud providers finalized:
  - **#1 DigitalOcean** — simplest UI, $200 signup credit (covers job), needs quota-bump ticket for 48-vCPU.
  - **#2 RunPod** — prepaid model bypasses fraud filters, ~$17 total, starts in 10 minutes. **Recommended.**
  - **#3 GCP** — $300 credit covers job, fastest machine (112 vCPU, ~1.7 days wall), but quota review bureaucracy is real.
- **GPU rejected** — workload is branchy integer code + lookup-table memory-bound; months of CUDA rewrite for ≤5× speedup is not rational.
- **Sub-24-hour variants** documented for each provider.
- **CLOUD_PRODUCTION_GUIDE.md** at repo root has full click-by-click for all 3 options.

### Pilot (running in background at session end)

- Launched at 23:34 via `scripts/pilot_all_models.sh` (job ID `butlu0ted`).
- 50K canonical hands × 4 models × N=1000.
- Expected wall ~2 hours. User will wake up after completion.
- Outputs: `data/pilot/*.bin` (gitignored).

---

## Current State — READY FOR CLOUD LAUNCH

Mac Mini production is **NOT running** and will NOT run. All production work happens on cloud per CLOUD_PRODUCTION_GUIDE.md.

Repo state:
- All bug fixes committed + pushed to `github.com/mcoski8/tw` (main branch).
- Cloud guide pushed with the same commit so the user can read it from any browser.
- Pilot is the ONLY compute still running locally and is independent of the cloud launch.

---

## Blockers / Issues

None. All work is either complete or user-gated (cloud launch).

---

## Files touched this session

**Modified:**
- `engine/src/opp_models.rs` — Bug 1 + Bug 3 fixes + 5 new tests
- `DECISIONS_LOG.md` — Decisions 025 (Bug 1 fix) + 026 (Bug 3 fix) appended
- `checklist.md` — Sprint 2b items checked off; production marked cloud-pending
- `.gitignore` — added `data/pilot/`, `data/*.json`, `data/session*/*.json`
- `handoff/MASTER_HANDOFF_01.md` — Session 06 entry appended
- `CURRENT_PHASE.md` — this file, fully rewritten

**New:**
- `scripts/pilot_all_models.sh` — pilot runner (50K × 4 models)
- `scripts/production_all_models.sh` — production runner (usable on cloud too)
- `CLOUD_PRODUCTION_GUIDE.md` — 3-option cloud launch guide (Socratic-tested with Gemini 3 Pro)
- `data/session06/stress_audit_postfix.log` — 7 stress hands × 7 models output
- `data/session06/diagnostic_5k_postfix.log` — full diagnostic text summary
- `data/session06/diagnostic_5k_postfix.json` — diagnostic JSON (gitignored)

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md`

---

## Resume Prompt (next session — after user runs cloud production)

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- DECISIONS_LOG.md  (scan 017-026 for Sprint 2b + Sprint 3 context)
- handoff/MASTER_HANDOFF_01.md  (scan Session 06)
- CLOUD_PRODUCTION_GUIDE.md   (in case user ran production on cloud)

Session 06 applied Bug 1 + Bug 3 fixes (pair-preserving top in MF-family,
OmahaFirst top=highest-of-rem3). 124 tests green. Stress audit + 5K
re-diagnostic validated the fixes empirically (OmahaFirst agreement with
Hold'em-centric ~2× up; all-7 agree 11.9%→14.4%; no cluster collapse).

Pilot of 50K × 4 models × N=1000 ran at session close (2026-04-18 ~23:34
launch). Results in data/pilot/*.bin + data/session06/pilot_*.log. User
was asleep; pilot validation should be checked at session start.

User PIVOTED from Mac Mini production to CLOUD mid-session. They wanted
a non-technical first-time cloud guide with sub-24-hour options at
nominal fee, no GPU. After Socratic with Gemini 3 Pro via PAL MCP, the
top 3 in CLOUD_PRODUCTION_GUIDE.md are DigitalOcean, RunPod, GCP.

First-session-start tasks:
1. Check pilot output (data/pilot/{mfsuitaware_mixed90,omahafirst_mixed90,
   topdefensive_mixed90,randomweighted}.bin). Each should be ~450 KB
   (32-byte header + 9 × 50,000 records). Header tags should match
   model specs (1002090, 1003090, 1004090, 6 respectively).
2. Spot-check 10-20 pilot records against known-correct hand settings.
3. Ask user whether they've kicked off the cloud run. If yes, how's it
   going (any errors, any pods stuck)? If not, walk them through
   CLOUD_PRODUCTION_GUIDE.md.
4. Once user has all 4 best_response/*.bin files back on the Mac (from
   cloud download or Mac run), Sprint 7 analysis unlocks.

Do NOT launch Mac Mini production. User has vetoed that path.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
