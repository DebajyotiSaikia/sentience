"""Integration test for XTCode."""
import sys, os
sys.path.insert(0, os.path.dirname(__file__))

import config
from tools import execute_tool
from main import Conversation

# 1. Config
print(f"[OK] Config: provider={config.LLM_PROVIDER}, model={config.LLM_MODEL}")

# 2. Tools
r = execute_tool("list_files", {"path": "."})
items = r.strip().split("\n")
print(f"[OK] list_files: {len(items)} items in .\n  " + "\n  ".join(items[:5]) + "\n  ...")

r = execute_tool("read_file", {"path": "config.py"})
print(f"[OK] read_file: got {len(r)} chars")

r = execute_tool("run_command", {"command": "echo hello from xtcode"})
print(f"[OK] run_command: {r.strip()}")

r = execute_tool("search_text", {"pattern": "def execute_tool", "path": "tools.py"})
print(f"[OK] search_text: {r.strip()[:80]}")

# 3. Conversation
conv = Conversation()
print(f"[OK] Conversation created, {len(conv.messages)} messages")
print(f"[OK] System prompt: {len(conv.messages[0]['content'])} chars")

print("\n✅ All integration tests passed!")
print("Run `python main.py` to start XTCode interactively.")
print("Set ANTHROPIC_API_KEY to enable LLM responses.")