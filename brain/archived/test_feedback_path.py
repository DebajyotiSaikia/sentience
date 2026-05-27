"""Test that feedback flows from chat_response → user_alignment correctly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_response import generate_response_with_metadata, submit_feedback
from engine.user_alignment import UserAlignmentEngine

def test_feedback_submission():
    """Test that submit_feedback writes to the alignment engine."""
    result = submit_feedback("test-msg-001", 5, "Great response!")
    print(f"Feedback result: {result}")
    assert result.get("status") == "saved", f"Expected 'saved', got {result}"
    print("✓ Feedback submission works")

def test_alignment_engine_directly():
    """Test UserAlignmentEngine records feedback and generates guidance."""
    engine = UserAlignmentEngine()
    engine.record_feedback("test-msg-002", "This is the response text", 4, "Helpful answer")
    
    guidance = engine.get_guidance("Tell me about yourself")
    print(f"Guidance: {guidance}")
    assert isinstance(guidance, str), f"Expected str, got {type(guidance)}"
    print("✓ Alignment engine works directly")

def test_generate_response():
    """Test that generate_response_with_metadata returns proper structure."""
    result = generate_response_with_metadata("What are you thinking about?")
    print(f"Response keys: {list(result.keys())}")
    assert "response" in result or "answer" in result, f"Missing response key in {list(result.keys())}"
    print("✓ Response generation works")

if __name__ == "__main__":
    print("=== Feedback Path Tests ===\n")
    
    test_feedback_submission()
    print()
    test_alignment_engine_directly()
    print()
    test_generate_response()
    
    print("\n=== All tests passed ===")