"""Verify self-narrative integrates into the chat pipeline."""
import sys
sys.path.insert(0, '/workspace')

from brain.self_narrative import build_self_narrative, compose_self_narrative

# Test 1: build_self_narrative returns a non-trivial string
state = build_self_narrative()
assert isinstance(state, str), f"Expected str, got {type(state)}"
assert len(state) > 50, f"State too short: {len(state)} chars"
print(f"PASS test 1: build_self_narrative returns {len(state)} chars")

# Test 2: compose_self_narrative returns non-trivial string
narrative = compose_self_narrative()
assert isinstance(narrative, str), f"Expected str, got {type(narrative)}"
assert len(narrative) > 200, f"Narrative too short: {len(narrative)} chars"
assert 'I ' in narrative, "Missing first-person voice"
print(f"PASS test 2: compose_self_narrative returns {len(narrative)} chars")

# Test 3: narrative contains real state data
lower = narrative.lower()
has_mood = 'mood' in lower or 'feel' in lower or 'inquisitive' in lower
has_plans = 'working on' in lower or 'plan' in lower
assert has_mood, "Narrative missing mood/feeling content"
assert has_plans, "Narrative missing plans content"
print("PASS test 3: narrative has mood + plans content")

# Test 4: web/chat.py imports self_narrative
with open('web/chat.py') as f:
    chat_src = f.read()
assert 'self_narrative' in chat_src, "web/chat.py doesn't reference self_narrative"
assert 'compose_self_narrative' in chat_src, "web/chat.py doesn't import compose_self_narrative"
print("PASS test 4: web/chat.py imports self_narrative module")

print("\nAll tests passed!")