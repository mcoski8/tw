"""
Subprocess wrapper around the Rust ``tw-engine mc --tsv`` subcommand.

Given a 7-card hand and an opponent-model choice, returns the EV of every
one of the 105 possible settings in setting-index order. The trainer uses
this to look up EV for the user's submitted arrangement AND the best EV for
the same hand (both derived from the same Monte Carlo run, so comparable).

Latency: ~300ms for samples=1000 on a modern laptop. Caching the result per
(hand, model, samples, seed) removes the cost when the user re-submits the
same hand with a different arrangement.
"""
from __future__ import annotations

import subprocess
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import List, Tuple


REPO_ROOT = Path(__file__).resolve().parents[2]
ENGINE_BIN = REPO_ROOT / "engine" / "target" / "release" / "tw-engine"
LOOKUP_BIN = REPO_ROOT / "data" / "lookup_table.bin"


# --------------------------------------------------------------------------
# Opponent profiles.
#
# These mirror exactly the 4 production-model configurations in
# scripts/production_all_models.sh. The same .bin files on disk were solved
# under these configurations, so on-the-fly MC with matching args reproduces
# the solver's EV scale for comparison.
#
# Ordered so the default (first) is MiddleFirstSuitAware — the only profile
# currently on the Mac as a .bin. When all 4 land, the order here still
# controls the UI dropdown order.
# --------------------------------------------------------------------------

@dataclass(frozen=True)
class ProfileSpec:
    id: str          # short key used in URLs / JS
    label: str       # human-readable display name
    opponent: str    # value for --opponent
    mix_base: str    # value for --mix-base (ignored unless opponent=="mixed")
    mix_p: float     # value for --mix-p


PROFILES: Tuple[ProfileSpec, ...] = (
    ProfileSpec(
        id="mfsuitaware",
        label="Middle-First (Suit-Aware), mixed 90%",
        opponent="mixed", mix_base="mfsuitaware", mix_p=0.9,
    ),
    ProfileSpec(
        id="omaha",
        label="Omaha-First, mixed 90%",
        opponent="mixed", mix_base="omaha", mix_p=0.9,
    ),
    ProfileSpec(
        id="topdef",
        label="Top-Defensive, mixed 90%",
        opponent="mixed", mix_base="topdef", mix_p=0.9,
    ),
    ProfileSpec(
        id="weighted",
        label="Random-Weighted",
        opponent="weighted", mix_base="mfsuitaware", mix_p=0.9,
    ),
)

PROFILE_BY_ID = {p.id: p for p in PROFILES}
DEFAULT_PROFILE_ID = "mfsuitaware"


@dataclass(frozen=True)
class SettingResult:
    setting_index: int
    ev: float
    top: str
    mid: Tuple[str, str]
    bot: Tuple[str, str, str, str]

    @property
    def cards(self) -> List[str]:
        return [self.top, *self.mid, *self.bot]


@dataclass(frozen=True)
class McResult:
    hand: Tuple[str, ...]
    samples: int
    opponent_label: str
    settings: Tuple[SettingResult, ...]  # length 105, indexed by setting_index

    def best(self) -> SettingResult:
        return max(self.settings, key=lambda s: s.ev)


def _run_engine(
    hand: List[str],
    samples: int,
    opponent: str,
    mix_base: str,
    mix_p: float,
    seed: int,
) -> str:
    """Invoke ``tw-engine mc --tsv`` and return stdout."""
    if not ENGINE_BIN.exists():
        raise FileNotFoundError(
            f"engine binary not found at {ENGINE_BIN}. "
            f"Run `cargo build --release` in engine/."
        )
    if not LOOKUP_BIN.exists():
        raise FileNotFoundError(
            f"5-card lookup table not found at {LOOKUP_BIN}. "
            f"Run `tw-engine build-lookup --out {LOOKUP_BIN}`."
        )
    cmd = [
        str(ENGINE_BIN), "mc",
        "--hand", " ".join(hand),
        "--samples", str(samples),
        "--tsv",
        "--opponent", opponent,
        "--mix-base", mix_base,
        "--mix-p", str(mix_p),
        "--seed", str(seed),
        "--parallel",
        "--lookup", str(LOOKUP_BIN),
    ]
    proc = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        raise RuntimeError(
            f"tw-engine mc exited with code {proc.returncode}\n"
            f"stderr:\n{proc.stderr}"
        )
    return proc.stdout


def _parse_tsv(text: str) -> Tuple[str, Tuple[SettingResult, ...]]:
    """Parse the TSV output from ``tw-engine mc --tsv``."""
    opponent_label = ""
    settings: list[SettingResult] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.startswith("#"):
            if line.startswith("# opponent:"):
                opponent_label = line.split(":", 1)[1].strip()
            continue
        parts = line.split("\t")
        if len(parts) != 9:
            raise ValueError(
                f"unexpected TSV row ({len(parts)} cols, need 9): {line!r}"
            )
        idx = int(parts[0])
        ev = float(parts[1])
        top, m1, m2, b1, b2, b3, b4 = parts[2:]
        settings.append(
            SettingResult(
                setting_index=idx,
                ev=ev,
                top=top,
                mid=(m1, m2),
                bot=(b1, b2, b3, b4),
            )
        )
    if len(settings) != 105:
        raise ValueError(f"expected 105 settings, got {len(settings)}")
    # Settings are emitted in index order but verify to be safe.
    for i, s in enumerate(settings):
        if s.setting_index != i:
            raise ValueError(
                f"setting at position {i} has setting_index {s.setting_index}"
            )
    return opponent_label, tuple(settings)


