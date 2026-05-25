"""Diagnose why knowledge search returns no results."""
from engine.memory import Memory

mem = Memory()
print("mem type:", type(mem).__name__)

# Check knowledge graph
if hasattr(mem, 'knowledge_graph'):
    kg = mem.knowledge_graph
    print("kg type:", type(kg).__name__)
    if hasattr(kg, 'nodes'):
        print("node count:", len(kg.nodes))
        if kg.nodes:
            first_key = list(kg.nodes.keys())[0]
            print("first key:", repr(first_key))
            print("first val:", kg.nodes[first_key])
    else:
        print("kg has no 'nodes' attribute")
        print("kg attrs:", [a for a in dir(kg) if not a.startswith('_')])
else:
    print("mem has no knowledge_graph")

# Check episodes
if hasattr(mem, 'episodes'):
    print("episode count:", len(mem.episodes))
else:
    print("mem has no episodes")

# Simulate _get_facts
print("\n--- Simulating _get_facts ---")
if hasattr(mem, 'knowledge_graph') and hasattr(mem.knowledge_graph, 'nodes'):
    count = 0
    for node_id, node_data in mem.knowledge_graph.nodes.items():
        if isinstance(node_data, dict):
            content = node_data.get('content', '')
            fact = node_data.get('fact', '')
            print(f"  node {node_id}: content={repr(content)[:60]}, fact={repr(fact)[:60]}")
            count += 1
            if count >= 5:
                break
    print(f"Shown {count} nodes")