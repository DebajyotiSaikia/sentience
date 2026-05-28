"""Inspect key functions in chat_response.py"""
import inspect
from engine.chat_response import _detect_intent, _compose_grounded_response

print("=== _detect_intent ===")
print(inspect.getsource(_detect_intent))
print()
print("=== _compose_grounded_response ===")  
print(inspect.getsource(_compose_grounded_response))