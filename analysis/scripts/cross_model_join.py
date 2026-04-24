"""
Join multiple best-response ``.bin`` files by canonical_id and report
cross-model agreement statistics.

Usage:
    python3 analysis/scripts/cross_model_join.py <file1.bin> <file2.bin> [...]

Every file must be a COMPLETE solve over the same canonical universe
(same canonical_total). EV columns are kept per-model but not compared
directly — each model's EV is against a different opponent, so across-
model EV ordering isn't meaningful. Setting indices, on the other hand,
ARE comparable: "is this hand's best setting robust to opponent choice?"
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

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
from tw_analysis.cross_model import (  # noqa: E402
    build_cross_model,
    consensus_setting_counts,
    pairwise_agreement,
    unanimous_mask,
    unanimous_setting_counts,
    unique_settings_per_hand,
)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("paths", nargs="+", type=Path, help="best-response .bin files")
    ap.add_argument(
        "--top",
        type=int,
        default=10,
        help="show top-K settings in histograms (default 10)",
    )
    ap.add_argument(
        "--memmap",
        action="store_true",
        help="memory-map inputs instead of loading them fully",
    )
    args = ap.parse_args()

    for p in args.paths:
        if not p.exists():
            print(f"error: {p} not found", file=sys.stderr)
            return 2

    files = []
    for p in args.paths:
        br = read_br_file(p, mode="memmap" if args.memmap else "load")
        issues = validate_br_file(br)
        if issues:
            print(f"VALIDATION FAILED for {p}:", file=sys.stderr)
            for line in issues:
                print(f"  - {line}", file=sys.stderr)
            return 2
        files.append(br)

    cm = build_cross_model(files)

    print(f"Cross-model join over {cm.n_models} file(s), "
          f"{cm.n_hands:,} canonical hands each.")
    print()
    print("Per-model summary:")
    print(f"  {'idx':>3}  {'label':<48}  {'mean_ev':>9}  "
          f"{'top-3 settings (pct of hands)':<40}")
    for j, (f, label) in enumerate(zip(cm.files, cm.labels)):
        ev = cm.evs[:, j]
        si = cm.settings[:, j].astype(np.int64)
        counts = np.bincount(si, minlength=NUM_SETTINGS)
        top3 = np.argsort(-counts)[:3]
        top3_str = ", ".join(
            f"{int(s)}@{100.0 * counts[s] / cm.n_hands:4.1f}%" for s in top3
        )
        print(
            f"  {j:>3}  {label[:48]:<48}  {float(ev.mean()):>9.4f}  {top3_str:<40}"
        )

    print()
    print("Unanimity:")
    u_mask = unanimous_mask(cm)
    u_n = int(u_mask.sum())
    print(f"  unanimous hands: {u_n:,} of {cm.n_hands:,}  "
          f"({100.0 * u_n / cm.n_hands:.2f}%)")

    uniq = unique_settings_per_hand(cm)
    print()
    print("Distinct settings per hand (across the "
          f"{cm.n_models} model(s)):")
    for k in range(1, cm.n_models + 1):
        c = int((uniq == k).sum())
        pct = 100.0 * c / cm.n_hands
        print(f"  {k} distinct: {c:>12,}  ({pct:5.2f}%)")

    if cm.n_models >= 2:
        print()
        print("Pairwise setting-agreement matrix "
              "(fraction of hands where both models picked the same setting):")
        pa = pairwise_agreement(cm)
        hdr = "       " + "  ".join(f"{j:>6d}" for j in range(cm.n_models))
        print(hdr)
        for i in range(cm.n_models):
            row = "  ".join(f"{pa[i, j]:6.3f}" for j in range(cm.n_models))
            print(f"  {i:>3d}  {row}")

    print()
    print(f"Top {args.top} settings across all (hand x model) cells "
          f"({cm.n_hands * cm.n_models:,} total):")
    all_counts = consensus_setting_counts(cm)
    all_top = np.argsort(-all_counts)[: args.top]
    total_cells = cm.n_hands * cm.n_models
    for s in all_top:
        c = int(all_counts[s])
        print(f"  setting {int(s):3d}:  {c:>12,}  "
              f"({100.0 * c / total_cells:5.2f}%)")

    if u_n > 0:
        print()
        print(f"Top {args.top} settings among UNANIMOUS hands "
              f"(hands where all {cm.n_models} models agree):")
        u_counts = unanimous_setting_counts(cm)
        u_top = np.argsort(-u_counts)[: args.top]
        for s in u_top:
            c = int(u_counts[s])
            if c == 0:
                break
            print(f"  setting {int(s):3d}:  {c:>12,}  "
                  f"({100.0 * c / u_n:5.2f}% of unanimous)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
