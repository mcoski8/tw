"""
Session 43 — weak-hand high-card defense drill (Q1, Q2, Q5).

Population: high_only (no pair, no trip, no quad). Stratified into 4 zones
that match the user's framing in docs/SESSION_43_WEAK_HAND_DEFENSE.md:
  - J-low: max card <= J  (the "primary defensive zone", ~85.8K hands)
  - Q-high weak: max=Q AND 2nd_highest <= T
  - K-high weak: max=K AND 2nd_highest <= T  (Q2)
  - A-high weak: max=A AND 2nd_highest <= 9   (Q1)

Question: when is high-card-on-top right, vs high-card-in-bot anchoring a
4-flush bot, vs split-the-high-card-into-mid?

Per hand we compute EVs for these candidate settings:

    A_TOP_HI    top=highest, mid=next-two-highest (canonical default)
    B_BOT_FLUSH HI in bot anchoring 4 same-suited cards (if achievable):
                requires suit S with cards>=3 incl. HI;
                top = highest non-S card; mid = remaining 2;
                bot = the 4 cards of suit S (or 3-of-S + 1 lowest non-S
                fallback if S has 3+HI but only 3 of S exist).
    C_TOP_2ND   top=2nd-highest, mid=highest+3rd-highest, bot=rest
                (split-the-high-card variant, the user's "break broadway"
                case in Q2)
    D_TOP_LO    top=lowest singleton, mid=2 highest, bot=rest 4 (counter-
                test: dump weakest to top to free strong mid+bot)

Plus oracle ceilings:
    OC_OVERALL  best of all 105 settings (full ceiling)
    OC_TOP_HI   oracle restricted to top=highest position
    OC_TOP_2ND  oracle restricted to top=2nd-highest position
    OC_TOP_LO   oracle restricted to top=lowest position

Aggregated per stratum:
  - mean regret (the standard $/1000h $-cost-vs-oracle metric)
  - WORST-CASE regret (avoid the 20-pt scoop) — Session 43 methodology rule:
    "weak-hand drills should report worst-case regret in addition to mean".

Validate on full grid (N=200) AND prefix grid (N=1000) per Session 42
methodology gate (rule does not ship if prefix regression > 2x full lift).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_card_defense.py

A 'sample' mode for quick iteration:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_high_card_defense.py --sample 5000
"""
from __future__ import annotations

import argparse
import sys
import time
from collections import defaultdict
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.grade_strategy import categorize_hands  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v39_rule9 import strategy_v39_rule9  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}


def stratum_for(max_r: int, second_r: int) -> str | None:
    """Return stratum label, or None if hand is outside Q1/Q2/Q5 scope."""
    if max_r <= 11:
        # Sub-stratify by max card to surface boundary effects.
        return f"{RANK_CHAR[max_r]}-high"
    if max_r == 12 and second_r <= 10:
        return "Q-high+weak"
    if max_r == 13 and second_r <= 10:
        return "K-high+weak"
    if max_r == 14 and second_r <= 9:
        return "A-high+weak"
    return None


def _settings_with_top_at(top_pos: int) -> list[int]:
    """Return all 15 setting_indexes whose top position equals top_pos."""
    return list(range(top_pos * 15, top_pos * 15 + 15))


