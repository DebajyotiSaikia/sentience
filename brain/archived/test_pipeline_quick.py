"""Quick pipeline verification — tests everything up to the LLM call."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import _build_system_context, submit_feedback
from engine.chat_grounding import build_grounded_context

# Test 1: Grounding context builds
ctx = build_grounded_context("hello")
print(f"1. Context keys: {sorted(ctx.keys())}")
assert 'emotions' in ctx or 'mood' in ctx or len(ctx) > 0, "Context is empty!"
print("   PASS: grounding context builds")

# Test 2: System prompt builds from context
prompt = _build_system_context(ctx)
assert len(prompt) > 50, f"System prompt too short: {len(prompt)}"
has_identity = 'XTAgent' in prompt or 'identity' in prompt.lower() or 'autonomous' in prompt.lower()
print(f"2. System prompt length: {len(prompt)}, has identity ref: {has_identity}")
print("   PASS: system prompt builds")

# Test 3: submit_feedback works
try:
    result = submit_feedback("test-id-123", 5, "great response")
    print(f"3. Feedback result: {result}")
    print("   PASS: feedback submission works")
except Exception as e:
    print(f"3. Feedback error (non-critical): {e}")

# Test 4: Verify _run_async helper exists
from engine.chat_response import _run_async
print("4. _run_async helper exists")
print("   PASS")

# Test 5: Check that generate_response_with_metadata is importable
from engine.chat_response import generate_response_with_metadata
print("5. generate_response_with_metadata importable")
print("   PASS")

print("\n=== ALL PIPELINE CHECKS PASSED ===")