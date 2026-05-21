"""One-shot diagnosis of the SYNTHESIZE() KeyError bug."""
import sys, traceback, json
from pathlib import Path

sys.path.insert(0, '.')

# 1. Show knowledge data shape
kg = json.loads(Path('brain/knowledge.json').read_text())
nodes = kg.get('nodes', kg)
edges = kg.get('edges', [])
print(f"KNOWLEDGE: {len(nodes)} nodes, {len(edges)} edges")

for key in list(nodes.keys())[:5]:
    val = nodes[key]
    if isinstance(val, dict):
        print(f"  Node '{key[:50]}': keys={list(val.keys())}")
    else:
        print(f"  Node '{key[:50]}': type={type(val).__name__}, val={str(val)[:60]}")

# 2. Try synthesize() as a bare function
print("\n=== CALLING synthesize() ===")
try:
    from engine.knowledge_synthesis import synthesize
    result = synthesize()
    print("SUCCESS!")
    print(result[:500])
except Exception as e:
    traceback.print_exc()
    print(f"\nERROR: {type(e).__name__}: {e}")

# 3. Also check how the tool system calls it
print("\n=== CHECKING TOOL HANDLER ===")
try:
    from engine.tools import TOOL_REGISTRY
    if 'SYNTHESIZE' in TOOL_REGISTRY:
        print(f"SYNTHESIZE tool: {TOOL_REGISTRY['SYNTHESIZE']}")
    else:
        print("Available tools:", list(TOOL_REGISTRY.keys())[:10])
except Exception as e:
    print(f"Could not check tool registry: {e}")