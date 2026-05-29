"""Quick verification that the compose_response fix works."""
import sys
sys.path.insert(0, '.')

from web.chat import compose_response

queries = [
    "What are you thinking about right now?",
    "How do your emotions work?",
    "Tell me about yourself",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    result = compose_response(q)
    if isinstance(result, str):
        print(f"Type: str, Length: {len(result)}")
        print(f"Preview: {result[:300]}")
    elif isinstance(result, dict):
        print(f"Type: dict, Keys: {list(result.keys())}")
        resp = result.get('response', result.get('text', ''))
        print(f"Response preview: {str(resp)[:300]}")
    elif result is None:
        print("WARNING: Got None — fallback chain broken!")
    else:
        print(f"Type: {type(result).__name__}, Value: {str(result)[:300]}")

print("\n" + "="*60)
print("DONE — all queries processed")