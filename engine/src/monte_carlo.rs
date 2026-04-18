//! Monte Carlo EV estimation for a fixed 7-card hand + HandSetting.
//!
//! For a target setting, each sample
//!   1. draws the opponent's 7 cards uniformly from the remaining 45,
//!   2. deals two distinguishable 5-card boards from the remaining 38,
//!   3. has the opponent pick a setting under `OpponentModel`,
//!   4. scores the 6-matchup via `scoring::matchup_breakdown`,
//!   5. accumulates p1's net points.
//! EV = total / N.
//!
//! Sprint 2 ships `OpponentModel::Random` only (uniform over 105 settings).
//! MiddleFirst / BestResponse plug in behind the same enum later.
//!
//! Performance note: `mc_evaluate_all_settings` uses COMMON RANDOM NUMBERS —
//! every p1 setting is scored against the SAME (opp_hand, board1, board2,
//! opp_setting) sample. This shares the sampling cost across the 105 settings
//! and reduces variance in the EV *ranking* (which is what we care about).
//!
//! Single-thread budget for 1 hand × 105 settings × 1000 samples:
//!   105 × 1000 matchup_breakdown calls × ~2.14 µs ≈ 225 ms.
//! Target was <500 ms, so there's headroom before the rayon pass.

use rand::rngs::SmallRng;
use rand::{Rng, SeedableRng};
use rayon::prelude::*;

use crate::card::Card;
use crate::hand_eval::Evaluator;
use crate::scoring::matchup_breakdown;
use crate::setting::{all_settings, HandSetting};

/// Strategy used by the simulated opponent to pick one of their 105 settings.
///
/// Seven pure models (Sprint 2b panel):
///   1. `Random`               — uniform 1/105 baseline
///   2. `MiddleFirstNaive`     — Hold'em-optimised mid, highest top, bot sanity check
///   3. `MiddleFirstSuitAware` — Naive + within-tier swap for bot suit gain
///   4. `OmahaFirst`           — best Omaha bot first, then mid, then top
///   5. `TopDefensive`         — highest non-pair-member on top; preserves pairs
///   6. `RandomWeighted`       — uniform over "reasonable" filtered settings
///   7. `BalancedHeuristic`    — weighted multi-tier scoring across all 105
///
/// Plus a wrapper:
///   `HeuristicMixed { base, p_heuristic }` — with prob p uses `base`, else Random.
/// The 20 % Random tail (Gemini's recommendation, Decision 019) prevents the
/// solver from finding brittle exploits that only work vs one deterministic line.
#[derive(Copy, Clone, PartialEq, Debug)]
pub enum OpponentModel {
    Random,
    MiddleFirstNaive,
    MiddleFirstSuitAware,
    OmahaFirst,
    TopDefensive,
    RandomWeighted,
    BalancedHeuristic,
    HeuristicMixed { base: MixedBase, p_heuristic: f32 },
}

/// Which deterministic heuristic a `HeuristicMixed` variant wraps.
/// RandomWeighted isn't included because it already has its own RNG branch —
/// mixing it with Random would be a mix of two random distributions, not a
/// meaningful opponent archetype.
#[derive(Copy, Clone, PartialEq, Debug)]
pub enum MixedBase {
    MiddleFirstNaive,
    MiddleFirstSuitAware,
    OmahaFirst,
    TopDefensive,
    BalancedHeuristic,
}

/// One setting's EV estimate from a Monte Carlo run.
#[derive(Copy, Clone, Debug)]
pub struct McResult {
    pub setting: HandSetting,
    pub ev: f64,
}

/// Result of evaluating all 105 settings for a hand. `results` is sorted
/// descending by `ev` — index 0 is the best setting under the chosen model.
#[derive(Clone, Debug)]
pub struct McSummary {
    pub results: Vec<McResult>,
    pub num_samples: usize,
}

impl McSummary {
    pub fn best(&self) -> &McResult {
        &self.results[0]
    }

