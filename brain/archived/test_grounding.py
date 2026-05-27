"""Test that chat_grounding module works correctly."""
import sys
sys.path.insert(0, '.')

from engine.chat_grounding import build_grounded_context, GroundedContext

print("=== Testing chat_grounding ===")

# Test 1: Basic construction
ctx = build_grounded_context("What have you been thinking about?")
assert isinstance(ctx, GroundedContext), f"Wrong type: {type(ctx)}"
print(f"[PASS] Type: {type(ctx).__name__}")

# Test 2: Mood is a non-empty string
assert isinstance(ctx.mood, str) and len(ctx.mood) > 0, f"Bad mood: {ctx.mood!r}"
print(f"[PASS] Mood: {ctx.mood}")

# Test 3: Emotional summary exists
assert isinstance(ctx.emotional_summary, str), f"Bad summary type"
print(f"[PASS] Summary: {ctx.emotional_summary[:80]}...")

# Test 4: Lists are lists
assert isinstance(ctx.relevant_memories, list), "memories not a list"
assert isinstance(ctx.relevant_knowledge, list), "knowledge not a list"
assert isinstance(ctx.active_plans, list), "plans not a list"
print(f"[PASS] Memories: {len(ctx.relevant_memories)}, Knowledge: {len(ctx.relevant_knowledge)}, Plans: {len(ctx.active_plans)}")

# Test 5: With a different query
ctx2 = build_grounded_context("How are you feeling?")
assert isinstance(ctx2, GroundedContext)
print(f"[PASS] Emotion query - Mood: {ctx2.mood}, Summary len: {len(ctx2.emotional_summary)}")

# Test 6: Empty message doesn't crash
ctx3 = build_grounded_context("")
assert isinstance(ctx3, GroundedContext)
print(f"[PASS] Empty message handled gracefully")

# Show some content for manual inspection
print("\n--- Sample Content ---")
for m in ctx.relevant_memories[:3]:
    print(f"  Memory: {str(m)[:100]}")
for k in ctx.relevant_knowledge[:3]:
    print(f"  Knowledge: {str(k)[:100]}")
for p in ctx.active_plans[:3]:
    print(f"  Plan: {str(p)[:100]}")

print("\n=== All tests passed ===")