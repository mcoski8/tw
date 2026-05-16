"""S93 Phase B — correctness test for --id-list-file mode.

Generate a small id list (sample of canonical_ids in the prefix N=1000 range
[0, 500_000)), invoke the engine via --id-list-file, then bit-exact compare
the resulting records against the existing prefix grid for the same ids.

Per-hand seed in solve_grid_one is `base_seed + canonical_id * φ`, so given
the same samples / seed / opponent the EVs must be byte-identical.
"""
from __future__ import annotations

import os
import struct
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PREFIX = ROOT / "data/oracle_grid_prefix500k_n1000.bin"
ID_LIST = ROOT / "data/session93/test_id_list_100.txt"
OUT = ROOT / "data/session93/test_id_list_100_out.bin"
ENGINE = ROOT / "engine/target/release/tw-engine"
CANONICAL = ROOT / "data/canonical_hands.bin"
LOOKUP = ROOT / "data/lookup_table.bin"

REC_SIZE = 4 + 105 * 4
HEADER_SIZE = 32

# Deterministic sample of 100 ids spread across the prefix range.
PREFIX_LEN = 500_000
N_SAMPLE = 100
STEP = PREFIX_LEN // N_SAMPLE  # 5000
SAMPLE_IDS = list(range(STEP // 2, PREFIX_LEN, STEP))[:N_SAMPLE]


def read_record(f, offset):
    f.seek(HEADER_SIZE + offset * REC_SIZE)
    return f.read(REC_SIZE)


def parse_record(rec):
    cid = struct.unpack("<I", rec[0:4])[0]
    evs = struct.unpack(f"<{105}f", rec[4 : 4 + 105 * 4])
    return cid, evs


def main():
    # Prepare id list
    ID_LIST.parent.mkdir(parents=True, exist_ok=True)
    ID_LIST.write_text("\n".join(str(i) for i in SAMPLE_IDS) + "\n")
    print(f"wrote id-list ({len(SAMPLE_IDS)} ids) to {ID_LIST}")

    # Remove any prior output so we get a fresh run
    if OUT.exists():
        OUT.unlink()
    OUT.parent.mkdir(parents=True, exist_ok=True)

    # Invoke engine (defaults match the prefix grid: samples=1000, seed=0xC0FFEE,
    # opponent=realistic, canonical_total in header = id_list.len() = 100).
    cmd = [
        str(ENGINE),
        "oracle-grid",
        "--canonical",
        str(CANONICAL),
        "--out",
        str(OUT),
        "--lookup",
        str(LOOKUP),
        "--samples",
        "1000",
        "--seed",
        str(0xC0FFEE),
        "--opponent",
        "realistic",
        "--block-size",
        "50",
        "--id-list-file",
        str(ID_LIST),
    ]
    print("running:", " ".join(cmd))
    rc = subprocess.run(cmd, cwd=ROOT)
    if rc.returncode != 0:
        print("engine FAILED")
        sys.exit(rc.returncode)

    # Read both files for the sampled ids and compare bit-exact.
    n_match = 0
    n_diff = 0
    max_abs = 0.0
    diffs = []
    with open(PREFIX, "rb") as fp, open(OUT, "rb") as fo:
        # OUT records are in input order = sorted id-list order.
        # PREFIX records are indexed by canonical_id (sequential 0..500k).
        # Confirm header on OUT.
        oh = fo.read(HEADER_SIZE)
        ph = fp.read(HEADER_SIZE)
        assert oh[0:4] == b"TWOG"
        assert ph[0:4] == b"TWOG"
        # canonical_total on OUT should equal N_SAMPLE
        o_ct = struct.unpack("<Q", oh[20:28])[0]
        p_ct = struct.unpack("<Q", ph[20:28])[0]
        print(f"OUT header canonical_total={o_ct} (expect {N_SAMPLE})")
        print(f"PREFIX header canonical_total={p_ct} (expect 6,009,159)")
        assert o_ct == N_SAMPLE, "id-list-mode header canonical_total mismatch"

        # Sample IDs from id-list are already sorted by construction.
        sorted_ids = sorted(set(SAMPLE_IDS))
        for k, want_id in enumerate(sorted_ids):
            # OUT row k
            o_rec = fo.read(REC_SIZE)
            o_id, o_evs = parse_record(o_rec)
            # PREFIX row at offset want_id
            p_rec = read_record(fp, want_id)
            p_id, p_evs = parse_record(p_rec)
            assert o_id == want_id, f"OUT row {k}: id {o_id} != {want_id}"
            assert p_id == want_id, f"PREFIX row {want_id}: id {p_id} != {want_id}"
            if o_evs == p_evs:
                n_match += 1
            else:
                n_diff += 1
                row_max = max(abs(a - b) for a, b in zip(o_evs, p_evs))
                if row_max > max_abs:
                    max_abs = row_max
                if len(diffs) < 5:
                    diffs.append((want_id, row_max))

    print(f"\nrows checked: {n_match + n_diff}")
    print(f"  bit-identical rows: {n_match}")
    print(f"  differing rows:     {n_diff}")
    print(f"  max abs ev diff:    {max_abs}")
    for d in diffs:
        print("  example diff:", d)

    if n_diff == 0:
        print("\n  ✅ PASS — id-list mode reproduces prefix grid bit-exact.")
        sys.exit(0)
    else:
        print("\n  ❌ FAIL — id-list mode does NOT match prefix grid bit-exact.")
        sys.exit(1)


if __name__ == "__main__":
    main()
