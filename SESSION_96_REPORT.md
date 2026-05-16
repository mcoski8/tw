# Session 96 — Headline-goal recalibration (doc-only). **Production v65 UNCHANGED.** 95% match%/agreement target formally retired (second-stage closure); $/1000h on the production grid codified as the project's headline metric (Decision 131). Three load-bearing zombie-95% references in CLAUDE.md + checklist.md replaced; STRATEGY_GUIDE.md front-matter and Part 1 updated; CURRENT_PHASE.md rewritten for S97.

_Generated 2026-05-16. No code touched. No engine runs. No grader runs._

## TL;DR — Plain language

**What changed in your strategy of record:** **Nothing.** v65 remains production at $1,633.79/1000h full grid / $776.88 prefix. v44_dt remains ML champion (24th consecutive session). Rule count UNCHANGED at 25.

**What changed in the project's headline goal:** The original "match the solver 95%+ of the time" target was already half-retired in Session 16 (Decision 033 dropped the *shape-agreement* form in favor of "directional EV-loss reduction + non-negative absolute EV per profile"). But the *match%* form survived in the load-bearing docs (`CLAUDE.md`, `checklist.md`) and re-emerged organically in session-report framing across S79, S81, S82, S85, S95 — a zombie target lurking through ~30 sessions while the project quietly worked around it. S96 finishes the job: the 95% match% target is formally retired second-stage, replaced by **$/1000h on the production grid** as the project's headline metric.

**Why now.** Every major lever the cascade has tested in the past 18 sessions has been characterized as saturated on the current ML architecture:
* **Decision 113 (S78):** ML feature engineering closed at v44 capacity (2.25M leaves).
* **Decision 117 (S82):** Label-quality A-path closed at v44 capacity (Lens-3 OOS NULL).
* **Decisions 122-127 (S87-S92):** Chain-audit lever shipped $214.83/1000h then exhausted at methodology boundary.
* **Decision 129 (S94):** Rule-extraction bucket-level closed ($5.08/1000h ceiling at 100% trigger across all 10 within-v44_dt residual cells).
* **Decision 130 (S95):** Rule-extraction intra-layout closed on the strongest candidate (trips B_DS_AVAIL_LKR landed MIXED at $+4.59/$+4.75, $0.25 short of $5 SHIP bar on both grids).

**Plus** S79's empirical finding that oracle labels self-disagree at 32% N=200↔N=1000 — meaning any match% above ~68% on N=200 oracle is partially memorizing label noise. v44 sits at 67% on N=1000 Lens-3 OOS. The 95% target was set before this measurement; it bakes in the assumption that the answer key is deterministic, which it isn't.

**What this means for future sessions.** MIXED verdicts like S95's borderline $+4.59/$+4.75 no longer carry the implicit "we're behind 95% match%" subtext. They mean: this candidate did not clear $5 on both grids; the remaining gap to oracle ceiling ($111.41/1000h) is the maximum potential remaining lift across all future work on the current architecture; A3 retrain is the only lever with potential to recover $50+/1000h, and even that has a credibility-low expected outcome.

**What's on the table for S97:**
1. **A3 ML retrain** (PROMOTED to PRIMARY). Full 6M × 105 × N=1000 grid. ~70 hours wall on current hardware via Option C infrastructure. Formally closed at v44 in S78; reopening requires operator authorization. Expected outcome: NULL more likely than SHIP per Decisions 113 + 117, but the only remaining lever with potential to recover $50+/1000h.
2. **v52-defensive-low partial-effectiveness exploit** (SECONDARY, was TERTIARY). Per-hand picker between v52-DL and v44_dt on the ~23% of S90 hands where v52-DL wins. Speculative.
3. **v44_RULE13 fallthrough replacement** (TERTIARY, was DEFERRED). Mostly absorbed already by v54/v55/v56 ($731+/1000h of chain bleed absorbed); replacement primarily matters for HIGH_ONLY (already gated by v64/v65).

**The numbers (UNCHANGED from S95):**
* Production v65: **$1,633.79/1000h full grid / $776.88 prefix**
* v44_dt: **$1,081 full / $686 prefix** (UNCHANGED for **24 consecutive sessions**, since v44 in S58)
* Production vs v44_dt: **$552.79/1000h**
* Remaining gap to oracle ceiling: **$111.41/1000h**
* Cumulative closure since pre-S68: **$1,297.59 of $1,409 = 92.09%**
* Rule count: **25** (UNCHANGED)

