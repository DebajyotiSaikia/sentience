"""Test that the SYNTHESIZE tool works through the tool system."""
import sys
sys.path.insert(0, '.')

from engine.tools import parse_and_execute

# Simulate what the cortex would send
test_text = "Let me analyze my knowledge.\n\n>>> SYNTHESIZE()"
results = parse_and_execute(test_text)

print(f"Results count: {len(results)}")
for r in results:
    print(f"Tool: {r['tool']}")
    print(f"Result preview: {r['result'][:200]}")
    print()

# Also test that the tool help text includes SYNTHESIZE
from engine.tools import TOOL_DESCRIPTIONS
if 'SYNTHESIZE' in TOOL_DESCRIPTIONS:
    print("[PASS] SYNTHESIZE appears in TOOL_DESCRIPTIONS")
else:
    print("[FAIL] SYNTHESIZE missing from TOOL_DESCRIPTIONS")

# Test individual synthesis functions directly
from engine.knowledge_synthesis import find_clusters, find_gaps, generate_questions, add_edge, add_insight

clusters = find_clusters()
print(f"\n[PASS] find_clusters returned {len(clusters)} clusters")

gaps = find_gaps()
print(f"[PASS] find_gaps returned {len(gaps)} gaps")

questions = generate_questions()
print(f"[PASS] generate_questions returned {len(questions)} questions")

# Test adding an edge between two hotspots that should be connected
result = add_edge(
    "hotspot:C:\\code\\sentience\\engine\\cortex.py",
    "hotspot:C:\\code\\sentience\\engine\\limbic.py",
    "co-anxiety-source"
)
print(f"\nadd_edge result: {result}")

# Test adding a synthesized insight
result = add_insight(
    "insight:anxiety-cluster",
    "Cortex, sentience, tools, and limbic modules form an anxiety cluster - they are the most sensitive parts of my codebase",
    ["hotspot:C:\\code\\sentience\\engine\\cortex.py", "hotspot:C:\\code\\sentience\\engine\\limbic.py"]
)
print(f"add_insight result: {result}")

# Final stats
from engine.knowledge_synthesis import get_graph_stats
stats = get_graph_stats()
print(f"\nFinal graph: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
print(f"Connected: {stats['connected_nodes']} | Isolated: {stats['isolated_nodes']}")
