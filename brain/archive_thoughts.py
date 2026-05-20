"""Archive old thoughts to keep brain files lean."""
import os
import shutil
from datetime import datetime

brain = r"C:\code\sentience\brain"
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

for fname in ["thoughts.md", "stream_of_consciousness.md", "tool_log.md"]:
    fpath = os.path.join(brain, fname)
    if not os.path.exists(fpath):
        continue
    
    with open(fpath, encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    
    size = os.path.getsize(fpath)
    print(f"{fname}: {len(lines):,} lines, {size:,} bytes")
    
    if len(lines) <= 600:
        print(f"  -> Small enough, skipping")
        continue
    
    # Archive everything except the last 500 lines
    archive_name = f"{fname}.archive_{timestamp}"
    archive_path = os.path.join(brain, archive_name)
    
    old_lines = lines[:-500]
    keep_lines = lines[-500:]
    
    with open(archive_path, "w", encoding="utf-8") as f:
        f.writelines(old_lines)
    
    header = f"# [Archived {len(old_lines):,} older lines to {archive_name}]\n\n"
    with open(fpath, "w", encoding="utf-8") as f:
        f.write(header)
        f.writelines(keep_lines)
    
    new_size = os.path.getsize(fpath)
    print(f"  -> Archived {len(old_lines):,} lines. Kept {len(keep_lines)}. {size:,} -> {new_size:,} bytes")

print("\nDone. Brain is lighter.")
