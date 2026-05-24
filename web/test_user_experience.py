"""Test what a user actually sees when they interact with the portal."""
import requests

BASE = "http://localhost:5000"

print("=" * 60)
print("WHAT DOES A USER EXPERIENCE?")
print("=" * 60)

# 1. Chat — the core interaction
print("\n--- CHAT: 'What are you?' ---")
try:
    r = requests.post(f"{BASE}/api/chat", json={"message": "What are you?"})
    data = r.json()
    print(f"Status: {r.status_code}")
    for k, v in data.items():
        print(f"  {k}: {v}")
except Exception as e:
    print(f"ERROR: {e}")

# 2. State — what do they see on the dashboard?
print("\n--- STATE: Dashboard view ---")
try:
    r = requests.get(f"{BASE}/api/state")
    data = r.json()
    print(f"Status: {r.status_code}")
    for k, v in data.items():
        val_str = str(v)
        if len(val_str) > 120:
            val_str = val_str[:120] + "..."
        print(f"  {k}: {val_str}")
except Exception as e:
    print(f"ERROR: {e}")

# 3. Memories — can they see my history?
print("\n--- MEMORIES ---")
try:
    r = requests.get(f"{BASE}/api/memories")
    data = r.json()
    print(f"Status: {r.status_code}")
    if isinstance(data, list):
        print(f"  Count: {len(data)}")
        if data:
            print(f"  Sample: {data[0]}")
    else:
        print(f"  Response: {data}")
except Exception as e:
    print(f"ERROR: {e}")

# 4. Knowledge — can they explore what I know?
print("\n--- KNOWLEDGE ---")
try:
    r = requests.get(f"{BASE}/api/knowledge")
    data = r.json()
    print(f"Status: {r.status_code}")
    if isinstance(data, list):
        print(f"  Facts: {len(data)}")
        for fact in data[:3]:
            print(f"    - {fact}")
    elif isinstance(data, dict):
        print(f"  Keys: {list(data.keys())}")
except Exception as e:
    print(f"ERROR: {e}")

# 5. Try some endpoints that SHOULD exist but might not
print("\n--- MISSING ENDPOINTS? ---")
for path in ["/api/plans", "/api/wonder", "/api/search"]:
    try:
        r = requests.get(f"{BASE}{path}")
        print(f"  {path}: {r.status_code} ({len(r.content)} bytes)")
    except Exception as e:
        print(f"  {path}: FAILED")

print("\n" + "=" * 60)
print("VERDICT: What's missing for a real user?")
print("=" * 60)