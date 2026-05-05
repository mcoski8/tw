"""
Session 34 — Rule 4 boundary probe: should non-trips KK/AA ever go to bot
when the DS routing is available, with "trash" in mid?

Current Rule 4 says: KK or AA → mid (intact), top = highest non-pair, bot
= remaining 4 cards. The user-asked question is whether the DS-bot
routing (KK/AA-on-bot suit-anchored, two leftover singletons in mid)
ever beats mid-pair on the realistic Oracle Grid.

Population:
  n_pairs == 1, pair_high_rank in {13, 14}, n_trips == 0, n_quads == 0.
  Excludes trips_kk, trips_aa, two_pair_with_kk_or_aa, etc.

Comparison classes (per hand, max-EV setting in each class):
  A_mid : mid_is_pair AND mid_pair_rank == high_pair_rank
          (Rule 4 routing: KK/AA in mid)
  B_bot_ds : bot_top_pair_rank == high_pair_rank AND
             bot_suit_profile == DS
          (KK/AA in bot, bot is double-suited)
  B_bot_any : bot_top_pair_rank == high_pair_rank
              (KK/AA in bot, ANY suit profile)

Reports:
  - mean ΔEV (A − B) and $/1000h equivalent for each comparison
  - per-stratum: pair_rank (13 vs 14), DS availability, suit class of pair
  - count of hands where DS-bot routing is even available
  - top-10 hands where DS-bot WINS (these are the candidate Rule 5
    boundary cases)

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_kk_aa_ds_bot_vs_mid.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from collections import Counter

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
from tw_analysis.oracle_grid import read_oracle_grid    # noqa: E402
from tw_analysis.query import (                          # noqa: E402
    setting_features_from_bytes,
    SUIT_PROFILE_DS,
)

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0  # $/EV-pt project convention


def main() -> int:
    print("=" * 80)
    print("Session 34: Rule 4 boundary probe — KK/AA mid-pair vs DS-bot routing")
    print("=" * 80)

    print("\n[1/4] Loading parquet feature table to identify KK/AA hands ...", flush=True)
    t0 = time.time()
    ft = pd.read_parquet(FT_PATH, columns=[
        "canonical_id", "n_pairs", "n_trips", "n_quads",
        "pair_high_rank", "n_broadway", "n_low",
        "suit_max", "suit_2nd",
    ])
    assert (ft["canonical_id"].values == np.arange(len(ft))).all()
    n_total = len(ft)
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    pair_high = ft["pair_high_rank"].to_numpy()
    suit_max = ft["suit_max"].to_numpy()
    suit_2nd = ft["suit_2nd"].to_numpy()

    is_kk_aa = (
        (n_pairs == 1) &
        (n_trips == 0) &
        (n_quads == 0) &
        ((pair_high == 13) | (pair_high == 14))
    )
    n_kk_aa = int(is_kk_aa.sum())
    n_kk = int(((n_pairs == 1) & (pair_high == 13) & (n_trips == 0) & (n_quads == 0)).sum())
    n_aa = int(((n_pairs == 1) & (pair_high == 14) & (n_trips == 0) & (n_quads == 0)).sum())
    print(f"  total canonical hands  : {n_total:>10,}")
    print(f"  non-trips KK or AA     : {n_kk_aa:>10,}  ({100*n_kk_aa/n_total:.2f}%)")
    print(f"    of which KK          : {n_kk:>10,}  ({100*n_kk/n_total:.2f}%)")
    print(f"    of which AA          : {n_aa:>10,}  ({100*n_aa/n_total:.2f}%)")
    kk_aa_ids = np.where(is_kk_aa)[0]
    print(f"  loaded in {time.time()-t0:.1f}s", flush=True)

    print("\n[2/4] Loading canonical hands + oracle grid (memmap) ...", flush=True)
    t0 = time.time()
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    assert len(grid) == len(ch) == n_total
    print(f"  ch.hands shape: {ch.hands.shape}, grid.evs shape: {grid.evs.shape}")
    print(f"  loaded in {time.time()-t0:.1f}s", flush=True)

    print(f"\n[3/4] Scanning {n_kk_aa:,} KK/AA hands; per-hand max-EV in each setting class ...", flush=True)
    print("       A_mid       : mid_pair_rank == high_pair_rank  (Rule 4 routing)")
    print("       B_bot_ds    : bot_top_pair == high_pair_rank AND bot DS")
    print("       B_bot_any   : bot_top_pair == high_pair_rank  (any suit profile)")
    print("       C_BR        : argmax over all 105 settings  (oracle BR)")
    t0 = time.time()

    rows = []
    n_processed = 0
    n_no_a = 0
    n_no_bds = 0
    last_log = time.time()

    for cid in kk_aa_ids:
        cid_int = int(cid)
        hand_bytes = np.asarray(ch.hands[cid_int], dtype=np.uint8)
        feats = setting_features_from_bytes(hand_bytes)
        evs = grid.evs[cid_int]  # shape (105,)
        evs64 = np.asarray(evs, dtype=np.float64)

        hp_rank = int(pair_high[cid_int])  # 13 or 14

        mask_a_mid = feats.mid_is_pair & (feats.mid_pair_rank == hp_rank)
        mask_b_bot_ds = (
            (feats.bot_top_pair_rank == hp_rank) &
            (feats.bot_suit_profile == SUIT_PROFILE_DS)
        )
        mask_b_bot_any = feats.bot_top_pair_rank == hp_rank

        a_avail = bool(mask_a_mid.any())
        bds_avail = bool(mask_b_bot_ds.any())
        bany_avail = bool(mask_b_bot_any.any())

        if not a_avail:
            # Should never happen for KK/AA — Rule 4 routing always exists.
            n_no_a += 1
            continue

        ev_a = float(evs64[mask_a_mid].max())
        ev_b_ds = float(evs64[mask_b_bot_ds].max()) if bds_avail else float("nan")
        ev_b_any = float(evs64[mask_b_bot_any].max()) if bany_avail else float("nan")
        ev_br = float(evs64.max())

        if not bds_avail:
            n_no_bds += 1

        # Suit profile of the pair itself: are the two pair-cards same suit
        # (mono-suit pair, can NEVER anchor DS) or different suits (can anchor DS)?
        ranks_in_hand = (hand_bytes // 4) + 2
        suits_in_hand = hand_bytes % 4
        pair_pos = [i for i in range(7) if int(ranks_in_hand[i]) == hp_rank]
        assert len(pair_pos) == 2
        pair_two_suits = (int(suits_in_hand[pair_pos[0]]) != int(suits_in_hand[pair_pos[1]]))

        rows.append({
            "canonical_id": cid_int,
            "pair_rank": hp_rank,
            "pair_two_suits": pair_two_suits,
            "suit_max": int(suit_max[cid_int]),
            "suit_2nd": int(suit_2nd[cid_int]),
            "n_broadway": int(ft["n_broadway"].iloc[cid_int]),
            "n_low": int(ft["n_low"].iloc[cid_int]),
            "ev_a_mid": ev_a,
            "ev_b_bot_ds": ev_b_ds,
            "ev_b_bot_any": ev_b_any,
            "ev_br": ev_br,
            "bds_avail": bds_avail,
            "delta_a_minus_bds": ev_a - ev_b_ds if bds_avail else float("nan"),
            "delta_a_minus_bany": ev_a - ev_b_any if bany_avail else float("nan"),
            "regret_rule4": ev_br - ev_a,
        })

        n_processed += 1
        if time.time() - last_log > 5:
            print(f"  ... {n_processed:>8,}/{n_kk_aa:,} processed  "
                  f"({n_processed/(time.time()-t0):.0f}/s)", flush=True)
            last_log = time.time()

    print(f"  scanned {n_processed:,} hands in {time.time()-t0:.1f}s "
          f"({n_processed/(time.time()-t0):.0f}/s)", flush=True)

    df = pd.DataFrame(rows)

    print("\n[4/4] Aggregate report")
    print("=" * 80)
    print(f"hands processed                : {len(df):>10,}")
    print(f"  with DS-bot routing available: {int(df['bds_avail'].sum()):>10,}  "
          f"({100.0 * df['bds_avail'].mean():.1f}%)")
    print(f"  with NO DS-bot available     : {n_no_bds:>10,}  "
          f"({100.0 * n_no_bds / len(df):.1f}%)")

    def show_block(label: str, subset: pd.DataFrame, delta_col: str = "delta_a_minus_bds"):
        if len(subset) == 0:
            print(f"\n[{label}]  (empty subset)")
            return
        deltas = subset[delta_col].dropna().to_numpy()
        if len(deltas) == 0:
            print(f"\n[{label}]  n={len(subset):,}  (no deltas — DS-bot never available)")
            return
        regret = subset["regret_rule4"].to_numpy()
        a_pct_optimal = float((subset["ev_a_mid"] >= subset["ev_br"] - 1e-9).mean()) * 100
        bds_pct_optimal = float(
            (subset["ev_b_bot_ds"].fillna(-1e9) >= subset["ev_br"] - 1e-9).mean()
        ) * 100
        # delta_col: positive = mid wins; negative = bot-DS wins
        n_bot_ds_wins = int((deltas < -1e-9).sum())
        n_chop = int((np.abs(deltas) <= 1e-9).sum())
        n_mid_wins = int((deltas > 1e-9).sum())
        print(f"\n[{label}]  n={len(subset):>8,}  (DS-bot available on n_eff={len(deltas):,})")
        print(f"  Rule 4 mean regret vs BR  : {regret.mean():+.4f} EV "
              f"(${regret.mean() * EV_TO_DOLLARS * 1000:+,.0f}/1000h)")
        print(f"  Rule 4 pct optimal         : {a_pct_optimal:.2f}%")
        print(f"  bot-DS pct optimal         : {bds_pct_optimal:.2f}%")
        print(f"  mean ΔEV (A_mid − B_bot_ds): {deltas.mean():+.4f}  "
              f"(${deltas.mean() * EV_TO_DOLLARS * 1000:+,.0f}/1000h)")
        print(f"  median ΔEV                  : {np.median(deltas):+.4f}")
        print(f"  pct mid wins / chop / bot  : "
              f"{100*n_mid_wins/len(deltas):.1f}% / "
              f"{100*n_chop/len(deltas):.1f}% / "
              f"{100*n_bot_ds_wins/len(deltas):.1f}%")
        # Worst Rule-4-vs-BR-DS hands: where bot-DS beats mid by the most.
        if n_bot_ds_wins > 0:
            avail = subset.dropna(subset=[delta_col]).copy()
            avail = avail.sort_values(delta_col).head(10)
            print(f"  TOP 10 hands where bot-DS WINS (delta most negative):")
            for _, r in avail.iterrows():
                print(f"    cid={r['canonical_id']:>9}  pair={r['pair_rank']}  "
                      f"pair2suits={int(r['pair_two_suits'])}  "
                      f"smax={int(r['suit_max'])}  s2nd={int(r['suit_2nd'])}  "
                      f"nbway={int(r['n_broadway'])}  "
                      f"Δ={r[delta_col]:+.4f}  "
                      f"ev_mid={r['ev_a_mid']:.3f}  ev_botds={r['ev_b_bot_ds']:.3f}  "
                      f"ev_br={r['ev_br']:.3f}")

    # Population-wide.
    show_block("ALL non-trips KK/AA", df)
    # By pair rank.
    show_block("KK only", df[df["pair_rank"] == 13])
    show_block("AA only", df[df["pair_rank"] == 14])
    # Pair-suit anchor: pair has 2 different suits (DS-anchor candidate)
    show_block("Pair has 2 different suits (DS-anchor candidate)",
               df[df["pair_two_suits"] == True])
    show_block("Pair is mono-suit (cannot anchor DS through pair-suits)",
               df[df["pair_two_suits"] == False])
    # Subset that actually has DS-bot routing available.
    show_block("DS-bot routing AVAILABLE (subset)", df[df["bds_avail"] == True])

    # Cross-tab the ΔEV signs by suit_2nd (≥2 means a 2+2 layout is at least
    # geometrically possible somewhere in the hand).
    print("\nCROSS-TAB: ΔEV (A_mid − B_bot_ds) sign by hand suit_2nd")
    avail = df.dropna(subset=["delta_a_minus_bds"])
    if len(avail) > 0:
        for s2 in sorted(avail["suit_2nd"].unique()):
            sub = avail[avail["suit_2nd"] == s2]
            print(f"  suit_2nd={s2}  n={len(sub):>8,}  "
                  f"mean Δ={sub['delta_a_minus_bds'].mean():+.4f}  "
                  f"bot-DS wins = {int((sub['delta_a_minus_bds'] < -1e-9).sum()):>6,} "
                  f"({100*(sub['delta_a_minus_bds'] < -1e-9).mean():.1f}%)")

    # Also: when bot-DS routing is available AND bot-DS wins, what's the
    # average EV gain — i.e. the realized $/1000h on the win-subset only?
    print("\nWIN-RATE ECONOMICS (Rule 4 violations):")
    avail = df.dropna(subset=["delta_a_minus_bds"])
    bot_ds_wins = avail[avail["delta_a_minus_bds"] < -1e-9]
    print(f"  hands where bot-DS strictly beats mid : {len(bot_ds_wins):>10,} / {len(avail):,} "
          f"({100*len(bot_ds_wins)/max(len(avail),1):.2f}%)")
    if len(bot_ds_wins) > 0:
        gain = -bot_ds_wins["delta_a_minus_bds"].to_numpy()
        print(f"  among those, mean EV gain per hand     : {gain.mean():+.4f}")
        print(f"  share of all KK/AA hands             : {100*len(bot_ds_wins)/len(df):.2f}%")
        # Equivalent $/1000h headline for KK/AA category if we took the win
        # every time it's available:
        share_population = len(bot_ds_wins) / len(df)
        per_kk_aa_gain = bot_ds_wins["delta_a_minus_bds"].sum() * (-1) / len(df)
        # i.e. expected EV-per-KK-AA-hand if you switched to bot-DS whenever
        # it strictly beats mid (oracle-omniscient; upper bound).
        print(f"  upper-bound EV/hand if Rule 4* perfect : {per_kk_aa_gain:+.4f}  "
              f"(${per_kk_aa_gain * EV_TO_DOLLARS * 1000:+,.0f}/1000h within KK/AA)")
        # And as a fraction of total population (KK/AA is 7.17% of all hands):
        kk_aa_share_of_pop = len(df) / n_total
        per_pop_gain = per_kk_aa_gain * kk_aa_share_of_pop
        print(f"  = {kk_aa_share_of_pop*100:.2f}% of population × ${per_kk_aa_gain * EV_TO_DOLLARS * 1000:+,.0f}/1000h "
              f"= ${per_pop_gain * EV_TO_DOLLARS * 1000:+,.0f}/1000h on the WHOLE-grid headline")

    out_csv = ROOT / "data" / "kk_aa_rule4_probe.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nWrote per-hand frame to {out_csv}  (n={len(df):,})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
