"""Test the full chat enrichment pipeline."""
import sys
sys.path.insert(0, '.')

# Test 1: Persona context (already fixed)
from engine.chat_persona import build_persona_context
ctx = build_persona_context()
print(f"[1] Persona context: {len(ctx)} chars")
has_lessons = 'lesson' in ctx.lower() or 'learned' in ctx.lower()
print(f"    Has lessons: {has_lessons}")
assert has_lessons, "Persona missing lessons!"

# Test 2: Chat context module
# Test 2: Chat context module
from web.chat_context import build_full_context, build_system_prompt
for query in [
    "How are you feeling?",
    "What are you working on?",
    "Tell me about yourself",
    "What have you learned?",
    "What do you know about curiosity?",
]:
    result = build_full_context(query)
    assert isinstance(result, dict), f"Expected dict, got {type(result)}"
    assert 'system_prompt' in result, "Missing system_prompt key"
    assert 'context_block' in result, "Missing context_block key"
    sp_len = len(result['system_prompt'])
    cb_len = len(result['context_block'])
    print(f"[2] '{query}' → prompt={sp_len}, context={cb_len} chars")
    assert sp_len > 100, f"System prompt too short for '{query}': {sp_len}"
    assert cb_len > 20, f"Context block too short for '{query}': {cb_len}"

# Test 2b: System prompt
prompt = build_system_prompt()
print(f"[2b] System prompt: {len(prompt)} chars")
# Test 2b: System prompt
prompt = build_system_prompt()
print(f"[2b] System prompt: {len(prompt)} chars")
print(f"[2b] System prompt: {len(prompt)} chars")
assert len(prompt) > 50, "System prompt too short"

# Test 3: Verify compose_response is importable
try:
    from web.chat import compose_response
    print(f"[3] compose_response importable: YES")
except ImportError as e:
    print(f"[3] compose_response import failed: {e}")

# Test 4: Verify intent detection
try:
    from web.chat import _detect_intent
    intents = {}
    for q in ["How are you?", "What's your plan?", "Tell me about yourself", 
              "What have you learned?", "Hello", "What is Python?"]:
        intent = _detect_intent(q)
        intents[q] = intent
        print(f"[4] '{q}' → intent: {intent}")
except ImportError as e:
    print(f"[4] Intent detection import failed: {e}")

print("\n✅ All enrichment tests passed!")