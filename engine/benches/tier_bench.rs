//! Tier evaluator + full-matchup benchmarks.
//!
//! Targets (from docs/modules/hand-evaluation.md + compute-pipeline.md):
//!   - Top:    <100 ns  (6 lookups)
//!   - Middle: <250 ns  (21 lookups)
//!   - Omaha:  <700 ns  (60 lookups)
//!   - Full matchup (3 tiers × 2 boards + scoop check): <2 µs
//!
//! Rotating input arrays keep the CPU branch predictor honest — measuring the
//! same straight flush over and over would mislead us about real workload
//! costs in later sprints.

use std::hint::black_box;

use criterion::{criterion_group, criterion_main, Criterion};

use tw_engine::{
    eval_middle, eval_omaha, eval_top, matchup_breakdown, Card, Evaluator, HandSetting,
};

fn mk_setting(top: (u8, u8), mid: [(u8, u8); 2], bot: [(u8, u8); 4]) -> HandSetting {
    HandSetting {
        top: Card::new(top.0, top.1),
        mid: [Card::new(mid[0].0, mid[0].1), Card::new(mid[1].0, mid[1].1)],
        bot: [
            Card::new(bot[0].0, bot[0].1),
            Card::new(bot[1].0, bot[1].1),
            Card::new(bot[2].0, bot[2].1),
            Card::new(bot[3].0, bot[3].1),
        ],
    }
}

fn bench_top(c: &mut Criterion) {
    let ev = Evaluator::build();
    // Mix of 8 (hole, board) pairs covering high-card, pair, trips, straight,
    // flush-draw misses, etc., so the 6-lookup inner loop isn't trivially
    // one-branch.
    let cases: [(Card, [Card; 5]); 8] = [
        // A + KQJT2 = broadway straight
        (Card::new(14, 3), [Card::new(13, 1), Card::new(12, 2), Card::new(11, 0), Card::new(10, 3), Card::new(2, 0)]),
        // 7 + 77KQ3 = trips
        (Card::new(7, 3), [Card::new(7, 2), Card::new(7, 1), Card::new(13, 0), Card::new(12, 3), Card::new(3, 0)]),
        // 2 + dry board = high card
        (Card::new(2, 0), [Card::new(9, 1), Card::new(8, 2), Card::new(4, 3), Card::new(6, 0), Card::new(13, 1)]),
        // K + flushy board (K of off-suit) = K-high high card likely
        (Card::new(13, 0), [Card::new(14, 3), Card::new(12, 3), Card::new(10, 3), Card::new(9, 3), Card::new(3, 3)]),
        // 9 + wheel-ish board
        (Card::new(9, 1), [Card::new(14, 0), Card::new(2, 1), Card::new(3, 2), Card::new(4, 3), Card::new(5, 0)]),
        // J + paired board
        (Card::new(11, 2), [Card::new(11, 1), Card::new(11, 0), Card::new(7, 3), Card::new(4, 0), Card::new(2, 1)]),
        // A + monochrome board (flush not possible with off-suit A)
        (Card::new(14, 2), [Card::new(9, 3), Card::new(7, 3), Card::new(5, 3), Card::new(4, 3), Card::new(2, 3)]),
        // 6 + straightish board
        (Card::new(6, 0), [Card::new(7, 1), Card::new(8, 2), Card::new(9, 3), Card::new(10, 0), Card::new(13, 1)]),
    ];
    c.bench_function("eval_top_rotating", |b| {
        let mut i = 0usize;
        b.iter(|| {
            let (hole, board) = cases[i & 7];
            i = i.wrapping_add(1);
            black_box(eval_top(&ev, black_box(hole), black_box(board)));
        })
    });
}

fn bench_middle(c: &mut Criterion) {
    let ev = Evaluator::build();
    let cases: [([Card; 2], [Card; 5]); 8] = [
        // AA + dry board = pair of aces
        ([Card::new(14, 0), Card::new(14, 1)], [Card::new(13, 2), Card::new(12, 3), Card::new(11, 0), Card::new(3, 1), Card::new(2, 2)]),
        // 87s + 654AK = 8-high straight
        ([Card::new(8, 3), Card::new(7, 3)], [Card::new(6, 3), Card::new(5, 2), Card::new(4, 1), Card::new(14, 0), Card::new(13, 0)]),
        // junk + strong board
        ([Card::new(2, 0), Card::new(3, 1)], [Card::new(13, 0), Card::new(13, 1), Card::new(13, 2), Card::new(7, 3), Card::new(7, 1)]),
        // suited connectors + monochrome board
        ([Card::new(10, 3), Card::new(9, 3)], [Card::new(7, 3), Card::new(6, 3), Card::new(2, 3), Card::new(4, 0), Card::new(3, 0)]),
        // offsuit broadway + low board
        ([Card::new(14, 1), Card::new(13, 2)], [Card::new(6, 0), Card::new(5, 0), Card::new(4, 0), Card::new(3, 1), Card::new(2, 2)]),
        // pocket pair + paired board (boat potential)
        ([Card::new(9, 0), Card::new(9, 1)], [Card::new(9, 2), Card::new(5, 3), Card::new(5, 0), Card::new(12, 1), Card::new(2, 2)]),
        // wheel wheel
        ([Card::new(14, 0), Card::new(2, 1)], [Card::new(3, 2), Card::new(4, 3), Card::new(5, 0), Card::new(13, 1), Card::new(12, 2)]),
        // trash
        ([Card::new(7, 0), Card::new(2, 1)], [Card::new(9, 2), Card::new(6, 3), Card::new(4, 0), Card::new(12, 1), Card::new(3, 2)]),
    ];
    c.bench_function("eval_middle_rotating", |b| {
        let mut i = 0usize;
        b.iter(|| {
            let (hole, board) = cases[i & 7];
            i = i.wrapping_add(1);
            black_box(eval_middle(&ev, black_box(hole), black_box(board)));
        })
    });
}

