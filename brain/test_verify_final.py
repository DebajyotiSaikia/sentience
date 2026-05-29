"""Quick verification that all wiring is correct."""
import sys
sys.path.insert(0, '/workspace')

def main():
    errors = []
    
    # 1. Import check
    try:
        from brain.interaction_memory import record_chat_exchange, get_interaction_summary
        print("✓ interaction_memory imports OK")
    except Exception as e:
        errors.append(f"interaction_memory import: {e}")
        print(f"✗ interaction_memory import failed: {e}")
    
    try:
        from brain.chat_composer import compose_system_prompt
        print("✓ chat_composer imports OK")
    except Exception as e:
        errors.append(f"chat_composer import: {e}")
        print(f"✗ chat_composer import failed: {e}")
    
    # 2. Functional check - get_interaction_summary returns a string for prompt inclusion
    try:
        summary = get_interaction_summary()
        assert isinstance(summary, str), f"Expected str, got {type(summary)}"
        print(f"✓ get_interaction_summary() → {len(summary)} chars")
    except Exception as e:
        errors.append(f"interaction_summary: {e}")
        print(f"✗ interaction_summary failed: {e}")
    
    try:
        prompt = compose_system_prompt("hello", {})
        assert isinstance(prompt, str), f"Expected str, got {type(prompt)}"
        assert len(prompt) > 100, f"Prompt too short: {len(prompt)} chars"
        print(f"✓ compose_system_prompt() → {len(prompt)} chars")
        has_personality = any(word in prompt.lower() for word in ['feel', 'mood', 'curious', 'genuine', 'honest'])
        print(f"  {'✓' if has_personality else '⚠'} Personality markers present: {has_personality}")
    except Exception as e:
        errors.append(f"compose_system_prompt: {e}")
        print(f"✗ compose_system_prompt failed: {e}")
    
    # 3. Record + retrieve roundtrip
    try:
        record_chat_exchange("test question", "test answer", {"source": "verify_test"})
        summary_after = get_interaction_summary()
        assert isinstance(summary_after, str), f"Expected str, got {type(summary_after)}"
        assert len(summary_after) > 0, "Summary should not be empty after recording"
        print(f"✓ record→retrieve roundtrip OK ({len(summary_after)} chars)")
    except Exception as e:
        errors.append(f"roundtrip: {e}")
        print(f"✗ roundtrip failed: {e}")
    
    # 4. Syntax check on web/chat.py
    try:
        import ast
        ast.parse(open('/workspace/web/chat.py').read())
        print("✓ web/chat.py syntax OK")
    except Exception as e:
        errors.append(f"web/chat.py syntax: {e}")
        print(f"✗ web/chat.py syntax failed: {e}")
    
    print()
    print("=" * 40)
    if errors:
        print(f"FAILED: {len(errors)} error(s)")
        for e in errors:
            print(f"  - {e}")
    else:
        print("ALL CHECKS PASSED ✓")
    
    return len(errors) == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
