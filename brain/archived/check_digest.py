"""Quick diagnostic: what routes does digest.py define?"""
lines = open('web/digest.py').readlines()
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('def ') or stripped.startswith('@') or 'render_template' in stripped:
        print(f"{i+1:>4}: {stripped}")