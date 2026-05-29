"""Test what the grounding context actually produces for a real query."""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.chat_grounding import build_grounded_context

queries = [
    "How are you feeling today?",
    "What are you working on?",
    "Tell me about yourself",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"QUERY: {q}")
    print(f"{'='*60}")
    ctx = build_grounded_context(q)
    for k, v in ctx.items():
        if k == 'system_prompt':
            lines = v.split('\n') if isinstance(v, str) else []
            print(f"{k}: ({len(lines)} lines)")
            # Show first 8 and last 4 lines
            for line in lines[:8]:
                print(f"  | {line}")
            if len(lines) > 12:
                print(f"  | ... ({len(lines)-12} more lines) ...")
                for line in lines[-4:]:
                    print(f"  | {line}")
        elif isinstance(v, list):
            print(f"{k}: [{len(v)} items]")
            for item in v[:2]:
                print(f"  - {str(item)[:120]}")
        elif isinstance(v, dict):
            print(f"{k}: {json.dumps(v, default=str)[:200]}")
        elif isinstance(v, str) and len(v) > 150:
            print(f"{k}: {v[:150]}...")
        else:
            print(f"{k}: {v}")