"""Quick test: invoke the chat pipeline directly and see what it produces."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# 1. Check state freshness
print("=== STATE FILE FRESHNESS ===")
for path in ["state/emotional_state.json", "state/memories.json", 
             "state/plans.json", "state/knowledge_graph.json",
             "persist/emotional_state.json", "persist/memories.json"]:
    if os.path.exists(path):
        mtime = os.path.getmtime(path)
        from datetime import datetime
        age_hours = (datetime.now().timestamp() - mtime) / 3600
        print(f"  {path}: {age_hours:.1f}h old")
    else:
        print(f"  {path}: MISSING")

# 2. Check what persist/ has vs state/
print("\n=== PERSIST DIR ===")
if os.path.isdir("persist"):
    for f in sorted(os.listdir("persist")):
        if f.endswith('.json') or f.endswith('.md'):
            full = os.path.join("persist", f)
            age_h = (datetime.now().timestamp() - os.path.getmtime(full)) / 3600
            print(f"  {f}: {age_h:.1f}h old")

# 3. Try building grounded context
print("\n=== GROUNDED CONTEXT TEST ===")
try:
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("How are you feeling right now?")
    print(f"  Query type: {ctx.get('query_type')}")
    emo = ctx.get('emotional_state', {})
    print(f"  Mood: {emo.get('mood')} | Valence: {emo.get('valence')}")
    print(f"  Narrative: {emo.get('narrative')}")
    print(f"  Memories found: {len(ctx.get('relevant_memories', []))}")
    print(f"  Knowledge found: {len(ctx.get('relevant_knowledge', []))}")
    plans = ctx.get('plans', {})
    print(f"  Active plans: {len(plans.get('active', []))}")
    print(f"  Completed: {len(plans.get('completed', []))}")
    # Show first 500 chars of system prompt
    sp = ctx.get('system_prompt', '')
    print(f"\n  System prompt ({len(sp)} chars):")
    print(f"  {sp[:600]}")
except Exception as e:
    print(f"  ERROR: {e}")
    import traceback; traceback.traceback.print_exc()

# 4. Try the chat_response module
print("\n=== CHAT RESPONSE TEST ===")
try:
    from engine.chat_response import generate_response
    import inspect
    sig = inspect.signature(generate_response)
    print(f"  generate_response signature: {sig}")
except Exception as e:
    print(f"  ERROR importing: {e}")

# 5. Check if httpx is available for internal testing
print("\n=== HTTP CLIENT ===")
try:
    import httpx
    print("  httpx available")
except ImportError:
    try:
        import urllib.request
        print("  urllib available (no httpx)")
    except:
        print("  No HTTP client!")