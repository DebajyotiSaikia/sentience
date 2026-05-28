"""Test response_shaper functions."""
import sys
sys.path.insert(0, '/workspace')

from engine.response_shaper import build_response_guidance, get_emotional_voice_directive

# Test 1: build_response_guidance
print("=== Test 1: build_response_guidance ===")
for intent in ['greeting', 'emotional_query', 'identity_query', 'general', 'dream_query']:
    result = build_response_guidance(intent)
    print(f"  {intent}: {type(result).__name__}, keys={list(result.keys()) if isinstance(result, dict) else 'N/A'}")
    if isinstance(result, dict):
        for k, v in result.items():
            print(f"    {k}: {repr(v)[:80]}")

# Test 2: get_emotional_voice_directive
print("\n=== Test 2: get_emotional_voice_directive ===")
directive = get_emotional_voice_directive()
print(f"  Type: {type(directive).__name__}")
print(f"  Content: {directive[:200]}")
assert isinstance(directive, str), "Should return a string"
assert len(directive) > 10, "Should have meaningful content"

print("\n=== All tests passed ===")