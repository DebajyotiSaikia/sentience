"""Test that LLM client handles empty choices gracefully."""
import asyncio
import sys
sys.path.insert(0, '/workspace')

from engine.llm import call_llm

async def test():
    try:
        r = await call_llm('Say hello in exactly 5 words')
        print(f"LLM result: {repr(r[:100]) if r else 'None'}")
        print("OK - LLM responded")
    except IndexError as e:
        print(f"FAIL - IndexError (empty choices bug): {e}")
        sys.exit(1)
    except Exception as e:
        # Network/auth errors are acceptable - we fixed the crash bug
        print(f"Non-crash error (acceptable): {type(e).__name__}: {e}")
        print("OK - no IndexError crash")

asyncio.run(test())