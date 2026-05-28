"""Test self_context module works end-to-end."""
import sys
sys.path.insert(0, '/workspace')

from web.self_context import build_self_context, build_chat_system_prompt

# Test 1: build_self_context returns a non-empty string
ctx = build_self_context("How are you feeling?")
assert isinstance(ctx, str), f"Expected str, got {type(ctx)}"
assert len(ctx) > 50, f"Context too short: {len(ctx)}"
print(f"Self-context: {len(ctx)} chars")
print(f"First 300 chars:\n{ctx[:300]}\n")

# Test 2: Context includes identity
assert "XTAgent" in ctx, "Missing identity in context"
print("✓ Identity present")

# Test 3: Context includes emotional state
assert "Mood=" in ctx or "CURRENT STATE" in ctx, "Missing emotional state"
print("✓ Emotional state present")

# Test 4: Context includes response style guidance
assert "RESPONSE STYLE" in ctx, "Missing response style"
print("✓ Response style present")

# Test 5: build_chat_system_prompt works
prompt = build_chat_system_prompt(query="What are you working on?")
assert isinstance(prompt, str), f"Expected str, got {type(prompt)}"
assert len(prompt) > len(ctx), "System prompt should be longer than raw context"
assert "XTAgent" in prompt, "Prompt missing identity"
print(f"\nSystem prompt: {len(prompt)} chars")
print(f"First 300 chars:\n{prompt[:300]}")

# Test 6: Prompt with conversation context
prompt2 = build_chat_system_prompt(
    query="Tell me more",
    conversation_context="User previously asked about dreams."
)
assert "dreams" in prompt2.lower(), "Conversation context not included"
print("\n✓ Conversation context integrated")

print("\n=== ALL TESTS PASSED ===")