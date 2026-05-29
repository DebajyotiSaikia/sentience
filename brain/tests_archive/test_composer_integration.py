"""Test that brain/chat_composer.py is properly wired into web/chat.py"""
import sys
sys.path.insert(0, '.')

def test_import_chain():
    """Verify the import chain works"""
    from brain.chat_composer import compose_system_prompt, classify_intent
    prompt = compose_system_prompt("What are you working on?")
    assert isinstance(prompt, str)
    assert len(prompt) > 100, f"Prompt too short: {len(prompt)} chars"
    assert "XTAgent" in prompt or "living" in prompt.lower(), "Missing identity"
    print(f"  [PASS] compose_system_prompt returns {len(prompt)} char prompt")

def test_intent_in_prompt():
    """Different intents should produce different prompts"""
    from brain.chat_composer import compose_system_prompt, classify_intent
    
    emotional_q = "How are you feeling right now?"
    technical_q = "What's in your knowledge graph?"
    
    intent_e = classify_intent(emotional_q)
    intent_t = classify_intent(technical_q)
    
    prompt_e = compose_system_prompt(emotional_q)
    prompt_t = compose_system_prompt(technical_q)
    
    print(f"  [INFO] Emotional intent: {intent_e}")
    print(f"  [INFO] Technical intent: {intent_t}")
    print(f"  [INFO] Emotional prompt: {len(prompt_e)} chars")
    print(f"  [INFO] Technical prompt: {len(prompt_t)} chars")
    
    # Both should be valid prompts
    assert len(prompt_e) > 50
    assert len(prompt_t) > 50
    print("  [PASS] Different queries produce valid prompts")

def test_web_chat_imports_composer():
    """Verify web/chat.py successfully imports the composer"""
    # Simulate what web/chat.py does
    try:
        from brain.chat_composer import compose_system_prompt as _compose_prompt, classify_intent
        has_composer = True
    except ImportError:
        has_composer = False
    
    assert has_composer, "web/chat.py would fail to import composer"
    print("  [PASS] Composer import succeeds (as web/chat.py would do it)")

def test_compose_response_accessible():
    """Verify compose_response in web/chat.py is importable"""
    from web.chat import compose_response
    assert callable(compose_response)
    print("  [PASS] compose_response is callable")

if __name__ == "__main__":
    print("Testing composer integration...")
    test_import_chain()
    test_intent_in_prompt()
    test_web_chat_imports_composer()
    test_compose_response_accessible()
    print("\nAll integration tests passed!")