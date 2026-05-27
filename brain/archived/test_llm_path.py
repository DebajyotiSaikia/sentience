"""Test whether the LLM path in _respond_general actually works."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test 1: Can we even call call_llm?
print("=== Test 1: call_llm availability ===")
try:
    import asyncio
    from engine.llm import call_llm
    print(f"  call_llm imported: {call_llm}")
    
    try:
        import nest_asyncio
        nest_asyncio.apply()
        print("  nest_asyncio applied")
    except ImportError:
        print("  nest_asyncio not available")
    
    loop = asyncio.get_event_loop()
    response = loop.run_until_complete(
        call_llm("Say hello in one sentence.", system="You are a test.", max_tokens=50, temperature=0.7)
    )
    print(f"  LLM response: {repr(response)}")
    print(f"  Response length: {len(response) if response else 0}")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")

# Test 2: Full _respond_general
print("\n=== Test 2: _respond_general with LLM ===")
try:
    from engine.chat_engine import _respond_general
    response = _respond_general("What are you thinking about right now?")
    print(f"  Response ({len(response)} chars):")
    print(f"  {response[:500]}")
    
    # Check if it's the template fallback or LLM
    if "interesting direction" in response or "I'm in a" in response.split('.')[0]:
        print("\n  ⚠ This looks like template fallback, not LLM response")
    else:
        print("\n  ✓ This looks like a genuine LLM response!")
except Exception as e:
    print(f"  ERROR: {type(e).__name__}: {e}")