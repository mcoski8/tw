//! Suit canonicalization for 7-card hands (Decision 006).
//!
//! Two hands that differ only by a permutation of suit labels are strategically
//! identical — e.g. `A♠K♠Q♥J♥` ≡ `A♥K♥Q♠J♠`. The orbit of a 7-card hand under
//! the symmetric group S_4 on suits has size at most 24; hands with repeated
//! suit patterns (e.g. all same suit) have smaller orbits. Picking one
//! canonical representative per orbit reduces the 133,784,560 = C(52,7)
//! distinct hands to a much smaller set (empirically measured in
//! `enumerate_canonical_hands`; ballpark 6–8M under Burnside for this variant).
//!
//! Representation: a hand is a sorted-ascending `[u8; 7]` of packed card
//! indices (see `card.rs`: index = (rank-2)*4 + suit). Suit permutation
//! `sigma: [u8;4]` sends old suit `s` → `sigma[s]`; permuting a card preserves
//! its rank bits. The canonical form is the lex-smallest sorted `[u8;7]`
//! obtained under all 24 permutations — including identity.
//!
//! Enumeration strategy: iterate all C(52,7) combinations in lex order; keep
//! only hands that equal their own canonical form (early-exit: a hand fails
//! the canonical test as soon as ANY non-identity permutation yields a
//! lex-smaller representation). Parallelized across the outermost card value
//! via rayon. Each worker walks a contiguous lex-slice independently.

use std::fs::File;
use std::io::{BufReader, BufWriter, Read, Write};
use std::path::Path;

use rayon::prelude::*;

use crate::card::Card;

pub const HAND_SIZE: usize = 7;
pub const NUM_CARDS: u8 = 52;

pub const CANON_MAGIC: [u8; 4] = *b"TWCH";
pub const CANON_VERSION: u32 = 1;
pub const CANON_HEADER_SIZE: u64 = 32;

/// All 24 permutations of the 4 suits. Row i maps old_suit → new_suit.
/// Row 0 is identity; comparing against it is free (any other permutation
/// producing a smaller sorted form is a rejection).
const SUIT_PERMUTATIONS: [[u8; 4]; 24] = [
    [0, 1, 2, 3], [0, 1, 3, 2], [0, 2, 1, 3], [0, 2, 3, 1], [0, 3, 1, 2], [0, 3, 2, 1],
    [1, 0, 2, 3], [1, 0, 3, 2], [1, 2, 0, 3], [1, 2, 3, 0], [1, 3, 0, 2], [1, 3, 2, 0],
    [2, 0, 1, 3], [2, 0, 3, 1], [2, 1, 0, 3], [2, 1, 3, 0], [2, 3, 0, 1], [2, 3, 1, 0],
    [3, 0, 1, 2], [3, 0, 2, 1], [3, 1, 0, 2], [3, 1, 2, 0], [3, 2, 0, 1], [3, 2, 1, 0],
];

/// Apply a suit permutation to a single packed card. The rank bits are in the
/// high 6 bits of `index` and the suit bits are `index & 0b11`.
#[inline]
fn permute_card(idx: u8, sigma: &[u8; 4]) -> u8 {
    (idx & !0b11) | sigma[(idx & 0b11) as usize]
}

/// Apply a suit permutation to a sorted 7-card hand and re-sort.
#[inline]
fn apply_perm(hand: &[u8; HAND_SIZE], sigma: &[u8; 4]) -> [u8; HAND_SIZE] {
    let mut out = [0u8; HAND_SIZE];
    for i in 0..HAND_SIZE {
        out[i] = permute_card(hand[i], sigma);
    }
    out.sort_unstable();
    out
}

/// Produce the canonical representative of a 7-card hand (sorted ascending).
///
/// Input need not be sorted — we sort internally. Output is always sorted
/// ascending and is the lex-smallest form across all 24 suit relabelings.
pub fn canonicalize(hand: &[u8; HAND_SIZE]) -> [u8; HAND_SIZE] {
    let mut sorted = *hand;
    sorted.sort_unstable();
    let mut best = sorted;
    // Skip index 0 (identity — produces `sorted` itself, already the baseline).
    for sigma in SUIT_PERMUTATIONS[1..].iter() {
        let cand = apply_perm(&sorted, sigma);
        if cand < best {
            best = cand;
        }
    }
    best
}

