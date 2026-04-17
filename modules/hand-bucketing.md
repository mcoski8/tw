# Module: Hand Bucketing

## Overview
Groups similar 7-card hands into buckets for CFR computation. Hands in the same bucket should have similar optimal strategies.

## Feature Vector
Each 7-card hand is described by features:

1. **Pair count:** 0, 1, 2, 3 pairs (including trips counting as 1 pair + extra)
2. **Trips count:** 0 or 1 (or 2 for double trips)
3. **Quads:** 0 or 1
4. **Highest pair rank:** 0-14 (0 = no pair)
5. **Second pair rank:** 0-14
6. **Highest card rank:** 2-14
7. **Second highest card rank:** 2-14
8. **Connectivity:** max run length of consecutive ranks (2-7)
9. **Suited count:** max cards of one suit (1-4, but 1-2 is typical in 7 cards)
10. **Double suited:** boolean (two suits with 2+ cards each)
11. **Best middle hand type:** pair rank or high card values
12. **Has broadway (T+) count:** 0-7

## Bucketing Methods
1. **Feature hashing:** Deterministic bucket from feature vector
2. **K-means clustering:** Cluster on feature vectors using EV similarity
3. **EHS (Expected Hand Strength):** Group by pre-computed strength percentile

## Recommended: Hierarchical bucketing
- Level 1: Hand structure (pairs/trips/quads/unpaired) — ~10 categories
- Level 2: Within structure, rank of key cards — ~50-100 sub-categories
- Level 3: Within sub-category, suitedness — 3 levels (DS/SS/rainbow)
- Total: ~1,500-3,000 buckets
