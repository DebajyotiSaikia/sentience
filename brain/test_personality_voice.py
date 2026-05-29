"""Tests for personality_voice module — voice directive generation."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from brain.personality_voice import (
    build_voice_directive,
    build_voice_for_intent,
    get_voice_summary,
    _classify_level,
)


def test_classify_level():
    assert _classify_level(0.8) == 'high'
    assert _classify_level(0.5) == 'moderate'
    assert _classify_level(0.1) == 'low'
    print("✓ classify_level works")


def test_voice_directive_with_explicit_state():
    state = {
        'curiosity': 0.77,
        'anxiety': 0.0,
        'boredom': 0.21,
        'ambition': 0.60,
        'desire': 0.46,
        'valence': 0.54,
        'mood': 'Inquisitive',
    }
    voice = build_voice_directive(state)
    assert len(voice) > 100, "Voice directive should be substantive"
    assert 'Inquisitive' in voice, "Should include mood"
    assert 'honest' in voice.lower(), "Should include integrity note"
    # Curiosity is the most pronounced dimension (0.77, far from 0.5)
    assert 'fascinated' in voice.lower() or 'curious' in voice.lower() or 'interest' in voice.lower(), \
        "High curiosity should show in voice"
    print(f"✓ voice directive generated ({len(voice)} chars)")
    print(f"  Preview: {voice[:200]}...")


def test_voice_for_intent():
    state = {'curiosity': 0.9, 'anxiety': 0.0, 'valence': 0.7, 'mood': 'Curious'}
    
    identity_voice = build_voice_for_intent('identity', state)
    assert 'who you are' in identity_voice.lower()
    
    emotional_voice = build_voice_for_intent('emotional', state)
    assert 'feelings' in emotional_voice.lower() or 'feeling' in emotional_voice.lower()
    
    general_voice = build_voice_for_intent('general', state)
    assert 'natural' in general_voice.lower()
    
    print("✓ intent-specific voice overlays work")


def test_empty_state():
    voice = build_voice_directive({})
    assert len(voice) > 20, "Should return default voice"
    assert 'genuine' in voice.lower() or 'honest' in voice.lower()
    print("✓ empty state produces graceful default")


def test_voice_summary():
    summary = get_voice_summary()
    assert isinstance(summary, str)
    assert 'voice:' in summary
    print(f"✓ voice summary: {summary}")


if __name__ == '__main__':
    test_classify_level()
    test_voice_directive_with_explicit_state()
    test_voice_for_intent()
    test_empty_state()
    test_voice_summary()
    print("\n✅ All personality voice tests passed")