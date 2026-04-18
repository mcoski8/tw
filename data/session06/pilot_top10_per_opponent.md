# Top-10 Hands by +EV per Opponent Model (50K-hand pilot)

> These are the best-performing hero hands within the 50K-hand pilot — hero's cards are strong enough that even against the stated opponent, the solver's optimal setting yields the highest positive EV in the sample.

**Methodology**: Session 06 pilot scanned canonical ids 0–49,999 (the lowest-card canonical hands: all 2s, 3s, 4s, 5s; occasional 6, 7, 8 appear in later ids) × 4-model P2-alt panel × N=1000 samples. For each opponent model, hands are sorted by `best_ev` and the **highest** 10 are reported below, along with the solver's chosen optimal setting.

**EV interpretation**: `best_ev` is hero's net points per matchup — positive means hero wins on average, negative means hero loses. Net-points encoding means `hero_ev + opp_ev = 0` exactly (see Decision 013). Scoop = +20 (or -20); non-scoop ranges from -12 to +12 across the 6 tier matchups.

## Opponent: MFSuitAware-mixed-0.9
*Thoughtful Hold'em-centric player. Picks the best 2-card mid for Hold'em strength and prefers suit-preserving bots within tier. Uses heuristic 90% of samples, Random 10%.*

| # | id | Hand (7 cards) | Structure | Best setting | EV |
|--:|---:|----------------|-----------|--------------|---:|
| 1 | 45832 | `2c 2d 3c 3d Kh Ks Ah` | 3 pairs, 1 singleton, high=A; 3x 2-suits + 1 | `top [Ah]  mid [Ks Kh]  bot [3d 3c 2d 2c]` | **+3.130** |
| 2 | 45836 | `2c 2d 3c 3d Kh Ah As` | 3 pairs, 1 singleton, high=A; 3x 2-suits + 1 | `top [Kh]  mid [As Ah]  bot [3d 3c 2d 2c]` | **+3.069** |
| 3 | 45826 | `2c 2d 3c 3d Kc Kh As` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [As]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+2.847** |
| 4 | 45835 | `2c 2d 3c 3d Kh Ac As` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [Kh]  mid [As Ac]  bot [3d 3c 2d 2c]` | **+2.760** |
| 5 | 45831 | `2c 2d 3c 3d Kh Ks Ac` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [Ac]  mid [Ks Kh]  bot [3d 3c 2d 2c]` | **+2.713** |
| 6 | 45830 | `2c 2d 3c 3d Kc Ah As` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [Kc]  mid [As Ah]  bot [3d 3c 2d 2c]` | **+2.698** |
| 7 | 45800 | `2c 2d 3c 3d Qh Qs Ah` | 3 pairs, 1 singleton, high=A; 3x 2-suits + 1 | `top [Ah]  mid [Qs Qh]  bot [3d 3c 2d 2c]` | **+2.694** |
| 8 | 45825 | `2c 2d 3c 3d Kc Kh Ah` | 3 pairs, 1 singleton, high=A; 3+2+2 | `top [Ah]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+2.651** |
| 9 | 45838 | `2c 2d 3c 3d Ac Ah As` | trips, 2 pairs, high=A; 3+2+1+1 | `top [Ac]  mid [As Ah]  bot [3d 3c 2d 2c]` | **+2.581** |
| 10 | 45824 | `2c 2d 3c 3d Kc Kh Ad` | 3 pairs, 1 singleton, high=A; 3+3+1 | `top [Ad]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+2.560** |

## Opponent: OmahaFirst-mixed-0.9
*Omaha-priority player. Picks the best 4-card Omaha bottom first, then the highest non-bot card for top and the other two for mid. Uses heuristic 90% of samples.*

| # | id | Hand (7 cards) | Structure | Best setting | EV |
|--:|---:|----------------|-----------|--------------|---:|
| 1 | 40842 | `2c 2d 2h Jc Ks Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3x 2-suits + 1 | `top [Ks]  mid [Jc 2c]  bot [Ah Ad 2h 2d]` | **+3.750** |
| 2 | 40962 | `2c 2d 2h Qc Kc Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3+2+2 | `top [Kc]  mid [Qc 2c]  bot [Ah Ad 2h 2d]` | **+3.508** |
| 3 | 40896 | `2c 2d 2h Js Kc Ac Ad` | trips, 1 pair, 2 singletons, high=A; 3+2+1+1 | `top [Kc]  mid [Js 2h]  bot [Ad Ac 2d 2c]` | **+3.464** |
| 4 | 40980 | `2c 2d 2h Qc Ks Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3x 2-suits + 1 | `top [Ks]  mid [Qc 2c]  bot [Ah Ad 2h 2d]` | **+3.450** |
| 5 | 40750 | `2c 2d 2h Jc Qc Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3+2+2 | `top [Qc]  mid [Jc 2c]  bot [Ah Ad 2h 2d]` | **+3.435** |
| 6 | 40811 | `2c 2d 2h Jc Qs Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3x 2-suits + 1 | `top [Qs]  mid [Jc 2c]  bot [Ah Ad 2h 2d]` | **+3.432** |
| 7 | 40792 | `2c 2d 2h Jc Qd Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3+2+2 | `top [Qd]  mid [Jc 2c]  bot [Ah Ad 2h 2d]` | **+3.403** |
| 8 | 40824 | `2c 2d 2h Jc Kc Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3+2+2 | `top [Kc]  mid [Jc 2c]  bot [Ah Ad 2h 2d]` | **+3.378** |
| 9 | 40455 | `2c 2d 2h Tc Kc Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3+2+2 | `top [Kc]  mid [Tc 2c]  bot [Ah Ad 2h 2d]` | **+3.372** |
| 10 | 40877 | `2c 2d 2h Js Qc Ad Ah` | trips, 1 pair, 2 singletons, high=A; 3x 2-suits + 1 | `top [Js]  mid [Qc 2c]  bot [Ah Ad 2h 2d]` | **+3.332** |

## Opponent: TopDefensive-mixed-0.9
*Scoop-avoidant / pair-preserving player. Highest-rank non-pair-member goes on top (or highest rank overall if every card is a pair member). Uses heuristic 90% of samples.*

| # | id | Hand (7 cards) | Structure | Best setting | EV |
|--:|---:|----------------|-----------|--------------|---:|
| 1 | 45832 | `2c 2d 3c 3d Kh Ks Ah` | 3 pairs, 1 singleton, high=A; 3x 2-suits + 1 | `top [Ah]  mid [Ks Kh]  bot [3d 3c 2d 2c]` | **+3.095** |
| 2 | 45836 | `2c 2d 3c 3d Kh Ah As` | 3 pairs, 1 singleton, high=A; 3x 2-suits + 1 | `top [Kh]  mid [As Ah]  bot [3d 3c 2d 2c]` | **+2.904** |
| 3 | 45826 | `2c 2d 3c 3d Kc Kh As` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [As]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+2.770** |
| 4 | 45800 | `2c 2d 3c 3d Qh Qs Ah` | 3 pairs, 1 singleton, high=A; 3x 2-suits + 1 | `top [Ah]  mid [Qs Qh]  bot [3d 3c 2d 2c]` | **+2.643** |
| 5 | 45831 | `2c 2d 3c 3d Kh Ks Ac` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [Ac]  mid [Ks Kh]  bot [3d 3c 2d 2c]` | **+2.594** |
| 6 | 45838 | `2c 2d 3c 3d Ac Ah As` | trips, 2 pairs, high=A; 3+2+1+1 | `top [As]  mid [Ah Ac]  bot [3d 3c 2d 2c]` | **+2.543** |
| 7 | 45835 | `2c 2d 3c 3d Kh Ac As` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [Kh]  mid [As Ac]  bot [3d 3c 2d 2c]` | **+2.526** |
| 8 | 45825 | `2c 2d 3c 3d Kc Kh Ah` | 3 pairs, 1 singleton, high=A; 3+2+2 | `top [Ah]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+2.489** |
| 9 | 45824 | `2c 2d 3c 3d Kc Kh Ad` | 3 pairs, 1 singleton, high=A; 3+3+1 | `top [Ad]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+2.479** |
| 10 | 45823 | `2c 2d 3c 3d Kc Kh Ac` | 3 pairs, 1 singleton, high=A; 4+2+1 | `top [Ac]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+2.470** |

