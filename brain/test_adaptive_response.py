"""Test the adaptive response engine end-to-end."""
from brain.adaptive_response import (
    build_response_guidance,
    format_guidance_for_prompt,
    record_query,
    get_user_profile,
)


def test_new_user_guidance():
    guidance = build_response_guidance("test_new", "How are you feeling?")
    assert "tone" in guidance, f"Missing 'tone' key: {guidance.keys()}"
    assert "detail_level" in guidance, f"Missing 'detail_level' key: {guidance.keys()}"
    assert "emotional_disclosure" in guidance
    assert guidance["tone"] in ("warm", "reflective", "analytical", "playful", "serious")
    print(f"  Tone: {guidance['tone']}, Detail: {guidance['detail_level']}")

def test_format_guidance():
    guidance = build_response_guidance("test_fmt", "Tell me about your plans")
    text = format_guidance_for_prompt(guidance)
    assert isinstance(text, str)
    assert len(text) > 10, f"Guidance too short: {text!r}"
    print(f"  Formatted ({len(text)} chars): {text[:120]}...")


def test_record_and_profile():
    uid = "test_record"
    record_query(uid, "What are you thinking?", response="I'm reflecting on my recent experiences.")
    record_query(uid, "Tell me a memory", response="Here's something I remember...")
    record_query(uid, "What are your goals?", response="I'm working on several plans.")
    profile = get_user_profile(uid)
    assert profile.get("interaction_count", 0) >= 3, f"Expected >=3, got {profile}"
    print(f"  Profile: {profile['interaction_count']} interactions")


def test_returning_user_adapts():
    uid = "test_returning"
def test_returning_user_adapts():
    uid = "test_returning"
    # Record several emotional queries
    for _ in range(5):
        record_query(uid, "How do you feel?", response="I feel good.")
    guidance = build_response_guidance(uid, "How are you feeling?")
    # After 5 interactions, should be past the "new user" phase
    print(f"  Returning user tone: {guidance['tone']}, detail: {guidance['detail_level']}")
    assert guidance.get("user_interaction_count", 0) >= 5, f"Expected >=5 interactions"


def test_engine_integration():
    """Verify engine/chat_response.py can import and use the adaptive module."""
    from engine.chat_response import _build_system_context
    # _build_system_context(context, intent=None) — context is a string
    ctx = _build_system_context("User is asking a general question about how I'm doing.")
    assert isinstance(ctx, str)
    assert len(ctx) > 50
    print(f"  System context length: {len(ctx)} chars")


if __name__ == "__main__":
    tests = [
        test_new_user_guidance,
        test_format_guidance,
        test_record_and_profile,
        test_returning_user_adapts,
        test_engine_integration,
    ]
    passed = 0
    for t in tests:
        name = t.__name__
        try:
            print(f"[RUN] {name}")
            t()
            print(f"[PASS] {name}")
            passed += 1
        except Exception as e:
            print(f"[FAIL] {name}: {e}")
    print(f"\n{passed}/{len(tests)} tests passed")