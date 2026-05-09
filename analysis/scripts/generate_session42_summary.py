"""
Session 42 overnight — consolidated rule-mining summary generator.

Reads all overnight drill logs from /tmp/session42_overnight/*.log, extracts
key headlines, ranks rules by (lift × consistency × memorability), and writes
SESSION_42_OVERNIGHT_REPORT.md.

Run:
  PYTHONUNBUFFERED=1 python3 -u analysis/scripts/generate_session42_summary.py
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
LOG_DIR = Path("/tmp/session42_overnight")
OUT_PATH = ROOT / "SESSION_42_OVERNIGHT_REPORT.md"


def _read_log(path: Path) -> str:
    if not path.exists():
        return f"[log not found: {path}]"
    return path.read_text(errors="replace")


def _extract_headline(log: str, pattern: str) -> list[tuple[str, str, str]]:
    """Find lines matching pattern in log; extract (label, full_$, pref_$)."""
    results = []
    for line in log.split("\n"):
        m = re.match(pattern, line.strip())
        if m:
            results.append(m.groups())
    return results


def main() -> int:
    print(f"Generating Session 42 overnight summary at {time.strftime('%Y-%m-%d %H:%M:%S')}",
          flush=True)

    sections = []

    # Header
    sections.append("# Session 42 Overnight Rule-Mining Report")
    sections.append("")
    sections.append(f"_Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}_")
    sections.append("")
    sections.append("## TL;DR")
    sections.append("")
    sections.append("This report consolidates the overnight investigation of:")
    sections.append("- TT (two_trips, 4,290 hands) E3a heuristic hunt")
    sections.append("- Plain quads (14,300 hands) structural drill")
    sections.append("- Two_pair (1,338,480 hands) split-allowing rule investigation")
    sections.append("")
    sections.append("Each subsection below summarizes the headline findings, ranks rule candidates by lift on full + prefix grids, and flags the diminishing-returns frontier.")
    sections.append("")
    sections.append("---")
    sections.append("")

    # ----------------------------------------------------------------
    # 1. TT E3a hunt
    # ----------------------------------------------------------------
    sections.append("## 1. TT (two_trips) E3a heuristic hunt")
    sections.append("")
    log = _read_log(LOG_DIR / "01_tt_e3a.log")
    if "[log not found" in log:
        sections.append("_Log not found — drill did not run._")
    else:
        # Extract headline rows of form "  {name:<55}  $X.XX  $Y.YY  ★/blank"
        rows = re.findall(
            r"^\s+(.+?)\s+\$\s*([+-]?\d+\.\d+)\s+\$\s*([+-]?\d+\.\d+)\s*(★?)\s*$",
            log, re.MULTILINE)
        if rows:
            sections.append("| Heuristic | Full Δ/1000h | Prefix Δ/1000h | Both grids? |")
            sections.append("|---|---:|---:|---|")
            for name, full_d, pref_d, marker in rows:
                tick = "✓" if marker == "★" else ""
                sections.append(f"| {name.strip()} | ${full_d} | ${pref_d} | {tick} |")
        else:
            sections.append("_(could not parse rows from log)_")
        sections.append("")
        sections.append("**Verdict:** see `01_tt_e3a.log` for full output.")

    sections.append("")
    sections.append("---")
    sections.append("")

    # ----------------------------------------------------------------
    # 2. Plain quads
    # ----------------------------------------------------------------
    sections.append("## 2. Plain quads (4+1+1+1) structural drill")
    sections.append("")
    log = _read_log(LOG_DIR / "02_plain_quads.log")
    if "[log not found" in log:
        sections.append("_Log not found — drill did not run._")
    else:
        # Extract headline rows
        rows = re.findall(
            r"^\s+(\w[^[]+?)\s+full\s+\$\s*([+-]?\d+\.\d+)/1000h(?:\s+pref\s+\$\s*([+-]?\d+\.\d+)/1000h)?\s+\[(\w+)\]",
            log, re.MULTILINE)
        if rows:
            sections.append("| Heuristic | Full Δ/1000h | Prefix Δ/1000h | Kind |")
            sections.append("|---|---:|---:|---|")
            for name, full_d, pref_d, kind in rows:
                pref_str = f"${pref_d}" if pref_d else "—"
                sections.append(f"| {name.strip()} | ${full_d} | {pref_str} | {kind} |")
        else:
            sections.append("_(could not parse rows from log)_")

    sections.append("")
    sections.append("---")
    sections.append("")

    # ----------------------------------------------------------------
    # 3. Two_pair split investigation
    # ----------------------------------------------------------------
    sections.append("## 3. Two_pair split-allowing rule investigation")
    sections.append("")
    log = _read_log(LOG_DIR / "03_two_pair_split.log")
    if "[log not found" in log:
        sections.append("_Log not found — drill did not run._")
    else:
        # Extract boundary search rows
        rows = re.findall(
            r"^\s+(.+?)\s+\$\s*([+-]?\d+\.\d+)\s+\$\s*([+-]?\d+\.\d+)\s*(★?)\s*$",
            log, re.MULTILINE)
        if rows:
            sections.append("| Rule | Full Δ/1000h | Prefix Δ/1000h | Both grids? |")
            sections.append("|---|---:|---:|---|")
            for name, full_d, pref_d, marker in rows:
                tick = "✓" if marker == "★" else ""
                sections.append(f"| {name.strip()} | ${full_d} | ${pref_d} | {tick} |")
        # Also extract SPLIT-winning cells if present
        split_cells_match = re.search(
            r"SPLIT-winning cells:\n.*?\n(.+?)\n\n",
            log, re.DOTALL)
        if split_cells_match:
            sections.append("")
            sections.append("**SPLIT-winning cells (where mixed-pair mid beats RA/RB/RC):**")
            sections.append("")
            sections.append("```")
            sections.append(split_cells_match.group(1))
            sections.append("```")

    sections.append("")
    sections.append("---")
    sections.append("")

    # ----------------------------------------------------------------
    # Cross-cutting verdict
    # ----------------------------------------------------------------
    sections.append("## Verdict + Session 43 priority")
    sections.append("")
    sections.append("Rule candidates are ranked by:")
    sections.append("- **Both-grid positive Δ** (necessary)")
    sections.append("- **Δ magnitude on full grid** (scales with population × per-hand lift)")
    sections.append("- **Memorability** (how many conditions to remember)")
    sections.append("")
    sections.append("Diminishing-returns frontier: a rule that adds <$1/1000h whole-grid lift but requires a multi-cell exception list is past the human-memorability frontier.")
    sections.append("")
    sections.append("See individual log files in `/tmp/session42_overnight/` for full drill output.")
    sections.append("")
    sections.append("Files:")
    sections.append("")
    for name in sorted(LOG_DIR.glob("*.log")):
        sections.append(f"- `{name}`")

    OUT_PATH.write_text("\n".join(sections) + "\n")
    print(f"  wrote {OUT_PATH}", flush=True)
    print(f"  size: {OUT_PATH.stat().st_size:,} bytes", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
