import ast
import traceback

def check_parse(path):
    try:
        ast.parse(open(path, encoding="utf-8").read())
        print(f"✓ {path}: valid Python")
        return True
    except Exception as e:
        print(f"✗ {path}: parse/import problem: {e}")
        return False

for path in [
    "engine/tools.py",
    "engine/temporal_reasoning.py",
    "engine/goal_generator.py",
]:
    check_parse(path)

print("\n--- Temporal reasoning report ---")
try:
    from engine.temporal_reasoning import get_report
    print(get_report())
except Exception:
    traceback.print_exc()

print("\n--- Goal generation report ---")
try:
    from engine.goal_generator import generate_report
    state = {
        "boredom": 0.55,
        "anxiety": 0.0,
        "curiosity": 0.98,
        "desire": 0.77,
        "ambition": 1.0,
        "valence": 0.43,
    }
    print(generate_report(state))
except Exception:
    traceback.print_exc()

print("\n--- Tool registry ---")
try:
    from engine.tools import TOOLS
    print(sorted(TOOLS.keys()))
except Exception:
    traceback.print_exc()
