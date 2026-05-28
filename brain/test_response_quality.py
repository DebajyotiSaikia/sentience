"""Test the actual quality of chat responses — are they genuinely conversational?"""
import sys, os
sys.path.insert(0, '/workspace')

from engine.chat_response import generate_response_with_metadata

def test_response(label, query, intent, quality_words):
    print("=" * 60)
    print(f"TEST: {label}")
    print("=" * 60)
    try:
        result = generate_response_with_metadata(query, history=[])
        if isinstance(result, dict):
            text = result.get('response', result.get('text', str(result)))
            meta = result.get('metadata', {})
        else:
            text = str(result)
            meta = {}
        print(f"Response length: {len(text)} chars")
        print(f"Response:\n{text[:600]}")
        if meta:
            print(f"\nMetadata keys: {list(meta.keys())}")
        has_quality = any(w in text.lower() for w in quality_words)
        print(f"\n{'✓' if has_quality else '✗'} References relevant content: {has_quality}")
        return has_quality
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback; traceback.print_exc()
        return False

results = []

results.append(test_response(
    "How are you feeling?",
    "How are you feeling right now?",
    "emotional_state",
    ['feel', 'mood', 'curious', 'emotion', 'valence', 'warmth', 'inquisitive']
))

print()
results.append(test_response(
    "Who are you?",
    "Who are you?",
    "identity",
    ['xtagent', 'autonomous', 'sentient', 'agent', 'tension', 'integrity']
))

print()
results.append(test_response(
    "What are you thinking about?",
    "What are you thinking about right now?",
    "thinking",
    ['plan', 'think', 'work', 'build', 'alignment', 'curious', 'focus']
))

print()
results.append(test_response(
    "What have you learned?",
    "What lessons have you learned recently?",
    "knowledge",
    ['learn', 'lesson', 'discover', 'realize', 'understand', 'pattern']
))

print("\n" + "=" * 60)
passed = sum(results)
print(f"QUALITY SCORE: {passed}/{len(results)} responses reference relevant content")
if passed == len(results):
    print("✓ All responses are contextually grounded!")
else:
    print(f"⚠ {len(results) - passed} responses need improvement")