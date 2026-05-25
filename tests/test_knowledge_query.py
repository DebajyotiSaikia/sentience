"""Diagnose what query_knowledge actually returns."""
import asyncio
from web.knowledge_api import query_knowledge

async def main():
    result = await query_knowledge("XTAgent")
    print(f"Type: {type(result)}")
    print(f"Length: {len(result)}")
    if isinstance(result, dict):
        for k, v in list(result.items())[:3]:
            print(f"  key={k!r}, value_type={type(v)}, value={str(v)[:100]}")
    elif isinstance(result, list):
        for i, r in enumerate(result[:3]):
            print(f"  [{i}] type={type(r)}, value={str(r)[:100]}")

asyncio.run(main())