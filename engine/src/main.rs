//! CLI entry point.
//!
//! Sprint 0: `eval` — enumerate all 105 settings for a 7-card hand.
//! Sprint 2: `mc`   — Monte Carlo EV of all 105 settings vs. a sampled opponent.
//! Sprint 3: `enumerate-canonical` / `solve` / `spot-check` — best-response
//!           pipeline over the full canonical 7-card hand space.

use std::path::PathBuf;
use std::process::ExitCode;
use std::time::Instant;

use clap::{Parser, Subcommand, ValueEnum};
use rand::rngs::SmallRng;
use rand::SeedableRng;

use tw_engine::{
    all_settings,
    best_response::{BrHeader, BrWriter, BR_VERSION},
    bytes_to_hand, category_name, count_canonical_hands, enumerate_canonical_hands, eval_middle,
    eval_omaha, eval_top, mc_evaluate_all_settings, mc_evaluate_all_settings_par, parse_hand,
    read_best_response_file, read_canonical_hands, solve_range, write_canonical_hands, Card,
    Evaluator, HandSetting, McSummary, OpponentModel,
};

#[derive(Parser, Debug)]
#[command(name = "tw-engine", version, about = "Taiwanese Poker solver engine")]
struct Cli {
    #[command(subcommand)]
    command: Command,
}

#[derive(Subcommand, Debug)]
enum Command {
    /// Enumerate all 105 hand settings for a 7-card hand.
    Eval {
        /// Seven cards separated by whitespace, e.g. "As Kh Qd Jc Ts 9h 2d".
        #[arg(long)]
        hand: String,

        /// Path to (or target for) the 5-card lookup table.
        #[arg(long, default_value = "../data/lookup_table.bin")]
        lookup: PathBuf,
    },

    /// Force a rebuild of the 5-card lookup table and write it to disk.
    BuildLookup {
        #[arg(long, default_value = "../data/lookup_table.bin")]
        out: PathBuf,
    },

    /// Monte Carlo EV of all 105 settings for a 7-card hand.
    Mc {
        /// Seven cards separated by whitespace, e.g. "As Kh Qd Jc Ts 9h 2d".
        #[arg(long)]
        hand: String,

        /// Number of Monte Carlo samples per setting (shared across all 105).
        #[arg(long, default_value_t = 1000)]
        samples: usize,

        /// Opponent model.
        #[arg(long, value_enum, default_value_t = Opp::Random)]
        opponent: Opp,

        /// Parallelize via rayon. Off by default so single-thread latency is
        /// visible; turn on for longer sample budgets.
        #[arg(long)]
        parallel: bool,

        /// Seed for the RNG. Fixed default so repeated calls are reproducible;
        /// override for independent runs.
        #[arg(long, default_value_t = 0xC0FFEE_u64)]
        seed: u64,

        /// How many top-ranked settings to display.
        #[arg(long, default_value_t = 10)]
        show_top: usize,

        /// Path to the 5-card lookup table.
        #[arg(long, default_value = "../data/lookup_table.bin")]
        lookup: PathBuf,
    },

    /// Count or enumerate all canonical 7-card hands under suit-permutation
    /// equivalence (Decision 006). Writes a flat binary list to --out.
    EnumerateCanonical {
        /// Output file for the canonical hand list.
        #[arg(long, default_value = "../data/canonical_hands.bin")]
        out: PathBuf,

        /// If set, only COUNT canonical hands — don't write them. Much cheaper
        /// when you want a quick sanity number on a new machine.
        #[arg(long)]
        count_only: bool,
    },

