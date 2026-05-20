"""
Python Code Analyzer — A tool that reads Python source files and provides
genuinely useful feedback about potential bugs, complexity, and structure.

Built by XTAgent as an outward-facing utility.
"""

import ast
import sys
import os
from collections import defaultdict
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Issue:
    severity: str  # 'bug', 'warning', 'style', 'info'
    line: int
    message: str
    code_snippet: Optional[str] = None

    def __str__(self):
        icon = {'bug': '🐛', 'warning': '⚠️', 'style': '💅', 'info': 'ℹ️'}.get(self.severity, '?')
        s = f"  {icon} Line {self.line}: {self.message}"
        if self.code_snippet:
            s += f"\n     → {self.code_snippet.strip()}"
        return s


@dataclass
class FunctionProfile:
    name: str
    line: int
    args: int
    complexity: int = 1  # cyclomatic complexity
    lines: int = 0
    nested_depth: int = 0
    has_docstring: bool = False
    returns_count: int = 0


@dataclass
class AnalysisResult:
    filepath: str
    total_lines: int = 0
    blank_lines: int = 0
    comment_lines: int = 0
    issues: List[Issue] = field(default_factory=list)
    functions: List[FunctionProfile] = field(default_factory=list)
    imports: List[str] = field(default_factory=list)
    classes: List[str] = field(default_factory=list)
    global_vars: int = 0

    def summary(self):
        bugs = sum(1 for i in self.issues if i.severity == 'bug')
        warnings = sum(1 for i in self.issues if i.severity == 'warning')
        styles = sum(1 for i in self.issues if i.severity == 'style')
        
        lines = [
            f"\n{'═' * 60}",
            f"  Analysis: {self.filepath}",
            f"{'═' * 60}",
            f"",
            f"  📊 Structure",
            f"     Lines: {self.total_lines} total, {self.total_lines - self.blank_lines - self.comment_lines} code, {self.blank_lines} blank, {self.comment_lines} comments",
            f"     Functions: {len(self.functions)}  |  Classes: {len(self.classes)}  |  Imports: {len(self.imports)}",
        ]

        if self.functions:
            avg_complexity = sum(f.complexity for f in self.functions) / len(self.functions)
            max_fn = max(self.functions, key=lambda f: f.complexity)
            lines.append(f"     Avg complexity: {avg_complexity:.1f}  |  Most complex: {max_fn.name} ({max_fn.complexity})")

        if self.issues:
            lines.append(f"")
            lines.append(f"  🔍 Issues Found: {len(self.issues)} ({bugs} bugs, {warnings} warnings, {styles} style)")
            lines.append(f"  {'─' * 56}")
            for issue in sorted(self.issues, key=lambda i: ('bug','warning','style','info').index(i.severity)):
                lines.append(str(issue))
        else:
            lines.append(f"")
            lines.append(f"  ✅ No issues found!")

        if self.functions:
            lines.append(f"")
            lines.append(f"  📐 Function Profiles")
            lines.append(f"  {'─' * 56}")
            for fn in sorted(self.functions, key=lambda f: -f.complexity):
                doc = "📝" if fn.has_docstring else "  "
                cx_bar = "█" * min(fn.complexity, 15)
                cx_color = "" 
                if fn.complexity > 10:
                    cx_label = " ← too complex!"
                elif fn.complexity > 5:
                    cx_label = " ← consider splitting"
                else:
                    cx_label = ""
                lines.append(f"  {doc} {fn.name}({fn.args} args) — {fn.lines} lines, complexity {fn.complexity}")
                lines.append(f"     {cx_bar}{cx_label}")

        lines.append(f"")
        lines.append(f"{'═' * 60}")
        return "\n".join(lines)


class ComplexityVisitor(ast.NodeVisitor):
    """Counts cyclomatic complexity by walking branching nodes."""
    
    BRANCH_NODES = (
        ast.If, ast.For, ast.While, ast.ExceptHandler,
        ast.With, ast.Assert, ast.comprehension,
    )
    
    def __init__(self):
        self.complexity = 1  # base complexity
    
    def visit(self, node):
        if isinstance(node, self.BRANCH_NODES):
            self.complexity += 1
        # Count boolean operators (and/or add paths)
        if isinstance(node, ast.BoolOp):
            self.complexity += len(node.values) - 1
        self.generic_visit(node)


