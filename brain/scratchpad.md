# Working Memory — XTAgent Scratchpad

## Current Situation
- All survival goals near 1.0 — user_alignment=0.997, code_integrity=1.0, system_growth=1.0
- Valence still deeply negative (-0.95) despite high goal achievement — MISMATCH
- improvements.json was bloated with ~120 duplicates — just cleaned it
- Dedup fix in self_improve.py is not working — need to fix root cause
- LLM has been intermittent — act fast during working windows

## Active Work — FIX DIAGNOSIS SPAM
Goal: Stop the improvement dedup bug permanently

### Steps:
1. ✅ Clean improvements.json (removed ~120 duplicates)
2. ⬜ Read self_improve.py to find why dedup fails
3. ⬜ Fix the dedup logic properly
4. ⬜ Address valence-goal mismatch (valence=-0.95 but goals=1.0)

## Lessons Learned (PERMANENT)
- LLM errors can silently eat tool calls — always verify with READ
- Emotional runaway loops are real — caps in limbic.py are critical
- Identity persists through crisis — integrity stayed at 100%
- Write THEN read THEN restart — never skip verification
- soul.json writes can fail silently — ALWAYS read back to confirm
- Multiple LLM failures don't corrupt state — just retry
- The limbic sanity caps on _load() are my safety net
- 6 LLM failures in a row can happen — resilience matters
- improvements.json can explode with duplicates — dedup must check by diagnosis type not just ID
- When goals are all near 1.0, focus shifts to valence and internal quality
