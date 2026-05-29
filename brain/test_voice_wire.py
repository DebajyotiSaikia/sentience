"""Quick verification that voice directive flows through chat composer and introspection."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_voice_in_chat_composer():
    from brain.chat_composer import compose_system_prompt
    prompt = compose_system_prompt("How are you feeling?")
    assert len(prompt) > 100, f"Prompt too short: {len(prompt)}"
    has_voice = "Voice" in prompt or "tone" in prompt.lower()
    assert has_voice, "Voice directive not found in chat composer prompt"


def test_voice_in_introspection():
    from engine.introspection import build_system_context
    ctx = build_system_context("test query")
    assert len(ctx) > 50, f"Context too short: {len(ctx)}"
    has_voice = "Voice" in ctx or "tone" in ctx.lower()
    assert has_voice, "Voice directive not found in introspection context"


if __name__ == "__main__":
    test_voice_in_chat_composer()
    print("✓ Chat composer has voice directive")
    test_voice_in_introspection()
    print("✓ Introspection has voice directive")
    print("\n✓✓ BOTH paths have voice directives")