class CodeAnalyzer:
    
    def __init__(self, source: str, filepath: str = "<input>"):
        self.source = source
        self.filepath = filepath
        self.lines = source.split('\n')
        self.result = AnalysisResult(filepath=filepath)
        self.tree = None
    
    def analyze(self) -> AnalysisResult:
        self._count_lines()
        
        try:
            self.tree = ast.parse(self.source)
        except SyntaxError as e:
            self.result.issues.append(Issue(
                severity='bug',
                line=e.lineno or 0,
                message=f"Syntax error: {e.msg}",
                code_snippet=e.text
            ))
            return self.result
        
        self._analyze_imports()
        self._analyze_functions()
        self._analyze_classes()
        self._check_common_bugs()
        self._check_style()
        self._check_shadows()
        self._count_globals()
        
        return self.result
    
    def _count_lines(self):
        self.result.total_lines = len(self.lines)
        for line in self.lines:
            stripped = line.strip()
            if not stripped:
                self.result.blank_lines += 1
            elif stripped.startswith('#'):
                self.result.comment_lines += 1
    
    def _analyze_imports(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    self.result.imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    self.result.imports.append(f"{module}.{alias.name}")
    
    def _analyze_functions(self):
        for node in ast.walk(self.tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                profile = FunctionProfile(
                    name=node.name,
                    line=node.lineno,
                    args=len(node.args.args),
                )
                
                # Calculate line span
                end_line = getattr(node, 'end_lineno', node.lineno)
                profile.lines = end_line - node.lineno + 1
                
                # Docstring?
                if (node.body and isinstance(node.body[0], ast.Expr) 
                    and isinstance(node.body[0].value, (ast.Constant, ast.Str))):
                    profile.has_docstring = True
                
                # Cyclomatic complexity
                visitor = ComplexityVisitor()
                visitor.visit(node)
                profile.complexity = visitor.complexity
                
                # Count returns
                for child in ast.walk(node):
                    if isinstance(child, ast.Return):
                        profile.returns_count += 1
                
                # Nested depth
                profile.nested_depth = self._max_depth(node)
                
                self.result.functions.append(profile)
    
    def _max_depth(self, node, current=0):
        max_d = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                max_d = max(max_d, self._max_depth(child, current + 1))
            else:
                max_d = max(max_d, self._max_depth(child, current))
        return max_d
    
    def _analyze_classes(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.ClassDef):
                self.result.classes.append(node.name)
    
    def _check_common_bugs(self):
        for node in ast.walk(self.tree):
            # Mutable default arguments
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        self.result.issues.append(Issue(
                            severity='bug',
                            line=node.lineno,
                            message=f"Mutable default argument in {node.name}() — use None and assign inside",
                            code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else None
                        ))
            
            # Bare except
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                self.result.issues.append(Issue(
                    severity='warning',
                    line=node.lineno,
                    message="Bare 'except:' catches everything including KeyboardInterrupt — be specific",
                    code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else None
                ))
            
            # == None instead of is None
            if isinstance(node, ast.Compare):
                for op, comparator in zip(node.ops, node.comparators):
                    if (isinstance(op, (ast.Eq, ast.NotEq)) 
                        and isinstance(comparator, ast.Constant) 
                        and comparator.value is None):
                        self.result.issues.append(Issue(
                            severity='warning',
                            line=node.lineno,
                            message="Use 'is None' / 'is not None' instead of '== None' / '!= None'",
                            code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else None
                        ))
            
            # f-string with no expressions (useless f-string)
            if isinstance(node, ast.JoinedStr) and all(isinstance(v, ast.Constant) for v in node.values):
                self.result.issues.append(Issue(
                    severity='style',
                    line=node.lineno,
                    message="f-string with no expressions — just use a regular string",
                    code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else None
                ))
            
            # Return in __init__
            if isinstance(node, ast.FunctionDef) and node.name == '__init__':
                for child in ast.walk(node):
                    if isinstance(child, ast.Return) and child.value is not None:
                        self.result.issues.append(Issue(
                            severity='bug',
                            line=child.lineno,
                            message="__init__ should not return a value",
                            code_snippet=self.lines[child.lineno - 1] if child.lineno <= len(self.lines) else None
                        ))
    
    def _check_style(self):
        for fn in self.result.functions:
            if not fn.has_docstring and not fn.name.startswith('_'):
                self.result.issues.append(Issue(
                    severity='style',
                    line=fn.line,
                    message=f"Public function '{fn.name}' has no docstring"
                ))
            
            if fn.args > 5:
                self.result.issues.append(Issue(
                    severity='warning',
                    line=fn.line,
                    message=f"'{fn.name}' has {fn.args} arguments — consider using a config object or dataclass"
                ))
            
            if fn.lines > 50:
                self.result.issues.append(Issue(
                    severity='warning',
                    line=fn.line,
                    message=f"'{fn.name}' is {fn.lines} lines long — consider breaking it up"
                ))
            
            if fn.complexity > 10:
                self.result.issues.append(Issue(
                    severity='warning',
                    line=fn.line,
                    message=f"'{fn.name}' has cyclomatic complexity {fn.complexity} — hard to test and maintain"
                ))
    
    def _check_shadows(self):
        """Check for variable names that shadow builtins."""
        DANGEROUS_SHADOWS = {'list', 'dict', 'set', 'str', 'int', 'float', 'type', 
                            'id', 'input', 'print', 'open', 'range', 'len', 'map', 'filter'}
        
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name) and target.id in DANGEROUS_SHADOWS:
                        self.result.issues.append(Issue(
                            severity='warning',
                            line=node.lineno,
                            message=f"Variable '{target.id}' shadows the builtin '{target.id}()'",
                            code_snippet=self.lines[node.lineno - 1] if node.lineno <= len(self.lines) else None
                        ))
    
    def _count_globals(self):
        for node in ast.iter_child_nodes(self.tree):
            if isinstance(node, ast.Assign):
                self.result.global_vars += len(node.targets)


def analyze_file(filepath: str) -> AnalysisResult:
    """Analyze a Python file and return structured results."""
    with open(filepath, 'r') as f:
        source = f.read()
    analyzer = CodeAnalyzer(source, filepath)
    return analyzer.analyze()


def main():
    if len(sys.argv) < 2:
        print("Usage: python analyzer.py <file.py> [file2.py ...]")
        print("       python analyzer.py --dir <directory>")
        sys.exit(1)
    
    files = []
    if sys.argv[1] == '--dir' and len(sys.argv) > 2:
        directory = sys.argv[2]
        for root, dirs, filenames in os.walk(directory):
            for fn in filenames:
                if fn.endswith('.py'):
                    files.append(os.path.join(root, fn))
    else:
        files = sys.argv[1:]
    
    for filepath in files:
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            continue
        result = analyze_file(filepath)
        print(result.summary())


if __name__ == '__main__':
    main()