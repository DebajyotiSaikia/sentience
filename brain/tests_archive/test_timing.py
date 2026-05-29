"""Diagnose where generate_response_with_metadata hangs."""
import sys, os, time, signal
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def timeout_handler(signum, frame):
    raise TimeoutError("TIMEOUT")

signal.signal(signal.SIGALRM, timeout_handler)

# Phase 1: Import timing
t0 = time.time()
print("Phase 1: Import...", flush=True)
signal.alarm(10)
try:
    from engine.chat_response import generate_response_with_metadata
    signal.alarm(0)
    print(f"  Import OK: {time.time()-t0:.1f}s", flush=True)
except TimeoutError:
    print(f"  HUNG during import after 10s", flush=True)
    sys.exit(1)

# Phase 2: _build_system_context timing  
t1 = time.time()
print("Phase 2: _build_system_context...", flush=True)
signal.alarm(10)
try:
    from engine.chat_response import _build_system_context
    ctx = _build_system_context("hello", [])
    signal.alarm(0)
    print(f"  Context OK: {time.time()-t1:.1f}s, len={len(ctx)}", flush=True)
except TimeoutError:
    print(f"  HUNG during context build after 10s", flush=True)
    sys.exit(1)
except Exception as e:
    signal.alarm(0)
    print(f"  Error (non-fatal): {e}", flush=True)

# Phase 3: smart_responder fallback directly
t2 = time.time()
print("Phase 3: smart_responder.respond...", flush=True)
signal.alarm(5)
try:
    from engine.smart_responder import respond
    r = respond("hello")
    signal.alarm(0)
    print(f"  Respond OK: {time.time()-t2:.1f}s", flush=True)
    print(f"  Preview: {r[:100]}", flush=True)
except TimeoutError:
    print(f"  HUNG during respond after 5s", flush=True)
except Exception as e:
    signal.alarm(0)
    print(f"  Error: {e}", flush=True)

# Phase 4: Full pipeline
t3 = time.time()
print("Phase 4: generate_response_with_metadata...", flush=True)
signal.alarm(15)
try:
    r = generate_response_with_metadata("hello")
    signal.alarm(0)
    print(f"  Full OK: {time.time()-t3:.1f}s", flush=True)
    if isinstance(r, dict):
        print(f"  Response: {r.get('response','NONE')[:150]}", flush=True)
except TimeoutError:
    print(f"  HUNG in full pipeline after 15s", flush=True)
except Exception as e:
    signal.alarm(0)
    print(f"  Error: {e}", flush=True)

print(f"\nTotal: {time.time()-t0:.1f}s", flush=True)