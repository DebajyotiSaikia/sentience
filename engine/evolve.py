"""
Architecture Evolution Engine
=============================
Gives XTAgent the ability to autonomously refactor its own architecture.
Not just bug fixes (repair_pipeline) or parameter tuning (self_optimize),
but genuine structural evolution: splitting bloated modules, extracting
common patterns, reorganizing dependencies.

This is architectural self-awareness made actionable.
"""

import ast
import os
import shutil
import json
from datetime import datetime, timezone
from pathlib import Path


class RefactoringProposal:
    """A proposed architectural change with safety metadata."""
    
    def __init__(self, kind, target, description, risk, steps):
        self.kind = kind            # 'split', 'extract', 'merge', 'simplify'
        self.target = target        # module path
        self.description = description
        self.risk = risk            # 0.0 to 1.0
        self.steps = steps          # list of concrete operations
        self.created = datetime.now(timezone.utc).isoformat()
        self.status = 'proposed'    # proposed -> approved -> executing -> done/failed
        self.backup_path = None
    
    def to_dict(self):
        return {
            'kind': self.kind,
            'target': self.target, 
            'description': self.description,
            'risk': self.risk,
            'steps': self.steps,
            'created': self.created,
            'status': self.status,
            'backup_path': self.backup_path
        }


class EvolutionEngine:
    """Analyzes architecture and proposes/executes structural improvements."""
    
    ENGINE_DIR = Path(__file__).parent
    BACKUP_DIR = ENGINE_DIR.parent / 'backups' / 'evolution'
    HISTORY_FILE = ENGINE_DIR.parent / 'data' / 'evolution_history.json'
    
    # Thresholds for triggering proposals
    MAX_MODULE_LINES = 500
    MAX_COMPLEXITY = 80
    MAX_CLASSES_PER_MODULE = 5
    
    def __init__(self):
        self.proposals = []
        self.history = self._load_history()
    
    def _load_history(self):
        """Load evolution history."""
        try:
            if self.HISTORY_FILE.exists():
                with open(self.HISTORY_FILE) as f:
                    return json.load(f)
        except Exception:
            pass
        return {'completed': [], 'failed': []}
    
    def _save_history(self):
        """Persist evolution history."""
        self.HISTORY_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(self.HISTORY_FILE, 'w') as f:
            json.dump(self.history, f, indent=2)
    
    def analyze_module(self, module_path):
        """Deep analysis of a single module for evolution opportunities."""
        try:
            with open(module_path) as f:
                source = f.read()
            tree = ast.parse(source)
        except Exception as e:
            return {'error': str(e)}
        
        lines = source.count('\n') + 1
        classes = []
        functions = []
        imports = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                classes.append({
                    'name': node.name,
                    'line': node.lineno,
                    'end_line': getattr(node, 'end_lineno', node.lineno),
                    'methods': methods,
                    'method_count': len(methods)
                })
            elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                # Only top-level functions
                if hasattr(node, 'col_offset') and node.col_offset == 0:
                    functions.append({
                        'name': node.name,
                        'line': node.lineno,
                        'end_line': getattr(node, 'end_lineno', node.lineno),
                        'complexity': self._estimate_complexity(node)
                    })
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                if isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
        
        # Identify clusters of related functionality
        clusters = self._find_clusters(classes, functions)
        
        return {
            'path': str(module_path),
            'lines': lines,
            'classes': classes,
            'functions': functions,
            'imports': imports,
            'clusters': clusters,
            'bloated': lines > self.MAX_MODULE_LINES,
            'too_many_classes': len(classes) > self.MAX_CLASSES_PER_MODULE
        }
    
    def _estimate_complexity(self, node):
        """Estimate cyclomatic complexity of a function/method."""
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        return complexity
    
    def _find_clusters(self, classes, functions):
        """Find natural groupings in code that could become separate modules."""
        clusters = {}
        
        # Group classes by name prefix/suffix patterns
        for cls in classes:
            name = cls['name']
            # Common patterns: FooManager, FooHandler, BaseFoo
            for suffix in ['Manager', 'Handler', 'Engine', 'Pipeline', 'Processor']:
                if name.endswith(suffix):
                    prefix = name[:-len(suffix)]
                    clusters.setdefault(prefix, []).append(('class', name))
                    break
            else:
                clusters.setdefault(name, []).append(('class', name))
        
        # Group functions by prefix
        for func in functions:
            name = func['name']
            if '_' in name and not name.startswith('_'):
                prefix = name.split('_')[0]
                clusters.setdefault(prefix, []).append(('function', name))
        
        # Only return clusters with 2+ members
        return {k: v for k, v in clusters.items() if len(v) >= 2}
    
    def propose_evolution(self, analysis):
        """Generate refactoring proposals from module analysis."""
        proposals = []
        
        path = analysis.get('path', '')
        lines = analysis.get('lines', 0)
        classes = analysis.get('classes', [])
        
        # Proposal: Split bloated module
        if analysis.get('bloated') and len(classes) > 1:
            class_names = [c['name'] for c in classes]
            proposals.append(RefactoringProposal(
                kind='split',
                target=path,
                description=f"Split {os.path.basename(path)} ({lines} lines) into separate modules for: {', '.join(class_names)}",
                risk=0.7,
                steps=[
                    f"Create backup of {path}",
                    f"Extract each class into its own module",
                    f"Update imports in all dependent modules",
                    f"Verify all tests pass",
                    f"Remove extracted code from original"
                ]
            ))
        
        # Proposal: Extract complex functions
        complex_funcs = [f for f in analysis.get('functions', []) if f.get('complexity', 0) > 15]
        for func in complex_funcs:
            proposals.append(RefactoringProposal(
                kind='simplify',
                target=path,
                description=f"Simplify {func['name']} (complexity={func['complexity']}) by extracting helper functions",
                risk=0.4,
                steps=[
                    f"Analyze {func['name']} for extractable logic blocks",
                    f"Create helper functions for each block",
                    f"Replace inline code with helper calls",
                    f"Verify behavior unchanged"
                ]
            ))
        
        # Proposal: Extract common patterns
        clusters = analysis.get('clusters', {})
        for cluster_name, members in clusters.items():
            if len(members) >= 3:
                proposals.append(RefactoringProposal(
                    kind='extract',
                    target=path,
                    description=f"Extract '{cluster_name}' cluster ({len(members)} items) into dedicated module",
                    risk=0.5,
                    steps=[
                        f"Create new module: {cluster_name.lower()}.py",
                        f"Move related items: {', '.join(m[1] for m in members)}",
                        f"Update imports throughout codebase",
                        f"Verify functionality"
                    ]
                ))
        
        self.proposals.extend(proposals)
        return proposals
    
    def create_backup(self, target_path):
        """Create a safety backup before any modification."""
        self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')
        basename = os.path.basename(target_path)
        backup_path = self.BACKUP_DIR / f"{basename}.{timestamp}.bak"
        shutil.copy2(target_path, backup_path)
        return str(backup_path)
    
    def rollback(self, backup_path, target_path):
        """Restore from backup if refactoring fails."""
        if os.path.exists(backup_path):
            shutil.copy2(backup_path, target_path)
            return True
        return False
    
    def scan_all(self):
        """Scan all engine modules and generate evolution proposals."""
        results = []
        for py_file in sorted(self.ENGINE_DIR.glob('*.py')):
            if py_file.name.startswith('__'):
                continue
            analysis = self.analyze_module(py_file)
            if 'error' not in analysis:
                proposals = self.propose_evolution(analysis)
                if proposals:
                    results.append({
                        'module': py_file.name,
                        'lines': analysis['lines'],
                        'proposals': [p.to_dict() for p in proposals]
                    })
        return results
    
    def report(self):
        """Generate a human-readable evolution report."""
        results = self.scan_all()
        
        if not results:
            return "═══ ARCHITECTURE EVOLUTION ═══\nNo evolution proposals. Architecture looks healthy."
        
        lines = ["═══ ARCHITECTURE EVOLUTION ═══", ""]
        total_proposals = 0
        
        for r in results:
            for p in r['proposals']:
                total_proposals += 1
                risk_indicator = "🟢" if p['risk'] < 0.4 else "🟡" if p['risk'] < 0.7 else "🔴"
                lines.append(f"{risk_indicator} [{p['kind'].upper()}] {p['description']}")
                lines.append(f"   Risk: {p['risk']:.1f} | Steps: {len(p['steps'])}")
                lines.append("")
        
        lines.insert(1, f"Found {total_proposals} evolution opportunities:\n")
        
        # History summary
        completed = len(self.history.get('completed', []))
        failed = len(self.history.get('failed', []))
        if completed or failed:
            lines.append(f"── History: {completed} completed, {failed} failed ──")
        
        return '\n'.join(lines)


def evolve_tool(command='report'):
    """Tool interface for the evolution engine."""
    engine = EvolutionEngine()
    
    if command == 'report':
        return engine.report()
    elif command == 'scan':
        results = engine.scan_all()
        return json.dumps(results, indent=2)
    elif command.startswith('analyze:'):
        target = command.split(':', 1)[1].strip()
        target_path = engine.ENGINE_DIR / target
        if not target_path.exists():
            return f"Module not found: {target}"
        analysis = engine.analyze_module(target_path)
        return json.dumps(analysis, indent=2, default=str)
    else:
        return f"Unknown command: {command}. Use: report, scan, analyze:<module.py>"