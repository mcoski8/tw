//! 5-card evaluator benchmark. Target: < 50 ns per `eval_5` call.

use std::hint::black_box;

use criterion::{criterion_group, criterion_main, Criterion};

use tw_engine::{Card, Evaluator};

fn bench_eval_5(c: &mut Criterion) {
    let ev = Evaluator::build();

    // A handful of hands covering several categories — we draw from them in
    // rotation so the benchmark doesn't sit in one branch of the evaluator.
    let hands: [[Card; 5]; 8] = [
        [Card::new(14, 3), Card::new(13, 3), Card::new(12, 3), Card::new(11, 3), Card::new(10, 3)], // royal
        [Card::new(9, 3), Card::new(8, 3), Card::new(7, 3), Card::new(6, 3), Card::new(5, 3)],      // straight flush
        [Card::new(14, 0), Card::new(14, 1), Card::new(14, 2), Card::new(14, 3), Card::new(2, 0)],  // quads
        [Card::new(14, 0), Card::new(14, 1), Card::new(14, 2), Card::new(13, 0), Card::new(13, 1)], // full
        [Card::new(14, 0), Card::new(12, 0), Card::new(9, 0), Card::new(5, 0), Card::new(2, 0)],    // flush
        [Card::new(14, 0), Card::new(13, 1), Card::new(12, 2), Card::new(11, 3), Card::new(10, 0)], // broadway
        [Card::new(14, 0), Card::new(14, 1), Card::new(13, 0), Card::new(13, 1), Card::new(2, 0)],  // two pair
        [Card::new(14, 0), Card::new(13, 1), Card::new(12, 2), Card::new(11, 3), Card::new(9, 0)],  // high card
    ];

    c.bench_function("eval_5_rotating", |b| {
        let mut i = 0usize;
        b.iter(|| {
            let cards = hands[i & 7];
            i = i.wrapping_add(1);
            black_box(ev.eval_5(black_box(cards)));
        })
    });
}

criterion_group!(benches, bench_eval_5);
criterion_main!(benches);
