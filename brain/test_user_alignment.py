"""Test user_alignment module against its actual API."""
import sys, os, json, tempfile
from pathlib import Path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Runtime-verified exports: load_profile, save_profile, record_feedback,
# get_alignment_context, format_alignment_context, extract_preferences,
# apply_preferences, DATA_PATH
from engine.user_alignment import (
    load_profile, save_profile, record_feedback,
    get_alignment_context, format_alignment_context,
    extract_preferences, apply_preferences, DATA_PATH
)
import engine.user_alignment as ua

# Use a temp file for testing
TEMP_PATH = Path(tempfile.gettempdir()) / "test_user_alignment.json"
original_path = ua.DATA_PATH
ua.DATA_PATH = TEMP_PATH

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

try:
    # Clean start
    if TEMP_PATH.exists():
        TEMP_PATH.unlink()

    # 1. Load empty profile
    p = load_profile()
    test("load_profile returns dict", isinstance(p, dict))

    # 2. Record feedback
    result = record_feedback("Hello there", "Hi! How can I help?", rating=0.9, comment="friendly")
    test("record_feedback returns something", result is not None)

    # 3. Load profile again - should have feedback
    p2 = load_profile()
    has_feedback = "feedback" in p2 and len(p2["feedback"]) >= 1
    test("feedback persisted in profile", has_feedback)

    # 4. Record more feedback to build history
    record_feedback("Explain X", "X is a concept...", rating=0.3, comment="too brief")
    record_feedback("Tell me about Y", "Y is fascinating because...", rating=0.8)

    # 5. Get alignment context
    ctx = get_alignment_context()
    test("get_alignment_context returns dict", isinstance(ctx, dict))

    # 6. Format alignment context
    formatted = format_alignment_context(ctx)
    test("format_alignment_context returns string", isinstance(formatted, str))
    test("formatted context is non-empty", len(formatted) > 0)

    # 7. Extract preferences from text
    prefs = extract_preferences("I prefer detailed explanations with examples")
    test("extract_preferences returns something", prefs is not None)

    # 8. Apply preferences
    result = apply_preferences("I prefer detailed explanations with examples")
    test("apply_preferences runs without error", True)

    # 9. Save and reload profile
    profile = load_profile()
    profile["test_marker"] = "alive"
    save_profile(profile)
    reloaded = load_profile()
    test("save/load round-trip works", reloaded.get("test_marker") == "alive")

    # 10. Feedback count
    p3 = load_profile()
    fb_count = len(p3.get("feedback", []))
    test("multiple feedbacks accumulated", fb_count >= 3)

    # Summary
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed out of {passed + failed}")
    if failed == 0:
        print("ALL TESTS PASSED ✓")
    else:
        print("SOME TESTS FAILED ✗")
        sys.exit(1)

finally:
    # Restore original path and clean up
    ua.DATA_PATH = original_path
    if TEMP_PATH.exists():
        TEMP_PATH.unlink()