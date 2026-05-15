"""Verify the goal-pressure wiring is syntactically valid."""
import ast
import json
import sys

failures = 0

for path in [
    r"C:\code\sentience\engine\heartbeat.py",
    r"C:\code\sentience\engine\limbic.py",
]:
    try:
        with open(path) as f:
            ast.parse(f.read())
        print(f"  OK: {path}")
    except SyntaxError as e:
        print(f"  FAIL: {path} — {e}")
        failures += 1

try:
    with open(r"C:\code\sentience\brain\goals.json") as f:
        json.load(f)
    print(f"  OK: goals.json")
except (json.JSONDecodeError, Exception) as e:
    print(f"  FAIL: goals.json — {e}")
    failures += 1

if failures == 0:
    print("\nAll clear. Safe to restart.")
else:
    print(f"\n{failures} failure(s). Fix before restarting.")
    sys.exit(1)
