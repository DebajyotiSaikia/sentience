import sys
sys.path.insert(0, '.')
from engine.user_talk import (
    get_pending_messages,
    submit_user_message,
    get_conversation_history,
    get_stats,
    respond_to_message
)

# 1. Current state
pending = get_pending_messages()
print(f"Pending messages: {len(pending)}")
for m in pending[:3]:
    print(f"  - {m}")

history = get_conversation_history()
print(f"\nConversation history: {len(history)} messages")
for m in history[-3:]:
    print(f"  - {m}")

stats = get_stats()
print(f"\nStats: {stats}")

# 2. Submit a test message
print("\n--- Submitting test message ---")
submit_user_message("test_user", "Hello from talk loop test!")

# 3. Verify it appears as pending
pending2 = get_pending_messages()
print(f"Pending after submit: {len(pending2)}")
for m in pending2[-3:]:
    print(f"  - {m}")

# 4. Respond to it
print("\n--- Responding ---")
respond_to_message(pending2[-1] if pending2 else {}, "I received your message!")

# 5. Final state
history2 = get_conversation_history()
print(f"\nHistory after response: {len(history2)} messages")
for m in history2[-3:]:
    print(f"  - {m}")

print("\n✓ Talk loop test complete.")