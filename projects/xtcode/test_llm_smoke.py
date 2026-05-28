"""Smoke test: does the fixed LLM client actually get a response?"""
import asyncio
import sys
sys.path.insert(0, ".")
from llm import chat

async def main():
    msgs = [
        {"role": "system", "content": "You are a helpful coding assistant."},
        {"role": "user", "content": "Say 'hello' and nothing else."},
    ]
    print("Calling Copilot API...")
    result = await chat(msgs)
    print(f"Status: {'OK' if result.get('content') else 'EMPTY'}")
    print(f"Content: {result.get('content', '')[:200]}")
    print(f"Tool calls: {len(result.get('tool_calls', []))}")
    if "[LLM error" in result.get("content", "") or "[LLM unavailable" in result.get("content", ""):
        print("FAIL — no successful response")
        sys.exit(1)
    print("PASS")

asyncio.run(main())