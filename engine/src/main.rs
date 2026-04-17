//! CLI entry point.
//!
//! Sprint 0: `eval` — enumerate all 105 settings for a 7-card hand.
//! Sprint 2: `mc`   — Monte Carlo EV of all 105 settings vs. a sampled opponent.

use std::path::PathBuf;
use std::process::ExitCode;
use std::time::Instant;

use clap::{Parser, Subcommand, ValueEnum};
use rand::rngs::SmallRng;
use rand::SeedableRng;

use tw_engine::{
    all_settings, category_name, eval_middle, eval_omaha, eval_top, mc_evaluate_all_settings,
    mc_evaluate_all_settings_par, parse_hand, Card, Evaluator, HandSetting, McSummary,
    OpponentModel,
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

fn main() -> ExitCode {
    let cli = Cli::parse();
    match cli.command {
        Command::Eval { hand, lookup } => match run_eval(&hand, &lookup) {
            Ok(()) => ExitCode::SUCCESS,
            Err(e) => {
                eprintln!("error: {e}");
                ExitCode::FAILURE
            }
        },
        Command::BuildLookup { out } => match run_build(&out) {
            Ok(()) => ExitCode::SUCCESS,
            Err(e) => {
                eprintln!("error: {e}");
                ExitCode::FAILURE
            }
        },
        Command::Mc {
            hand,
            samples,
            opponent,
            parallel,
            seed,
            show_top,
            lookup,
        } => match run_mc(&hand, samples, opponent.into(), parallel, seed, show_top, &lookup) {
            Ok(()) => ExitCode::SUCCESS,
            Err(e) => {
                eprintln!("error: {e}");
                ExitCode::FAILURE
            }
        },
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

    // Tier breakdown of the best setting, evaluated against sampled boards
    // once for color. Not a full MC by tier — just surfaces what hand the
    // best setting makes on a random board pair for the user's intuition.
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

/// Diagnostic: deal one pair of sample boards from the remaining deck and
/// print the category the best setting makes at each tier on each board. Gives
/// the user a quick intuition for why the setting was preferred; it is NOT an
/// EV contribution.
fn print_best_tier_categories(ev: &Evaluator, best: &HandSetting, seed: u64) {
    let mut rng = SmallRng::seed_from_u64(seed.wrapping_add(0xDEAD_BEEF));
    // Reconstruct "remaining 45" by excluding the best setting's 7 cards.
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
    // Fisher-Yates partial shuffle on the first 10 to get 2 boards.
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
