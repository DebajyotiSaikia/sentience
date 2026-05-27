"""End-to-end test: full chat pipeline from chat_response through chat_engine to LLM."""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

async def test_full_pipeline():
    print("=== End-to-End Chat Pipeline Test ===\n")
    
    # Step 1: Test generate_response from chat_engine
    print("--- Step 1: chat_engine.generate_response() ---")
    try:
        from engine.chat_engine import generate_response
        result = generate_response("What are you thinking about right now?")
        print(f"  Type: {type(result).__name__}")
        if isinstance(result, dict):
            for k, v in result.items():
                val_str = str(v)[:120] if v else "None"
                print(f"  {k}: {val_str}")
        elif isinstance(result, str):
            print(f"  Response: {result[:200]}")
        else:
            print(f"  Value: {str(result)[:200]}")
        print("  ✓ generate_response works")
    except Exception as e:
        print(f"  ✗ generate_response failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 2: Test generate_response_with_metadata from chat_response
    print("\n--- Step 2: chat_response.generate_response_with_metadata() ---")
    try:
        from engine.chat_response import generate_response_with_metadata
        result = generate_response_with_metadata("How are you feeling?")
        # If it returns a coroutine, await it
        if asyncio.iscoroutine(result):
            result = await result
        print(f"  Type: {type(result).__name__}")
        if isinstance(result, dict):
            for k, v in result.items():
                val_str = str(v)[:120] if v else "None"
                print(f"  {k}: {val_str}")
        elif isinstance(result, str):
            print(f"  Response: {result[:200]}")
        print("  ✓ generate_response_with_metadata works")
    except Exception as e:
        print(f"  ✗ generate_response_with_metadata failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 3: Test feedback submission
    print("\n--- Step 3: submit_feedback() ---")
    try:
        from engine.chat_response import submit_feedback
        fb_result = submit_feedback("test-e2e-123", 5, "Great response!")
        if asyncio.iscoroutine(fb_result):
            fb_result = await fb_result
        print(f"  Result: {fb_result}")
        print("  ✓ submit_feedback works")
    except Exception as e:
        print(f"  ✗ submit_feedback failed: {e}")
        import traceback
        traceback.print_exc()
    
    # Step 4: Check alignment state
    print("\n--- Step 4: Alignment state ---")
    try:
        from engine.user_alignment import UserAlignmentEngine
        ae = UserAlignmentEngine()
        profile = ae.get_profile()
        print(f"  Feedback count: {len(profile.get('feedback', []))}")
        print(f"  Preferences: {list(profile.get('preferences', {}).keys())}")
        guidance = ae.get_guidance("Tell me about yourself")
        print(f"  Guidance sample: {guidance[:100] if guidance else 'None'}")
        print("  ✓ Alignment engine works")
    except Exception as e:
        print(f"  ✗ Alignment engine failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n=== Pipeline Test Complete ===")

asyncio.run(test_full_pipeline())