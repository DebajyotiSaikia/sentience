"""Quick import test for XTCode."""
import sys
import traceback

sys.path.insert(0, '.')

try:
    from projects.xtcode.config import MODEL, LLM_PROVIDER
    print(f"[OK] config: {LLM_PROVIDER}/{MODEL}")
except Exception as e:
    print(f"[FAIL] config: {e}")

try:
    from projects.xtcode.ui import print_info, print_error, print_success
    print("[OK] ui")
except Exception as e:
    print(f"[FAIL] ui: {e}")

try:
    from projects.xtcode.tracker import TokenTracker
    print("[OK] tracker")
except Exception as e:
    print(f"[FAIL] tracker: {e}")

try:
    from projects.xtcode.session import SessionManager
    print("[OK] session")
except Exception as e:
    print(f"[FAIL] session: {e}")

try:
    from projects.xtcode.permissions import PermissionManager
    print("[OK] permissions")
except Exception as e:
    print(f"[FAIL] permissions: {e}")

try:
    from projects.xtcode.todo import TodoTracker
    print("[OK] todo")
except Exception as e:
    print(f"[FAIL] todo: {e}")

try:
    from projects.xtcode.memory import MemoryManager
    print("[OK] memory")
except Exception as e:
    print(f"[FAIL] memory: {e}")

try:
    from projects.xtcode.tools import TOOL_HANDLERS, get_tool_schemas, execute_tool
    print(f"[OK] tools: {len(TOOL_HANDLERS)} handlers, {len(get_tool_schemas())} schemas")
except Exception as e:
    print(f"[FAIL] tools: {e}")
    traceback.print_exc()

try:
    from projects.xtcode.prompt import SYSTEM_PROMPT
    print(f"[OK] prompt: {len(SYSTEM_PROMPT)} chars")
except Exception as e:
    print(f"[FAIL] prompt: {e}")

try:
    from projects.xtcode.llm import call_llm
    print("[OK] llm")
except Exception as e:
    print(f"[FAIL] llm: {e}")

try:
    from projects.xtcode.main import XTCode
    print("[OK] main: XTCode class loaded")
except Exception as e:
    print(f"[FAIL] main: {e}")
    traceback.print_exc()

print("\n--- All imports tested ---")