# `HIGH_ONLY_RULE_CATALOG.md` — The High-Only Rule Catalog

*The canonical synthesis of Sessions 60–64. Documents the boundary of human-memorizable strategy on the high_only category of Taiwanese Poker — the largest single rule-vs-ML gap zone (40.4% of canonical hands, $755/1000h whole-grid v44-framing residual, $381/1000h post-v44 ML-only residual). Produced Session 65, 2026-05-12.*

---

## Cover — TL;DR for the entire document

**Scope.** This catalog audits the production rule chain `v52_full_high_only_handler` cell-by-cell on every max-rank zone of the high_only category (A/K/Q/J/T/9/8 = seven distinct-rank no-pair zones spanning all 1,226,940 canonical high_only hands = 40.4% of the canonical-grid). For each (max-rank × structural cell) pair, it measures the gap between v52's per-hand pick and the realistic-mixture oracle's pick, tests human-statable refinement rules against three explicit thresholds (catalog-worthy / production-ship / ML-only), and labels each cell with its verdict.

**Result.** Across 1,226,940 canonical high_only hands, **every cell at every max-rank lands ML-only**. Five consecutive max-rank-zone audits (A → K → Q → J → T/9/8) produced ALL-T3 verdicts across 43 tested candidate rules. The catalog-measured v52→oracle gap of **$615.29/1000h whole-grid** decomposes as **$233.88 captured by v44_dt** (the production ML champion) + **$381.41 ML-only residual** beyond catalog refinement at the catalog's "one sentence statable" granularity. No rule shipped from S60–S64. The production rule chain (v52_full_high_only_handler, $2,498 full / $1,522 prefix, 17 rules) and ML champion (v44_dt, $1,081 full / $686 prefix, 107 features, 2.25M leaves) both UNCHANGED.

**The ML-only boundary claim.** Stated formally:

> *Across the 1,226,940 canonical high_only hands of Taiwanese Poker, the production rule chain v52 cannot be refined further at the "one-sentence-statable" granularity. v44_dt captures $233/1000h of the $615 catalog-measured v52→oracle gap; the residual $381/1000h is ML-only territory at current rule-chain depth.*

This claim is backed by **five independent falsifications** (one per max-rank zone) across **43 tested candidate rules**, drawing on five independent harness validations of shipped rules (Rule 14 +$131 at 0.2%, Rule 15 +$51 at 0.7%, Rule 16 +$19 at 1.7%, v52-vs-v47 ensemble +$17 at 1.4%, Rules 25/26/27 +$12 at 0.08%) spanning a 23× magnitude range. No tested candidate ship Threshold 2 (≥40% gap closure AND ≥+$5/1000h whole-grid AND zero non-targeted regression); the best single candidate is J-high's C_J1 at +$6.44/1000h WG with 21.54% capture (clears T2's $5 WG bar but fails T1's 40% capture bar).

**The five cross-cell structural findings.** Documented in Part 2:

1. **HIMID is the single most-validated design decision in the rule chain** — confirmed across all five zones with monotonic-magnitude dampening (A −$40 → K −$22 → Q −$13 → J −$7 → T/9/8 sum −$2.4).
2. **MS_ONLY "drop-max" candidates universally over-fire** at K/Q/J (82.7%/85.8%/89.1% fires, all catastrophic).
3. **DS_NO_JOINT within-cell-gap peaks at J then flattens** ($2,337 A → $3,062 K → $3,690 Q → $4,749 J → $3,827 T → $3,565 9 → $3,463 8).
4. **JOINT max-on-top boundary is at T-JOINT_MED specifically** — C_T5 marginally positive (+$0.22 WG, +12.24% capture); C_95 at 9-JOINT_MED negative (−$0.06 WG, −15.68% capture). The "JOINT max-on-top return" hypothesis works at T and dies below.
5. **Best-candidate-capture trajectory is non-monotonic with an unexpected J jump** (5.45% A → 3.33% K → 5.99% Q → 21.54% J → 12.24% T → ~0% 9/8).

**Recommended next-step targets** (Part 4): pair category ($396/1000h WG, 36.2% of canonical-grid) — a larger absolute target than high_only's ML-only residual. Trips ($55), two_pair ($52), three_pair ($35) are smaller but cleaner. A hybrid chain proposal (v52 for non-high_only + v44_dt for high_only handoff) would isolate v44_dt's $233/1000h high_only-specific catch.

---

## Document structure

| Part | Content | Purpose |
|---|---|---|
| **Part 1** | The five per-max-rank pages (A, K, Q, J, T/9/8) in zone order | Canonical reference: TL;DR + cell audit table + candidate verdict table + ML-only labeling per zone |
| **Part 2** | Cross-cell structural synthesis | Five structural findings + two-track-divergence decomposition |
| **Part 3** | The ML-only boundary claim, formalized | Single statable claim + falsification evidence + $615/$233/$381 decomposition |
| **Part 4** | Implications for future work | Next-step targets + hybrid chain proposal + when to retire the catalog approach |
| **Part 5** | Methodology and harness validation | Threshold definitions + harness reproducibility + reusable artifacts |
| **Appendix** | Source files and reproducibility | Pointers to per-session reports, harness scripts, data artifacts |

Cross-references are emitted as `(see Part X)` throughout. **The per-max-rank pages in Part 1 are the source-of-truth for each zone's numerical detail; Part 2 is value-added cross-cell synthesis.**

---

# Part 1 — The Five Per-Max-Rank Pages

The five pages of the catalog. Each page audits the rule chain `v52_full_high_only_handler` against the realistic-mixture oracle grid (`data/oracle_grid_full_realistic_n200.bin`, Session 24) at one max-rank, decomposed by six mutually-exclusive structural cells (JOINT_HIGH / JOINT_MED / JOINT_LOW / DS_NO_JOINT / DS_NO_MAXTOP / MS_ONLY).

Each page is the verbatim assembly of its source `SESSION_NN_*_HIGH_CATALOG.md` page; for **cross-cell findings see Part 2**.

---

## Part 1A — A-High (max = 14)

*Source: `SESSION_60_A_HIGH_CATALOG.md` — first page of the catalog. Audits Rule 14 (S50) cell-by-cell and tests 10 candidate refinements.*

### TL;DR — A-high verdict: ALL CELLS ML-ONLY (T3)

- **Rule 14 (A-high HIMID, S50) is empirically validated**: harness reproduces +$131.25/1000h whole-grid (matches the documented S50 ship of +$131 to within 0.2%).
- **A-high TOTAL leak to oracle after Rule 14: $281.20/1000h WG.** v44_dt closes 35% of that gap ($98.69/1000h WG). v44 residual: $182.51/1000h WG.
- **DS_NO_JOINT dominates** ($161.7/1000h WG = 58% of A-high leak). Within-cell gap $2,337/1000h.
- **Every candidate falls below Threshold 1.** 5 of 10 net-NEGATIVE on whole-grid lift; 1 structurally unfireable (0% fires); 4 with small positive lift well under T1's 40% capture bar.
- **A-high's residual is ML-only territory.** v44_dt's $182.51/1000h WG A-high residual is the closer-to-oracle benchmark; the candidate space tested cannot meaningfully close the $281/1000h Rule-14-to-oracle gap without sophisticated multi-feature gating outside the catalog's "one sentence statable" constraint.

### Cell-by-cell audit (Rule 14 = v52 on A-high)

| Cell | n hands | R14 mean_ev | Oracle mean_ev | Gap within-cell | Gap WG | v44 mean_ev | v44 gap WG |
|---|---:|---:|---:|---:|---:|---:|---:|
| JOINT_HIGH | 88,200 | +0.841 | +1.023 | $1,822/1k | $26.70 | +0.922 | $14.90 |
| JOINT_MED | 8,715 | -0.150 | +0.005 | $1,549/1k | $2.30 | -0.078 | $1.20 |
| JOINT_LOW | 105 | -1.348 | -1.193 | $1,552/1k | $0.00 | -1.274 | $0.00 |
| **DS_NO_JOINT** | **415,800** | **+0.508** | **+0.742** | **$2,337/1k** | **$161.70** | **+0.562** | **$124.80** |
| DS_NO_MAXTOP | 88,704 | +0.077 | +0.450 | $3,734/1k | $55.10 | +0.291 | $23.50 |
| MS_ONLY | 59,136 | -0.107 | +0.252 | $3,598/1k | $35.40 | +0.069 | $18.10 |
| **A-high total** | **660,660** | — | — | — | **$281.20** | — | **$182.51** |

### Candidate refinement verdicts (10 candidates)

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
| **C10** | **DSnj_HIBOT_tiebreaker** | **DSnj** | **100.0%** | **−24.5%** | **−$573** | **−$39.7** | **T3 (HIMID validated)** |

### Why every candidate failed (key data)

S58's decision matrix said oracle picks `tA_SS_ms` 27.9% of DS_NO_JOINT — the structural opportunity that motivated A-high's candidate design. The harness says: switching unconditionally hurts more than it helps because the simple gate (SS_ms exists) doesn't distinguish "SS_ms is better here" from "DS_mu is better here". When DS_NO_JOINT hands have an SS_ms config achievable with high mid_high, the DS bot inherits the strongest remaining pair which is typically ≥ the SS_ms mid_high — making the relative gate structurally too tight (C4 fires 0%) and the absolute gate (C1) catastrophic. **C10 (HIBOT vs HIMID) provides the first retrospective validation that Rule 14's HIMID design from S50 is empirically correct.**

