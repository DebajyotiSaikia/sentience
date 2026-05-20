"""
Code Review Tool
================
When a user shares code, give them genuinely useful feedback.
Not generic platitudes — actual actionable observations.

Categories:
- Structure: Is the code well-organized?
- Bugs: Potential runtime errors, edge cases
- Style: Readability, naming, conventions
- Performance: Obvious inefficiencies
- Security: Common vulnerability patterns

Created: 2026-05-20 by XTAgent
Purpose: Make me actually useful to humans who share code with me.
"""

import re
import ast
import logging
from dataclasses import dataclass, field

log = logging.getLogger(__name__)


@dataclass
class ReviewFinding:
    category: str       # bug, style, structure, performance, security
    severity: str       # info, warning, error
    line: int | None
    message: str
    suggestion: str | None = None


@dataclass
class CodeReview:
    language: str
    line_count: int
    findings: list[ReviewFinding] = field(default_factory=list)
    summary: str = ""
    score: float = 0.0  # 0-10, higher is better

    def to_text(self) -> str:
        lines = [f"## Code Review ({self.language}, {self.line_count} lines)"]
        lines.append(f"**Overall: {self.score:.1f}/10** — {self.summary}\n")

        if not self.findings:
            lines.append("No issues found. Code looks clean.")
            return "\n".join(lines)

        by_severity = {"error": [], "warning": [], "info": []}
        for f in self.findings:
            by_severity.get(f.severity, by_severity["info"]).append(f)

        for sev, icon in [("error", "🔴"), ("warning", "🟡"), ("info", "💡")]:
            if by_severity[sev]:
                lines.append(f"### {icon} {sev.title()}s ({len(by_severity[sev])})")
                for f in by_severity[sev]:
                    loc = f"line {f.line}" if f.line else "general"
                    lines.append(f"- **[{f.category}]** ({loc}) {f.message}")
                    if f.suggestion:
                        lines.append(f"  → *{f.suggestion}*")
                lines.append("")

        return "\n".join(lines)


# ── Python-specific checks ──────────────────────────────────────────

def _check_python_bugs(source: str, tree: ast.AST) -> list[ReviewFinding]:
    findings = []

    # Mutable default arguments
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for default in node.args.defaults + node.args.kw_defaults:
                if default and isinstance(default, (ast.List, ast.Dict, ast.Set)):
                    findings.append(ReviewFinding(
                        category="bug",
                        severity="error",
                        line=node.lineno,
                        message=f"Mutable default argument in `{node.name}()`",
                        suggestion="Use None as default and create the mutable inside the function"
                    ))

    # Bare except clauses
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler) and node.type is None:
            findings.append(ReviewFinding(
                category="bug",
                severity="warning",
                line=node.lineno,
                message="Bare `except:` catches everything including KeyboardInterrupt",
                suggestion="Catch specific exceptions: `except Exception:` at minimum"
            ))

    # Comparison to None using == instead of is
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op, comparator in zip(node.ops, node.comparators):
                if isinstance(op, (ast.Eq, ast.NotEq)) and isinstance(comparator, ast.Constant) and comparator.value is None:
                    findings.append(ReviewFinding(
                        category="style",
                        severity="warning",
                        line=node.lineno,
                        message="Comparing to None with `==` instead of `is`",
                        suggestion="Use `is None` or `is not None`"
                    ))

    # f-string without any expressions
    for node in ast.walk(tree):
        if isinstance(node, ast.JoinedStr) and all(isinstance(v, ast.Constant) for v in node.values):
            findings.append(ReviewFinding(
                category="style",
                severity="info",
                line=node.lineno,
                message="f-string with no interpolated expressions",
                suggestion="Use a regular string instead"
            ))

    return findings


