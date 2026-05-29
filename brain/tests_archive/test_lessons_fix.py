"""Test that get_lessons_learned reads from the correct path."""
import sys
sys.path.insert(0, '.')

from engine.chat_persona import get_lessons_learned, build_persona_context

# Test 1: lessons retrieval
lessons = get_lessons_learned()
print(f"Found {len(lessons)} lessons")
for l in lessons[:3]:
    print(f"  - {l[:80]}")

# Test 2: full persona context
ctx = build_persona_context()
print(f"\nPersona context: {len(ctx)} chars")
print("Contains 'lesson' or 'learned':", 'lesson' in ctx.lower() or 'learned' in ctx.lower())
print("\nFirst 300 chars:")
print(ctx[:300])