"""
Verify User Model — end-to-end tests for user preference learning.
Tests: load, feedback recording, preference extraction, guidance generation, persistence.
"""
import sys, os, json, shutil

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

PASS = 0
FAIL = 0

def test(name, condition, detail=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ {name}")
    else:
        FAIL += 1
        print(f"  ✗ {name} — {detail}")

print("═══ User Model Verification ═══\n")

# --- Imports ---
try:
    from engine.user_model import (
        UserModel, load_user_model, save_user_model,
        update_from_feedback, get_response_guidance,
        summarize_user_alignment, StyleSignal
    )
    test("All imports succeed", True)
except ImportError as e:
    test("All imports succeed", False, str(e))
    sys.exit(1)

# --- Backup existing data ---
data_path = "data/user_model.json"
backup_path = None
if os.path.exists(data_path):
    backup_path = data_path + ".bak_test"
    shutil.copy2(data_path, backup_path)

try:
    # --- Load model ---
    model = load_user_model()
    test("load_user_model() returns UserModel", isinstance(model, UserModel))
    test("Model has preferred_styles method", callable(getattr(model, 'preferred_styles', None)))
    test("Model has disliked_patterns", isinstance(getattr(model, 'disliked_patterns', None), list))
    test("Model has satisfaction_history", isinstance(getattr(model, 'satisfaction_history', None), list))
    test("Model has style_signals", isinstance(getattr(model, 'style_signals', None), dict))

    # --- StyleSignal ---
    sig = StyleSignal(name="test_style")
    test("StyleSignal creates correctly", sig is not None)
    test("StyleSignal has name", sig.name == "test_style")
    test("StyleSignal has confidence", hasattr(sig, 'confidence'))
    test("StyleSignal has weight", hasattr(sig, 'weight'))

    # --- Feedback integration ---
    feedback_data = {
        "message_id": "test_001",
        "feedback": "positive",
        "message": "Great answer, very clear and concise!"
    }
    try:
        update_from_feedback(feedback_data)
        test("update_from_feedback() runs without error", True)
    except Exception as e:
        test("update_from_feedback() runs without error", False, str(e))

    # --- Guidance generation ---
    try:
        guidance = get_response_guidance()
        test("get_response_guidance() returns string", isinstance(guidance, str))
    except Exception as e:
        test("get_response_guidance() returns string", False, str(e))

    # --- Summary ---
    try:
        summary = summarize_user_alignment()
        test("summarize_user_alignment() returns dict", isinstance(summary, dict))
    except Exception as e:
        test("summarize_user_alignment() returns dict", False, str(e))

    # --- Persistence ---
    try:
        model2 = load_user_model()
        save_user_model(model2)
        model3 = load_user_model()
        test("Save/load round-trip works", isinstance(model3, UserModel))
    except Exception as e:
        test("Save/load round-trip works", False, str(e))

    # --- Negative feedback ---
    neg_feedback = {
        "message_id": "test_002",
        "feedback": "negative",
        "message": "Too verbose, I wanted a shorter answer."
    }
    try:
        update_from_feedback(neg_feedback)
        test("Negative feedback records without error", True)
    except Exception as e:
        test("Negative feedback records without error", False, str(e))

finally:
    # --- Restore original data ---
    if backup_path and os.path.exists(backup_path):
        shutil.copy2(backup_path, data_path)
        os.remove(backup_path)
        print("\n  [restored original user_model.json]")

print(f"\n  Results: {PASS} passed, {FAIL} failed out of {PASS + FAIL}")
if FAIL == 0:
    print("  ✅ ALL TESTS PASS")
else:
    print(f"  ❌ {FAIL} FAILURES")
    sys.exit(1)