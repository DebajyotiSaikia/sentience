import json

for f in ['plans.json', 'knowledge.json', 'improvements.json']:
    try:
        d = json.load(open(f'brain/{f}'))
        print(f"\n=== {f} ===")
        if f == 'plans.json':
            active = d.get('active_plans', [])
            completed = d.get('completed_plans', [])
            print(f"  Active: {len(active)}, Completed: {len(completed)}")
            for p in active:
                print(f"    - {p.get('name','?')}: {p.get('status','?')}")
        elif f == 'knowledge.json':
            nodes = d.get('nodes', {})
            print(f"  Nodes: {len(nodes)}")
            print(f"  Gaps: {d.get('gaps', [])}")
            print(f"  Questions: {d.get('questions', [])}")
        elif f == 'improvements.json':
            pending = d.get('pending', [])
            print(f"  Pending diagnoses: {len(pending)}")
            for diag in pending[:3]:
                print(f"    - {diag.get('diagnosis','?')}: {diag.get('status','?')}")
    except Exception as e:
        print(f"{f}: ERROR - {e}")
