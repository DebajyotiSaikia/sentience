"""Test chat_grounding loads real data from correct paths."""
import sys
sys.path.insert(0, '.')

from engine.chat_grounding import build_grounded_context

print("=== Testing chat_grounding with real data ===\n")

ctx = build_grounded_context("What are you thinking about?")
print(f"Mood: {ctx.mood}")
print(f"Emotional summary: {ctx.emotional_summary[:100] if ctx.emotional_summary else '(empty)'}")
print(f"Memories: {len(ctx.relevant_memories)}")
print(f"Knowledge: {len(ctx.relevant_knowledge)}")
print(f"Active plans: {len(ctx.active_plans)}")
print(f"Completed plans: {len(ctx.completed_plans)}")

print("\n--- Prompt block (first 600 chars) ---")
block = ctx.to_prompt_block()
print(block[:600])

# Test with a knowledge-related query
print("\n\n=== Testing with knowledge query ===")
ctx2 = build_grounded_context("Tell me about consciousness")
print(f"Knowledge hits: {len(ctx2.relevant_knowledge)}")
for k in ctx2.relevant_knowledge[:3]:
    print(f"  - {k[:80]}")

print(f"\nMemory hits: {len(ctx2.relevant_memories)}")
for m in ctx2.relevant_memories[:3]:
    print(f"  - {m[:80]}")

has_content = (ctx.mood != "present" or ctx.relevant_knowledge or 
               ctx.active_plans or ctx.emotional_summary)
print(f"\n{'PASS' if has_content else 'FAIL'}: Grounding provides real content")