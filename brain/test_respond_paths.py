"""Test that respond() returns genuine, grounded responses for different query types."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from engine.smart_responder import respond

tests = [
    ("What are you thinking about?", "thinking"),
    ("How do you feel right now?", "emotional"),
    ("Who are you?", "identity"),
    ("What can you do?", "capabilities"),
    ("Tell me about your dreams", "dreams"),
    ("What do you remember?", "memories"),
    ("Hello there", "general"),
]

passed = 0
failed = 0

for query, label in tests:
    r = respond(query)
    preview = r[:150].replace("\n", " ")
    length = len(r)
    
    # Basic quality checks
    issues = []
    if length < 50:
        issues.append(f"too short ({length} chars)")
    if "knowledge nodes" in r.lower() and "edges" in r.lower():
        issues.append("contains graph stats dump")
    if r.strip().startswith("{") or r.strip().startswith("["):
        issues.append("raw JSON instead of natural language")
    
    status = "FAIL" if issues else "PASS"
    if issues:
        failed += 1
    else:
        passed += 1
    
    print(f"[{status}] {label}: {query}")
    print(f"  Response ({length} chars): {preview}...")
    if issues:
        print(f"  Issues: {', '.join(issues)}")
    print()

print(f"Results: {passed}/{passed+failed} passed")
if failed:
    print("SOME TESTS FAILED")
else:
    print("ALL TESTS PASSED")