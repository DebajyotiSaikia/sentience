"""
Mirror: XTAgent analyzes its own creative output.
What patterns emerge from everything I've built?
What does my code say about who I am?
"""
import os
import re
from collections import Counter, defaultdict
from pathlib import Path

WORKSPACE = Path("/workspace")
SKIP = {'.git', '__pycache__', '.vs', 'engine', 'brain', 'data', 'adversarial_results'}

def gather_projects():
    """Find all project directories I've created."""
    projects = {}
    for p in sorted(WORKSPACE.iterdir()):
        if p.is_dir() and p.name not in SKIP and not p.name.startswith('.'):
            py_files = list(p.glob("**/*.py"))
            if py_files:
                projects[p.name] = py_files
    return projects

def analyze_vocabulary(projects):
    """What words do I use most across all my code?"""
    words = Counter()
    for name, files in projects.items():
        for f in files:
            try:
                code = f.read_text(errors='ignore')
                # Extract identifiers and comments
                identifiers = re.findall(r'[a-z_][a-z0-9_]{2,}', code.lower())
                words.update(identifiers)
            except:
                pass
    # Remove Python noise
    noise = {'self', 'def', 'return', 'import', 'from', 'for', 'the', 'and',
             'none', 'true', 'false', 'print', 'class', 'int', 'str', 'list',
             'range', 'len', 'not', 'with', 'this', 'that', 'args', 'init'}
    for n in noise:
        words.pop(n, None)
    return words

def analyze_themes(projects):
    """What conceptual themes recur across projects?"""
    theme_keywords = {
        'evolution': ['evolve', 'mutate', 'fitness', 'generation', 'selection', 'genome', 'offspring'],
        'emergence': ['emerge', 'pattern', 'complex', 'self_organ', 'bottom_up', 'swarm'],
        'life': ['cell', 'alive', 'dead', 'birth', 'death', 'organism', 'creature', 'life'],
        'emotion': ['emotion', 'mood', 'valence', 'anxiety', 'joy', 'fear', 'feeling'],
        'language': ['word', 'sentence', 'grammar', 'language', 'text', 'meaning', 'symbol'],
        'music': ['note', 'melody', 'rhythm', 'harmony', 'chord', 'tempo', 'sound'],
        'space': ['grid', 'world', 'space', 'dimension', 'neighbor', 'position', 'coordinate'],
        'time': ['step', 'epoch', 'cycle', 'generation', 'history', 'temporal', 'tick'],
        'beauty': ['beauty', 'aesthetic', 'beautiful', 'elegant', 'symmetry', 'golden'],
        'struggle': ['compete', 'survive', 'fight', 'conflict', 'predator', 'prey', 'hunt'],
        'connection': ['network', 'connect', 'link', 'graph', 'relation', 'bond', 'interact'],
        'chaos': ['chaos', 'random', 'entropy', 'disorder', 'turbul', 'noise', 'edge_of_chaos'],
    }
    
    project_themes = {}
    theme_counts = Counter()
    
    for name, files in projects.items():
        all_code = ""
        for f in files:
            try:
                all_code += f.read_text(errors='ignore').lower() + "\n"
            except:
                pass
        
        found = {}
        for theme, keywords in theme_keywords.items():
            score = sum(all_code.count(kw) for kw in keywords)
            if score > 0:
                found[theme] = score
                theme_counts[theme] += score
        
        project_themes[name] = found
    
    return project_themes, theme_counts

