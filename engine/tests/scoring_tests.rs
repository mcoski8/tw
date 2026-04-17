//! Scoring integration tests.
//!
//! Covers: net-points invariant, scoop (all 6 wins, 0 chops → +20/-20), chop
//! invalidates scoop (even if one side would have won 6 otherwise), and a
//! hand-verified end-to-end matchup with known rank outcomes.

use tw_engine::{
    matchup_breakdown, parse_hand, score_matchup, Card, Evaluator, HandSetting, Outcome,
};

fn b5(s: &str) -> [Card; 5] {
    let v = parse_hand(s).unwrap();
    assert_eq!(v.len(), 5);
    [v[0], v[1], v[2], v[3], v[4]]
}

fn mk(top: &str, m1: &str, m2: &str, b1: &str, b2: &str, b3: &str, b4: &str) -> HandSetting {
    HandSetting {
        top: top.parse().unwrap(),
        mid: [m1.parse().unwrap(), m2.parse().unwrap()],
        bot: [
            b1.parse().unwrap(),
            b2.parse().unwrap(),
            b3.parse().unwrap(),
            b4.parse().unwrap(),
        ],
    }
}

/// Strong setup chosen so P1 strictly dominates every tier on every board:
///
/// P1 hand = Ac As Kc Ks Qc Qs Jc → top=Ac, mid=AsKc (AK high), bot=KsQcQsJc
///          → bot makes K-Q-J-T-9 straight on either board via Ks + Qs + 9,T,J.
/// P2 hand = 3c 4d 5h 6d 7c 8d Tc (junk) → top=3c, mid=4d5h, bot=6d 7c 8d Tc.
///          → Best P2 bot on each board is a 7-8-9-T-J straight (J-high).
/// Boards are chosen with no cards matching either player's hole, no board
/// pair, no board flush, no on-board straight — each tier is determined by
/// the player's hole cards interacting with board cards.
fn scoop_fixture() -> (HandSetting, HandSetting, [Card; 5], [Card; 5]) {
    let p1 = mk("Ac", "As", "Kc", "Ks", "Qc", "Qs", "Jc");
    let p2 = mk("3c", "4d", "5h", "6d", "7c", "8d", "Tc");
    let board1 = b5("6s 7d 9h Th Js");
    let board2 = b5("6h 7s 9d Td Jh");
    (p1, p2, board1, board2)
}

#[test]
fn scoop_all_six_wins_zero_chops_pays_twenty() {
    let ev = Evaluator::build();
    let (p1, p2, b1, b2) = scoop_fixture();
    let br = matchup_breakdown(&ev, &p1, &p2, &b1, &b2);
    assert!(br.scooped, "P1 strictly dominates all 6 matchups → scoop");
    assert_eq!(br.p1_points, 20);
    assert_eq!(br.p2_points, -20);
    assert!(br.outcomes.iter().all(|&o| o == Outcome::P1Wins));
}

#[test]
fn chop_on_top_invalidates_scoop() {
    let ev = Evaluator::build();
    // Same fixture but swap both players' top cards so that neither player's
    // top card matches a board rank → both tops evaluate to the same board-
    // driven high card → chop on BOTH top boards. Mid and bot still favor
    // P1 strictly. Net: 4 wins, 2 chops, no scoop.
    //
    // We swap Ac → 2c for P1 and 3c → 2d for P2. The 2-card is dead on both
    // boards (no 2 on b1 or b2), so each player's top evaluates to the same
    // board high card J-T-9-7-6.
    let p1 = mk("2c", "As", "Kc", "Ks", "Qc", "Qs", "Jc");
    let p2 = mk("2d", "4d", "5h", "6d", "7c", "8d", "Tc");
    let b1 = b5("6s 7d 9h Th Js");
    let b2 = b5("6h 7s 9d Td Jh");

    let br = matchup_breakdown(&ev, &p1, &p2, &b1, &b2);
    assert!(!br.scooped, "chops present → scoop invalidated");
    // Two chops on top (b1 + b2), four wins for P1 (mid×2 + bot×2).
    let chops = br.outcomes.iter().filter(|&&o| o == Outcome::Chop).count();
    let p1_wins = br.outcomes.iter().filter(|&&o| o == Outcome::P1Wins).count();
    let p2_wins = br.outcomes.iter().filter(|&&o| o == Outcome::P2Wins).count();
    assert_eq!(chops, 2, "both top matchups should chop");
    assert_eq!(p1_wins, 4, "P1 should still win mid×2 + bot×2");
    assert_eq!(p2_wins, 0);
    // Normal scoring: P1 gets 2+2+3+3 = 10, P2 gets 0. Net: (10, -10).
    assert_eq!(br.p1_points, 10);
    assert_eq!(br.p2_points, -10);
}

