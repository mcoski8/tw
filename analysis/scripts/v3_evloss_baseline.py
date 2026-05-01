"""
EV-loss baseline for strategy_v3 against all 4 production opponent profiles.

For each random 7-card hand:
  1. Compute v3's setting via strategy_v3(sorted_hand_array)
  2. For each profile, run MC over all 105 settings via trainer/src/engine.py
  3. Per-profile EV-loss = mc.best().ev - mc.settings[v3_idx].ev   (always >= 0)

Aggregate:
  - mean / median / p95 EV-loss per profile
  - distribution histogram
  - worst-10 hands per profile

Usage:
  python3 analysis/scripts/v3_evloss_baseline.py --hands 100   # smoke test
  python3 analysis/scripts/v3_evloss_baseline.py --hands 2000  # full run

Reuses trainer/src/engine.py (subprocess to mc --tsv) so we match exactly
the same MC convention used by the trainer and the production .bin solves.
"""
from __future__ import annotations

import argparse
import random
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
TRAINER_SRC = ROOT / "trainer" / "src"
for p in (str(SRC), str(SCRIPTS), str(TRAINER_SRC)):
    if p not in sys.path:
        sys.path.insert(0, p)

from encode_rules import strategy_v3, strategy_v3_no_top_bias  # noqa: E402
from strategy_v5_dt import strategy_v5_dt  # noqa: E402
from strategy_v6_ensemble import strategy_v6_ensemble  # noqa: E402
from strategy_v7_regression import strategy_v7_regression  # noqa: E402
from strategy_v7_patched import strategy_v7_patched  # noqa: E402

STRATEGIES = {
    "v3": strategy_v3,
    "v3_no_top_bias": strategy_v3_no_top_bias,
    "v5_dt": strategy_v5_dt,
    "v6_ensemble": strategy_v6_ensemble,
    "v7_regression": strategy_v7_regression,
    "v7_patched": strategy_v7_patched,
}
from engine import (  # noqa: E402
    PROFILES,
    evaluate_all_profiles,
)


# Card byte = (rank-2)*4 + suit, where suit order matches dealer.py: c=0,d=1,h=2,s=3.
SUITS = ["c", "d", "h", "s"]
RANKS_STR = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]


