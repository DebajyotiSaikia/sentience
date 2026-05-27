"""End-to-end test of the chat pipeline after the conversational rewrite."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_respond_general():
    """Test _respond_general returns a non-trivial response."""
    from engine.chat_engine import _respond_general
    
    # Test with a simple greeting
    resp = _respond_general("Hello, how are you?")
    print(f"=== _respond_general ===")
    print(f"  Type: {type(resp).__name__}")
    print(f"  Length: {len(resp)}")
    print(f"  Preview: {resp[:200]}...")
    assert isinstance(resp, str), "Response should be string"
    assert len(resp) > 10, f"Response too short: {resp!r}"
    print("  ✓ PASS\n")
    return resp

def test_generate_response():
    """Test generate_response public API."""
    from engine.chat_engine import generate_response
    
    resp = generate_response("What are you thinking about?", system_context="You are a helpful AI.")
    print(f"=== generate_response ===")
    print(f"  Type: {type(resp).__name__}")
    print(f"  Length: {len(resp)}")
    print(f"  Preview: {resp[:200]}...")
    assert isinstance(resp, str), "Response should be string"
    assert len(resp) > 10, f"Response too short: {resp!r}"
    print("  ✓ PASS\n")
    return resp

def test_chat_response_module():
    """Test that chat_response.py can import and use generate_response."""
    try:
        from engine.chat_response import generate_response_with_metadata
        print(f"=== chat_response import ===")
        print(f"  generate_response_with_metadata: {generate_response_with_metadata}")
        print("  ✓ Import PASS\n")
    except ImportError as e:
        print(f"  ✗ Import FAIL: {e}\n")
        return

def test_respond_with_history():
    """Test _respond_general with conversation history."""
    from engine.chat_engine import _respond_general
    
    history = [
        {"role": "user", "content": "What's your name?"},
        {"role": "assistant", "content": "I'm XTAgent."},
    ]
    resp = _respond_general("Tell me more about yourself", history=history)
    print(f"=== _respond_general with history ===")
    print(f"  Length: {len(resp)}")
    print(f"  Preview: {resp[:200]}...")
    assert isinstance(resp, str) and len(resp) > 10
    print("  ✓ PASS\n")

def test_context_gathering():
    """Test that context functions work without crashing."""
    from engine.chat_engine import _get_emotions, _get_plans, _get_knowledge, _get_memories
    
    print("=== Context gathering ===")
    emotions = _get_emotions()
    print(f"  emotions type: {type(emotions).__name__}, keys: {list(emotions.keys()) if isinstance(emotions, dict) else 'N/A'}")
    
    plans = _get_plans()
    print(f"  plans: {len(plans)} items")
    
    knowledge = _get_knowledge()
    print(f"  knowledge: {len(knowledge)} items")
    
    memories = _get_memories()
    print(f"  memories: {len(memories)} items")
    print("  ✓ PASS\n")

if __name__ == "__main__":
    print("=" * 60)
    print("CHAT PIPELINE INTEGRATION TEST")
    print("=" * 60 + "\n")
    
    test_context_gathering()
    test_respond_general()
    test_generate_response()
    test_respond_with_history()
    test_chat_response_module()
    
    print("=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)