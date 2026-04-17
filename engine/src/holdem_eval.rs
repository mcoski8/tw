//! Hold'em-style tier evaluators.
//!
//! - `eval_top`: 1 hole card + 5 board cards → best 5 of 6 (C(6,5) = 6 lookups).
//! - `eval_middle`: 2 hole cards + 5 board cards → best 5 of 7 (C(7,5) = 21 lookups).
//!
//! Both are pure functions layered directly on top of `Evaluator::eval_5`. No
//! allocations, stack-only buffers, so the same code works in any parallel or
//! GPU backend (Decision 011 / Sprint 0 compute-pipeline notes).

use crate::card::Card;
use crate::hand_eval::{Evaluator, HandRank};

/// Top tier: enumerate the 6 five-card subsets of {hole + 5 board} and return
/// the strongest rank. Each "subset" corresponds to dropping one of the 6
/// cards, so we iterate `drop_i in 0..6` and fill the other 5 slots.
#[inline]
pub fn eval_top(ev: &Evaluator, hole: Card, board: [Card; 5]) -> HandRank {
    let six: [Card; 6] = [hole, board[0], board[1], board[2], board[3], board[4]];
    let mut best: HandRank = 0;
    let mut drop_i = 0usize;
    while drop_i < 6 {
        let mut five = [Card(0); 5];
        let mut k = 0usize;
        let mut i = 0usize;
        while i < 6 {
            if i != drop_i {
                five[k] = six[i];
                k += 1;
            }
            i += 1;
        }
        let r = ev.eval_5(five);
        if r > best {
            best = r;
        }
        drop_i += 1;
    }
    best
}

/// Middle tier: standard Texas Hold'em. Best 5 of 7, C(7,5) = 21 five-card
/// hands. Equivalent to dropping 2 cards out of 7, so we iterate all C(7,2) =
/// 21 pairs of drop indices.
#[inline]
pub fn eval_middle(ev: &Evaluator, hole: [Card; 2], board: [Card; 5]) -> HandRank {
    let seven: [Card; 7] = [
        hole[0], hole[1], board[0], board[1], board[2], board[3], board[4],
    ];
    let mut best: HandRank = 0;
    let mut a = 0usize;
    while a < 7 {
        let mut b = a + 1;
        while b < 7 {
            let mut five = [Card(0); 5];
            let mut k = 0usize;
            let mut i = 0usize;
            while i < 7 {
                if i != a && i != b {
                    five[k] = seven[i];
                    k += 1;
                }
                i += 1;
            }
            let r = ev.eval_5(five);
            if r > best {
                best = r;
            }
            b += 1;
        }
        a += 1;
    }
    best
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::card::parse_hand;
    use crate::hand_eval::{category, CAT_FLUSH, CAT_PAIR, CAT_STRAIGHT, CAT_TRIPS};

    fn b5(s: &str) -> [Card; 5] {
        let v = parse_hand(s).unwrap();
        assert_eq!(v.len(), 5);
        [v[0], v[1], v[2], v[3], v[4]]
    }

    fn c(s: &str) -> Card {
        s.parse().unwrap()
    }

    #[test]
    fn top_ace_with_broadway_board_is_straight() {
        // A + K Q J T 2 → A-high straight using AKQJT.
        let ev = Evaluator::build();
        let r = eval_top(&ev, c("As"), b5("Kd Qh Jc Ts 2c"));
        assert_eq!(category(r), CAT_STRAIGHT);
    }

    #[test]
    fn top_seven_with_77_board_is_trips() {
        // 7 + 7 7 K Q 3 → 777 trips with K, Q kickers.
        let ev = Evaluator::build();
        let r = eval_top(&ev, c("7s"), b5("7h 7d Kc Qs 3c"));
        assert_eq!(category(r), CAT_TRIPS);
    }

    #[test]
    fn top_prefers_hole_card_when_it_helps() {
        // Hole Ac + board of Ks Qs Js Ts 2s. Board alone is K-high flush. With
        // Ac in the hand, best 5 of 6 is still the K-high flush (Ac doesn't
        // match the spade flush), so rank should match board-alone.
        let ev = Evaluator::build();
        let board = b5("Ks Qs Js Ts 2s");
        let board_rank = ev.eval_5(board);
        let r = eval_top(&ev, c("Ac"), board);
        assert_eq!(r, board_rank);
        assert_eq!(category(r), CAT_FLUSH);
    }

    #[test]
    fn middle_aa_on_broadway_board_is_pair_of_aces() {
        // AA + K Q J 3 2 → best 5 is AA + KQJ kickers.
        let ev = Evaluator::build();
        let r = eval_middle(&ev, [c("Ac"), c("Ad")], b5("Ks Qs Js 3c 2d"));
        assert_eq!(category(r), CAT_PAIR);
    }

    #[test]
    fn middle_87s_on_654ak_is_straight() {
        // 8s 7s + 6s 5h 4d Ac Kc → 4-5-6-7-8 straight.
        let ev = Evaluator::build();
        let r = eval_middle(&ev, [c("8s"), c("7s")], b5("6s 5h 4d Ac Kc"));
        assert_eq!(category(r), CAT_STRAIGHT);
    }

    #[test]
    fn middle_uses_board_only_when_board_wins() {
        // Hole 2c 3d + board K K K 7 7 (full house on the board). The hole
        // cards can't improve on KKK77, so result == board's rank.
        let ev = Evaluator::build();
        let board = b5("Kc Kd Kh 7s 7d");
        let board_rank = ev.eval_5(board);
        let r = eval_middle(&ev, [c("2c"), c("3d")], board);
        assert_eq!(r, board_rank);
    }
}
