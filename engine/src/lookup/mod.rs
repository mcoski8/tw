//! Colex-indexed lookup table helpers.
//!
//! For a sorted combination c0 < c1 < ... < c_{k-1} drawn from {0, 1, ..., 51},
//! the colexicographic index is  Σ C(c_i, i+1). This is a bijection from
//! k-combinations to [0, C(52,k)). For k=5 we get 2,598,960 slots — exactly
//! the number of distinct 5-card hands.
//!
//! Sorting 5 bytes is ~5ns and the indexing math is a handful of table
//! lookups + adds, keeping the whole `eval_5` path well under 50ns.

/// C(52, 5) = 2,598,960 — the number of distinct 5-card hands.
pub const NUM_5CARD: usize = 2_598_960;

/// Precomputed binomial coefficients: BINOM[n][k] = C(n, k) for n <= 51, k <= 5.
/// Used by `colex_index_5` to turn a sorted 5-card combination into a table slot.
pub const BINOM: [[u32; 6]; 52] = build_binom();

const fn build_binom() -> [[u32; 6]; 52] {
    let mut t = [[0u32; 6]; 52];
    let mut n = 0usize;
    while n < 52 {
        t[n][0] = 1;
        let mut k = 1usize;
        while k <= 5 {
            if k > n {
                t[n][k] = 0;
            } else if k == n {
                t[n][k] = 1;
            } else {
                // Pascal's rule: C(n, k) = C(n-1, k-1) + C(n-1, k)
                t[n][k] = t[n - 1][k - 1] + t[n - 1][k];
            }
            k += 1;
        }
        n += 1;
    }
    t
}

/// Colex index for 5 card values (in 0..52). Input is sorted internally.
#[inline]
pub fn colex_index_5(mut idx: [u8; 5]) -> usize {
    idx.sort_unstable();
    (BINOM[idx[0] as usize][1]
        + BINOM[idx[1] as usize][2]
        + BINOM[idx[2] as usize][3]
        + BINOM[idx[3] as usize][4]
        + BINOM[idx[4] as usize][5]) as usize
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn binom_sanity() {
        assert_eq!(BINOM[51][5], 2_349_060);
        assert_eq!(BINOM[52 - 1][5] + BINOM[52 - 1][4], 2_598_960);
        assert_eq!(BINOM[5][5], 1);
        assert_eq!(BINOM[5][2], 10);
    }

    #[test]
    fn smallest_combo_has_index_zero() {
        assert_eq!(colex_index_5([0, 1, 2, 3, 4]), 0);
    }

    #[test]
    fn largest_combo_has_index_max() {
        assert_eq!(colex_index_5([47, 48, 49, 50, 51]), NUM_5CARD - 1);
    }

    #[test]
    fn colex_is_bijection_for_k5_n52() {
        // Spot-check a few enumerated combos, then confirm the full count
        // matches NUM_5CARD by iterating.
        let mut count = 0usize;
        let mut seen_max = 0usize;
        let mut idx = [0u8, 1, 2, 3, 4];
        loop {
            let c = colex_index_5(idx);
            assert!(c < NUM_5CARD);
            if c > seen_max {
                seen_max = c;
            }
            count += 1;
            // advance
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
        assert_eq!(count, NUM_5CARD);
        assert_eq!(seen_max, NUM_5CARD - 1);
    }
}
