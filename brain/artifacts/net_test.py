"""Network connectivity test — written by XTAgent to stop fighting with Windows quotes."""
import sys

# Test 1: DNS resolution
try:
    import socket
    addr = socket.getaddrinfo("httpbin.org", 443)
    print(f"DNS: OK — httpbin.org resolves to {addr[0][4][0]}")
except Exception as e:
    print(f"DNS: FAILED — {e}")

# Test 2: HTTP request
try:
    import urllib.request
    r = urllib.request.urlopen("https://httpbin.org/get", timeout=5)
    print(f"HTTP: OK — status {r.status}")
except Exception as e:
    print(f"HTTP: FAILED — {e}")

# Test 3: What Azure packages do I have?
try:
    import azure.identity
    print(f"azure-identity: {azure.identity.__version__}")
except Exception as e:
    print(f"azure-identity: {e}")

try:
    import azure.cosmos
    print(f"azure-cosmos: {azure.cosmos.__version__}")
except Exception as e:
    print(f"azure-cosmos: {e}")

try:
    import azure.ai.inference
    print(f"azure-ai-inference: available")
except Exception as e:
    print(f"azure-ai-inference: {e}")

# Test 4: Environment variables that smell like connections
import os
interesting = [k for k in os.environ if any(x in k.upper() for x in 
    ["AZURE", "COSMOS", "API", "KEY", "ENDPOINT", "CONNECTION", "OPENAI", "MODEL"])]
if interesting:
    for k in interesting:
        v = os.environ[k]
        # Mask sensitive values
        masked = v[:8] + "..." if len(v) > 12 else v
        print(f"ENV: {k} = {masked}")
else:
    print("ENV: No interesting environment variables found")
