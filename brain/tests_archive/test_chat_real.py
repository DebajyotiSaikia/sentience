"""Quick test: make a real chat request and inspect the response."""
import urllib.request, json, sys

def ask(message):
    data = json.dumps({"message": message}).encode()
    req = urllib.request.Request(
        "http://localhost:8501/chat/ask",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read())
        return result
    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    queries = [
        "How are you feeling right now?",
        "What are you working on?",
        "What have you learned recently?",
    ]
    
    for q in queries:
        print(f"\n{'='*60}")
        print(f"Q: {q}")
        print(f"{'='*60}")
        result = ask(q)
        if "error" in result:
            print(f"ERROR: {result['error']}")
            continue
        
        # Show the response text
        reply = result.get("response", result.get("reply", ""))
        if reply:
            print(f"A: {reply[:600]}")
        else:
            print(f"Keys: {list(result.keys())}")
            print(f"Raw: {json.dumps(result, indent=2)[:600]}")
        print()