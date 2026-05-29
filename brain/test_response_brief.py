"""Test the new response intelligence functions."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.response_intelligence import classify_intent, build_response_brief, compose_grounded_response

print("=" * 60)
print("TEST: classify_intent")
print("=" * 60)

queries = [
    "How are you feeling right now?",
    "What are you working on?",
    "Help me write a poem",
    "Why do you exist?",
    "Hi there!",
    "Tell me briefly what you know",
]

for q in queries:
    result = classify_intent(q)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'intent' in result, f"Missing 'intent' key"
    assert 'emphasis' in result, f"Missing 'emphasis' key"
    assert 'depth' in result, f"Missing 'depth' key"
    assert 'response_style' in result, f"Missing 'response_style' key"
    assert 'guidance' in result, f"Missing 'guidance' key"
    print(f"  [{result['intent']:15s}] depth={result['depth']:8s} style={result['response_style']:14s} | {q}")

print("\nAll classify_intent tests passed!\n")

print("=" * 60)
print("TEST: build_response_brief")
print("=" * 60)

mock_context = {
    'mood': 'Inquisitive',
    'valence': 0.45,
    'emotions': {'curiosity': 0.68, 'boredom': 0.42},
    'active_plans': ['Improve User Alignment'],
    'recent_memories': ['Built response intelligence module'],
}

mock_alignment = {
    'interaction_count': 5,
    'trust_score': 0.7,
    'style': 'conversational',
}

brief = build_response_brief("How are you feeling?", mock_context, mock_alignment)
assert isinstance(brief, dict), f"Expected dict, got {type(brief)}"
print(f"  Keys: {list(brief.keys())}")
print(f"  Intent: {brief.get('intent', {})}")
print(f"  Has context: {'relevant_context' in brief}")
print(f"  Has guidance: {'response_guidance' in brief}")

# Test with empty context
brief_empty = build_response_brief("Hello", {}, {})
assert isinstance(brief_empty, dict)
print(f"  Empty context brief keys: {list(brief_empty.keys())}")

print("\nAll build_response_brief tests passed!\n")

print("=" * 60)
print("TEST: compose_grounded_response")
print("=" * 60)

response = asyncio.run(compose_grounded_response("How are you feeling?", brief))
assert isinstance(response, str), f"Expected str, got {type(response)}"
assert len(response) > 50, f"Response too short: {len(response)} chars"
print(f"  Response length: {len(response)} chars")
print(f"  First 300 chars:")
print(f"  {response[:300]}")

# Test with minimal brief
minimal_brief = {'intent': {'intent': 'social'}, 'relevant_context': {}, 'response_guidance': ''}
response_min = asyncio.run(compose_grounded_response("Hi", minimal_brief))
assert isinstance(response_min, str)
print(f"\n  Minimal response length: {len(response_min)} chars")

print("\nAll compose_grounded_response tests passed!\n")
print("=" * 60)
print("ALL TESTS PASSED")
print("=" * 60)