def _bot_flush_setting(hand_ranks: np.ndarray, hand_suits: np.ndarray
                        ) -> int | None:
    """Try to construct a 4-flush bot using the highest-rank card.
    Returns the setting_index, or None if no such config exists.

    Logic:
      - Let HI = position of the highest-rank card; let S = suit(HI).
      - Count how many positions have suit S. Need >=4 incl. HI to put
        all 4 in bot.
      - bot = 4 positions of suit S (HI + 3 others).
      - top = highest-rank position whose suit != S (most defensible top).
      - mid = the remaining 2 positions.
    """
    pos_hi = int(np.argmax(hand_ranks))
    s_hi = int(hand_suits[pos_hi])
    same_suit = [j for j in range(7) if int(hand_suits[j]) == s_hi]
    if len(same_suit) < 4:
        return None
    # Pick HI + 3 others of same suit, prefer keeping HI in bot.
    same_suit_sorted = sorted(same_suit, key=lambda j: -int(hand_ranks[j]))
    bot_set = set(same_suit_sorted[:4])  # top 4 by rank within suit S
    if pos_hi not in bot_set:
        # Force HI into bot (drop the lowest of the bot_set).
        bot_set.discard(min(bot_set, key=lambda j: int(hand_ranks[j])))
        bot_set.add(pos_hi)
    # Remaining = 3 cards. Top = highest-rank non-S card (most defensible).
    rem = [j for j in range(7) if j not in bot_set]
    rem.sort(key=lambda j: -int(hand_ranks[j]))
    top_pos = rem[0]
    mid_a, mid_b = sorted(rem[1:3])
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _bot_3flush_extended_setting(hand_ranks: np.ndarray,
                                   hand_suits: np.ndarray) -> int | None:
    """Construct bot = 3 same-suit + 1 lowest-non-S, with HI in those 3.
    Useful when HI's suit has exactly 3 cards (no 4-flush available).

    Returns setting_index or None.
    """
    pos_hi = int(np.argmax(hand_ranks))
    s_hi = int(hand_suits[pos_hi])
    same_suit = [j for j in range(7) if int(hand_suits[j]) == s_hi]
    if len(same_suit) != 3:
        return None
    other = [j for j in range(7) if int(hand_suits[j]) != s_hi]
    if len(other) != 4:
        return None
    other_sorted = sorted(other, key=lambda j: int(hand_ranks[j]))
    # bot = 3 same-suit + lowest non-S (4 cards)
    bot_extra = other_sorted[0]
    bot_set = set(same_suit) | {bot_extra}
    rem = [j for j in range(7) if j not in bot_set]
    rem.sort(key=lambda j: -int(hand_ranks[j]))
    top_pos = rem[0]
    mid_a, mid_b = sorted(rem[1:3])
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _setting_top_hi(hand_ranks: np.ndarray) -> int:
    """top=highest, mid=next-two-highest by rank (canonical default)."""
    order = sorted(range(7), key=lambda j: (-int(hand_ranks[j]), j))
    top_pos = order[0]
    mid_a, mid_b = sorted(order[1:3])
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _setting_top_2nd(hand_ranks: np.ndarray) -> int:
    """top=2nd-highest, mid=highest+3rd-highest (split-the-high-card)."""
    order = sorted(range(7), key=lambda j: (-int(hand_ranks[j]), j))
    top_pos = order[1]
    mid_a, mid_b = sorted([order[0], order[2]])
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _setting_top_lo(hand_ranks: np.ndarray) -> int:
    """top=lowest, mid=2 highest by rank (counter-test: dump weakest)."""
    order = sorted(range(7), key=lambda j: (-int(hand_ranks[j]), j))
    top_pos = order[6]
    mid_a, mid_b = sorted(order[0:2])
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _hi_pos(hand_ranks: np.ndarray) -> int:
    return int(sorted(range(7), key=lambda j: (-int(hand_ranks[j]), j))[0])


def _2nd_pos(hand_ranks: np.ndarray) -> int:
    return int(sorted(range(7), key=lambda j: (-int(hand_ranks[j]), j))[1])


