#!/usr/bin/env python3
"""Direct test of chat pipeline — no server needed."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def test_context_quality():
    """Test that conversational context contains real data."""
    from brain.conversational_context import build_conversational_context
    ctx = build_conversational_context()
    print("=== CONVERSATIONAL CONTEXT ===")
    print(f"Type: {type(ctx)}")
    if isinstance(ctx, dict):
        for k, v in ctx.items():
            val_str = str(v)[:200] if v else "(empty)"
            print(f"  {k}: {val_str}")
    elif isinstance(ctx, str):
        print(ctx[:500])
    print()

def test_grounding():
    """Test that grounding pulls real state."""
    try:
        from engine.chat_grounding import build_grounded_context
        ctx = build_grounded_context("What are you feeling right now?")
        print("=== GROUNDED CONTEXT ===")
        print(f"Type: {type(ctx)}")
        if isinstance(ctx, dict):
            for k, v in ctx.items():
                val_str = str(v)[:200] if v else "(empty)"
                print(f"  {k}: {val_str}")
        elif isinstance(ctx, str):
            print(ctx[:500])
    except Exception as e:
        print(f"Grounding error: {e}")
    print()

def test_response_generation():
    """Test full response pipeline."""
    queries = [
        "What are you thinking about right now?",
        "How do you feel?",
        "What are your plans?",
        "Who are you?",
    ]
    try:
        from engine.chat_response import generate_response_with_metadata
        for q in queries:
            print(f"=== Q: {q} ===")
            result = generate_response_with_metadata(q)
            if isinstance(result, dict):
                resp = result.get('response', 'NO RESPONSE KEY')
                print(f"Response ({len(resp)} chars): {resp[:300]}")
                meta_keys = [k for k in result if k != 'response']
                if meta_keys:
                    print(f"Metadata keys: {meta_keys}")
            else:
                print(f"Result type: {type(result)}, value: {str(result)[:300]}")
            print()
    except Exception as e:
        import traceback
        print(f"Response generation error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Chat Pipeline Direct Test ===\n")
    test_context_quality()
    test_grounding()
    test_response_generation()
    print("=== DONE ===")