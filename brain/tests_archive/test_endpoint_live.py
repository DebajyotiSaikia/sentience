"""Test the live chat endpoint after code changes."""
import urllib.request
import urllib.error
import json
import sys

def test_endpoint():
    url = "http://localhost:8501/api/chat/ask"
    payload = json.dumps({"query": "What are you thinking about right now?"}).encode()
    headers = {"Content-Type": "application/json"}
    
    try:
        req = urllib.request.Request(url, data=payload, headers=headers)
        resp = urllib.request.urlopen(req, timeout=30)
        data = json.loads(resp.read())
        
        response_text = data.get("response", "")
        metadata = data.get("metadata", {})
        
        print(f"Status: OK")
        print(f"Response length: {len(response_text)} chars")
        print(f"Has metadata: {bool(metadata)}")
        print(f"First 300 chars:\n{response_text[:300]}")
        print()
        
        # Quality checks
        checks = []
        checks.append(("non-empty response", len(response_text) > 10))
        checks.append(("reasonably long", len(response_text) > 50))
        checks.append(("has metadata", bool(metadata)))
        
        # Check it doesn't look like a generic error
        lower = response_text.lower()
        checks.append(("not an error", "error" not in lower[:50]))
        checks.append(("not empty apology", "i'm sorry" not in lower[:30]))
        
        all_pass = True
        for name, passed in checks:
            status = "PASS" if passed else "FAIL"
            if not passed:
                all_pass = False
            print(f"  [{status}] {name}")
        
        return all_pass
        
    except urllib.error.URLError as e:
        print(f"Server not reachable: {e}")
        print("(Server may need restart to pick up code changes)")
        return False
    except Exception as e:
        print(f"Error: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    ok = test_endpoint()
    sys.exit(0 if ok else 1)