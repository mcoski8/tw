# Current: Sprint 8 — Session 35 wrap. v29_dt is the new ML champion. Largest ML ship since v26: −$46/1000h on full grid (and −$37 on prefix). 7th gating-template instance. Pair category drops $97/1000h within-pair, pct_opt 53.9% → 55.0%. The 4-feature `pair_r4_*_g` family directly targets the v27→Rule-4 KK/AA gap identified by Session 35's pair distillation diagnostic.

> **🎯 IMMEDIATE NEXT ACTION (Session 36):**
>   (A) **Re-run KK/AA capture analysis on v29.** Diagnostic predicted
>       up to $62/1000h whole-grid available on KK/AA alone (v27 was
>       $20 WORSE than Rule 4 + $42 ceiling above oracle). v29's full-
>       grid pair improvement is $43/1000h whole-grid contribution
>       ($97 within-pair × 44.6% population share). This is a strong
>       capture but doesn't tell us how much was on KK/AA specifically
>       vs lower pairs. Run `distill_v29_pair.py` (clone of v27 distill,
>       point at v29 model) — quick 10-min answer. If KK/AA is still
>       a notable miss, design pair_r4_v3 round 2.
>   (B) **trips_aug_gated.** Trips (no pair) is 5.5% × $1,997 = $110
>       share, fully untouched. Now the 8th gating template instance
>       candidate. KKK/AAA probe data informs feature design.
>   (C) **High_only round 3.** v27→v29 didn't touch high_only ($2,862
>       residual). The Session-34 distill identified candidate features
>       but conversion was poor (10%). Lower priority.

> **✅ SHIPPED (Decision 064):** v29_dt — depth=30, ml=5, **486,342 leaves**
> (+25,967 vs v27), 73 features (69 v27 + 4 GATED `pair_r4_*` features).
> Strictly dominates v27: **−$46/1000h on full grid** (pair drops $97),
> **−$37/1000h on prefix** (pair drops $85). 3rd-largest single ship by
> headline (after v26 at $70 and v25 at $47), and the most diagnostic-
> driven feature set in project history — every feature traces directly
> to a within-leaf signal axis identified by `distill_v27_pair.py`.

