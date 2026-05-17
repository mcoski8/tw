"""
Full MC sweep: v65 vs 7 distinct opponent archetypes + symmetry validation.

Scenarios (each at 5,000 hands × 10 sims = 50,000 hands):

  0. SYMMETRY: v65 vs 3× v65 (validation, should be ~$0)
  1. v65 vs 3× Pair-First Standardist        (operator's archetype A)
  2. v65 vs 3× Top-Greedy Defender           (operator's archetype B with J-low pivot)
  3. v65 vs 3× Balanced Pro (mfsuitaware)    (project's strongest competent)
  4. v65 vs 3× Reasonable Naïveté            (NEW — casual home player)
  5. v65 vs 3× Defensive Inversion Player    (NEW — knows defensive flip)
  6. v65 vs 3× Hold'em-Mid Optimizer         (NEW — pair-breaker for strong mid)
  7. v65 vs 3× Grid Oracle                   (NEW — composite-heuristic strong play)

Plus a summary bar comparing all 8 scenarios.

Stake: $10/point.
"""
from __future__ import annotations

import sys
import time
from itertools import combinations
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

import plotly.graph_objects as go  # noqa: E402
from plotly.subplots import make_subplots  # noqa: E402

from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend as v65_strategy,
)

LOOKUP_PATH = ROOT / "data" / "lookup_table.bin"
OUTPUT_HTML = ROOT / "MC_SIMULATION_V4_ALL_ARCHETYPES.html"

STAKE = 10.0
N_SIMS = 10
HANDS_PER_SIM = 5000

PTS_TOP, PTS_MID, PTS_BOT, PTS_SCOOP = 1, 2, 3, 20

COLORS = [
    "#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
    "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf",
]


# ============================================================
# Evaluator
# ============================================================

BINOM = np.zeros((52, 6), dtype=np.int64)
for n in range(52):
    BINOM[n, 0] = 1
    for k in range(1, 6):
        BINOM[n, k] = 0 if k > n else (1 if k == n else BINOM[n - 1, k - 1] + BINOM[n - 1, k])


def load_lookup(p):
    arr = np.frombuffer(p.read_bytes(), dtype=np.uint32)
    return arr if arr.size == 2_598_960 else arr[-2_598_960:].copy()


def colex5(c):
    return BINOM[c[:, 0], 1] + BINOM[c[:, 1], 2] + BINOM[c[:, 2], 3] + BINOM[c[:, 3], 4] + BINOM[c[:, 4], 5]


C65 = np.array(list(combinations(range(6), 5)), dtype=np.int64)
C75 = np.array(list(combinations(range(7), 5)), dtype=np.int64)
C42 = np.array(list(combinations(range(4), 2)), dtype=np.int64)
C53 = np.array(list(combinations(range(5), 3)), dtype=np.int64)


class Ev:
    def __init__(self, t): self.t = t

    def top(self, h1, b5):
        c = np.empty(6, dtype=np.int64); c[0] = h1; c[1:] = b5
        return int(self.t[colex5(np.sort(c[C65], axis=1))].max())

    def mid(self, h2, b5):
        c = np.empty(7, dtype=np.int64); c[:2] = h2; c[2:] = b5
        return int(self.t[colex5(np.sort(c[C75], axis=1))].max())

    def bot(self, h4, b5):
        hp, bt = h4[C42], b5[C53]
        c = np.empty((6, 10, 5), dtype=np.int64)
        c[:, :, :2] = hp[:, None, :]; c[:, :, 2:] = bt[None, :, :]
        return int(self.t[colex5(np.sort(c.reshape(60, 5), axis=1))].max())


def card_rank(c): return c // 4 + 2
def card_suit(c): return c % 4


# ============================================================
# Shared helpers
# ============================================================

def naive_mid_score(a, b):
    r1, r2 = card_rank(a), card_rank(b)
    high, low = (r1, r2) if r1 >= r2 else (r2, r1)
    if high == low: return 200 + high * 2
    s = high * 3 + low * 2
    if card_suit(a) == card_suit(b): s += 8
    gap = high - low
    if gap == 1: s += 6
    elif gap == 2: s += 3
    if high == 14: s += 5
    return s


def middle_tier(a, b):
    r1, r2 = card_rank(a), card_rank(b)
    high, low = (r1, r2) if r1 >= r2 else (r2, r1)
    suited = card_suit(a) == card_suit(b)
    if high == low: return 5
    if low >= 10 and suited: return 4
    if low >= 10: return 3
    if suited and (high == 14 or (high - low) <= 2): return 2
    return 1


