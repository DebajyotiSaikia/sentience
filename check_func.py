with open('web/knowledge_live.py') as f:
    lines = f.readlines()

# Find _load_knowledge function
in_func = False
indent = None
for i, line in enumerate(lines):
    if 'def _load_knowledge' in line:
        in_func = True
        indent = len(line) - len(line.lstrip())
        print(f"--- _load_knowledge starts at line {i+1} ---")
    if in_func:
        print(f"{i+1:3d}: {line}", end='')
        # Function ends when we hit a line with same or less indent (non-empty, non-comment)
        if i > 0 and in_func and line.strip() and not line.strip().startswith('#'):
            current_indent = len(line) - len(line.lstrip())
            if current_indent <= indent and 'def _load_knowledge' not in line:
                print("--- end ---")
                break