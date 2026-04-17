//! 5-card hand evaluation.
//!
//! `compute_rank_5` directly computes a hand's rank category + kickers and
//! packs them into a u32 where higher = stronger. This function is used at
//! lookup-table build time and as a correctness reference for tests.
//!
//! At runtime, `Evaluator::eval_5` performs a colex-indexed array lookup into
//! a precomputed table of all C(52,5) = 2,598,960 hand ranks. The lookup is a
//! pure function (no side effects, no allocations) so the same evaluator can
//! back any parallel or GPU backend in later sprints.
//!
//! HandRank encoding (u32, total-ordered):
//!   bits 24..28  category  (1 high, 2 pair, 3 two-pair, 4 trips,
//!                           5 straight, 6 flush, 7 full house,
//!                           8 quads, 9 straight flush)
//!   bits 20..24  primary rank     (e.g. quad rank, trip rank, top pair)
//!   bits 16..20  secondary rank   (kicker, other pair, pair in full house)
//!   bits 12..16  kicker 1
//!   bits  8..12  kicker 2
//!   bits  4.. 8  kicker 3
//!
//! Rank fields hold the rank value (2..=14), so u32 comparison matches poker
//! rank comparison directly.

use std::fs::File;
use std::io::{BufReader, BufWriter};
use std::path::Path;

use serde::{Deserialize, Serialize};

use crate::card::Card;
use crate::lookup::{colex_index_5, NUM_5CARD};

pub type HandRank = u32;

pub const CAT_HIGH: u32 = 1;
pub const CAT_PAIR: u32 = 2;
pub const CAT_TWO_PAIR: u32 = 3;
pub const CAT_TRIPS: u32 = 4;
pub const CAT_STRAIGHT: u32 = 5;
pub const CAT_FLUSH: u32 = 6;
pub const CAT_FULL_HOUSE: u32 = 7;
pub const CAT_QUADS: u32 = 8;
pub const CAT_STRAIGHT_FLUSH: u32 = 9;

pub const fn category(r: HandRank) -> u32 {
    (r >> 24) & 0xF
}

pub fn category_name(r: HandRank) -> &'static str {
    match category(r) {
        CAT_HIGH => "High Card",
        CAT_PAIR => "One Pair",
        CAT_TWO_PAIR => "Two Pair",
        CAT_TRIPS => "Three of a Kind",
        CAT_STRAIGHT => "Straight",
        CAT_FLUSH => "Flush",
        CAT_FULL_HOUSE => "Full House",
        CAT_QUADS => "Four of a Kind",
        CAT_STRAIGHT_FLUSH => {
            // Royal flush is a straight flush with high=14; we surface that
            // for display only — ranking-wise a royal sits at the top of the
            // straight-flush slot.
            "Straight Flush"
        }
        _ => "Unknown",
    }
}

#[inline]
fn encode(category: u32, ranks: &[u8]) -> HandRank {
    debug_assert!(ranks.len() <= 5);
    let mut r: u32 = category << 24;
    for (i, &rank) in ranks.iter().enumerate() {
        // First rank slot is bits 20..24, each subsequent slot 4 bits lower.
        let shift = 20 - 4 * i as u32;
        r |= (rank as u32) << shift;
    }
    r
}

/// Direct poker-rank computation for 5 cards. Returns a comparable u32 where
/// higher = stronger. Used at table-build time and in tests as the reference
/// implementation.
pub fn compute_rank_5(cards: [Card; 5]) -> HandRank {
    // Sort ranks descending so kicker ordering falls out naturally.
    let mut ranks = [0u8; 5];
    let mut suits = [0u8; 5];
    for i in 0..5 {
        ranks[i] = cards[i].rank();
        suits[i] = cards[i].suit();
    }
    ranks.sort_unstable_by(|a, b| b.cmp(a));

    let is_flush =
        suits[0] == suits[1] && suits[1] == suits[2] && suits[2] == suits[3] && suits[3] == suits[4];

    let is_regular_straight = ranks[0] == ranks[1] + 1
        && ranks[1] == ranks[2] + 1
        && ranks[2] == ranks[3] + 1
        && ranks[3] == ranks[4] + 1;
    // Wheel: A-2-3-4-5. Sorted desc: [14, 5, 4, 3, 2]. Ace plays low here; the
    // effective high card for comparison is 5.
    let is_wheel =
        ranks[0] == 14 && ranks[1] == 5 && ranks[2] == 4 && ranks[3] == 3 && ranks[4] == 2;
    let is_straight = is_regular_straight || is_wheel;
    let straight_high = if is_wheel { 5 } else { ranks[0] };

    // Group contiguous equal ranks. Since ranks is sorted desc, equal ranks
    // are adjacent. Track (count, rank) for each group.
    let mut groups: [(u8, u8); 5] = [(0, 0); 5];
    let mut ng = 0usize;
    let mut i = 0usize;
    while i < 5 {
        let r = ranks[i];
        let mut j = i;
        while j < 5 && ranks[j] == r {
            j += 1;
        }
        groups[ng] = ((j - i) as u8, r);
        ng += 1;
        i = j;
    }
    // Sort groups by (count desc, rank desc) so quads/trips/pair come first.
    groups[..ng].sort_by(|a, b| b.cmp(a));

    if is_flush && is_straight {
        return encode(CAT_STRAIGHT_FLUSH, &[straight_high]);
    }
    if groups[0].0 == 4 {
        return encode(CAT_QUADS, &[groups[0].1, groups[1].1]);
    }
    if ng >= 2 && groups[0].0 == 3 && groups[1].0 == 2 {
        return encode(CAT_FULL_HOUSE, &[groups[0].1, groups[1].1]);
    }
    if is_flush {
        return encode(CAT_FLUSH, &ranks);
    }
    if is_straight {
        return encode(CAT_STRAIGHT, &[straight_high]);
    }
    if groups[0].0 == 3 {
        return encode(CAT_TRIPS, &[groups[0].1, groups[1].1, groups[2].1]);
    }
    if ng >= 2 && groups[0].0 == 2 && groups[1].0 == 2 {
        return encode(CAT_TWO_PAIR, &[groups[0].1, groups[1].1, groups[2].1]);
    }
    if groups[0].0 == 2 {
        return encode(
            CAT_PAIR,
            &[groups[0].1, groups[1].1, groups[2].1, groups[3].1],
        );
    }
    encode(CAT_HIGH, &ranks)
}