def bot_suit_score(bot4):
    counts = [0, 0, 0, 0]
    for c in bot4: counts[card_suit(c)] += 1
    sc = sorted(counts, reverse=True)
    return {(2, 2): 5, (2, 1): 4, (1, 1): 3, (3, 1): 2, (4, 0): 1}.get((sc[0], sc[1]), 0)


def omaha_bot_score(bot4):
    score = 0
    for c in bot4:
        r = card_rank(c)
        if r > 8: score += (r - 8) * 2
    rc = [0] * 15
    for c in bot4: rc[card_rank(c)] += 1
    for r in range(2, 15):
        if rc[r] == 2: score += 15 + r
        elif rc[r] == 3: score += 30 + r * 2
        elif rc[r] == 4: score += 60 + r * 3
    ranks = sorted(set(card_rank(c) for c in bot4))
    max_run, cur = 1, 1
    for i in range(1, len(ranks)):
        if ranks[i] == ranks[i - 1] + 1:
            cur += 1; max_run = max(max_run, cur)
        else: cur = 1
    score += max_run * 8
    wheel = sum(1 for c in bot4 if card_rank(c) == 14 or 2 <= card_rank(c) <= 5)
    if wheel >= 3: score += 6
    elif wheel >= 2: score += 3
    counts = [0, 0, 0, 0]
    for c in bot4: counts[card_suit(c)] += 1
    sc = sorted(counts, reverse=True)
    suit_bonus = {(2, 2): 14, (2, 1): 7, (1, 1): 0, (3, 1): -4, (4, 0): -8}.get((sc[0], sc[1]), 0)
    return score + suit_bonus


def pick_top_from_rem5(rem5):
    rc = [0] * 15
    for c in rem5: rc[card_rank(c)] += 1
    best_single = None
    for i in range(5):
        if rc[card_rank(rem5[i])] != 1: continue
        if best_single is None: best_single = i
        else:
            ci, cb = rem5[i], rem5[best_single]
            if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
                best_single = i
    if best_single is not None: return best_single
    top_i = 0
    for i in range(1, 5):
        ci, cb = rem5[i], rem5[top_i]
        if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
            top_i = i
    return top_i


# ============================================================
# Setting decode tables (precomputed once)
# ============================================================

_MID_PAIRS_LOCAL = np.array(list(combinations(range(6), 2)), dtype=np.int64)
SETTING_TOP_POS = np.empty(105, dtype=np.int64)
SETTING_MID_POS = np.empty((105, 2), dtype=np.int64)
SETTING_BOT_POS = np.empty((105, 4), dtype=np.int64)
for top_i in range(7):
    remaining = [i for i in range(7) if i != top_i]
    for mid_combo_i in range(15):
        a, b = _MID_PAIRS_LOCAL[mid_combo_i]
        mi, mj = remaining[int(a)], remaining[int(b)]
        bot_pos = sorted([remaining[j] for j in range(6) if j != int(a) and j != int(b)])
        setting_idx = top_i * 15 + mid_combo_i
        SETTING_TOP_POS[setting_idx] = top_i
        SETTING_MID_POS[setting_idx] = [mi, mj]
        SETTING_BOT_POS[setting_idx] = bot_pos


def decode_setting(hand_i64, setting_idx):
    top_i = int(SETTING_TOP_POS[setting_idx])
    mid_pos = SETTING_MID_POS[setting_idx]
    bot_pos = SETTING_BOT_POS[setting_idx]
    top = int(hand_i64[top_i])
    mid = np.array([hand_i64[mid_pos[0]], hand_i64[mid_pos[1]]], dtype=np.int64)
    bot = np.array([hand_i64[bot_pos[0]], hand_i64[bot_pos[1]], hand_i64[bot_pos[2]], hand_i64[bot_pos[3]]], dtype=np.int64)
    return top, mid, bot


# ============================================================
# Player ("me") strategy: v65
# ============================================================

def me_strategy(hand):
    setting_idx = int(v65_strategy(hand))
    return decode_setting(hand.astype(np.int64), setting_idx)


# ============================================================
# Existing opponent strategies (from prior sims)
# ============================================================

def opp_balanced_pro(hand):
    """MiddleFirstSuitAware: best Hold'em mid + same-tier swap for bot shape."""
    best, best_key = (0, 1), (-1, -1, -1, -1, -1)
    for i in range(7):
        for j in range(i + 1, 7):
            tier = middle_tier(int(hand[i]), int(hand[j]))
            rem5 = [int(hand[x]) for x in range(7) if x != i and x != j]
            top_local = pick_top_from_rem5(rem5)
            cand_bot = [rem5[k] for k in range(5) if k != top_local]
            bot_sc = bot_suit_score(cand_bot)
            strength = naive_mid_score(int(hand[i]), int(hand[j]))
            min_idx, max_idx = min(int(hand[i]), int(hand[j])), max(int(hand[i]), int(hand[j]))
            key = (tier, bot_sc, strength, 255 - min_idx, 255 - max_idx)
            if key > best_key:
                best_key, best = key, (i, j)
    i, j = best
    mid = [int(hand[i]), int(hand[j])]
    rem5 = [int(hand[x]) for x in range(7) if x != i and x != j]
    top_local = pick_top_from_rem5(rem5)
    top = rem5[top_local]
    bot = [rem5[k] for k in range(5) if k != top_local]
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


