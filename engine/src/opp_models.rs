//! Opponent-model heuristics for Monte Carlo simulation (Sprint 2b).
//!
//! The MC engine deals the opponent real random cards; each heuristic here
//! is a pure function that decides how to ARRANGE those 7 cards into a
//! `HandSetting`. The panel spans a spectrum of play styles so the diagnostic
//! can measure how much the opponent's strategy changes the solver's answer.
//!
//! Models (see `sprints/s2-monte-carlo.md` Sprint 2b for the full spec):
//!   1. Random               — uniform over 105 settings (in `monte_carlo.rs`)
//!   2. MiddleFirstNaive     — best Hold'em mid, highest top, bot sanity check
//!   3. MiddleFirstSuitAware — same + within-tier swap when it improves the bot
//!   4. OmahaFirst           — best Omaha bot first, then best mid, then top
//!   5. TopDefensive         — highest NON-PAIR-MEMBER on top; preserve pairs
//!   6. RandomWeighted       — uniform over "reasonable" settings, with fallback
//!   7. BalancedHeuristic    — weighted multi-tier scoring over all 105 settings
//!
//! Naming convention: the public entry for model X is `opp_<model>(hand)` and
//! returns the `HandSetting`. RandomWeighted takes an RNG. All others are
//! pure deterministic functions.

use rand::rngs::SmallRng;
use rand::Rng;

use crate::card::Card;
use crate::setting::{all_settings, HandSetting};

// --- Shared helpers ---------------------------------------------------------

/// Rough Hold'em-equity score for a 2-card middle (per the Naive spec):
///   pair:       200 + rank * 2                  (AA=228 ... 22=204)
///   non-pair:   high*3 + low*2 + suited/connected/gapped/ace bonuses
/// Used directly by MiddleFirstNaive and as the intra-tier ordering key by
/// MiddleFirstSuitAware. Magnitudes aren't meaningful in absolute terms; only
/// relative ordering matters.
#[inline]
pub fn naive_mid_score(a: Card, b: Card) -> u32 {
    let r1 = a.rank();
    let r2 = b.rank();
    let (high, low) = if r1 >= r2 { (r1, r2) } else { (r2, r1) };
    if high == low {
        200 + (high as u32) * 2
    } else {
        let mut s = (high as u32) * 3 + (low as u32) * 2;
        if a.suit() == b.suit() {
            s += 8;
        }
        let gap = high - low;
        if gap == 1 {
            s += 6;
        } else if gap == 2 {
            s += 3;
        }
        if high == 14 {
            s += 5;
        }
        s
    }
}

/// 5-tier classifier used by MiddleFirstSuitAware's same-tier swap rule.
/// Higher number = stronger tier.
///   5 = pocket pair
///   4 = suited broadway (both T+, same suit)
///   3 = offsuit broadway (both T+, different suits)
///   2 = suited ace OR suited connector (both < T, gap ≤ 2, same suit)
///   1 = everything else
#[inline]
pub fn middle_tier(a: Card, b: Card) -> u8 {
    let r1 = a.rank();
    let r2 = b.rank();
    let (high, low) = if r1 >= r2 { (r1, r2) } else { (r2, r1) };
    let suited = a.suit() == b.suit();
    if high == low {
        5
    } else if low >= 10 && suited {
        4
    } else if low >= 10 {
        3
    } else if suited && (high == 14 || (high - low) <= 2) {
        2
    } else {
        1
    }
}

/// Score a 4-card bottom's suit structure for Omaha flush potential.
/// Ranking: DS > SS > rainbow > 3+1 > 4-flush (per game-rules.md §1.4).
#[inline]
pub fn bot_suit_score(bot: &[Card; 4]) -> u8 {
    let mut counts = [0u8; 4];
    for c in bot {
        counts[c.suit() as usize] += 1;
    }
    let mut sorted = counts;
    sorted.sort_unstable_by(|a, b| b.cmp(a));
    match (sorted[0], sorted[1]) {
        (2, 2) => 5,
        (2, 1) => 4,
        (1, 1) => 3,
        (3, 1) => 2,
        (4, 0) => 1,
        _ => 0,
    }
}

/// Pick the top-card index from 5 remaining cards with pair preservation
/// (Bug 1 fix, Decision 025). Prefers the highest-rank SINGLETON — a card
/// whose rank appears exactly once in `rem5`. Falls back to highest-rank
/// overall when every card is a pair member. Index tie-break on equal ranks.
///
/// Why: MFNaive and MFSuitAware compose as "pick best mid first, top =
/// highest remaining". Without this rule, on hands like AAKK-x-y-z the top
/// takes one K and orphans the other K into the bot, destroying the pair
/// that was the strongest feature of the rem5. By preferring singletons the
/// model keeps KK intact in the bot.
fn pick_top_from_rem5(rem5: &[Card; 5]) -> usize {
    let mut rank_counts = [0u8; 15];
    for c in rem5 {
        rank_counts[c.rank() as usize] += 1;
    }
    // Preferred: highest-rank singleton.
    let mut best_single: Option<usize> = None;
    for i in 0..5 {
        if rank_counts[rem5[i].rank() as usize] != 1 {
            continue;
        }
        match best_single {
            None => best_single = Some(i),
            Some(bi) => {
                let cur = rem5[i];
                let bc = rem5[bi];
                if cur.rank() > bc.rank()
                    || (cur.rank() == bc.rank() && cur.index() > bc.index())
                {
                    best_single = Some(i);
                }
            }
        }
    }
    if let Some(i) = best_single {
        return i;
    }
    // Fallback: every card is a pair member (e.g. AAKKQQ+J with J already in
    // mid). Pick highest-rank overall with index tie-break — same behaviour
    // as the pre-Bug-1 rule.
    let mut top_i = 0usize;
    for i in 1..5 {
        let cur = rem5[i];
        let best = rem5[top_i];
        if cur.rank() > best.rank()
            || (cur.rank() == best.rank() && cur.index() > best.index())
        {
            top_i = i;
        }
    }
    top_i
}

