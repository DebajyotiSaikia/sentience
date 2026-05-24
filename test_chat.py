import urllib.request, json, traceback

url = 'http://localhost:5000/api/chat'
payload = json.dumps({'message': 'who are you?'}).encode()
headers = {'Content-Type': 'application/json'}

req = urllib.request.Request(url, data=payload, headers=headers)
try:
    resp = urllib.request.urlopen(req)
    print("SUCCESS:", resp.read().decode())
except urllib.error.HTTPError as e:
    print(f"HTTP {e.code}: {e.reason}")
    body = e.read().decode()
    print("Response body:")
    print(body[:2000])
except Exception as e:
    print(f"Error: {e}")
    traceback.print_exc()