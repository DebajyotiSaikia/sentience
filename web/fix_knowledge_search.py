"""Remove duplicate API routes from knowledge_search.py.
Canonical API endpoints live in knowledge_api.py."""

filepath = 'web/knowledge_search.py'
lines = open(filepath).readlines()

cut_at = None
for i, line in enumerate(lines):
    if "@knowledge_search_bp.route('/api/knowledge/search')" in line:
        cut_at = i
        break

if cut_at is not None:
    # Also remove any decorator above it (like 2 blank lines)
    while cut_at > 0 and lines[cut_at - 1].strip() == '':
        cut_at -= 1
    kept = lines[:cut_at]
    kept.append('\n# API routes removed — canonical endpoints live in knowledge_api.py\n')
    open(filepath, 'w').writelines(kept)
    print(f'Cut {len(lines) - cut_at} lines starting at line {cut_at + 1}.')
    print(f'{len(kept)} lines remain.')
else:
    print('API route not found — already removed?')