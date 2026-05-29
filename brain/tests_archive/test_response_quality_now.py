#!/usr/bin/env python3
"""Quick test: what does respond() actually produce for common queries?"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from engine.smart_responder import respond

queries = [
    "How do you feel right now?",
    "What are you working on?",
    "What have you learned recently?",
    "Who are you?",
    "What are you thinking about?",
    "Tell me about your dreams",
]

for q in queries:
    print(f"\n{'='*60}")
    print(f"Q: {q}")
    print(f"{'='*60}")
    r = respond(q)
    print(r[:800] if r else "(empty)")
    print(f"[length: {len(r) if r else 0} chars]")