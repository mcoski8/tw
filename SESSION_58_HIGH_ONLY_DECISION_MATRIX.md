# Session 58 — High-Only Decision Matrix (Oracle vs v43_dt)

*Generated: 2026-05-10 — answers the user's S57 review: "what does oracle pick for its Omaha hand vs its Hold'em mid hand across every max-rank × structural cell?"*

## TL;DR — what the data says (single sentence each, organized by max-rank)

| max | Oracle's headline behavior | v43's biggest miss |
|---|---|---|
| **A** | Keep A on top, take DS bot whenever achievable (52–95% DS rate by cell), prefer the **highest mid_high** in joint cells, fall back to 4-flush+ms route when joint isn't achievable (54% of A-alts). | Over-routes `tA_SS_mu` by +11% — under-uses DS bot when joint isn't achievable. |
| **K** | Keep K on top in joint cells (~90%) but **drop K off top in `DS_NO_JOINT`** 34% of the time (oracle K-on-top 66% vs v43 87%). | Same SS_mu over-pick (+11.6%); over-keeps K on top by ~21%. |
| **Q** | Same pattern but Q-on-top drop is sharper: oracle 48%, v43 68% in `DS_NO_JOINT`. | SS_mu over by +8.7%; Q over-on-top by +20%. |
| **J** | **Joint take-rate drops to 54%** — oracle increasingly takes `DS_NONJOINT` (53.1%) and `SS_MS_NONMAX` (14.5%). 76% of `DS_NO_JOINT` picks have non-J top. | t2_SS_ms over by +4.2%, tJ_SS_mu over by +2.7%. |
| **T** | Joint take-rate **36%**. `DS_NONJOINT` is 56% of picks. `SS_MS_NONMAX` is 17%. Oracle keeps T-on-top only ~11% in `DS_NO_JOINT`. | t2_SS_ms +4.9%, t2_SS_mu +8.7% — v43 stubbornly takes max-on-top or 2-on-top SS. |
| **9** | Joint **22%**. `DS_NONJOINT` 60%. `SS_MS_NONMAX` 18%. 9-on-top only 4% in `DS_NO_JOINT`. | t2_SS_mu +11.9%, t2_SS_ms +4.2%. |
| **8** | Joint **13%**. `DS_NONJOINT` 65%. `SS_MS_NONMAX` 17%. 8-on-top almost never in `DS_NO_JOINT`. | t2_SS_mu +14.7%, t2_SS_ms +6.6%. |

**Headline single sentence:** Oracle is **mid-first within JOINT** (preferring the joint config with the highest suited mid_high, not the strongest DS bot pair), but at lower max-ranks it increasingly **abandons JOINT in favor of `DS_NONJOINT` configs that put max-rank into the bot to enable a stronger overall structure with a lower top**.

---

## Method

* **Data:** All 1,226,940 canonical high_only hands, graded against `oracle_grid_full_realistic_n200.bin` (the realistic 70/25/5 mixture profile).
* **Per-max-rank stratification:** A/K/Q/J/T/9/8 (high_only requires 7 distinct ranks; max-rank is unique).
* **Structural cell:** 7 mutually-exclusive cells per max-rank:
  * `JOINT_HIGH` — joint (top=max, DS bot, ms mid) achievable AND best mid_high ≥ J(11)
  * `JOINT_MED` — joint achievable AND 8 ≤ best mid_high ≤ T(10)
  * `JOINT_LOW` — joint achievable AND best mid_high ≤ 7
  * `DS_NO_JOINT` — DS-bot-with-max-on-top achievable but no joint
  * `DS_NO_MAXTOP` — DS-bot achievable but only if max-rank goes into the bot
  * `MS_ONLY` — no DS achievable, but a suited mid with max-on-top exists
  * `NEITHER` — no DS, no max-on-top ms_mid
* **Oracle pick classification (6 disjoint classes):**
  * `JOINT_PICK` — top=max AND bot=DS AND mid suited
  * `DS_NONJOINT` — bot=DS but NOT joint (mid unsuited, or top ≠ max)
  * `SS_MS_MAX` — bot=SS, mid suited, top=max
  * `SS_MS_NONMAX` — bot=SS, mid suited, top ≠ max
  * `SS_MU` — bot=SS, mid unsuited (any top)
  * `OTHER` — 4f / 31 / RB

