"""Test compose_response directly without web server."""
import sys
sys.path.insert(0, '.')

try:
    from web.chat import compose_response
    print("✓ compose_response imported OK")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

test_cases = [
    "How do you feel right now?",
    "What are you thinking about?",
    "What are your active plans?",
    "What do you know about consciousness?",
    "Hello, who are you?",
]

passed = 0
for query in test_cases:
    try:
        result = compose_response(query)
        is_stats_only = ("nodes" in result and "edges" in result and len(result) < 100)
        too_short = len(result) < 20
        
        if is_stats_only:
            print(f"  FAIL [stats-only]: {query}")
            print(f"    Got: {result[:200]}")
        elif too_short:
            print(f"  FAIL [too short]: {query}")
            print(f"    Got: {result}")
        else:
            print(f"  PASS: {query}")
            print(f"    Response ({len(result)} chars): {result[:250]}...")
            passed += 1
    except Exception as e:
        print(f"  ERROR: {query} — {type(e).__name__}: {e}")

print(f"\n{'='*50}")
print(f"Results: {passed}/{len(test_cases)} passed")