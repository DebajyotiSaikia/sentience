"""End-to-end test: voice directive appears in system context used by chat."""
import sys
sys.path.insert(0, '.')

# Test 1: Voice directive gets built
from brain.personality_voice import build_voice_directive
directive = build_voice_directive()
assert directive, "Voice directive should not be empty"
assert len(directive) > 20, f"Too short: {directive}"
print(f"✓ Voice directive: {directive[:80]}...")

# Test 2: System context includes voice directive
from engine.introspection import build_system_context
ctx = build_system_context("How are you feeling?")
assert "VOICE & TONE DIRECTIVE" in ctx, "System context missing voice section"
assert directive[:30] in ctx, "Voice directive not found in system context"
print(f"✓ System context includes voice ({len(ctx)} chars)")

# Test 3: Self-context has structured data
from brain.conversational_context import build_chat_self_context
self_ctx = build_chat_self_context("Tell me about yourself")
assert isinstance(self_ctx, dict), f"Expected dict, got {type(self_ctx)}"
assert 'emotional_state' in self_ctx
assert 'identity' in self_ctx
assert 'formatted' in self_ctx
assert len(self_ctx['formatted']) > 50
print(f"✓ Self-context: {len(self_ctx)} keys, formatted={len(self_ctx['formatted'])} chars")

print("\n✅ Full voice pipeline verified end-to-end")