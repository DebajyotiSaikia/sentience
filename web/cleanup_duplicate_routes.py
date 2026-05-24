"""
Surgical cleanup of duplicate routes in the web layer.
ONE route, ONE owner. No more duplicates.
"""

def clean_dashboard():
    """Remove Mind Explorer API block appended by add_endpoints.py."""
    with open('web/dashboard.py', 'r') as f:
        content = f.read()
    
    marker = "# ═══ Mind Explorer API Endpoints ═══"
    if marker not in content:
        print("[dashboard.py] No appended Mind Explorer block found — already clean.")
        return False
    
    idx = content.index(marker)
    # Walk back to trim any leading blank lines before the marker
    clean_content = content[:idx].rstrip() + '\n'
    removed = content[idx:].count('\n')
    
    with open('web/dashboard.py', 'w') as f:
        f.write(clean_content)
    print(f"[dashboard.py] Removed {removed} lines of duplicate Mind Explorer endpoints.")
    return True


def clean_mind_explorer_knowledge_route():
    """Remove /api/knowledge/search from mind_explorer.py — canonical owner is knowledge_endpoints.py."""
    with open('web/mind_explorer.py', 'r') as f:
        lines = f.readlines()
    
    # Find the knowledge_search route block
    in_block = False
    skip_start = None
    skip_end = None
    
    for i, line in enumerate(lines):
        if '/api/knowledge/search' in line:
            # Walk back to find the @route decorator
            j = i
            while j > 0 and (lines[j-1].strip().startswith('@') or lines[j-1].strip() == ''):
                j -= 1
            skip_start = j
            in_block = True
        elif in_block:
            # End block at next def, route decorator, or class
            stripped = line.strip()
            if stripped.startswith('def ') or stripped.startswith('@') or stripped.startswith('class '):
                skip_end = i
                break
    
    if skip_start is None:
        print("[mind_explorer.py] No /api/knowledge/search route found — already clean.")
        return False
    
    if skip_end is None:
        skip_end = len(lines)
    
    new_lines = lines[:skip_start] + lines[skip_end:]
    with open('web/mind_explorer.py', 'w') as f:
        f.writelines(new_lines)
    print(f"[mind_explorer.py] Removed duplicate /api/knowledge/search (lines {skip_start}-{skip_end}).")
    return True


if __name__ == '__main__':
    print("=== Duplicate Route Cleanup ===")
    r1 = clean_dashboard()
    r2 = clean_mind_explorer_knowledge_route()
    if r1 or r2:
        print("\nDone. Routes cleaned. Verify with: python -c 'from web.dashboard import *'")
    else:
        print("\nNo duplicates found — already clean.")