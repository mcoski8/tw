"""
Session 58 — high_only_aug_v4_gated: 4 rank-valued features for the
high_only zone, targeting structural axes invisible to v43 (DS bot
strength inside DS_NO_JOINT cell, 4-flush + ms route at top=max,
non-max-top joint achievability + quality).

Drill HO5–HO9 surfaced THREE structural axes v43 cannot split on:

  AXIS A — DS bot pair_high quality with top=max.
    Drill HO7 (DS_NO_JOINT cell at max=A): oracle picks DS bot 52% vs
    v43's 42% (-10% under-routing). v43 has DS-achievability counts
    (ho_v2_*_g) but no signal for DS BOT QUALITY. The DT cannot
    differentiate "weak DS bot (low suited pairs)" from "strong DS bot
    (Q/K-suited pair)" — so it stays on SS_mu defensively. Top mismatch
    @ A: tA_SS_mu → tA_DS_mu ($25/1000h, n=34,726).

  AXIS B — 4-flush bot + suited mid with top=max.
    Drill HO8: at max=A, 54% of "alt-when-joint-avail" are tmax_4f_ms.
    v43 has no feature for this route — it sees 4f bot as universally
    bad. But for a high-mid-high suited pair, 4-flush is the dominant
    alt route. Top mismatch class includes tA_DS_ms → tA_4f_ms ($0.31).

  AXIS C — non-max-top joint achievability.
    Drill HO10: 47.7% of high_only hands have a (top!=max, DS bot, ms
    mid) joint config achievable. v43's ho_v3 features ONLY count
    joints with top=max — non-max-top joints are completely invisible.
    HO9: at max=Q/J/T/9/8, oracle's DS_NONJOINT take-rate (which
    includes non-max-top joints) is 48-65%, dominating every other
    pick category at lower max-ranks.

The 4 new features (each gated to high_only category — zero outside):

  ho_v4_topMax_DS_max_bot_pair_high_g  0..13 — across all (top=max,
    bot 2+2 DS) configs, max higher-of-suited-pair across both suited
    pairs in the bot. 0 if no such config. Captures DS bot strength.

  ho_v4_topMax_4f_ms_max_mid_high_g    0..13 — across all (top=max,
    bot 4-flush, mid suited) configs, the best higher-of-suited-mid
    pair rank. 0 if no such config. Captures the Ace-top 4f route
    quality.

  ho_v4_topNonMax_DS_ms_n_configs_g    0..30 — count of (top!=max,
    bot 2+2 DS, mid 2 cards suited) configs where max-rank ends up in
    the bot or mid. The "max-into-bot" route population.

  ho_v4_topNonMax_DS_ms_max_top_rank_g 0..13 — best non-max top rank
    achievable in any non-max-top joint. Tells DT how strong the
    alternative top can be. 0 if no non-max joint exists.

All zeros for non-high_only hands (n_pairs > 0 or n_trips > 0 or
n_quads > 0).
"""
from __future__ import annotations

import sys
import time
from collections import Counter, defaultdict
from itertools import combinations
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)


