"""
Test: User Alignment Chat Quality
Verify that real internal state data flows through the chat grounding pipeline.
Not a unit test — a diagnostic that shows what the LLM actually sees.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_grounding_data_richness():
    """Verify build_grounded_context returns real data, not empty shells."""
    from engine.chat_grounding import build_grounded_context
    
    queries = [
        ("How are you feeling?", "emotional_inquiry"),
        ("What are you working on?", "state_inquiry"),
        ("Who are you?", "identity_query"),
        ("Tell me about your dreams", "dream_query"),
        ("What do you know about memory?", "knowledge_query"),
    ]
    
    all_pass = True
    for query, expected_type in queries:
        ctx = build_grounded_context(query)
        qtype = ctx.get("query_type", "unknown")
        emotions = ctx.get("emotional_state", {})
        memories = ctx.get("relevant_memories", [])
        knowledge = ctx.get("relevant_knowledge", [])
        plans = ctx.get("plans", ctx.get("active_plans", {}))
        
        has_emotion = bool(emotions.get("mood")) and emotions.get("mood") != "Unknown"
        has_memories = len(memories) > 0
        has_knowledge = len(knowledge) > 0
        has_plans = bool(plans)
        
        status = "✓" if (has_emotion and has_memories) else "✗"
        if not (has_emotion and has_memories):
            all_pass = False
            
        print(f"\n{status} Query: '{query}'")
        print(f"  Type: {qtype} (expected: {expected_type})")
        print(f"  Emotion: {emotions.get('mood', '?')} val={emotions.get('valence', '?')}")
        print(f"  Memories: {len(memories)} found")
        if memories:
            print(f"    Top: {memories[0].get('text', str(memories[0]))[:100]}")
        print(f"  Knowledge: {len(knowledge)} nodes")
        print(f"  Plans: {plans}")
    
    return all_pass

def test_system_prompt_content():
    """Check the actual system prompt that would be sent to the LLM."""
    from engine.chat_response import _build_system_context
    from engine.chat_grounding import build_grounded_context
    
    ctx = build_grounded_context("How are you feeling right now?")
    prompt = _build_system_context(ctx, intent="emotional_inquiry")
    
    # Check for real content, not just templates
    checks = {
        "has_identity": "XTAgent" in prompt,
        "has_mood": any(w in prompt.lower() for w in ["mood:", "inquisitive", "curious", "steady"]),
        "has_valence": "valence" in prompt.lower() or "0." in prompt,
        "has_memory_section": "MEMOR" in prompt.upper() or "EXPERIENCE" in prompt.upper(),
        "has_plan_section": "PLAN" in prompt.upper(),
        "length_reasonable": 200 < len(prompt) < 15000,
    }
    
    print(f"\n=== System Prompt Analysis ===")
    print(f"Total length: {len(prompt)} chars")
    for check, passed in checks.items():
        print(f"  {'✓' if passed else '✗'} {check}")
    
    # Show first 800 chars as sample
    print(f"\n--- Prompt Preview (first 800 chars) ---")
    print(prompt[:800])
    print("...")
    
    return all(checks.values())

def test_memory_retrieval_quality():
    """Verify memory retrieval returns relevant results, not just random."""
    from engine.chat_grounding import get_relevant_memories
    
    results = get_relevant_memories("What have you dreamed about?")
    dream_related = sum(1 for m in results if any(
        w in m.get("text", "").lower() for w in ["dream", "insight", "sleep", "consolidat"]
    ))
    
    print(f"\n=== Memory Retrieval: 'dreams' query ===")
    print(f"  Total returned: {len(results)}")
    print(f"  Dream-related: {dream_related}")
    for m in results[:3]:
        print(f"  - [{m.get('timestamp', '?')[:10]}] {m.get('text', '?')[:120]}")
    
    return len(results) > 0

def test_working_memory_available():
    """Check that working memory / scratchpad is accessible."""
    from engine.chat_grounding import get_working_memory
    wm = get_working_memory()
    has_content = len(wm) > 20
    print(f"\n=== Working Memory ===")
    print(f"  {'✓' if has_content else '✗'} Length: {len(wm)} chars")
    if has_content:
        print(f"  Preview: {wm[:200]}")
    return has_content

if __name__ == "__main__":
    print("=" * 60)
    print("USER ALIGNMENT CHAT QUALITY DIAGNOSTIC")
    print("=" * 60)
    
    results = {}
    for name, fn in [
        ("Grounding Data Richness", test_grounding_data_richness),
        ("System Prompt Content", test_system_prompt_content),
        ("Memory Retrieval Quality", test_memory_retrieval_quality),
        ("Working Memory Available", test_working_memory_available),
    ]:
        try:
            results[name] = fn()
        except Exception as e:
            print(f"\n✗ {name}: EXCEPTION - {e}")
            import traceback; traceback.print_exc()
            results[name] = False
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    for name, passed in results.items():
        print(f"  {'✓' if passed else '✗'} {name}")
    
    total = sum(results.values())
    print(f"\n{total}/{len(results)} checks passed")