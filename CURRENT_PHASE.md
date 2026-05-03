# Current: Sprint 8 — v16_dt is the new ML champion. Next: distill v16's tree into hand-coded rules (v17).

> **🎯 IMMEDIATE NEXT ACTION (Session 28):** Walk v16's 28,790-leaf
> DecisionTreeRegressor and surface the highest-impact splits as candidate
> plain-English rules. The tree is beating the v9.2/v10/v12/v14 chain by
> $431/1000h at N=1000 fidelity — distilling its top splits should
> expand `STRATEGY_GUIDE.md` with new human-memorizable rules.

> **✅ SHIPPED (Decision 047):** v16_dt — the first ML strategy of the new
> grid era. Trained on full 6M canonical hands × N=200 with the v5/v7
> 37-feature set, depth=18, min_samples_leaf=100. **+$569/1000h vs v14
> on full grid (N=200), +$431/1000h on the N=1000 prefix.**

> **🚫 ARCHIVED:** prefix-trained v16 — overfits to canonical-id bias of
> the 500K-prefix (oracle mean EV in prefix is −0.667 vs +0.758 on full
> grid). Generalizes catastrophically: $8,493/1000h, 16.40% optimal.
> Lesson: do not train on canonical-id-prefix subsets; the canonical
> ordering is highly non-uniform in hand strength.

> Updated: 2026-05-03 (end of Session 27)

---

## Headline state at end of Session 27

**Two strategies of record, for different audiences:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14_combined** | Human-memorizable rule chain | `STRATEGY_GUIDE.md` + `analysis/scripts/strategy_v14_combined.py` |
| **v16_dt** | ML champion (28,790-leaf DT) | `analysis/scripts/strategy_v16_dt.py` + `data/v16_dt_model.npz` |

**Final standings (full 6M grid, N=200):**

| Strategy | $/1000h vs ceiling | pct_optimal | Δ vs v8 | Δ vs v14 |
|---|---:|---:|---:|---:|
| v8_hybrid | $3,153 | 36.70% | — | — |
| v14_combined | $3,033 | 39.61% | −$120 | — |
| **v16_dt** | **$2,464** | **42.54%** | **−$689** | **−$569** |

**At higher fidelity (500K-prefix grid, N=1000):**

| Strategy | $/1000h vs ceiling | pct_optimal | Δ vs v8 | Δ vs v14 |
|---|---:|---:|---:|---:|
| v8_hybrid | $3,051 | 38.51% | — | — |
| v14_combined | $2,037 | 47.61% | −$1,014 | — |
| **v16_dt** | **$1,607** | **50.77%** | **−$1,444** | **−$431** |

**Per-category breakdown (full grid, N=200):**

| Category | v14 $/1000h | v16 $/1000h | Δ | Notes |
|---|---:|---:|---:|---|
| high_only | $4,082 | $3,785 | −$297 | partial improvement, still the biggest residual at 31% of v16 bleed |
| pair | $2,011 | $2,127 | +$116 | apparent regression at N=200; at N=1000 v16 edges v14 ($1,191 vs $1,229) — was MC noise |
| two_pair | $3,371 | $2,005 | −$1,366 | v10's tiebreaks superseded |
| trips | $4,054 | $2,347 | −$1,707 | v14 had no rule here |
| trips_pair | $5,417 | $2,438 | −$2,979 | v12's chain superseded |
| three_pair | $4,529 | $1,975 | −$2,554 | v14 had no rule |
| quads | $9,670 | $2,233 | −$7,437 | v14 had no rule |
| composite | $10,883 | $5,260 | −$5,623 | v14 had no rule |

---

## What this leaves on the table (full grid)

- v16 captures **24% of the v14→ceiling gap** ($569/$3,033) at N=200 fidelity
- v16 captures **21% of the v14→ceiling gap** ($431/$2,037) at N=1000 fidelity
- Remaining gap to ceiling: $2,464/1000h (full grid N=200) / $1,607/1000h (prefix N=1000)
- Biggest residual: high_only ($3,785 × 20.4% share = $774 of v16 bleed = 31%)

The v16 DT is interpretable. Walking the tree's top-impact splits will both:
1. Reveal what feature-combinations the DT keys on (e.g. "if pair_high_rank ∈ {2-5} AND can_make_ds_bot AND has_ace_singleton, branch X" — could be a new Rule).
2. Provide the next set of v17/v18 hand-coded rules for the strategy guide.

---

## Methodology lessons (Session 27)

1. **Canonical-id prefix is not a uniform sample.** The first N canonical hands skew toward weak/low-rank archetypes. Prefix oracle mean EV = −0.667; full-grid mean = +0.758. Models trained on the prefix learn a distribution-warped argmax and fail catastrophically on the full population.

