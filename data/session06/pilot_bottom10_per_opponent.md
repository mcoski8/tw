# Bottom-10 Hands by -EV per Opponent Model (50K-hand pilot)

> These are the worst-performing hero hands within the 50K-hand pilot — hero's cards are so weak that no arrangement wins. The solver still picks the least-bad setting; these EVs are floors.

**Methodology**: Session 06 pilot scanned canonical ids 0–49,999 (the lowest-card canonical hands: all 2s, 3s, 4s, 5s; occasional 6, 7, 8 appear in later ids) × 4-model P2-alt panel × N=1000 samples. For each opponent model, hands are sorted by `best_ev` and the **lowest** 10 are reported below, along with the solver's chosen optimal setting.

**EV interpretation**: `best_ev` is hero's net points per matchup — positive means hero wins on average, negative means hero loses. Net-points encoding means `hero_ev + opp_ev = 0` exactly (see Decision 013). Scoop = +20 (or -20); non-scoop ranges from -12 to +12 across the 6 tier matchups.

## Opponent: MFSuitAware-mixed-0.9
*Thoughtful Hold'em-centric player. Picks the best 2-card mid for Hold'em strength and prefers suit-preserving bots within tier. Uses heuristic 90% of samples, Random 10%.*

| # | id | Hand (7 cards) | Structure | Best setting | EV |
|--:|---:|----------------|-----------|--------------|---:|
| 1 | 1376 | `2c 2d 2h 3c 3d 3h 3s` | quads, high=3; 3x 2-suits + 1 | `top [3s]  mid [3d 2d]  bot [3h 3c 2h 2c]` | **-9.839** |
| 2 | 24 | `2c 2d 2h 2s 3c 4c 5c` | quads, 3 singletons, high=5; 4+1+1+1 | `top [3c]  mid [2h 2d]  bot [5c 4c 2s 2c]` | **-9.630** |
| 3 | 0 | `2c 2d 2h 2s 3c 3d 3h` | quads, high=3; 3x 2-suits + 1 | `top [2s]  mid [3h 2h]  bot [3d 3c 2d 2c]` | **-9.611** |
| 4 | 26 | `2c 2d 2h 2s 3c 4c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [6c]  mid [2s 2h]  bot [4c 3c 2d 2c]` | **-9.435** |
| 5 | 28 | `2c 2d 2h 2s 3c 4c 7c` | quads, 3 singletons, high=7; 4+1+1+1 | `top [7c]  mid [2s 2h]  bot [4c 3c 2d 2c]` | **-9.085** |
| 6 | 30 | `2c 2d 2h 2s 3c 4c 8c` | quads, 3 singletons, high=8; 4+1+1+1 | `top [8c]  mid [2s 2h]  bot [4c 3c 2d 2c]` | **-9.037** |
| 7 | 78 | `2c 2d 2h 2s 3c 5c 7c` | quads, 3 singletons, high=7; 4+1+1+1 | `top [3c]  mid [2s 2d]  bot [7c 5c 2h 2c]` | **-8.959** |
| 8 | 320 | `2c 2d 2h 2s 4c 4d 4h` | quads, high=4; 3x 2-suits + 1 | `top [2s]  mid [4h 2h]  bot [4d 4c 2d 2c]` | **-8.946** |
| 9 | 342 | `2c 2d 2h 2s 4c 5c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [6c]  mid [2s 2d]  bot [5c 4c 2h 2c]` | **-8.943** |
| 10 | 32 | `2c 2d 2h 2s 3c 4c 9c` | quads, 3 singletons, high=9; 4+1+1+1 | `top [9c]  mid [2s 2d]  bot [4c 3c 2h 2c]` | **-8.867** |

## Opponent: OmahaFirst-mixed-0.9
*Omaha-priority player. Picks the best 4-card Omaha bottom first, then the highest non-bot card for top and the other two for mid. Uses heuristic 90% of samples.*

| # | id | Hand (7 cards) | Structure | Best setting | EV |
|--:|---:|----------------|-----------|--------------|---:|
| 1 | 0 | `2c 2d 2h 2s 3c 3d 3h` | quads, high=3; 3x 2-suits + 1 | `top [3d]  mid [2s 2d]  bot [3h 3c 2h 2c]` | **-7.183** |
| 2 | 1376 | `2c 2d 2h 3c 3d 3h 3s` | quads, high=3; 3x 2-suits + 1 | `top [2c]  mid [3s 3c]  bot [3h 3d 2h 2d]` | **-7.130** |
| 3 | 320 | `2c 2d 2h 2s 4c 4d 4h` | quads, high=4; 3x 2-suits + 1 | `top [4h]  mid [2s 2h]  bot [4d 4c 2d 2c]` | **-6.857** |
| 4 | 586 | `2c 2d 2h 2s 5c 5d 5h` | quads, high=5; 3x 2-suits + 1 | `top [2s]  mid [5h 5c]  bot [5d 2h 2d 2c]` | **-6.564** |
| 5 | 24 | `2c 2d 2h 2s 3c 4c 5c` | quads, 3 singletons, high=5; 4+1+1+1 | `top [3c]  mid [2s 2d]  bot [5c 4c 2h 2c]` | **-6.490** |
| 6 | 26 | `2c 2d 2h 2s 3c 4c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [6c]  mid [2h 2d]  bot [4c 3c 2s 2c]` | **-6.380** |
| 7 | 28 | `2c 2d 2h 2s 3c 4c 7c` | quads, 3 singletons, high=7; 4+1+1+1 | `top [7c]  mid [2h 2d]  bot [4c 3c 2s 2c]` | **-6.012** |
| 8 | 76 | `2c 2d 2h 2s 3c 5c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [6c]  mid [2h 2d]  bot [5c 3c 2s 2c]` | **-5.953** |
| 9 | 78 | `2c 2d 2h 2s 3c 5c 7c` | quads, 3 singletons, high=7; 4+1+1+1 | `top [7c]  mid [2s 2h]  bot [5c 3c 2d 2c]` | **-5.939** |
| 10 | 342 | `2c 2d 2h 2s 4c 5c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [2d]  mid [2s 2h]  bot [6c 5c 4c 2c]` | **-5.920** |

