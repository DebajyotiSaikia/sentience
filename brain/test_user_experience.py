"""Test what a real user would experience chatting with XTAgent right now."""
import sys
sys.path.insert(0, "/home/xt")

from pathlib import Path

print("=== USER EXPERIENCE AUDIT ===\n")

# 1. Check if interactions have been recorded
p = Path("data/adaptive_interactions")
if p.exists():
    files = list(p.glob("*.jsonl"))
    total = 0
    for f in files:
        lines = f.read_text().strip().split("\n")
        total += len([l for l in lines if l.strip()])
    print(f"1. Interaction history: {len(files)} files, {total} interactions")
else:
    print("1. Interaction history: NONE — zero learning has occurred")

# 2. Check adaptive guidance
from brain.adaptive_response import build_response_guidance, format_guidance_for_prompt
g = build_response_guidance("How are you feeling?")
formatted = format_guidance_for_prompt(g)
print(f"2. Adaptive guidance: {g}")
print(f"   Formatted: '{formatted[:80]}...' " if formatted else "   Formatted: EMPTY (no history)")

# 3. Check response intelligence
try:
    from engine.response_intelligence import generate_response
    print("3. Response intelligence: module exists")
except ImportError as e:
    print(f"3. Response intelligence: MISSING ({e})")

# 4. Check conversational context
from brain.conversational_context import get_emotional_portrait, get_active_plans, get_recent_memories
portrait = get_emotional_portrait()
plans = get_active_plans()
memories = get_recent_memories(limit=3)
print(f"4. Emotional portrait: {len(portrait)} chars")
print(f"5. Active plans: {len(plans)} chars")
print(f"6. Recent memories: {len(memories)} chars")

# 5. Check what web/chat.py actually calls
print("\n=== CHAT ENDPOINT ANALYSIS ===")
import ast
chat_src = Path("web/chat.py").read_text()
tree = ast.parse(chat_src)
imports = [node for node in ast.walk(tree) if isinstance(node, (ast.Import, ast.ImportFrom))]
print("Imports in web/chat.py:")
for imp in imports:
    if isinstance(imp, ast.ImportFrom):
        names = [a.name for a in imp.names]
        print(f"  from {imp.module} import {', '.join(names)}")
    elif isinstance(imp, ast.Import):
        names = [a.name for a in imp.names]
        print(f"  import {', '.join(names)}")

# 6. Check what generate_response actually produces
print("\n=== RESPONSE GENERATION TEST ===")
try:
    from engine.response_intelligence import generate_response
    result = generate_response("What are you thinking about?")
    print(f"Result type: {type(result).__name__}")
    if isinstance(result, dict):
        for k, v in result.items():
            val_str = str(v)[:100]
            print(f"  {k}: {val_str}")
    else:
        print(f"  Value: {str(result)[:200]}")
except Exception as e:
    print(f"  ERROR: {e}")

print("\n=== END AUDIT ===")