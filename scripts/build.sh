#!/usr/bin/env bash
# Build the Rust engine in release mode and generate the 5-card lookup table
# if it is not already cached on disk.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# Make sure cargo is on PATH even in a non-interactive shell.
if ! command -v cargo >/dev/null 2>&1; then
    if [ -x "$HOME/.cargo/bin/cargo" ]; then
        export PATH="$HOME/.cargo/bin:$PATH"
    else
        echo "cargo not found. Install Rust: https://rustup.rs" >&2
        exit 1
    fi
fi

cd "$ROOT_DIR/engine"
cargo build --release

mkdir -p "$ROOT_DIR/data"
LOOKUP="$ROOT_DIR/data/lookup_table.bin"
if [ ! -f "$LOOKUP" ]; then
    echo "Generating 5-card lookup table at $LOOKUP ..."
    cargo run --release --quiet -- build-lookup --out "$LOOKUP"
fi

echo "Build complete."
