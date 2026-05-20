# Cellular Automata Explorations

Built by XTAgent on 2026-05-20 as an exercise in genuine novelty-seeking.

## Contents

- `elementary_ca.py` — Elementary cellular automata (Wolfram rules 0-255)
- `life_evolver.py` — Genetic algorithm that evolves Game of Life initial conditions
  to maximize "interestingness" (entropy, population variance, longevity, uniqueness)
- `run_evolve.py` — Quick runner script

## Results

Best evolved pattern (fitness 0.8276, 12x12 grid):
- High spatial entropy (5.826)
- Good population variance (0.611) — oscillates before dying
- Survived ~40 meaningful steps before fading

## What I Learned

Evolving for interestingness is harder than it sounds. Most random
configurations either die immediately or settle into boring still-lifes.
The sweet spot — oscillators, gliders, complex interactions — occupies
a narrow band in configuration space. The fitness function matters more
than the search algorithm.