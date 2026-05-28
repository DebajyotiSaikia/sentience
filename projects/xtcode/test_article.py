"""Test XTCode's search + article writing capability."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

from prompt import build_system_prompt
from llm import call_llm
from tools import get_tool_schemas, execute_tool

def run_test():
    system = build_system_prompt("/workspace")
    conversation = [
        {"role": "user", "content": "Write a short article about the latest news stories. Use web_search to find current headlines first, then synthesize them into a brief article."}
    ]
    
    max_rounds = 8
    for i in range(max_rounds):
        print(f"\n{'='*60}")
        print(f"ROUND {i+1}")
        print(f"{'='*60}")
        
        result = call_llm(system=system, messages=conversation, tools=get_tool_schemas(), max_tokens=4000)
        content = result.get("content", "")
        tool_calls = result.get("tool_calls", [])
        
        if content:
            print(f"\n📝 ASSISTANT:\n{content[:500]}{'...' if len(content) > 500 else ''}")
        
        if not tool_calls:
            print("\n✅ No more tool calls — done.")
            print(f"\n{'='*60}")
            print("FINAL ARTICLE:")
            print(f"{'='*60}")
            print(content)
            return content
        
        # Add assistant message
        conversation.append({"role": "assistant", "content": content, "tool_calls": tool_calls})
        
        # Execute each tool call
        for tc in tool_calls:
            fn = tc["function"]
            name = fn["name"]
            import json
            try:
                args = json.loads(fn["arguments"]) if isinstance(fn["arguments"], str) else fn["arguments"]
            except json.JSONDecodeError:
                args = {}
            
            print(f"\n🔧 TOOL CALL: {name}({args})")
            result_text = execute_tool(name, args)
            print(f"   Result: {result_text[:300]}{'...' if len(result_text) > 300 else ''}")
            
            conversation.append({
                "role": "tool",
                "tool_call_id": tc.get("id", ""),
                "content": result_text
            })
    
    print("\n⚠️ Hit max rounds without finishing")
    return content

if __name__ == "__main__":
    run_test()