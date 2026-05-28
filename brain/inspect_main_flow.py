"""Inspect the main flow: generate_response, context building, general handler"""
import inspect
import sys
sys.path.insert(0, '/workspace')

from engine import chat_response

# The main entry point
for name in ['generate_response', '_compose_grounded_response', 
             '_respond_general_grounded', '_respond_knowledge',
             '_respond_help', '_build_system_context',
             '_build_grounding_context', '_gather_grounding']:
    fn = getattr(chat_response, name, None)
    if fn:
        print(f"\n{'='*60}")
        print(f"=== {name} ===")
        print(f"{'='*60}")
        src = inspect.getsource(fn)
        print(src)
    else:
        print(f"\n=== {name} === NOT FOUND")