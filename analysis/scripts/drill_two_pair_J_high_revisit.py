"""
Session 43 — J-high two_pair DEFENSIVE re-examination (Q4).

Population: category=two_pair, max card <= J. 262,080 hands (4.36% of grid).

This is the SAME population where Session 42 morning's deferred Rule 8
candidate broke (+$197 full / -$512 prefix). The user's hypothesis: maybe
v33's adaptive splitting on weak two-pair hands was correct DEFENSIVE play
that I dismissed as "ML-only" without inspecting the defensive lens.

Per-hand candidate settings (singletons s1>s2>s3, pairs pair_H>pair_L):

  v39       production fallthrough
  RA        top=s1, mid=H-pair, bot=L-pair+s2+s3      (HIGH pair → mid)
  RB        top=s1, mid=L-pair, bot=H-pair+s2+s3      (HIGH pair → bot)
  RC        top=s1, mid=s2+s3, bot=H-pair+L-pair      (double-pair-bot)
  RA_TOP_LO top=s3, mid=H-pair, bot=L-pair+s1+s2      (defensive RA)
  RC_TOP_LO top=s3, mid=s1+s2, bot=H-pair+L-pair      (defensive RC)
  F_SPLIT   top=s1, mid=H_member+L_member, bot=other_H+other_L+s2+s3
            (split-pair mid)

Oracles:
  OC_OVERALL
  OC_TOP_HI / OC_TOP_LO / OC_TOP_S2 / OC_TOP_PAIR
  OC_PAIR_BOT_DOUBLE  (mid unpaired AND bot contains both H+L pairs)
  OC_PAIR_MID_H       (mid is paired by H-pair-rank)
  OC_PAIR_MID_L       (mid is paired by L-pair-rank)
  OC_SPLIT_MID        (mid has 1 H-pair-member + 1 L-pair-member, unpaired)

Stratify by (max_r, pair_H, pair_L). Validate on full grid (N=200) AND
prefix grid (N=1000). Report mean regret + worst-case regret per candidate.

Methodology: per Session 43 framing, "minimize loss". Worst-case
regret (avoid the 20-pt scoop) is reported in addition to mean.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_J_high_revisit.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_J_high_revisit.py --sample 200
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
from tw_analysis.query import setting_features_from_bytes  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v39_rule9 import strategy_v39_rule9  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
EV_TO_DOL = 10.0
RANK_CHAR = {2:"2",3:"3",4:"4",5:"5",6:"6",7:"7",8:"8",9:"9",
             10:"T",11:"J",12:"Q",13:"K",14:"A"}


def _settings_with_top_at(top_pos: int) -> list[int]:
    return list(range(top_pos * 15, top_pos * 15 + 15))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0)
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 43: J-high TWO_PAIR DEFENSIVE re-examination (Q4)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    tp_idx = np.where(cats == 2)[0]
    n_total = len(ch.hands)
    print(f"  total two_pair hands: {len(tp_idx):,}")

    print("\n[2/4] filtering to J-high (max <= 11) + extracting features ...",
          flush=True)
    t0 = time.time()
    qualifying = []
    pair_h_arr = []
    pair_l_arr = []
    max_r_arr = []
    for cid in tp_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        prs = sorted([r for r in range(2, 15) if rc[r] == 2], reverse=True)
        H, L = prs
        max_r = int(ranks.max())
        if max_r > 11:
            continue
        qualifying.append(int(cid))
        pair_h_arr.append(H)
        pair_l_arr.append(L)
        max_r_arr.append(max_r)
    qualifying = np.asarray(qualifying, dtype=np.int64)
    pair_h_arr = np.asarray(pair_h_arr, dtype=np.int8)
    pair_l_arr = np.asarray(pair_l_arr, dtype=np.int8)
    max_r_arr = np.asarray(max_r_arr, dtype=np.int8)
    print(f"  J-high two_pair: {len(qualifying):,}  "
          f"({100*len(qualifying)/n_total:.3f}%)")
    print(f"  done in {time.time()-t0:.1f}s")

    cells = defaultdict(list)
    for i, (mr, ph, pl) in enumerate(zip(max_r_arr, pair_h_arr, pair_l_arr)):
        cells[(int(mr), int(ph), int(pl))].append(i)

    full_cell_sizes = {k: len(v) for k, v in cells.items()}

    if args.sample > 0:
        rng = np.random.default_rng(args.seed)
        for k, lst in list(cells.items()):
            if len(lst) > args.sample:
                cells[k] = sorted(rng.choice(lst, size=args.sample,
                                              replace=False).tolist())
        total_proc = sum(len(v) for v in cells.values())
        print(f"  [sample mode: capped each cell at {args.sample}; "
              f"total={total_proc:,}]")

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    candidates = ["v39", "RA", "RB", "RC", "RA_TOP_LO", "RC_TOP_LO", "F_SPLIT",
                  "OC_TOP_HI", "OC_TOP_LO", "OC_TOP_S2", "OC_TOP_PAIR",
                  "OC_PAIR_BOT_DOUBLE", "OC_PAIR_MID_H", "OC_PAIR_MID_L",
                  "OC_SPLIT_MID", "OC_OVERALL"]
    full_reg = {k: defaultdict(list) for k in candidates}
    pref_reg = {k: defaultdict(list) for k in candidates}
    full_worst = {k: defaultdict(float) for k in candidates}
    pref_worst = {k: defaultdict(float) for k in candidates}
    n_pref_hands = defaultdict(int)
    top_pos_counter = defaultdict(lambda: defaultdict(int))
    mid_kind_counter = defaultdict(lambda: defaultdict(int))

    print("\n[4/4] per-hand candidate evaluation ...", flush=True)
    t0 = time.time()
    total_to_process = sum(len(v) for v in cells.values())
    processed = 0

    for cell_key, idx_list in cells.items():
        max_r, H, L = cell_key
        for i in idx_list:
            cid = int(qualifying[i])
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            ranks = (h // 4) + 2

            pos_H = sorted(j for j in range(7) if int(ranks[j]) == H)
            pos_L = sorted(j for j in range(7) if int(ranks[j]) == L)
            sings = sorted([j for j in range(7) if int(ranks[j]) not in (H, L)],
                            key=lambda j: (-int(ranks[j]), j))
            assert len(sings) == 3
            s1, s2, s3 = sings

            v39_pick = int(strategy_v39_rule9(h))
            ra = int(_setting_index_from_tmb(s1, pos_H[0], pos_H[1]))
            rb = int(_setting_index_from_tmb(s1, pos_L[0], pos_L[1]))
            rc = int(_setting_index_from_tmb(s1, s2, s3))
            ra_lo = int(_setting_index_from_tmb(s3, pos_H[0], pos_H[1]))
            rc_lo = int(_setting_index_from_tmb(s3, s1, s2))
            f_split = int(_setting_index_from_tmb(s1, pos_H[0], pos_L[0]))

            rowf = np.asarray(gf.evs[cid], dtype=np.float64)
            ev_oc_full = float(rowf.max())

            feats = setting_features_from_bytes(h)
            mid_is_pair = feats.mid_is_pair
            mid_pair_rank = feats.mid_pair_rank
            bot_pair_rank = feats.bot_pair_rank
            top_indices = np.arange(105) // 15

            top_is_H = np.isin(top_indices, np.asarray(pos_H))
            top_is_L = np.isin(top_indices, np.asarray(pos_L))
            top_is_pair = top_is_H | top_is_L

            mid_is_H_pair = mid_is_pair & (mid_pair_rank == H)
            mid_is_L_pair = mid_is_pair & (mid_pair_rank == L)

            # OC_PAIR_BOT_DOUBLE: top NOT pair member, mid NOT paired,
            # bot has BOTH pair-ranks.
            # Both pair-ranks in bot iff: top not in pos_H AND top not in pos_L
            # AND mid is not H_pair AND mid is not L_pair AND
            # AND not all H-pair-members in top|mid (need at least one in bot)
            # Simplest: bot has both ranks → bot_pair_rank == H AND
            # bot also contains an L card. Use: top NOT pair AND mid NOT
            # paired AND mid does NOT contain any L card AND mid does NOT
            # contain any H card.
            # Alternative: a setting is "double-pair-bot" iff top is a singleton
            # AND mid is 2 singletons (ie mid_is_pair False AND mid does not
            # contain a pair member). The mid "contains a pair member" detector
            # is harder vectorized — use: bot_pair_rank == H AND mid_is_pair
            # is False AND top is a singleton-position.
            top_is_sing = ~top_is_pair
            # mid contains an H-pair-member iff: bot has only 1 H card.
            # Easier: count_H_in_bot = bot_pair_rank flags.
            # bot_pair_rank == H means bot has BOTH H cards (since H is unique).
            # Similarly bot_pair_rank can also be L if L is highest rank in bot.
            # bot_pair_rank is the HIGHEST paired rank in bot — if both H and L
            # are in bot, bot_pair_rank reports H (highest).
            # For "double-pair-bot" we need both H AND L in bot. Need a separate
            # check for L-in-bot. Use: mid_pair_rank != L AND mid_is_pair False
            # AND top NOT in pos_L AND bot has L pair → derive by counting.
            # Simpler: build mask by enumerating valid settings (105 is cheap).
            # Build double_pair_bot_mask via direct iteration over settings.
            # ...implement using numpy without enumeration:
            # bot_has_L_pair = same as bot_pair_rank for L iff H is not in bot.
            # If H NOT in bot at all (i.e., both H in top|mid), bot_pair_rank
            # would be L if L pair is in bot.
            # So:
            # bot_has_H_pair = (bot_pair_rank == H)
            # bot_has_L_pair = (bot_pair_rank == L) | (
            #   bot_has_H_pair & (mid_pair_rank != L) & (~top_is_L) &
            #   (mid contains both L cards if bot_pair_rank == H))
            # Skip clever vectorization; iterate 105 once per hand.
            double_pair_bot_mask = np.zeros(105, dtype=bool)
            split_mid_mask = np.zeros(105, dtype=bool)
            for s in range(105):
                top_idx = s // 15
                if top_idx in pos_H or top_idx in pos_L:
                    # Skip — top is pair member
                    continue
                # Determine mid + bot positions.
                mid_a, mid_b = ((s % 15) // (5*1), (s % 15) % (5*1))
                # decode mid combo properly from setting index using same logic
                # as decode_setting:
                top_i = top_idx
                mid_combo_i = s - top_idx * 15
                # Map mid_combo_i (0..14) to (a, b) in 0..5
                a_local, b_local = _MID_PAIRS[mid_combo_i]
                remaining = [j for j in range(7) if j != top_i]
                mid_pos_a = remaining[a_local]
                mid_pos_b = remaining[b_local]
                bot_positions = [j for j in remaining
                                  if j != mid_pos_a and j != mid_pos_b]
                # Is mid a pair (same rank)? If yes, skip (we want unpaired mid).
                mid_ranks_pair = (int(ranks[mid_pos_a]) == int(ranks[mid_pos_b]))
                if mid_ranks_pair:
                    continue
                # Does bot contain both H pair-members AND both L pair-members?
                bot_ranks_int = [int(ranks[j]) for j in bot_positions]
                if bot_ranks_int.count(H) == 2 and bot_ranks_int.count(L) == 2:
                    double_pair_bot_mask[s] = True
                # Is mid one H_member + one L_member (split mid)?
                mid_ranks_int = (int(ranks[mid_pos_a]), int(ranks[mid_pos_b]))
                if (H in mid_ranks_int) and (L in mid_ranks_int):
                    split_mid_mask[s] = True

            oc_pair_bot_double = (float(rowf[double_pair_bot_mask].max())
                                   if double_pair_bot_mask.any() else float('-inf'))
            oc_pair_mid_h = (float(rowf[mid_is_H_pair].max())
                              if mid_is_H_pair.any() else float('-inf'))
            oc_pair_mid_l = (float(rowf[mid_is_L_pair].max())
                              if mid_is_L_pair.any() else float('-inf'))
            oc_split_mid = (float(rowf[split_mid_mask].max())
                             if split_mid_mask.any() else float('-inf'))

            # Top-class oracles
            oc_top_hi = float(rowf[_settings_with_top_at(s1)].max())
            oc_top_lo = float(rowf[_settings_with_top_at(s3)].max())
            oc_top_s2 = float(rowf[_settings_with_top_at(s2)].max())
            oc_top_pair = max(float(rowf[_settings_with_top_at(p)].max())
                              for p in (pos_H[0], pos_H[1], pos_L[0], pos_L[1]))

            picks_full = {
                "v39": float(rowf[v39_pick]),
                "RA": float(rowf[ra]),
                "RB": float(rowf[rb]),
                "RC": float(rowf[rc]),
                "RA_TOP_LO": float(rowf[ra_lo]),
                "RC_TOP_LO": float(rowf[rc_lo]),
                "F_SPLIT": float(rowf[f_split]),
                "OC_TOP_HI": oc_top_hi,
                "OC_TOP_LO": oc_top_lo,
                "OC_TOP_S2": oc_top_s2,
                "OC_TOP_PAIR": oc_top_pair,
                "OC_PAIR_BOT_DOUBLE": oc_pair_bot_double,
                "OC_PAIR_MID_H": oc_pair_mid_h,
                "OC_PAIR_MID_L": oc_pair_mid_l,
                "OC_SPLIT_MID": oc_split_mid,
                "OC_OVERALL": ev_oc_full,
            }
            for cand, ev in picks_full.items():
                if ev == float('-inf'):
                    continue
                reg = ev_oc_full - ev
                full_reg[cand][cell_key].append(reg)
                if reg > full_worst[cand][cell_key]:
                    full_worst[cand][cell_key] = reg

            oc_pick = int(np.argmax(rowf))
            oc_top_idx = oc_pick // 15
            if oc_top_idx in (pos_H[0], pos_H[1], pos_L[0], pos_L[1]):
                top_pos_counter[cell_key]["pair_member"] += 1
            elif oc_top_idx == s1:
                top_pos_counter[cell_key]["s1_top"] += 1
            elif oc_top_idx == s2:
                top_pos_counter[cell_key]["s2_top"] += 1
            elif oc_top_idx == s3:
                top_pos_counter[cell_key]["s3_top"] += 1
            else:
                top_pos_counter[cell_key]["other"] += 1
            if mid_is_H_pair[oc_pick]:
                mid_kind_counter[cell_key]["mid_H_pair"] += 1
            elif mid_is_L_pair[oc_pick]:
                mid_kind_counter[cell_key]["mid_L_pair"] += 1
            elif split_mid_mask[oc_pick]:
                mid_kind_counter[cell_key]["mid_split"] += 1
            elif double_pair_bot_mask[oc_pick]:
                mid_kind_counter[cell_key]["double_pair_bot"] += 1
            else:
                mid_kind_counter[cell_key]["other"] += 1

            if cid < 500_000:
                rowp = np.asarray(gp.evs[cid], dtype=np.float64)
                ev_oc_pref = float(rowp.max())
                p_oc_top_hi = float(rowp[_settings_with_top_at(s1)].max())
                p_oc_top_lo = float(rowp[_settings_with_top_at(s3)].max())
                p_oc_top_s2 = float(rowp[_settings_with_top_at(s2)].max())
                p_oc_top_pair = max(float(rowp[_settings_with_top_at(p)].max())
                                     for p in (pos_H[0], pos_H[1], pos_L[0], pos_L[1]))
                p_oc_pbd = (float(rowp[double_pair_bot_mask].max())
                              if double_pair_bot_mask.any() else float('-inf'))
                p_oc_pmh = (float(rowp[mid_is_H_pair].max())
                              if mid_is_H_pair.any() else float('-inf'))
                p_oc_pml = (float(rowp[mid_is_L_pair].max())
                              if mid_is_L_pair.any() else float('-inf'))
                p_oc_split = (float(rowp[split_mid_mask].max())
                                if split_mid_mask.any() else float('-inf'))

                picks_pref = {
                    "v39": float(rowp[v39_pick]),
                    "RA": float(rowp[ra]),
                    "RB": float(rowp[rb]),
                    "RC": float(rowp[rc]),
                    "RA_TOP_LO": float(rowp[ra_lo]),
                    "RC_TOP_LO": float(rowp[rc_lo]),
                    "F_SPLIT": float(rowp[f_split]),
                    "OC_TOP_HI": p_oc_top_hi,
                    "OC_TOP_LO": p_oc_top_lo,
                    "OC_TOP_S2": p_oc_top_s2,
                    "OC_TOP_PAIR": p_oc_top_pair,
                    "OC_PAIR_BOT_DOUBLE": p_oc_pbd,
                    "OC_PAIR_MID_H": p_oc_pmh,
                    "OC_PAIR_MID_L": p_oc_pml,
                    "OC_SPLIT_MID": p_oc_split,
                    "OC_OVERALL": ev_oc_pref,
                }
                for cand, ev in picks_pref.items():
                    if ev == float('-inf'):
                        continue
                    reg = ev_oc_pref - ev
                    pref_reg[cand][cell_key].append(reg)
                    if reg > pref_worst[cand][cell_key]:
                        pref_worst[cand][cell_key] = reg
                n_pref_hands[cell_key] += 1

            processed += 1
            if processed % 5000 == 0:
                rate = processed / (time.time() - t0)
                print(f"    progress {processed:>7,}/{total_to_process:,}  "
                      f"rate={rate:.0f}/s", flush=True)
    print(f"  done in {time.time()-t0:.1f}s.\n", flush=True)

    # Reporting.
    print("=" * 100)
    print("AGGREGATED across pair-rank pairs (all J-high two_pair)")
    print("=" * 100)
    agg_full = {}
    agg_pref = {}
    total_full_cnt = sum(len(v) for v in cells.values())
    total_pref_cnt = sum(n_pref_hands.values())
    pop_in_grid = sum(full_cell_sizes[k] for k in cells.keys())
    total_full_share = pop_in_grid / n_total
    for cand in candidates:
        all_full = []
        all_pref = []
        for cell_key in cells.keys():
            all_full.extend(full_reg[cand][cell_key])
            all_pref.extend(pref_reg[cand][cell_key])
        agg_full[cand] = np.mean(all_full) if all_full else float('nan')
        agg_pref[cand] = np.mean(all_pref) if all_pref else float('nan')
    v39_f = agg_full["v39"]; v39_p = agg_pref["v39"]
    pref_density = total_pref_cnt / total_full_cnt if total_full_cnt > 0 else 0.0
    pref_share = pref_density * (pop_in_grid / 500_000)
    print(f"   {'cand':<22} {'mean_reg_full':>14}  {'mean_reg_pref':>14}  "
          f"Δ_v39_full  Δ_v39_pref")
    for cand in candidates:
        f_delta = (v39_f - agg_full[cand]) * EV_TO_DOL * 1000 * total_full_share
        p_delta = (v39_p - agg_pref[cand]) * EV_TO_DOL * 1000 * pref_share
        print(f"   {cand:<22} ${agg_full[cand]*EV_TO_DOL*1000:>+11.1f}  "
              f"${agg_pref[cand]*EV_TO_DOL*1000:>+11.1f}  "
              f"f${f_delta:>+7.2f}  p${p_delta:>+7.2f}")

    print("\n" + "=" * 100)
    print("PER-CELL: best deterministic candidate by mean regret + Δ vs v39")
    print("=" * 100)
    print(f"{'cell':<14}  {'n_full':>7}  {'best_cand':<14} {'best_full$':>11} "
          f"{'best_pref$':>11}  {'Δfull':>9} {'Δpref':>9}")
    det_cands = ["RA", "RB", "RC", "RA_TOP_LO", "RC_TOP_LO", "F_SPLIT"]
    cell_keys_sorted = sorted(cells.keys())
    for cell_key in cell_keys_sorted:
        max_r, H, L = cell_key
        v39_full = (np.mean(full_reg["v39"][cell_key])
                     if full_reg["v39"][cell_key] else 0.0)
        v39_pref = (np.mean(pref_reg["v39"][cell_key])
                     if pref_reg["v39"][cell_key] else float('nan'))
        best_cand = None
        best_full_mean = float('inf')
        for cand in det_cands:
            if not full_reg[cand][cell_key]: continue
            m = np.mean(full_reg[cand][cell_key])
            if m < best_full_mean:
                best_full_mean = m
                best_cand = cand
        if best_cand is None:
            continue
        best_pref_mean = (np.mean(pref_reg[best_cand][cell_key])
                          if pref_reg[best_cand][cell_key] else float('nan'))
        f_n = full_cell_sizes[cell_key]
        share = f_n / n_total
        n_pref = n_pref_hands[cell_key]
        n = len(cells[cell_key])
        pref_share_cell = (n_pref / n) * (f_n / 500_000) if n > 0 else 0.0
        d_full = (v39_full - best_full_mean) * EV_TO_DOL * 1000 * share
        d_pref = (v39_pref - best_pref_mean) * EV_TO_DOL * 1000 * pref_share_cell
        cell_label = f"{RANK_CHAR[max_r]}h_p{RANK_CHAR[H]}{RANK_CHAR[L]}"
        print(f"{cell_label:<14}  {f_n:>7,}  {best_cand:<14} "
              f"${best_full_mean*EV_TO_DOL*1000:>+10.1f} "
              f"${best_pref_mean*EV_TO_DOL*1000:>+10.1f}  "
              f"f${d_full:>+7.2f}  p${d_pref:>+7.2f}")

    print("\n" + "=" * 100)
    print("ORACLE TOP-POSITION + MID-KIND DISTRIBUTION (oracle pick per cell)")
    print("=" * 100)
    print(f"{'cell':<14}  top: s1 | s2 | s3 | pair | other  |  "
          f"mid: H_pair | L_pair | split | dpb | other")
    for cell_key in cell_keys_sorted:
        max_r, H, L = cell_key
        ctr = top_pos_counter[cell_key]
        n = sum(ctr.values())
        if n == 0:
            continue
        mctr = mid_kind_counter[cell_key]
        mn = sum(mctr.values())
        cell_label = f"{RANK_CHAR[max_r]}h_p{RANK_CHAR[H]}{RANK_CHAR[L]}"
        print(f"{cell_label:<14}  "
              f"{100*ctr.get('s1_top',0)/n:>5.1f}% | "
              f"{100*ctr.get('s2_top',0)/n:>4.1f}% | "
              f"{100*ctr.get('s3_top',0)/n:>4.1f}% | "
              f"{100*ctr.get('pair_member',0)/n:>5.1f}% | "
              f"{100*ctr.get('other',0)/n:>5.1f}%   |  "
              f"{100*mctr.get('mid_H_pair',0)/mn:>5.1f}% | "
              f"{100*mctr.get('mid_L_pair',0)/mn:>5.1f}% | "
              f"{100*mctr.get('mid_split',0)/mn:>5.1f}% | "
              f"{100*mctr.get('double_pair_bot',0)/mn:>5.1f}% | "
              f"{100*mctr.get('other',0)/mn:>5.1f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


# Mid-pair table (same as engine: a in 0..5, b in (a+1)..5; 15 pairs).
_MID_PAIRS = tuple((a, b) for a in range(6) for b in range(a + 1, 6))
assert len(_MID_PAIRS) == 15


if __name__ == "__main__":
    sys.exit(main())
