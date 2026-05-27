"""Diagnose each grounding function individually."""
import sys, json
sys.path.insert(0, '.')
from pathlib import Path
ROOT = Path('.').resolve()

# 1. Check what _get_mood actually returns and why
print("=== 1. Mood Source ===")
emo_path = ROOT / "state" / "emotional_state.json"
if emo_path.exists():
    with open(emo_path) as f:
        emo = json.load(f)
    print(f"  mood field: {emo.get('mood', 'MISSING')}")
    print(f"  valence: {emo.get('valence', 'MISSING')}")
    if 'emotions' in emo:
        print(f"  emotions: {emo['emotions']}")
    else:
        # Maybe emotions are top-level?
        for k in ['boredom', 'curiosity', 'anxiety', 'desire', 'ambition']:
            if k in emo:
                print(f"  {k}: {emo[k]}")
else:
    print(f"  FILE MISSING: {emo_path}")

# 2. Check knowledge format
print("\n=== 2. Knowledge Format ===")
know_path = ROOT / "brain" / "knowledge.json"
if know_path.exists():
    with open(know_path) as f:
        k = json.load(f)
    if isinstance(k, dict) and 'nodes' in k:
        nodes = k['nodes']
        if isinstance(nodes, dict):
            print(f"  nodes: dict with {len(nodes)} entries")
            for key in list(nodes.keys())[:3]:
                node = nodes[key]
                print(f"    [{key}] type={type(node).__name__}")
                if isinstance(node, dict):
                    print(f"      keys: {list(node.keys())}")
                    print(f"      content: {str(node.get('content', node.get('text', str(node))))[:150]}")
                elif isinstance(node, str):
                    print(f"      text: {node[:150]}")
        elif isinstance(nodes, list):
            print(f"  nodes: list with {len(nodes)} entries")
            if nodes:
                print(f"    sample: {str(nodes[0])[:200]}")

# 3. Check what chat_grounding actually does
print("\n=== 3. chat_grounding internals ===")
try:
    from engine import chat_grounding as cg
    # Check if ROOT is set correctly in the module
    if hasattr(cg, 'ROOT'):
        print(f"  module ROOT: {cg.ROOT}")
    if hasattr(cg, 'DATA_DIR'):
        print(f"  module DATA_DIR: {cg.DATA_DIR}")
    
    # Try calling individual functions
    for func_name in ['_get_mood', '_get_emotional_summary', '_get_active_plans']:
        if hasattr(cg, func_name):
            fn = getattr(cg, func_name)
            result = fn()
            print(f"  {func_name}(): {str(result)[:200]}")
        else:
            print(f"  {func_name}: NOT FOUND")
    
    for func_name in ['_search_knowledge', '_search_memories']:
        if hasattr(cg, func_name):
            fn = getattr(cg, func_name)
            result = fn("thinking")
            print(f"  {func_name}('thinking'): {str(result)[:200]}")
        else:
            print(f"  {func_name}: NOT FOUND")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()