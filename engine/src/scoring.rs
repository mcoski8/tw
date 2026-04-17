//! Scoring: compare two `HandSetting`s across two community boards.
//!
//! Six matchups total (3 tiers × 2 boards). Point values per matchup:
//!   - Top: 1, Middle: 2, Bottom (Omaha): 3.
//! Max non-scoop total is 12 per board pair. Chops (equal ranks) award 0 to
//! both. If one player wins ALL 6 matchups with ZERO chops, scoop → (+20, -20)
//! or (-20, +20). Any single chop invalidates the scoop and normal scoring
//! applies (Decision 004 / scoring-system.md).

use crate::card::Card;
use crate::holdem_eval::{eval_middle, eval_top};
use crate::omaha_eval::eval_omaha;
use crate::hand_eval::Evaluator;
use crate::setting::HandSetting;

pub const PTS_TOP: i32 = 1;
pub const PTS_MID: i32 = 2;
pub const PTS_BOT: i32 = 3;
pub const SCOOP_POINTS: i32 = 20;

/// Per-tier, per-board outcome on a single matchup.
#[derive(Copy, Clone, Eq, PartialEq, Debug)]
pub enum Outcome {
    P1Wins,
    P2Wins,
    Chop,
}

/// Full breakdown of a matchup. Useful for debugging and for the trainer's
/// explanation view (Sprint 5). Ordered [top_b1, top_b2, mid_b1, mid_b2,
/// bot_b1, bot_b2].
#[derive(Copy, Clone, Debug)]
pub struct MatchupBreakdown {
    pub outcomes: [Outcome; 6],
    pub p1_points: i32,
    pub p2_points: i32,
    pub scooped: bool,
}

/// Convenience: just the final points (p1, p2). Always sums to zero.
#[inline]
pub fn score_matchup(
    ev: &Evaluator,
    p1: &HandSetting,
    p2: &HandSetting,
    board1: &[Card; 5],
    board2: &[Card; 5],
) -> (i32, i32) {
    let br = matchup_breakdown(ev, p1, p2, board1, board2);
    (br.p1_points, br.p2_points)
}

/// Full 6-matchup breakdown with scoop detection.
pub fn matchup_breakdown(
    ev: &Evaluator,
    p1: &HandSetting,
    p2: &HandSetting,
    board1: &[Card; 5],
    board2: &[Card; 5],
) -> MatchupBreakdown {
    // Evaluate each tier on each board for both players. Order matters for
    // the outcomes[] array: [top_b1, top_b2, mid_b1, mid_b2, bot_b1, bot_b2].
    let p1_top_b1 = eval_top(ev, p1.top, *board1);
    let p1_top_b2 = eval_top(ev, p1.top, *board2);
    let p1_mid_b1 = eval_middle(ev, p1.mid, *board1);
    let p1_mid_b2 = eval_middle(ev, p1.mid, *board2);
    let p1_bot_b1 = eval_omaha(ev, p1.bot, *board1);
    let p1_bot_b2 = eval_omaha(ev, p1.bot, *board2);

    let p2_top_b1 = eval_top(ev, p2.top, *board1);
    let p2_top_b2 = eval_top(ev, p2.top, *board2);
    let p2_mid_b1 = eval_middle(ev, p2.mid, *board1);
    let p2_mid_b2 = eval_middle(ev, p2.mid, *board2);
    let p2_bot_b1 = eval_omaha(ev, p2.bot, *board1);
    let p2_bot_b2 = eval_omaha(ev, p2.bot, *board2);

    let pairs = [
        (p1_top_b1, p2_top_b1, PTS_TOP),
        (p1_top_b2, p2_top_b2, PTS_TOP),
        (p1_mid_b1, p2_mid_b1, PTS_MID),
        (p1_mid_b2, p2_mid_b2, PTS_MID),
        (p1_bot_b1, p2_bot_b1, PTS_BOT),
        (p1_bot_b2, p2_bot_b2, PTS_BOT),
    ];

    let mut outcomes = [Outcome::Chop; 6];
    let mut p1_normal = 0i32;
    let mut p2_normal = 0i32;
    let mut p1_wins = 0i32;
    let mut p2_wins = 0i32;
    let mut chops = 0i32;

    for (i, &(a, b, pts)) in pairs.iter().enumerate() {
        if a > b {
            outcomes[i] = Outcome::P1Wins;
            p1_normal += pts;
            p1_wins += 1;
        } else if b > a {
            outcomes[i] = Outcome::P2Wins;
            p2_normal += pts;
            p2_wins += 1;
        } else {
            outcomes[i] = Outcome::Chop;
            chops += 1;
        }
    }

    // Scoop rule: 6 wins AND 0 chops. Any chop — even on a matchup the
    // scooping player "would have" won — invalidates the scoop.
    let scooped = chops == 0 && (p1_wins == 6 || p2_wins == 6);
    if scooped {
        if p1_wins == 6 {
            MatchupBreakdown {
                outcomes,
                p1_points: SCOOP_POINTS,
                p2_points: -SCOOP_POINTS,
                scooped: true,
            }
        } else {
            MatchupBreakdown {
                outcomes,
                p1_points: -SCOOP_POINTS,
                p2_points: SCOOP_POINTS,
                scooped: true,
            }
        }
    } else {
        // Net-points form: each player's score is what they won minus what
        // the opponent won, so the pair always sums to zero.
        MatchupBreakdown {
            outcomes,
            p1_points: p1_normal - p2_normal,
            p2_points: p2_normal - p1_normal,
            scooped: false,
        }
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::card::{parse_hand, Card};

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

    #[test]
    fn identical_settings_chop_all_six_zero_points() {
        let ev = Evaluator::build();
        // Two identical settings with two identical boards. Every matchup is a
        // chop → zero points each, no scoop.
        let p = mk("As", "Kc", "Kd", "Qc", "Qd", "Jc", "Jd");
        let board1 = b5("2c 3d 4h 5s 7c");
        let board2 = b5("9c Th Jc Qs Kd");
        let br = matchup_breakdown(&ev, &p, &p, &board1, &board2);
        assert_eq!((br.p1_points, br.p2_points), (0, 0));
        assert!(!br.scooped);
        assert!(br.outcomes.iter().all(|&o| o == Outcome::Chop));
    }

    #[test]
    fn sums_to_zero_in_all_branches() {
        // Randomly-chosen but fixed settings + boards. Regardless of outcome,
        // p1 + p2 must always sum to 0.
        let ev = Evaluator::build();
        let p1 = mk("As", "Kc", "Kd", "Qc", "Qd", "Jc", "Jd");
        let p2 = mk("2d", "3c", "4d", "5c", "6d", "7c", "8d");
        let board1 = b5("Tc 9h 8s 7d 2h");
        let board2 = b5("Ah Kh Qh Jh Th");
        let br = matchup_breakdown(&ev, &p1, &p2, &board1, &board2);
        assert_eq!(br.p1_points + br.p2_points, 0);
    }
}
