"""Quick integration test for action_diversity module."""
import sys
sys.path.insert(0, '/workspace')

from engine.action_diversity import record, novelty_pressure, generate_report, underused_actions

# Test recording
record("READ", "engine/tools.py", "success")
record("READ", "engine/cortex.py", "success") 
record("READ", "engine/cortex.py", "success")
record("WRITE", "test.py", "success")
record("RUN", "python test.py", "success")

# Test novelty pressure
np = novelty_pressure()
print(f"Novelty pressure score: {np['score']}")
print(f"Diversity: {np['diversity']}")
print(f"Message: {np['message']}")

# Test report
report = generate_report()
print(f"\nReport:\n{report}")

# Test underused
unused = underused_actions()
print(f"\nUnderused actions: {unused}")

print("\n=== All action_diversity functions work ===")
