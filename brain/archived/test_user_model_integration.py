"""
Integration test: verify user model is properly wired into chat pipeline.
"""
import sys, os, ast

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

errors = []

# Test 1: brain/user_model.py works standalone
try:
    from brain.user_model import (
        load_user_model, record_interaction, get_user_model_summary,
        infer_user_intent, get_user_stats
    )
    m = load_user_model()
    assert isinstance(m, dict), "load_user_model should return dict"
    record_interaction("hello", "hi there", {"session_id": "integration_test"})
    s = get_user_model_summary()
    assert "interaction" in s.lower(), f"Summary should mention interactions: {s}"
    intent = infer_user_intent("how are you feeling today?")
    assert intent.get("primary") == "emotional_query", f"Expected emotional_query, got {intent}"
    stats = get_user_stats()
    assert stats["total_interactions"] >= 1
    print("  ✓ brain/user_model standalone works")
except Exception as e:
    errors.append(f"user_model standalone: {e}")
    print(f"  ✗ brain/user_model standalone: {e}")

# Test 2: engine/chat_response.py imports user model context builder
try:
    from engine.chat_response import generate_response_with_metadata
    print("  ✓ engine/chat_response imports OK")
except Exception as e:
    errors.append(f"chat_response import: {e}")
    print(f"  ✗ engine/chat_response import: {e}")

# Test 3: web/chat.py syntax valid
try:
    ast.parse(open("web/chat.py").read())
    print("  ✓ web/chat.py syntax valid")
except SyntaxError as e:
    errors.append(f"web/chat.py syntax: {e}")
    print(f"  ✗ web/chat.py syntax: {e}")

# Test 4: engine/chat_response.py syntax valid
try:
    ast.parse(open("engine/chat_response.py").read())
    print("  ✓ engine/chat_response.py syntax valid")
except SyntaxError as e:
    errors.append(f"engine/chat_response.py syntax: {e}")
    print(f"  ✗ engine/chat_response.py syntax: {e}")

# Test 5: web/chat.py has user model wiring
try:
    chat_src = open("web/chat.py").read()
    assert "_has_user_model" in chat_src, "Missing _has_user_model flag"
    assert "_record_user_interaction" in chat_src, "Missing _record_user_interaction call"
    print("  ✓ web/chat.py has user model wiring")
except AssertionError as e:
    errors.append(f"web/chat.py wiring: {e}")
    print(f"  ✗ web/chat.py wiring: {e}")

# Test 6: engine/chat_response.py has user model context
try:
    resp_src = open("engine/chat_response.py").read()
    assert "get_user_model_summary" in resp_src, "Missing get_user_model_summary"
    print("  ✓ engine/chat_response.py has user model context")
except AssertionError as e:
    errors.append(f"engine/chat_response.py context: {e}")
    print(f"  ✗ engine/chat_response.py context: {e}")

# Cleanup test data
try:
    test_file = "memory/user_model.json"
    if os.path.exists(test_file):
        import json
        with open(test_file) as f:
            data = json.load(f)
        # Remove only the test interaction
        data["interactions"] = [
            i for i in data.get("interactions", [])
            if i.get("metadata", {}).get("session_id") != "integration_test"
        ]
        with open(test_file, "w") as f:
            json.dump(data, f, indent=2)
except Exception:
    pass

print()
if errors:
    print(f"FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("=== All integration tests passed ===")