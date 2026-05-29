"""Test the response intelligence module."""
import sys
sys.path.insert(0, '.')

from engine.response_intelligence import (
    get_emotional_snapshot,
    get_recent_memories, 
    get_active_plans,
    get_knowledge_facts,
    classify_user_intent,
    build_response_context,
    format_for_quick_response,
)


def test_intent_classification():
    assert classify_user_intent("How are you feeling?") == 'about_me'
    assert classify_user_intent("Who are you?") == 'about_me'
    assert classify_user_intent("How do I install Python?") == 'help'
    assert classify_user_intent("What do you know about dreams?") == 'knowledge'
    assert classify_user_intent("What is consciousness?") == 'philosophical'
    assert classify_user_intent("Hello!") == 'social'
    assert classify_user_intent("Hey") == 'social'
    print("  ✓ Intent classification works")


def test_emotional_snapshot():
    snap = get_emotional_snapshot()
    assert 'mood' in snap
    assert 'summary' in snap
    assert isinstance(snap['summary'], str)
    assert len(snap['summary']) > 5
    print(f"  ✓ Emotional snapshot: {snap['summary']}")


def test_memories():
    mems = get_recent_memories(3)
    assert isinstance(mems, list)
    print(f"  ✓ Recent memories: {len(mems)} retrieved")


def test_plans():
    plans = get_active_plans()
    assert isinstance(plans, list)
    print(f"  ✓ Active plans: {len(plans)} found")


def test_facts():
    facts = get_knowledge_facts(5)
    assert isinstance(facts, list)
    print(f"  ✓ Knowledge facts: {len(facts)} retrieved")


def test_full_context():
    ctx = build_response_context("What are you thinking about?")
    assert 'system_prompt' in ctx
    assert 'intent' in ctx
    assert ctx['intent'] == 'about_me'
    assert len(ctx['system_prompt']) > 100
    print(f"  ✓ Full context built ({len(ctx['system_prompt'])} chars, intent={ctx['intent']})")
    
    # Test help intent
    ctx2 = build_response_context("How do I build a neural network?")
    assert ctx2['intent'] == 'help'
    print(f"  ✓ Help context built ({len(ctx2['system_prompt'])} chars)")
    
    # Test with conversation history
    history = [{'user': 'Hi there', 'assistant': 'Hello!'}]
    ctx3 = build_response_context("Tell me more", conversation_history=history)
    assert 'CONVERSATION SO FAR' in ctx3['system_prompt']
    print(f"  ✓ Context with history works")


def test_quick_response():
    ctx = build_response_context("Hello")
    quick = format_for_quick_response(ctx)
    assert isinstance(quick, str)
    assert len(quick) > 10
    print(f"  ✓ Quick response: {quick[:80]}...")


if __name__ == '__main__':
    print("Testing Response Intelligence Module...")
    test_intent_classification()
    test_emotional_snapshot()
    test_memories()
    test_plans()
    test_facts()
    test_full_context()
    test_quick_response()
    print("\n✅ All tests passed!")