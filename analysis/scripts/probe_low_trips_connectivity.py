"""
Session 40 — Priority A0.2: Test bot-connectivity as a 4th tier in Rule 6
Step 2 (suit-matching).

USER HYPOTHESIS: At low trips (rank ≤ T) with low kickers, the bot can
sometimes form a connected (4-card run, wheel-eligible, or near-straight)
shape that ought to outweigh the current suit-profile priority.

  Examples the user named:
    trip 5 + kickers 2-3-4 → bot 5,2,3,4   (wheel made: A is on board)
    trip 7 + kickers 4-5-6 → bot 7,4,5,6   (4-card run; needs an 8 or 3)
    trip 6 + kickers 5-7-8 → bot 6,5,7,8   (4-card run; needs a 4 or 9)

The current Rule 6 Step 2 priority (encoded in v33's heuristic-A) is:
  bot_suit_profile (DS=4 > SS=3 > rainbow=2 > 3+1=1 > 4-flush=0)
    × 1,000,000
  + bot_rank_sum × 1,000
  + bot_longest_run × 100

So a DS bot ALWAYS beats a rainbow bot, regardless of run. The question is
whether the oracle ever prefers a higher-run rainbow bot over a low-run
DS or SS bot at low trips.

WHAT THIS PROBE COMPUTES (on the same 30K trips sample as Sessions 37–39):
  Filter to trips with trip_rank ≤ T (10) and the v35 boundary firing A
  (always for trip ≤ J). For each hand, enumerate all 3 trip-to-bot picks.
  For each pick, compute (suit_profile, longest_run, oracle_ev).

  Reports:
    [1] Mean oracle EV stratified by (suit_profile, longest_run): does
        run > 1 add EV beyond what suit_profile predicts?
    [2] Per-hand disagreement: when v33-heuristic's pick differs from
        oracle's pick, what's the (profile, run) signature of each?
    [3] Alternative tier ("DS > rainbow run≥3 > SS > rainbow run<3 > 3+1")
        head-to-head against the v33 priority.
    [4] Wheel-bonus test: for trips ≤ 7 where bot ranks contain {2,3,4,5}
        or A-low-low-low, do oracle EVs jump?

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_low_trips_connectivity.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from collections import defaultdict

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0
SAMPLE_N = 30000
RANK_CHARS = {2: "2", 3: "3", 4: "4", 5: "5", 6: "6", 7: "7", 8: "8",
              9: "9", 10: "T", 11: "J", 12: "Q", 13: "K", 14: "A"}
PROFILE_LABELS = {0: "4-flush", 1: "3+1", 2: "rainbow", 3: "SS", 4: "DS"}


def _bot_suit_profile_score(bot_suits: list[int]) -> int:
    """Higher = better. DS=4, SS=3, rainbow=2, 3+1=1, 4-flush=0.
    Matches v33/v35 heuristic exactly."""
    counts = [0, 0, 0, 0]
    for s in bot_suits:
        counts[s] += 1
    counts.sort(reverse=True)
    if counts[0] == 2 and counts[1] == 2:
        return 4
    if counts[0] == 2 and counts[1] == 1:
        return 3
    if counts[0] == 1:
        return 2
    if counts[0] == 3:
        return 1
    return 0


def _bot_longest_run(bot_ranks: list[int]) -> int:
    """Longest consecutive run of distinct bot ranks (1..4)."""
    distinct = sorted(set(bot_ranks))
    longest = 1
    cur = 1
    for k in range(1, len(distinct)):
        if distinct[k] == distinct[k - 1] + 1:
            cur += 1
            longest = max(longest, cur)
        else:
            cur = 1
    return longest


def _wheel_eligible(bot_ranks: list[int]) -> bool:
    """True if bot ranks contain at least 3 of {A,2,3,4,5}, since the wheel
    A-2-3-4-5 plays straight-with-board-A or straight-with-board-cards."""
    wheel_set = {14, 2, 3, 4, 5}
    return sum(1 for r in bot_ranks if r in wheel_set) >= 3


def main() -> int:
    print("=" * 80)
    print("Session 40: Bot connectivity probe for Rule 6 Step 2 (low trips)")
    print("=" * 80)

    print("\n[1/4] loading feature_table for trips mask ...", flush=True)
    ft = pd.read_parquet(FT_PATH,
                         columns=["n_pairs", "n_trips", "n_quads", "trips_rank"])
    n_trips = ft["n_trips"].to_numpy()
    n_pairs = ft["n_pairs"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    trips_rank_full = ft["trips_rank"].to_numpy()
    mask_trips = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0)
    n_total = len(ft)
    pop_share = float(mask_trips.mean())
    print(f"  pure trips: {int(mask_trips.sum()):,}  ({100*pop_share:.4f}%)")

    print("\n[2/4] loading canonical hands + oracle grid (memmap) ...",
          flush=True)
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    Y = np.asarray(grid.evs[:n_total])

    trips_idx_full = np.where(mask_trips)[0]
    rng = np.random.RandomState(0)
    sample_pos = rng.choice(len(trips_idx_full), SAMPLE_N, replace=False)
    sample_pos.sort()
    sample_canonical_ids = trips_idx_full[sample_pos]
    sample_trip_ranks = trips_rank_full[sample_canonical_ids]

    # Filter: trip_rank ≤ T (10) AND v35 boundary always picks A here.
    mask_low = sample_trip_ranks <= 10
    n_low = int(mask_low.sum())
    print(f"  trip_rank ≤ T subset: {n_low:,}/{SAMPLE_N:,} hands "
          f"({100*n_low/SAMPLE_N:.1f}%)")

    print(f"\n[3/4] enumerating 3 trip-to-bot picks per hand on {n_low:,} "
          f"low-trips hands ...", flush=True)

    rows = []  # one per (hand, pick); columns described below
    t0 = time.time()
    last_log = time.time()
    n_processed = 0

    for i in range(SAMPLE_N):
        if not mask_low[i]:
            continue
        cid = int(sample_canonical_ids[i])
        h = np.asarray(ch.hands[cid], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        tr = int(sample_trip_ranks[i])

        trip_idx = sorted(j for j in range(7) if int(ranks[j]) == tr)
        kicker_idx = sorted(
            (j for j in range(7) if j not in trip_idx),
            key=lambda j: -int(ranks[j]),
        )
        if len(trip_idx) != 3 or len(kicker_idx) != 4:
            continue

        top_pos = kicker_idx[0]
        max_kicker = int(ranks[top_pos])
        other_kickers = kicker_idx[1:4]
        other_kicker_suits = [int(suits[j]) for j in other_kickers]
        other_kicker_ranks = [int(ranks[j]) for j in other_kickers]

        evs_row = np.asarray(Y[cid], dtype=np.float64)

        per_pick = []
        for trip_for_bot_pos_idx in range(3):
            trip_for_bot = trip_idx[trip_for_bot_pos_idx]
            trips_for_mid = [trip_idx[k] for k in range(3)
                             if k != trip_for_bot_pos_idx]
            bot_suits = [int(suits[trip_for_bot])] + other_kicker_suits
            bot_ranks = [int(ranks[trip_for_bot])] + other_kicker_ranks
            profile = _bot_suit_profile_score(bot_suits)
            run = _bot_longest_run(bot_ranks)
            wheel = _wheel_eligible(bot_ranks)
            rank_sum = sum(bot_ranks)
            heuristic_score = (profile * 1_000_000
                               + rank_sum * 1_000
                               + run * 100)
            setting_idx = _setting_index_from_tmb(top_pos,
                                                  trips_for_mid[0],
                                                  trips_for_mid[1])
            oracle_ev = float(evs_row[setting_idx])
            per_pick.append({
                "hand_i": i,
                "trip_rank": tr,
                "max_kicker": max_kicker,
                "trip_pos": trip_for_bot,
                "profile": profile,
                "run": run,
                "wheel": wheel,
                "rank_sum": rank_sum,
                "heuristic_score": heuristic_score,
                "oracle_ev": oracle_ev,
            })
        # Tag heuristic + oracle picks within this hand.
        h_idx = max(range(3), key=lambda k: per_pick[k]["heuristic_score"])
        o_idx = max(range(3), key=lambda k: per_pick[k]["oracle_ev"])
        for k, p in enumerate(per_pick):
            p["is_heuristic"] = (k == h_idx)
            p["is_oracle"] = (k == o_idx)
            rows.append(p)

        n_processed += 1
        if time.time() - last_log > 5:
            rate = n_processed / (time.time() - t0)
            eta_s = (n_low - n_processed) / max(rate, 1.0)
            print(f"    progress {n_processed:>6,}/{n_low:,}  "
                  f"rate={rate:.0f} hands/s  eta {eta_s:.0f}s", flush=True)
            last_log = time.time()

    elapsed = time.time() - t0
    print(f"  done in {elapsed:.1f}s ({n_processed/elapsed:.0f} hands/s, "
          f"{len(rows):,} pick-rows)")

    df = pd.DataFrame(rows)

    def fmt_in(x):
        return x * EV_TO_DOLLARS * 1000

    def fmt_grid(x):
        return x * EV_TO_DOLLARS * 1000 * pop_share

    # ============================================================
    # [1] Mean oracle EV stratified by (suit_profile, longest_run)
    # ============================================================
    print("\n" + "=" * 80)
    print("[1] Mean oracle EV per (suit_profile, longest_run)")
    print("    All trip-to-bot picks across hands with trip_rank ≤ T.")
    print("    Bigger = better. Look for run-length contributing within profile.")
    print("=" * 80)
    print(f"  {'profile':<10}  {'run':>3}  {'n':>6}  {'mean_EV':>9}  "
          f"{'$/1000h_in':>10}")
    for prof in sorted(df["profile"].unique(), reverse=True):
        for run in sorted(df.loc[df["profile"] == prof, "run"].unique()):
            sub = df[(df["profile"] == prof) & (df["run"] == run)]
            if len(sub) < 5:
                continue
            m = sub["oracle_ev"].mean()
            print(f"  {PROFILE_LABELS[prof]:<10}  {run:>3}  {len(sub):>6,}  "
                  f"{m:>+8.4f}  ${fmt_in(m):>+9,.1f}")

    # Per-hand "what's the gap from 'rainbow run k' to the best DS or SS at
    # the same rank floor?" — show that connectivity rarely overpowers profile.
    print("\n[1b] Within-hand: when oracle picks a NON-DS option, what's the run?")
    n_hands = df["hand_i"].nunique()
    oracle_picks = df[df["is_oracle"]].copy()
    print(f"  oracle picks: {len(oracle_picks):,} (one per low-trips hand)")
    profile_run_counts = (oracle_picks.groupby(["profile", "run"])
                          .size().rename("n").reset_index())
    profile_run_counts["pct"] = 100.0 * profile_run_counts["n"] / n_hands
    for _, r in profile_run_counts.iterrows():
        print(f"    {PROFILE_LABELS[int(r['profile'])]:<10} run={int(r['run'])}  "
              f"n={int(r['n']):>5,}  ({r['pct']:>4.1f}%)")

    # ============================================================
    # [2] When v33-heuristic disagrees with oracle, classify
    # ============================================================
    print("\n" + "=" * 80)
    print("[2] Per-hand: heuristic-pick vs oracle-pick disagreement")
    print("=" * 80)
    pivot_h = df[df["is_heuristic"]].set_index("hand_i")
    pivot_o = df[df["is_oracle"]].set_index("hand_i")
    cmp = pivot_h.join(pivot_o, lsuffix="_h", rsuffix="_o")
    disagree = cmp[cmp["trip_pos_h"] != cmp["trip_pos_o"]]
    n_disagree = len(disagree)
    n_total_low = len(cmp)
    print(f"  disagreement rate: {n_disagree:,}/{n_total_low:,} "
          f"({100*n_disagree/n_total_low:.2f}% of low-trips hands)")

    if n_disagree > 0:
        # Profile transition matrix: heuristic profile → oracle profile
        print(f"\n  PROFILE TRANSITIONS (heuristic_profile → oracle_profile)")
        print(f"    h_prof    o_prof    n      pct of disagreements   mean Δev")
        trans = (disagree.groupby(["profile_h", "profile_o"])
                 .agg(n=("oracle_ev_o", "size"),
                      delta=("oracle_ev_o", "mean"),
                      base=("oracle_ev_h", "mean"))
                 .reset_index())
        trans["mean_delta_ev"] = trans["delta"] - trans["base"]
        trans = trans.sort_values("n", ascending=False)
        for _, r in trans.iterrows():
            ph = PROFILE_LABELS[int(r["profile_h"])]
            po = PROFILE_LABELS[int(r["profile_o"])]
            pct = 100 * r["n"] / n_disagree
            print(f"    {ph:<8}  {po:<8}  {int(r['n']):>5,}  {pct:>5.1f}%   "
                  f"${fmt_in(r['mean_delta_ev']):>+9,.1f}/1000h_in")

        # Run transitions: heuristic run → oracle run
        print(f"\n  RUN TRANSITIONS (h_run → o_run) within disagreements")
        print(f"    h_run  o_run    n      pct   mean Δev_$ within trips")
        run_tr = (disagree.groupby(["run_h", "run_o"])
                  .agg(n=("oracle_ev_o", "size"),
                       delta=("oracle_ev_o", "mean"),
                       base=("oracle_ev_h", "mean"))
                  .reset_index())
        run_tr["mean_delta_ev"] = run_tr["delta"] - run_tr["base"]
        run_tr = run_tr.sort_values("n", ascending=False)
        for _, r in run_tr.iterrows():
            pct = 100 * r["n"] / n_disagree
            print(f"      {int(r['run_h'])}      {int(r['run_o'])}   "
                  f"{int(r['n']):>5,}  {pct:>5.1f}%   "
                  f"${fmt_in(r['mean_delta_ev']):>+9,.1f}")

        # Overall lift if we always picked oracle vs heuristic on disagreements
        mean_lift_hand = (disagree["oracle_ev_o"]
                          - disagree["oracle_ev_h"]).mean()
        gain_low = mean_lift_hand * (n_disagree / n_total_low)
        gain_grid = gain_low * (n_total_low / SAMPLE_N) * pop_share
        print(f"\n  ORACLE-vs-HEURISTIC headline (within A-variant trip-to-bot pick):")
        print(f"    mean lift on disagreements: ${fmt_in(mean_lift_hand):+,.1f}/1000h_in")
        print(f"    amortized over low-trips:   ${fmt_in(gain_low):+,.1f}/1000h_within_low_trips")
        print(f"    amortized over whole-grid:  ${fmt_grid(gain_low * (n_total_low/SAMPLE_N)):+,.2f}/1000h whole-grid")

    # ============================================================
    # [3] Alt tier "DS > rainbow run≥3 > SS > rainbow run<3 > 3+1"
    # ============================================================
    print("\n" + "=" * 80)
    print("[3] Alternative priority: DS > rainbow run≥3 > SS > rainbow run<3 > 3+1")
    print("=" * 80)

    def _alt_score(row):
        """Connectivity-aware tier. Higher = better."""
        prof = row["profile"]
        run = row["run"]
        if prof == 4:                           # DS
            tier = 5
        elif prof == 2 and run >= 3:            # rainbow run≥3
            tier = 4
        elif prof == 3:                         # SS
            tier = 3
        elif prof == 2:                         # rainbow run<3
            tier = 2
        elif prof == 1:                         # 3+1
            tier = 1
        else:                                   # 4-flush
            tier = 0
        return tier * 1_000_000 + row["rank_sum"] * 1_000 + run * 100

    df["alt_score"] = df.apply(_alt_score, axis=1)
    # Per-hand: pick max alt_score, compare oracle EV vs heuristic and oracle.
    alt_picks = (df.sort_values(["hand_i", "alt_score"], ascending=[True, False])
                  .groupby("hand_i").first().reset_index())
    alt_pivot = alt_picks.set_index("hand_i")
    cmp2 = pivot_h.join(alt_pivot, lsuffix="_h", rsuffix="_a")
    delta_alt_h = (cmp2["oracle_ev_a"] - cmp2["oracle_ev_h"]).mean()
    delta_alt_o = (cmp2["oracle_ev_a"] - pivot_o["oracle_ev"]).mean()
    print(f"  mean alt_picked_EV − heuristic_EV: ${fmt_in(delta_alt_h):+,.1f}/1000h_in_low_trips")
    print(f"  mean alt_picked_EV − oracle_EV:   ${fmt_in(delta_alt_o):+,.1f}/1000h_in_low_trips "
          f"(0 = matches oracle)")
    grid_gain_alt = delta_alt_h * (n_total_low / SAMPLE_N) * pop_share
    print(f"  whole-grid lift over heuristic: ${fmt_grid(delta_alt_h * (n_total_low/SAMPLE_N)):+,.2f}/1000h")

    # ============================================================
    # [4] Wheel-eligible bonus test
    # ============================================================
    print("\n" + "=" * 80)
    print("[4] Wheel-eligible bot pick test (≥3 of {A,2,3,4,5} in bot ranks)")
    print("    For trips ≤ 7 (where wheel structures appear most)")
    print("=" * 80)
    wheel_low = df[df["trip_rank"] <= 7].copy()
    if len(wheel_low) > 0:
        for wheel_val in [True, False]:
            sub = wheel_low[wheel_low["wheel"] == wheel_val]
            if len(sub) >= 5:
                m = sub["oracle_ev"].mean()
                print(f"  wheel={wheel_val}:  n={len(sub):,}  "
                      f"mean EV = {m:+.4f}  "
                      f"(${fmt_in(m):+,.1f}/1000h within sub)")

        # Within-hand: among hands with ≥1 wheel-eligible pick AND ≥1 non-wheel,
        # does oracle prefer the wheel one?
        hand_summary = wheel_low.groupby("hand_i").agg(
            any_wheel=("wheel", "any"),
            all_wheel=("wheel", "all"),
        ).reset_index()
        mixed_hands = hand_summary[hand_summary["any_wheel"]
                                   & ~hand_summary["all_wheel"]]["hand_i"]
        wheel_subset = wheel_low[wheel_low["hand_i"].isin(mixed_hands)]
        if len(wheel_subset) > 0:
            within = wheel_subset.groupby("hand_i").apply(
                lambda g: g.loc[g["wheel"], "oracle_ev"].mean()
                          - g.loc[~g["wheel"], "oracle_ev"].mean()
            )
            print(f"\n  Mixed hands (some picks wheel, some not): {len(within):,}")
            print(f"    mean (wheel_pick − non_wheel_pick) EV: "
                  f"${fmt_in(within.mean()):+,.1f}/1000h_in")
            n_wheel_better = int((within > 0).sum())
            print(f"    fraction where wheel_pick beats non_wheel_pick: "
                  f"{100*n_wheel_better/len(within):.1f}%")

    # ============================================================
    # [5] Rainbow-run-4 spotlight: how often does it occur, what's its EV?
    # ============================================================
    print("\n" + "=" * 80)
    print("[5] Rainbow + 4-card run spotlight")
    print("=" * 80)
    rb4 = df[(df["profile"] == 2) & (df["run"] == 4)]
    if len(rb4) > 0:
        print(f"  rainbow-run-4 picks available: {len(rb4):,} across "
              f"{rb4['hand_i'].nunique():,} hands")
        # When this is available, does oracle prefer it?
        rb4_hands = rb4["hand_i"].unique()
        rb4_oracle = oracle_picks[oracle_picks["hand_i"].isin(rb4_hands)]
        n_rb4_oracle = len(rb4_oracle[(rb4_oracle["profile"] == 2)
                                      & (rb4_oracle["run"] == 4)])
        print(f"  oracle picks rainbow-run-4 in {n_rb4_oracle:,}/{len(rb4_hands):,} "
              f"hands where it's available ({100*n_rb4_oracle/len(rb4_hands):.1f}%)")
    else:
        print(f"  rainbow-run-4 picks: 0 in sample")

    print("\n" + "=" * 80)
    print("VERDICT GUIDE")
    print("=" * 80)
    print("  • If [1] shows run >> profile contribution at low-profile cells")
    print("    (e.g., rainbow run=4 mean EV > SS run=1 mean EV), connectivity")
    print("    deserves a tier rearrangement.")
    print("  • If [2] disagreement rate is < 5% AND mean lift < $50/1000h_in,")
    print("    the current priority is good enough — leave Step 2 as-is.")
    print("  • If [3] alt-tier gain > $5/1000h whole-grid, ship the alt-tier")
    print("    in STRATEGY_GUIDE.md Part 6 as a 4th-tier addendum.")
    print("  • If [4]/[5] show wheel/rainbow-4 isn't preferred by oracle,")
    print("    no rule change — note in the guide that connectivity is already")
    print("    a tertiary tiebreaker but not a primary tier.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
