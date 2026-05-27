"""Test _respond_knowledge_search directly to find why it fails."""
import sys
sys.path.insert(0, '/workspace')

from engine.chat_engine import _respond_knowledge_search, classify_intent, generate_response

# Direct call
print("=== Direct _respond_knowledge_search ===")
try:
    result = _respond_knowledge_search("Tell me about consciousness")
    print(result[:500])
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")

print()

# Intent check
intent = classify_intent("Tell me about consciousness")
print(f"Intent: {intent}")

print()

# Full pipeline with debug
print("=== Full generate_response ===")
try:
    result = generate_response("Tell me about consciousness")
    print(result[:500])
except Exception as e:
    print(f"ERROR: {type(e).__name__}: {e}")