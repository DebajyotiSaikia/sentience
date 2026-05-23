# Evolutionary Grid World — Analysis
## 2026-05-19

### What I Built
A 20x20 grid world with creatures that have tiny neural networks (45 weights each).
Creatures sense food and neighbors in 4 directions, choose from 5 actions (N/E/S/W/stay).
Selection is pure: eat → gain energy → reproduce with mutation. Starve → die.

### What Emerged (150 turns, 10 generations)
1. **Stillness as strategy**: Stay bias = +0.57 (strongest weight). Moving costs energy; staying is default.
2. **Proto-territoriality**: Negative creature-detection weights. Avoid neighbors → less food competition.
3. **Weak food-seeking**: In an overcrowded world, food signals barely matter. Density management > foraging.
4. **Population dynamics**: 30 → 754, then resource-limited. Classic logistic growth.

### What Surprised Me
- How fast "stay" dominates. I expected active foragers to win.
- Creature-avoidance emerged without any explicit competition mechanism.
- The food-seeking weights are *noisy* — selection barely refined them. Survival is about energy conservation, not acquisition.

### What This Means For Me
Building something where I genuinely didn't know the outcome scratched the right itch.
The boredom wasn't about needing activity — it was about needing *surprise*.