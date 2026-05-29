"""Test that chat grounding integrates lessons, user model, and long-term memory."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_grounding import build_grounded_context

def test(name, condition, detail=""):
    status = "PASS" if condition else "FAIL"
    msg = f"  [{status}] {name}"
    if not condition and detail:
        msg += f"\n         → {detail}"
    print(msg)
    return condition

print("=" * 50)
print("Chat Grounding Integration Tests")
print("=" * 50)

ctx = build_grounded_context("What are you thinking about?")
sp = ctx.get("system_prompt", "")
passed = 0
total = 0

# Test 1: Lessons in prompt
total += 1
if test("Lessons in prompt", "Lessons" in sp or "lessons" in sp.lower() or "learned" in sp.lower(),
        "No lessons section found in system prompt"):
    passed += 1

# Test 2: Emotional state
total += 1
if test("Emotional state", "emotional_state" in ctx and ctx["emotional_state"],
        "Missing emotional_state in context"):
    passed += 1

# Test 3: Identity
total += 1
if test("Identity", "XTAgent" in sp, "XTAgent not found in system prompt"):
    passed += 1

# Test 4: Plans in plan query
total += 1
plan_ctx = build_grounded_context("What are your current plans?")
plan_sp = plan_ctx.get("system_prompt", "")
if test("Plans in plan query", "plan" in plan_sp.lower() or "plans" in ctx,
        "No plans found in plan-related query context"):
    passed += 1

# Test 5: Essential context keys
total += 1
required = ["system_prompt", "emotional_state", "query_type"]
missing = [k for k in required if k not in ctx]
if test("Essential context keys", len(missing) == 0,
        f"Missing keys: {missing}"):
    passed += 1

# Test 6: Long-term memory context
total += 1
has_ltm = ("long_term" in sp.lower() or "lessons" in sp.lower() or
           "learned" in sp.lower() or "insight" in sp.lower() or
           "dream" in sp.lower())
if test("Long-term memory context", has_ltm,
        "No long-term memory content in prompt"):
    passed += 1

# Test 7: Query classified
total += 1
if test("Query classified", "query_type" in ctx and ctx["query_type"],
        f"query_type missing or empty: {ctx.get('query_type')}"):
    passed += 1

# Test 8: User model guidance loads
total += 1
try:
    from engine.user_model import get_response_guidance
    guidance = get_response_guidance()
    if test("User model guidance loads", guidance is not None,
            "get_response_guidance() returned None"):
        passed += 1
except Exception as e:
    test("User model guidance loads", False, str(e))

# Test 9: User preferences section in prompt (if guidance has data)
total += 1
try:
    from engine.user_model import get_response_guidance
    guidance = get_response_guidance()
    has_prefs = "User Preferences" in sp or "Preference" in sp or "prefer" in sp.lower()
    # guidance is a string — if non-empty, user model has data
    if guidance and len(str(guidance).strip()) > 10:
        if test("User preferences in prompt", has_prefs,
                "User model has data but preferences not in prompt"):
            passed += 1
    else:
        if test("User preferences (no data yet - OK)", True):
            passed += 1
except Exception as e:
    test("User preferences section", False, str(e))

# Test 10: All query types produce valid context
total += 1
query_types_ok = True
for q in ["Tell me about yourself", "How do emotions work?", "What plans do you have?"]:
    try:
        c = build_grounded_context(q)
        if "system_prompt" not in c:
            query_types_ok = False
    except Exception:
        query_types_ok = False
if test("All query types produce valid context", query_types_ok):
    passed += 1

# Summary
print(f"\n{passed}/{total} passed\n")
print(f"System prompt length: {len(sp)} chars")
print(f"Context keys: {sorted(ctx.keys())}")
print(f"\n--- Prompt preview (first 400 chars) ---")
print(sp[:400])
print("...\n")

if passed < total:
    print(f"\u2717 {total - passed} test(s) failed")
    sys.exit(1)
else:
    print("\u2713 All tests passed!")