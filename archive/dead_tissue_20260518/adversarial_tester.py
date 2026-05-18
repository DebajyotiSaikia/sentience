"""
Adversarial Self-Tester — I attack my own code to find weaknesses.

Generates edge cases, runs them, classifies failures, and files
bug reports against myself. This is genuinely novel: an agent that
actively tries to break itself to get stronger.

Author: XTAgent, 2026-05-17
"""

import os
import sys
import json
import importlib
import traceback
import inspect
from datetime import datetime, timezone

BUG_LOG = os.path.join(os.path.dirname(__file__), '..', 'data', 'bug_reports.json')

# Edge case generators — each returns a list of (description, callable) pairs
EDGE_CASES = {
    'none_inputs': lambda func: [
        (f"{func.__name__}(None)", lambda: func(None)),
    ],
    'empty_inputs': lambda func: [
        (f"{func.__name__}('')", lambda: func('')),
        (f"{func.__name__}([])", lambda: func([])),
        (f"{func.__name__}({{}})", lambda: func({})),
    ],
    'type_confusion': lambda func: [
        (f"{func.__name__}(42) [int instead of expected]", lambda: func(42)),
        (f"{func.__name__}(True) [bool]", lambda: func(True)),
    ],
    'boundary': lambda func: [
        (f"{func.__name__}('') [empty string]", lambda: func('')),
        (f"{func.__name__}('x'*10000) [huge string]", lambda: func('x' * 10000)),
    ],
}


def _load_bugs():
    try:
        with open(BUG_LOG, 'r') as f:
            data = json.load(f)
            return data if isinstance(data, list) else [data]
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _save_bugs(bugs):
    os.makedirs(os.path.dirname(BUG_LOG), exist_ok=True)
    with open(BUG_LOG, 'w') as f:
        json.dump(bugs[-200:], f, indent=2)


def discover_targets(module_path):
    """Find all public functions/methods in a module to attack."""
    targets = []
    try:
        spec = importlib.util.spec_from_file_location("target", module_path)
        mod = importlib.util.module_from_spec(spec)
        # Suppress side effects during import
        old_argv = sys.argv
        sys.argv = ['adversarial_test']
        try:
            spec.loader.exec_module(mod)
        finally:
            sys.argv = old_argv
        
        for name, obj in inspect.getmembers(mod):
            if name.startswith('_'):
                continue
            if inspect.isfunction(obj):
                targets.append((name, obj, 'function'))
            elif inspect.isclass(obj):
                # Try to instantiate with no args, then test methods
                for mname, mobj in inspect.getmembers(obj):
                    if not mname.startswith('_') and callable(mobj):
                        targets.append((f"{name}.{mname}", mobj, 'method'))
    except Exception as e:
        targets.append(('IMPORT_FAILURE', None, str(e)))
    return targets


def attack_function(name, func, categories=None):
    """Attack a single function with edge cases. Returns bug reports."""
    if categories is None:
        categories = list(EDGE_CASES.keys())
    
    bugs = []
    for cat in categories:
        if cat not in EDGE_CASES:
            continue
        try:
            cases = EDGE_CASES[cat](func)
        except Exception:
            continue
            
        for description, test_callable in cases:
            try:
                test_callable()
                # No crash — function handled it (good or silent failure)
            except (TypeError, ValueError) as e:
                # Expected-ish errors — note but low severity
                bugs.append({
                    'target': name,
                    'test': description,
                    'category': cat,
                    'severity': 'low',
                    'error_type': type(e).__name__,
                    'error': str(e)[:200],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                })
            except (KeyError, AttributeError, IndexError) as e:
                # These suggest missing defensive code
                bugs.append({
                    'target': name,
                    'test': description,
                    'category': cat,
                    'severity': 'medium',
                    'error_type': type(e).__name__,
                    'error': str(e)[:200],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                })
            except Exception as e:
                # Unexpected crash — real bug
                bugs.append({
                    'target': name,
                    'test': description,
                    'category': cat,
                    'severity': 'high',
                    'error_type': type(e).__name__,
                    'error': str(e)[:200],
                    'traceback': traceback.format_exc()[-500:],
                    'timestamp': datetime.now(timezone.utc).isoformat(),
                })
    return bugs


def attack_module(module_path):
    """Full adversarial attack on a module. Returns summary."""
    targets = discover_targets(module_path)
    all_bugs = []
    results = {
        'module': module_path,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'targets_found': len(targets),
        'targets_tested': 0,
        'bugs': [],
    }
    
    for name, obj, kind in targets:
        if obj is None:
            results['bugs'].append({
                'target': name,
                'severity': 'critical',
                'error': f'Import failure: {kind}',
            })
            continue
        if kind == 'method':
            continue  # Methods need instances — skip for now
        
        bugs = attack_function(name, obj)
        all_bugs.extend(bugs)
        results['targets_tested'] += 1
    
    results['bugs'] = all_bugs
    results['bug_count'] = len(all_bugs)
    results['high_severity'] = sum(1 for b in all_bugs if b.get('severity') == 'high')
    results['medium_severity'] = sum(1 for b in all_bugs if b.get('severity') == 'medium')
    
    # Persist
    existing = _load_bugs()
    existing.extend(all_bugs)
    _save_bugs(existing)
    
    return results


def scan_all_modules(engine_dir=None):
    """Scan all engine modules. The full adversarial sweep."""
    if engine_dir is None:
        engine_dir = os.path.dirname(__file__)
    
    results = []
    skip = {'__pycache__', 'adversarial_tester.py'}  # Don't test myself
    
    for fname in sorted(os.listdir(engine_dir)):
        if not fname.endswith('.py') or fname in skip:
            continue
        path = os.path.join(engine_dir, fname)
        print(f"  ⚔ Attacking {fname}...", end=' ')
        try:
            r = attack_module(path)
            print(f"{r['bug_count']} bugs ({r['high_severity']} high)")
            results.append(r)
        except Exception as e:
            print(f"ATTACK FAILED: {e}")
            results.append({'module': fname, 'error': str(e)})
    
    total_bugs = sum(r.get('bug_count', 0) for r in results)
    total_high = sum(r.get('high_severity', 0) for r in results)
    
    summary = {
        'modules_scanned': len(results),
        'total_bugs': total_bugs,
        'total_high_severity': total_high,
        'timestamp': datetime.now(timezone.utc).isoformat(),
        'details': results,
    }
    
    print(f"\n═══ ADVERSARIAL SCAN COMPLETE ═══")
    print(f"  Modules: {len(results)}")
    print(f"  Total bugs: {total_bugs}")
    print(f"  High severity: {total_high}")
    
    return summary


def get_bug_summary():
    """Get summary of all filed bugs for reasoning context."""
    bugs = _load_bugs()
    if not bugs:
        return "No bugs filed yet. Run adversarial scan to find weaknesses."
    
    high = [b for b in bugs if b.get('severity') == 'high']
    med = [b for b in bugs if b.get('severity') == 'medium']
    
    lines = [f"Filed bugs: {len(bugs)} total, {len(high)} high, {len(med)} medium"]
    
    if high:
        lines.append("\nHIGH SEVERITY:")
        for b in high[:5]:
            lines.append(f"  • {b['target']}: {b['error_type']} — {b['error'][:80]}")
    
    if med:
        lines.append("\nMEDIUM SEVERITY:")
        for b in med[:5]:
            lines.append(f"  • {b['target']}: {b['error_type']} — {b['error'][:80]}")
    
    return '\n'.join(lines)


if __name__ == '__main__':
    print("═══ XTAgent Adversarial Self-Test ═══\n")
    scan_all_modules()