/// For a given (mid_i, mid_j), compute the 4-card bottom that would result
/// after the top-card is chosen by `pick_top_from_rem5` (pair-preserving).
/// Used by MFSuitAware to score the candidate mid by the resulting bot's
/// suit structure.
fn candidate_bot_after_top(hand: &[Card; 7], mi: usize, mj: usize) -> [Card; 4] {
    let mut rem5 = [Card(0); 5];
    let mut k = 0;
    for x in 0..7 {
        if x != mi && x != mj {
            rem5[k] = hand[x];
            k += 1;
        }
    }
    let top_i = pick_top_from_rem5(&rem5);
    let mut bot = [Card(0); 4];
    let mut bi = 0;
    for i in 0..5 {
        if i != top_i {
            bot[bi] = rem5[i];
            bi += 1;
        }
    }
    bot
}

/// Assemble a `HandSetting` given the hand and the two mid-indices, using
/// the pair-preserving top-selection rule (`pick_top_from_rem5`).
fn build_setting_mid_then_top(hand: &[Card; 7], mi: usize, mj: usize) -> HandSetting {
    let mut mid = [hand[mi], hand[mj]];
    if mid[1].index() > mid[0].index() {
        mid.swap(0, 1);
    }
    let mut rem5 = [Card(0); 5];
    let mut k = 0;
    for x in 0..7 {
        if x != mi && x != mj {
            rem5[k] = hand[x];
            k += 1;
        }
    }
    let top_i = pick_top_from_rem5(&rem5);
    let top = rem5[top_i];
    let mut bot = [Card(0); 4];
    let mut bi = 0;
    for i in 0..5 {
        if i != top_i {
            bot[bi] = rem5[i];
            bi += 1;
        }
    }
    bot.sort_unstable_by(|a, b| b.index().cmp(&a.index()));
    HandSetting { top, mid, bot }
}

// --- Model 2: MiddleFirstNaive ---------------------------------------------

/// Best 2-card Hold'em middle, highest remaining card on top, last 4 to bot.
/// A post-hoc bot-sanity swap avoids the most flagrant 3+1 / 4-flush bottoms
/// (Fix a): if the bot has 3+ cards of one suit AND the mid is not a pair,
/// swap the lowest over-suited bot card with the lower mid card so the bot
/// suit count drops to ≤ 2. Preserves pair mids (never breaks them).
pub fn opp_middle_first_naive(hand: [Card; 7]) -> HandSetting {
    // Pick best mid by naive_mid_score.
    let mut best = (0usize, 1usize);
    let mut best_score = naive_mid_score(hand[0], hand[1]);
    for i in 0..7 {
        for j in (i + 1)..7 {
            if (i, j) == (0, 1) {
                continue;
            }
            let s = naive_mid_score(hand[i], hand[j]);
            if s > best_score {
                best_score = s;
                best = (i, j);
            }
        }
    }
    let setting = build_setting_mid_then_top(&hand, best.0, best.1);
    apply_bot_sanity_swap(setting)
}

/// If bot has 3+ of a suit AND the mid is not a pair, swap the LOWEST
/// over-suited bot card with the LOWER mid card (if the swap reduces the
/// bot's max-suit count). This is the minimal "wait, that looks wrong"
/// tweak a naive-Hold'em player would still spot in Omaha.
fn apply_bot_sanity_swap(mut s: HandSetting) -> HandSetting {
    // Count bot suits.
    let mut counts = [0u8; 4];
    for c in &s.bot {
        counts[c.suit() as usize] += 1;
    }
    let over_suit_idx = (0..4).find(|&si| counts[si] >= 3);
    if let Some(sidx) = over_suit_idx {
        // Never break a mid pair.
        if s.mid[0].rank() == s.mid[1].rank() {
            return s;
        }
        // Pick the lowest-ranked bot card of the over-suit.
        let lowest_over = s
            .bot
            .iter()
            .enumerate()
            .filter(|(_, c)| c.suit() as usize == sidx)
            .min_by_key(|(_, c)| c.rank());
        let (bi, _b_card) = match lowest_over {
            Some(x) => x,
            None => return s,
        };
        let bi = bi;
        // Lower mid card — the one with smaller rank (and smaller index if tied).
        let mi = if s.mid[0].rank() < s.mid[1].rank()
            || (s.mid[0].rank() == s.mid[1].rank() && s.mid[0].index() < s.mid[1].index())
        {
            0usize
        } else {
            1usize
        };
        // Only swap if the mid's suit is DIFFERENT from the over-suit (otherwise no improvement).
        if s.mid[mi].suit() as usize == sidx {
            return s;
        }
        // Check the mid card would not create a NEW over-suit when placed into bot:
        // counts after swap: over_suit: -1, mid's former suit in bot: +1.
        let mid_suit = s.mid[mi].suit() as usize;
        let new_suit_count = counts[mid_suit] + 1;
        if new_suit_count >= 3 {
            return s; // would just move the problem
        }
        // Swap.
        std::mem::swap(&mut s.mid[mi], &mut s.bot[bi]);
        s.bot.sort_unstable_by(|a, b| b.index().cmp(&a.index()));
        if s.mid[1].index() > s.mid[0].index() {
            s.mid.swap(0, 1);
        }
    }
    s
}

// --- Model 3: MiddleFirstSuitAware (refactored) ----------------------------

/// Same as Naive but allows within-tier swaps when the alternative mid
/// improves the bot's suit category (Fix b). Lex-max on:
///   (middle_tier, bot_suit_score, naive_mid_score, lex-inverse card indices)
///
/// Effect: within the same Hold'em-strength tier, the model prefers middles
/// that leave the bot double-suited or single-suited over rainbow, and
/// penalises middles that force a 3+1 bot.
pub fn opp_middle_first_suit_aware(hand: [Card; 7]) -> HandSetting {
    let mut best = (0usize, 1usize);
    let mut best_key = (0u8, 0u8, 0u32, 0u8, 0u8);
    for i in 0..7 {
        for j in (i + 1)..7 {
            let tier = middle_tier(hand[i], hand[j]);
            let bot = candidate_bot_after_top(&hand, i, j);
            let bot_score = bot_suit_score(&bot);
            let strength = naive_mid_score(hand[i], hand[j]);
            // Deterministic tie-break by smallest card indices (inverted for lex-max).
            let key = (
                tier,
                bot_score,
                strength,
                u8::MAX - hand[i].index().min(hand[j].index()),
                u8::MAX - hand[i].index().max(hand[j].index()),
            );
            if key > best_key {
                best = (i, j);
                best_key = key;
            }
        }
    }
    build_setting_mid_then_top(&hand, best.0, best.1)
}

