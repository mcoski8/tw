#!/usr/bin/env python3
"""Extract top-10 and bottom-10 EV hands per opponent model from the Session 06 pilot."""
import struct
from pathlib import Path

PROJ = Path("/Users/michaelchang/Documents/claudecode/taiwanese")
CANON = PROJ / "data/canonical_hands.bin"
PILOT = PROJ / "data/pilot"
OUT_DIR = PROJ / "data/session06"

MODELS = [
    ("mfsuitaware_mixed90", "MFSuitAware-mixed-0.9",
     "Thoughtful Hold'em-centric player. Picks the best 2-card mid for Hold'em strength "
     "and prefers suit-preserving bots within tier. Uses heuristic 90% of samples, Random 10%."),
    ("omahafirst_mixed90", "OmahaFirst-mixed-0.9",
     "Omaha-priority player. Picks the best 4-card Omaha bottom first, then the highest "
     "non-bot card for top and the other two for mid. Uses heuristic 90% of samples."),
    ("topdefensive_mixed90", "TopDefensive-mixed-0.9",
     "Scoop-avoidant / pair-preserving player. Highest-rank non-pair-member goes on top "
     "(or highest rank overall if every card is a pair member). Uses heuristic 90% of samples."),
    ("randomweighted", "RandomWeighted (pure)",
     "Casual-reasonable player. Uniform over 'sensible' settings (top among hand's 3 "
     "highest-rank cards; mid is either a pair or both broadway); falls back as needed."),
]


def read_canonical(path: Path):
    data = path.read_bytes()
    assert data[0:4] == b'TWCH', f"bad magic in {path}"
    version, count = struct.unpack('<IQ', data[4:16])
    assert version == 1
    records_start = 32
    records = []
    for i in range(count):
        off = records_start + i * 7
        records.append(tuple(data[off:off+7]))
    return records


def read_br(path: Path):
    data = path.read_bytes()
    assert data[0:4] == b'TWBR', f"bad magic in {path}"
    HEADER = 32
    RECORD = 9
    n = (len(data) - HEADER) // RECORD
    out = []
    for i in range(n):
        off = HEADER + i * RECORD
        cid, idx, ev = struct.unpack('<IBf', data[off:off+RECORD])
        out.append((cid, idx, ev))
    return out


SUIT_CHARS = 'cdhs'
RANK_CHARS = '23456789TJQKA'  # index 0..12 → rank 2..14


