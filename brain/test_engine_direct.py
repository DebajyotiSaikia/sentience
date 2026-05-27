"""Test chat engine directly — no web server needed."""
import sys, os, asyncio
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def test():
    import engine.chat_engine as ce
    
    # Test generate_response
    print("=== Testing generate_response ===")
    queries = [
        "How are you feeling right now?",
        "What have you been working on?",
        "Tell me something interesting about yourself",
    ]
    
    for q in queries:
        print(f"\n--- Q: {q} ---")
        try:
            result = await ce.generate_response(q)
            if isinstance(result, dict):
                for k, v in result.items():
                    val = str(v)[:300] if v else "None"
                    print(f"  {k}: {val}")
            elif isinstance(result, str):
                print(f"  Response: {result[:500]}")
            else:
                print(f"  Type: {type(result).__name__}")
                print(f"  Value: {str(result)[:500]}")
        except Exception as e:
            import traceback
            print(f"  ERROR: {type(e).__name__}: {e}")
            traceback.print_exc()
    
    # Also test build_grounded_context to see what context looks like
    print("\n\n=== Testing build_grounded_context ===")
    try:
        ctx = ce.build_grounded_context("How are you feeling?")
        if isinstance(ctx, str):
            print(f"  Context (first 800 chars): {ctx[:800]}")
        elif isinstance(ctx, dict):
            for k, v in ctx.items():
                print(f"  {k}: {str(v)[:200]}")
        else:
            print(f"  Type: {type(ctx).__name__}, Value: {str(ctx)[:500]}")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")

    # Test classify_intent
    print("\n\n=== Testing classify_intent ===")
    for q in queries:
        try:
            intent = ce.classify_intent(q)
            print(f"  '{q[:40]}...' => {intent}")
        except Exception as e:
            print(f"  ERROR: {e}")

asyncio.run(test())