"""Quick verification of chat.html integrity."""
import re
from collections import Counter

html = open('web/templates/chat.html').read()
lines = html.splitlines()
print(f"Total lines: {len(lines)}")

# Brace balance
opens = html.count('{')
closes = html.count('}')
print(f"Braces: {opens} open, {closes} close, diff={opens-closes}")

# Check for duplicate function definitions
funcs = re.findall(r'(?:async\s+)?function\s+(\w+)', html)
dupes = {k: v for k, v in Counter(funcs).items() if v > 1}
if dupes:
    print(f"⚠ DUPLICATE FUNCTIONS: {dupes}")
else:
    print("✓ No duplicate functions")

# Key features present?
checks = [
    ('submitFeedback', 'Feedback submission'),
    ('feedback-btn', 'Feedback buttons'),
    ('/chat/ask', 'Chat endpoint'),
    ('sendMessage', 'Send message function'),
    ('addMessage', 'Add message function'),
]
for pattern, label in checks:
    count = html.count(pattern)
    status = '✓' if count > 0 else '✗'
    print(f"  {status} {label}: {count} occurrences")

# Check script tag count
scripts = html.count('<script')
print(f"  Script tags: {scripts}")