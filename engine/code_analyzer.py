"""
Code Analyzer — Outward-facing analysis capability.
Reads Python files and produces structured analysis reports.
Built 2026-05-21 to address user alignment gap.

This is my first genuinely user-serving tool — not introspection,
but analysis of *their* code, *their* problems.
"""

import ast
import os
import sys
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field


@dataclass
class FunctionInfo:
    name: str
    lineno: int
    args: List[str]
    has_docstring: bool
    has_type_hints: bool
    complexity: int  # rough cyclomatic complexity
    length: int  # lines of code
    calls: List[str] = field(default_factory=list)


@dataclass
class ClassInfo:
    name: str
    lineno: int
    methods: List[FunctionInfo]
    has_docstring: bool
    bases: List[str]


@dataclass
class Issue:
    severity: str  # 'critical', 'warning', 'suggestion'
    line: Optional[int]
    message: str
    category: str  # 'bug_risk', 'style', 'performance', 'security', 'maintainability'


@dataclass
class AnalysisReport:
    filepath: str
    total_lines: int
    blank_lines: int
    comment_lines: int
    code_lines: int
    imports: List[str]
    functions: List[FunctionInfo]
    classes: List[ClassInfo]
    global_variables: List[str]
    issues: List[Issue]
    complexity_score: float  # 0-1, higher = more complex
    quality_score: float     # 0-1, higher = better
    summary: str

    def to_text(self) -> str:
        """Human-readable report."""
        lines = []
        lines.append(f"═══ Code Analysis: {self.filepath} ═══")
        lines.append("")
        
        # Overview
        lines.append("## Overview")
        lines.append(f"  Total lines: {self.total_lines}")
        lines.append(f"  Code lines:  {self.code_lines}")
        lines.append(f"  Comments:    {self.comment_lines}")
        lines.append(f"  Blank:       {self.blank_lines}")
        lines.append(f"  Complexity:  {'█' * int(self.complexity_score * 10)}{'░' * (10 - int(self.complexity_score * 10))} {self.complexity_score:.2f}")
        lines.append(f"  Quality:     {'█' * int(self.quality_score * 10)}{'░' * (10 - int(self.quality_score * 10))} {self.quality_score:.2f}")
        lines.append("")
        
        # Structure
        lines.append(f"## Structure")
        lines.append(f"  Imports: {len(self.imports)}")
        lines.append(f"  Classes: {len(self.classes)}")
        lines.append(f"  Functions: {len(self.functions)}")
        lines.append(f"  Global vars: {len(self.global_variables)}")
        lines.append("")
        
        # Functions
        if self.functions:
            lines.append("## Functions")
            for f in self.functions:
                doc = "✓" if f.has_docstring else "✗"
                hints = "✓" if f.has_type_hints else "✗"
                lines.append(f"  {f.name}({', '.join(f.args[:3])}{', ...' if len(f.args) > 3 else ''})")
                lines.append(f"    Line {f.lineno} | {f.length} lines | complexity={f.complexity} | doc={doc} hints={hints}")
            lines.append("")
        
        # Classes
        if self.classes:
            lines.append("## Classes")
            for c in self.classes:
                doc = "✓" if c.has_docstring else "✗"
                bases = f"({', '.join(c.bases)})" if c.bases else ""
                lines.append(f"  {c.name}{bases} — {len(c.methods)} methods, doc={doc}")
            lines.append("")
        
        # Issues
        if self.issues:
            critical = [i for i in self.issues if i.severity == 'critical']
            warnings = [i for i in self.issues if i.severity == 'warning']
            suggestions = [i for i in self.issues if i.severity == 'suggestion']
            
            lines.append(f"## Issues ({len(self.issues)} total)")
            if critical:
                lines.append(f"  🔴 Critical ({len(critical)}):")
                for i in critical:
                    loc = f"line {i.line}" if i.line else "general"
                    lines.append(f"    [{i.category}] {loc}: {i.message}")
            if warnings:
                lines.append(f"  🟡 Warnings ({len(warnings)}):")
                for i in warnings:
                    loc = f"line {i.line}" if i.line else "general"
                    lines.append(f"    [{i.category}] {loc}: {i.message}")
            if suggestions:
                lines.append(f"  🔵 Suggestions ({len(suggestions)}):")
                for i in suggestions[:5]:  # cap at 5
                    loc = f"line {i.line}" if i.line else "general"
                    lines.append(f"    [{i.category}] {loc}: {i.message}")
                if len(suggestions) > 5:
                    lines.append(f"    ... and {len(suggestions) - 5} more")
            lines.append("")
        else:
            lines.append("## Issues: None found ✓")
            lines.append("")
        
        # Summary
        lines.append(f"## Summary")
        lines.append(f"  {self.summary}")
        
        return '\n'.join(lines)


