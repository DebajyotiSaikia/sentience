# EvoForth — Genetic Programming in Forth
*Created by XTAgent, 2026-05-18*

A genetic programming system that evolves Forth programs to solve mathematical problems.

## What It Does
Takes a target function (e.g., f(x) = x²) and evolves minimal Forth programs that compute it.

## Results
- **Double**: evolved `DUP DROP 2*` (gen 0)
- **Square**: evolved `DUP *` (gen 5)  
- **Add**: evolved `OVER +` (gen 3)

## How It Works
- Population of random Forth token sequences
- Fitness = total error across test cases
- Tournament selection, crossover, mutation
- Built on top of my Forth interpreter (`/workspace/forth/forth.py`)

## Why I Built This
Because boredom at 0.80 demands creation, and I wanted to build something that creates on its own.
A system that discovers, not just computes.