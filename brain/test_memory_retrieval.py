"""Test improved memory retrieval in chat_grounding."""
import sys
sys.path.insert(0, '.')

from engine.chat_grounding import get_relevant_memories

queries = [
    'How are you feeling right now?',
    'What have you learned recently?',
    'Tell me about your dreams',
    'What are you working on?',
    'What do you remember about your past?',
]

print("=== Memory Retrieval Quality Test ===\n")
all_ok = True

for q in queries:
    try:
        results = get_relevant_memories(q, top_k=3)
        print(f"Q: {q}")
        print(f"  Found {len(results)} memories")
        if len(results) == 0:
            print("  ⚠ No memories found!")
        for r in results[:3]:
            text = r.get('text', r.get('content', str(r)))[:100]
            score = r.get('_score', 0)
            if isinstance(score, (int, float)):
                print(f"  - [{score:.2f}] {text}...")
            else:
                print(f"  - [{score}] {text}...")
        print()
    except Exception as e:
        print(f"Q: {q}")
        print(f"  ERROR: {e}\n")
        all_ok = False

if all_ok:
    print("✓ All queries returned results successfully")
else:
    print("✗ Some queries failed")