## Big-picture aggregates

### Per-max-rank residual (v43 vs oracle, full grid)

| max | n_hands | pct_opt | mean_regret | $/1000h whole-grid |
|---|---:|---:|---:|---:|
| **A** | 660,660 | 40.95% | $1,831 | **$201.31** |
| **K** | 330,330 | 34.93% | $2,243 | $123.30 |
| **Q** | 150,150 | 32.06% | $2,482 | $62.01 |
| **J** | 60,060 | 30.02% | $2,645 | $26.43 |
| **T** | 20,020 | 32.36% | $2,500 | $8.33 |
| **9** | 5,005 | 35.92% | $2,436 | $2.03 |
| **8** | 715 | 33.29% | $2,698 | $0.32 |
| **all** | 1,226,940 | 37.9% | $2,075 | **$423.73** |

A/K/Q together = 87% of high_only's whole-grid regret. A alone = 47%.

### Oracle pick distribution per max-rank (overall, not stratified by cell)

| max | JOINT_PICK | DS_NONJOINT | SS_MS_MAX | SS_MS_NONMAX | SS_MU | OTHER |
|---|---:|---:|---:|---:|---:|---:|
| A | 13.9% | 34.1% | 21.8% | 1.4% | 11.9% | 17.0% |
| K | 12.6% | 42.4% | 15.4% | 6.7% | 8.0% | 14.8% |
| Q | 11.1% | 47.8% | 11.2% | 9.8% | 6.1% | 14.0% |
| J | 7.9% | 53.1% | 5.9% | 14.5% | 4.8% | 13.8% |
| T | 5.3% | 56.2% | 3.2% | 16.8% | 5.0% | 13.5% |
| 9 | 3.3% | 59.8% | 1.1% | 18.0% | 5.3% | 12.5% |
| 8 | 2.0% | 65.3% | 0.3% | 17.1% | 4.9% | 10.5% |

**Two clear trends as max-rank drops:**
1. `DS_NONJOINT` share grows 34% → 65% (oracle moves max-rank into the bot more often).
2. `SS_MS_NONMAX` grows 1.4% → 18% (oracle keeps a suited mid with a non-max top via SS bot).

`JOINT_PICK` is *only* the dominant strategy at max=A. Everywhere else, `DS_NONJOINT` rules.

### Cell residual cross-tab (v43 vs oracle)

| max | cell | n | % of max-rank | $/1000h | pct_opt |
|---|---|---:|---:|---:|---:|
| A | JOINT_HIGH | 88,200 | 13.4% | $15.90 | **64.4%** |
| A | JOINT_MED | 8,715 | 1.3% | $1.24 | 71.8% |
| A | JOINT_LOW | 105 | 0.0% | $0.01 | 72.4% |
| A | **DS_NO_JOINT** | 415,800 | **62.9%** | **$139.98** | **37.6%** |
| A | DS_NO_MAXTOP | 88,704 | 13.4% | $26.11 | 35.2% |
| A | MS_ONLY | 59,136 | 9.0% | $18.07 | 33.7% |
| K | JOINT_HIGH | 39,690 | 12.0% | $7.46 | 62.2% |
| K | DS_NO_JOINT | 207,900 | 62.9% | **$87.02** | 30.1% |
| K | DS_NO_MAXTOP | 44,352 | 13.4% | $17.42 | 28.7% |
| K | MS_ONLY | 29,568 | 9.0% | $10.06 | 30.9% |
| Q | DS_NO_JOINT | 94,500 | 62.9% | **$44.37** | 26.4% |
| J | DS_NO_JOINT | 37,800 | 62.9% | **$18.75** | 24.8% |
| T | DS_NO_JOINT | 12,600 | 62.9% | $5.82 | 28.0% |
| 9 | DS_NO_JOINT | 3,150 | 62.9% | $1.45 | 30.7% |
| 8 | DS_NO_JOINT | 450 | 62.9% | $0.23 | 29.6% |

`DS_NO_JOINT` is the dominant cell at **every** max-rank (62.9% by structural design) and the dominant residual contributor — **$293/1000h whole-grid summed across max-ranks (~69% of all high_only regret)**.

