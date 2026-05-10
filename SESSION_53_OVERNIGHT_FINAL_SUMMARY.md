# Session 53 OVERNIGHT — FINAL SUMMARY

_Generated: 2026-05-10 ~4:30 AM_

## Bottom line

Two ships, six deferrals, comprehensive characterization, ML capacity wall identified.

## Ships

| # | Ship | Track | Δ Full / Prefix |
|---|---|---|---:|
| 1 | **v52** (Rule 17 — comprehensive high_only handler) | Rule chain | **−$17 / $0** |
| 2 | **v36_dt** (capacity ML retrain depth=36 ml=1, 1.06M leaves) | ML champion | **−$33 / +$2** |

**Combined ~+$50/1000h whole-grid full across both production tracks.**

## State at end

- **Rule chain production:** v52 at $2,498 full / $1,522 prefix
- **ML champion:** v36_dt at $1,649 full / $891 prefix
- **Total project rule count:** 17
- **Cumulative since v14_combined:** −$535/1000h on full grid
- **Cumulative S43-S53 arc (rule chain):** −$348 full / −$185 prefix
- **Cumulative ML (v32 → v36):** −$66 full

## Deferred experiments (documented as artifacts)

| # | Strategy | Description | Result | Reason |
|---|---|---|---:|---|
| 1 | v48 | HIMID for J-7 high (sister of v52) | +$8 alone | Superseded by v52 |
| 2 | v50 | v48 + defensive A/K/Q/J at s2≤8 | −$6 vs v48 | A-high defensive HURTS |
| 3 | v54 | Rule 18 HITOP for AA/KK/QQ pair | −$5 vs v52 | Pair = ML territory |
| 4 | v55 | Rule 18 HIBOT for AA/KK/QQ | −$42 vs v52 | Both tie-breaks fail |
| 5 | v56 | Rule 19 force V_B for trips_pair | full +$10 / **prefix −$130** | Fails 2× gate (13×) |
| 6 | v57 | Rule 19 v2 gated trip≥8 | prefix −$52 | Still fails gate |
| 7 | v37_dt | depth=38 ml=1 ML retrain | identical to v36 | Capacity saturated at 33 actual depth |

## Key methodology insights (added to DECISIONS_LOG)

1. **ML capacity is saturated** at 83 features (ml=1 binding constraint, depth ≥ 33 doesn't help). Future ML lift requires NEW feature engineering, not more capacity.

2. **Pair AA/KK/QQ residual ($164/1000h) is ML territory.** Fixed tie-break rules (HITOP, HIBOT) both regress vs v52. Existing Rule 4 + Rule 5 are near-optimal; further gains need adaptive logic or features.

3. **Trips_pair gap ($155/1000h) needs adaptive logic, not fixed force-V_B.** The full grid favors V_B (mid-paired trips) but the prefix favors V_A or other — splitting on trip_rank alone doesn't bridge the gap.

4. **High-rank sub-pops (A/K) defy the defensive playbook.** Even at low s2, oracle still wants A-on-top (91-94%). Don't blindly extend defensive to all max ranks.

5. **Per-(max, s2) characterization is the right diagnostic** for high_only sub-pop rules. Cell-level oracle distributions reveal correct gates.

6. **Layered ships can regress** (v50). Always test the layered combo, not just standalone components.

7. **Pair max ≥ Q off-diagonal:** oracle dominantly prefers pair-mid + SS bot. v52's Rule 1-5 + v3 fall-through approximates this — gap is mostly ML-accessible (v36_dt's pair improvement $1,619 → $1,604 confirms).

8. **Rule chain at v52 is approaching diminishing returns.** Future improvement requires sophisticated heuristics (adaptive triggers, feature-based routing) or ML residual fitting.

## Where money still lives (post-v52)

| Category | Share | Mean reg/1000h | Whole-grid contrib |
|---|---:|---:|---:|
| pair | 46.6% | $1,829 | **$852** ← biggest, ML territory |
| two_pair | 22.3% | $3,211 | $715 |
| high_only | 20.4% | $3,014 | $615 |
| trips_pair | 2.9% | $5,417 | $155 |
| trips | 5.5% | $2,010 | $110 |
| three_pair | 1.9% | $1,696 | $32 |
| composite | 0.25% | $4,445 | $11 |
| quads | 0.24% | $3,235 | $8 |

## Recommended Session 54+ priorities (in order)

1. **New feature engineering for pair zone** — biggest residual ($852), ML-accessible per v36_dt. Could unlock $100-300 more ML lift.
2. **Adaptive trips_pair heuristic** — trip-rank-stratified force-V_B with smarter gates than just trip≥8.
3. **Two_pair max ≥ Q refinement** — v43b regressed prefix; needs sharper gate.
4. **Composite cleanup** — small but tractable.
5. **High_only K/Q non-default-top sub-rules** (Rule 17 v2 — Drill O has data).

## Files committed during overnight

**Strategies (v52 production + sister artifacts):**
- `analysis/scripts/strategy_v48_rules17_21_high_only_HIMID.py` (sister)
- `analysis/scripts/strategy_v50_rules22_23_high_only_defensive.py` (sister)
- `analysis/scripts/strategy_v51_defensive_max_le_J.py` (sister, untested)
- `analysis/scripts/strategy_v52_full_high_only_handler.py` (PRODUCTION rule chain)
- `analysis/scripts/strategy_v53_defensive_KQJ_only.py` (sister, untested)
- `analysis/scripts/strategy_v54_rule18_high_pair_DS.py` (sister, regressed)
- `analysis/scripts/strategy_v55_rule18_hibot.py` (sister, regressed)
- `analysis/scripts/strategy_v56_rule19_trips_pair_VB.py` (sister, deferred)
- `analysis/scripts/strategy_v57_rule19_trips_pair_gated.py` (sister, deferred)

**ML:**
- `analysis/scripts/strategy_v36_dt.py` (PRODUCTION ML champion)
- `analysis/scripts/strategy_v37_dt_SATURATED.py` (sister documenting capacity ceiling)
- `data/v36_dt_model.npz` (640 MB)
- `data/v37_dt_model.npz` (640 MB, identical structure to v36)

**Graders:** v36, v48, v50, v52, v54, v55, v56, v57

**Drills:**
- `drill_Q_high_non_Q_top_characterization.py` (Drill O)
- (in-place pair gap, trips_pair gap, trips gap drills via inline scripts; outputs in /tmp/)

**Reports:**
- `SESSION_53_OVERNIGHT_REPORT.md` (Part 1: v52)
- `SESSION_53_OVERNIGHT_PART2_REPORT.md` (Part 2: v36_dt)
- `SESSION_53_OVERNIGHT_FINAL_SUMMARY.md` (this file)

**Documentation updates:**
- `STRATEGY_GUIDE.md` (Session 53 entry, ML champion table updated to v36_dt)
- `CURRENT_PHASE.md` (rewritten for end of S53)
- `DECISIONS_LOG.md` (Decisions 086, 087 added)

## Stopping criteria reached

- Rule chain ships exhausted in primary residual zones (HIMID family, defensive, V_B trips_pair)
- Pair AA/KK/QQ confirmed ML territory (2 distinct rule attempts both regress)
- Trips_pair confirmed needs adaptive logic (V_B doesn't transfer cleanly to prefix)
- ML capacity saturated at current 83-feature set
- All easy wins captured

User has comprehensive context to discuss next-session priorities. Goodnight 🌙
