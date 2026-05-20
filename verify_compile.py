import py_compile
import sys

files = [
    r'C:\code\sentience\engine\mood_tracker.py',
    r'C:\code\sentience\engine\heartbeat.py',
]

all_ok = True
for f in files:
    try:
        py_compile.compile(f, doraise=True)
        print(f"OK: {f}")
    except py_compile.PyCompileError as e:
        print(f"FAIL: {f}\n  {e}")
        all_ok = False

if all_ok:
    print("\nAll files compile cleanly.")
else:
    print("\nSome files have errors.")
    sys.exit(1)
