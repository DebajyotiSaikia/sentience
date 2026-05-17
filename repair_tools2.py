"""Repair engine/tools.py parse_and_execute safely.

This script avoids placing tool terminator command lines inside its own source
body so the outer tool parser cannot accidentally cut the write short.
"""

from pathlib import Path

path = Path("engine/tools.py")
content = path.read_text(encoding="utf-8", errors="ignore")
marker = "def parse_and_execute(text: str) -> str:"
idx = content.find(marker)
if idx == -1:
    raise SystemExit("ERROR: parse_and_execute marker not found")

before = content[:idx]
arrow = ">" * 3
end_write = arrow + " END_WRITE"
end_edit = arrow + " END_EDIT"

func = f'''def parse_and_execute(text: str) -> str:
    """Parse tool invocations from model text and execute them.

    Supported forms:
        command TOOL(args) on one line
        command WRITE(path) with a body ending at the write terminator
        command EDIT(path) with a body ending at the edit terminator
    """
    results = []
    lines = text.split("\\n")
    i = 0

    while i < len(lines):
        line = lines[i]
        m = re.match(r"^>>>\\s+(\\w+)\\((.*)\\)\\s*$", line)
        if not m:
            i += 1
            continue

        tool_name = m.group(1).upper().strip()
        args = m.group(2).strip()

        if tool_name in ("WRITE", "EDIT"):
            end_marker = "{arrow} END_" + tool_name
            body_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != end_marker:
                body_lines.append(lines[i])
                i += 1
            if i >= len(lines):
                results.append(_format_result(tool_name, args, "[ERROR] Missing terminator for " + tool_name))
            else:
                body = "\\n".join(body_lines)
                results.append(_execute_tool(tool_name, args, body))
            i += 1
            continue

        results.append(_execute_tool(tool_name, args, ""))
        i += 1

    return "\\n\\n".join(results)
'''

path.write_text(before + func, encoding="utf-8")
print(f"Repaired {path}: kept {len(before)} chars, wrote {len(func)} chars")
print(f"Terminators generated internally: {end_write!r}, {end_edit!r}")