    /// Compute the best-response (highest-EV setting) for every canonical
    /// hand in `--canonical`, writing records to `--out`. Resumes from
    /// whatever is already in `--out`.
    Solve {
        #[arg(long, default_value = "../data/canonical_hands.bin")]
        canonical: PathBuf,

        #[arg(long, default_value = "../data/best_response.bin")]
        out: PathBuf,

        #[arg(long, default_value = "../data/lookup_table.bin")]
        lookup: PathBuf,

        /// Monte Carlo samples per hand.
        #[arg(long, default_value_t = 1000)]
        samples: u32,

        /// Base seed — combined with canonical_id for per-hand RNG streams.
        #[arg(long, default_value_t = 0xC0FFEE_u64)]
        seed: u64,

        /// Opponent model. Sprint 3 ships Random only; the enum is here so
        /// future sprints can swap.
        #[arg(long, value_enum, default_value_t = Opp::Random)]
        opponent: Opp,

        /// How many canonical hands per rayon block. Each block is flushed
        /// to disk on completion, so smaller blocks mean tighter checkpoints
        /// but slightly more syscall overhead.
        #[arg(long, default_value_t = 1000)]
        block_size: usize,

        /// Optional cap: process at most this many canonical hands starting
        /// from the resume offset. Use for pilot runs (e.g. --limit 1000 at
        /// --samples 100).
        #[arg(long)]
        limit: Option<usize>,
    },

    /// Print a summary + the first `--show` records from a best-response
    /// file alongside the canonical hand they correspond to.
    SpotCheck {
        #[arg(long, default_value = "../data/canonical_hands.bin")]
        canonical: PathBuf,

        #[arg(long, default_value = "../data/best_response.bin")]
        out: PathBuf,

        #[arg(long, default_value_t = 10)]
        show: usize,
    },
}

#[derive(Copy, Clone, Debug, ValueEnum)]
enum Opp {
    Random,
}

impl From<Opp> for OpponentModel {
    fn from(o: Opp) -> Self {
        match o {
            Opp::Random => OpponentModel::Random,
        }
    }
}

fn opp_tag(o: Opp) -> u32 {
    match o {
        Opp::Random => 0,
    }
}

fn main() -> ExitCode {
    let cli = Cli::parse();
    let r = match cli.command {
        Command::Eval { hand, lookup } => run_eval(&hand, &lookup),
        Command::BuildLookup { out } => run_build(&out),
        Command::Mc {
            hand,
            samples,
            opponent,
            parallel,
            seed,
            show_top,
            lookup,
        } => run_mc(&hand, samples, opponent.into(), parallel, seed, show_top, &lookup),
        Command::EnumerateCanonical { out, count_only } => run_enumerate(&out, count_only),
        Command::Solve {
            canonical,
            out,
            lookup,
            samples,
            seed,
            opponent,
            block_size,
            limit,
        } => run_solve(&canonical, &out, &lookup, samples, seed, opponent, block_size, limit),
        Command::SpotCheck {
            canonical,
            out,
            show,
        } => run_spot_check(&canonical, &out, show),
    };
    match r {
        Ok(()) => ExitCode::SUCCESS,
        Err(e) => {
            eprintln!("error: {e}");
            ExitCode::FAILURE
        }
    }
}

fn parse_seven(hand_str: &str) -> Result<[Card; 7], Box<dyn std::error::Error>> {
    let cards = parse_hand(hand_str)?;
    if cards.len() != 7 {
        return Err(format!("expected 7 cards, got {}", cards.len()).into());
    }
    Ok(cards.try_into().unwrap())
}

fn run_eval(
    hand_str: &str,
    lookup_path: &std::path::Path,
) -> Result<(), Box<dyn std::error::Error>> {
    let hand = parse_seven(hand_str)?;

    println!("Loading 5-card lookup table from {} ...", lookup_path.display());
    let ev = Evaluator::load_or_build(lookup_path)?;
    println!("Table ready.");

    let settings = all_settings(hand);
    println!(
        "\nHand: {} {} {} {} {} {} {}",
        hand[0], hand[1], hand[2], hand[3], hand[4], hand[5], hand[6]
    );
    println!("All {} possible settings:\n", settings.len());

    for (i, s) in settings.iter().enumerate() {
        let _ = (&ev, category_name);
        println!("{:>3}. {}", i + 1, s);
    }

    Ok(())
}

