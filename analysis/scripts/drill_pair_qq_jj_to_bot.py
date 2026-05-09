"""
Session 42 deep-dive — pair QQ/JJ-to-bot Rule 1 extension drill.

Findings from `drill_pair_rule1_extension.py`:
  - QQ has $2,833/1000h within-cat v33 loss with 50/50 oracle split
    between mid=P_pair vs unpaired_mid
  - JJ has $2,541/1000h with 51/49 split
  - Other pair ranks have skewed distributions (mid=P_pair dominant)

Hypothesis: an extension to Rule 1 — "if QQ or JJ has 2 distinct suits AND
balanced kickers AND DS-bot is constructible, move pair to bot" — could
capture significant value.

This drill walks the QQ + JJ subsets specifically. For each hand:
  - Compute v37 baseline EV (pair stays in mid via v33's default)
  - Compute "pair-to-bot" EVs across various structural arrangements:
    * top = highest singleton, mid = 2 kickers, bot = pair + 2 kickers
    * top = highest singleton, mid = 2 kickers, bot = pair + 2 kickers (DS-aware)
    * various suit-aware mid/bot picks
  - Test gates: any pair-suit combo, balanced kickers, etc.

Goal: find a deterministic gate-and-pick that wins on BOTH full + prefix.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_pair_qq_jj_to_bot.py
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
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
from tw_analysis.oracle_grid import read_oracle_grid  # noqa: E402
from tw_analysis.query import setting_features_from_bytes  # noqa: E402
from strategy_v9_pair_to_bot_ds import _setting_index_from_tmb  # noqa: E402
from strategy_v37_rule7_three_pair import strategy_v37_rule7_three_pair  # noqa: E402

GRID_FULL = ROOT / "data" / "oracle_grid_full_realistic_n200.bin"
GRID_PREFIX = ROOT / "data" / "oracle_grid_prefix500k_n1000.bin"
CANON = ROOT / "data" / "canonical_hands.bin"
FT_PATH = ROOT / "data" / "feature_table.parquet"
EV_TO_DOL = 10.0


def main() -> int:
    print("=" * 80)
    print("Session 42 deep-dive: pair QQ/JJ-to-bot Rule 1 extension")
    print("=" * 80)
    print(f"Started: {time.strftime('%Y-%m-%d %H:%M:%S')}", flush=True)

    print("\n[1/4] loading pair mask + grids ...", flush=True)
    ft = pd.read_parquet(FT_PATH, columns=["n_pairs", "n_trips", "n_quads", "pair_high_rank"])
    mask = ((ft["n_pairs"].to_numpy() == 1)
            & (ft["n_trips"].to_numpy() == 0)
            & (ft["n_quads"].to_numpy() == 0))
    pair_high = ft["pair_high_rank"].to_numpy()
    # Only QQ (12) and JJ (11)
    target_mask = mask & ((pair_high == 12) | (pair_high == 11))
    pair_idx = np.where(target_mask)[0]
    n_target = len(pair_idx)
    pop_share_full = n_target / len(ft)
    print(f"  QQ + JJ pair hands: {n_target:,} ({100*pop_share_full:.4f}%)")

    ch = read_canonical_hands(CANON, mode="memmap")
    gf = read_oracle_grid(GRID_FULL, mode="memmap")
    gp = read_oracle_grid(GRID_PREFIX, mode="memmap")

    in_pref = pair_idx < 500_000
    pop_share_pref = int(in_pref.sum()) / 500_000

    # For each hand, compute multiple structural EVs:
    # M0: v37 default pick (pair stays in mid usually)
    # M1: top=hi-sing, mid=pair, bot=4 kickers (default-pair-mid)
    # M2: top=hi-sing, mid=2 kickers (suit-aware), bot=pair+2 kickers (pair-to-bot DS-aware)
    # M3: top=hi-sing, mid=2 kickers (suit-non-pair), bot=pair+2 kickers
    print(f"\n[2/4] enumerating structural EVs for {n_target:,} hands ...",
          flush=True)
    full_v37 = np.zeros(n_target)
    full_oracle = np.zeros(n_target)
    full_M2_oc = np.zeros(n_target)  # pair-to-bot oracle within: best top × mid choice
    full_M2_det = np.zeros(n_target)  # pair-to-bot deterministic: kickers split by pair-suit
    pref_v37 = np.full(n_target, np.nan)
    pref_oracle = np.full(n_target, np.nan)
    pref_M2_det = np.full(n_target, np.nan)

    P_arr = np.zeros(n_target, dtype=np.int8)
    pair_diff_suits_arr = np.zeros(n_target, dtype=bool)
    has_ace_arr = np.zeros(n_target, dtype=bool)
    kicker_suit_balance = np.zeros(n_target, dtype=np.int8)  # 0=balanced, 1=lopsided

    t0 = time.time()
    last_log = time.time()
    for i, cid in enumerate(pair_idx):
        h = np.asarray(ch.hands[int(cid)], dtype=np.uint8).copy()
        ranks = (h // 4) + 2
        suits = h & 0b11
        rc = np.bincount(ranks, minlength=15)
        P = next(r for r in range(2, 15) if rc[r] == 2)
        sings = sorted([r for r in range(2, 15) if rc[r] == 1], reverse=True)
        P_arr[i] = P
        has_ace_arr[i] = any(r == 14 for r in sings)
        pos_P = sorted(j for j in range(7) if int(ranks[j]) == P)
        pair_suit_a = int(suits[pos_P[0]])
        pair_suit_b = int(suits[pos_P[1]])
        pair_diff_suits_arr[i] = pair_suit_a != pair_suit_b
        pos_sings = [next(j for j in range(7) if int(ranks[j]) == r)
                     for r in sings]
        pos_shi = pos_sings[0]
        # Count kickers by pair-suit match
        n_at_a = sum(1 for j in pos_sings if int(suits[j]) == pair_suit_a)
        n_at_b = sum(1 for j in pos_sings if int(suits[j]) == pair_suit_b)
        # "Balanced" = (1,1), (2,2), (1,3), (3,1)
        if pair_diff_suits_arr[i] and {n_at_a, n_at_b} & {1, 2, 3} and n_at_a + n_at_b >= 2:
            balanced = (n_at_a >= 1 and n_at_b >= 1
                        and not (n_at_a == 2 and n_at_b == 1)
                        and not (n_at_a == 1 and n_at_b == 2))
        else:
            balanced = False
        kicker_suit_balance[i] = 0 if balanced else 1

        rowf = np.asarray(gf.evs[int(cid)], dtype=np.float64)
        full_v37[i] = rowf[int(strategy_v37_rule7_three_pair(h))]
        full_oracle[i] = rowf.max()

        # M2 deterministic: pair-to-bot
        # Top = highest singleton. Bot = pair + lowest 2 kickers matching
        # pair-suits if possible, else canonical 2 lowest. Mid = remaining 2 kickers.
        if pair_diff_suits_arr[i]:
            # Find lowest kicker matching each pair-suit
            kickers_a = sorted([j for j in pos_sings
                                if int(suits[j]) == pair_suit_a],
                               key=lambda j: int(ranks[j]))
            kickers_b = sorted([j for j in pos_sings
                                if int(suits[j]) == pair_suit_b],
                               key=lambda j: int(ranks[j]))
            if kickers_a and kickers_b:
                kicker_a = kickers_a[0]  # lowest at suit_a
                kicker_b = kickers_b[0]
            else:
                # Fallback: pick 2 lowest kickers
                low_kickers = sorted(pos_sings, key=lambda j: int(ranks[j]))[:2]
                kicker_a, kicker_b = low_kickers[0], low_kickers[1]
        else:
            # Pair has same suit (rare); fallback
            low_kickers = sorted(pos_sings, key=lambda j: int(ranks[j]))[:2]
            kicker_a, kicker_b = low_kickers[0], low_kickers[1]

        # The 2 mid kickers = 2 of remaining 2 kickers
        bot_set = {pos_P[0], pos_P[1], kicker_a, kicker_b}
        mid_kickers = sorted(j for j in pos_sings if j not in bot_set)
        if len(mid_kickers) >= 2:
            mid_a, mid_b = mid_kickers[0], mid_kickers[1]
        else:
            # Skip this hand (malformed)
            full_M2_det[i] = full_v37[i]  # neutral
            full_M2_oc[i] = full_v37[i]
            continue
        m2_setting = _setting_index_from_tmb(pos_shi, mid_a, mid_b)
        full_M2_det[i] = rowf[m2_setting]

        # M2 oracle: best within "pair-to-bot, top=any-sing" subspace
        m2_best = -np.inf
        for top_pos in pos_sings:
            for ka in pos_sings:
                for kb in pos_sings:
                    if ka >= kb or ka == top_pos or kb == top_pos:
                        continue
                    # Bot must contain pair + ka + kb (so ka,kb are in bot)
                    # Actually mid choice = the other 2 sings (not top, not in bot)
                    other_sings = [j for j in pos_sings
                                   if j not in (top_pos, ka, kb)]
                    if len(other_sings) != 2:
                        continue
                    mid_a_, mid_b_ = sorted(other_sings)
                    s = _setting_index_from_tmb(top_pos, mid_a_, mid_b_)
                    m2_best = max(m2_best, float(rowf[s]))
        full_M2_oc[i] = m2_best

        if cid < 500_000:
            rowp = np.asarray(gp.evs[int(cid)], dtype=np.float64)
            pref_v37[i] = rowp[int(strategy_v37_rule7_three_pair(h))]
            pref_oracle[i] = rowp.max()
            pref_M2_det[i] = rowp[m2_setting]

        if time.time() - last_log > 10:
            rate = (i + 1) / (time.time() - t0)
            print(f"    progress {i+1:>6,}/{n_target:,}  rate={rate:.0f}/s",
                  flush=True)
            last_log = time.time()
    print(f"  done in {time.time()-t0:.0f}s")

    full_v37_reg = full_oracle - full_v37
    pref_v37_reg = pref_oracle[in_pref] - pref_v37[in_pref]

    print(f"\n[3/4] HEADLINES")
    print(f"  v37 baseline regret on QQ+JJ: full ${full_v37_reg.mean()*EV_TO_DOL*1000:+.1f}/1000h "
          f"({full_v37_reg.mean()*EV_TO_DOL*1000*pop_share_full:+.2f} whole-grid)")

    def _row(name, picked_full, picked_pref=None, kind="det"):
        full_reg = full_oracle - picked_full
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        s = f"  {name:<60}  full ${full_delta:>+8.2f}/1000h"
        if picked_pref is not None:
            pref_reg = pref_oracle[in_pref] - picked_pref[in_pref]
            pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
            s += f"  pref ${pref_delta:>+8.2f}/1000h"
        s += f"  [{kind}]"
        print(s)

    _row("v37 baseline (no Rule 1 extension)", full_v37, pref_v37, "actual")
    print(f"  {'─'*100}")
    _row("M2 deterministic always (pair-to-bot)", full_M2_det, pref_M2_det)
    _row("M2 oracle within (best top + mid)", full_M2_oc, kind="oracle")

    # Gated variants — only fire when conditions met
    print(f"\n  Gated rule variants:")

    def evaluate_gated(gate_fn, picked_full, picked_pref, label):
        """Apply rule only when gate_fn(i) is True; else use v37."""
        gated_full = np.where([gate_fn(i) for i in range(n_target)],
                              picked_full, full_v37)
        gated_pref = np.where([gate_fn(i) for i in range(n_target)],
                              picked_pref, pref_v37)
        full_reg = full_oracle - gated_full
        full_delta = (full_v37_reg.mean() - full_reg.mean()) * EV_TO_DOL * 1000 * pop_share_full
        pref_reg = pref_oracle[in_pref] - gated_pref[in_pref]
        pref_delta = (pref_v37_reg.mean() - pref_reg.mean()) * EV_TO_DOL * 1000 * pop_share_pref
        marker = "★" if (full_delta > 0 and pref_delta > 0) else ""
        gate_share = sum(1 for i in range(n_target) if gate_fn(i)) / n_target
        print(f"  {label:<60}  full ${full_delta:>+8.2f}  pref ${pref_delta:>+8.2f}  "
              f"fires {100*gate_share:.0f}%  {marker}")

    # Various gates
    evaluate_gated(lambda i: True, full_M2_det, pref_M2_det,
                   "always M2 (always fire pair-to-bot)")
    evaluate_gated(lambda i: pair_diff_suits_arr[i],
                   full_M2_det, pref_M2_det,
                   "M2 if pair has 2 distinct suits")
    evaluate_gated(lambda i: pair_diff_suits_arr[i] and kicker_suit_balance[i] == 0,
                   full_M2_det, pref_M2_det,
                   "M2 if pair-suits-distinct AND balanced kickers")
    evaluate_gated(lambda i: pair_diff_suits_arr[i] and kicker_suit_balance[i] == 0 and has_ace_arr[i],
                   full_M2_det, pref_M2_det,
                   "M2 if pair-suits-distinct AND balanced AND has-Ace (Rule 1)")
    evaluate_gated(lambda i: pair_diff_suits_arr[i] and kicker_suit_balance[i] == 0 and not has_ace_arr[i],
                   full_M2_det, pref_M2_det,
                   "M2 if pair-suits-distinct AND balanced AND NO-Ace (extension)")

    # Per-pair-rank breakdown
    print(f"\n[4/4] Per-pair-rank breakdown:")
    print(f"  {'P':>2}  {'n':>6}  {'v37$':>10}  {'M2_det$':>10}  {'M2_oc$':>10}")
    for P in [12, 11]:
        mask_P = (P_arr == P)
        n = int(mask_P.sum())
        v37_m = full_v37_reg[mask_P].mean()
        m2_det_m = (full_oracle[mask_P] - full_M2_det[mask_P]).mean()
        m2_oc_m = (full_oracle[mask_P] - full_M2_oc[mask_P]).mean()
        print(f"  {'Q' if P==12 else 'J':>2}  {n:>6,}  ${v37_m*EV_TO_DOL*1000:>+8.1f}  "
              f"${m2_det_m*EV_TO_DOL*1000:>+8.1f}  ${m2_oc_m*EV_TO_DOL*1000:>+8.1f}")

    print(f"\nFinished: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