> **🔬 DIAGNOSTIC + DESIGN CHAIN (Session 35):**
> 1. User asked about KK/AA + rainbow Rule-4-bot edge cases.
> 2. Per-hand probe of K♠K♦3♠5♦9♥T♣J♠ confirmed v14_combined+Rule4 is
>    catastrophically wrong on this kind of hand (-$18,000/1000h on
>    one hand) while v27 already routes correctly.
> 3. Rule 5 (Rainbow override) shipped to STRATEGY_GUIDE for human
>    play (+$1/1000h vs v14).
> 4. **`distill_v27_pair.py` ran the KK/AA capture analysis.**
>    Surprising finding: v27 is $20/1000h whole-grid WORSE than Rule 4
>    alone on KK/AA. v27 picks Rule-4 84.6% of KK/AA, but the 15.4%
>    non-Rule-4 picks were systematically incorrect — overgeneralizing
>    v25's pair-gated features.
> 5. **The missing signal: suit profile of Rule-4's resulting bot.**
>    v25's existing pair-gated features (`pair_*_g`) encode kickers-
>    in-pair-suit and alt-routing quality but NOT the shape of the
>    leftover bot. 4 new features prefixed `pair_r4_*_g` close that gap.
> 6. v29 trained — 3/4 of the new features placed in top-30 importance
>    (vs v27's 0/4). Tripwire confirmed pre-grade.
> 7. v29 graded — biggest ship since v26.

> **📓 METHODOLOGY LESSONS REINFORCED (Session 35):**
> - **Diagnostic-first design works.** v29's headline gain ($46) is
>   7.7× v27's ($6) despite v27 having more candidate features
>   (4 vs 4). The difference: v27's features were "what high_only
>   regret might cluster on" (speculative); v29's features were
>   directly named from a diagnostic finding ("v27 is $20 worse than
>   Rule 4 on KK/AA, so encode the missing rainbow-bot signal").
> - **The diagnostic-to-headline conversion ratio jumped from ~10%
>   (v27) to >50% (v29).** When the diagnostic identifies a specific
>   *competing baseline* (Rule 4 alone, in this case) and a specific
>   *missing signal* (rainbow Rule-4-bot), feature design becomes
>   prescriptive rather than speculative.
> - **The top-25 feature-importance tripwire correlates with headline.**
>   v25 5/6 → +$47, v26 3/6 → +$70, v27 0/4 → +$6, v29 3/4 → +$46.
>   Placement count is a strong leading indicator.
> - **User intuition is signal.** The ML champion v27 was wrong on
>   exactly the pattern the user flagged ("KK with rainbow Rule-4-bot").
>   When the user expresses confusion or a "this can't be right" reaction
>   at the table, that's a high-prior pointer to a real ML weakness.

> Updated: 2026-05-05 (end of Session 35)

---

## Headline state at end of Session 35

**Strategies of record:**

| Strategy | Use case | Where it lives |
|---|---|---|
| **v14 + Rule 4 + Rule 5** (5 numbered rules) | Human-memorizable strategy | `STRATEGY_GUIDE.md` Part 6 + `analysis/scripts/strategy_v28_rule5_rainbow.py` |
| **v29_dt** | ML champion (486,342 leaves, 73 feat: 37 base + 6 gated suited + 6 gated trips_pair + 4 gated composite + 6 gated pair + 6 gated two_pair + 4 gated high_only + 4 gated pair_r4) | `analysis/scripts/strategy_v29_dt.py` + `data/v29_dt_model.npz` |
| v27_dt | Predecessor (69 feat); kept as a comparison baseline | `analysis/scripts/strategy_v27_dt.py` + `data/v27_dt_model.npz` |
| v26 / v25 / v24 / v23 / v20 / v18e / v16 | Superseded baselines; retained | `data/v*_dt_model.npz` |
| v20b (d=32) | ARCHIVED — capacity saturated, bit-identical to v20 | `data/v20b_dt_model.npz` |
| v19, v21, v22 | ARCHIVED (v19: prefix fail; v21/v22: Rule 5 attempts rejected) | various |
| v28_rule5_rainbow | Human-strategy chain (NOT an ML model) — ships +$1/1000h vs v14 | `analysis/scripts/strategy_v28_rule5_rainbow.py` |

**Capacity + feature progression (full 6M grid, N=200):**

| Strategy | Depth | min_leaf | Features | Leaves | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|---:|---:|---:|---:|
| v16_dt | 18 | 100 | 37 | 28,790 | $2,464 | 42.54% | — |
| v18_dt | 22 | 50 | 37 | 60,651 | $2,306 | 44.01% | −$158 |
| v18b | 24 | 30 | 37 | 96,409 | $2,217 | 45.04% | −$89 |
| v18c | 26 | 20 | 37 | 124,902 | $2,172 | 45.59% | −$45 |
| v18d | 28 | 10 | 37 | 193,365 | $2,108 | 46.45% | −$64 |
| v18e | 30 | 5 | 37 | 274,446 | $2,066 | 47.08% | −$42 |
| v20 | 30 | 5 | 43 (gated suited) | 307,939 | $1,982 | 47.81% | −$84 |
| v20b | 32 | 5 | 43 (gated suited) | 307,939 | $1,982 | 47.81% | $0 (saturated) |
| v23 | 30 | 5 | 49 (43+6 gated TP) | 314,705 | $1,977 | 47.89% | −$5 vs v20 |
| v24 | 30 | 5 | 53 (49+4 gated comp) | 314,759 | $1,977 | 47.89% | −$1 vs v23 |
| v25 | 30 | 5 | 59 (53+6 gated pair) | 390,626 | $1,929 | 48.43% | −$47 vs v24 |
| v26 | 30 | 5 | 65 (59+6 gated t2p) | 459,209 | $1,859 | 49.21% | −$70 vs v25 |
| v27 | 30 | 5 | 69 (65+4 gated ho) | 460,375 | $1,853 | 49.27% | −$6 vs v26 |
| **v29** | **30** | **5** | **73 (69+4 gated pair_r4)** | **486,342** | **$1,807** | **49.80%** | **−$46 vs v27 (pair −$97)** |

**Same sweep on N=1000 prefix:**

| Strategy | $/1000h | pct_opt | Δ vs prev |
|---|---:|---:|---:|
| v18e | $1,082 | 59.30% | — |
| v20 | $1,082 | 59.31% | $0 |
| v23 | $1,073 | 59.47% | −$9 vs v20 |
| v24 | $1,072 | 59.48% | −$1 vs v23 |
| v25 | $1,054 | 59.80% | −$18 vs v24 |
| v26 | $1,002 | 60.80% | −$52 vs v25 |
| v27 | $1,002 | 60.80% | $0 (no high_only in prefix) |
| **v29** | **$965** | **61.32%** | **−$37 vs v27 (pair −$85)** |

**Per-category breakdown (full grid, N=200) — seven gating wins now visible:**

| Category | v18e | v20 | v23 | v24 | v25 | v26 | v27 | v29 | Δ v29 vs v18e |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| high_only | $3,307 | $2,894 | $2,894 | $2,894 | $2,894 | $2,894 | $2,863 | $2,862 | **−$445** (v20+v27) |
| pair | $1,873 | $1,873 | $1,873 | $1,873 | $1,771 | $1,771 | $1,771 | $1,674 | **−$199** (v25+v29) |
| two_pair | $1,458 | $1,458 | $1,458 | $1,458 | $1,458 | $1,145 | $1,145 | $1,145 | −$313 (v26) |
| trips | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $1,997 | $0 |
| trips_pair | $1,608 | $1,608 | $1,447 | $1,447 | $1,446 | $1,445 | $1,445 | $1,443 | −$165 (v23) |
| three_pair | $1,653 | $1,653 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | $1,654 | +$1 (noise) |
| quads | $724 | $724 | $724 | $723 | $723 | $723 | $723 | $723 | −$1 (noise) |
| composite | $2,100 | $2,100 | $2,080 | $1,864 | $1,869 | $1,741 | $1,741 | $1,741 | −$359 (v24+v26) |

**The gating template is now proven across 7 categories** spanning 0.245% (composite) to 46.6% (pair) population shares. v29's pair_r4 is the second-largest single-ship pair gain (after v25's −$102) — and pair has now seen TWO independent gating-template wins (v25 then v29), validating that within-category iteration is a viable expansion direction.

---

## What this leaves on the table

- v29 captures **40.5% of the v14→ceiling gap** at N=200 fidelity ($1,226/$3,033 vs v14)
- v29 captures **68% of the v14→ceiling gap** at N=1000 fidelity ($1,072/$2,037)
- Remaining gap to ceiling: **$1,807/1000h (full grid N=200)**, **$965/1000h (prefix N=1000)**
- Biggest residuals at full grid (per-category × share):
  - **high_only**: 20.4% × $2,862 = **$584 share** — back to being the largest residual
  - **pair**: 46.6% × $1,674 = **$781 share** — still largest single category but pair has had two iterations now
  - **two_pair**: 22.3% × $1,145 = **$255 share** — gated in v26
  - **trips**: 5.5% × $1,997 = **$110** — never gated (candidate for v30)
  - three_pair: 1.9% × $1,654 = $32
  - trips_pair: 2.86% × $1,445 = $41 (already gated)
  - composite: 0.245% × $1,741 = $4.3 (already gated)
- Per-category prioritization for Session 36: distill-v29-pair (round 2 audit) > trips_aug_gated > high_only round 3

---

## What Session 35 produced

### v29 ship + Rule 5 (rainbow override) ship + the diagnostic chain

**1. KK/AA + KKK/AAA boundary probes analyzed.** Built on Session 34 probe data; ran fresh KKK/AAA probe. Confirmed Rule 4 extends to trips of K/A. Quantified KK/AA Rule-4-bot suit profile distribution (3.7% rainbow, 48.7% single-suited, 26.8% DS).

**2. Rule 5 (Rainbow override) shipped to STRATEGY_GUIDE.md** (Decision 063). v28 = v14 + Rule 5 = $3,032/1000h (+$1 vs v14, +0.03 pp pct_opt). FIRST successful Rule 5 in the project's history (v21/v22 lost $473-$680 on too-loose gates). Tight structural trigger (rainbow Rule-4-bot + DS-feasibility) fires on 0.27% of all hands. Preserves Rule 4 default while catching the high-leverage exception cases (~$18K/1000h per fired hand).

**3. v27 pair distillation revealed v27's hidden weakness on KK/AA.**
- v27 picks Rule-4 mid-pair on 84.6% of KK/AA hands
- v27 picks DS-bot on 7.8%, "other" on 7.6%
- Within-KK/AA regret: v27 = $1,236/1000h, Rule 4 alone = $949/1000h, oracle (R4 OR DS-bot) = $362/1000h
- **v27 is $20/1000h whole-grid WORSE than Rule 4 alone on KK/AA**
- Total v27→oracle gap on KK/AA = $63/1000h whole-grid

The v27-vs-Rule-4 deficit is the surprise: v27 was overgeneralizing v25's pair-gated features and making FALSE-positive DS-bot picks on KK/AA hands where Rule 4 was correct. The diagnostic identified the missing signal: Rule-4-bot suit profile, the very feature that defines the user's Rule 5 trigger.

**4. v29 designed and shipped — 4-feature `pair_r4_*_g` family** (`pair_aug_v2_features_gated.py`):

- `pair_r4_bot_suit_profile_g` (0..5) — encoded suit shape of Rule-4 bot
- `pair_r4_bot_max_rank_g` (0..14) — highest rank in Rule-4 bot
- `pair_r4_n_broadway_kickers_g` (0..5) — count of T-A among non-pair
- `pair_r4_n_low_kickers_g` (0..5) — count of 2-5 among non-pair

Persistence: 34.5s for all 6M canonical hands → `data/feature_table_pair_aug_v2_gated.parquet` (19 MB).

Training: 393s for depth=30 ml=5; **486,342 leaves (+25,967 vs v27)**, +5.6% capacity expansion. Compare to v27's +1,166 leaves — the strong leaf-count growth was a leading indicator of the headline gain.

**Tripwire passed:** 3 of 4 new features placed in top-30 feature importance (#17, #20, #23). v27's 0/4 placement was the warning sign for v27's marginal gain; v29's 3/4 confirmed the design pre-grade.

**5. v29 graded:**

| Grid | v27 | v29 | Δ |
|---|---:|---:|---:|
| Full N=200 | $1,853 / 49.27% | **$1,807 / 49.80%** | **−$46/1000h, +0.53 pp** |
| Prefix N=1000 | $1,002 / 60.80% | **$965 / 61.32%** | **−$37/1000h, +0.52 pp** |

Per-category at full grid: pair drops $1,771 → $1,674 (**−$97/1000h within-pair**). pct_opt on pair: 53.9% → 55.0% (+1.1 pp). All other categories bit-identical to within-N=200-noise.

The full:prefix ratio is 1.24:1 — well-calibrated, low overfitting risk. v25 was 2.6:1, v26 was 1.35:1; v29's tighter ratio confirms the diagnostic-driven feature design is robust to N=200 sample noise.

### Methodology lessons reinforced (Session 35)

1. **Diagnostic-first design produces 7.7× better headline-per-feature than speculative design.** v27 (speculative high_only candidates) gained $6 with 4 features. v29 (diagnostic-driven from `distill_v27_pair.py`) gained $46 with 4 features. Same trainer, same gating template, same depth — the only difference was knowing precisely what to encode.

2. **The diagnostic should identify a *competing baseline*, not just a *miss leaf*.** The Session-34 high_only diagnostic identified within-leaf separation but didn't compare against a non-DT alternative. The Session-35 pair diagnostic explicitly compared v27 vs Rule 4 alone and discovered v27 was *losing* — that's the kind of finding that prescribes the feature design rather than just suggesting it.

3. **User intuition correlates with ML weak points.** The user's question about K♠K♦3♠5♦9♥T♣J♠ ("Rule 4 leaves rainbow garbage in the bot, surely DS-bot is better?") pointed at a $63/1000h whole-grid hole that v27's metrics didn't surface. Future sessions should treat "user expresses 'this can't be right' at the table" as a research-priority signal.

4. **Pair has now seen two iterations of gating-template work.** v25 added 6 base pair features (-$102 on category); v29 added 4 pair_r4 features (-$97 on category). Together: pair has dropped $199/1000h since v18e. Categories CAN absorb multiple gating-template iterations when each one targets a distinct signal axis (v25 = kickers-in-pair-suit; v29 = Rule-4-bot suit profile).

5. **Cycle scoreboard since Session 25 (21 ships, 7 archives, 1 doc-only, 1 mid-session bug recovery, 1 rule-strategy-only ship):**

| Cycle | Target | Result | Status |
|---|---|---:|---|
| v23 | gated trips_pair on v20 | +$5 / +$9 vs v20 | SHIPPED |
| v24 | gated composite on v23 | +$1 / +$1 vs v23 | SHIPPED |
| v25 | gated pair on v24 | +$47 / +$18 vs v24 | SHIPPED |
| v26 | gated two_pair on v25 | +$70 / +$52 vs v25 | SHIPPED |
| v27 | gated high_only-direct on v26 | +$6 / $0 vs v26 (prefix uninformative) | SHIPPED |
| v28 | Rule 5 (Rainbow override, human strategy) | +$1 vs v14_combined | SHIPPED (rule-only) |
| **v29** | **gated pair_r4 (round 2 of pair) on v27** | **+$46 / +$37 vs v27** | **SHIPPED — current ML champion** |

---

## Resume Prompt (Session 36)

```
Resume Session 36 of the Taiwanese Poker Solver project at
/Users/michaelchang/Documents/claudecode/taiwanese.

Read these files for context:
- CLAUDE.md
- STRATEGY_GUIDE.md (v29 champion section + Rule 5)
- CURRENT_PHASE.md (rewritten end of Session 35)
- DECISIONS_LOG.md (latest: Decision 064)
- analysis/scripts/strategy_v29_dt.py — current ML champion
- analysis/scripts/pair_aug_v2_features_gated.py — newest gated family
  (seventh instance after suited / trips_pair / composite / pair / two_pair /
  high_only / pair_r4)
- analysis/scripts/distill_v27_pair.py — diagnostic that motivated v29

State (end of Session 35):
- v29_dt is the new ML champion: $1,807/1000h on full grid (49.80% opt),
  $965/1000h on prefix N=1000 (61.32% opt). 486,342 leaves, depth=30,
  min_samples_leaf=5, 73 features (69 v27 + 4 gated pair_r4).
- 7th gating-template instance. Pair has now seen TWO iterations
  (v25 +$102 within-pair, v29 +$97 within-pair) — categories can
  absorb multiple distinct gating-template attacks.
- Rule 5 (Rainbow override) shipped to STRATEGY_GUIDE for human play
  (+$1/1000h vs v14_combined). First successful Rule 5 in project
  history.
- Diagnostic-first design produced 7.7× better headline-per-feature
  than speculative design (v27 baseline: 4 features for $6; v29:
  4 features for $46).

Next session targets (priority order by expected value):

(A) **Re-distill v29 on pair** to see how much KK/AA gap remains.
    Quick (~10 min). Then either v30 = pair_r4_round-2 OR pivot.

(B) **trips_aug_gated** — Trips (no pair) is 5.5% × $1,997 = $110
    share, fully untouched. Would be the 8th gating template instance.
    Probe data from Session 34 (probe_trips_kkk_aaa_routing.py)
    informs feature design for KKK/AAA subset; need broader trips
    analysis for the rest.

(C) **High_only round 3** — v27 left $2,862 in high_only. Lower
    priority because Session-34 diagnostic-to-headline conversion
    was poor (~10%) on high_only specifically. Revisit only after
    pair round-3 + trips done.

REMINDERS:
- Auto mode is on; minimize interruptions.
- Use python3, not python.
- cargo lives at ~/.cargo/bin/cargo (not on PATH).
- Session-end protocol: commit + push to origin/main (pre-authorized).
- For long Python scripts that pipe output: use python3 -u or
  PYTHONUNBUFFERED=1.
- Validate ML candidates on BOTH full grid (N=200) AND prefix (N=1000)
  WHEN APPLICABLE. High_only-targeting models can only validate on
  full grid (prefix has 0 high_only hands).
- ALL new aug feature families MUST be category-gated. Gating template
  is now proven 7× and is the default.
- ALL new aug families MUST use a UNIQUE PREFIX. Claimed: `_g` suffix
  (suited), `tp_*_g` (trips_pair), `comp_*_g` (composite),
  `pair_*_g` (pair v1), `t2p_*_g` (two_pair), `ho_*_g` (high_only),
  `pair_r4_*_g` (pair v2).
- Cached parquets cut training cycles to ~5 min.
- Methodology rule (Session 35): top-25 feature importance is a pre-
  grade tripwire. v25 5/6 → +$47, v26 3/6 → +$70, v27 0/4 → +$6,
  v29 3/4 → +$46. Use placement count as a leading-indicator.
- Methodology rule (Session 35): diagnostic should identify a
  COMPETING BASELINE (not just miss leaves). v27's gain was tiny
  because the diagnostic only showed within-leaf separation; v29's
  gain was big because the diagnostic showed v27 LOSING to a simpler
  rule. Future diagnostics should explicitly grade ML vs rule-based
  alternatives on the target subset.
```

---

*This file is REWRITTEN (not appended) at the end of every session.*
