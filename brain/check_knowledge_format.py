"""Check knowledge data format for grounding improvements."""
import json, os, sys
sys.path.insert(0, '.')

# Check for standalone knowledge store files
candidates = [
    'persist/knowledge/facts.json',
    'state/knowledge_store.json', 
    'persist/knowledge_store.json',
    'state/facts.json',
    'persist/facts.json',
]
for p in candidates:
    if os.path.exists(p):
        d = json.load(open(p))
        print(f"FOUND: {p} type={type(d).__name__} len={len(d)}")
        if isinstance(d, dict):
            for k in list(d.keys())[:2]:
                print(f"  sample: {k} -> {repr(d[k])[:150]}")
        elif isinstance(d, list) and d:
            print(f"  sample[0]: {repr(d[0])[:150]}")

# Check knowledge graph
kg_path = 'state/knowledge_graph.json'
if os.path.exists(kg_path):
    kg = json.load(open(kg_path))
    print(f"\nKG keys: {list(kg.keys())}")
    nodes = kg.get('nodes', {})
    print(f"KG nodes: {len(nodes)}")
    if nodes:
        if isinstance(nodes, dict):
            first_key = list(nodes.keys())[0]
            n = nodes[first_key]
            print(f"Node key format: {repr(first_key)[:80]}")
            print(f"Node value keys: {list(n.keys()) if isinstance(n, dict) else type(n).__name__}")
            print(f"Sample node: {repr(n)[:200]}")
            # Show a few more keys
            for k in list(nodes.keys())[:5]:
                v = nodes[k]
                label = v.get('label', v.get('fact', repr(v)[:60])) if isinstance(v, dict) else repr(v)[:60]
                print(f"  {k}: {label}")
        elif isinstance(nodes, list):
            n = nodes[0]
            print(f"Sample node keys: {list(n.keys()) if isinstance(n, dict) else 'not dict'}")
            print(f"Sample node: {repr(n)[:200]}")
try:
    ctx = build_grounded_context("What do you know about consciousness?")
    print(f"\nGrounding context keys: {list(ctx.keys())}")
    # Use the actual key names from the context
    knowledge = ctx.get('relevant_knowledge', ctx.get('knowledge', []))
    memories = ctx.get('relevant_memories', ctx.get('memories', []))
    print(f"Knowledge items: {len(knowledge)}")
    for ki in knowledge[:3]:
        print(f"  knowledge: {repr(ki)[:150]}")
    print(f"Memory items: {len(memories)}")
    for mi in memories[:3]:
        print(f"  memory: {repr(mi)[:150]}")
    # Also check working_memory and system_prompt lengths
    wm = ctx.get('working_memory', '')
    sp = ctx.get('system_prompt', '')
    print(f"Working memory length: {len(wm)}")
    print(f"System prompt length: {len(sp)}")
    if sp:
        print(f"System prompt preview: {sp[:300]}...")
except Exception as e:
    print(f"\nGrounding import error: {e}")