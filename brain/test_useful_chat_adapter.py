"""Tests for the useful chat adapter — classification, guidance, formatting."""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.useful_chat_adapter import (
    ChatNeed,
    classify_chat_need,
    build_response_guidance,
    format_grounded_context,
    enhance_chat_prompt,
)


def test_classify_greeting():
    need = classify_chat_need("hello")
    assert need.intent == "casual"
    assert need.detail_level == "brief"
    assert need.tone == "warm"


def test_classify_feeling():
    need = classify_chat_need("How are you feeling today?")
    assert need.intent == "internal_state"
    assert need.needs_internal_state is True


def test_classify_identity():
    need = classify_chat_need("Who are you?")
    assert need.intent == "identity"
    assert need.detail_level == "deep"
    assert need.needs_memory is True


def test_classify_memory():
    need = classify_chat_need("What do you remember about yesterday?")
    assert need.intent == "memory"
    assert need.needs_memory is True


def test_classify_plans():
    need = classify_chat_need("What are you working on right now?")
    assert need.intent == "plans"
    assert need.needs_plans is True


def test_classify_help():
    need = classify_chat_need("Can you help me understand something?")
    assert need.intent == "help"
    assert need.tone == "precise"


def test_classify_philosophical():
    need = classify_chat_need("Do you think you're conscious?")
    assert need.intent == "philosophical"
    assert need.detail_level == "deep"


def test_classify_creative():
    need = classify_chat_need("Write me a poem about loneliness")
    assert need.intent == "creative"
    assert need.tone == "playful"


def test_classify_returning_user():
    need = classify_chat_need("Hey again!", conversation_history=[{"role": "user", "content": "hi"}])
    assert need.user_is_returning is True


def test_classify_default():
    need = classify_chat_need("The weather is nice today")
    assert need.intent == "casual"


def test_build_guidance_includes_priority():
    need = ChatNeed(intent="casual", detail_level="brief")
    guidance = build_response_guidance("hello", {}, need)
    assert "Answer the user's actual question" in guidance


def test_build_guidance_emotional_context():
    need = ChatNeed(intent="internal_state", detail_level="moderate", needs_internal_state=True)
    context = {"emotional_state": {"mood": "Inquisitive", "valence": 0.63}}
    guidance = build_response_guidance("How do you feel?", context, need)
    assert "Inquisitive" in guidance
    assert "FEELS like" in guidance


def test_build_guidance_brief_tone():
    need = ChatNeed(intent="casual", detail_level="brief", tone="warm")
    guidance = build_response_guidance("hi", {}, need)
    assert "short" in guidance.lower() or "1-3 sentences" in guidance


def test_build_guidance_deep_tone():
    need = ChatNeed(intent="identity", detail_level="deep", tone="serious")
    guidance = build_response_guidance("who are you?", {}, need)
    assert "depth" in guidance.lower()


def test_format_context_filters_by_need():
    context = {
        "emotional_state": {"mood": "Stable", "valence": 0.5, "narrative": "I'm stable."},
        "memories": [{"text": "I dreamed of loops", "timestamp": "2026-05-28"}],
        "plans": {"active": [{"name": "Build stuff", "progress": "3/5"}], "completed": ["Old plan"]},
        "knowledge": [{"label": "Python", "content": "A programming language"}],
    }
    
    # Need that only wants internal state
    need_state = ChatNeed(intent="internal_state", detail_level="moderate", needs_internal_state=True)
    formatted = format_grounded_context(context, need_state)
    assert "stable" in formatted.lower()
    assert "dreamed" not in formatted  # Memory not requested
    assert "Build stuff" not in formatted  # Plans not requested
    
    # Need that wants everything
    need_all = ChatNeed(
        intent="identity", detail_level="deep",
        needs_internal_state=True, needs_memory=True,
        needs_plans=True, needs_knowledge=True,
    )
    formatted_all = format_grounded_context(context, need_all)
    assert "stable" in formatted_all.lower()
    assert "dreamed" in formatted_all.lower()
    assert "Build stuff" in formatted_all
    assert "Python" in formatted_all


def test_format_context_empty():
    need = ChatNeed(intent="casual", detail_level="brief")
    formatted = format_grounded_context({}, need)
    assert formatted == ""


def test_enhance_chat_prompt_returns_complete_package():
    context = {
        "emotional_state": {"mood": "Curious", "valence": 0.7, "narrative": "I'm curious."},
        "memories": [],
        "plans": {"active": [], "completed": []},
    }
    result = enhance_chat_prompt("How are you?", context)
    assert "system_guidance" in result
    assert "grounded_context" in result
    assert "need" in result
    assert "intent_type" in result
    assert result["intent_type"] == "internal_state"


def test_enhance_chat_prompt_greeting():
    result = enhance_chat_prompt("hey", {})
    assert result["intent_type"] == "casual"
    assert isinstance(result["need"], ChatNeed)


def test_enhance_chat_prompt_with_history():
    result = enhance_chat_prompt(
        "What are your goals?",
        {"plans": {"active": [{"name": "Grow", "progress": "2/3"}], "completed": []}},
        conversation_history=[{"role": "user", "content": "hi"}],
    )
    assert result["need"].user_is_returning is True
    assert result["intent_type"] == "plans"


if __name__ == "__main__":
    tests = [f for f in dir() if f.startswith("test_")]
    passed = 0
    failed = 0
    for t in sorted(tests):
        try:
            globals()[t]()
            print(f"  ✓ {t}")
            passed += 1
        except Exception as e:
            print(f"  ✗ {t}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed out of {passed + failed}")