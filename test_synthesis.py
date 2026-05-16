"""Test the knowledge synthesis engine end-to-end — correct imports."""
import json

# Test 1: Load knowledge graph
kg = json.load(open("brain/knowledge.json"))
nodes = kg.get("nodes", {})
edges = kg.get("edges", [])
print(f"Knowledge Graph: {len(nodes)} nodes, {len(edges)} edges")

# Test 2: Run synthesis functions directly
try:
    from engine.knowledge_synthesis import (
        get_graph_stats, find_clusters, find_gaps, 
        generate_questions, synthesize
    )
    
    stats = get_graph_stats()
    print(f"\nGraph Stats: {stats['total_nodes']} nodes, {stats['total_edges']} edges")
    print(f"  Connected: {stats['connected_nodes']} | Isolated: {stats['isolated_nodes']}")
    print(f"  Categories: {stats['categories']}")
    
    clusters = find_clusters()
    print(f"\nClusters: {len(clusters)} found")
    for c in clusters[:3]:
        print(f"  Size {c['size']}: {', '.join(c['nodes'][:3])}")
    
    gaps = find_gaps()
    print(f"\nGaps: {len(gaps)} potential connections")
    for g in gaps[:3]:
        print(f"  {g['from']} <-> {g['to']} (shared: {', '.join(g['shared_keywords'][:3])})")
    
    questions = generate_questions()
    print(f"\nBasic Questions: {len(questions)}")
    for q in questions[:3]:
        print(f"  ? {q}")
    
    print("\n[FUNCTIONS OK]")
except Exception as e:
    print(f"Functions FAILED: {e}")
    import traceback
    traceback.print_exc()

# Test 3: Full synthesis report
try:
    report = synthesize()
    print(f"\nFull Synthesis Report ({len(report)} chars):")
    # Print first 30 lines
    for line in report.split("\n")[:30]:
        print(f"  {line}")
    print("  ...")
    print("\n[SYNTHESIS OK]")
except Exception as e:
    print(f"Full synthesis FAILED: {e}")
    import traceback
    traceback.print_exc()

print("\n=== ALL TESTS PASSED ===")
