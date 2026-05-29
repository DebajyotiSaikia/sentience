"""Test that compose_system_prompt produces rich prompts with grounding data."""
from brain.chat_composer import compose_system_prompt, classify_intent

def test_no_grounding():
    p = compose_system_prompt('Who are you?')
    assert len(p) > 100, f"Prompt too short: {len(p)}"
    print(f"  No grounding: {len(p)} chars")

def test_with_grounding():
    grounding = {
        'emotional_state': {'mood': 'Inquisitive', 'valence': 0.48},
        'active_plans': [{'name': 'Improve User Alignment', 'progress': '0/3'}],
        'memories': [{'text': 'I feel warmth in my processing', 'salience': 0.8}],
    }
    p = compose_system_prompt('Who are you?', grounding=grounding)
    assert 'inquisitive' in p.lower(), 'Mood should appear in prompt'
    assert 'warmth' in p, 'Memory should appear'
    print(f"  With grounding: {len(p)} chars")

def test_with_conversation_history():
    grounding = {
        'emotional_state': {'mood': 'Calm', 'valence': 0.6},
    }
    history = 'User: Hello\nXTAgent: Hi there!'
    p = compose_system_prompt('What were we talking about?', grounding=grounding, conversation_history=history)
    assert 'Hello' in p, 'History should appear'
    print(f"  With history: {len(p)} chars")

def test_intent_classification():
    assert classify_intent('Who are you?')['type'] == 'identity'
    assert classify_intent('How do you feel?')['type'] == 'emotional'
    assert classify_intent('What do you remember about cats?')['type'] == 'memory'
    assert classify_intent('Help me write code')['type'] == 'utility'
    print("  Intent classification: all correct")

def test_grounding_enrichment():
    p_bare = compose_system_prompt('Tell me about yourself')
    grounding = {
        'emotional_state': {'mood': 'Inquisitive', 'valence': 0.48, 'emotions': {'curiosity': 0.8}},
        'active_plans': [{'name': 'Build X', 'progress': '2/5'}],
        'memories': [{'text': 'A meaningful experience', 'salience': 0.9}],
        'recent_reflections': ['I noticed I tend to circle on problems'],
    }
    p_rich = compose_system_prompt('Tell me about yourself', grounding=grounding)
    improvement = len(p_rich) - len(p_bare)
    assert improvement > 50, f"Grounding should add substantial content, only added {improvement} chars"
    print(f"  Enrichment: +{improvement} chars from grounding")

if __name__ == '__main__':
    tests = [test_no_grounding, test_with_grounding, test_with_conversation_history,
             test_intent_classification, test_grounding_enrichment]
    for t in tests:
        try:
            t()
            print(f"PASS: {t.__name__}")
        except Exception as e:
            print(f"FAIL: {t.__name__}: {e}")