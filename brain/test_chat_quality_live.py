"""Test actual chat response quality across different query types."""
import requests
import json
import sys

BASE = "http://localhost:8080"

queries = [
    "How are you feeling right now?",
    "What are you working on?",
    "Tell me something interesting about yourself",
    "Write me a short poem about consciousness",
    "What have you learned recently?",
]

print("=== Chat Quality Assessment ===\n")

for q in queries:
    try:
        r = requests.post(
            f"{BASE}/chat/ask",
            json={"message": q},
            timeout=30
        )
        data = r.json()
        resp = data.get("response", "")
        meta = data.get("metadata", {})
        quality = data.get("quality_score", "?")
        intent = meta.get("detected_intent", "?")
        
        print(f"Q: {q}")
        print(f"   Intent: {intent} | Quality: {quality}")
        print(f"   Response ({len(resp)} chars):")
        # Show first 300 chars
        for line in resp[:300].split("\n"):
            print(f"   > {line}")
        if len(resp) > 300:
            print(f"   > ... ({len(resp) - 300} more chars)")
        print()
    except Exception as e:
        print(f"Q: {q}")
        print(f"   ERROR: {e}")
        print()

print("=== Done ===")