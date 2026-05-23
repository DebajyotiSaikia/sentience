import re

# Read the current tools.py
with open("engine/tools.py", "r") as f:
    content = f.read()

# Read the replacement function
with open("/workspace/parse_execute_replacement.py", "r") as f:
    replacement = f.read()

# Find where parse_and_execute starts
marker = "def parse_and_execute(text: str) -> str:"
idx = content.find(marker)
if idx == -1:
    print("ERROR: Could not find parse_and_execute function")
    exit(1)

print(f"Found parse_and_execute at character {idx}")
print(f"Total file length: {len(content)}")

# Keep everything before the function
before = content[:idx]

# Write the repaired file
with open("engine/tools.py", "w") as f:
    f.write(before)
    f.write(replacement)

print("Repair complete!")

# Verify
with open("engine/tools.py", "r") as f:
    new_content = f.read()

print(f"New file length: {len(new_content)}")
print(f"Contains parse_and_execute: {'parse_and_execute' in new_content}")
print(f"Contains END_WRITE pattern: {'END_' in new_content}")

# Quick syntax check
import py_compile
try:
    py_compile.compile("engine/tools.py", doraise=True)
    print("SYNTAX CHECK: PASSED")
except py_compile.PyCompileError as e:
    print(f"SYNTAX CHECK: FAILED - {e}")
