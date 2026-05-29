"""End-to-end test: verify personality-driven chat works and alignment isn't artificially inflated."""
import sys, os, time
sys.path.insert(0, '.')

def test_personality_pipeline():
    """Test that personality_respond produces real conversational output."""
    from brain.chat_personality import personality_respond
    
    # Test 1: emotional question
    print("Test 1: 'How are you feeling?'")
    t0 = time.time()
    r1 = personality_respond("How are you feeling?")
    t1 = time.time()
    print(f"  Response ({len(r1)} chars, {t1-t0:.1f}s): {r1[:200]}...")
    assert len(r1) > 50, f"Response too short: {len(r1)}"
    assert r1 != "I'm not sure how to respond to that.", "Got fallback response"
    
    # Test 2: plans question  
    print("\nTest 2: 'What are you working on?'")
    t0 = time.time()
    r2 = personality_respond("What are you working on?")
    t1 = time.time()
    print(f"  Response ({len(r2)} chars, {t1-t0:.1f}s): {r2[:200]}...")
    assert len(r2) > 50, f"Response too short: {len(r2)}"
    
    # Test 3: with conversation history
    print("\nTest 3: Follow-up with history")
    history = [
        {"role": "user", "content": "How are you feeling?"},
        {"role": "assistant", "content": r1},
    ]
    t0 = time.time()
    r3 = personality_respond("Tell me more about that", conversation_history=history)
    t1 = time.time()
    print(f"  Response ({len(r3)} chars, {t1-t0:.1f}s): {r3[:200]}...")
    assert len(r3) > 50, f"Response too short: {len(r3)}"
    
    print("\n✅ All personality pipeline tests passed!")

def test_no_artificial_inflation():
    """Verify record_feedback(0.65) is no longer called in compose_response."""
    with open('web/chat.py', 'r') as f:
        source = f.read()
    
    with open('web/chat.py', 'r') as f:
        for i, line in enumerate(f, 1):
            stripped = line.strip()
            if stripped.startswith('#') or stripped.startswith('def ') or 'import' in stripped:
                continue
            if 'rating=0.65' in stripped:
                raise AssertionError(f"Artificial rating=0.65 still in code at line {i}: {stripped}")
            if 'record_feedback(' in stripped and '=' not in stripped.split('record_feedback')[0]:
                # Only flag actual calls, not assignments like `x = record_feedback`
                raise AssertionError(f"record_feedback still called at line {i}: {stripped}")
if __name__ == '__main__':
    test_no_artificial_inflation()
    test_personality_pipeline()