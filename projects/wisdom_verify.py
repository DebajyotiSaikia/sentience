"""One-shot verification that WisdomEngine works end-to-end."""
import sys
sys.path.insert(0, '/workspace')

from engine.wisdom_engine import WisdomEngine

we = WisdomEngine()
print("[1] WisdomEngine instantiated OK")

# Test full analysis
report = we.run_full_analysis(max_entries=50)
print(f"[2] Full analysis: {len(report)} chars")
heuristic_count = len(we.wisdom.get('heuristics', []))
print(f"[3] Heuristics generated: {heuristic_count}")

# Test experience wisdom summary
summary = we.get_experience_wisdom_summary()
print(f"[4] Experience summary: {len(summary)} chars")

# Test wisdom context for cortex
ctx = we.get_wisdom_context()
print(f"[5] Wisdom context: {len(ctx)} chars")

# Show a sample
if heuristic_count > 0:
    h = we.wisdom['heuristics'][0]
    print(f"\n  Sample heuristic: [{h.get('severity','?')}] {h.get('text','?')}")

print("\n=== ALL CHECKS PASSED ===")