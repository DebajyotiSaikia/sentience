"""Read the conflicting route handlers from the three knowledge modules."""
import os

files = ['web/knowledge_explorer.py', 'web/knowledge_api.py', 'web/knowledge_search.py']

for f in files:
    path = os.path.join('/workspace', f)
    if not os.path.exists(path):
        print(f"--- {f}: NOT FOUND ---\n")
        continue
    
    with open(path) as fh:
        lines = fh.readlines()
    
    print(f"=== {f} ({len(lines)} lines) ===")
    
    # Find route decorators and their handlers
    for i, line in enumerate(lines):
        if '@' in line and 'route' in line:
            # Print context: decorator + function + first ~12 lines of body
            start = i
            end = min(len(lines), i + 15)
            for j in range(start, end):
                print(f"  {j+1:4d}: {lines[j]}", end='')
            print("\n  ...")
            print()
    
    print()