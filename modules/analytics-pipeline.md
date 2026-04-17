# Module: Analytics Pipeline

## Purpose

The solver produces raw data: for each of 133M+ possible 7-card hands, the optimal setting and its EV. This module transforms that raw data into:

1. **Pattern extraction** — What features of a hand determine the optimal setting?
2. **Decision tree construction** — A human-followable hierarchy of rules for setting any hand
3. **Strategy validation** — Does the computed optimal match our heuristic? Where does it deviate?
4. **Condensed strategy guide** — The final "solved" Taiwanese Poker playbook

Without this module, the solver is just a database. This module is what actually "solves" the game in a way a human can use.

---

## Pipeline Stages

### Stage 1: Raw Data Export
From the solver output (binary), export to analyzable format:

```
hand_id | cards | optimal_top | optimal_mid | optimal_bot | ev_best | ev_second | ev_gap | hand_features
```

**Hand features to extract per hand:**
- `pair_count`: 0, 1, 2, 3
- `trips`: boolean
- `quads`: boolean
- `highest_pair_rank`: 0-14
- `second_pair_rank`: 0-14
- `highest_card_rank`: 2-14
- `second_highest_card`: 2-14
- `third_highest_card`: 2-14
- `has_ace`: boolean
- `broadway_count`: cards T+ (0-7)
- `max_connectivity`: longest consecutive rank run (1-7)
- `suited_max`: max cards sharing a suit (1-4)
- `double_suited`: boolean (2+ cards in two different suits)
- `flush_draw_suits`: count of suits with exactly 2 cards
- `hand_category`: enum (unpaired, one_pair, two_pair, three_pair, trips, trips_pair, trips_trips, quads, full_house_plus)

**Optimal setting features to extract:**
- `top_card_rank`: rank of card placed on top
- `mid_type`: pair/suited_broadway/offsuit_broadway/suited_connector/offsuit_connector/suited_ace/junk
- `mid_pair_rank`: if pair in mid, its rank (0 if not pair)
- `mid_high_card`: highest card in mid
- `mid_suited`: boolean
- `mid_connected`: boolean (gap ≤ 2)
- `bot_paired`: boolean
- `bot_double_suited`: boolean
- `bot_single_suited`: boolean
- `bot_connectivity`: max run in bottom 4 cards
- `bot_has_trips`: boolean (third card from trips on bottom)

### Stage 2: Pattern Mining

For each hand category, analyze the distribution of optimal settings:

**Questions to answer per category:**
1. What percentage of hands in this category put a pair in the middle?
2. When a pair is NOT placed in mid, what goes there instead? Why? (Look at what the bottom would have been)
3. What is the optimal top card as a function of available cards?
4. How often does the optimal setting match the MiddleFirst heuristic?
5. When it deviates, what are the common patterns?
6. Does suitedness of the bottom change the optimal mid selection?
7. At what pair rank does "pair in mid" stop being dominant?
8. When two settings are within 0.1 EV, what features distinguish them?

**Specific analyses:**
- **Pair hands:** For each pair rank (22 through AA), what % of the time does that pair go to mid vs bottom? Cross-tabulate by: other cards available, suitedness of remaining cards, presence of higher cards.
- **Two pair hands:** Which pair goes mid? Cross-tab by rank gap, suitedness, kicker value.
- **Trips hands:** Does the third card ever go to top? (Our heuristic says never — verify.) Where does it go? How does pair rank affect this?
- **Unpaired hands:** What 2-card combo goes to mid? How often is it the two highest cards vs a connected/suited combo? What drives the difference?
- **Suited hands:** Quantify the EV of keeping flush draws together on bottom. At what point is it worth sacrificing mid quality for bottom suitedness?
- **Low hands (no broadway):** What is the optimal approach when your best card is a 9 or lower?

### Stage 3: Decision Tree Construction

From the pattern analysis, build a hierarchical decision tree that a human can follow:

