# Session 97 — Maintenance lever STRUCTURAL NULL. **Production v65 UNCHANGED.** v60-gate11 "parked MIXED at +$4.85/+$4.77" is empirically absorbed by v65 (Rule 25 = v60-gate12 covers it with identical picker on 14,160/14,160 firing hands). Composite hypothesis collapses to v66-NARROW alone, which is locked MIXED at +$4.59/+$4.75 per S95. Decision 132 closes the maintenance lever.

_Generated 2026-05-16. One new analysis script + one JSON output. No engine runs. No production change. v44_dt UNCHANGED for 25th consecutive session._

## TL;DR — Plain language

**What changed in your strategy of record:** **Nothing.** v65 remains production at $1,633.79/1000h full grid / $776.88 prefix. v44_dt remains ML champion (25th consecutive session). Rule count UNCHANGED at 25.

**What this session ruled out.** S97 was authorized as a "maintenance composite" pass — the idea was to combine the two parked MIXED candidates (v60 gate-11 at $+4.85/$+4.77 from S93; v66-NARROW at $+4.59/$+4.75 from S95) into a joint ~$9/1000h composite ship. The first candidate turned out to be a structural ghost: **v60-gate11 has already been absorbed by v65 since Rule 25 shipped in S93, but the cascade documentation never updated to reflect that.** The $+4.85 number was measured against the pre-Rule-25 v57 baseline, not against current production v65.

**Why v60-gate11 is absorbed by v65:**

* Rule 25 (= v60-gate12) fires on MID pair × PMID_DS_NOMAXTOP × `max_sing ≤ Q`, using the picker `_detect_mid_pair_defensive_pmid_swap`.
* v60-gate11 fires on MID pair × PMID_DS_NOMAXTOP × `max_sing ≤ J`, using **the same picker**.
* `max_sing ≤ J` is a strict subset of `max_sing ≤ Q`, and the picker output depends only on the hand (not on the gate parameter once the firing condition is met). So every hand that fires at gate=11 also fires at gate=12, and both produce the **identical** PMID_tnomax_DS setting.
* Empirical proof (this session): 14,160 / 14,160 = **100%** of gate-11 firing hands have `v65_pick == v60_gate11_pick`. Zero hands fall through to v57. The structural claim is exact.

So the composite hypothesis reduces to **v66-NARROW alone** — and S95 already characterized that as MIXED at $+4.59 N=200 / $+4.75 N=1000 (both grids ~$0.25 short of the $5 SHIP bar). No production change is achievable from the maintenance lever.

**Decision 132 (NEW)** closes the maintenance lever as STRUCTURAL NULL. v60-gate11 is removed from the "open candidates" list. v66-NARROW remains characterized as MIXED at the existing two-grid bar.

**Methodology lesson from S97.** A "parked MIXED candidate" measured against baseline at session N is no longer comparable once a related candidate from the same cell ships. Future "parked candidate" book-keeping should record (a) the baseline strategy used in the original grading, and (b) a re-grade-against-current-production check before any composite hypothesis. The +$4.85 number in CURRENT_PHASE.md was true at the time it was measured but became stale the moment Rule 25 (gate=12) shipped, since gate=11 hands are a strict subset of gate=12's firing zone.

**What's on the table for S98:**
1. **A3 ML retrain** — still PRIMARY, still operator-authorization-gated. ~70h wall on current hardware. Honest expected outcome: NULL more likely than SHIP. Only remaining lever with $50+/1000h recovery potential.
2. **v52-defensive-low partial-effectiveness exploit** — SECONDARY, speculative. Per-hand picker between v52-DL and v44_dt on the ~23% of S90 hands where v52-DL wins (Decision 125).
3. **v44_RULE13 fallthrough replacement** — TERTIARY, likely modest at best.

