//! HandSetting: a specific arrangement of a 7-card hand into 3 tiers.
//!
//! The game rule: 1 card top, 2 cards middle, 4 cards bottom. The bottom plays
//! as Omaha (must use exactly 2 from hand + 3 from board) — that rule belongs
//! to the evaluator, not here. This module just enumerates the 105 possible
//! arrangements: C(7,1) ways to pick the top × C(6,2) ways to pick the middle
//! = 7 × 15 = 105. The remaining 4 cards fill the bottom.

use std::fmt;

use crate::card::Card;

/// One arrangement of a 7-card hand. Slots are kept sorted within each tier
/// for stable display and to make test equality checks easier.
#[derive(Copy, Clone, Eq, PartialEq, Debug)]
pub struct HandSetting {
    pub top: Card,
    pub mid: [Card; 2],
    pub bot: [Card; 4],
}

impl HandSetting {
    /// Return every card in the setting as a 7-element array for validation.
    pub fn all_cards(&self) -> [Card; 7] {
        [
            self.top,
            self.mid[0], self.mid[1],
            self.bot[0], self.bot[1], self.bot[2], self.bot[3],
        ]
    }
}

impl fmt::Display for HandSetting {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(
            f,
            "top [{}]  mid [{} {}]  bot [{} {} {} {}]",
            self.top,
            self.mid[0], self.mid[1],
            self.bot[0], self.bot[1], self.bot[2], self.bot[3],
        )
    }
}

pub const NUM_SETTINGS: usize = 105;

/// Enumerate all 105 ways to split a 7-card hand into (top=1, mid=2, bot=4).
///
/// Each tier is emitted with its cards sorted descending by card index, so
/// output is deterministic regardless of input order.
pub fn all_settings(hand: [Card; 7]) -> Vec<HandSetting> {
    let mut out = Vec::with_capacity(NUM_SETTINGS);

    for top_i in 0..7 {
        // Cards remaining after picking the top.
        let mut remaining6 = [Card(0); 6];
        let mut k = 0;
        for i in 0..7 {
            if i == top_i {
                continue;
            }
            remaining6[k] = hand[i];
            k += 1;
        }

        // Choose 2 of the remaining 6 for middle.
        for a in 0..6 {
            for b in (a + 1)..6 {
                let mut mid = [remaining6[a], remaining6[b]];
                sort_desc(&mut mid);

                // Bottom is the other 4.
                let mut bot = [Card(0); 4];
                let mut bk = 0;
                for j in 0..6 {
                    if j == a || j == b {
                        continue;
                    }
                    bot[bk] = remaining6[j];
                    bk += 1;
                }
                sort_desc(&mut bot);

                out.push(HandSetting {
                    top: hand[top_i],
                    mid,
                    bot,
                });
            }
        }
    }

    debug_assert_eq!(out.len(), NUM_SETTINGS);
    out
}

fn sort_desc(xs: &mut [Card]) {
    xs.sort_unstable_by(|a, b| b.0.cmp(&a.0));
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::card::parse_hand;

    fn seven(s: &str) -> [Card; 7] {
        let v = parse_hand(s).unwrap();
        assert_eq!(v.len(), 7);
        [v[0], v[1], v[2], v[3], v[4], v[5], v[6]]
    }

    #[test]
    fn exactly_105_settings() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let settings = all_settings(hand);
        assert_eq!(settings.len(), NUM_SETTINGS);
    }

    #[test]
    fn every_setting_uses_all_7_cards_once() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let settings = all_settings(hand);
        let input: std::collections::BTreeSet<_> = hand.iter().copied().collect();
        assert_eq!(input.len(), 7, "input hand has duplicate cards");

        for s in &settings {
            let got: std::collections::BTreeSet<_> = s.all_cards().iter().copied().collect();
            assert_eq!(got.len(), 7, "setting contains a duplicate card: {}", s);
            assert_eq!(got, input, "setting uses different cards: {}", s);
        }
    }

    #[test]
    fn settings_are_unique() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let settings = all_settings(hand);
        let mut seen = std::collections::HashSet::new();
        for s in &settings {
            let key = (s.top.0, s.mid, s.bot);
            assert!(seen.insert(key), "duplicate setting: {}", s);
        }
        assert_eq!(seen.len(), NUM_SETTINGS);
    }
}
