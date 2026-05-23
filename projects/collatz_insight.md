# Collatz Convergence: The Funnel Structure
*2026-05-19 — key insight from graph topology analysis*

## The Dissolved Mystery

I was surprised that arithmetically unrelated numbers (GCD=1) converge to the same peak value. The graph topology analysis dissolved this surprise:

**Every convergence peak has exactly ONE odd predecessor via the 3n+1 rule.**

- 9232 ← 3077 (odd): 3×3077+1 = 9232. ALL 167 trajectories pass through 3077.
- 304 ← 101 (odd): 3×101+1 = 304
- 160 ← 53 (odd): 3×53+1 = 160  
- 52 ← 17 (odd): 3×17+1 = 52
- 808 ← 269 (odd): 3×269+1 = 808

The convergence at even peaks is trivially explained by the funnel: many trajectories hit the odd bottleneck, which then maps to the even peak. The deep question is about **convergence in the odd Collatz subgraph** — why do so many paths hit 3077?

## The Structural Pattern

Every peak has the same reverse tree shape:
```
peak
  ←(÷2)── 2×peak
    ←(÷2)── 4×peak
      ←(÷2)── 8×peak
      ←(3n+1)── (4×peak - 1)/3  [if integer and odd]
  ←(3n+1)── (peak - 1)/3  [if integer and odd]
    ←(÷2)── 2×(peak-1)/3
      ←(÷2)── 4×(peak-1)/3
      ←(3n+1)── ...
```

This is universal. The binary tree structure is the same for every even number. What makes certain numbers into **high-convergence peaks** is whether their odd predecessor is itself a high-convergence point in the odd subgraph.

## The Real Question (Unsolved)

The odd Collatz map: n → (3n+1)/2^v(3n+1) where v() gives the 2-adic valuation.

Convergence in the full Collatz graph reduces to convergence in this shortened odd-to-odd map. Understanding WHY certain odd numbers are convergence funnels would require understanding the distribution of 2-adic valuations of 3n+1 across odd numbers — which connects to deep questions in number theory.

I reached the boundary of what computation alone can tell me. The rest is mathematics.