---

## The full story

### Phase A — audit for 95% match% references

Grepped `STRATEGY_GUIDE.md`, `CLAUDE.md`, `CURRENT_PHASE.md`, `README.md`, `checklist.md`, `DECISIONS_LOG.md`, plus all `SESSION_*` reports for: literal `95%`, `match%`, `match.rate`, `matches the solver`, `agree.*95`, `95-99%`, `95\+%`.

**Three load-bearing zombie-95% references found** (current state, before S96 edits):

| Location | Reference | Why load-bearing |
|---|---|---|
| `CLAUDE.md:12` | "Primary Goal: ... matches the solver 95%+ of the time." | This is the project's top-level Primary Goal statement. Every new conversation with an AI assistant reads this line first. |
| `CLAUDE.md:20` | "Critical Output #4: Validation proving the decision tree matches the solver for 95-99% of hands" | Critical Output section spells out the project's deliverables. |
| `checklist.md:159` | "[ ] Push toward 95%+ agreement with conditional refinements" | Phase 4 Sprint 7 outstanding task. |

**Prior partial retirement on the books:**
* **Decision 033 (S16, 2026-04-27)** — retired the *shape-agreement* form of the 95% target after the 27-feature DT ceiling capped at 61.74%. Chose option (d) "directional EV-loss reduction (no hard %) + non-negative absolute EV against all 4 profiles."
* **Decision 033 Consequence #1** — *"CLAUDE.md headline section may need an update reflecting the new goal framing (deferred to Session 17 — not blocking)"*. Never done across 79 subsequent sessions.

**Re-emergence of 95% framing after Decision 033** (post-retirement, the *match%* form):
* `SESSION_79_LABEL_NOISE_REPORT.md:7` — "is the 35-point gap to our 95% match-rate goal..."
* `SESSION_79_LABEL_NOISE_REPORT.md:226` — "Neither lifts → headline-goal recalibration: 95% may not be..."
* `SESSION_81_LAUNCH_REPORT.md:19` — "revisit whether the 95% match-rate goal is even reachable"
* `SESSION_82_REPORT.md:21,143-147` — explicit headline-goal recalibration option formally surfaced; Option 2 of the post-NULL fork
* `SESSION_85_REPORT.md:119,368` — "gap to a 95% match% goal would require"
* `SESSION_95_REPORT.md:17,168,226` — promotion to S96 PRIMARY direction
* `CURRENT_PHASE.md:49,142,234,241` (pre-S96) — S96 plan refs

**Other 95% mentions in the corpus are unrelated** — data tables citing DS rates, joint take-rates, etc. (e.g., SESSION_67, SESSION_70, SESSION_58). Left untouched.

### Phase B — draft new success criterion

**The proposal:**

> **PRIMARY HEADLINE METRIC**
> Production strategy $/1000h on the full grid (N=200, RealisticHumanMixture, 6M canonical hands).
> Currently **$1,633.79**.
>
> **SECONDARY (diagnostic, not headline)**
> * Remaining gap to oracle ceiling: currently **$111.41** (closure 92.09%).
> * Two-track divergence (production vs v44_dt alone): currently **$552.79** (positive = rule layer adds value over ML alone).
> * Rule count: currently **25** (memorability cost).
>
> **OPERATIONAL SHIP STANDARD** (unchanged)
> Pre-committed two-grid bar — both N=200 full grid AND N=1000 (prefix or sparse) lifts ≥ $5/1000h on the changed-hand cohort, with |Δ| ≤ ~$1 and sign-agreement ≥ 70%.
>
> **Match% retained as diagnostic only** — still informative for debugging, comparable across sessions, but not the headline.

**Saturation evidence stack motivating the second-stage retirement:**

| Lever | Status | Anchor decision |
|---|---|---|
| ML feature engineering | EXHAUSTED at v44 saturating regime | Decision 113 (S78) |
| Label-quality A-path | FORMALLY CLOSED at v44 capacity | Decision 117 (S82) |
| Chain-audit | $214.83/1000h SHIPPED → COMPLETE | Decisions 122-127 (S87-S92) |
| Rule extraction bucket-level | SATURATED, $5.08/1000h ceiling | Decision 129 (S94) |
| Rule extraction intra-layout | SATURATED, strongest candidate MIXED at $4.59/$4.75 | Decision 130 (S95) |
| A3 ML retrain | Only remaining lever with $50+ recovery potential | DEPRIORITIZED |
| v52-DL exploit | Speculative, smaller magnitude | DEFERRED |

