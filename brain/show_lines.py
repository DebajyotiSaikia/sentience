"""Show the exact lines I need to edit to fix duplicate routes."""

print("=== web/app.py — lines with knowledge_api or inline routes ===")
for i, line in enumerate(open('web/app.py'), 1):
    if any(kw in line for kw in ['knowledge_api', 'api_search', 'api_knowledge_synthesis', 'api_state']):
        print(f"  {i:3}: {line.rstrip()}")

print("\n=== web/api.py — route decorators and function names ===")
for i, line in enumerate(open('web/api.py'), 1):
    if '@api_bp.route' in line or line.strip().startswith('def '):
        print(f"  {i:3}: {line.rstrip()}")