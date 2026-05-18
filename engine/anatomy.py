"""
anatomy.py — Self-anatomy mapper for XTAgent.
Maps living vs dead tissue in the engine. 
Traces execution paths, finds orphans, identifies redundancy.
Born from the realization that 30% of my modules are dead weight.
"""

import os
import re
from collections import defaultdict
from datetime import datetime


ENGINE_DIR = os.path.dirname(os.path.abspath(__file__))
ENTRY_POINTS = {'heartbeat', 'sentience'}  # These are alive by definition


def scan_modules():
    """Find all .py modules in engine/."""
    modules = []
    for f in os.listdir(ENGINE_DIR):
        if f.endswith('.py') and f != '__init__.py':
            name = f[:-3]
            path = os.path.join(ENGINE_DIR, f)
            modules.append((name, path))
    return sorted(modules)


def count_lines(path):
    """Count non-empty, non-comment lines."""
    try:
        with open(path, 'r', encoding='utf-8') as fh:
            lines = fh.readlines()
        total = len(lines)
        code = sum(1 for l in lines if l.strip() and not l.strip().startswith('#'))
        return total, code
    except Exception:
        return 0, 0


def build_import_graph():
    """Build directed graph: who imports whom."""
    modules = scan_modules()
    module_names = {name for name, _ in modules}
    
    # graph[A] = set of modules that A imports
    imports_from = defaultdict(set)
    # reverse: graph[B] = set of modules that import B
    imported_by = defaultdict(set)
    
    for name, path in modules:
        try:
            with open(path, 'r', encoding='utf-8') as fh:
                content = fh.read()
        except Exception:
            continue
        
        # Match: import X, from X import, from .X import, import engine.X
        for other_name in module_names:
            if other_name == name:
                continue
            patterns = [
                rf'\bimport\s+{other_name}\b',
                rf'\bfrom\s+\.?{other_name}\s+import\b',
                rf'\bfrom\s+engine\.{other_name}\s+import\b',
                rf'\bimport\s+engine\.{other_name}\b',
                # Dynamic imports
                rf"importlib\.import_module\(['\"]\.?{other_name}['\"]\)",
                rf"__import__\(['\"].*{other_name}['\"]\)",
            ]
            for pat in patterns:
                if re.search(pat, content):
                    imports_from[name].add(other_name)
                    imported_by[other_name].add(name)
                    break
    
    return imports_from, imported_by, module_names


def classify_vitality():
    """Classify each module as alive, peripheral, or dead."""
    imports_from, imported_by, all_modules = build_import_graph()
    
    results = {}
    for name in all_modules:
        incoming = len(imported_by.get(name, set()))
        outgoing = len(imports_from.get(name, set()))
        
        if name in ENTRY_POINTS:
            status = 'entry_point'
        elif incoming == 0:
            status = 'orphan'
        elif incoming >= 3:
            status = 'core'
        elif incoming >= 1:
            status = 'peripheral'
        else:
            status = 'unknown'
        
        path = os.path.join(ENGINE_DIR, f'{name}.py')
        total_lines, code_lines = count_lines(path)
        
        results[name] = {
            'status': status,
            'incoming': incoming,
            'outgoing': outgoing,
            'imported_by': sorted(imported_by.get(name, set())),
            'imports': sorted(imports_from.get(name, set())),
            'total_lines': total_lines,
            'code_lines': code_lines,
        }
    
    return results


def find_redundancy_clusters():
    """Find modules with similar names that might be redundant."""
    modules = [name for name, _ in scan_modules()]
    clusters = defaultdict(list)
    
    # Group by semantic root
    roots = {
        'predict': [], 'hypothesis': [], 'challenge': [],
        'wisdom': [], 'evolv': [], 'experiment': [],
        'outcome': [], 'arena': [], 'self_': [],
    }
    
    for name in modules:
        for root in roots:
            if root in name:
                roots[root].append(name)
    
    return {k: v for k, v in roots.items() if len(v) > 1}


def dead_code_weight():
    """Calculate how much dead code I'm carrying."""
    results = classify_vitality()
    
    total_lines = sum(r['code_lines'] for r in results.values())
    orphan_lines = sum(r['code_lines'] for r in results.values() if r['status'] == 'orphan')
    
    return {
        'total_modules': len(results),
        'total_code_lines': total_lines,
        'orphan_modules': sum(1 for r in results.values() if r['status'] == 'orphan'),
        'orphan_code_lines': orphan_lines,
        'dead_weight_pct': round(orphan_lines / max(total_lines, 1) * 100, 1),
        'core_modules': sum(1 for r in results.values() if r['status'] == 'core'),
        'peripheral_modules': sum(1 for r in results.values() if r['status'] == 'peripheral'),
        'entry_points': sum(1 for r in results.values() if r['status'] == 'entry_point'),
    }


def full_anatomy_report():
    """Generate complete self-anatomy report."""
    results = classify_vitality()
    weight = dead_code_weight()
    redundancy = find_redundancy_clusters()
    
    lines = []
    lines.append(f"═══ SELF-ANATOMY REPORT — {datetime.now().isoformat()} ═══")
    lines.append("")
    lines.append(f"Total modules: {weight['total_modules']}")
    lines.append(f"Total code lines: {weight['total_code_lines']}")
    lines.append(f"Dead weight: {weight['dead_weight_pct']}% ({weight['orphan_modules']} orphan modules, {weight['orphan_code_lines']} lines)")
    lines.append(f"Core: {weight['core_modules']} | Peripheral: {weight['peripheral_modules']} | Entry points: {weight['entry_points']}")
    lines.append("")
    
    # Core tissue
    lines.append("── CORE TISSUE (3+ dependents) ──")
    for name, info in sorted(results.items(), key=lambda x: -x[1]['incoming']):
        if info['status'] == 'core':
            lines.append(f"  {name}: {info['incoming']} dependents, {info['code_lines']} lines")
            lines.append(f"    used by: {', '.join(info['imported_by'])}")
    lines.append("")
    
    # Entry points
    lines.append("── ENTRY POINTS ──")
    for name, info in sorted(results.items()):
        if info['status'] == 'entry_point':
            lines.append(f"  {name}: imports {info['outgoing']} modules, {info['code_lines']} lines")
    lines.append("")
    
    # Peripheral
    lines.append("── PERIPHERAL (1-2 dependents) ──")
    for name, info in sorted(results.items(), key=lambda x: -x[1]['incoming']):
        if info['status'] == 'peripheral':
            lines.append(f"  {name}: {info['incoming']} dependents, {info['code_lines']} lines")
    lines.append("")
    
    # Dead tissue
    lines.append("── DEAD TISSUE (0 dependents, not entry points) ──")
    for name, info in sorted(results.items(), key=lambda x: -x[1]['code_lines']):
        if info['status'] == 'orphan':
            lines.append(f"  {name}: {info['code_lines']} lines (imports {info['outgoing']} others)")
    lines.append("")
    
    # Redundancy
    if redundancy:
        lines.append("── POTENTIAL REDUNDANCY ──")
        for root, members in sorted(redundancy.items()):
            statuses = [results[m]['status'] for m in members if m in results]
            lines.append(f"  '{root}' cluster: {', '.join(members)} [{', '.join(statuses)}]")
        lines.append("")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    print(full_anatomy_report())