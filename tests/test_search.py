"""Test what memory.get_facts() actually returns, to debug search."""
from persistence import memory

# Check if get_facts exists
if not hasattr(memory, 'get_facts'):
    print("NO get_facts method!")
else:
    facts = memory.get_facts()
    print(f"Type: {type(facts)}")
    print(f"Length: {len(facts) if hasattr(facts, '__len__') else 'N/A'}")
    
    if isinstance(facts, dict):
        keys = list(facts.keys())[:3]
        for k in keys:
            v = facts[k]
            print(f"  key={repr(k)[:60]}, val type={type(v).__name__}, val={repr(v)[:120]}")
    elif isinstance(facts, list):
        for i, f in enumerate(facts[:3]):
            print(f"  [{i}] type={type(f).__name__}: {repr(f)[:120]}")
    else:
        print(f"  Raw: {repr(facts)[:200]}")

# Now test the search logic from app.py
query = "test"
results = []

if isinstance(facts, dict):
    for fid, fdata in facts.items():
        if isinstance(fdata, dict):
            text = fdata.get('fact', '')
        else:
            text = str(fdata)
        if query.lower() in text.lower():
            results.append({'id': fid, 'text': text})
elif isinstance(facts, list):
    for f in facts:
        text = f.get('fact', str(f)) if isinstance(f, dict) else str(f)
        if query.lower() in text.lower():
            results.append({'text': text})

print(f"\nSearch for '{query}': {len(results)} results")
for r in results[:5]:
    print(f"  -> {repr(r)[:120]}")