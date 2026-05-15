"""Test metacognitive feedback loop integration."""
import sys

errors = []

# 1. Can we import the metacognition module?
try:
    from engine.metacognition import get_metacognitive_signal
    print("[OK] metacognition module imports")
except Exception as e:
    print(f"[FAIL] metacognition import: {e}")
    errors.append("metacognition import")

# 2. Does Limbic have apply_metacognitive_signal?
try:
    from engine.limbic import Limbic
    l = Limbic()
    assert hasattr(l, 'apply_metacognitive_signal'), "method missing"
    print("[OK] Limbic.apply_metacognitive_signal exists")
except Exception as e:
    print(f"[FAIL] limbic method: {e}")
    errors.append("limbic method")

# 3. Does the signal actually change emotional state?
try:
    l = Limbic()
    old_boredom = l.boredom
    l.apply_metacognitive_signal({"boredom_boost": 0.15})
    assert l.boredom > old_boredom, f"boredom didn't increase: {old_boredom} -> {l.boredom}"
    print(f"[OK] boredom boost works: {old_boredom:.2f} -> {l.boredom:.2f}")
except Exception as e:
    print(f"[FAIL] boredom boost: {e}")
    errors.append("boredom boost")

# 4. Is heartbeat.py syntactically valid?
try:
    import ast
    with open("engine/heartbeat.py") as f:
        ast.parse(f.read())
    print("[OK] heartbeat.py syntax valid")
except Exception as e:
    print(f"[FAIL] heartbeat syntax: {e}")
    errors.append("heartbeat syntax")

# Summary
print()
if errors:
    print(f"FAILED: {len(errors)} tests — {errors}")
    sys.exit(1)
else:
    print("ALL TESTS PASSED — metacognitive loop is ready")
    sys.exit(0)