/// Is this sorted hand already in canonical form?
///
/// Fast-path rejection: as soon as any non-identity permutation yields a
/// lex-smaller sorted form, return false. For most hands (~23/24 on average)
/// this is the first or second permutation checked.
#[inline]
pub fn is_canonical(sorted_hand: &[u8; HAND_SIZE]) -> bool {
    for sigma in SUIT_PERMUTATIONS[1..].iter() {
        let cand = apply_perm(sorted_hand, sigma);
        if cand < *sorted_hand {
            return false;
        }
    }
    true
}

/// Convert a `[Card; 7]` (in any order) to the sorted `[u8; 7]` byte form this
/// module operates on.
pub fn hand_to_bytes(hand: &[Card; HAND_SIZE]) -> [u8; HAND_SIZE] {
    let mut out = [0u8; HAND_SIZE];
    for i in 0..HAND_SIZE {
        out[i] = hand[i].index();
    }
    out.sort_unstable();
    out
}

/// Convert a sorted `[u8; 7]` back to a `[Card; 7]` for downstream consumers
/// that want typed cards.
pub fn bytes_to_hand(bytes: &[u8; HAND_SIZE]) -> [Card; HAND_SIZE] {
    [
        Card::from_index(bytes[0]),
        Card::from_index(bytes[1]),
        Card::from_index(bytes[2]),
        Card::from_index(bytes[3]),
        Card::from_index(bytes[4]),
        Card::from_index(bytes[5]),
        Card::from_index(bytes[6]),
    ]
}

/// Advance `combo` to the next 7-card combination in lex order over 0..n.
/// Returns false when the last combination has been consumed.
#[inline]
fn next_combination(combo: &mut [u8; HAND_SIZE], n: u8) -> bool {
    const K: usize = HAND_SIZE;
    // Rightmost position i whose value is less than its per-slot maximum
    // n - K + i. Bump it and cascade-reset the tail to i+1, i+2, ...
    for i in (0..K).rev() {
        let max_at_i = n - (K as u8) + (i as u8);
        if combo[i] < max_at_i {
            combo[i] += 1;
            for j in (i + 1)..K {
                combo[j] = combo[j - 1] + 1;
            }
            return true;
        }
    }
    false
}

/// Enumerate every canonical 7-card hand from a 52-card deck, sorted by lex
/// order of the `[u8;7]` representation.
///
/// Parallelized over the value of the first card: worker `c0` iterates all
/// combinations whose smallest card equals `c0`. Workers run independently
/// and produce disjoint output slices; results are concatenated in order so
/// the final `Vec` is globally lex-sorted.
pub fn enumerate_canonical_hands() -> Vec<[u8; HAND_SIZE]> {
    // Smallest card can be at most 52 - 7 = 45.
    let chunks: Vec<Vec<[u8; HAND_SIZE]>> = (0u8..=45)
        .into_par_iter()
        .map(|c0| {
            let mut out: Vec<[u8; HAND_SIZE]> = Vec::new();
            let mut combo = [c0, c0 + 1, c0 + 2, c0 + 3, c0 + 4, c0 + 5, c0 + 6];
            loop {
                if is_canonical(&combo) {
                    out.push(combo);
                }
                // Only advance within this c0-slice: stop once combo[0] changes.
                let prev_c0 = combo[0];
                if !next_combination(&mut combo, NUM_CARDS) {
                    break;
                }
                if combo[0] != prev_c0 {
                    break;
                }
            }
            out
        })
        .collect();

    let total: usize = chunks.iter().map(|c| c.len()).sum();
    let mut out = Vec::with_capacity(total);
    for mut c in chunks {
        out.append(&mut c);
    }
    out
}

/// Write a canonical-hand list to disk. Format:
///   magic "TWCH" (4) | version u32 (4) | num_hands u64 (8) | reserved [u8;16]
///   then num_hands × 7 bytes of sorted card indices.
pub fn write_canonical_hands(path: &Path, hands: &[[u8; HAND_SIZE]]) -> std::io::Result<()> {
    if let Some(parent) = path.parent() {
        if !parent.as_os_str().is_empty() {
            std::fs::create_dir_all(parent)?;
        }
    }
    let f = File::create(path)?;
    let mut w = BufWriter::new(f);
    let mut header = [0u8; 32];
    header[0..4].copy_from_slice(&CANON_MAGIC);
    header[4..8].copy_from_slice(&CANON_VERSION.to_le_bytes());
    header[8..16].copy_from_slice(&(hands.len() as u64).to_le_bytes());
    w.write_all(&header)?;
    for h in hands {
        w.write_all(h)?;
    }
    w.flush()?;
    Ok(())
}