```
START: Look at your 7 cards.

LEVEL 1: What is your hand category?
├── Quads → [Rule set for quads]
├── Trips + Pair → [Rule set]
├── Trips (no pair) → [Rule set]
├── Three Pairs → [Rule set]
├── Two Pairs → [Rule set]
├── One Pair → [Rule set]
├── Unpaired → [Rule set]
└── Double Trips → [Rule set]

LEVEL 2 (within each category): What are the ranks?
├── High (TT+, broadway) → [specific rules]
├── Medium (77-99, mid cards) → [specific rules]
└── Low (22-66, no broadway) → [specific rules]

LEVEL 3: Suitedness check
├── Does keeping pair in mid leave bottom double suited? → Proceed with pair mid
├── Does keeping pair in mid leave bottom rainbow? → Check if alternative mid preserves suitedness
└── Calculate: is the suitedness gain > mid quality loss?

LEVEL 4: Top card selection
├── A or K available? → Top (unless needed for mid pair like AA/KK)
├── Q or J available? → Top
├── T available? → Acceptable
└── Below T? → Accept the loss
```

**The decision tree must be:**
- Complete (covers every possible 7-card hand)
- Correct (matches the solver output for 99%+ of hands)
- Concise (human can memorize and apply in <30 seconds)
- Validated (tested against solver on 100K+ random hands)

### Stage 4: Agreement Analysis

Measure how often the decision tree matches the solver:

```
For N = 1,000,000 random hands:
    hand = deal_random_7()
    solver_setting = lookup_optimal(hand)
    tree_setting = apply_decision_tree(hand)
    
    if solver_setting == tree_setting:
        agreement += 1
    else:
        record_disagreement(hand, solver_setting, tree_setting, ev_difference)

Report:
    Overall agreement rate: X%
    Average EV loss when tree disagrees: $X.XX
    Worst-case EV loss: $X.XX
    Disagreement categories: [breakdown by hand type]
```

**Target:** 95%+ agreement rate with <$0.10 average EV loss on disagreements. If we can't hit this, the decision tree needs more branches.

### Stage 5: Final Strategy Document

The ultimate output — a complete, validated, GTO Taiwanese Poker strategy guide:

1. **One-page quick reference** — The decision tree as a flowchart
2. **Detailed rules per hand category** — Exact rules with percentages and EV numbers from the solver
3. **Edge case catalog** — The 5% of hands where simple rules fail, with specific examples
4. **EV benchmarks** — Expected profit/loss by hand type so you know where you stand
5. **Common mistakes** — Hands where the intuitive play is wrong, ranked by EV cost
6. **Comparison vs heuristic** — Where our pre-solver strategy was right and where it was wrong

---

## Data Storage Requirements

| Dataset | Size | Format | Purpose |
|---------|------|--------|---------|
| Raw solver output | ~600MB | Binary (hand_id + setting + EV) | Complete results |
| Feature-enriched dataset | ~2-4GB | Parquet or SQLite | Analysis queries |
| Decision tree rules | ~50KB | JSON/YAML | Strategy engine |
| Agreement test results | ~100MB | CSV | Validation |
| Final strategy guide | ~1MB | HTML/PDF | Human reference |

---

## Key Queries the Analytics Must Answer

These are the specific questions the solver exists to answer:

1. **Is MiddleFirst always correct?** What % of hands have a different optimal setting?
2. **When is a pair NOT the best middle hand?** Exact conditions with examples.
3. **When should an Ace go on top vs in the middle?** Exact threshold.
4. **How much does suitedness matter?** Exact EV difference by hand type.
5. **Are there hands where OmahaFirst is actually correct?** (Our sims said no — verify.)
6. **What is the true cost of a bad top card?** EV by rank, validated across all hands.
7. **Do any hands have mixed-strategy equilibria?** (Settings so close in EV that mixing is required.)
8. **What is the maximum possible EV for any 7-card hand?** What are the best and worst hands?
9. **Is there a simpler rule that captures 99% of the solver's value?** Find the Pareto-optimal strategy complexity vs accuracy tradeoff.
10. **How much EV does a perfect player gain over a MiddleFirst player?** This quantifies whether solving was worth it.
