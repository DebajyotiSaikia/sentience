"""Test conversation_store.py end-to-end."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.conversation_store import ConversationStore

store = ConversationStore()
passed = 0
total = 0

# Test 1: Create thread
total += 1
tid = store.create_thread("Test thread")
assert tid and len(tid) > 0, "Thread ID should be non-empty"
print(f"  ✓ Created thread: {tid[:12]}...")
passed += 1

# Test 2: Add messages
total += 1
store.add_message(tid, "user", "Hello, how are you?")
store.add_message(tid, "assistant", "I'm doing well! Curious about many things.")
thread = store.get_thread(tid)
assert thread is not None, "Thread should exist"
assert len(thread["messages"]) == 2, f"Expected 2 messages, got {len(thread['messages'])}"
print(f"  ✓ Added 2 messages to thread")
passed += 1

# Test 3: Message structure
total += 1
msg = thread["messages"][0]
assert msg["role"] == "user", f"Expected role 'user', got {msg['role']}"
assert msg["content"] == "Hello, how are you?", "Content mismatch"
assert "timestamp" in msg, "Message should have timestamp"
print(f"  ✓ Message structure correct")
passed += 1

# Test 4: List threads
total += 1
threads = store.list_threads()
assert len(threads) >= 1, "Should have at least 1 thread"
found = any(t["id"] == tid for t in threads)
assert found, "Our thread should appear in list"
print(f"  ✓ Thread listing works ({len(threads)} threads)")
passed += 1

# Test 5: Get history for context
total += 1
history = store.get_history_for_context(tid, max_turns=5)
assert len(history) == 2, f"Expected 2 history entries, got {len(history)}"
assert history[0]["role"] == "user"
assert history[1]["role"] == "assistant"
print(f"  ✓ History for context extraction works")
passed += 1

# Test 6: Thread metadata
total += 1
thread_meta = store.get_thread(tid)
assert thread_meta["title"] == "Test thread"
assert "created_at" in thread_meta
assert "updated_at" in thread_meta
print(f"  ✓ Thread metadata correct")
passed += 1

# Test 7: Non-existent thread
total += 1
ghost = store.get_thread("nonexistent-id-12345")
assert ghost is None, "Non-existent thread should return None"
print(f"  ✓ Non-existent thread returns None")
passed += 1

# Test 8: Multiple threads
total += 1
tid2 = store.create_thread("Second thread")
store.add_message(tid2, "user", "Different conversation")
threads2 = store.list_threads()
assert len(threads2) >= 2, "Should have at least 2 threads now"
print(f"  ✓ Multiple threads supported")
passed += 1

# Cleanup test threads
try:
    import json
    data_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "conversations.json")
    if os.path.exists(data_path):
        with open(data_path) as f:
            data = json.load(f)
        data["threads"] = {k: v for k, v in data["threads"].items() if k not in (tid, tid2)}
        with open(data_path, "w") as f:
            json.dump(data, f)
        print(f"  ✓ Cleaned up test data")
except:
    pass

print(f"\n{'='*40}")
print(f"Results: {passed}/{total} passed")
if passed == total:
    print("ALL TESTS PASSED ✓")
else:
    print(f"FAILURES: {total - passed}")
    sys.exit(1)