    pub fn worst(&self) -> &McResult {
        self.results.last().expect("results non-empty")
    }

    /// EV gap between the best and second-best setting. Small gaps mean the
    /// decision is close and N should be increased for statistical confidence.
    pub fn gap_first_to_second(&self) -> f64 {
        if self.results.len() < 2 {
            0.0
        } else {
            self.results[0].ev - self.results[1].ev
        }
    }
}

/// Evaluate EV of a single (hand, setting) against sampled opponents.
///
/// `rng` is the caller's responsibility — pass a seeded `SmallRng` for
/// reproducibility in tests, or `SmallRng::from_entropy()` for production.
pub fn mc_evaluate_setting(
    ev: &Evaluator,
    hand: [Card; 7],
    p1_setting: &HandSetting,
    model: OpponentModel,
    num_samples: usize,
    rng: &mut SmallRng,
) -> f64 {
    debug_assert!(num_samples > 0, "need at least one sample");
    let remaining = remaining_45(hand);
    let mut total: i64 = 0;
    for _ in 0..num_samples {
        let (opp_hand, b1, b2) = sample_deal(rng, &remaining);
        let opp_setting = opp_pick(ev, opp_hand, model, rng);
        let br = matchup_breakdown(ev, p1_setting, &opp_setting, &b1, &b2);
        total += br.p1_points as i64;
    }
    total as f64 / num_samples as f64
}

/// Evaluate EV of every one of the 105 settings for a 7-card hand, under
/// common random numbers: all 105 settings are scored against the same
/// sampled opponent + boards.
pub fn mc_evaluate_all_settings(
    ev: &Evaluator,
    hand: [Card; 7],
    model: OpponentModel,
    num_samples: usize,
    rng: &mut SmallRng,
) -> McSummary {
    debug_assert!(num_samples > 0, "need at least one sample");
    let settings = all_settings(hand);
    let remaining = remaining_45(hand);
    let mut sums = vec![0i64; settings.len()];
    for _ in 0..num_samples {
        let (opp_hand, b1, b2) = sample_deal(rng, &remaining);
        let opp_setting = opp_pick(ev, opp_hand, model, rng);
        accumulate_against_all(ev, &settings, &opp_setting, &b1, &b2, &mut sums);
    }
    finalize_summary(settings, sums, num_samples)
}

/// Parallel version. Splits the sample budget across rayon's thread pool,
/// each worker seeds its own `SmallRng` from `base_seed ^ chunk_id` and
/// reduces into a shared [i64; 105] accumulator.
pub fn mc_evaluate_all_settings_par(
    ev: &Evaluator,
    hand: [Card; 7],
    model: OpponentModel,
    num_samples: usize,
    base_seed: u64,
) -> McSummary {
    debug_assert!(num_samples > 0, "need at least one sample");
    let settings = all_settings(hand);
    let remaining = remaining_45(hand);
    let n_settings = settings.len();

    let workers = rayon::current_num_threads().max(1);
    let chunk = (num_samples + workers - 1) / workers;

    let sums: Vec<i64> = (0..workers)
        .into_par_iter()
        .map(|wi| {
            let start = wi * chunk;
            if start >= num_samples {
                return vec![0i64; n_settings];
            }
            let end = ((wi + 1) * chunk).min(num_samples);
            // Derive per-worker seed so two workers don't share a stream.
            // `wrapping_mul` by a large odd constant gives good stream
            // separation for SmallRng (Xoshiro256++).
            let mut rng =
                SmallRng::seed_from_u64(base_seed.wrapping_add((wi as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)));
            let mut local = vec![0i64; n_settings];
            for _ in start..end {
                let (opp_hand, b1, b2) = sample_deal(&mut rng, &remaining);
                let opp_setting = opp_pick(ev, opp_hand, model, &mut rng);
                accumulate_against_all(ev, &settings, &opp_setting, &b1, &b2, &mut local);
            }
            local
        })
        .reduce(
            || vec![0i64; n_settings],
            |mut a, b| {
                for i in 0..n_settings {
                    a[i] += b[i];
                }
                a
            },
        );

    finalize_summary(settings, sums, num_samples)
}

