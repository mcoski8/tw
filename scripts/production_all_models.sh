#!/bin/bash
# Sprint 3 production solve: 6,009,159 canonical hands × 4-model P2-alt × N=1000.
# Session 06, 2026-04-18. Approved via Claude Desktop recommendation.
#
# Sequential by model to keep the machine responsive.
# Wall-clock: ~2.6 days per model (9× rayon speedup on Mac Mini), ~10.4 days total.
# Each output file: 32-byte TWBR header + 9 × 6,009,159 bytes = 54,082,463 bytes ≈ 51.6 MB.
#
# Crash-safe: rerun the same command to resume from the last flushed block.

set -euo pipefail

PROJ="/Users/michaelchang/Documents/claudecode/taiwanese"
ENGINE="$PROJ/engine/target/release/tw-engine"
CANON="$PROJ/data/canonical_hands.bin"
LOOKUP="$PROJ/data/lookup_table.bin"
BR_DIR="$PROJ/data/best_response"
LOG_DIR="$PROJ/data/session06"

SAMPLES=1000
SEED=12648430          # 0xC0FFEE

mkdir -p "$BR_DIR" "$LOG_DIR"

run_model() {
    local name="$1"
    local extra_args="$2"

    local out="$BR_DIR/${name}.bin"
    local log="$LOG_DIR/prod_${name}.log"

    echo "[$(date +%H:%M:%S)] === Production: $name ==="
    # shellcheck disable=SC2086
    /usr/bin/time -l "$ENGINE" solve \
        --canonical "$CANON" \
        --lookup "$LOOKUP" \
        --out "$out" \
        --samples "$SAMPLES" \
        --seed "$SEED" \
        --block-size 2000 \
        $extra_args \
        > "$log" 2>&1
    local rc=$?
    echo "[$(date +%H:%M:%S)] $name exit=$rc"
    if [ $rc -ne 0 ]; then
        echo "FAIL: $name — tail of $log:"
        tail -20 "$log"
        return $rc
    fi
}

run_model mfsuitaware_mixed90 "--opponent mixed --mix-base mfsuitaware --mix-p 0.9"
run_model omahafirst_mixed90  "--opponent mixed --mix-base omaha       --mix-p 0.9"
run_model topdefensive_mixed90 "--opponent mixed --mix-base topdef      --mix-p 0.9"
run_model randomweighted       "--opponent weighted"

echo "[$(date +%H:%M:%S)] Production complete — all 4 files written to $BR_DIR/"
ls -la "$BR_DIR/"
