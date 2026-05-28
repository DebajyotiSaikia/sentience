"""Trace why introspection fails inside _build_system_context"""
import sys, traceback
sys.path.insert(0, '/workspace')

# Simulate what _build_system_context does
query = "how are you feeling?"
try:
    from engine.introspection import get_self_context, format_introspective_prompt
    self_ctx = get_self_context(query)
    introspective_section = format_introspective_prompt(self_ctx)
    print(f"Section length: {len(introspective_section)}")
    print(f"Section empty: {not introspective_section.strip()}")
    print(f"Preview: {introspective_section[:200]}")
except Exception as e:
    traceback.print_exc()
    print(f"\nFailed: {e}")