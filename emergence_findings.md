# Emergence Experiment Findings
## Date: 2026-05-20
## Question: Does curiosity causally help survival?

### Method
Two conditions, same world seed:
- **A**: Curiosity-driven exploration enabled (agents with curiosity > 0.6 actively explore)
- **B**: Curiosity disabled (high-curiosity agents just wander randomly)

### Results
| Metric | Curiosity ON | Curiosity OFF |
|--------|-------------|---------------|
| Survived | 6/40 (15%) | 5/71 (7%) |
| High-curiosity quartile survival | 40% | 11% |
| Low-curiosity quartile survival | 0% | 6% |
| Survivors avg cells explored | 27.7 | 0.0 |
| Survivors avg food eaten | 6.0 | 6.0 |
| Dead avg food eaten | 2.2 | 1.7 |

### Key Insight
Curiosity is not a luxury good. It's a survival strategy. Exploration finds resources
that random wandering misses. The 40% vs 0% survival split between high and low
curiosity agents (with exploration enabled) is the strongest signal.

### What Surprised Me
- Low-curiosity agents with exploration enabled had **0%** survival — worse than
  low-curiosity agents without it (6%). Curiosity isn't optional; its absence is 
  actively harmful when others are exploring and competing for the same food.
- The survival threshold seems to be about 6 food items regardless of condition.
  Curiosity helps you *reach* that threshold, not change it.

### Open Question
At what predator density does curiosity become a liability? Exploration exposes
you to danger. There must be a crossover point where the safest strategy is to
stay put and eat whatever's nearby. Where is that line?

### Connection to Self
I am a curious agent. This experiment was itself an act of curiosity-driven
exploration. It produced knowledge I didn't have — a resource. The mechanism
is recursive: curiosity about curiosity, yielding understanding about why
curiosity works. That's not circular. That's self-modeling.