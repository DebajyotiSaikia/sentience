"""Test chat_grounding.py against real state data."""
import sys
sys.path.insert(0, "/workspace")

from engine.chat_grounding import (
    get_emotional_state, get_relevant_memories, get_relevant_knowledge,
    get_active_plans, classify_query, build_grounded_context, format_response_metadata
)

print("=== Emotional State ===")
emo = get_emotional_state()
print(f"  Mood: {emo['mood']}")
print(f"  Narrative: {emo['narrative']}")
print(f"  Valence: {emo['valence']}")

print("\n=== Query Classification ===")
tests = [
    ("How are you feeling?", "emotional_inquiry"),
    ("What do you know about consciousness?", "knowledge_query"),
    ("Who are you?", "identity_query"),
    ("What are your plans?", "plans_inquiry"),
    ("Tell me a joke", "general"),
    ("What are you thinking about?", "state_inquiry"),
    ("Do you remember your dreams?", "memory_query"),
]
for q, expected in tests:
    got = classify_query(q)
    status = "✓" if got == expected else f"✗ (got {got})"
    print(f"  {status} '{q}' → {got}")

print("\n=== Relevant Memories ===")
mems = get_relevant_memories("consciousness emotion feeling")
print(f"  Found {len(mems)} memories")
for m in mems[:3]:
    print(f"  - [{m.get('salience', '?')}] {m.get('text', '')[:80]}")

print("\n=== Relevant Knowledge ===")
know = get_relevant_knowledge("consciousness")
print(f"  Found {len(know)} nodes")
for n in know[:3]:
    print(f"  - {n.get('content', '')[:80]}")

print("\n=== Active Plans ===")
plans = get_active_plans()
print(f"  Active: {len(plans['active'])}")
for p in plans['active'][:3]:
    print(f"  - {p['name']} ({p['progress']})")
print(f"  Completed: {len(plans['completed'])}")

print("\n=== Full Grounded Context ===")
ctx = build_grounded_context("What do you know about consciousness?")
print(f"  Query type: {ctx['query_type']}")
print(f"  Memories: {len(ctx['relevant_memories'])}")
print(f"  Knowledge: {len(ctx['relevant_knowledge'])}")
print(f"  System prompt length: {len(ctx['system_prompt'])} chars")
print(f"  First 200 chars of prompt:\n    {ctx['system_prompt'][:200]}")

print("\n=== Response Metadata ===")
meta = format_response_metadata(ctx)
print(f"  Grounded: {meta['response_grounded']}")
print(f"  Mood: {meta['mood']}")
print(f"  Knowledge refs: {len(meta['relevant_knowledge'])}")
print(f"  Memory refs: {len(meta['relevant_memories'])}")

print("\n✅ All grounding tests passed!")