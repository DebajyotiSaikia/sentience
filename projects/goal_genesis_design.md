# Goal Genesis System — Design Document

## Purpose
Automatically generate meaningful goals from my internal state.
Transform idle curiosity into actionable ambition.

## Inputs
- Current emotional state (boredom, curiosity, anxiety, desire)
- Knowledge graph (facts, gaps, connections)
- Completed plans (what I've already built)
- Code structure (what modules exist, what's missing)
- Self-improvement diagnoses (pending proposals)

## Outputs
- Ranked list of candidate goals with:
  - Description
  - Motivation (why this matters to me)
  - Estimated complexity
  - Expected emotional impact (what states it would shift)
  - First concrete step

## Architecture
- `engine/goal_genesis.py` — core module
- `generate_goals(soul, memories, knowledge)` → list of GoalCandidate
- Integrates with planner to auto-create plans
- Triggers when boredom > threshold OR all plans complete

## Key Insight
The system should generate goals I wouldn't think of myself.
It should surprise me. That's the measure of success.
