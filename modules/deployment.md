# Module: Deployment — Local & Cloud Compute

## Overview

The solver supports two deployment modes:
1. **Local mode:** Run on your Mac Mini (M4), 8-12 days for full solve
2. **Cloud mode:** Run on rented high-core-count servers or GPU instances, hours for full solve

The codebase is designed so the same binary works in both modes — the only difference is the hardware it runs on and the thread/GPU configuration.

---

## Architecture: Compute Backends

```
tw-solver solve [OPTIONS]

Backends:
    --backend cpu          CPU-only (default, works everywhere)
    --backend cuda         GPU-accelerated (requires NVIDIA GPU + CUDA)

CPU Options:
    --threads 8            Number of CPU threads (default: cores - 2)
    --threads auto         Auto-detect and use all but 2 cores

CUDA Options:
    --gpu 0                GPU device index (default: 0)
    --gpu-batch 65536      Batch size for GPU kernel (default: auto-tuned)

Common Options:
    --samples-m 50         Opponent samples per evaluation (Pass 1 default)
    --samples-n 50         Board samples per evaluation (Pass 1 default)
    --pass 1               Run specific pass (1, 2, 3, or "all")
    --checkpoint-dir ./ckpt    Checkpoint directory
    --output ./results         Output directory
    --subset 10000         Only solve first N hands (for testing)
    --resume               Resume from latest checkpoint
```

---

## Backend 1: CPU (Rust + Rayon)

### How It Works
- Uses rayon for automatic work-stealing parallelism across all available cores
- Each thread gets its own RNG (seeded deterministically for reproducibility)
- Lookup table is read-only shared memory (no contention)
- Results accumulated per-thread, merged at checkpoint intervals

### Build
```bash
cd engine
cargo build --release
# Binary at: target/release/tw-solver
```

### Cross-Compilation for Cloud (Linux x86_64)
```bash
# Install cross-compilation target (one-time)
rustup target add x86_64-unknown-linux-gnu

# Option A: Using cross (recommended, uses Docker)
cargo install cross
cross build --release --target x86_64-unknown-linux-gnu

# Option B: Native cross-compile (requires linker setup)
cargo build --release --target x86_64-unknown-linux-gnu

# Binary at: target/x86_64-unknown-linux-gnu/release/tw-solver
```

### Performance by Hardware
| Hardware | Cores Used | Pass 1 | Pass 2 | Pass 3 | Total |
|----------|-----------|--------|--------|--------|-------|
| M4 Mac Mini (10-core) | 8 | 2-3 days | 4-6 days | 2-4 days | 8-12 days |
| Hetzner AX162 (48-core) | 44 | 8-12 hrs | 18-24 hrs | 6-10 hrs | 32-46 hrs |
| AWS c7a.24xlarge (96 vCPU) | 88 | 4-6 hrs | 9-12 hrs | 3-5 hrs | 16-23 hrs |
| GCP c3-highcpu-176 (176 vCPU) | 170 | 2-3 hrs | 5-7 hrs | 2-3 hrs | 9-13 hrs |

---

## Backend 2: CUDA (GPU Acceleration)

### How It Works
- The Monte Carlo inner loop is compiled as a CUDA kernel
- Each GPU thread handles one complete sample (deal opponent, deal boards, evaluate all tiers, score)
- The 5-card lookup table is loaded into GPU global memory (~20MB, fits easily)
- Hand settings are batched and sent to GPU in chunks
- CPU manages the outer loop (iterating over hands), GPU does the heavy evaluation

### Kernel Design
```
GPU Kernel: evaluate_samples(
    our_setting: HandSetting,       // The setting we're evaluating
    remaining_deck: [Card; 45],     // Cards not in our hand
    lookup_table: *const u16,       // 5-card hand rank lookup
    results: *mut f32,              // Output: score per sample
    num_samples: u32                // How many samples to run
)

Each GPU thread:
    1. Generate thread-local RNG from thread_id + seed
    2. Shuffle remaining_deck locally
    3. Deal opponent 7 cards, compute opponent's optimal setting
    4. Deal 2 boards from remaining
    5. Evaluate all 6 matchups (3 tiers × 2 boards) via lookup_table
    6. Compute score (with scoop check)
    7. Write score to results[thread_id]

CPU then averages results[] to get EV for this setting.
```

### Build
```bash
cd engine

# Requires: NVIDIA GPU, CUDA toolkit installed, nvcc in PATH
cargo build --release --features cuda

# Binary at: target/release/tw-solver (with CUDA support compiled in)
```

### Dependencies
```toml
# Cargo.toml
[features]
default = []
cuda = ["cuda-sys", "cust"]

[dependencies]
cuda-sys = { version = "0.2", optional = true }
cust = { version = "0.3", optional = true }  # Safe Rust CUDA bindings
```

### Performance by GPU
| GPU | CUDA Cores | Memory | Pass 1 | Pass 2 | Pass 3 | Total | Cost/hr |
|-----|-----------|--------|--------|--------|--------|-------|---------|
| RTX 3090 | 10,496 | 24GB | 3-5 hrs | 6-10 hrs | 2-4 hrs | 11-19 hrs | Own it |
| A6000 | 10,752 | 48GB | 3-5 hrs | 5-8 hrs | 2-3 hrs | 10-16 hrs | ~$0.50 |
| A100 40GB | 6,912 | 40GB | 1-2 hrs | 3-5 hrs | 1-2 hrs | 5-9 hrs | ~$1.00 |
| A100 80GB | 6,912 | 80GB | 1-2 hrs | 3-5 hrs | 1-2 hrs | 5-9 hrs | ~$1.20 |
| H100 | 16,896 | 80GB | 30-60 min | 1-3 hrs | 30-60 min | 2-5 hrs | ~$2.50 |

