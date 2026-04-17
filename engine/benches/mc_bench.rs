//! Monte Carlo benchmarks.
//!
//! The headline target from Sprint 2: **1 hand × 105 settings × 1000 samples
//! in <500 ms**, single-thread. Also measure:
//!   - single-setting MC at N=1000 (budget <5 ms) — the inner building block
//!   - parallel all-settings path (no explicit budget; scaling matters)
//!
//! Criterion reports wall-clock per invocation, so the numbers here are
//! directly comparable to the <500 ms ceiling.

use std::hint::black_box;
use std::time::Duration;

use criterion::{criterion_group, criterion_main, Criterion};
use rand::rngs::SmallRng;
use rand::SeedableRng;

use tw_engine::{
    all_settings, mc_evaluate_all_settings, mc_evaluate_all_settings_par, mc_evaluate_setting,
    parse_hand, Card, Evaluator, OpponentModel,
};

fn seven(s: &str) -> [Card; 7] {
    let v = parse_hand(s).unwrap();
    [v[0], v[1], v[2], v[3], v[4], v[5], v[6]]
}

fn bench_mc_single_setting_1k(c: &mut Criterion) {
    let ev = Evaluator::build();
    let hand = seven("As Kh Qd Jc Ts 9h 2d");
    let setting = all_settings(hand)[0];
    let mut group = c.benchmark_group("mc_single_setting");
    // <5 ms budget. Sample size tuned so criterion has room to detect regressions.
    group.sample_size(30);
    group.measurement_time(Duration::from_secs(8));
    group.bench_function("N=1000_random_opp", |b| {
        let mut rng = SmallRng::seed_from_u64(1);
        b.iter(|| {
            black_box(mc_evaluate_setting(
                &ev,
                black_box(hand),
                black_box(&setting),
                OpponentModel::Random,
                1000,
                &mut rng,
            ));
        })
    });
    group.finish();
}

fn bench_mc_all_settings_1k_serial(c: &mut Criterion) {
    let ev = Evaluator::build();
    let hand = seven("As Kh Qd Jc Ts 9h 2d");
    let mut group = c.benchmark_group("mc_all_settings_serial");
    // The 500 ms headline target. One iteration is ~200-300 ms, so 10 samples
    // give criterion enough signal without dragging the bench into minutes.
    group.sample_size(10);
    group.measurement_time(Duration::from_secs(30));
    group.bench_function("105x1000_random_opp", |b| {
        let mut rng = SmallRng::seed_from_u64(42);
        b.iter(|| {
            black_box(mc_evaluate_all_settings(
                &ev,
                black_box(hand),
                OpponentModel::Random,
                1000,
                &mut rng,
            ));
        })
    });
    group.finish();
}

fn bench_mc_all_settings_1k_parallel(c: &mut Criterion) {
    let ev = Evaluator::build();
    let hand = seven("As Kh Qd Jc Ts 9h 2d");
    let mut group = c.benchmark_group("mc_all_settings_parallel");
    group.sample_size(10);
    group.measurement_time(Duration::from_secs(20));
    group.bench_function("105x1000_random_opp_par", |b| {
        b.iter(|| {
            black_box(mc_evaluate_all_settings_par(
                &ev,
                black_box(hand),
                OpponentModel::Random,
                1000,
                42,
            ));
        })
    });
    group.finish();
}

criterion_group!(
    benches,
    bench_mc_single_setting_1k,
    bench_mc_all_settings_1k_serial,
    bench_mc_all_settings_1k_parallel,
);
criterion_main!(benches);
