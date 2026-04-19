# Current: Sprint 3 — Cloud production RUNNING on RunPod

> Updated: 2026-04-19 (end of Session 07)
> Previous sprint status: Bug fixes + pilot validated in Session 06; cloud launch was user-gated. Session 07 pivoted the guide to overspend-safety ranking and got the user actually running on cloud.

---

## What Was Completed This Session (Session 07)

### Cloud production guide rewrite

- User surfaced concern that "hourly pricing" might be a monthly subscription. Rewrote `CLOUD_PRODUCTION_GUIDE.md` entirely:
  - New upfront callout: **none of the 3 options are monthly commitments** — metered billing, destroy = stops.
  - Re-ranked by **overspend-safety** rather than raw cost/speed:
    - **#1 RunPod** — strictly prepaid, deposit is a hard physical cap. No credit-card auto-charging.
    - **#2 GCP** — $300 free-trial credit as hard cap; per-second billing; expanded section explains SUDs (auto) vs CUDs (commitment — avoid).
    - **#3 DigitalOcean** — $200 credit + per-second billing (since Jan 2026) + monthly price cap as safety net.
  - Dropped Hetzner entirely per user preference; added Google Cloud per-usage pricing section.
  - Updated pricing: verified April 2026 via web search (RunPod $0.96/hr 32-vCPU, GCP `c2d-highcpu-112` ~$4.22/hr, DO monthly cap for 48-vCPU).
  - Added billing-alert steps for DO + GCP.
  - Added explicit "don't click Reserved / Savings Plan / CUD" warnings on every provider.

### Script portability fixes (critical — scripts were Mac-only)

- `scripts/production_all_models.sh` + `scripts/pilot_all_models.sh` had two fatal macOS-isms:
  - Hardcoded `PROJ="/Users/michaelchang/Documents/claudecode/taiwanese"` — doesn't exist on Linux.
  - `/usr/bin/time -l` — `-l` is BSD-only; Linux GNU time doesn't accept it.
- Both files now use portable `PROJ="$(cd "$(dirname "$0")/.." && pwd)"` and call the engine binary directly (no `/usr/bin/time` prefix).
- Decision 027 appended to `DECISIONS_LOG.md` covering this fix.

### RunPod cloud production — LAUNCHED and RUNNING

User completed the full RunPod onboarding flow with click-by-click guidance. Current state:

- **Pod ID**: `0f8279f6fd0a`
- **Region**: `US-GA-2` (first attempt `US-TX-3` had no 32-vCPU capacity — network volume had to be re-created in GA region)
- **Hardware**: 3 GHz Compute-Optimized, 32 vCPU, 64 GB RAM @ $0.96/hr
- **Storage**: Network volume `tw-solver-data` (20 GB, persistent — survives pod termination) mounted at `/workspace`; container disk 20 GB
- **Balance**: $120 prepaid + auto-refill $25 when below $10
- **Launch time**: 2026-04-19 19:16:28 UTC
- **First model running**: `mfsuitaware_mixed90` (PID 2009 on the pod at launch)
- **Expected wall-clock**: ~4.9 days sequential for all 4 models

User can close the browser tab; `nohup` keeps the job alive.

### Session gotchas worth remembering

- **Web terminal mangles large heredoc pastes.** First attempt to create `production_cloud.sh` via `cat > ... <<'EOF'` hung in heredoc mode with line-joined/whitespace-stripped content. Fallback: two `sed -i` in-place patches on the original script worked cleanly. For future non-technical cloud walkthroughs, prefer `sed` over heredocs for long content.
- **Markdown code fences (```` ``` ````) get copied with the commands** when users select an entire code block visually. First install attempt pasted the fences and bash interpreted them as command substitution, silently swallowing the whole script. Always remind non-technical users to copy only the lines *between* the fences.
- **RunPod capacity is region-sensitive.** User's first choice (US-TX-3) had no 32-vCPU available; had to delete the tw-solver-data network volume and re-create it in US-GA-2. Volume region is locked to pod region.
- **Auto-refill softens the "prepaid hard cap" guarantee.** With auto-refill enabled, deposit is no longer the absolute ceiling — noted in the guide. User consciously chose it for safety-net over strict-cap.

---

## Current State — CLOUD PRODUCTION RUNNING

Next action is monitoring + download, not launching anything else. Repo state:

- All fixes committed + pushed (will be true after this session's commit).
- Mac Mini production remains vetoed. Cloud is the only production path.
- Pilot from Session 06 remains intact at `data/pilot/` for spot-check reference.

---

## Blockers / Issues

None. Job is running on cloud; user is free to disconnect.

---

## Files touched this session

**Modified:**
- `CLOUD_PRODUCTION_GUIDE.md` — full rewrite: overspend-safety ranking, RunPod #1, expanded GCP per-usage section, Hetzner removed
- `scripts/production_all_models.sh` — portable `PROJ` via `dirname`; removed `/usr/bin/time -l`
- `scripts/pilot_all_models.sh` — same two fixes
- `DECISIONS_LOG.md` — Decision 027 appended
- `handoff/MASTER_HANDOFF_01.md` — Session 07 entry appended
- `CURRENT_PHASE.md` — this file, fully rewritten

---

## Active Handoff File

`handoff/MASTER_HANDOFF_01.md`

---

## Resume Prompt (next session)

```
Read these files for context:
- CLAUDE.md
- CURRENT_PHASE.md
- modules/game-rules.md   (MANDATORY)
- DECISIONS_LOG.md  (scan 025-027 for Sprint 2b/3 context)
- handoff/MASTER_HANDOFF_01.md  (scan Session 07)
- CLOUD_PRODUCTION_GUIDE.md   (in case user asks about re-running)

Session 07 pivoted CLOUD_PRODUCTION_GUIDE.md to an overspend-safety
ranking (RunPod #1 prepaid, GCP #2 $300 credit, DO #3 signup credit).
Also fixed Mac-only bugs in scripts/production_all_models.sh and
scripts/pilot_all_models.sh (hardcoded PROJ path, /usr/bin/time -l).

User launched RunPod cloud production at 2026-04-19 19:16:28 UTC:
- Pod 0f8279f6fd0a, region US-GA-2
- 32 vCPU / 64 GB @ $0.96/hr
- Network volume tw-solver-data (20 GB) mounted at /workspace
- Balance $120 + auto-refill $25 at $10
- Expected wall ~4.9 days for all 4 models sequentially
- First model mfsuitaware_mixed90 running (PID 2009 at launch)

First-session-start tasks:
1. Ask user the pod status. Monitor via RunPod web terminal:
   cd /workspace/tw
   tail -15 data/session06/production_launch.log
   for f in data/session06/prod_*.log; do echo "=== $f ==="; tail -3 "$f"; done
   pgrep -af "tw-engine solve" || echo "Job stopped."
2. If any prod_*.bin files are complete in /workspace/tw/data/best_response/,
   walk the user through scp or Jupyter download to
   /Users/michaelchang/Documents/claudecode/taiwanese/data/best_response_cloud/.
3. If job has crashed mid-run, resume with same command — append-only .bin
   writer continues from last flushed block.
4. After all 4 .bin files are on the Mac, Sprint 7 analysis unlocks.
5. Remind user to TERMINATE (not just Stop) the pod once downloads finish.

Do NOT launch Mac Mini production. User has vetoed that path.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