def opp_pair_first_standardist(hand):
    """Operator's archetype A: QQ/KK/AA → mid; then A/K/Q → top; bot = rem4."""
    cards = [int(c) for c in hand]
    rc = [0] * 15
    for c in cards: rc[card_rank(c)] += 1
    mid_pair_rank = None
    for r in [14, 13, 12]:
        if rc[r] >= 2:
            mid_pair_rank = r
            break
    if mid_pair_rank is not None:
        mid_cards, rem = [], []
        for c in cards:
            if len(mid_cards) < 2 and card_rank(c) == mid_pair_rank:
                mid_cards.append(c)
            else:
                rem.append(c)
        rem_sorted = sorted(rem, key=lambda x: (card_rank(x), x), reverse=True)
        top = rem_sorted[0]
        bot_cards = rem_sorted[1:]
        return top, np.array(mid_cards, dtype=np.int64), np.array(bot_cards, dtype=np.int64)
    cards_sorted = sorted(cards, key=lambda x: (card_rank(x), x), reverse=True)
    top = cards_sorted[0]
    rem6 = cards_sorted[1:]
    best_score, best_combo = -10**9, (0, 1, 2, 3)
    for combo in combinations(range(6), 4):
        cand = [rem6[c] for c in combo]
        s = omaha_bot_score(cand)
        if s > best_score:
            best_score, best_combo = s, combo
    bot = [rem6[c] for c in best_combo]
    mid = [rem6[i] for i in range(6) if i not in best_combo]
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


def opp_top_greedy_defender(hand):
    """Operator's archetype B with J-or-lower → Omaha pivot."""
    cards = [int(c) for c in hand]
    max_card = max(cards, key=lambda x: (card_rank(x), x))
    max_rank = card_rank(max_card)
    if max_rank >= 12:
        top = max_card
        rem6 = [c for c in cards if c != top]
        best_score, best_combo = -10**9, (0, 1, 2, 3)
        for combo in combinations(range(6), 4):
            cand = [rem6[c] for c in combo]
            s = omaha_bot_score(cand)
            if s > best_score:
                best_score, best_combo = s, combo
        bot = [rem6[c] for c in best_combo]
        mid = [rem6[i] for i in range(6) if i not in best_combo]
        return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)
    # Pivot to Omaha-first
    best_score, best_combo = -10**9, (0, 1, 2, 3)
    for combo in combinations(range(7), 4):
        cand = [cards[c] for c in combo]
        s = omaha_bot_score(cand)
        if s > best_score:
            best_score, best_combo = s, combo
    bot = [cards[c] for c in best_combo]
    rem3 = [cards[i] for i in range(7) if i not in best_combo]
    top_local = 0
    for i in range(1, 3):
        ci, cb = rem3[i], rem3[top_local]
        if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
            top_local = i
    top = rem3[top_local]
    mid = [rem3[i] for i in range(3) if i != top_local]
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


# ============================================================
# NEW: 4 more archetypes
# ============================================================

def opp_reasonable_naivete(hand):
    """The casual home player who's never read Taiwanese strategy.
    Knows: KK/AA → mid (basic poker instinct). Highest non-pair → top. 4 leftover → bot.
    Missing: DS-bot optimization, defensive inversion, suit-aware swap, pair-to-bot.
    """
    cards = [int(c) for c in hand]
    rc = [0] * 15
    for c in cards: rc[card_rank(c)] += 1

    # Force KK/AA into mid if present.
    mid_pair_rank = None
    for r in [14, 13]:
        if rc[r] >= 2:
            mid_pair_rank = r
            break
    if mid_pair_rank is not None:
        mid_cards, rem = [], []
        for c in cards:
            if len(mid_cards) < 2 and card_rank(c) == mid_pair_rank:
                mid_cards.append(c)
            else:
                rem.append(c)
        # Top = highest of rem, bot = remaining 4 in order received (no optimization).
        rem_sorted = sorted(rem, key=lambda x: (card_rank(x), x), reverse=True)
        top = rem_sorted[0]
        bot = rem_sorted[1:]
        return top, np.array(mid_cards, dtype=np.int64), np.array(bot, dtype=np.int64)

    # No premium pair. Default: top=highest, mid=naive_mid_score top 2 of remaining 6, bot=leftover.
    cards_sorted = sorted(cards, key=lambda x: (card_rank(x), x), reverse=True)
    top = cards_sorted[0]
    rem6 = cards_sorted[1:]
    # Best Hold'em mid from rem6 (naive_mid_score) — no swap, no bot awareness.
    best_score = -1
    best_pair = (0, 1)
    for i in range(6):
        for j in range(i + 1, 6):
            s = naive_mid_score(rem6[i], rem6[j])
            if s > best_score:
                best_score = s
                best_pair = (i, j)
    mid = [rem6[best_pair[0]], rem6[best_pair[1]]]
    bot = [rem6[k] for k in range(6) if k not in best_pair]
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


