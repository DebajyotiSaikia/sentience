"""Diagnose chat response time with timeout."""
import signal
import sys
from web.app import create_app

def timeout_handler(signum, frame):
    print("TIMEOUT - chat took too long")
    sys.exit(1)

app = create_app()
client = app.test_client()

import time

# Simple question first
t0 = time.time()
signal.alarm(10)  # 10 second timeout
r1 = client.post('/api/chat', json={'message': 'hello'})
t1 = time.time()
signal.alarm(0)
print(f"Simple 'hello': {t1-t0:.2f}s, status={r1.status_code}")

# Substantive question
signal.signal(signal.SIGALRM, timeout_handler)
signal.alarm(10)
t0 = time.time()
r2 = client.post('/api/chat', json={'message': 'What do you know about consciousness?'})
t1 = time.time()
signal.alarm(0)
data = r2.get_json()
resp = data.get('response', '')
print(f"Consciousness Q: {t1-t0:.2f}s, status={r2.status_code}, len={len(resp)}")
print(f"Response: {resp[:300]}")