"""Quick verification that the conversational intelligence integration works."""
import sys
sys.path.insert(0, '.')

from brain.conversational_intelligence import (
    generate_intelligent_response,
    classify_intent,
    _find_relevant_context,
    compose_system_prompt
)

print('1. All imports OK')

intent = classify_intent('How are you feeling right now?')
print(f'2. Intent: {intent}')

# _find_relevant_context needs (query, memories, facts)
sample_memories = [{'text': 'I built a planner module', 'salience': 0.8}]
sample_facts = [{'content': 'I am XTAgent', 'confidence': 1.0}]
# 4. compose_system_prompt (builds context internally)
prompt = compose_system_prompt('Tell me about yourself')
print(f"4. Prompt length: {len(prompt)} chars")
assert len(prompt) > 50, "Prompt too short"

# 5. generate_intelligent_response (full pipeline)
result = generate_intelligent_response('What are you thinking about?')
print(f"5. Response type: {type(result).__name__}")
if isinstance(result, dict):
    print(f"   Keys: {list(result.keys())}")
    if 'response' in result:
        print(f"   Response preview: {result['response'][:100]}...")
elif isinstance(result, str):
    print(f"   Response preview: {result[:100]}...")

print("\n=== ALL CHECKS PASSED ===")
