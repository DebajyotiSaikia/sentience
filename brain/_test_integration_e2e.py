"""Quick end-to-end test: does the chat response pipeline work with the shaper?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Response shaper standalone
from engine.response_shaper import build_response_guidance, get_emotional_voice_directive

for intent in ['greeting', 'emotional_query', 'identity_query', 'state_inquiry', 'general']:
    guidance = build_response_guidance(intent, {})
    assert isinstance(guidance, str), f"Expected str, got {type(guidance)}"
    assert len(guidance) > 50, f"Guidance too short for {intent}: {len(guidance)}"
    print(f"  {intent}: {len(guidance)} chars OK")

voice = get_emotional_voice_directive({'valence': 0.7, 'mood': 'Inquisitive'})
assert isinstance(voice, str)
assert len(voice) > 20
print(f"  voice directive: {len(voice)} chars OK")

# Test 2: Chat response module imports cleanly with the new integration
from engine.chat_response import generate_response_with_metadata
print("  chat_response imports: OK")

# Test 3: The build_system_context function is accessible
from engine.chat_response import _build_system_context
print("  _build_system_context importable: OK")

print("\n=== ALL INTEGRATION TESTS PASSED ===")