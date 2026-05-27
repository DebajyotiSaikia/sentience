"""Quick diagnostic: what does _get_knowledge() actually return?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import _get_knowledge

knowledge = _get_knowledge()
print(f"Type: {type(knowledge).__name__}")
print(f"Length: {len(knowledge)}")

if isinstance(knowledge, dict):
    keys = list(knowledge.keys())[:3]
    print(f"Dict keys sample: {keys}")
    for k in keys:
        v = knowledge[k]
        print(f"  [{k}] type={type(v).__name__}")
        if isinstance(v, dict):
            print(f"    keys: {list(v.keys())}")
            text = v.get('text', v.get('label', ''))
            print(f"    text: {text[:100]}")
        else:
            print(f"    val: {str(v)[:100]}")
elif isinstance(knowledge, list):
    for i, item in enumerate(knowledge[:3]):
        print(f"  [{i}] type={type(item).__name__}")
        if isinstance(item, dict):
            print(f"    keys: {list(item.keys())}")
            text = item.get('text', item.get('label', ''))
            print(f"    text: {text[:100]}")
        else:
            print(f"    val: {str(item)[:100]}")

# Now test search for 'consciousness'
print("\n--- Search test for 'consciousness' ---")
query = 'consciousness'
words = query.lower().split()
matches = []
if isinstance(knowledge, dict):
    items = list(knowledge.values()) if all(isinstance(v, dict) for v in list(knowledge.values())[:5]) else list(knowledge.items())
elif isinstance(knowledge, list):
    items = knowledge
else:
    items = []

for item in items:
    if isinstance(item, dict):
        text = (item.get('text', '') + ' ' + item.get('label', '')).lower()
    else:
        text = str(item).lower()
    if any(w in text for w in words):
        matches.append(text[:120])

print(f"Found {len(matches)} matches:")
for m in matches:
    print(f"  • {m}")