fn bench_omaha(c: &mut Criterion) {
    let ev = Evaluator::build();
    // 8 (hole, board) pairs covering the interesting Omaha cases: double
    // suited → flush, four-to-straight board, trips on board, wheel, etc.
    let cases: [([Card; 4], [Card; 5]); 8] = [
        // As Ks Qs Js (4 suited) + Ts 9s 8s junk junk → straight flush
        ([Card::new(14, 3), Card::new(13, 3), Card::new(12, 3), Card::new(11, 3)], [Card::new(10, 3), Card::new(9, 3), Card::new(8, 3), Card::new(2, 0), Card::new(3, 1)]),
        // AAKK + dry = two pair
        ([Card::new(14, 0), Card::new(14, 1), Card::new(13, 2), Card::new(13, 3)], [Card::new(7, 0), Card::new(5, 1), Card::new(9, 2), Card::new(3, 3), Card::new(2, 0)]),
        // Connected hole + straight board
        ([Card::new(10, 0), Card::new(11, 1), Card::new(2, 2), Card::new(3, 3)], [Card::new(6, 0), Card::new(7, 1), Card::new(8, 2), Card::new(9, 3), Card::new(13, 0)]),
        // Double suited rainbow
        ([Card::new(12, 0), Card::new(11, 0), Card::new(10, 1), Card::new(9, 1)], [Card::new(8, 2), Card::new(7, 3), Card::new(2, 0), Card::new(3, 1), Card::new(4, 2)]),
        // Pair hole + pair board
        ([Card::new(13, 0), Card::new(13, 1), Card::new(2, 2), Card::new(3, 3)], [Card::new(7, 0), Card::new(7, 1), Card::new(9, 2), Card::new(12, 3), Card::new(5, 0)]),
        // Trips on board + pair in hand (boat)
        ([Card::new(13, 0), Card::new(13, 1), Card::new(2, 2), Card::new(3, 3)], [Card::new(14, 0), Card::new(14, 1), Card::new(14, 2), Card::new(4, 3), Card::new(5, 0)]),
        // All four hole clubs, zero board clubs (no flush legal)
        ([Card::new(3, 0), Card::new(4, 0), Card::new(5, 0), Card::new(6, 0)], [Card::new(14, 1), Card::new(13, 1), Card::new(9, 2), Card::new(10, 3), Card::new(2, 2)]),
        // Wheel via 2+3
        ([Card::new(14, 3), Card::new(2, 1), Card::new(9, 0), Card::new(9, 1)], [Card::new(3, 2), Card::new(4, 0), Card::new(5, 3), Card::new(13, 1), Card::new(12, 0)]),
    ];
    c.bench_function("eval_omaha_rotating", |b| {
        let mut i = 0usize;
        b.iter(|| {
            let (hole, board) = cases[i & 7];
            i = i.wrapping_add(1);
            black_box(eval_omaha(&ev, black_box(hole), black_box(board)));
        })
    });
}

fn bench_full_matchup(c: &mut Criterion) {
    let ev = Evaluator::build();
    // One realistic scoop-fixture matchup: 3 tiers × 2 boards + scoop check.
    // This is the measurement that matters most for Sprint 2's Monte Carlo —
    // every sample inside the MC inner loop calls matchup_breakdown once.
    let p1 = mk_setting((14, 0), [(14, 3), (13, 0)], [(13, 3), (12, 0), (12, 3), (11, 0)]);
    let p2 = mk_setting((3, 0), [(4, 1), (5, 2)], [(6, 1), (7, 0), (8, 1), (10, 0)]);
    let board1: [Card; 5] = [
        Card::new(6, 3), Card::new(7, 1), Card::new(9, 2), Card::new(10, 2), Card::new(11, 3),
    ];
    let board2: [Card; 5] = [
        Card::new(6, 2), Card::new(7, 3), Card::new(9, 1), Card::new(10, 1), Card::new(11, 2),
    ];
    c.bench_function("matchup_breakdown_scoop_fixture", |b| {
        b.iter(|| {
            black_box(matchup_breakdown(
                &ev,
                black_box(&p1),
                black_box(&p2),
                black_box(&board1),
                black_box(&board2),
            ));
        })
    });
}

criterion_group!(benches, bench_top, bench_middle, bench_omaha, bench_full_matchup);
criterion_main!(benches);
