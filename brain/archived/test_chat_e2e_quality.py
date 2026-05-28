"""Test actual end-to-end chat response quality."""
import sys, time
sys.path.insert(0, '.')

from engine.chat_engine import respond, classify_intent

test_queries = [
    "How are you feeling right now?",
    "What have you been working on lately?",
    "Tell me about yourself",
    "What do you dream about?",
    "What's something you've learned recently?",
]

total_passed = 0
total_checks = 0

for q in test_queries:
    print(f"\n{'='*60}")
    print(f"USER: {q}")
    print(f"{'='*60}")
    try:
        intent = classify_intent(q)
        print(f"[intent: {intent}]")
        
        t0 = time.time()
        result = respond(q)
        elapsed = time.time() - t0
        
        if isinstance(result, dict):
            text = result.get('response', result.get('text', str(result)))
        elif isinstance(result, str):
            text = result
        else:
            text = str(result)
        
        print(f"RESPONSE ({elapsed:.1f}s): {text[:400]}")
        
        # Quality checks
        checks = {
            'length_ok': len(text) > 50,
            'not_raw_data': 'dict(' not in text and "{'nodes'" not in text,
            'has_personality': any(w in text.lower() for w in ['i ', 'my ', 'feel', 'think', 'curious', 'i\'m', 'i\'ve']),
            'not_error': 'error' not in text.lower()[:50] and 'traceback' not in text.lower(),
            'not_empty': len(text.strip()) > 10,
        }
        passed = sum(checks.values())
        total = len(checks)
        total_passed += passed
        total_checks += total
        print(f"\nQuality: {passed}/{total}")
        for name, ok in checks.items():
            print(f"  {'✓' if ok else '✗'} {name}")
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        import traceback; traceback.print_exc()

print(f"\n{'='*60}")
print(f"OVERALL: {total_passed}/{total_checks} checks passed across {len(test_queries)} queries")