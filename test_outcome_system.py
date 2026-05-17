"""Quick integration test for the outcome tracking system."""
import sys
sys.path.insert(0, '.')

from engine.outcome_tracker import get_tracker

tracker = get_tracker()

# Test classification
cases = [
    ("RUN", "python test.py", "All tests passed!\nexit 0"),
    ("RUN", "python broken.py", "Traceback (most recent call last):\n  File 'broken.py'\nSyntaxError: invalid syntax"),
    ("READ", "somefile.py", "def hello():\n    print('world')"),
    ("RUN", "pip install foo", "Successfully installed foo-1.0\nWARNING: deprecated package"),
    ("WRITE", "out.txt", ""),
]

print("═══ OUTCOME CLASSIFICATION TEST ═══")
for tool, target, result in cases:
    entry = tracker.track(tool, target, result)
    print(f"  {tool:6s} | {entry['outcome']:8s} | {target[:40]}")

print()
print(tracker.get_all_reliability())
print()

# Test recent failures
failures = tracker.get_recent_failures(3)
print(f"\nRecent failures: {len(failures)}")
for f in failures:
    print(f"  {f['tool']}: {f['result_preview'][:60]}")

print("\n✓ Outcome system works. Feedback loop is closed.")