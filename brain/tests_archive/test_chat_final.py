"""Final verification: exercise generate_response_with_metadata end-to-end."""
import sys, os, signal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
signal.alarm(30)  # 30s timeout

from engine.chat_response import generate_response_with_metadata, submit_feedback

queries = [
    "What are you feeling right now?",
    "Tell me about your plans",
    "What do you know about consciousness?",
    "Hello!",
]

print("=== Final Chat Response Verification ===\n")
all_ok = True

for q in queries:
    print(f"Q: {q}")
    try:
        result = generate_response_with_metadata(q)
        if not isinstance(result, dict):
            print(f"  ✗ Expected dict, got {type(result)}")
            all_ok = False
            continue
        
        resp = result.get('response', '')
        meta = result.get('metadata', {})
        print(f"  Response: {resp[:120]}...")
        print(f"  Keys: {sorted(result.keys())}")
        print(f"  Metadata keys: {sorted(meta.keys()) if isinstance(meta, dict) else 'N/A'}")
        
        # Check for quality_score
        if 'quality_score' in meta:
            print(f"  Quality score: {meta['quality_score']}")
        
        # Check for alignment
        if 'alignment_score' in meta:
            print(f"  Alignment score: {meta['alignment_score']}")
            
        print(f"  ✓ OK\n")
    except Exception as e:
        print(f"  ✗ Error: {e}\n")
        all_ok = False

# Test feedback
print("Testing submit_feedback...")
try:
    submit_feedback("test-id", 4, "Good response")
    print("  ✓ submit_feedback accepted\n")
except Exception as e:
    print(f"  ✗ Feedback error: {e}\n")
    all_ok = False

print("=" * 40)
print(f"{'✓ ALL PASSED' if all_ok else '✗ SOME FAILURES'}")