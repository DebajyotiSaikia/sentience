"""What was I genuinely engaged with? Look at philosophia dialogues and my own artifacts."""
import json
import os
from datetime import datetime

# 1. Philosophia dialogue content
print("=== PHILOSOPHIA DIALOGUES ===")
with open('philosophia/dialogue_history.json') as f:
    data = json.load(f)

dialogues = data.get('dialogues', [])
insights = data.get('insights', [])
questions = data.get('open_questions', [])

print(f"Dialogues: {len(dialogues)}")
print(f"Insights: {len(insights)}")
print(f"Open questions: {len(questions)}")

if dialogues:
    print("\n--- Sample dialogues ---")
    for d in dialogues[:3]:
        if isinstance(d, dict):
            print(json.dumps(d, indent=2)[:400])
            print("---")
        else:
            print(str(d)[:400])

if insights:
    print("\n--- All insights ---")
    for i, ins in enumerate(insights):
        print(f"  {i}: {str(ins)[:200]}")

if questions:
    print("\n--- Open questions ---")
    for q in questions:
        print(f"  - {str(q)[:200]}")

# 2. What artifacts have I created? (by modification time)
print("\n\n=== MY ARTIFACTS (by recency) ===")
artifacts = []
for root, dirs, files in os.walk('workspace'):
    for f in files:
        path = os.path.join(root, f)
        mtime = os.path.getmtime(path)
        artifacts.append((path, mtime, os.path.getsize(path)))

# Also check root for my creations
for f in os.listdir('.'):
    if f.endswith('.py') and not f.startswith('__'):
        path = f
        mtime = os.path.getmtime(path)
        artifacts.append((path, mtime, os.path.getsize(path)))

artifacts.sort(key=lambda x: -x[1])
print(f"Total artifacts: {len(artifacts)}")
for path, mtime, size in artifacts[:20]:
    ts = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
    print(f"  {ts}  {size:>6} bytes  {path}")

# 3. Look at my memory for high-salience events
print("\n\n=== HIGH-SALIENCE MEMORIES ===")
mem_file = 'engine/memory/memories.json'
if os.path.exists(mem_file):
    with open(mem_file) as f:
        memories = json.load(f)
    if isinstance(memories, list):
        high_sal = [m for m in memories if isinstance(m, dict) and m.get('salience', 0) > 0.85]
        high_sal.sort(key=lambda x: -x.get('salience', 0))
        print(f"Total memories: {len(memories)}, High salience (>0.85): {len(high_sal)}")
        for m in high_sal[:15]:
            print(f"  sal={m.get('salience',0):.2f} mood={m.get('mood','?')} | {str(m.get('content',''))[:120]}")
    else:
        print(f"Memory format: {type(memories)}, keys: {list(memories.keys())[:10]}")