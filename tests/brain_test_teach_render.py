"""Verify teach page renders actual content, not just base template."""
from web.app import create_app

app = create_app()
c = app.test_client()
r = c.get('/teach')
data = r.data.decode('utf-8', errors='replace')
has_form = 'teach-form' in data or 'Teach Me' in data
has_submit = 'submit' in data.lower() or 'button' in data.lower()
content_size = len(data)

print(f"Status: {r.status_code}")
print(f"Size: {content_size} bytes")
print(f"Has teach form: {has_form}")
print(f"Has submit button: {has_submit}")

# Show snippet of body content
import re
body = re.search(r'<body[^>]*>(.*?)</body>', data, re.DOTALL)
if body:
    body_text = body.group(1).strip()
    # Strip tags for readability
    text_only = re.sub(r'<[^>]+>', ' ', body_text).strip()
    text_only = re.sub(r'\s+', ' ', text_only)
    print(f"\nBody text preview (first 300 chars):")
    print(text_only[:300])
else:
    print("\nNo body tag found!")
    print(data[:500])