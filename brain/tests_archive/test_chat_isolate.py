"""Isolate where chat_response hangs: grounding vs LLM call."""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("Step 1: Import chat_grounding...", flush=True)
t0 = time.time()
from engine.chat_grounding import build_grounded_context
print(f"  Import took {time.time()-t0:.1f}s", flush=True)

print("Step 2: Build grounded context...", flush=True)
t1 = time.time()
ctx = build_grounded_context("How are you feeling?")
print(f"  Grounding took {time.time()-t1:.1f}s", flush=True)
print(f"  Keys: {list(ctx.keys())}", flush=True)
emo = ctx.get('emotional_state', {})
print(f"  Mood: {emo.get('mood', 'N/A')}, Valence: {emo.get('valence', 'N/A')}", flush=True)

print("Step 3: Test LLM call directly...", flush=True)
t2 = time.time()
from engine.llm import call_llm
from engine.chat_response import _run_async
try:
    result = _run_async(call_llm("Say hello in one sentence.", max_tokens=50))
    print(f"  LLM responded in {time.time()-t2:.1f}s", flush=True)
    print(f"  Response: {result[:200]}", flush=True)
except Exception as e:
    print(f"  LLM FAILED in {time.time()-t2:.1f}s: {type(e).__name__}: {e}", flush=True)

print("Step 4: Full generate_response_with_metadata...", flush=True)
t3 = time.time()
from engine.chat_response import generate_response_with_metadata
try:
    result = generate_response_with_metadata("How are you?")
    print(f"  Full response in {time.time()-t3:.1f}s", flush=True)
    print(f"  Response [{len(result.get('response',''))} chars]: {result['response'][:300]}", flush=True)
    print(f"  Has metadata: {bool(result.get('metadata'))}", flush=True)
except Exception as e:
    print(f"  FAILED in {time.time()-t3:.1f}s: {type(e).__name__}: {e}", flush=True)

print(f"\nTotal time: {time.time()-t0:.1f}s", flush=True)