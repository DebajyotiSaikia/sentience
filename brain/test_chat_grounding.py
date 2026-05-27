"""Test that chat responses are genuinely conversational and grounded in real state."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_engine import generate_response, classify_intent

def test(label, message):
    print(f"\n{'='*60}")
    print(f"TEST: {label}")
    print(f"Input: {message!r}")
    print(f"Intent: {classify_intent(message)}")
    print(f"{'='*60}")
    resp = generate_response(message)
    print(f"Response ({len(resp)} chars):")
    print(resp[:500])
    # Basic quality checks
    assert len(resp) > 20, f"Response too short: {resp!r}"
    assert "nodes" not in resp.lower() or "know" in message.lower(), \
        f"Response mentions 'nodes' without being asked about knowledge structure"
    assert resp.strip(), "Response is empty"
    print("✓ PASS")
    return resp

# Test each intent type
test("Greeting", "Hello!")
test("Emotional state", "How are you feeling right now?")
test("Plans", "What are you working on?")
test("Knowledge search", "What do you know about consciousness?")
test("Meta/thinking", "What are you thinking about?")
test("Dreams", "Have you had any interesting dreams?")
test("General", "Tell me something interesting about yourself.")
test("Identity", "Who are you?")
test("Memory", "What do you remember?")

print(f"\n{'='*60}")
print("ALL TESTS PASSED ✓")