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

3. **MASTER_HANDOFF_XX.md** — APPEND session log entry

4. **DECISIONS_LOG.md** — APPEND any non-trivial decisions

5. **checklist.md** — Check off `[x]` completed tasks

6. **SPRINT_INDEX.md** — Update if sprint status changed

## Final Confirmation

After updating ALL files:
1. Confirm all documentation is updated
2. Provide the resume prompt from CURRENT_PHASE.md
3. State what the next session should focus on

---

*This file is a static template. Do not modify it.*
