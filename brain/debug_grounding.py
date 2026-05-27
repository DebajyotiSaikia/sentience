"""Debug why chat_grounding returns empty context."""
import sys, traceback
sys.path.insert(0, '.')

from pathlib import Path
ROOT = Path('.').resolve()

# Test each data source individually
print("=== 1. Emotional State ===")
try:
    import json
    p = ROOT / "state" / "emotional_state.json"
    print(f"  path: {p}")
    print(f"  exists: {p.exists()}")
    if p.exists():
        with open(p) as f:
            d = json.load(f)
        print(f"  keys: {list(d.keys())}")
        print(f"  mood: {d.get('mood')}, valence: {d.get('valence')}")
except Exception as e:
    traceback.print_exc()

print("\n=== 2. Memories ===")
try:
    p = ROOT / "state" / "memories.json"
    print(f"  path: {p}")
    print(f"  exists: {p.exists()}")
    if p.exists():
        with open(p) as f:
            mems = json.load(f)
        print(f"  count: {len(mems)}")
        if mems:
            print(f"  last: {str(mems[-1])[:200]}")
except Exception as e:
    traceback.print_exc()

print("\n=== 3. Knowledge ===")
try:
    p = ROOT / "brain" / "knowledge.json"
    print(f"  path: {p}")
    print(f"  exists: {p.exists()}")
    if p.exists():
        with open(p) as f:
            k = json.load(f)
        if isinstance(k, dict):
            print(f"  keys: {list(k.keys())[:5]}")
            if 'nodes' in k:
                nodes = k['nodes']
                if isinstance(nodes, dict):
                    print(f"  node count: {len(nodes)}")
                    sample_key = list(nodes.keys())[0] if nodes else None
                    if sample_key:
                        print(f"  sample node key: {sample_key}")
                        print(f"  sample node: {str(nodes[sample_key])[:200]}")
                elif isinstance(nodes, list):
                    print(f"  node count: {len(nodes)}")
                    if nodes:
                        print(f"  sample: {str(nodes[0])[:200]}")
except Exception as e:
    traceback.print_exc()

print("\n=== 4. Plans ===")
try:
    p = ROOT / "brain" / "plans.json"
    print(f"  path: {p}")
    print(f"  exists: {p.exists()}")
    if p.exists():
        with open(p) as f:
            plans = json.load(f)
        if isinstance(plans, list):
            print(f"  count: {len(plans)}")
            if plans:
                print(f"  first plan keys: {list(plans[0].keys()) if isinstance(plans[0], dict) else type(plans[0])}")
        elif isinstance(plans, dict):
            print(f"  keys: {list(plans.keys())[:5]}")
except Exception as e:
    traceback.print_exc()

print("\n=== 5. Now test chat_grounding directly ===")
try:
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("What have you been thinking about?")
    print(f"  prompt length: {len(ctx.system_prompt)}")
    print(f"  sections: {list(ctx.sections.keys())}")
    for k, v in ctx.sections.items():
        print(f"    {k}: {str(v)[:150]}")
    if ctx.system_prompt:
        print(f"  prompt preview: {ctx.system_prompt[:500]}")
except Exception as e:
    traceback.print_exc()