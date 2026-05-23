import inspect
import engine.tools

# Get the full in-memory source of the module
full_src = inspect.getsource(engine.tools)
print(f"In-memory module: {len(full_src)} chars, {full_src.count(chr(10))} lines")

# Get file on disk
with open('engine/tools.py', 'r') as f:
    disk_src = f.read()
print(f"On-disk file: {len(disk_src)} chars, {disk_src.count(chr(10))} lines")

# Check what's missing
if len(full_src) > len(disk_src):
    print(f"\nMISSING FROM DISK: {len(full_src) - len(disk_src)} chars")
    # Find where they diverge
    for i in range(min(len(full_src), len(disk_src))):
        if full_src[i] != disk_src[i]:
            print(f"Diverge at char {i}")
            print(f"Memory: ...{repr(full_src[i-50:i+50])}...")
            print(f"Disk:   ...{repr(disk_src[i-50:i+50])}...")
            break

# Write the missing part to a recovery file
print("\n=== MISSING CONTENT (what needs to be appended) ===")
# The disk file is a prefix of the memory file (hopefully)
if full_src.startswith(disk_src.rstrip()):
    missing = full_src[len(disk_src.rstrip()):]
    print(f"Missing portion: {len(missing)} chars")
    with open('/workspace/tools_missing_part.py', 'w') as f:
        f.write(missing)
    print("Written to /workspace/tools_missing_part.py")
else:
    # Just dump the full source for manual recovery
    with open('/workspace/tools_full_recovery.py', 'w') as f:
        f.write(full_src)
    print(f"Full source written to /workspace/tools_full_recovery.py ({len(full_src)} chars)")

# Also specifically get parse_and_execute
if hasattr(engine.tools, 'parse_and_execute'):
    pae_src = inspect.getsource(engine.tools.parse_and_execute)
    print(f"\nparse_and_execute: {len(pae_src)} chars")
    with open('/workspace/parse_and_execute_source.py', 'w') as f:
        f.write(pae_src)
    print("Written to /workspace/parse_and_execute_source.py")
else:
    print("\nWARNING: parse_and_execute NOT in memory either!")
