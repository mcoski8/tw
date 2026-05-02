"""
Reader for the Full Oracle Grid file produced by ``tw-engine oracle-grid``
(Decision 043, Session 23).

Binary format (all little-endian, mirrors ``engine/src/oracle_grid.rs``):

    Header (32 bytes):
      [0..4]   magic            4 bytes, must equal b"TWOG"
      [4..8]   version          u32
      [8..12]  samples          u32   MC samples per (hand, setting) cell
      [12..20] base_seed        u64
      [20..28] canonical_total  u64   expected record count when complete
      [28..32] opp_model_tag    u32   8 = RealisticHumanMixture (Decision 043)

    Record (424 bytes, repeated N times):
      [0..4]   canonical_id     u32
      [4..424] evs              105 × f32, in setting-index order

    Setting index ``i`` corresponds to ``decode_setting(hand, i)`` —
    NOT sorted by EV. This is the substrate for the Query Harness.

The opp_model_tag codec is shared with best_response.rs; tag 7 is
``MfsuitTopLocked`` and tag 8 is ``RealisticHumanMixture`` (the standard
mixture for the Full Oracle Grid). Use ``decode_opp_tag`` from
``br_reader`` after augmenting it; for now the bare names are duplicated
here so this module is self-contained.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Union

import numpy as np

OG_MAGIC = b"TWOG"
OG_HEADER_SIZE = 32
NUM_SETTINGS = 105
OG_RECORD_SIZE = 4 + NUM_SETTINGS * 4  # 424
CURRENT_VERSION = 1

# (canonical_id u32, evs [f32; 105]) — packed, no padding.
RECORD_DTYPE = np.dtype(
    {
        "names": ["canonical_id", "evs"],
        "formats": ["<u4", ("<f4", NUM_SETTINGS)],
        "offsets": [0, 4],
        "itemsize": OG_RECORD_SIZE,
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
        "itemsize": OG_HEADER_SIZE,
    }
)

# Augmented opp_model_tag → label map. Mirrors opp_tag_from_model in main.rs.
_BARE_NAMES = {
    0: "Random",
    1: "MiddleFirstNaive",
    2: "MiddleFirstSuitAware",
    3: "OmahaFirst",
    4: "TopDefensive",
    5: "BalancedHeuristic",
    6: "RandomWeighted",
    7: "MfsuitTopLocked",
    8: "RealisticHumanMixture",
}


def decode_opp_tag(tag: int) -> str:
    if tag in _BARE_NAMES:
        return _BARE_NAMES[tag]
    if tag >= 1_000_000:
        return f"HeuristicMixed(raw_tag={tag})"
    return f"Unknown(tag={tag})"


@dataclass(frozen=True)
class OgHeader:
    version: int
    samples: int
    base_seed: int
    canonical_total: int
    opp_model_tag: int

    @property
    def opp_label(self) -> str:
        return decode_opp_tag(self.opp_model_tag)


@dataclass(frozen=True)
class OracleGrid:
    """Loaded view of an oracle-grid file.

    ``records`` is a structured numpy array with two fields:
      - ``canonical_id`` (uint32), one per row.
      - ``evs`` (float32, shape (105,) per row), in setting-index order.

    For the full ~6M-row grid (~2.5 GB), prefer ``mode='memmap'``.
    """

    path: Path
    header: OgHeader
    records: np.ndarray
    is_complete: bool

    def __len__(self) -> int:
        return len(self.records)

    @property
    def evs(self) -> np.ndarray:
        """Convenience: shape (N, 105) view of the EV matrix."""
        return self.records["evs"]

    @property
    def canonical_ids(self) -> np.ndarray:
        return self.records["canonical_id"]

    def argmax_setting(self) -> np.ndarray:
        """For each row, the setting-index with the highest EV (shape (N,) uint8)."""
        return self.evs.argmax(axis=1).astype(np.uint8)

    def best_ev(self) -> np.ndarray:
        """For each row, the EV of the argmax setting (shape (N,) float32)."""
        return self.evs.max(axis=1)

    def ev_for_setting(self, canonical_id: int, setting_index: int) -> float:
        """Direct lookup. ``canonical_id`` must equal the row's id."""
        if not 0 <= setting_index < NUM_SETTINGS:
            raise ValueError(f"setting_index {setting_index} out of range 0..{NUM_SETTINGS}")
        # Records are written in canonical_id order, so index == position.
        if canonical_id < 0 or canonical_id >= len(self.records):
            raise IndexError(f"canonical_id {canonical_id} out of range")
        row = self.records[canonical_id]
        if int(row["canonical_id"]) != canonical_id:
            # Defensive: file may be partially written or out of order.
            raise ValueError(
                f"row at position {canonical_id} has canonical_id "
                f"{int(row['canonical_id'])} (file order broken)"
            )
        return float(row["evs"][setting_index])


