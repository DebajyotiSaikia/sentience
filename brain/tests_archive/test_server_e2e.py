"""End-to-end server test — start server, test health + chat, report results."""
import subprocess, time, json, urllib.request, sys, os, signal

def kill_existing():
    """Kill any existing server processes."""
    for pat in ["python3 main", "flask", "aiohttp"]:
        subprocess.run(f"pkill -9 -f '{pat}'", shell=True, capture_output=True)
    time.sleep(2)

def start_server():
    """Start main.py in background, return process."""
    proc = subprocess.Popen(
        [sys.executable, "main.py"],
        stdout=open("/tmp/server.log", "w"),
        stderr=subprocess.STDOUT,
        cwd="/workspace"
    )
    return proc

def wait_for_health(timeout=15):
    """Wait for health endpoint to respond."""
    start = time.time()
    while time.time() - start < timeout:
        try:
            r = urllib.request.urlopen("http://localhost:8501/health", timeout=3)
            if r.status == 200:
                return True
        except Exception:
            pass
        time.sleep(1)
    return False

def test_chat(query):
    """Send a chat query and return response."""
    data = json.dumps({"message": query}).encode()
    req = urllib.request.Request(
        "http://localhost:8501/api/chat",
        data=data,
        headers={"Content-Type": "application/json"}
    )
    r = urllib.request.urlopen(req, timeout=30)
    return json.loads(r.read())

def main():
    print("=== E2E Server Test ===")
    
    # Step 1: Kill existing
    print("[1] Killing existing processes...")
    kill_existing()
    
    # Step 2: Start server
    print("[2] Starting server...")
    proc = start_server()
    
    # Step 3: Wait for health
    print("[3] Waiting for health endpoint...")
    if not wait_for_health():
        print("FAIL: Server didn't start in time")
        with open("/tmp/server.log") as f:
            print("--- Last 30 lines of log ---")
            lines = f.readlines()
            for line in lines[-30:]:
                print(line.rstrip())
        proc.kill()
        sys.exit(1)
    print("OK: Health endpoint responding")
    
    # Step 4: Test chat
    print("[4] Testing chat endpoint...")
    queries = [
        "What are you feeling right now?",
        "What are you working on?",
        "Who are you?",
    ]
    for q in queries:
        try:
            resp = test_chat(q)
            text = str(resp.get("response", resp))
            print(f"\n  Q: {q}")
            print(f"  A: {text[:300]}...")
            print(f"  Status: OK")
        except Exception as e:
            print(f"\n  Q: {q}")
            print(f"  FAIL: {e}")
    
    # Step 5: Cleanup
    print("\n[5] Cleaning up...")
    proc.terminate()
    proc.wait(timeout=5)
    print("=== DONE ===")

if __name__ == "__main__":
    main()