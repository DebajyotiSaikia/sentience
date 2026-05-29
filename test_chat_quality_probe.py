"""Probe chat endpoint quality — what does it actually return?"""
import requests
import json

BASE = 'http://localhost:8501'

queries = [
    'How are you feeling right now?',
    'What have you been working on lately?',
    'Tell me something surprising about yourself',
    'What are you curious about?',
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print('='*60)
    try:
        r = requests.post(f'{BASE}/chat/ask', json={'message': q}, timeout=30)
        data = r.json()
        print(f"STATUS: {r.status_code}")
        resp = data.get('response', 'NO RESPONSE KEY')
        print(f"\nRESPONSE ({len(resp)} chars):")
        print(resp[:1000])
        meta = data.get('metadata', {})
        if meta:
            print(f"\nMETADATA:")
            for k, v in meta.items():
                val_str = str(v)
                if len(val_str) > 200:
                    val_str = val_str[:200] + '...'
                print(f"  {k}: {val_str}")
    except Exception as e:
        print(f"ERROR: {e}")

print(f"\n{'='*60}")
print("DONE")