//! Omaha bottom-tier evaluator.
//!
//! THE rule: use EXACTLY 2 from the 4-card hole + EXACTLY 3 from the 5-card
//! board — never 1 or 3 or 4 from hole. This is the #1 source of bugs in any
//! Omaha implementation. The algorithm is an unrolled double loop:
//!   - C(4,2) = 6 hole-pair choices (pre-enumerated as a const table)
//!   - C(5,3) = 10 board-triple choices (equivalently: drop 2 of 5 from board)
//! Total = 60 `eval_5` lookups; return the max rank.
//!
//! The hole-pair indices are pre-enumerated rather than computed from a
//! double loop — it's 6 fixed pairs, lifting them out of the inner loop means
//! the compiler can keep the two hole cards in registers across all 10 board
//! triples (see compute-pipeline.md "Lookup Table Optimization" note).

use crate::card::Card;
use crate::hand_eval::{Evaluator, HandRank};

/// All 6 pairs of indices into a 4-card hole, in lex order.
const HOLE_PAIRS: [(u8, u8); 6] = [(0, 1), (0, 2), (0, 3), (1, 2), (1, 3), (2, 3)];

/// All 10 pairs of indices to DROP from a 5-card board (equivalently: choose
/// 3 of 5 to keep). Kept as drop-indices because it's trivial to emit the
/// surviving 3 cards by skipping those positions in a single pass.
const BOARD_DROPS: [(u8, u8); 10] = [
    (0, 1), (0, 2), (0, 3), (0, 4),
    (1, 2), (1, 3), (1, 4),
    (2, 3), (2, 4),
    (3, 4),
];

