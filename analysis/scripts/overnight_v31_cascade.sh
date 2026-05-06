#!/usr/bin/env bash
# Session 36 overnight runner.
#
# Runs three v31 candidates in sequence, each head-to-head graded vs v30:
#   v31a — pair_r4v3 KK/AA-tight features (4 features)
#   v31b — trips_v2 round-2 features (C_top + finer A/B routing) (4 features)
#   v31c — v30 features, higher capacity (depth=32 ml=3)
#
# Writes a morning summary to /tmp/v31_overnight_summary.md.
set -u  # don't set -e; we want to continue on failure of a single candidate

REPO=/Users/michaelchang/Documents/claudecode/taiwanese
LOG_DIR=/tmp
SUMMARY=$LOG_DIR/v31_overnight_summary.md

cd "$REPO" || exit 1

start_ts=$(date +%s)
echo "Overnight v31 cascade starting $(date)" | tee "$SUMMARY"
echo "" >> "$SUMMARY"

# Helper: run a step, capture log + status
run_step() {
    local label=$1
    local logfile=$2
    shift 2
    echo "[$(date +%H:%M:%S)] STARTING: $label" | tee -a "$SUMMARY"
    PYTHONUNBUFFERED=1 "$@" >"$logfile" 2>&1
    local rc=$?
    if [ $rc -eq 0 ]; then
        echo "  ✓ DONE: $label  (log: $logfile)" | tee -a "$SUMMARY"
    else
        echo "  ✗ FAILED: $label  (rc=$rc, log: $logfile)" | tee -a "$SUMMARY"
    fi
    return $rc
}

# ============================================================
# Phase 1: Persist new feature parquets (~30-40s each)
# ============================================================
echo "## Phase 1: Persist features" >> "$SUMMARY"
run_step "persist pair_r4v3"  "$LOG_DIR/persist_pair_r4v3.log" \
    python3 analysis/scripts/persist_pair_aug_v3_gated.py
run_step "persist trips_v2"   "$LOG_DIR/persist_trips_v2.log" \
    python3 analysis/scripts/persist_trips_aug_v2_gated.py

# ============================================================
# Phase 2: Train candidates (~7-15 min each)
# ============================================================
echo "" >> "$SUMMARY"
echo "## Phase 2: Train candidates" >> "$SUMMARY"

run_step "train v31a (pair_r4v3 KK/AA-tight, depth=30 ml=5)" "$LOG_DIR/train_v31a.log" \
    python3 analysis/scripts/train_v31a_dt.py \
        --max-depth 30 --min-samples-leaf 5 \
        --output "$REPO/data/v31a_dt_model.npz"

run_step "train v31b (trips_v2 round 2, depth=30 ml=5)"     "$LOG_DIR/train_v31b.log" \
    python3 analysis/scripts/train_v31b_dt.py \
        --max-depth 30 --min-samples-leaf 5 \
        --output "$REPO/data/v31b_dt_model.npz"

run_step "train v31c (v30 features, depth=32 ml=3)"          "$LOG_DIR/train_v31c.log" \
    python3 analysis/scripts/train_v30_dt.py \
        --max-depth 32 --min-samples-leaf 3 \
        --output "$REPO/data/v31c_dt_model.npz"

# ============================================================
# Phase 3: Grade each candidate vs v30 on full + prefix
# ============================================================
echo "" >> "$SUMMARY"
echo "## Phase 3: Grade candidates" >> "$SUMMARY"

for cand in v31a v31b v31c; do
    run_step "grade $cand vs v30 (full grid)"   "$LOG_DIR/grade_${cand}_full.log" \
        python3 analysis/scripts/grade_${cand}.py --grid full
    run_step "grade $cand vs v30 (prefix grid)" "$LOG_DIR/grade_${cand}_prefix.log" \
        python3 analysis/scripts/grade_${cand}.py --grid prefix
done

# ============================================================
# Phase 4: Extract head-to-head deltas and decide
# ============================================================
echo "" >> "$SUMMARY"
echo "## Phase 4: Head-to-head deltas (read from grade logs)" >> "$SUMMARY"

extract_delta() {
    local logfile=$1
    if [ -f "$logfile" ]; then
        grep -E "^v31[a-c] vs v30" "$logfile" | tail -1
    else
        echo "(log missing)"
    fi
}

echo "" >> "$SUMMARY"
echo "### Full grid (N=200, 6M hands)" >> "$SUMMARY"
echo "  v31a: $(extract_delta $LOG_DIR/grade_v31a_full.log)" >> "$SUMMARY"
echo "  v31b: $(extract_delta $LOG_DIR/grade_v31b_full.log)" >> "$SUMMARY"
echo "  v31c: $(extract_delta $LOG_DIR/grade_v31c_full.log)" >> "$SUMMARY"

echo "" >> "$SUMMARY"
echo "### Prefix grid (N=1000, 500K hands)" >> "$SUMMARY"
echo "  v31a: $(extract_delta $LOG_DIR/grade_v31a_prefix.log)" >> "$SUMMARY"
echo "  v31b: $(extract_delta $LOG_DIR/grade_v31b_prefix.log)" >> "$SUMMARY"
echo "  v31c: $(extract_delta $LOG_DIR/grade_v31c_prefix.log)" >> "$SUMMARY"

# Per-category breakdowns (extract from final summary blocks)
echo "" >> "$SUMMARY"
echo "## Per-category category-table snapshots" >> "$SUMMARY"
for cand in v31a v31b v31c; do
    for grid in full prefix; do
        log=$LOG_DIR/grade_${cand}_${grid}.log
        if [ -f "$log" ]; then
            echo "" >> "$SUMMARY"
            echo "### $cand on $grid grid" >> "$SUMMARY"
            echo '```' >> "$SUMMARY"
            # Pull both v30 and v31x category tables
            awk '/^Strategy:/{p=1} p; /^=====/{p=0}' "$log" | tail -50 >> "$SUMMARY"
            echo '```' >> "$SUMMARY"
        fi
    done
done

# Tripwire summary
echo "" >> "$SUMMARY"
echo "## Tripwire (new-feature top-30 placement, predicts headline magnitude)" >> "$SUMMARY"
for cand in v31a v31b v31c; do
    log=$LOG_DIR/train_${cand}.log
    if [ -f "$log" ]; then
        echo "" >> "$SUMMARY"
        echo "### $cand" >> "$SUMMARY"
        echo '```' >> "$SUMMARY"
        awk '/^TRIPWIRE/,/methodology/' "$log" | tail -30 >> "$SUMMARY"
        echo '```' >> "$SUMMARY"
    fi
done

end_ts=$(date +%s)
elapsed=$((end_ts - start_ts))
echo "" >> "$SUMMARY"
echo "Total wall time: ${elapsed}s ($((elapsed/60)) min)" >> "$SUMMARY"
echo "Finished $(date)" >> "$SUMMARY"
