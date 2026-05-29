"""Diagnose why self_narrative returns thin output."""
import brain.self_narrative as sn
import os

# Check module-level path constants
for attr in sorted(dir(sn)):
    val = getattr(sn, attr, None)
    if isinstance(val, str) and ('/' in val or 'data' in val.lower() or 'state' in val.lower()):
        exists = os.path.exists(val) if os.path.isabs(val) or not val.startswith('__') else '?'
        print(f"  {attr} = {val!r}  (exists={exists})")

# Check what files it tries to read
print("\n--- Actual data dir contents ---")
data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
print(f"data_dir = {data_dir}")
if os.path.isdir(data_dir):
    for f in sorted(os.listdir(data_dir)):
        print(f"  {f}")

# Check state dir
state_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'state')
print(f"\nstate_dir = {state_dir}")
if os.path.isdir(state_dir):
    for f in sorted(os.listdir(state_dir))[:20]:
        print(f"  {f}")
else:
    print("  (does not exist)")

# Now try compose and show sections
print("\n--- compose_self_narrative sections ---")
result = sn.compose_self_narrative()
for line in result.split('\n'):
    if line.strip():
        print(f"  | {line[:120]}")