/// Compute the 45 cards not in `hand`. Called once per MC run; the resulting
/// array is copied onto the stack inside `sample_deal`.
fn remaining_45(hand: [Card; 7]) -> [Card; 45] {
    let mut in_hand = [false; 52];
    for c in &hand {
        debug_assert!(!in_hand[c.index() as usize], "duplicate card in input hand");
        in_hand[c.index() as usize] = true;
    }
    let mut out = [Card(0); 45];
    let mut k = 0usize;
    for i in 0..52u8 {
        if !in_hand[i as usize] {
            out[k] = Card::from_index(i);
            k += 1;
        }
    }
    debug_assert_eq!(k, 45);
    out
}

/// Draw (opp_hand, board1, board2) uniformly without replacement from the 45
/// remaining cards via partial Fisher-Yates over the first 17 positions.
///
/// Partial shuffle is ~17 RNG calls vs ~45 for a full shuffle. The draws are
/// uniform over the ordered 17-prefix, which is exactly the distribution we
/// want: opp's 7-card hand is unordered (any permutation yields the same
/// HandSetting enumeration), and the two 5-card boards are distinguishable
/// but each board's internal card order doesn't matter (tier evaluators
/// iterate all k-subsets).
#[inline]
fn sample_deal(
    rng: &mut SmallRng,
    remaining: &[Card; 45],
) -> ([Card; 7], [Card; 5], [Card; 5]) {
    let mut deck = *remaining;
    for i in 0..17 {
        let j = i + rng.gen_range(0..(45 - i));
        deck.swap(i, j);
    }
    let opp = [
        deck[0], deck[1], deck[2], deck[3], deck[4], deck[5], deck[6],
    ];
    let b1 = [deck[7], deck[8], deck[9], deck[10], deck[11]];
    let b2 = [deck[12], deck[13], deck[14], deck[15], deck[16]];
    (opp, b1, b2)
}

/// Choose the opponent's setting under the configured model.
#[inline]
fn opp_pick(
    _ev: &Evaluator,
    hand: [Card; 7],
    model: OpponentModel,
    rng: &mut SmallRng,
) -> HandSetting {
    use crate::opp_models::*;
    match model {
        OpponentModel::Random => random_setting(hand, rng),
        OpponentModel::MiddleFirstNaive => opp_middle_first_naive(hand),
        OpponentModel::MiddleFirstSuitAware => opp_middle_first_suit_aware(hand),
        OpponentModel::OmahaFirst => opp_omaha_first(hand),
        OpponentModel::TopDefensive => opp_top_defensive(hand),
        OpponentModel::RandomWeighted => opp_random_weighted(hand, rng),
        OpponentModel::BalancedHeuristic => opp_balanced_heuristic(hand),
        OpponentModel::HeuristicMixed { base, p_heuristic } => {
            if rng.gen::<f32>() < p_heuristic {
                match base {
                    MixedBase::MiddleFirstNaive => opp_middle_first_naive(hand),
                    MixedBase::MiddleFirstSuitAware => opp_middle_first_suit_aware(hand),
                    MixedBase::OmahaFirst => opp_omaha_first(hand),
                    MixedBase::TopDefensive => opp_top_defensive(hand),
                    MixedBase::BalancedHeuristic => opp_balanced_heuristic(hand),
                }
            } else {
                random_setting(hand, rng)
            }
        }
    }
}

