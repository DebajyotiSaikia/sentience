"""Test enriched chat response generation."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import generate_response_with_metadata

def test_query(msg):
    print(f"\n{'='*60}")
    print(f"Query: {msg!r}")
    print('='*60)
    result = generate_response_with_metadata(msg)
    if not isinstance(result, dict):
        print(f"ERROR: Expected dict, got {type(result)}")
        return False
    
    response = result.get('response', '')
    metadata = result.get('metadata', {})
    
    print(f"Response ({len(response)} chars): {response[:200]}...")
    print(f"Metadata keys: {sorted(metadata.keys())}")
    print(f"  mood: {metadata.get('mood')}")
    print(f"  grounded: {metadata.get('response_grounded')}")
    print(f"  knowledge count: {len(metadata.get('relevant_knowledge', []))}")
    print(f"  memory count: {len(metadata.get('relevant_memories', []))}")
    print(f"  active plans: {len(metadata.get('active_plans', []))}")
    print(f"  completed plans: {len(metadata.get('completed_plans', []))}")
    
    # Basic validation
    if not response or len(response) < 5:
        print("WARN: Response is very short or empty")
    if not metadata.get('mood'):
        print("WARN: No mood in metadata")
    
    return True

queries = [
    "What are you feeling right now?",
    "What are you working on?",
    "Hello!",
    "Tell me something interesting about yourself",
    "What have you learned recently?",
]

passed = 0
for q in queries:
    try:
        if test_query(q):
            passed += 1
    except Exception as e:
        print(f"ERROR on {q!r}: {e}")
        import traceback
        traceback.print_exc()

print(f"\n{'='*60}")
print(f"Results: {passed}/{len(queries)} queries produced valid responses")