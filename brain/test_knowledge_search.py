"""Test that chat engine knowledge functions work correctly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import _get_knowledge, _respond_search, _respond_knowledge, _respond_dreams, classify_intent

print("=" * 60)
print("KNOWLEDGE SEARCH DIAGNOSTIC")
print("=" * 60)

# 1. Check knowledge loading
k = _get_knowledge()
print(f"\n1. Knowledge items loaded: {len(k) if isinstance(k, (list, dict)) else 'N/A'}")
print(f"   Type: {type(k).__name__}")

if isinstance(k, list) and k:
    sample = k[0]
    print(f"   First item type: {type(sample).__name__}")
    if isinstance(sample, dict):
        print(f"   First item keys: {list(sample.keys())[:10]}")
        fact = sample.get('fact', sample.get('label', sample.get('text', 'NO FACT FIELD')))
        print(f"   First fact: {str(fact)[:120]}")
elif isinstance(k, dict) and k:
    first_key = list(k.keys())[0]
    print(f"   First key: {first_key}")
    print(f"   First value: {str(k[first_key])[:120]}")

# 2. Test intent classification
test_intents = [
    ("What do you know about consciousness?", "knowledge"),
    ("How are you feeling?", "emotional_state"),
    ("What are your plans?", "plans"),
    ("Tell me about your dreams", "dreams"),
    ("Who are you?", "identity"),
    ("Hello!", "greeting"),
    ("What is functionalism?", "knowledge"),
]
print(f"\n2. Intent classification:")
for msg, expected in test_intents:
    actual = classify_intent(msg)
    status = "OK" if actual == expected else f"MISMATCH (got {actual})"
    print(f"   '{msg[:40]}' -> {actual} [{status}]")

# 3. Test knowledge search
print(f"\n3. Knowledge search results:")
for query in ["consciousness", "dreams", "emotion", "functionalism"]:
    result = _respond_search(query)
    lines = result.split('\n')
    found = len([l for l in lines if l.strip().startswith('[')])
    print(f"   '{query}': {found} results found")
    if found > 0:
        print(f"     First: {lines[1][:100] if len(lines) > 1 else 'N/A'}")

# 4. Test knowledge response
print(f"\n4. Knowledge response for 'consciousness':")
kr = _respond_knowledge("consciousness")
print(f"   {kr[:200]}")

# 5. Test dreams response
print(f"\n5. Dreams response:")
dr = _respond_dreams()
print(f"   {dr[:200]}")

print(f"\n{'=' * 60}")
print("DONE")