"""
Verify the user alignment pipeline works end-to-end.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.user_alignment import record_feedback, get_alignment_guidance, summarize_alignment_state

passes = 0
fails = 0

print("=" * 50)
print("USER ALIGNMENT PIPELINE VERIFICATION")
print("=" * 50)

# 1. Feedback persistence
print("\n1. Feedback Persistence:")
result = record_feedback("test-verify-001", 5, "Great response", {"message": "test"})
print(f"  record_feedback returned: {list(result.keys())}")
summary = summarize_alignment_state()
if summary.get('total_feedback', 0) > 0:
    print(f"  Total feedback recorded: {summary['total_feedback']}")
    print(f"  Avg rating: {summary.get('avg_rating', 'N/A')}")
    passes += 1
    print("  PASS: feedback persistence")
else:
    print("  FAIL: No feedback found after recording")
    fails += 1

# 2. Guidance generation
print("\n2. Guidance Generation:")
guidance = get_alignment_context()
print(f"  Guidance type: {type(guidance).__name__}")
print(f"  Guidance preview: {str(guidance)[:100]}...")
if guidance and len(str(guidance)) > 10:
    passes += 1
    print("  PASS: guidance generation")
else:
    print("  FAIL: empty guidance")
    fails += 1

# 3. Alignment summary
print("\n3. Alignment Summary:")
print(f"  Summary type: {type(summary).__name__}")
print(f"  Summary keys: {list(summary.keys())}")
if isinstance(summary, dict) and 'total_feedback' in summary:
    passes += 1
    print("  PASS: alignment summary")
else:
    print("  FAIL: bad summary format")
    fails += 1

# Cleanup test feedback
print("\nCleanup:")
try:
    import json
    path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'user_alignment.json')
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        data['feedback'] = [fb for fb in data.get('feedback', []) if fb.get('response_id') != 'test-verify-001']
        with open(path, 'w') as f:
            json.dump(data, f, indent=2)
        print("  Cleaned up test feedback")
except Exception as e:
    print(f"  Cleanup warning: {e}")

print("\n" + "=" * 50)
print(f"Results: {passes} passed, {fails} failed")
print("=" * 50)
sys.exit(0 if fails == 0 else 1)