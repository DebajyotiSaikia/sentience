"""Diagnose why knowledge search returns 0 results."""
import sys, json, os
sys.path.insert(0, '.')

# First, check what functions knowledge_search actually exports
import engine.knowledge_search as ks
print("=== knowledge_search exports ===")
public = [x for x in dir(ks) if not x.startswith('_')]
print(f"  Functions: {public}")

# Try calling whatever search function exists
for name in ['search_knowledge', 'search', 'query', 'find']:
    fn = getattr(ks, name, None)
    if fn and callable(fn):
        print(f"\n=== Trying ks.{name}('emotion') ===")
        try:
            result = fn('emotion')
            print(f"  Type: {type(result).__name__}, Value: {str(result)[:200]}")
        except Exception as e:
            print(f"  Error: {e}")

# Now try the grounding pipeline
print("\n=== Chat Grounding ===")
try:
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("What do you know about emotions?")
    print(f"  Context keys: {list(ctx.keys()) if isinstance(ctx, dict) else type(ctx)}")
    if isinstance(ctx, dict):
        for k, v in ctx.items():
            if isinstance(v, (list, tuple)):
                print(f"  {k}: {len(v)} items")
                for item in list(v)[:2]:
                    print(f"    -> {str(item)[:120]}")
            elif isinstance(v, str):
                print(f"  {k}: {v[:120]}...")
            else:
                print(f"  {k}: {type(v).__name__} = {str(v)[:100]}")
except Exception as e:
    print(f"  Error: {e}")

# Check raw knowledge data
print("\n=== Raw Knowledge Data ===")
for path in ['persist/knowledge/graph.json', 'state/knowledge_graph.json']:
    if os.path.exists(path):
        with open(path) as f:
            data = json.load(f)
        nodes = data.get('nodes', [])
        edges = data.get('edges', [])
        print(f"\n{path}: {len(nodes)} nodes, {len(edges)} edges")
        # Show node structure
        for n in nodes[:3]:
            if isinstance(n, dict):
                print(f"  Node keys: {list(n.keys())}")
                label = n.get('label', n.get('text', n.get('id', '?')))
                print(f"  [{n.get('type','?')}] {str(label)[:100]}")
            else:
                print(f"  Raw: {str(n)[:100]}")