def _lo_pos(hand_ranks: np.ndarray) -> int:
    return int(sorted(range(7), key=lambda j: (-int(hand_ranks[j]), j))[6])


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, randomly subsample N hands per stratum for quick run")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 43: weak-hand HIGH-CARD-DEFENSE drill (Q1, Q2, Q5)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading canonical hands + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    high_only_idx = np.where(cats == 0)[0]
    print(f"  total high_only hands: {len(high_only_idx):,}")
    n_total = len(ch.hands)

    # Identify stratum + per-hand max_r/second_r by walking high_only_idx
    print("\n[2/4] stratifying by max-card / weak-body ...", flush=True)
    t0 = time.time()
    strata: dict[str, list[int]] = defaultdict(list)
    max_r_arr = np.zeros(len(high_only_idx), dtype=np.int8)
    second_r_arr = np.zeros(len(high_only_idx), dtype=np.int8)
    for i, cid in enumerate(high_only_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        sr = sorted(int(r) for r in ranks)
        max_r = sr[-1]; second_r = sr[-2]
        max_r_arr[i] = max_r; second_r_arr[i] = second_r
        s = stratum_for(max_r, second_r)
        if s is not None:
            strata[s].append(i)
    full_stratum_sizes = {k: len(v) for k, v in strata.items()}
    print(f"  done in {time.time()-t0:.1f}s. Strata sizes:")
    for k in sorted(strata.keys()):
        share = len(strata[k]) / n_total * 100
        print(f"    {k:>14}  {len(strata[k]):>7,}  ({share:.3f}% of grid)")

    if args.sample > 0:
        rng = np.random.default_rng(args.seed)
        for k, lst in list(strata.items()):
            if len(lst) > args.sample:
                strata[k] = sorted(rng.choice(lst, size=args.sample,
                                               replace=False).tolist())
        print(f"\n  [sample mode: capped each stratum at {args.sample}]")

    print("\n[3/4] loading oracle grids (full N=200 + prefix N=1000) ...",
          flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    # Aggregate metrics: per-stratum lists of (regret_full, regret_pref) per
    # candidate setting, plus oracle restrictions and v39 baseline.
    candidates = ["v39", "A_TOP_HI", "B_BOT_FLUSH", "B_BOT_3FLUSH_EXT",
                  "C_TOP_2ND", "D_TOP_LO",
                  "OC_TOP_HI", "OC_TOP_2ND", "OC_TOP_LO", "OC_OVERALL"]
    full_reg = {k: defaultdict(list) for k in candidates}
    pref_reg = {k: defaultdict(list) for k in candidates}
    # Worst-case regret per candidate per stratum: track max
    full_worst = {k: defaultdict(float) for k in candidates}
    pref_worst = {k: defaultdict(float) for k in candidates}
    # Counts of "n applicable" for B_BOT_FLUSH / B_BOT_3FLUSH_EXT
    n_b_flush = defaultdict(int)
    n_b_3flush = defaultdict(int)
    n_pref_hands = defaultdict(int)

    print("\n[4/4] per-hand candidate evaluation ...", flush=True)
    t0 = time.time()
    total_to_process = sum(len(v) for v in strata.values())
    processed = 0
    for stratum, idxs in strata.items():
        for i in idxs:
            cid = int(high_only_idx[i])
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            ranks = (h // 4) + 2
            suits = h & 0b11

            top_hi = _setting_top_hi(ranks)
            top_2nd = _setting_top_2nd(ranks)
            top_lo = _setting_top_lo(ranks)
            bot_flush = _bot_flush_setting(ranks, suits)
            bot_3flush = _bot_3flush_extended_setting(ranks, suits)
            v39_pick = int(strategy_v39_rule9(h))
            hi_pos = _hi_pos(ranks)
            second_pos = _2nd_pos(ranks)
            lo_pos = _lo_pos(ranks)

            rowf = np.asarray(gf.evs[cid], dtype=np.float64)
            ev_oracle_full = float(rowf.max())

            picks_full = {
                "v39": float(rowf[v39_pick]),
                "A_TOP_HI": float(rowf[top_hi]),
                "B_BOT_FLUSH": float(rowf[bot_flush]) if bot_flush is not None else None,
                "B_BOT_3FLUSH_EXT": float(rowf[bot_3flush]) if bot_3flush is not None else None,
                "C_TOP_2ND": float(rowf[top_2nd]),
                "D_TOP_LO": float(rowf[top_lo]),
                "OC_TOP_HI": float(rowf[_settings_with_top_at(hi_pos)].max()),
                "OC_TOP_2ND": float(rowf[_settings_with_top_at(second_pos)].max()),
                "OC_TOP_LO": float(rowf[_settings_with_top_at(lo_pos)].max()),
                "OC_OVERALL": ev_oracle_full,
            }
            for cand, ev in picks_full.items():
                if ev is None:
                    continue
                reg = ev_oracle_full - ev
                full_reg[cand][stratum].append(reg)
                if reg > full_worst[cand][stratum]:
                    full_worst[cand][stratum] = reg

            if bot_flush is not None:
                n_b_flush[stratum] += 1
            if bot_3flush is not None:
                n_b_3flush[stratum] += 1

            if cid < 500_000:
                rowp = np.asarray(gp.evs[cid], dtype=np.float64)
                ev_oracle_pref = float(rowp.max())
                picks_pref = {
                    "v39": float(rowp[v39_pick]),
                    "A_TOP_HI": float(rowp[top_hi]),
                    "B_BOT_FLUSH": float(rowp[bot_flush]) if bot_flush is not None else None,
                    "B_BOT_3FLUSH_EXT": float(rowp[bot_3flush]) if bot_3flush is not None else None,
                    "C_TOP_2ND": float(rowp[top_2nd]),
                    "D_TOP_LO": float(rowp[top_lo]),
                    "OC_TOP_HI": float(rowp[_settings_with_top_at(hi_pos)].max()),
                    "OC_TOP_2ND": float(rowp[_settings_with_top_at(second_pos)].max()),
                    "OC_TOP_LO": float(rowp[_settings_with_top_at(lo_pos)].max()),
                    "OC_OVERALL": ev_oracle_pref,
                }
                for cand, ev in picks_pref.items():
                    if ev is None:
                        continue
                    reg = ev_oracle_pref - ev
                    pref_reg[cand][stratum].append(reg)
                    if reg > pref_worst[cand][stratum]:
                        pref_worst[cand][stratum] = reg
                n_pref_hands[stratum] += 1
            processed += 1
            if processed % 20000 == 0:
                rate = processed / (time.time() - t0)
                print(f"    progress {processed:>7,}/{total_to_process:,}  "
                      f"rate={rate:.0f}/s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n", flush=True)

    # Reporting.
    print("=" * 88)
    print("RESULTS — mean regret ($/hand-stratum) and worst-case regret")
    print("=" * 88)
    print("Note: $-figures are within-stratum mean regret * $10. Whole-grid"
          " contribution = within-stratum * $10 * 1000 * stratum_share.")
    print()
    for stratum in sorted(strata.keys()):
        n = len(strata[stratum])
        # Use FULL stratum size for whole-grid extrapolation, regardless of sample mode.
        full_n = full_stratum_sizes[stratum]
        share = full_n / n_total
        n_pref = n_pref_hands[stratum]
        # pref_share uses sampled prefix-applicable count scaled to full
        # stratum density; sample mode preserves prefix-density approximately.
        share_pref = (n_pref / n) * (full_n / 500_000) if n > 0 and n_pref > 0 else 0.0
        print(f"\n── {stratum}  (n_full={full_n:,}, sampled={n:,}, "
              f"share={share*100:.3f}%; n_pref_sampled={n_pref:,}) ──")
        if n_b_flush[stratum] > 0 or n_b_3flush[stratum] > 0:
            print(f"   B_BOT_FLUSH applicable: {n_b_flush[stratum]:>5,} / {n:,} "
                  f"({100*n_b_flush[stratum]/n:.1f}%)")
            print(f"   B_BOT_3FLUSH_EXT applicable: {n_b_3flush[stratum]:>5,} / {n:,} "
                  f"({100*n_b_3flush[stratum]/n:.1f}%)")
        print(f"   {'candidate':<22} {'mean_reg_full':>14} {'worst_full':>11}  "
              f"{'mean_reg_pref':>14} {'worst_pref':>11}  Δ_vs_v39 (whole-grid)")
        v39_full_mean = (np.mean(full_reg["v39"][stratum])
                         if full_reg["v39"][stratum] else 0.0)
        v39_pref_mean = (np.mean(pref_reg["v39"][stratum])
                         if pref_reg["v39"][stratum] else float('nan'))
        for cand in candidates:
            f_lst = full_reg[cand][stratum]
            p_lst = pref_reg[cand][stratum]
            f_mean = np.mean(f_lst) if f_lst else float('nan')
            p_mean = np.mean(p_lst) if p_lst else float('nan')
            f_worst = full_worst[cand][stratum]
            p_worst = pref_worst[cand][stratum]
            n_f = len(f_lst); n_p = len(p_lst)
            n_f_str = f"({n_f:,})" if n_f != n else ""
            applicable_share_full = (n_f / n) if n else 0.0
            applicable_share_pref = (n_p / n_pref) if n_pref else 0.0
            f_delta_whole = ((v39_full_mean - f_mean) * EV_TO_DOL * 1000
                              * share * applicable_share_full)
            p_delta_whole = ((v39_pref_mean - p_mean) * EV_TO_DOL * 1000
                              * share_pref * applicable_share_pref)
            print(f"   {cand:<22} ${f_mean*EV_TO_DOL*1000:>+11.1f} {n_f_str:<3} "
                  f"${f_worst*EV_TO_DOL:>+9.2f}  "
                  f"${p_mean*EV_TO_DOL*1000:>+11.1f}    "
                  f"${p_worst*EV_TO_DOL:>+9.2f}  "
                  f"full ${f_delta_whole:>+7.2f}  pref ${p_delta_whole:>+7.2f}")

    # Aggregate "top-position" classification
    print("\n" + "=" * 88)
    print("ORACLE TOP-POSITION DISTRIBUTION")
    print("=" * 88)
    print("Of the OC_OVERALL pick per hand, what fraction has top=highest vs"
          " top=2nd vs top=lower?")
    for stratum in sorted(strata.keys()):
        idxs = strata[stratum]
        n = len(idxs)
        c_hi = c_2nd = c_lo = c_3rd = c_other = 0
        for i in idxs:
            cid = int(high_only_idx[i])
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            ranks = (h // 4) + 2
            order = sorted(range(7), key=lambda j: (-int(ranks[j]), j))
            rowf = np.asarray(gf.evs[cid], dtype=np.float64)
            best = int(rowf.argmax())
            top_pos = best // 15
            if top_pos == order[0]: c_hi += 1
            elif top_pos == order[1]: c_2nd += 1
            elif top_pos == order[2]: c_3rd += 1
            elif top_pos == order[6]: c_lo += 1
            else: c_other += 1
        print(f"  {stratum:>14}: top=hi {100*c_hi/n:>5.1f}% | "
              f"top=2nd {100*c_2nd/n:>5.1f}% | top=3rd {100*c_3rd/n:>5.1f}% | "
              f"top=lo {100*c_lo/n:>5.1f}% | other {100*c_other/n:>5.1f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
