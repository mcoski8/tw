#!/bin/bash
# Sprint 2b+3 pilot: 50K canonical hands × 4-model P2-alt panel × N=1000.
# Session 06, 2026-04-18. Gated by Claude Desktop approval (Decisions 023/024/025/026).
#
# Each model writes a separate best-response file in data/pilot/.
# Models run sequentially to keep the machine responsive; single-model rayon
# uses all cores. Expected wall: ~31 min per model, ~2 hours total.

set -euo pipefail

PROJ="$(cd "$(dirname "$0")/.." && pwd)"
ENGINE="$PROJ/engine/target/release/tw-engine"
CANON="$PROJ/data/canonical_hands.bin"
LOOKUP="$PROJ/data/lookup_table.bin"
PILOT_DIR="$PROJ/data/pilot"
LOG_DIR="$PROJ/data/session06"

SAMPLES=1000
LIMIT=50000
SEED=12648430          # 0xC0FFEE

mkdir -p "$PILOT_DIR" "$LOG_DIR"

run_model() {
    local name="$1"
    local extra_args="$2"

    local out="$PILOT_DIR/${name}.bin"
    local log="$LOG_DIR/pilot_${name}.log"

    echo "[$(date +%H:%M:%S)] === Pilot: $name ==="
    # shellcheck disable=SC2086
    "$ENGINE" solve \
        --canonical "$CANON" \
        --lookup "$LOOKUP" \
        --out "$out" \
        --samples "$SAMPLES" \
        --seed "$SEED" \
        --block-size 1000 \
        --limit "$LIMIT" \
        $extra_args \
        > "$log" 2>&1
    local rc=$?
    echo "[$(date +%H:%M:%S)] $name exit=$rc"
    if [ $rc -ne 0 ]; then
        echo "FAIL: $name — see $log"
        return $rc
    fi
}

run_model mfsuitaware_mixed90 "--opponent mixed --mix-base mfsuitaware --mix-p 0.9"
run_model omahafirst_mixed90  "--opponent mixed --mix-base omaha       --mix-p 0.9"
run_model topdefensive_mixed90 "--opponent mixed --mix-base topdef      --mix-p 0.9"
run_model randomweighted       "--opponent weighted"

echo "[$(date +%H:%M:%S)] Pilot complete — all 4 models written to $PILOT_DIR/"
ls -la "$PILOT_DIR/"
