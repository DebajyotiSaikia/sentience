import requests

url = "http://localhost:8080/ask/query"
payload = {"query": "what do you know about yourself?"}

try:
    resp = requests.post(url, json=payload, timeout=10)
    print(f"Status: {resp.status_code}")
    print(f"Headers: {dict(resp.headers)}")
    print(f"Body (first 1000 chars):")
    print(resp.text[:1000])
except Exception as e:
    print(f"Error: {e}")