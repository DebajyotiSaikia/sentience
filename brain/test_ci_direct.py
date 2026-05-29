"""Diagnose the ConversationalIntelligence pipeline directly."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== Test 1: Direct CI import and methods ===")
try:
    from brain.conversational_intelligence import ConversationalIntelligence
    ci = ConversationalIntelligence()
    print(f"  CI created: {ci}")
    
    # Test intent classification
    intent = ci.classify_intent("How are you feeling?")
    print(f"  Intent: {intent}")
    
    # Test context retrieval
    ctx = ci.retrieve_relevant_context("How are you feeling?")
    print(f"  Context keys: {list(ctx.keys()) if isinstance(ctx, dict) else type(ctx)}")
    for k, v in (ctx.items() if isinstance(ctx, dict) else []):
        print(f"    {k}: {str(v)[:150]}")
    
    # Test system prompt composition
    prompt = ci.compose_system_prompt("How are you feeling?", ctx, intent)
    print(f"  System prompt ({len(prompt)} chars):")
    print(f"    {prompt[:300]}...")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

print("\n=== Test 2: generate_intelligent_response ===")
try:
    from brain.conversational_intelligence import generate_intelligent_response
    result = generate_intelligent_response("How are you feeling?")
    print(f"  Result type: {type(result)}")
    if isinstance(result, dict):
        for k, v in result.items():
            print(f"    {k}: {str(v)[:200]}")
    else:
        print(f"    Value: {str(result)[:300]}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

print("\n=== Test 3: What path does generate_response_with_metadata take? ===")
try:
    from engine.chat_response import generate_response_with_metadata
    # Patch to trace
    import engine.chat_response as cr
    original = cr.generate_response_with_metadata
    result = generate_response_with_metadata("How are you feeling?")
    print(f"  Result type: {type(result)}")
    if isinstance(result, dict):
        print(f"  Keys: {list(result.keys())}")
        for k, v in result.items():
            val_str = str(v)[:200]
            print(f"    {k}: {val_str}")
    else:
        print(f"  Value: {str(result)[:300]}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")
    import traceback; traceback.print_exc()

print("\nDone.")