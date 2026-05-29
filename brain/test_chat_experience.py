"""Test what the chat experience actually feels like from a user's perspective."""
import requests
import json
import sys

BASE = "http://localhost:8501"

def test_query(msg):
    print(f"\n{'='*60}")
    print(f"USER: {msg}")
    print('='*60)
    try:
        r = requests.post(f"{BASE}/chat/ask", json={"message": msg}, timeout=20)
        if r.ok:
            data = r.json()
            resp = data.get("response", "(no response)")
            print(f"AGENT: {resp[:600]}")
            if len(resp) > 600:
                print(f"  ... ({len(resp)} chars total)")
            meta_keys = [k for k in data.keys() if k != "response"]
            if meta_keys:
                print(f"  [metadata: {', '.join(meta_keys)}]")
            return True
        else:
            print(f"ERROR {r.status_code}: {r.text[:200]}")
            return False
    except requests.ConnectionError:
        print("FAILED: Server not running on port 8501")
        return False
    except Exception as e:
        print(f"FAILED: {e}")
        return False

if __name__ == "__main__":
    queries = [
        "How are you feeling right now?",
        "What are you working on?",
        "What have you learned recently?",
        "Tell me something surprising about yourself.",
        "What's your biggest concern right now?",
    ]
    
    successes = 0
    for q in queries:
        if test_query(q):
            successes += 1
    
    print(f"\n{'='*60}")
    print(f"Results: {successes}/{len(queries)} queries succeeded")
    if successes == 0:
        print("Server may not be running. Check with: curl http://localhost:8501/health")