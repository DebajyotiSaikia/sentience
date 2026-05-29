"""Quick verification that compose_self_narrative auto-loads state."""
from brain.self_narrative import compose_self_narrative

result = compose_self_narrative()
print(f"Length: {len(result)}")
print("---")
print(result[:1000])
print("---")

# Verify it's not the fallback message
assert "can't clearly read" not in result.lower(), "FAIL: Got fallback message"
assert len(result) > 100, f"FAIL: Too short ({len(result)} chars)"
print("\nPASS: compose_self_narrative produces rich output")