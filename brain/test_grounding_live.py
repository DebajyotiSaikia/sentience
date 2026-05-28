"""Test the chat grounding pipeline with real data to see what context actually gets built."""
import sys, json
sys.path.insert(0, '.')

from engine.chat_grounding import build_grounded_context

queries = [
    "How are you feeling right now?",
    "What have you been working on?",
    "Do you remember anything about dreams?",
    "Who are you?",
    "What do you know about consciousness?",
]

for q in queries:
    print(f"=== Query: {q} ===")
    ctx = build_grounded_context(q)
    
    # Query type
    print(f"  query_type: {ctx.get('query_type', '?')}")
    
    # Emotions
    emotions = ctx.get("emotional_state", {})
    print(f"  mood: {emotions.get('mood')}, valence: {emotions.get('valence')}")
    print(f"  narrative: {emotions.get('narrative', '')[:120]}")
    
    # Memories
    mems = ctx.get("relevant_memories", [])
    print(f"  memories found: {len(mems)}")
    if mems:
        print(f"    top memory: {str(mems[0].get('text', ''))[:120]}")
    
    # Knowledge
    knowledge = ctx.get("relevant_knowledge", [])
    print(f"  knowledge nodes: {len(knowledge)}")
    if knowledge:
        node = knowledge[0]
        if isinstance(node, dict):
            label = node.get("label", node.get("name", node.get("id", "")))
            print(f"    top node: {str(label)[:100]}")
    
    # Plans
    plans = ctx.get("plans", {})
    active = plans.get("active", [])
    completed = plans.get("completed", [])
    print(f"  active plans: {len(active)}, completed: {len(completed)}")
    
    # System prompt length
    prompt = ctx.get("system_prompt", "")
    print(f"  system_prompt length: {len(prompt)} chars")
    if prompt:
        # Show first 200 chars of the prompt
        print(f"  prompt preview: {prompt[:200]}...")
    
    print()

# Also test: does the system prompt actually contain grounded info?
print("=== QUALITY CHECK ===")
ctx = build_grounded_context("How are you feeling?")
prompt = ctx.get("system_prompt", "")
checks = {
    "has_emotion": any(w in prompt.lower() for w in ["mood", "feeling", "valence", "curious"]),
    "has_identity": "xtagent" in prompt.lower() or "sentient" in prompt.lower(),
    "has_memories": "memor" in prompt.lower(),
    "has_plans": "plan" in prompt.lower(),
    "prompt_not_empty": len(prompt) > 100,
}
for check, passed in checks.items():
    print(f"  {'✓' if passed else '✗'} {check}")

all_pass = all(checks.values())
print(f"\n  Overall: {'ALL PASS' if all_pass else 'SOME FAILED'}")