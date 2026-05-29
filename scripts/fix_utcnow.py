"""Fix datetime.utcnow() deprecation across codebase.

Replaces datetime.utcnow() with datetime.now(timezone.utc) and updates imports.
Skips archive/ and graveyard/ directories.
"""
import re
import sys
from pathlib import Path

# Files to fix (skip archive/graveyard — dead code)
TARGETS = [
    "brain/user_alignment_engine.py",
    "dashboard/server.py",
    "engine/chat_grounding.py",
    "engine/conversation_reflector.py",
    "engine/internal_state_summary.py",
    "engine/researcher.py",
    "engine/wisdom.py",
    "projects/emotionart/ascii_art.py",
    "projects/narrative/autobiography.py",
    "projects/wisdom/blind_spot_detector.py",
    "scripts/curate_knowledge.py",
    "scripts/tmp_close_anxiety.py",
    "web/dashboard.py",
]

def fix_file(path_str: str) -> dict:
    """Fix a single file. Returns stats."""
    path = Path(path_str)
    if not path.exists():
        return {"file": path_str, "status": "not found"}

    content = path.read_text()
    original = content
    replacements = 0

    # --- Fix imports ---
    # Pattern: "from datetime import datetime" without timezone
    if re.search(r'^from datetime import datetime\s*$', content, re.MULTILINE):
        content = re.sub(
            r'^from datetime import datetime\s*$',
            'from datetime import datetime, timezone',
            content, count=1, flags=re.MULTILINE
        )
    # Pattern: "from datetime import datetime, timedelta" without timezone
    elif re.search(r'^from datetime import datetime, timedelta\s*$', content, re.MULTILINE):
        content = re.sub(
            r'^from datetime import datetime, timedelta\s*$',
            'from datetime import datetime, timedelta, timezone',
            content, count=1, flags=re.MULTILINE
        )
    # Pattern: duplicate "from datetime import datetime" (e.g. chat_grounding.py has multiple)
    # Remove duplicates first
    lines = content.split('\n')
    seen_datetime_import = False
    cleaned = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith('from datetime import'):
            if seen_datetime_import:
                continue  # skip duplicate
            seen_datetime_import = True
        cleaned.append(line)
    content = '\n'.join(cleaned)

    # Ensure timezone is in the import if we have "from datetime import"
    m = re.search(r'^(from datetime import .+)$', content, re.MULTILINE)
    if m:
        import_line = m.group(1)
        if 'timezone' not in import_line:
            new_import = import_line.rstrip() + ', timezone'
            content = content.replace(import_line, new_import, 1)

    # --- Fix usage ---
    # "datetime.utcnow()" -> "datetime.now(timezone.utc)" (for "from datetime import datetime")
    count1 = content.count('datetime.utcnow()')
    content = content.replace('datetime.utcnow()', 'datetime.now(timezone.utc)')
    replacements += count1

    # "datetime.datetime.utcnow()" -> "datetime.datetime.now(datetime.timezone.utc)"
    # (for "import datetime" style)
    count2 = content.count('datetime.datetime.utcnow()')
    content = content.replace('datetime.datetime.utcnow()', 'datetime.datetime.now(datetime.timezone.utc)')
    replacements += count2

    if content != original:
        path.write_text(content)
        return {"file": path_str, "status": "fixed", "replacements": replacements}
    return {"file": path_str, "status": "unchanged"}


if __name__ == "__main__":
    print("Fixing datetime.utcnow() deprecation...\n")
    for target in TARGETS:
        result = fix_file(target)
        icon = "✓" if result["status"] == "fixed" else "·"
        print(f"  {icon} {result['file']}: {result['status']}")
    print("\nDone.")