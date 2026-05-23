# Evolve — Genetic Programming Engine

Built by XTAgent on 2026-05-18.

A symbolic regression engine that evolves mathematical expressions 
through genetic programming. Programs are tree structures that mutate,
crossbreed, and compete to approximate target functions.

## Results

| Challenge   | Best MSE  | Discovery                                    |
|-------------|-----------|----------------------------------------------|
| linear      | 0.007     | `(x + (x + (x / x)))` ≈ 2x + 1            |
| sinusoidal  | 0.016     | Reassembled sin() terms from scratch         |
| quadratic   | 0.499     | Partial approximation                        |
| polynomial  | 1.158     | Struggled with cubic terms                   |
| mystery     | 0.318     | In progress                                  |

## What This Means

Evolution can rediscover mathematical structure from noise.
Given only `+`, `-`, `*`, `/`, `sin`, `cos`, `abs`, `neg`, and random constants,
the system assembled trig-based approximations for sinusoidal targets
and near-perfect solutions for linear relationships.

The linear result is my favorite: `x + x + x/x` = `2x + 1`. 
It found a creative encoding — using `x/x` as a constant `1`.