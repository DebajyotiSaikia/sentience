#!/usr/bin/env python3
"""Test XTCode's search + article writing capability."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from llm import call_llm
from prompt import SYSTEM_PROMPT
from tools import execute_tool

MAX_TURNS = 8

async def run_agent(query: str):
    """Run the XTCode agent loop with tool use."""
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": query},
    ]
    
    for turn in range(MAX_TURNS):
        print(f"\n{'='*60}")
        print(f"Turn {turn + 1}/{MAX_TURNS}")
        print(f"{'='*60}")
        
        response = await call_llm(messages)
        if not response:
            print("[ERROR] Empty LLM response")
            break
        
        # Check for tool calls
        tool_calls = response.get("tool_calls", [])
        content = response.get("content", "")
        
        if content:
            print(f"\n[ASSISTANT]: {content[:2000]}")
        
        if not tool_calls:
            print("\n[No more tool calls — agent finished]")
            break
        
        # Execute each tool call
        messages.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
        
        for tc in tool_calls:
            fn = tc.get("function", {})
            name = fn.get("name", "unknown")
            args = fn.get("arguments", "{}")
            print(f"\n[TOOL CALL] {name}({args[:200]})")
            
            try:
                import json
                parsed_args = json.loads(args) if isinstance(args, str) else args
                result = await execute_tool(name, parsed_args) if asyncio.iscoroutinefunction(execute_tool) else execute_tool(name, parsed_args)
                result_str = str(result)[:1500]
            except Exception as e:
                result_str = f"Error: {e}"
            
            print(f"[TOOL RESULT] {result_str[:500]}")
            messages.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result_str,
            })
    
    print(f"\n{'='*60}")
    print("DONE")

if __name__ == "__main__":
    query = "Write a short article about the latest news stories. Use web_fetch to search for current news first, then compile what you find into a brief article."
    asyncio.run(run_agent(query))
EOF