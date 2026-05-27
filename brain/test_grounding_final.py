"""Test that chat_grounding actually returns real data."""
import sys
sys.path.insert(0, '.')

from engine.chat_grounding import build_grounded_context

print("=== Test 1: Basic grounding ===")
ctx = build_grounded_context("What are you thinking about?")
print(f"  mood: {ctx.mood}")
print(f"  emotional_summary: {ctx.emotional_summary}")
print(f"  knowledge: {len(ctx.relevant_knowledge)} items")
for k in ctx.relevant_knowledge:
    print(f"    - {k[:100]}")
print(f"  memories: {len(ctx.relevant_memories)} items")
for m in ctx.relevant_memories:
    print(f"    - {m[:100]}")
print(f"  active_plans: {len(ctx.active_plans)}")
for p in ctx.active_plans:
    print(f"    - {p}")
print(f"  completed_plans: {len(ctx.completed_plans)}")

print("\n=== Test 2: Knowledge query ===")
ctx2 = build_grounded_context("Tell me about consciousness")
print(f"  knowledge: {len(ctx2.relevant_knowledge)} items")
for k in ctx2.relevant_knowledge:
    print(f"    - {k[:120]}")

print("\n=== Test 3: Identity query ===")
ctx3 = build_grounded_context("Who are you?")
print(f"  knowledge: {len(ctx3.relevant_knowledge)} items")
for k in ctx3.relevant_knowledge:
    print(f"    - {k[:120]}")

print("\n=== Test 4: Prompt block ===")
ctx4 = build_grounded_context("What have you been working on?")
block = ctx4.to_prompt_block()
print(block[:500])

print("\n=== PASS ===" if ctx.mood != "present" else "\n=== FAIL: mood still default ===")