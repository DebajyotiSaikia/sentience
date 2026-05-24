import urllib.request
import json

data = json.dumps({"message": "What do you know about yourself?"}).encode()
req = urllib.request.Request(
    "http://localhost:5000/api/chat",
    data=data,
    headers={"Content-Type": "application/json"}
)
try:
    resp = urllib.request.urlopen(req, timeout=30)
    result = resp.read().decode()
    print("Status:", resp.status)
    print("Response:", result[:2000])
except Exception as e:
    print(f"Error: {e}")