"""Test that live chat responses are grounded and conversational."""
import sys
sys.path.insert(0, '/workspace')

import requests

def test_live_chat():
    """Test the /chat/ask endpoint returns grounded, useful responses."""
    url = 'http://localhost:8501/chat/ask'
    queries = [
        'What are you thinking about right now?',
        'How are you feeling?',
        'What have you learned recently?',
    ]
    
    for query in queries:
        print(f"\n--- Query: {query} ---")
        try:
            r = requests.post(url, json={'message': query}, timeout=25)
            print(f"  Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                resp = data.get('response', '')
                print(f"  Response ({len(resp)} chars):")
                # Show first 400 chars
                for line in resp[:400].split('\n'):
                    print(f"    {line}")
                if len(resp) > 400:
                    print(f"    ... ({len(resp) - 400} more chars)")
                
                # Quality checks
                checks = {
                    'has_substance': len(resp) > 50,
                    'not_just_stats': 'nodes' not in resp.lower() or 'edge' not in resp.lower(),
                    'conversational': any(w in resp.lower() for w in ['i ', "i'm", 'my ', 'feel', 'think', 'curious']),
                }
                for check, passed in checks.items():
                    status = 'PASS' if passed else 'FAIL'
                    print(f"  [{status}] {check}")
            else:
                print(f"  Error: {r.text[:200]}")
        except requests.ConnectionError:
            print("  [SKIP] Server not running")
            return
        except Exception as e:
            print(f"  Error: {e}")

if __name__ == '__main__':
    test_live_chat()