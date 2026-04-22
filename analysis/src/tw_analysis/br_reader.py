"""
Reader for best-response ``.bin`` files produced by ``tw-engine solve``.

Binary format (all little-endian):

    Header (32 bytes, written once at file start):
      [0..4]   magic               4 bytes, must equal b"TWBR"
      [4..8]   version             u32
      [8..12]  samples             u32   Monte Carlo samples per setting
      [12..20] base_seed           u64
      [20..28] canonical_total     u64   expected record count when complete
      [28..32] opp_model_tag       u32

    Record (9 bytes, repeated N times):
      [0..4]   canonical_id        u32
      [4]      best_setting_index  u8    0..=104
      [5..9]   best_ev             f32

Opponent-model tag codec (mirrors ``opp_tag_from_model`` in engine/src/main.rs):
  0              Random
  1..=5          MiddleFirstNaive, MiddleFirstSuitAware, OmahaFirst,
                 TopDefensive, BalancedHeuristic
  6              RandomWeighted
  1_000_000 + base*1_000 + pct   HeuristicMixed, base in 1..=5, pct in 0..=100
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Union

import numpy as np

MAGIC = b"TWBR"
HEADER_SIZE = 32
RECORD_SIZE = 9
CURRENT_VERSION = 1
NUM_SETTINGS = 105

# Explicit offsets + itemsize guarantee the 9-byte layout with no numpy padding.
RECORD_DTYPE = np.dtype(
    {
        "names": ["canonical_id", "best_setting_index", "best_ev"],
        "formats": ["<u4", "u1", "<f4"],
        "offsets": [0, 4, 5],
        "itemsize": RECORD_SIZE,
    }
)

HEADER_DTYPE = np.dtype(
    {
        "names": [
            "magic",
            "version",
            "samples",
            "base_seed",
            "canonical_total",
            "opp_model_tag",
        ],
        "formats": ["S4", "<u4", "<u4", "<u8", "<u8", "<u4"],
        "offsets": [0, 4, 8, 12, 20, 28],
        "itemsize": HEADER_SIZE,
    }
)

_BASE_NAMES = {
    1: "MiddleFirstNaive",
    2: "MiddleFirstSuitAware",
    3: "OmahaFirst",
    4: "TopDefensive",
    5: "BalancedHeuristic",
}

_BARE_NAMES = {
    0: "Random",
    1: "MiddleFirstNaive",
    2: "MiddleFirstSuitAware",
    3: "OmahaFirst",
    4: "TopDefensive",
    5: "BalancedHeuristic",
    6: "RandomWeighted",
}


def decode_opp_tag(tag: int) -> str:
    """Human-readable label for an ``opp_model_tag`` value."""
    if tag in _BARE_NAMES:
        return _BARE_NAMES[tag]
    if tag >= 1_000_000:
        rest = tag - 1_000_000
        base_digit, pct = divmod(rest, 1_000)
        if base_digit in _BASE_NAMES and 0 <= pct <= 100:
            return (
                f"HeuristicMixed(base={_BASE_NAMES[base_digit]}, p={pct / 100:.2f})"
            )
    return f"Unknown(tag={tag})"


@dataclass(frozen=True)
class BrHeader:
    version: int
    samples: int
    base_seed: int
    canonical_total: int
    opp_model_tag: int

    @property
    def opp_label(self) -> str:
        return decode_opp_tag(self.opp_model_tag)


@dataclass(frozen=True)
class BrFile:
    """Structured view of a best-response file."""

    path: Path
    header: BrHeader
    records: np.ndarray  # structured array, dtype=RECORD_DTYPE
    is_complete: bool  # True iff len(records) == header.canonical_total

    def __len__(self) -> int:
        return len(self.records)


def read_br_file(
    path: Union[str, Path],
    mode: Literal["load", "memmap"] = "load",
) -> BrFile:
    """
    Read a best-response file.

    mode="load"   — read the whole body into RAM (~50 MB per model). Default.
    mode="memmap" — zero-copy mapping; better when working with multiple files
                    at once, or for random-access lookups without loading all.
    """
    path = Path(path)
    size = path.stat().st_size

    if size < HEADER_SIZE:
        raise ValueError(
            f"{path}: file is {size} bytes, smaller than the {HEADER_SIZE}-byte header"
        )

    with open(path, "rb") as f:
        header_buf = f.read(HEADER_SIZE)
    header_arr = np.frombuffer(header_buf, dtype=HEADER_DTYPE, count=1)[0]

    if bytes(header_arr["magic"]) != MAGIC:
        raise ValueError(
            f"{path}: bad magic {bytes(header_arr['magic'])!r} (expected {MAGIC!r})"
        )

    version = int(header_arr["version"])
    if version != CURRENT_VERSION:
        raise ValueError(
            f"{path}: version {version} unsupported (reader knows v{CURRENT_VERSION})"
        )

    header = BrHeader(
        version=version,
        samples=int(header_arr["samples"]),
        base_seed=int(header_arr["base_seed"]),
        canonical_total=int(header_arr["canonical_total"]),
        opp_model_tag=int(header_arr["opp_model_tag"]),
    )

    body_size = size - HEADER_SIZE
    if body_size % RECORD_SIZE != 0:
        raise ValueError(
            f"{path}: body is {body_size} bytes, not a multiple of {RECORD_SIZE}"
        )
    n = body_size // RECORD_SIZE
    is_complete = n == header.canonical_total

    if mode == "memmap":
        records = np.memmap(
            path,
            dtype=RECORD_DTYPE,
            mode="r",
            offset=HEADER_SIZE,
            shape=(n,),
        )
    elif mode == "load":
        with open(path, "rb") as f:
            f.seek(HEADER_SIZE)
            body = f.read(body_size)
        records = np.frombuffer(body, dtype=RECORD_DTYPE, count=n)
    else:
        raise ValueError(f"mode must be 'load' or 'memmap', got {mode!r}")

    return BrFile(path=path, header=header, records=records, is_complete=is_complete)


def validate_br_file(br: BrFile) -> list[str]:
    """
    Run integrity checks against a ``BrFile``. Returns a list of problem
    descriptions; an empty list means everything passed.
    """
    issues: list[str] = []
    recs = br.records
    n = len(recs)

    ids = recs["canonical_id"]
    expected = np.arange(n, dtype=np.uint32)
    if not np.array_equal(ids, expected):
        mismatch = int(np.argmax(ids != expected))
        issues.append(
            f"canonical_id not 0..N-1 in order: first mismatch at position "
            f"{mismatch}: got {int(ids[mismatch])} expected {int(expected[mismatch])}"
        )

    si = recs["best_setting_index"]
    if n > 0 and int(si.max()) >= NUM_SETTINGS:
        bad = int((si >= NUM_SETTINGS).sum())
        issues.append(f"{bad} records have best_setting_index >= {NUM_SETTINGS}")

    ev = recs["best_ev"]
    if n > 0 and not np.all(np.isfinite(ev)):
        bad = int((~np.isfinite(ev)).sum())
        issues.append(f"{bad} records have non-finite best_ev")

    # Scoring caps (see scoring.rs): per-matchup max +20 scoop, +12 non-scoop,
    # min -12. Leave slack; we're looking for corruption, not tight bounds.
    if n > 0 and (ev.min() < -20.0 or ev.max() > 25.0):
        issues.append(
            f"best_ev outside plausible range: "
            f"min={float(ev.min()):.3f}, max={float(ev.max()):.3f}"
        )

    return issues
