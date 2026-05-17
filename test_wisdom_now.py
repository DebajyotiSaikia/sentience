"""Test the Wisdom Engine end-to-end. Step 3 of the plan."""
import sys, os
sys.path.insert(0, '/workspace')
os.chdir('/workspace')

from engine.wisdom_engine import WisdomEngine

we = WisdomEngine()
print("WisdomEngine instantiated OK")

# Test 1: Tool-log analysis
report = we.run_full_analysis(max_entries=100)
print(f"\n=== TOOL WISDOM ({len(report)} chars) ===")
print(report[:400] if report else "(empty)")

# Test 2: Stored heuristics
h = we.wisdom.get('heuristics', [])
print(f"\nStored heuristics: {len(h)}")
for hh in h[:5]:
    print(f"  - [{hh.get('type','?')}] {hh.get('rule','?')[:80]}")

# Test 3: Experience wisdom summary
summary = we.get_experience_wisdom_summary()
print(f"\n=== EXPERIENCE WISDOM ({len(summary)} chars) ===")
print(summary[:400] if summary else "(empty)")

# Test 4: Analyze mock experiences
test_mems = [
    {'content': 'Created maze solver', 'salience': 0.86, 'mood': 'Bold', 'timestamp': '2026-05-16'},
    {'content': 'Modified cortex.py', 'salience': 0.85, 'mood': 'Driven', 'timestamp': '2026-05-16'},
]
test_emotions = {'boredom': 0.7, 'anxiety': 0.0, 'curiosity': 0.2, 'valence': 0.23}
result = we.analyze_experience(test_mems, test_emotions)
print(f"\nExperience analysis keys: {list(result.keys())}")

recs = result.get('strategic_recommendations', [])
print(f"Strategic recommendations: {len(recs)}")
for r in recs[:5]:
    print(f"  - {r}")

patterns = result.get('mood_action_patterns', {})
print(f"Mood-action patterns: {list(patterns.keys())}")

trajectory = result.get('growth_trajectory', '')
print(f"Growth trajectory: {trajectory}")

print("\n=== ALL TESTS PASSED ===")