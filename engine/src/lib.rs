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

pub mod card;
pub mod hand_eval;
pub mod holdem_eval;
pub mod lookup;
pub mod monte_carlo;
pub mod omaha_eval;
pub mod scoring;
pub mod setting;

pub use card::{parse_hand, Card, Deck, Suit};
pub use hand_eval::{category, category_name, compute_rank_5, Evaluator, HandRank};
pub use holdem_eval::{eval_middle, eval_top};
pub use monte_carlo::{
    mc_evaluate_all_settings, mc_evaluate_all_settings_par, mc_evaluate_setting, McResult,
    McSummary, OpponentModel,
};
pub use omaha_eval::eval_omaha;
pub use scoring::{matchup_breakdown, score_matchup, MatchupBreakdown, Outcome};
pub use setting::{all_settings, HandSetting, NUM_SETTINGS};
