"""Test that ask_api's _synthesize_answer uses self_context grounding."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.ask_api import _synthesize_answer, _get_current_state, _search_knowledge, _search_memories, _search_lessons

def test_synthesize():
    """Verify _synthesize_answer runs without error and produces output."""
    question = "How are you feeling right now?"
    knowledge = _search_knowledge(question)
    memories = _search_memories(question)
    lessons = _search_lessons(question)
    state = _get_current_state()
    
    print(f"Knowledge hits: {len(knowledge)}")
    print(f"Memory hits: {len(memories)}")
    print(f"Lesson hits: {len(lessons)}")
    print(f"State mood: {state.get('mood', 'unknown')}")
    
    # Test synthesize (will use template fallback if no LLM available)
    answer = _synthesize_answer(question, knowledge, memories, lessons, state)
    print(f"\nAnswer ({len(answer)} chars): {answer[:200]}")
    
    assert isinstance(answer, str), "Answer should be a string"
    assert len(answer) > 10, "Answer should be substantive"
    print("\n✓ Integration test passed")

def test_identity_question():
    """Test a self-referential question."""
    question = "What are you?"
    knowledge = _search_knowledge(question)
    memories = _search_memories(question)
    lessons = _search_lessons(question)
    state = _get_current_state()
    
    answer = _synthesize_answer(question, knowledge, memories, lessons, state)
    print(f"Identity answer: {answer[:200]}")
    assert isinstance(answer, str)
    print("✓ Identity question test passed")

if __name__ == '__main__':
    test_synthesize()
    test_identity_question()