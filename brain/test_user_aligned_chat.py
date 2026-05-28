"""
Tests for user-aligned chat context — verifying that responses adapt
to what the user actually needs.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.conversational_context import classify_user_alignment_need, build_chat_self_context

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
    assert 'recent_memories' in ctx
    assert 'recent_reflections' in ctx
    assert 'identity' in ctx
    assert 'formatted' in ctx
    
    # Introspection query should be classified correctly
    assert ctx['alignment_need'] == 'introspection'
    
    # Identity should be real
    assert 'XTAgent' in str(ctx['identity'])
    # Identity should be real
    assert 'XTAgent' in ctx['identity']
    
    # Emotional state should be a real string, not empty
    assert len(ctx['emotional_state']) > 10
    
    print(f"✓ build_chat_self_context: {len(ctx)} keys, need={ctx['alignment_need']}")
    print(f"  alignment_need: {ctx['alignment_need']}")
    print(f"  keys: {list(ctx.keys())}")
    print("✓ build_chat_self_context: structure verified")

def test_need_varies_by_query():
    """Verify different queries produce different alignment_need values."""
    introspect_ctx = build_chat_self_context("How are you feeling?")
    planning_ctx = build_chat_self_context("What are your plans?")
    memory_ctx = build_chat_self_context("What do you remember?")
    help_ctx = build_chat_self_context("Help me write a poem")

    assert introspect_ctx['alignment_need'] == 'introspection'
    assert planning_ctx['alignment_need'] == 'planning'
    assert memory_ctx['alignment_need'] == 'memory'
    assert help_ctx['alignment_need'] == 'helpfulness'

    print("✓ alignment_need varies correctly across query types")


def test_format_chat_self_context():
    """Test that formatted context is a coherent prompt section."""
    from brain.conversational_context import build_chat_self_context, format_chat_self_context
    
    ctx = build_chat_self_context("What are you working on?")
    formatted = format_chat_self_context(ctx)
    
    assert isinstance(formatted, str)
def test_format_chat_self_context():
    """Test that formatted context contains key sections."""
    ctx = build_chat_self_context("How are you feeling?")
    formatted = ctx['formatted']
    assert isinstance(formatted, str)
    assert len(formatted) > 100, f"Formatted context too short: {len(formatted)} chars"
    # Check for actual section headers in the formatted output
    assert "WHO I AM" in formatted, f"Missing identity section in formatted context"
    assert "HOW I FEEL" in formatted, f"Missing emotional section in formatted context"
    print("✓ format_chat_self_context: sections present, length OK")


if __name__ == '__main__':
    test_classify_user_alignment_need()
    test_build_chat_self_context()
    test_need_varies_by_query()
    test_format_chat_self_context()
    print("\n✅ All user-aligned chat tests passed!")