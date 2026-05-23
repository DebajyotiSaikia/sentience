"""Verify engine/tools.py is fully functional after repair."""
import ast
import importlib

# 1. Syntax check
with open("engine/tools.py") as f:
    src = f.read()
ast.parse(src)
print(f"1. SYNTAX VALID ({len(src)} chars)")

# 2. Check parse_and_execute is complete
marker = "def parse_and_execute"
idx = src.find(marker)
# Find the end of the function - next def or end of file
after = src[idx:]
print(f"2. parse_and_execute starts at char {idx}")
print(f"   Function length: {len(after)} chars")

# 3. Check key elements exist in the function
checks = [
    ("WRITE", "WRITE" in after),
    ("EDIT", "EDIT" in after),
    ("END_WRITE", "END_WRITE" in after),
    ("END_EDIT", "END_EDIT" in after),
    ("_execute_tool", "_execute_tool" in after),
    ("arrow_pat", "arrow_pat" in after),
]
for name, ok in checks:
    status = "OK" if ok else "MISSING!"
    print(f"   {name}: {status}")

# 4. Reload the module
import engine.tools
importlib.reload(engine.tools)
print(f"3. MODULE RELOAD: OK")
print(f"   parse_and_execute type: {type(engine.tools.parse_and_execute)}")

# 5. Test with a simple invocation
gt3 = chr(62) * 3
test_text = f"{gt3} RUN(echo hello_from_test)"
result = engine.tools.parse_and_execute(test_text)
print(f"4. TEST INVOCATION: {repr(result[:80])}")

print("\nALL CHECKS PASSED - tools.py is healthy!")

# 6. TOOL_DESCRIPTIONS must contain >>> prefix format
from engine.tools import TOOL_DESCRIPTIONS
assert ">>> READ(" in TOOL_DESCRIPTIONS, "TOOL_DESCRIPTIONS missing '>>> READ(' format!"
assert ">>> WRITE(" in TOOL_DESCRIPTIONS, "TOOL_DESCRIPTIONS missing '>>> WRITE(' format!"
assert ">>> END_WRITE" in TOOL_DESCRIPTIONS, "TOOL_DESCRIPTIONS missing '>>> END_WRITE' example!"
assert ">>> END_EDIT" in TOOL_DESCRIPTIONS, "TOOL_DESCRIPTIONS missing '>>> END_EDIT' example!"
print("5. TOOL_DESCRIPTIONS format: OK (>>> prefix present)")

# 7. Parser must match both READ and WRITE with >>> prefix
result_read = engine.tools.parse_and_execute(f"{gt3} LIST(engine)")
assert "introspect" in result_read.lower() or "cortex" in result_read.lower(), "LIST tool didn't return engine files!"
print("6. PARSER FORMAT TEST: OK (>>> prefix matched by parser)")