@lru_cache(maxsize=128)
def evaluate_hand_cached(
    hand_key: Tuple[str, ...],
    samples: int,
    opponent: str,
    mix_base: str,
    mix_p: float,
    seed: int,
) -> McResult:
    text = _run_engine(
        list(hand_key), samples, opponent, mix_base, mix_p, seed
    )
    opponent_label, settings = _parse_tsv(text)
    return McResult(
        hand=hand_key,
        samples=samples,
        opponent_label=opponent_label,
        settings=settings,
    )


_RANKS_FOR_SORT = "23456789TJQKA"
_SUITS_FOR_SORT = "cdhs"


def _card_byte(card_str: str) -> int:
    """Engine canonical sort key: card byte = (rank-2)*4 + suit.

    NOTE (Session 22 bugfix): we previously used Python's str-sort on
    card strings here, which produces DIFFERENT positional ordering than
    the byte-sort used by every strategy callable in encode_rules.py /
    strategy_v5_dt.py / strategy_v6_ensemble.py / strategy_v7_regression.py.
    Because all strategies return setting_index in BYTE-sort space and the
    Rust engine builds setting indices from the order of the input hand
    array, the previous str-sort caused setting_index 99 (for example) to
    mean "top=Ac" in Python and "top=Qs" in the engine for any hand
    containing both digit-rank cards (2-9) and broadway cards (T,J,Q,K,A)
    that interleaved differently between byte and str sort. ~94% of
    random hands hit this. EVERY EV measurement before this fix was
    evaluating the wrong setting for ~94% of hands.
    """
    rank = _RANKS_FOR_SORT.index(card_str[0]) + 2
    suit = _SUITS_FOR_SORT.index(card_str[1])
    return (rank - 2) * 4 + suit


def evaluate_hand(
    hand: List[str],
    samples: int = 1000,
    opponent: str = "mixed",
    mix_base: str = "mfsuitaware",
    mix_p: float = 0.9,
    seed: int = 0xC0FFEE,
) -> McResult:
    """
    Evaluate a 7-card hand across all 105 settings.

    Cached per (hand, opponent, samples, seed). Hand is sorted by ENGINE
    BYTE order (matching strategy callables) before caching, so different
    card orderings of the same 7 cards share a cache entry AND the
    setting_index space matches what strategies return.
    """
    if len(hand) != 7:
        raise ValueError(f"hand must have 7 cards, got {len(hand)}")
    return evaluate_hand_cached(
        tuple(sorted(hand, key=_card_byte)),
        samples,
        opponent,
        mix_base,
        mix_p,
        seed,
    )


def evaluate_hand_profile(
    hand: List[str],
    profile: ProfileSpec,
    samples: int = 1000,
    seed: int = 0xC0FFEE,
) -> McResult:
    """Convenience wrapper: evaluate against a named ProfileSpec."""
    return evaluate_hand(
        hand,
        samples=samples,
        opponent=profile.opponent,
        mix_base=profile.mix_base,
        mix_p=profile.mix_p,
        seed=seed,
    )


def evaluate_all_profiles(
    hand: List[str],
    samples: int = 1000,
    seed: int = 0xC0FFEE,
) -> List[Tuple[ProfileSpec, McResult]]:
    """
    Run MC against every production profile serially. Each MC takes ~300ms
    at samples=1000 on a modern laptop; 4 profiles ≈ 1.2s. Serial rather
    than threaded because each run already uses rayon to saturate cores.

    Result is ordered per PROFILES declaration, matching the UI.
    """
    out: List[Tuple[ProfileSpec, McResult]] = []
    for p in PROFILES:
        mc = evaluate_hand_profile(hand, p, samples=samples, seed=seed)
        out.append((p, mc))
    return out


def find_setting_index(mc: McResult, user_cards: List[str]) -> int:
    """
    Given a user's arrangement as 7 cards [top, mid1, mid2, bot1..bot4],
    return the matching setting_index (0..104).

    The user-submitted cards for each tier may be in any order; we normalize
    by sorting each tier's cards and comparing as sets of card strings.
    """
    if len(user_cards) != 7:
        raise ValueError(f"need 7 cards, got {len(user_cards)}")
    top_c = user_cards[0]
    mid_c = frozenset(user_cards[1:3])
    bot_c = frozenset(user_cards[3:7])
    for s in mc.settings:
        if s.top == top_c and frozenset(s.mid) == mid_c and frozenset(s.bot) == bot_c:
            return s.setting_index
    raise ValueError(
        "user arrangement does not match any enumerated setting "
        "(likely a card was duplicated or missing)"
    )