def byte_to_str(b: int) -> str:
    rank = (b // 4) + 2          # 2..14
    suit = b % 4                  # 0..3
    return RANKS_STR[rank - 2] + SUITS[suit]


def deal_random_hand(rng: random.Random) -> np.ndarray:
    """Return a sorted uint8 array of 7 distinct card bytes."""
    bytes_ = rng.sample(range(52), 7)
    return np.array(sorted(bytes_), dtype=np.uint8)


def run_baseline(n_hands: int, samples: int, seed: int, strategy_fn=strategy_v3):
    rng = random.Random(seed)
    profile_ids = [p.id for p in PROFILES]

    # losses[profile_id] = list of (hand_str, v3_idx, br_idx, v3_ev, br_ev, loss)
    losses: dict[str, list] = {pid: [] for pid in profile_ids}
    # records[h] = full per-hand row (one entry per dealt hand, all 4 profiles flattened)
    records: list[dict] = []

    t0 = time.time()
    for h in range(n_hands):
        hand_array = deal_random_hand(rng)
        hand_strs = [byte_to_str(int(b)) for b in hand_array]
        v3_idx = int(strategy_fn(hand_array))

        # Single subprocess sweep of all 4 profiles (each is one MC call).
        results = evaluate_all_profiles(hand_strs, samples=samples, seed=0xC0FFEE + h)

        rec = {
            "hand_str": " ".join(hand_strs),
            "hand_bytes": [int(b) for b in hand_array],
            "v3_idx": v3_idx,
        }
        max_loss = 0.0
        for profile, mc in results:
            v3_ev = float(mc.settings[v3_idx].ev)
            br = mc.best()
            loss = float(br.ev - v3_ev)  # always >= 0 within MC noise
            if loss > max_loss:
                max_loss = loss
            losses[profile.id].append(
                (" ".join(hand_strs), v3_idx, br.setting_index, v3_ev, br.ev, loss)
            )
            rec[f"br_{profile.id}"] = int(br.setting_index)
            rec[f"v3_ev_{profile.id}"] = v3_ev
            rec[f"br_ev_{profile.id}"] = float(br.ev)
            rec[f"loss_{profile.id}"] = loss
        rec["max_loss"] = max_loss
        records.append(rec)

        if (h + 1) % max(1, n_hands // 20) == 0 or h + 1 == n_hands:
            elapsed = time.time() - t0
            rate = (h + 1) / elapsed
            eta = (n_hands - h - 1) / rate if rate > 0 else 0
            print(
                f"  {h + 1:>5}/{n_hands}  "
                f"elapsed {elapsed:>5.1f}s  rate {rate:.2f}/s  eta {eta:>5.1f}s"
            )

    print(f"\nTotal time: {time.time() - t0:.1f}s\n")
    return losses, records


def save_records(records: list[dict], out_path: Path) -> None:
    """Save per-hand records as parquet for downstream analysis."""
    import pyarrow as pa
    import pyarrow.parquet as pq_writer
    df = pd.DataFrame(records)
    table = pa.Table.from_pandas(df)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pq_writer.write_table(table, out_path)
    print(f"Saved {len(records)} per-hand records to {out_path}")


def report(losses: dict[str, list], samples: int) -> None:
    print(f"=== v3 EV-loss baseline (samples={samples}) ===\n")
    print(
        f"{'profile':<14}{'mean':>10}{'median':>10}{'p95':>10}"
        f"{'p99':>10}{'max':>10}{'%>0.1':>10}{'%>0.5':>10}"
    )
    print("-" * 84)

    for pid, rows in losses.items():
        loss_arr = np.array([r[5] for r in rows])
        # MC noise can produce tiny negatives — clip to 0 for reporting.
        loss_arr = np.clip(loss_arr, 0, None)
        n = len(loss_arr)
        mean = loss_arr.mean()
        median = float(np.median(loss_arr))
        p95 = float(np.percentile(loss_arr, 95))
        p99 = float(np.percentile(loss_arr, 99))
        mx = float(loss_arr.max())
        gt_p1 = float((loss_arr > 0.1).mean()) * 100
        gt_p5 = float((loss_arr > 0.5).mean()) * 100
        print(
            f"{pid:<14}{mean:>10.4f}{median:>10.4f}{p95:>10.4f}"
            f"{p99:>10.4f}{mx:>10.4f}{gt_p1:>9.1f}%{gt_p5:>9.1f}%"
        )

    print("\nWorst 5 hands per profile (highest EV-loss):")
    for pid, rows in losses.items():
        rows_sorted = sorted(rows, key=lambda r: r[5], reverse=True)
        print(f"\n  -- {pid} --")
        for r in rows_sorted[:5]:
            hand_str, v3_i, br_i, v3_ev, br_ev, loss = r
            print(
                f"    {hand_str:<24}  v3={v3_i:>3} (ev={v3_ev:+.3f})  "
                f"br={br_i:>3} (ev={br_ev:+.3f})  loss={loss:.3f}"
            )

    # Distribution buckets
    print("\nLoss-distribution buckets (% of hands per profile):")
    buckets = [0.0, 0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.0]
    print(
        f"  {'profile':<14}"
        + "".join(f"{f'<{b}':>9}" for b in buckets[1:])
        + f"{'>=2.0':>9}"
    )
    for pid, rows in losses.items():
        loss_arr = np.clip(np.array([r[5] for r in rows]), 0, None)
        cells = []
        prev = buckets[0]
        for b in buckets[1:]:
            pct = float(((loss_arr >= prev) & (loss_arr < b)).mean()) * 100
            cells.append(f"{pct:>8.1f}%")
            prev = b
        pct_top = float((loss_arr >= buckets[-1]).mean()) * 100
        cells.append(f"{pct_top:>8.1f}%")
        print(f"  {pid:<14}" + "".join(cells))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hands", type=int, default=100,
                    help="number of random hands to test (default 100)")
    ap.add_argument("--samples", type=int, default=1000,
                    help="MC samples per setting (default 1000)")
    ap.add_argument("--seed", type=int, default=42,
                    help="RNG seed for reproducibility (default 42)")
    ap.add_argument("--save", type=str, default=None,
                    help="if set, write per-hand records to this parquet path")
    ap.add_argument("--strategy", type=str, default="v3",
                    choices=list(STRATEGIES.keys()),
                    help="which strategy function to evaluate")
    args = ap.parse_args()

    strategy_fn = STRATEGIES[args.strategy]
    print(f"Running EV-loss baseline: strategy={args.strategy}  "
          f"hands={args.hands}  profiles={len(PROFILES)}  samples={args.samples}")
    print(f"Profiles: {[p.id for p in PROFILES]}")
    print(f"Seed: {args.seed}\n")

    losses, records = run_baseline(
        args.hands, args.samples, args.seed, strategy_fn=strategy_fn
    )
    report(losses, args.samples)
    if args.save:
        save_records(records, Path(args.save))
    return 0


if __name__ == "__main__":
    sys.exit(main())