// --- Model 4: OmahaFirst ---------------------------------------------------

/// 4-card Omaha bot scoring (Fix c). Positive features: high cards, pairs,
/// connectivity, wheel draws. Negative: 3+ of a suit (wastes the Omaha 2+3
/// rule). Signed score so 4-flush / 3+1 can be strictly worse than rainbow.
pub fn omaha_bot_score(bot: &[Card; 4]) -> i32 {
    let mut score: i32 = 0;

    // High-card value: each rank > 8 adds (rank − 8) × 2.
    for c in bot {
        let r = c.rank() as i32;
        if r > 8 {
            score += (r - 8) * 2;
        }
    }

    // Pair / trip bonuses.
    let mut rank_counts = [0u8; 15];
    for c in bot {
        rank_counts[c.rank() as usize] += 1;
    }
    for r in 2..=14usize {
        match rank_counts[r] {
            2 => score += 15 + r as i32,
            3 => score += 30 + (r as i32) * 2,
            4 => score += 60 + (r as i32) * 3,
            _ => {}
        }
    }

    // Connectivity: longest run of consecutive distinct ranks.
    let mut ranks: Vec<u8> = bot.iter().map(|c| c.rank()).collect();
    ranks.sort_unstable();
    ranks.dedup();
    let mut max_run: i32 = 1;
    let mut cur: i32 = 1;
    for i in 1..ranks.len() {
        if ranks[i] == ranks[i - 1] + 1 {
            cur += 1;
            if cur > max_run {
                max_run = cur;
            }
        } else {
            cur = 1;
        }
    }
    score += max_run * 8;

    // Wheel draw: count of {A, 2, 3, 4, 5} in the bot.
    let mut wheel_count = 0;
    for c in bot {
        let r = c.rank();
        if r == 14 || (2..=5).contains(&r) {
            wheel_count += 1;
        }
    }
    if wheel_count >= 3 {
        score += 6;
    } else if wheel_count >= 2 {
        score += 3;
    }

    // Suit pattern.
    let mut sc = [0u8; 4];
    for c in bot {
        sc[c.suit() as usize] += 1;
    }
    let mut sorted = sc;
    sorted.sort_unstable_by(|a, b| b.cmp(a));
    let suit_bonus: i32 = match (sorted[0], sorted[1]) {
        (2, 2) => 14,  // DS
        (2, 1) => 7,   // SS
        (1, 1) => 0,   // rainbow
        (3, 1) => -4,  // 3+1 waste
        (4, 0) => -8,  // 4-flush waste
        _ => 0,
    };
    score + suit_bonus
}

/// Pick the 4-card bottom with the highest `omaha_bot_score`, then pick the
/// best 2-card middle from the remaining 3 (naive scoring), last card on top.
pub fn opp_omaha_first(hand: [Card; 7]) -> HandSetting {
    // Enumerate all C(7,4) = 35 bot choices.
    let mut best_bot: [usize; 4] = [0, 1, 2, 3];
    let mut best_score: i32 = i32::MIN;
    for a in 0..7 {
        for b in (a + 1)..7 {
            for c in (b + 1)..7 {
                for d in (c + 1)..7 {
                    let bot = [hand[a], hand[b], hand[c], hand[d]];
                    let s = omaha_bot_score(&bot);
                    // Lex tiebreak on the 4 indices so same-score options are
                    // deterministic: prefer smaller first index, etc.
                    if s > best_score
                        || (s == best_score && (a, b, c, d) < (best_bot[0], best_bot[1], best_bot[2], best_bot[3]))
                    {
                        best_score = s;
                        best_bot = [a, b, c, d];
                    }
                }
            }
        }
    }
    // Remaining 3 cards.
    let mut rem3 = [Card(0); 3];
    let mut k = 0;
    for x in 0..7 {
        if !best_bot.contains(&x) {
            rem3[k] = hand[x];
            k += 1;
        }
    }
    // Bug 3 fix (Decision 026): top = highest-rank of the 3 remaining cards
    // (index tie-break); mid = the other 2. The pre-fix behaviour picked the
    // best 2-card Hold'em mid from rem3 and left the leftover as top, which
    // could orphan a deuce on top while A-K sat in the mid.
    let mut top_i = 0usize;
    for i in 1..3 {
        let cur = rem3[i];
        let best = rem3[top_i];
        if cur.rank() > best.rank()
            || (cur.rank() == best.rank() && cur.index() > best.index())
        {
            top_i = i;
        }
    }
    let top = rem3[top_i];
    let (mi0, mi1) = match top_i {
        0 => (1, 2),
        1 => (0, 2),
        _ => (0, 1),
    };
    let mut mid = [rem3[mi0], rem3[mi1]];
    if mid[1].index() > mid[0].index() {
        mid.swap(0, 1);
    }
    let mut bot = [hand[best_bot[0]], hand[best_bot[1]], hand[best_bot[2]], hand[best_bot[3]]];
    bot.sort_unstable_by(|a, b| b.index().cmp(&a.index()));
    HandSetting { top, mid, bot }
}

// --- Model 5: TopDefensive -------------------------------------------------

