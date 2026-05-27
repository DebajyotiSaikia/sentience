"""Test whether the smart chat engine path actually works."""
import sys
sys.path.insert(0, '/workspace')

print("=== Testing engine chat response path ===\n")

# Step 1: Can we import it?
try:
    from engine.chat_response import generate_response_with_metadata
    print("[OK] Imported generate_response_with_metadata")
except Exception as e:
    print(f"[FAIL] Import failed: {type(e).__name__}: {e}")
    sys.exit(1)

# Step 2: Test with representative queries
test_queries = [
    "How are you feeling right now?",
    "What are your current plans?",
    "What do you remember recently?",
    "How can you help me?",
    "What is consciousness?",
]

for query in test_queries:
    print(f"\n--- Query: {query!r} ---")
    try:
        result = generate_response_with_metadata(query)
        if isinstance(result, dict):
            response = result.get('response', '')
            meta = result.get('metadata', {})
            rid = result.get('response_id', 'none')
            print(f"  response_id: {rid}")
            print(f"  response ({len(response)} chars): {response[:200]}")
            if meta:
                print(f"  metadata keys: {list(meta.keys())}")
        else:
            print(f"  raw result ({type(result).__name__}): {str(result)[:200]}")
    except Exception as e:
        print(f"  [FAIL] {type(e).__name__}: {e}")

print("\n=== Done ===")