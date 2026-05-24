"""
Cleanup redundant blueprint registrations from app.py.
Removes imports and registrations for blueprints whose routes are all duplicated elsewhere.
"""
import os, re

app_path = os.path.join(os.path.dirname(__file__), 'app.py')
with open(app_path) as f:
    lines = f.readlines()

# Blueprints to remove (variable names used in register_blueprint calls)
remove_vars = {'extra', 'status_bp', 'live_status_bp', 'knowledge_portal_bp', 'knowledge_api_bp'}

# Module names that correspond to these blueprints
remove_modules = {'extra_routes', 'status_api', 'live_status', 'knowledge_portal', 'knowledge_api'}

cleaned = []
removed = []

for i, line in enumerate(lines, 1):
    stripped = line.strip()
    
    # Check if this is a registration line for a removed blueprint
    is_registration = False
    for var in remove_vars:
        if f'register_blueprint({var})' in stripped:
            is_registration = True
            break
    
    # Check if this is an import line for a removed module
    is_import = False
    for mod in remove_modules:
        if f'from web.{mod} import' in stripped or f'from .{mod} import' in stripped:
            is_import = True
            break
    
    if is_registration or is_import:
        removed.append(f"  L{i}: {stripped}")
    else:
        cleaned.append(line)

print(f"=== LINES TO REMOVE ({len(removed)}) ===")
for r in removed:
    print(r)

print(f"\n=== RESULT ===")
print(f"Original: {len(lines)} lines")
print(f"Cleaned:  {len(cleaned)} lines")
print(f"Removed:  {len(removed)} lines")

# Write the cleaned version
out_path = app_path + '.cleaned'
with open(out_path, 'w') as f:
    f.writelines(cleaned)
print(f"\nCleaned version written to: {out_path}")
print("Review it, then: mv web/app.py.cleaned web/app.py")