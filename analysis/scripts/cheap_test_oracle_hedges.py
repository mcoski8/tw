"""
Session 21 — cheap-test for the path-(A) target pivot (Decision 033 doctrine).

Question (the Step-4 cheap-test):
  If we trained a regression-style strategy that picks the setting with
  highest predicted mean-across-profiles EV (path A.1) — or per-profile DTs
  ensembled (A.2) — what's the upper bound on $/1000h vs v3 / v5_dt?

The argmax-of-mean-EV setting and the per-profile BR are computable from
the full 105×4 EV grid. This script samples N hands from the SAME RNG as
v3_evloss_baseline.py (seed=42) so the hands overlap with v3_evloss_records
and v5_dt_records, then evaluates every hand against all 4 profiles to get
the full grid. With the grid we can score:

  v3                  : strategy_v3(hand)
  v5_dt               : strategy_v5_dt(hand)
  oracle_BR_per_profile: br_<profile> per profile (profile-known upper bound)
  oracle_argmax_mean   : argmax over 105 of mean(ev[s][p] for p in profiles)
                        (== A.1's ev_mean target ceiling — the hedge ceiling)
  oracle_argmax_<p>    : argmax over 105 of ev[s][p]  (== br_<p>)
  oracle_minimax_loss  : argmin over 105 of max_p (br_ev[p] - ev[s][p])

For each strategy we report:
  - per-profile mean EV across the N hands
  - mean-across-profiles EV
  - $/1000h delta vs v5_dt at $10/EV-pt
  - $/1000h delta vs v3 at $10/EV-pt

This is in silico — no training. The numbers are upper bounds (oracle access
to true EVs); a learned approximator will be strictly worse. If the hedge
ceiling (oracle_argmax_mean) is only marginally better than v5_dt's mean,
then path A.1 is unlikely to pay off and we should pivot differently.

Usage:
  python3 analysis/scripts/cheap_test_oracle_hedges.py --hands 200
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

from encode_rules import strategy_v3  # noqa: E402
from strategy_v5_dt import strategy_v5_dt  # noqa: E402
from engine import PROFILES, evaluate_all_profiles  # noqa: E402


SUITS = ["c", "d", "h", "s"]
RANKS_STR = ["2", "3", "4", "5", "6", "7", "8", "9", "T", "J", "Q", "K", "A"]


def byte_to_str(b: int) -> str:
    rank = (b // 4) + 2
    suit = b % 4
    return RANKS_STR[rank - 2] + SUITS[suit]


def deal_random_hand(rng: random.Random) -> np.ndarray:
    bytes_ = rng.sample(range(52), 7)
    return np.array(sorted(bytes_), dtype=np.uint8)


def collect_full_grid(n_hands: int, samples: int, seed: int):
    """Return:
      hands_bytes : (N, 7) uint8
      ev_grid     : (N, P, 105) float64  — EV of setting s vs profile p on hand n
      v3_choice   : (N,) int
      v5_dt_choice: (N,) int
    """
    rng = random.Random(seed)
    P = len(PROFILES)
    grid = np.empty((n_hands, P, 105), dtype=np.float64)
    hands_bytes = np.empty((n_hands, 7), dtype=np.uint8)
    v3_choice = np.empty(n_hands, dtype=np.int32)
    v5_dt_choice = np.empty(n_hands, dtype=np.int32)

    t0 = time.time()
    for h in range(n_hands):
        hand = deal_random_hand(rng)
        hands_bytes[h] = hand
        hand_strs = [byte_to_str(int(b)) for b in hand]
        v3_choice[h] = int(strategy_v3(hand))
        v5_dt_choice[h] = int(strategy_v5_dt(hand))
        results = evaluate_all_profiles(hand_strs, samples=samples, seed=0xC0FFEE + h)
        for pi, (_profile, mc) in enumerate(results):
            for s in mc.settings:
                grid[h, pi, s.setting_index] = s.ev
        if (h + 1) % max(1, n_hands // 10) == 0 or h + 1 == n_hands:
            elapsed = time.time() - t0
            rate = (h + 1) / elapsed
            eta = (n_hands - h - 1) / rate
            print(f"  {h+1:>4}/{n_hands}  elapsed {elapsed:>5.1f}s  rate {rate:.2f}/s  eta {eta:>5.1f}s")
    print(f"\nTotal MC time: {time.time()-t0:.1f}s\n")
    return hands_bytes, grid, v3_choice, v5_dt_choice


def per_strategy_metrics(grid: np.ndarray, choice: np.ndarray, label: str) -> dict:
    """grid: (N, P, 105). choice: (N,) int OR (N, P) int (per-profile)."""
    N, P, _ = grid.shape
    if choice.ndim == 1:
        # Fixed setting per hand — vectorised gather.
        ev_per_profile = np.empty((N, P), dtype=np.float64)
        for p in range(P):
            ev_per_profile[:, p] = grid[np.arange(N), p, choice]
    else:
        # Per-profile setting (oracle BR-per-profile case).
        ev_per_profile = np.empty((N, P), dtype=np.float64)
        for p in range(P):
            ev_per_profile[:, p] = grid[np.arange(N), p, choice[:, p]]
    mean_per_profile = ev_per_profile.mean(axis=0)  # (P,)
    grand_mean = mean_per_profile.mean()
    return {
        "label": label,
        "mean_per_profile": mean_per_profile,
        "grand_mean": grand_mean,
        "ev_per_profile": ev_per_profile,
    }


def report(metrics: list[dict], v3_grand: float, v5_grand: float, samples: int) -> None:
    profile_ids = [p.id for p in PROFILES]
    P = len(profile_ids)
    header = f"{'strategy':<28}" + "".join(f"{pid:>13}" for pid in profile_ids) + f"{'mean':>12}{'$/1000 vs v3':>16}{'$/1000 vs v5':>16}"
    print(header)
    print("-" * len(header))
    for m in metrics:
        row = f"{m['label']:<28}"
        for p in range(P):
            row += f"{m['mean_per_profile'][p]:>+13.4f}"
        row += f"{m['grand_mean']:>+12.4f}"
        row += f"{(m['grand_mean'] - v3_grand) * 10000:>+16.0f}"
        row += f"{(m['grand_mean'] - v5_grand) * 10000:>+16.0f}"
        print(row)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--hands", type=int, default=200)
    ap.add_argument("--samples", type=int, default=1000)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--save-grid", type=str, default=None,
                    help="optional path to save the (N,P,105) EV grid as .npz")
    args = ap.parse_args()

    print(f"Cheap-test oracle hedges: hands={args.hands}  samples={args.samples}  seed={args.seed}")
    print(f"Profiles: {[p.id for p in PROFILES]}\n")

    hands_bytes, grid, v3_choice, v5_dt_choice = collect_full_grid(
        args.hands, args.samples, args.seed
    )
    P = len(PROFILES)

    # Per-profile BR setting (oracle, profile known).
    br_per_profile = grid.argmax(axis=2)  # (N, P)
    # Hedge: argmax over 105 of mean across profiles.
    mean_grid = grid.mean(axis=1)  # (N, 105)
    argmax_mean = mean_grid.argmax(axis=1)  # (N,)
    # Per-profile argmax (each is the BR for that profile, shown alone).
    argmax_per_profile = [grid[:, p, :].argmax(axis=1) for p in range(P)]
    # Minimax-loss hedge:
    #   For each (n, s) compute loss[n][p] = br_ev[n][p] - ev[n][p][s]
    #   then argmin over s of max_p loss = argmin_s max_p (-grid[n,p,s] + br_ev[n,p])
    br_ev = np.array([grid[np.arange(grid.shape[0]), p, br_per_profile[:, p]] for p in range(P)]).T  # (N,P)
    loss_grid = br_ev[:, :, None] - grid  # (N, P, 105)
    minimax_idx = loss_grid.max(axis=1).argmin(axis=1)  # (N,)

    # Score every strategy.
    metrics = []
    metrics.append(per_strategy_metrics(grid, v3_choice, "v3"))
    metrics.append(per_strategy_metrics(grid, v5_dt_choice, "v5_dt"))
    metrics.append(per_strategy_metrics(grid, br_per_profile, "oracle_BR_per_profile"))
    metrics.append(per_strategy_metrics(grid, argmax_mean, "oracle_argmax_mean (A.1)"))
    metrics.append(per_strategy_metrics(grid, minimax_idx, "oracle_minimax_loss"))
    for p, pid in enumerate([pp.id for pp in PROFILES]):
        metrics.append(per_strategy_metrics(grid, argmax_per_profile[p], f"oracle_argmax_{pid}"))

    v3_grand = metrics[0]["grand_mean"]
    v5_grand = metrics[1]["grand_mean"]

    print("=== Mean EV per profile, $/1000h deltas at $10/EV-pt ===\n")
    report(metrics, v3_grand, v5_grand, args.samples)

    print("\n=== EV-loss vs BR (each strategy's mean loss against each profile) ===\n")
    profile_ids = [p.id for p in PROFILES]
    print(f"{'strategy':<28}" + "".join(f"{pid:>13}" for pid in profile_ids) + f"{'mean loss':>13}")
    print("-" * 100)
    for m in metrics:
        row = f"{m['label']:<28}"
        loss_per_profile = (br_ev - m["ev_per_profile"]).mean(axis=0)
        for v in loss_per_profile:
            row += f"{v:>+13.4f}"
        row += f"{loss_per_profile.mean():>+13.4f}"
        print(row)

    # Choice-overlap diagnostics: how often does argmax_mean equal v5_dt or v3?
    print("\n=== Choice-overlap with oracle_argmax_mean ===")
    for label, choice in (("v3", v3_choice), ("v5_dt", v5_dt_choice)):
        agree = float((choice == argmax_mean).mean()) * 100
        print(f"  {label:<14}  agreement with argmax_mean: {agree:.1f}%")
    for p, pid in enumerate(profile_ids):
        agree = float((br_per_profile[:, p] == argmax_mean).mean()) * 100
        print(f"  br_{pid:<11}  agreement with argmax_mean: {agree:.1f}%")

    # How often is argmax_mean unique vs tied with multiple settings?
    # (Ties matter because a learned regressor has to break them somehow.)
    sorted_mean = np.sort(mean_grid, axis=1)
    margin = sorted_mean[:, -1] - sorted_mean[:, -2]
    print(f"\nargmax_mean margin: mean={margin.mean():.4f}  median={np.median(margin):.4f}  "
          f"<0.01={(margin < 0.01).mean()*100:.1f}%  <0.05={(margin < 0.05).mean()*100:.1f}%")

    if args.save_grid:
        out = Path(args.save_grid)
        out.parent.mkdir(parents=True, exist_ok=True)
        np.savez_compressed(
            out,
            hands_bytes=hands_bytes,
            ev_grid=grid,
            v3_choice=v3_choice,
            v5_dt_choice=v5_dt_choice,
            br_per_profile=br_per_profile,
            argmax_mean=argmax_mean,
            minimax_idx=minimax_idx,
            profile_ids=np.array(profile_ids, dtype=object),
        )
        print(f"\nSaved EV grid + choices to {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
