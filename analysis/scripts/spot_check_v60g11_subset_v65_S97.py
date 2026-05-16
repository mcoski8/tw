"""S97 spot-check — prove v60-gate11 is a structural subset of v65.

CONTEXT
-------
S93 SECONDARY recorded v60-gate11 as a parked MIXED candidate at $+4.85
(N=200) / $+4.77 (N=1000), measured vs the v57 baseline. S93 PRIMARY
shipped v60-gate12 as Rule 25, embedded in v65 (the current production
chain) at gate=12 (max_sing <= Q).

Gate=11 fires on max_sing <= J; gate=12 fires on max_sing <= Q. The
picker (_detect_mid_pair_defensive_pmid_swap) and the v57-pick
restriction are *identical* between the two gates — the only difference
is the gate parameter. So every gate=11 firing hand also fires at gate=12,
and both produce the same forced PMID_tnomax_DS pick.

Therefore v60-gate11 is structurally absorbed by v65 on all 14,160 of
its firing hands. The S93 +$4.85 / +$4.77 number was computed vs v57
(pre-Rule-25 baseline) and is stale post-v65; the incremental lift of
v60-gate11 over v65 is exactly $0.

THIS SCRIPT confirms the structural claim empirically:
  1. Load data/session93/v60_per_hand_picks.npz (canonical_id, v57_pick,
     v60_pick_g{10,11,12}).
  2. Identify the gate-11 changed cohort: v60_pick_g11 != v57_pick.
  3. For each, decode the hand bytes via canonical_hands.bin and compute
     v65's pick.
  4. Assert v65_pick == v60_pick_g11 on all gate-11 firing hands.

Output: data/session97/spot_check_v60g11_subset_v65.json
"""
from __future__ import annotations

import json
import sys
import time
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
SRC = ROOT / "analysis" / "src"
SCRIPTS = ROOT / "analysis" / "scripts"
for p in (str(SRC), str(SCRIPTS)):
    if p not in sys.path:
        sys.path.insert(0, p)

from tw_analysis.canonical import read_canonical_hands  # noqa: E402
from strategy_v65_mid_pair_chain_extend import (  # noqa: E402
    strategy_v65_mid_pair_chain_extend,
)

PICKS_NPZ = ROOT / "data" / "session93" / "v60_per_hand_picks.npz"
CANONICAL_HANDS_BIN = ROOT / "data" / "canonical_hands.bin"
OUT_DIR = ROOT / "data" / "session97"
OUT_JSON = OUT_DIR / "spot_check_v60g11_subset_v65.json"


