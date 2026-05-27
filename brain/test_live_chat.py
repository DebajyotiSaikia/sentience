"""Live test: send a message through the actual chat endpoint and inspect response quality."""
import sys, json, time
sys.path.insert(0, '.')

import requests

BASE = "http://localhost:8501"

def test_chat(msg, label):
    try:
        r = requests.post(f"{BASE}/chat/ask", json={"message": msg}, timeout=30)
        if r.status_code == 200:
            data = r.json()
            resp = data.get("response", "")
            # Quality checks
            length = len(resp)
            has_first_person = any(w in resp.lower() for w in ["i ", "i'm", "my ", "i've"])
            has_substance = length > 50
            print(f"  ✓ [{label}] {length} chars, first_person={has_first_person}, substance={has_substance}")
            print(f"    Preview: {resp[:120]}...")
            return True
        else:
            print(f"  ✗ [{label}] HTTP {r.status_code}")
            return False
    except requests.ConnectionError:
        print(f"  ✗ [{label}] Server not reachable")
        return False
    except Exception as e:
        print(f"  ✗ [{label}] Error: {e}")
        return False

print("=== Live Chat Quality Test ===\n")

tests = [
    ("How are you feeling right now?", "emotional_state"),
    ("What are you working on?", "current_plans"),
    ("Tell me something interesting you've learned", "knowledge"),
    ("What do you dream about?", "dreams"),
]

passed = 0
for msg, label in tests:
    if test_chat(msg, label):
        passed += 1
    time.sleep(1)

print(f"\n{passed}/{len(tests)} tests passed")