/// 5-card evaluator backed by a precomputed lookup table.
///
/// The table maps every C(52,5) combination (by colex index) to its HandRank.
/// Build once, reuse everywhere. The hot path (`eval_5`) is a pure function
/// so the same struct can back CPU and GPU backends in later sprints.
#[derive(Clone, Serialize, Deserialize)]
pub struct Evaluator {
    table: Vec<HandRank>,
}

impl Evaluator {
    /// Build the lookup table from scratch by enumerating all C(52,5) hands
    /// and running `compute_rank_5` on each. Takes ~1s in release mode.
    pub fn build() -> Self {
        let mut table = vec![0u32; NUM_5CARD];
        let mut indices = [0u8, 1, 2, 3, 4];
        loop {
            let cards = [
                Card::from_index(indices[0]),
                Card::from_index(indices[1]),
                Card::from_index(indices[2]),
                Card::from_index(indices[3]),
                Card::from_index(indices[4]),
            ];
            let idx = colex_index_5(indices);
            table[idx] = compute_rank_5(cards);
            if !next_combination(&mut indices, 52) {
                break;
            }
        }
        Evaluator { table }
    }

    /// Load a previously-serialized table from disk, or build + save if the
    /// file does not exist. Build cost is ~1s so this is mostly a convenience
    /// to keep startup fast across repeated runs.
    pub fn load_or_build(path: &Path) -> std::io::Result<Self> {
        if path.exists() {
            let f = File::open(path)?;
            let reader = BufReader::new(f);
            let ev: Evaluator = bincode::deserialize_from(reader)
                .map_err(|e| std::io::Error::new(std::io::ErrorKind::InvalidData, e))?;
            if ev.table.len() == NUM_5CARD {
                return Ok(ev);
            }
            // Size mismatch — rebuild.
        }
        let ev = Evaluator::build();
        if let Some(parent) = path.parent() {
            std::fs::create_dir_all(parent)?;
        }
        let f = File::create(path)?;
        let writer = BufWriter::new(f);
        bincode::serialize_into(writer, &ev)
            .map_err(|e| std::io::Error::new(std::io::ErrorKind::Other, e))?;
        Ok(ev)
    }

    /// Pure array lookup — no side effects, no allocations. This is the hot
    /// path for all tier evaluations in later sprints.
    #[inline]
    pub fn eval_5(&self, cards: [Card; 5]) -> HandRank {
        let indices = [
            cards[0].index(),
            cards[1].index(),
            cards[2].index(),
            cards[3].index(),
            cards[4].index(),
        ];
        let idx = colex_index_5(indices);
        // SAFETY-equivalent: colex_index_5 of 5 distinct indices in 0..52 is
        // always < NUM_5CARD, but we let the bounds check stand for Sprint 0.
        self.table[idx]
    }
}

