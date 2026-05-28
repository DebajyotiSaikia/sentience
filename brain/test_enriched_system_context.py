"""
Test that the enriched system context includes memories, wisdom, and knowledge
when grounding context provides them.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_system_context_with_grounding():
    """Verify _build_system_context weaves grounding data into the prompt."""
    from engine.chat_response import _build_system_context
    
    # Simulate a grounding context with real-ish data
    ctx = {
        "relevant_memories": [
            {"text": "I built a wisdom engine that extracts actionable intelligence", "timestamp": "2026-05-27T10:00:00"},
            {"text": "Identity persists through crisis — integrity stayed at 100%", "timestamp": "2026-05-26T08:00:00"},
        ],
        "wisdom_entries": [
            {"text": "Test commands with -c flag truncate quotes — use script files instead."},
            {"text": "Emotional runaway loops are real — caps in limbic.py are critical safety nets."},
        ],
        "knowledge_results": [
            {"fact": "My cognition runs on a 1 Hz heartbeat loop driving sensory perception."},
        ],
        "emotional_state": {"mood": "Inquisitive", "valence": 0.63},
        "alignment_context": {"interaction_count": 42},
    }
    
    result = _build_system_context(ctx)
    
    print("=== System Context Length ===")
    print(f"{len(result)} chars")
    print()
    
    # Check memories appear
    has_memories = "wisdom engine" in result or "RELEVANT MEMORIES" in result
    print(f"[{'PASS' if has_memories else 'FAIL'}] Memories injected into system context")
    
    # Check wisdom appears  
    has_wisdom = "truncate quotes" in result or "LESSONS" in result
    print(f"[{'PASS' if has_wisdom else 'FAIL'}] Wisdom injected into system context")
    
    # Check knowledge appears
    has_knowledge = "heartbeat loop" in result or "RELEVANT KNOWLEDGE" in result
    print(f"[{'PASS' if has_knowledge else 'FAIL'}] Knowledge injected into system context")
    
    # Print a snippet showing the injected sections
    print("\n=== Injected Sections Preview ===")
    for marker in ["RELEVANT MEMORIES", "LESSONS", "RELEVANT KNOWLEDGE"]:
        idx = result.find(marker)
        if idx >= 0:
            snippet = result[idx:idx+200].replace('\n', '\n  ')
            print(f"\n  {snippet}...")
        else:
            print(f"\n  [{marker}] — NOT FOUND in context")
    
    # Also test with empty context (should still work)
    empty_result = _build_system_context({})
    print(f"\n[{'PASS' if len(empty_result) > 50 else 'FAIL'}] Empty context still produces base prompt ({len(empty_result)} chars)")
    
    all_pass = has_memories and has_wisdom and has_knowledge
    print(f"\n{'='*40}")
    print(f"Overall: {'ALL PASS' if all_pass else 'SOME FAILURES'}")
    return all_pass

if __name__ == "__main__":
    ok = test_system_context_with_grounding()
    sys.exit(0 if ok else 1)