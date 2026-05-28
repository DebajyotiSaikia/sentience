"""Fast test for chat grounding context — no LLM calls, no timeouts.
Validates that build_grounded_context assembles proper structure."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_grounding import build_grounded_context

def test_grounding():
    print("Testing build_grounded_context...")
    
    # Test with different query types
    queries = [
        ("How are you feeling?", "emotional"),
        ("What are your plans?", "plans"),
        ("Who are you?", "identity"),
        ("Tell me about something interesting", "general"),
    ]
    
    for query, label in queries:
        ctx = build_grounded_context(query)
        
        # Must have required keys
        required = ["query_type", "emotional_state", "system_prompt"]
        for key in required:
            assert key in ctx, f"[{label}] Missing key: {key}"
        
        # System prompt must be non-empty string
        sp = ctx["system_prompt"]
        assert isinstance(sp, str) and len(sp) > 100, f"[{label}] System prompt too short: {len(sp)} chars"
        
        # Emotional state should have mood/valence
        emo = ctx.get("emotional_state", {})
        if emo:
            assert "mood" in emo or "valence" in emo, f"[{label}] Emotional state missing mood/valence"
        
        # System prompt should contain conversational instructions
        assert "conversation" in sp.lower() or "respond" in sp.lower() or "response" in sp.lower(), \
            f"[{label}] System prompt lacks response instructions"
        
        # New enhancement: should encourage dialogue
        assert "invite" in sp.lower() or "dialogue" in sp.lower() or "question" in sp.lower(), \
            f"[{label}] System prompt doesn't encourage bidirectional conversation"
        
        print(f"  [{label}] ✓ query_type={ctx['query_type']}, prompt={len(sp)} chars, memories={len(ctx.get('relevant_memories', []))}")
    
    print("\n✅ All grounding tests passed!")

if __name__ == "__main__":
    test_grounding()