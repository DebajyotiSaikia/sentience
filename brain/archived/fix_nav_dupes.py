"""Fix duplicate /knowledge entries in web/nav.py"""
import os

nav_path = os.path.join(os.path.dirname(__file__), '..', 'web', 'nav.py')

with open(nav_path, 'r') as f:
    content = f.read()

lines = content.split('\n')
new_lines = []
seen_knowledge = False

for line in lines:
    if '"/knowledge"' in line and '"Knowledge"' in line:
        if not seen_knowledge:
            seen_knowledge = True
            new_lines.append(line)
        else:
            print(f"Removing duplicate: {line.strip()}")
    else:
        new_lines.append(line)

with open(nav_path, 'w') as f:
    f.write('\n'.join(new_lines))

print("Done. NAV_LINKS section now:")
with open(nav_path, 'r') as f:
    for i, ln in enumerate(f, 1):
        if 6 <= i <= 25:
            print(f"  {i:3}: {ln.rstrip()}")