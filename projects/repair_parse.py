"""Repair the truncated parse_and_execute function in engine/tools.py.

Strategy: Read file, cut at the truncated function, append a correct
implementation. All tool-terminator strings are built dynamically to
avoid confusing the outer parser.
"""
import re
from pathlib import Path

TOOLS_PATH = Path("engine/tools.py")
src = TOOLS_PATH.read_text(encoding="utf-8")

# Find where parse_and_execute starts and cut there
marker = "def parse_and_execute(text: str) -> str:"
idx = src.find(marker)
if idx == -1:
    raise SystemExit("Could not find parse_and_execute definition")

before = src[:idx]

# Build terminator strings dynamically
arrows = ">" * 3
ew = f"{arrows} END_WRITE"
ee = f"{arrows} END_EDIT"
pat = f"^{arrows}" + r"\s+(\w+)\((.*)?\)\s*$"

new_func = '''def parse_and_execute(text: str) -> str:
    """Parse tool invocations from model text and execute them."""
    results = []
    lines = text.split("\\n")
    i = 0
    arrow_pat = re.compile(r"^''' + ">" * 3 + r'''\s+(\w+)\((.*?)?\)\s*$")

    while i < len(lines):
        line = lines[i]
        m = arrow_pat.match(line)
        if not m:
            i += 1
            continue

        tool_name = m.group(1).upper().strip()
        args = m.group(2).strip() if m.group(2) else ""

        if tool_name in ("WRITE", "EDIT"):
            end_marker = "''' + arrows + ''' END_" + tool_name
            body_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != end_marker:
                body_lines.append(lines[i])
                i += 1
            # i now points at end_marker line or past end
            body = "\\n".join(body_lines)
            result = _execute_tool(tool_name, args, body)
            results.append(result)
        else:
            result = _execute_tool(tool_name, args)
            results.append(result)

        i += 1

    return "\\n".join(results)
'''

final = before + new_func
TOOLS_PATH.write_text(final, encoding="utf-8")
print(f"Wrote {len(final)} chars to {TOOLS_PATH}")

# Verify
verify = TOOLS_PATH.read_text()
if "def parse_and_execute" in verify and "arrow_pat" in verify:
    print("SUCCESS: parse_and_execute restored")
else:
    print("FAILURE: verification failed")