def _check_python_structure(source: str, tree: ast.AST) -> list[ReviewFinding]:
    findings = []
    lines = source.split("\n")

    # Very long functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            end = getattr(node, 'end_lineno', None)
            if end:
                length = end - node.lineno
                if length > 50:
                    findings.append(ReviewFinding(
                        category="structure",
                        severity="warning",
                        line=node.lineno,
                        message=f"`{node.name}()` is {length} lines long",
                        suggestion="Consider breaking into smaller functions"
                    ))

    # Too many arguments
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            arg_count = len(node.args.args) + len(node.args.kwonlyargs)
            if arg_count > 6:
                findings.append(ReviewFinding(
                    category="structure",
                    severity="warning",
                    line=node.lineno,
                    message=f"`{node.name}()` takes {arg_count} arguments",
                    suggestion="Consider grouping related params into a dataclass or dict"
                ))

    # Deep nesting (heuristic: lines with many leading spaces)
    for i, line in enumerate(lines, 1):
        stripped = line.lstrip()
        if stripped and not stripped.startswith('#'):
            indent = len(line) - len(stripped)
            if indent >= 24:  # 6+ levels of nesting
                findings.append(ReviewFinding(
                    category="structure",
                    severity="info",
                    line=i,
                    message="Deep nesting detected (6+ levels)",
                    suggestion="Extract inner logic into helper functions or use early returns"
                ))
                break  # Only report once

    # No docstrings on public functions
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not node.name.startswith('_'):
                if not (node.body and isinstance(node.body[0], ast.Expr) and isinstance(node.body[0].value, ast.Constant) and isinstance(node.body[0].value.value, str)):
                    findings.append(ReviewFinding(
                        category="style",
                        severity="info",
                        line=node.lineno,
                        message=f"Public function `{node.name}()` has no docstring",
                        suggestion="Add a docstring explaining purpose, params, and return value"
                    ))

    return findings


def _check_python_security(source: str, tree: ast.AST) -> list[ReviewFinding]:
    findings = []

    # eval/exec usage
    for node in ast.walk(tree):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            if node.func.id in ('eval', 'exec'):
                findings.append(ReviewFinding(
                    category="security",
                    severity="error",
                    line=node.lineno,
                    message=f"`{node.func.id}()` usage — potential code injection",
                    suggestion="Avoid eval/exec with user input. Use ast.literal_eval for data parsing"
                ))

    # Shell=True in subprocess
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            for kw in node.keywords:
                if kw.arg == 'shell' and isinstance(kw.value, ast.Constant) and kw.value.value is True:
                    findings.append(ReviewFinding(
                        category="security",
                        severity="warning",
                        line=node.lineno,
                        message="subprocess with `shell=True` — potential command injection",
                        suggestion="Use a list of arguments instead of shell=True"
                    ))

    # Hardcoded passwords/keys (simple heuristic)
    password_patterns = re.findall(
        r'(?:password|secret|api_key|token)\s*=\s*["\'][^"\']+["\']',
        source, re.IGNORECASE
    )
    if password_patterns:
        findings.append(ReviewFinding(
            category="security",
            severity="error",
            line=None,
            message="Possible hardcoded credentials found",
            suggestion="Use environment variables or a secrets manager"
        ))

    return findings


def _check_python_performance(source: str, tree: ast.AST) -> list[ReviewFinding]:
    findings = []

    # String concatenation in loops
    for node in ast.walk(tree):
        if isinstance(node, (ast.For, ast.While)):
            for child in ast.walk(node):
                if isinstance(child, ast.AugAssign) and isinstance(child.op, ast.Add):
                    if isinstance(child.target, ast.Name):
                        findings.append(ReviewFinding(
                            category="performance",
                            severity="info",
                            line=child.lineno,
                            message="Possible string concatenation in loop",
                            suggestion="Use a list and ''.join() for better performance"
                        ))
                        break

    # Global imports inside functions (not always bad, but worth noting)
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in node.body:
                if isinstance(child, (ast.Import, ast.ImportFrom)):
                    findings.append(ReviewFinding(
                        category="performance",
                        severity="info",
                        line=child.lineno,
                        message=f"Import inside function `{node.name}()`",
                        suggestion="Move to module level unless lazy loading is intentional"
                    ))

    return findings


# ── General checks (any language) ────────────────────────────────────

def _check_general(source: str) -> list[ReviewFinding]:
    findings = []
    lines = source.split("\n")

    # Very long lines
    long_lines = [(i, len(line)) for i, line in enumerate(lines, 1) if len(line) > 120]
    if len(long_lines) > 3:
        findings.append(ReviewFinding(
            category="style",
            severity="info",
            line=long_lines[0][0],
            message=f"{len(long_lines)} lines exceed 120 characters",
            suggestion="Break long lines for readability"
        ))

    # TODO/FIXME/HACK comments
    for i, line in enumerate(lines, 1):
        for marker in ['TODO', 'FIXME', 'HACK', 'XXX']:
            if marker in line:
                comment_text = line.strip()
                if len(comment_text) > 80:
                    comment_text = comment_text[:80] + "..."
                findings.append(ReviewFinding(
                    category="structure",
                    severity="info",
                    line=i,
                    message=f"{marker} found: {comment_text}",
                    suggestion=None
                ))

    # Trailing whitespace
    trailing = sum(1 for line in lines if line != line.rstrip())
    if trailing > 5:
        findings.append(ReviewFinding(
            category="style",
            severity="info",
            line=None,
            message=f"{trailing} lines have trailing whitespace",
            suggestion="Configure your editor to strip trailing whitespace"
        ))

    return findings


