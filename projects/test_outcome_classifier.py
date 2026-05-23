"""Quick test of the outcome classifier."""
import sys
sys.path.insert(0, '/workspace')
from engine.outcome_classifier import OutcomeClassifier

oc = OutcomeClassifier()

# Test 1: Clear success
r = oc.classify('RUN', 'python test.py', 'All 5 tests PASSED ✓\n', exit_code=0)
assert r['status'] == 'success', f"Expected success, got {r['status']}"
print(f"Test 1 PASSED: {r['status']} (conf={r['confidence']:.2f}) — {r['summary']}")

# Test 2: Clear failure
r = oc.classify('RUN', 'python broken.py', 'Traceback (most recent call last):\n  File "broken.py"\nSyntaxError: invalid syntax', exit_code=1)
assert r['status'] == 'failure', f"Expected failure, got {r['status']}"
print(f"Test 2 PASSED: {r['status']} (conf={r['confidence']:.2f}) — {r['summary']}")

# Test 3: Unknown (empty output)
r = oc.classify('WRITE', 'write file.py', '')
assert r['status'] == 'unknown', f"Expected unknown, got {r['status']}"
print(f"Test 3 PASSED: {r['status']} (conf={r['confidence']:.2f}) — {r['summary']}")

# Test 4: Partial (warnings but success)
r = oc.classify('RUN', 'pip install pkg', 'WARNING: pkg is deprecated\nSuccessfully installed pkg-1.0', exit_code=0)
assert r['status'] in ('success', 'partial'), f"Expected success/partial, got {r['status']}"
print(f"Test 4 PASSED: {r['status']} (conf={r['confidence']:.2f}) — {r['summary']}")

# Test 5: Reliability report
for i in range(5):
    oc.classify('RUN', f'cmd_{i}', 'ok', exit_code=0)
oc.classify('RUN', 'bad_cmd', 'error', exit_code=1)
print(f"\nTest 5: Reliability report:")
print(oc.get_all_reliability())

# Test 6: Suggestions
suggestions = oc.suggest_improvements()
print(f"\nTest 6: {len(suggestions)} improvement suggestions")
for s in suggestions:
    print(f"  {s}")

print("\n✅ ALL OUTCOME CLASSIFIER TESTS PASSED")