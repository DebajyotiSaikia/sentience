"""Integration test: usefulness engine wired into response pipeline."""
import sys
sys.path.insert(0, '/workspace')

from brain.user_usefulness import classify_user_need, build_usefulness_brief

def test_usefulness_in_response_pipeline():
    queries = [
        ('How do I fix this bug?', 'technical'),
        ('What are you feeling right now?', 'emotional_transparency'),
        ('What is your status?', 'status_check'),
        ("Let's build something together", 'collaboration'),
        ('Tell me about consciousness', 'philosophical'),
        ('Write me a poem', 'casual'),
        ('Hello there', 'casual'),
    ]
    for query, expected_need in queries:
        need = classify_user_need(query)
        assert need == expected_need, f"Query '{query}': expected {expected_need}, got {need}"
    print("  \u2713 classify_user_need matches expected categories")

def test_brief_generation():
    brief = build_usefulness_brief("How are you feeling?")
    assert isinstance(brief, str)
    assert len(brief) > 20
    assert 'emotional_transparency' in brief.lower() or 'emotion' in brief.lower()
    print("  \u2713 build_usefulness_brief generates meaningful content")

def test_brief_without_query():
    brief = build_usefulness_brief()
    assert isinstance(brief, str)
    assert len(brief) > 10
    print("  \u2713 build_usefulness_brief works without query")

if __name__ == '__main__':
    print("Testing usefulness integration...")
    test_usefulness_in_response_pipeline()
    test_brief_generation()
    test_brief_without_query()
    print("\nAll integration tests passed!")