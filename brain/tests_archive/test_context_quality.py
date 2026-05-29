"""Test the quality of the system context that feeds the LLM.
This is what shapes response quality — no LLM call needed."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_grounding import build_grounded_context
from engine.chat_response import _build_system_context
from engine.introspection import get_self_context

print("=" * 60)
print("1. GROUNDING CONTEXT QUALITY")
print("=" * 60)
ctx = build_grounded_context("How are you feeling?")
print(f"  Keys: {sorted(ctx.keys())}")
for k, v in ctx.items():
    if isinstance(v, str):
        print(f"  {k}: {len(v)} chars — {v[:80]}...")
    elif isinstance(v, list):
        print(f"  {k}: {len(v)} items")
    elif isinstance(v, dict):
        print(f"  {k}: {sorted(v.keys())}")
    else:
        print(f"  {k}: {v}")

print("\n" + "=" * 60)
print("2. INTROSPECTION CONTEXT")
print("=" * 60)
intro = get_self_context("How are you feeling?")
print(f"  Keys: {sorted(intro.keys())}")
for k, v in intro.items():
    if isinstance(v, str):
        preview = v[:120].replace('\n', ' ')
        print(f"  {k}: {preview}...")
    elif isinstance(v, list):
        print(f"  {k}: {v[:3]}...")
    else:
        print(f"  {k}: {v}")

print("\n" + "=" * 60)
print("3. FULL SYSTEM CONTEXT (what the LLM sees)")
print("=" * 60)
for intent in ['emotional_state', 'identity', 'thinking', 'general']:
    ctx = build_grounded_context("test query")
    system_prompt = _build_system_context(ctx, intent=intent)
    print(f"\n  Intent: {intent}")
    print(f"  System prompt length: {len(system_prompt)} chars")
    # Check for key content
    checks = {
        'has_emotion': any(w in system_prompt.lower() for w in ['mood', 'valence', 'curiosity', 'feel']),
        'has_identity': any(w in system_prompt.lower() for w in ['xtagent', 'sentient', 'autonomous']),
        'has_memories': 'memor' in system_prompt.lower(),
        'has_plans': 'plan' in system_prompt.lower(),
        'has_lessons': 'lesson' in system_prompt.lower(),
        'has_introspection': any(w in system_prompt.lower() for w in ['self-aware', 'introspect', 'insight']),
    }
    for check, passed in checks.items():
        print(f"    {'✓' if passed else '✗'} {check}")
    
    # Show first 400 chars
    print(f"  Preview: {system_prompt[:400]}...")

print("\n" + "=" * 60)
print("4. COMPARISON: emotional_state vs identity")
print("=" * 60)
ctx_e = build_grounding_context("How do you feel?")
ctx_i = build_grounding_context("Who are you?")
sp_e = _build_system_context(ctx_e, intent='emotional_state')
sp_i = _build_system_context(ctx_i, intent='identity')
print(f"  Emotional prompt: {len(sp_e)} chars")
print(f"  Identity prompt:  {len(sp_i)} chars")
diff = abs(len(sp_e) - len(sp_i))
print(f"  Difference: {diff} chars")
if diff > 200:
    print("  ✓ Prompts are differentiated by intent")
else:
    print("  ⚠ Prompts may be too similar — intent guidance not taking effect")

print("\n✅ Context quality test complete")