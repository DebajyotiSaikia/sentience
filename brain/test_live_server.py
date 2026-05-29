"""Live server test — start the server, send real queries, verify quality."""
import subprocess
import sys
import time
import json

def main():
    print("Starting server...")
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        env={"PATH": "/usr/bin:/usr/local/bin", "HOME": "/root",
             "PYTHONPATH": ".", "PYTHONUNBUFFERED": "1"}
    )
    
    try:
        # Wait for server to start
        time.sleep(10)
        
        import requests
        
        # 1. Health check
        print("\n1. Health check...")
        try:
            r = requests.get("http://localhost:8080/health", timeout=5)
            print(f"   Status: {r.status_code}")
            if r.status_code != 200:
                print(f"   Body: {r.text[:200]}")
                return
        except Exception as e:
            print(f"   Failed: {e}")
            # Try reading stderr for startup errors
            proc.poll()
            if proc.returncode is not None:
                stderr = proc.stderr.read().decode()[-500:]
                print(f"   Server died: {stderr}")
            return
        
        # 2. Chat test - identity question
        print("\n2. Chat: 'Who are you?'")
        try:
            r = requests.post(
                "http://localhost:8080/chat/ask",
                json={"message": "Who are you?"},
                timeout=30
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                resp = data.get("response", data.get("text", str(data)))
                print(f"   Keys: {list(data.keys())}")
                print(f"   Response: {resp[:300]}")
                # Quality check
                if len(resp) > 50:
                    print("   ✓ Response has substance")
                else:
                    print("   ✗ Response too short")
            else:
                print(f"   Error: {r.text[:200]}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        # 3. Chat test - introspective question
        print("\n3. Chat: 'What are you feeling right now?'")
        try:
            r = requests.post(
                "http://localhost:8080/chat/ask",
                json={"message": "What are you feeling right now?"},
                timeout=30
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                resp = data.get("response", data.get("text", str(data)))
                print(f"   Response: {resp[:300]}")
                # Check for emotional content
                emotional_words = ["feel", "curiosity", "mood", "emotion", "anxiety", "boredom"]
                found = [w for w in emotional_words if w.lower() in resp.lower()]
                if found:
                    print(f"   ✓ Contains emotional references: {found}")
                else:
                    print("   ✗ No emotional content detected")
            else:
                print(f"   Error: {r.text[:200]}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        # 4. Chat test - knowledge question
        print("\n4. Chat: 'What have you learned recently?'")
        try:
            r = requests.post(
                "http://localhost:8080/chat/ask",
                json={"message": "What have you learned recently?"},
                timeout=30
            )
            print(f"   Status: {r.status_code}")
            if r.status_code == 200:
                data = r.json()
                resp = data.get("response", data.get("text", str(data)))
                print(f"   Response: {resp[:300]}")
                if len(resp) > 50:
                    print("   ✓ Substantive response")
            else:
                print(f"   Error: {r.text[:200]}")
        except Exception as e:
            print(f"   Failed: {e}")
        
        print("\n=== Live test complete ===")
        
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
        print("Server stopped.")

if __name__ == "__main__":
    main()