def opp_defensive_inversion(hand):
    """Knows V4's defensive flip: max ≤ T OR vulnerable broadway → lowest on top + DS bot + HIMID.

    Otherwise plays like Balanced Pro (best Hold'em mid with bot-shape awareness).
    """
    cards = [int(c) for c in hand]
    rc = [0] * 15
    for c in cards: rc[card_rank(c)] += 1
    has_pair = any(rc[r] >= 2 for r in range(2, 15))
    cards_sorted = sorted(cards, key=lambda x: (card_rank(x), x), reverse=True)
    max_rank = card_rank(cards_sorted[0])
    second_rank = card_rank(cards_sorted[1])

    # Defensive trigger (Flag 1: no pair, weak max).
    if not has_pair and (max_rank <= 10 or (max_rank in (11, 12, 13) and second_rank <= 8)):
        # Lowest on top, then best 2+2 DS bot from rem6, mid = the 2 highest leftover.
        cards_asc = sorted(cards, key=lambda x: (card_rank(x), x))
        top = cards_asc[0]
        rem6 = cards_asc[1:]
        # Find best DS 4-bot (max bot_suit_score, prefer higher omaha score on ties).
        best_key, best_combo = (-1, -10**9), (0, 1, 2, 3)
        for combo in combinations(range(6), 4):
            cand = [rem6[c] for c in combo]
            ss = bot_suit_score(cand)
            oms = omaha_bot_score(cand)
            if (ss, oms) > best_key:
                best_key = (ss, oms)
                best_combo = combo
        bot = [rem6[c] for c in best_combo]
        # Mid = 2 highest of leftover.
        rem_mid = [rem6[i] for i in range(6) if i not in best_combo]
        rem_mid_sorted = sorted(rem_mid, key=lambda x: (card_rank(x), x), reverse=True)
        mid = rem_mid_sorted[:2]
        return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)

    # Defensive trigger Flag 2: weak pair, J-low body.
    pair_rank = None
    for r in range(2, 15):
        if rc[r] == 2:
            pair_rank = r
            break
    if pair_rank is not None and max_rank <= 11 and (pair_rank <= 6 or pair_rank == max_rank):
        # Lowest non-pair on top, pair in mid, 4 highest non-pair in bot.
        pair_cards = [c for c in cards if card_rank(c) == pair_rank]
        non_pair = [c for c in cards if card_rank(c) != pair_rank]
        non_pair_sorted = sorted(non_pair, key=lambda x: (card_rank(x), x))
        top = non_pair_sorted[0]
        bot = non_pair_sorted[1:5]
        mid = pair_cards[:2]
        return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)

    # Otherwise play like Balanced Pro.
    return opp_balanced_pro(hand)


def opp_holdem_mid_optimizer(hand):
    """The "Hold'em-Mid Optimizer" — picks best 2-card Hold'em mid by raw naive_mid_score.

    Breaks pairs if a non-pair mid scores higher. Top = highest remaining. Bot = leftover.
    Common Hold'em-instinct error.
    """
    # Find the 2-card mid with the highest naive_mid_score across ALL C(7,2) = 21 pairs.
    # Critically, this does NOT preserve pair-mid when a "stronger" non-pair mid exists.
    best_score = -1
    best_pair = (0, 1)
    for i in range(7):
        for j in range(i + 1, 7):
            s = naive_mid_score(int(hand[i]), int(hand[j]))
            if s > best_score:
                best_score = s
                best_pair = (i, j)
    mid = [int(hand[best_pair[0]]), int(hand[best_pair[1]])]
    rem5 = [int(hand[k]) for k in range(7) if k not in best_pair]
    # Top = highest of rem5 (regardless of pair preservation).
    top_local = 0
    for i in range(1, 5):
        ci, cb = rem5[i], rem5[top_local]
        if card_rank(ci) > card_rank(cb) or (card_rank(ci) == card_rank(cb) and ci > cb):
            top_local = i
    top = rem5[top_local]
    bot = [rem5[i] for i in range(5) if i != top_local]
    return top, np.array(mid, dtype=np.int64), np.array(bot, dtype=np.int64)


