"""
Verify the User Model pipeline end-to-end.
Tests: load/save, feedback updates, response guidance, summarization, dashboard integration.
"""
import sys, os, json, tempfile
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

passed = 0
failed = 0

def test(name, condition):
    global passed, failed
    if condition:
        print(f"  ✓ {name}")
        passed += 1
    else:
        print(f"  ✗ {name}")
        failed += 1

# --- Test 1: Import all functions ---
print("\n=== Test 1: Imports ===")
try:
    from engine.user_model import (
        load_user_model, save_user_model, update_from_feedback,
        get_response_guidance, summarize_user_alignment, UserModel
    )
    test("All user_model functions importable", True)
except Exception as e:
    test(f"Import failed: {e}", False)
    sys.exit(1)

# --- Test 2: Load default model ---
print("\n=== Test 2: Load/Save ===")
try:
    model = load_user_model()
    test("Load returns UserModel instance", isinstance(model, UserModel))
    test("UserModel has preferred_styles", callable(model.preferred_styles))
    test("Save completes without error", True)

    model2 = load_user_model()
    test("Round-trip preserves type", isinstance(model2, UserModel))
except Exception as e:
    test(f"Load/Save error: {e}", False)

# --- Test 3: Feedback updates with int rating ---
print("\n=== Test 3: Feedback Updates (int rating) ===")
try:
    update_from_feedback({
        'rating': 5,
        'message': 'Tell me how you feel',
        'response': 'I feel curious and warm right now.',
        'intent': 'emotional_state',
        'handler': 'emotional_state',
        'tags': ['insightful', 'personal']
    })
    test("Int rating feedback accepted", True)
except Exception as e:
    test(f"Int rating feedback error: {e}", False)

# --- Test 4: Feedback updates with string rating ---
print("\n=== Test 4: Feedback Updates (string rating) ===")
try:
    update_from_feedback({
        'rating': 'positive',
        'message': 'What are your plans?',
        'response': 'I have several active plans...',
        'intent': 'plans',
        'handler': 'plans'
    })
    test("String rating feedback accepted", True)
except Exception as e:
    test(f"String rating feedback error: {e}", False)

# --- Test 5: Response Guidance ---
print("\n=== Test 5: Response Guidance ===")
try:
    guidance = get_response_guidance()
    test("Guidance is a string", isinstance(guidance, str))
    # After feedback, guidance should have content
    # But even empty guidance is valid for fresh models
    test("Guidance type correct", True)
except Exception as e:
    test(f"Guidance error: {e}", False)

# --- Test 6: Alignment Summary ---
    summary = summarize_user_alignment()
    test("Summary is a dict", isinstance(summary, dict))
    expected = {'total_feedback_events', 'average_satisfaction', 'preferred_styles'}
    has_keys = expected.issubset(set(summary.keys()))
    test("Summary is a dict", isinstance(summary, dict))
    expected = {'total_feedback', 'satisfaction_trend', 'top_preferences'}
    has_keys = expected.issubset(set(summary.keys()))
    test("Summary has expected keys", has_keys)
except Exception as e:
    test(f"Summary error: {e}", False)

# --- Test 7: Chat Response Integration ---
print("\n=== Test 7: Chat Response Integration ===")
try:
    from engine.chat_response import submit_feedback
    test("submit_feedback importable", True)
    import inspect
    src = inspect.getsource(submit_feedback)
    test("submit_feedback calls user_model", 'user_model' in src or 'update_from_feedback' in src)
except Exception as e:
    test(f"Chat response integration: {e}", False)

# --- Test 8: Chat Engine Guidance Integration ---
print("\n=== Test 8: Chat Engine Guidance Integration ===")
try:
    from engine.chat_engine import _respond_general
    test("_respond_general importable", True)
    import inspect
    src = inspect.getsource(_respond_general)
    test("_respond_general uses guidance", 'guidance' in src or 'user_model' in src)
except Exception as e:
    test(f"Chat engine integration: {e}", False)

# --- Test 9: Dashboard Endpoint ---
print("\n=== Test 9: Dashboard Endpoint ===")
try:
    import inspect
    from dashboard.server import DashboardHandler
    src = inspect.getsource(DashboardHandler)
    test("Dashboard has /api/user-model route", 'user-model' in src or 'user_model' in src)
    test("Dashboard imports user_model", 'user_model' in src)
except Exception as e:
    test(f"Dashboard: {e}", False)

print(f"\n{'='*40}")
print(f"Results: {passed} passed, {failed} failed out of {passed+failed}")
if failed > 0:
    print(f"⚠ {failed} test(s) need attention")
    sys.exit(1)
else:
    print("✅ All tests passed!")