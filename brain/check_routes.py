"""Check for duplicate/conflicting routes in the web app."""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web.app import create_app
app = create_app()

seen = {}
knowledge_routes = []
duplicates = []

for rule in app.url_map.iter_rules():
    methods = sorted(rule.methods - {"OPTIONS", "HEAD"})
    key = f"{rule.rule} [{','.join(methods)}]"
    endpoint = rule.endpoint
    if key in seen:
        duplicates.append((key, endpoint, seen[key]))
    seen[key] = endpoint
    if "knowledge" in key.lower() or "search" in key.lower():
        knowledge_routes.append((key, endpoint))

print(f"Total routes: {len(seen)}")
print(f"\n=== KNOWLEDGE/SEARCH ROUTES ===")
for key, ep in sorted(knowledge_routes):
    print(f"  {key} -> {ep}")

if duplicates:
    print(f"\n=== DUPLICATES ({len(duplicates)}) ===")
    for key, ep1, ep2 in duplicates:
        print(f"  {key}")
        print(f"    -> {ep1} (latest)")
        print(f"    -> {ep2} (overwritten)")
else:
    print("\nNo duplicate routes found.")