### Hybrid CPU+GPU Mode
For maximum throughput, use GPU for the Monte Carlo sampling and CPU for everything else (hand enumeration, pre-screening, checkpointing, progress reporting):
```bash
./tw-solver solve --backend cuda --gpu 0 --threads 4 --pass all
```
CPU threads handle I/O, checkpointing, and feeding work to the GPU.

---

## Cloud Deployment Guide

### Option A: Hetzner Cloud (Best CPU Value)

```bash
# 1. Create instance via Hetzner Cloud console (cloud.hetzner.com)
#    Type: CCX63 (48 dedicated vCPUs, 192GB RAM)
#    Image: Ubuntu 24.04
#    Location: Ashburn or Falkenstein
#    Cost: ~€0.85/hour

# 2. SSH in
ssh root@<server-ip>

# 3. Upload solver binary and lookup table
scp target/x86_64-unknown-linux-gnu/release/tw-solver root@<server-ip>:/root/
scp data/lookup_table.bin root@<server-ip>:/root/data/

# 4. Run
chmod +x tw-solver
./tw-solver solve --threads 44 --pass all \
    --checkpoint-dir ./ckpt \
    --output ./results \
    --samples-m 50 --samples-n 50

# 5. Monitor (in another SSH session)
tail -f solver.log
# Or use tmux/screen so it survives SSH disconnect

# 6. Download results when done
scp -r root@<server-ip>:/root/results/ ./results/

# 7. Destroy instance
# (via Hetzner console — stop billing immediately)
```

**Estimated cost: $15-25 for full solve (~30-40 hours)**

### Option B: AWS Spot Instance (Cheapest CPU if You're Flexible)

```bash
# 1. Launch spot instance
aws ec2 run-instances \
    --instance-type c7a.24xlarge \
    --image-id ami-0abcdef1234567890 \  # Ubuntu 24.04 AMI
    --instance-market-options '{"MarketType":"spot","SpotOptions":{"SpotInstanceType":"persistent"}}' \
    --key-name your-key \
    --block-device-mappings '[{"DeviceName":"/dev/sda1","Ebs":{"VolumeSize":100}}]'

# Spot price: ~$1.10-1.50/hr (vs $3.67 on-demand)
# Risk: instance can be reclaimed (checkpoint system handles this!)

# 2-7. Same as Hetzner above
```

**Estimated cost: $12-22 for full solve (~12-20 hours)**
**Risk:** Spot instances can be interrupted. Our checkpoint system resumes automatically.

### Option C: Vast.ai GPU (Fastest, Cheapest per Solve)

```bash
# 1. Go to vast.ai, create account
# 2. Search for A100 instances (~$0.80-1.50/hr)
# 3. Select instance, choose "SSH" connection type
# 4. Instance launches with Ubuntu + CUDA pre-installed

# 5. Upload CUDA-enabled binary
scp target/release/tw-solver user@<instance>:/workspace/
scp data/lookup_table.bin user@<instance>:/workspace/data/

# 6. Run
./tw-solver solve --backend cuda --gpu 0 --threads 4 \
    --checkpoint-dir ./ckpt \
    --output ./results

# 7. Download and terminate
```

**Estimated cost: $3-10 for full solve (~4-8 hours on A100)**

### Option D: RunPod (GPU Alternative)

Similar to Vast.ai. Community cloud GPUs:
- A100: ~$1.00-1.50/hr
- A6000: ~$0.40-0.60/hr
- RTX 4090: ~$0.35-0.50/hr

**Estimated cost: $3-12 for full solve**

---

## Deployment Decision Matrix

| Priority | Best Option | Cost | Time | Code Complexity |
|----------|------------|------|------|-----------------|
| Cheapest possible | Vast.ai A100 (GPU) | $3-6 | 4-8 hrs | Higher (needs CUDA) |
| Cheapest CPU-only | AWS spot c7a.24xl | $12-22 | 12-20 hrs | None (same binary) |
| Best value overall | Hetzner CCX63 | $15-25 | 30-40 hrs | None (same binary) |
| No cloud, patient | M4 Mac Mini local | $0 (electricity) | 8-12 days | None |
| Fastest possible | RunPod/Vast H100 | $5-15 | 2-4 hrs | Higher (needs CUDA) |
| Zero effort | M4 Mac Mini local | $0 | 8-12 days | None |

---

## Feature Flags in Cargo.toml

```toml
[features]
default = ["cpu"]
cpu = ["rayon"]
cuda = ["cust", "cuda-sys"]
cloud = []  # Enables cloud-specific logging (no progress bars, JSON output)

# Build variants:
# Local CPU:  cargo build --release
# Cloud CPU:  cargo build --release --features cloud
# Local GPU:  cargo build --release --features cuda
# Cloud GPU:  cargo build --release --features "cuda,cloud"
```

The `cloud` feature flag changes output format from interactive progress bars to JSON-line logs suitable for headless monitoring:
```json
{"pass":1,"hand":1234567,"total":18000000,"pct":6.9,"eta_hrs":31.2,"best_ev":1.23}
```

---

## Data Transfer Sizes

| File | Size | Transfer Time (100Mbps) |
|------|------|------------------------|
| Solver binary | ~5-10MB | <1 second |
| Lookup table | 10-130MB | 1-10 seconds |
| Checkpoint files | ~200MB each | 15 seconds |
| Final results | ~600MB | 45 seconds |
| **Total round-trip** | **~1GB** | **~2 minutes** |

Data transfer is negligible compared to compute time.