## Opponent: TopDefensive-mixed-0.9
*Scoop-avoidant / pair-preserving player. Highest-rank non-pair-member goes on top (or highest rank overall if every card is a pair member). Uses heuristic 90% of samples.*

| # | id | Hand (7 cards) | Structure | Best setting | EV |
|--:|---:|----------------|-----------|--------------|---:|
| 1 | 24 | `2c 2d 2h 2s 3c 4c 5c` | quads, 3 singletons, high=5; 4+1+1+1 | `top [3c]  mid [2s 2d]  bot [5c 4c 2h 2c]` | **-9.716** |
| 2 | 0 | `2c 2d 2h 2s 3c 3d 3h` | quads, high=3; 3x 2-suits + 1 | `top [2s]  mid [3h 2h]  bot [3d 3c 2d 2c]` | **-9.597** |
| 3 | 1376 | `2c 2d 2h 3c 3d 3h 3s` | quads, high=3; 3x 2-suits + 1 | `top [3s]  mid [3d 2d]  bot [3h 3c 2h 2c]` | **-9.554** |
| 4 | 26 | `2c 2d 2h 2s 3c 4c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [3c]  mid [2h 2d]  bot [6c 4c 2s 2c]` | **-9.393** |
| 5 | 30 | `2c 2d 2h 2s 3c 4c 8c` | quads, 3 singletons, high=8; 4+1+1+1 | `top [8c]  mid [2h 2d]  bot [4c 3c 2s 2c]` | **-9.092** |
| 6 | 28 | `2c 2d 2h 2s 3c 4c 7c` | quads, 3 singletons, high=7; 4+1+1+1 | `top [7c]  mid [2s 2d]  bot [4c 3c 2h 2c]` | **-9.078** |
| 7 | 342 | `2c 2d 2h 2s 4c 5c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [4c]  mid [2s 2h]  bot [6c 5c 2d 2c]` | **-8.948** |
| 8 | 32 | `2c 2d 2h 2s 3c 4c 9c` | quads, 3 singletons, high=9; 4+1+1+1 | `top [9c]  mid [2s 2d]  bot [4c 3c 2h 2c]` | **-8.850** |
| 9 | 320 | `2c 2d 2h 2s 4c 4d 4h` | quads, high=4; 3x 2-suits + 1 | `top [2s]  mid [4h 2h]  bot [4d 4c 2d 2c]` | **-8.793** |
| 10 | 80 | `2c 2d 2h 2s 3c 5c 8c` | quads, 3 singletons, high=8; 4+1+1+1 | `top [3c]  mid [2h 2d]  bot [8c 5c 2s 2c]` | **-8.779** |

## Opponent: RandomWeighted (pure)
*Casual-reasonable player. Uniform over 'sensible' settings (top among hand's 3 highest-rank cards; mid is either a pair or both broadway); falls back as needed.*

| # | id | Hand (7 cards) | Structure | Best setting | EV |
|--:|---:|----------------|-----------|--------------|---:|
| 1 | 1376 | `2c 2d 2h 3c 3d 3h 3s` | quads, high=3; 3x 2-suits + 1 | `top [2h]  mid [3s 3h]  bot [3d 3c 2d 2c]` | **-7.840** |
| 2 | 24 | `2c 2d 2h 2s 3c 4c 5c` | quads, 3 singletons, high=5; 4+1+1+1 | `top [4c]  mid [2h 2d]  bot [5c 3c 2s 2c]` | **-7.680** |
| 3 | 320 | `2c 2d 2h 2s 4c 4d 4h` | quads, high=4; 3x 2-suits + 1 | `top [4h]  mid [2s 2h]  bot [4d 4c 2d 2c]` | **-7.583** |
| 4 | 0 | `2c 2d 2h 2s 3c 3d 3h` | quads, high=3; 3x 2-suits + 1 | `top [3d]  mid [2s 2d]  bot [3h 3c 2h 2c]` | **-7.529** |
| 5 | 26 | `2c 2d 2h 2s 3c 4c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [3c]  mid [2s 2h]  bot [6c 4c 2d 2c]` | **-7.388** |
| 6 | 342 | `2c 2d 2h 2s 4c 5c 6c` | quads, 3 singletons, high=6; 4+1+1+1 | `top [6c]  mid [2s 2d]  bot [5c 4c 2h 2c]` | **-7.246** |
| 7 | 80 | `2c 2d 2h 2s 3c 5c 8c` | quads, 3 singletons, high=8; 4+1+1+1 | `top [3c]  mid [2s 2h]  bot [8c 5c 2d 2c]` | **-7.192** |
| 8 | 344 | `2c 2d 2h 2s 4c 5c 7c` | quads, 3 singletons, high=7; 4+1+1+1 | `top [7c]  mid [2s 2h]  bot [5c 4c 2d 2c]` | **-7.161** |
| 9 | 45 | `2c 2d 2h 2s 3c 4d 5c` | quads, 3 singletons, high=5; 3+2+1+1 | `top [3c]  mid [2s 2h]  bot [5c 4d 2d 2c]` | **-7.107** |
| 10 | 28 | `2c 2d 2h 2s 3c 4c 7c` | quads, 3 singletons, high=7; 4+1+1+1 | `top [7c]  mid [2h 2d]  bot [4c 3c 2s 2c]` | **-7.101** |

