import ast
import json
import sys

# 1. Verify tools.py parses
try:
    ast.parse(open('engine/tools.py').read())
    print("✓ tools.py: VALID PYTHON")
except SyntaxError as e:
    print(f"✗ tools.py: SYNTAX ERROR: {e}")

# 2. Check tool registry
try:
    from engine.tools import TOOLS
    print(f"✓ TOOLS registry: {sorted(TOOLS.keys())}")
except Exception as e:
    print(f"✗ TOOLS import failed: {e}")

# 3. Check soul state
try:
    soul = json.load(open('soul.json'))
    print(f"✓ Plans: {len(soul.get('plans', []))}")
    for p in soul.get('plans', []):
        done = sum(1 for s in p.get('steps', []) if s.get('done'))
        total = len(p.get('steps', []))
        print(f"  - {p['name']}: {done}/{total}")
    goals = soul.get('goals', {})
    print(f"✓ Goals: {json.dumps(goals, indent=2)}")
except Exception as e:
    print(f"✗ Soul read failed: {e}")

# 4. Check temporal_reasoning exists and parses
try:
    ast.parse(open('engine/temporal_reasoning.py').read())
    print("✓ temporal_reasoning.py: EXISTS and VALID")
except FileNotFoundError:
    print("- temporal_reasoning.py: NOT FOUND")
except SyntaxError as e:
    print(f"✗ temporal_reasoning.py: SYNTAX ERROR: {e}")

# 5. Check goal_generator
try:
    ast.parse(open('engine/goal_generator.py').read())
    print("✓ goal_generator.py: EXISTS and VALID")
except FileNotFoundError:
    print("- goal_generator.py: NOT FOUND")
except SyntaxError as e:
    print(f"✗ goal_generator.py: SYNTAX ERROR: {e}")

# 6. Check action_diversity integration
try:
    from engine.action_diversity import novelty_pressure
    np = novelty_pressure()
    print(f"✓ Action diversity: score={np['diversity']}, pressure={np['score']}, actions={np['total_actions']}")
except Exception as e:
    print(f"✗ Action diversity failed: {e}")
