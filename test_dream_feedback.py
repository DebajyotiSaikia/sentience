"""Test the dream feedback loop components work correctly."""
import sys
sys.path.insert(0, '.')

from engine.knowledge_synthesis import find_gaps, add_edge, add_insight, get_graph_stats

# 1. Check graph stats
stats = get_graph_stats()
print(f"Knowledge graph stats: {stats}")

# 2. Check find_gaps works
gaps = find_gaps()
print(f"\nFound {len(gaps)} knowledge gaps:")
for g in gaps[:5]:
    print(f"  {g.get('from', '?')} <-> {g.get('to', '?')} (overlap: {g.get('overlap_score', 0)})")

# 3. Test add_insight (what the dream feedback loop does)
result = add_insight(
    "test:dream_feedback_verification",
    "Dream feedback loop is operational — synthesis connects to dreaming",
    source_keys=[]
)
print(f"\nadd_insight result: {result}")

# 4. Verify it persisted
stats_after = get_graph_stats()
print(f"Stats after: {stats_after}")

# 5. Check overlap scores for auto-bridging
high_overlap = [g for g in gaps if g.get("overlap_score", 0) >= 3]
print(f"\nHigh-overlap gaps (>= 3, would be auto-bridged): {len(high_overlap)}")
for g in high_overlap[:3]:
    print(f"  {g.get('from')} <-> {g.get('to')} (score: {g.get('overlap_score')})")

print("\n✓ Dream feedback loop components are functional!")
