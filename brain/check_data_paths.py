"""Check actual data formats for chat grounding."""
import sys, json, glob, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Data File Discovery ===\n")

# Check brain/knowledge.json
try:
    with open('brain/knowledge.json') as f:
        k = json.load(f)
    if isinstance(k, dict):
        print(f"brain/knowledge.json: dict with keys: {list(k.keys())[:10]}")
        for key in list(k.keys())[:3]:
            val = k[key]
            if isinstance(val, list):
                print(f"  {key}: list[{len(val)}]")
                if val:
                    print(f"    sample: {str(val[0])[:200]}")
            elif isinstance(val, dict):
                print(f"  {key}: dict keys={list(val.keys())[:5]}")
            else:
                print(f"  {key}: {str(val)[:100]}")
    elif isinstance(k, list):
        print(f"brain/knowledge.json: list[{len(k)}]")
        if k:
            print(f"  sample: {str(k[0])[:200]}")
except Exception as e:
    print(f"brain/knowledge.json: ERROR - {e}")

print()

# Check brain/plans.json
try:
    with open('brain/plans.json') as f:
        p = json.load(f)
    if isinstance(p, dict):
        print(f"brain/plans.json: dict with keys: {list(p.keys())[:10]}")
        for key in list(p.keys())[:3]:
            print(f"  {key}: {str(p[key])[:150]}")
    elif isinstance(p, list):
        print(f"brain/plans.json: list[{len(p)}]")
        if p:
            print(f"  sample: {str(p[0])[:200]}")
except Exception as e:
    print(f"brain/plans.json: ERROR - {e}")

print()

# Check episodes/memories
for pattern in ['brain/episodes*', 'brain/memories*', 'brain/journal*', 
                'data/episodes*', 'data/emotional*', 'data/memory*',
                'data/journal*', 'brain/emotional*']:
    matches = glob.glob(pattern)
    for m in matches:
        try:
            sz = os.path.getsize(m)
            with open(m) as f:
                d = json.load(f)
            if isinstance(d, list):
                print(f"{m}: list[{len(d)}] ({sz}B)")
                if d:
                    print(f"  sample keys: {list(d[0].keys())[:8] if isinstance(d[0], dict) else str(d[0])[:100]}")
            elif isinstance(d, dict):
                print(f"{m}: dict keys={list(d.keys())[:8]} ({sz}B)")
            else:
                print(f"{m}: {type(d).__name__} ({sz}B)")
        except Exception as e:
            print(f"{m}: ERROR - {e}")

print()

# Check what existing code uses for memories
print("=== Checking existing data loading patterns ===")
try:
    from engine.chat_engine import _get_memories, _get_knowledge, _get_plans
    print("_get_memories:", str(_get_memories("test"))[:200])
    print("_get_knowledge:", str(_get_knowledge("test"))[:200])
    print("_get_plans:", str(_get_plans())[:200])
except Exception as e:
    print(f"chat_engine functions: {e}")

# Check what conversation_enricher uses
try:
    from engine.conversation_enricher import ConversationEnricher
    enricher = ConversationEnricher.__init__.__doc__
    print(f"ConversationEnricher doc: {enricher}")
except Exception as e:
    print(f"ConversationEnricher: {e}")