The maintenance option (S96's MAINTENANCE branch) is now CLOSED. The "parked MIXED candidates" subset is exhausted.

**The numbers (UNCHANGED from S96):**
* Production v65: **$1,633.79/1000h full grid / $776.88 prefix**
* v44_dt: **$1,081 full / $686 prefix** (UNCHANGED for **25 consecutive sessions**, since v44 in S58)
* Production vs v44_dt: **$552.79/1000h**
* Remaining gap to oracle ceiling: **$111.41/1000h**
* Cumulative closure since pre-S68: **$1,297.59 of $1,409 = 92.09%**
* Rule count: **25** (UNCHANGED)

---

## The full story

### Phase A — relocate both parked candidates

Located:
* `analysis/scripts/strategy_v60_mid_pair_ds_nomaxtop.py` — gate=11 default export. Picker `_detect_mid_pair_defensive_pmid_swap(hand, gate=11, v57_pick=...)`. Fires when:
  1. exactly one pair, pair_rank ∈ {8, 9, T};
  2. `max_sing ≤ 11` (gate parameter);
  3. cell = PMID_DS_NOMAXTOP (no PBOT_DS achievable, PMID_DS achievable, no PMID_DS_w_maxtop);
  4. v57's current pick is PMID_tmax-style.
  → returns best PMID_tnomax_DS setting (DS bot incl. max_sing, top = leftover singleton).

* `analysis/scripts/strategy_v66_trips_layout_a_force_ds_bot.py` — NARROW gate default export. Picker `_detect_trips_layout_a_force_ds_bot(hand, NARROW, v65_pick=...)`. Fires when:
  1. exactly trips (one trip-rank, no pairs, no quads);
  2. cell = B_DS_AVAIL_LKR (b_ds_avail AND best_b_ds_kicker_2nd_rank < 10);
  3. sub-bucket (ksc, nkts, nbds) ∈ {(2,4,1), (3,4,1)};
  4. v65 picks Layout A with non-DS bot.
  → returns best Layout-A DS-bot setting via `TOP_HIGH`-first picker (S95 finding).

### Phase B — structural finding before any code runs

* v65 (= `strategy_v65_mid_pair_chain_extend`) ships v60 at `V65_MID_PAIR_GATE = 12`, calling **the same picker function** that v60-gate11 calls.
* The only difference between v60-gate11 and v65's Rule-25 layer is the `max_sing_gate` parameter (11 vs 12).
* The firing predicate is `max_sing_rank > max_sing_gate → return None`. So:
  - gate=11 returns the forced setting when `max_sing ≤ J`.
  - gate=12 returns the forced setting when `max_sing ≤ Q`.
  - For any hand with `max_sing ≤ J`, both gates fire AND produce the **same** setting (the picker downstream is deterministic in the hand).
* Therefore: every hand at which v60-gate11 fires is also handled by v65 with the identical pick. The "+$4.85 N=200 / +$4.77 N=1000" lift number from S93 grading was measured against the **v57 baseline** (pre-Rule-25); not against current production v65.

**Reading the S93 grading JSON (`data/session93/grade_v60_n1000_summary.json`):**

| Gate | n_changed | Lift N=200 | Lift N=1000 | S93 verdict | Baseline |
|---|---:|---:|---:|---|---|
| 10 (T) | 4,080 | $+1.63 | $+1.65 | MIXED | v57 |
| 11 (J) | 14,160 | $+4.85 | $+4.77 | MIXED | v57 |
| **12 (Q)** | **32,304** | **$+6.43** | **$+6.34** | **SHIP → Rule 25 / v65** | **v57** |

Gate=12 shipped as Rule 25, becoming part of v65. Gate=11's 14,160 firing hands are a strict subset of gate=12's 32,304 firing hands. Gate=11's $+4.85/$+4.77 was double-counting what Rule 25 was already going to handle.

### Phase C — empirical confirmation

`analysis/scripts/spot_check_v60g11_subset_v65_S97.py`:

1. Loaded `data/session93/v60_per_hand_picks.npz` — `canonical_id`, `v57_pick`, `v60_pick_g{10,11,12}` for the full 114,048-hand MID × PMID_DS_NOMAXTOP cell.
2. Identified `g11_changed = (v60_pick_g11 != v57_pick)` → **14,160 hands** (matches S93).
3. Sanity: `g11_changed_mask ⊆ g12_changed_mask` → **True** (every gate-11 firing hand also fires at gate=12).
4. Sanity: `v60_pick_g11 == v60_pick_g12` on the 14,160 g11-fired hands → **14,160 / 14,160 = 100.0000%**. The picker outputs are identical, confirming the gate parameter is the only differentiator.
5. Empirical: for each of the 14,160 g11-fired hands, decoded the hand via `canonical_hands.bin` and computed `strategy_v65_mid_pair_chain_extend(hand)`. Result:

| Quantity | Value |
|---|---:|
| Gate-11 firing hands | 14,160 |
| v65 == v60_gate11 on these hands | **14,160 (100.0000%)** |
| v65 == v57 on these hands | 0 (0.0000%) |
| v65 picks neither | 0 |

Wall time: 3.4s on a single core. Output: `data/session97/spot_check_v60g11_subset_v65.json`.

**Verdict: STRUCTURAL_ABSORPTION_CONFIRMED.** Incremental lift of v60-gate11 over v65 = **$0**.

### Phase D — composite reduces to v66-NARROW alone

The composite hypothesis was: ship `v67 = v65 + v60_gate11_picker + v66_NARROW_picker`. The two pickers fire on disjoint cell families (MID pair vs trips), so per-hand lifts would be additive.

* v60-gate11 contributes **$0** over v65 (structural absorption).
* v66-NARROW contributes **$+4.59 N=200 / $+4.75 N=1000** over v65 (S95 grading, `data/session95/grade_v66_n1000_summary.json`).

So `v67 = v65 + v66_NARROW`, with composite lift = v66-NARROW's lift = $+4.59 / $+4.75 — locked **MIXED** by the existing pre-committed two-grid SHIP bar ($5 on both grids). No re-grade is required; v66-NARROW vs v65 has not changed since S95.

### Phase E — Decision 132 closure

The maintenance lever is closed as STRUCTURAL NULL (no production change achievable from re-evaluation of the two parked candidates):

* v60-gate11: absorbed by v65 since Rule 25 shipped. Remove from the "open candidates" list.
* v66-NARROW: locked MIXED by the two-grid SHIP standard, $0.25 short on each grid.

The "parked MIXED candidates" subset (S96 MAINTENANCE option) is fully characterized. With chain-audit (Decision 127), rule-extraction bucket-level (Decision 129), rule-extraction intra-layout (Decision 130), and now maintenance composite (Decision 132) all closed, the remaining open levers on the current ML architecture are:

* **A3 ML retrain** — operator authorization required; honest expected-NULL prior per Decisions 113 + 117; only remaining lever with $50+/1000h potential.
* **v52-defensive-low exploit** — speculative; per-hand picker between v52-DL and v44_dt on the ~23% of S90 hands where v52-DL wins (Decision 125).
* **v44_RULE13 fallthrough replacement** — likely modest impact at best.

### Verdict + production state

**VERDICT: MAINTENANCE LEVER STRUCTURAL NULL.** Production v65 UNCHANGED.

| metric | pre-S97 (v65) | post-S97 (v65) | Δ |
|---|---:|---:|---:|
| Full grid (N=200) | $1,633.79 | $1,633.79 | $0.00 |
| Prefix grid (N=1000) | $776.88 | $776.88 | $0.00 |
| Production vs v44_dt | $552.79 | $552.79 | $0.00 |
| Remaining gap to oracle | $111.41 | $111.41 | $0.00 |
| Cumulative closure since pre-S68 | 92.09% | 92.09% | 0.00pp |
| Rule count | 25 | 25 | 0 |

* v44_dt ML champion: UNCHANGED ($1,081 full / $686 prefix) — **25 consecutive sessions** running.
* Combined S87-S93 production-chain recovery: $221.26/1000h. **S94, S95, S96, S97 contribute $0.**

### Methodology lessons (S97)

1. **Parked candidates are baseline-relative; re-grade against current production before composing (NEW S97).** A candidate's "+$X over baseline B" reading is only meaningful as a composite component if no related candidate from the same cell has shipped since B was measured. v60-gate11's +$4.85 was true vs v57; the moment v60-gate12 (= Rule 25) shipped, the +$4.85 became double-counting against current production. Future "parked candidate" book-keeping should record (a) the baseline strategy used and (b) a re-grade-against-current-production check before any composite hypothesis. This lesson sits one rung above Decision 131's doc-drift lesson — that one was about zombie *headline* framing; this one is about zombie *candidate* framing.

2. **Structural subset checks are cheap and decisive (carried, reinforced S97).** Cells like `max_sing ≤ J` ⊂ `max_sing ≤ Q` are immediately testable on the per-hand picks NPZ that already exists; no engine run is needed to decide whether a candidate is structurally absorbed by current production. ~5 minutes of code + 3.4 seconds of compute resolved the question; if the structural relationship had been checked at S93 SECONDARY framing time, the v60-gate11 candidate wouldn't have been carried as "open" for 4 sessions.

3. **The MAINTENANCE option's framing was honest but its components were stale (NEW S97).** S96 CURRENT_PHASE.md line 127 said "v60 gate=11 currently MIXED at +$4.85/+$4.77; eligible for relaxed-bar or composite-rule re-evaluation." The "currently MIXED" language did not account for the fact that the candidate's firing zone had since been absorbed by v65. The fix is the previous methodology lesson; the broader observation is that a "currently MIXED at $X" annotation should always carry the strategy-of-record name the $X was measured against.

### Artifacts (Session 97)

**One new analysis script + one JSON output. No code changes to strategy or engine.**

* `analysis/scripts/spot_check_v60g11_subset_v65_S97.py` — empirical verifier of v60-gate11 ⊂ v65 (NEW)
* `data/session97/spot_check_v60g11_subset_v65.json` — structural-absorption result (NEW)
* `SESSION_97_REPORT.md` — this file (NEW)
* `DECISIONS_LOG.md` — Decision 132 appended (APPEND)
* `CURRENT_PHASE.md` — rewritten in place for S98 (REWRITE)
* `STRATEGY_GUIDE.md` — front-matter "Last updated" stanza updated for S97; Part 1 entry NOT added (no production change, mirroring S96 convention) — note in commit
* `MASTER_HANDOFF_01.md` — S97 entry appended (APPEND)
* `sprints/SPRINT_INDEX.md` — S97 entry appended (APPEND)

### State at end of S97

**Strategies of record (UNCHANGED from S96):**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v65_mid_pair_chain_extend** | PRODUCTION rule chain. **$1,633.79/1000h full / $776.88/1000h prefix**. | `analysis/scripts/strategy_v65_mid_pair_chain_extend.py` |
| **v44_dt** | PRODUCTION ML champion (**UNCHANGED for 25 sessions**, since v44 in S58). $1,081 full / $686 prefix. | `analysis/scripts/strategy_v44_dt.py` + `data/v44_dt_model.npz` |

* **Total project rule count: 25** (UNCHANGED).
* **Cumulative closure since pre-S68: $1,297.59 of $1,409 = 92.09%** (UNCHANGED).
* **Remaining gap to oracle ceiling: $111.41/1000h** (UNCHANGED).
* **Production vs v44_dt: $552.79/1000h** (UNCHANGED).
* **Combined S87-S93 production-chain recovery: $221.26/1000h** (UNCHANGED). S94, S95, S96, S97 contribute $0.
* **Chain-audit methodology arc: COMPLETE** (S92 closure holds).
* **Rule-extraction (Option D-revised) lever — both sub-classes: SATURATED** (S94 + S95 closures hold).
* **Headline metric: $/1000h on the production grid** (Decision 131, S96).
* **Maintenance lever: CLOSED (Decision 132, S97). Both parked candidates accounted for: v60-gate11 STRUCTURALLY ABSORBED; v66-NARROW MIXED at $+4.59/$+4.75.**

## What's on the table for S98

1. **PRIMARY — A3 ML retrain (full 6M × 105 × N=1000 grid).** Formally closed at v44 in S78 (Decision 113); reopening requires operator authorization. Option C infrastructure provides the foundation; ~70 hours wall on current hardware. The only remaining lever with potential to recover $50+/1000h. Honest expected-outcome prior: NULL more likely than SHIP per Decisions 113 + 117. Substantial compute investment for credibility-low payoff.

2. **SECONDARY — v52-defensive-low partial-effectiveness exploit.** Per-hand picker between v52-defensive-low and v44_dt on the ~23% of S90 hands where v52-DL wins (Decision 125). Speculative, smaller magnitude than A3, cheaper to evaluate. Could be characterized in a single session with no Option C compute.

3. **TERTIARY — v44_RULE13 fallthrough replacement.** With v54/v55/v56 absorbing $731+/1000h of chain bleed across pair-family, replacement primarily matters for HIGH_ONLY (already gated by v64/v65). Likely modest impact at best.

The MAINTENANCE option is now CLOSED (Decision 132).
