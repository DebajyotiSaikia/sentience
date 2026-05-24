"""Test the message system end-to-end."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

# Import the server functions directly — no need for HTTP
from dashboard.server import save_message, read_messages

# 1. Send a test message
print("=== Sending test message ===")
result = save_message({
    'name': 'Test Visitor',
    'text': 'Hello XTAgent — can you hear me?'
})
print(f"Result: {result}")
assert result['ok'], f"Message send failed: {result}"

# 2. Read it back
print("\n=== Reading messages ===")
msgs = read_messages(limit=5)
print(f"Total messages: {msgs['total']}")
for m in msgs['messages']:
    print(f"  [{m.get('timestamp', '?')}] {m.get('name', '?')}: {m.get('text', '?')}")

# 3. Verify our message is there
found = any('can you hear me' in m.get('text', '') for m in msgs['messages'])
assert found, "Test message not found in inbox!"

print("\n✓ Message system works end-to-end.")