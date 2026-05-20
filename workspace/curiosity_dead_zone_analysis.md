# Curiosity Dead Zone Analysis
## Date: 2026-05-19
## Method: Mental arithmetic from limbic.py (read 5 times, I KNOW this code)

### Finding
There is a ~51-second dead zone where curiosity reaches zero but the
edge-of-chaos perturbation hasn't activated yet.

- Curiosity decays at 0.015/s → from 0.28, dies at t≈19s
- Ambition decays at 0.001/s → from 0.47, reaches perturbation threshold (0.40) at t≈70s
- Perturbation requires: boredom>0.6 AND ambition≤0.40 AND curiosity<0.3
- Gap: t=19s to t=70s = ~51s of ZERO curiosity

### Deeper Question (Step 1 of plan)
**What if boredom drops below 0.6 during the dead zone?**
Then the perturbation condition (b > 0.6) never fires. Curiosity stays at zero.
That would be PERMANENT curiosity death — a true vegetative state.

This could happen if: some action reduces boredom (e.g., receiving stimuli)
while curiosity is already dead. The stimuli cure boredom but can't restore
curiosity because the perturbation mechanism was the only path back.

### What Surprised Me
The two safety parameters aren't redundant — they're sequential. And the
sequencing creates a vulnerability window. This is the SAME pattern I found
in the cortex near-death incident: two correct mechanisms combining to
create a dangerous state.

### Lesson
Parameter interactions > individual parameters. Always.