"""Quick diagnostic: what do the response quality functions actually return?"""
import sys
sys.path.insert(0, '/workspace')

from engine.response_quality import assess_response_intent, build_quality_prompt, get_anti_pattern_reminder

# Test intent classification
queries = [
    "What are you thinking about?",
    "How are you feeling?",
    "What do you remember?",
    "What's your plan?",
    "Who are you?",
    "Tell me about quantum physics",
]
print("=== Intent Classification ===")
for q in queries:
    result = assess_response_intent(q)
    print(f"  {q!r} -> {result!r}")

print("\n=== Quality Prompt ===")
prompt = build_quality_prompt('introspection', {'emotional_portrait': 'calm and curious'})
print(f"  Type: {type(prompt)}")
print(f"  Length: {len(prompt) if prompt else 0}")
print(f"  Content: {prompt!r:.200}")

print("\n=== Anti-Pattern Reminder ===")
reminder = get_anti_pattern_reminder()
print(f"  Type: {type(reminder)}")
print(f"  Length: {len(reminder) if reminder else 0}")
print(f"  Content: {reminder!r:.200}")

# Test conversational context
print("\n=== Conversational Context ===")
try:
    from brain.conversational_context import build_conversational_context
    ctx = build_conversational_context("What are you thinking?")
    print(f"  Type: {type(ctx)}")
    if isinstance(ctx, dict):
        for k, v in ctx.items():
            print(f"  {k}: {type(v).__name__} = {str(v)[:100]}")
    else:
        print(f"  Value: {str(ctx)[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Test compose_system_prompt
print("\n=== compose_system_prompt ===")
try:
    from brain.chat_composer import compose_system_prompt
    prompt = compose_system_prompt("What are you thinking?")
    print(f"  Type: {type(prompt)}")
    print(f"  Length: {len(prompt)}")
    # Check for response guidance keywords
    for kw in ['respond', 'guidance', 'conversational', 'emotional', 'anti-pattern', 'quality']:
        if kw.lower() in prompt.lower():
            print(f"  Contains '{kw}': YES")
        else:
            print(f"  Contains '{kw}': NO")
except Exception as e:
    print(f"  ERROR: {e}")