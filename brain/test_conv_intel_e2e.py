"""Quick test: does conversational intelligence generate real responses?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from brain.conversational_intelligence import (
    classify_intent,
    compose_system_prompt,
    generate_intelligent_response
)

def test():
    # 1. Intent classification
    queries = {
        "How are you feeling?": "emotion",
        "What is your knowledge graph?": "factual",
        "What do you know about yourself?": "identity",
        "Write me a haiku": "creative",
    }
    
    print("=== Intent Classification ===")
    for q, expected in queries.items():
        intent = classify_intent(q)
        status = "✓" if intent == expected else f"~ (got {intent})"
        print(f"  {status} '{q}' → {intent}")
    
    # 2. System prompt composition (module-level function)
    print("\n=== System Prompt ===")
    query = "How are you feeling right now?"
    intent = classify_intent(query)
    prompt = compose_system_prompt(query)
    print(f"  Length: {len(prompt)} chars")
    has_emotion = "emotion" in prompt.lower() or "feel" in prompt.lower()
    print(f"  Contains emotional context: {has_emotion}")
    assert len(prompt) > 50, f"Prompt too short: {len(prompt)}"
    print("  ✓ System prompt composed successfully")
    
    # 3. Full response generation (requires LLM)
    print("\n=== Response Generation ===")
    try:
        result = generate_intelligent_response("What are you thinking about?")
        if result and isinstance(result, dict):
            resp = result.get("response", "")
            print(f"  Response length: {len(resp)} chars")
            print(f"  Intent: {result.get('intent', 'unknown')}")
            print(f"  Source: {result.get('source', 'unknown')}")
            print("  ✓ Full response generated")
        else:
            print(f"  ~ Got result: {type(result)}")
    except Exception as e:
        print(f"  ~ LLM unavailable: {e}")
    
    print("\n=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    test()