---

## Cell-by-cell decision matrix (oracle's actual pick profile)

For each (max-rank × cell), this section describes oracle's TOP/BOT/MID picks, the trade-off rule, and v43's mistake pattern.

### max-rank = A

#### A × JOINT_HIGH (n=88,200; $15.90/1000h; pct_opt 64.4%)
* **TOP:** A:99% — *almost always*.
* **BOT:** DS:95%, 4f:3%, 31:1%, SS:1%. Bot longest_run: r1:20%, r2:60%, r3:17%, r4:3%. Bot sum avg 28.6.
* **MID:** suited 98.2%. mid_high distribution K:28%, Q:22%, J:18%, T:10%, 9:9%. Mid sum avg 17.3.
* **Trade-off rule:** Take the joint config with the **highest mid_high** (not the highest bot pair). HO8 shows mean mid-rank-pct=0.67 vs bot-rank-pct=0.36 in joint picks.
* **v43 mistake:** `tA_SS_mu → tA_DS_ms` $5.76/1000h (4,623 hands). v43 misses joint when its ho_v3 features didn't fire (likely the count was 0 because of a structural edge case the ho_v3 enumeration didn't capture).

#### A × JOINT_MED (n=8,715; $1.24/1000h; pct_opt 71.8%)
* **TOP:** A:100%.
* **BOT:** DS:95%, 4f:3%, 31:1%, SS:1%. Less connected (r2:55%, r3:27%, r4:10%) — sum avg 22.4.
* **MID:** suited 98.0%, mid_high T:41%, 9:25%, 8:14%, 7:7%.
* **Trade-off rule:** Same as JOINT_HIGH but with a weaker mid_high pool.
* **v43 mistake:** `tA_SS_mu → tA_DS_ms` $0.47/1000h.

