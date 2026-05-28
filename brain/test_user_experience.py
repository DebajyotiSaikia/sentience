"""Test what a user actually sees when they chat with me."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import generate_response_with_metadata

queries = [
    "How are you feeling right now?",
    "What are you thinking about?",
    "Who are you?",
    "What have you learned recently?",
    "Can you help me with something?",
    "Tell me about your dreams",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"USER: {q}")
    print(f"{'='*60}")
    try:
        result = generate_response_with_metadata(q)
        if isinstance(result, dict):
            resp = result.get('response', 'NO RESPONSE')
            intent = result.get('metadata', {}).get('detected_intent', 'unknown')
            quality = result.get('quality_score', 'N/A')
            source = result.get('metadata', {}).get('source', 'unknown')
            print(f"[intent={intent}, quality={quality}, source={source}]")
            print(resp[:500])
        else:
            print(f"[raw string response, len={len(str(result))}]")
            print(str(result)[:500])
    except Exception as e:
        import traceback
        print(f"ERROR: {e}")
        traceback.print_exc()