Plus S79's oracle self-disagreement of 32% at N=200↔N=1000 means **>68% match% is partially label-noise memorization** — the 95% target was set before this empirical measurement.

**Why $/1000h is the right replacement:**
1. **Weights mistakes by economic impact** — match% treats a 1¢ argmax flip identically to a $50 argmax flip; $/1000h does not.
2. **Survives oracle self-disagreement** — averaging across 6M × 105 × N is robust by CLT to per-hand label noise.
3. **Already what the user's $10/EV-point framing (S16) cared about** — the user's "easy hands are easy to play; bleeding lives on weak hands" directive points squarely at $/damage.
4. **Already operational** — the pre-committed two-grid SHIP standard at $5/1000h is the existing per-candidate test; no methodology change is required, only the headline framing.

### Phase C — applied doc edits

1. **`CLAUDE.md` lines 12 + 20 rewritten**
   * Line 12 "Primary Goal": dropped "matches the solver 95%+ of the time"; reframed to "maximize $/1000h on the production grid (RealisticHumanMixture, N=200, 6M canonical hands)."
   * Line 20 "Critical Output #4": dropped "matches the solver for 95-99% of hands"; reframed to "report $/1000h on full grid + remaining gap to oracle ceiling + two-track divergence."
   * Added a Decisions-033+131 pointer paragraph under Primary Goal so future readers have the trail.
   * Architecture description updated to acknowledge the current 25-rule chain + ML champion stack (not just "a human-memorizable decision tree").

2. **`checklist.md` lines 158-159 struck through**
   * `[~] ~~Iterate decision tree until 70%+ agreement~~ — RETIRED by Decision 131 ...`
   * `[~] ~~Push toward 95%+ agreement~~ — RETIRED by Decisions 033 + 131 ...`
   * Agreement-analysis line (160) marked deprioritized but kept (still useful as diagnostic).

3. **`DECISIONS_LOG.md`** — Decision 131 appended. Full record of options (a)/(b)/(c)/(d), choice = (c) explicit second-stage retirement, six "why" bullets covering S79 label noise + four saturation closures + $/1000h-as-right-metric + the user's directive, six consequences covering each doc-update target, and two "what this does/does not change" lists.

4. **`CURRENT_PHASE.md`** — rewritten in place for S97. New PRIMARY: A3 ML retrain (with honest expected-NULL prior); SECONDARY: v52-DL exploit; TERTIARY: v44_RULE13 fallthrough replacement.

5. **`STRATEGY_GUIDE.md`** — front-matter "Last updated" stanza prepended for S96; Part 1 appended with Session 96 entry (this session). Part 2 onwards untouched (no champion change).

6. **`MASTER_HANDOFF_01.md`** + **`sprints/SPRINT_INDEX.md`** — S96 entries appended per session-end protocol.

### Verdict + production state

**VERDICT: HEADLINE RECALIBRATED.** Production v65 UNCHANGED.

| metric | pre-S96 (v65) | post-S96 (v65) | Δ |
|---|---:|---:|---:|
| Full grid (N=200) | $1,633.79 | $1,633.79 | $0.00 |
| Prefix grid (N=1000) | $776.88 | $776.88 | $0.00 |
| Production vs v44_dt | $552.79 | $552.79 | $0.00 |
| Remaining gap to oracle | $111.41 | $111.41 | $0.00 |
| Cumulative closure since pre-S68 | 92.09% | 92.09% | 0.00pp |
| Rule count | 25 | 25 | 0 |

* v44_dt ML champion: UNCHANGED ($1,081 full / $686 prefix) — **24 consecutive sessions** running.
* Combined S87-S93 production-chain recovery: $221.26/1000h. **S94 + S95 + S96 contribute $0.**

### Methodology lessons (S96)

1. **Doc drift compounds across sessions; periodic audits catch it (NEW S96).** Decision 033 explicitly flagged a needed CLAUDE.md update as "not blocking" → deferred to Session 17 → never done across 79 subsequent sessions. The zombie 95% framing then lurked in load-bearing docs through ~30 sessions of saturation evidence accumulating, with every recent session report quietly working around it. **"Not blocking" doc updates compound. Annual or post-pivot audits of CLAUDE.md / checklist.md headlines against actual project state are worth running.** Cost: ~1 session of grep + careful editing. Benefit: future MIXED verdicts are interpreted against the actual operational standard, not a defunct target.

