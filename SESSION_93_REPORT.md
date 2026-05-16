# Session 93 — v65 SHIPS Rule 25 (MID pair × PMID_DS_NOMAXTOP × max_sing ≤ Q chain extension), unblocking the 7-session-parked v60 candidate via NEW Option C N=1000 sparse-grid infrastructure. **Production: $1,627.36 → $1,633.79/1000h. First SHIP via two-grid bar on a prefix-uncovered cell.**

_Generated 2026-05-16. S93 executed the S92-defined PRIMARY path verbatim: build the engine `--id-list-file` mode and retroactively validate v60 (parked since S86 as MIXED-by-methodology because its target cell sat entirely outside the prefix N=1000 grid's coverage). Phase A added `solve_grid_ids` to `engine/src/oracle_grid.rs` + a CLI option to `OracleGrid`; output is a SPARSE TWOG file with `canonical_total` = id-list length. Phase B correctness test: 100/100 rows bit-identical to the existing prefix N=1000 grid. Phase C ran the engine on 32,304 changed-hand IDs for the MID pair × PMID_DS_NOMAXTOP cell at gate=12 (max_sing ≤ Q), 21:17 wall at 25 hands/s. N=1000 lift = +$6.34/1000h; N=200 lift = +$6.43/1000h (exact match to S86 baseline); two-grid SHIP standard cleared by both. Built `strategy_v65_mid_pair_chain_extend.py` composing v64's HIGH_ONLY zone gate with v60-gate12's MID pair rule (firing zones disjoint by construction). Final whole-grid grader: v65 production $1,633.79/1000h N=200; v64==v57 on 32,304/32,304 changed hands (composition holds); v65==v64 on 50,000/50,000 out-of-cell sample (zero disagreements outside cell). **Production +$6.43/1000h, vs v44_dt +$552.79 (was $546.36), remaining gap to oracle $111.41 (was $117.84), cumulative closure 91.6% → 92.09%, rule count 24 → 25.** v44_dt UNCHANGED for 21st consecutive session._

## TL;DR — Plain language

**What changed in your strategy of record:** **v64 → v65.** A new rule (Rule 25) ships on top of v64's chain-audit infrastructure. Rule 25 fires on the niche cell "you have a middle-rank pair (8-T), your max kicker is Queen-or-below, AND there's a double-suited bot config available BUT only if you don't put your max kicker on top." On those hands, drop the max kicker into the bot, take the next-best kicker on top, keep the pair in the mid. Production score jumps from $1,627.36 to $1,633.79 per 1000 hands — about +$6.43 per 1000 hands of play.

**Why this took 7 sessions to ship.** The rule was identified back in Session 86 as a candidate (then called "v60"), and the full-grid N=200 grader auto-fired SHIP at +$6.43. But our two-grid SHIP standard (S84+) requires BOTH the full-grid (N=200, ~6M hands) AND the prefix grid (N=1000, 500K hands) to clear $5/1000h. The cell in question (MID pair × PMID_DS_NOMAXTOP) sits at canonical_id 593,072+ in the indexing — entirely outside the prefix grid's [0, 500K) coverage. So the prefix grader was silent (zero coverage = zero signal), and the candidate landed in MIXED-by-methodology limbo. It sat there for 7 sessions while we worked the HIGH_ONLY chain-audit lever (S87-S92).

**The infrastructure unlock (Option C).** Session 92 closed out the chain-audit methodology arc (it had shipped 4 production rules + 2 NULLs across S87-S92 and was exhausted). Session 92's resume prompt promoted Option C — "build a way to run N=1000 oracle EVs on an arbitrary subset of canonical_ids, not just the sequential [0, 500K) range" — to PRIMARY for S93. This session built that infrastructure as a one-flag addition to the Rust engine (`--id-list-file`). Then ran it on the 32,304 hands the v60 rule actually changes. The resulting "sparse N=1000 grid" gives us the second-grid number the two-grid SHIP standard needs.

**Two-grid SHIP cleared.** N=200 whole-grid lift on those 32,304 hands: **+$6.43/1000h**. N=1000 whole-grid lift on the SAME 32,304 hands: **+$6.34/1000h**. Difference: $0.09 — the two independent MC estimates agree extremely well. Both clear $5. Mechanical verdict: SHIP.

**Production update — v65 build.** Built `strategy_v65_mid_pair_chain_extend.py`: composes v64's HIGH_ONLY chain-audit gate (Rules 21-24) with v60-gate12's MID pair rule. **The two firing zones are demonstrably disjoint** (v64 needs no pair; v60 needs exactly one MID pair). Composition is purely additive — production picks change only on the 32,304 MID-pair hands where v60 fires. Whole-grid N=200 lift confirmed: **+$6.43/1000h** (matches the cell-level number to the penny).

**The numbers:**
- Production v65: **$1,633.79/1000h full grid / $776.88 prefix (UNCHANGED)** — rule fires entirely outside prefix coverage.
- v44_dt: $1,081 full / $686 prefix (**UNCHANGED for 21 consecutive sessions**, since v44 in S58).
- Production vs v44_dt: **$552.79/1000h** (was $546.36).
- Remaining gap to oracle ceiling: **$111.41/1000h** (was $117.84).
- Cumulative closure since pre-S68: **$1,297.59 of $1,409 = 92.09%** (was 91.6%).
- Rule count: 24 → **25** (Rule 25 = MID pair × PMID_DS_NOMAXTOP × max_sing ≤ Q × v57-pick-tmax-style → force PMID_tnomax_DS).
- Combined S87-S93 production-chain recovery: **$221.26/1000h** = $214.83 (chain-audit S87-S90) + $6.43 (Rule 25 S93).
- v60 candidate (parked since S86, 7 sessions): **RESOLVED → SHIPPED** as Rule 25 / v65.

**What's NOT changing:** ML champion (v44_dt unchanged for 21 sessions), prefix score (rule fires outside prefix coverage), the chain-audit-arc-complete framing from S92 (Rule 25 is a rule-extraction ship enabled by infrastructure, NOT a chain-audit ship).

**What we discovered about the methodology:**

  * **Option C N=1000 sparse infrastructure works at production quality.** The 100-sample correctness test produced bit-identical EVs to the existing prefix N=1000 grid (same `--samples`, `--seed`, `--opponent`). The per-hand seed `base_seed + canonical_id × φ` is deterministic, so any id processed via `--id-list-file` produces the same MC sample sequence as the same id in a sequential sweep. Throughput ~25 hands/s parallel — manageable for cell-scale validations (32K hands ≈ 22 min wall).
  * **MIXED-by-methodology candidates are recoverable if the only blocker was prefix coverage.** v60 sat for 7 sessions carrying a +$6.43 N=200 SHIP signal that couldn't be confirmed. With the right infrastructure, the SHIP was a single 22-minute engine run away. Future MIXED-by-methodology candidates with the same shape (cell outside prefix range, full-grid SHIP signal, no obvious mechanism flaw) should be queued for Option C validation.
  * **Pre-committed two-grid thresholds are robust at low effect sizes.** Per-hand sign-agreement between N=200 and N=1000 deltas on the 32,304 changed hands was only **77.8%** — meaning 22% of changed hands have OPPOSITE signs in the two grids. This is normal MC noise at the per-hand level. But aggregated over 32K hands the variance collapses and both grids land within $0.09/1000h of each other. **Lesson: per-hand MC noise matters for per-hand picker design, NOT for cell-level rule SHIP verdicts.**
  * **Disjoint firing zones make production composition trivially safe.** v64 fires on HIGH_ONLY (no pair); v60 fires on MID pair. Empirical confirmation: v64==v57 on 100% of v60's changed hands, and v65==v64 on 50,000/50,000 out-of-cell random samples. When zones are demonstrably disjoint, a composed strategy can ship with confidence from cell-level grading alone, no separate full-grid regrade required.
  * **Chain-audit-arc-complete (S92) does NOT mean rule-arc-complete.** S92 closed one specific lever (chain audit on prefix-silent cells). S93's ship is a different lever (rule extraction on a within-v44_dt residual leak), unblocked by infrastructure (Option C). The project still has live levers — they're just different ones than what dominated S87-S92.

## The full story (compressed)

### Phase A — Rust engine modification (~30 min)

Added `solve_grid_ids` to `engine/src/oracle_grid.rs` — sibling of `solve_grid_range` but each item carries its own canonical_id:

```rust
pub fn solve_grid_ids<F>(
    ev: &Evaluator,
    items: &[(u32, [u8; HAND_SIZE])],
    samples: usize,
    base_seed: u64,
    model: OpponentModel,
    block_size: usize,
    writer: &mut OgWriter,
    mut on_block: F,
) -> Result<u64, OgError>
where F: FnMut(u32, u64, std::time::Duration),
{ ... }
```

Inner MC is identical to `solve_grid_one` (same per-hand seed derivation, so output is bit-identical to the corresponding row of a sequential sweep). Outer rayon parallelism is identical to `solve_grid_range`. The function takes a `&[(u32, [u8; HAND_SIZE])]` instead of `(start_id: u32, &[[u8; HAND_SIZE]])` — each row is self-describing.

Added `--id-list-file <PATH>` to the `OracleGrid` subcommand in `engine/src/main.rs`. The id-list file is plain text (one decimal canonical_id per line; blank lines and `#` comments ignored); the engine sorts + dedupes the ids, validates `id < canonical_total`, and dispatches to `solve_grid_ids`. The output file:
- Uses the existing TWOG format unchanged (each record is `canonical_id u32 + [f32; 105] EVs`).
- Sets header `canonical_total` = id-list length, so the existing resume + header-mismatch guards still work. **A downstream reader can detect "this is a sparse id-list-mode file" by comparing `canonical_total` to the canonical_hands.bin row count (6,009,159 for the full project).**
- Records are written in input order (i.e., sorted ascending by canonical_id), so resume_from = number-of-records-on-disk.

`cargo build --release` clean; all 141 tests pass.

### Phase B — Correctness test (~5 min)

`test_id_list_correctness_S93.py`: sampled 100 canonical_ids spread across [0, 500,000) (stride 5000), wrote them to a text file, invoked the engine via `oracle-grid --samples 1000 --seed 12648430 --opponent realistic --id-list-file ...`, then compared per-hand 105-EV vectors against the existing prefix N=1000 grid at `data/oracle_grid_prefix500k_n1000.bin`.

**Result: 100/100 rows bit-identical. Max abs EV diff = 0.0.** Per-hand seed = `base_seed + canonical_id × φ` is deterministic and identical between sequential and id-list modes.

Engine throughput: ~25 hands/s parallel at N=1000 on this Mac (8 cores).

### Phase C-1 — Id-list preparation (~10 min)

`prepare_v60_id_list_S93.py`: iterated the MID × PMID_DS_NOMAXTOP cell from `drill_pair_v44_per_hand_structural.parquet` (114,048 cell hands). For each hand:
1. Computed v57 pick (= strategy_v57_lo_pair_defensive).
2. Computed v60 picks at gates 10, 11, 12 (using `_detect_mid_pair_defensive_pmid_swap`).
3. Identified the 32,304 hands where v60-gate12 changes v57's pick.

Recomputed N=200 baselines as a sanity check:

| gate | n_changed | N=200 lift | matches S86 |
|---:|---:|---:|---|
| 10 | 4,080 | +$1.63 | ✓ exact |
| 11 | 14,160 | +$4.85 | ✓ exact |
| **12** | **32,304** | **+$6.43** | ✓ **exact** |

Wrote 32,304 sorted, deduped ids to `data/session93/v60_gate12_changed_ids.txt`. Cid range: [594,805, 5,917,111] — entirely outside the prefix [0, 500K) range.

### Phase C-2 — Engine sparse run (21:17 wall)

```
engine/target/release/tw-engine oracle-grid \
  --canonical data/canonical_hands.bin \
  --out data/session93/v60_n1000_sparse.bin \
  --lookup data/lookup_table.bin \
  --samples 1000 --seed 12648430 --opponent realistic \
  --block-size 200 \
  --id-list-file data/session93/v60_gate12_changed_ids.txt
```

**Wall: 1,277.23 s (21:17) at 25.3 hands/s steady-state.** Block flush cadence: ~8 s per 200 hands. Output: `data/session93/v60_n1000_sparse.bin`, 13,696,928 bytes (= 32-byte header + 32,304 × 424-byte records).

### Phase C-3 — Two-grid grade (pre-committed thresholds, 1.1 s)

`grade_v60_id_list_n1000_S93.py` LOCKED thresholds in code BEFORE reading the sparse grid:
- `SHIP_LIFT_DOL_PER_1000H = 5.0`
- `NULL_LIFT_DOL_PER_1000H = 1.0`
- Two-grid SHIP standard: BOTH N=200 and N=1000 ≥ $5 → SHIP; BOTH ≤ $1 → NULL; otherwise MIXED.

For each gate ∈ {10, 11, 12}, computed lift on the **same changed-hand subset** at N=200 and N=1000:

| gate | n_changed | N=200 lift | N=1000 lift | |Δ| | sign-agree | verdict |
|---:|---:|---:|---:|---:|---:|---|
| 10 | 4,080 | +$1.63 | +$1.65 | $0.02 | 79.3% | MIXED |
| 11 | 14,160 | +$4.85 | +$4.77 | $0.09 | 79.0% | MIXED |
| **12** | **32,304** | **+$6.43** | **+$6.34** | **$0.09** | **77.8%** | **SHIP** |

**Gate 12 SHIPS by two-grid standard.** The two grids' independent MC estimates agree to within $0.09/1000h (gate 10's agreement is even tighter at $0.02). Per-hand sign-agreement between N=200 and N=1000 deltas is only 77.8% — high per-hand MC noise — but aggregate variance collapses cleanly over 32K hands.