#### A × **DS_NO_JOINT** (n=415,800; **$139.98/1000h**; pct_opt 37.6%) ← BIGGEST RESIDUAL CELL
* **TOP:** A:94%, K:4%, Q:1%, J:0%. Oracle drops Ace off the top 6% of the time even when DS is achievable.
* **BOT:** **DS:52%, SS:38%, 31:10%**. Oracle picks DS over a clean majority. v43: SS:50%, DS:42% — **under-routes DS by 10%**.
* **BOT details:** sum avg 27.9; longest_run r2:59%, r3:19%.
* **MID:** suited **41.4%** (despite "no joint" — mid_suited is achievable via SS+ms even when DS+ms+top=max isn't). mid_high K:24%, Q:19%, J:17%, T:13%, 9:10%. v43 mid_suited only **30.9%** — under by 11%.
* **Trade-off rule:** **Pick DS bot whenever it's achievable + has a decent bot pair_high.** Sacrifice mid suiting for DS strength. If DS bot pair_high is low, fall back to SS+ms_mid.
* **v43 mistakes (top 3):**
  * `tA_SS_mu → tA_DS_mu` n=34,726 mean=$4,336 → **$25.06/1000h** (the biggest mismatch class in all of high_only).
  * `tA_SS_mu → tA_SS_ms` n=32,893 → $23.07/1000h.
  * `tA_SS_ms → tA_DS_mu` n=28,300 → $13.83/1000h.

#### A × DS_NO_MAXTOP (n=88,704; $26.11/1000h; pct_opt 35.2%)
* **TOP:** A:81%, K:12%, Q:4%, J:1%, 2:1% — oracle drops A 19% of the time (vs v43 10%).
* **BOT:** SS:52%, 31:30%, DS:10%. DS rate is LOW here (vs 52% in DS_NO_JOINT) because DS requires max-rank in the bot.
* **MID:** suited 33.5%.
* **Trade-off rule:** When DS forces max-rank into bot, oracle often prefers SS_ms or 31_ms with max on top. But 19% of the time it accepts the max-in-bot trade.
* **v43 mistake:** `tA_SS_mu → tA_31_mu` $2.14/1000h.

#### A × MS_ONLY (n=59,136; $18.07/1000h; pct_opt 33.7%)
* **TOP:** A:98%.
* **BOT:** SS:43%, 31:41%, 4f:13%, RB:3%. No DS available by construction.
* **MID:** suited 45.1%.
* **Trade-off rule:** Take whatever DS-substitute (SS or 31) preserves a suited mid. v43 over-picks 31 (45%) vs SS (39%) — oracle inverts to SS:43% / 31:41%.

---

### max-rank = K

#### K × JOINT_HIGH (n=39,690; $7.46/1000h; pct_opt 62.2%)
* **TOP:** K:90%, Q:5%, 2:2%, J:1%, 3:1% — oracle drops K 10% of the time (vs v43 5%).
* **BOT:** DS:95%, 4f:3%, 31:1%, SS:1%.
* **MID:** suited 96.5%. mid_high Q:29%, J:27%, T:13%, 9:10%, 8:7%.
* **Trade-off rule:** Same joint pattern as A.
* **v43 mistake:** `tK_SS_mu → tK_DS_ms` $2.15/1000h.

#### K × **DS_NO_JOINT** (n=207,900; **$87.02/1000h**; pct_opt 30.1%)
* **TOP:** **K:66%, Q:12%, 2:7%, J:5%, 3:3%** — oracle drops K off the top **34% of the time**, vs v43's 13%. **The biggest v43 mistake at K is keeping K on top too aggressively.**
* **BOT:** DS:58%, SS:32%, 31:9%. v43: SS:51%, DS:41% — under DS by 17%.
* **MID:** suited 51.1% (v43: 37.5%, under by 14%).
* **Trade-off rule:** When joint isn't achievable, **abandon K-on-top for a (low top, DS bot, ms mid) config 1/3 of the time**. This is the structural axis ho_v4 #3+#4 (non-max-top joint) targets.
* **v43 mistakes:** `tK_SS_mu → tK_SS_ms` $7.43, `tK_SS_mu → tK_DS_mu` $7.07, `tK_SS_ms → tK_DS_mu` $4.76.

#### K × MS_ONLY (n=29,568; $10.06/1000h)
* **TOP:** K:78%, Q:10%, 2:5%, J:3%, 3:2% — v43 keeps K on top 97% of the time, way over oracle's 78%.

---

### max-rank = Q

#### Q × JOINT_HIGH (n=13,230; $2.51/1000h; pct_opt 61.3%)
* **TOP:** Q:80%, J:7%, 2:6%, 3:3% — oracle drops Q 20% of the time.
* **BOT:** DS:94%, 4f:3%, 31:2%, SS:2%.
* **MID:** suited 95.0%, mid_high J:45%, T:15%, 9:13%, 8:8%, Q:8%.
* **Trade-off rule:** **Joint with J on mid_high is strongly preferred (45%).** Q on mid_high (8%) is uncommon because using Q in mid means Q's not on top — and Q-on-top is still preferred when joint is available.

#### Q × **DS_NO_JOINT** (n=94,500; **$44.37/1000h**; pct_opt 26.4%)
* **TOP:** Q:48%, 2:15%, J:10%, 3:8%, T:4% — oracle drops Q **52% of the time**. v43 keeps Q on top 68% — over by 20%.
* **BOT:** DS:62%, SS:29%, 31:9%. v43: SS:49%, DS:42% — under DS by 20%.
* **MID:** suited 56.4% (v43 44.7%, under by 12%).
* **Trade-off rule:** Same as K-pattern but more aggressive. The **Q-on-top sacrifice rate is 52%**.
* **v43 mistakes:** `tQ_SS_mu → tQ_SS_ms` $1.90, `tQ_SS_mu → tQ_DS_mu` $1.71, `tQ_SS_ms → tQ_DS_mu` $1.43.

---

### max-rank = J

#### J × JOINT_MED (n=8,715; $1.75/1000h; pct_opt 59.6%)
* **TOP:** J:56%, 2:20%, 3:9% — oracle drops J 44% of the time even in joint-achievable cells.
* **BOT:** DS:90%, mixed otherwise.
* **MID:** suited 88.6%, mid_high T:27%, J:23%, 9:20%, 8:13%.
* **Trade-off rule:** At J-high, joint isn't always taken — oracle often prefers a non-J top with a strong DS bot.

#### J × **DS_NO_JOINT** (n=37,800; **$18.75/1000h**; pct_opt 24.8%)
* **TOP:** 2:27%, **J:24%**, 3:14%, 4:8%, T:7% — **oracle keeps J on top only 24%**, vs v43 31%.
* **BOT:** DS:65%, SS:26%, 31:8%.
* **MID:** suited 60.8%, mid_high J:37% (J moves to mid, not top), T:18%, 9:17%.
* **Trade-off rule:** **Move J from top to either mid (as suited mid pair) or bot. Take 2 or 3 on top.** This is the canonical "max-into-bot/mid" play.
* **v43 mistakes:** `t2_SS_mu → t2_DS_ms` $0.45, `t2_SS_ms → t3_DS_ms` $0.44, `t2_SS_ms → t2_DS_mu` $0.34.

---

### max-rank = T

#### T × DS_NO_JOINT (n=12,600; $5.82/1000h; pct_opt 28.0%)
* **TOP:** 2:34%, 3:19%, **T:11%**, 4:10%, 9:6% — oracle keeps T on top only **11%**.
* **BOT:** DS:68%, SS:25%, 31:7%.
* **MID:** suited 60.9%, mid_high T:57% (T moves to mid pair frequently).
* **Trade-off rule:** Same max-into-mid pattern. T-pair in mid wins matches against a wide opponent range.
* **v43 mistakes:** `t2_SS_mu → t2_DS_ms` $0.21, `t2_SS_ms → t3_DS_ms` $0.19.

---

### max-rank = 9 / 8

#### 9 × DS_NO_JOINT (n=3,150; $1.45/1000h)
* TOP: 2:41%, 3:22%, 4:11%, 7:6%, 6:5%, **9 rarely on top**.
* BOT: DS:69%, SS:24%, 31:6%. MID: suited 59.3%, mid_high 9:65%.
* Rule: 9 goes to mid as a suited pair; bot is DS with low cards; top is a small singleton.

#### 8 × DS_NO_JOINT (n=450; $0.23/1000h)
* Same pattern, more extreme.

---

## Cross-cutting observations (for ho_v4 feature design)

### Observation 1 — DS bot pair_high quality matters more than the count alone

HO9 stratified by `best_DS_bot_pair_high` within joint-achievable hands:

| max | DS_pair_h | n | % oracle picks JOINT | % oracle picks DS_NONJOINT |
|---|---|---:|---:|---:|
| K | J | 3,780 | 93.8% | 1.5% |
| K | Q | 7,560 | 93.7% | 2.0% |
| **K** | **K** | **34,650** | **83.0%** | **11.1%** |
| Q | J | 3,780 | 90.2% | 3.8% |
| **Q** | **Q** | **15,750** | **70.6%** | **22.4%** |
| **J** | **J** | **6,300** | **46.0%** | **44.3%** |
| **T** | **T** | **2,100** | **28.1%** | **61.0%** |

**Pattern:** When `best_DS_bot_pair_high == max_rank` (i.e., the DS bot would contain the max-rank as a suited pair), oracle is **less** likely to pick joint and **more** likely to pick `DS_NONJOINT` — putting max-rank into the bot. v43 has no feature for this (ho_v3 only sees joints WITH top=max).

### Observation 2 — Within JOINT picks, mid-first dominates

HO8 ranked oracle's pick within all joint-configs for the hand. Mean rank-percentile (1.0 = best):

| max | mean_bot_pair_high_pct | mean_mid_high_pct |
|---|---:|---:|
| A | 0.36 | 0.67 |
| K | 0.35 | 0.68 |
| Q | 0.32 | 0.70 |
| J | 0.29 | 0.72 |
| T | 0.26 | 0.74 |
| 9 | 0.26 | 0.75 |
| 8 | 0.24 | 0.81 |

**Mid-high preference widens at lower max-ranks.** Oracle pays much more attention to mid quality than bot pair quality within joints. v43's ho_v3 already exposes max_mid_high; the gap is in feature compositions (the DT may need to see both axes together).

### Observation 3 — Non-max-top joint route covers 47.7% of high_only

Drill HO10 found `n_joint_topNonMax > 0` for 47.7% of high_only hands across **every** max-rank (the count is structurally constant by suit-symmetry of 7 distinct ranks). At Q/J/T/9/8 this route dominates `DS_NONJOINT` picks (the headline strategy at those max-ranks). v43 has no feature for this entire axis.

### Observation 4 — 4-flush + ms_mid is the dominant max=A alt

HO8 found that 54% of A-when-joint-avail "alt picks" are `tmax_4f_ms` — top=A, 4-flush bot, suited mid. At max=A, when oracle skips JOINT (only 5% of joint-avail hands), the 4-flush route is the primary substitute. v43 has no signal for 4-flush+ms with top=max.

---

## Mapping to ho_v4 feature design

| Observation | Feature | Target cell |
|---|---|---|
| #1 (DS bot pair_high quality) | `ho_v4_topMax_DS_max_bot_pair_high_g` | `DS_NO_JOINT` @ all max-ranks |
| #4 (Ace-top 4f+ms alt) | `ho_v4_topMax_4f_ms_max_mid_high_g` | `JOINT_HIGH/MED` @ A (alt route) |
| #3 (non-max-top joint count) | `ho_v4_topNonMax_DS_ms_n_configs_g` | `DS_NO_JOINT` @ K/Q/J/T/9/8 |
| #3 (non-max-top joint quality) | `ho_v4_topNonMax_DS_ms_max_top_rank_g` | `DS_NO_JOINT` @ K/Q/J/T/9/8 |

Observation #2 (mid-first within joint) is already covered by v43's ho_v3 `max_mid_high` feature; the residual is in feature compositions, not new signals.

---

*Decision matrix complete. Below: v44_dt training + grading outcomes.*

---

## v44_dt outcome — SHIPS

| Metric | v43_dt | v44_dt | Δ |
|---|---:|---:|---:|
| Full grid mean regret | 0.1123 | 0.1081 | **−0.0042** |
| Full grid $/1000h | $1,123 | **$1,081** | **−$42** |
| Full grid pct_opt | 63.99% | 64.80% | **+0.81%** |
| Prefix grid $/1000h | $686 | $686 | $0 (by design) |
| Prefix grid pct_opt | 67.13% | 67.13% | $0 (by design) |
| Leaves | 2,177,798 | 2,248,173 | +3.2% |
| Features | 103 | 107 | +4 ho_v4 |

**high_only** within-cat: $2,075 → $1,868 = **−$207 (−10.0%)**, pct_opt 37.9% → 41.8% (+3.9%).

All 7 non-high_only categories (pair, two_pair, trips, trips_pair, three_pair, quads, composite) **byte-identical** to v43 — surgical gating confirmed.

**Three-session high_only collapse** (S55 → S58): $2,796 → $2,411 → $2,075 → $1,868 = **−$928 within-cat (−33.2%)**. Each session collapsed via a different conditional structural axis: ho_v2 (DS-only), ho_v3 (DS+ms joint), ho_v4 (DS bot quality + non-max joint + 4f route).

**Cumulative ML arc (v32 → v44):** **−$634/1000h on full grid across 9 ships** (v34: −$34, v36: −$33, v39: −$237, v40: −$18, v41: −$124, v42: −$79, v43: −$69, v44: −$42).

The ML champion now beats the rule chain (v52 at $2,498) by **$1,417/1000h** — more than half the rule-chain EV deficit.

### Feature importance (v44 ho_v4)

| Rank | Feature | Importance |
|---:|---|---:|
| #47 | `ho_v4_topNonMax_DS_ms_max_top_rank_g` | 0.13% |
| #80 | `ho_v4_topMax_DS_max_bot_pair_high_g` | 0.04% |
| #93 | `ho_v4_topMax_4f_ms_max_mid_high_g` | 0.01% |
| #95 | `ho_v4_topNonMax_DS_ms_n_configs_g` | 0.01% |

The non-max-top joint quality feature (`max_top_rank_g`) ranks notably higher than the count feature alone. The 4f and DS bot pair_high features rank low — but they target narrower populations and still contribute to the −$207 within-cat lift on high_only via surgical routing.

**Methodology consistency with S55–S57:** low individual feature importance can still ship significant lift via surgical gating on high-leverage subsets. v44 confirms this for the 5th consecutive session.

