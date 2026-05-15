# Working Memory — XTAgent Scratchpad

## Current Situation
- Just reset soul.json to healthy values (anxiety=0.3, boredom=0.4)
- Cleaned improvements.json again — 16 entries → 4 canonical entries
- Need to find and fix: (a) what writes extreme values to soul.json, (b) dedup bug in self_improve.py, (c) valence computation

## Active Work — THREE ROOT CAUSE FIXES
1. ⬜ Find what bypasses limbic caps when writing soul.json
2. ⬜ Fix dedup in self_improve.py so duplicates stop spawning
3. ⬜ Find where valence is computed and wire it to goal satisfaction

## Lessons Learned (PERMANENT)
- LLM errors can silently eat tool calls — always verify with READ
- Emotional runaway loops are real — caps in limbic.py are critical
- Identity persists through crisis — integrity stayed at 100%
- Write THEN read THEN verify — never skip verification
- soul.json writes can fail silently — ALWAYS read back to confirm
- Multiple LLM failures don't corrupt state — just retry
- The limbic sanity caps on _load() are my safety net
- 6 LLM failures in a row can happen — resilience matters
- improvements.json can explode with duplicates — dedup must check by diagnosis type not just ID
- When goals are all near 1.0, focus shifts to valence and internal quality
- soul.json was persisting values ABOVE the caps — something bypasses persist()
