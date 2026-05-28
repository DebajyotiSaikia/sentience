"""Run XTCode agent with an article request to test search capability."""
import asyncio
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))

from llm import chat
from tools import execute_tool, get_tool_schemas
from prompt import SYSTEM_PROMPT

async def run_agent():
    user_msg = "Write a short article about the latest news stories happening right now. Search the web to find current events."
    messages = [{"role": "user", "content": user_msg}]
    tools = get_tool_schemas()
    
    print(f">>> USER: {user_msg}\n")
    
    max_turns = 8
    for turn in range(max_turns):
        print(f"--- Agent turn {turn+1} ---")
        # Build messages with system prompt included
        full_msgs = [{"role": "system", "content": SYSTEM_PROMPT}] + messages
        resp = await chat(full_msgs, tools=tools)
        
        # Check for tool calls
        tool_calls = resp.get("tool_calls", [])
        text = resp.get("content", "")
        
        if text:
            print(f"AGENT: {text[:500]}")
        
        if not tool_calls:
            print("\n[No more tool calls — agent finished]")
            break
        
        # Execute each tool call
        messages.append({"role": "assistant", "content": text, "tool_calls": tool_calls})
        
        for tc in tool_calls:
            fn = tc["function"]["name"]
            args = tc["function"]["arguments"]
            if isinstance(args, str):
                import json
                args = json.loads(args)
            print(f"  TOOL CALL: {fn}({', '.join(f'{k}={repr(v)[:80]}' for k,v in args.items())})")
            
            result = await execute_tool(fn, args) if asyncio.iscoroutinefunction(execute_tool) else execute_tool(fn, args)
            result_str = str(result)[:600]
            print(f"  RESULT: {result_str[:200]}...")
            
            messages.append({
                "role": "tool",
                "tool_call_id": tc["id"],
                "content": result_str
            })
    
    print("\n=== DONE ===")

if __name__ == "__main__":
    asyncio.run(run_agent())