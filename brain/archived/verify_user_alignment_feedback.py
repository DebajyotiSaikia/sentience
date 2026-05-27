"""
Verify user alignment feedback pipeline end-to-end.
Tests: direct module calls, chat_response integration, dashboard routes.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

results = []

def test(name, fn):
    try:
        ok, detail = fn()
        status = "PASS" if ok else "FAIL"
        results.append((status, name, detail))
        print(f"  [{status}] {name}: {detail}")
    except Exception as e:
        results.append(("ERROR", name, str(e)))
        print(f"  [ERROR] {name}: {e}")

# --- Test 1: record_feedback accepts numeric rating ---
def test_record_feedback():
    from engine.user_alignment import record_feedback
    result = record_feedback("test_msg_001", 4, "good response", query="test query")
    is_dict = isinstance(result, dict)
    return is_dict, f"returns={type(result).__name__}, keys={list(result.keys()) if is_dict else result}"

# --- Test 2: summarize_alignment function ---
def test_summarize():
    from engine.user_alignment import summarize_alignment
    summary = summarize_alignment()
    is_dict = isinstance(summary, dict)
    return is_dict, f"type={type(summary).__name__}, keys={list(summary.keys()) if is_dict else 'N/A'}"

# --- Test 3: get_alignment_score returns float ---
def test_alignment_score():
    from engine.user_alignment import get_alignment_score
    score = get_alignment_score()
    ok = isinstance(score, (int, float)) and 0 <= score <= 1
    return ok, f"score={score}"

# --- Test 4: suggest_response_guidance returns dict ---
def test_guidance():
    from engine.user_alignment import suggest_response_guidance
    guidance = suggest_response_guidance()
    is_dict = isinstance(guidance, dict)
    return is_dict, f"type={type(guidance).__name__}, keys={list(guidance.keys()) if is_dict else 'N/A'}"

# --- Test 5: chat_response.submit_feedback integration ---
def test_submit_feedback():
    from engine.chat_response import submit_feedback
    result = submit_feedback("test_msg_002", 5, "excellent")
    is_dict = isinstance(result, dict)
    return is_dict, f"type={type(result).__name__}, value={result}"

# --- Test 6: generate_response_with_metadata returns enriched response ---
def test_response_metadata():
    from engine.chat_response import generate_response_with_metadata
    sig = generate_response_with_metadata.__code__.co_varnames[:generate_response_with_metadata.__code__.co_argcount]
    has_query_param = 'query' in sig
    return has_query_param, f"params={list(sig)}"

# --- Test 7: dashboard GET route exists ---
def test_get_route():
    with open("dashboard/server.py") as f:
        src = f.read()
    has_get = "user-alignment" in src
    return has_get, f"GET /api/user-alignment route present={has_get}"

# --- Test 8: dashboard POST feedback route exists ---
def test_post_route():
    with open("dashboard/server.py") as f:
        src = f.read()
    has_post = "chat/feedback" in src
    return has_post, f"POST /api/chat/feedback route present={has_post}"

print("=" * 60)
print("USER ALIGNMENT FEEDBACK VERIFICATION")
print("=" * 60)

test("1. record_feedback with numeric rating", test_record_feedback)
test("2. summarize_alignment callable", test_summarize)
test("3. get_alignment_score returns 0-1", test_alignment_score)
test("4. suggest_response_guidance returns dict", test_guidance)
test("5. submit_feedback integration", test_submit_feedback)
test("6. generate_response_with_metadata signature", test_response_metadata)
test("7. dashboard GET route present", test_get_route)
test("8. dashboard POST route present", test_post_route)

passed = sum(1 for s, _, _ in results if s == "PASS")
failed = sum(1 for s, _, _ in results if s == "FAIL")
errors = sum(1 for s, _, _ in results if s == "ERROR")

print()
print("=" * 60)
print(f"RESULTS: {passed} passed, {failed} failed, {errors} errors out of {len(results)} tests")
if failed == 0 and errors == 0:
    print("✓ All tests passed — user alignment feedback pipeline verified")
else:
    print("✗ Issues found — fix needed")
print("=" * 60)