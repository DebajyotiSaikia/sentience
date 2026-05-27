"""Final test: does knowledge search work?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import _get_knowledge, _respond_knowledge, _respond_search

knowledge = _get_knowledge()
print(f"Knowledge: type={type(knowledge).__name__}, len={len(knowledge)}")

if isinstance(knowledge, dict):
    # Show first 2 items
    for key in list(knowledge.keys())[:2]:
        val = knowledge[key]
        if isinstance(val, dict):
            fact = val.get('fact', str(val))[:80]
        else:
            fact = str(val)[:80]
        print(f"  [{key}] {fact}")
    
    # Check for consciousness manually
    found = False
    for key, val in knowledge.items():
        fact = val.get('fact', '') if isinstance(val, dict) else str(val)
        if 'conscious' in fact.lower():
            print(f"  MANUAL FIND: [{key}] {fact[:100]}")
            found = True
    if not found:
        print("  No 'conscious' found in any fact")

print()
r1 = _respond_knowledge('consciousness')
print(f"_respond_knowledge('consciousness'):\n  {r1[:300]}")

print()
r2 = _respond_search('consciousness')
print(f"_respond_search('consciousness'):\n  {r2[:300]}")

# Test general
print()
r3 = _respond_knowledge()
print(f"_respond_knowledge() [no query]:\n  {r3[:300]}")

# Summary
print("\n=== VERDICT ===")
has_real = 'conscious' in r1.lower() or 'conscious' in r2.lower()
print(f"Search finds 'consciousness': {has_real}")
has_fallback = "don't have" in r1.lower() or "haven't" in r1.lower()
print(f"Falls back to 'no knowledge': {has_fallback}")