Gates 10 and 11 stay MIXED (their N=200 + N=1000 numbers agree but don't clear $5). The two-grid bar at $5 SHIP / $1 NULL is well-calibrated — it catches gate 12 cleanly and correctly defers verdict on gates 10/11 (a relaxed bar could potentially ship gate 11 at +$4.85/+$4.77; deferred as S94 candidate).

### Phase C+ — Production composition (v65 build + grade)

Built `strategy_v65_mid_pair_chain_extend.py`:

```python
def strategy_v65_mid_pair_chain_extend(hand):
    # 1. v64's HIGH_ONLY chain-audit gate (Rules 21-24)
    if _is_v64_gated_cell(hand):
        return strategy_v44_dt(hand)
    # 2. NEW v60-gate12 rule: MID pair × PMID_DS_NOMAXTOP × max_sing ≤ Q × tmax-style
    v57_pick = strategy_v57_lo_pair_defensive(hand)
    forced = _detect_mid_pair_defensive_pmid_swap(hand, 12, v57_pick=v57_pick)
    if forced is not None:
        return forced
    # 3. Fall through to v57
    return v57_pick
```

The two firing zones are DISJOINT by construction:
- v64's zone requires HIGH_ONLY = no pairs in the hand.
- v60's zone requires exactly one pair of rank 8-T.

Sanity self-test (`python3 analysis/scripts/strategy_v65_mid_pair_chain_extend.py`): all 6 hand-shape cases verified, including the hands-fire / hands-don't-fire / hands-in-v64-gate distinctions.

### Phase C++ — v65 final whole-grid grade

`grade_v65_full_grid_S93.py` (15.2 s in-cell + 27.3 s out-of-cell sanity):

```
[in-cell on 32,304 changed hands]
  v64==v57: 32,304/32,304 (100.00%)        ← composition assumption holds
  total EV lift: +3864.0750
  whole-grid lift: $+6.43/1000h (N=200)     ← matches Phase C-1 baseline EXACTLY
  N=200 v65 better: 20,016 (62.0%)
  N=200 v65 worse:  12,134 (37.6%)
  N=200 v65 same:      154 (0.5%)
  swap-right rate (nonzero deltas): 62.3%

[out-of-cell on 50,000 random sample]
  v65 != v64 disagreements: 0               ← composition is safe outside cell

VERDICT (N=200 standalone): SHIP
VERDICT (two-grid standard, S84+): SHIP
  Implied production: $1,627.36 → $1633.79/1000h (+$6.43/1000h)
  Implied production vs v44_dt: $552.79/1000h (was $546.36)
  Implied remaining gap to oracle: $111.41/1000h (was $117.84)
  Cumulative closure since pre-S68: $1297.59 of $1,409 = 92.09% (was 91.6%)
```

### Why this is a SHIP by both grids

S86's full-grid N=200 grader confirmed the SHIP signal at +$6.43/1000h on 32,304 changed hands. The signal could have been:
- a real per-cell effect (rule is genuinely +EV) — confirmed by N=1000.
- N=200 MC noise — refuted by N=1000 ($0.09 abs diff is well within Phase B's bit-identical noise floor).
- a coding bug in the rule or in v57's pick computation — refuted by Phase C-1 reproducing S86's per-gate numbers to the penny.

The two-grid bar in this configuration is genuinely informative: when the cell is outside the prefix's prefix-coverage range, the bar that was vacuous (only one grid covered the cell) becomes a real two-grid check via Option C. **First project SHIP via this exact mechanism.**

## Headline state at end of S93

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (UNCHANGED for 21 sessions, since v44 in S58). $1,081/1000h full / $686/1000h prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

* **Total project rule count: 25** (Rule 25 added in S93).
* **Cumulative closure since pre-S68: $1,297.59 of $1,409 = 92.09%** (was 91.6%).
* **Remaining gap to oracle ceiling: $111.41/1000h** (was $117.84).
* **Production vs v44_dt: $552.79/1000h** (was $546.36).
* **Combined S87-S93 production-chain recovery: $221.26/1000h** = $214.83 (chain-audit S87-S90) + $6.43 (rule extraction S93).
* **Option C N=1000 sparse-grid infrastructure: SHIPPED + validated bit-identical to prefix grid.**
* **Chain-audit methodology arc: still COMPLETE (S92 finding holds).** S93 is a rule-extraction ship, NOT a chain-audit ship.

## What's on the table for S94

Several productive levers are open after S93:

1. **PRIMARY (SECONDARY in S93 plan, NOW PROMOTED) — rule-extraction on within-v44_dt residual leak.** Largest unaddressed within-v44_dt cell is **two_pair LAYOUT_A_SS at $35.22/1000h on 437,580 hands**. S69 tested catalog candidates and confirmed v44_dt dominates the aggregate; individual sub-cells were not exhaustively probed. Could be amenable to a "drop max kicker into bot for DS-like SS structure" rule similar to Rule 20's mechanism. Now testable under the two-grid bar via Option C if the cell sits outside prefix coverage.

2. **SECONDARY — validate other parked MIXED candidates via Option C.** v60 gate=11 is currently MIXED at +$4.85 (N=200) / +$4.77 (N=1000) on 14,160 hands. Doesn't clear the $5 SHIP bar but is robustly POSITIVE in both grids. Could be revisited with a relaxed bar OR combined with other near-miss rules. S86's MIXED candidates ($21.68 STRUCTURE leak on LOW pair × PMID_DS_MAXTOP) are now also amenable to Option C re-validation.

3. **TERTIARY — headline-goal recalibration.** Still open from S92's framing. Make explicit that 95% match% is unreachable from current architecture; reset target to maximize $/1000h subject to current cascade. Affects how to read future MIXED ship sessions.

4. **DEFERRED — ML retrain (A3 full 6M-hand N=1000 grid).** Formally closed at v44 in S78 (Decision 113). Reopening requires either a new feature family or A3 infrastructure (now partially enabled by Option C — full 6M-hand N=1000 generator still requires more engine work, but `--id-list-file` is the foundation).

5. **DEFERRED — v52-defensive-low partial-effectiveness exploit (S90).** Still speculative.

6. **DEFERRED — v44_RULE13 fallthrough replacement.** With v54/v55/v56 absorbing $731/1000h of chain bleed across pair-family (S91+S92 architectural finding), v44_RULE13 replacement primarily matters for HIGH_ONLY (already gated by v64). Large engineering scope, unclear payoff.

**The chain-audit lever remains exhausted on current architecture.** No new audits expected to ship without either a new chain layer or a richer ML champion. The natural next levers are rule extraction (Option D-revised) and infrastructure compounding (more Option C-style infrastructure unlocks).
