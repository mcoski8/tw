//! Integration tests for the 5-card hand evaluator and all_settings.
//! These run against the built lookup table (not just the direct-compute
//! function), so they exercise colex indexing + table storage end-to-end.

use tw_engine::{all_settings, category, compute_rank_5, parse_hand, Card, Evaluator, NUM_SETTINGS};
use tw_engine::hand_eval::{
    CAT_FLUSH, CAT_FULL_HOUSE, CAT_HIGH, CAT_PAIR, CAT_QUADS, CAT_STRAIGHT, CAT_STRAIGHT_FLUSH,
    CAT_TRIPS, CAT_TWO_PAIR,
};

fn h(s: &str) -> [Card; 5] {
    let v = parse_hand(s).unwrap();
    assert_eq!(v.len(), 5);
    [v[0], v[1], v[2], v[3], v[4]]
}

fn seven(s: &str) -> [Card; 7] {
    let v = parse_hand(s).unwrap();
    assert_eq!(v.len(), 7);
    [v[0], v[1], v[2], v[3], v[4], v[5], v[6]]
}

#[test]
fn table_lookup_matches_direct_on_every_hand() {
    // Build the table, then walk every 5-card combination and confirm the
    // stored rank equals a fresh direct computation. This is the strongest
    // possible correctness check for the table + indexing.
    let ev = Evaluator::build();
    let mut idx = [0u8, 1, 2, 3, 4];
    let mut count = 0usize;
    loop {
        let cards = [
            Card::from_index(idx[0]),
            Card::from_index(idx[1]),
            Card::from_index(idx[2]),
            Card::from_index(idx[3]),
            Card::from_index(idx[4]),
        ];
        let stored = ev.eval_5(cards);
        let direct = compute_rank_5(cards);
        assert_eq!(
            stored, direct,
            "mismatch at {:?}: stored {:x}, direct {:x}",
            idx, stored, direct
        );
        count += 1;

        let mut i = 5;
        let mut bumped = false;
        while i > 0 {
            i -= 1;
            if (idx[i] as usize) + (5 - i) < 52 {
                idx[i] += 1;
                for j in (i + 1)..5 {
                    idx[j] = idx[j - 1] + 1;
                }
                bumped = true;
                break;
            }
        }
        if !bumped {
            break;
        }
    }
    assert_eq!(count, 2_598_960);
}

#[test]
fn royal_flush_is_highest() {
    let royal = compute_rank_5(h("As Ks Qs Js Ts"));
    // There's no higher 5-card hand than a royal flush.
    assert_eq!(category(royal), CAT_STRAIGHT_FLUSH);
    // And it must beat a straight flush.
    let sf = compute_rank_5(h("9s 8s 7s 6s 5s"));
    assert!(royal > sf);
}

#[test]
fn straight_flush_beats_quads() {
    assert!(compute_rank_5(h("9s 8s 7s 6s 5s")) > compute_rank_5(h("Ac Ad Ah As Kd")));
}

#[test]
fn quads_beats_full_house() {
    assert!(compute_rank_5(h("Ac Ad Ah As 2d")) > compute_rank_5(h("Kc Kd Kh As Ad")));
    assert_eq!(category(compute_rank_5(h("Ac Ad Ah As 2d"))), CAT_QUADS);
    assert_eq!(category(compute_rank_5(h("Kc Kd Kh As Ad"))), CAT_FULL_HOUSE);
}

#[test]
fn full_house_trip_dominates_pair() {
    let aaa_kk = compute_rank_5(h("Ac Ad Ah Ks Kd"));
    let kkk_aa = compute_rank_5(h("Kc Kd Kh As Ad"));
    assert!(aaa_kk > kkk_aa);
}

#[test]
fn flush_beats_straight() {
    assert!(compute_rank_5(h("As 2s 5s 7s 9s")) > compute_rank_5(h("As Kd Qh Jc Th")));
    assert_eq!(category(compute_rank_5(h("As 2s 5s 7s 9s"))), CAT_FLUSH);
    assert_eq!(category(compute_rank_5(h("As Kd Qh Jc Th"))), CAT_STRAIGHT);
}

