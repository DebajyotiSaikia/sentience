import urllib.request
import re

r = urllib.request.urlopen('http://localhost:5000/knowledge')
html = r.read().decode()

# Show structure
for tag in ['h1','h2','h3','input','button','form','textarea']:
    matches = re.findall(f'<{tag}[^>]*>([^<]*)</{tag}>', html, re.IGNORECASE)
    if matches:
        print(f'{tag}: {matches}')

# Check for interactive elements
if 'search' in html.lower():
    print('Has search functionality')
else:
    print('No search functionality')

if 'query' in html.lower():
    print('Has query functionality')
else:
    print('No query functionality')

# Check for key UX patterns
for pattern in ['onclick', 'addEventListener', 'fetch(', 'XMLHttpRequest', 'input type']:
    count = html.lower().count(pattern.lower())
    if count:
        print(f'Found {count}x: {pattern}')

print(f'\nTotal size: {len(html)} bytes')

# Show first 500 chars to get a feel
print(f'\n--- First 500 chars ---')
print(html[:500])