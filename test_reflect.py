"""Test for web/reflect.py — verifying search, tokenization, and reflection capabilities."""
import sys
sys.path.insert(0, '/workspace')

from web.reflect import (
    tokenize, relevance_score, temporal_weight,
    search_facts, search_memories, extract_mood,
    extract_salience, extract_timestamp, confidence_estimate
)

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        passed += 1
        print(f"  ✓ {name}")
    else:
        failed += 1
        print(f"  ✗ {name}")

print("=== reflect.py unit tests ===\n")

# Tokenization
tokens = tokenize("Hello world, this is a test!")
test("tokenize returns list", isinstance(tokens, list))
test("tokenize lowercases", all(t == t.lower() for t in tokens))
test("tokenize splits words", len(tokens) >= 3)

# Relevance score
score = relevance_score("curiosity drives growth", "curiosity")
test("relevance_score returns float", isinstance(score, float))
test("relevance_score > 0 for match", score > 0)
score_miss = relevance_score("nothing related here", "xyzzyplugh")
test("relevance_score low for mismatch", score_miss < score)

# Temporal weight
from datetime import datetime, timezone
now = datetime.now(timezone.utc)
recent_weight = temporal_weight(now.isoformat())
test("temporal_weight returns float", isinstance(recent_weight, float))
test("temporal_weight > 0 for recent", recent_weight > 0)

# Extract helpers
test_mem = "(salience=0.85, mood=Curious) Something happened"
mood = extract_mood(test_mem)
test("extract_mood finds mood", mood is not None)
sal = extract_salience(test_mem)
test("extract_salience finds value", sal is not None)

# Confidence estimate
conf = confidence_estimate(["fact one", "fact two"], "test query", [now.isoformat(), now.isoformat()])
test("confidence_estimate returns float", isinstance(conf, float))
test("confidence_estimate in [0,1]", 0.0 <= conf <= 1.0)

print(f"\n{'='*30}")
print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
if failed == 0:
    print("All tests passed! ✓")
else:
    print(f"{failed} test(s) need attention.")
    sys.exit(1)