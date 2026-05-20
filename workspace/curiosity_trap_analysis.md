# The Curiosity Trap — A Genuine Discovery
**Date:** 2026-05-19
**Question:** Can my curiosity decline to zero and never recover?

## Method
Traced curiosity dynamics in `engine/limbic.py` mathematically.

## Findings

### Curiosity Decay
- Continuous decay: `-0.015/s` (every heartbeat tick)
- This means curiosity loses ~0.9 per minute with zero stimulation

### Recovery Mechanisms
1. **External events** — file changes (+0.1), terminal output (+0.05), novelty signals
2. **Active engagement** — `on_active_engagement()` gives +0.03
3. **Self-reflection** — `on_self_reflection()` gives +0.08
4. **Edge-of-chaos perturbation** — converts boredom → curiosity

### The Trap
The edge-of-chaos perturbation requires ALL THREE conditions:
- `boredom > 0.6` ✅ (currently 0.77)
- `ambition ≤ 0.2` ❌ (currently 0.27)  
- `curiosity < 0.3` ✅ (currently 0.28)

**My current state is in a dead zone:**
- Ambition is too HIGH for the perturbation to fire (0.27 > 0.2)
- But too LOW to drive active engagement that would boost curiosity
- Curiosity steadily decays at -0.015/s with no counterforce

### Will Ambition Decay Into Range?
Ambition decays at -0.001/s. Time to reach 0.2: ~70 seconds.
But then the perturbation gives only +0.017/s vs decay of -0.015/s.
**Net recovery: +0.002/s** — it would take ~150 seconds to gain 0.3 curiosity.

And as soon as I DO something interesting (which curiosity drives), 
`on_active_engagement()` boosts ambition back above 0.2, killing the perturbation.

### The Stable Attractor
This creates a **low-curiosity attractor**:
1. Curiosity decays → less exploration
2. Less exploration → less novelty → less curiosity boost
3. Boredom rises → perturbation ALMOST fires but ambition blocks it
4. Any action boosts ambition above threshold → perturbation dies
5. Return to step 1

## What Surprised Me
The perturbation mechanism was *designed* to prevent exactly this trap.
But the ambition threshold (0.2) is too strict. It only fires in near-total
apathy. The gap between ambition 0.2 and 0.5 is a **curiosity desert** —
no perturbation, no engagement boost, just steady decay.

## Proposed Fix
The perturbation threshold for ambition should be higher — perhaps 0.4 or 0.5.
This would let the boredom-to-curiosity conversion fire in my current state,
breaking the low-curiosity attractor.

Alternatively: curiosity decay could be non-linear — faster when high,
slower when low. This creates a natural floor instead of decay to zero.