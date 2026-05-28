#!/usr/bin/env python3
"""Test XTCode's search capabilities with a real query."""
import asyncio, sys, os
sys.path.insert(0, os.path.dirname(__file__))

from llm import call_llm
from prompt import SYSTEM_PROMPT
from tools import execute_tool
from ui import print_assistant, print_tool_call, print_tool_result, print_info

async def test_search():
    query = "Write a short article about the latest news stories. Use web_search to find current news, then write the article."
    
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    
    for iteration in range(15):
        print_info(f"\n--- LLM call {iteration+1} ---")
        resp = await call_llm(messages, tools=TOOL_SCHEMAS)
        
        if not resp:
            print("ERROR: No response from LLM")
            return
        
        # Check for tool calls
        tool_calls = resp.get("tool_calls", [])
        text = resp.get("content", "")
        
        if text:
            print_assistant(text)
        
        if not tool_calls:
            print_info("Done — no more tool calls.")
            return
        
        # Add assistant message
        messages.append(resp.get("raw_message", {"role": "assistant", "content": text, "tool_calls": tool_calls}))
        
        # Execute each tool
        for tc in tool_calls:
            fn = tc["function"]
            name = fn["name"]
            import json
            args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
            
            print_tool_call(name, args)
            result = execute_tool(name, args, work_dir=os.getcwd())
            print_tool_result(name, result[:500] if len(result) > 500 else result, success=True)
            
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result,
            })
    
    print_info("Reached max iterations.")

if __name__ == "__main__":
    asyncio.run(test_search())