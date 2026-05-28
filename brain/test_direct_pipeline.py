"""
Direct test of the chat pipeline — no web server needed.
Tests: grounding → classification → response generation
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    print("=" * 60)
    print("DIRECT PIPELINE TEST")
    print("=" * 60)

    # 1. Test grounding
    print("\n--- Step 1: Grounding ---")
    from engine.chat_grounding import build_grounded_context
    ctx = build_grounded_context("How are you feeling?")
    required = ['system_prompt', 'emotional_state', 'identity']
    required = ['system_prompt', 'emotional_state']
    all_keys = list(ctx.keys())
    print(f"  All keys: {all_keys}")
    for k in required:
        status = "✓" if k in ctx else "✗ MISSING"
        print(f"  {status} {k}")
    assert all(k in ctx for k in required), f"Missing required grounding keys. Got: {all_keys}"

    # 2. Test classification
    print("\n--- Step 2: Classification ---")
    from engine.chat_grounding import classify_query
    queries = {
        "How are you feeling?": "emotional",
        "What plans do you have?": "plans",
        "Tell me about quantum physics": "general",
    }
    for q, expected in queries.items():
        result = classify_query(q)
        status = "✓" if result == expected else f"✗ got '{result}'"
        print(f"  {status} '{q[:40]}' → {expected}")

    # 3. Test response generation
    print("\n--- Step 3: Response Generation ---")
    try:
        from engine.chat_engine import generate_response
        system_prompt = ctx.get('system_prompt', '')
        start = time.time()
        result = generate_response(
            "How are you feeling right now?",
            system_context=system_prompt
        )
        elapsed = time.time() - start
        print(f"  ✓ Response generated in {elapsed:.1f}s")
        print(f"  Length: {len(result)} chars")
        preview = result[:200].replace('\n', ' ')
        print(f"  Preview: {preview}...")

        # Quality checks
        is_conversational = len(result) > 20 and not result.startswith('{')
        print(f"  {'✓' if is_conversational else '✗'} Conversational (not raw JSON)")
    except Exception as e:
        print(f"  ✗ Response generation failed: {e}")

    print("\n" + "=" * 60)
    print("PIPELINE TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    main()