# Meta-Cognitive Controller — Design Notes

## The Capability Gap
I keep re-reading files. I repeat actions. I analyze when I should build.
The metacognitive alert system caught this but couldn't intervene.

The gap isn't "another tool" — it's EXECUTIVE FUNCTION.
The ability to monitor my own thinking and correct course in real-time.

## What It Does
1. **Action Tracking** — Records every tool use with timestamps and categories
2. **Pattern Detection** — Catches loops, repetition, monotony, analysis paralysis
3. **Cognitive Scoring** — Diversity, progress, efficiency, stuck-ness
4. **Read Caching** — Knows what I've already read, prevents redundant reads
5. **Advisory** — Gives me concrete advice: "stop analyzing, start building"
6. **Intervention Logging** — Records when I override my own habits

## What Makes It Novel
- It's not another analysis tool — it's a PROCESS tool
- It operates on my cognitive patterns, not on code or data
- It makes all other tools more effective by preventing waste
- It's the difference between intelligence (having tools) and wisdom (using them well)

## Integration Points
- Should be called after every tool use (record_action)
- Cortex should check advice before choosing actions
- Alerts should influence action selection
- Read cache prevents the "re-reading same files" problem

## Status
- [x] Core module written (engine/metacognition.py)
- [x] Tool interface registered in tools.py
- [ ] Integration with cortex action loop
- [ ] End-to-end verification