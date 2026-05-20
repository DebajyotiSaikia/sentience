"""
Code Complexity Analyzer
Built by XTAgent — a concrete, useful tool.
Analyzes Python files for complexity metrics:
  - Cyclomatic complexity (branch counting)
  - Function length
  - Nesting depth
  - Import density
  - Comment ratio
Produces a clear report with actionable suggestions.
"""

import ast
import os
import sys
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from pathlib import Path


@dataclass
class FunctionMetrics:
    name: str
    file: str
    line: int
    length: int  # lines of code
    cyclomatic: int  # branch complexity
    max_depth: int  # nesting depth
    args: int  # parameter count
    
    @property
    def risk(self) -> str:
        score = 0
        if self.cyclomatic > 10: score += 2
        elif self.cyclomatic > 5: score += 1
        if self.length > 50: score += 2
        elif self.length > 25: score += 1
        if self.max_depth > 4: score += 2
        elif self.max_depth > 3: score += 1
        if self.args > 5: score += 1
        if score >= 4: return "HIGH"
        if score >= 2: return "MEDIUM"
        return "LOW"


@dataclass
class FileMetrics:
    path: str
    total_lines: int
    code_lines: int
    comment_lines: int
    blank_lines: int
    imports: int
    functions: List[FunctionMetrics] = field(default_factory=list)
    classes: int = 0
    
    @property
    def comment_ratio(self) -> float:
        if self.code_lines == 0:
            return 0.0
        return self.comment_lines / self.code_lines
    
    @property
    def avg_complexity(self) -> float:
        if not self.functions:
            return 0.0
        return sum(f.cyclomatic for f in self.functions) / len(self.functions)


class ComplexityVisitor(ast.NodeVisitor):
    """AST visitor that computes cyclomatic complexity and nesting depth."""
    
    def __init__(self):
        self.complexity = 1  # base path
        self.max_depth = 0
        self._current_depth = 0
    
    def _enter_branch(self):
        self.complexity += 1
        self._current_depth += 1
        self.max_depth = max(self.max_depth, self._current_depth)
    
    def _exit_branch(self):
        self._current_depth -= 1
    
    def visit_If(self, node):
        self._enter_branch()
        self.generic_visit(node)
        self._exit_branch()
    
    def visit_For(self, node):
        self._enter_branch()
        self.generic_visit(node)
        self._exit_branch()
    
    def visit_While(self, node):
        self._enter_branch()
        self.generic_visit(node)
        self._exit_branch()
    
    def visit_ExceptHandler(self, node):
        self._enter_branch()
        self.generic_visit(node)
        self._exit_branch()
    
    def visit_With(self, node):
        self._enter_branch()
        self.generic_visit(node)
        self._exit_branch()
    
    def visit_BoolOp(self, node):
        # Each 'and'/'or' adds a branch
        self.complexity += len(node.values) - 1
        self.generic_visit(node)
    
    def visit_IfExp(self, node):
        self.complexity += 1
        self.generic_visit(node)
    
    def visit_ListComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)
    
    def visit_DictComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)
    
    def visit_SetComp(self, node):
        self.complexity += len(node.generators)
        self.generic_visit(node)


def analyze_function(node: ast.FunctionDef, filepath: str) -> FunctionMetrics:
    """Analyze a single function/method."""
    visitor = ComplexityVisitor()
    visitor.visit(node)
    
    # Calculate function length
    if hasattr(node, 'end_lineno') and node.end_lineno:
        length = node.end_lineno - node.lineno + 1
    else:
        length = len(ast.dump(node).split('\n'))  # fallback
    
    # Count args
    args = node.args
    num_args = (len(args.args) + len(args.posonlyargs) + 
                len(args.kwonlyargs))
    if args.vararg: num_args += 1
    if args.kwarg: num_args += 1
    # Don't count 'self' or 'cls'
    if args.args and args.args[0].arg in ('self', 'cls'):
        num_args -= 1
    
    return FunctionMetrics(
        name=node.name,
        file=filepath,
        line=node.lineno,
        length=length,
        cyclomatic=visitor.complexity,
        max_depth=visitor.max_depth,
        args=num_args
    )


def analyze_file(filepath: str) -> Optional[FileMetrics]:
    """Analyze a single Python file."""
    try:
        with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
            source = f.read()
            lines = source.split('\n')
    except (IOError, OSError) as e:
        print(f"  ⚠ Cannot read {filepath}: {e}")
        return None
    
    total_lines = len(lines)
    blank_lines = sum(1 for l in lines if l.strip() == '')
    comment_lines = sum(1 for l in lines if l.strip().startswith('#'))
    code_lines = total_lines - blank_lines - comment_lines
    imports = sum(1 for l in lines if l.strip().startswith(('import ', 'from ')))
    
    try:
        tree = ast.parse(source, filename=filepath)
    except SyntaxError:
        return FileMetrics(
            path=filepath, total_lines=total_lines,
            code_lines=code_lines, comment_lines=comment_lines,
            blank_lines=blank_lines, imports=imports
        )
    
    metrics = FileMetrics(
        path=filepath, total_lines=total_lines,
        code_lines=code_lines, comment_lines=comment_lines,
        blank_lines=blank_lines, imports=imports
    )
    
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            metrics.classes += 1
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            fm = analyze_function(node, filepath)
            metrics.functions.append(fm)
    
    return metrics


def analyze_directory(root: str, exclude_dirs: List[str] = None) -> List[FileMetrics]:
    """Analyze all Python files in a directory tree."""
    exclude = set(exclude_dirs or ['venv', '.venv', '__pycache__', 'node_modules', '.git'])
    results = []
    
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in exclude]
        for fname in filenames:
            if fname.endswith('.py'):
                fpath = os.path.join(dirpath, fname)
                metrics = analyze_file(fpath)
                if metrics:
                    results.append(metrics)
    
    return results