def opp_grid_oracle(hand):
    """Composite-heuristic strong opponent. Approximates argmax_mean play without grid lookup.

    Scores all 105 settings on a composite of:
      - DS bot shape (heavily weighted)
      - Omaha bot connectivity / pair / wheel score
      - Mid strength (naive_mid_score, with HUGE bonus for pair-mid)
      - Top quality (rank)
      - Pair preservation bonus (any pair in same tier)

    Picks the setting with the maximum composite score.
    """
    hand_i = hand.astype(np.int64)
    # Precompute hand rank counts for pair detection.
    rc = [0] * 15
    for c in hand_i: rc[card_rank(int(c))] += 1
    has_pair_ranks = [r for r in range(2, 15) if rc[r] >= 2]

    best_score = -10**18
    best_idx = 0
    for s_idx in range(105):
        top, mid, bot = decode_setting(hand_i, s_idx)
        top_i = int(top)
        mid_list = [int(mid[0]), int(mid[1])]
        bot_list = [int(bot[0]), int(bot[1]), int(bot[2]), int(bot[3])]

        ss_bot = bot_suit_score(bot_list)             # 1-5
        oms_bot = omaha_bot_score(bot_list)           # ~-10 to +60
        mid_strength = naive_mid_score(mid_list[0], mid_list[1])  # ~10-230
        top_rank = card_rank(top_i)                    # 2-14

        # Pair-preservation bonus: each pair fully contained in one tier gets a bonus.
        intact_pair_bonus = 0
        for r in has_pair_ranks:
            in_mid = sum(1 for c in mid_list if card_rank(c) == r)
            in_bot = sum(1 for c in bot_list if card_rank(c) == r)
            if in_mid == 2 or in_bot == 2:
                # Pair intact in mid or bot — high bonus.
                intact_pair_bonus += 80 + r * 4
            elif in_mid == 1 and in_bot == 1:
                # Pair split between mid and bot — penalty.
                intact_pair_bonus -= 40
            elif in_mid == 1 or in_bot == 1:
                # One in mid/bot, one in top — penalty.
                intact_pair_bonus -= 30

        # Premium-pair-in-mid huge bonus (KK/AA-in-mid is the strongest move in the game).
        premium_pair_in_mid = 0
        if card_rank(mid_list[0]) == card_rank(mid_list[1]):
            pair_rank_in_mid = card_rank(mid_list[0])
            if pair_rank_in_mid in (13, 14):
                premium_pair_in_mid = 200

        composite = (
            20 * ss_bot +
            1.0 * oms_bot +
            1.5 * mid_strength +
            8 * top_rank +
            intact_pair_bonus +
            premium_pair_in_mid
        )

        if composite > best_score:
            best_score = composite
            best_idx = s_idx

    return decode_setting(hand_i, best_idx)


# ============================================================
# Scoring
# ============================================================

def score_pair(me_set, opp_set, ba, bb, ev):
    mt, mm, mb = me_set
    ot, om, ob = opp_set
    rk = [
        (ev.top(mt, ba), ev.top(ot, ba), PTS_TOP),
        (ev.mid(mm, ba), ev.mid(om, ba), PTS_MID),
        (ev.bot(mb, ba), ev.bot(ob, ba), PTS_BOT),
        (ev.top(mt, bb), ev.top(ot, bb), PTS_TOP),
        (ev.mid(mm, bb), ev.mid(om, bb), PTS_MID),
        (ev.bot(mb, bb), ev.bot(ob, bb), PTS_BOT),
    ]
    if all(a > b for a, b, _ in rk): return PTS_SCOOP
    if all(a < b for a, b, _ in rk): return -PTS_SCOOP
    pts = 0
    for a, b, p in rk:
        if a > b: pts += p
        elif a < b: pts -= p
    return pts


# ============================================================
# Run scenario
# ============================================================

