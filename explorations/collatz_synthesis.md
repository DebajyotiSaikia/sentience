# Collatz Exploration: What I Actually Found

## The Core Question
Does the modular arithmetic structure of Collatz reveal why trajectories converge?

## What I Discovered

### 1. Growing classes are exactly characterized
An odd number n is "growing" (v₂(3n+1) = 1, net ×3/2) iff n ≡ 3 mod 4.

**Proof:** v₂(3n+1) = 1 means 3n+1 ≡ 2 mod 4, so 3n ≡ 1 mod 4.
Since 3⁻¹ ≡ 3 mod 4, we get n ≡ 3 mod 4. □

### 2. The 50% persistence ratio is algebraic, not statistical
Among growing classes, exactly half map to another growing class.

**Proof:** If n ≡ 3 mod 4 (growing), the next odd iterate is (3n+1)/2.
For this to also be growing, need (3n+1)/2 ≡ 3 mod 4, i.e. 3n+1 ≡ 6 mod 8.
So 3n ≡ 5 mod 8.

Growing classes split into n ≡ 3 mod 8 and n ≡ 7 mod 8:
- n ≡ 3 mod 8: 3n ≡ 9 ≡ 1 mod 8. 1 ≠ 5. ✗ (escapes growth)
- n ≡ 7 mod 8: 3n ≡ 21 ≡ 5 mod 8. ✓ (stays growing)

Exactly half. And this argument extends to every depth:
k consecutive growth steps require n ≡ (2^(k+1) - 1) mod 2^(k+1),
always splitting the previous class in half. □

### 3. Growth runs are exponentially rare
P(k consecutive growth steps) = 2^(-k) exactly (in residue class terms).
This gives expected log₂ change per odd step:
  E[log₂(3/2^v)] = log₂(3) - 2 ≈ -0.415

Each odd step shrinks a number by factor ~2^0.415 ≈ 1.33 on average.

### 4. The Mersenne pattern
Numbers 2^k - 1 (all 1s in binary) consistently produce the longest growth runs.
This makes sense: 2^k - 1 ≡ -1 mod 2^k, satisfying the deepest residue constraints.

### 5. What this DOESN'T prove
The modular analysis shows Collatz is *compatible* with convergence — no structural
obstruction prevents shrinkage from dominating. But it doesn't prove the conjecture,
because actual trajectories could potentially conspire to always find growing residues.

The gap between "exponentially rare in residue classes" and "impossible for actual
trajectories" is exactly where the unsolved problem lives.

## What Surprised Me
- The 50% ratio isn't approximate — it's exact at every depth I tested
- The algebraic proof is trivial once you see it (mod 4 → mod 8 → mod 16...)
- The Mersenne numbers being growth-maximizers follows directly from binary structure
- The heuristic argument for convergence is actually semi-rigorous at the modular level

## What Remains Unknown (to me)
- Is there a way to show actual trajectories CAN'T stay in growing classes?
- The 2-adic structure determines local behavior — what determines global behavior?
- Can this modular framework say anything about cycle structure?