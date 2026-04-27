# Resume the Taiwanese Poker project

If you're starting a new Claude Code session here, just paste this:

> Resume the project. Read CLAUDE.md, CURRENT_PHASE.md, and the latest entries in DECISIONS_LOG.md (031, 032). Then follow the IMMEDIATE NEXT ACTION at the top of CURRENT_PHASE.md.

That's it. CURRENT_PHASE.md has the full state, the methodology agreed with Gemini, and the resume prompt with all carry-forward.

---

## Quick context (Session 16 starts here)

- Last session was Session 15 (Sprint 7 Phase C/C+).
- Production rule chain `strategy_v3` is at 56.16% multiway-robust shape-agreement on full 6M canonical hands.
- Per-profile overlays shipped (omaha 54.69% on br_omaha, topdef 50.14% on br_topdef).
- All 74 python tests + 124 rust tests green at session close.
- 4 commits pushed to origin/main: d5ed9ff, a5df1d8, 5a815ce, c8ea4fc.

## Immediate next action

Run from project root:
```
python3 analysis/scripts/dt_phase1.py
```

This is the Phase D ceiling-curve experiment — sklearn DecisionTreeClassifier at depths {3, 5, 7, 10, 15, 20, None} on (27 hand_features, multiway_robust setting_index), scored by shape-equivalence. The depth=None tree is the empirical ceiling for our feature set; it determines whether the 95% target is reachable.

Should run ~3-8 minutes and print a 7-row depth-vs-agreement table. Paste the table into the Claude Code session and Phase D step 2 (rule extraction → byte-identical parity check → EV-loss backtest) follows.

## If permissions break again

Mid-Session-15 we hit a transient macOS TCC bug after a SIGKILL'd Python child poisoned the kernel permission cache. Symptom: `PermissionError: [Errno 1] Operation not permitted` on any file under this directory.

Fix: System Settings → Privacy & Security → App Management → ensure python3.13 + Terminal toggles are ON, then **Cmd+Q Terminal completely** and reopen. Permissions return to fresh.
