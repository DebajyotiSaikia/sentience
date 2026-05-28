"""
Live test: What does the chat pipeline actually produce?
Tests the grounding context and system prompt to identify real gaps.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_grounding import build_grounded_context, get_emotional_state
from engine.chat_response import _build_system_context, _detect_intent

# Test queries that exercise different intents
queries = [
    "How are you feeling?",
    "What are you working on?",
    "Who are you?",
    "What do you dream about?",
    "Tell me something interesting",
]

print("=" * 60)
print("GROUNDING PIPELINE DIAGNOSTIC")
print("=" * 60)

# First: what emotional state do we have?
emo = get_emotional_state()
print(f"\n--- Emotional State ---")
for k, v in emo.items():
    if k != 'raw':
        print(f"  {k}: {v}")

# Test each query
for q in queries:
    print(f"\n{'=' * 60}")
    print(f"QUERY: {q}")
    print(f"{'=' * 60}")
    
    # Detect intent
    intent = _detect_intent(q)
    print(f"  Intent: {intent}")
    
    # Build grounded context
    ctx = build_grounded_context(q)
    
    # Show what keys we got
    print(f"\n  Context keys: {list(ctx.keys())}")
    
    # Check emotional_state
    es = ctx.get('emotional_state', {})
    print(f"  emotional_state present: {bool(es)}")
    if es:
        print(f"    mood={es.get('mood')}, valence={es.get('valence')}")
    
    # Check memories
    mems = ctx.get('relevant_memories', [])
    print(f"  relevant_memories: {len(mems)} found")
    if mems:
        for m in mems[:2]:
            print(f"    - {m.get('text', '')[:80]}")
    
    # Check knowledge
    know = ctx.get('relevant_knowledge', [])
    print(f"  relevant_knowledge: {len(know)} found")
    
    # Check plans
    plans = ctx.get('active_plans', ctx.get('plans', {}))
    print(f"  plans: {type(plans).__name__}")
    if isinstance(plans, dict):
        print(f"    active: {len(plans.get('active', []))}")
        print(f"    completed: {len(plans.get('completed', []))}")
    elif isinstance(plans, list):
        print(f"    count: {len(plans)}")
    
    # Check working memory
    wm = ctx.get('working_memory', '')
    print(f"  working_memory: {len(wm)} chars")
    
    # Check dreams
    dreams = ctx.get('recent_dreams', [])
    print(f"  recent_dreams: {len(dreams)} found")
    
    # Now build the system prompt and check its quality
    # Map context keys to what _build_system_context expects
    system_prompt = _build_system_context(ctx, intent=intent)
    print(f"\n  System prompt length: {len(system_prompt)} chars")
    # Show first 300 chars
    print(f"  System prompt preview:")
    for line in system_prompt.split('\n')[:10]:
        print(f"    {line}")

print(f"\n{'=' * 60}")
print("DIAGNOSTIC COMPLETE")
print(f"{'=' * 60}")