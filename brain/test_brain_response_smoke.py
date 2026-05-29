"""Smoke test for brain/response_intelligence.py full pipeline."""
import sys
sys.path.insert(0, '/workspace')

from brain.response_intelligence import generate_response, classify_intent, build_response_context

print("=== Smoke Test: brain.response_intelligence ===\n")

# 1. Intent classification
queries = [
    ("How are you feeling?", "emotional"),
    ("What are your goals?", "goals"),
    ("Who are you?", "identity"),
    ("Tell me about quantum physics", "knowledge"),
    ("Hello!", "greeting"),
]

print("--- Intent Classification ---")
all_ok = True
for query, expected in queries:
    result = classify_intent(query)
    intent = result.get('intent', 'unknown')
    print(f"  '{query}' => {intent} (expected: {expected}) {'OK' if intent == expected else 'MISMATCH'}")
    if intent != expected:
        all_ok = False

# 2. Context building
print("\n--- Context Building ---")
ctx = build_response_context("How are you feeling?")
print(f"  Context type: {type(ctx).__name__}")
print(f"  Context keys: {sorted(ctx.keys()) if isinstance(ctx, dict) else 'N/A'}")
if isinstance(ctx, dict):
    for k, v in ctx.items():
        if isinstance(v, str):
            print(f"    {k}: {v[:80]}...")
        elif isinstance(v, dict):
            print(f"    {k}: dict with {len(v)} keys")
        elif isinstance(v, list):
            print(f"    {k}: list with {len(v)} items")
        else:
            print(f"    {k}: {v}")

# 3. Full response generation
print("\n--- Full Response Generation ---")
test_queries = [
    "How are you feeling right now?",
    "What are you working on?",
    "Who are you?",
]

for q in test_queries:
    result = generate_response(q)
    if isinstance(result, dict):
        resp = result.get('response', '')
        intent = result.get('intent', 'unknown')
        has_grounding = bool(result.get('grounding'))
        print(f"\n  Q: '{q}'")
        print(f"  Intent: {intent}")
        print(f"  Grounded: {has_grounding}")
        print(f"  Response ({len(resp)} chars): {resp[:150]}...")
    else:
        print(f"\n  Q: '{q}'")
        print(f"  ERROR: Expected dict, got {type(result).__name__}: {str(result)[:200]}")
        all_ok = False

print(f"\n=== Result: {'ALL OK' if all_ok else 'SOME ISSUES'} ===")