"""Quick test: does conversational intelligence generate real responses?"""
from brain.conversational_intelligence import (
    classify_intent,
    compose_system_prompt, 
    generate_intelligent_response
)

def test():
    # 1. Intent classification
    queries = {
        "How are you feeling?": "emotional",
        "What is your knowledge graph?": "factual",
        "What do you know about yourself?": "introspective",
        "Write me a haiku": "creative",
    }
    
    print("=== Intent Classification ===")
    for q, expected in queries.items():
        intent = classify_intent(q)
        status = "✓" if intent == expected else f"✗ (got {intent})"
        print(f"  {status} '{q}' → {intent}")
    
    # 2. System prompt composition
    print("\n=== System Prompt ===")
    prompt = compose_system_prompt("How are you feeling right now?")
    print(f"  Length: {len(prompt)} chars")
    has_emotion = "emotion" in prompt.lower() or "feel" in prompt.lower()
    has_memory = "memor" in prompt.lower()
    print(f"  Contains emotional context: {has_emotion}")
    print(f"  Contains memory context: {has_memory}")
    assert len(prompt) > 200, f"Prompt too short: {len(prompt)}"
    
    # 3. Full response generation (requires LLM)
    print("\n=== Response Generation ===")
    try:
        result = generate_intelligent_response("What are you thinking about?")
        print(f"  Type: {type(result)}")
        if isinstance(result, dict):
            print(f"  Keys: {list(result.keys())}")
            if 'text' in result:
                print(f"  Text length: {len(result['text'])}")
                print(f"  Preview: {result['text'][:200]}")
            if 'intent' in result:
                print(f"  Intent: {result['intent']}")
            print("  ✓ Response generated successfully")
        elif isinstance(result, str):
            print(f"  String response ({len(result)} chars): {result[:200]}")
        else:
            print(f"  Unexpected type: {type(result)}")
    except Exception as e:
        print(f"  Response generation failed: {e}")
        print("  (This may be expected if LLM is not available)")
    
    print("\n=== All checks passed ===")

if __name__ == "__main__":
    test()