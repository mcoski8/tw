# Current: Sprint 3 cloud production ~75% through; Sprint 5a trainer foundation complete; Sprint 7 cross-model tooling bootstrapped

> Updated: 2026-04-24 (end of Session 09)
> Previous sprint status: Session 08 landed the Python analysis stack (readers/decoders + byte-identical Rust parity). Session 09 built the Sprint 5a trainer + the Sprint 7 cross-model join scaffolding, all while the cloud solve continued.

---

## Cloud production status (Sprint 3) — Models 1 & 2 DONE, Model 3 in progress

- **Model 1** `mfsuitaware_mixed90.bin` — DONE 2026-04-21. 52 MB, 6,009,159 records. On Mac at `data/best_response_cloud/`.
- **Model 2** `omahafirst_mixed90.bin` — DONE 2026-04-23 04:52 UTC. 52 MB, 6,009,159 records. **Downloaded to Mac this session**, validated via `inspect_br.py`, mean EV +2.123, setting 104 picked 22.72%.
- **Model 3** `topdefensive_mixed90` — RUNNING. At ~80% / 4,796,000 of 6,009,159 at last check (2026-04-24 ~00:48 UTC). Solver-reported ETA ~8.2 hours remaining; should finish approximately 2026-04-25 morning UTC.
- **Model 4** `randomweighted` — queued. Note the 4th production model is `--opponent weighted` (RandomWeighted), not another heuristic mix — this is correct per `scripts/production_all_models.sh`. Estimated ~41 hours after Model 3 completes.
- **Projected full-project finish:** ~2026-04-26 late afternoon UTC.
- **Budget:** user had $26.06 at start of session, planned to add $40 and disable auto-refill — target ~$2.70 leftover at completion. (Action was described to the user; we don't know which path was actually taken.)

---

## What was completed this session (Session 09)

### Model 2 download + cross-model tooling (Sprint 7 prep)
- SCP pulled `omahafirst_mixed90.bin` to `data/best_response_cloud/`. Validated clean via `inspect_br.py`.
- Added `analysis/src/tw_analysis/cross_model.py` — joins N BrFiles by canonical_id, exposes settings/EV matrices, `unanimous_mask`, `unique_settings_per_hand`, `pairwise_agreement`, `consensus_setting_counts`, `unanimous_setting_counts`.
- Added `analysis/scripts/cross_model_join.py` — CLI report (per-model summary, unanimity %, distinct-settings histogram, pairwise matrix, top consensus settings).
- Added `analysis/scripts/test_cross_model.py` — 9 unit tests, all pass (uses synthetic BrFile fixtures; no reliance on real .bin files).
- **First real cross-model finding** (on 2 of 4 models): 39.31% unanimous hands, setting 104 dominates unanimous bucket (28.6%). Mean EV shift MF→Omaha is +1.59 points (opponent quality differential).

### Sprint 5a trainer foundation (new `trainer/` package)
- **Rust engine change:** added `--tsv` flag to `mc` subcommand (`engine/src/main.rs`). Emits all 105 settings with EVs in setting-index order, status prints routed to stderr so stdout stays parseable. 105 data rows verified.
- **Python backend** (`trainer/src/`):
  - `dealer.py` — random 7-card hand dealer, "Rs" card string format.
  - `engine.py` — subprocess wrapper around `tw-engine mc --tsv` with LRU cache keyed by (sorted hand, opponent, samples, seed). Exposes `ProfileSpec`, `PROFILES` (4 production profiles matching `scripts/production_all_models.sh`), `evaluate_hand_profile`, `evaluate_all_profiles`, `find_setting_index`.
  - `explain.py` — heuristic explanation layer v1. Severity tag (trivial / minor / moderate / major) by EV delta. 4 pre-Sprint-7 detectors: split-pair, isolated-bottom-suit (double-suited vs 3+ of a suit), wrong-top-card, tier-swap.
- **Flask app** (`trainer/app.py`): routes `/`, `/api/deal`, `/api/score`, `/api/profiles`, `/api/compare`. Port 5050 (avoids macOS AirPlay Receiver on 5000). `use_reloader=True` so Python edits live-reload.
- **Web UI** (`trainer/static/`): `index.html`, `style.css`, `app.js`. Dark theme, drag-and-drop, click-to-fill (hand → next empty tier slot), per-tier + clear-all buttons, submit/compare flow. Result panel shows user EV vs best EV, severity-colored headline, best arrangement, heuristic findings list. Compare mode shows per-profile table + "per-profile optimal arrangement" panel with mini tier layouts. If all 4 profiles agree, one large "all 4 agree — robust / GTO-approximating" banner; if they differ, 4 stacked mini-layouts per profile.

### Decisions logged
- Decision 029 — Session 09 below.

---

## Blockers / Issues

None. Cloud job is healthy. Trainer works end-to-end (verified via Flask test client + user's browser).

---

## Files touched this session

**Added:**
- `analysis/src/tw_analysis/cross_model.py`
- `analysis/scripts/cross_model_join.py`
- `analysis/scripts/test_cross_model.py`
- `trainer/app.py`
- `trainer/src/__init__.py`, `trainer/src/dealer.py`, `trainer/src/engine.py`, `trainer/src/explain.py`
- `trainer/static/index.html`, `trainer/static/style.css`, `trainer/static/app.js`
- `data/best_response_cloud/omahafirst_mixed90.bin` (52 MB, gitignored)

**Modified:**
- `engine/src/main.rs` — added `--tsv` flag to `mc` subcommand
- `analysis/src/tw_analysis/__init__.py` — exports for `cross_model`
- `CURRENT_PHASE.md`, `DECISIONS_LOG.md` (Decision 029), `handoff/MASTER_HANDOFF_01.md` (Session 09), `checklist.md` (Sprint 5a + cross-model sections)

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
- DECISIONS_LOG.md  (scan Decisions 028 + 029)
- handoff/MASTER_HANDOFF_01.md  (scan Session 09)
- trainer/  (Sprint 5a foundation complete; Flask on port 5050)
- analysis/src/tw_analysis/cross_model.py  (Sprint 7 cross-model join)

Cloud pod `0f8279f6fd0a` has Models 1 & 2 DONE and downloaded to the Mac.
Model 3 (topdefensive_mixed90) was at ~80% with ~8h ETA at end of Session 09.
Model 4 (randomweighted) is queued and launches automatically after Model 3.

First-session-start tasks:
1. Ask user for current pod status. Monitoring commands (single line so web-
   terminal line-wrap doesn't mangle it):

   cd /workspace/tw && echo "=== Launcher ===" && tail -8 data/session06/production_launch.log && echo "" && echo "=== Model 3 last 5 ===" && tail -5 data/session06/prod_topdefensive_mixed90.log && echo "" && echo "=== Model 4 last 5 if started ===" && (tail -5 data/session06/prod_randomweighted.log 2>/dev/null || echo "not started yet") && echo "" && echo "=== Job running? ===" && (pgrep -af "tw-engine solve" || echo "Job stopped.") && echo "" && echo "=== Files ===" && ls -lh data/best_response/

2. Pull any completed models to the Mac with:
   scp -P 11400 root@205.196.19.130:/workspace/tw/data/best_response/<model>.bin \
       /Users/michaelchang/Documents/claudecode/taiwanese/data/best_response_cloud/
   Then `python3 analysis/scripts/inspect_br.py data/best_response_cloud/<model>.bin`.

3. When all 4 files are local, remind user to TERMINATE (not Stop) the pod.

4. Sprint 7 formally unlocks once all 4 .bin files are local. Immediate tasks:
   (a) re-run `analysis/scripts/cross_model_join.py` with all 4 files for the
       true 4-way unanimity rate, (b) hand-feature extractor over canonical
       hands + join on canonical_id for per-hand feature × per-profile setting.

5. Trainer refinements (user-requested once all data is in):
   - Replace heuristic explain.py rules with solver-derived rules from Sprint 7
     pattern mining
   - Cache Compare results so re-runs don't re-MC — currently per-profile
     caches are independent so Compare re-runs the 4 MCs fresh if parameters
     shift; fine for now.

Do NOT launch Mac Mini production. User has vetoed that path.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