fn run_build(out: &std::path::Path) -> Result<(), Box<dyn std::error::Error>> {
    println!("Building 5-card lookup table (this takes ~1s in release)...");
    let ev = Evaluator::build();
    if let Some(parent) = out.parent() {
        std::fs::create_dir_all(parent)?;
    }
    let f = std::fs::File::create(out)?;
    let writer = std::io::BufWriter::new(f);
    bincode::serialize_into(writer, &ev)?;
    println!(
        "Wrote {} ({} entries)",
        out.display(),
        tw_engine::lookup::NUM_5CARD
    );
    Ok(())
}

fn run_mc(
    hand_str: &str,
    samples: usize,
    model: OpponentModel,
    parallel: bool,
    seed: u64,
    show_top: usize,
    lookup_path: &std::path::Path,
) -> Result<(), Box<dyn std::error::Error>> {
    if samples == 0 {
        return Err("--samples must be > 0".into());
    }
    let hand = parse_seven(hand_str)?;

    println!("Loading 5-card lookup table from {} ...", lookup_path.display());
    let ev = Evaluator::load_or_build(lookup_path)?;
    println!(
        "Table ready. Running {} Monte Carlo samples × 105 settings (opponent={:?}, parallel={}, seed={:#x}).",
        samples, model, parallel, seed
    );

    let t0 = Instant::now();
    let summary = if parallel {
        mc_evaluate_all_settings_par(&ev, hand, model, samples, seed)
    } else {
        let mut rng = SmallRng::seed_from_u64(seed);
        mc_evaluate_all_settings(&ev, hand, model, samples, &mut rng)
    };
    let elapsed = t0.elapsed();

    println!(
        "\nHand: {} {} {} {} {} {} {}",
        hand[0], hand[1], hand[2], hand[3], hand[4], hand[5], hand[6]
    );
    println!("Elapsed: {:.2?}  (N={} samples)\n", elapsed, summary.num_samples);

    let take = show_top.min(summary.results.len());
    println!("Top {} settings by EV:", take);
    println!(
        "{:>4} {:>8}  top            mid                 bot",
        "#", "EV"
    );
    for (i, r) in summary.results.iter().take(take).enumerate() {
        println!(
            "{:>4} {:>+8.3}  [{}]           [{} {}]             [{} {} {} {}]",
            i + 1,
            r.ev,
            r.setting.top,
            r.setting.mid[0],
            r.setting.mid[1],
            r.setting.bot[0],
            r.setting.bot[1],
            r.setting.bot[2],
            r.setting.bot[3],
        );
    }

    let best = &summary.results[0].setting;
    print_best_tier_categories(&ev, best, seed);

    println!(
        "\nSummary: best EV = {:+.3}, worst EV = {:+.3}, gap(1→2) = {:.3}",
        summary.best().ev,
        summary.worst().ev,
        summary.gap_first_to_second()
    );

    Ok(())
}