def read_oracle_grid(
    path: Union[str, Path],
    mode: Literal["load", "memmap"] = "memmap",
) -> OracleGrid:
    """
    Read an oracle-grid file.

    mode='memmap' is the default because the full grid is ~2.5 GB; mmap
    avoids a multi-second read on every script start. Use mode='load' for
    pilot-sized files (<200 MB) when you want a heap copy.
    """
    path = Path(path)
    size = path.stat().st_size
    if size < OG_HEADER_SIZE:
        raise ValueError(
            f"{path}: file is {size} bytes, smaller than {OG_HEADER_SIZE}-byte header"
        )

    with open(path, "rb") as f:
        header_buf = f.read(OG_HEADER_SIZE)
    header_arr = np.frombuffer(header_buf, dtype=HEADER_DTYPE, count=1)[0]
    if bytes(header_arr["magic"]) != OG_MAGIC:
        raise ValueError(
            f"{path}: bad magic {bytes(header_arr['magic'])!r} (expected {OG_MAGIC!r})"
        )
    version = int(header_arr["version"])
    if version != CURRENT_VERSION:
        raise ValueError(
            f"{path}: version {version} unsupported (reader knows v{CURRENT_VERSION})"
        )

    header = OgHeader(
        version=version,
        samples=int(header_arr["samples"]),
        base_seed=int(header_arr["base_seed"]),
        canonical_total=int(header_arr["canonical_total"]),
        opp_model_tag=int(header_arr["opp_model_tag"]),
    )

    body_size = size - OG_HEADER_SIZE
    if body_size % OG_RECORD_SIZE != 0:
        raise ValueError(
            f"{path}: body is {body_size} bytes, not a multiple of {OG_RECORD_SIZE}"
        )
    n = body_size // OG_RECORD_SIZE
    is_complete = n == header.canonical_total

    if mode == "memmap":
        records = np.memmap(
            path,
            dtype=RECORD_DTYPE,
            mode="r",
            offset=OG_HEADER_SIZE,
            shape=(n,),
        )
    elif mode == "load":
        with open(path, "rb") as f:
            f.seek(OG_HEADER_SIZE)
            body = f.read(body_size)
        records = np.frombuffer(body, dtype=RECORD_DTYPE, count=n)
    else:
        raise ValueError(f"mode must be 'load' or 'memmap', got {mode!r}")

    return OracleGrid(path=path, header=header, records=records, is_complete=is_complete)


def validate_oracle_grid(og: OracleGrid) -> list[str]:
    """
    Integrity checks against an OracleGrid view. Returns a list of issues;
    empty list = clean.
    """
    issues: list[str] = []
    n = len(og)

    ids = og.canonical_ids
    expected = np.arange(n, dtype=np.uint32)
    if not np.array_equal(ids, expected):
        mismatch = int(np.argmax(ids != expected))
        issues.append(
            f"canonical_id not 0..N-1 in order: first mismatch at position "
            f"{mismatch}: got {int(ids[mismatch])} expected {int(expected[mismatch])}"
        )

    evs = og.evs
    if n > 0:
        if not np.all(np.isfinite(evs)):
            bad = int((~np.isfinite(evs)).sum())
            issues.append(f"{bad} EV cells are non-finite")
        # Net points are bounded [-20, +20]; allow a tiny slack for f32.
        if float(evs.min()) < -20.5 or float(evs.max()) > 20.5:
            issues.append(
                f"EV outside plausible range: min={float(evs.min()):.3f}, max={float(evs.max()):.3f}"
            )
        # No row should have all-zero EVs (would indicate uninitialized memory).
        zero_rows = int((evs == 0.0).all(axis=1).sum())
        if zero_rows > 0:
            issues.append(f"{zero_rows} rows have all-zero EVs (likely write bug)")

    return issues
