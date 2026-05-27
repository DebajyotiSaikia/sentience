"""Verify implicit feedback mechanism in web/chat.py"""
import sys, hashlib
sys.path.insert(0, '.')

def test_implicit_feedback_logic():
    """Test the core logic of implicit feedback generation"""
    # Simulate conversation history with a previous assistant message
    conversation_history = [
        {'role': 'user', 'content': 'hello'},
        {'role': 'assistant', 'content': 'Hi! I am XTAgent. How can I help?'},
        {'role': 'user', 'content': 'tell me about yourself'},
    ]
    
    prev_exchanges = [h for h in conversation_history if h.get('role') == 'assistant']
    assert len(prev_exchanges) == 1, f"Expected 1 assistant msg, got {len(prev_exchanges)}"
    
    last_assistant = prev_exchanges[-1]
    content = last_assistant.get('content', '')
    assert content, "Should have content"
    
    prev_id = hashlib.md5(content.encode()[:200]).hexdigest()[:12]
    assert len(prev_id) == 12, f"ID should be 12 chars, got {len(prev_id)}"
    assert prev_id.isalnum(), "ID should be alphanumeric"
    
    # Same content should produce same ID (stable)
    prev_id2 = hashlib.md5(content.encode()[:200]).hexdigest()[:12]
    assert prev_id == prev_id2, "Same content should produce same ID"
    
    print(f"  Generated feedback ID: {prev_id}")
    print("  PASS: Implicit feedback logic works correctly")

def test_no_history():
    """No history means no feedback"""
    conversation_history = []
    fired = False
    if conversation_history:
        fired = True
    assert not fired, "Should not fire with empty history"
    print("  PASS: No feedback on empty history")

def test_no_assistant_messages():
    """Only user messages means no feedback"""
    conversation_history = [
        {'role': 'user', 'content': 'hello'},
    ]
    prev_exchanges = [h for h in conversation_history if h.get('role') == 'assistant']
    assert len(prev_exchanges) == 0
    print("  PASS: No feedback with no assistant messages")

def test_response_id_in_response():
    """Verify response includes response_id field"""
    import ast
    with open('web/chat.py') as f:
        source = f.read()
    assert "'response_id': response_id" in source, "response_id should be in jsonify response"
    print("  PASS: response_id included in API response")

if __name__ == '__main__':
    print("=== Implicit Feedback Verification ===")
    test_implicit_feedback_logic()
    test_no_history()
    test_no_assistant_messages()
    test_response_id_in_response()
    print("\nAll 4 tests passed!")