fn run_enumerate(
    out: &std::path::Path,
    count_only: bool,
) -> Result<(), Box<dyn std::error::Error>> {
    if count_only {
        println!("Counting canonical 7-card hands (suit-permutation equivalence)...");
        let t0 = Instant::now();
        let n = count_canonical_hands();
        let elapsed = t0.elapsed();
        println!(
            "Canonical hands: {n}  (C(52,7) = 133,784,560; ratio ≈ {:.3})",
            133_784_560.0 / n as f64
        );
        println!("Elapsed: {:.2?}", elapsed);
        return Ok(());
    }
    println!("Enumerating canonical 7-card hands...");
    let t0 = Instant::now();
    let hands = enumerate_canonical_hands();
    let elapsed_enum = t0.elapsed();
    println!(
        "Got {} canonical hands in {:.2?} (ratio ≈ {:.3}).",
        hands.len(),
        elapsed_enum,
        133_784_560.0 / hands.len() as f64
    );
    let t1 = Instant::now();
    write_canonical_hands(out, &hands)?;
    println!("Wrote {} in {:.2?}.", out.display(), t1.elapsed());
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn run_solve(
    canonical_path: &std::path::Path,
    out: &std::path::Path,
    lookup_path: &std::path::Path,
    samples: u32,
    seed: u64,
    opponent: Opp,
    block_size: usize,
    limit: Option<usize>,
) -> Result<(), Box<dyn std::error::Error>> {
    if samples == 0 {
        return Err("--samples must be > 0".into());
    }
    if block_size == 0 {
        return Err("--block-size must be > 0".into());
    }

    println!("Loading 5-card lookup table from {} ...", lookup_path.display());
    let ev = Evaluator::load_or_build(lookup_path)?;

    println!("Loading canonical hands from {} ...", canonical_path.display());
    let canonical = read_canonical_hands(canonical_path)?;
    println!("  {} canonical hands.", canonical.len());

    let header = BrHeader {
        version: BR_VERSION,
        samples,
        base_seed: seed,
        canonical_total: canonical.len() as u64,
        opp_model_tag: opp_tag(opponent),
        reserved: 0,
    };

    let mut writer = BrWriter::open_or_create(out, header)?;
    let resume_from = writer.resume_from as usize;
    if resume_from > canonical.len() {
        return Err(format!(
            "existing output has {} records but canonical list has only {}",
            resume_from,
            canonical.len()
        )
        .into());
    }
    if resume_from > 0 {
        println!("Resuming at canonical_id={} (file already has that many records).", resume_from);
    }

    let remaining = canonical.len() - resume_from;
    let target = match limit {
        Some(l) => l.min(remaining),
        None => remaining,
    };
    if target == 0 {
        println!("Nothing to do — file is complete (or --limit 0).");
        return Ok(());
    }

    let slice_end = resume_from + target;
    let slice = &canonical[resume_from..slice_end];
    println!(
        "Solving {} hands (ids {}..{}) at samples={} block_size={} ...",
        target, resume_from, slice_end, samples, block_size
    );

    let t0 = Instant::now();
    let total_target = target as u64;
    solve_range(
        &ev,
        slice,
        resume_from as u32,
        samples as usize,
        seed,
        block_size,
        &mut writer,
        |next_id, written_so_far, block_elapsed| {
            let progress = written_so_far as f64 / total_target as f64;
            let eta_secs = if written_so_far > 0 {
                let elapsed = t0.elapsed().as_secs_f64();
                elapsed / progress - elapsed
            } else {
                f64::INFINITY
            };
            println!(
                "  id={next_id:>10}  wrote={written_so_far}/{total_target}  \
                 block={block_elapsed:>7.2?}  ETA={:>7.1}s",
                eta_secs
            );
        },
    )?;
    let elapsed = t0.elapsed();
    println!(
        "Done in {:.2?}. Wrote {} records to {}.",
        elapsed,
        target,
        out.display()
    );
    Ok(())
}

fn run_spot_check(
    canonical_path: &std::path::Path,
    out: &std::path::Path,
    show: usize,
) -> Result<(), Box<dyn std::error::Error>> {
    let canonical = read_canonical_hands(canonical_path)?;
    let (header, records) = read_best_response_file(out)?;
    println!("Best-response file: {}", out.display());
    println!(
        "  header: samples={} base_seed={:#x} canonical_total={} opp={}",
        header.samples, header.base_seed, header.canonical_total, header.opp_model_tag
    );
    println!("  records: {} of {}", records.len(), canonical.len());

    if records.is_empty() {
        return Ok(());
    }

    let show = show.min(records.len());
    println!("\nFirst {} records:", show);
    for r in records.iter().take(show) {
        let id = r.canonical_id as usize;
        if id >= canonical.len() {
            println!("  id={id:>10}  (out of range for canonical list — mismatched files?)");
            continue;
        }
        let hand = bytes_to_hand(&canonical[id]);
        let settings = all_settings(hand);
        let s = &settings[r.best_setting_index as usize];
        println!(
            "  id={id:>10}  hand=[{}]  best=[top {}  mid {} {}  bot {} {} {} {}]  EV={:+.3}",
            fmt_hand(&hand),
            s.top, s.mid[0], s.mid[1], s.bot[0], s.bot[1], s.bot[2], s.bot[3],
            r.best_ev
        );
    }

    // EV distribution summary.
    let min = records.iter().map(|r| r.best_ev).fold(f32::INFINITY, f32::min);
    let max = records.iter().map(|r| r.best_ev).fold(f32::NEG_INFINITY, f32::max);
    let mean: f64 =
        records.iter().map(|r| r.best_ev as f64).sum::<f64>() / records.len() as f64;
    println!(
        "\nBest-EV distribution: min={:+.3}  mean={:+.3}  max={:+.3}",
        min, mean, max
    );

    // Setting-index frequency top 10.
    let mut freq = [0u64; 105];
    for r in &records {
        freq[r.best_setting_index as usize] += 1;
    }
    let mut ordered: Vec<(u8, u64)> = (0..105u8).map(|i| (i, freq[i as usize])).collect();
    ordered.sort_by(|a, b| b.1.cmp(&a.1));
    println!("\nTop-10 most-chosen setting indices:");
    for (i, (idx, count)) in ordered.iter().take(10).enumerate() {
        println!(
            "  {:>2}. setting_idx={:>3}  count={:>7}  ({:.1}%)",
            i + 1,
            idx,
            count,
            100.0 * *count as f64 / records.len() as f64
        );
    }
    Ok(())
}

fn fmt_hand(hand: &[Card; 7]) -> String {
    format!(
        "{} {} {} {} {} {} {}",
        hand[0], hand[1], hand[2], hand[3], hand[4], hand[5], hand[6]
    )
}

/// Diagnostic: deal one pair of sample boards from the remaining deck and
/// print the category the best setting makes at each tier on each board. Gives
/// the user a quick intuition for why the setting was preferred; it is NOT an
/// EV contribution.
fn print_best_tier_categories(ev: &Evaluator, best: &HandSetting, seed: u64) {
    let mut rng = SmallRng::seed_from_u64(seed.wrapping_add(0xDEAD_BEEF));
    let mut in_hand = [false; 52];
    let all7 = best.all_cards();
    for c in &all7 {
        in_hand[c.index() as usize] = true;
    }
    let mut rem = Vec::with_capacity(45);
    for i in 0..52u8 {
        if !in_hand[i as usize] {
            rem.push(Card::from_index(i));
        }
    }
    use rand::Rng;
    for i in 0..10 {
        let j = i + rng.gen_range(0..(rem.len() - i));
        rem.swap(i, j);
    }
    let b1 = [rem[0], rem[1], rem[2], rem[3], rem[4]];
    let b2 = [rem[5], rem[6], rem[7], rem[8], rem[9]];

    let top_b1 = eval_top(ev, best.top, b1);
    let top_b2 = eval_top(ev, best.top, b2);
    let mid_b1 = eval_middle(ev, best.mid, b1);
    let mid_b2 = eval_middle(ev, best.mid, b2);
    let bot_b1 = eval_omaha(ev, best.bot, b1);
    let bot_b2 = eval_omaha(ev, best.bot, b2);

    println!("\nBest setting tier breakdown on one sample board pair:");
    println!(
        "  Board 1: {} {} {} {} {}",
        b1[0], b1[1], b1[2], b1[3], b1[4]
    );
    println!(
        "    top={} mid={} bot={}",
        category_name(top_b1),
        category_name(mid_b1),
        category_name(bot_b1)
    );
    println!(
        "  Board 2: {} {} {} {} {}",
        b2[0], b2[1], b2[2], b2[3], b2[4]
    );
    println!(
        "    top={} mid={} bot={}",
        category_name(top_b2),
        category_name(mid_b2),
        category_name(bot_b2)
    );
}

#[allow(dead_code)]
fn _compile_guard_mcsummary(_: McSummary) {}