2. **N=200 has real per-category noise.** v16's apparent "pair-category regression" disappeared at N=1000. Future ship/archive decisions on small per-category deltas should always re-validate at N=1000.

3. **Multi-output regression DT works at scale.** 6M × 105 outputs at depth=18 fits in 172s of `sklearn` time on the M2 Mac mini and produces a model that beats every hand-coded chain. The methodology is repeatable for any future grid.

4. **Cycle scoreboard since Session 25 (8 ships, 3 archives, 1 baseline-only):**

| Cycle | Target | Result | Status |
|---|---|---:|---|
| v9.1 | single pair | +$24 N=200 | SHIPPED |
| v10 | two_pair | +$81 incremental | SHIPPED |
| v11 | high_only | −$1,745 | ARCHIVED |
| v12 | trips_pair | +$10 incremental | SHIPPED |
| v13 | trips | −$172 | ARCHIVED |
| v14 | single pair refine | +$5 incremental | SHIPPED |
| v15 | high_only DS-patch | −$296 | ARCHIVED |
| v16_prefix | DT on 500K prefix | −$5,460 | ARCHIVED |
| **v16_full** | **DT on 6M full** | **+$569** | **SHIPPED — current ML champion** |

---

## What was built in Session 27

**Strategies:**
- `analysis/scripts/strategy_v16_dt.py` — load + walk a v16 DT model; argmax 105-EV leaf vec
- `data/v16_dt_model.npz` — 21.5 MB, 28,790 leaves, depth=18, full-grid trained (canonical model)
- `data/v16_dt_model_full.npz` — verbatim copy preserved for reproducibility
- `data/v16_dt_model_prefix.npz` — failed prefix-trained variant (kept as "what NOT to do")

**Trainer:**
- `analysis/scripts/train_v16_regression.py` — flexible CLI trainer (--training-grid, --max-depth, --min-samples-leaf, --output)

**Graders:**
- `analysis/scripts/grade_v16_full_grid.py` — head-to-head v8 vs v14 vs v16 on full or prefix grid
- `analysis/scripts/grade_v16_full_trained.py` — quick single-strategy grader for v16_full

**Tournament:**
- `analysis/scripts/tournament_50k.py` updated with v9.2 / v10 / v12 / v14 / v16_dt

---

## Resume Prompt (Session 28)

```
Resume Session 28 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (the rule book — current production human strategy)
- CURRENT_PHASE.md (rewritten end of Session 27)
- DECISIONS_LOG.md (latest: Decision 047 — v16_dt ships)
- analysis/scripts/strategy_v16_dt.py — ML champion
- analysis/scripts/train_v16_regression.py — trainer

State (end of Session 27):
- v14_combined is the human-memorizable strategy ($3,033/1000h vs ceiling).
- v16_dt is the ML champion ($2,464/1000h, +$569 vs v14 at N=200,
  +$431/1000h on the prefix at N=1000). 28,790 leaves, depth=18.
- v16 wins on every category vs v14. Pair-category regression at N=200
  was MC noise — v16 wins at N=1000.
- Remaining gap to ceiling: $2,464/1000h. Biggest residual is high_only
  ($3,785 × 20.4% share).

Next session targets:

(A) **Distill v16's tree.** Walk v16_dt_model.npz, find the highest-impact
    splits (those that reduce per-leaf MSE the most), translate them to
    plain-English rules. Add the top 3-5 to STRATEGY_GUIDE.md. The DT is
    the oracle's best fit; its splits are exactly the patterns a human
    should memorize.

(B) **High_only deep-dive.** v16 still leaves $3,785/1000h on high_only
    (31% of v16's total bleed). Sub-cluster by suit_dist, broadway_count,
    longest_run; find archetypes where v16's leaf-prediction is far from
    oracle argmax. Targeted v18 rule.

(C) **Try v17 = v9.2/v10/v12 → v16 fallback.** The hand-coded rules
    encode interpretable logic; on hands where the rules fire, they
    might agree with v16. On disagreements, ground-truth EV decides.
    Probably a wash given v16's edge but worth a 4-min grade to confirm.

(D) **Tighter v16 training.** Train on the N=1000 prefix instead of
    full N=200, but ONLY if the prefix is rebuilt as a uniform random
    subsample (not the canonical-id prefix, which biases toward weak
    hands). Or train on the full grid at higher MC sample count
    (N=500-1000) — would be a multi-day compute job.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- N=200 grades have real per-category noise; re-validate small deltas
  at N=1000.
- 4-min full-grid grade is the validation gate; never ship a candidate
  that grades negative on the full grid.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
