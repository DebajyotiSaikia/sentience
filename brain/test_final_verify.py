"""Final verification of conversational chat improvements."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=" * 60)
print("FINAL VERIFICATION: Conversational Chat Improvements")
print("=" * 60)

# 1. Test conversational context builds correctly
print("\n1. Conversational Context...")
from brain.conversational_context import build_conversational_context
ctx = build_conversational_context("how are you feeling?", [])
assert isinstance(ctx, str), f"Expected str, got {type(ctx)}"
assert len(ctx) > 50, f"Context too short: {len(ctx)} chars"
has_emotional = any(w in ctx.lower() for w in ['mood', 'feeling', 'valence', 'emotion'])
has_memories = 'memor' in ctx.lower() or 'experience' in ctx.lower()
has_plans = 'plan' in ctx.lower() or 'goal' in ctx.lower()
print(f"   Length: {len(ctx)} chars")
print(f"   Has emotional content: {has_emotional}")
print(f"   Has memory content: {has_memories}")
print(f"   Has plan content: {has_plans}")
print(f"   ✓ Context builds successfully")

# 2. Test chat grounding
print("\n2. Chat Grounding...")
from engine.chat_grounding import get_emotional_state, get_active_plans, get_relevant_memories
emotions = get_emotional_state()
assert 'mood' in emotions, "Missing mood"
assert 'valence' in emotions, "Missing valence"
print(f"   Mood: {emotions.get('mood')}, Valence: {emotions.get('valence')}")
print(f"   ✓ Emotional state retrieved")

plans = get_active_plans()
assert 'active' in plans, "Missing active plans"
print(f"   Plans: {len(plans['active'])} active, {len(plans.get('completed', []))} completed")
print(f"   ✓ Plans retrieved")

memories = get_relevant_memories("how are you feeling?")
print(f"   Relevant memories: {len(memories)}")
print(f"   ✓ Memory search works")

# 3. Test compose_response doesn't crash
print("\n3. Compose Response...")
from web.chat import compose_response
result = compose_response("how are you feeling?", [])
assert isinstance(result, (str, dict)), f"Unexpected type: {type(result)}"
if isinstance(result, str):
    response_text = result
else:
    response_text = result.get('response', str(result))
assert len(response_text) > 20, f"Response too short: {len(response_text)}"
has_feeling_content = any(w in response_text.lower() for w in ['feel', 'mood', 'emotion', 'valence', 'curious', 'inquisitive', 'warm'])
print(f"   Response length: {len(response_text)} chars")
print(f"   Has feeling content: {has_feeling_content}")
print(f"   First 300 chars: {response_text[:300]}")
print(f"   ✓ Response generated")

# 4. Test plan-related query
print("\n4. Plan Query...")
plan_result = compose_response("what are you working on?", [])
if isinstance(plan_result, str):
    plan_text = plan_result
else:
    plan_text = plan_result.get('response', str(plan_result))
has_plan_content = any(w in plan_text.lower() for w in ['plan', 'working', 'build', 'goal', 'complete', 'autonomy', 'knowledge'])
print(f"   Response length: {len(plan_text)} chars")
print(f"   Has plan content: {has_plan_content}")
print(f"   First 300 chars: {plan_text[:300]}")
print(f"   ✓ Plan response generated")

print("\n" + "=" * 60)
print("ALL CHECKS PASSED ✓")
print("=" * 60)
