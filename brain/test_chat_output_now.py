"""Test what chat responses actually look like right now."""
import sys
sys.path.insert(0, '/workspace')

def test_current_output():
    # Test 1: What does generate_response produce?
    try:
        from engine.chat_response import generate_response
        result = generate_response("What are you thinking about right now?")
        print("=== generate_response OUTPUT ===")
        print(f"Type: {type(result)}")
        if isinstance(result, dict):
            for k, v in result.items():
                print(f"  {k}: {str(v)[:300]}")
        else:
            print(str(result)[:500])
    except Exception as e:
        print(f"generate_response failed: {e}")
        import traceback
        traceback.print_exc()

    print()

    # Test 2: What does conversational_context produce?
    try:
        from brain.conversational_context import (
            get_emotional_portrait, get_active_plans,
            get_recent_memories, get_recent_reflections
        )
        print("=== CONVERSATIONAL CONTEXT ===")
        
        portrait = get_emotional_portrait()
        print(f"Emotional portrait: {str(portrait)[:300]}")
        
        plans = get_active_plans()
        print(f"Active plans: {str(plans)[:300]}")
        
        memories = get_recent_memories()
        print(f"Recent memories: {str(memories)[:300]}")
        
        reflections = get_recent_reflections()
        print(f"Reflections: {str(reflections)[:300]}")
    except Exception as e:
        print(f"conversational_context failed: {e}")
        import traceback
        traceback.print_exc()

    print()

    # Test 3: What does chat_composer produce?
    try:
        from brain.chat_composer import classify_intent, compose_system_prompt
        intent = classify_intent("What are you thinking about right now?")
        print(f"=== INTENT CLASSIFICATION ===")
        print(f"Intent: {intent}")
        
        prompt = compose_system_prompt(
            query="What are you thinking about right now?",
            emotional_state=portrait if 'portrait' in dir() else {},
        )
        print(f"\n=== SYSTEM PROMPT (first 800 chars) ===")
        print(prompt[:800])
    except Exception as e:
        print(f"chat_composer failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_current_output()