/// Omaha evaluation with the strict 2+3 rule. Pure function: 60 lookups, no
/// allocations.
#[inline]
pub fn eval_omaha(ev: &Evaluator, hole: [Card; 4], board: [Card; 5]) -> HandRank {
    let mut best: HandRank = 0;
    // For each of the 6 hole pairs, try each of the 10 board triples.
    let mut p = 0usize;
    while p < HOLE_PAIRS.len() {
        let (hi, hj) = HOLE_PAIRS[p];
        let h0 = hole[hi as usize];
        let h1 = hole[hj as usize];

        let mut d = 0usize;
        while d < BOARD_DROPS.len() {
            let (di, dj) = BOARD_DROPS[d];
            // Pick the 3 board cards whose positions are NOT di or dj.
            let mut five = [h0, h1, Card(0), Card(0), Card(0)];
            let mut k = 2usize;
            let mut i = 0u8;
            while i < 5 {
                if i != di && i != dj {
                    five[k] = board[i as usize];
                    k += 1;
                }
                i += 1;
            }
            let r = ev.eval_5(five);
            if r > best {
                best = r;
            }
            d += 1;
        }
        p += 1;
    }
    best
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::card::parse_hand;
    use crate::hand_eval::{
        category, CAT_FLUSH, CAT_PAIR, CAT_STRAIGHT, CAT_STRAIGHT_FLUSH, CAT_TRIPS,
    };

    fn b5(s: &str) -> [Card; 5] {
        let v = parse_hand(s).unwrap();
        assert_eq!(v.len(), 5);
        [v[0], v[1], v[2], v[3], v[4]]
    }

    fn h4(s: &str) -> [Card; 4] {
        let v = parse_hand(s).unwrap();
        assert_eq!(v.len(), 4);
        [v[0], v[1], v[2], v[3]]
    }

    #[test]
    fn four_suited_hole_with_three_suited_board_makes_flush() {
        // Hole: As Ks Qs Js (four spades). Board: Ts 9s 8s 2c 3d (three spades
        // + two offsuit). In Hold'em this is a royal flush. In Omaha we can
        // only use 2 hole spades + 3 board spades — still a flush.
        let ev = Evaluator::build();
        let hole = h4("As Ks Qs Js");
        let board = b5("Ts 9s 8s 2c 3d");
        let r = eval_omaha(&ev, hole, board);
        // Best: pick AK from hole (highest 2) + T98 from board → A-K-T-9-8
        // royal/straight check: not a straight (A-K gap), just a flush.
        assert!(
            category(r) == CAT_FLUSH || category(r) == CAT_STRAIGHT_FLUSH,
            "expected flush/SF, got category {}",
            category(r)
        );
    }

    #[test]
    fn four_suited_hole_with_zero_suited_board_is_not_a_flush() {
        // Hole 4 spades, board has 0 spades → impossible to get a 5-card flush
        // under the 2+3 rule.
        let ev = Evaluator::build();
        let hole = h4("As Ks Qs Js");
        let board = b5("Tc 9c 8c 2d 3d");
        let r = eval_omaha(&ev, hole, board);
        // Not a flush — just high card at best.
        assert!(
            category(r) != CAT_FLUSH && category(r) != CAT_STRAIGHT_FLUSH,
            "must NOT be a flush (2+3 rule violated otherwise)"
        );
    }

    #[test]
    fn four_suited_hole_with_four_suited_board_still_flush_from_2plus3() {
        // Hole: As Ks Qs Js. Board: Ts 9s 8s 7s 3d (four spades). The 2+3
        // rule means we pick 2 spades from hole and 3 spades from board —
        // still a flush. The board's 4th spade goes unused.
        let ev = Evaluator::build();
        let hole = h4("As Ks Qs Js");
        let board = b5("Ts 9s 8s 7s 3d");
        let r = eval_omaha(&ev, hole, board);
        // Best five spades: AKTS9S8S → a flush, NOT a straight flush (A-K-T-9-8
        // is not consecutive; A is not connected to KTs under straight rules,
        // and we need 5 consecutive). But QsJs + Ts9s8s = Q-J-T-9-8 straight
        // flush! Let's verify that's possible and therefore preferred.
        // In fact QJTs + 98s from board = Q,J,T,9,8 spades → straight flush.
        assert_eq!(
            category(r),
            CAT_STRAIGHT_FLUSH,
            "QJ hole + T98 board → Q-high straight flush"
        );
    }

    #[test]
    fn four_straight_board_needs_2_hole_to_complete() {
        // Board has 4 cards to a straight (6 7 8 9 + K). In Omaha we need 2
        // from hole + 3 from board — so a hole with a single "T" does NOT
        // make a straight. Verify: hole Tc 2c 3d 4h → should NOT be a straight.
        let ev = Evaluator::build();
        let hole = h4("Tc 2c 3d 4h");
        let board = b5("6s 7s 8h 9d Kc");
        let r = eval_omaha(&ev, hole, board);
        assert!(
            category(r) != CAT_STRAIGHT,
            "1 hole card cannot complete a straight under 2+3"
        );

        // But hole Tc Jd + board 6789K → use TJ from hole + 789 from board →
        // 7-8-9-T-J straight. Verify this case works.
        let hole2 = h4("Tc Jd 2c 3h");
        let r2 = eval_omaha(&ev, hole2, board);
        assert_eq!(category(r2), CAT_STRAIGHT);
    }

    #[test]
    fn trips_in_hand_can_only_use_two() {
        // Hole JJJ5. Board: 4c 5d 9h Kc Qs (one pair of 5s forms w/ hand's 5).
        // Under 2+3 rule: best is JJ (from hole, 2 of the 3 jacks) + 3 board
        // → pair of jacks with board kickers. We can NOT make trips of J
        // because only 2 jacks can come from hand and no board card is a J.
        let ev = Evaluator::build();
        let hole = h4("Jc Jd Jh 5s");
        let board = b5("4c 5d 9h Kc Qs");
        let r = eval_omaha(&ev, hole, board);
        // Best should be two pair: JJ + 55 (55 via 5s hole + 5d board — but
        // that's only 1 hole 5 + 1 board 5 = 2 cards, we still need 3 more
        // from board and 1 more from hole). Wait: 2+3 means pick exactly 2
        // hole + exactly 3 board. Options:
        //   - JJ hole + 5d-KQ board → pair of J with K kicker
        //   - J5 hole + 5d-KQ board → two pair JJ? No, only 1 J on board.
        //     Actually J5(hole) + 5d9hKc(board) = J-5-5-9-K → pair of 5s w/ J
        //   - J5 hole + 4c5d9h(board) = pair of 5s, J-9-4 kickers.
        // Nothing makes two pair, no way to get trips. So best is pair of
        // jacks (JJ from hole) with K-Q-9 kickers. Category: PAIR.
        assert_eq!(
            category(r),
            CAT_PAIR,
            "cannot make trips of J with only 2-from-hand"
        );
    }

    #[test]
    fn trips_on_board_becomes_trips_via_hand_pair() {
        // Board AAA24 (trips on board). In Hold'em best 5 of 7 with any hand
        // makes trips at minimum. In Omaha: must use 2 hole + 3 board. To use
        // the trip aces from board we'd need 3 board cards (the 3 A's) + 2
        // hole cards — that's legal. With hole KK we get AAAKK = full house.
        let ev = Evaluator::build();
        let hole = h4("Kc Kd 2s 3d");
        let board = b5("Ac Ad Ah 4s 5c");
        let r = eval_omaha(&ev, hole, board);
        // Best: KK hole + AAA board → aces-full-of-kings full house.
        use crate::hand_eval::CAT_FULL_HOUSE;
        assert_eq!(category(r), CAT_FULL_HOUSE);
    }

    #[test]
    fn wheel_straight_via_2plus3() {
        // Hole As 2d + board 3h 4c 5s Kd Qc → A-2-3-4-5 wheel using 2 hole
        // + 3 board.
        let ev = Evaluator::build();
        let hole = h4("As 2d 9c 9d");
        let board = b5("3h 4c 5s Kd Qc");
        let r = eval_omaha(&ev, hole, board);
        // Wheel is a straight.
        assert_eq!(category(r), CAT_STRAIGHT);
    }

    #[test]
    fn all_hole_required_no_board_only_hand() {
        // Hole: AAAA (four aces). Board: 22222? Can't exist. Use 2233K for
        // board instead. Under 2+3 rule, using 4 aces from hole is ILLEGAL.
        // Best we can do is AA hole + 3 board → two pair AA + 22 (or 33).
        let ev = Evaluator::build();
        let hole = h4("Ac Ad Ah As");
        let board = b5("2c 2d 3h 3s Kc");
        let r = eval_omaha(&ev, hole, board);
        use crate::hand_eval::CAT_TWO_PAIR;
        // AA + 22/33 → two pair.  Could also be AA + 33K → two pair (AA,33,K).
        // Could NOT be quads (would need 4 hole aces).
        assert_eq!(
            category(r),
            CAT_TWO_PAIR,
            "cannot use 4 aces from hole — two pair is the best"
        );
    }

    #[test]
    fn trips_requires_pair_in_hand_or_board() {
        // Hole JJ9h8c, board: JhKcQs2d3c. Under 2+3 we can use JJ hole + any 3
        // board. Best: JJ + KQ-something → JJJ? Only 1 J on board + 2 J in
        // hole = 3 J's. But that needs exactly 2 J from hole (yes, JJ) and 1
        // J from board — the other 2 board cards come from {K,Q,2,3}. So
        // JJ + JhKQ → JJJ with KQ kickers → trips.
        let ev = Evaluator::build();
        let hole = h4("Jc Jd 9h 8c");
        let board = b5("Jh Kc Qs 2d 3c");
        let r = eval_omaha(&ev, hole, board);
        assert_eq!(category(r), CAT_TRIPS);
    }
}