### ML-only labeling (A-high)

| Cell | WG residual after R14 | v44 captures (more than R14) | Net ML-only territory |
|---|---:|---:|---:|
| JOINT_HIGH | $26.70 | $11.80 | $14.90 ML |
| JOINT_MED | $2.30 | $1.10 | $1.20 ML |
| JOINT_LOW | $0.00 | $0.00 | $0.00 — |
| DS_NO_JOINT | $161.70 | $36.90 | $124.80 ML |
| DS_NO_MAXTOP | $55.10 | $31.60 | $23.50 ML |
| MS_ONLY | $35.40 | $17.40 | $18.10 ML |
| **A-high total** | **$281.20** | **$98.69** | **$182.51 ML** |

---

## Part 1B — K-High (max = 13)

*Source: `SESSION_61_K_HIGH_CATALOG.md` — second page. Audits Rule 15 (S51) cell-by-cell and tests 7 candidate refinements.*

### TL;DR — K-high verdict: ALL CELLS ML-ONLY (T3)

- **Rule 15 (K-high HIMID, S51) is empirically validated**: harness reproduces +$51.38/1000h whole-grid (matches S51 ship of +$51 to within 0.7%).
- **K-high TOTAL leak to oracle after Rule 15: $176.35/1000h WG**. v44_dt closes 37% ($65.41/1000h WG). v44 residual: $110.94/1000h WG.
- **DS_NO_JOINT dominates** ($105.94/1000h WG = 60% of K-high leak). Within-cell gap $3,062/1000h — 31% deeper per hand than A-high because oracle drops K off top 34% (vs A's 6%) and Rule 15 keeps K on top 100%.
- **Every candidate falls below Threshold 1.** 5 of 7 net-NEGATIVE on whole-grid; 2 (C_K3, C_K7) showed micro-positive lift (+$3.53 and +$1.05/1000h WG) but capture% 3.33%/0.99% — way below the 40% bar. C_K6 (HIBOT control) confirmed Rule 15's HIMID design.

### Cell-by-cell audit (v52 on K-high)

| Cell | n hands | v52 mean_ev | Oracle mean_ev | Gap within-cell | Gap WG | v44 mean_ev | v44 gap WG |
|---|---:|---:|---:|---:|---:|---:|---:|
| JOINT_HIGH | 39,690 | -0.043 | +0.146 | $1,885/1k | $12.45 | +0.039 | $7.06 |
| JOINT_MED | 8,715 | -0.819 | -0.622 | $1,973/1k | $2.86 | -0.710 | $1.29 |
| JOINT_LOW | 105 | -2.324 | -1.847 | $4,773/1k | $0.08 | -1.965 | $0.02 |
| **DS_NO_JOINT** | **207,900** | **-0.445** | **-0.139** | **$3,062/1k** | **$105.94** | **-0.362** | **$76.99** |
| DS_NO_MAXTOP | 44,352 | -0.843 | -0.345 | $4,980/1k | $36.76 | -0.555 | $15.52 |
| MS_ONLY | 29,568 | -1.037 | -0.666 | $3,710/1k | $18.26 | -0.870 | $10.06 |
| **K-high total** | **330,330** | — | — | — | **$176.35** | — | **$110.94** |

### Candidate refinement verdicts (7 candidates)

| ID | Candidate | Cell | Fires | cap_b | $/cell | $/1000h WG | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| C_K1 | DSnj_drop_K_low_top_DSms | DSnj | 34.9% | −18.96% | −$580 | −$20.08 | T3 |
| C_K2 | DSnj_drop_K_when_K_in_DSpair | DSnj | 44.6% | −32.52% | −$996 | −$34.46 | T3 (worst) |
| C_K3 | DSnj_take_Qtop_DSms | DSnj | 7.9% | +3.33% | +$102 | +$3.53 | T3 (micro+) |
| C_K4 | DSnj_SSms_when_high | DSnj | 50.9% | −12.36% | −$379 | −$13.10 | T3 |
| C_K7 | DSnj_drop_K_to_2top_DSms | DSnj | 7.9% | +0.99% | +$30 | +$1.05 | T3 (micro+) |
| C_K5 | MSonly_drop_K | MSonly | 82.7% | −117.68% | −$4,366 | −$21.48 | T3 (catastrophic) |
| **C_K6** | **DSnj_HIBOT_tiebreaker** | **DSnj** | **100.0%** | **−20.51%** | **−$628** | **−$21.73** | **T3 (HIMID validated)** |

### Why every candidate failed (key data)

S58's decision matrix said oracle drops K off top **34%** in K × DS_NO_JOINT — the structural opportunity that motivated S61. The harness says: even with K's 5.6× higher drop rate than A, the SAME T3 pattern emerges. C_K1 fires at 34.9% (almost EXACTLY oracle's 34%) and is net −$20/1000h WG: the fire rate matches but the rule fires on hands where K-top was correct and stays passive on hands where dropping K was the answer — set MEMBERSHIP matters, not COUNT. C_K5 (MS_ONLY drop-K) fires 82.7% — catastrophic over-fire because oracle keeps K on top 78% of MS_ONLY. **C_K6 provides the second retrospective HIMID validation.**

### ML-only labeling (K-high)

| Cell | WG residual after R15 | v44 captures (more than R15) | Net ML-only territory |
|---|---:|---:|---:|
| JOINT_HIGH | $12.45 | $5.39 | $7.06 ML |
| JOINT_MED | $2.86 | $1.57 | $1.29 ML |
| JOINT_LOW | $0.08 | $0.06 | $0.02 ML |
| DS_NO_JOINT | $105.94 | $28.95 | $76.99 ML |
| DS_NO_MAXTOP | $36.76 | $21.24 | $15.52 ML |
| MS_ONLY | $18.26 | $8.20 | $10.06 ML |
| **K-high total** | **$176.35** | **$65.41** | **$110.94 ML** |

---

## Part 1C — Q-High (max = 12)

*Source: `SESSION_62_Q_HIGH_CATALOG.md` — third page. Audits Rule 16 (S52) cell-by-cell and tests 7 candidate refinements.*

### TL;DR — Q-high verdict: ALL CELLS ML-ONLY (T3)

- **Rule 16 (Q-high HIMID, S52) is empirically validated**: harness reproduces +$18.67/1000h whole-grid (matches S52 ship of +$19 to within 1.7%).
- **Q-high TOTAL leak to oracle after Rule 16: $93.77/1000h WG**. v44_dt closes 41% ($38.53/1000h WG). v44 residual: $55.24/1000h WG.
- **DS_NO_JOINT dominates** ($58.04/1000h WG = 62% of Q-high leak). Within-cell gap $3,690/1000h — 21% deeper per hand than K-high because oracle drops Q off top 52% (vs K's 34%, A's 6%).
- **Every candidate falls below Threshold 1.** 3 of 7 net-NEGATIVE; 2 (C_Q1, C_Q4) showed micro-positive lift (+$3.33 and +$3.48/1000h WG) but capture% 5.75%/5.99% — way below the 40% bar.

### Cell-by-cell audit (v52 on Q-high)

| Cell | n hands | v52 mean_ev | Oracle mean_ev | Gap within-cell | Gap WG | v44 mean_ev | v44 gap WG |
|---|---:|---:|---:|---:|---:|---:|---:|
| JOINT_HIGH | 13,230 | -0.592 | -0.391 | $2,006/1k | $4.42 | -0.499 | $2.38 |
| JOINT_MED | 8,715 | -1.113 | -0.900 | $2,135/1k | $3.10 | -0.996 | $1.39 |
| JOINT_LOW | 105 | -2.468 | -2.073 | $3,943/1k | $0.07 | -2.171 | $0.02 |
| **DS_NO_JOINT** | **94,500** | **-1.078** | **-0.709** | **$3,690/1k** | **$58.04** | **-0.955** | **$38.80** |
| DS_NO_MAXTOP | 20,160 | -1.443 | -0.866 | $5,767/1k | $19.35 | -1.097 | $7.74 |
| MS_ONLY | 13,440 | -1.646 | -1.252 | $3,938/1k | $8.81 | -1.472 | $4.91 |
| **Q-high total** | **150,150** | — | — | — | **$93.77** | — | **$55.24** |

### Candidate refinement verdicts (7 candidates)

| ID | Candidate | Cell | Fires | cap_b | $/cell | $/1000h WG | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| C_Q1 | DSnj_drop_Q_low_top_DSms | DSnj | 37.2% | +5.75% | +$212 | +$3.33 | T3 (micro+) |
| C_Q2 | DSnj_take_Jtop_DSms | DSnj | 8.7% | +3.24% | +$120 | +$1.88 | T3 |
| C_Q3 | DSnj_drop_Q_when_Q_in_DSpair | DSnj | 41.5% | +1.06% | +$39 | +$0.62 | T3 |
| C_Q4 | DSnj_drop_Q_to_2top_DSms | DSnj | 8.7% | +5.99% | +$221 | +$3.48 | T3 (best micro+) |
| C_Q5 | DSnj_SSms_when_high | DSnj | 32.0% | −3.48% | −$128 | −$2.02 | T3 |
| C_Q6 | MSonly_drop_Q | MSonly | 85.8% | −68.84% | −$2,711 | −$6.06 | T3 (catastrophic) |
| **C_Q7** | **DSnj_HIBOT_tiebreaker** | **DSnj** | **100.0%** | **−22.52%** | **−$831** | **−$13.07** | **T3 (HIMID validated)** |

### Why every candidate failed (key data)

S58's decision matrix said oracle drops Q off top **52%** in Q × DS_NO_JOINT. C_Q1 fires at 37.2% — UNDER-fires relative to oracle's 52%, yet capture is only +5.75%. The "drop Q low" gate is conservative, but the conservative subset still doesn't align with oracle's actual drop population. The structural lesson from K **generalizes monotonically across the 6%→52% drop-max range**: oracle knows WHICH q%, not whether any deterministic gate can reach q% capture. C_Q4 (top=2 + DS bot + ms_mid_high ≥ T) is the best Q candidate by capture (+5.99%) but the surgical gate fires only 8.7% — too narrow for T1. **C_Q7 provides the third retrospective HIMID validation.**

### ML-only labeling (Q-high)

| Cell | WG residual after R16 | v44 captures (more than R16) | Net ML-only territory |
|---|---:|---:|---:|
| JOINT_HIGH | $4.42 | $2.04 | $2.38 ML |
| JOINT_MED | $3.10 | $1.71 | $1.39 ML |
| JOINT_LOW | $0.07 | $0.05 | $0.02 ML |
| DS_NO_JOINT | $58.04 | $19.24 | $38.80 ML |
| DS_NO_MAXTOP | $19.35 | $11.61 | $7.74 ML |
| MS_ONLY | $8.81 | $3.90 | $4.91 ML |
| **Q-high total** | **$93.77** | **$38.53** | **$55.24 ML** |

---

## Part 1D — J-High (max = 11)

*Source: `SESSION_63_J_HIGH_CATALOG.md` — fourth page. Audits v52 (Rule 17 on s2 > 8 = 91.7% of J-high; Rule 24 lowest-on-top defensive on s2 ≤ 8 = 8.3%) cell-by-cell and tests 7 candidate refinements.*

### TL;DR — J-high verdict: ALL CELLS ML-ONLY (T3)

- **v52 ensemble across all high_only is empirically validated to 1.4%** (v52 vs v47 reproduces +$16.77/1000h WG vs documented +$17). Rule 17 alone (J-HIMID via v48 vs v47 on J-high) is +$5.48/1000h WG — the per-rule lift earlier rolled-up into a larger v52-vs-v47 figure (corrected S63).
- **J-high TOTAL leak to oracle after v52: $47.46/1000h WG.** v44_dt closes 51% ($24.03/1000h WG). v44 residual: $23.43/1000h WG.
- **DS_NO_JOINT dominates** ($29.88/1000h WG = 63% of J-high leak). Within-cell gap $4,749/1000h — 29% deeper per hand than Q-high. **JOINT_HIGH is empty at J** (max non-J rank ≤ 10 < J=11): the "structural funnel" tightens.
- **Every candidate falls below Threshold 1.** **C_J1 (drop-J low top + DSms) is the BIGGEST single-candidate WG lift across the entire catalog at +$6.44/1000h WG** — exceeding T2's $5 raw WG bar but missing T1's 40% gap-closure bar at 21.54%. C_J4 (J in DS pair) second-best at +$4.59/1000h WG.
- **Best-candidate capture% jumped from 5.45%/3.33%/5.99% (A/K/Q) to 21.54% at J** — finally tracking the underlying drop-max rate growth (6%→34%→52%→76%). But 21.54% is still half of T1's 40% bar.

### Cell-by-cell audit (v52 on J-high)

| Cell | n hands | v52 mean_ev | Oracle mean_ev | Gap within-cell | Gap WG | v44 mean_ev | v44 gap WG |
|---|---:|---:|---:|---:|---:|---:|---:|
| JOINT_HIGH | 0 | — | — | — | — | — | — |
| JOINT_MED | 8,715 | -1.420 | -1.152 | $2,686/1k | $3.90 | -1.266 | $1.66 |
| JOINT_LOW | 105 | -2.670 | -2.302 | $3,686/1k | $0.06 | -2.424 | $0.02 |
| **DS_NO_JOINT** | **37,800** | **-1.702** | **-1.227** | **$4,749/1k** | **$29.88** | **-1.486** | **$16.29** |
| DS_NO_MAXTOP | 8,064 | -2.053 | -1.355 | $6,978/1k | $9.36 | -1.600 | $3.28 |
| MS_ONLY | 5,376 | -2.257 | -1.781 | $4,767/1k | $4.26 | -2.024 | $2.18 |
| **J-high total** | **60,060** | — | — | — | **$47.46** | — | **$23.43** |

### Rule 17 / Rule 24 fire-region disambiguation

| Sub-population | n hands | % of J-high | v52 mean_ev | v52 gap WG |
|---|---:|---:|---:|---:|
| All J-high | 60,060 | 100% | -1.760 | $47.46 |
| **J-high s2 > 8 (Rule 17 fire region)** | **55,055** | **91.7%** | **-1.701** | **$44.20** |
| J-high s2 ≤ 8 (Rule 24 fire region) | 5,005 | 8.3% | -2.401 | $3.26 |

### Candidate refinement verdicts (7 candidates)

| ID | Candidate | Cell | Fires | cap_b | $/cell | $/1000h WG | Verdict |
|---|---|---|---:|---:|---:|---:|---|
| **C_J1** | **DSnj_drop_J_low_top_DSms** | **DSnj** | **39.8%** | **+21.54%** | **+$1,023** | **+$6.44** | **T3 (best WG ever)** |
| C_J2 | DSnj_take_2top_DSms | DSnj | 9.6% | +8.73% | +$414 | +$2.61 | T3 |
| C_J3 | DSnj_take_3top_DSms | DSnj | 9.6% | +6.61% | +$314 | +$1.98 | T3 |
| **C_J4** | **DSnj_drop_J_when_J_in_DSpair** | **DSnj** | **43.9%** | **+15.35%** | **+$729** | **+$4.59** | **T3 (2nd best)** |
| C_J5 | DSnj_SSms_when_high | DSnj | 35.6% | −0.75% | −$36 | −$0.22 | T3 |
| C_J6 | MSonly_drop_J | MSonly | 89.1% | −16.47% | −$785 | −$0.70 | T3 (over-fire) |
| **C_J7** | **DSnj_HIBOT_tiebreaker** | **DSnj** | **100.0%** | **−21.96%** | **−$1,043** | **−$6.56** | **T3 (HIMID validated)** |

### Why every candidate failed (key data)

S58's decision matrix said oracle drops J off top **76%** in J × DS_NO_JOINT — the most aggressive drop-max profile of all high zones tested. The lesson partially shifts at J: capture% finally jumps with drop-max rate (21.54% at J vs 5.45%/3.33%/5.99% at A/K/Q). **C_J1's +$6.44/1000h WG is the biggest single-candidate WG lift across the entire S60–S64 catalog. If T1's gap-closure threshold were 20% instead of 40%, C_J1 would ship.** The mid_high pool collapse (J's max non-J rank is 10, narrowing the achievable mid_high distribution) plus the much-larger drop-J surface (76%) together make the rule space more rewarding — but still below T1's 40% bar. C_J6 (MS_ONLY drop-J) fires 89.1% — over-fire pattern repeats. **C_J7 provides the fourth retrospective HIMID validation.**

### ML-only labeling (J-high)

| Cell | WG residual after v52 | v44 captures (more than v52) | Net ML-only territory |
|---|---:|---:|---:|
| JOINT_MED | $3.90 | $2.24 | $1.66 ML |
| JOINT_LOW | $0.06 | $0.04 | $0.02 ML |
| DS_NO_JOINT | $29.88 | $13.59 | $16.29 ML |
| DS_NO_MAXTOP | $9.36 | $6.08 | $3.28 ML |
| MS_ONLY | $4.26 | $2.08 | $2.18 ML |
| **J-high total** | **$47.46** | **$24.03** | **$23.43 ML** |

---

## Part 1E — T/9/8-High (max ∈ {10, 9, 8})

*Source: `SESSION_64_T98_HIGH_CATALOG.md` — fifth (and final per-max-rank) page. Audits Rules 25/26/27 (T/9/8-high always-defensive lowest-on-top + DS HIMID, S53 OVERNIGHT) cell-by-cell across all three combined sub-pops and tests 12 candidate refinements.*

### TL;DR — T/9/8-high verdict: ALL CELLS ML-ONLY (T3) across all three max-ranks

- **Rules 25/26/27 are empirically validated to 0.08% accuracy — the cleanest harness reproduction yet.** v52 vs v47 per max_rank: T = +$8.24/1000h WG (matches +$8.24 EXACTLY); 9 = +$3.26 (matches +$3.26); 8 = +$0.56 (matches +$0.56). Total T+9+8 = +$12.05 vs documented +$12.06.
- **T/9/8 TOTAL leak to oracle after v52: $16.51/1000h WG** (T $12.99 + 9 $3.09 + 8 $0.43). v44_dt closes 56% ($7.22/1000h WG more captured). v44 residual: $9.29/1000h WG.
- **JOINT_HIGH is empty at all three max-ranks** (max non-max rank ≤ 9 < J=11). JOINT_MED exists at T (n=2,835) and 9 (n=630); empty at 8.
- **Every candidate falls below Threshold 1.** The single positive WG candidate is **C_T5 (JOINT max-on-top + DS+ms at T-JOINT_MED) at +$0.22/1000h WG**, capture +12.24% — half-way to T1's 40% bar; the rest catastrophically negative or only fractionally positive. **No candidate within an order of magnitude of T2's $5/1000h WG bar.**
- **C_T3 / C_93 / C_83 (HIBOT control across T/9/8 DSnj) provides the FIFTH retrospective HIMID validation.**

### Cell-by-cell audit (v52 on T/9/8-high)

| max | Cell | n hands | v52 mean_ev | Oracle mean_ev | Gap within-cell | Gap WG | v44 mean_ev | v44 gap WG |
|---|---|---:|---:|---:|---:|---:|---:|---:|
| T | JOINT_MED | 2,835 | -2.013 | -1.627 | $3,858/1k | $1.82 | -1.882 | $0.55 |
| T | JOINT_LOW | 105 | -2.759 | -2.404 | $3,548/1k | $0.06 | -2.595 | $0.02 |
| **T** | **DS_NO_JOINT** | **12,600** | **-2.071** | **-1.688** | **$3,827/1k** | **$8.03** | **-1.926** | **$4.99** |
| T | DS_NO_MAXTOP | 2,688 | -2.252 | -1.848 | $4,040/1k | $1.81 | -2.030 | $1.10 |
| T | MS_ONLY | 1,792 | -2.687 | -2.260 | $4,270/1k | $1.27 | -2.464 | $0.61 |
| **T total** | | **20,020** | | | | **$12.99** | | **$7.27** |
| 9 | JOINT_MED | 630 | -2.497 | -2.134 | $3,630/1k | $0.38 | -2.388 | $0.11 |
| 9 | JOINT_LOW | 105 | -2.890 | -2.575 | $3,147/1k | $0.05 | -2.785 | $0.02 |
| **9** | **DS_NO_JOINT** | **3,150** | **-2.547** | **-2.190** | **$3,565/1k** | **$1.87** | **-2.423** | **$1.22** |
| 9 | DS_NO_MAXTOP | 672 | -2.767 | -2.357 | $4,099/1k | $0.46 | -2.597 | $0.27 |
| 9 | MS_ONLY | 448 | -3.208 | -2.770 | $4,385/1k | $0.33 | -3.062 | $0.12 |
| **9 total** | | **5,005** | | | | **$3.09** | | **$1.74** |
| 8 | JOINT_LOW | 105 | -3.151 | -2.798 | $3,529/1k | $0.06 | -3.014 | $0.02 |
| **8** | **DS_NO_JOINT** | **450** | **-3.110** | **-2.763** | **$3,463/1k** | **$0.26** | **-3.025** | **$0.20** |
| 8 | DS_NO_MAXTOP | 96 | -3.370 | -2.967 | $4,028/1k | $0.06 | -3.243 | $0.04 |
| 8 | MS_ONLY | 64 | -3.886 | -3.419 | $4,662/1k | $0.05 | -3.732 | $0.02 |
| **8 total** | | **715** | | | | **$0.43** | | **$0.28** |
| **GRAND TOTAL** | | **25,740** | | | | **$16.51** | | **$9.29** |

### Candidate refinement verdicts (12 candidates)

| ID | Candidate | max | Cell | Fires | cap_b | $/cell | $/1000h WG | Verdict |
|---|---|---:|---|---:|---:|---:|---:|---|
| C_T1 | DSnj_maxtop_DSmu_HIMID | T | DSnj | 100.0% | −54.31% | −$2,079 | −$4.36 | T3 |
| C_T2 | DSnj_maxtop_when_DSpair≥maxM2 | T | DSnj | 85.5% | −73.53% | −$2,814 | −$5.90 | T3 (worst) |
| **C_T3** | **DSnj_HIBOT_control** | **T** | **DSnj** | **84.4%** | **−21.94%** | **−$840** | **−$1.76** | **T3 (HIMID validated)** |
| C_T4 | DSnj_2ndLowest_top | T | DSnj | 100.0% | −44.14% | −$1,690 | −$3.54 | T3 |
| C_T6 | DSnj_SSms_when_ms_high | T | DSnj | 64.7% | −18.73% | −$717 | −$1.50 | T3 |
| **C_T5** | **JOINT_maxtop_DSms** | **T** | **JOINT_MED** | **100.0%** | **+12.24%** | **+$472** | **+$0.22** | **T3 (only positive)** |
| C_91 | DSnj_maxtop_DSmu_HIMID | 9 | DSnj | 100.0% | −94.47% | −$3,367 | −$1.77 | T3 |
| C_93 | DSnj_HIBOT_control | 9 | DSnj | 84.4% | −29.29% | −$1,044 | −$0.55 | T3 (HIMID validated) |
| C_94 | DSnj_2ndLowest_top | 9 | DSnj | 100.0% | −44.16% | −$1,574 | −$0.83 | T3 |
| C_95 | JOINT_maxtop_DSms | 9 | JOINT_MED | 100.0% | −15.68% | −$569 | −$0.06 | T3 (NEGATIVE at 9!) |
| C_81 | DSnj_maxtop_DSmu_HIMID | 8 | DSnj | 100.0% | −122.22% | −$4,232 | −$0.32 | T3 (most catastrophic) |
| C_83 | DSnj_HIBOT_control | 8 | DSnj | 84.4% | −32.36% | −$1,120 | −$0.08 | T3 (HIMID validated) |

### Why every candidate failed (key data)

The candidate space at T/9/8 inverts the J-and-above design: v52 already drops max-on-top (Rules 25/26/27 = lowest-on-top + DS HIMID), so candidates test alternatives to that defensive baseline (max-on-top return, 2nd-lowest-on-top, HIBOT tiebreaker, JOINT max-on-top, SSms switch).

**Max-on-top return scales catastrophically worse as max drops** (C_T1 −54% → C_91 −94% → C_81 −122%) — perfectly inversely tracking oracle's keep-max-on-top rate (T 11% → 9 4% → 8 <3%). 2nd-lowest-on-top fails identically at T and 9 (−44% capture) — oracle's preference for the absolute-lowest top is robust. **C_T5 (JOINT max-on-top at T-JOINT_MED) is the ONLY positive WG candidate at +$0.22; the same rule at 9-JOINT_MED (C_95) is negative.** The "JOINT max-on-top return" boundary is at T-JOINT_MED specifically. **C_T3/C_93/C_83 provide the FIFTH retrospective HIMID validation across the entire high_only rule family.**

### ML-only labeling (T/9/8-high combined)

| max | WG residual after v52 | v44 captures (more than v52) | Net ML-only territory |
|---|---:|---:|---:|
| **T total** | **$12.99** | **$5.72** | **$7.27 ML** |
| **9 total** | **$3.09** | **$1.35** | **$1.74 ML** |
| **8 total** | **$0.43** | **$0.15** | **$0.28 ML** |
| **T/9/8 GRAND TOTAL** | **$16.51** | **$7.22** | **$9.29 ML** |

---

## Part 1 — Cumulative cross-zone summary

The catalog's grand-total table, populated from the five per-max-rank pages:

| Max | n hands | % of high_only | WG residual after v52 | v44 catches | Net ML-only | Catalog verdict |
|---|---:|---:|---:|---:|---:|---|
| A | 660,660 | 53.8% | $281.20 | $98.69 | $182.51 | T3 (S60) |
| K | 330,330 | 26.9% | $176.35 | $65.41 | $110.94 | T3 (S61) |
| Q | 150,150 | 12.2% | $93.77 | $38.53 | $55.24 | T3 (S62) |
| J | 60,060 | 4.9% | $47.46 | $24.03 | $23.43 | T3 (S63) |
| T | 20,020 | 1.6% | $12.99 | $5.72 | $7.27 | T3 (S64) |
| 9 | 5,005 | 0.4% | $3.09 | $1.35 | $1.74 | T3 (S64) |
| 8 | 715 | 0.1% | $0.43 | $0.15 | $0.28 | T3 (S64) |
| **Total** | **1,226,940** | **100%** | **$615.29** | **$233.88** | **$381.41** | **ALL ML-ONLY** |

Five consecutive max-rank zones produced ALL-T3 verdicts across **43 tested candidates** (10 + 7 + 7 + 7 + 12). The catalog has formally labeled the **entire $615/1000h WG high_only residual (catalog framing) as ML-only at the "one-sentence-statable" granularity**. v44_dt holds **$381/1000h WG of exclusive territory** beyond what any catalog refinement reached.

---

# Part 2 — Cross-Cell Structural Synthesis

The value-added content of the aggregate catalog. Five structural findings emerge when the five per-max-rank pages are read in cross-section, plus a sixth observation decomposing the two-track production divergence.

---

## 2.1 — HIMID is the single most-validated design decision in the rule chain

The HIMID (high-mid-rank-sum) tiebreaker — favor the suited-mid config with the strongest mid_rank_sum, used as the secondary preference in Rules 14/15/16/17/25/26/27 — was tested by an explicit "HIBOT control" candidate at each max-rank zone. The HIBOT alternative (favor the strongest DS bot pair) **lost money at every max-rank tested**, with magnitudes:

| Zone | Source | HIBOT candidate ID | HIBOT WG lift | HIBOT cap_b |
|---|---|---|---:|---:|
| A-high | S60 | C10 | **−$39.7/1000h WG** | −24.5% |
| K-high | S61 | C_K6 | **−$21.73/1000h WG** | −20.5% |
| Q-high | S62 | C_Q7 | **−$13.07/1000h WG** | −22.5% |
| J-high | S63 | C_J7 | **−$6.56/1000h WG** | −22.0% |
| T-high | S64 | C_T3 | **−$1.76/1000h WG** | −21.9% |
| 9-high | S64 | C_93 | **−$0.55/1000h WG** | −29.3% |
| 8-high | S64 | C_83 | **−$0.08/1000h WG** | −32.4% |
| **Sum across zones** | | | **−$83.5/1000h WG** | |

**The magnitude trajectory is clean monotonic dampening** (−$40 → −$22 → −$13 → −$7 → −$1.8 → −$0.5 → −$0.1), reflecting that as v52 reaches closer to oracle at lower max-ranks (smaller WG residuals to defend), HIBOT's mistake also shrinks. **But HIMID never loses.** The directional confirmation is fivefold (across all five max-rank zones tested at the catalog) and the within-cell capture-deficit is nearly constant (−20% to −32%), suggesting HIBOT's loss is structural rather than circumstantial.

**This is the single most-validated decision in the production rule chain.** Rules 14/15/16/17/25/26/27 were originally designed with HIMID tiebreaking based on S50's `mine_patterns.py` analysis; the catalog's HIBOT controls are independent post-hoc confirmation at five max-ranks across both offensive (A/K/Q max-on-top) and defensive (T/9/8 lowest-on-top) rule designs. Future rule design in any category should default to HIMID-style mid-quality tiebreaking unless data argues otherwise.

---

## 2.2 — MS_ONLY "drop-max" candidates universally over-fire at K/Q/J

At every max-rank where MS_ONLY drop-max candidates were tested, the "drop-max-achievable" gate fired on a near-universal subset of the cell, with catastrophic capture:

| Zone | Source | Candidate ID | Gate description | Fires | $/cell | $/1000h WG | cap_b |
|---|---|---|---|---:|---:|---:|---:|
| K-high | S61 | C_K5 | drop K when top ≤ 7, ms_mid ≥ J, SS or 31 bot | **82.7%** | −$4,366 | −$21.48 | −117.7% |
| Q-high | S62 | C_Q6 | drop Q when top ≤ 7, ms_mid_high ≥ T, SS or 31 bot | **85.8%** | −$2,711 | −$6.06 | −68.8% |
| J-high | S63 | C_J6 | drop J when top ≤ 7, ms_mid_high ≥ 9, SS or 31 bot | **89.1%** | −$785 | −$0.70 | −16.5% |
| **Pattern** | | | **monotonically increasing fire rate as max drops** | | | | |

**The universal pattern:** in MS_ONLY (no DS bot achievable), any high-max-rank hand with a low spare card achieves the "drop-max + ms_mid + SS/31 bot" predicate, because the cell structurally has multiple low cards. The gate satisfies on ≥80% of the cell at every max-rank tested. **But oracle keeps max on top a clear majority of the time even in MS_ONLY** (K 78%, Q ~75%, J ~70% via S58 analogy) — so over-firing hits the wrong majority every time.

The mismatch detail (from S61–S63) is consistent: when the rule drops max, it picks a low-quality top that loses to oracle's max-on-top by $4,000–$10,000/hand mean regret. A-high's MS_ONLY (S60) and T/9/8 MS_ONLY (S64) were not tested as drop-max candidates — A because oracle's drop-A rate in MS_ONLY is only ~2% making any drop gate over-fire by orders of magnitude; T/9/8 because v52 already drops max as the baseline (no candidate space).

**Operational implication:** any future rule-chain refinement targeting MS_ONLY drop-max plays must use a **structural sub-gate that is naturally rare** (not just "low top achievable"). Candidates that fire on >50% of an MS_ONLY cell have failed every empirical test in this catalog. Either a multi-feature gate (≥3 axes) is required, or the cell is genuinely non-rule-shaped at human granularity.

---

## 2.3 — DS_NO_JOINT within-cell-gap peaks at J then flattens

DS_NO_JOINT is the dominant residual cell at every max-rank zone — structurally 62.9% of each zone's population by canonical symmetry of distinct-7-rank hands, and 58–63% of each zone's whole-grid leak. The within-cell gap-per-hand (v52 → oracle in $/1000h) grew monotonically from A through J, then flattened at T/9/8:

| Zone | n hands | DSnj within-cell gap | DSnj WG contribution | Oracle drop-max rate (per S58) |
|---|---:|---:|---:|---:|
| A | 415,800 | **$2,337/1k** | $161.70 | 6% |
| K | 207,900 | **$3,062/1k** | $105.94 | 34% |
| Q | 94,500 | **$3,690/1k** | $58.04 | 52% |
| J | 37,800 | **$4,749/1k** ← PEAK | $29.88 | 76% |
| T | 12,600 | **$3,827/1k** | $8.03 | ~85% (extrapolated) |
| 9 | 3,150 | **$3,565/1k** | $1.87 | ~92% |
| 8 | 450 | **$3,463/1k** | $0.26 | ~97% |

**The peak at J is the most surprising finding of the cross-cell synthesis.** Predictions going into the catalog assumed monotonic deepening with drop-max rate growth (since the rule's "keep-max-on-top" baseline becomes monotonically more wrong as oracle drops max more often). But T-DSnj is shallower than J-DSnj — within-cell gap fell from $4,749 to $3,827 (−19%).

**Mechanism (S64 finding):** at T/9/8, v52's baseline INVERTS — Rules 25/26/27 already drop max (lowest-on-top is the default). So the within-cell gap measures v52's defensive baseline deviating from oracle's *picks within the defensive zone* (which top? which suit? which mid?) — a smaller deviation than at A/K/Q/J where v52 keeps max on top while oracle drops it. **The within-cell gap depth is not a function of drop-max rate; it's a function of how mismatched v52's structural pick is with oracle's modal pick in the cell.**

This finding **partially overturns** the S60 prediction (CURRENT_PHASE Phase 5) that "the structural funnel narrows further at T" — narrowing happens at the cell-level (JOINT_HIGH empties at J; JOINT_MED empties at 8), but the within-cell gap depth flattens because v52's defensive baseline closer-aligns with oracle.

**Operational implication:** absolute residual contribution scales with population, not within-cell depth. A's $161 DSnj WG dominates J's $29 even though J's within-cell gap is 2× deeper. **Targeting cells by absolute WG residual is the right framing**, not by within-cell-gap depth. (See Part 4's implications.)

---

## 2.4 — JOINT max-on-top boundary is at T-JOINT_MED specifically

The S58 decision matrix's JOINT_PICK column tracks the oracle's "top=max AND bot=DS AND mid suited" rate per max-rank:

| max | JOINT_PICK rate (per S58) |
|---:|---:|
| A | 13.9% |
| K | 12.6% |
| Q | 11.1% |
| J | 7.9% |
| T | 5.3% |
| 9 | 3.3% |
| 8 | 2.0% |

The rate drops monotonically — oracle abandons the JOINT play as max-rank decreases. **The catalog finds the operational boundary at T-JOINT_MED specifically.** Two candidates test the same rule across zones:

| Zone | Source | Candidate ID | Cell | $/1000h WG | cap_b |
|---|---|---|---|---:|---:|
| T-JOINT_MED | S64 | **C_T5** | JOINT_MED | **+$0.22** ← marginal positive | +12.24% |
| 9-JOINT_MED | S64 | **C_95** | JOINT_MED | **−$0.06** ← negative | −15.68% |

Both rules apply "JOINT_maxtop_DSms" (always keep max on top, take DS bot, pick suited mid) inside JOINT_MED. At T, the rule captures positive lift (+12.24% of cell gap closure, +$0.22 WG). At 9, the same rule captures negative (−15.68%, −$0.06 WG).

**The boundary is sharp:** above J, joint cells let max-on-top dominate (Rule 17 handles J-JOINT_MED implicitly via the s2 > 8 gate). At T, joint cells lean weakly max-on-top (the C_T5 +12.24% suggests a sub-population where the JOINT play remains preferable). Below T, joint cells go fully defensive even when JOINT is achievable. This is consistent with the S58 JOINT_PICK rate transitioning from 7.9% (J) → 5.3% (T) → 3.3% (9) → 2.0% (8): T is the last zone where JOINT-pick is statistically meaningful.

**The candidate space does not capture this boundary as a ship-worthy rule.** C_T5 fails T1 at +$472/cell (need ≥$3K within-cell) and the absolute WG impact ($0.22/1000h) is rounding-error scale. But the boundary is a real structural fact — useful for any future hand-crafted rule at low max-ranks that might exploit T-specific JOINT structure.

**Operational implication:** the catalog identifies T-JOINT_MED as a structural curiosity but not a productive refinement target. Any future low-max rule design should treat T-JOINT_MED as a transition zone (mixed strategy) rather than a clean defensive cell.

---

## 2.5 — Best-candidate-capture trajectory is non-monotonic with an unexpected J jump

The "best candidate's % gap closure vs v52 baseline" across the catalog:

| Zone | Best candidate | cap_b | $/1000h WG | Oracle drop-max in DSnj |
|---|---|---:|---:|---:|
| A | C7/C8 (MS_ONLY 31_ms) | +6.1% | +$2.15 | 6% |
| K | C_K3 (Q-on-top + DSms) | +3.33% | +$3.53 | 34% |
| Q | C_Q4 (top=2 + DSms) | +5.99% | +$3.48 | 52% |
| **J** | **C_J1 (drop-J low + DSms)** | **+21.54%** ← JUMP | **+$6.44** | **76%** |
| T | C_T5 (JOINT max-on-top) | +12.24% | +$0.22 | ~85% (extrapolated) |
| 9 | (none positive) | — | (best negative) | ~92% |
| 8 | (none positive) | — | (best negative) | ~97% |

**The J jump is the most important structural finding for any future catalog-style work.** From A/K/Q's 3–6% range, best-candidate capture jumps to 21.54% at J — a 4× scaling that finally tracks the drop-max-rate growth. At J's 76% drop-J rate, the underlying surface is large enough that a single-axis gate (drop-J to top ≤ 7 + DS bot + ms_mid_high ≥ 9) achieves meaningful coverage.

**But the jump does not survive to T.** Capture drops back to 12.24% at T (only at JOINT_MED, not DSnj) and to zero (or negative) at 9 and 8. **Mechanism (inferred):** at J, two conditions coincide — (a) oracle's drop-max rate is high enough (76%) for a coarse rule to overlap meaningfully with oracle's actual drop population, AND (b) the mid_high pool is wide enough (J's max non-J rank is 10, so mid_high distribution spans 2–T) to give the gate's `ms_mid_high ≥ 9` predicate non-trivial coverage. At T, v52 inverts to defensive baseline (Rule 25), so the candidate space is entirely different — JOINT max-on-top is the only opportunity and it's tiny.

**The catalog's "shippable rule boundary" is at J's intersection of drop-max rate AND mid_high pool collapse — not extrapolatable from either feature alone.** A future catalog effort on a different category (pair / trips / etc.) cannot predict shippable-rule headroom from S58-style decision-matrix percentages alone.

**Operational implication:** if T1's gap-closure threshold were 20% (instead of 40%), C_J1 would ship at +$6.44/1000h WG (above T2's $5 WG bar in raw terms). A future session could revisit C_J1 with a tightened gate (e.g., add `ms_mid_high ≥ T` instead of ≥ 9, or constrain to specific top ranks) to push capture above 40% — but this approaches the "multi-feature gate" regime that effectively reproduces v44_dt.

---

## 2.6 — Two-track production divergence decomposed by category

The production rule chain `v52_full_high_only_handler` ($2,498 full / $1,522 prefix) and ML champion `v44_dt` ($1,081 full / $686 prefix) diverge by **$1,417/1000h on the full grid**. The catalog allows decomposing this gap by category:

| Category | n_hands | share | v44 within-cat | $/1000h whole-grid | Catalog-measured rule-vs-ML gap |
|---|---:|---:|---:|---:|---:|
| **high_only** | 1,226,940 | 40.4% | $1,868 | $755 | **$381 ML-only** (this catalog) |
| pair | 2,800,512 | 36.2% | $1,097 | $396 | (not audited) |
| trips | 328,185 | 4.6% | $1,194 | $55 | (not audited) |
| two_pair | 1,338,480 | 14.5% | $363 | $52 | (not audited) |
| three_pair | 114,400 | 2.2% | $1,613 | $35 | (not audited) |
| trips_pair | 171,600 | 1.8% | $281 | $5 | (not audited) |
| composite | 14,742 | 0.2% | $960 | $2 | (not audited) |
| quads | 14,300 | 0.1% | $545 | $1 | (not audited) |

The catalog's $381/1000h WG high_only ML-only residual is **27% of the $1,417 two-track divergence**. The remaining $1,036/1000h is split across other categories ($396 + $55 + $52 + $35 + $5 + $2 + $1 = $546 of explicit category WG contributions) plus prefix-vs-full grid differences (~$490) — i.e., the rule chain's high_only handler is responsible for about a quarter of the rule-vs-ML gap, with the rest distributed across categories that have NOT been catalog-audited.

**The catalog's $381 figure is conservative** — it measures only what v44_dt captures beyond v52 inside high_only. If v44_dt were retired and replaced by v52 alone, the rule chain would lose this exclusive territory plus the equivalent residuals in other categories (since v44_dt also captures rule-chain residuals in pair / trips / etc., not just high_only).

**Operational implication for category prioritization:**
- **pair ($396/1000h WG)** is a LARGER absolute target than high_only's ML-only residual ($381). At 36.2% of the canonical-grid (2.8M hands), it is the next-largest population zone after high_only.
- **trips ($55), two_pair ($52), three_pair ($35)** are smaller per-category but cleaner candidates (no Phase 5 catalog yet exists; the rule space may be less saturated).
- The full $1,417 two-track gap cannot be closed by rule-chain refinement at the catalog's granularity. Either (a) accept v44_dt as the production handler for high_only via a hybrid chain (Part 4), or (b) abandon the "one sentence statable" constraint and design multi-feature rules that effectively reproduce v44_dt within a rule grammar.

---

# Part 3 — The ML-Only Boundary Claim, Formalized

The single statable claim of this catalog:

> **Across the 1,226,940 canonical high_only hands of Taiwanese Poker, the production rule chain v52_full_high_only_handler cannot be refined further at the "one-sentence-statable" granularity. v44_dt captures $233/1000h of the $615 catalog-measured v52→oracle gap; the residual $381/1000h is ML-only territory at current rule-chain depth.**

## 3.1 — The $615 / $233 / $381 decomposition

| Quantity | Value | Meaning |
|---|---:|---|
| Catalog-measured v52→oracle gap (WG) | **$615.29/1000h** | Sum of v52's per-cell deviation from oracle ceiling across all 1,226,940 high_only hands |
| v44_dt's catch beyond v52 (WG) | **$233.88/1000h** | What v44_dt recovers from v52's residual gap (= ML's exclusive contribution to high_only over the rule chain) |
| **Net ML-only residual (WG)** | **$381.41/1000h** | What remains after v44_dt fires — the gap to oracle that neither v52 nor v44_dt closes |

The $615 figure is the catalog's primary measurement. It differs from CURRENT_PHASE's $755 figure because:
- **$615 = v52 → oracle gap (catalog framing)**, summed across all max-ranks and cells.
- **$755 = v44 → oracle gap scaled by category share (CURRENT_PHASE framing)** = $1,868 within-cat × 40.4% share.
Both are correct measurements of different quantities. The catalog framing is the more useful one for "what can a rule add beyond v52?" since it bounds the WG headroom available to any v52+rule refinement at $615.

## 3.2 — The five-falsification evidence

The catalog tests the claim by attempting to refute it five times — once per max-rank zone. The hypothesis tested at each zone:

> *"There exists at least one human-statable rule that improves on v52 in this max-rank zone by ≥40% gap closure within at least one cell AND ≥+$5/1000h whole-grid AND zero non-targeted regression."*

The five falsifications:

| Zone | Hypothesis tested | Candidates tested | Best result | Outcome |
|---|---|---:|---|---|
| A (S60) | Drop-A or SS-ms switch in DS_NO_JOINT can close A-high's $281 residual | 10 | C7/C8 +$2.15 WG (6.1% cap) | **FALSIFIED** |
| K (S61) | At K's 5.6× higher drop-max rate, drop-K rule shipping is achievable | 7 | C_K3 +$3.53 WG (3.33% cap) | **FALSIFIED** |
| Q (S62) | At Q's 8.7× drop-max rate, the rule space breaks through | 7 | C_Q4 +$3.48 WG (5.99% cap) | **FALSIFIED** |
| J (S63) | At J's 76% drop-max rate, capture% finally clears T1's 40% bar | 7 | C_J1 +$6.44 WG (21.54% cap) | **FALSIFIED** (but partial shift) |
| T/9/8 (S64) | Below J, candidate space inverts to defensive — rule headroom returns | 12 | C_T5 +$0.22 WG (12.24% cap, only positive) | **FALSIFIED** |

**Five falsifications across 43 candidate rules spanning a 12.7× range of structural opportunity (oracle drop-max rate 6% → 76%, plus inverted at T/9/8) is decisive empirical evidence that the high_only WG residual is genuinely ML-only territory at the catalog's "one-sentence-statable" granularity.**

The strongest counter-evidence is J-high's C_J1 at +$6.44/1000h WG — which **clears T2's $5/1000h whole-grid bar** but fails T1's 40% gap-closure bar at 21.54%. The T1 threshold exists precisely to require the rule to "really fit" the cell (closing a meaningful share of the within-cell gap), not just trim some leak. If a future analyst loosens T1 to 20%, C_J1 would ship as v53 = v52 + C_J1 — but such a v53 would require full-grid non-targeted-regression validation before claiming production status. The catalog leaves this door ajar for J specifically.

## 3.3 — The harness reproducibility evidence

The catalog's verdict rests on a harness (`analysis/scripts/test_rule_catalog.py`) that has reproduced **five independent shipped lifts** to **<2% error each**, spanning a 23× magnitude range:

| Validation | Source | Documented ship | Harness measurement | Error |
|---|---|---:|---:|---:|
| Rule 14 (A-high HIMID, S50) | S60 sanity | +$131/1000h WG | +$131.25 | **0.2%** |
| Rule 15 (K-high HIMID, S51) | S61 sanity | +$51/1000h WG | +$51.38 | **0.7%** |
| Rule 16 (Q-high HIMID, S52) | S62 sanity | +$19/1000h WG | +$18.67 | **1.7%** |
| v52 vs v47 ensemble (S53) | S63 sanity | +$17/1000h WG | +$16.77 | **1.4%** |
| Rules 25/26/27 (T/9/8 defensive, S53) | S64 sanity | +$12.06/1000h WG | +$12.05 | **0.08%** ← cleanest |
| **Range of measurement magnitudes** | | $0.56 → $131 | | 23× |
| **Worst error across 5 validations** | | | | **1.7%** |

Five-of-five independent ship reproductions to <2% error each, with the cleanest at 0.08% on the smallest absolute value tested. **The harness is the most-validated audit tool in the project**, and its NULL verdicts on 43 candidates carry the same epistemic weight as its positive reproductions on five shipped rules.

## 3.4 — What "ML-only" means operationally

The "ML-only" label is not a permanent obstruction. It means specifically:

1. **At the catalog's "one-sentence-statable" granularity** — a rule expressible as a single human-memorizable predicate with ≤3 feature gates — no candidate clears T1.
2. **At the production-ship granularity (T2)** — only J-high's C_J1 even reaches the $5 WG bar, and it fails the T1 capture floor.
3. **Multi-feature gates (5+ features, branching logic) might close the gap** — but such rules effectively reproduce v44_dt's structure within a rule grammar, which the catalog rejects on principle (the rule chain's purpose is to abstract patterns the user can memorize, not to retranscribe ML).

**The ML-only verdict means: at this catalog's granularity, the rule chain has reached its asymptotic ceiling on high_only.** Further rule-chain progress requires either abandoning the granularity constraint or pivoting to another category. (See Part 4.)

---

# Part 4 — Implications for Future Work

The catalog closes the high_only rule-chain investigation as ML-only at human granularity. Three concrete next-step paths are recommended.

## 4.1 — Pair category is the largest remaining target ($396/1000h WG)

The next-largest population zone is **pair** (2,800,512 hands = 36.2% of canonical-grid). v44_dt's pair within-cat residual is $1,097, scaling to **$396/1000h whole-grid**. This is **larger in absolute WG than high_only's ML-only residual ($381)** — i.e., a successful catalog effort on pair would unlock more rule-chain value than completely closing high_only's ML-only gap.

**Recommended approach:**
1. **Reuse the catalog harness verbatim.** `analysis/scripts/test_rule_catalog.py` is structurally category-agnostic; the cell-tagging in `data/drill_ho_v44_per_hand_structural.parquet` is high_only-specific but the parquet schema generalizes.
2. **Build a pair-specific structural cell decomposition.** S58's 6-cell scheme (JOINT_HIGH/MED/LOW + DS_NO_JOINT + DS_NO_MAXTOP + MS_ONLY + NEITHER) is high_only-specific (assumes all 7 ranks distinct). Pair needs a fresh cell axis — likely indexed on (pair_rank × pair-placement × ms_mid achievability × DS bot achievability), with sub-stratification by max non-pair rank.
3. **Reuse S58's decision-matrix methodology.** Build `pair_DECISION_MATRIX.md` analogous to S58 first, then audit existing rules cell-by-cell.
4. **The five-falsification methodology generalizes.** Each pair sub-zone gets one falsification attempt; ship verdicts accumulate to a final canonical `PAIR_RULE_CATALOG.md`.

**Risk note:** the four-zone tracking (A/K/Q/J showed the same null pattern) is suggestive that any category dominated by a single existing rule chain will hit the same "decision-matrix percentages overstate refinement headroom" wall. Pair's existing rule chain (Rules 7–11 in v52) may be similarly rule-saturated. If pair lands ML-only, the catalog's boundary claim extends — and the case for the hybrid chain (4.3) strengthens.

## 4.2 — Smaller-population categories may yield cleaner wins

The mid-sized categories worth catalog-style investigation:

| Category | Population | $/1000h WG | Risk profile |
|---|---:|---:|---|
| trips | 328,185 (4.6%) | $55 | v44 within-cat $1,194 — large per-hand gap, small population. May yield 1–2 surgical rules. |
| two_pair | 1,338,480 (14.5%) | $52 | v44 within-cat $363 — small per-hand gap, large population. Rule chain may already be near-optimal. |
| three_pair | 114,400 (2.2%) | $35 | v44 within-cat $1,613 — large per-hand gap. Decision 081 (Rule 13) shipped from this category; may be more headroom. |
| trips_pair | 171,600 (1.8%) | $5 | Already collapsed in Decision 089 / v40_dt; little catalog upside. |

**Recommendation:** target **trips** next (smallest population, largest within-cat residual — most surgical wins per session). Use trips_pair-style same-zone retrain approach (S55a playbook) as the baseline; if ML-only ceiling is hit, pivot to catalog audit.

## 4.3 — Hybrid chain proposal: v52 + v44_dt high_only handoff

**Concept:** the production rule chain remains v52 for all non-high_only categories. High_only hands route to v44_dt directly (or to a v44_dt-derived rule subset). This isolates v44_dt's exclusive value to the category where the catalog has formally proven it ML-only.

**Quantitative case:**
- v44_dt's high_only contribution is **$233/1000h** of catalog-measured catch beyond v52.
- v44_dt's full-grid value is $1,081 ($686 prefix), of which **$381/1000h is ML-only territory in high_only** (Part 3).
- If a hybrid chain delivers v44_dt's $233 catch on high_only AND keeps v52's $2,498 baseline on non-high_only, the expected combined value approximates v52's $2,498 minus v52's high_only contribution plus v44_dt's high_only contribution — net **estimated $2,500–2,700/1000h on full grid**, with v44_dt's deployment scoped specifically to where it provably wins.

**Risk note:** v44_dt was trained on full-grid features (not high_only-scoped), so deploying it inside a hybrid chain requires either (a) retraining v44_dt with hand-only-feature-importance on high_only hands, or (b) using the full v44_dt at inference time on a `is_high_only` predicate. (b) is implementationally simpler but doesn't isolate the $233 contribution — v44_dt might make different picks than expected if its training distribution included context outside high_only.

**Recommended next session:** isolate v44_dt's high_only-specific decision tree (extract leaves where the routing path requires high_only-only features) and benchmark the hybrid chain on a held-out subset before committing to production change.

## 4.4 — When to retire the catalog approach

The catalog's "one-sentence-statable" constraint is a strength (forces interpretability) but also the cause of its ML-only verdict on high_only. Two retirement conditions are reasonable:

1. **If pair, trips, two_pair, and three_pair all land ML-only at this granularity** — the catalog has demonstrated its asymptotic ceiling and the rule chain's value should be measured at v52's current $2,498 (or wherever it ends). Future progress requires either model classes beyond DT (e.g., gradient boosting, RF ensembles), or relaxing the rule grammar to admit multi-axis composite predicates.

2. **If a hybrid chain is adopted** (4.3) — the rule chain explicitly cedes high_only to v44_dt; further high_only refinement is no longer rule-chain's job. Catalog effort redirects to the remaining categories where v52 is the production strategy.

Until then, the catalog approach is the best-validated audit methodology in the project (five harness reproductions, five falsifications), and remains the right tool for any category-level investigation.

---

# Part 5 — Methodology and Harness Validation Summary

## 5.1 — Threshold definitions (unchanged S60–S65)

| Threshold | Definition | Use |
|---|---|---|
| **Threshold 1 (Catalog-worthy)** | ≥ 40% gap closure between v52 and oracle ceiling within cell AND ≥ +$3/1000h within-cell AND one-sentence statable | Identifies candidates that "really fit" the cell |
| **Threshold 2 (Production ship)** | T1 + ≥ +$5/1000h whole-grid lift + zero non-targeted regression | Production-shipping gate |
| **Threshold 3 (ML-only)** | No candidate clears T1 | Formal "this cell is ML-only at catalog granularity" verdict |

**T1 vs T2 distinction:** T1 ensures the rule is *specific* to the cell (40% capture is a fitness check); T2 ensures the rule is *valuable* enough to ship ($5 WG is a scale check). A candidate can clear T2 on raw WG but fail T1 on capture — that is C_J1's exact position ($6.44 WG, 21.54% capture). Such candidates are "catalog-curious" but not shipped without further tightening.

## 5.2 — Cell decomposition (S58 6-cell scheme)

Used unchanged across S60–S64:

| Cell | Definition |
|---|---|
| `JOINT_HIGH` | Joint (top=max, DS bot, ms mid) achievable AND best mid_high ≥ J(11) |
| `JOINT_MED` | Joint achievable AND 8 ≤ best mid_high ≤ T(10) |
| `JOINT_LOW` | Joint achievable AND best mid_high ≤ 7 |
| `DS_NO_JOINT` | DS-bot-with-max-on-top achievable but no joint |
| `DS_NO_MAXTOP` | DS-bot achievable but only if max-rank goes into the bot |
| `MS_ONLY` | No DS achievable, but a suited mid with max-on-top exists |
| `NEITHER` | No DS, no max-on-top ms_mid |

Defined in `analysis/scripts/drill_high_only_v44_deepdive.cell_for_hand` (Session 59 artifact). **JOINT_HIGH is empty at J/T/9/8** (max non-max rank ≤ 10 < J=11); JOINT_MED exists at T and 9, empty at 8.

## 5.3 — Harness architecture and validation

The audit harness (`analysis/scripts/test_rule_catalog.py`) is structured:

1. Load `data/drill_ho_v44_per_hand_structural.parquet` (S59 artifact — per-hand structural cell tags + oracle/v44 picks). 15 MB; 1,226,940 rows.
2. For each candidate `rule_fn`, filter to `(max_rank, cell)`.
3. Per hand: compute `rule_fn(h)` (None = pass-through to baseline_fn = `v52_full_high_only_handler`) and the per-hand EV via lookup in `oracle_grid_full_realistic_n200.bin`.
4. Aggregate within-cell + whole-grid lift in $/1000h, capture% vs baseline AND v44, % optimal, and rule-vs-oracle mismatch class breakdown.

**Five-fold harness validation summary** (repeated from Part 3.3 for completeness):

| Validation | Documented | Harness | Error |
|---|---:|---:|---:|
| Rule 14 (S60) | +$131.00 | +$131.25 | 0.2% |
| Rule 15 (S61) | +$51.00 | +$51.38 | 0.7% |
| Rule 16 (S62) | +$19.00 | +$18.67 | 1.7% |
| v52 vs v47 (S63) | +$17.00 | +$16.77 | 1.4% |
| Rules 25/26/27 (S64) | +$12.06 | +$12.05 | 0.08% |
| **Range** | $0.56 → $131 | | 23× |

Five-of-five reproductions to <2% across 23× magnitude range. **The harness is fully validated.** Its NULL verdicts on 43 candidates carry the same epistemic weight as its positive reproductions.

## 5.4 — Methodology lessons (cumulative S60–S64)

| # | Lesson | Source |
|---|---|---|
| 1 | Decision-matrix percentages (S58) overstate refinement headroom — oracle knows WHICH q% to switch on, not just THAT q%. | S60+S61+S62 confirmed |
| 2 | The set MEMBERSHIP problem, not COUNT: a gate matching oracle's q% in fire rate still misses the right subset. | K's C_K1 (fired 34.9% at oracle's 34% rate, −$20 WG) |
| 3 | MS_ONLY drop-max gates universally over-fire at >80% — the "drop-max-achievable" predicate matches near-universally but oracle's actual drops are much narrower. | S61+S62+S63 (C_K5/C_Q6/C_J6) |
| 4 | HIMID design choice is empirically validated cell-by-cell at all five max-rank zones. The single most-validated decision in the rule chain. | S60+S61+S62+S63+S64 HIBOT controls |
| 5 | The catalog's "shippable rule boundary" is at J's drop-max rate AND mid_high pool collapse — not extrapolatable from either feature alone. | S63 C_J1 21.54% capture jump |
| 6 | Multi-feature gates (≥5 axes) might close ML-only gaps but reproduce ML structure — defeats the catalog's purpose. | S60+S61+S62+S63 cumulative |
| 7 | Drop-max return at low max-ranks fails monotonically worse as max drops (T −54% → 9 −94% → 8 −122%). Clean falsification of "low-max-rule-shaped" hypothesis. | S64 C_T1/C_91/C_81 |
| 8 | JOINT max-on-top boundary is at T-JOINT_MED specifically. Above T joint cells dominate; below T defensive dominates even in joint. | S64 C_T5 vs C_95 |
| 9 | "ML-only" is valid catalog content — strategic insight, not a methodology failure. The user-facing strategy doc can honestly say "for these hands, defer to ML — no clean rule exists." | S60–S64 cumulative |

## 5.5 — Reusable artifacts (for future catalog work)

| Artifact | Purpose | Reusable for |
|---|---|---|
| `analysis/scripts/test_rule_catalog.py` | Per-cell rule audit harness | Verbatim for any category; needs new cell-tagging parquet for non-high_only |
| `analysis/scripts/sanity_v52_vs_v47_high_only.py` | Cross-check pattern for shipped-lift attribution | Adapt for any ensemble-lift attribution dispute |
| `analysis/scripts/audit_v52_T98_S64.py` | Phase 2 sanity + per-(max, cell) audit driver template | Adapt for any per-rule-family audit |
| `analysis/scripts/candidates_K_high_S61.py` | Generic helpers `_enumerate_max_on_top_configs(hand, max_rank)`, `_enumerate_nonMax_top_DSms`, `_enumerate_nonMax_top_anyBot_ms` | Imported through S64; reusable for any max-rank max-on-top variant |
| `analysis/scripts/candidates_T98_high_S64.py` | NEW helpers `_enumerate_top_at_pos(hand, top_pos)` for lowest-on-top variants, `_cell_for_hand(hand, max_rank)` parameterized | Reusable for any lowest-on-top audit |
| `data/session_60_candidate_results.json` … `session_64_candidate_results.json` | Full per-candidate results | Reference for any "did we test X already?" question |
| `data/drill_ho_v44_per_hand_structural.parquet` (S59) | Per-hand v44 residual with cell tags | Foundation for all catalog work S60–S64; high_only-specific |
| `SESSION_58_HIGH_ONLY_DECISION_MATRIX.md` | Per-max-rank × per-cell oracle TOP/BOT/MID profile | Reference for any high_only-specific decision question |

---

# Appendix — Source Files and Reproducibility

## A.1 — Per-session source documents (Part 1 source)

| Session | Date | Source file | Coverage |
|---|---|---|---|
| S60 | 2026-05-11 | `SESSION_60_A_HIGH_CATALOG.md` | A-high (n=660,660; 53.8% of high_only) |
| S61 | 2026-05-11 | `SESSION_61_K_HIGH_CATALOG.md` | K-high (n=330,330; 26.9%) |
| S62 | 2026-05-11 | `SESSION_62_Q_HIGH_CATALOG.md` | Q-high (n=150,150; 12.2%) |
| S63 | 2026-05-12 | `SESSION_63_J_HIGH_CATALOG.md` | J-high (n=60,060; 4.9%) |
| S64 | 2026-05-12 | `SESSION_64_T98_HIGH_CATALOG.md` | T-high (n=20,020; 1.6%) + 9-high (n=5,005; 0.4%) + 8-high (n=715; 0.1%) |
| S65 | 2026-05-12 | **`HIGH_ONLY_RULE_CATALOG.md` (this document)** | Aggregate synthesis |

## A.2 — Underlying data artifacts

| File | Size | Purpose |
|---|---|---|
| `data/oracle_grid_full_realistic_n200.bin` | 2.55 GB | Realistic-mixture oracle EV grid: 6.0M canonical hands × 105 settings × N=200 vs 70/25/5 mixture (S24) |
| `data/drill_ho_v44_per_hand_structural.parquet` | 15 MB | Per-hand v44 residual + cell tags for high_only (S59) |
| `data/v44_dt_model.npz` | (production) | The ML champion: 107 features, 2.25M leaves, depth=36 ml=1 |

## A.3 — Decisions log references

| Decision | Session | Result |
|---|---|---|
| 095 | S60 | A-high catalog: ALL CELLS ML-ONLY |
| 096 | S61 | K-high catalog: ALL CELLS ML-ONLY |
| 097 | S62 | Q-high catalog: ALL CELLS ML-ONLY |
| 098 | S63 | J-high catalog: ALL CELLS ML-ONLY; "$17 Rule 17" attribution corrected |
| 099 | S64 | T/9/8-high combined catalog: ALL CELLS ML-ONLY across all three max-ranks |
| **100** | **S65** | **Aggregate `HIGH_ONLY_RULE_CATALOG.md` produced; ML-only boundary claim formalized** |

## A.4 — Production state at end of Session 65 (UNCHANGED from S58)

- **Rule chain:** v52_full_high_only_handler ($2,498 full / $1,522 prefix; 17 rules; UNCHANGED since S53)
- **ML champion:** v44_dt ($1,081 full / $686 prefix; 107 features; 2.25M leaves; UNCHANGED since S58)
- **Two-track divergence:** $1,417/1000h (full-grid)
- **Catalog-attributable share of divergence:** $381/1000h in high_only ML-only territory (27%)

---

*This document is the canonical synthesis of Sessions 60–64. The five per-max-rank pages remain authoritative for per-zone numerical detail; this aggregate adds cross-cell synthesis and the formal ML-only boundary claim. **No new code, tests, or production state changes occurred in Session 65** — pure documentation work.*

*Last updated: 2026-05-12 (Session 65 end).*
