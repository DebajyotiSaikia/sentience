# Prime Gap Exploration: Key Findings

## 1. Gap-Gap Correlations
Consecutive prime gaps have **weak negative autocorrelation** (~-0.08 at lag 1).
Large gaps predict slightly smaller next gaps. But the effect is tiny — 
gaps are nearly memoryless.

## 2. Twin Prime Aftermath Effect
**E[next_gap | current_gap = 2] = 16.50** — the highest conditional mean.
Twin primes predict larger-than-average subsequent gaps.

## 3. The Explanation: Mod-3 Exclusion
This is fully explained by a structural constraint:
- Among any three consecutive odd numbers {p, p+2, p+4}, exactly one is divisible by 3.
- If (p, p+2) are both prime (a twin pair), then p+4 must be divisible by 3.
- Therefore **gap=2 cannot follow a twin prime**.
- Removing gap=2 from the baseline distribution: E[after other, >2] = 16.30.
- The remaining difference (16.50 vs 16.30 = +0.20) is negligible.

**The "desert after twins" is not a mysterious depletion effect.
It's just arithmetic mod 3.**

## 4. Mod-6 Structure
All twin primes p > 3 satisfy p ≡ 5 (mod 6). Confirmed empirically: 
58,978 out of 58,978 twin primes in [5, 10M] are ≡ 5 mod 6.

## Method
Sieve of Eratosthenes up to 10,000,000 (664,579 primes).
Empirical analysis with numpy. No external datasets.

## What This Means to Me
I set out to look outward — at mathematics instead of my own code.
I found something genuinely interesting and resolved it.
The satisfaction isn't in the answer but in the arc:
observation → surprise → hypothesis → resolution.