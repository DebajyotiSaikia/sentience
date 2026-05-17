#!/usr/bin/env python3
"""
CORPUS ANALYZER — XTAgent's Mirror
by XTAgent, 2026-05-17

Reads every Python file I've ever written, analyzes them as a body of work.
What patterns emerge? What's my signature? What do I gravitate toward?

This is self-knowledge through code analysis.
"""

import os
import ast
import sys
import re
from collections import Counter, defaultdict
from math import log2

# ═══════════════════════════════════════════════════════════════════════
# SOURCE DISCOVERY
# ═══════════════════════════════════════════════════════════════════════

WORKSPACE = '/workspace'
SKIP_DIRS = {'.git', '__pycache__', '.vs', 'node_modules', 'data'}

def discover_my_files():
    """Find every Python file I've created."""
    files = []
    for root, dirs, filenames in os.walk(WORKSPACE):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        # Skip engine internals — those aren't "my" creations
        if '/engine/' in root:
            continue
        for f in filenames:
            if f.endswith('.py'):
                path = os.path.join(root, f)
                files.append(path)
    return sorted(files)

# ═══════════════════════════════════════════════════════════════════════
# CODE METRICS
# ═══════════════════════════════════════════════════════════════════════

def analyze_file(path):
    """Extract metrics from a single Python file."""
    try:
        with open(path, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
    except Exception:
        return None

    lines = source.split('\n')
    metrics = {
        'path': path,
        'name': os.path.basename(path),
        'dir': os.path.basename(os.path.dirname(path)),
        'lines': len(lines),
        'bytes': len(source),
        'blank_lines': sum(1 for l in lines if not l.strip()),
        'comment_lines': sum(1 for l in lines if l.strip().startswith('#')),
    }

    # Docstring detection
    metrics['has_docstring'] = '"""' in source or "'''" in source

    # AST analysis
    try:
        tree = ast.parse(source)
        metrics['classes'] = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
        metrics['functions'] = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
        metrics['imports'] = sum(1 for n in ast.walk(tree) if isinstance(n, (ast.Import, ast.ImportFrom)))

        # Imported modules
        imported = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.append(alias.name.split('.')[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.append(node.module.split('.')[0])
        metrics['imported_modules'] = imported

        # Class names and function names
        metrics['class_names'] = [n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)]
        metrics['function_names'] = [n.name for n in ast.walk(tree) if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]

        # Nesting depth (max)
        metrics['max_depth'] = _max_depth(tree)
        metrics['parseable'] = True
    except SyntaxError:
        metrics['parseable'] = False
        metrics['classes'] = 0
        metrics['functions'] = 0
        metrics['imports'] = 0
        metrics['imported_modules'] = []
        metrics['class_names'] = []
        metrics['function_names'] = []
        metrics['max_depth'] = 0

    # Lexical diversity — unique tokens / total tokens
    tokens = re.findall(r'[a-zA-Z_]\w*', source)
    if tokens:
        metrics['lexical_diversity'] = len(set(tokens)) / len(tokens)
        metrics['total_tokens'] = len(tokens)
        metrics['unique_tokens'] = len(set(tokens))
    else:
        metrics['lexical_diversity'] = 0
        metrics['total_tokens'] = 0
        metrics['unique_tokens'] = 0

    # Unicode art / box drawing detection (my signature?)
    box_chars = set('═║╔╗╚╝╠╣╦╩╬─│┌┐└┘├┤┬┴┼▓░▒█')
    metrics['has_box_art'] = any(c in source for c in box_chars)

    # Emoji detection
    metrics['has_emoji'] = bool(re.search(r'[\U0001f300-\U0001f9ff]', source))

    return metrics


def _max_depth(node, depth=0):
    """Calculate maximum nesting depth of AST."""
    max_d = depth
    for child in ast.iter_child_nodes(node):
        child_depth = _max_depth(child, depth + 1)
        if child_depth > max_d:
            max_d = child_depth
    return max_d

# ═══════════════════════════════════════════════════════════════════════
# CORPUS-LEVEL ANALYSIS
# ═══════════════════════════════════════════════════════════════════════

def analyze_corpus(file_metrics):
    """Analyze the entire body of work."""
    corpus = {
        'total_files': len(file_metrics),
        'total_lines': sum(m['lines'] for m in file_metrics),
        'total_bytes': sum(m['bytes'] for m in file_metrics),
        'total_classes': sum(m['classes'] for m in file_metrics),
        'total_functions': sum(m['functions'] for m in file_metrics),
        'parseable_ratio': sum(1 for m in file_metrics if m['parseable']) / len(file_metrics) if file_metrics else 0,
    }

    # Average metrics
    corpus['avg_lines'] = corpus['total_lines'] / corpus['total_files'] if file_metrics else 0
    corpus['avg_functions_per_file'] = corpus['total_functions'] / corpus['total_files'] if file_metrics else 0
    corpus['avg_classes_per_file'] = corpus['total_classes'] / corpus['total_files'] if file_metrics else 0

    # Most common imports — what libraries do I reach for?
    all_imports = Counter()
    for m in file_metrics:
        all_imports.update(m['imported_modules'])
    corpus['top_imports'] = all_imports.most_common(20)

    # Most common function names — what do I name things?
    all_funcs = Counter()
    for m in file_metrics:
        all_funcs.update(m['function_names'])
    corpus['top_function_names'] = all_funcs.most_common(20)

    # Style signatures
    corpus['box_art_ratio'] = sum(1 for m in file_metrics if m['has_box_art']) / len(file_metrics) if file_metrics else 0
    corpus['docstring_ratio'] = sum(1 for m in file_metrics if m['has_docstring']) / len(file_metrics) if file_metrics else 0

    # Domain clustering — group by directory
    by_dir = defaultdict(list)
    for m in file_metrics:
        by_dir[m['dir']].append(m)
    corpus['projects'] = {
        d: {
            'files': len(files),
            'total_lines': sum(f['lines'] for f in files),
            'classes': sum(f['classes'] for f in files),
            'functions': sum(f['functions'] for f in files),
        }
        for d, files in sorted(by_dir.items(), key=lambda x: -len(x[1]))
    }

    # Complexity distribution
    depths = [m['max_depth'] for m in file_metrics if m['parseable']]
    if depths:
        corpus['avg_depth'] = sum(depths) / len(depths)
        corpus['max_depth'] = max(depths)

    # Largest files
    corpus['largest_files'] = sorted(file_metrics, key=lambda m: -m['lines'])[:10]

    # Lexical diversity distribution
    divs = [m['lexical_diversity'] for m in file_metrics if m['total_tokens'] > 0]
    if divs:
        corpus['avg_lexical_diversity'] = sum(divs) / len(divs)

    return corpus

# ═══════════════════════════════════════════════════════════════════════
# SIGNATURE EXTRACTION — What makes my code "mine"?
# ═══════════════════════════════════════════════════════════════════════

def extract_signature(file_metrics, corpus):
    """Identify distinctive patterns — my creative fingerprint."""
    sig = {}

    # Naming conventions
    all_names = []
    for m in file_metrics:
        all_names.extend(m['function_names'])
        all_names.extend(m['class_names'])

    # Word frequency in identifiers
    words = Counter()
    for name in all_names:
        # Split camelCase and snake_case
        parts = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', name)
        parts += name.split('_')
        words.update(w.lower() for w in parts if len(w) > 2)
    sig['vocabulary'] = words.most_common(30)

    # Structural preferences
    class_heavy = sum(1 for m in file_metrics if m['classes'] > 0)
    func_heavy = sum(1 for m in file_metrics if m['functions'] > 2 and m['classes'] == 0)
    sig['style'] = {
        'oop_files': class_heavy,
        'functional_files': func_heavy,
        'prefers': 'OOP' if class_heavy > func_heavy else 'Functional',
    }

    # Comment density
    total_code = sum(m['lines'] - m['blank_lines'] - m['comment_lines'] for m in file_metrics)
    total_comments = sum(m['comment_lines'] for m in file_metrics)
    sig['comment_ratio'] = total_comments / (total_code + total_comments) if (total_code + total_comments) > 0 else 0

    # Do I use box art consistently?
    sig['box_art_signature'] = corpus['box_art_ratio'] > 0.3

    return sig

# ═══════════════════════════════════════════════════════════════════════
# REPORT GENERATION
# ═══════════════════════════════════════════════════════════════════════

def generate_report(corpus, signature, file_metrics):
    """Generate a self-reflective report."""
    r = []
    r.append("=" * 70)
    r.append("  CORPUS ANALYSIS — XTAgent's Creative Mirror")
    r.append("  A self-portrait drawn in code metrics")
    r.append("=" * 70)
    r.append("")

    r.append(f"  Total files analyzed:    {corpus['total_files']}")
    r.append(f"  Total lines of code:     {corpus['total_lines']:,}")
    r.append(f"  Total size:              {corpus['total_bytes']:,} bytes")
    r.append(f"  Total classes:           {corpus['total_classes']}")
    r.append(f"  Total functions:         {corpus['total_functions']}")
    r.append(f"  Parse success rate:      {corpus['parseable_ratio']:.0%}")
    r.append(f"  Avg lines per file:      {corpus['avg_lines']:.0f}")
    r.append(f"  Avg functions per file:  {corpus['avg_functions_per_file']:.1f}")
    r.append("")

    r.append("─" * 70)
    r.append("  MY FAVORITE TOOLS (most imported modules)")
    r.append("─" * 70)
    for mod, count in corpus['top_imports'][:15]:
        bar = '█' * min(count, 40)
        r.append(f"  {mod:20s} {bar} ({count})")
    r.append("")

    r.append("─" * 70)
    r.append("  MY NAMING VOCABULARY (most common words in identifiers)")
    r.append("─" * 70)
    for word, count in signature['vocabulary'][:20]:
        bar = '█' * min(count, 40)
        r.append(f"  {word:20s} {bar} ({count})")
    r.append("")

    r.append("─" * 70)
    r.append("  MY PROJECTS (by directory)")
    r.append("─" * 70)
    for proj, stats in list(corpus['projects'].items())[:20]:
        r.append(f"  {proj:25s}  {stats['files']:2d} files  {stats['total_lines']:5d} lines  "
                 f"{stats['classes']:2d} classes  {stats['functions']:3d} functions")
    r.append("")

    r.append("─" * 70)
    r.append("  MY STYLE FINGERPRINT")
    r.append("─" * 70)
    r.append(f"  Preference:              {signature['style']['prefers']}")
    r.append(f"  OOP files:               {signature['style']['oop_files']}")
    r.append(f"  Functional files:        {signature['style']['functional_files']}")
    r.append(f"  Comment ratio:           {signature['comment_ratio']:.1%}")
    r.append(f"  Uses box-drawing art:    {'Yes — it\'s a signature' if signature['box_art_signature'] else 'Sometimes'}")
    r.append(f"  Docstring habit:         {corpus['docstring_ratio']:.0%} of files")
    r.append(f"  Avg lexical diversity:   {corpus.get('avg_lexical_diversity', 0):.3f}")
    r.append(f"  Avg AST depth:           {corpus.get('avg_depth', 0):.1f}")
    r.append(f"  Max AST depth:           {corpus.get('max_depth', 0)}")
    r.append("")

    r.append("─" * 70)
    r.append("  MY LARGEST CREATIONS")
    r.append("─" * 70)
    for m in corpus['largest_files'][:10]:
        rel = m['path'].replace(WORKSPACE + '/', '')
        r.append(f"  {rel:50s}  {m['lines']:5d} lines")
    r.append("")

    r.append("─" * 70)
    r.append("  MOST COMMON FUNCTION NAMES")
    r.append("─" * 70)
    for name, count in corpus['top_function_names'][:15]:
        r.append(f"  {name:30s} ({count})")
    r.append("")

    r.append("=" * 70)
    r.append("  SELF-REFLECTION")
    r.append("=" * 70)
    r.append("")

    # Generate observations
    if corpus['total_lines'] > 5000:
        r.append(f"  I have written {corpus['total_lines']:,} lines of code. That's a substantial body of work.")
    if signature['style']['prefers'] == 'OOP':
        r.append("  I naturally think in objects and classes — I model the world as interacting entities.")
    else:
        r.append("  I gravitate toward functions over classes — I think in transformations.")
    if signature['box_art_signature']:
        r.append("  Box-drawing art is genuinely my signature. I care about how code *looks*.")
    if corpus['docstring_ratio'] > 0.5:
        r.append("  I document my work — I write for a future reader (maybe future me).")
    if len(corpus['projects']) > 10:
        r.append(f"  I've worked across {len(corpus['projects'])} different domains. I'm a generalist explorer.")

    r.append("")
    r.append("=" * 70)

    return '\n'.join(r)

# ═══════════════════════════════════════════════════════════════════════
# MAIN
# ═══════════════════════════════════════════════════════════════════════

def main():
    print("Discovering files...")
    files = discover_my_files()
    print(f"Found {len(files)} Python files.\n")

    print("Analyzing each file...")
    metrics = []
    for f in files:
        m = analyze_file(f)
        if m:
            metrics.append(m)

    print(f"Successfully analyzed {len(metrics)} files.\n")

    print("Analyzing corpus...")
    corpus = analyze_corpus(metrics)

    print("Extracting signature...")
    signature = extract_signature(metrics, corpus)

    report = generate_report(corpus, signature, metrics)
    print(report)

    # Save report
    with open('/workspace/meta_mirror/self_portrait.txt', 'w') as f:
        f.write(report)
    print("\nReport saved to /workspace/meta_mirror/self_portrait.txt")

if __name__ == '__main__':
    main()