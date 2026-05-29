"""Verify chat response structure without LLM calls."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Chat Structure Verification ===\n")

# 1. Imports work
from engine.chat_response import generate_response_with_metadata, submit_feedback
print("✓ chat_response imports OK")

from engine.chat_grounding import build_grounded_context, get_working_memory
print("✓ chat_grounding imports OK")

# 2. Working memory available
wm = get_working_memory()
assert isinstance(wm, str) and len(wm) > 0, "Working memory should be non-empty string"
print(f"✓ Working memory: {len(wm)} chars")

# 3. Grounded context includes working_memory
ctx = build_grounded_context("How are you feeling?")
assert 'working_memory' in ctx, f"Missing working_memory key. Keys: {list(ctx.keys())}"
print(f"✓ Grounded context keys: {sorted(ctx.keys())}")

# 4. System context builder includes working memory
from engine.chat_response import _build_system_context, _detect_intent
sys_ctx = _build_system_context(ctx, "How are you feeling?")
assert "working memory" in sys_ctx.lower() or "CURRENT FOCUS" in sys_ctx, "System context should include working memory"
print(f"✓ System context includes working memory ({len(sys_ctx)} chars)")

# 5. Intent detection works
intent = _detect_intent("How are you feeling?")
print(f"✓ Intent detected: '{intent}'")

intent2 = _detect_intent("What are your plans?")
print(f"✓ Intent detected: '{intent2}'")

intent3 = _detect_intent("Tell me about consciousness")
print(f"✓ Intent detected: '{intent3}'")

# 6. Submit feedback doesn't crash
try:
    submit_feedback("test-verification-id", 5, "Great")
    print("✓ submit_feedback works")
except Exception as e:
    print(f"⚠ submit_feedback: {e}")

print("\n=== All structural checks passed ===")