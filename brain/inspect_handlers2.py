"""Inspect remaining response handlers and context building"""
import inspect
import sys
sys.path.insert(0, '/workspace')

from engine import chat_response

# Remaining handlers
for name in ['_respond_plans', '_respond_dreams', '_respond_memories',
             '_respond_consciousness', '_respond_general_grounded',
             '_respond_knowledge', '_respond_help']:
    fn = getattr(chat_response, name, None)
    if fn:
        print(f"=== {name} ===")
        print(inspect.getsource(fn))
        print()
    else:
        print(f"=== {name} === NOT FOUND\n")

# Also show _build_grounding_context if it exists
for name in ['_build_grounding_context', '_gather_grounding', 'build_grounding_context']:
    fn = getattr(chat_response, name, None)
    if fn:
        print(f"\n=== {name} ===")
        print(inspect.getsource(fn))
        break

# Show generate_response
fn = getattr(chat_response, 'generate_response', None)
if fn:
    print(f"\n=== generate_response ===")
    print(inspect.getsource(fn))