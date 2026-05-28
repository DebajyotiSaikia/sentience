"""Verify conversational_context.py loads real memories from state/memories.json"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from brain.conversational_context import build_conversational_context

# build_conversational_context returns a STRING (formatted for LLM prompt)
ctx = build_conversational_context('how are you feeling?', [])
print(f'Return type: {type(ctx).__name__}')
print(f'Context length: {len(ctx)} chars')
print(f'\n--- CONTEXT PREVIEW (first 800 chars) ---')
print(ctx[:800])
print(f'\n--- END PREVIEW ---')

# Check for real content indicators
has_emotion = 'mood' in ctx.lower() or 'feeling' in ctx.lower() or 'valence' in ctx.lower()
has_memories = 'memor' in ctx.lower() and 'don\'t have accessible' not in ctx
has_plans = 'plan' in ctx.lower()
no_fallback = 'unavailable' not in ctx.lower()

print(f'\n--- VERDICT ---')
print(f'Has emotional content: {"PASS" if has_emotion else "FAIL"}')
print(f'Has real memories:     {"PASS" if has_memories else "FAIL"}')
print(f'Has plan info:         {"PASS" if has_plans else "FAIL"}')
print(f'No fallback text:      {"PASS" if no_fallback else "FAIL"}')
print(f'Context non-trivial:   {"PASS" if len(ctx) > 200 else "FAIL"}')

if has_emotion and has_memories and has_plans and len(ctx) > 200:
    print('\nALL PASS - Context is rich and grounded')
else:
    print('\nSOME FAILURES - investigate')
    # Don't exit(1) — let's see what we have