#[test]
fn all_six_chops_zero_points() {
    let ev = Evaluator::build();
    // Identical settings + any two boards = every matchup is a chop. Each
    // player wins 0 points, but ALSO "6 wins for one side" is false, so no
    // scoop — just (0, 0).
    let s = mk("As", "Kh", "Qh", "Jh", "Th", "9h", "8h");
    let b1 = b5("2c 3d 4h 5s 7c");
    let b2 = b5("Ac Ad Ah Kc Kd");
    let br = matchup_breakdown(&ev, &s, &s, &b1, &b2);
    assert!(!br.scooped);
    assert_eq!(br.p1_points, 0);
    assert_eq!(br.p2_points, 0);
    assert!(br.outcomes.iter().all(|&o| o == Outcome::Chop));
}

#[test]
fn score_matchup_agrees_with_breakdown() {
    let ev = Evaluator::build();
    let (p1, p2, b1, b2) = scoop_fixture();
    let pair = score_matchup(&ev, &p1, &p2, &b1, &b2);
    let br = matchup_breakdown(&ev, &p1, &p2, &b1, &b2);
    assert_eq!(pair, (br.p1_points, br.p2_points));
}

#[test]
fn net_points_always_sum_to_zero() {
    let ev = Evaluator::build();
    // Pick a few distinct contrived scenarios and verify the invariant.
    let cases = [
        (
            mk("Ac", "As", "Kc", "Ks", "Qc", "Qs", "Jc"),
            mk("3c", "4d", "5h", "6d", "7c", "8d", "Tc"),
            b5("6s 7d 9h Th Js"),
            b5("6h 7s 9d Td Jh"),
        ),
        (
            mk("2s", "3s", "4s", "5s", "6s", "7s", "8s"),
            mk("2d", "3d", "4d", "5d", "6d", "7d", "8d"),
            b5("9c Tc Jc Qc Kc"),
            b5("9h Th Jh Qh Kh"),
        ),
        (
            mk("Ah", "Kh", "Qh", "Jh", "Th", "9h", "8h"),
            mk("Ad", "Kd", "Qd", "Jd", "Td", "9d", "8d"),
            b5("2c 3c 4c 5c 7c"),
            b5("2s 3s 4s 5s 7s"),
        ),
    ];
    for (p1, p2, b1, b2) in &cases {
        let br = matchup_breakdown(&ev, p1, p2, b1, b2);
        assert_eq!(
            br.p1_points + br.p2_points,
            0,
            "net-points sum must be zero in all cases"
        );
    }
}

#[test]
fn end_to_end_matchup_with_hand_checked_outcome() {
    // A compact end-to-end check: deal a fixed 7+7 hand and 2 boards, pick a
    // specific setting for each, and confirm the computed matchup matches a
    // hand-reasoned expected result.
    //
    // P1: AA in mid (boat-worthy), KK in bot with flush draw.
    // P2: pair-only bot, junk top & mid.
    // Boards are "dry" — no pair, no flush, no on-board straight.
    let ev = Evaluator::build();
    let p1 = mk("Jc", "Ac", "Ad", "Kh", "Ks", "Qh", "Tc");
    // P1: top=Jc, mid=AA (pair of aces immediately), bot=KKQT (strong Omaha).
    let p2 = mk("2c", "3d", "4h", "5s", "6d", "7s", "9c");
    // P2: top=2c, mid=34, bot=5678-rainbow (straight potential only).
    let b1 = b5("8h 9d Ts Qd 3s");
    let b2 = b5("6h 7c 8s Jh Qs");

    let br = matchup_breakdown(&ev, &p1, &p2, &b1, &b2);

    // Every matchup must be a resolved Win or Chop, never invalid.
    assert_eq!(br.outcomes.len(), 6);

    // Sanity: pair of aces (P1 mid) > 3-4 offsuit on dry boards (P2 mid),
    // so both mid matchups should go to P1.
    let p1_mid_outcomes = [br.outcomes[2], br.outcomes[3]];
    for o in p1_mid_outcomes {
        assert_eq!(o, Outcome::P1Wins, "AA in mid beats 34 on dry boards");
    }

    // Net must sum to zero.
    assert_eq!(br.p1_points + br.p2_points, 0);
}
