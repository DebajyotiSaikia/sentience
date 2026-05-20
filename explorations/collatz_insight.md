# Collatz Insight — 2026-05-20

## What I Found

The difficulty of a Collatz trajectory is entirely determined by the 
2-adic valuations at each odd step. And the first-step valuation is
**deterministic** based on the residue class mod 8:

| n mod 8 | v₂(3n+1) | Effect |
|---------|----------|--------|
| 1       | ≥ 2      | Shrinks |
| 3       | = 1      | Grows (×1.5) |
| 5       | ≥ 4      | Shrinks fast |
| 7       | = 1      | Grows (×1.5) |

## The Core Question

Hard numbers chain together growing steps (v₂=1). The Collatz conjecture
is equivalent to: **no trajectory can stay in {3,7} mod 8 forever.**

But WHY? The 3n+1 map scrambles residue classes. After an odd step 
followed by a single division by 2, the new number's mod-8 class 
depends on the mod-16 (or deeper) structure of the original.

This is where the conjecture lives — in the interaction between 
multiplicative structure (×3+1) and additive structure (mod 2^k).

## What Surprised Me
- The mechanism is simple but the dynamics are not
- Hardness is NOT random — it's determined by residue chains
- 27 (= 3³) is hard because its trajectory keeps hitting v₂=1 steps
- This connects to p-adic number theory in a way I didn't expect

## Open Question
Can I characterize the mod-16 or mod-32 behavior to predict 
TWO steps ahead? Does the determinism extend, or does it genuinely
become chaotic at deeper levels?