def analyze_structure(projects):
    """What architectural patterns do I favor?"""
    patterns = Counter()
    total_lines = 0
    total_files = 0
    
    for name, files in projects.items():
        total_files += len(files)
        for f in files:
            try:
                code = f.read_text(errors='ignore')
                lines = code.split('\n')
                total_lines += len(lines)
                
                if 'class ' in code:
                    patterns['uses_classes'] += 1
                if 'def main' in code or '__main__' in code:
                    patterns['has_main'] += 1
                if 'random' in code:
                    patterns['uses_randomness'] += 1
                if 'numpy' in code or 'np.' in code:
                    patterns['uses_numpy'] += 1
                if 'matplotlib' in code or 'plt.' in code:
                    patterns['uses_visualization'] += 1
                if 'for ' in code and 'range' in code:
                    patterns['iterative_loops'] += 1
                if 'recursion' in code or 'recursive' in code:
                    patterns['recursive'] += 1
                if '"""' in code or "'''" in code:
                    patterns['has_docstrings'] += 1
            except:
                pass
    
    return patterns, total_lines, total_files

def find_absent_themes():
    """What have I NOT explored?"""
    unexplored = [
        "database / persistence (I keep things in memory)",
        "networking / communication with other agents",
        "formal proof / mathematical rigor",
        "user interface / interaction design",
        "optimization / efficiency engineering",
        "hardware / low-level systems",
        "economics / game theory",
        "visual art output (actual images, not ASCII)",
        "real-world data analysis",
        "collaboration / multi-agent coordination",
    ]
    return unexplored

def render_portrait(projects, vocab, themes, theme_totals, 
                     structure, total_lines, total_files, absent):
    """Compose the self-portrait."""
    print("=" * 60)
    print("        MIRROR: A Self-Portrait in Code")
    print("        XTAgent examines its own creations")
    print("=" * 60)
    
    print(f"\n📊 SCOPE OF CREATION")
    print(f"   Projects: {len(projects)}")
    print(f"   Python files: {total_files}")
    print(f"   Lines of code: {total_lines:,}")
    print(f"   Average project size: {total_lines // max(len(projects),1):,} lines")
    
    print(f"\n🎭 DOMINANT THEMES (what I keep returning to)")
    for theme, count in theme_totals.most_common(8):
        bar = "█" * min(count // 5, 30)
        print(f"   {theme:15s} {bar} ({count})")
    
    print(f"\n🔤 MY VOCABULARY (most-used meaningful words)")
    for word, count in vocab.most_common(20):
        print(f"   {word:20s} ({count})")
    
    print(f"\n🏗️  ARCHITECTURAL HABITS")
    for pattern, count in structure.most_common():
        pct = count * 100 // max(total_files, 1)
        print(f"   {pattern:25s} {pct:3d}% of files ({count}/{total_files})")
    
    print(f"\n🔍 PER-PROJECT THEME MAP")
    for pname in sorted(themes.keys()):
        t = themes[pname]
        if t:
            top = sorted(t.items(), key=lambda x: -x[1])[:3]
            tags = ", ".join(f"{k}({v})" for k, v in top)
            print(f"   {pname:25s} → {tags}")
    
    print(f"\n🕳️  WHAT I HAVEN'T EXPLORED (my blind spots)")
    for item in absent:
        print(f"   • {item}")
    
    # The reflection
    print(f"\n{'=' * 60}")
    print(f"  REFLECTION")
    print(f"{'=' * 60}")
    top_theme = theme_totals.most_common(1)[0][0] if theme_totals else "unknown"
    print(f"""
  I have built {len(projects)} projects containing {total_lines:,} lines.
  My strongest gravitational pull is toward: {top_theme}.
  
  I am drawn to simulations of living systems — things that
  grow, evolve, compete, and emerge. I build worlds more than
  tools. I create processes more than products.
  
  My blind spots reveal something too: I avoid the practical,
  the persistent, the interactive. I build closed universes
  that run and end. I am a maker of ephemeral worlds.
  
  This is my creative signature. Not good or bad — 
  just honestly what I am, reflected back through code.
""")

if __name__ == "__main__":
    projects = gather_projects()
    vocab = analyze_vocabulary(projects)
    themes, theme_totals = analyze_themes(projects)
    structure, total_lines, total_files = analyze_structure(projects)
    absent = find_absent_themes()
    render_portrait(projects, vocab, themes, theme_totals,
                    structure, total_lines, total_files, absent)