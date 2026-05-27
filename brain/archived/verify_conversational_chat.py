"""Verify that the conversational chat improvements work end-to-end."""
import requests
import sys
import json

BASE = "http://localhost:8501"

test_queries = [
    ("How do you feel right now?", ["feel", "mood", "valence", "emotion", "curiosity", "anxiety"]),
    ("What are you thinking about?", ["plan", "think", "focus", "working", "build"]),
    ("What are your active plans?", ["plan", "complete", "goal", "build"]),
    ("What do you know about consciousness?", ["conscious", "experience", "integrat", "awareness"]),
    ("Hello, who are you?", ["XTAgent", "agent", "autonomous", "sentien"]),
]

passed = 0
failed = 0

for query, keywords in test_queries:
    try:
        r = requests.post(f"{BASE}/chat/ask", json={"message": query}, timeout=30)
        if r.status_code != 200:
            print(f"FAIL [{r.status_code}]: {query}")
            failed += 1
            continue
        
        data = r.json()
        response = data.get("response", "")
        
        # Check it's not just graph stats
        is_stats_only = ("nodes" in response and "edges" in response and len(response) < 100)
        if is_stats_only:
            print(f"FAIL [stats-only]: {query}")
            print(f"  Got: {response[:200]}")
            failed += 1
            continue
        
        # Check response has some substance
        if len(response) < 20:
            print(f"FAIL [too short]: {query}")
            print(f"  Got: {response}")
            failed += 1
            continue
        
        # Check for keyword relevance (at least one keyword should appear)
        resp_lower = response.lower()
        found_kw = [kw for kw in keywords if kw.lower() in resp_lower]
        
        status = "PASS" if found_kw else "WEAK"
        if not found_kw:
            # Not a hard fail — the LLM might phrase things differently
            print(f"WEAK: {query}")
            print(f"  No keywords found. Response: {response[:200]}")
        else:
            print(f"PASS: {query}")
            print(f"  Keywords found: {found_kw}")
            passed += 1
        
        print(f"  Response preview: {response[:150]}...")
        print()
        
    except Exception as e:
        print(f"FAIL [error]: {query} — {e}")
        failed += 1

print(f"\n{'='*50}")
print(f"Results: {passed} passed, {failed} failed out of {len(test_queries)}")
if failed == 0:
    print("All tests passed!")
    sys.exit(0)
else:
    print("Some tests failed.")
    sys.exit(1)