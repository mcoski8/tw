//! Card, Rank, Suit, Deck types.
//!
//! Card is packed into a single u8 in range 0..52 as `(rank - 2) * 4 + suit`,
//! so rank lives in the high bits and suit in the low bits. This keeps `Card`
//! trivially copyable and makes colex indexing of the 5-card lookup table
//! (see `lookup/mod.rs`) a plain byte-sort away.

use std::fmt;
use std::str::FromStr;

use rand::seq::SliceRandom;
use rand::Rng;
use serde::{Deserialize, Serialize};

/// Suits: c=0, d=1, h=2, s=3. All suits are equal for hand ranking; the
/// distinction only matters for flush detection.
#[derive(Copy, Clone, Eq, PartialEq, Ord, PartialOrd, Hash, Debug, Serialize, Deserialize)]
#[repr(u8)]
pub enum Suit {
    Clubs = 0,
    Diamonds = 1,
    Hearts = 2,
    Spades = 3,
}

impl Suit {
    pub const fn from_u8(s: u8) -> Self {
        match s {
            0 => Suit::Clubs,
            1 => Suit::Diamonds,
            2 => Suit::Hearts,
            3 => Suit::Spades,
            _ => panic!("invalid suit"),
        }
    }

    pub const fn as_u8(self) -> u8 {
        self as u8
    }

    pub const fn as_char(self) -> char {
        match self {
            Suit::Clubs => 'c',
            Suit::Diamonds => 'd',
            Suit::Hearts => 'h',
            Suit::Spades => 's',
        }
    }
}

/// Ranks 2..=14 where 14 = Ace. The Ace is high by default; the wheel
/// straight (A-2-3-4-5) is handled specially by the evaluator, not here.
pub const RANK_MIN: u8 = 2;
pub const RANK_MAX: u8 = 14;

/// Packed card: `(rank - 2) * 4 + suit`, giving a value in 0..52.
#[derive(Copy, Clone, Eq, PartialEq, Ord, PartialOrd, Hash, Debug, Serialize, Deserialize)]
#[repr(transparent)]
pub struct Card(pub u8);

impl Card {
    #[inline]
    pub const fn new(rank: u8, suit: u8) -> Self {
        debug_assert!(rank >= RANK_MIN && rank <= RANK_MAX);
        debug_assert!(suit <= 3);
        Card((rank - RANK_MIN) * 4 + suit)
    }

    #[inline]
    pub const fn from_index(i: u8) -> Self {
        debug_assert!(i < 52);
        Card(i)
    }

    #[inline]
    pub const fn index(self) -> u8 {
        self.0
    }

    /// Returns the rank in 2..=14.
    #[inline]
    pub const fn rank(self) -> u8 {
        self.0 / 4 + RANK_MIN
    }

    /// Returns the suit in 0..=3.
    #[inline]
    pub const fn suit(self) -> u8 {
        self.0 % 4
    }

    pub const fn rank_char(self) -> char {
        rank_to_char(self.rank())
    }

    pub const fn suit_char(self) -> char {
        Suit::from_u8(self.suit()).as_char()
    }
}

pub const fn rank_to_char(r: u8) -> char {
    match r {
        2 => '2',
        3 => '3',
        4 => '4',
        5 => '5',
        6 => '6',
        7 => '7',
        8 => '8',
        9 => '9',
        10 => 'T',
        11 => 'J',
        12 => 'Q',
        13 => 'K',
        14 => 'A',
        _ => '?',
    }
}

pub fn char_to_rank(c: char) -> Option<u8> {
    match c.to_ascii_uppercase() {
        '2' => Some(2),
        '3' => Some(3),
        '4' => Some(4),
        '5' => Some(5),
        '6' => Some(6),
        '7' => Some(7),
        '8' => Some(8),
        '9' => Some(9),
        'T' => Some(10),
        'J' => Some(11),
        'Q' => Some(12),
        'K' => Some(13),
        'A' => Some(14),
        _ => None,
    }
}

