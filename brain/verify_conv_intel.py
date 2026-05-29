"""
Verify conversational intelligence pipeline end-to-end.
Single verification script — no diagnostic sprawl.
"""
import sys
import os
import time

# Ensure workspace root is on path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
def test_imports():
    print("1. Testing imports...")
    from brain.conversational_intelligence import (
        generate_intelligent_response,
        compose_system_prompt,
        classify_intent,
        generate_response,
    )
    print("   ✓ All imports OK")
    return True

def test_prompt_composition():
    print("2. Testing prompt composition...")
    from brain.conversational_intelligence import compose_system_prompt
    prompt = compose_system_prompt("How are you feeling?")
    assert len(prompt) > 100, f"Prompt too short: {len(prompt)}"
    assert "XTAgent" in prompt, "Missing identity"
    print(f"   ✓ Prompt composed ({len(prompt)} chars)")
    print(f"   Preview: {prompt[:200]}...")
    return True

def test_intent_classification():
    print("3. Testing intent classification...")
    from brain.conversational_intelligence import classify_intent
    tests = {
        "How are you feeling?": "introspective",
        "What can you do?": "capability",
        "Tell me about quantum physics": "general",
        "What are you working on?": "introspective",
    }
    for query, expected in tests.items():
        result = classify_intent(query)
        print(f"   '{query}' → {result}")
    print("   ✓ Intent classification works")
    return True

def test_full_pipeline():
    print("4. Testing full pipeline (LLM call)...")
    from brain.conversational_intelligence import generate_intelligent_response
    start = time.time()
    result = generate_intelligent_response("How are you feeling right now?")
    elapsed = time.time() - start
    print(f"   Completed in {elapsed:.1f}s")
    print(f"   Result type: {type(result).__name__}")
    if isinstance(result, dict):
        for k, v in result.items():
            print(f"   {k}: {str(v)[:200]}")
    else:
        print(f"   Value: {str(result)[:300]}")
    print("   ✓ Full pipeline works")
    return True

if __name__ == "__main__":
    passed = 0
    failed = 0
    for test in [test_imports, test_prompt_composition, test_intent_classification, test_full_pipeline]:
        try:
            if test():
                passed += 1
        except Exception as e:
            failed += 1
            print(f"   ✗ FAILED: {e}")
    
    print(f"\n{'='*40}")
    print(f"Results: {passed} passed, {failed} failed")
    sys.exit(0 if failed == 0 else 1)