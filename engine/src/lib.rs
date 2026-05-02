//! Taiwanese Poker solver engine — core library.
//!
//! Sprint 0 surface: cards, 5-card hand evaluation with lookup table, and the
//! 105 possible hand settings.
//!
//! Sprint 1 surface adds: tier evaluators (top/middle/Omaha) and the
//! six-matchup scoring module. Monte Carlo and CFR are layered on later.
//!
//! Design rule (see `docs/modules/compute-pipeline.md` and prompt note #5):
//! the evaluator is a pure function — cards in, rank out, no side effects, no
//! allocations — so the same logic can back a CPU (rayon) or GPU (CUDA)
//! backend without changes.

pub mod best_response;
pub mod bucketing;
pub mod card;
pub mod hand_eval;
pub mod holdem_eval;
pub mod lookup;
pub mod monte_carlo;
pub mod omaha_eval;
pub mod opp_models;
pub mod oracle_grid;
pub mod scoring;
pub mod setting;

pub use best_response::{
    read_all as read_best_response_file, solve_one, solve_range, BestResponseRecord, BrError,
    BrHeader, BrWriter, BR_HEADER_SIZE, BR_MAGIC, BR_RECORD_SIZE, BR_VERSION,
};
pub use bucketing::{
    bytes_to_hand, canonicalize, count_canonical_hands, enumerate_canonical_hands, hand_to_bytes,
    is_canonical, read_canonical_hands, write_canonical_hands, HAND_SIZE, NUM_CARDS,
};
pub use card::{parse_hand, Card, Deck, Suit};
pub use hand_eval::{category, category_name, compute_rank_5, Evaluator, HandRank};
pub use holdem_eval::{eval_middle, eval_top};
pub use monte_carlo::{
    mc_evaluate_all_settings, mc_evaluate_all_settings_par, mc_evaluate_setting, McResult,
    McSummary, MixedBase, OpponentModel,
};
pub use omaha_eval::eval_omaha;
pub use oracle_grid::{
    read_all as read_oracle_grid_file, solve_grid_one, solve_grid_range, OgError, OgHeader,
    OgWriter, OracleGridRecord, OG_HEADER_SIZE, OG_MAGIC, OG_RECORD_SIZE, OG_VERSION,
};
pub use scoring::{matchup_breakdown, score_matchup, MatchupBreakdown, Outcome};
pub use setting::{all_settings, HandSetting, NUM_SETTINGS};
