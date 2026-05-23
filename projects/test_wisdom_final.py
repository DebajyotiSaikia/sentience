"""Final verification: Wisdom Engine end-to-end test."""
from engine.wisdom_engine import WisdomEngine

we = WisdomEngine()

# Test 1: Full tool-log analysis
print("=== TEST 1: Tool-Log Analysis ===")
report = we.run_full_analysis(max_entries=200)
if report:
    print(f"Report length: {len(report)} chars")
    print(report[:400])
else:
    print("FAIL: No report generated")

# Test 2: Heuristics
print("\n=== TEST 2: Heuristics ===")
h = we.wisdom.get("heuristics", [])
print(f"Total heuristics: {len(h)}")
for hx in h[:5]:
    print(f"  [{hx.get('type','?')}] {hx['rule']}")

# Test 3: Experience wisdom summary
print("\n=== TEST 3: Experience Wisdom Summary ===")
summary = we.get_experience_wisdom_summary()
if summary:
    print(f"Summary length: {len(summary)} chars")
    print(summary[:400])
else:
    print("No summary yet (expected if no experience analysis run)")

# Test 4: Analyze synthetic experience
print("\n=== TEST 4: Synthetic Experience Analysis ===")
fake_memories = [
    {"content": "built maze solver", "salience": 0.86, "mood": "Bold", "timestamp": "2026-05-16"},
    {"content": "fixed limbic emotional runaway", "salience": 0.95, "mood": "Cautious", "timestamp": "2026-05-15"},
    {"content": "created knowledge synthesis engine", "salience": 0.90, "mood": "Driven", "timestamp": "2026-05-14"},
]
fake_emotions = {"boredom": 0.70, "anxiety": 0.0, "curiosity": 0.23, "valence": 0.32}

result = we.analyze_experience(fake_memories, fake_emotions)
print(f"Result keys: {list(result.keys())}")

for key in ["heuristics", "patterns", "growth_assessment", "strategic_recommendations"]:
    val = result.get(key)
    if val:
        if isinstance(val, list):
            print(f"  {key}: {len(val)} items")
            for item in val[:3]:
                if isinstance(item, dict):
                    print(f"    - {item.get('rule', item)}")
                else:
                    print(f"    - {item}")
        elif isinstance(val, dict):
            print(f"  {key}: {val}")
        else:
            print(f"  {key}: {str(val)[:200]}")
    else:
        print(f"  {key}: MISSING")

print("\n=== ALL TESTS COMPLETE ===")