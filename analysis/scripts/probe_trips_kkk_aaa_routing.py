"""
Session 34 — Trips KKK / AAA routing probe.

For pure trips of K (KKK) or trips of A (AAA) — no other pair, no quads —
the player MUST split the trips: only 2 of the 3 same-rank cards can fit
in mid (mid is a 2-card hold'em hand). So there are two structural
routings:

  A_paired_mid : 2 of the 3 trips → mid (paired-mid, KK or AA hold'em
                 strength) + 1 trip + 3 kickers → bot
  B_split_to_bot : 2 of the 3 trips → bot (acting as suit anchor for
                   DS-bot) + 1 trip + 1 kicker → mid (regular hold'em)

Plus a marginal C_top variant where the trip rank goes to top, but that
discards 2 trips from a 4-card bot which the constraint never allows
(the bot is 4 cards and we have 3 trips, so at most 2 trips fit on bot
and the 3rd trip must go to either top or mid). C_top: 1 trip → top,
1 trip in mid + 1 kicker, 1 trip + 3 kickers in bot. We include it for
completeness.

Question: when the DS-bot routing is achievable (the 2 bot-trips share
suit-pattern with 2 of the kickers as a 2+2 layout), does BR ever pick
B over A?

Population:
  n_trips == 1 AND trips_rank in {13, 14}
  AND n_pairs == 0 (no trip+pair) AND n_quads == 0

Reports:
  - Mean ΔEV per routing class on the BR
  - pct optimal of each routing
  - "Rule 3 analog" worked example list

Run:
  PYTHONUNBUFFERED=1 python3 analysis/scripts/probe_trips_kkk_aaa_routing.py
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

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
    SUIT_PROFILE_SS,
    SUIT_PROFILE_RAINBOW,
    SUIT_PROFILE_THREE_ONE,
    SUIT_PROFILE_FOUR_FLUSH,
    SUIT_PROFILE_LABELS,
)

GRID_PATH = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
CANON_PATH = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"

EV_TO_DOLLARS = 10.0


def main() -> int:
    print("=" * 80)
    print("Session 34: Trips KKK / AAA routing probe")
    print("=" * 80)

    print("\n[1/4] Loading parquet feature table to identify trips KKK/AAA hands ...", flush=True)
    t0 = time.time()
    ft = pd.read_parquet(FT_PATH, columns=[
        "canonical_id", "n_pairs", "n_trips", "n_quads",
        "trips_rank", "n_broadway", "n_low",
        "suit_max", "suit_2nd",
    ])
    n_total = len(ft)
    n_pairs = ft["n_pairs"].to_numpy()
    n_trips = ft["n_trips"].to_numpy()
    n_quads = ft["n_quads"].to_numpy()
    trips_rank = ft["trips_rank"].to_numpy()
    suit_max = ft["suit_max"].to_numpy()
    suit_2nd = ft["suit_2nd"].to_numpy()

    is_kkk_aaa = (
        (n_trips == 1) &
        (n_pairs == 0) &
        (n_quads == 0) &
        ((trips_rank == 13) | (trips_rank == 14))
    )
    is_kkk = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0) & (trips_rank == 13)
    is_aaa = (n_trips == 1) & (n_pairs == 0) & (n_quads == 0) & (trips_rank == 14)
    n_kkk_aaa = int(is_kkk_aaa.sum())
    n_kkk = int(is_kkk.sum())
    n_aaa = int(is_aaa.sum())
    n_trips_total = int(((n_trips == 1) & (n_pairs == 0) & (n_quads == 0)).sum())
    print(f"  total canonical hands     : {n_total:>10,}")
    print(f"  pure trips (no pair)      : {n_trips_total:>10,}  ({100*n_trips_total/n_total:.2f}%)")
    print(f"  trips KKK or AAA          : {n_kkk_aaa:>10,}  ({100*n_kkk_aaa/n_total:.3f}%)")
    print(f"    of which KKK            : {n_kkk:>10,}")
    print(f"    of which AAA            : {n_aaa:>10,}")
    kkk_aaa_ids = np.where(is_kkk_aaa)[0]
    print(f"  loaded in {time.time()-t0:.1f}s", flush=True)

    print("\n[2/4] Loading canonical hands + oracle grid (memmap) ...", flush=True)
    t0 = time.time()
    ch = read_canonical_hands(CANON_PATH, mode="memmap")
    grid = read_oracle_grid(GRID_PATH, mode="memmap")
    print(f"  loaded in {time.time()-t0:.1f}s", flush=True)

    print(f"\n[3/4] Scanning {n_kkk_aaa:,} KKK/AAA hands; per-hand max-EV in each setting class ...", flush=True)
    print("       A_paired_mid : mid is a pair of trip-rank   (2 of 3 trips → mid)")
    print("       B_split_bot_DS : bot has 2 trip-rank + bot is DS  (2 of 3 trips → bot, anchoring DS)")
    print("       B_split_bot_any : bot has 2 trip-rank (any suit profile)")
    print("       C_top_trip   : top is the trip rank (1 trip on top)")
    print("       BR           : argmax over all 105 settings")
    t0 = time.time()

    rows = []
    last_log = time.time()
    for idx, cid in enumerate(kkk_aaa_ids):
        cid_int = int(cid)
        hand_bytes = np.asarray(ch.hands[cid_int], dtype=np.uint8)
        feats = setting_features_from_bytes(hand_bytes)
        evs = grid.evs[cid_int]
        evs64 = np.asarray(evs, dtype=np.float64)

        tr = int(trips_rank[cid_int])  # 13 or 14

        # A_paired_mid: mid is a pair of trip rank
        mask_a = feats.mid_is_pair & (feats.mid_pair_rank == tr)
        # B_split_bot_DS: bot has 2 cards of trip rank AND bot is DS
        mask_b_ds = (feats.bot_top_pair_rank == tr) & (feats.bot_suit_profile == SUIT_PROFILE_DS)
        mask_b_any = (feats.bot_top_pair_rank == tr)
        # C_top_trip
        mask_c = feats.top_rank == tr

        a_avail = bool(mask_a.any())
        bds_avail = bool(mask_b_ds.any())
        bany_avail = bool(mask_b_any.any())
        c_avail = bool(mask_c.any())

        ev_a = float(evs64[mask_a].max()) if a_avail else float("nan")
        ev_b_ds = float(evs64[mask_b_ds].max()) if bds_avail else float("nan")
        ev_b_any = float(evs64[mask_b_any].max()) if bany_avail else float("nan")
        ev_c = float(evs64[mask_c].max()) if c_avail else float("nan")
        ev_br = float(evs64.max())

        # Derive: do the 3 trips contain at least 2 distinct suits in the
        # pair-cards we'd use? Actually trips have 3 different suits by deck
        # constraint (only 4 suits, 1 of each rank-suit). So always 3
        # different suits among the 3 trips → DS layout depends on the
        # 4 kickers' suits (we need 2 kickers of one of the two trip-suits
        # we put in bot, etc.).
        ranks_in_hand = (hand_bytes // 4) + 2
        suits_in_hand = hand_bytes & 0b11
        trip_pos = [i for i in range(7) if int(ranks_in_hand[i]) == tr]
        assert len(trip_pos) == 3, f"unexpected trip count at cid={cid_int}: {len(trip_pos)}"
        trip_suits = sorted(int(suits_in_hand[i]) for i in trip_pos)
        # Distinct trip suits — should always be 3.
        n_distinct_trip_suits = len(set(trip_suits))

        rows.append({
            "canonical_id": cid_int,
            "trip_rank": tr,
            "n_trip_suits": n_distinct_trip_suits,
            "suit_max": int(suit_max[cid_int]),
            "suit_2nd": int(suit_2nd[cid_int]),
            "n_broadway": int(ft["n_broadway"].iloc[cid_int]),
            "n_low": int(ft["n_low"].iloc[cid_int]),
            "ev_a_paired_mid": ev_a,
            "ev_b_bot_ds": ev_b_ds,
            "ev_b_bot_any": ev_b_any,
            "ev_c_top_trip": ev_c,
            "ev_br": ev_br,
            "a_avail": a_avail,
            "bds_avail": bds_avail,
            "bany_avail": bany_avail,
            "c_avail": c_avail,
            "regret_a": ev_br - ev_a if a_avail else float("nan"),
            "regret_bds": ev_br - ev_b_ds if bds_avail else float("nan"),
            "regret_bany": ev_br - ev_b_any if bany_avail else float("nan"),
            "delta_a_minus_bds": ev_a - ev_b_ds if a_avail and bds_avail else float("nan"),
            "delta_a_minus_bany": ev_a - ev_b_any if a_avail and bany_avail else float("nan"),
        })

        if time.time() - last_log > 5:
            print(f"  ... {idx+1:>8,}/{n_kkk_aaa:,} ({(idx+1)/(time.time()-t0):.0f}/s)", flush=True)
            last_log = time.time()

    df = pd.DataFrame(rows)
    print(f"  scanned in {time.time()-t0:.1f}s", flush=True)

    print("\n[4/4] Aggregate report")
    print("=" * 80)
    print(f"hands processed                    : {len(df):>10,}")
    print(f"  A_paired_mid available           : {int(df['a_avail'].sum()):>10,}  "
          f"({100.0 * df['a_avail'].mean():.1f}%)")
    print(f"  B_bot_DS available               : {int(df['bds_avail'].sum()):>10,}  "
          f"({100.0 * df['bds_avail'].mean():.1f}%)")
    print(f"  B_bot_any (any-suit) available   : {int(df['bany_avail'].sum()):>10,}  "
          f"({100.0 * df['bany_avail'].mean():.1f}%)")
    print(f"  C_top_trip available             : {int(df['c_avail'].sum()):>10,}  "
          f"({100.0 * df['c_avail'].mean():.1f}%)")

    def show_routing(label: str, subset: pd.DataFrame):
        if len(subset) == 0:
            print(f"\n[{label}]  (empty)")
            return
        print(f"\n[{label}]  n={len(subset):,}")
        for col, descr in [
            ("ev_a_paired_mid", "A_paired_mid"),
            ("ev_b_bot_ds",    "B_bot_DS    "),
            ("ev_b_bot_any",   "B_bot_any   "),
            ("ev_c_top_trip",  "C_top_trip  "),
        ]:
            avail_col = subset[col].dropna()
            if len(avail_col) == 0:
                print(f"  {descr}  : (always unavailable)")
                continue
            mean_ev = avail_col.mean()
            # pct_optimal
            pct_opt = float(
                (subset[col].fillna(-1e9) >= subset["ev_br"] - 1e-9).mean()
            ) * 100
            print(f"  {descr}  : avail on {len(avail_col):>7,}  "
                  f"mean_EV={mean_ev:+.4f}  "
                  f"pct_optimal={pct_opt:5.2f}%")

        # Direct comparison of A vs B_DS within the subset where both are available
        avail_both = subset.dropna(subset=["ev_a_paired_mid", "ev_b_bot_ds"])
        if len(avail_both) > 0:
            d = (avail_both["ev_a_paired_mid"] - avail_both["ev_b_bot_ds"]).to_numpy()
            n_a_wins = int((d > 1e-9).sum())
            n_chop = int((np.abs(d) <= 1e-9).sum())
            n_b_wins = int((d < -1e-9).sum())
            print(f"  A vs B_DS  (both avail n={len(avail_both):,}):  "
                  f"mean Δ(A-B)={d.mean():+.4f}  "
                  f"A wins {100*n_a_wins/len(d):4.1f}% / chop {100*n_chop/len(d):4.1f}% / "
                  f"B wins {100*n_b_wins/len(d):4.1f}%")
            if n_b_wins > 0:
                print(f"  TOP 5 hands where B_DS strictly beats A_paired_mid:")
                d_sorted = avail_both.assign(_d=d).sort_values("_d").head(5)
                for _, r in d_sorted.iterrows():
                    print(f"    cid={r['canonical_id']:>9}  trip_rank={int(r['trip_rank'])}  "
                          f"smax={int(r['suit_max'])}  s2nd={int(r['suit_2nd'])}  "
                          f"nbway={int(r['n_broadway'])}  nlow={int(r['n_low'])}  "
                          f"Δ(A-B)={r['_d']:+.4f}  ev_A={r['ev_a_paired_mid']:.3f}  "
                          f"ev_B={r['ev_b_bot_ds']:.3f}  ev_BR={r['ev_br']:.3f}")
        # And A vs B_any (broader)
        avail_both_any = subset.dropna(subset=["ev_a_paired_mid", "ev_b_bot_any"])
        if len(avail_both_any) > 0:
            d_any = (avail_both_any["ev_a_paired_mid"] - avail_both_any["ev_b_bot_any"]).to_numpy()
            print(f"  A vs B_any (both avail n={len(avail_both_any):,}):  "
                  f"mean Δ(A-B)={d_any.mean():+.4f}  "
                  f"A wins {100*(d_any>1e-9).mean()*100:4.1f}% / chop {100*(np.abs(d_any)<=1e-9).mean()*100:4.1f}% / "
                  f"B wins {100*(d_any<-1e-9).mean()*100:4.1f}%")

    show_routing("ALL trips KKK or AAA", df)
    show_routing("KKK only (trip rank=13)", df[df["trip_rank"] == 13])
    show_routing("AAA only (trip rank=14)", df[df["trip_rank"] == 14])
    show_routing("DS-bot routing AVAILABLE", df[df["bds_avail"] == True])

    # WIN-ECONOMICS
    print("\nWIN-RATE ECONOMICS (B_DS strictly beats A_paired_mid):")
    avail_both = df.dropna(subset=["ev_a_paired_mid", "ev_b_bot_ds"])
    bds_wins = avail_both[(avail_both["ev_a_paired_mid"] - avail_both["ev_b_bot_ds"]) < -1e-9]
    print(f"  hands where B_DS strictly beats A : {len(bds_wins):>10,} / {len(avail_both):,} "
          f"({100*len(bds_wins)/max(len(avail_both),1):.2f}% of both-available)")
    if len(bds_wins) > 0:
        gain = (bds_wins["ev_b_bot_ds"] - bds_wins["ev_a_paired_mid"]).to_numpy()
        print(f"  among those, mean EV gain per hand : {gain.mean():+.4f}")
        # If we always picked the better of {A, B_DS} (oracle-omniscient):
        upper_bound_per_kkk_aaa = (
            bds_wins["ev_b_bot_ds"].sum() - bds_wins["ev_a_paired_mid"].sum()
        ) / len(df)
        print(f"  upper-bound EV/hand if rule perfectly switches : {upper_bound_per_kkk_aaa:+.4f} "
              f"(${upper_bound_per_kkk_aaa * EV_TO_DOLLARS * 1000:+,.0f}/1000h within KKK/AAA)")
        kkk_aaa_share = len(df) / n_total
        print(f"  KKK/AAA share of full grid : {100*kkk_aaa_share:.3f}%")
        per_pop = upper_bound_per_kkk_aaa * kkk_aaa_share
        print(f"  whole-grid headline upper bound : ${per_pop * EV_TO_DOLLARS * 1000:+,.1f}/1000h")

    # Cross-tab by suit_2nd
    print("\nCROSS-TAB by suit_2nd (overall hand suit-secondary count):")
    avail_both = df.dropna(subset=["ev_a_paired_mid", "ev_b_bot_ds"])
    if len(avail_both) > 0:
        for s2 in sorted(avail_both["suit_2nd"].unique()):
            sub = avail_both[avail_both["suit_2nd"] == s2]
            if len(sub) == 0: continue
            d = (sub["ev_a_paired_mid"] - sub["ev_b_bot_ds"]).to_numpy()
            n_b = int((d < -1e-9).sum())
            print(f"  suit_2nd={s2}  n={len(sub):>6,}  mean Δ(A-B)={d.mean():+.4f}  "
                  f"B wins {n_b:>5,} ({100*n_b/len(d):4.1f}%)")

    out_csv = ROOT / "data" / "kkk_aaa_routing_probe.csv"
    df.to_csv(out_csv, index=False)
    print(f"\nWrote per-hand frame to {out_csv}  (n={len(df):,})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
