# Session End Prompt

> **Usage:** Copy everything below the line and paste it to Claude Code when you're ready to end a session.

---

Before ending this session, complete the following pre-flight checks and documentation updates:

## Pre-Flight Checklist

Verify these BEFORE updating docs:
1. **Build check** — Run `cd engine && cargo build --release` and confirm no errors
2. **Test check** — Run `cargo test` and confirm all tests pass
3. **Uncommitted changes** — Check `git status`, commit if needed

## Documentation Updates

Once pre-flight passes, update these files:

1. **Active sprint file** (e.g., `docs/sprints/s0-foundation.md`):
   - Update task statuses in the task table
   - Add a session log entry with: date, what was completed (with file paths), decisions made, gotchas encountered

2. **CURRENT_PHASE.md** — REWRITE entirely (do not append):
   - Current sprint name and status
   - What was completed this session
   - What's in progress / not started
   - Blockers, gotchas, lessons learned
   - Immediate next actions
   - Ready-to-paste resume prompt

3. **STRATEGY_GUIDE.md** — MIXED update mode. **READ THE STRUCTURE NOTE AT THE TOP OF THE FILE FIRST** (lines ~7-15) before editing. The file is divided into 6 parts with different update conventions:
   - **Part 1 (Strategy Evolution) — APPEND-ONLY.** Add a new `## Session NN: <one-line title>` section at the END of Part 1 (right before the `# Part 2` divider) summarizing this session's strategy-relevant work. Match the format of the most recent existing session entry: bold-titled paragraphs, per-category numbers, a `**Score: $X/1000h on full grid. Improvement: −$Y vs v16, −$Z vs v14.**` line near the end, and a `**Methodology lesson —**` takeaway. Do NOT edit prior session entries.
   - **Parts 2–6 — UPDATE IN PLACE.** Refresh tables, file pointers, and "current standard" text to reflect the latest champion. The "Last updated" line in the front matter must reflect this session.
   - Skip Part 1 if this session did NOT change the strategy of record (e.g., a pure bug fix or doc-only session). State so explicitly in the commit message.

4. **MASTER_HANDOFF_XX.md** — APPEND session log entry

5. **DECISIONS_LOG.md** — APPEND any non-trivial decisions

6. **checklist.md** — Check off `[x]` completed tasks

7. **SPRINT_INDEX.md** — Update if sprint status changed

## Final Confirmation

After updating ALL files:
1. Confirm all documentation is updated
2. Provide the resume prompt from CURRENT_PHASE.md
3. State what the next session should focus on

---

*This file is a static template. Do not modify it.*
