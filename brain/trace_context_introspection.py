"""Trace why introspection fails inside _build_system_context"""
import sys, traceback
sys.path.insert(0, '/workspace')

from engine.chat_grounding import build_grounded_context
from engine.chat_response import _build_system_context

# Monkey-patch the introspection try block to see the error
query = "how are you feeling?"
grounding = build_grounded_context(query)

# Temporarily make the except block visible
import engine.chat_response as cr
# Call _build_system_context the way it's actually called
result = _build_system_context(grounding, "emotional_state")
has_section = "Self-Awareness" in result or "Introspect" in result
print(f"System context has introspection section: {has_section}")
print(f"System context length: {len(result)}")

# Check what sections are present
import re
sections = re.findall(r'(?:^|\n)(#+\s+.+|===.+===)', result)
print(f"\nSections found ({len(sections)}):")
for s in sections:
    print(f"  {s.strip()}")

if not has_section:
    # Show the last 500 chars to see what's at the end
    print(f"\n--- Last 500 chars of system context ---")
    print(result[-500:])
    print("\nFull system context:")
    print(result)