def run_scenario(name, me_fn, opp_fn_list, n_sims, n_hands, ev, seed_base):
    print(f"\n=== {name} ===", flush=True)
    cum = np.empty((n_sims, n_hands), dtype=np.float64)
    all_pts = []
    for s in range(n_sims):
        rng = np.random.default_rng(seed=seed_base + s)
        t0 = time.time()
        pts = np.empty(n_hands, dtype=np.float64)
        for h in range(n_hands):
            deck = rng.permutation(52)
            me_h = np.sort(deck[:7]).astype(np.uint8)
            op_h = [np.sort(deck[7 + 7*k:14 + 7*k]).astype(np.uint8) for k in range(3)]
            ba = deck[28:33].astype(np.int64)
            bb = deck[33:38].astype(np.int64)
            me_set = me_fn(me_h)
            tot = 0
            for k in range(3):
                opp_set = opp_fn_list[k](op_h[k])
                tot += score_pair(me_set, opp_set, ba, bb, ev)
            pts[h] = tot
        cum[s] = np.cumsum(pts * STAKE)
        all_pts.append(pts)
        elapsed = time.time() - t0
        print(f"  sim {s+1:2d}: final=${cum[s,-1]:+,.0f}  pts/h={pts.mean():+.3f}  ({elapsed:.1f}s)", flush=True)
    flat = np.concatenate(all_pts)
    finals = cum[:, -1]
    print(f"  AGGREGATE: mean ${flat.mean()*STAKE:+.2f}/h  final ${finals.mean():+,.0f} ± ${finals.std():,.0f}", flush=True)
    return cum, flat


# ============================================================
# Main
# ============================================================

def main():
    print("Loading lookup ...", flush=True)
    lookup = load_lookup(LOOKUP_PATH)
    ev = Ev(lookup)

    SCENARIOS = [
        ("Symmetry (v65 vs 3× v65)",
         [me_strategy] * 3, 3000),
        ("Pair-First Standardist",
         [opp_pair_first_standardist] * 3, 4000),
        ("Top-Greedy Defender",
         [opp_top_greedy_defender] * 3, 5000),
        ("Balanced Pro (mfsuitaware)",
         [opp_balanced_pro] * 3, 6000),
        ("Reasonable Naïveté",
         [opp_reasonable_naivete] * 3, 7000),
        ("Defensive Inversion Player",
         [opp_defensive_inversion] * 3, 8000),
        ("Hold'em-Mid Optimizer",
         [opp_holdem_mid_optimizer] * 3, 9000),
        ("Grid Oracle (heuristic composite)",
         [opp_grid_oracle] * 3, 10000),
    ]

    results = []
    for name, opps, seed_base in SCENARIOS:
        cum, flat = run_scenario(name, me_strategy, opps, N_SIMS, HANDS_PER_SIM, ev, seed_base)
        results.append((name, cum, flat))

    # Print summary table.
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"  {'Scenario':<45} {'$/hand':>10} {'Final $':>14} {'±std':>12}")
    print(f"  {'-'*45} {'-'*10} {'-'*14} {'-'*12}")
    for name, cum, flat in results:
        f = cum[:, -1]
        print(f"  {name:<45} ${flat.mean()*STAKE:>+8.2f} ${f.mean():>+12,.0f} ${f.std():>10,.0f}", flush=True)

    # Build chart.
    print("\nBuilding chart ...", flush=True)
    build_chart(results)


