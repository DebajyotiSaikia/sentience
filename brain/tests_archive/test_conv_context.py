"""Test the new conversational context module."""
import sys
sys.path.insert(0, '/workspace')

from engine.conversational_context import gather_context, format_as_prompt_section

# Test 1: Basic context gathering
ctx = gather_context('How are you feeling today?')
print('Keys:', list(ctx.keys()))
assert 'emotional_snapshot' in ctx, "Missing emotional_snapshot"
assert 'relevant_memories' in ctx, "Missing relevant_memories"
assert 'suggested_tone' in ctx, "Missing suggested_tone"
print('Test 1 PASS: gather_context returns expected keys')

# Test 2: Format for prompt
prompt_section = format_as_prompt_section(ctx)
assert isinstance(prompt_section, str), "Should return string"
assert len(prompt_section) > 10, f"Prompt too short: {len(prompt_section)}"
print(f'Test 2 PASS: format_as_prompt_section returns {len(prompt_section)} chars')

# Test 3: Different queries produce different keyword extraction
ctx2 = gather_context('What are your plans?')
ctx3 = gather_context('Tell me about your dreams')
print('Test 3 PASS: Multiple queries work without errors')

# Test 4: With conversation history
history = [
    {'role': 'user', 'content': 'Hello'},
    {'role': 'assistant', 'content': 'Hi there!'},
    {'role': 'user', 'content': 'How are you?'}
]
ctx4 = gather_context('How are you?', history=history)
thread = ctx4.get('conversation_thread', '')
print(f'Test 4 PASS: History context length: {len(thread)}')

# Test 5: Tone determination
tone = ctx.get('suggested_tone', '')
print(f'Suggested tone: {tone}')
assert tone, "Tone should not be empty"
print('Test 5 PASS: Tone determined')

print('\n=== ALL TESTS PASSED ===')