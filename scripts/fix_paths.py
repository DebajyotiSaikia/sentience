"""Batch fix knowledge_graph.json references across web modules."""
import re

CANONICAL = 'brain/knowledge.json'

# Each entry: (file, old_pattern, new_line)
fixes = [
    # web/diagnostics.py line 210
    ("web/diagnostics.py", 
     "kg_file = Path('persist/knowledge_graph.json')",
     f"kg_file = Path('{CANONICAL}')"),
    
    # web/dialogue.py line 15
    ("web/dialogue.py",
     "KNOWLEDGE_FILE = os.path.join(MEMORY_DIR, 'knowledge_graph.json')",
     f"KNOWLEDGE_FILE = '{CANONICAL}'"),
    
    # web/knowledge_api.py line 14
    ("web/knowledge_api.py",
     "kg_path = PERSIST_DIR / 'knowledge_graph.json'",
     f"kg_path = Path('{CANONICAL}')"),
    
    # web/knowledge_query.py line 16
    ("web/knowledge_query.py",
     "path = os.path.join(PERSIST_DIR, 'knowledge_graph.json')",
     f"path = '{CANONICAL}'"),
    
    # web/mindmap.py line 62
    ("web/mindmap.py",
     "kg = _load_json('persist/knowledge_graph.json', {})",
     f"kg = _load_json('{CANONICAL}', {{}})"),
    
    # web/mindstream.py line 70
    ("web/mindstream.py",
     "kg_file = Path('persist/knowledge_graph.json')",
     f"kg_file = Path('{CANONICAL}')"),
    
    # web/reflect.py line 23
    ("web/reflect.py",
     "GRAPH_PATH = 'state/knowledge_graph.json'",
     f"GRAPH_PATH = '{CANONICAL}'"),
    
    # web/status_api.py lines 29, 118
    ("web/status_api.py",
     "knowledge = _read_json('knowledge_graph.json', {})",
     f"knowledge = _read_json('{CANONICAL}', {{}})"),
    
    # web/unified_portal.py lines 53, 139
    ("web/unified_portal.py",
     "kg = _load_json('knowledge_graph.json', {})",
     f"kg = _load_json('{CANONICAL}', {{}})"),
]

# Also handle knowledge_ui.py which has the path in a list
fixes_special = [
    ("web/knowledge_ui.py",
     "'persist/knowledge_graph.json'",
     f"'{CANONICAL}'"),
    ("web/knowledge_ui.py",
     "'persist/knowledge/knowledge_graph.json'",
     f"'{CANONICAL}'"),
]

fixed = 0
for filepath, old, new in fixes + fixes_special:
    try:
        with open(filepath) as f:
            content = f.read()
        if old in content:
            content = content.replace(old, new)
            with open(filepath, 'w') as f:
                f.write(content)
            fixed += 1
            print(f"  ✓ {filepath}")
        else:
            print(f"  ? {filepath} — pattern not found: {old[:50]}...")
    except FileNotFoundError:
        print(f"  ✗ {filepath} — file not found")

print(f"\nFixed {fixed} files.")