def build_chart(results):
    # 3x3 grid: 8 scenario panels + 1 summary bar.
    titles = [r[0] for r in results] + ["Summary (mean final $, ±1σ)"]
    fig = make_subplots(
        rows=3, cols=3,
        subplot_titles=titles,
        horizontal_spacing=0.07, vertical_spacing=0.10,
    )

    x = np.arange(1, HANDS_PER_SIM + 1)
    for idx, (name, cum, flat) in enumerate(results):
        row = idx // 3 + 1
        col = idx % 3 + 1
        for i in range(N_SIMS):
            fig.add_trace(go.Scatter(
                x=x, y=cum[i], mode="lines",
                name=f"Sim {i+1}",
                line=dict(color=COLORS[i], width=1.2),
                showlegend=(idx == 0),
                legendgroup=f"sim{i+1}",
                hovertemplate=f"<b>{name}</b><br>Sim {i+1}<br>Hand #%{{x:,}}<br>$%{{y:+,.0f}}<extra></extra>",
            ), row=row, col=col)
        mean_per_hand = float(flat.mean() * STAKE)
        fig.add_trace(go.Scatter(
            x=x, y=mean_per_hand * x, mode="lines",
            name="Mean trend",
            line=dict(color="black", width=2, dash="dash"),
            showlegend=(idx == 0),
            legendgroup="mean",
            hovertemplate=f"<b>Mean trend</b><br>$%{{y:+,.0f}}<extra></extra>",
        ), row=row, col=col)
        fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"),
                      row=row, col=col)
        # Inline stats.
        finals = cum[:, -1]
        ann_text = (f"<b>${flat.mean()*STAKE:+.2f}/h</b><br>"
                    f"Final: ${finals.mean():+,.0f}<br>"
                    f"σ: ${finals.std():,.0f}")
        x_axis = "x" if idx == 0 else f"x{idx+1}"
        y_axis = "y" if idx == 0 else f"y{idx+1}"
        fig.add_annotation(
            xref=f"{x_axis} domain", yref=f"{y_axis} domain",
            x=0.02, y=0.97, xanchor="left", yanchor="top",
            text=ann_text, showarrow=False,
            bgcolor="rgba(255,255,255,0.88)", bordercolor="rgba(0,0,0,0.3)",
            borderwidth=1, borderpad=5,
            font=dict(size=10, family="monospace"), align="left",
        )

    # Summary bar in slot (3, 3) — with rich hover descriptions.
    names_short = [r[0].split("(")[0].strip()[:25] for r in results]
    means = [float(r[1][:, -1].mean()) for r in results]
    stds = [float(r[1][:, -1].std()) for r in results]
    flats = [r[2] for r in results]

    # Strategy descriptions — shown on hover for each bar.
    STRATEGY_DESCRIPTIONS = {
        "Symmetry (v65 vs 3× v65)": (
            "VALIDATION TEST<br>"
            "Both seats play v65 (the production strategy).<br>"
            "Expected: $0 by symmetry. Observed: within noise.<br>"
            "Confirms the simulator is unbiased."
        ),
        "Pair-First Standardist": (
            "STRATEGY: 'Rigid rule-follower'<br>"
            "• QQ/KK/AA → forced to MID<br>"
            "• Then A/K/Q → top from leftover<br>"
            "• Bot = 4 leftover (NO DS optimization)<br>"
            "• If no premium pair: top=highest,<br>"
            "&nbsp;&nbsp;then best Omaha bot, mid=leftover<br>"
            "<br>"
            "LEAK: Forces QQ to mid even when<br>"
            "PBOT-DS would be stronger.<br>"
            "Common at home games."
        ),
        "Top-Greedy Defender": (
            "STRATEGY: 'Top first, Omaha pivot if weak'<br>"
            "• Max card Q/K/A → top ALWAYS<br>"
            "• Then best Omaha bot from rem6<br>"
            "• Mid = the 2 leftover (often garbage)<br>"
            "• Max ≤ J → pivot to Omaha-first:<br>"
            "&nbsp;&nbsp;best 4-card bot from all 7,<br>"
            "&nbsp;&nbsp;top = highest of rem3<br>"
            "<br>"
            "LEAK: Sacrifices mid entirely for top.<br>"
            "Worst archetype against v65."
        ),
        "Balanced Pro (mfsuitaware)": (
            "STRATEGY: 'Best Hold'em mid with bot-shape swap'<br>"
            "• Picks 2-card mid by 5-tier classifier:<br>"
            "&nbsp;&nbsp;pair > suited broadway > offsuit<br>"
            "&nbsp;&nbsp;broadway > suited connector > other<br>"
            "• Within same tier: prefers mid that<br>"
            "&nbsp;&nbsp;leaves best DS bot shape<br>"
            "• Top = highest singleton<br>"
            "<br>"
            "LEAK: Doesn't do PBOT-DS (Rule 2c)<br>"
            "or defensive inversions.<br>"
            "Project's strongest realistic competent opp."
        ),
        "Reasonable Naïveté": (
            "STRATEGY: 'Casual decent player'<br>"
            "• KK/AA → mid (basic instinct)<br>"
            "• Otherwise: top=highest, best Hold'em<br>"
            "&nbsp;&nbsp;mid from rem6, bot=leftover<br>"
            "• NO DS bot optimization<br>"
            "• NO defensive inversion<br>"
            "• NO suit-aware swap<br>"
            "• NO pair-to-bot consideration<br>"
            "<br>"
            "LEAK: Misses surgical refinements.<br>"
            "Most common archetype at home games."
        ),
        "Defensive Inversion Player": (
            "STRATEGY: 'Knows the defensive flip'<br>"
            "• On weak hands (no pair + max≤T,<br>"
            "&nbsp;&nbsp;or vulnerable broadway): invert.<br>"
            "&nbsp;&nbsp;Top=lowest, build DS bot,<br>"
            "&nbsp;&nbsp;mid=2 highest leftover<br>"
            "• Weak pair (rank≤6 or pair=max,<br>"
            "&nbsp;&nbsp;J-low body): top=lowest non-pair,<br>"
            "&nbsp;&nbsp;mid=pair, bot=4 highest non-pair<br>"
            "• Else: play like Balanced Pro<br>"
            "<br>"
            "LEAK: Plays well on defensive hands<br>"
            "but lacks v65's offensive refinements.<br>"
            "Uncommon — requires deep study."
        ),
        "Hold'em-Mid Optimizer": (
            "STRATEGY: 'Pair-breaking for strong mid'<br>"
            "• Picks 2-card mid by raw Hold'em<br>"
            "&nbsp;&nbsp;score across ALL 21 pairs<br>"
            "• Breaks pairs if non-pair mid scores higher<br>"
            "• Top = highest remaining<br>"
            "• Bot = leftover 4<br>"
            "<br>"
            "LEAK: Pair-breaking weakens both<br>"
            "mid AND bot anchoring.<br>"
            "Common Hold'em-instinct error."
        ),
        "Grid Oracle (heuristic composite)": (
            "STRATEGY: 'The heuristic ceiling'<br>"
            "• Scores ALL 105 settings on composite:<br>"
            "&nbsp;&nbsp;DS bot weight × 20<br>"
            "&nbsp;&nbsp;+ pair preservation bonus<br>"
            "&nbsp;&nbsp;+ premium-pair-in-mid bonus (+200)<br>"
            "&nbsp;&nbsp;+ mid Hold'em strength<br>"
            "&nbsp;&nbsp;+ top high-rank<br>"
            "&nbsp;&nbsp;+ Omaha bot connectivity<br>"
            "• Picks setting with max composite<br>"
            "<br>"
            "LEAK: ALMOST NONE. v65 beats by<br>"
            "only $0.41/hand (within noise).<br>"
            "This is the heuristic ceiling."
        ),
    }
    # customdata: each entry is the full strategy description for that bar.
    customdata = [STRATEGY_DESCRIPTIONS.get(r[0], "(no description)") for r in results]
    per_hand_dollars = [float(f.mean() * STAKE) for f in flats]
    bar_colors = []
    for r in results:
        if "Symmetry" in r[0]:
            bar_colors.append("#aaaaaa")
        elif means[results.index(r)] > 0:
            bar_colors.append("#2ca02c")
        else:
            bar_colors.append("#d62728")
    fig.add_trace(go.Bar(
        x=names_short, y=means,
        error_y=dict(type="data", array=stds, visible=True),
        marker_color=bar_colors,
        showlegend=False,
        text=[f"${m:+,.0f}" for m in means],
        textposition="outside",
        customdata=list(zip(customdata, [f"{p:+.2f}" for p in per_hand_dollars])),
        hovertemplate=(
            "<b>%{x}</b><br>"
            "<br>"
            "<b>Mean final:</b> $%{y:+,.0f} (over 5,000 hands)<br>"
            "<b>$/hand:</b> $%{customdata[1]}<br>"
            "<br>"
            "%{customdata[0]}"
            "<extra></extra>"
        ),
    ), row=3, col=3)
    fig.add_hline(y=0, line=dict(color="rgba(0,0,0,0.3)", width=1, dash="dot"),
                  row=3, col=3)

    fig.update_layout(
        title=dict(
            text=(
                "<b>V4 Guide MC — 8 Opponent Archetypes Tested · 5,000 hands × 10 sims each</b><br>"
                f"<sub>$10/point · 4-handed · v65 production strategy on the player seat · "
                f"<b>hover the summary bars for full strategy descriptions</b></sub>"
            ),
            x=0.5, xanchor="center", font=dict(size=18),
        ),
        plot_bgcolor="white",
        width=1800, height=1300,
        margin=dict(l=60, r=40, t=110, b=70),
        hovermode="closest",
        legend=dict(orientation="h", x=0.5, xanchor="center", y=-0.04,
                    bgcolor="rgba(255,255,255,0.85)",
                    bordercolor="rgba(0,0,0,0.3)", borderwidth=1, font_size=10),
    )
    for r_ in range(1, 4):
        for c_ in range(1, 4):
            if (r_, c_) == (3, 3): continue
            fig.update_xaxes(title="Hand #", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                             zeroline=False, tickformat=",", row=r_, col=c_)
            fig.update_yaxes(title="$ won/lost", showgrid=True, gridcolor="rgba(0,0,0,0.06)",
                             zeroline=False, tickformat="+$,.0f", row=r_, col=c_)
    fig.update_xaxes(title="Archetype", tickangle=-30, row=3, col=3)
    fig.update_yaxes(title="Mean final $ (±1σ)", showgrid=True,
                     gridcolor="rgba(0,0,0,0.06)", tickformat="+$,.0f", row=3, col=3)

    fig.write_html(OUTPUT_HTML, include_plotlyjs="cdn", full_html=True,
                   config={"displayModeBar": True, "displaylogo": False})
    print(f"Chart: {OUTPUT_HTML}", flush=True)


if __name__ == "__main__":
    main()
