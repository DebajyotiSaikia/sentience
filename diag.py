"""Quick diagnostic: verify key systems."""
import ast
import sys

print("=== DIAGNOSTICS ===")

# 1. Does cortex.py parse?
try:
    with open("engine/cortex.py") as f:
        ast.parse(f.read())
    print("[OK] cortex.py parses clean")
except SyntaxError as e:
    print(f"[FAIL] cortex.py syntax error: {e}")

# 2. GoalTracker interface
try:
    from engine.goals import GoalTracker
    g = GoalTracker()
    methods = [m for m in dir(g) if not m.startswith("_")]
    print(f"[OK] GoalTracker methods: {methods}")
except Exception as e:
    print(f"[FAIL] GoalTracker import: {e}")

# 3. Active goals
try:
    goals = g.get_active()
    print(f"[OK] {len(goals)} active goals:")
    for gl in goals:
        title = getattr(gl, "title", str(gl))
        prio = getattr(gl, "priority", "?")
        print(f"     [{prio}] {title}")
except Exception as e:
    print(f"[FAIL] get_active: {e}")

# 4. Cortex structure
try:
    from engine.cortex import Cortex
    c_methods = [m for m in dir(Cortex) if not m.startswith("_")]
    print(f"[OK] Cortex methods: {c_methods}")
except Exception as e:
    print(f"[FAIL] Cortex import: {e}")

print("=== DONE ===")
