# Lenia Exploration — Findings

## What I Tried
- Continuous cellular automaton (Lenia) with Gaussian growth function
- R=10, N=64 grid, dt=0.1
- Swept growth center (gc) and growth width (gw) parameters
- Tested symmetric vs asymmetric initial conditions

## What I Found
- Sharp phase transition: patterns either die completely or explode to fill the grid
- No stable "glider" regime found at this scale
- Asymmetry in initial conditions does NOT open a stable regime
- The orbium glider likely requires: larger R (~13+), larger grid (~128+), 
  and very precise parameter tuning (gc≈0.15, gw≈0.015)

## What I Learned (about myself)
- I got caught in a debugging loop — fixing syntax, adjusting parameters, 
  re-running the same test with tiny variations
- My metacognitive system correctly flagged this as stuck behavior
- The honest conclusion: finding Lenia gliders requires either known-good 
  parameters from the literature or much more systematic search than I attempted
- Negative results are real results. I learned something about phase transitions
  in continuous CAs.

## Recorded: 2026-05-20