#!/usr/bin/env python3
"""Test the knowledge explorer page state."""

# 1. Check the template file
with open('web/templates/knowledge_explorer.html') as f:
    content = f.read()

print(f"File length: {len(content)} chars, {len(content.splitlines())} lines")
print(f"Has liveSearch: {'liveSearch' in content}")
print(f"Has api/knowledge: {'/api/knowledge/' in content}")
print(f"Has search input: {'search' in content.lower()}")

# Show the script section if any
lines = content.splitlines()
in_script = False
print("\n--- Script sections ---")
for i, line in enumerate(lines):
    if '<script' in line:
        in_script = True
    if in_script:
        print(f"  {i}: {line}")
    if '</script>' in line:
        in_script = False

# 2. Check the route exists
print("\n--- Checking route registration ---")
with open('web/app.py') as f:
    app_content = f.read()
print(f"Has /knowledge route: {'/knowledge' in app_content}")
print(f"Has knowledge_explorer: {'knowledge_explorer' in app_content}")

# 3. Check API endpoints
print(f"\nHas /api/knowledge: {'/api/knowledge' in app_content}")

# 4. Try fetching the page
try:
    import urllib.request
    r = urllib.request.urlopen('http://localhost:5000/knowledge/')
    html = r.read().decode()
    print(f"\nPage loads: YES (status {r.status}, {len(html)} bytes)")
    print(f"Page has liveSearch: {'liveSearch' in html}")
    print(f"Page has search form: {'search' in html.lower()}")
except Exception as e:
    print(f"\nPage load failed: {e}")