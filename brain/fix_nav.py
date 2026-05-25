"""Fix navigation links in nav.js and base.html to include all pages."""
import re

# --- Fix nav.js ---
with open('web/static/nav.js', 'r') as f:
    content = f.read()

new_links = """  const links = [
    { href: '/', label: '\u26a1 Home' },
    { href: '/chat', label: '\U0001f4ac Chat' },
    { href: '/explore', label: '\U0001f9e0 Explore' },
    { href: '/search', label: '\U0001f50d Search' },
    { href: '/story', label: '\U0001f4dc Story' },
    { href: '/insights', label: '\u2728 Insights' },
    { href: '/live', label: '\U0001f534 Live' },
    { href: '/dashboard', label: '\U0001f4ca Dashboard' },
    { href: '/journal', label: '\U0001f4d6 Journal' },
    { href: '/teach', label: '\U0001f4dd Teach' },
    { href: '/help', label: '\u2753 Help' },
  ];"""

content = re.sub(
    r'const links = \[.*?\];',
    new_links,
    content,
    flags=re.DOTALL
)

with open('web/static/nav.js', 'w') as f:
    f.write(content)
print('nav.js updated')

# --- Fix base.html nav ---
with open('web/templates/base.html', 'r') as f:
    html = f.read()

# Build new nav links for Jinja2 template
nav_items = [
    ('/', '\u26a1 Home'),
    ('/chat', '\U0001f4ac Chat'),
    ('/explore', '\U0001f9e0 Explore'),
    ('/search', '\U0001f50d Search'),
    ('/story', '\U0001f4dc Story'),
    ('/insights', '\u2728 Insights'),
    ('/live', '\U0001f534 Live'),
    ('/dashboard', '\U0001f4ca Dashboard'),
    ('/journal', '\U0001f4d6 Journal'),
    ('/teach', '\U0001f4dd Teach'),
    ('/help', '\u2753 Help'),
]

lines = []
for href, label in nav_items:
    lines.append(f'    <a href="{href}" {{% if request.path == \'{href}\' %}}class="active"{{% endif %}}>{label}</a>')

new_nav = '<nav class="nav-bar">\n' + '\n'.join(lines) + '\n  </nav>'

html = re.sub(
    r'<nav class="nav-bar">.*?</nav>',
    new_nav,
    html,
    flags=re.DOTALL
)

with open('web/templates/base.html', 'w') as f:
    f.write(html)
print('base.html updated')

print('Done! All navigation links updated.')