## Opponent: RandomWeighted (pure)
*Casual-reasonable player. Uniform over 'sensible' settings (top among hand's 3 highest-rank cards; mid is either a pair or both broadway); falls back as needed.*

| # | id | Hand (7 cards) | Structure | Best setting | EV |
|--:|---:|----------------|-----------|--------------|---:|
| 1 | 45826 | `2c 2d 3c 3d Kc Kh As` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [As]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+3.680** |
| 2 | 45832 | `2c 2d 3c 3d Kh Ks Ah` | 3 pairs, 1 singleton, high=A; 3x 2-suits + 1 | `top [Ah]  mid [Ks Kh]  bot [3d 3c 2d 2c]` | **+3.650** |
| 3 | 45828 | `2c 2d 3c 3d Kc Ac Ah` | 3 pairs, 1 singleton, high=A; 4+2+1 | `top [Kc]  mid [Ah Ac]  bot [3d 3c 2d 2c]` | **+3.626** |
| 4 | 45836 | `2c 2d 3c 3d Kh Ah As` | 3 pairs, 1 singleton, high=A; 3x 2-suits + 1 | `top [Kh]  mid [As Ah]  bot [3d 3c 2d 2c]` | **+3.555** |
| 5 | 45831 | `2c 2d 3c 3d Kh Ks Ac` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [Ac]  mid [Ks Kh]  bot [3d 3c 2d 2c]` | **+3.516** |
| 6 | 45778 | `2c 2d 3c 3d Qc Qh As` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [As]  mid [Qh Qc]  bot [3d 3c 2d 2c]` | **+3.485** |
| 7 | 45838 | `2c 2d 3c 3d Ac Ah As` | trips, 2 pairs, high=A; 3+2+1+1 | `top [Ac]  mid [As Ah]  bot [3d 3c 2d 2c]` | **+3.442** |
| 8 | 45825 | `2c 2d 3c 3d Kc Kh Ah` | 3 pairs, 1 singleton, high=A; 3+2+2 | `top [Ah]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+3.419** |
| 9 | 45835 | `2c 2d 3c 3d Kh Ac As` | 3 pairs, 1 singleton, high=A; 3+2+1+1 | `top [Kh]  mid [As Ac]  bot [3d 3c 2d 2c]` | **+3.403** |
| 10 | 45823 | `2c 2d 3c 3d Kc Kh Ac` | 3 pairs, 1 singleton, high=A; 4+2+1 | `top [Ac]  mid [Kh Kc]  bot [3d 3c 2d 2c]` | **+3.355** |

