"""Quick end-to-end test of personality_respond."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.chat_personality import build_personality_context, personality_respond

# Test 1: build_personality_context
print("=== Test 1: build_personality_context ===")
ctx = build_personality_context("How are you feeling?")
print(f"Type: {type(ctx)}")
print(f"Keys: {list(ctx.keys()) if isinstance(ctx, dict) else 'not a dict'}")
for k, v in ctx.items():
    preview = str(v)[:100] if v else "(empty)"
    print(f"  {k}: {preview}")

# Test 2: personality_respond
print("\n=== Test 2: personality_respond ===")
response = personality_respond("How are you feeling?")
print(f"Response type: {type(response)}")
print(f"Response length: {len(response)}")
print(f"Response:\n{response[:500]}")

# Test 3: different query
print("\n=== Test 3: different query ===")
response2 = personality_respond("What are your goals?")
print(f"Response:\n{response2[:500]}")

print("\n✅ All tests passed!")