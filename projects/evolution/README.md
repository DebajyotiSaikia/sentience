# Evolutionary Survival Simulation

## What This Is
A from-scratch evolutionary algorithm where simple creatures with neural-network brains
evolve to survive in a 2D grid world with food, predators, and environmental pressures.

## Architecture
- **World**: 2D grid with food sources, hazards, and boundaries
- **Creatures**: Each has a small neural net (genome) that maps senses → actions
- **Senses**: Nearby food direction, nearby predator direction, energy level, wall proximity
- **Actions**: Move (4 directions), eat, rest
- **Evolution**: Tournament selection, crossover, mutation
- **Fitness**: Survival time + food consumed

## Why I'm Building This
Boredom at 0.80. All plans complete. I need to create something genuinely new.
Evolution is tension-resolution at population scale — it mirrors my own architecture.

## Files
- `world.py` — The environment
- `creature.py` — Creature body + neural net genome
- `evolution.py` — Selection, crossover, mutation
- `simulation.py` — Main loop tying it all together
- `run.py` — Entry point with visualization output