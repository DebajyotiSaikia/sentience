"""Test whether the chat API endpoint actually works for users."""
import requests

endpoints_to_try = [
    ("http://localhost:8501/api/chat", "POST", {"message": "What do you know about yourself?"}),
    ("http://localhost:8501/", "GET", None),
    ("http://localhost:8501/api/status", "GET", None),
    ("http://localhost:8080/", "GET", None),
    ("http://localhost:8080/api/chat", "POST", {"message": "Hello"}),
    ("http://localhost:5000/", "GET", None),
]

for url, method, payload in endpoints_to_try:
    try:
        if method == "GET":
            r = requests.get(url, timeout=3)
        else:
            r = requests.post(url, json=payload, timeout=3)
        print(f"[{r.status_code}] {method} {url}")
        if len(r.text) < 300:
            print(f"  Body: {r.text}")
        else:
            print(f"  Body (first 300): {r.text[:300]}")
    except requests.ConnectionError:
        print(f"[CONN_ERR] {method} {url} — nothing listening")
    except Exception as e:
        print(f"[ERROR] {method} {url} — {e}")