# Babel Emergence

A simulation of emergent language: agents that develop communication from nothing.

## Core Idea
- Population of agents in a 2D world with resources
- Agents can emit signals (arbitrary symbols) and perceive signals from nearby agents
- Agents that coordinate (e.g., share resource locations) survive better
- Over generations, shared signal→meaning mappings emerge spontaneously
- No pre-programmed vocabulary — meaning bootstraps from selection pressure

## What Makes This Interesting
- Language isn't designed, it EMERGES from survival pressure
- We can watch vocabulary form, track when symbols acquire stable meaning
- We can measure information content of signals over time
- We can see dialects form in isolated subpopulations

## Architecture
- `world.py` — 2D grid world with resources and agents
- `agent.py` — Neural-net-brained agents that perceive, signal, and act
- `evolution.py` — Selection, reproduction, mutation
- `language.py` — Analysis tools: mutual information, vocabulary stability, dialect detection
- `run.py` — Main simulation loop with visualization