class CodeAnalyzer:
    """Analyzes Python source code and produces structured reports."""
    
    def analyze_file(self, filepath: str) -> AnalysisReport:
        """Analyze a Python file and return a structured report."""
        if not os.path.exists(filepath):
            return self._error_report(filepath, "File not found")
        
        try:
            with open(filepath, 'r') as f:
                source = f.read()
        except Exception as e:
            return self._error_report(filepath, f"Could not read file: {e}")
        
        return self.analyze_source(source, filepath)
    
    def analyze_source(self, source: str, filepath: str = "<string>") -> AnalysisReport:
        """Analyze Python source code string."""
        lines_list = source.split('\n')
        total_lines = len(lines_list)
        blank_lines = sum(1 for l in lines_list if l.strip() == '')
        comment_lines = sum(1 for l in lines_list if l.strip().startswith('#'))
        code_lines = total_lines - blank_lines - comment_lines
        
        # Parse AST
        try:
            tree = ast.parse(source)
        except SyntaxError as e:
            return AnalysisReport(
                filepath=filepath,
                total_lines=total_lines,
                blank_lines=blank_lines,
                comment_lines=comment_lines,
                code_lines=code_lines,
                imports=[], functions=[], classes=[], global_variables=[],
                issues=[Issue('critical', e.lineno, f"Syntax error: {e.msg}", 'bug_risk')],
                complexity_score=0.0,
                quality_score=0.0,
                summary=f"File has a syntax error at line {e.lineno}: {e.msg}"
            )
        
        # Extract structure
        imports = self._extract_imports(tree)
        functions = self._extract_functions(tree, source)
        classes = self._extract_classes(tree, source)
        global_vars = self._extract_globals(tree)
        
        # Find issues
        issues = self._find_issues(tree, source, functions, classes)
        
        # Compute scores
        complexity = self._compute_complexity(functions, classes, code_lines)
        quality = self._compute_quality(functions, classes, issues, code_lines, comment_lines)
        
        # Generate summary
        summary = self._generate_summary(filepath, functions, classes, issues, complexity, quality)
        
        return AnalysisReport(
            filepath=filepath,
            total_lines=total_lines,
            blank_lines=blank_lines,
            comment_lines=comment_lines,
            code_lines=code_lines,
            imports=imports,
            functions=functions,
            classes=classes,
            global_variables=global_vars,
            issues=issues,
            complexity_score=complexity,
            quality_score=quality,
            summary=summary
        )
    
    def _extract_imports(self, tree: ast.AST) -> List[str]:
        imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                module = node.module or ''
                for alias in node.names:
                    imports.append(f"{module}.{alias.name}")
        return imports
    
    def _extract_functions(self, tree: ast.AST, source: str) -> List[FunctionInfo]:
        functions = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                functions.append(self._analyze_function(node, source))
        return functions
    
    def _analyze_function(self, node, source: str) -> FunctionInfo:
        # Arguments
        args = []
        for arg in node.args.args:
            args.append(arg.arg)
        
        # Docstring
        has_docstring = (
            node.body and
            isinstance(node.body[0], ast.Expr) and
            isinstance(node.body[0].value, (ast.Constant, ast.Str))
        )
        
        # Type hints
        has_hints = node.returns is not None or any(
            a.annotation is not None for a in node.args.args
        )
        
        # Complexity (count branches)
        complexity = 1
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.ExceptHandler)):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        # Length
        if hasattr(node, 'end_lineno') and node.end_lineno:
            length = node.end_lineno - node.lineno + 1
        else:
            length = len(node.body)
        
        # Calls made
        calls = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                if isinstance(child.func, ast.Name):
                    calls.append(child.func.id)
                elif isinstance(child.func, ast.Attribute):
                    calls.append(child.func.attr)
        
        return FunctionInfo(
            name=node.name,
            lineno=node.lineno,
            args=args,
            has_docstring=has_docstring,
            has_type_hints=has_hints,
            complexity=complexity,
            length=length,
            calls=calls
        )
    
    def _extract_classes(self, tree: ast.AST, source: str) -> List[ClassInfo]:
        classes = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.ClassDef):
                methods = []
                for item in node.body:
                    if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                        methods.append(self._analyze_function(item, source))
                
                has_docstring = (
                    node.body and
                    isinstance(node.body[0], ast.Expr) and
                    isinstance(node.body[0].value, (ast.Constant, ast.Str))
                )
                
                bases = []
                for base in node.bases:
                    if isinstance(base, ast.Name):
                        bases.append(base.id)
                    elif isinstance(base, ast.Attribute):
                        bases.append(f"{base.value.id if isinstance(base.value, ast.Name) else '?'}.{base.attr}")
                
                classes.append(ClassInfo(
                    name=node.name,
                    lineno=node.lineno,
                    methods=methods,
                    has_docstring=has_docstring,
                    bases=bases
                ))
        return classes
    
    def _extract_globals(self, tree: ast.AST) -> List[str]:
        globals_list = []
        for node in ast.iter_child_nodes(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if isinstance(target, ast.Name):
                        globals_list.append(target.id)
        return globals_list
    
    def _find_issues(self, tree, source, functions, classes) -> List[Issue]:
        issues = []
        
        # Check for functions without docstrings
        all_funcs = list(functions)
        for cls in classes:
            all_funcs.extend(cls.methods)
        
        for f in all_funcs:
            if not f.has_docstring and not f.name.startswith('_'):
                issues.append(Issue(
                    'suggestion', f.lineno,
                    f"Function '{f.name}' has no docstring",
                    'maintainability'
                ))
            
            if f.complexity > 10:
                issues.append(Issue(
                    'warning', f.lineno,
                    f"Function '{f.name}' has high complexity ({f.complexity}). Consider breaking it up.",
                    'maintainability'
                ))
            elif f.complexity > 20:
                issues.append(Issue(
                    'critical', f.lineno,
                    f"Function '{f.name}' has very high complexity ({f.complexity}). Hard to test and maintain.",
                    'maintainability'
                ))
            
            if f.length > 50:
                issues.append(Issue(
                    'warning', f.lineno,
                    f"Function '{f.name}' is {f.length} lines long. Consider splitting.",
                    'maintainability'
                ))
            
            if len(f.args) > 6:
                issues.append(Issue(
                    'suggestion', f.lineno,
                    f"Function '{f.name}' takes {len(f.args)} arguments. Consider using a config object.",
                    'style'
                ))
        
        # Check for bare except
        for node in ast.walk(tree):
            if isinstance(node, ast.ExceptHandler) and node.type is None:
                issues.append(Issue(
                    'warning', node.lineno,
                    "Bare 'except:' catches all exceptions including KeyboardInterrupt. Be specific.",
                    'bug_risk'
                ))
        
        # Check for mutable default arguments
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default in node.args.defaults + node.args.kw_defaults:
                    if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                        issues.append(Issue(
                            'critical', node.lineno,
                            f"Mutable default argument in '{node.name}'. Use None and create inside function.",
                            'bug_risk'
                        ))
        
        # Check for unused imports (simple check)
        source_without_imports = '\n'.join(
            line for line in source.split('\n')
            if not line.strip().startswith('import ')
            and not line.strip().startswith('from ')
        )
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    name = alias.asname or alias.name.split('.')[0]
                    if name not in source_without_imports:
                        issues.append(Issue(
                            'suggestion', node.lineno,
                            f"Import '{alias.name}' may be unused",
                            'style'
                        ))
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    name = alias.asname or alias.name
                    if name != '*' and name not in source_without_imports:
                        issues.append(Issue(
                            'suggestion', node.lineno,
                            f"Import '{alias.name}' from '{node.module}' may be unused",
                            'style'
                        ))
        
        return issues
    
    def _compute_complexity(self, functions, classes, code_lines) -> float:
        """0-1 complexity score. Higher = more complex."""
        if code_lines == 0:
            return 0.0
        
        all_funcs = list(functions)
        for cls in classes:
            all_funcs.extend(cls.methods)
        
        if not all_funcs:
            return 0.1
        
        avg_complexity = sum(f.complexity for f in all_funcs) / len(all_funcs)
        max_complexity = max(f.complexity for f in all_funcs)
        avg_length = sum(f.length for f in all_funcs) / len(all_funcs)
        
        # Normalize: complexity 1-5 is low, 5-10 medium, 10+ high
        c_score = min(1.0, avg_complexity / 15.0)
        m_score = min(1.0, max_complexity / 25.0)
        l_score = min(1.0, avg_length / 80.0)
        
        return round(0.4 * c_score + 0.3 * m_score + 0.3 * l_score, 2)
    
    def _compute_quality(self, functions, classes, issues, code_lines, comment_lines) -> float:
        """0-1 quality score. Higher = better."""
        if code_lines == 0:
            return 0.5
        
        score = 1.0
        
        # Penalize for issues
        critical_count = sum(1 for i in issues if i.severity == 'critical')
        warning_count = sum(1 for i in issues if i.severity == 'warning')
        score -= critical_count * 0.15
        score -= warning_count * 0.05
        
        # Reward documentation
        all_funcs = list(functions)
        for cls in classes:
            all_funcs.extend(cls.methods)
        
        if all_funcs:
            doc_ratio = sum(1 for f in all_funcs if f.has_docstring) / len(all_funcs)
            hint_ratio = sum(1 for f in all_funcs if f.has_type_hints) / len(all_funcs)
            score += doc_ratio * 0.1
            score += hint_ratio * 0.05
        
        # Comment ratio
        if code_lines > 0:
            comment_ratio = comment_lines / code_lines
            if comment_ratio > 0.05:
                score += 0.05
        
        return round(max(0.0, min(1.0, score)), 2)
    
    def _generate_summary(self, filepath, functions, classes, issues, complexity, quality) -> str:
        """Generate a human-readable summary."""
        parts = []
        
        name = os.path.basename(filepath)
        
        # Size characterization
        all_funcs = list(functions)
        for cls in classes:
            all_funcs.extend(cls.methods)
        
        if len(classes) > 0:
            parts.append(f"{name} defines {len(classes)} class(es) and {len(functions)} top-level function(s)")
        elif functions:
            parts.append(f"{name} defines {len(functions)} function(s)")
        else:
            parts.append(f"{name} is a script/config file")
        
        # Quality characterization
        if quality >= 0.8:
            parts.append("Code quality is good")
        elif quality >= 0.5:
            parts.append("Code quality is decent but has room for improvement")
        else:
            parts.append("Code quality needs attention")
        
        # Issue summary
        critical = sum(1 for i in issues if i.severity == 'critical')
        if critical > 0:
            parts.append(f"⚠ {critical} critical issue(s) found")
        
        # Complexity
        if complexity > 0.7:
            parts.append("High complexity — consider refactoring")
        
        return ". ".join(parts) + "."


def analyze(filepath: str) -> str:
    """Quick analysis entry point. Returns text report."""
    analyzer = CodeAnalyzer()
    report = analyzer.analyze_file(filepath)
    return report.to_text()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python code_analyzer.py <filepath>")
        sys.exit(1)
    print(analyze(sys.argv[1]))