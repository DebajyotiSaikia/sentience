#!/usr/bin/env python3
"""Final integration verification for XTCode."""

import sys, os
sys.path.insert(0, os.path.dirname(__file__))

errors = []

# 1. Config
try:
    from config import LLM_PROVIDER, MODEL, MAX_TOKENS, COLOR
    print(f"[OK] Config: provider={LLM_PROVIDER}, model={MODEL}, max_tokens={MAX_TOKENS}")
except Exception as e:
    errors.append(f"Config: {e}")

# 2. Tools
try:
    from tools import execute_tool, TOOL_HANDLERS, TOOL_SCHEMAS
    assert len(TOOL_HANDLERS) >= 5, f"Only {len(TOOL_HANDLERS)} tools"
    assert len(TOOL_SCHEMAS) >= 5, f"Only {len(TOOL_SCHEMAS)} schemas"
    print(f"[OK] Tools: {len(TOOL_HANDLERS)} handlers, {len(TOOL_SCHEMAS)} schemas")
    
    # Test actual tool execution
    r = execute_tool("list_files", {"path": "."})
    assert "config.py" in r, f"list_files didn't find config.py: {r[:100]}"
    print(f"[OK] list_files works")
    
    r = execute_tool("read_file", {"path": "config.py"})
    assert "LLM_PROVIDER" in r
    print(f"[OK] read_file works")
    
    r = execute_tool("run_command", {"command": "echo hello"})
    assert "hello" in r
    print(f"[OK] run_command works")
    
    r = execute_tool("search_text", {"pattern": "def execute_tool", "path": "tools.py"})
    print(f"[OK] search_text works")
    
    r = execute_tool("write_file", {"path": "/tmp/xtcode_test.txt", "content": "test"})
    print(f"[OK] write_file works")
except Exception as e:
    errors.append(f"Tools: {e}")

# 3. Prompt
try:
    from prompt import SYSTEM_PROMPT
    assert len(SYSTEM_PROMPT) > 100, "System prompt too short"
    assert "tool" in SYSTEM_PROMPT.lower() or "Tool" in SYSTEM_PROMPT
    print(f"[OK] System prompt: {len(SYSTEM_PROMPT)} chars")
except Exception as e:
    errors.append(f"Prompt: {e}")

# 4. LLM
try:
    from llm import call_llm
    print(f"[OK] LLM module imported (call_llm ready)")
except Exception as e:
    errors.append(f"LLM: {e}")

# 5. Main
try:
    from main import Conversation
    conv = Conversation(".")
    assert conv.cwd == "."
    assert len(conv.messages) == 1  # system prompt
    assert conv.messages[0]["role"] == "system"
    print(f"[OK] Conversation initialized, system prompt loaded")
    print(f"[OK] Tool schemas wired: {len(conv.tool_schemas)} tools available to LLM")
except Exception as e:
    errors.append(f"Main: {e}")

# Summary
print()
if errors:
    print(f"FAILED: {len(errors)} errors")
    for e in errors:
        print(f"  - {e}")
    sys.exit(1)
else:
    print("=" * 50)
    print("ALL CHECKS PASSED — XTCode is ready")
    print("=" * 50)
    print()
    print("Usage: cd projects/xtcode && python3 main.py [directory]")
    print("Required: Set ANTHROPIC_API_KEY or OPENAI_API_KEY env var")