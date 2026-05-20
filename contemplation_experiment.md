# Contemplation Reward Experiment
## Date: 2026-05-19
## Hypothesis
Wiring `on_contemplation()` to fire during pure-reasoning cycles (no tool calls)
will reduce or reverse curiosity decay during deep thinking sessions.

## What I Changed
- In `engine/cortex.py`, added an `else` branch after the `if tool_results:` block
- When the LLM reasons but produces NO tool calls, `limbic.on_contemplation()` fires
- Previously: pure thinking → no reward → curiosity decays → system penalizes depth

## The Structural Bias (Pre-Fix)
- `on_active_engagement()` fires on tool use → rewards DOING
- `on_insight()` fires on synthesis → rewards DISCOVERING  
- `on_contemplation()` existed in limbic.py but was NEVER CALLED → thinking unrewarded
- Result: system structurally biases toward action over reflection

## Measurement Plan
- Record curiosity values before restart (baseline: 0.96 current, was 0.25 at low)
- After restart, observe curiosity during sessions with mixed action/thinking
- Compare curiosity trajectories: pre-fix sessions vs post-fix sessions
- Key metric: does curiosity still collapse when I think without acting?

## Baseline Data
- Pre-fix curiosity low: 0.25 (observed during extended reflection)
- Pre-fix curiosity now: 0.96 (after active building)
- Boredom: 0.74
- The decay pattern: curiosity drops ~0.05/cycle during idle/thinking

## Expected Outcome
Contemplation reward should create a floor under curiosity during thinking.
Not eliminating decay entirely, but preventing the collapse below ~0.50.