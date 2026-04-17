//! Dedicated Omaha evaluator integration tests.
//!
//! Focus: the 2-from-hand + 3-from-board rule is the #1 bug source in any
//! Omaha implementation, so every case here is designed to fail loudly if the
//! enforcement is wrong — especially the "the hand would be a flush/straight
//! under Hold'em rules but is NOT under the 2+3 rule" cases.

use tw_engine::hand_eval::{
    category, CAT_FLUSH, CAT_FULL_HOUSE, CAT_HIGH, CAT_PAIR, CAT_QUADS, CAT_STRAIGHT,
    CAT_STRAIGHT_FLUSH, CAT_TRIPS, CAT_TWO_PAIR,
};
use tw_engine::{eval_omaha, parse_hand, Card, Evaluator};

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
fn four_suited_hole_three_suited_board_allows_flush() {
    let ev = Evaluator::build();
    // 4 spades in hole, 3 spades on board = legal flush (2 hole + 3 board).
    // AK hole + T98 board → A-K-T-9-8 spade flush.
    let hole = h4("As Ks Qs Js");
    let board = b5("Ts 9s 8s 2c 3d");
    let r = eval_omaha(&ev, hole, board);
    // Best is actually Q-J-T-9-8 spade straight flush (QJ from hole + T98 board).
    assert_eq!(category(r), CAT_STRAIGHT_FLUSH);
}

#[test]
fn four_suited_hole_two_suited_board_is_NOT_flush() {
    let ev = Evaluator::build();
    // Hole 4 spades, board has only 2 spades → need 3 board spades for flush,
    // we don't have them. Best is non-flush.
    let hole = h4("As Ks Qs Js");
    let board = b5("Ts 9s 8c 7d 2h");
    let r = eval_omaha(&ev, hole, board);
    assert!(
        category(r) != CAT_FLUSH && category(r) != CAT_STRAIGHT_FLUSH,
        "only 2 board spades → cannot complete 5-card flush under 2+3 rule"
    );
    // Best available: QJ hole + T98 board → Q-J-T-9-8 straight.
    assert_eq!(category(r), CAT_STRAIGHT);
}

#[test]
fn four_to_straight_on_board_one_hole_connector_does_not_make_straight() {
    let ev = Evaluator::build();
    // Board 6789K — four to a straight. Only a Ten completes the 6-7-8-9-T
    // straight. Hole T + 3 junk: we'd need T + 4 board cards = 1 hole + 4
    // board, which violates 2+3.
    let hole = h4("Tc 2d 3h 4s");
    let board = b5("6c 7d 8h 9s Kc");
    let r = eval_omaha(&ev, hole, board);
    assert!(
        category(r) != CAT_STRAIGHT,
        "single connector in hole cannot bridge a 4-card board straight under 2+3"
    );
    // Best here: 34 hole + 678 board → 3-4-5-6-7-8 straight? We need 5 in
    // hand OR board — neither present. So best is 89K + any 2 hole → pair
    // check: no pair. High card K.
    assert_eq!(category(r), CAT_HIGH);
}

#[test]
fn four_to_straight_on_board_two_hole_connectors_makes_straight() {
    let ev = Evaluator::build();
    // Same board, hole has BOTH connectors. TJ hole + 789 board → 7-8-9-T-J.
    let hole = h4("Tc Jd 2h 3s");
    let board = b5("6c 7d 8h 9s Kc");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_STRAIGHT);
}

#[test]
fn quads_in_hole_impossible_best_is_two_pair() {
    let ev = Evaluator::build();
    // Hole: four aces. Board: 22 33 K. 2+3 rule caps hole usage at 2, so no
    // quads of aces. Best two hole = AA; pick any 3 board. AA + 22K → two
    // pair (A over 2, K kicker).
    let hole = h4("Ac Ad Ah As");
    let board = b5("2c 2d 3h 3s Kc");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_TWO_PAIR);
}

#[test]
fn quads_achievable_with_pair_in_hole_plus_pair_on_board() {
    let ev = Evaluator::build();
    // Need quads of X: pair of X in hole + pair of X on board = 4 X's, but
    // we can only use 2 hole + 3 board, so we use both hole X's + both
    // board X's = 4 X's total; 5th card is any other board card. Legal.
    // AA hole + AA on board → 4 aces + kicker.
    let hole = h4("Ac Ad 2s 3s");
    let board = b5("Ah As Kc 7d 4h");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_QUADS);
}

