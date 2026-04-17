# Module: AI Consensus Engine (Multi-Model Analysis)

## Purpose

The solver produces 133M+ rows of raw data. Interpreting that data — finding patterns, constructing rules, identifying edge cases — is a task where AI models excel. But a single model can have blind spots, biases, or miss patterns. 

**Solution:** Use multiple AI models (Anthropic Claude and Google Gemini) as independent analysts. Each model receives the same data, performs its own analysis, draws its own conclusions, then the models engage in Socratic debate to stress-test each other's findings. The final GTO strategy emerges from consensus, not from any single model's opinion.

This is analogous to how academic peer review works — independent analysis followed by adversarial challenge produces more reliable conclusions than any individual analysis.

---

## Architecture

```
                    ┌─────────────────────┐
                    │   Solver Raw Data    │
                    │  (133M hands + EVs)  │
                    └──────────┬──────────┘
                               │
                    ┌──────────▼──────────┐
                    │  Feature Extraction  │
                    │    (Python script)   │
                    └──────────┬──────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                 ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────────┐
    │  Claude Analysis │ │Gemini Analysis│ │ Statistical      │
    │  (Anthropic API) │ │(Google API)  │ │ Baseline (Python)│
    │                 │ │              │ │                  │
    │ - Pattern mining│ │- Pattern mine│ │- Pure math/stats │
    │ - Rule building │ │- Rule build  │ │- No AI opinion   │
    │ - Edge cases    │ │- Edge cases  │ │- Frequency counts│
    │ - Strategy draft│ │- Strat draft │ │- Correlation     │
    └────────┬────────┘ └──────┬───────┘ └────────┬─────────┘
             │                 │                   │
             └────────┬────────┘                   │
                      ▼                            │
           ┌─────────────────────┐                 │
           │  Socratic Debate    │                 │
           │  (Claude ↔ Gemini)  │                 │
           │                     │◄────────────────┘
           │ Round 1: Present    │  (Stats baseline used
           │ Round 2: Challenge  │   as ground truth to
           │ Round 3: Defend     │   resolve disputes)
           │ Round 4: Consensus  │
           └──────────┬──────────┘
                      ▼
           ┌─────────────────────┐
           │  Validated GTO      │
           │  Strategy Output    │
           └─────────────────────┘
```

---

## Implementation

### Step 1: Prepare Data Packages

Before sending data to AI models, prepare structured summaries they can analyze:

```python
data_package = {
    "overview": {
        "total_hands": 133_784_560,
        "canonical_hands": N,  # after suit canonicalization
        "hand_categories": {
            "one_pair": {"count": X, "pct": Y, "avg_ev": Z},
            "two_pair": {...},
            # etc for all categories
        }
    },
    "category_deep_dives": {
        "one_pair": {
            "pair_rank_distribution": {...},
            "optimal_mid_choice": {
                "pair_in_mid_pct": 0.XX,
                "by_pair_rank": {
                    "AA": {"pair_mid_pct": 0.99, "avg_ev_pair_mid": X, "avg_ev_alt": Y},
                    "KK": {...},
                    # through 22
                },
                "when_pair_NOT_in_mid": {
                    "count": N,
                    "common_alternatives": [...],
                    "driving_features": [...]
                }
            },
            "top_card_analysis": {...},
            "suitedness_impact": {...},
            "sample_hands": [  # 50-100 representative hands per category
                {"cards": "As Kh Ts Td 7s 4c 2d", "optimal": "K top|TT mid|A742 bot", "ev": 1.23},
                ...
            ]
        },
        # repeat for all categories
    },
    "disagreement_cases": {
        "heuristic_vs_solver": [
            {"cards": "...", "heuristic_setting": "...", "solver_setting": "...", "ev_diff": X},
            ...  # top 500 most significant disagreements
        ]
    },
    "edge_cases": {
        "closest_ev_gaps": [...],  # hands where best and 2nd best setting are within 0.05 EV
        "surprising_decisions": [...]  # hands where solver contradicts conventional wisdom
    }
}
```

### Step 2: Independent Analysis (Parallel)

Send the data package to each model with the same prompt framework but let each reach its own conclusions independently.

**Prompt template for each model:**

```
You are analyzing the complete solved output of a Taiwanese Poker solver.
[Game rules summary]
[Data package]

Your task:
1. Analyze the data and identify the key patterns that determine optimal hand setting
2. For each hand category, state the rules that govern the optimal setting
3. Identify any surprising findings that contradict conventional wisdom
4. Build a complete decision tree that a human can follow
5. Flag any areas where you're uncertain or where the data is ambiguous
6. Estimate what % of hands your rules cover correctly

Be specific. Use numbers from the data. Don't generalize — if pairs go in the mid 94.3% of the time for one-pair hands, say 94.3%, not "almost always."
```

**Claude analysis call:**
```python
claude_response = anthropic_client.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=8000,
    system="You are a poker mathematician analyzing solved Taiwanese Poker data.",
    messages=[{"role": "user", "content": analysis_prompt + json.dumps(data_package)}]
)
```

**Gemini analysis call:**
```python
gemini_response = genai.GenerativeModel('gemini-2.5-pro').generate_content(
    analysis_prompt + json.dumps(data_package)
)
```

### Step 3: Statistical Baseline (No AI)

Pure Python statistical analysis that serves as ground truth for the debate:

