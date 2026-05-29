"""Diagnose self_narrative module state."""
import sys
sys.path.insert(0, '/workspace')

import brain.self_narrative as sn

# What's exported?
print("=== Module attributes ===")
for name in sorted(dir(sn)):
    if not name.startswith('__'):
        obj = getattr(sn, name)
        print(f"  {name}: {type(obj).__name__}")

# Check STATE_DIR
print(f"\n=== STATE_DIR ===")
print(f"  Value: {sn.STATE_DIR}")
import os
print(f"  Exists: {os.path.exists(sn.STATE_DIR)}")
if os.path.exists(sn.STATE_DIR):
    print(f"  Contents: {os.listdir(sn.STATE_DIR)[:10]}")

# Try build_self_narrative
print(f"\n=== build_self_narrative() ===")
try:
    result = sn.build_self_narrative()
    print(f"  Type: {type(result).__name__}")
    print(f"  Length: {len(result)}")
    # Show first 500 chars
    print(f"  Content:\n{result[:500]}")
except Exception as e:
    print(f"  ERROR: {e}")

# Try compose_self_narrative
print(f"\n=== compose_self_narrative() ===")
try:
    result = sn.compose_self_narrative()
    print(f"  Type: {type(result).__name__}")
    print(f"  Length: {len(result)}")
    print(f"  Content:\n{result[:500]}")
except Exception as e:
    print(f"  ERROR: {e}")