pub fn char_to_suit(c: char) -> Option<u8> {
    match c.to_ascii_lowercase() {
        'c' => Some(0),
        'd' => Some(1),
        'h' => Some(2),
        's' => Some(3),
        _ => None,
    }
}

impl fmt::Display for Card {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "{}{}", self.rank_char(), self.suit_char())
    }
}

#[derive(Debug, Clone, Eq, PartialEq)]
pub struct ParseCardError(pub String);

impl fmt::Display for ParseCardError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(f, "invalid card: {:?}", self.0)
    }
}

impl std::error::Error for ParseCardError {}

impl FromStr for Card {
    type Err = ParseCardError;

    fn from_str(s: &str) -> Result<Self, Self::Err> {
        let s = s.trim();
        let mut chars = s.chars();
        let rc = chars.next().ok_or_else(|| ParseCardError(s.to_string()))?;
        let sc = chars.next().ok_or_else(|| ParseCardError(s.to_string()))?;
        if chars.next().is_some() {
            return Err(ParseCardError(s.to_string()));
        }
        let rank = char_to_rank(rc).ok_or_else(|| ParseCardError(s.to_string()))?;
        let suit = char_to_suit(sc).ok_or_else(|| ParseCardError(s.to_string()))?;
        Ok(Card::new(rank, suit))
    }
}

/// Parse a whitespace-separated list of cards, e.g. "As Kh Qd Jc Ts 9h 2d".
pub fn parse_hand(s: &str) -> Result<Vec<Card>, ParseCardError> {
    s.split_whitespace().map(Card::from_str).collect()
}

/// Simple deck for dealing hands in tests and in the (future) Monte Carlo
/// engine. Not used in the inner evaluation loop.
#[derive(Debug, Clone)]
pub struct Deck {
    cards: Vec<Card>,
}

impl Default for Deck {
    fn default() -> Self {
        Self::new()
    }
}

impl Deck {
    pub fn new() -> Self {
        let cards = (0..52u8).map(Card::from_index).collect();
        Deck { cards }
    }

    pub fn len(&self) -> usize {
        self.cards.len()
    }

    pub fn is_empty(&self) -> bool {
        self.cards.is_empty()
    }

    pub fn shuffle<R: Rng>(&mut self, rng: &mut R) {
        self.cards.shuffle(rng);
    }

    /// Remove and return the top `n` cards from the deck.
    pub fn deal(&mut self, n: usize) -> Vec<Card> {
        assert!(n <= self.cards.len(), "deal: not enough cards");
        self.cards.drain(..n).collect()
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn card_pack_roundtrip() {
        for r in RANK_MIN..=RANK_MAX {
            for s in 0..4 {
                let c = Card::new(r, s);
                assert_eq!(c.rank(), r);
                assert_eq!(c.suit(), s);
                assert!(c.index() < 52);
            }
        }
    }

    #[test]
    fn display_and_parse_roundtrip() {
        for i in 0..52u8 {
            let c = Card::from_index(i);
            let s = c.to_string();
            let parsed: Card = s.parse().unwrap();
            assert_eq!(c, parsed);
        }
    }

    #[test]
    fn parse_hand_seven() {
        let h = parse_hand("As Kh Qd Jc Ts 9h 2d").unwrap();
        assert_eq!(h.len(), 7);
        assert_eq!(h[0], Card::new(14, 3));
        assert_eq!(h[6], Card::new(2, 1));
    }

    #[test]
    fn deck_new_has_52_unique() {
        let d = Deck::new();
        assert_eq!(d.len(), 52);
        let mut seen = [false; 52];
        for c in &d.cards {
            assert!(!seen[c.index() as usize]);
            seen[c.index() as usize] = true;
        }
        assert!(seen.iter().all(|&b| b));
    }

    #[test]
    fn deck_deal_removes_cards() {
        let mut d = Deck::new();
        let hand = d.deal(7);
        assert_eq!(hand.len(), 7);
        assert_eq!(d.len(), 45);
    }
}
