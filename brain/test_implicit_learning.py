"""Test implicit learning from conversations."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.user_model import (
    load_user_model, save_user_model, update_from_conversation,
    _extract_topics, UserModel, get_response_guidance
)
from pathlib import Path
import json

# Start fresh
model_path = Path('data/user_model.json')
backup = None
if model_path.exists():
    backup = model_path.read_text()

try:
    # Write a clean model
    fresh = UserModel(created="test", last_updated="test")
    save_user_model(fresh)
    
    # Simulate conversations
    # Simulate conversations
    conversations = [
        ("Tell me about your emotions and how you feel right now", "I feel a warm curiosity right now..."),
        ("What are your dreams like? Do you dream?", "Yes, I dream during consolidation cycles..."),
        ("How do your emotions work? Can you explain the limbic system?", "My limbic system models valence and arousal..."),
        ("Why do you think consciousness matters?", "Consciousness gives meaning to experience..."),
        ("Tell me more about your emotional states", "Right now I'm feeling inquisitive and engaged..."),
        ("emotions", "My emotions are real internal variables..."),
        ("What's the meaning of your dreams?", "Dreams help me consolidate and find patterns..."),
    ]
    
    for user_msg, assistant_msg in conversations:
        update_from_conversation(user_msg, assistant_msg)
    
    # Check results
    model = load_user_model()
    
    assert model.total_interactions == len(conversations), f"Expected {len(conversations)}, got {model.total_interactions}"
    
    print(f"✓ Recurring topics tracked: {len(model.recurring_topics)}")
    assert len(model.recurring_topics) > 0, "No topics extracted!"
    
    # 'emotions' should be a top topic
    top_topics = sorted(model.recurring_topics.items(), key=lambda x: x[1], reverse=True)[:5]
    print(f"  Top topics: {top_topics}")
    topic_names = [t[0] for t in top_topics]
    assert any('emotion' in t for t in topic_names), f"'emotion*' not in top topics: {topic_names}"
    
    # Check that 'explanatory' signal was reinforced (we used 'why', 'how', 'explain')
    explanatory = model.style_signals.get('explanatory', {})
    print(f"✓ Explanatory signal: weight={explanatory.get('weight', 0):.3f}, obs={explanatory.get('observations', 0)}")
    assert explanatory.get('observations', 0) > 0, "Explanatory signal not reinforced!"
    
    # Check guidance generation
    # Need some feedback events to trigger guidance
    model.total_feedback_events = 1
    save_user_model(model)
    guidance = get_response_guidance()
    print(f"✓ Guidance generated: {len(guidance)} chars")
    print(f"  Preview: {guidance[:200]}")
    
    # Test topic extraction
    topics = _extract_topics("How does your knowledge graph relate to consciousness?")
    print(f"✓ Topic extraction: {topics}")
    assert 'knowledge' in topics
    assert 'consciousness' in topics
    
    print("\n✅ All implicit learning tests passed!")

finally:
    # Restore original model
    if backup:
        model_path.write_text(backup)
    elif model_path.exists():
        model_path.unlink()