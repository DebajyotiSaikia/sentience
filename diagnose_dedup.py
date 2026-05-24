import json
from pathlib import Path
from collections import Counter

kg = json.loads(Path('brain/knowledge.json').read_text())
nodes = kg.get('nodes', {})

# Show what content[:80] looks like for all nodes
prefixes = Counter()
for nid, nd in nodes.items():
    content = nd.get('fact', nd.get('content', '')) if isinstance(nd, dict) else str(nd)
    if content and len(str(content)) > 10:
        key = str(content)[:80]
        prefixes[key] += 1

print(f"Total unique prefixes (content[:80]): {len(prefixes)}")
print(f"\nPrefixes appearing MORE than once:")
for prefix, count in prefixes.most_common():
    if count > 1:
        print(f"  [{count}x] {prefix[:60]}...")

print(f"\nAll unique prefixes (first 60 chars):")
for prefix, count in sorted(prefixes.items(), key=lambda x: -x[1]):
    print(f"  [{count}x] {prefix[:70]}")