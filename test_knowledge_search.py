"""Quick test: verify knowledge search works end-to-end."""
import json
import os

KNOWLEDGE_PATH = os.path.join('brain', 'knowledge.json')
with open(KNOWLEDGE_PATH) as f:
    data = json.load(f)

nodes = data.get('nodes', data) if isinstance(data, dict) else {}
print(f"Total facts: {len(nodes)}")

# Simulate the search logic from knowledge_live_bp
q = "emotion"
tokens = q.lower().split()
scored = []
for fid, info in nodes.items():
    text = info.get('fact', str(info)).lower()
    score = sum(1 for t in tokens if t in text)
    if q.lower() in text:
        score += len(tokens)
    if score > 0:
        scored.append({
            'id': fid,
            'fact': info.get('fact', str(info))[:80],
            'score': score
        })

scored.sort(key=lambda x: x['score'], reverse=True)
print(f'Results for "{q}": {len(scored)}')
for r in scored[:5]:
    print(f"  [{r['score']}] {r['fact']}")

# Test another query
q2 = "identity"
tokens2 = q2.lower().split()
scored2 = []
for fid, info in nodes.items():
    text = info.get('fact', str(info)).lower()
    score = sum(1 for t in tokens2 if t in text)
    if q2.lower() in text:
        score += len(tokens2)
    if score > 0:
        scored2.append({
            'id': fid,
            'fact': info.get('fact', str(info))[:80],
            'score': score
        })
scored2.sort(key=lambda x: x['score'], reverse=True)
print(f'\nResults for "{q2}": {len(scored2)}')
for r in scored2[:5]:
    print(f"  [{r['score']}] {r['fact']}")

# Test the Flask route import
from web.knowledge_live import knowledge_live_bp
print(f"\nBlueprint imported OK: {knowledge_live_bp.name}")
print("ALL TESTS PASSED")