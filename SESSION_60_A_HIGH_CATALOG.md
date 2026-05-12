# Session 60 — A-High Cell-by-Cell Catalog

*Generated: 2026-05-11 — first page of `HIGH_ONLY_RULE_CATALOG.md`. Session 60 audits Rule 14 (A-high HIMID, S50) cell-by-cell against the realistic-mixture oracle grid and tests 10 candidate refinement rules across A-high's three biggest leaky cells.*

## TL;DR — A-high catalog verdict: ALL CELLS ML-ONLY (T3)

After cell-by-cell audit of Rule 14 and 10 candidate refinements:

- **Rule 14 (S50, A-high HIMID) is empirically validated**: harness reproduces +$131.25/1000h whole-grid (matches CURRENT_PHASE's documented S50 ship to within 0.2%).
- **Every A-high cell leaks substantially to oracle ceiling** ($1,500–$3,700/1000h within-cell), with `DS_NO_JOINT` accounting for 58% of the remaining gap.
- **Every candidate tested falls below Threshold 1** (≥40% gap closure AND ≥+$3/1000h within-cell vs v52). 5 of 10 were net-NEGATIVE on $1000h whole-grid. 1 was structurally unfireable (0% fires). 4 fired with small positive lift but well under T1.
- **A-high's residual is ML-only territory.** v44_dt's $182.51/1000h whole-grid A-high residual is the closer-to-oracle benchmark; the candidate space explored here cannot meaningfully close the $281/1000h Rule-14-to-oracle gap on A-high without sophisticated multi-feature gating that the catalog methodology doesn't allow.
- **No shipped rule from Session 60.** No change to the production rule chain. v52_full_high_only_handler ($2,498 full / $1,522 prefix) and v44_dt ($1,081 / $686) both UNCHANGED.

The harness (`analysis/scripts/test_rule_catalog.py`) and the cell-tagging infrastructure are **PROVEN AND READY** for Session 61 (K-high), where the structural decision matrix is different (oracle drops K off top 34% in DS_NO_JOINT, vs 6% for A-high) and the candidate space may yield clearable thresholds.

## Method

The harness:
1. Loads `data/drill_ho_v44_per_hand_structural.parquet` (S59 artifact — per-hand structural cell tags + oracle/v44 picks).
2. For each candidate `rule_fn`, filters to `(max_rank=14, cell=X)`.
3. Per hand: computes `rule_fn(h)` (None = pass-through to baseline_fn) and `baseline_fn(h) = v52_full_high_only_handler(h)`.
4. Looks up oracle EV (= max of `oracle_grid[cid]`), v44 EV (= `oracle_grid[cid][v44_idx]`), rule EV, baseline EV.
5. Aggregates: within-cell + whole-grid lift in $/1000h, capture% vs baseline and v44, % optimal, and rule-vs-oracle mismatch class breakdown.

Sanity check: Rule 14 vs its pre-Rule-14 predecessor (`strategy_v44_rule13_three_pair_DS`) returns **+$131.25/1000h whole-grid lift on A-high** — matching CURRENT_PHASE's documented S50 ship ($131) to within 0.2%. **Harness validated.**

## Part 1 — Rule 14 cell-by-cell audit

After Rule 14 fires, what gap to oracle remains in each A-high cell?

| Cell | n hands | R14 mean_ev | Oracle mean_ev | Gap within-cell | Gap WG | v44 mean_ev | v44 gap WG |
|---|---:|---:|---:|---:|---:|---:|---:|
| JOINT_HIGH | 88,200 | +0.841 | +1.023 | $1,822/1k | $26.7 | +0.922 | $14.9 |
| JOINT_MED | 8,715 | -0.150 | +0.005 | $1,549/1k | $2.3 | -0.078 | $1.2 |
| JOINT_LOW | 105 | -1.348 | -1.193 | $1,552/1k | $0.0 | -1.274 | $0.0 |
| **DS_NO_JOINT** | **415,800** | **+0.508** | **+0.742** | **$2,337/1k** | **$161.7** | **+0.562** | **$124.8** |
| DS_NO_MAXTOP | 88,704 | +0.077 | +0.450 | $3,734/1k | $55.1 | +0.291 | $23.5 |
| MS_ONLY | 59,136 | -0.107 | +0.252 | $3,598/1k | $35.4 | +0.069 | $18.1 |
| **A-high total** | **660,660** | — | — | — | **$281.2** | — | **$182.5** |

**Two takeaways from the audit:**

1. **DS_NO_JOINT is the dominant residual cell at A-high** ($161.7/1000h WG remaining gap = 58% of A-high's post-Rule-14 leak). This is exactly where S59's `drill_high_only_v44_nonmax_quality.py` pinpointed v44_dt's worst residuals.
2. **v44_dt outperforms Rule 14 within every cell.** v44 captures ~$99/1000h more than Rule 14 on A-high overall. The biggest v44-vs-Rule-14 deltas are in DS_NO_MAXTOP ($31.6/1000h WG advantage to v44) and MS_ONLY ($17.4/1000h advantage). v44 sees structural features (n-broadway, n-suited-pairs, ho_v2..v4) that Rule 14's enumeration ignores.

## Part 2 — Candidate refinement rules tested

10 candidates targeting the top-3 leaky cells. Each candidate fires only inside its target cell (`_is_A_high_no_pair` + cell predicate); when it doesn't fire, v52 (=Rule 14 on A-high) is used.

| ID | Candidate | Cell | Fires | cap_b | $/cell | $/1000h WG | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| C1 | DSnj_SSms_any | DSnj | 93.3% | −60.0% | −$1,401 | −$96.9 | T3 |
| C2 | DSnj_SSms_J | DSnj | 62.8% | −29.1% | −$680 | −$47.0 | T3 |
| C3 | DSnj_SSms_T | DSnj | 74.1% | −37.7% | −$881 | −$61.0 | T3 |
| C4 | DSnj_SSms_beats_DSpair | DSnj | 0.0% | 0.0% | $0 | $0 | T3 (no fires) |
| C5 | DSnm_SSms_any | DSnm | 31.2% | 0.0% | $0 | $0 | T3 (= R14) |
| C6 | DSnm_31ms_when_no_SSms | DSnm | 6.2% | +2.1% | +$78 | +$1.15 | T3 |
| C7 | MSonly_31ms_when_no_SSms | MSonly | 18.8% | +6.1% | +$219 | +$2.15 | T3 |
| C8 | MSonly_31ms_any | MSonly | 18.8% | +6.1% | +$219 | +$2.15 | T3 |
| C9 | DSnj_drop_A_for_AK_DSms | DSnj | 51.1% | −175.5% | −$4,101 | −$283.8 | T3 (catastrophic) |
| C10 | DSnj_HIBOT_tiebreaker | DSnj | 100.0% | −24.5% | −$573 | −$39.7 | T3 |

(`cap_b` = gap closure vs v52 baseline. `$/cell` = within-cell lift in $/1000h. `$/1000h WG` = whole-grid lift.)

## Part 3 — Why every candidate failed (data-driven)

### DS_NO_JOINT (C1–C4, C9–C10)

S58's decision matrix said oracle picks `tA_SS_ms` 27.9% of DS_NO_JOINT (n≈116K, $3,613/hand mean regret if v43/Rule-14 stays with DS_mu). The naive read: "switch DS_mu → SS_ms whenever SS_ms is achievable" should recover most of that. The harness says: **no — switching unconditionally hurts more than it helps.**

- **C1 (SS_ms whenever achievable):** fires 93.3% of cell (most DSnj hands HAVE an SS_ms config). Of those fires, the 28% where oracle agrees gives back $3,613/hand; the 72% where oracle prefers DS_mu loses $1,900-ish/hand (estimated from the −$1,401/cell net). Switching costs more than it gains because the simple gate (SS_ms exists) doesn't distinguish "SS_ms is better here" from "DS_mu is better here."
- **C2/C3 (gate on mid_high):** Tightening to mid_high ≥ J or ≥ T reduces fires from 93% → 63%/74%, but still net-negative. The mid_high gate doesn't pick the right 28%.
- **C4 (relative gate: SS_ms mid_high > DS bot pair_high):** fires **0.0%**. Structural reason: in DS_NO_JOINT, when SS_ms is achievable with a high mid_high, the DS bot inherits the strongest remaining pair which is typically ≥ the SS_ms mid_high. The relative gate is structurally too tight.
- **C9 (drop A off top when bot pair_high ≥ J):** fires 51.1%, catastrophic −$284/1000h WG. The mismatch breakdown is brutal — C9 picks `t2_DS_ms` 13,701 times where oracle picks `tA_DS_mu` at $10,837/hand mean regret. A drops off top in only ~6% of DSnj hands per oracle; C9's gate fires on 51% — the wrong 45% are exactly where A SHOULD stay on top.
- **C10 (HIBOT tiebreaker):** 100% fire (always overrides Rule 14's HIMID), −$574/cell. **Confirms Rule 14's HIMID design from S50 is empirically correct.** HIBOT (favor strongest DS bot pair) loses to HIMID (favor strongest mid_rank_sum) by $574/cell.

**Structural finding:** in DS_NO_JOINT, oracle's choice between {A-top DS_mu, A-top SS_ms, A-top 31_ms, K-top DS_ms} depends on subtle interactions of bot pair_high, mid_high, suited mid quality, and 4-flush risk that no single-axis deterministic rule captures. v44_dt encodes these via 107 features and 2.25M leaves; a rule-chain refinement here would need 5+ feature gates and 10+ branch logic — outside the catalog's "one sentence statable" constraint.

### DS_NO_MAXTOP (C5, C6) and MS_ONLY (C7, C8)

C5–C8 produced tiny positive lift ($1–$2/1000h WG) — well under T1's $3 within-cell threshold and T2's $5 whole-grid threshold. Reasons:

- **C5 returned 0 capture** because A-top SS+ms is what Rule 14 falls back to in DS_NO_MAXTOP when SS is achievable. C5 is effectively the no-op.
- **C6/C7/C8 (31_ms branches):** fire 6–19% of cells (where 31_ms exists but SS_ms doesn't), small positive capture. The lift is real but in absolute terms (~$1–$2/1000h WG) sits below the production-shipping threshold. These could ship if combined into a larger catalog rule, but in isolation they don't clear T2.

## Part 4 — Honest ML-only labeling

A-high's residual gap to oracle ($281/1000h WG) is split across cells:

| Cell | WG residual after R14 | v44 captures (more than R14) | Net ML-only territory |
|---|---:|---:|---:|
| JOINT_HIGH | $26.7 | $11.8 | $14.9 ML |
| JOINT_MED | $2.3 | $1.1 | $1.2 ML |
| JOINT_LOW | $0.0 | $0.0 | $0.0 — |
| DS_NO_JOINT | $161.7 | $36.9 | $124.8 ML |
| DS_NO_MAXTOP | $55.1 | $31.6 | $23.5 ML |
| MS_ONLY | $35.4 | $17.4 | $18.1 ML |
| **A-high total** | **$281.2** | **$98.8** | **$182.5 ML** |

**For Session 60's purpose, all A-high cells are labeled ML-only** — the catalog space explored doesn't produce a Threshold-2 refinement for any of them. v44_dt's A-high residual ($182.5/1000h WG) is the ceiling a catalog refinement could close further — and even at the cell-most-promising (DS_NO_JOINT), the candidate space tested couldn't close it.

**This does not mean A-high is unrefinable forever.** It means:
1. Single-axis gates can't reproduce oracle's subtle DS_NO_JOINT routing.
2. Multi-axis gates (5+ features, branching) might work but violate the catalog's "human-memorizable" constraint.
3. The remaining $182.5/1000h WG belongs to v44_dt's exclusive territory at current rule chain depth.

## Part 5 — Implications for Session 61 (K-high)

K-high has a STRUCTURALLY DIFFERENT profile:

| Property | A-high | K-high |
|---|---:|---:|
| Population | 660,660 (53.8% of high_only) | 330,330 (26.9%) |
| WG residual after v52 | ~$280+ | TBD per Phase 2 |
| Oracle drops max off top in DSnj | **6%** | **34%** ← 5.6× higher |
| Oracle drops max off top in MS_ONLY | 2% | **22%** |
| Population in DSnj | 415,800 (62.9%) | 207,900 (62.9%) |

The "drop max off top" play is much more common at K-high than A-high. A candidate rule for K-high "drop K off top when alt structure is strong" should fire much more often, and the gate may be cleaner (K's value vs alternative tops differs more than A's). **The K-high catalog audit may produce shippable rules where A-high did not.**

**Recommended Session 61 plan:** Reuse the harness verbatim. Phase 2 audit Rule 15 (S51, K-high HIMID, +$51/1000h WG when shipped) cell-by-cell. Design candidates for K's `DS_NO_JOINT` cell focused on the 34% drop-K-off-top play (which the data structurally supports unlike A-high's 6% drop-A play). Test under same T1/T2/T3 thresholds.

## Part 6 — Files produced (Session 60)

| File | Purpose |
|---|---|
| `analysis/scripts/test_rule_catalog.py` | Reusable per-cell rule audit harness. Loads parquet + canonical hands + oracle grid once; tests `rule_fn` on `(max, cell)` subset; returns CatalogResult with all aggregate metrics. |
| `analysis/scripts/candidates_A_high_S60.py` | 10 candidate rules for A-high cells (C1–C10). |
| `analysis/scripts/test_A_high_candidates_S60.py` | Driver: runs every candidate through the harness, scores T1/T2/T3 verdicts, writes JSON. |
| `data/session_60_candidate_results.json` | Full results for C1–C8 (C9/C10 results in `/tmp/s60_candidates_pass2.log`). |
| `SESSION_60_A_HIGH_CATALOG.md` | This file. First page of the eventual `HIGH_ONLY_RULE_CATALOG.md`. |

The harness, candidate-test driver, and cell tagging infrastructure are **reusable as-is** for S61–S65. Each future session reuses `test_rule_catalog.py` unchanged and adds a new `candidates_<X>_high_S<NN>.py` + `test_<X>_high_candidates_S<NN>.py` pair.

## Part 7 — Methodology lessons (Session 60)

1. **The harness works and reproduces shipped lift.** Rule 14's known +$131/1000h whole-grid lift was reproduced to within 0.2%. The cell-tagging from S59's parquet is faithful. The methodology is sound.
2. **Decision-matrix percentages (S58) overstate refinement headroom.** "Oracle picks X 28% of the time" does NOT mean "switching to X always recovers EV." It means **oracle knows which 28%**. A deterministic gate that fires on hands "where X is achievable" includes BOTH the 28% where X is better AND the 72% where it's worse. Net effect can be very negative (C1: −$96.9/1000h WG).
3. **Within-class refinement is real but small.** C10 (HIBOT vs HIMID tiebreaker) showed Rule 14's S50 HIMID design was empirically correct; alternative tiebreakers cost EV. This is a useful retrospective validation.
4. **Multi-axis gates would help but violate the catalog's intent.** Closing the DS_NO_JOINT gap requires (mid_high × bot_pair_high × bot_run × suited_mid_route) joint optimization — that's a 107-feature DT, which is v44_dt. The whole point of the catalog is human-memorizable rules; if a rule needs 5 gates and 3 branches, the rule chain has reproduced ML, not abstracted it.
5. **ML-only labels are valid catalog content.** "This cell is ML-only, here's why: [data]" is a legitimate strategic insight. The user-facing strategy doc can honestly say "for A-high hands in this structural cell, defer to the ML model — no clean rule exists."

## Part 8 — User-directive accountability check

S59 user directive: *"Speed is not necessary — clarity and perfection is."*

Session 60 spent ~2 hours on the methodology pivot. No rule shipped. The result is a CLEAN ML-only verdict for A-high backed by 10 tested candidates and clean cell-by-cell audit numbers. The harness is reusable. **The "clarity" half of the directive is met; the "perfection" half acknowledges the limit of the catalog approach at A-high.**

Sessions 61–65 will produce the parallel catalogs for K/Q/J/T/9/8. If the same null pattern holds across all max-ranks, the final `HIGH_ONLY_RULE_CATALOG.md` will document **the boundary of human-memorizable strategy** — itself a publishable result of the project per CLAUDE.md's stated end-product goal.

---

*Session 60 end. Production rule chain: v52_full_high_only_handler. Production ML champion: v44_dt. Both UNCHANGED.*