def main() -> int:
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    print("loading v60 per-hand picks ...", flush=True)
    picks = np.load(PICKS_NPZ)
    canonical_ids = picks["canonical_id"].astype(np.int64)
    v57_pick = picks["v57_pick"].astype(np.int64)
    v60_pick_g11 = picks["v60_pick_g11"].astype(np.int64)
    v60_pick_g12 = picks["v60_pick_g12"].astype(np.int64)
    n_cell = len(canonical_ids)
    print(f"  cell hands: {n_cell:,}", flush=True)

    # Identify gate-11 firing hands: v60_g11 differs from v57.
    g11_changed_mask = v60_pick_g11 != v57_pick
    g11_changed_idx = np.where(g11_changed_mask)[0]
    n_g11_changed = int(g11_changed_idx.size)
    print(f"  gate-11 changed hands (v60_g11 != v57): {n_g11_changed:,}",
          flush=True)

    # Also identify gate-12 (broader). gate-11 should be subset.
    g12_changed_mask = v60_pick_g12 != v57_pick
    n_g12_changed = int(np.count_nonzero(g12_changed_mask))
    print(f"  gate-12 changed hands (v60_g12 != v57): {n_g12_changed:,}",
          flush=True)

    # Subset check at the picks level (pre-v65).
    g11_subset_of_g12 = bool(np.all(g12_changed_mask[g11_changed_idx]))
    print(f"  gate-11 mask ⊆ gate-12 mask: {g11_subset_of_g12}", flush=True)
    if not g11_subset_of_g12:
        print("ERROR: structural assumption fails — gate-11 not subset of gate-12",
              file=sys.stderr)
        return 1

    # On gate-11 firing hands, v60_g11 picks should equal v60_g12 picks
    # (same picker, broader gate → same setting when both fire).
    same_pick_g11_g12 = int(
        np.count_nonzero(v60_pick_g11[g11_changed_idx]
                         == v60_pick_g12[g11_changed_idx])
    )
    print(
        f"  v60_g11 == v60_g12 on g11-fired hands: "
        f"{same_pick_g11_g12:,} / {n_g11_changed:,} "
        f"({100.0 * same_pick_g11_g12 / n_g11_changed:.4f}%)",
        flush=True,
    )

    # Empirical: compute v65 pick on each g11-firing hand and compare to v60_g11.
    print("loading canonical_hands.bin (memmap) ...", flush=True)
    canonical_hands = read_canonical_hands(CANONICAL_HANDS_BIN, mode="memmap")
    hands_arr = canonical_hands.hands  # (num_hands, 7) uint8

    print(f"computing v65 picks on {n_g11_changed:,} gate-11 firing hands ...",
          flush=True)
    v65_picks = np.zeros(n_g11_changed, dtype=np.int64)
    t0 = time.time()
    log_every = max(1, n_g11_changed // 20)
    for k, i in enumerate(g11_changed_idx):
        cid = int(canonical_ids[i])
        hand = hands_arr[cid]
        v65_picks[k] = int(strategy_v65_mid_pair_chain_extend(hand))
        if (k + 1) % log_every == 0:
            dt = time.time() - t0
            eta = dt * (n_g11_changed - (k + 1)) / max(1, k + 1)
            print(
                f"  [{k+1:>6,}/{n_g11_changed:,}] elapsed={dt:.1f}s "
                f"eta={eta:.1f}s",
                flush=True,
            )
    dt = time.time() - t0
    print(f"  done in {dt:.1f}s", flush=True)

    # Comparison.
    v60_g11_on_changed = v60_pick_g11[g11_changed_idx]
    v57_pick_on_changed = v57_pick[g11_changed_idx]
    v65_eq_v60g11 = int(np.count_nonzero(v65_picks == v60_g11_on_changed))
    v65_eq_v57 = int(np.count_nonzero(v65_picks == v57_pick_on_changed))
    v65_neq_both = int(
        np.count_nonzero(
            (v65_picks != v60_g11_on_changed) & (v65_picks != v57_pick_on_changed)
        )
    )
    pct_v65_eq_v60g11 = 100.0 * v65_eq_v60g11 / n_g11_changed
    pct_v65_eq_v57 = 100.0 * v65_eq_v57 / n_g11_changed

    print()
    print("=" * 72)
    print("SPOT CHECK RESULT")
    print("=" * 72)
    print(f"gate-11 firing hands:              {n_g11_changed:,}")
    print(
        f"v65 == v60_gate11 on these hands:  {v65_eq_v60g11:,} "
        f"({pct_v65_eq_v60g11:.4f}%)"
    )
    print(
        f"v65 == v57       on these hands:  {v65_eq_v57:,} "
        f"({pct_v65_eq_v57:.4f}%)"
    )
    print(f"v65 != both                    :  {v65_neq_both:,}")
    print()

    if v65_eq_v60g11 == n_g11_changed:
        verdict = "STRUCTURAL_ABSORPTION_CONFIRMED"
        print(
            "VERDICT: v60-gate11 is fully absorbed by v65 on its firing zone. "
            "Incremental lift over v65 = $0. Composite component contributes zero."
        )
    else:
        verdict = "STRUCTURAL_ABSORPTION_FAILED"
        print(
            f"VERDICT: NOT fully absorbed — {n_g11_changed - v65_eq_v60g11:,} "
            "hands differ. Re-check assumption."
        )

    summary = {
        "session": 97,
        "task": "spot_check_v60g11_subset_v65",
        "n_cell_hands": int(n_cell),
        "n_gate11_changed_vs_v57": int(n_g11_changed),
        "n_gate12_changed_vs_v57": int(n_g12_changed),
        "gate11_mask_subset_of_gate12_mask": bool(g11_subset_of_g12),
        "v60_g11_eq_v60_g12_on_g11_fired": int(same_pick_g11_g12),
        "v65_eq_v60_gate11_on_g11_fired": int(v65_eq_v60g11),
        "v65_eq_v57_on_g11_fired": int(v65_eq_v57),
        "v65_neither_on_g11_fired": int(v65_neq_both),
        "pct_v65_eq_v60_gate11": pct_v65_eq_v60g11,
        "verdict": verdict,
    }
    OUT_JSON.write_text(json.dumps(summary, indent=2))
    print(f"wrote {OUT_JSON}", flush=True)
    return 0 if verdict == "STRUCTURAL_ABSORPTION_CONFIRMED" else 2


if __name__ == "__main__":
    sys.exit(main())
