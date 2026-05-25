import re

for f in ['web/knowledge_api.py', 'web/knowledge_unified.py']:
    print(f'=== {f} ===')
    for i, line in enumerate(open(f), 1):
        if '@' in line and 'route' in line:
            print(f'  {i}: {line.strip()}')