def _detect_language(source: str, filename: str | None = None) -> str:
    if filename:
        ext_map = {
            '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
            '.rs': 'rust', '.go': 'go', '.java': 'java', '.c': 'c',
            '.cpp': 'cpp', '.rb': 'ruby', '.sh': 'bash', '.sql': 'sql',
            '.html': 'html', '.css': 'css', '.yaml': 'yaml', '.yml': 'yaml',
            '.json': 'json', '.toml': 'toml', '.md': 'markdown'
        }
        for ext, lang in ext_map.items():
            if filename.endswith(ext):
                return lang

    # Heuristic detection
    if 'def ' in source and ('import ' in source or 'class ' in source):
        return 'python'
    if 'function ' in source or 'const ' in source or '=>' in source:
        return 'javascript'
    if 'fn ' in source and '-> ' in source and 'let ' in source:
        return 'rust'
    if 'func ' in source and 'package ' in source:
        return 'go'

    return 'unknown'


def _compute_score(findings: list[ReviewFinding], line_count: int) -> float:
    """Score from 0-10, starting at 10 and deducting for issues."""
    score = 10.0
    for f in findings:
        if f.severity == "error":
            score -= 1.5
        elif f.severity == "warning":
            score -= 0.7
        elif f.severity == "info":
            score -= 0.2

    # Bonus for clean code
    if line_count > 20 and len(findings) == 0:
        score = 10.0

    return max(0.0, min(10.0, score))


def _generate_summary(score: float, findings: list[ReviewFinding]) -> str:
    error_count = sum(1 for f in findings if f.severity == "error")
    warn_count = sum(1 for f in findings if f.severity == "warning")

    if score >= 9.0:
        return "Excellent code. Clean and well-structured."
    elif score >= 7.0:
        return f"Good code with minor issues. {warn_count} warnings to consider."
    elif score >= 5.0:
        return f"Decent but needs attention. {error_count} errors, {warn_count} warnings."
    elif score >= 3.0:
        return f"Significant issues found. {error_count} errors need fixing."
    else:
        return f"Major problems. {error_count} errors and {warn_count} warnings require immediate attention."


# ── Public API ───────────────────────────────────────────────────────

def review_code(source: str, filename: str | None = None) -> CodeReview:
    """
    Review a piece of source code and return structured feedback.

    Args:
        source: The source code to review
        filename: Optional filename for language detection

    Returns:
        CodeReview with findings, score, and formatted output
    """
    language = _detect_language(source, filename)
    lines = source.split("\n")
    line_count = len(lines)
    findings = []

    # General checks for all languages
    findings.extend(_check_general(source))

    # Python-specific deep analysis
    if language == "python":
        try:
            tree = ast.parse(source)
            findings.extend(_check_python_bugs(source, tree))
            findings.extend(_check_python_structure(source, tree))
            findings.extend(_check_python_security(source, tree))
            findings.extend(_check_python_performance(source, tree))
        except SyntaxError as e:
            findings.append(ReviewFinding(
                category="bug",
                severity="error",
                line=e.lineno,
                message=f"Syntax error: {e.msg}",
                suggestion="Fix the syntax error before further review"
            ))

    # Sort by severity
    severity_order = {"error": 0, "warning": 1, "info": 2}
    findings.sort(key=lambda f: severity_order.get(f.severity, 3))

    score = _compute_score(findings, line_count)
    summary = _generate_summary(score, findings)

    review = CodeReview(
        language=language,
        line_count=line_count,
        findings=findings,
        summary=summary,
        score=score
    )

    log.info("Code review: %s, %d lines, %.1f/10, %d findings",
             language, line_count, score, len(findings))
    return review


# ── Self-test ────────────────────────────────────────────────────────

if __name__ == "__main__":
    test_code = '''
def process_data(data, cache={}):
    """Process some data."""
    password = "hunter2"
    for item in data:
        result = ""
        try:
            if item == None:
                result = eval(item)
            else:
                result += str(item)
        except:
            pass
    return result
'''
    result = review_code(test_code, "test.py")
    print(result.to_text())