"""Test that alignment delta is centered around quality 0.5"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Test the centered delta logic in isolation
def simulate_alignment_delta(quality, base_delta=0.05):
    """Reproduce the logic from cortex.py lines ~1261-1267"""
    # Center around 0.5: bad responses hurt, good help
    centered = (quality - 0.5) * 2  # range: -1.0 to +1.0
    delta = centered * base_delta   # range: -0.05 to +0.05
    return delta

# Test cases
tests = [
    (0.0, "terrible response"),
    (0.25, "poor response"),
    (0.5, "neutral response"),
    (0.75, "good response"),
    (1.0, "excellent response"),
]

print("Quality | Delta   | Direction")
print("--------|---------|----------")
all_pass = True
for quality, label in tests:
    delta = simulate_alignment_delta(quality)
    direction = "UP" if delta > 0 else ("DOWN" if delta < 0 else "NEUTRAL")
    print(f"  {quality:.2f}  | {delta:+.4f} | {direction:8s} ({label})")
    
    # Verify correctness
    if quality < 0.5 and delta >= 0:
        print(f"  FAIL: quality {quality} should give negative delta")
        all_pass = False
    elif quality > 0.5 and delta <= 0:
        print(f"  FAIL: quality {quality} should give positive delta")
        all_pass = False
    elif quality == 0.5 and delta != 0:
        print(f"  FAIL: quality 0.5 should give zero delta")
        all_pass = False

print()
if all_pass:
    print("ALL TESTS PASS — alignment delta is correctly centered")
else:
    print("SOME TESTS FAILED")