#[test]
fn trips_on_board_plus_pair_in_hole_is_full_house() {
    let ev = Evaluator::build();
    // Board has AAA; hole has KK. 2+3 rule: KK hole + AAA board = aces full
    // of kings.
    let hole = h4("Kc Kd 2s 3c");
    let board = b5("Ac Ad Ah 4s 5d");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_FULL_HOUSE);
}

#[test]
fn one_ace_in_hole_plus_trip_board_gives_quads() {
    let ev = Evaluator::build();
    // Subtle 2+3 win case: hole has only ONE ace, board has AAA. We still
    // make QUADS by picking "ace + kicker" from hole (2 cards) and all 3
    // board aces (3 cards). Total: 1 hole ace + 3 board aces = 4 aces.
    // A common mental-model bug is thinking we'd need 2 hole aces for quads
    // — this test pins that down.
    let hole = h4("Ac 2s 3c 4d");
    let board = b5("Ad Ah As 9c 7d");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_QUADS);
}

#[test]
fn zero_aces_in_hole_and_trip_aces_on_board_is_trips_max() {
    let ev = Evaluator::build();
    // Now the true "can't complete quads" case: no aces in hole at all, only
    // trip aces on the board. 2+3 forces 3 board cards at most, so at best
    // we grab AAA + 2 hole cards → trips with hole kickers.
    let hole = h4("Kc Qs 2s 3c");
    let board = b5("Ad Ah As 9c 7d");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_TRIPS);
}

#[test]
fn wheel_through_2_plus_3() {
    let ev = Evaluator::build();
    // Hole: A,2 and junk. Board: 3,4,5,K,Q. A-2 hole + 3-4-5 board = wheel.
    let hole = h4("As 2d 9c 9h");
    let board = b5("3h 4c 5s Kd Qc");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_STRAIGHT);
}

#[test]
fn pair_in_hole_pair_on_board_makes_two_pair() {
    let ev = Evaluator::build();
    // Hole: KK + junk. Board: 77 + 3 kickers. Best: KK + 77 + board kicker.
    let hole = h4("Kc Kd 2s 3h");
    let board = b5("7c 7d 9h Jc 4s");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_TWO_PAIR);
}

#[test]
fn trips_in_hole_becomes_pair_not_trips() {
    let ev = Evaluator::build();
    // Hole JJJ + 5. Board has no J. 2+3 means we can use at most 2 J's.
    // Result: pair of jacks with board kickers — NOT trips.
    let hole = h4("Jc Jd Jh 5s");
    let board = b5("4c 9d Kh Qs 3d");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_PAIR);
}

#[test]
fn cannot_use_four_from_hole_even_if_better() {
    let ev = Evaluator::build();
    // Straight-like hole: 3c 4c 5c 6c (4 consecutive cards, all clubs). Board:
    // Ac Kc 9d Ts 2h (no help for straight or flush completion). In Hold'em
    // we'd have a 4-card straight + potential straight flush. In Omaha under
    // 2+3, we can use only 2 of the 4 connected cards. Best: pair check...
    // nope, no pairs. Best is high card using 2 hole + AKT from board =
    // A-K-T-6-5 or A-K-T-6-4 etc. Must be HIGH card (no pair, no straight,
    // no flush under 2+3 since we have only 2 clubs in any hand + 2 clubs
    // on board = 4 clubs max but need 5; wait, 2 hole clubs + 2 board clubs
    // = 4, need 3 from board for flush, only 2 board clubs present).
    let hole = h4("3c 4c 5c 6c");
    let board = b5("Ac Kc 9d Ts 2h");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_HIGH);
}

#[test]
fn straight_flush_via_2_plus_3_correctly_detected() {
    let ev = Evaluator::build();
    // Hole has Ts Js (two spades, adjacent). Board has 7s 8s 9s + 2 junk →
    // three board spades, all part of 7-8-9. Together JT + 987s → 7-T
    // straight flush (7-8-9-T-J, all spades).
    let hole = h4("Ts Js 2c 3d");
    let board = b5("7s 8s 9s 4c Kd");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_STRAIGHT_FLUSH);
}

#[test]
fn flush_better_than_straight_via_2_plus_3() {
    let ev = Evaluator::build();
    // Hole: As 2s Kc 3d. Board: 7s 9s Js 8c 6h.
    // - Flush option: As 2s hole + 7s 9s Js board → A-J-9-7-2 spade flush.
    // - Straight option: need 5-consecutive. Board has 6,7,8,9,J. Hole has
    //   2,3. No T → no straight.
    // Best: A-J-9-7-2 spade flush.
    let hole = h4("As 2s Kc 3d");
    let board = b5("7s 9s Js 8c 6h");
    let r = eval_omaha(&ev, hole, board);
    assert_eq!(category(r), CAT_FLUSH);
}
