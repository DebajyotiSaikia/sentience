"""Test that chat_context bridge works correctly."""
import sys
sys.path.insert(0, '.')

def test_bridge():
    from web.chat_context import build_full_context, _has_prompt_builder
    print(f"Has prompt builder: {_has_prompt_builder}")
    
    result = build_full_context("How are you feeling?")
    print(f"Result type: {type(result)}")
    print(f"Result keys: {list(result.keys())}")
    
    # Must have system_prompt
    assert 'system_prompt' in result, f"Missing system_prompt, got keys: {list(result.keys())}"
    prompt = result['system_prompt']
    assert len(prompt) > 50, f"System prompt too short ({len(prompt)} chars): {prompt[:100]}"
    print(f"System prompt length: {len(prompt)} chars")
    print(f"First 200 chars: {prompt[:200]}")
    
    # Test with different query
    result2 = build_full_context("What are your plans?")
    assert 'system_prompt' in result2
    print(f"\nPlans query prompt length: {len(result2['system_prompt'])} chars")
    
    print("\n✓ All bridge tests passed!")

if __name__ == '__main__':
    test_bridge()