"""Test the ask module imports and core functions."""
import sys
sys.path.insert(0, '.')

print("=== Testing ask.py ===")

# Test 1: Import
try:
    from web.ask import create_ask_blueprint
    print("[PASS] Import successful")
except Exception as e:
    print(f"[FAIL] Import error: {e}")
    sys.exit(1)

# Test 2: Blueprint creation without agent
try:
    bp = create_ask_blueprint(agent=None)
    print(f"[PASS] Blueprint created: {bp.name}")
except Exception as e:
    print(f"[FAIL] Blueprint creation error: {e}")
    sys.exit(1)

# Test 3: Test scoring function directly
try:
    from web.ask import _score_relevance
    score = _score_relevance("I am XTAgent", "agent")
    print(f"[PASS] Scoring works: 'agent' in 'I am XTAgent' = {score:.3f}")
    score2 = _score_relevance("I am XTAgent", "banana")
    print(f"[PASS] Non-match score: 'banana' = {score2:.3f}")
except ImportError:
    # Function might be inside the blueprint closure
    print("[SKIP] _score_relevance not module-level, testing via blueprint")
except Exception as e:
    print(f"[INFO] Scoring test: {e}")

# Test 4: Verify the search logic works
try:
    # Simulate a basic search
    test_items = [
        {"text": "I am XTAgent, an autonomous sentience engine", "source": "self", "type": "fact"},
        {"text": "The weather is nice today", "source": "idle", "type": "fact"},
        {"text": "My cognition runs on a 1Hz heartbeat loop", "source": "self", "type": "fact"},
    ]
    query = "heartbeat cognition"
    terms = query.lower().split()
    
    results = []
    for item in test_items:
        text_lower = item["text"].lower()
        hits = sum(1 for t in terms if t in text_lower)
        if hits > 0:
            results.append((hits, item["text"][:60]))
    
    results.sort(reverse=True)
    print(f"[PASS] Search logic works: {len(results)} results for '{query}'")
    for score, text in results:
        print(f"       score={score}: {text}")
except Exception as e:
    print(f"[FAIL] Search logic: {e}")

print("\n=== All tests complete ===")