with open('web/templates/base.html') as f:
    content = f.read()

# Basic checks
print(f"File size: {len(content)} chars")
print(f"Has <nav>: {'<nav' in content}")
print(f"Has </nav>: {'</nav>' in content}")
print(f"Has nav-primary: {'nav-primary' in content}")
print(f"Has nav-group: {'nav-group' in content}")

# Check it's valid-ish HTML (balanced nav tags)
nav_opens = content.count('<nav')
nav_closes = content.count('</nav>')
print(f"Nav tags balanced: {nav_opens == nav_closes} ({nav_opens} open, {nav_closes} close)")

# Show the nav section
start = content.find('<nav')
end = content.find('</nav>') + len('</nav>')
if start >= 0 and end > start:
    nav = content[start:end]
    print(f"\nNav section ({len(nav)} chars):")
    for line in nav.split('\n'):
        print(f"  {line.rstrip()}")
else:
    print("\nWARNING: Could not extract nav section!")