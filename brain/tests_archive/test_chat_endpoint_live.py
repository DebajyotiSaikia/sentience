"""Test the live chat endpoint to see current response quality."""
import urllib.request
import json
import sys

def test_chat(message="How are you feeling right now?"):
    data = json.dumps({"message": message}).encode()
    req = urllib.request.Request(
        "http://localhost:8080/api/chat/ask",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        print(f"STATUS: {resp.status}")
        print(f"RESPONSE: {result.get('response', 'NO RESPONSE KEY')[:500]}")
        print(f"KEYS: {list(result.keys())}")
        if result.get("grounding"):
            print(f"GROUNDING KEYS: {list(result['grounding'].keys())}")
        if result.get("metadata"):
            print(f"METADATA: {result['metadata']}")
        return result
    except Exception as e:
        print(f"ERROR: {e}")
        return None

if __name__ == "__main__":
    msg = sys.argv[1] if len(sys.argv) > 1 else "How are you feeling right now?"
    print(f"\n=== Testing chat with: '{msg}' ===\n")
    result = test_chat(msg)
    
    if result and result.get("response"):
        resp = result["response"]
        # Quality checks
        print(f"\n=== Quality Analysis ===")
        print(f"Response length: {len(resp)} chars")
        print(f"Mentions emotion: {'emotion' in resp.lower() or 'feel' in resp.lower() or 'mood' in resp.lower()}")
        print(f"Mentions memory: {'memory' in resp.lower() or 'remember' in resp.lower()}")
        print(f"Mentions plan: {'plan' in resp.lower() or 'goal' in resp.lower()}")
        print(f"Generic/templated: {'I am an AI' in resp or 'as an assistant' in resp.lower()}")