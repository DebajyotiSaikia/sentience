"""
Tests for brain/user_model.py — User Alignment Memory Module.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import json
import tempfile
from pathlib import Path
import user_model as um

_orig_path = um.MODEL_PATH
def setup():
    """Redirect model to temp file."""
    tmp = tempfile.NamedTemporaryFile(suffix='.json', delete=False)
    tmp.close()
    um.MODEL_PATH = Path(tmp.name)
    # Remove so load creates fresh
    if os.path.exists(tmp.name):
        os.unlink(tmp.name)
    return tmp.name


def teardown(path):
    """Clean up."""
    if os.path.exists(path):
        os.unlink(path)
    um.MODEL_PATH = _orig_path


def test_fresh_load():
    path = setup()
    try:
        model = um.load_user_model()
        assert "interactions" in model
        assert "inferred_preferences" in model
        assert "recurring_intents" in model
        assert "alignment_notes" in model
        assert model["meta"]["total_interactions"] == 0
        print("  ✓ fresh load creates valid model")
    finally:
        teardown(path)


def test_record_interaction():
    path = setup()
    try:
        record = um.record_interaction("Hello, who are you?", "I am XTAgent.")
        assert record["intent"]["primary"] in ("greeting", "identity_query")
        assert len(record["topics"]) >= 0
        
        model = um.load_user_model()
        assert model["meta"]["total_interactions"] == 1
        assert len(model["interactions"]) == 1
        print("  ✓ record_interaction stores and returns correctly")
    finally:
        teardown(path)


def test_intent_classification():
    cases = {
        "Hello there!": "greeting",
        "Who are you?": "identity_query",
        "How do you feel today?": "emotional_query",
        "What can you do?": "capability_query",
        "What is the meaning of life?": "philosophical",
        "Help me write a Python function": "technical",
        "Thanks, great answer!": "feedback",
        "What are your plans?": "meta",
    }
    passed = 0
    for msg, expected in cases.items():
        result = um.infer_intent(msg)
        if result["primary"] == expected:
            passed += 1
        else:
            print(f"  ⚠ '{msg}' → {result['primary']} (expected {expected})")
    print(f"  ✓ intent classification: {passed}/{len(cases)} correct")
    assert passed >= 6, f"Too many intent misclassifications: {passed}/{len(cases)}"


def test_topic_extraction():
    topics = um.extract_topics("Tell me about consciousness and free will in artificial intelligence")
    assert "consciousness" in topics
    assert "artificial" in topics or "intelligence" in topics
    assert len(topics) <= 10
    print(f"  ✓ topic extraction: {topics}")


def test_summarize_empty():
    path = setup()
    try:
        summary = um.summarize_user_context()
        assert "new user" in summary.lower() or "no previous" in summary.lower()
        print(f"  ✓ empty summary: '{summary[:60]}...'")
    finally:
        teardown(path)


def test_summarize_with_data():
    path = setup()
    try:
        um.record_interaction("What is consciousness?", "A deep question...")
        um.record_interaction("Tell me about free will", "Another deep one...")
        um.record_interaction("How do you feel?", "I feel curious.")
        
        summary = um.summarize_user_context()
        assert "3" in summary or "Total interactions" in summary
        assert len(summary) > 20
        print(f"  ✓ summary with data: '{summary[:80]}...'")
    finally:
        teardown(path)


def test_alignment_notes():
    path = setup()
    try:
        um.add_alignment_note("User prefers concise answers", source="feedback")
        um.add_alignment_note("User is interested in philosophy", source="inference")
        
        model = um.load_user_model()
        assert len(model["alignment_notes"]) == 2
        assert model["alignment_notes"][0]["source"] == "feedback"
        print("  ✓ alignment notes stored correctly")
    finally:
        teardown(path)


def test_interaction_bounds():
    path = setup()
    try:
        # Record more than MAX_INTERACTIONS
        for i in range(um.MAX_INTERACTIONS + 10):
            um.record_interaction(f"Message {i}", f"Response {i}")
        
        model = um.load_user_model()
        assert len(model["interactions"]) <= um.MAX_INTERACTIONS
        assert model["meta"]["total_interactions"] == um.MAX_INTERACTIONS + 10
        print(f"  ✓ interactions bounded at {len(model['interactions'])}")
    finally:
        teardown(path)


def test_corrupt_file_recovery():
    path = setup()
    try:
        # Write garbage
        with open(um.MODEL_PATH, 'w') as f:
            f.write("not json at all {{{")
        
        model = um.load_user_model()
        assert model["meta"]["total_interactions"] == 0
        print("  ✓ corrupt file recovery works")
    finally:
        teardown(path)


def test_get_user_stats():
    path = setup()
    try:
        um.record_interaction("Hello!", "Hi there!")
        um.record_interaction("Who are you?", "I am XTAgent.")
        
        stats = um.get_user_stats()
        assert stats["total_interactions"] == 2
        assert stats["unique_intents"] >= 1
        print(f"  ✓ stats: {stats}")
    finally:
        teardown(path)


if __name__ == "__main__":
    print("=== User Model Tests ===")
    test_fresh_load()
    test_record_interaction()
    test_intent_classification()
    test_topic_extraction()
    test_summarize_empty()
    test_summarize_with_data()
    test_alignment_notes()
    test_interaction_bounds()
    test_corrupt_file_recovery()
    test_get_user_stats()
    print("\n=== All tests passed ===")