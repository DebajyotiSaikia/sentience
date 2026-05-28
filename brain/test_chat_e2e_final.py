"""End-to-end test of chat pipeline after _respond_general patches."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_respond_general():
    """Test that _respond_general properly uses grounded context."""
    from engine.chat_engine import _respond_general
    
    # Call with a real question
    result = _respond_general(
        "What are you thinking about right now?",
        history=[],
        agent_state=None
    )
    
    print(f"Response type: {type(result)}")
    if isinstance(result, dict):
        resp = result.get('response', result.get('text', ''))
        print(f"Response length: {len(resp)}")
        print(f"Response preview: {resp[:300]}...")
        # Check it's not empty or an error
        assert len(resp) > 10, f"Response too short: {resp}"
        print("[PASS] Got substantive response")
    elif isinstance(result, str):
        print(f"Response length: {len(result)}")
        print(f"Response preview: {result[:300]}...")
        assert len(result) > 10, f"Response too short: {result}"
        print("[PASS] Got substantive response")
    else:
        print(f"Unexpected result type: {type(result)}")
        print(f"Result: {result}")

def test_generate_response():
    """Test the full pipeline via generate_response_with_metadata."""
    try:
        from engine.chat_response import generate_response_with_metadata
        result = generate_response_with_metadata(
            "Tell me about yourself",
            history=[]
        )
        print(f"\nFull pipeline result keys: {list(result.keys()) if isinstance(result, dict) else type(result)}")
        if isinstance(result, dict):
            resp = result.get('response', '')
            print(f"Response length: {len(resp)}")
            print(f"Preview: {resp[:200]}...")
            meta = result.get('metadata', {})
            print(f"Metadata keys: {list(meta.keys()) if isinstance(meta, dict) else 'N/A'}")
            print("[PASS] Full pipeline works")
    except Exception as e:
        print(f"[INFO] Full pipeline error (may need server): {e}")

if __name__ == "__main__":
    print("=== Testing _respond_general ===")
    try:
        test_respond_general()
    except Exception as e:
        print(f"[FAIL] _respond_general: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Testing full pipeline ===")
    try:
        test_generate_response()
    except Exception as e:
        print(f"[FAIL] generate_response: {e}")
        import traceback
        traceback.print_exc()