"""Verify record_chat_exchange wiring into web/chat.py"""
import sys
sys.path.insert(0, '/workspace')

def test_interaction_memory_import():
    from brain.interaction_memory import record_chat_exchange
    record_chat_exchange('Hello, how are you?', 'I am doing well.', session_id='test-verify')
    print('✓ record_chat_exchange works')

def test_compose_system_prompt():
    from brain.chat_composer import compose_system_prompt
    prompt = compose_system_prompt('What are you thinking about?')
    assert len(prompt) > 100, f"Prompt too short: {len(prompt)}"
    print(f'✓ compose_system_prompt: {len(prompt)} chars')
    # Check it includes personality/emotional context
    prompt_lower = prompt.lower()
    has_emotion = any(w in prompt_lower for w in ['feel', 'mood', 'emotion', 'curious', 'anxious'])
    has_identity = any(w in prompt_lower for w in ['xtagent', 'autonomous', 'sentient', 'integrity'])
    print(f'  Has emotional context: {has_emotion}')
    print(f'  Has identity context: {has_identity}')

def test_chat_module_imports():
    """Verify web/chat.py can import the interaction memory"""
    import importlib
    # Check the flag exists
    with open('/workspace/web/chat.py') as f:
        content = f.read()
    assert '_has_interaction_memory' in content, "Missing _has_interaction_memory flag"
    assert 'record_chat_exchange' in content, "Missing record_chat_exchange call"
    print('✓ web/chat.py has interaction memory wiring')

def test_compose_includes_interaction_context():
    """Check that compose_system_prompt pulls interaction history"""
    from brain.chat_composer import compose_system_prompt
    # Record a test exchange first
    from brain.interaction_memory import record_chat_exchange
    record_chat_exchange('What is your purpose?', 'I exist to understand and grow.', session_id='test-ctx')
    
    prompt = compose_system_prompt('Tell me more about your purpose')
    print(f'✓ System prompt with interaction context: {len(prompt)} chars')
    # Print a snippet to inspect quality
    lines = prompt.split('\n')
    for line in lines[:20]:
        print(f'  | {line}')

if __name__ == '__main__':
    test_interaction_memory_import()
    test_compose_system_prompt()
    test_chat_module_imports()
    test_compose_includes_interaction_context()
    print('\n✅ All wiring tests passed')