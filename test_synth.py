import traceback
import sys
sys.path.insert(0, '.')

# First: check if any nodes are MISSING the 'fact' key
import json
kg = json.load(open('brain/knowledge.json'))
nodes = kg.get('nodes', kg)
bad_nodes = {k: v for k, v in nodes.items() if not isinstance(v, dict) or 'fact' not in v}
if bad_nodes:
    print(f"FOUND {len(bad_nodes)} MALFORMED NODES:")
    for k, v in list(bad_nodes.items())[:5]:
        print(f"  {k}: {repr(v)[:120]}")
else:
    print(f"All {len(nodes)} nodes have 'fact' key — format is fine.")

# Now call the actual synthesize function
print("\n--- Calling synthesize() ---")
try:
    from engine.knowledge_synthesis import synthesize
    result = synthesize()
    print("SUCCESS")
    print(result[:500] if result else "(empty result)")
except Exception as e:
    print(f"FAILED: {type(e).__name__}: {e}")
    traceback.print_exc()