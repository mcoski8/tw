# Current: Sprint 3 — Best Response Computation | Sprint 2b opponent-model panel BUILT, AWAITING CLAUDE DESKTOP APPROVAL for production launch

> Updated: 2026-04-18 (early AM session after overnight diagnostics)
> Previous session: 05 (this one) — 7-model opp panel + 10K-hand diagnostic + behavioural audit + 4 bugs found + adversarial review with Gemini 2.5 Pro → P2-alt commitment proposed.
> Previous sprint status: S3 pipeline done (Session 04); S3 extended with Sprint 2b opp-panel work this session. No production compute launched yet.

---

## What Was Completed Last Session (Session 05)

### Sprint 2b opponent-model panel (user request, via Claude Desktop spec)

Full 7-model opp panel implemented + diagnosed + audited.

**New code:**
- `engine/src/opp_models.rs` (NEW, ~650 lines incl. tests) — all 7 opp heuristics + helpers:
  - `naive_mid_score` (Hold'em 2-card preflop ladder)
  - `middle_tier` (5-tier classifier)
  - `bot_suit_score` (DS>SS>rainbow>3+1>4)
  - `omaha_bot_score` (signed; wheel bonus; 3+1 → −4, 4-flush → −8)
  - `balanced_setting_score` (weighted multi-tier)
  - `opp_middle_first_naive` (bot sanity swap, preserves pairs)
  - `opp_middle_first_suit_aware` (lex-max on (tier, bot_suit, score, indices))
  - `opp_omaha_first` (bot-first, then mid-from-remaining-3, leftover = top)
  - `opp_top_defensive` (highest non-pair-member on top)
  - `opp_random_weighted` (filter → relaxed fallback → pure random)
  - `opp_balanced_heuristic` (evaluates all 105 settings, picks max)
- `engine/src/monte_carlo.rs` — extended `OpponentModel` enum (7 pure variants + `HeuristicMixed { base: MixedBase, p_heuristic: f32 }`); rewrote `opp_pick` dispatcher to route to `opp_models::*`.
- `engine/src/main.rs` — CLI extended with `--opponent {random|mfnaive|mfsuitaware|omaha|topdef|weighted|balanced|mixed}` + `--mix-base` + `--mix-p`; new subcommands `diagnostic` (7-model panel, pairwise matrix, JSON sidecar), `validate-model`, `show-opp-picks`.
- `engine/src/best_response.rs` — `solve_one` and `solve_range` now take `OpponentModel` explicitly.
- `engine/src/lib.rs` — new module registered + re-exports (`MixedBase`).

### Test totals: 119 passing (+14 from Session 04, which was 105).

### Diagnostics run this session

**(a) BalancedHeuristic pre-panel validation** (Claude Desktop's gate):
- 1000 canonical hands × N=5000 vs MC ground truth (Random opp).
- **Result: 18.7% agreement, mean regret 0.653 EV** — FAILS the ≥70% / ≤0.3 gate.
- Wall: 420 s.

**(b) 7-model diagnostic** (Sprint 2b core deliverable):
- 10,000 canonical hands (uniform stride) × N=1000 samples × 7 pure models.
- **Wall: 45.6 min** (predicted 46 — accurate to 1%).
- **Headline: only 11.9% of hands have the same best setting across all 7 models** (vs 45.6% same-best rate in the earlier 2-model diagnostic).
- Mean per-hand EV spread: **2.225** (p50 2.24, p95 3.12, p99 3.50, max 4.18).
- No pair ≥ 95% agreement. Loose clusters: MFNaive/MFSuitAware/TopDefensive (77-88% within Hold'em-centric), OmahaFirst isolated (17-19% with others), BalancedHeuristic's highest correlate is Random (51.4%) — the earlier prediction that it would cluster with middle-heavy models was WRONG.
- Output: `data/diagnostic_7model.json` (10K rows × 7-model EV vectors).

**(c) Behavioural audit on 7 stress-test hands** (`show-opp-picks` per hand):
- Found **4 bugs**:
  - **Bug 1 (CRITICAL):** MFNaive + MFSuitAware split the second pair on AAKK hands. Root cause: "highest-rank remaining card → top" rule ignores pair-membership. `As Ah Kd Kh 7s 4c 2d` → they produce top=Kh, mid=AsAh, bot=Kd 7s 4c 2d (orphaning KK).
  - **Bug 2 (CRITICAL, moot):** BalancedHeuristic puts Ace in bot instead of on top when bot has enough other high cards. Formula arithmetic confirmed: top=7d setting scored 321 vs top=As at 309 due to ×2.5-weighted bot high-card component. Moot because Gemini recommended dropping the model.
  - **Bug 3 (CRITICAL):** OmahaFirst picks absurd tops (e.g., 2d) because my impl picks best-Hold'em-mid from remaining 3 and leaves the *other* card as top, rather than picking top = highest of remaining 3.
  - **Bug 4 (MINOR):** TopDefensive over-splits trips (puts lone J in bot). Gemini's verdict: treat as archetype eccentricity, not a bug.

### Gemini 2.5 Pro adversarial review

Full Socratic debate across Claude Desktop's Topics A-G. Key consensus:
- **Panel: P2-alt** = MFSuitAware-fixed + OmahaFirst-fixed + TopDefensive-fixed + RandomWeighted. Drop MFNaive (88.4% redundant) and BalancedHeuristic (fundamentally miscalibrated, Bug 2).
- **Wrapping: `HeuristicMixed{p=0.9}`** for the three deterministic members; RandomWeighted stays pure.
- **Aggregation: DEFER to Sprint 7**, output 4 separate best-response files.
- **N=1000 uniform.** No adaptive passes, no previews.
- **Fix Bugs 1 and 3** before launch; defer Bug 4; drop the model so Bug 2 is moot.

### Decisions staged this session (to be logged on launch-approval)

- **Decision 019 — 7-model opp panel** built per Sprint 2b spec
- **Decision 020 — Validation gate ≥70% was wrong metric for archetype-distinctness panel** (critique from Gemini + Claude Code)
- **Decision 021 — Drop BalancedHeuristic** entirely; miscalibrated, Bug 2
- **Decision 022 — Aggregation strategy DEFERRED** to Sprint 7; output 4 per-model files
- **Decision 023 — Production panel = P2-alt** (pending Claude Desktop final approval)
- **Decision 024 — `HeuristicMixed{p=0.9}`** for deterministic panel members (not 0.8)

---

## Current State — BLOCKED on Claude Desktop approval

Full PRODUCTION COMMITMENT RECOMMENDATION document sent to Claude Desktop at end of Session 05. Document includes:
- Panel: P2-alt (4 models)
- Bug fixes needed (Bugs 1 and 3)
- 6 yes/no questions for Claude Desktop to answer before launch
- Dissents flagged for user review (ATs-vs-AKo preference; TopDefensive trip-split; potential 5th solver-app-assisted model)

Once Claude Desktop responds, the next session's work is:
1. Apply Gemini-staged bug fixes to `opp_models.rs` (diffs held, NOT applied this session).
2. Add unit tests for the fixes (AAKK pair-preservation; OmahaFirst top=highest-of-remaining).
3. Re-run the 7-model diagnostic on 5K hands subset to confirm bugfix impact (~25 min).
4. Run a mini-pilot: 50K canonical hands × 4-model panel × N=1000 (~4 hours).
5. Launch full production: 6,009,159 hands × 4 models × N=1000 ≈ **10.4 days** on Mac Mini or ~2 days / ~$41 on 48-core cloud.

---

## Blockers / Issues

- **Claude Desktop approval gate** for P2-alt panel + bug-fix plan. Non-trivial compute commitment (10+ days) deserves explicit sign-off.
- **Bug 1 fix is non-trivial** (affects both MFNaive and MFSuitAware). Risk: fix introduces edge cases on trip hands or high-card hands that don't have pairs. Mitigation: audit with `show-opp-picks` across 15+ hand archetypes before committing.

---

## Files touched this session

Modified:
- `engine/src/lib.rs` — opp_models registered; `MixedBase` re-exported
- `engine/src/monte_carlo.rs` — OpponentModel enum extended with 7 variants + HeuristicMixed wrapper; opp_pick dispatcher rewritten; duplicated heuristic helpers removed (moved to opp_models.rs)
- `engine/src/main.rs` — CLI: new subcommands `diagnostic`, `validate-model`, `show-opp-picks`; `--opponent` now takes all 7 variants + mixed + `--mix-base` / `--mix-p`
- `engine/src/best_response.rs` — `solve_one` / `solve_range` take `OpponentModel` explicitly

New:
- `engine/src/opp_models.rs` — all 7 deterministic-ish opp heuristics + tests
- `data/diagnostic_7model.json` (gitignored) — 7-model diagnostic output
- `data/diagnostic_7model.log` (gitignored) — diagnostic stdout

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
- DECISIONS_LOG.md  (scan 017-024 for Sprint 2b context)
- engine/src/opp_models.rs  (all 7 opp models)
- sprints/s3-best-response.md

Session 05 built + audited the 7-model opponent panel for Sprint 2b.
119 tests green. 10K-hand 7-model diagnostic showed 11.9% all-agree +
4 behavioural bugs found in audit. Gemini 2.5 Pro + Claude Code agreed on
P2-alt = MFSuitAware-fixed + OmahaFirst-fixed + TopDefensive-fixed +
RandomWeighted, wrapped in HeuristicMixed{p=0.9}, defer aggregation,
fix Bugs 1 and 3 before launch. A full PRODUCTION COMMITMENT
RECOMMENDATION document was sent to Claude Desktop for final approval.

The user will paste Claude Desktop's response to that document in this
chat session after acknowledging this prompt. Wait for that response
before taking action.

When Claude Desktop's response lands:

1. If P2-alt is approved as-is:
   a. Apply Bug 1 + Bug 3 fixes to engine/src/opp_models.rs using
      Gemini's staged diffs (held in Session 05's context). Integrate
      carefully — don't copy-paste wholesale.
   b. Add two new unit tests:
      - `mfsuitaware_preserves_kk_on_aakk_hands` (input: As Ah Kd Kh 7s
        4c 2d; expect top = non-king, KK intact in mid or bot)
      - `omahafirst_top_is_highest_of_remaining_three` (input: As Kh
        Qd Jc Ts 9h 2d; expect top rank ≥ 9)
   c. Re-run `show-opp-picks` on the 7 stress-test hands to verify.
   d. Re-run the 7-model diagnostic on 5K hands to confirm bug-fixes
      changed cluster structure as expected (MFNaive↔MFSuitAware
      should drop below 88.4%).
   e. Run a mini-pilot: 50K canonical hands × 4-model P2-alt panel
      × N=1000 (~4 hours).
   f. If pilot OK, launch full production.

2. If Claude Desktop course-corrects (adds 5th model, changes
   wrapping, etc.), integrate the changes and re-propose before
   applying.

Session 05's final commit: the Sprint 2b panel + diagnostic are committed
on origin/main. Audit evidence for the 4 bugs is in session 05's
conversation — user can re-share if needed.

Your job: wait for Claude Desktop's paste, then execute the approved
plan.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
