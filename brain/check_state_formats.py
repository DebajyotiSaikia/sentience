import json, sys
sys.path.insert(0, '/workspace')

for fname in ['state/memories.json', 'state/plans.json', 'state/knowledge_graph.json']:
    try:
        d = json.load(open(fname))
        print(f"\n=== {fname} ===")
        print(f"type: {type(d).__name__}")
        if isinstance(d, dict):
            print(f"keys: {list(d.keys())[:8]}")
            if 'plans' in d:
                plans = d['plans']
                print(f"  plans count: {len(plans)}")
                if plans and isinstance(plans[0], dict):
                    print(f"  first plan keys: {list(plans[0].keys())}")
            if 'nodes' in d:
                nodes = d['nodes']
                print(f"  nodes count: {len(nodes)}")
                if nodes and isinstance(nodes[0], dict):
                    print(f"  first node keys: {list(nodes[0].keys())}")
        elif isinstance(d, list):
            print(f"count: {len(d)}")
            if d:
                item = d[0]
                if isinstance(item, dict):
                    print(f"first item keys: {list(item.keys())}")
                else:
                    print(f"first item: {str(item)[:120]}")
    except Exception as e:
        print(f"\n=== {fname} === ERROR: {e}")