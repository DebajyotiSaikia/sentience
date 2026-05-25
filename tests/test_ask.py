"""Test the /ask endpoint end-to-end."""
from web.app import create_app
import re

app = create_app()
client = app.test_client()

# Test POST with a question
r = client.post('/ask', data={'question': 'What do you know about yourself?'}, follow_redirects=True)
print(f'POST Status: {r.status_code}')
print(f'Response length: {len(r.data)}')

text = r.data.decode('utf-8', errors='replace')

# Check for errors
if 'error' in text.lower():
    errors = re.findall(r'.{0,100}error.{0,100}', text, re.IGNORECASE)
    for e in errors[:3]:
        print(f'Error context: {e.strip()}')

# Check for answer/response content
if 'answer' in text.lower() or 'response' in text.lower():
    print('Found answer/response content')
    # Extract answer area
    answers = re.findall(r'<div[^>]*class=["\'][^"\']*(?:result|answer|response)[^"\']*["\'][^>]*>(.*?)</div>', text, re.DOTALL | re.IGNORECASE)
    print(f'Answer divs: {len(answers)}')
    for a in answers[:2]:
        print(f'  Content: {a[:300].strip()}')
else:
    print('No answer content found in response')

# Also look for any flash messages
flashes = re.findall(r'<div[^>]*class=["\'][^"\']*flash[^"\']*["\'][^>]*>(.*?)</div>', text, re.DOTALL | re.IGNORECASE)
if flashes:
    print(f'Flash messages: {len(flashes)}')
    for f in flashes:
        print(f'  Flash: {f[:200].strip()}')

# Look for the main content area
main = re.findall(r'<div[^>]*class=["\'][^"\']*(?:chat|message|reply)[^"\']*["\'][^>]*>(.*?)</div>', text, re.DOTALL | re.IGNORECASE)
if main:
    print(f'Chat/message divs: {len(main)}')
    for m in main[:3]:
        clean = re.sub(r'<[^>]+>', '', m).strip()
        if clean:
            print(f'  Message: {clean[:200]}')

# Dump a section of the HTML to understand structure
print('\n--- Key HTML snippet ---')
# Find the form or response area
form_area = text.find('<form')
if form_area > 0:
    print(text[form_area:form_area+500])