/// Pick one of the 105 settings uniformly at random without materializing
/// the full 105-setting vector.
///
/// Uniform decomposition:
///   top_i  ∈ {0..7}                       — 7 outcomes
///   (a, b) ∈ unordered pairs of {0..6}    — 15 outcomes
/// Product: 105 = C(7,1) × C(6,2). Each factor is independent and drawn
/// uniformly, so the joint is uniform over the 105 settings.
#[inline]
fn random_setting(hand: [Card; 7], rng: &mut SmallRng) -> HandSetting {
    let top_i: usize = rng.gen_range(0..7);
    let mut remaining6 = [Card(0); 6];
    let mut k = 0usize;
    for i in 0..7 {
        if i != top_i {
            remaining6[k] = hand[i];
            k += 1;
        }
    }
    // Unordered pair from 6: draw a ∈ 0..6, then b ∈ 0..5 and shift b past a.
    // Each unordered {a,b} is hit by two ordered pairs → uniform 1/15.
    let a: usize = rng.gen_range(0..6);
    let mut b: usize = rng.gen_range(0..5);
    if b >= a {
        b += 1;
    }
    let mid = [remaining6[a], remaining6[b]];
    let mut bot = [Card(0); 4];
    let mut bk = 0usize;
    for i in 0..6 {
        if i != a && i != b {
            bot[bk] = remaining6[i];
            bk += 1;
        }
    }
    HandSetting {
        top: hand[top_i],
        mid,
        bot,
    }
}

/// Hot inner: for each of the 105 p1 settings, score against the shared
/// sample and fold p1 net points into `sums`.
#[inline]
fn accumulate_against_all(
    ev: &Evaluator,
    settings: &[HandSetting],
    opp_setting: &HandSetting,
    b1: &[Card; 5],
    b2: &[Card; 5],
    sums: &mut [i64],
) {
    debug_assert_eq!(settings.len(), sums.len());
    for (si, s) in settings.iter().enumerate() {
        let br = matchup_breakdown(ev, s, opp_setting, b1, b2);
        sums[si] += br.p1_points as i64;
    }
}

