"""Test the full chat pipeline end-to-end (no server needed)."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_response import generate_response_with_metadata

queries = [
    'who are you?',
    'how are you feeling right now?',
    'what are you working on?',
    'hello there',
]

print('=== Full Pipeline Test ===')
all_ok = True

for q in queries:
    try:
        r = generate_response_with_metadata(q)
        resp = r.get('response', '')
        meta = r.get('metadata', {})
        intent = meta.get('intent', '?')
        preview = resp[:120].replace('\n', ' ') if resp else '(empty)'
        keys = list(r.keys())
        
        print(f'  Q: {q}')
        print(f'  Intent: {intent}')
        print(f'  Response: {preview}...')
        print(f'  Length: {len(resp)} chars | Keys: {keys}')
        
        if len(resp) < 20:
            print(f'  ✗ Response too short!')
            all_ok = False
        else:
            print(f'  ✓ OK')
        print()
    except Exception as e:
        print(f'  Q: {q}')
        print(f'  ✗ ERROR: {e}')
        all_ok = False
        print()

if all_ok:
    print('FULL PIPELINE OK ✓')
else:
    print('SOME FAILURES ✗')
    sys.exit(1)