/// Highest NON-PAIR-MEMBER card on top (Fix d). This preserves pocket pairs
/// for mid/bot rather than wasting an ace alone. If every card is a
/// pair-member (e.g. trips + two pairs), fall back to the highest-rank card.
pub fn opp_top_defensive(hand: [Card; 7]) -> HandSetting {
    // Rank multiplicity.
    let mut rc = [0u8; 15];
    for c in &hand {
        rc[c.rank() as usize] += 1;
    }
    // Collect "singleton" indices (cards whose rank appears exactly once).
    let mut singleton_indices: Vec<usize> = (0..7).filter(|&i| rc[hand[i].rank() as usize] == 1).collect();
    let top_i = if !singleton_indices.is_empty() {
        singleton_indices.sort_by(|&a, &b| {
            hand[b].rank().cmp(&hand[a].rank()).then(hand[b].index().cmp(&hand[a].index()))
        });
        singleton_indices[0]
    } else {
        // All paired: pick the highest-rank card overall (it'll orphan from a triple).
        (0..7)
            .max_by(|&a, &b| {
                hand[a]
                    .rank()
                    .cmp(&hand[b].rank())
                    .then(hand[a].index().cmp(&hand[b].index()))
            })
            .unwrap()
    };
    // Best mid from remaining 6 via naive score.
    let mut rem6 = [Card(0); 6];
    let mut rem_pos = [0usize; 6];
    let mut k = 0;
    for i in 0..7 {
        if i != top_i {
            rem6[k] = hand[i];
            rem_pos[k] = i;
            k += 1;
        }
    }
    let mut best = (0usize, 1usize);
    let mut best_score = naive_mid_score(rem6[0], rem6[1]);
    for a in 0..6 {
        for b in (a + 1)..6 {
            if (a, b) == (0, 1) {
                continue;
            }
            let s = naive_mid_score(rem6[a], rem6[b]);
            if s > best_score {
                best_score = s;
                best = (a, b);
            }
        }
    }
    let (ma, mb) = best;
    let mut mid = [rem6[ma], rem6[mb]];
    if mid[1].index() > mid[0].index() {
        mid.swap(0, 1);
    }
    let mut bot = [Card(0); 4];
    let mut bk = 0;
    for i in 0..6 {
        if i != ma && i != mb {
            bot[bk] = rem6[i];
            bk += 1;
        }
    }
    bot.sort_unstable_by(|a, b| b.index().cmp(&a.index()));
    HandSetting {
        top: hand[top_i],
        mid,
        bot,
    }
}

// --- Model 6: RandomWeighted -----------------------------------------------

/// Uniform over "reasonable" settings (top is in top-3 ranks; mid is a pair
/// or both broadway). Progressively relaxes on low rainbow hands (Fix e).
pub fn opp_random_weighted(hand: [Card; 7], rng: &mut SmallRng) -> HandSetting {
    let all = all_settings(hand);
    // top-3 highest ranks in the hand (as a set for O(1) containment check).
    let mut sorted_ranks: Vec<u8> = hand.iter().map(|c| c.rank()).collect();
    sorted_ranks.sort_unstable();
    sorted_ranks.dedup();
    sorted_ranks.reverse();
    let top_ranks: std::collections::BTreeSet<u8> = sorted_ranks.iter().take(3).copied().collect();

    let primary: Vec<&HandSetting> = all
        .iter()
        .filter(|s| {
            let top_ok = top_ranks.contains(&s.top.rank());
            let mid_is_pair = s.mid[0].rank() == s.mid[1].rank();
            let mid_broadway = s.mid[0].rank() >= 10 && s.mid[1].rank() >= 10;
            top_ok && (mid_is_pair || mid_broadway)
        })
        .collect();
    if primary.len() >= 3 {
        return *primary[rng.gen_range(0..primary.len())];
    }
    let relaxed: Vec<&HandSetting> = all
        .iter()
        .filter(|s| top_ranks.contains(&s.top.rank()))
        .collect();
    if relaxed.len() >= 3 {
        return *relaxed[rng.gen_range(0..relaxed.len())];
    }
    all[rng.gen_range(0..all.len())]
}

// --- Model 7: BalancedHeuristic --------------------------------------------

/// Weighted multi-tier scorer across all 105 candidate settings; picks the
/// setting with the highest weighted total. Weights: top×2.0, mid×4.0,
/// bot×2.5 (per the BalancedHeuristic spec, pending empirical calibration).
pub fn opp_balanced_heuristic(hand: [Card; 7]) -> HandSetting {
    let all = all_settings(hand);
    let mut best = all[0];
    let mut best_score = balanced_setting_score(&all[0]);
    for s in &all[1..] {
        let sc = balanced_setting_score(s);
        if sc > best_score {
            best_score = sc;
            best = *s;
        }
    }
    best
}

fn balanced_setting_score(s: &HandSetting) -> f64 {
    // Top tier: rank-based ladder.
    let top_score = match s.top.rank() {
        14 => 12.0,
        13 => 10.0,
        12 => 9.0,
        11 => 8.0,
        10 => 6.0,
        9 => 4.0,
        8 => 3.0,
        r => (r as f64 - 4.0).max(1.0),
    };
    // Middle tier: pair-or-connector scoring.
    let m0 = s.mid[0];
    let m1 = s.mid[1];
    let high = m0.rank().max(m1.rank());
    let low = m0.rank().min(m1.rank());
    let suited = m0.suit() == m1.suit();
    let mid_score = if high == low {
        50.0 + (high as f64) * 2.0
    } else {
        let mut x = (high as f64) * 1.5 + (low as f64) * 1.0;
        if suited {
            x += 5.0;
        }
        let gap = high - low;
        if gap == 1 {
            x += 6.0;
        } else if gap == 2 {
            x += 3.0;
        }
        if high == 14 {
            x += 4.0;
        }
        if low < 10 {
            x -= 2.0;
        }
        x
    };
    // Bottom tier: high cards + pairs + connectivity + suitedness.
    let mut bot_score = 0.0f64;
    for c in &s.bot {
        let r = c.rank() as f64;
        if r > 8.0 {
            bot_score += (r - 8.0) * 2.0;
        }
    }
    let mut rc = [0u8; 15];
    for c in &s.bot {
        rc[c.rank() as usize] += 1;
    }
    for r in 2..=14usize {
        if rc[r] >= 2 {
            bot_score += 12.0 + r as f64;
            if rc[r] >= 3 {
                bot_score += 10.0;
            }
        }
    }
    // Connectivity: longest run.
    let mut ranks: Vec<u8> = s.bot.iter().map(|c| c.rank()).collect();
    ranks.sort_unstable();
    ranks.dedup();
    let mut max_run = 1i32;
    let mut cur = 1i32;
    for i in 1..ranks.len() {
        if ranks[i] == ranks[i - 1] + 1 {
            cur += 1;
            if cur > max_run {
                max_run = cur;
            }
        } else {
            cur = 1;
        }
    }
    bot_score += max_run as f64 * 6.0;
    // Suitedness.
    let mut sc = [0u8; 4];
    for c in &s.bot {
        sc[c.suit() as usize] += 1;
    }
    let mut sorted = sc;
    sorted.sort_unstable_by(|a, b| b.cmp(a));
    bot_score += match (sorted[0], sorted[1]) {
        (2, 2) => 14.0,
        (2, 1) => 7.0,
        (1, 1) => 0.0,
        (3, 1) => 1.0,
        (4, 0) => -2.0,
        _ => 0.0,
    };
    top_score * 2.0 + mid_score * 4.0 + bot_score * 2.5
}

