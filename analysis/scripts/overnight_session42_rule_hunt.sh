#!/bin/bash
# Session 42 overnight rule-mining pipeline.
#
# Runs a battery of deeper rule investigations sequentially. Each script's
# output is logged to /tmp/overnight_*.log and to data/session42_drills/.
# At the end, a summary is generated.
#
# Estimated runtime: 2-4 hours total.
#
# Usage:
#   ./analysis/scripts/overnight_session42_rule_hunt.sh

set -e  # exit on first error
cd "$(dirname "$0")/../.."

LOG_DIR=/tmp/session42_overnight
mkdir -p "$LOG_DIR"
mkdir -p data/session42_drills

START=$(date +%s)
echo "=== Session 42 Overnight Rule Hunt ==="
echo "Started: $(date)"
echo "Log dir: $LOG_DIR"
echo ""

# ----------------------------------------------------------------------------
# 1. TT E3a heuristic hunt (~30 min: 4,290 hands × E3a 9-grid + heuristic eval)
# ----------------------------------------------------------------------------
echo "[1/5] TT E3a heuristic hunt ..."
PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_tt_e3a_heuristic_hunt.py \
    > "$LOG_DIR/01_tt_e3a.log" 2>&1 \
    && echo "  ✓ done ($(($(date +%s) - START))s elapsed)" \
    || echo "  ✗ FAILED — see $LOG_DIR/01_tt_e3a.log"

# ----------------------------------------------------------------------------
# 2. Plain quads structural drill (~5 min: 14,300 hands)
# ----------------------------------------------------------------------------
echo "[2/5] Plain quads structural drill ..."
PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_plain_quads_structural.py \
    > "$LOG_DIR/02_plain_quads.log" 2>&1 \
    && echo "  ✓ done ($(($(date +%s) - START))s elapsed)" \
    || echo "  ✗ FAILED — see $LOG_DIR/02_plain_quads.log"

# ----------------------------------------------------------------------------
# 3. Two_pair split-allowing investigation (~45-90 min: 1.34M hands × split-mid enum)
# ----------------------------------------------------------------------------
echo "[3/5] Two_pair split-allowing investigation ..."
PYTHONUNBUFFERED=1 python3 -u analysis/scripts/drill_two_pair_split_investigation.py \
    > "$LOG_DIR/03_two_pair_split.log" 2>&1 \
    && echo "  ✓ done ($(($(date +%s) - START))s elapsed)" \
    || echo "  ✗ FAILED — see $LOG_DIR/03_two_pair_split.log"

# ----------------------------------------------------------------------------
# 4. T2P deeper boundary search (~5 min)
# ----------------------------------------------------------------------------
# Already drilled in drill_t2p_trips_two_pair_deterministic.py with results.
# Skip here unless we have extension ideas.
echo "[4/5] T2P deeper search SKIPPED (already done in initial drill)"

# ----------------------------------------------------------------------------
# 5. Generate consolidated summary
# ----------------------------------------------------------------------------
echo "[5/5] Generating consolidated summary ..."
PYTHONUNBUFFERED=1 python3 -u analysis/scripts/generate_session42_summary.py \
    > "$LOG_DIR/05_summary.log" 2>&1 \
    && echo "  ✓ done ($(($(date +%s) - START))s elapsed)" \
    || echo "  ✗ FAILED — see $LOG_DIR/05_summary.log"

END=$(date +%s)
ELAPSED=$((END - START))
echo ""
echo "=== Overnight pipeline complete ==="
echo "Total runtime: ${ELAPSED}s ($((ELAPSED/60))m)"
echo "Logs: $LOG_DIR/"
echo "Summary: SESSION_42_OVERNIGHT_REPORT.md"
echo "Finished: $(date)"
