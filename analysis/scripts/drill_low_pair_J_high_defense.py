"""
Session 43 — weak-hand DEFENSIVE drill, J-high single-pair zone (Q3).

Population: category=pair (exactly one pair, no trip/quad), max card = J-or-lower.

Per docs/SESSION_43_WEAK_HAND_DEFENSE.md, this is the BIGGEST sub-territory of
the defensive zone:
  - 342,720 hands (40.4% of the J-or-lower defensive zone)
  - skews very low: pair=2 is 34.27%, pair=J is 5.14%

User's Q3 framing (verbatim): "the pair is too weak to anchor a strong mid;
the high card is too weak to scoop. is there a 'minimize damage' structural
pick?"

Sub-stratify by pair-rank within {2..J}, then test candidate settings:

  v39        production fallthrough (Rules 1-9 don't fire on most of these →
             v3 via v8_hybrid)
  A_PAIR_MID      top=hi-singleton, mid=pair, bot=4 lower singletons (the
                  CONVENTIONAL pick — pair anchors mid Hold'em)
  B_PAIR_BOT      top=hi-singleton, mid=2 mid-rank singletons, bot=pair+2
                  lower singletons (pair-to-bot for Omaha 2-pair anchor)
  C_TOP_LO       top=lowest-singleton, mid=pair, bot=4 highest non-pair
                  (defensive: dump weakest top, keep pair anchored mid,
                  stack bot)
  D_TOP_PAIR_M   top=one of pair (split pair), mid=2 highest singletons,
                  bot=other-pair-member + 3 lower singletons (split pair)

  OC_OVERALL  best of all 105
  OC_TOP_HI   oracle restricted to top=hi-singleton
  OC_TOP_LO   oracle restricted to top=lo-singleton
  OC_TOP_PAIR oracle restricted to top=a pair-member (split-pair class)
  OC_PAIR_MID oracle restricted to mid=pair
  OC_PAIR_BOT oracle restricted to mid != pair AND bot contains both pair
              members (mid is unpaired)

Validate on full grid (N=200) AND prefix grid (N=1000). Prefix coverage of
J-high pair is HEALTHY (~10% of prefix is J-high; ~43% of prefix is pair).

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_low_pair_J_high_defense.py
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_low_pair_J_high_defense.py --sample 5000
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


def _sing_pos_sorted(ranks: np.ndarray, pair_rank: int) -> list[int]:
    """Return positions of the 5 non-pair singletons, sorted by rank desc."""
    return sorted([j for j in range(7) if int(ranks[j]) != pair_rank],
                  key=lambda j: (-int(ranks[j]), j))


def _pair_pos(ranks: np.ndarray, pair_rank: int) -> list[int]:
    return sorted(j for j in range(7) if int(ranks[j]) == pair_rank)


def _setting_pair_mid(ranks: np.ndarray, pair_rank: int) -> int:
    """Top=hi-sing, mid=pair, bot=4 lower singletons. Conventional pick."""
    sings = _sing_pos_sorted(ranks, pair_rank)
    pps = _pair_pos(ranks, pair_rank)
    top_pos = sings[0]
    mid_a, mid_b = sorted(pps)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _setting_pair_bot(ranks: np.ndarray, pair_rank: int) -> int:
    """Top=hi-sing, mid=2 mid-rank singletons (s2+s3), bot=pair + s4 + s5."""
    sings = _sing_pos_sorted(ranks, pair_rank)
    top_pos = sings[0]
    mid_a, mid_b = sorted([sings[1], sings[2]])
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _setting_top_lo_pair_mid(ranks: np.ndarray, pair_rank: int) -> int:
    """Top=lowest-sing, mid=pair, bot=4 highest non-pair singletons.
    Defensive: dump weakest, keep pair as mid anchor."""
    sings = _sing_pos_sorted(ranks, pair_rank)
    pps = _pair_pos(ranks, pair_rank)
    top_pos = sings[-1]  # lowest singleton
    mid_a, mid_b = sorted(pps)
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _setting_top_pair_split(ranks: np.ndarray, pair_rank: int) -> int:
    """Top=one of pair, mid=2 highest singletons, bot=remaining (1 pair + 3
    singletons)."""
    sings = _sing_pos_sorted(ranks, pair_rank)
    pps = _pair_pos(ranks, pair_rank)
    top_pos = pps[0]
    mid_a, mid_b = sorted([sings[0], sings[1]])
    return int(_setting_index_from_tmb(top_pos, mid_a, mid_b))


def _settings_with_top_at(top_pos: int) -> list[int]:
    return list(range(top_pos * 15, top_pos * 15 + 15))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--sample", type=int, default=0,
                    help="If >0, randomly subsample N hands per pair-rank cell")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    print("=" * 88)
    print("Session 43: J-high LOW-PAIR DEFENSIVE drill (Q3)")
    print("=" * 88)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading canonical hands + categorizing ...", flush=True)
    ch = read_canonical_hands(CANON, mode="memmap")
    cats = categorize_hands(np.asarray(ch.hands[:]))
    pair_idx = np.where(cats == 1)[0]
    n_total = len(ch.hands)
    print(f"  total pair hands: {len(pair_idx):,}")

    print("\n[2/4] filtering to J-high (max rank <= 11) ...", flush=True)
    t0 = time.time()
    qualifying = []
    pair_rank_arr = []
    max_r_arr = []
    for cid in pair_idx:
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8)
        ranks = (h // 4) + 2
        rc = np.bincount(ranks, minlength=15)
        P = next(r for r in range(2, 15) if rc[r] == 2)
        max_r = int(ranks.max())
        if max_r > 11:
            continue
        qualifying.append(int(cid))
        pair_rank_arr.append(P)
        max_r_arr.append(max_r)
    qualifying = np.asarray(qualifying, dtype=np.int64)
    pair_rank_arr = np.asarray(pair_rank_arr, dtype=np.int8)
    max_r_arr = np.asarray(max_r_arr, dtype=np.int8)
    print(f"  J-high pair: {len(qualifying):,}  ({100*len(qualifying)/n_total:.3f}%)")
    print(f"  done in {time.time()-t0:.1f}s")

    # Stratify by (max_r, pair_rank)
    cells = defaultdict(list)
    for i, (mr, pr) in enumerate(zip(max_r_arr, pair_rank_arr)):
        cells[(int(mr), int(pr))].append(i)

    # Optional sampling per cell
    if args.sample > 0:
        rng = np.random.default_rng(args.seed)
        sampled = []
        for k, lst in cells.items():
            if len(lst) > args.sample:
                cells[k] = sorted(rng.choice(lst, size=args.sample,
                                              replace=False).tolist())
            sampled.extend(cells[k])
        sampled_set = set(sampled)
        print(f"  [sample mode: capped each cell at {args.sample}; "
              f"total={len(sampled):,} hands processed]")
    else:
        sampled_set = set(range(len(qualifying)))

    full_cell_sizes = {k: sum(1 for _ in v) for k, v in cells.items()}

    print("\n[3/4] loading oracle grids ...", flush=True)
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")
    print("  ready.")

    candidates = ["v39", "A_PAIR_MID", "B_PAIR_BOT", "C_TOP_LO_PMID",
                  "D_TOP_PAIR_SPLIT",
                  "OC_TOP_HI", "OC_TOP_LO", "OC_TOP_PAIR",
                  "OC_PAIR_MID", "OC_PAIR_BOT", "OC_OVERALL"]
    full_reg = {k: defaultdict(list) for k in candidates}
    pref_reg = {k: defaultdict(list) for k in candidates}
    full_worst = {k: defaultdict(float) for k in candidates}
    pref_worst = {k: defaultdict(float) for k in candidates}
    n_pref_hands = defaultdict(int)
    # Top-position counter (oracle pick)
    top_pos_counter = defaultdict(lambda: defaultdict(int))
    # Mid-kind counter (P_pair / unpaired)
    mid_kind_counter = defaultdict(lambda: defaultdict(int))

    print("\n[4/4] per-hand candidate evaluation ...", flush=True)
    t0 = time.time()
    total_to_process = sum(len(v) for v in cells.values())
    processed = 0

    for cell_key, idx_list in cells.items():
        max_r, P = cell_key
        for i in idx_list:
            cid = int(qualifying[i])
            h = np.asarray(ch.hands[cid], dtype=np.uint8)
            ranks = (h // 4) + 2

            sings = _sing_pos_sorted(ranks, P)
            pps = _pair_pos(ranks, P)
            hi_pos = sings[0]
            lo_pos = sings[-1]

            v39_pick = int(strategy_v39_rule9(h))
            pmid = _setting_pair_mid(ranks, P)
            pbot = _setting_pair_bot(ranks, P)
            tlo_pmid = _setting_top_lo_pair_mid(ranks, P)
            tpair = _setting_top_pair_split(ranks, P)

            rowf = np.asarray(gf.evs[cid], dtype=np.float64)
            ev_oc_full = float(rowf.max())

            # Oracle restricted to top=hi-sing
            oc_hi = float(rowf[_settings_with_top_at(hi_pos)].max())
            oc_lo = float(rowf[_settings_with_top_at(lo_pos)].max())
            # top=pair: try both pair-member positions
            oc_pair = max(float(rowf[_settings_with_top_at(p)].max()) for p in pps)

            # Vectorized per-setting features for this hand.
            feats = setting_features_from_bytes(h)
            mid_is_pair = feats.mid_is_pair
            mid_pair_rank = feats.mid_pair_rank
            bot_pair_rank = feats.bot_pair_rank

            pair_mid_mask = mid_is_pair & (mid_pair_rank == P)
            oc_pair_mid = (float(rowf[pair_mid_mask].max())
                            if pair_mid_mask.any() else float('-inf'))

            # OC_PAIR_BOT mask: top is NOT a pair member AND mid is NOT P-pair
            # AND bot contains the P-pair (bot_pair_rank == P).
            # Top is at setting_idx // 15; positions in pps are pair members.
            top_indices = np.arange(105) // 15
            top_is_pair_member = np.isin(top_indices, np.asarray(pps))
            pair_bot_mask = (~top_is_pair_member) & (~pair_mid_mask) & (bot_pair_rank == P)
            ev_pair_bot_best = (float(rowf[pair_bot_mask].max())
                                  if pair_bot_mask.any() else float('-inf'))

            picks_full = {
                "v39": float(rowf[v39_pick]),
                "A_PAIR_MID": float(rowf[pmid]),
                "B_PAIR_BOT": float(rowf[pbot]),
                "C_TOP_LO_PMID": float(rowf[tlo_pmid]),
                "D_TOP_PAIR_SPLIT": float(rowf[tpair]),
                "OC_TOP_HI": oc_hi,
                "OC_TOP_LO": oc_lo,
                "OC_TOP_PAIR": oc_pair,
                "OC_PAIR_MID": oc_pair_mid,
                "OC_PAIR_BOT": ev_pair_bot_best,
                "OC_OVERALL": ev_oc_full,
            }

            for cand, ev in picks_full.items():
                if ev == float('-inf'):
                    continue
                reg = ev_oc_full - ev
                full_reg[cand][cell_key].append(reg)
                if reg > full_worst[cand][cell_key]:
                    full_worst[cand][cell_key] = reg

            # Top-pos / mid-kind classification of oracle pick
            oc_pick = int(np.argmax(rowf))
            oc_top_idx = oc_pick // 15
            if oc_top_idx in pps:
                top_pos_counter[cell_key]["pair_member"] += 1
            elif oc_top_idx == hi_pos:
                top_pos_counter[cell_key]["hi_sing"] += 1
            elif oc_top_idx == lo_pos:
                top_pos_counter[cell_key]["lo_sing"] += 1
            elif oc_top_idx == sings[1]:
                top_pos_counter[cell_key]["s2_sing"] += 1
            elif oc_top_idx == sings[2]:
                top_pos_counter[cell_key]["s3_sing"] += 1
            else:
                top_pos_counter[cell_key]["other_sing"] += 1
            if pair_mid_mask[oc_pick]:
                mid_kind_counter[cell_key]["pair_in_mid"] += 1
            elif bool(pair_bot_mask[oc_pick]):
                mid_kind_counter[cell_key]["pair_in_bot"] += 1
            else:
                mid_kind_counter[cell_key]["pair_split"] += 1

            if cid < 500_000:
                rowp = np.asarray(gp.evs[cid], dtype=np.float64)
                ev_oc_pref = float(rowp.max())
                # Re-pick within prefix's EVs, oracle selectors recomputed.
                p_oc_hi = float(rowp[_settings_with_top_at(hi_pos)].max())
                p_oc_lo = float(rowp[_settings_with_top_at(lo_pos)].max())
                p_oc_pair = max(float(rowp[_settings_with_top_at(p)].max()) for p in pps)
                p_oc_pmid = (float(rowp[pair_mid_mask].max())
                              if pair_mid_mask.any() else float('-inf'))
                # Vectorized OC_PAIR_BOT on prefix using the same structural mask.
                p_pbot_best = (float(rowp[pair_bot_mask].max())
                                if pair_bot_mask.any() else float('-inf'))

                picks_pref = {
                    "v39": float(rowp[v39_pick]),
                    "A_PAIR_MID": float(rowp[pmid]),
                    "B_PAIR_BOT": float(rowp[pbot]),
                    "C_TOP_LO_PMID": float(rowp[tlo_pmid]),
                    "D_TOP_PAIR_SPLIT": float(rowp[tpair]),
                    "OC_TOP_HI": p_oc_hi,
                    "OC_TOP_LO": p_oc_lo,
                    "OC_TOP_PAIR": p_oc_pair,
                    "OC_PAIR_MID": p_oc_pmid,
                    "OC_PAIR_BOT": p_pbot_best,
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

    # ── Reporting ──
    print("=" * 100)
    print("RESULTS — per (max_r, pair_rank) cell, mean regret per candidate "
          "($/1000h within-cell)")
    print("=" * 100)
    # Aggregate first by pair-rank (since J-high is dominant max_r)
    cell_keys = sorted(cells.keys())
    print()
    for cell_key in cell_keys:
        max_r, P = cell_key
        n = len(cells[cell_key])
        full_n = full_cell_sizes[cell_key]
        share = full_n / n_total
        n_pref = n_pref_hands[cell_key]
        print(f"\n── max={RANK_CHAR[max_r]}-high, pair={RANK_CHAR[P]}  "
              f"(n_full={full_n:,}, sampled={n:,}, share={share*100:.4f}%; "
              f"n_pref_sampled={n_pref:,}) ──")
        v39_full_mean = (np.mean(full_reg["v39"][cell_key])
                         if full_reg["v39"][cell_key] else 0.0)
        v39_pref_mean = (np.mean(pref_reg["v39"][cell_key])
                         if pref_reg["v39"][cell_key] else float('nan'))
        print(f"   {'cand':<22} {'mean_reg_full':>14}  {'worst_f':>9}  "
              f"{'mean_reg_pref':>14}  {'worst_p':>9}  Δ_v39 (whole-grid)")
        for cand in candidates:
            f_lst = full_reg[cand][cell_key]
            p_lst = pref_reg[cand][cell_key]
            f_mean = np.mean(f_lst) if f_lst else float('nan')
            p_mean = np.mean(p_lst) if p_lst else float('nan')
            f_worst = full_worst[cand][cell_key]
            p_worst = pref_worst[cand][cell_key]
            f_delta_whole = ((v39_full_mean - f_mean) * EV_TO_DOL * 1000 * share)
            # prefix share = full_n / 500K (only counts the prefix-applicable subset)
            pref_share = (n_pref / n) * (full_n / 500_000) if n > 0 and n_pref > 0 else 0.0
            p_delta_whole = ((v39_pref_mean - p_mean) * EV_TO_DOL * 1000 * pref_share)
            print(f"   {cand:<22} ${f_mean*EV_TO_DOL*1000:>+11.1f}  "
                  f"${f_worst*EV_TO_DOL:>+7.2f}  "
                  f"${p_mean*EV_TO_DOL*1000:>+11.1f}   "
                  f"${p_worst*EV_TO_DOL:>+7.2f}  "
                  f"f${f_delta_whole:>+7.2f}  p${p_delta_whole:>+7.2f}")

    # ── Aggregated across pair-rank within max_r ──
    print("\n" + "=" * 100)
    print("AGGREGATED across pair-rank (within max=J-high)")
    print("=" * 100)
    # Build a flat aggregation by candidate
    print("Mean regret aggregated weighted by cell size:")
    print(f"   {'cand':<22} {'mean_reg_full':>14}  {'mean_reg_pref':>14}  "
          f"Δ_v39_full  Δ_v39_pref")
    agg_full = {}
    agg_pref = {}
    total_full_cnt = sum(len(v) for v in cells.values())
    total_pref_cnt = sum(n_pref_hands.values())
    total_full_share = sum(full_cell_sizes[k] for k in cells.keys()) / n_total
    for cand in candidates:
        all_full = []
        all_pref = []
        for cell_key in cells.keys():
            all_full.extend(full_reg[cand][cell_key])
            all_pref.extend(pref_reg[cand][cell_key])
        f_mean = np.mean(all_full) if all_full else float('nan')
        p_mean = np.mean(all_pref) if all_pref else float('nan')
        agg_full[cand] = f_mean
        agg_pref[cand] = p_mean
    v39_f = agg_full["v39"]; v39_p = agg_pref["v39"]
    for cand in candidates:
        f_delta = (v39_f - agg_full[cand]) * EV_TO_DOL * 1000 * total_full_share
        # prefix share: total_pref_cnt / total_full_cnt scales sample coverage
        # to full pop size; full pop in prefix = sum(full_cell_sizes) but only
        # those <500K. We approximate via observed prefix density.
        if total_pref_cnt > 0 and total_full_cnt > 0:
            pref_density = total_pref_cnt / total_full_cnt
            pref_share = pref_density * (sum(full_cell_sizes[k] for k in cells.keys()) / 500_000)
        else:
            pref_share = 0.0
        p_delta = (v39_p - agg_pref[cand]) * EV_TO_DOL * 1000 * pref_share
        print(f"   {cand:<22} ${agg_full[cand]*EV_TO_DOL*1000:>+11.1f}  "
              f"${agg_pref[cand]*EV_TO_DOL*1000:>+11.1f}  "
              f"f${f_delta:>+7.2f}  p${p_delta:>+7.2f}")

    # ── Oracle top-pos and mid-kind distribution per cell ──
    print("\n" + "=" * 100)
    print("ORACLE TOP-POSITION + MID-KIND DISTRIBUTION (oracle pick per cell)")
    print("=" * 100)
    print(f"{'cell':<17}  top: hi_sing | s2 | s3 | lo_sing | other | pair_member  "
          f"|  mid: in_mid | in_bot | split")
    for cell_key in cell_keys:
        max_r, P = cell_key
        ctr = top_pos_counter[cell_key]
        n = sum(ctr.values())
        if n == 0:
            continue
        mctr = mid_kind_counter[cell_key]
        mn = sum(mctr.values())
        label = f"{RANK_CHAR[max_r]}h_p{RANK_CHAR[P]}"
        print(f"{label:<17}  "
              f"{100*ctr.get('hi_sing',0)/n:>5.1f}% | "
              f"{100*ctr.get('s2_sing',0)/n:>4.1f}% | "
              f"{100*ctr.get('s3_sing',0)/n:>4.1f}% | "
              f"{100*ctr.get('lo_sing',0)/n:>5.1f}% | "
              f"{100*ctr.get('other_sing',0)/n:>5.1f}% | "
              f"{100*ctr.get('pair_member',0)/n:>5.1f}%   |  "
              f"{100*mctr.get('pair_in_mid',0)/mn:>5.1f}% | "
              f"{100*mctr.get('pair_in_bot',0)/mn:>5.1f}% | "
              f"{100*mctr.get('pair_split',0)/mn:>5.1f}%")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
