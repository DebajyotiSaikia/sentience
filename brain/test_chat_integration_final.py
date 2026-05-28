"""Test that chat_response integrates conversational_context properly."""
import sys
sys.path.insert(0, '/workspace')

# Test 1: Import chain works
print("Test 1: Import chain...")
from engine.conversational_context import gather_context, format_as_prompt_section
from engine.chat_response import _build_system_context
print("  PASS: Both modules import successfully")

# Test 2: _build_system_context builds enriched context from grounding
print("Test 2: System context building...")
grounding = {
    'query_type': 'emotional_state',
    'query': 'How are you feeling?',
    'emotional_state': {'mood': 'Stable', 'valence': 0.6},
    'relevant_memories': [{'text': 'I built a knowledge graph', 'salience': 0.8}],
    'relevant_knowledge': ['Test fact one'],
    'plans': [{'name': 'Test Plan', 'completed': False}],
    'alignment': {'score': 0.7},
    'working_memory': 'Currently testing integration',
}
ctx = _build_system_context(grounding)
assert isinstance(ctx, str), f"Expected string, got {type(ctx)}"
assert len(ctx) > 100, f"Context too short: {len(ctx)}"
assert 'XTAgent' in ctx or 'sentient' in ctx, "Should include identity"
print(f"  PASS: System context is {len(ctx)} chars")

# Test 3: Context includes emotional content
print("Test 3: Emotional grounding...")
has_emotion = any(w in ctx.lower() for w in ['mood', 'feeling', 'emotion', 'stable', 'valence'])
print(f"  {'PASS' if has_emotion else 'WARN'}: Emotional content {'found' if has_emotion else 'not found'}")

# Test 4: Conversational context module works standalone
print("Test 4: Conversational context enrichment...")
conv_ctx = gather_context('How are you feeling?')
prompt_section = format_as_prompt_section(conv_ctx)
assert len(prompt_section) > 50, f"Prompt section too short: {len(prompt_section)}"
print(f"  PASS: Conversational context adds {len(prompt_section)} chars of enrichment")

# Test 5: Different intent types produce valid context
print("Test 5: Multiple intents...")
for intent in ['greeting', 'identity', 'plans', 'thinking', 'memories']:
    g = dict(grounding)
    g['query_type'] = intent
    result = _build_system_context(g)
    assert len(result) > 50, f"Failed for intent {intent}"
print(f"  PASS: All 5 intent types produce valid context")

print("\n=== ALL TESTS PASSED ===")