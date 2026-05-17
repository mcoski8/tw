"""
Monte Carlo simulation: V4 player vs 3 "competent Hold'em/Omaha" opponents.

Models a player following TEMP_PLAY_GUIDE_BY_SHAPE_V4.md perfectly (no
blunders), seated at a 4-handed table against 3 opponents who play the
`mfsuitaware` ("Middle-First Suit-Aware") heuristic — described in the
project's own docs as "the closest proxy to a competent human opponent"
(tournament_50k.py docstring). They're consistent thinkers, Hold'em/Omaha
winners in their other games, but they don't have Taiwanese-specific
edges (no PMID-swap, no defensive inversion, no buyout signature, no
KK/AA rainbow override).

Player strategy proxy: `strategy_v65_mid_pair_chain_extend` (production
chain). This is the closest available approximation of "human applying
V4 guide cleanly + ML routes" — slightly overstates the human's edge
because v65 includes the ML model for some categories where the V4 guide
falls back to default play, but this is the cleanest empirical proxy.

How variance enters:
  1. Cross-hand variance: each simulation samples 1000 hands at random from
     the 50K-hand reference grid. Different hand mixes → different
     trajectories. This is the dominant source of variance in the chart.
  2. Within-hand realization variance: a single Taiwanese hand outcome
     against one opponent has natural per-deal stdev of ~6 points (most
     hands cluster, scoops contribute heavy tails). For 3 opponents
     sharing the same 2 community boards, outcomes are correlated; the
     per-hand sum stdev empirically lands around 8 points = $80 at $10/pt.
     We add Gaussian noise of that scale on top of the expected value.

Output: standalone HTML chart in the project root.

Stake: $10 per point (operator's default; see memory project_taiwanese_stake.md).
Buyout cost: 4 pts = $40 per willing opponent (not simulated here — buyouts
are handled by the player's strategy choice at the table, not by the grid).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import plotly.graph_objects as go  # noqa: E402

from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend as v65_strategy,
)


GRID_PATH = ROOT / "data" / "oracle_grid_50k.npz"
OUTPUT_HTML = ROOT / "MC_SIMULATION_V4_GUIDE.html"

STAKE_DOLLARS_PER_POINT = 10.0
N_OPPONENTS = 3
N_SIMULATIONS = 10
HANDS_PER_SIMULATION = 1000

# Per-hand realization noise (after expected-value lookup).
# Captures the within-hand variance from card luck on a specific deal
# that the grid's mean-EV smooths out. Calibrated to typical Taiwanese
# Poker per-hand outcome spread.
REALIZATION_NOISE_STDEV_PER_HAND = 80.0  # $ per hand, ~$80 at $10/point

# Color palette — distinct enough for 10 lines, color-blind reasonable.
COLORS = [
    "#1f77b4",  # blue
    "#ff7f0e",  # orange
    "#2ca02c",  # green
    "#d62728",  # red
    "#9467bd",  # purple
    "#8c564b",  # brown
    "#e377c2",  # pink
    "#7f7f7f",  # gray
    "#bcbd22",  # olive
    "#17becf",  # teal
]


def main() -> int:
    print(f"Loading {GRID_PATH} ...")
    arr = np.load(GRID_PATH, allow_pickle=True)
    hands_bytes = arr["hands_bytes"]       # (50000, 7), dtype=uint8
    ev_grid = arr["ev_grid"]                # (50000, 4, 105)
    profile_ids = list(arr["profile_ids"])  # ['mfsuitaware', 'omaha', 'topdef', 'weighted']
    n_hands_in_grid = hands_bytes.shape[0]
    print(f"  {n_hands_in_grid:,} hands × {len(profile_ids)} profiles × 105 settings")
    print(f"  profiles: {profile_ids}")

    mfsuitaware_idx = profile_ids.index("mfsuitaware")
    print(f"  using profile_id={mfsuitaware_idx} ({profile_ids[mfsuitaware_idx]}) as the 'competent human' opponent\n")

    # Apply v65 strategy to every hand in the grid.
    print(f"Applying v65 strategy to {n_hands_in_grid:,} hands ...")
    t0 = time.time()
    v65_picks = np.empty(n_hands_in_grid, dtype=np.int32)
    for i in range(n_hands_in_grid):
        v65_picks[i] = int(v65_strategy(hands_bytes[i]))
        if (i + 1) % 10000 == 0:
            print(f"  {i+1:,} / {n_hands_in_grid:,} ({(i+1)/(time.time()-t0):,.0f} hands/s)")
    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_hands_in_grid/elapsed:,.0f} hands/s)\n")

    # Look up per-hand EV at the v65-picked setting vs mfsuitaware.
    # ev_grid[hand_idx, profile_idx, setting_idx] = EV in POINTS per hand
    # against ONE opponent. We'll multiply by N_OPPONENTS and convert to $.
    hand_ev_points_per_opp = ev_grid[np.arange(n_hands_in_grid), mfsuitaware_idx, v65_picks]
    mean_ev_per_hand_per_opp = float(np.mean(hand_ev_points_per_opp))
    std_ev_per_hand_per_opp = float(np.std(hand_ev_points_per_opp))
    print(f"v65 vs mfsuitaware — per-hand-per-opp EV stats over {n_hands_in_grid:,} hands:")
    print(f"  mean = {mean_ev_per_hand_per_opp:+.4f} points/hand/opp")
    print(f"  std  = {std_ev_per_hand_per_opp:.4f} points (cross-hand)")
    print(f"  at $10/point:  mean = ${mean_ev_per_hand_per_opp*STAKE_DOLLARS_PER_POINT:+.2f}/hand/opp")
    print(f"  vs {N_OPPONENTS} opponents: mean = ${mean_ev_per_hand_per_opp*STAKE_DOLLARS_PER_POINT*N_OPPONENTS:+.2f}/hand expected\n")

    # Expected score per hand vs 3-opponent field, in dollars.
    hand_dollars_per_hand_vs_field = (
        hand_ev_points_per_opp * STAKE_DOLLARS_PER_POINT * N_OPPONENTS
    )

    # Run simulations.
    print(f"Running {N_SIMULATIONS} simulations × {HANDS_PER_SIMULATION:,} hands each ...")
    rng = np.random.default_rng(seed=42)  # reproducible
    cumulative_per_sim = np.empty((N_SIMULATIONS, HANDS_PER_SIMULATION), dtype=np.float64)
    final_dollars_per_sim = np.empty(N_SIMULATIONS, dtype=np.float64)

    for sim_idx in range(N_SIMULATIONS):
        # Sample 1000 random hand indices (with replacement — bootstrap).
        sampled_hand_indices = rng.integers(0, n_hands_in_grid, size=HANDS_PER_SIMULATION)
        sampled_expected_dollars = hand_dollars_per_hand_vs_field[sampled_hand_indices]

        # Add per-hand realization noise (Gaussian).
        realization_noise = rng.normal(
            loc=0.0,
            scale=REALIZATION_NOISE_STDEV_PER_HAND,
            size=HANDS_PER_SIMULATION,
        )
        realized_dollars_per_hand = sampled_expected_dollars + realization_noise

        # Cumulative sum.
        cumulative_per_sim[sim_idx] = np.cumsum(realized_dollars_per_hand)
        final_dollars_per_sim[sim_idx] = cumulative_per_sim[sim_idx, -1]
        print(f"  sim {sim_idx+1:2d}/{N_SIMULATIONS}: final = ${final_dollars_per_sim[sim_idx]:+,.0f}")

    # Stats across sims.
    mean_final = float(np.mean(final_dollars_per_sim))
    std_final = float(np.std(final_dollars_per_sim))
    min_final = float(np.min(final_dollars_per_sim))
    max_final = float(np.max(final_dollars_per_sim))
    expected_trend_per_hand = float(
        mean_ev_per_hand_per_opp * STAKE_DOLLARS_PER_POINT * N_OPPONENTS
    )

    print()
    print(f"Final-cumulative stats across {N_SIMULATIONS} sims:")
    print(f"  mean = ${mean_final:+,.0f}")
    print(f"  std  = ${std_final:,.0f}")
    print(f"  min  = ${min_final:+,.0f}")
    print(f"  max  = ${max_final:+,.0f}")
    print(f"  expected (theoretical) = ${expected_trend_per_hand * HANDS_PER_SIMULATION:+,.0f}\n")

    # Build the Plotly chart.
    print(f"Building Plotly chart ...")
    hand_numbers = np.arange(1, HANDS_PER_SIMULATION + 1)

    fig = go.Figure()

    # Add each simulation as a line.
    for sim_idx in range(N_SIMULATIONS):
        fig.add_trace(go.Scatter(
            x=hand_numbers,
            y=cumulative_per_sim[sim_idx],
            mode="lines",
            name=f"Simulation {sim_idx+1}",
            line=dict(color=COLORS[sim_idx], width=1.8),
            hovertemplate=(
                f"<b>Sim {sim_idx+1}</b><br>"
                "Hand #%{x:,}<br>"
                "Cumulative: $%{y:+,.0f}"
                "<extra></extra>"
            ),
        ))

    # Add the expected (theoretical) trend line.
    expected_trend_line = expected_trend_per_hand * hand_numbers
    fig.add_trace(go.Scatter(
        x=hand_numbers,
        y=expected_trend_line,
        mode="lines",
        name="Expected trend (no variance)",
        line=dict(color="black", width=2.5, dash="dash"),
        hovertemplate=(
            "<b>Expected trend</b><br>"
            "Hand #%{x:,}<br>"
            "Expected: $%{y:+,.0f}"
            "<extra></extra>"
        ),
    ))

    # Add zero reference line.
    fig.add_hline(
        y=0,
        line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"),
        annotation_text="break-even",
        annotation_position="bottom right",
        annotation_font_size=10,
    )

    # Annotation with stats summary.
    summary_text = (
        f"<b>Setup</b><br>"
        f"• Stake: ${STAKE_DOLLARS_PER_POINT:.0f}/point<br>"
        f"• {N_OPPONENTS} opponents using mfsuitaware (competent human proxy)<br>"
        f"• Player strategy: v65 production chain<br>"
        f"&nbsp; (closest proxy to V4 guide perfectly applied)<br>"
        f"<br>"
        f"<b>Results across {N_SIMULATIONS} simulations</b><br>"
        f"• Expected: ${expected_trend_per_hand * HANDS_PER_SIMULATION:+,.0f}/1000h<br>"
        f"• Mean final: ${mean_final:+,.0f}<br>"
        f"• Std final: ${std_final:,.0f}<br>"
        f"• Worst sim: ${min_final:+,.0f}<br>"
        f"• Best sim: ${max_final:+,.0f}<br>"
        f"<br>"
        f"<b>Per-hand EV</b><br>"
        f"• vs 1 opponent: ${mean_ev_per_hand_per_opp*STAKE_DOLLARS_PER_POINT:+.2f}<br>"
        f"• vs {N_OPPONENTS}-opp field: ${expected_trend_per_hand:+.2f}<br>"
    )

    fig.add_annotation(
        xref="paper", yref="paper",
        x=0.012, y=0.985,
        xanchor="left", yanchor="top",
        text=summary_text,
        showarrow=False,
        bgcolor="rgba(255,255,255,0.92)",
        bordercolor="rgba(0,0,0,0.4)",
        borderwidth=1,
        borderpad=10,
        font=dict(size=11, family="monospace"),
        align="left",
    )

    # Layout.
    fig.update_layout(
        title=dict(
            text=(
                "<b>Monte Carlo: V4 Play Guide vs 3 Competent Opponents</b><br>"
                f"<sub>{N_SIMULATIONS} simulations × {HANDS_PER_SIMULATION:,} hands each · "
                f"$10/point · opponents = mfsuitaware profile</sub>"
            ),
            x=0.5,
            xanchor="center",
            font=dict(size=18),
        ),
        xaxis=dict(
            title="Hand number",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.08)",
            zeroline=False,
            tickformat=",",
        ),
        yaxis=dict(
            title="Cumulative $ won/lost (at $10/point)",
            showgrid=True,
            gridcolor="rgba(0,0,0,0.08)",
            zeroline=False,
            tickformat="+$,.0f",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="rgba(255,255,255,0.95)",
            bordercolor="rgba(0,0,0,0.4)",
            font_size=12,
        ),
        legend=dict(
            x=0.99, y=0.01,
            xanchor="right", yanchor="bottom",
            bgcolor="rgba(255,255,255,0.85)",
            bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1,
            font_size=11,
        ),
        plot_bgcolor="white",
        width=1400,
        height=800,
        margin=dict(l=80, r=40, t=100, b=70),
    )

    # Save.
    OUTPUT_HTML.parent.mkdir(parents=True, exist_ok=True)
    fig.write_html(
        OUTPUT_HTML,
        include_plotlyjs="cdn",
        full_html=True,
        config={"displayModeBar": True, "displaylogo": False},
    )
    print(f"Chart written to {OUTPUT_HTML}")
    print(f"Open in a browser to interact.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