/// Read a canonical-hand list previously produced by `write_canonical_hands`.
pub fn read_canonical_hands(path: &Path) -> std::io::Result<Vec<[u8; HAND_SIZE]>> {
    let f = File::open(path)?;
    let mut r = BufReader::new(f);
    let mut header = [0u8; 32];
    r.read_exact(&mut header)?;
    if header[0..4] != CANON_MAGIC {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            "bad magic — not a canonical-hand file",
        ));
    }
    let mut v = [0u8; 4];
    v.copy_from_slice(&header[4..8]);
    let version = u32::from_le_bytes(v);
    if version != CANON_VERSION {
        return Err(std::io::Error::new(
            std::io::ErrorKind::InvalidData,
            format!("canon version mismatch: expected {CANON_VERSION}, got {version}"),
        ));
    }
    let mut n = [0u8; 8];
    n.copy_from_slice(&header[8..16]);
    let num = u64::from_le_bytes(n) as usize;
    let mut hands = Vec::with_capacity(num);
    let mut buf = [0u8; HAND_SIZE];
    for _ in 0..num {
        r.read_exact(&mut buf)?;
        hands.push(buf);
    }
    Ok(hands)
}

/// Count canonical 7-card hands without materializing them. Cheap sanity
/// check; used in tests and can be called by the CLI to preview enumeration
/// cost without the memory footprint.
pub fn count_canonical_hands() -> u64 {
    (0u8..=45)
        .into_par_iter()
        .map(|c0| {
            let mut n: u64 = 0;
            let mut combo = [c0, c0 + 1, c0 + 2, c0 + 3, c0 + 4, c0 + 5, c0 + 6];
            loop {
                if is_canonical(&combo) {
                    n += 1;
                }
                let prev_c0 = combo[0];
                if !next_combination(&mut combo, NUM_CARDS) {
                    break;
                }
                if combo[0] != prev_c0 {
                    break;
                }
            }
            n
        })
        .sum()
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::card::parse_hand;

    fn bytes(s: &str) -> [u8; HAND_SIZE] {
        let v = parse_hand(s).unwrap();
        assert_eq!(v.len(), HAND_SIZE);
        let mut out = [0u8; HAND_SIZE];
        for i in 0..HAND_SIZE {
            out[i] = v[i].index();
        }
        out.sort_unstable();
        out
    }

    #[test]
    fn suit_permutations_are_all_24_distinct_bijections() {
        let mut seen = std::collections::HashSet::new();
        for sigma in SUIT_PERMUTATIONS.iter() {
            // Each sigma must be a bijection of {0,1,2,3}.
            let mut hit = [false; 4];
            for &v in sigma {
                assert!(v < 4, "out of range");
                assert!(!hit[v as usize], "not a bijection: {:?}", sigma);
                hit[v as usize] = true;
            }
            assert!(hit.iter().all(|&b| b));
            assert!(seen.insert(*sigma), "duplicate perm: {:?}", sigma);
        }
        assert_eq!(seen.len(), 24);
    }

    #[test]
    fn canonicalize_is_idempotent() {
        let h = bytes("As Kh Qd Jc Ts 9h 2d");
        let c1 = canonicalize(&h);
        let c2 = canonicalize(&c1);
        assert_eq!(c1, c2, "canonicalize must be idempotent");
    }

    #[test]
    fn canonicalize_agrees_across_suit_permutations() {
        // Any of the 24 suit relabelings of the same hand must produce the
        // same canonical representative.
        let original = bytes("As Kh Qd Jc Ts 9h 2d");
        let canon = canonicalize(&original);
        for sigma in SUIT_PERMUTATIONS.iter() {
            let relabeled = apply_perm(&original, sigma);
            assert_eq!(
                canonicalize(&relabeled),
                canon,
                "relabeling via {:?} changed the canonical form",
                sigma
            );
        }
    }

    #[test]
    fn is_canonical_matches_canonicalize_fixpoint() {
        // For a sampling of hands, `is_canonical(h)` must equal `canonicalize(h) == h`.
        let hands = [
            "2c 3d 4h 5s 6c 7d 8h",
            "As Ad Ah Ac Kh Qd Jc",
            "2c 2d 2h 2s 3c 3d 3h",
            "As Kh Qd Jc Ts 9h 2d",
            "As 2c 3c 4c 5c 6c 7c",
        ];
        for s in hands {
            let h = bytes(s);
            let c = canonicalize(&h);
            assert_eq!(is_canonical(&h), h == c, "mismatch on {}", s);
        }
    }

    #[test]
    fn next_combination_walks_all_combos_for_small_n() {
        // Walk all C(7,7) = 1 then C(8,7) = 8 then C(10,7) = 120 to sanity-check
        // the iterator and its per-slot maximum.
        for n in [7u8, 8, 10] {
            let mut combo = [0u8, 1, 2, 3, 4, 5, 6];
            let mut count: usize = 1;
            while next_combination(&mut combo, n) {
                // Each combo is strictly increasing and within [0, n).
                for i in 0..HAND_SIZE {
                    assert!(combo[i] < n, "combo[{}]={} n={}", i, combo[i], n);
                }
                for i in 1..HAND_SIZE {
                    assert!(combo[i - 1] < combo[i]);
                }
                count += 1;
            }
            let expected = n_choose_k(n as usize, HAND_SIZE);
            assert_eq!(count, expected, "n={}", n);
        }
    }

    fn n_choose_k(n: usize, k: usize) -> usize {
        if k > n {
            return 0;
        }
        let mut num: u128 = 1;
        let mut den: u128 = 1;
        for i in 0..k {
            num *= (n - i) as u128;
            den *= (i + 1) as u128;
        }
        (num / den) as usize
    }

    #[test]
    fn enumerate_canonical_subset_round_trips_for_tiny_deck() {
        // The subset must be CLOSED under suit permutation for this round-trip
        // to be well-defined: if a hand's canonical form uses a suit-sibling
        // outside the subset, the two enumerations diverge. The first 12 card
        // indices are ranks {2, 3, 4} in all four suits — closed.
        let n = 12u8;
        let mut full_canon = std::collections::BTreeSet::<[u8; HAND_SIZE]>::new();
        let mut combo = [0u8, 1, 2, 3, 4, 5, 6];
        loop {
            if combo[HAND_SIZE - 1] < n {
                full_canon.insert(canonicalize(&combo));
            }
            if !next_combination(&mut combo, n) {
                break;
            }
        }
        let by_is_canon = {
            let mut out: std::collections::BTreeSet<[u8; HAND_SIZE]> = std::collections::BTreeSet::new();
            let mut combo = [0u8, 1, 2, 3, 4, 5, 6];
            loop {
                if combo[HAND_SIZE - 1] < n && is_canonical(&combo) {
                    out.insert(combo);
                }
                if !next_combination(&mut combo, n) {
                    break;
                }
            }
            out
        };
        assert_eq!(full_canon, by_is_canon);
        assert!(!full_canon.is_empty(), "must have at least one canonical hand");
    }

    #[test]
    fn canonical_hand_file_roundtrip() {
        let hands: Vec<[u8; HAND_SIZE]> = vec![
            [0, 1, 2, 3, 4, 5, 6],
            [10, 11, 12, 13, 14, 15, 16],
            [45, 46, 47, 48, 49, 50, 51],
        ];
        let tmp = tempfile::NamedTempFile::new().unwrap();
        let path = tmp.path().to_path_buf();
        drop(tmp);
        write_canonical_hands(&path, &hands).unwrap();
        let back = read_canonical_hands(&path).unwrap();
        assert_eq!(hands, back);
        std::fs::remove_file(&path).ok();
    }

    #[test]
    fn canonical_hand_uses_lowest_suits_first() {
        // Suit 0 (clubs) should appear at least once in any canonical hand that
        // contains any suited card. This is a weak check but catches the common
        // bug where sigma is applied inverted.
        let h = bytes("As Kh Qd Jc Ts 9h 2d");
        let c = canonicalize(&h);
        let has_suit0 = c.iter().any(|&idx| (idx & 0b11) == 0);
        assert!(has_suit0, "canonical hand should reassign smallest used suit to 0");
    }
}
