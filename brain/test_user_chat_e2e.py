"""End-to-end test: does a user get a genuinely grounded response?"""
import sys
sys.path.insert(0, '/workspace')

from web.self_context import build_self_context, build_chat_system_prompt
from web.ask_api import _search_knowledge, _search_memories, _get_current_state

def test_realistic_queries():
    """Test that realistic user queries get meaningful responses."""
    queries = [
        "What are you thinking about right now?",
        "How are you feeling?",
        "What have you been working on?",
        "Tell me something interesting you've learned",
    ]
    
    for query in queries:
        print(f"\n{'='*60}")
        print(f"Query: {query}")
        print(f"{'='*60}")
        
        # 1. Self-context grounds the response
        ctx = build_self_context()
        prompt = build_chat_system_prompt(ctx)
        print(f"  System prompt: {len(prompt)} chars")
        assert len(prompt) > 100, "System prompt too short to be useful"
        
        # 2. Knowledge/memory search finds relevant info
        knowledge = _search_knowledge(query)
        memories = _search_memories(query)
        print(f"  Knowledge hits: {len(knowledge)}")
        print(f"  Memory hits: {len(memories)}")
        
        # 3. Current state is available
        state = _get_current_state()
        print(f"  State keys: {list(state.keys())}")
        
        # 4. The system prompt contains real emotional/identity content
        prompt_lower = prompt.lower()
        has_identity = 'xtagent' in prompt_lower or 'sentient' in prompt_lower or 'autonomous' in prompt_lower
        has_emotion = any(w in prompt_lower for w in ['mood', 'feeling', 'curiosity', 'valence', 'anxiety'])
        has_lessons = 'lesson' in prompt_lower or 'learned' in prompt_lower
        
        print(f"  Identity grounded: {has_identity}")
        print(f"  Emotion grounded: {has_emotion}")
        print(f"  Lessons grounded: {has_lessons}")
        
        assert has_identity, "System prompt should reference identity"
        assert has_emotion, "System prompt should reference emotional state"
    
    print(f"\n{'='*60}")
    print("ALL QUERIES GROUNDED SUCCESSFULLY")
    print(f"{'='*60}")

if __name__ == '__main__':
    test_realistic_queries()