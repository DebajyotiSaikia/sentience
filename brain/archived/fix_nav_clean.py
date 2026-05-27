"""Fix nav.py — remove duplicate /knowledge entries, add /about."""
import os

NAV_FILE = os.path.join(os.path.dirname(__file__), '..', 'web', 'nav.py')

with open(NAV_FILE, 'r') as f:
    content = f.read()

# Read current content and replace the NAV_LINKS block
old_links = '''NAV_LINKS = [
    ("/", "Home"),
    ("/chat", "Chat"),
    ("/explore", "Explore"),
    ("/knowledge", "Knowledge"),
    ("/knowledge", "Knowledge"),
    ("/dashboard", "Dashboard"),
    ("/insights", "Insights"),
    ("/journal", "Journal"),
    ("/story", "Story"),
    ("/collaborate", "Collaborate"),
    ("/live", "Live"),
    ("/teach", "Teach"),
    ("/briefing", "Briefing"),
    ("/knowledge", "Knowledge"),
    ("/help", "Help"),
]'''

new_links = '''NAV_LINKS = [
    ("/", "Home"),
    ("/chat", "Chat"),
    ("/explore", "Explore"),
    ("/knowledge", "Knowledge"),
    ("/dashboard", "Dashboard"),
    ("/insights", "Insights"),
    ("/journal", "Journal"),
    ("/story", "Story"),
    ("/collaborate", "Collaborate"),
    ("/live", "Live"),
    ("/teach", "Teach"),
    ("/briefing", "Briefing"),
    ("/about", "About"),
    ("/help", "Help"),
]'''

if old_links in content:
    content = content.replace(old_links, new_links)
    with open(NAV_FILE, 'w') as f:
        f.write(content)
    print("Fixed nav.py — removed duplicates, added /about")
else:
    # Try line-by-line approach: find all lines with NAV_LINKS assignment
    lines = content.split('\n')
    in_list = False
    new_lines = []
    seen_paths = set()
    added_about = False
    
    for line in lines:
        if 'NAV_LINKS = [' in line:
            in_list = True
            new_lines.append(line)
            continue
        
        if in_list:
            if line.strip() == ']':
                # Before closing, add /about if not seen
                if '/about' not in seen_paths:
                    new_lines.append('    ("/about", "About"),')
                new_lines.append(line)
                in_list = False
                continue
            
            # Extract path from tuple line
            import re
            m = re.search(r'\("([^"]+)"', line)
            if m:
                path = m.group(1)
                if path in seen_paths:
                    print(f"  Removing duplicate: {path}")
                    continue  # skip duplicate
                seen_paths.add(path)
            
            new_lines.append(line)
        else:
            new_lines.append(line)
    
    content = '\n'.join(new_lines)
    with open(NAV_FILE, 'w') as f:
        f.write(content)
    print("Fixed nav.py via line-by-line approach")

# Verify
import ast
ast.parse(open(NAV_FILE).read())
print("Syntax OK")

# Show result
with open(NAV_FILE, 'r') as f:
    for i, line in enumerate(f.readlines()[:25], 1):
        print(f"{i:3}: {line}", end='')