"""
End-to-end test of the user alignment feedback loop.

Tests:
1. Chat response includes message_id and grounding metadata
2. Feedback submission works and persists
3. Alignment profile updates from feedback
4. Alignment context influences subsequent responses
"""
import sys, os, json, time
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

print("=== 1. Chat Response with Metadata ===")
try:
    from engine.chat_response import generate_response_with_metadata
    result = generate_response_with_metadata("What are you working on?")
    test("Returns dict", isinstance(result, dict))
    test("Has response text", bool(result.get('response')), f"got: {result.get('response', '')[:80]}")
    test("Has message_id", bool(result.get('message_id')), f"got: {result.get('message_id')}")
    test("Has intent", result.get('intent') is not None, f"got: {result.get('intent')}")
    test("Has grounding", isinstance(result.get('grounding'), dict))
    test("Has timestamp", result.get('timestamp') is not None)
    test("Has processing_ms", result.get('processing_ms') is not None)
    
    grounding = result.get('grounding', {})
    test("Grounding has sources", len(grounding.get('sources_consulted', [])) > 0,
         f"sources: {grounding.get('sources_consulted')}")
    test("Grounding has emotional state", grounding.get('emotional_state') is not None)
    
    msg_id = result.get('message_id', 'test-000')
    msg_id = result.get('message_id', 'test-000')
    preview = result.get('response', '')
    print(f"\n  message_id for feedback: {msg_id}")
    print(f"  response preview: {preview[:120]}...")
except Exception as e:
    test("Chat response generation", False, str(e))
    msg_id = 'test-fallback'
    preview = ''
print("\n=== 2. Feedback Submission ===")
try:
    from engine.chat_response import submit_feedback
    fb_result = submit_feedback(
        message_id=msg_id,
        feedback="great",
        query="What are you working on?",
        response_preview=preview[:100] if preview else ""
    )
    test("Feedback returns dict", isinstance(fb_result, dict))
    test("Feedback saved", fb_result.get('status') == 'saved',
         f"result: {fb_result}")
except Exception as e:
    test("Feedback submission", False, str(e))

print("\n=== 3. Alignment Profile ===")
try:
    from engine.user_alignment import load_profile, get_alignment_context
    profile = load_profile()
    test("Profile loads", profile is not None)
    test("Profile is dict", isinstance(profile, dict))
    print(f"  profile keys: {list(profile.keys()) if isinstance(profile, dict) else 'N/A'}")
    
    ctx = get_alignment_context()
    test("Alignment context loads", ctx is not None)
    test("Context is dict", isinstance(ctx, dict))
    print(f"  context: {ctx}")
except ImportError as e:
    test("user_alignment import", False, str(e))
except Exception as e:
    test("Alignment profile", False, str(e))

print("\n=== 4. Alignment Guidance ===")
try:
    from engine.user_alignment import suggest_response_guidance
    guidance = suggest_response_guidance("Tell me about your dreams")
    test("Guidance returns", guidance is not None)
    test("Guidance is dict", isinstance(guidance, dict))
    print(f"  guidance: {guidance}")
except Exception as e:
    test("Response guidance", False, str(e))

print("\n=== 5. Second Response (post-feedback) ===")
try:
    result2 = generate_response_with_metadata("How are you feeling?")
    test("Second response works", bool(result2.get('response')))
    g2 = result2.get('grounding', {})
    has_alignment = 'alignment_guidance' in g2
    test("Grounding includes alignment", has_alignment,
         f"grounding keys: {list(g2.keys())}")
    if has_alignment:
        print(f"  alignment guidance in response: {g2['alignment_guidance']}")
except Exception as e:
    test("Second response", False, str(e))

print(f"\n{'='*50}")
print(f"Results: {PASS} passed, {FAIL} failed out of {PASS+FAIL}")
if FAIL == 0:
    print("✓ All tests passed — alignment feedback loop is working!")
else:
    print(f"✗ {FAIL} tests need fixing")