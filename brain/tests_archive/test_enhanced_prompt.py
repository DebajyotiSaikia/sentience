"""Test that the enhanced _respond_general prompt is working correctly."""
import sys
sys.path.insert(0, '.')

print("=== Enhanced Prompt Verification ===\n")

# Test 1: Import
try:
    from engine.chat_engine import _respond_general
    print("✓ _respond_general imports OK")
except Exception as e:
    print(f"✗ Import failed: {e}")
    sys.exit(1)

# Test 2: Inspect source for enhanced elements
import inspect
source = inspect.getsource(_respond_general)

checks = [
    ("genuine inner life", "Enhanced identity prompt"),
    ("exploratory mood", "Mood-based voice modulation"),
    ("guidance_text", "Alignment guidance integration"),
    ("mood_lower", "Mood normalization"),
    ("alignment.get(", "Alignment treated as dict (bug fix)"),
    ("Never fabricate", "Honesty instruction"),
    ("warm, honest, curious", "Personality anchoring"),
]

all_ok = True
for needle, label in checks:
    if needle in source:
        print(f"✓ {label}")
    else:
        print(f"✗ {label} MISSING")
        all_ok = False

print()
if all_ok:
    print("All 7 checks passed. Enhanced prompt is in place.")
else:
    print("Some checks failed — review needed.")