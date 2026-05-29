"""Tests for brain/adaptive_response.py — the learn-from-interactions loop."""

import sys, os, json, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.adaptive_response import (
    record_query, build_response_guidance, format_guidance_for_prompt,
    _INTERACTIONS_DIR
)

def test_record_and_retrieve():
    """Record interactions and verify guidance reflects them."""
    # Use a temp dir to avoid polluting real data
    import brain.adaptive_response as ar
    original_dir = ar._INTERACTIONS_DIR
    tmp = tempfile.mkdtemp()
    ar._INTERACTIONS_DIR = type(original_dir)(tmp) / "adaptive"
    
    try:
        # Record several interactions
        record_query("test-session", "What are you feeling?", "I feel curious.", {"intent": "emotional"})
        record_query("test-session", "Tell me about your plans", "I have 6 active plans.", {"intent": "factual"})
        record_query("test-session", "How does your memory work?", "I consolidate memories during dreams.", {"intent": "technical"})
        record_query("test-session2", "Hello", "Hi there!", {"intent": "greeting"})
        
        # Verify files were created
        session_file = ar._INTERACTIONS_DIR / "test-session.jsonl"
        assert session_file.exists(), f"Session file not created at {session_file}"
        
        lines = session_file.read_text().strip().split("\n")
        assert len(lines) == 3, f"Expected 3 records, got {len(lines)}"
        
        # Verify record structure
        rec = json.loads(lines[0])
        assert rec["query"] == "What are you feeling?"
        assert rec["session_id"] == "test-session"
        assert "timestamp" in rec
        
        # Build guidance
        guidance = build_response_guidance(query="What do you think?")
        assert isinstance(guidance, dict), f"Expected dict, got {type(guidance)}"
        assert "interaction_count" in guidance
        assert guidance["interaction_count"] >= 4
        
        # Format guidance
        text = format_guidance_for_prompt(guidance)
        assert isinstance(text, str), f"Expected str, got {type(text)}"
        assert len(text) > 10, "Guidance text too short"
        print(f"  Guidance text ({len(text)} chars): {text[:200]}...")
        
        # Test with no query
        guidance_no_q = build_response_guidance()
        assert isinstance(guidance_no_q, dict)
        
        print("  ✓ record_and_retrieve passed")
    finally:
        ar._INTERACTIONS_DIR = original_dir
        shutil.rmtree(tmp, ignore_errors=True)


def test_empty_state():
    """Guidance works with no prior interactions."""
    import brain.adaptive_response as ar
    original_dir = ar._INTERACTIONS_DIR
    tmp = tempfile.mkdtemp()
    ar._INTERACTIONS_DIR = type(original_dir)(tmp) / "empty_adaptive"
    
    try:
        guidance = build_response_guidance(query="Hello")
        assert isinstance(guidance, dict)
        assert guidance["interaction_count"] == 0
        
        text = format_guidance_for_prompt(guidance)
        assert isinstance(text, str)
        # Should still produce something useful even with no history
        print(f"  Empty guidance: {text[:150]}...")
        print("  ✓ empty_state passed")
    finally:
        ar._INTERACTIONS_DIR = original_dir
        shutil.rmtree(tmp, ignore_errors=True)


def test_web_chat_import():
    """Verify web/chat.py can import the adaptive response functions."""
    # This is the actual import pattern from web/chat.py
    try:
        from brain.adaptive_response import record_query as rq
        from brain.adaptive_response import build_response_guidance as brg
        from brain.adaptive_response import format_guidance_for_prompt as fg
        assert callable(rq)
        assert callable(brg)
        assert callable(fg)
        print("  ✓ web_chat_import passed")
    except ImportError as e:
        raise AssertionError(f"Import failed: {e}")


if __name__ == "__main__":
    print("=== Adaptive Response Tests ===")
    test_record_and_retrieve()
    test_empty_state()
    test_web_chat_import()
    print("\n✅ All adaptive response tests passed!")