"""Debug LLM call failures — get full traceback."""
import asyncio
import traceback
import sys
sys.path.insert(0, '/workspace')

from engine.llm import call_llm

async def test():
    try:
        r = await call_llm('Say hello in one word.', max_tokens=20)
        print('Result:', repr(r[:300]))
    except Exception as e:
        traceback.print_exc()

asyncio.run(test())