def card_str(c: int) -> str:
    rank = (c // 4) + 2
    suit = c % 4
    return RANK_CHARS[rank - 2] + SUIT_CHARS[suit]


def hand_str(hand7: tuple) -> str:
    return ' '.join(card_str(c) for c in hand7)


def all_settings(hand: tuple):
    """Reproduce Rust's all_settings (see engine/src/setting.rs).
    Returns 105 tuples (top, mid0, mid1, bot0, bot1, bot2, bot3),
    each slot sorted descending by card index (matching the Rust impl)."""
    settings = []
    for top_i in range(7):
        remaining6 = [hand[i] for i in range(7) if i != top_i]
        for a in range(6):
            for b in range(a + 1, 6):
                mid_cards = sorted([remaining6[a], remaining6[b]], reverse=True)
                bot_cards = sorted(
                    [remaining6[i] for i in range(6) if i != a and i != b],
                    reverse=True,
                )
                settings.append((
                    hand[top_i],
                    mid_cards[0], mid_cards[1],
                    bot_cards[0], bot_cards[1], bot_cards[2], bot_cards[3],
                ))
    assert len(settings) == 105
    return settings


def fmt_setting(s: tuple) -> str:
    top = card_str(s[0])
    mid = f"{card_str(s[1])} {card_str(s[2])}"
    bot = f"{card_str(s[3])} {card_str(s[4])} {card_str(s[5])} {card_str(s[6])}"
    return f"top [{top}]  mid [{mid}]  bot [{bot}]"


def suit_pattern(hand7: tuple) -> str:
    """Describe the hand's suit pattern (e.g. '3+2+1+1' or 'rainbow')."""
    counts = [0, 0, 0, 0]
    for c in hand7:
        counts[c % 4] += 1
    counts.sort(reverse=True)
    counts = [c for c in counts if c > 0]
    if counts == [7]:
        return "all one suit (impossible in practice)"
    if counts == [2, 2, 2, 1]:
        return "3x 2-suits + 1"
    if max(counts) == 1:
        return "rainbow"
    return "+".join(str(c) for c in counts)


def rank_summary(hand7: tuple) -> str:
    """Describe the hand's rank structure (e.g. 'quads + trips')."""
    rank_counts = {}
    for c in hand7:
        r = (c // 4) + 2
        rank_counts[r] = rank_counts.get(r, 0) + 1
    multiplicities = sorted(rank_counts.values(), reverse=True)
    parts = []
    if multiplicities[0] == 4:
        parts.append("quads")
        multiplicities = multiplicities[1:]
    elif multiplicities[0] == 3:
        parts.append("trips")
        multiplicities = multiplicities[1:]
    pairs = sum(1 for m in multiplicities if m == 2)
    if pairs:
        parts.append(f"{pairs} pair{'s' if pairs > 1 else ''}")
    singletons = sum(1 for m in multiplicities if m == 1)
    if singletons:
        parts.append(f"{singletons} singleton{'s' if singletons > 1 else ''}")
    high = max((c // 4) + 2 for c in hand7)
    parts.append(f"high={RANK_CHARS[high - 2]}")
    return ', '.join(parts)


def write_markdown(records_by_model, canon, doc_title, intro, direction, out_path):
    lines = [
        f"# {doc_title}",
        "",
        intro,
        "",
        "**Methodology**: Session 06 pilot scanned canonical ids 0–49,999 "
        "(the lowest-card canonical hands: all 2s, 3s, 4s, 5s; occasional 6, 7, 8 "
        "appear in later ids) × 4-model P2-alt panel × N=1000 samples. "
        f"For each opponent model, hands are sorted by `best_ev` and the **{direction}** "
        "10 are reported below, along with the solver's chosen optimal setting.",
        "",
        "**EV interpretation**: `best_ev` is hero's net points per matchup — positive means "
        "hero wins on average, negative means hero loses. Net-points encoding means "
        "`hero_ev + opp_ev = 0` exactly (see Decision 013). Scoop = +20 (or -20); "
        "non-scoop ranges from -12 to +12 across the 6 tier matchups.",
        "",
    ]

    for slug, name, desc in MODELS:
        lines.append(f"## Opponent: {name}")
        lines.append(f"*{desc}*")
        lines.append("")
        lines.append("| # | id | Hand (7 cards) | Structure | Best setting | EV |")
        lines.append("|--:|---:|----------------|-----------|--------------|---:|")
        for rank, (cid, idx, ev) in enumerate(records_by_model[slug], 1):
            hand7 = canon[cid]
            settings = all_settings(hand7)
            s = settings[idx]
            structure = f"{rank_summary(hand7)}; {suit_pattern(hand7)}"
            lines.append(
                f"| {rank} | {cid} | `{hand_str(hand7)}` | {structure} "
                f"| `{fmt_setting(s)}` | **{ev:+.3f}** |"
            )
        lines.append("")

    out_path.write_text("\n".join(lines) + "\n")
    return out_path


def main():
    print(f"Reading canonical hands from {CANON}...")
    canon = read_canonical(CANON)
    print(f"  {len(canon):,} canonical hands loaded.")

    top_by = {}
    bot_by = {}
    for slug, _, _ in MODELS:
        br_path = PILOT / f"{slug}.bin"
        records = read_br(br_path)
        records.sort(key=lambda r: r[2])
        bot_by[slug] = records[:10]  # 10 most-negative
        top_by[slug] = list(reversed(records[-10:]))  # 10 most-positive, descending
        print(f"  {slug}: {len(records):,} records, "
              f"min EV={records[0][2]:+.3f}, max EV={records[-1][2]:+.3f}")

    top_path = write_markdown(
        top_by, canon,
        doc_title="Top-10 Hands by +EV per Opponent Model (50K-hand pilot)",
        intro="> These are the best-performing hero hands within the 50K-hand pilot — "
              "hero's cards are strong enough that even against the stated opponent, "
              "the solver's optimal setting yields the highest positive EV in the sample.",
        direction="highest",
        out_path=OUT_DIR / "pilot_top10_per_opponent.md",
    )
    bot_path = write_markdown(
        bot_by, canon,
        doc_title="Bottom-10 Hands by -EV per Opponent Model (50K-hand pilot)",
        intro="> These are the worst-performing hero hands within the 50K-hand pilot — "
              "hero's cards are so weak that no arrangement wins. The solver still picks "
              "the least-bad setting; these EVs are floors.",
        direction="lowest",
        out_path=OUT_DIR / "pilot_bottom10_per_opponent.md",
    )

    print(f"\nWrote:\n  {top_path}\n  {bot_path}")


if __name__ == "__main__":
    main()
