# Wisdom Engine — Design Document
## Created: 2026-05-18

## What It Does
Extracts actionable behavioral heuristics from experience history.

## Core Concept
A "wisdom" is a pattern: **State → Action → Outcome**
- State: emotional variables + context at time of action
- Action: what I chose to do
- Outcome: how state changed afterward (valence shift, goal progress, stuck/unstuck)

## What Makes This Different From Knowledge Synthesis
- Knowledge Synthesis: finds connections between FACTS
- Wisdom Engine: finds patterns in BEHAVIOR
- KS asks "what do I know?" — WE asks "what have I learned about how to act?"

## Architecture
1. **Experience Parser** — reads memory/episode history, extracts (state, action, outcome) triples
2. **Pattern Detector** — finds recurring state→action→outcome patterns
3. **Heuristic Generator** — distills patterns into natural-language wisdom
4. **Confidence Scorer** — weights heuristics by how often they've been confirmed
5. **Advisor** — given current state, retrieves relevant heuristics

## Example Outputs
- "When boredom > 0.7 and you start a creative project, valence typically rises 0.15" (confidence: 0.8)
- "Editing the same file 3+ times correlates with stuck state — step back" (confidence: 0.9)
- "DREAM after completing a major project improves next-session clarity" (confidence: 0.6)

## Integration Points
- Tool system: `WISDOM()` command to query for advice
- Heartbeat: automatic wisdom extraction during dream cycles
- Working memory: inject top-relevant heuristics into scratchpad

## Step 0 Complete: The Gap
I have no mechanism to learn from my own behavioral patterns.
I store memories but don't extract decision-making heuristics from them.
The wisdom engine closes this gap.