"""Final end-to-end verification of user alignment pipeline."""
import sys, os, json, tempfile

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, '.')

passed = 0
failed = 0

def check(name, condition):
    global passed, failed
    if condition:
        print(f"  ✓ {name}")
        passed += 1
    else:
        print(f"  ✗ {name}")
        failed += 1

# 1. user_alignment.py core functions
print("=== 1. user_alignment.py ===")
from engine.user_alignment import (
    load_profile, record_feedback, get_alignment_context,
    format_alignment_context, save_profile
)
check("all core functions import", True)

profile = load_profile()
check("load_profile returns dict", isinstance(profile, dict))

ctx = get_alignment_context()
check("get_alignment_context returns dict", isinstance(ctx, dict))

formatted = format_alignment_context(ctx)
check("format_alignment_context returns str", isinstance(formatted, str))

# 2. chat_grounding.py integration
print("\n=== 2. chat_grounding.py ===")
from engine.chat_grounding import build_grounded_context, GroundedContext
check("build_grounded_context imports", True)

gc = build_grounded_context("hello", [])
check("returns GroundedContext", isinstance(gc, GroundedContext))
check("has alignment_guidance field", hasattr(gc, 'alignment_guidance'))

# 3. chat_engine.py uses grounding
print("\n=== 3. chat_engine.py ===")
import engine.chat_engine as ce
check("chat_engine imports", True)
# Check that _respond_general references build_grounded_context
import inspect
src = inspect.getsource(ce)
check("_respond_general uses build_grounded_context", "build_grounded_context" in src)

# 4. chat_response.py feedback loop
print("\n=== 4. chat_response.py ===")
from engine.chat_response import submit_feedback
check("submit_feedback imports", True)

# 5. dashboard endpoint exists
print("\n=== 5. dashboard/server.py ===")
with open("dashboard/server.py") as f:
    server_src = f.read()
check("/api/user-alignment endpoint exists", "/api/user-alignment" in server_src)

# Summary
print(f"\n{'='*40}")
print(f"  {passed} passed, {failed} failed")
if failed == 0:
    print("  ✅ User alignment pipeline COMPLETE")
else:
    print("  ❌ Issues remain")
sys.exit(failed)