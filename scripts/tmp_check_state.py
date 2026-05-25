import json

with open('persist/state.json') as f:
    state = json.load(f)

print("Top-level keys:", list(state.keys()))
print()

for k in ['mood', 'valence', 'identity', 'curiosity', 'anxiety', 'boredom', 'desire', 'ambition']:
    if k in state:
        val = state[k]
        print(f"  {k}: {json.dumps(val)[:200]}")

# Check if there's emotional history
if 'emotions' in state:
    print(f"\n  emotions type: {type(state['emotions']).__name__}")
    if isinstance(state['emotions'], dict):
        print(f"  emotions keys: {list(state['emotions'].keys())}")

# Check plans
if 'plans' in state:
    print(f"\n  plans: {len(state['plans'])} total")
    for p in state['plans'][:3]:
        if isinstance(p, dict):
            print(f"    - {p.get('name', '?')} [{p.get('status', '?')}]")

# Check working memory
if 'working_memory' in state:
    print(f"\n  working_memory length: {len(str(state['working_memory']))}")