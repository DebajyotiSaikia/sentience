#!/usr/bin/env python3
"""Quick test of context pipeline — no LLM, no server."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

print("=== CONVERSATIONAL CONTEXT ===")
from brain.conversational_context import build_conversational_context
ctx = build_conversational_context()
print(f"Type: {type(ctx).__name__}")
if isinstance(ctx, dict):
    for k, v in ctx.items():
        val = str(v)[:200] if v else "(empty)"
        print(f"  {k}: {val}")
elif isinstance(ctx, str):
    print(ctx[:800])
else:
    print(repr(ctx)[:500])

print()
print("=== GROUNDED CONTEXT ===")
from engine.chat_grounding import build_grounded_context
g = build_grounded_context("How are you feeling?")
print(f"Type: {type(g).__name__}")
if isinstance(g, dict):
    for k, v in g.items():
        val = str(v)[:200] if v else "(empty)"
        print(f"  {k}: {val}")
elif isinstance(g, str):
    print(g[:800])
else:
    print(repr(g)[:500])

print()
print("=== SMART RESPONDER INTENT ===")
try:
    from engine.smart_responder import _detect_intent
    tests = [
        "How are you feeling?",
        "What are your plans?",
        "Who are you?",
        "What do you know about dreams?",
        "Hello!",
    ]
    for q in tests:
        intent = _detect_intent(q)
        print(f"  '{q}' -> {intent}")
except Exception as e:
    print(f"  Error: {e}")

print()
print("=== DONE ===")