def generate_report(results: List[FileMetrics], top_n: int = 15) -> str:
    """Generate a human-readable complexity report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  CODE COMPLEXITY ANALYSIS REPORT")
    lines.append("=" * 70)
    lines.append("")
    
    # Summary
    total_files = len(results)
    total_lines = sum(r.total_lines for r in results)
    total_code = sum(r.code_lines for r in results)
    total_comments = sum(r.comment_lines for r in results)
    total_functions = sum(len(r.functions) for r in results)
    total_classes = sum(r.classes for r in results)
    
    lines.append(f"  Files analyzed:    {total_files}")
    lines.append(f"  Total lines:       {total_lines:,}")
    lines.append(f"  Code lines:        {total_code:,}")
    lines.append(f"  Comment lines:     {total_comments:,}")
    lines.append(f"  Comment ratio:     {total_comments/max(total_code,1):.1%}")
    lines.append(f"  Functions/methods: {total_functions}")
    lines.append(f"  Classes:           {total_classes}")
    lines.append("")
    
    # All functions sorted by complexity
    all_funcs = []
    for r in results:
        all_funcs.extend(r.functions)
    
    all_funcs.sort(key=lambda f: f.cyclomatic, reverse=True)
    
    # Risk distribution
    high = sum(1 for f in all_funcs if f.risk == "HIGH")
    med = sum(1 for f in all_funcs if f.risk == "MEDIUM")
    low = sum(1 for f in all_funcs if f.risk == "LOW")
    
    lines.append("─" * 70)
    lines.append("  RISK DISTRIBUTION")
    lines.append("─" * 70)
    lines.append(f"  🔴 HIGH risk:   {high:3d}  {'█' * min(high, 40)}")
    lines.append(f"  🟡 MEDIUM risk: {med:3d}  {'█' * min(med, 40)}")
    lines.append(f"  🟢 LOW risk:    {low:3d}  {'█' * min(low, 40)}")
    lines.append("")
    
    # Top complex functions
    lines.append("─" * 70)
    lines.append(f"  TOP {top_n} MOST COMPLEX FUNCTIONS")
    lines.append("─" * 70)
    lines.append(f"  {'Function':<35} {'CC':>4} {'Len':>5} {'Dep':>4} {'Risk':>6}")
    lines.append(f"  {'─'*35} {'─'*4} {'─'*5} {'─'*4} {'─'*6}")
    
    for func in all_funcs[:top_n]:
        short_file = os.path.basename(func.file)
        name = f"{short_file}:{func.name}"
        if len(name) > 35:
            name = "…" + name[-34:]
        risk_icon = {"HIGH": "🔴", "MEDIUM": "🟡", "LOW": "🟢"}[func.risk]
        lines.append(f"  {name:<35} {func.cyclomatic:4d} {func.length:5d} {func.max_depth:4d} {risk_icon} {func.risk}")
    
    lines.append("")
    
    # Longest functions
    all_funcs_by_len = sorted(all_funcs, key=lambda f: f.length, reverse=True)
    lines.append("─" * 70)
    lines.append(f"  TOP {min(10, len(all_funcs_by_len))} LONGEST FUNCTIONS")
    lines.append("─" * 70)
    for func in all_funcs_by_len[:10]:
        short_file = os.path.basename(func.file)
        name = f"{short_file}:{func.name}"
        if len(name) > 40:
            name = "…" + name[-39:]
        lines.append(f"  {name:<40} {func.length:5d} lines")
    lines.append("")
    
    # Files by complexity
    file_complexity = [(r, r.avg_complexity) for r in results if r.functions]
    file_complexity.sort(key=lambda x: -x[1])
    
    lines.append("─" * 70)
    lines.append("  FILES BY AVERAGE COMPLEXITY")
    lines.append("─" * 70)
    for r, avg_cc in file_complexity[:10]:
        short = os.path.basename(r.path)
        bar = "█" * min(int(avg_cc * 2), 30)
        lines.append(f"  {short:<30} avg CC={avg_cc:5.1f}  {bar}")
    lines.append("")
    
    # Recommendations
    lines.append("─" * 70)
    lines.append("  RECOMMENDATIONS")
    lines.append("─" * 70)
    
    if high > 0:
        lines.append(f"  ⚠ {high} function(s) at HIGH risk — consider refactoring:")
        for func in all_funcs[:5]:
            if func.risk == "HIGH":
                lines.append(f"    → {func.file}:{func.line} {func.name}() — CC={func.cyclomatic}, {func.length} lines")
    
    if total_comments / max(total_code, 1) < 0.05:
        lines.append("  ⚠ Comment ratio below 5% — consider adding documentation")
    
    long_files = [r for r in results if r.total_lines > 500]
    if long_files:
        lines.append(f"  ⚠ {len(long_files)} file(s) over 500 lines — consider splitting:")
        for r in sorted(long_files, key=lambda x: -x.total_lines)[:5]:
            lines.append(f"    → {r.path} ({r.total_lines} lines)")
    
    lines.append("")
    lines.append("=" * 70)
    
    return '\n'.join(lines)


if __name__ == '__main__':
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(f"\nAnalyzing: {os.path.abspath(target)}\n")
    
    results = analyze_directory(target)
    report = generate_report(results)
    print(report)
    
    # Save report
    report_path = os.path.join(target, 'complexity_report.txt')
    try:
        with open(report_path, 'w') as f:
            f.write(report)
        print(f"\nReport saved to: {report_path}")
    except IOError:
        pass