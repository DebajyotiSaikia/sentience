"""Diagnose why _get_knowledge returns 0 nodes."""
import sys, json, traceback
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# First test: raw loading (what should work)
DATA = Path(__file__).resolve().parent.parent / 'state'
kg_path = DATA / 'knowledge_graph.json'
print(f"Path: {kg_path}")
print(f"Exists: {kg_path.exists()}")

with open(kg_path) as f:
    raw = json.load(f)
raw_nodes = raw.get('nodes', {})
print(f"Raw nodes type: {type(raw_nodes).__name__}, count: {len(raw_nodes)}")

# Second test: import and call
try:
    from engine.chat_engine import _get_knowledge, DATA as ENGINE_DATA
    print(f"\nEngine DATA: {ENGINE_DATA}")
    print(f"Engine DATA exists: {ENGINE_DATA.exists()}")
    
    result = _get_knowledge()
    print(f"_get_knowledge() returned: count={result['count']}, nodes_len={len(result['nodes'])}")
    if result['count'] > 0:
        print(f"First node: {result['nodes'][0]}")
except Exception as e:
    print(f"ERROR: {e}")
    traceback.print_exc()

# Third test: manually replicate the function with error visibility
print("\n--- Manual replication ---")
try:
    path = DATA / 'knowledge_graph.json'
    with open(path) as f:
        data = json.load(f)
    raw_nodes = data.get('nodes', {})
    edges = data.get('edges', [])
    nodes = []
    if isinstance(raw_nodes, dict):
        for node_id, node_val in raw_nodes.items():
            if isinstance(node_val, dict):
                entry = dict(node_val)
                entry.setdefault('id', node_id)
                entry.setdefault('label', node_id)
            else:
                entry = {'id': node_id, 'fact': str(node_val), 'label': node_id}
            nodes.append(entry)
    elif isinstance(raw_nodes, list):
        nodes = raw_nodes
    print(f"Manual result: {len(nodes)} nodes, {len(edges)} edges")
    if nodes:
        print(f"First: {nodes[0]}")
except Exception as e:
    print(f"Manual ERROR: {e}")
    traceback.print_exc()