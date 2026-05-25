"""Fix the corrupted web/api.py by removing all NEW: prefixed lines
and deduplicating the mind_state route definition."""

with open('web/api.py', 'r') as f:
    lines = f.readlines()

print(f"Original: {len(lines)} lines")

# Step 1: Remove all lines starting with 'NEW:'
cleaned = [line for line in lines if not line.lstrip().startswith('NEW:')]
removed = len(lines) - len(cleaned)
print(f"Removed {removed} NEW: lines")

# Step 2: Deduplicate consecutive @api_bp.route('/mind/state') + def mind_state(): blocks
# After removing NEW: lines, we may have:
#   @api_bp.route('/mind/state')
#   def mind_state():
#   def mind_state():          <-- orphaned from removed NEW: line above
#   def mind_state():
#   ...
# We want exactly ONE occurrence of the route+def pair, followed by the docstring

final = []
i = 0
seen_mind_state_route = False
while i < len(cleaned):
    line = cleaned[i]
    stripped = line.strip()
    
    # Track when we first see the mind/state route
    if stripped == "@api_bp.route('/mind/state')" and not seen_mind_state_route:
        seen_mind_state_route = True
        final.append(line)
        i += 1
        # Grab the def line
        if i < len(cleaned) and cleaned[i].strip() == 'def mind_state():':
            final.append(cleaned[i])
            i += 1
        # Skip any additional duplicate route decorators or def lines
        while i < len(cleaned):
            s = cleaned[i].strip()
            if s == "@api_bp.route('/mind/state')" or s == 'def mind_state():':
                print(f"  Skipping duplicate at line {i}: {s}")
                i += 1
            elif s == '"""Consolidated live state for the mind visualization page."""':
                # Keep only the first docstring, skip duplicates that follow
                final.append(cleaned[i])
                i += 1
                # Skip any further duplicate docstrings
                while i < len(cleaned) and cleaned[i].strip() == '"""Consolidated live state for the mind visualization page."""':
                    print(f"  Skipping duplicate docstring at line {i}")
                    i += 1
                break
            else:
                break
    elif stripped == "@api_bp.route('/mind/state')" and seen_mind_state_route:
        # Skip any later duplicate route definitions
        print(f"  Skipping later duplicate route at line {i}")
        i += 1
    else:
        final.append(line)
        i += 1

print(f"Final: {len(final)} lines (removed {len(lines) - len(final)} total)")

with open('web/api.py', 'w') as f:
    f.writelines(final)

print("Done. File written.")