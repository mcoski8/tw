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
    read_best_response_file, read_canonical_hands, solve_one, solve_range,
    write_canonical_hands, Card, Evaluator, HandSetting, McSummary, MixedBase, OpponentModel,
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

        /// Opponent model. `mixed` uses --mix-p and --mix-base.
        #[arg(long, value_enum, default_value_t = Opp::Random)]
        opponent: Opp,

        /// For --opponent mixed: base heuristic to wrap.
        #[arg(long, value_enum, default_value_t = MixBaseCli::Mfsuitaware)]
        mix_base: MixBaseCli,

        /// For --opponent mixed: fraction of samples that use the heuristic.
        #[arg(long, default_value_t = 0.8)]
        mix_p: f32,

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

        /// Emit all 105 settings as machine-readable TSV on stdout (status
        /// prints go to stderr). Columns: setting_index, ev, top, mid1, mid2,
        /// bot1..bot4. Settings are emitted in setting-index order (not sorted
        /// by EV). Used by the trainer to score user-submitted arrangements.
        #[arg(long)]
        tsv: bool,

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

        /// Opponent model. `mixed` uses --mix-p and --mix-base.
        #[arg(long, value_enum, default_value_t = Opp::Random)]
        opponent: Opp,

        /// For --opponent mixed: base heuristic to wrap.
        #[arg(long, value_enum, default_value_t = MixBaseCli::Mfsuitaware)]
        mix_base: MixBaseCli,

        /// For --opponent mixed: fraction of samples that use the heuristic.
        #[arg(long, default_value_t = 0.8)]
        mix_p: f32,

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

    /// Sprint 2b diagnostic: run every sampled canonical hand against ALL
    /// 7 PURE opponent models, compute best-setting agreement per hand, then
    /// report:
    ///   (a) overall "all-7 agree" rate,
    ///   (b) pairwise agreement matrix (7×7),
    ///   (c) EV-delta distribution,
    ///   (d) worst-disagreement example hands,
    ///   (e) JSON sidecar for Sprint 7 analytics consumption.
    /// Gates the production-model commitment.
    Diagnostic {
        #[arg(long, default_value = "../data/canonical_hands.bin")]
        canonical: PathBuf,

        #[arg(long, default_value = "../data/lookup_table.bin")]
        lookup: PathBuf,

        /// Uniform-stride sample of canonical hands (span full index range).
        #[arg(long, default_value_t = 10_000)]
        hands: usize,

        /// MC samples per hand per model.
        #[arg(long, default_value_t = 1000)]
        samples: usize,

        /// Base seed. All models use the SAME seed so opp-hand / board draws
        /// match across models — setting differences are attributable to
        /// opp-strategy, not RNG drift.
        #[arg(long, default_value_t = 0xC0FFEE_u64)]
        seed: u64,

        /// How many worst-disagreement hands to print in detail.
        #[arg(long, default_value_t = 15)]
        show_top: usize,

        /// Optional JSON sidecar output path.
        #[arg(long)]
        json_out: Option<PathBuf>,
    },

    /// Validate a heuristic opponent model against MC ground truth. Picks
    /// `--num-hands` canonical hands uniformly at random, computes both:
    ///   (i)  the heuristic's chosen setting for each hand (as if it were
    ///        arranging its own cards), and
    ///   (ii) the MC-best setting (N=--samples, Random opp baseline).
    /// Reports: agreement rate + EV regret on disagreement.
    /// Intended use: gate BalancedHeuristic inclusion in the diagnostic panel.
    ValidateModel {
        #[arg(long, default_value = "../data/canonical_hands.bin")]
        canonical: PathBuf,

        #[arg(long, default_value = "../data/lookup_table.bin")]
        lookup: PathBuf,

        /// Which heuristic model to validate.
        #[arg(long, value_enum)]
        model: Opp,

        /// Sample size (canonical hands).
        #[arg(long, default_value_t = 1_000)]
        num_hands: usize,

        /// MC samples per hand for ground-truth EVs.
        #[arg(long, default_value_t = 5_000)]
        samples: usize,

        #[arg(long, default_value_t = 0xC0FFEE_u64)]
        seed: u64,
    },

    /// Audit tool: print each of the 7 pure opponent models' setting choice
    /// for a given 7-card hand, side by side. Used to pressure-test that
    /// model labels actually match behaviour on representative hands
    /// (paired, trips, AAKK, broadway, connectors, etc.).
    ShowOppPicks {
        /// Seven cards separated by whitespace, e.g. "As Kh Qd Jc Ts 9h 2d".
        #[arg(long)]
        hand: String,
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

/// CLI choice of opponent-model family.
#[derive(Copy, Clone, Debug, ValueEnum, PartialEq)]
enum Opp {
    /// Uniform over 105 settings. Baseline.
    Random,
    /// Best Hold'em mid, highest top, bot sanity check.
    Mfnaive,
    /// MFNaive + within-tier bot-suit-preserving swaps.
    Mfsuitaware,
    /// Best Omaha bot first, then best mid, then top.
    Omaha,
    /// Highest non-pair-member on top; preserves pocket pairs.
    Topdef,
    /// Uniform over filtered "reasonable" settings.
    Weighted,
    /// Weighted multi-tier scorer over all 105 settings.
    Balanced,
    /// Mixed wrapper: --mix-base with prob --mix-p, else Random.
    Mixed,
}

/// Mixed-wrapper base choice (only used when --opponent mixed).
#[derive(Copy, Clone, Debug, ValueEnum, PartialEq)]
enum MixBaseCli {
    Mfnaive,
    Mfsuitaware,
    Omaha,
    Topdef,
    Balanced,
}

impl From<MixBaseCli> for MixedBase {
    fn from(b: MixBaseCli) -> Self {
        match b {
            MixBaseCli::Mfnaive => MixedBase::MiddleFirstNaive,
            MixBaseCli::Mfsuitaware => MixedBase::MiddleFirstSuitAware,
            MixBaseCli::Omaha => MixedBase::OmahaFirst,
            MixBaseCli::Topdef => MixedBase::TopDefensive,
            MixBaseCli::Balanced => MixedBase::BalancedHeuristic,
        }
    }
}

fn resolve_opp(o: Opp, mix_p: f32, mix_base: MixBaseCli) -> OpponentModel {
    match o {
        Opp::Random => OpponentModel::Random,
        Opp::Mfnaive => OpponentModel::MiddleFirstNaive,
        Opp::Mfsuitaware => OpponentModel::MiddleFirstSuitAware,
        Opp::Omaha => OpponentModel::OmahaFirst,
        Opp::Topdef => OpponentModel::TopDefensive,
        Opp::Weighted => OpponentModel::RandomWeighted,
        Opp::Balanced => OpponentModel::BalancedHeuristic,
        Opp::Mixed => OpponentModel::HeuristicMixed {
            base: mix_base.into(),
            p_heuristic: mix_p,
        },
    }
}

/// Persist an `OpponentModel` as a u32 tag for the best-response header.
///   0        Random
///   1..=5    MiddleFirstNaive, MiddleFirstSuitAware, OmahaFirst, TopDefensive, BalancedHeuristic
///   6        RandomWeighted
///   1_xyz    HeuristicMixed — x ∈ {1..=5} for base kind, yz ∈ 00..=99 for round(p*100)
fn opp_tag_from_model(m: OpponentModel) -> u32 {
    match m {
        OpponentModel::Random => 0,
        OpponentModel::MiddleFirstNaive => 1,
        OpponentModel::MiddleFirstSuitAware => 2,
        OpponentModel::OmahaFirst => 3,
        OpponentModel::TopDefensive => 4,
        OpponentModel::BalancedHeuristic => 5,
        OpponentModel::RandomWeighted => 6,
        OpponentModel::HeuristicMixed { base, p_heuristic } => {
            let base_digit = match base {
                MixedBase::MiddleFirstNaive => 1,
                MixedBase::MiddleFirstSuitAware => 2,
                MixedBase::OmahaFirst => 3,
                MixedBase::TopDefensive => 4,
                MixedBase::BalancedHeuristic => 5,
            } as u32;
            let pct = (p_heuristic * 100.0).round().clamp(0.0, 100.0) as u32;
            1_000_000 + base_digit * 1_000 + pct
        }
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
            mix_base,
            mix_p,
            parallel,
            seed,
            show_top,
            tsv,
            lookup,
        } => run_mc(
            &hand,
            samples,
            resolve_opp(opponent, mix_p, mix_base),
            parallel,
            seed,
            show_top,
            tsv,
            &lookup,
        ),
        Command::EnumerateCanonical { out, count_only } => run_enumerate(&out, count_only),
        Command::Solve {
            canonical,
            out,
            lookup,
            samples,
            seed,
            opponent,
            mix_base,
            mix_p,
            block_size,
            limit,
        } => run_solve(
            &canonical,
            &out,
            &lookup,
            samples,
            seed,
            resolve_opp(opponent, mix_p, mix_base),
            block_size,
            limit,
        ),
        Command::Diagnostic {
            canonical,
            lookup,
            hands,
            samples,
            seed,
            show_top,
            json_out,
        } => run_diagnostic(&canonical, &lookup, hands, samples, seed, show_top, json_out.as_deref()),
        Command::ValidateModel {
            canonical,
            lookup,
            model,
            num_hands,
            samples,
            seed,
        } => run_validate_model(&canonical, &lookup, model, num_hands, samples, seed),
        Command::ShowOppPicks { hand } => run_show_opp_picks(&hand),
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
    tsv: bool,
    lookup_path: &std::path::Path,
) -> Result<(), Box<dyn std::error::Error>> {
    if samples == 0 {
        return Err("--samples must be > 0".into());
    }
    let hand = parse_seven(hand_str)?;

    // When emitting TSV, status prints go to stderr so stdout stays parseable.
    if tsv {
        eprintln!("Loading 5-card lookup table from {} ...", lookup_path.display());
    } else {
        println!("Loading 5-card lookup table from {} ...", lookup_path.display());
    }
    let ev = Evaluator::load_or_build(lookup_path)?;
    let status = format!(
        "Table ready. Running {} Monte Carlo samples × 105 settings (opponent={:?}, parallel={}, seed={:#x}).",
        samples, model, parallel, seed
    );
    if tsv {
        eprintln!("{}", status);
    } else {
        println!("{}", status);
    }

    let t0 = Instant::now();
    let summary = if parallel {
        mc_evaluate_all_settings_par(&ev, hand, model, samples, seed)
    } else {
        let mut rng = SmallRng::seed_from_u64(seed);
        mc_evaluate_all_settings(&ev, hand, model, samples, &mut rng)
    };
    let elapsed = t0.elapsed();

    if tsv {
        eprintln!(
            "Elapsed: {:.2?}  (N={} samples) — best EV = {:+.3}",
            elapsed,
            summary.num_samples,
            summary.best().ev
        );
        print_mc_tsv(&hand, model, &summary);
        return Ok(());
    }

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

/// Emit all 105 settings in setting-index order as TSV on stdout.
///
/// Format:
///   # header lines starting with '#'
///   # columns: setting_index ev top mid1 mid2 bot1 bot2 bot3 bot4
///   0<TAB>-1.234<TAB>As<TAB>Kh<TAB>Qd<TAB>Jc<TAB>Ts<TAB>9h<TAB>2d
///   ...
///
/// The summary's results are pre-sorted by EV; for TSV we reorder back into
/// setting-index order so index i maps to the i-th HandSetting from
/// `all_settings(hand)`. 105 × 105 linear scan is trivially cheap.
fn print_mc_tsv(hand: &[Card; 7], model: OpponentModel, summary: &McSummary) {
    println!("# engine-mc-tsv v1");
    println!(
        "# hand: {} {} {} {} {} {} {}",
        hand[0], hand[1], hand[2], hand[3], hand[4], hand[5], hand[6]
    );
    println!("# samples: {}", summary.num_samples);
    println!("# opponent: {:?}", model);
    println!("# columns: setting_index\tev\ttop\tmid1\tmid2\tbot1\tbot2\tbot3\tbot4");

    let settings = all_settings(*hand);
    for (idx, s) in settings.iter().enumerate() {
        let ev = summary
            .results
            .iter()
            .find(|r| r.setting == *s)
            .map(|r| r.ev)
            .expect("every enumerated setting must appear in summary");
        println!(
            "{}\t{:.6}\t{}\t{}\t{}\t{}\t{}\t{}\t{}",
            idx, ev,
            s.top,
            s.mid[0], s.mid[1],
            s.bot[0], s.bot[1], s.bot[2], s.bot[3],
        );
    }
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
    model: OpponentModel,
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
        opp_model_tag: opp_tag_from_model(model),
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
        "Solving {} hands (ids {}..{}) at samples={} opp={:?} block_size={} ...",
        target, resume_from, slice_end, samples, model, block_size
    );

    let t0 = Instant::now();
    let total_target = target as u64;
    solve_range(
        &ev,
        slice,
        resume_from as u32,
        samples as usize,
        seed,
        model,
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

/// Sprint 2b diagnostic. For each sampled canonical hand, runs the SAME
/// hand through all 7 pure opponent models (Random, MFNaive, MFSuitAware,
/// OmahaFirst, TopDefensive, RandomWeighted, BalancedHeuristic) at identical
/// seed + sample count, then computes:
///   - overall "all-7-agree" rate,
///   - pairwise 7×7 agreement matrix,
///   - EV-delta distribution across models (max − min EV per hand),
///   - worst-disagreement examples.
/// Writes an optional JSON sidecar for analytics.
#[allow(clippy::too_many_arguments)]
fn run_diagnostic(
    canonical_path: &std::path::Path,
    lookup_path: &std::path::Path,
    hands: usize,
    samples: usize,
    seed: u64,
    show_top: usize,
    json_out: Option<&std::path::Path>,
) -> Result<(), Box<dyn std::error::Error>> {
    if samples == 0 || hands == 0 {
        return Err("--hands and --samples must be > 0".into());
    }

    println!("Loading 5-card lookup table from {} ...", lookup_path.display());
    let ev = Evaluator::load_or_build(lookup_path)?;
    println!("Loading canonical hands from {} ...", canonical_path.display());
    let canonical = read_canonical_hands(canonical_path)?;
    let total = canonical.len();
    println!("  {total} canonical hands on disk.");

    let n = hands.min(total);
    let stride = total as f64 / n as f64;
    let picks: Vec<u32> = (0..n)
        .map(|i| ((i as f64) * stride).round() as u32)
        .map(|p| p.min((total - 1) as u32))
        .collect();
    println!(
        "Sampling {} hands at stride {:.1} (first id={}, last id={}).",
        picks.len(),
        stride,
        picks.first().copied().unwrap_or(0),
        picks.last().copied().unwrap_or(0)
    );

    // The 7-pure-model panel.
    const MODEL_NAMES: [&str; 7] = [
        "Random",
        "MFNaive",
        "MFSuitAware",
        "OmahaFirst",
        "TopDefensive",
        "RandomWeighted",
        "BalancedHeuristic",
    ];
    let models: [OpponentModel; 7] = [
        OpponentModel::Random,
        OpponentModel::MiddleFirstNaive,
        OpponentModel::MiddleFirstSuitAware,
        OpponentModel::OmahaFirst,
        OpponentModel::TopDefensive,
        OpponentModel::RandomWeighted,
        OpponentModel::BalancedHeuristic,
    ];
    println!(
        "Running all 7 pure models at samples={samples} seed={seed:#x}. Est. wall ≈ {} min at 37 ms/hand/model.",
        (picks.len() as f64 * 7.0 * 37.3 / 60_000.0).round() as u32
    );

    use rayon::prelude::*;
    let t0 = Instant::now();
    // Per hand: 7 (best_setting_index u8, best_ev f32) records.
    let rows: Vec<(u32, [u8; 7], [f32; 7])> = picks
        .par_iter()
        .map(|&id| {
            let bytes = canonical[id as usize];
            let mut idx = [0u8; 7];
            let mut evs = [0f32; 7];
            for (k, m) in models.iter().enumerate() {
                let r = solve_one(&ev, &bytes, id, samples, seed, *m);
                idx[k] = r.best_setting_index;
                evs[k] = r.best_ev;
            }
            (id, idx, evs)
        })
        .collect();
    let elapsed = t0.elapsed();
    println!("Done in {:.2?}.\n", elapsed);

    // Overall all-7-agree count.
    let all_agree = rows
        .iter()
        .filter(|(_, idx, _)| idx.iter().all(|&v| v == idx[0]))
        .count();
    println!(
        "All-7 models agree: {}/{} ({:.1}%)",
        all_agree,
        rows.len(),
        100.0 * all_agree as f64 / rows.len() as f64
    );

    // Pairwise 7×7 agreement matrix.
    let mut agreement = [[0u64; 7]; 7];
    for (_, idx, _) in &rows {
        for a in 0..7 {
            for b in 0..7 {
                if idx[a] == idx[b] {
                    agreement[a][b] += 1;
                }
            }
        }
    }
    let n_hands = rows.len() as f64;
    println!("\nPairwise agreement matrix (%):");
    print!("{:>18}", "");
    for name in &MODEL_NAMES {
        print!(" {:>9.9}", name);
    }
    println!();
    for a in 0..7 {
        print!("{:>18}", MODEL_NAMES[a]);
        for b in 0..7 {
            let pct = 100.0 * agreement[a][b] as f64 / n_hands;
            print!(" {:>8.1}%", pct);
        }
        println!();
    }

    // EV spread per hand: max − min across the 7 models.
    let mut spreads: Vec<(u32, f32)> = rows
        .iter()
        .map(|(id, _, evs)| {
            let max = evs.iter().cloned().fold(f32::NEG_INFINITY, f32::max);
            let min = evs.iter().cloned().fold(f32::INFINITY, f32::min);
            (*id, max - min)
        })
        .collect();
    spreads.sort_by(|a, b| a.1.partial_cmp(&b.1).unwrap());
    fn pct(v: &[(u32, f32)], p: f64) -> f32 {
        if v.is_empty() {
            0.0
        } else {
            let idx = ((p / 100.0) * (v.len() - 1) as f64).round() as usize;
            v[idx].1
        }
    }
    let mean_spread: f32 =
        spreads.iter().map(|(_, s)| *s).sum::<f32>() / spreads.len() as f32;
    println!("\nPer-hand EV spread (max_model_EV − min_model_EV):");
    println!("  mean  {:>6.3}", mean_spread);
    println!("  p50   {:>6.3}", pct(&spreads, 50.0));
    println!("  p90   {:>6.3}", pct(&spreads, 90.0));
    println!("  p95   {:>6.3}", pct(&spreads, 95.0));
    println!("  p99   {:>6.3}", pct(&spreads, 99.0));
    println!("  max   {:>6.3}", spreads.last().map(|x| x.1).unwrap_or(0.0));

    // Worst-disagreement examples: largest EV spread.
    let mut worst_spreads = spreads.clone();
    worst_spreads.reverse();
    let take = show_top.min(worst_spreads.len());
    if take > 0 {
        println!("\nTop {take} hands by max EV spread across models:");
        println!(
            "  {:>10}  {:<30}  spread    {}",
            "id",
            "canonical hand",
            MODEL_NAMES
                .iter()
                .enumerate()
                .map(|(_i, n)| format!("{:>9.9}", n))
                .collect::<Vec<_>>()
                .join(" ")
        );
        for (id, spread) in worst_spreads.iter().take(take) {
            let row = rows.iter().find(|(rid, _, _)| rid == id).unwrap();
            let hand = bytes_to_hand(&canonical[*id as usize]);
            let evs = row.2;
            println!(
                "  {:>10}  {:<30}  {:>6.3}    {}",
                id,
                fmt_hand(&hand),
                spread,
                evs.iter()
                    .map(|e| format!("{:>+9.3}", e))
                    .collect::<Vec<_>>()
                    .join(" ")
            );
        }
    }

    // Cluster analysis hint: which pairs have >95% agreement?
    println!("\nHigh-agreement pairs (≥95%): candidate collapses for production:");
    let mut any = false;
    for a in 0..7 {
        for b in (a + 1)..7 {
            let pct = 100.0 * agreement[a][b] as f64 / n_hands;
            if pct >= 95.0 {
                println!("  {} ↔ {}: {:.1}%", MODEL_NAMES[a], MODEL_NAMES[b], pct);
                any = true;
            }
        }
    }
    if !any {
        println!("  (none — all 7 models are meaningfully distinct)");
    }

    // JSON sidecar.
    if let Some(path) = json_out {
        write_diagnostic_json(path, &MODEL_NAMES, &rows, &agreement, mean_spread, &spreads)?;
        println!("\nJSON sidecar written to {}.", path.display());
    }

    println!(
        "\nInterpretation guide:\n  All-7 agree > 95%  →  opp model barely matters; use the cheapest.\n  70-95%             →  partial clustering; pick one representative per cluster.\n  < 70%              →  models meaningfully diverge; may need the full panel in production."
    );

    Ok(())
}

/// Minimal hand-rolled JSON writer — no extra dependency required. Numbers
/// are serialised with full precision; strings are conservatively escaped.
fn write_diagnostic_json(
    path: &std::path::Path,
    model_names: &[&str; 7],
    rows: &[(u32, [u8; 7], [f32; 7])],
    agreement: &[[u64; 7]; 7],
    mean_spread: f32,
    spreads: &[(u32, f32)],
) -> std::io::Result<()> {
    use std::io::Write;
    let mut f = std::fs::File::create(path)?;
    writeln!(f, "{{")?;
    writeln!(f, "  \"num_hands\": {},", rows.len())?;
    writeln!(f, "  \"num_models\": 7,")?;
    writeln!(f, "  \"mean_spread\": {mean_spread},")?;
    // Models array.
    write!(f, "  \"models\": [")?;
    for (i, n) in model_names.iter().enumerate() {
        if i > 0 {
            write!(f, ", ")?;
        }
        write!(f, "\"{}\"", n)?;
    }
    writeln!(f, "],")?;
    // Pairwise agreement (raw counts).
    writeln!(f, "  \"agreement_counts\": [")?;
    for (i, row) in agreement.iter().enumerate() {
        write!(f, "    [")?;
        for (j, v) in row.iter().enumerate() {
            if j > 0 {
                write!(f, ", ")?;
            }
            write!(f, "{v}")?;
        }
        if i + 1 < 7 {
            writeln!(f, "],")?;
        } else {
            writeln!(f, "]")?;
        }
    }
    writeln!(f, "  ],")?;
    // Per-hand records (may be large).
    writeln!(f, "  \"hands\": [")?;
    let mut iter = rows.iter().enumerate().peekable();
    while let Some((_i, (id, idx, evs))) = iter.next() {
        write!(
            f,
            "    {{\"id\": {id}, \"best_idx\": [{}], \"best_ev\": [{}]}}",
            idx.iter()
                .map(|v| v.to_string())
                .collect::<Vec<_>>()
                .join(","),
            evs.iter()
                .map(|v| v.to_string())
                .collect::<Vec<_>>()
                .join(","),
        )?;
        if iter.peek().is_some() {
            writeln!(f, ",")?;
        } else {
            writeln!(f)?;
        }
    }
    writeln!(f, "  ],")?;
    // Spread series for convenience.
    writeln!(f, "  \"spread_series\": [")?;
    let mut iter = spreads.iter().peekable();
    while let Some((id, s)) = iter.next() {
        write!(f, "    {{\"id\": {id}, \"spread\": {s}}}")?;
        if iter.peek().is_some() {
            writeln!(f, ",")?;
        } else {
            writeln!(f)?;
        }
    }
    writeln!(f, "  ]")?;
    writeln!(f, "}}")?;
    f.flush()?;
    Ok(())
}

/// Validate a heuristic opponent model by comparing its own setting choice
/// to the MC-best setting (N samples vs Random opp) on `num_hands` canonical
/// hands. Reports agreement and EV regret.
fn run_validate_model(
    canonical_path: &std::path::Path,
    lookup_path: &std::path::Path,
    model_cli: Opp,
    num_hands: usize,
    samples: usize,
    seed: u64,
) -> Result<(), Box<dyn std::error::Error>> {
    use rand::rngs::SmallRng;
    use rand::{Rng, SeedableRng};
    use rayon::prelude::*;
    use tw_engine::opp_models;

    let model_opp = resolve_opp(model_cli, 0.0, MixBaseCli::Mfsuitaware);
    let model_name = format!("{:?}", model_opp);
    println!("Loading lookup from {} ...", lookup_path.display());
    let ev = Evaluator::load_or_build(lookup_path)?;
    println!("Loading canonical hands from {} ...", canonical_path.display());
    let canonical = read_canonical_hands(canonical_path)?;
    let total = canonical.len();
    // Uniform-random sample of canonical IDs.
    let mut rng = SmallRng::seed_from_u64(seed ^ 0xDEAD_BEEF);
    let mut picks: Vec<u32> = (0..num_hands.min(total))
        .map(|_| rng.gen_range(0..total as u32))
        .collect();
    picks.sort_unstable();
    picks.dedup();
    println!(
        "Validating {} vs MC ground truth at N={samples} on {} distinct canonical hands.",
        model_name,
        picks.len()
    );
    let t0 = Instant::now();
    let rows: Vec<(u32, u8, u8, f32, f32)> = picks
        .par_iter()
        .map(|&id| {
            let bytes = canonical[id as usize];
            let hand = bytes_to_hand(&bytes);
            // Heuristic's own choice of setting, interpreted as its "play."
            let heur_setting = match model_opp {
                OpponentModel::MiddleFirstNaive => opp_models::opp_middle_first_naive(hand),
                OpponentModel::MiddleFirstSuitAware => opp_models::opp_middle_first_suit_aware(hand),
                OpponentModel::OmahaFirst => opp_models::opp_omaha_first(hand),
                OpponentModel::TopDefensive => opp_models::opp_top_defensive(hand),
                OpponentModel::BalancedHeuristic => opp_models::opp_balanced_heuristic(hand),
                _ => {
                    // Random / RandomWeighted aren't "deterministic policies" for a self-play
                    // validation — just use MFSuitAware's choice as a placeholder (shouldn't be invoked here).
                    opp_models::opp_middle_first_suit_aware(hand)
                }
            };
            // MC ground-truth best setting under Random opp at this N.
            let gt = solve_one(&ev, &bytes, id, samples, seed, OpponentModel::Random);
            let all = all_settings(hand);
            let heur_idx = all.iter().position(|s| *s == heur_setting).unwrap() as u8;
            // Compute MC EV of the heuristic's pick at the SAME seed for apples-to-apples regret.
            let mut rng2 = SmallRng::seed_from_u64(
                seed.wrapping_add((id as u64).wrapping_mul(0x9E37_79B9_7F4A_7C15)),
            );
            let s_summary = mc_evaluate_all_settings(
                &ev,
                hand,
                OpponentModel::Random,
                samples,
                &mut rng2,
            );
            let heur_ev = s_summary
                .results
                .iter()
                .find(|r| r.setting == heur_setting)
                .map(|r| r.ev as f32)
                .unwrap_or(f32::NAN);
            (id, heur_idx, gt.best_setting_index, heur_ev, gt.best_ev)
        })
        .collect();
    let elapsed = t0.elapsed();
    println!("Done in {:.2?}.\n", elapsed);

    let agree = rows.iter().filter(|(_, h, g, _, _)| h == g).count();
    let total_checked = rows.len();
    let mut regrets: Vec<f32> = rows
        .iter()
        .map(|(_, _, _, h_ev, g_ev)| (g_ev - h_ev).max(0.0))
        .collect();
    regrets.sort_by(|a, b| a.partial_cmp(b).unwrap());
    let mean_regret: f32 = regrets.iter().sum::<f32>() / total_checked as f32;
    println!(
        "Agreement: {}/{} ({:.1}%)",
        agree,
        total_checked,
        100.0 * agree as f64 / total_checked as f64
    );
    println!(
        "EV regret (ground_truth − heuristic, max(0, ·)):  mean {:.3}, median {:.3}, p90 {:.3}, max {:.3}",
        mean_regret,
        regrets.get(regrets.len() / 2).copied().unwrap_or(0.0),
        regrets
            .get((regrets.len() * 9 / 10).min(regrets.len().saturating_sub(1)))
            .copied()
            .unwrap_or(0.0),
        regrets.last().copied().unwrap_or(0.0)
    );
    println!(
        "\nGating: agreement ≥ 70% AND mean regret ≤ 0.3 → include in diagnostic panel.\n        Otherwise: retune weights or swap for mini-MC variant."
    );
    Ok(())
}

/// Show what each of the 7 pure opponent models picks for a given hand.
/// Pure-function call; no MC required. Used by the model-audit review.
fn run_show_opp_picks(hand_str: &str) -> Result<(), Box<dyn std::error::Error>> {
    use rand::rngs::SmallRng;
    use rand::SeedableRng;
    use tw_engine::opp_models::*;

    let hand = parse_seven(hand_str)?;
    println!(
        "Hand: {} {} {} {} {} {} {}\n",
        hand[0], hand[1], hand[2], hand[3], hand[4], hand[5], hand[6]
    );

    // Random's setting is RNG-dependent; use a fixed seed so the audit is reproducible.
    let mut rng = SmallRng::seed_from_u64(12648430);

    let random = {
        use rand::seq::SliceRandom;
        let mut s = all_settings(hand);
        s.shuffle(&mut rng);
        s[0]
    };
    let mfnaive = opp_middle_first_naive(hand);
    let mfsuit = opp_middle_first_suit_aware(hand);
    let omaha = opp_omaha_first(hand);
    let topdef = opp_top_defensive(hand);
    // RandomWeighted draws an RNG from the shuffled stream; reseed so it's
    // independent of the random draw above.
    let mut rng_w = SmallRng::seed_from_u64(12648430 ^ 0xFEEDFACE);
    let weighted = opp_random_weighted(hand, &mut rng_w);
    let balanced = opp_balanced_heuristic(hand);

    let pick = |name: &str, s: &HandSetting| {
        println!(
            "{:<18}  top [{}]  mid [{} {}]  bot [{} {} {} {}]",
            name, s.top, s.mid[0], s.mid[1], s.bot[0], s.bot[1], s.bot[2], s.bot[3]
        );
    };
    pick("Random(fixed)", &random);
    pick("MFNaive", &mfnaive);
    pick("MFSuitAware", &mfsuit);
    pick("OmahaFirst", &omaha);
    pick("TopDefensive", &topdef);
    pick("RandomWeighted", &weighted);
    pick("BalancedHeuristic", &balanced);

    // Also print the suit layout of each bot for quick suitedness reading.
    println!("\nBot suit layout (spades=♠ hearts=♥ diamonds=♦ clubs=♣):");
    let bot_layout = |s: &HandSetting| -> String {
        let mut c = [0u8; 4];
        for card in &s.bot {
            c[card.suit() as usize] += 1;
        }
        let mut sorted = c;
        sorted.sort_unstable_by(|a, b| b.cmp(a));
        let pattern = match (sorted[0], sorted[1]) {
            (2, 2) => "2+2 DS",
            (2, 1) => "2+1+1 SS",
            (1, 1) => "1+1+1+1 rainbow",
            (3, 1) => "3+1 (wastes 1)",
            (4, 0) => "4-flush (wastes 2)",
            _ => "?",
        };
        format!(
            "♣{} ♦{} ♥{} ♠{}  →  {}",
            c[0], c[1], c[2], c[3], pattern
        )
    };
    println!("  Random(fixed)      {}", bot_layout(&random));
    println!("  MFNaive            {}", bot_layout(&mfnaive));
    println!("  MFSuitAware        {}", bot_layout(&mfsuit));
    println!("  OmahaFirst         {}", bot_layout(&omaha));
    println!("  TopDefensive       {}", bot_layout(&topdef));
    println!("  RandomWeighted     {}", bot_layout(&weighted));
    println!("  BalancedHeuristic  {}", bot_layout(&balanced));

    Ok(())
}

#[allow(dead_code)]
fn _compile_guard_mcsummary(_: McSummary) {}