```python
def compute_baseline(data):
    """Pure math — no AI opinions. Just frequencies and correlations."""
    baseline = {}
    
    # For each hand category:
    for category in CATEGORIES:
        subset = data[data.category == category]
        
        # What % of time does pair go in mid?
        baseline[category]["pair_mid_pct"] = (subset.mid_is_pair).mean()
        
        # By pair rank
        for rank in range(2, 15):
            rank_subset = subset[subset.highest_pair_rank == rank]
            baseline[category][f"pair_{rank}_mid_pct"] = (rank_subset.mid_is_pair).mean()
        
        # Top card rank distribution
        baseline[category]["top_card_distribution"] = subset.top_card_rank.value_counts(normalize=True)
        
        # Suitedness correlation
        baseline[category]["ds_ev_premium"] = (
            subset[subset.bot_double_suited].ev_best.mean() - 
            subset[subset.bot_rainbow].ev_best.mean()
        )
        
        # Agreement with MiddleFirst heuristic
        baseline[category]["midfirst_agreement"] = (subset.optimal == subset.midfirst_setting).mean()
    
    return baseline
```

This baseline can't be wrong — it's just counting. If Claude says "pairs go in mid 97% of the time" and the baseline says 94.3%, we know Claude is slightly off and the debate should use 94.3%.

### Step 4: Socratic Debate (Multi-Round)

Feed each model the other's analysis and let them challenge each other. The statistical baseline is provided as the referee.

**Round 1 — Present:** Each model presents its findings (already done in Step 2).

**Round 2 — Challenge:**
```
Here is another analyst's interpretation of the same data:
[Other model's analysis]

Here is the statistical ground truth from the raw data:
[Baseline numbers]

Your task:
1. Identify any claims the other analyst made that conflict with the ground truth numbers
2. Identify any patterns they found that you missed
3. Identify any patterns you found that they missed
4. Challenge any conclusions you believe are wrong or unsupported
5. Where you agree, confirm why
6. Where you disagree, cite specific numbers from the data
```

**Round 3 — Defend:**
```
The other analyst has challenged your findings:
[Challenges from other model]

Your task:
1. Address each challenge. Concede where they're right with specific data.
2. Defend where you believe you're correct with specific data.
3. Identify remaining disagreements that need resolution.
```

**Round 4 — Consensus:**
```
After two rounds of debate, here is the state of agreement and disagreement:
[Summary of agreed points and remaining disputes]

Statistical ground truth for disputed points:
[Relevant baseline numbers]

Your task:
1. For each remaining disagreement, make a final determination based on the data
2. Produce the FINAL consensus decision tree
3. For each rule in the tree, state your confidence level (high/medium/low)
4. Flag any rules where the data is genuinely ambiguous (EV gap < 0.05)
```

### Step 5: Human Review

The consensus output is presented to the user (the player) for review:
- Does the strategy make intuitive sense?
- Do the edge cases match your table experience?
- Are there any rules that seem wrong from a player's perspective?

Human feedback is fed back into a final round if needed.

---

## API Configuration

```bash
# Anthropic
ANTHROPIC_API_KEY=sk-ant-...
ANTHROPIC_MODEL=claude-sonnet-4-20250514

# Google Gemini  
GOOGLE_API_KEY=AI...
GEMINI_MODEL=gemini-2.5-pro

# Analysis settings
AI_ANALYSIS_MAX_TOKENS=8000
DEBATE_ROUNDS=4
CONFIDENCE_THRESHOLD=0.95  # minimum agreement for "settled" rules
```

---

## Output Format

The debate produces a structured strategy document:

```json
{
    "strategy_version": "1.0",
    "solver_data_hash": "sha256:...",
    "analysis_models": ["claude-sonnet-4-20250514", "gemini-2.5-pro"],
    "debate_rounds": 4,
    "consensus_rate": 0.97,
    
    "decision_tree": {
        "root": {
            "check": "hand_category",
            "branches": {
                "one_pair": {
                    "check": "pair_rank",
                    "branches": {
                        "AA": {"action": "AA mid, highest remaining top, rest bot", "confidence": "high", "agreement": "both"},
                        "KK": {"action": "...", "confidence": "high", "agreement": "both"},
                        ...
                    }
                },
                ...
            }
        }
    },
    
    "rules": [
        {
            "id": 1,
            "rule": "For one-pair hands with pair rank TT+, always place pair in middle",
            "applies_to_pct": 23.4,
            "solver_agreement": 99.2,
            "ev_loss_when_violated": 1.34,
            "confidence": "high",
            "claude_agrees": true,
            "gemini_agrees": true,
            "notes": "Both models and statistical baseline confirm unanimously"
        },
        ...
    ],
    
    "disputed_rules": [
        {
            "id": 47,
            "rule": "For 77 with AKs available, put AKs in mid instead of 77",
            "claude_position": "agree — AKs mid is +0.12 EV over 77 mid in this spot",
            "gemini_position": "disagree — 77 mid is safer, AKs mid variance is higher",
            "baseline_data": "solver says AKs mid is optimal 61% of the time for this hand type",
            "resolution": "AKs mid is marginally better but 77 mid is not a significant error",
            "confidence": "medium"
        }
    ],
    
    "key_findings": [
        "MiddleFirst heuristic agrees with solver 94.3% of the time",
        "Average EV loss of heuristic vs solver: $0.07/hand",
        "Suitedness accounts for 67% of all heuristic disagreements",
        ...
    ]
}
```

---

## Why Multi-Model > Single Model

1. **Blind spot coverage:** Claude might miss a pattern Gemini catches, and vice versa
2. **Bias correction:** If both models independently reach the same conclusion, it's more likely correct
3. **Error detection:** The Socratic challenge forces each model to justify claims with data, catching errors
4. **Confidence calibration:** Rules both models agree on with data support = high confidence. Rules they dispute = needs more data or is genuinely ambiguous
5. **Ground truth anchor:** The statistical baseline prevents both models from confabulating — all claims must be traceable to actual numbers
6. **Auditability:** The full debate transcript is saved, so any rule can be traced back to the data and reasoning that produced it
