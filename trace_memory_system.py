import json
import os

data_dir = 'data'
files_to_check = [
    'reasoning_history.json',
    'emotional_history.json', 
    'deliberation_log.json',
    'outcome_log.json',
    'wisdom.json',
    'experiments.json',
    'predictions.json',
]

for fname in files_to_check:
    path = os.path.join(data_dir, fname)
    if not os.path.exists(path):
        print(f"\n{fname}: MISSING")
        continue
    
    with open(path, 'r') as f:
        data = json.load(f)
    
    print(f"\n{'='*60}")
    print(f"FILE: {fname}")
    print(f"Type: {type(data).__name__}, ", end='')
    
    if isinstance(data, list):
        print(f"Length: {len(data)}")
        if len(data) > 0:
            sample = data[-1]  # most recent
            if isinstance(sample, dict):
                print(f"  Keys: {list(sample.keys())}")
                # Show condensed version
                for k, v in sample.items():
                    v_str = str(v)[:120]
                    print(f"    {k}: {v_str}")
    elif isinstance(data, dict):
        print(f"Keys: {list(data.keys())[:15]}")
        for k in list(data.keys())[:3]:
            v_str = str(data[k])[:120]
            print(f"  {k}: {v_str}")
    else:
        print(f"Value: {str(data)[:200]}")

# Now check: where does the engine store memories?
print(f"\n{'='*60}")
print("SEARCHING FOR MEMORY STORAGE CODE")
print('='*60)

engine_dir = 'engine'
if os.path.isdir(engine_dir):
    for fname in os.listdir(engine_dir):
        if fname.endswith('.py'):
            path = os.path.join(engine_dir, fname)
            with open(path, 'r') as f:
                content = f.read()
            # Look for memory-related patterns
            hits = []
            for i, line in enumerate(content.split('\n')):
                if any(kw in line.lower() for kw in ['episodic', 'memory', 'remember', 'store_memory', 'add_memory']):
                    hits.append((i+1, line.strip()))
            if hits:
                print(f"\n  {fname}:")
                for lineno, line in hits[:8]:
                    print(f"    L{lineno}: {line[:100]}")