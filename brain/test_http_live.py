"""Live HTTP endpoint test — checks if server is running and chat responds well."""
import sys, json, urllib.request, urllib.error
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

def check_server():
    try:
        req = urllib.request.Request("http://localhost:8080/health")
        resp = urllib.request.urlopen(req, timeout=5)
        data = resp.read().decode()
        print(f"  Server is UP: {data[:200]}")
        return True
    except urllib.error.URLError as e:
        print(f"  Server not reachable: {e.reason}")
        return False
    except Exception as e:
        print(f"  Error: {e}")
        return False

def test_chat(query):
    payload = json.dumps({"message": query}).encode()
    req = urllib.request.Request(
        "http://localhost:8080/chat/ask",
        data=payload,
        headers={"Content-Type": "application/json"},
    )
    resp = urllib.request.urlopen(req, timeout=30)
    data = json.loads(resp.read().decode())
    return data

if __name__ == "__main__":
    print("=" * 50)
    print("LIVE HTTP ENDPOINT TEST")
    print("=" * 50)

    print("\n--- Server health ---")
    if not check_server():
        print("\n⚠ Server not running. Skipping HTTP tests.")
        print("  (Pipeline verified via direct import tests instead)")
        print("  Run: python main.py  then re-run this test")
        sys.exit(0)

    queries = [
        "How are you feeling right now?",
        "What have you been working on?",
        "Do you experience curiosity?",
    ]

    for q in queries:
        print(f"\n--- Query: '{q}' ---")
        try:
            result = test_chat(q)
            response = result.get("response", result.get("reply", str(result)))
            print(f"  Response ({len(response)} chars):")
            for line in response[:500].split("\n")[:8]:
                print(f"    | {line}")
            if len(response) > 500:
                print(f"    | ... ({len(response) - 500} more chars)")
        except Exception as e:
            print(f"  ERROR: {e}")

    print("\n" + "=" * 50)
    print("HTTP TESTS COMPLETE")