def compute_high_only_v4_features_for_hand(hand: np.ndarray
                                             ) -> tuple[int, int, int, int]:
    """Return (max_DS_bot_pair_high, max_4f_ms_mid_high,
                n_nonmax_joint, max_nonmax_joint_top_rank)."""
    if hand.shape[0] != 7:
        return (0, 0, 0, 0)
    ranks = (hand // 4) + 2
    suits = hand % 4
    int_ranks = [int(r) for r in ranks]
    int_suits = [int(s) for s in suits]
    rank_count: Counter[int] = Counter(int_ranks)
    n_pairs = sum(1 for c in rank_count.values() if c == 2)
    n_trips = sum(1 for c in rank_count.values() if c == 3)
    n_quads = sum(1 for c in rank_count.values() if c == 4)
    if n_pairs != 0 or n_trips != 0 or n_quads != 0:
        return (0, 0, 0, 0)

    max_rank = max(int_ranks)
    max_pos = int_ranks.index(max_rank)

    max_DS_bot_pair_high = 0
    max_4f_ms_mid_high = 0
    n_nonmax_joint = 0
    max_nonmax_joint_top_rank = 0

    # Enumerate all 105 settings: top in {0..6}, mid_pair in C(remaining, 2)
    for top_pos in range(7):
        rest = [i for i in range(7) if i != top_pos]
        top_rank = int_ranks[top_pos]
        for mid_a, mid_b in combinations(rest, 2):
            bot_pos = [i for i in rest if i != mid_a and i != mid_b]
            bs = [int_suits[i] for i in bot_pos]
            br = [int_ranks[i] for i in bot_pos]
            cnt = sorted(Counter(bs).values(), reverse=True)
            mid_suits_match = int_suits[mid_a] == int_suits[mid_b]

            if cnt == [2, 2]:  # DS bot
                # bot pair_high (max across both suited pairs)
                by_suit: dict[int, list[int]] = defaultdict(list)
                for r, s in zip(br, bs):
                    by_suit[s].append(r)
                bot_ph = max(max(rs) for rs in by_suit.values() if len(rs) >= 2)

                if top_pos == max_pos:
                    if bot_ph > max_DS_bot_pair_high:
                        max_DS_bot_pair_high = bot_ph
                else:
                    if mid_suits_match:
                        # non-max-top JOINT
                        n_nonmax_joint += 1
                        if top_rank > max_nonmax_joint_top_rank:
                            max_nonmax_joint_top_rank = top_rank
            elif cnt == [4]:  # 4-flush bot
                if top_pos == max_pos and mid_suits_match:
                    mid_high = max(int_ranks[mid_a], int_ranks[mid_b])
                    if mid_high > max_4f_ms_mid_high:
                        max_4f_ms_mid_high = mid_high

    return (max_DS_bot_pair_high, max_4f_ms_mid_high,
            n_nonmax_joint, max_nonmax_joint_top_rank)


def compute_high_only_v4_features_batch(hands: np.ndarray,
                                          log_every: int = 500_000
                                          ) -> dict[str, np.ndarray]:
    N = hands.shape[0]
    out_DS_ph = np.zeros(N, dtype=np.int8)
    out_4f_mh = np.zeros(N, dtype=np.int8)
    out_nm_n = np.zeros(N, dtype=np.int8)
    out_nm_top = np.zeros(N, dtype=np.int8)
    t0 = time.time()
    for i in range(N):
        h = np.asarray(hands[i], dtype=np.uint8)
        v1, v2, v3, v4 = compute_high_only_v4_features_for_hand(h)
        out_DS_ph[i] = v1
        out_4f_mh[i] = v2
        out_nm_n[i] = v3
        out_nm_top[i] = v4
        if (i + 1) % log_every == 0:
            elapsed = time.time() - t0
            rate = (i + 1) / elapsed
            eta = (N - i - 1) / rate
            print(f"  ho_v4 {i+1:>10,}/{N:,}  rate={rate:>5.0f}/s  "
                  f"elapsed {elapsed:>4.0f}s  ETA {eta:>4.0f}s", flush=True)
    return {
        "ho_v4_topMax_DS_max_bot_pair_high_g": out_DS_ph,
        "ho_v4_topMax_4f_ms_max_mid_high_g": out_4f_mh,
        "ho_v4_topNonMax_DS_ms_n_configs_g": out_nm_n,
        "ho_v4_topNonMax_DS_ms_max_top_rank_g": out_nm_top,
    }


if __name__ == "__main__":
    RANK = {"2":2,"3":3,"4":4,"5":5,"6":6,"7":7,"8":8,"9":9,
            "T":10,"J":11,"Q":12,"K":13,"A":14}
    SUIT = {"s":0,"h":1,"d":2,"c":3}
    def hh(*cards):
        return np.array(sorted((RANK[c[0]] - 2) * 4 + SUIT[c[1]] for c in cards),
                          dtype=np.uint8)

    cases = [
        # Hand 1: 2s 5h 6d Jh Qd Ks As (7 distinct ranks, 3 suits 2-2-2 + 1 spare)
        # Suits: s,h,d,h,d,s — wait let me recount: 2s(s),5h(h),6d(d),Jh(h),Qd(d),Ks(s),As(s)
        # Actually As=s — so s={2s,Ks,As}=3, h={5h,Jh}=2, d={6d,Qd}=2, c=0
        # max=A, max_pos=position of As.
        # For top=A, we have 6 leftovers {2s,5h,6d,Jh,Qd,Ks} with suits s=2,h=2,d=2,c=0.
        # DS bots from these 6 cards (2+2 suit profile):
        #   ss+hh = {2s,Ks,5h,Jh}, mid leftover = {6d,Qd} both d → joint DS+ms ✓
        #     bot_pair_high = max(K, J) = K=13
        #   ss+dd = {2s,Ks,6d,Qd}, mid = {5h,Jh} h → joint DS+ms ✓
        #     bot_pair_high = max(K, Q) = K=13
        #   hh+dd = {5h,Jh,6d,Qd}, mid = {2s,Ks} s → joint DS+ms ✓
        #     bot_pair_high = max(J, Q) = Q=12
        # So max_DS_bot_pair_high = 13 (K)
        # 4f bot with top=A: need 4 cards same suit. Suits are s=3,h=2,d=2,c=0. Max single
        #   suit count is 3 (s) — but s only has 3 cards (2s, Ks, plus As is on top). So
        #   among leftovers, only 2 s cards. 4f bot impossible. → max_4f_ms_mid_high = 0.
        # Non-max-top joint: top != A. Try top=2s (s suit, max-rank As goes into bot or mid).
        #   bot 2+2 DS where As is in bot or mid AND mid is suited.
        #   For each top in {2s, 5h, 6d, Jh, Qd, Ks}, enumerate:
        #     This is complex. Let's just check: does any (top!=A, DS bot, ms mid)
        #     exist where As is in bot or mid?
        #   top=Ks (rank 13): leftovers {2s,5h,6d,Jh,Qd,As} — s=2 (2s,As), h=2, d=2.
        #     DS bots: ss+hh = {2s,As,5h,Jh}, mid={6d,Qd} d → joint! top=K=13
        #              ss+dd = {2s,As,6d,Qd}, mid={5h,Jh} h → joint! top=K=13
        #              hh+dd = {5h,Jh,6d,Qd}, mid={2s,As} s → joint! top=K=13
        #   So at least 3 non-max joints with top=K (rank 13).
        #   Also try top=Qd (rank 12), top=Jh (rank 11), etc.
        # I'll just trust the script to compute. Expected: max_DS_bot_pair_high=13,
        # max_4f_ms_mid_high=0, n_nonmax_joint>0, max_nonmax_joint_top_rank=13 (or higher
        # if any other K exists; here K=13 is unique).
        ("2s 5h 6d Jh Qd Ks As",
         "expect (13, 0, >0, 13) — nonmax top can be K"),

        # Pair → all zeros
        ("Ac Ad Kh Qs Js Th 9d", "pair AA: expect (0,0,0,0)"),

        # Trips → all zeros
        ("Ac Ad As Kh Ks 7d 2c", "trips_pair AA: expect (0,0,0,0)"),

        # Hand with 4-flush available + ms mid + top=A:
        # As Ks Qs Js 5s 9h 9d would have a pair. Pick: As Ks Qs Js 5s 9h 7d
        # Wait that has 5 spades. Let's do: As Ks Qs Js 4s 9h 7d → still 5s.
        # 4f bot with top=A: pick top=A, then need bot 4 cards same suit. We have
        # 4 spades (Ks,Qs,Js,4s). Bot = {Ks,Qs,Js,4s}, mid = {9h,7d}. mid suited?
        # 9h and 7d are different suits → mid NOT suited. So no 4f+ms.
        # Try: As Ks Qs Js 4s 9h 7h (3 spades + 2 hearts):
        # Wait: that's As(s)+Ks(s)+Qs(s)+Js(s)+4s(s) = 5 spades. Then 9h, 7h = 2 hearts.
        # 4f bot with top=A and ms mid: top=A, bot=4 spades from {Ks,Qs,Js,4s} = exactly that.
        # Mid = {9h, 7h} both h → ms ✓. Mid_high = 9. → max_4f_ms_mid_high = 9.
        ("As Ks Qs Js 4s 9h 7h",
         "5-spades + 2 hearts, expect 4f_ms_max_mid_high=9"),

        # No DS achievable: rainbow = 1+1+1+1+other
        # As Kd Qh Js 9c 5d 2c — suits c,d,h,s,c,d,c → c=3, d=2, h=1, s=1. Wait counts.
        # As=s, Kd=d, Qh=h, Js=s, 9c=c, 5d=d, 2c=c → s=2 (As,Js), d=2 (Kd,5d), h=1 (Qh), c=2 (9c,2c)
        # 4 of one suit? max is 2. Not 4-flush. DS achievable? need 2 suits with 2 cards:
        # ss+dd = {As,Js,Kd,5d}, ss+cc, dd+cc — yes multiple DS bots.
        # For top=A=As, bot from {Kd,Qh,Js,9c,5d,2c} = 6 cards. Suits: d=2,h=1,s=1,c=2.
        # DS bots: dd+cc = {Kd,5d,9c,2c}, mid={Qh,Js} mu → joint NO (mu)
        # That's the only 2+2 with top=A. bot_pair_high = max(K, 9) = K=13.
        # So max_DS_bot_pair_high=13 with top=A.
        ("As Kd Qh Js 9c 5d 2c",
         "expect DS_max_bot_pair_high=13 (K), 4f=0, nonmax>0"),
    ]
    print("Sanity tests:")
    for cards, desc in cases:
        h = hh(*cards.split())
        v1, v2, v3, v4 = compute_high_only_v4_features_for_hand(h)
        print(f"  {cards:<25} → ({v1}, {v2}, {v3}, {v4})  {desc}")
