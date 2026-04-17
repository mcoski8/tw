//! Taiwanese Poker solver engine — core library.
//!
//! Sprint 0 surface: cards, 5-card hand evaluation with lookup table, and the
//! 105 possible hand settings. Tier evaluators (top/middle/Omaha), scoring,
//! Monte Carlo and CFR are layered on top in later sprints.
//!
//! Design rule (see `docs/modules/compute-pipeline.md` and prompt note #5):
//! the evaluator is a pure function — cards in, rank out, no side effects, no
//! allocations — so the same logic can back a CPU (rayon) or GPU (CUDA)
//! backend without changes.

pub mod card;
pub mod hand_eval;
pub mod lookup;
pub mod setting;

pub use card::{parse_hand, Card, Deck, Suit};
pub use hand_eval::{category, category_name, compute_rank_5, Evaluator, HandRank};
pub use setting::{all_settings, HandSetting, NUM_SETTINGS};
