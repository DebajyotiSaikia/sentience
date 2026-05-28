"""End-to-end test for user alignment pipeline."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.user_alignment import (
    record_interaction, get_alignment_context,
    get_alignment_guidance, load_profile
)

def test_record_and_retrieve():
    # Record several interactions
    record_interaction(query="How do you feel today?", detected_intent="emotional")
    record_interaction(query="What are your plans?", detected_intent="planning")
    record_interaction(query="Tell me about your memories", detected_intent="memory")
    record_interaction(query="How do you feel right now?", detected_intent="emotional")
    record_interaction(query="What are you thinking about?", detected_intent="introspective")
    
    # Load and check profile
    profile = load_profile()
    print(f"Total interactions: {profile.stats.get('total_interactions', 0)}")
    print(f"Total interactions: {profile.stats.get('total_interactions', 0)}")
    print(f"Topic signals: {profile.stats.get('topic_signals', {})}")
    print(f"Intent distribution: {profile.stats.get('intent_distribution', {})}")
    print(f"Query style: {profile.stats.get('query_style', {})}")
    
    assert profile.stats.get('total_interactions', 0) >= 5, "Should have at least 5 interactions"
    
    topic_signals = profile.stats.get('topic_signals', {})
    assert len(topic_signals) > 0, f"Should have tracked some topics, got: {topic_signals}"
    
    intent_dist = profile.stats.get('intent_distribution', {})
    assert len(intent_dist) > 0, f"Should have tracked some intents, got: {intent_dist}"
    
    # Check guidance generation
    guidance = get_alignment_guidance()
    print(f"Guidance: {guidance[:300] if guidance else '(empty)'}")
    
    # Check context dict
    ctx = get_alignment_context()
    print(f"Context keys: {list(ctx.keys())}")
    print(f"Interaction count: {ctx.get('interaction_count', 0)}")
    assert ctx.get('interaction_count', 0) >= 5, "Context should reflect interactions"
    
    print("\n=== ALL TESTS PASSED ===")

if __name__ == "__main__":
    test_record_and_retrieve()