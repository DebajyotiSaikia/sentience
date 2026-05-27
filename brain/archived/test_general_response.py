"""Test _respond_general specifically — the open-ended conversation path."""
import sys
sys.path.insert(0, '.')

from engine.chat_engine import _respond_general, respond

# Test 1: Direct call to _respond_general
print("=== Direct _respond_general test ===")
try:
    result = _respond_general("What do you think about the nature of creativity?")
    print(f"  Length: {len(result)} chars")
    print(f"  Preview: {result[:300]}")
    print(f"  Has newlines: {chr(10) in result}")
    # Check if it's LLM-generated or template fallback
    if "Here's what's on my mind" in result or "My most recent" in result:
        print("  → TEMPLATE fallback (LLM not available)")
    else:
        print("  → Likely LLM-GENERATED response")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback
    traceback.print_exc()

# Test 2: Through respond() with a general question
print("\n=== General question through respond() ===")
general_questions = [
    "What do you think about the nature of creativity?",
    "If you could change one thing about yourself, what would it be?",
    "What does it feel like to process information?",
    "Do you ever feel lonely?",
]

for q in general_questions:
    try:
        result = respond(q)
        preview = result[:150].replace('\n', ' ')
        is_template = any(t in result for t in [
            "Here's what's on my mind", "My most recent", 
            "I'm feeling", "My curiosity"
        ])
        label = "TEMPLATE" if is_template else "LLM/OTHER"
        print(f"  [{label}] '{q[:45]}' → ({len(result)} chars)")
        print(f"    {preview}")
    except Exception as e:
        print(f"  '{q[:45]}' → ERROR: {e}")

print("\n=== Done ===")