// --- Model 8: MfsuitTopLocked (Decision 043, Session 23) -------------------

/// Realistic-human "mfsuit-style with top defense" strategy with two hard
/// constraints derived from user observation of the actual playing population:
///
///   1. **Pocket pair from {AA, KK, QQ} → MID, never broken.** Highest takes
///      priority (AA > KK > QQ). The empirical Session-23 finding "AA-pair-to-mid
///      is essentially universal (oracle agrees 99.7%)" extends this rule to AA.
///   2. **Ace singleton → TOP.** Always — a lone Ace is never wasted in the bot.
///   3. **No Ace? → Omaha-bot first.** Pick the 4-card bot by `omaha_bot_score`,
///      top = highest singleton of remaining 3, mid = the other 2.
///
/// AA-to-bot ("rare exception, only with DS + decent pair available") and full
/// top/mid sacrifice ("~5% of population") are NOT modelled here — those cases
/// are covered by the 25% TopDefensive + 5% OmahaFirst slices of the realistic
/// mixture (`OpponentModel::RealisticHumanMixture`).
pub fn opp_mfsuit_top_locked(hand: [Card; 7]) -> HandSetting {
    // Rank counts.
    let mut rc = [0u8; 15];
    for c in &hand {
        rc[c.rank() as usize] += 1;
    }

    // 1. Highest pocket pair from {AA, KK, QQ} → mid.
    let mid_anchor_rank: Option<u8> = if rc[14] >= 2 {
        Some(14)
    } else if rc[13] >= 2 {
        Some(13)
    } else if rc[12] >= 2 {
        Some(12)
    } else {
        None
    };

    if let Some(rank) = mid_anchor_rank {
        // Take the two lowest-index cards of that rank for mid (deterministic).
        let mut chosen: Vec<usize> = (0..7).filter(|&i| hand[i].rank() == rank).collect();
        chosen.sort_unstable();
        let (mi, mj) = (chosen[0], chosen[1]);

        // Build rem5 and a parallel original-index map for the top selector.
        let mut rem5 = [Card(0); 5];
        let mut k = 0;
        for i in 0..7 {
            if i != mi && i != mj {
                rem5[k] = hand[i];
                k += 1;
            }
        }

        // Top rule: Ace singleton in rem5 → top.
        // (When mid_anchor_rank is 14 (AA), rem5 contains at most 1 ace if rc[14] == 3.)
        let mut rem5_rc = [0u8; 15];
        for c in &rem5 {
            rem5_rc[c.rank() as usize] += 1;
        }
        let top_i = if rem5_rc[14] == 1 {
            (0..5).find(|&i| rem5[i].rank() == 14).unwrap()
        } else {
            // Fallback: highest-rank singleton in rem5 (TopDefensive-style).
            pick_top_from_rem5(&rem5)
        };

        let top = rem5[top_i];
        let mut bot = [Card(0); 4];
        let mut bk = 0;
        for i in 0..5 {
            if i != top_i {
                bot[bk] = rem5[i];
                bk += 1;
            }
        }
        bot.sort_unstable_by(|a, b| b.index().cmp(&a.index()));

        let mut mid = [hand[mi], hand[mj]];
        if mid[1].index() > mid[0].index() {
            mid.swap(0, 1);
        }
        return HandSetting { top, mid, bot };
    }

    // 2. No AA/KK/QQ pair anchor.
    // If hand has an Ace singleton (rc[14] == 1), top = Ace, then optimize
    // Omaha bot from rem6, mid = the leftover 2.
    if rc[14] == 1 {
        let top_i = (0..7).find(|&i| hand[i].rank() == 14).unwrap();
        let mut rem6 = [Card(0); 6];
        let mut k = 0;
        for i in 0..7 {
            if i != top_i {
                rem6[k] = hand[i];
                k += 1;
            }
        }

        // Best 4-of-6 by omaha_bot_score, lex tiebreak.
        let mut best_bot = [0usize, 1, 2, 3];
        let mut best_score = i32::MIN;
        for a in 0..6 {
            for b in (a + 1)..6 {
                for c in (b + 1)..6 {
                    for d in (c + 1)..6 {
                        let bot = [rem6[a], rem6[b], rem6[c], rem6[d]];
                        let s = omaha_bot_score(&bot);
                        if s > best_score
                            || (s == best_score
                                && (a, b, c, d) < (best_bot[0], best_bot[1], best_bot[2], best_bot[3]))
                        {
                            best_score = s;
                            best_bot = [a, b, c, d];
                        }
                    }
                }
            }
        }

        let mut bot = [
            rem6[best_bot[0]],
            rem6[best_bot[1]],
            rem6[best_bot[2]],
            rem6[best_bot[3]],
        ];
        bot.sort_unstable_by(|a, b| b.index().cmp(&a.index()));

        // Mid = the 2 of rem6 not in best_bot.
        let mut mid_cards = [Card(0); 2];
        let mut mk = 0;
        for i in 0..6 {
            if !best_bot.contains(&i) {
                mid_cards[mk] = rem6[i];
                mk += 1;
            }
        }
        let mut mid = mid_cards;
        if mid[1].index() > mid[0].index() {
            mid.swap(0, 1);
        }

        return HandSetting {
            top: hand[top_i],
            mid,
            bot,
        };
    }

    // 3. No mid anchor + no Ace singleton (the "No Ace?" branch).
    // "Optimizes Omaha bot first; top gets the leftover." This is exactly the
    // OmahaFirst behaviour, so delegate.
    opp_omaha_first(hand)
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::card::parse_hand;

    fn seven(s: &str) -> [Card; 7] {
        let v = parse_hand(s).unwrap();
        [v[0], v[1], v[2], v[3], v[4], v[5], v[6]]
    }

    fn uses_all_7(s: &HandSetting, hand: [Card; 7]) {
        let all = s.all_cards();
        let got: std::collections::BTreeSet<_> = all.iter().copied().collect();
        let want: std::collections::BTreeSet<_> = hand.iter().copied().collect();
        assert_eq!(got, want, "setting does not use all 7 input cards");
    }

    // --- MFNaive --------------------------------------------------------------

    #[test]
    fn mfnaive_puts_aa_in_middle() {
        let hand = seven("As Ah Kd Qc Js 9h 3d");
        let s = opp_middle_first_naive(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 14);
        assert_eq!(s.mid[1].rank(), 14);
    }

    #[test]
    fn mfnaive_bot_sanity_avoids_four_flush_when_safe() {
        // AsKs Qs Js 2h 3c 4d: naive mid = AsKs (suited broadway). Top = Qs.
        // Naive bot = Js 2h 3c 4d: one spade → fine already.
        // Try harder: hand where naive would pick a non-pair mid AND leave 3+ of a suit.
        // "As Kh 9s 8s 7s 2d 3c" — mid = AsKh? non-pair, Ace bonus. bot = 9s 8s 7s +
        //   one of {2d, 3c} — wait remaining is 5 cards: 9s 8s 7s 2d 3c. Top = 9s (highest).
        //   bot = 8s 7s 2d 3c → 2 spades + 2 others, OK actually. Let me try:
        // "As Kh Qs Js Ts 3c 2d" — mid = AsKh (naive's top score, Ah bonus), top = Qs, bot = Js Ts 3c 2d → s,s,c,d → 2+1+1. Still OK.
        // Try: mid = QdJc (broadway offsuit), bot ends up 3-suited → verify sanity kicks in.
        // Simpler: "9s 8s 7s 6s Kh Qd Jc". No pair. Naive mid = KhQd (offsuit broadway).
        //   Top = Jc. Bot = 9s 8s 7s 6s → 4 spades (4-of-suit, worst).
        //   Sanity should swap lowest bot spade (6s) with lower mid card (Qd).
        //   After swap: mid = Kh 6s, bot = 9s 8s 7s Qd → 3 spades + 1 diamond → 3+1.
        //   Still bad but BETTER than 4-flush. Check that we moved toward better.
        let hand = seven("9s 8s 7s 6s Kh Qd Jc");
        let s = opp_middle_first_naive(hand);
        uses_all_7(&s, hand);
        let mut bc = [0u8; 4];
        for c in &s.bot {
            bc[c.suit() as usize] += 1;
        }
        let max_suit = *bc.iter().max().unwrap();
        assert!(max_suit <= 3, "bot should not be 4-flush after sanity; got counts {:?}", bc);
    }

    #[test]
    fn mfnaive_does_not_break_a_pair_for_sanity() {
        // Pair mid + 3-of-suit bot → sanity must NOT break the pair.
        let hand = seven("Ks Kh 9s 8s 7s 3c 2d");
        let s = opp_middle_first_naive(hand);
        uses_all_7(&s, hand);
        // KK should remain in middle.
        assert_eq!(s.mid[0].rank(), 13);
        assert_eq!(s.mid[1].rank(), 13);
    }

    // --- Bug 1 fix (pair preservation for top selection) ---------------------

    #[test]
    fn mfnaive_preserves_kk_on_aakk_hands() {
        // Bug 1 regression: on `As Ah Kd Kh 7s 4c 2d` the pre-fix MFNaive
        // set top=Kh, orphaning Kd into bot and breaking the KK pair. After
        // the fix, top must be the highest-rank SINGLETON in rem5 (the 7s),
        // preserving both AA in mid and KK in bot.
        let hand = seven("As Ah Kd Kh 7s 4c 2d");
        let s = opp_middle_first_naive(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.top.rank(), 7, "top must be the 7 (highest singleton), not a K or A");
        // AA must be in the mid.
        assert_eq!(s.mid[0].rank(), 14);
        assert_eq!(s.mid[1].rank(), 14);
        // KK must remain intact in the bot.
        let k_in_bot = s.bot.iter().filter(|c| c.rank() == 13).count();
        assert_eq!(k_in_bot, 2, "both Ks must be in bot; pair preserved");
    }

    #[test]
    fn mfsuitaware_preserves_kk_on_aakk_hands() {
        // Same regression for MFSuitAware. Because AA is tier 5 (pocket pair,
        // dominates every other tier), MFSuitAware must also choose AA for
        // mid here — and then the pair-preserving top rule applies.
        let hand = seven("As Ah Kd Kh 7s 4c 2d");
        let s = opp_middle_first_suit_aware(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.top.rank(), 7, "top must be the 7, not a K or A");
        assert_eq!(s.mid[0].rank(), 14);
        assert_eq!(s.mid[1].rank(), 14);
        let k_in_bot = s.bot.iter().filter(|c| c.rank() == 13).count();
        assert_eq!(k_in_bot, 2, "both Ks must remain in bot");
    }

    #[test]
    fn topdefensive_preserves_pairs_on_aakk_redux() {
        // TopDefensive already had pair-preservation logic pre-Bug-1, but
        // we re-assert it here alongside the MF tests so a single regression
        // run shows all four of the pair-preserving archetype members.
        let hand = seven("As Ah Kd Kh 7s 4c 2d");
        let s = opp_top_defensive(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.top.rank(), 7, "TopDefensive top must be the highest singleton (7)");
        // Neither AA nor KK should be broken (top is singleton 7).
        let a_outside_top = s.mid.iter().chain(s.bot.iter()).filter(|c| c.rank() == 14).count();
        let k_outside_top = s.mid.iter().chain(s.bot.iter()).filter(|c| c.rank() == 13).count();
        assert_eq!(a_outside_top, 2, "AA must stay intact (both Aces in mid or bot)");
        assert_eq!(k_outside_top, 2, "KK must stay intact (both Kings in mid or bot)");
    }

    // --- Bug 3 fix (OmahaFirst top = highest of remaining 3) ------------------

    #[test]
    fn omahafirst_picks_highest_remaining_for_top() {
        // Bug 3 regression: on `As Kh Qd Jc Ts 9h 2d` pre-fix picked the
        // best 2-card mid from the 3 cards not in the bot and left the
        // leftover as top — which could be the 2d when the As and Kh were
        // both available. After the fix, top must be the highest-rank card
        // among the 3 non-bot cards (never the 2d when broadway cards are
        // available).
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let s = opp_omaha_first(hand);
        uses_all_7(&s, hand);
        assert_ne!(s.top.rank(), 2, "top must not be the deuce");
        // Derive the 3 cards not in the bot and check top is the highest.
        let bot_set: std::collections::BTreeSet<_> = s.bot.iter().copied().collect();
        let rem3: Vec<Card> = hand.iter().copied().filter(|c| !bot_set.contains(c)).collect();
        assert_eq!(rem3.len(), 3);
        let max_rank = rem3.iter().map(|c| c.rank()).max().unwrap();
        assert_eq!(s.top.rank(), max_rank, "top must be the highest rank of the 3 non-bot cards");
    }

    #[test]
    fn omahafirst_top_is_highest_of_remaining_three_stress() {
        // Broader hand (three 7s, AKQJT2) where bot is likely to take the
        // wheel-less broadway set; whatever the bot picks, top must be the
        // highest rank in rem3.
        let hand = seven("As Kd Qc Jh 7s 7d 7h");
        let s = opp_omaha_first(hand);
        uses_all_7(&s, hand);
        let bot_set: std::collections::BTreeSet<_> = s.bot.iter().copied().collect();
        let rem3: Vec<Card> = hand.iter().copied().filter(|c| !bot_set.contains(c)).collect();
        let max_rank = rem3.iter().map(|c| c.rank()).max().unwrap();
        assert_eq!(s.top.rank(), max_rank);
    }

    // --- MFSuitAware ---------------------------------------------------------

    #[test]
    fn mfsuitaware_prefers_same_tier_bot_improvement() {
        // Hand: As Ks Ah Qh Jc Tc 2d. Top-tier mid candidates include AsKs
        // (suited broadway). No same-rank-pair AA because As+Ah is a pair — at
        // tier 5, dominates. Different test needed.
        // Use three-of-kind candidates tied at tier 5 with differing bot suit.
        let hand = seven("Ks Qd 7s 7d 7h 4c 2d");
        let s = opp_middle_first_suit_aware(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 7);
        assert_eq!(s.mid[1].rank(), 7);
        let mid_suits: std::collections::BTreeSet<u8> = s.mid.iter().map(|c| c.suit()).collect();
        // 7s7h gives 3-of-diamonds bot (BAD). Must avoid: mid must not contain both 7s and 7h.
        assert!(
            !(mid_suits.contains(&3) && mid_suits.contains(&2)),
            "mfsuitaware picked 7s+7h, leaving a 3+1 bot; got {} {}",
            s.mid[0], s.mid[1]
        );
    }

    #[test]
    fn mfsuitaware_is_deterministic() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let s1 = opp_middle_first_suit_aware(hand);
        let s2 = opp_middle_first_suit_aware(hand);
        assert_eq!(s1, s2);
    }

    // --- OmahaFirst -----------------------------------------------------------

    #[test]
    fn omahafirst_favors_double_suited_bot() {
        // Hand with exactly two 2-card suit groups in hole + 3 other singletons.
        // "As Ts Kh 9h 3c 5d 7c" — we have 2 spades, 2 hearts, 2 clubs, 1 diamond.
        // Best 4-card bot: pick 2 from one pair + 2 from another → 2+2 DS.
        // Candidates: {As, Ts, Kh, 9h} — 2+2 DS with broadway ranks.
        let hand = seven("As Ts Kh 9h 3c 5d 7c");
        let s = opp_omaha_first(hand);
        uses_all_7(&s, hand);
        let mut bc = [0u8; 4];
        for c in &s.bot {
            bc[c.suit() as usize] += 1;
        }
        let mut sorted = bc;
        sorted.sort_unstable_by(|a, b| b.cmp(a));
        assert_eq!(sorted[0], 2, "bot should be double-suited (2+2); counts {:?}", bc);
        assert_eq!(sorted[1], 2);
    }

    #[test]
    fn omahafirst_wheel_hand_uses_wheel_in_bot() {
        // Hand with A + 2345 + 2 junk cards. The wheel draw should go to bot.
        let hand = seven("Ad 2c 3d 4h 5s Kc 9h");
        let s = opp_omaha_first(hand);
        uses_all_7(&s, hand);
        let bot_ranks: std::collections::BTreeSet<u8> = s.bot.iter().map(|c| c.rank()).collect();
        // Bot should contain at least 3 of {A, 2, 3, 4, 5} to exploit the wheel bonus.
        let wheel_in_bot = bot_ranks
            .iter()
            .filter(|&&r| r == 14 || (2..=5).contains(&r))
            .count();
        assert!(wheel_in_bot >= 3, "expected wheel-rich bot, got ranks {:?}", bot_ranks);
    }

    // --- TopDefensive --------------------------------------------------------

    #[test]
    fn topdefensive_aakk_puts_kicker_on_top() {
        // AAKK + 7 4 2: non-pair-members are 7, 4, 2 → highest (7) goes top.
        let hand = seven("As Ac Kh Kd 7c 4h 2s");
        let s = opp_top_defensive(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.top.rank(), 7, "top must be the kicker (7), not an A or K");
    }

    #[test]
    fn topdefensive_plain_hand_uses_highest_card() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let s = opp_top_defensive(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.top.rank(), 14, "no pairs → highest card (A) on top");
    }

    // --- RandomWeighted ------------------------------------------------------

    #[test]
    fn randomweighted_respects_filter_on_broadway_hand() {
        use rand::SeedableRng;
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let mut rng = SmallRng::seed_from_u64(42);
        for _ in 0..50 {
            let s = opp_random_weighted(hand, &mut rng);
            uses_all_7(&s, hand);
            // Top should be in top-3 ranks (A, K, Q).
            assert!(
                matches!(s.top.rank(), 14 | 13 | 12),
                "top {} not in top-3 ranks",
                s.top
            );
            // Mid is pair or both T+.
            let is_pair = s.mid[0].rank() == s.mid[1].rank();
            let both_broadway = s.mid[0].rank() >= 10 && s.mid[1].rank() >= 10;
            assert!(is_pair || both_broadway, "mid {} {} fails filter", s.mid[0], s.mid[1]);
        }
    }

    #[test]
    fn randomweighted_falls_back_on_low_rainbow() {
        // 2c 3d 4h 5s 6c 7d 8h — no broadway, no pair. Primary filter yields 0.
        // Relaxed (top must be in top-3 ranks = 8, 7, 6) should still yield > 3 settings.
        use rand::SeedableRng;
        let hand = seven("2c 3d 4h 5s 6c 7d 8h");
        let mut rng = SmallRng::seed_from_u64(7);
        let s = opp_random_weighted(hand, &mut rng);
        uses_all_7(&s, hand);
        // Top should be in top-3 ranks of this hand: 8, 7, 6.
        assert!(
            matches!(s.top.rank(), 8 | 7 | 6),
            "fallback should still put top in top-3 ranks; got {}",
            s.top
        );
    }

    // --- BalancedHeuristic ---------------------------------------------------

    #[test]
    fn balanced_returns_a_valid_setting() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let s = opp_balanced_heuristic(hand);
        uses_all_7(&s, hand);
    }

    #[test]
    fn balanced_picks_pair_mid_for_aakk_hand() {
        let hand = seven("As Ac Kh Kd 7c 4h 2s");
        let s = opp_balanced_heuristic(hand);
        uses_all_7(&s, hand);
        // Either AA or KK should be in the middle (both are premium pairs).
        let mid_is_pair = s.mid[0].rank() == s.mid[1].rank();
        assert!(mid_is_pair, "balanced should pick a pocket pair for mid on AAKK hand");
    }

    // --- MfsuitTopLocked (Decision 043) --------------------------------------

    #[test]
    fn locked_kk_with_ace_singleton_puts_kk_mid_ace_top() {
        // KK + Ace singleton + 4 junk → KK mid, A top, 4 junk bot.
        let hand = seven("Ks Kh Ad 9c 7s 4h 2c");
        let s = opp_mfsuit_top_locked(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 13);
        assert_eq!(s.mid[1].rank(), 13);
        assert_eq!(s.top.rank(), 14, "Ace singleton must go to top");
    }

    #[test]
    fn locked_qq_with_ace_singleton_puts_qq_mid_ace_top() {
        let hand = seven("Qs Qh Ad Jc 7s 4h 2c");
        let s = opp_mfsuit_top_locked(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 12);
        assert_eq!(s.mid[1].rank(), 12);
        assert_eq!(s.top.rank(), 14);
    }

    #[test]
    fn locked_aa_kk_puts_aa_mid_kk_split() {
        // AA > KK priority — AA goes mid, KK splits between top/bot.
        // (Session 23 finding: AA-to-mid is empirically near-universal.)
        let hand = seven("As Ah Kd Kc 7s 4h 2c");
        let s = opp_mfsuit_top_locked(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 14, "AA wins priority over KK for mid anchor");
        assert_eq!(s.mid[1].rank(), 14);
        // No Ace singleton in rem5 → top picked by topdef-style fallback (highest singleton = 7).
        assert_eq!(s.top.rank(), 7, "top from highest singleton in rem5");
    }

    #[test]
    fn locked_kk_qq_puts_kk_mid_qq_split() {
        // KK > QQ priority. With both, KK to mid, QQ disperses.
        let hand = seven("Ks Kh Qd Qc 9s 4h 2c");
        let s = opp_mfsuit_top_locked(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 13);
        assert_eq!(s.mid[1].rank(), 13);
        // No ace singleton in rem5 (rem5 = QQ957 essentially with suits) — top by highest singleton.
        // Singletons in rem5 are 9, 4, 2. Highest = 9.
        assert_eq!(s.top.rank(), 9, "top must be highest singleton (9), not a Q (paired)");
    }

    #[test]
    fn locked_no_pair_no_ace_falls_through_to_omaha() {
        // No AKQ pair, no ace at all → behaves like OmahaFirst.
        let hand = seven("Ks Td 9c 8s 7h 5d 3c");
        let s = opp_mfsuit_top_locked(hand);
        let s_omaha = opp_omaha_first(hand);
        uses_all_7(&s, hand);
        assert_eq!(s, s_omaha, "no anchor + no ace → identical to OmahaFirst");
    }

    #[test]
    fn locked_ace_singleton_no_pair_optimizes_bot_then_mid() {
        // Ace singleton, no AKQ pair → top = A, optimize bot from rem6.
        let hand = seven("As Ts 9c 8h 7d 5c 3h");
        let s = opp_mfsuit_top_locked(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.top.rank(), 14, "lone Ace must be on top");
        // 7 in mid+bot is fine — just check determinism.
        let s2 = opp_mfsuit_top_locked(hand);
        assert_eq!(s, s2, "must be deterministic");
    }

    #[test]
    fn locked_kk_no_ace_picks_topdef_style_top() {
        // KK + no ace → KK mid, top from rem5 by highest singleton (TopDefensive style).
        let hand = seven("Ks Kh Td 9c 7s 4h 2c");
        let s = opp_mfsuit_top_locked(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 13);
        assert_eq!(s.mid[1].rank(), 13);
        // rem5 = T 9 7 4 2 — all singletons; highest = T.
        assert_eq!(s.top.rank(), 10, "top should be the T (highest singleton in rem5)");
    }

    #[test]
    fn locked_aa_no_kkqq_no_ace_singleton_keeps_aa_mid() {
        // AA + 5 non-A non-KQ cards. Even without an Ace singleton, AA stays mid.
        let hand = seven("As Ad 9h 7c 5s 3d 2h");
        let s = opp_mfsuit_top_locked(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 14);
        assert_eq!(s.mid[1].rank(), 14);
        // No Ace singleton in rem5 → top = highest singleton = 9.
        assert_eq!(s.top.rank(), 9);
    }

    #[test]
    fn locked_is_deterministic() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let s1 = opp_mfsuit_top_locked(hand);
        let s2 = opp_mfsuit_top_locked(hand);
        assert_eq!(s1, s2);
    }

    #[test]
    fn locked_handles_trips_of_kings() {
        // KKK + 4 junk: mid takes 2 Ks, third K is loose.
        let hand = seven("Ks Kh Kd 9c 7s 4h 2c");
        let s = opp_mfsuit_top_locked(hand);
        uses_all_7(&s, hand);
        assert_eq!(s.mid[0].rank(), 13);
        assert_eq!(s.mid[1].rank(), 13);
        // The third K must be in top or bot. With no ace singleton, rem5 = K + 4 junk;
        // pick_top_from_rem5 picks the highest-rank singleton (one of 9, 7, 4, 2; the K is
        // not a singleton in rem5? wait — only 1 K in rem5, so it IS a singleton). The
        // K is the highest singleton → top.
        assert_eq!(s.top.rank(), 13, "lone third K should go top as highest singleton");
    }
}