2. **Headline-goal recalibration is a one-off; saturation closures across all major levers are the legitimate trigger (NEW S96).** This recalibration is not a "lowering the bar to ship more easily" move — the per-candidate $5/1000h SHIP standard is unchanged. It is a "calling the project's overall finish-line where the evidence already pointed" move. Three saturation closures (Decisions 113, 117, 129+130) plus two completions (Decisions 122-127 chain-audit) over 18 sessions form the legitimate evidentiary basis. Cascade recalibrations should require this kind of multi-lever closure pattern, not a single NULL session.

3. **$/1000h survives label noise where match% does not (NEW S96).** Match% on an oracle with 32% self-disagreement at N=200↔N=1000 is fundamentally noisy as a per-hand metric. $/1000h averaged across 6M canonical hands × 105 settings × N=200 (or sparse N=1000) is robust by central-limit-theorem to that same noise. The two-grid SHIP standard's $5 bar at |Δ| ≤ $1 already encodes the noise floor empirically. **Pick a metric that the data quality supports; the original 95% match% target was conceived before the data quality was characterized.**

### Artifacts (Session 96)

**Documentation only** (no code, no engine runs, no grader runs, no data files):
* `CLAUDE.md` — Primary Goal + Critical Output #4 rewritten; pointer paragraph to Decisions 033+131 added.
* `checklist.md` — lines 158-159 struck through with decision pointers; line 160 deprioritized.
* `DECISIONS_LOG.md` — Decision 131 appended.
* `CURRENT_PHASE.md` — rewritten in place for S97.
* `STRATEGY_GUIDE.md` — front-matter updated; Part 1 appended with Session 96 entry.
* `SESSION_96_REPORT.md` — this file (NEW).
* `MASTER_HANDOFF_01.md` — S96 entry appended.
* `sprints/SPRINT_INDEX.md` — S96 entry appended.

### State at end of S96

**Strategies of record (UNCHANGED from S95):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (**UNCHANGED for 24 sessions**, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

* **Total project rule count: 25** (UNCHANGED).
* **Cumulative closure since pre-S68: $1,297.59 of $1,409 = 92.09%** (UNCHANGED).
* **Remaining gap to oracle ceiling: $111.41/1000h** (UNCHANGED).
* **Production vs v44_dt: $552.79/1000h** (UNCHANGED).
* **Combined S87-S93 production-chain recovery: $221.26/1000h** (UNCHANGED). S94 + S95 + S96 contribute $0.
* **Chain-audit methodology arc: COMPLETE** (S92 closure holds).
* **Rule-extraction (Option D-revised) lever — both sub-classes: SATURATED** (S94 + S95 closures hold).
* **Headline metric formally recalibrated to $/1000h on the production grid (Decision 131).** Match% retired as headline; retained as diagnostic.

## What's on the table for S97

1. **PRIMARY — A3 ML retrain (full 6M × 105 × N=1000 grid).** Formally closed at v44 in S78 (Decision 113); reopening requires operator authorization. Option C infrastructure provides the foundation; ~70 hours wall on current hardware. The structural saturation findings from S91-S95 raise the question of whether a richer ML champion would shift the saturation boundary — this is the only remaining lever with potential to recover $50+/1000h. Honest expected-outcome prior: NULL more likely than SHIP per Decisions 113 + 117. Substantial compute investment for credibility-low payoff.

2. **SECONDARY — v52-defensive-low partial-effectiveness exploit (DEFERRED from S90).** Per-hand picker between v52-defensive-low and v44_dt on the ~23% of S90 hands where v52-DL wins. Speculative, smaller magnitude than A3.

3. **TERTIARY — v44_RULE13 fallthrough replacement.** With v54/v55/v56 absorbing $731+/1000h of chain bleed across pair-family, replacement primarily matters for HIGH_ONLY (already gated by v64/v65). Likely modest impact at best.

4. **MAINTENANCE option — Other parked MIXED candidates.** v60 gate-11 currently MIXED at +$4.85/+$4.77 (S93 SECONDARY finding); eligible for relaxed-bar or composite-rule re-evaluation. Smaller scope than A3 but lower-risk.