#[test]
fn flush_kickers_full_cascade() {
    let a_high_1 = compute_rank_5(h("As Ks Qs Js 9s"));
    let a_high_2 = compute_rank_5(h("As Ks Qs Js 8s"));
    let a_high_3 = compute_rank_5(h("As Ks Qs Ts 8s"));
    let a_high_4 = compute_rank_5(h("As Ks Js Ts 8s"));
    let a_high_5 = compute_rank_5(h("As Qs Js Ts 8s"));
    let k_high = compute_rank_5(h("Ks Qs Js Ts 8s"));
    assert!(a_high_1 > a_high_2);
    assert!(a_high_2 > a_high_3);
    assert!(a_high_3 > a_high_4);
    assert!(a_high_4 > a_high_5);
    assert!(a_high_5 > k_high);
}

#[test]
fn wheel_is_lowest_straight_not_ace_high() {
    let wheel = compute_rank_5(h("As 2d 3h 4c 5s"));
    let six_high = compute_rank_5(h("2s 3d 4h 5c 6s"));
    let broadway = compute_rank_5(h("As Kd Qh Jc Th"));
    assert_eq!(category(wheel), CAT_STRAIGHT);
    assert!(wheel < six_high, "wheel must be lowest straight");
    assert!(broadway > wheel);
}

#[test]
fn steel_wheel_is_lowest_straight_flush() {
    let steel = compute_rank_5(h("As 2s 3s 4s 5s"));
    let six_high_sf = compute_rank_5(h("2s 3s 4s 5s 6s"));
    let royal = compute_rank_5(h("As Ks Qs Js Ts"));
    assert_eq!(category(steel), CAT_STRAIGHT_FLUSH);
    assert!(steel < six_high_sf);
    assert!(royal > steel);
}

#[test]
fn two_pair_top_then_bottom_then_kicker() {
    let aa_kk_q = compute_rank_5(h("As Ad Ks Kd Qc"));
    let aa_kk_2 = compute_rank_5(h("As Ad Ks Kd 2c"));
    let aa_qq_k = compute_rank_5(h("As Ad Qs Qd Kc"));
    let kk_qq_a = compute_rank_5(h("Ks Kd Qs Qd Ac"));
    assert!(aa_kk_q > aa_kk_2, "kicker breaks tie");
    assert!(aa_kk_2 > aa_qq_k, "top pair beats top pair");
    assert!(aa_qq_k > kk_qq_a, "top pair > top pair even with higher kicker");
    assert_eq!(category(aa_kk_q), CAT_TWO_PAIR);
}

#[test]
fn one_pair_kickers_all_three_matter() {
    let pair_q = compute_rank_5(h("Qs Qd 9s 7d 5c"));
    let pair_q_big_kick = compute_rank_5(h("Qs Qd As 7d 5c"));
    assert!(pair_q_big_kick > pair_q);

    let pair_q_k1 = compute_rank_5(h("Qs Qd Ks Jd 5c"));
    let pair_q_k2 = compute_rank_5(h("Qs Qd Ks Td 5c"));
    let pair_q_k3 = compute_rank_5(h("Qs Qd Ks Jd 4c"));
    assert!(pair_q_k1 > pair_q_k2, "second kicker matters");
    assert!(pair_q_k1 > pair_q_k3, "third kicker matters");
    assert_eq!(category(pair_q_k1), CAT_PAIR);
}

#[test]
fn high_card_kickers_matter_down_to_fifth() {
    let ak_q_j_9 = compute_rank_5(h("As Kd Qh Jc 9h"));
    let ak_q_j_8 = compute_rank_5(h("As Kd Qh Jc 8h"));
    assert!(ak_q_j_9 > ak_q_j_8);
    assert_eq!(category(ak_q_j_9), CAT_HIGH);
}

#[test]
fn trips_over_two_pair() {
    assert!(compute_rank_5(h("9s 9d 9h Kc 2h")) > compute_rank_5(h("As Ad Ks Kd 2c")));
    assert_eq!(category(compute_rank_5(h("9s 9d 9h Kc 2h"))), CAT_TRIPS);
}

#[test]
fn all_settings_returns_exactly_105() {
    let hand = seven("As Kh Qd Jc Ts 9h 2d");
    assert_eq!(all_settings(hand).len(), NUM_SETTINGS);
}

#[test]
fn every_setting_partitions_the_seven_cards() {
    let hand = seven("As Kh Qd Jc Ts 9h 2d");
    let input: std::collections::BTreeSet<_> = hand.iter().copied().collect();
    assert_eq!(input.len(), 7);
    for s in all_settings(hand) {
        let got: std::collections::BTreeSet<_> = s.all_cards().iter().copied().collect();
        assert_eq!(got.len(), 7, "duplicate card in setting: {}", s);
        assert_eq!(got, input, "setting does not use the input hand");
    }
}
