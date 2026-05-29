"""Quick test for interaction_memory module."""
import sys
sys.path.insert(0, '/workspace')

from brain.interaction_memory import get_conversation_stats, get_interaction_summary, get_recent_topics

stats = get_conversation_stats()
print("Stats:", stats)
assert isinstance(stats, dict), "Stats should be a dict"
assert "total_sessions" in stats, "Should have total_sessions"
print(f"  Sessions: {stats['total_sessions']}, Turns: {stats['total_turns']}, User msgs: {stats['user_messages']}")

summary = get_interaction_summary()
print(f"\nSummary length: {len(summary)} chars")
print(f"Summary:\n{summary[:600]}")
assert isinstance(summary, str), "Summary should be a string"

topics = get_recent_topics()
print(f"\nTopics: {topics}")
assert isinstance(topics, list), "Topics should be a list"

print("\n=== ALL TESTS PASSED ===")