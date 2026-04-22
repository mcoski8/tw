"""
Inspect a best-response ``.bin`` file.

Usage:
    python3 analysis/scripts/inspect_br.py <path> [--sample N] [--memmap]

Prints header metadata, runs integrity validation, and shows summary stats
plus the first N records.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make the sibling ``src`` package importable without an install step.
HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "src"
if SRC.exists() and str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

import numpy as np  # noqa: E402

from tw_analysis.br_reader import (  # noqa: E402
    NUM_SETTINGS,
    read_br_file,
    validate_br_file,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("path", type=Path, help="path to a best-response .bin file")
    ap.add_argument(
        "--sample",
        type=int,
        default=5,
        help="number of head records to display (default 5)",
    )
    ap.add_argument(
        "--memmap",
        action="store_true",
        help="memory-map the file instead of loading it fully",
    )
    args = ap.parse_args()

    if not args.path.exists():
        print(f"error: {args.path} not found", file=sys.stderr)
        return 2

    br = read_br_file(args.path, mode="memmap" if args.memmap else "load")
    h = br.header

    print(f"File:             {br.path}")
    print(f"Size on disk:     {args.path.stat().st_size:,} bytes")
    status = "COMPLETE" if br.is_complete else "PARTIAL"
    print(f"Records:          {len(br):,} of {h.canonical_total:,}  [{status}]")
    print(f"Header version:   {h.version}")
    print(f"Samples per hand: {h.samples:,}")
    print(f"Base seed:        {h.base_seed}")
    print(f"Opponent model:   {h.opp_label}  (tag={h.opp_model_tag})")

    print()
    issues = validate_br_file(br)
    if issues:
        print("VALIDATION: FAIL")
        for line in issues:
            print(f"  - {line}")
    else:
        print("VALIDATION: PASS")

    if len(br) == 0:
        return 1 if issues else 0

    ev = br.records["best_ev"]
    si = br.records["best_setting_index"]
    print()
    print("EV stats:")
    print(
        f"  min={float(ev.min()):.4f}  "
        f"mean={float(ev.mean()):.4f}  "
        f"median={float(np.median(ev)):.4f}  "
        f"max={float(ev.max()):.4f}  "
        f"std={float(ev.std()):.4f}"
    )

    counts = np.bincount(si.astype(np.int64), minlength=NUM_SETTINGS)
    top = np.argsort(-counts)[:5]
    print()
    print("Most-chosen setting indices (of 105 possible):")
    for s in top:
        pct = 100.0 * counts[s] / len(br)
        print(f"  setting {int(s):3d}:  {int(counts[s]):>10,}  ({pct:5.2f}%)")
    zero = int((counts == 0).sum())
    if zero:
        print(f"  ({zero} of {NUM_SETTINGS} settings were never chosen)")

    if args.sample > 0:
        n = min(args.sample, len(br))
        print()
        print(f"First {n} records:")
        print(f"  {'canonical_id':>12}  {'setting':>7}  {'best_ev':>10}")
        for r in br.records[:n]:
            print(
                f"  {int(r['canonical_id']):>12}  "
                f"{int(r['best_setting_index']):>7}  "
                f"{float(r['best_ev']):>10.4f}"
            )

    return 1 if issues else 0


if __name__ == "__main__":
    sys.exit(main())
