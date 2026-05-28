"""Trace exactly where _compose_grounded_response fails."""
import traceback
from engine.chat_grounding import build_grounded_context
from engine.chat_response import _compose_grounded_response

grounding = build_grounded_context("how are you feeling?")
print("Grounding keys:", list(grounding.keys()))

# Check relevant_knowledge types
for i, k in enumerate(grounding.get("relevant_knowledge", [])):
    print(f"  knowledge[{i}]: type={type(k).__name__}, repr={repr(k)[:80]}")

try:
    result = _compose_grounded_response("how are you feeling?", grounding, [])
    print(f"SUCCESS, length: {len(result)}")
except AttributeError as e:
    print(f"FAILED: {e}")
    traceback.print_exc()