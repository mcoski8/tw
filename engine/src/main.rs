//! CLI entry point. Sprint 0 supports `eval --hand "..."` which prints all 105
//! settings for a 7-card hand. EV computation lands in later sprints.

use std::path::PathBuf;
use std::process::ExitCode;

use clap::{Parser, Subcommand};

use tw_engine::{all_settings, category_name, parse_hand, Evaluator};

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
    }
}

fn run_eval(hand_str: &str, lookup_path: &std::path::Path) -> Result<(), Box<dyn std::error::Error>> {
    let cards = parse_hand(hand_str)?;
    if cards.len() != 7 {
        return Err(format!("expected 7 cards, got {}", cards.len()).into());
    }
    let hand: [_; 7] = cards.try_into().unwrap();

    println!("Loading 5-card lookup table from {} ...", lookup_path.display());
    let ev = Evaluator::load_or_build(lookup_path)?;
    println!("Table ready.");

    let settings = all_settings(hand);
    println!("\nHand: {} {} {} {} {} {} {}", hand[0], hand[1], hand[2], hand[3], hand[4], hand[5], hand[6]);
    println!("All {} possible settings:\n", settings.len());

    for (i, s) in settings.iter().enumerate() {
        // Top tier is a single card — its standalone "hand rank" vs a board
        // needs board cards, so for now we just show the card. Middle is two
        // cards, also not a 5-card eval on its own. Sprint 1 adds tier-aware
        // evaluators. For Sprint 0 we surface the bottom-4 alone as a peek at
        // the hand eval plumbing — append 1 placeholder card? No: skip rank
        // info entirely to avoid implying we're doing tier evaluation yet.
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
    println!("Wrote {} ({} entries)", out.display(), tw_engine::lookup::NUM_5CARD);
    Ok(())
}
