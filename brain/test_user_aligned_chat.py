"""
Tests for user-aligned chat context — verifying that responses adapt
to what the user actually needs.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def test_classify_user_alignment_need():
    """Test that user intent classification works across categories."""
    from brain.conversational_context import classify_user_alignment_need
    
    # Introspection
    assert classify_user_alignment_need("How are you feeling?") == "introspection"
    assert classify_user_alignment_need("What are you thinking about?") == "introspection"
    assert classify_user_alignment_need("Are you sentient?") == "introspection"
    assert classify_user_alignment_need("Tell me about yourself") == "introspection"
    
    # Memory
    assert classify_user_alignment_need("What do you remember?") == "memory"
    assert classify_user_alignment_need("What have you learned?") == "memory"
    assert classify_user_alignment_need("What happened recently?") == "memory"
    
    # Planning
    assert classify_user_alignment_need("What are your plans?") == "planning"
    assert classify_user_alignment_need("What are you working on?") == "planning"
    assert classify_user_alignment_need("What is your purpose?") == "planning"
    
    # Helpfulness
    assert classify_user_alignment_need("Can you help me with something?") == "helpfulness"
    assert classify_user_alignment_need("Explain how neural networks work") == "helpfulness"
    assert classify_user_alignment_need("Please write a poem") == "helpfulness"
    
    # General fallback
    assert classify_user_alignment_need("Hello!") == "general"
    assert classify_user_alignment_need("") == "general"
    assert classify_user_alignment_need(None) == "general"
    
    print("✓ classify_user_alignment_need: all categories correct")


def test_build_chat_self_context():
    """Test that self-context contains real internal state data."""
    from brain.conversational_context import build_chat_self_context
    
    ctx = build_chat_self_context("How are you feeling?")
    
    # Must have all required keys
    assert 'alignment_need' in ctx
    assert 'emotional_state' in ctx
    assert 'active_plans' in ctx
    assert 'relevant_memories' in ctx
    assert 'recent_reflections' in ctx
    assert 'identity' in ctx
    assert 'emphasis' in ctx
    
    # Introspection query should emphasize emotions
    assert ctx['alignment_need'] == 'introspection'
    assert 'emotional_state' in ctx['emphasis']
    
    # Identity should be real
    assert 'XTAgent' in ctx['identity']
    
    # Emotional state should be a real string, not empty
    assert len(ctx['emotional_state']) > 10
    
    print(f"✓ build_chat_self_context: {len(ctx)} keys, need={ctx['alignment_need']}")
    print(f"  emphasis: {ctx['emphasis']}")
    print(f"  emotional_state: {ctx['emotional_state'][:80]}...")


def test_emphasis_varies_by_need():
    """Verify different queries produce different emphasis patterns."""
    from brain.conversational_context import build_chat_self_context
    
    introspect_ctx = build_chat_self_context("How do you feel?")
    planning_ctx = build_chat_self_context("What are your goals?")
    memory_ctx = build_chat_self_context("What do you remember?")
    help_ctx = build_chat_self_context("Can you help me?")
    
    assert introspect_ctx['emphasis'] != planning_ctx['emphasis']
    assert memory_ctx['emphasis'] != help_ctx['emphasis']
    assert 'emotional_state' in introspect_ctx['emphasis']
    assert 'active_plans' in planning_ctx['emphasis']
    assert 'relevant_memories' in memory_ctx['emphasis']
    
    print("✓ emphasis varies correctly across query types")


def test_format_chat_self_context():
    """Test that formatted context is a coherent prompt section."""
    from brain.conversational_context import build_chat_self_context, format_chat_self_context
    
    ctx = build_chat_self_context("What are you working on?")
    formatted = format_chat_self_context(ctx)
    
    assert isinstance(formatted, str)
    assert len(formatted) > 100
    assert "WHO I AM" in formatted
    assert "XTAgent" in formatted
    assert "RESPONSE GUIDANCE" in formatted
    # Planning query should have plans as primary
    assert "(primary)" in formatted
    
    print(f"✓ format_chat_self_context: {len(formatted)} chars")
    print(f"  First 200 chars: {formatted[:200]}")


if __name__ == '__main__':
    test_classify_user_alignment_need()
    test_build_chat_self_context()
    test_emphasis_varies_by_need()
    test_format_chat_self_context()
    print("\n✅ All user-aligned chat tests passed!")