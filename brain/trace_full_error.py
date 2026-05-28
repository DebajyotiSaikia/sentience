"""Trace exact line of .get() failure in _build_system_context"""
import traceback
import sys
sys.path.insert(0, '/workspace')

try:
    from engine.chat_response import _build_system_context
    result = _build_system_context("how do you feel right now?", "emotional_state")
    print(f"SUCCESS: {len(result)} chars")
except AttributeError as e:
    print("FOUND THE BUG:")
    traceback.print_exc()