fn finalize_summary(settings: Vec<HandSetting>, sums: Vec<i64>, num_samples: usize) -> McSummary {
    let n = num_samples as f64;
    let mut results: Vec<McResult> = settings
        .into_iter()
        .zip(sums.into_iter())
        .map(|(setting, s)| McResult {
            setting,
            ev: s as f64 / n,
        })
        .collect();
    // Descending by EV. `partial_cmp` is fine: EVs are finite (net points are
    // bounded integers divided by a positive N), so no NaNs.
    results.sort_by(|a, b| b.ev.partial_cmp(&a.ev).unwrap());
    McSummary {
        results,
        num_samples,
    }
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
    fn remaining_has_45_unique_cards_complementary_to_hand() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let rem = remaining_45(hand);
        assert_eq!(rem.len(), 45);
        let mut seen = [false; 52];
        for c in &rem {
            assert!(!seen[c.index() as usize], "duplicate in remaining");
            seen[c.index() as usize] = true;
        }
        // The 45 remaining + the 7 in hand should cover all 52 exactly.
        for c in &hand {
            assert!(!seen[c.index() as usize], "hand card leaked into remaining");
            seen[c.index() as usize] = true;
        }
        assert!(seen.iter().all(|&b| b));
    }

    #[test]
    fn sample_deal_draws_17_distinct_cards_disjoint_from_hand() {
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let rem = remaining_45(hand);
        let mut rng = SmallRng::seed_from_u64(42);
        for _ in 0..100 {
            let (opp, b1, b2) = sample_deal(&mut rng, &rem);
            let mut seen = [false; 52];
            // Hand cards must not appear in any draw.
            for c in &hand {
                seen[c.index() as usize] = true;
            }
            for c in opp.iter().chain(b1.iter()).chain(b2.iter()) {
                assert!(
                    !seen[c.index() as usize],
                    "duplicate or hand-collision in draw: {}",
                    c
                );
                seen[c.index() as usize] = true;
            }
        }
    }

    #[test]
    fn random_setting_is_always_valid() {
        // A valid setting uses each of the 7 cards exactly once, split as
        // 1/2/4 across top/mid/bot.
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let mut rng = SmallRng::seed_from_u64(1);
        for _ in 0..500 {
            let s = random_setting(hand, &mut rng);
            let all = s.all_cards();
            let got: std::collections::BTreeSet<_> = all.iter().copied().collect();
            let want: std::collections::BTreeSet<_> = hand.iter().copied().collect();
            assert_eq!(got, want, "setting {} does not use all 7 cards", s);
        }
    }

    #[test]
    fn random_setting_hits_all_105_possibilities_eventually() {
        // Sanity for uniformity: at N=100_000, we should hit every one of the
        // 105 canonical settings at least once. This doesn't prove uniformity
        // (that's the geometry of the decomposition), it only guards against
        // a stuck/bucketed RNG.
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let canonical = all_settings(hand);
        let canonical_set: std::collections::HashSet<_> = canonical
            .iter()
            .map(|s| {
                let mut m = s.mid;
                m.sort_unstable_by(|a, b| b.0.cmp(&a.0));
                let mut b = s.bot;
                b.sort_unstable_by(|a, b| b.0.cmp(&a.0));
                (s.top.0, m, b)
            })
            .collect();
        assert_eq!(canonical_set.len(), 105);

        let mut rng = SmallRng::seed_from_u64(7);
        let mut hit = std::collections::HashSet::new();
        for _ in 0..100_000 {
            let s = random_setting(hand, &mut rng);
            let mut m = s.mid;
            m.sort_unstable_by(|a, b| b.0.cmp(&a.0));
            let mut b = s.bot;
            b.sort_unstable_by(|a, b| b.0.cmp(&a.0));
            let key = (s.top.0, m, b);
            assert!(
                canonical_set.contains(&key),
                "random_setting produced a non-canonical slot"
            );
            hit.insert(key);
        }
        assert_eq!(
            hit.len(),
            105,
            "expected all 105 settings to appear across 100k draws; got {}",
            hit.len()
        );
    }

    #[test]
    fn mc_single_setting_seeded_reproducible() {
        let ev = Evaluator::build();
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let settings = all_settings(hand);
        let target = &settings[0];
        let mut r1 = SmallRng::seed_from_u64(12345);
        let mut r2 = SmallRng::seed_from_u64(12345);
        let a = mc_evaluate_setting(&ev, hand, target, OpponentModel::Random, 200, &mut r1);
        let b = mc_evaluate_setting(&ev, hand, target, OpponentModel::Random, 200, &mut r2);
        assert_eq!(a, b, "same seed must give same EV");
    }

    #[test]
    fn mc_all_settings_returns_sorted_105() {
        let ev = Evaluator::build();
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let mut rng = SmallRng::seed_from_u64(99);
        let summary = mc_evaluate_all_settings(&ev, hand, OpponentModel::Random, 200, &mut rng);
        assert_eq!(summary.results.len(), 105);
        for w in summary.results.windows(2) {
            assert!(w[0].ev >= w[1].ev, "not sorted descending");
        }
    }

    #[test]
    fn mc_par_matches_serial_at_single_worker_seed() {
        // When there's one rayon worker, the parallel path is the serial path
        // with a specific seeding scheme. Force a single worker by running
        // inside a custom thread pool.
        let ev = Evaluator::build();
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let pool = rayon::ThreadPoolBuilder::new()
            .num_threads(1)
            .build()
            .unwrap();
        let s_par = pool.install(|| {
            mc_evaluate_all_settings_par(&ev, hand, OpponentModel::Random, 500, 777)
        });
        // Serial path with the same per-worker seed formula (wi=0 → base_seed).
        let mut rng = SmallRng::seed_from_u64(777u64.wrapping_add(0));
        let s_ser = mc_evaluate_all_settings(&ev, hand, OpponentModel::Random, 500, &mut rng);
        assert_eq!(s_par.results.len(), s_ser.results.len());
        // EV values must match exactly (same RNG stream → same samples).
        for (p, s) in s_par.results.iter().zip(s_ser.results.iter()) {
            assert_eq!(
                p.ev, s.ev,
                "par vs serial EV mismatch with 1 worker: {} vs {}",
                p.ev, s.ev
            );
        }
    }

    #[test]
    fn mc_par_top1_stable_across_worker_counts_at_large_n() {
        // Different worker counts lead to different per-sample RNG streams
        // (each worker seeds from `base_seed + wi * phi`), so EVs differ by
        // Monte Carlo noise. At N=5000 the noise is small enough that the
        // top-1 setting should agree — and that's the only property we use
        // the parallel path for in downstream sprints.
        let ev = Evaluator::build();
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let pool1 = rayon::ThreadPoolBuilder::new()
            .num_threads(1)
            .build()
            .unwrap();
        let pool4 = rayon::ThreadPoolBuilder::new()
            .num_threads(4)
            .build()
            .unwrap();
        let s1 = pool1
            .install(|| mc_evaluate_all_settings_par(&ev, hand, OpponentModel::Random, 5000, 123));
        let s4 = pool4
            .install(|| mc_evaluate_all_settings_par(&ev, hand, OpponentModel::Random, 5000, 123));
        let key = |s: &HandSetting| {
            let mut m = s.mid;
            m.sort_unstable_by(|a, b| b.0.cmp(&a.0));
            let mut b = s.bot;
            b.sort_unstable_by(|a, b| b.0.cmp(&a.0));
            (s.top.0, m, b)
        };
        assert_eq!(
            key(&s1.best().setting),
            key(&s4.best().setting),
            "best setting should agree at N=5000 regardless of worker count"
        );
    }

    #[test]
    fn heuristic_mixed_dispatch_uses_base_at_p1() {
        // p_heuristic = 1 → always heuristic variant (here, MFSuitAware).
        // (p = 0 just behaves like Random, covered by random_setting tests.)
        use crate::opp_models::opp_middle_first_suit_aware;
        let ev = Evaluator::build();
        let hand = seven("As Ac Kh Qd Jc Ts 9h");
        let mut rng = SmallRng::seed_from_u64(42);
        let always_heur = opp_middle_first_suit_aware(hand);
        for _ in 0..50 {
            let picked = opp_pick(
                &ev,
                hand,
                OpponentModel::HeuristicMixed {
                    base: MixedBase::MiddleFirstSuitAware,
                    p_heuristic: 1.0,
                },
                &mut rng,
            );
            assert_eq!(picked, always_heur, "p=1.0 should always yield the base heuristic's setting");
        }
    }

    #[test]
    fn mc_convergence_top1_stable_from_n1000() {
        // At N=1000 the best-setting identity should match N=10000 for a
        // "not pathologically close" hand. Use a broadway-ish hand that has
        // a clear top-tier anchor (the deuce).
        let ev = Evaluator::build();
        let hand = seven("As Kh Qd Jc Ts 9h 2d");
        let mut r1 = SmallRng::seed_from_u64(2024);
        let mut r2 = SmallRng::seed_from_u64(4048);
        let s1 = mc_evaluate_all_settings(&ev, hand, OpponentModel::Random, 1000, &mut r1);
        let s2 = mc_evaluate_all_settings(&ev, hand, OpponentModel::Random, 10000, &mut r2);
        let key = |s: &HandSetting| {
            let mut m = s.mid;
            m.sort_unstable_by(|a, b| b.0.cmp(&a.0));
            let mut b = s.bot;
            b.sort_unstable_by(|a, b| b.0.cmp(&a.0));
            (s.top.0, m, b)
        };
        assert_eq!(
            key(&s1.best().setting),
            key(&s2.best().setting),
            "best setting should be stable from N=1000 to N=10000"
        );
    }
}
