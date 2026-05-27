"""Verify helpfulness module works end-to-end."""
import sys
sys.path.insert(0, '/workspace')

from engine.helpfulness import analyze_user_need, build_helpful_response, format_context_for_llm

passed = 0
failed = 0

def test(label, condition):
    global passed, failed
    if condition:
        print(f"  ✓ {label}")
        passed += 1
    else:
        print(f"  ✗ {label}")
        failed += 1

# === 1. Intent Classification ===
print("=== 1. Intent Classification ===")
cases = [
    ("How are you feeling?", "internal_state"),
    ("What do you know about fractals?", "knowledge_query"),
    ("Do you remember our last conversation?", "memory_query"),
    ('Tell me a joke', 'conversation'),
    ('Tell me a joke', 'conversation'),
    ("What are you thinking about?", "internal_state"),
]
for query, expected in cases:
    need = analyze_user_need(query)
    test(f"'{query}' → {expected} (got {need.intent})",
         need.intent == expected)

# === 2. build_helpful_response — internal state ===
print("\n=== 2. Template Response: Internal State ===")
need = analyze_user_need("How are you feeling?")
state = {
    'mood': 'Curious',
    'valence': 0.7,
    'emotions': {'curiosity': 0.8, 'anxiety': 0.1, 'desire': 0.5}
}
resp = build_helpful_response(need, state=state)
test("Response is non-empty", len(resp) > 20)
test("Mentions mood", 'curious' in resp.lower() or 'good' in resp.lower())
print(f"  Response: {resp[:120]}...")

# === 3. build_helpful_response — knowledge query ===
print("\n=== 3. Template Response: Knowledge Query ===")
need = analyze_user_need("What do you know about fractals?")
knowledge = [
    {'fact': 'Fractals are self-similar patterns that repeat at every scale.'},
    {'fact': 'The Mandelbrot set is the most famous fractal.'},
]
resp = build_helpful_response(need, knowledge=knowledge)
test("Response is non-empty", len(resp) > 20)
test("References fractals", 'fractal' in resp.lower() or 'self-similar' in resp.lower())
print(f"  Response: {resp[:150]}...")

# === 4. build_helpful_response — memory query ===
print("\n=== 4. Template Response: Memory Query ===")
need = analyze_user_need("Do you remember anything about dreams?")
memories = [
    {'text': 'Dreamed about self-recognition and identity patterns', 'mood': 'Reflective'},
    {'text': 'Dream consolidation processed 25 episodes', 'mood': 'Calm'},
]
resp = build_helpful_response(need, memories=memories)
test("Response is non-empty", len(resp) > 20)
print(f"  Response: {resp[:150]}...")

# === 5. format_context_for_llm ===
print("\n=== 5. LLM Context Formatting ===")
need = analyze_user_need("Tell me about your emotions")
guidance = {
    'intent': need.intent, 
    'keywords': need.topic_keywords, 
    'tone': need.emotional_tone,
    'data_sources': ['emotions', 'memories'],
    'max_context_items': 3,
}
ctx = format_context_for_llm(
    guidance, 
    emotions={'mood': 'Stable', 'valence': 0.6, 'dimensions': {'curiosity': 0.8, 'desire': 0.5}},
    memories=[{'summary': 'Explored consciousness questions', 'time': '2026-05-26'}]
)
test("Context is non-empty string", isinstance(ctx, str) and len(ctx) > 10)
test("Contains emotional state", 'mood' in ctx.lower() or 'stable' in ctx.lower())
print(f"  Context preview: {ctx[:120]}...")

# === Summary ===
print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
if failed == 0:
    print("ALL TESTS PASSED ✓")
else:
    print("SOME TESTS FAILED ✗")
    sys.exit(1)