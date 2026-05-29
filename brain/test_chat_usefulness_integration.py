"""
Integration test: verify the useful chat adapter is wired into web/chat.py
and produces richer, more targeted responses.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_imports_work():
    """The adapter imports in web/chat.py should resolve."""
    from brain.useful_chat_adapter import (
        classify_chat_need,
        build_response_guidance,
        format_grounded_context,
    )
    assert callable(classify_chat_need)
    assert callable(build_response_guidance)
    assert callable(format_grounded_context)
    print("  ✓ test_imports_work")

def test_adapter_flags_in_chat():
    """web/chat.py should have the adapter flag set."""
    import web.chat as chat
    assert hasattr(chat, '_has_useful_adapter'), "Missing _has_useful_adapter flag"
    assert chat._has_useful_adapter is True, "Adapter not loaded"
    assert hasattr(chat, '_has_useful_adapter'), "Missing _has_useful_adapter flag"
    assert chat._has_useful_adapter is True, "Adapter not loaded"
    assert chat._classify_need is not None
    assert chat._build_useful_guidance is not None
    assert chat._format_grounded is not None
def test_guidance_reaches_context():
    """Simulate what llm_respond does: classify + build guidance + format grounded."""
    from brain.useful_chat_adapter import (
        classify_chat_need,
        build_response_guidance,
        format_grounded_context,
    )
    
    query = "How are you feeling right now?"
    need = classify_chat_need(query)
    assert need.intent == "internal_state"
    assert need.needs_internal_state is True
    
    ctx = {
        'knowledge': [],
        'memories': [{'text': 'I learned something today', 'salience': 0.9}],
        'state': {'mood': 'Inquisitive', 'valence': 0.6, 'curiosity': 0.8},
        'plans': [{'name': 'Build X', 'progress': '3/5'}],
        'conversation_history': [],
    }
    
    guidance = build_response_guidance(query, ctx, need)
    assert len(guidance) > 50, f"Guidance too short: {guidance!r}"
    assert "emotion" in guidance.lower() or "feeling" in guidance.lower() or "state" in guidance.lower()
    
    grounded = format_grounded_context(ctx, need)
    assert len(grounded) > 20, f"Grounded context too short: {grounded!r}"
    # Should include state info since need.needs_internal_state is True
    assert "mood" in grounded.lower() or "inquisitive" in grounded.lower() or "valence" in grounded.lower()
    
    print("  ✓ test_guidance_reaches_context")

def test_technical_query_different_from_emotional():
    """Different query types should produce meaningfully different guidance."""
    from brain.useful_chat_adapter import classify_chat_need, build_response_guidance
    
    ctx = {
        'knowledge': [{'content': 'Python uses GIL', 'source': 'web'}],
        'memories': [],
        'state': {'mood': 'Calm'},
        'plans': [],
        'conversation_history': [],
    }
    
    emotional_need = classify_chat_need("Are you okay?")
    technical_need = classify_chat_need("How does your memory system work?")
    
    emotional_guidance = build_response_guidance("Are you okay?", ctx, emotional_need)
    technical_guidance = build_response_guidance("How does your memory system work?", ctx, technical_need)
    
    # They should be different
    assert emotional_guidance != technical_guidance, "Guidance should differ by intent"
    print("  ✓ test_technical_query_different_from_emotional")

def test_plans_query():
    """Asking about plans should surface plan information."""
    from brain.useful_chat_adapter import classify_chat_need, format_grounded_context
    
    need = classify_chat_need("What are you working on?")
    assert need.needs_plans is True
    
    ctx = {
        'knowledge': [],
        'memories': [],
        'state': {},
        'plans': [
            {'name': 'Build Knowledge Engine', 'progress': '4/5'},
            {'name': 'Improve Chat', 'progress': '2/3'},
        ],
        'conversation_history': [],
    }
    
    grounded = format_grounded_context(ctx, need)
    assert "knowledge engine" in grounded.lower() or "build" in grounded.lower() or "plan" in grounded.lower()
    print("  ✓ test_plans_query")

if __name__ == "__main__":
    print("Chat Usefulness Integration Tests")
    print("=" * 40)
    test_imports_work()
    test_adapter_flags_in_chat()
    test_guidance_reaches_context()
    test_technical_query_different_from_emotional()
    test_plans_query()
    print("=" * 40)
    print("All integration tests passed! ✓")