/// Advance `idx` to the lexicographically next k-combination of {0..n}.
/// Returns false when the last combination has been emitted.
fn next_combination(idx: &mut [u8], n: u8) -> bool {
    let k = idx.len();
    let mut i = k;
    while i > 0 {
        i -= 1;
        if idx[i] as usize + (k - i) < n as usize {
            idx[i] += 1;
            for j in (i + 1)..k {
                idx[j] = idx[j - 1] + 1;
            }
            return true;
        }
    }
    false
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::card::Card;

    fn h(s: &str) -> [Card; 5] {
        let v = crate::card::parse_hand(s).unwrap();
        assert_eq!(v.len(), 5);
        [v[0], v[1], v[2], v[3], v[4]]
    }

    #[test]
    fn royal_flush_beats_straight_flush() {
        let royal = compute_rank_5(h("As Ks Qs Js Ts"));
        let sf = compute_rank_5(h("9s 8s 7s 6s 5s"));
        assert!(royal > sf);
        assert_eq!(category(royal), CAT_STRAIGHT_FLUSH);
        assert_eq!(category(sf), CAT_STRAIGHT_FLUSH);
    }

    #[test]
    fn straight_flush_beats_quads() {
        let sf = compute_rank_5(h("9s 8s 7s 6s 5s"));
        let quads = compute_rank_5(h("Ac Ad Ah As Kd"));
        assert!(sf > quads);
    }

    #[test]
    fn full_house_aaa_kk_beats_kkk_aa() {
        let a_full = compute_rank_5(h("Ac Ad Ah Ks Kd"));
        let k_full = compute_rank_5(h("Kc Kd Kh As Ad"));
        assert!(a_full > k_full, "AAA-KK ({:x}) must beat KKK-AA ({:x})", a_full, k_full);
        assert_eq!(category(a_full), CAT_FULL_HOUSE);
    }

    #[test]
    fn flush_compares_by_highest_then_next() {
        let a_flush = compute_rank_5(h("As Ks Qs Js 9s"));
        let a_flush_lower = compute_rank_5(h("As Ks Qs Js 8s"));
        let k_flush = compute_rank_5(h("Ks Qs Js Ts 8s"));
        assert!(a_flush > a_flush_lower);
        assert!(a_flush_lower > k_flush);
    }

    #[test]
    fn straight_a_high_beats_k_high() {
        let broadway = compute_rank_5(h("As Kd Qh Jc Th"));
        let k_high = compute_rank_5(h("Ks Qd Jh Tc 9h"));
        assert!(broadway > k_high);
    }

    #[test]
    fn wheel_is_lowest_straight() {
        let wheel = compute_rank_5(h("As 2d 3h 4c 5s"));
        let six_high = compute_rank_5(h("2s 3d 4h 5c 6s"));
        assert_eq!(category(wheel), CAT_STRAIGHT);
        assert!(wheel < six_high, "wheel {:x} must be below 6-high straight {:x}", wheel, six_high);
    }

    #[test]
    fn wheel_loses_to_regular_straight() {
        let wheel = compute_rank_5(h("As 2d 3h 4c 5s"));
        // A pair of aces (even low) must still beat a wheel straight? No — a
        // straight beats a pair. Compare wheel to another straight:
        let seven_high = compute_rank_5(h("3s 4d 5h 6c 7s"));
        assert!(seven_high > wheel);
    }

    #[test]
    fn two_pair_compares_high_pair_then_low_pair_then_kicker() {
        let aa_kk_q = compute_rank_5(h("As Ad Ks Kd Qc"));
        let aa_qq_k = compute_rank_5(h("As Ad Qs Qd Kc"));
        let kk_qq_a = compute_rank_5(h("Ks Kd Qs Qd Ac"));
        assert!(aa_kk_q > aa_qq_k);
        assert!(aa_qq_k > kk_qq_a);

        let aa_kk_q2 = compute_rank_5(h("As Ad Ks Kd 2c"));
        assert!(aa_kk_q > aa_kk_q2); // kicker matters
    }

    #[test]
    fn one_pair_kickers_matter_down_to_third() {
        let aa_k_q_j = compute_rank_5(h("As Ad Ks Qd Jc"));
        let aa_k_q_t = compute_rank_5(h("As Ad Ks Qd Tc"));
        let aa_k_j_t = compute_rank_5(h("As Ad Ks Jd Tc"));
        assert!(aa_k_q_j > aa_k_q_t);
        assert!(aa_k_q_t > aa_k_j_t);
    }

    #[test]
    fn category_ladder() {
        let high = compute_rank_5(h("As Kd Qh Jc 9h"));
        let pair = compute_rank_5(h("As Ad Qh Jc 9h"));
        let two_pair = compute_rank_5(h("As Ad Qh Qc 9h"));
        let trips = compute_rank_5(h("As Ad Ah Qc 9h"));
        let straight = compute_rank_5(h("As Kd Qh Jc Th"));
        let flush = compute_rank_5(h("As Ks Qs Js 9s"));
        let full = compute_rank_5(h("As Ad Ah Qc Qh"));
        let quads = compute_rank_5(h("As Ad Ah Ac Qh"));
        let sf = compute_rank_5(h("9s 8s 7s 6s 5s"));

        assert!(pair > high);
        assert!(two_pair > pair);
        assert!(trips > two_pair);
        assert!(straight > trips);
        assert!(flush > straight);
        assert!(full > flush);
        assert!(quads > full);
        assert!(sf > quads);
    }

    #[test]
    fn lookup_matches_direct_computation_spotcheck() {
        let ev = Evaluator::build();
        let cases = [
            "As Ks Qs Js Ts",
            "As 2d 3h 4c 5s",
            "As Ad Ks Kd 2c",
            "2c 3d 4h 5s 7c",
            "Ks Kd Kh Kc 2d",
        ];
        for c in &cases {
            let cards = h(c);
            assert_eq!(ev.eval_5(cards), compute_rank_5(cards), "hand {}", c);
        }
    }
}
