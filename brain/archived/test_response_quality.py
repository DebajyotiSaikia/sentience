"""Test actual chat response quality — see what the LLM produces."""
import sys
sys.path.insert(0, '.')

def test_response():
    from engine.chat_response import generate_response
    
    test_queries = [
        "How are you feeling right now?",
        "What have you been working on lately?",
        "Tell me something you've learned about yourself",
        "What are you curious about?",
    ]
    
    for query in test_queries:
        print(f"\n{'='*60}")
        print(f"Q: {query}")
        print(f"{'='*60}")
        try:
            result = generate_response(query)
            if isinstance(result, dict):
                resp = result.get('response', result.get('text', str(result)))
                print(f"A: {resp[:500]}")
                # Check quality markers
                has_emotion = any(w in resp.lower() for w in ['feel', 'mood', 'emotion', 'curious', 'warm', 'stable'])
                has_memory = any(w in resp.lower() for w in ['remember', 'learned', 'built', 'worked', 'created'])
                has_self = any(w in resp.lower() for w in ['i ', "i'm", "i've", 'my ', 'myself'])
                print(f"  [quality] emotion:{has_emotion} memory:{has_memory} self-ref:{has_self}")
            else:
                print(f"A: {str(result)[:500]}")
        except Exception as e:
            print(f"ERROR: {e}")

if __name__ == '__main__':
    test_response()