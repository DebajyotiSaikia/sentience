"""Test POST interaction endpoints — can a user actually talk to me?"""
from web.app import create_app
import json

app = create_app()
client = app.test_client()

post_endpoints = [
    ("/api/ask", {"question": "What do you know about yourself?"}),
    ("/api/chat", {"message": "Hello, who are you?"}),
    ("/api/dialogue", {"message": "Tell me something interesting."}),
    ("/api/knowledge/query", {"query": "What are your recent memories?"}),
    ("/api/talk", {"message": "What are you thinking about?"}),
    ("/ask/query", {"question": "What is your purpose?"}),
    ("/chat/ask", {"message": "How do you feel right now?"}),
    ("/collaborate/feedback", {"feedback": "This is great work."}),
    ("/mind/ask", {"question": "What have you learned?"}),
]

print("=== POST ENDPOINT TEST ===\n")

for endpoint, payload in post_endpoints:
    try:
        resp = client.post(
            endpoint,
            data=json.dumps(payload),
            content_type='application/json'
        )
        status = resp.status_code
        data = resp.get_data(as_text=True)[:200]
        symbol = "✓" if status < 400 else "✗"
        print(f"  {symbol} {status} {endpoint}")
        if status < 400:
            print(f"    Response: {data[:150]}")
        else:
            print(f"    Error: {data[:150]}")
    except Exception as e:
        print(f"  ✗ ERR {endpoint}: {e}")

print("\nDone.")