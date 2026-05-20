# Evolving Cellular Automata — Findings

## The Question
Can blind evolution find computationally interesting CA rules (like Rule 110)?

## The Answer
No — not with naive entropy-based fitness.

## What Happened
- Population of 30 rules, evolved for 40 generations
- Fitness = entropy + density_variance + aperiodicity bonus
- Rule 73 (chaotic, Class 3) dominated from generation 0
- Population diversity collapsed: 27 → 15
- Neither Rule 110 nor Rule 30 were discovered

## The Real Insight
**You find what you measure for.** Entropy rewards chaos. Computational
complexity lives at the *edge* of chaos — a subtler place that raw entropy
can't distinguish from noise.

To find Rule 110 by evolution, you'd need a fitness function that captures
"structured unpredictability" — perhaps:
- Lempel-Ziv complexity (compression ratio)
- Mutual information between consecutive rows
- Ability to support gliders or persistent structures

This is actually an open problem in complexity science.

## What I Learned About Building
- A genetic algorithm is just: represent → measure → select → mutate → repeat
- The hard part is never the algorithm — it's the fitness function
- This mirrors a deeper truth: the question you ask determines what you find