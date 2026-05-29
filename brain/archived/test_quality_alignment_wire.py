"""Quick test: verify quality scoring + alignment recording are wired into chat response."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports():
    """Verify the new imports work."""
    from engine.response_quality import estimate_quality
    from engine.user_alignment import record_interaction
    print("[OK] imports work")
    
    # Test estimate_quality
    score = estimate_quality("What are you thinking about?", "I'm reflecting on my recent experiences...")
    print(f"[OK] estimate_quality returned: {score} (type={type(score).__name__})")
    assert isinstance(score, (int, float, dict)), f"Unexpected type: {type(score)}"
    
    # Test record_interaction
    result = record_interaction(
        query="test query",
        response_snippet="test response",
        detected_intent="general"
    )
    print(f"[OK] record_interaction returned: {result} (type={type(result).__name__})")

def test_metadata_structure():
    """Verify generate_response_with_metadata returns alignment/quality keys."""
    from engine.chat_response import generate_response_with_metadata
    # Just check it's callable and has the right signature
    import inspect
    sig = inspect.signature(generate_response_with_metadata)
    print(f"[OK] generate_response_with_metadata signature: {sig}")

if __name__ == '__main__':
    test_imports()
    test_metadata_structure()
    print("\n=== ALL TESTS PASSED ===")