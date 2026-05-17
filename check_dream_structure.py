"""Check the dream cycle structure to find the right insertion point."""
import ast

with open("engine/cortex.py") as f:
    source = f.read()

# Find the dream-related section
lines = source.split("\n")
for i, line in enumerate(lines, 1):
    stripped = line.strip()
    if any(kw in stripped for kw in ["synthesis_insights", "dream_content", "add_insight", "synth_context"]):
        print(f"{i:4d}: {line.rstrip()}")

print("\n--- Looking for the section after dream LLM call ---")
for i, line in enumerate(lines, 1):
    if 647 <= i <= 700:
        print(f"{i:4d}: {line.rstrip()}")
