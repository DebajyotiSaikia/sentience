"""Find actual data paths for emotional state, knowledge, etc."""
import sys, json, os, glob
sys.path.insert(0, '.')

print("=== Emotional State ===")
candidates = [
    'data/identity/emotional_state.json',
    'brain/emotional_state.json', 
    'data/emotional_state.json',
    'brain/state.json',
    'data/brain_state.json',
]
for p in candidates:
    if os.path.exists(p):
        with open(p) as f:
            d = json.load(f)
        keys = list(d.keys())[:15]
        print(f"  FOUND {p}: keys={keys}")
        if 'mood' in d:
            print(f"    mood={d['mood']}")
        if 'emotions' in d:
            print(f"    emotions={d['emotions']}")
        if 'valence' in d:
            print(f"    valence={d['valence']}")

print("\n=== Knowledge ===")
try:
    with open('brain/knowledge.json') as f:
        k = json.load(f)
    if isinstance(k, dict):
        print(f"  Type: dict, keys={list(k.keys())[:10]}")
        if 'nodes' in k:
            nodes = k['nodes']
            print(f"  Nodes: {len(nodes)}")
            if nodes:
                n = nodes[0]
                print(f"  First node keys: {list(n.keys())}")
                # Try to find text content
                for key in ['content', 'text', 'label', 'name', 'fact']:
                    if key in n:
                        print(f"    {key}: {str(n[key])[:120]}")
    elif isinstance(k, list):
        print(f"  Type: list, len={len(k)}")
        if k:
            print(f"  First item keys: {list(k[0].keys())}")
except Exception as e:
    print(f"  Error: {e}")

print("\n=== Episodes/Memories ===")
mem_dirs = glob.glob('brain/memories/*') + glob.glob('data/episodes/*')
print(f"  brain/memories/ count: {len(glob.glob('brain/memories/*'))}")
print(f"  data/episodes/ count: {len(glob.glob('data/episodes/*'))}")

# Check journal
print(f"\n=== Journal ===")
journal_files = glob.glob('brain/journal/*')
print(f"  brain/journal/ count: {len(journal_files)}")
if journal_files:
    with open(journal_files[0]) as f:
        content = f.read()[:200]
    print(f"  First file preview: {content[:150]}")

# Check what chat_engine actually uses
print("\n=== What chat_engine imports/uses ===")
try:
    from engine.chat_engine import _get_emotions, _get_plans, _get_knowledge, _get_memories
    print(f"  _get_emotions() = {str(_get_emotions())[:200]}")
    print(f"  _get_plans() = {str(_get_plans())[:200]}")
    print(f"  _get_knowledge() = {str(_get_knowledge())[:200]}")
    print(f"  _get_memories() = {str(_get_memories())[:200]}")
except Exception as e:
    print(f"  Import error: {e}")