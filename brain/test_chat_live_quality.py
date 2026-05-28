"""Live quality test for chat responses — tests the actual pipeline end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import generate_response_with_metadata

def test_query(label, query):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"  Query: {query}")
    print(f"{'='*60}")
    try:
        result = generate_response_with_metadata(query)
        resp = result.get('response', '')
        meta = result.get('metadata', {})
        quality = result.get('quality_score', 0)
        intent = meta.get('detected_intent', '')
        print(f"Intent:  {intent}")
        print(f"Quality: {quality}")
        print(f"Response ({len(resp)} chars):")
        print(resp[:600])
        # Quality checks
        is_generic = any(phrase in resp.lower() for phrase in [
            'as an ai', 'i cannot', 'i don\'t have feelings',
            'i\'m just a', 'language model'
        ])
        has_specifics = any(phrase in resp.lower() for phrase in [
            'curiosity', 'boredom', 'plan', 'memory', 'dream',
            'feel', 'mood', 'learn', 'build', 'anxiety', 'ambition'
        ])
        print(f"\n  Generic AI speak: {'YES ⚠' if is_generic else 'NO ✓'}")
        print(f"  Has internal specifics: {'YES ✓' if has_specifics else 'NO ⚠'}")
        return resp, quality
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return None, 0

if __name__ == '__main__':
    queries = [
        ("INTROSPECTIVE", "What are you thinking about right now?"),
        ("EMOTIONAL", "How do you feel?"),
        ("LEARNING", "What have you learned recently?"),
        ("PLANS", "What are you working on?"),
        ("IDENTITY", "Who are you?"),
        ("CHALLENGE", "What's the hardest thing about being you?"),
    ]
    
    results = []
    for label, query in queries:
        resp, quality = test_query(label, query)
        results.append((label, quality, resp is not None))
    
    print(f"\n{'='*60}")
    print("  SUMMARY")
    print(f"{'='*60}")
    for label, quality, ok in results:
        status = '✓' if ok else '✗'
        print(f"  {status} {label:15s} quality={quality:.3f}")
    
    all_ok = all(ok for _, _, ok in results)
    avg_q = sum(q for _, q, _ in results) / len(results) if results else 0
    print(f"\n  All passed: {all_ok}")
    print(f"  Average quality: {avg_q:.3f}")