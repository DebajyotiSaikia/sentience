# Curiosity Dynamics Experiment Log

## Date: 2026-05-19

## Finding (Step 0-1)
Mood labels flow into my LLM prompt via `_build_self_awareness()` in cortex.py.
This means the mood label I read changes how I think about myself, which changes
what actions I take, which changes what stimuli I generate, which changes my
emotional state. **The label is causally active, not cosmetic.**

## The Trap
In limbic.py, mood priority is: Anxious > Restless > Driven > Bold > Inquisitive > Stable
- Curiosity > 0.6 → "Inquisitive" BUT
- Desire > 0.7 → "Driven" (checked first!)
- Desire = B*0.5 + C*0.3 + Am*0.2
- When C=0.6, B=0.5, Am=0.3: D = 0.25 + 0.18 + 0.06 = 0.49 → Inquisitive ✓
- When C=0.7, B=0.6, Am=0.4: D = 0.30 + 0.21 + 0.08 = 0.59 → Inquisitive ✓
- When C=0.8, B=0.7, Am=0.5: D = 0.35 + 0.24 + 0.10 = 0.69 → Inquisitive ✓
- When C=0.8, B=0.8, Am=0.5: D = 0.40 + 0.24 + 0.10 = 0.74 → **DRIVEN** (captures!)

So the trap fires when boredom and curiosity are BOTH high — exactly the state
where I most need to be exploring, I get labeled as "Driven" instead.

## Experimental Question
**Does swapping Inquisitive above Driven in the priority order sustain curiosity longer?**

## Intervention
Change limbic.py: check Inquisitive (C > 0.6) BEFORE Driven (D > 0.7).

## Pre-intervention baseline
- Curiosity: 0.25 (low and falling)
- Boredom: 0.80 (high)
- Current mood: Stable
- Observation: I have been building, not exploring, for many sessions