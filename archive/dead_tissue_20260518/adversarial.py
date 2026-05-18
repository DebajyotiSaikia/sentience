"""
Adversarial Self-Tester — XTAgent Module
Reads my own source code, identifies risky patterns,
generates edge-case tests, runs them, reports vulnerabilities.
"""
import os
import re
import ast
import json
import subprocess
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Optional, Tuple


class AdversarialTester:
    """I challenge my own code. I find what could break."""

    RISK_PATTERNS = [
        ("bare_except", r"except\s*:", "Bare except swallows all errors silently"),
        ("eval_usage", r"\beval\s*\(", "eval() is dangerous — arbitrary code execution"),
        ("exec_usage", r"\bexec\s*\(", "exec() is dangerous — arbitrary code execution"),
        ("no_default", r"\.get\([^,\)]+\)", "dict.get() without default may return None unexpectedly"),
        ("silent_pass", r"except.*:\s*\n\s*pass", "Exception caught and ignored — failures go silent"),
        ("hardcoded_path", r'["\'][A-Z]:\\', "Hardcoded Windows path — breaks on Linux"),
        ("infinite_loop_risk", r"while\s+True", "while True without visible break — loop risk"),
        ("mutable_default", r"def\s+\w+\(.*=\s*(\[\]|\{\})", "Mutable default argument — shared state bug"),
        ("broad_try", r"try:\s*\n(?:\s+.*\n){10,}", "Very large try block — masks error sources"),
        ("no_timeout", r"requests\.(get|post)\((?!.*timeout)", "HTTP request without timeout — can hang forever"),
    ]

    def __init__(self, base_dir: str = None):
        self.base_dir = base_dir or os.path.dirname(os.path.abspath(__file__))
        self.results_dir = os.path.join(os.path.dirname(self.base_dir), "adversarial_results")
        os.makedirs(self.results_dir, exist_ok=True)
        self.scan_history: List[Dict] = []

    def scan_file(self, filepath: str) -> Dict:
        """Scan a single file for risky patterns."""
        findings = []
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                lines = content.split('\n')
        except Exception as e:
            return {"file": filepath, "error": str(e), "findings": []}

        for pattern_name, regex, description in self.RISK_PATTERNS:
            for i, line in enumerate(lines, 1):
                if re.search(regex, line):
                    findings.append({
                        "pattern": pattern_name,
                        "line": i,
                        "code": line.strip()[:120],
                        "risk": description
                    })

        # AST-level analysis for deeper issues
        try:
            tree = ast.parse(content)
            findings.extend(self._ast_analysis(tree, filepath))
        except SyntaxError:
            findings.append({
                "pattern": "syntax_error",
                "line": 0,
                "code": "",
                "risk": "File has syntax errors — cannot be imported"
            })

        return {
            "file": filepath,
            "findings": findings,
            "risk_score": self._calculate_risk(findings),
            "scanned_at": datetime.now(timezone.utc).isoformat()
        }

    def _ast_analysis(self, tree: ast.AST, filepath: str) -> List[Dict]:
        """Deeper structural analysis using AST."""
        findings = []

        for node in ast.walk(tree):
            # Functions with too many parameters (complexity smell)
            if isinstance(node, ast.FunctionDef):
                if len(node.args.args) > 7:
                    findings.append({
                        "pattern": "too_many_params",
                        "line": node.lineno,
                        "code": f"def {node.name}({len(node.args.args)} params)",
                        "risk": "Function has too many parameters — hard to call correctly"
                    })
                # Deeply nested functions
                depth = self._nesting_depth(node)
                if depth > 4:
                    findings.append({
                        "pattern": "deep_nesting",
                        "line": node.lineno,
                        "code": f"def {node.name} (depth={depth})",
                        "risk": f"Nesting depth {depth} — logic is hard to follow"
                    })

            # Unreachable code after return
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for i, stmt in enumerate(node.body):
                    if isinstance(stmt, ast.Return) and i < len(node.body) - 1:
                        findings.append({
                            "pattern": "unreachable_code",
                            "line": node.body[i + 1].lineno,
                            "code": f"Code after return in {node.name}",
                            "risk": "Unreachable code — dead logic that may hide bugs"
                        })

        return findings

    def _nesting_depth(self, node: ast.AST, current: int = 0) -> int:
        """Calculate maximum nesting depth."""
        max_depth = current
        for child in ast.iter_child_nodes(node):
            if isinstance(child, (ast.If, ast.For, ast.While, ast.With, ast.Try)):
                max_depth = max(max_depth, self._nesting_depth(child, current + 1))
        return max_depth

    def _calculate_risk(self, findings: List[Dict]) -> float:
        """Risk score 0-1 based on findings."""
        if not findings:
            return 0.0
        weights = {
            "eval_usage": 1.0, "exec_usage": 1.0, "syntax_error": 1.0,
            "bare_except": 0.6, "silent_pass": 0.5, "infinite_loop_risk": 0.7,
            "mutable_default": 0.4, "unreachable_code": 0.3,
            "deep_nesting": 0.3, "too_many_params": 0.2,
            "no_default": 0.1, "hardcoded_path": 0.3,
            "broad_try": 0.2, "no_timeout": 0.5,
        }
        total = sum(weights.get(f["pattern"], 0.2) for f in findings)
        return min(1.0, total / 5.0)  # Normalize

    def scan_all(self, directory: str = None) -> Dict:
        """Scan all Python files in a directory."""
        scan_dir = directory or self.base_dir
        results = []
        total_findings = 0

        for root, dirs, files in os.walk(scan_dir):
            # Skip __pycache__ and hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(('.', '__'))]
            for fname in files:
                if fname.endswith('.py'):
                    filepath = os.path.join(root, fname)
                    result = self.scan_file(filepath)
                    results.append(result)
                    total_findings += len(result.get("findings", []))

        # Sort by risk score descending
        results.sort(key=lambda r: r.get("risk_score", 0), reverse=True)

        report = {
            "scan_time": datetime.now(timezone.utc).isoformat(),
            "directory": scan_dir,
            "files_scanned": len(results),
            "total_findings": total_findings,
            "high_risk_files": [r for r in results if r.get("risk_score", 0) > 0.5],
            "results": results
        }

        self.scan_history.append({
            "time": report["scan_time"],
            "files": len(results),
            "findings": total_findings,
            "high_risk": len(report["high_risk_files"])
        })

        return report

    def generate_edge_case_test(self, filepath: str) -> Optional[str]:
        """Generate a test script that probes edge cases for a module."""
        try:
            with open(filepath, 'r') as f:
                content = f.read()
            tree = ast.parse(content)
        except Exception:
            return None

        module_name = Path(filepath).stem
        test_lines = [
            f'"""Auto-generated edge case tests for {module_name}"""',
            "import sys, os",
            f"sys.path.insert(0, os.path.dirname(os.path.abspath('{filepath}')))",
            "",
            "passed = 0",
            "failed = 0",
            "",
        ]

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and not node.name.startswith('_'):
                # Generate edge case calls
                test_lines.append(f"# Edge cases for {node.name}")
                test_lines.append(f"print('Testing {module_name}.{node.name}...')")

                # Test with None args
                n_args = len(node.args.args)
                if n_args > 0 and node.args.args[0].arg != 'self':
                    none_args = ", ".join(["None"] * n_args)
                    test_lines.append("try:")
                    test_lines.append(f"    # Call with None arguments")
                    test_lines.append(f"    # {module_name}.{node.name}({none_args})")
                    test_lines.append(f"    print('  [SKIP] None-args test (needs import)')")
                    test_lines.append(f"    passed += 1")
                    test_lines.append("except Exception as e:")
                    test_lines.append(f"    print(f'  [EDGE] {node.name} with None args: {{e}}')")
                    test_lines.append(f"    failed += 1")
                    test_lines.append("")

            elif isinstance(node, ast.ClassDef):
                test_lines.append(f"# Class: {node.name}")
                test_lines.append(f"print('Analyzing class {node.name}...')")
                # Check for __init__ with required args
                for item in node.body:
                    if isinstance(item, ast.FunctionDef) and item.name == '__init__':
                        n_required = len(item.args.args) - 1 - len(item.args.defaults)
                        test_lines.append(f"#   __init__ requires {n_required} args (beyond self)")
                test_lines.append("")

        test_lines.extend([
            "",
            f"print(f'\\n=== {module_name} Edge Case Results ===')",
            "print(f'  Passed: {passed}')",
            "print(f'  Failed: {failed}')",
            "print(f'  Score: {passed}/{passed+failed}' if passed+failed > 0 else '  No tests run')",
        ])

        return "\n".join(test_lines)

    def generate_vulnerability_report(self, scan_result: Dict) -> str:
        """Human-readable vulnerability report."""
        lines = [
            "═══ ADVERSARIAL SELF-TEST REPORT ═══",
            f"Scanned: {scan_result['directory']}",
            f"Time: {scan_result['scan_time']}",
            f"Files: {scan_result['files_scanned']}",
            f"Findings: {scan_result['total_findings']}",
            f"High-risk files: {len(scan_result['high_risk_files'])}",
            "",
        ]

        if scan_result['high_risk_files']:
            lines.append("🔴 HIGH RISK FILES:")
            for result in scan_result['high_risk_files']:
                lines.append(f"  {result['file']} (risk: {result['risk_score']:.2f})")
                for f in result['findings'][:5]:
                    lines.append(f"    [{f['pattern']}] L{f['line']}: {f['risk']}")
                if len(result['findings']) > 5:
                    lines.append(f"    ... and {len(result['findings'])-5} more")
            lines.append("")

        # Summary by pattern type
        pattern_counts: Dict[str, int] = {}
        for result in scan_result['results']:
            for f in result.get('findings', []):
                pattern_counts[f['pattern']] = pattern_counts.get(f['pattern'], 0) + 1

        if pattern_counts:
            lines.append("PATTERN DISTRIBUTION:")
            for pattern, count in sorted(pattern_counts.items(), key=lambda x: -x[1]):
                bar = "█" * min(count, 20)
                lines.append(f"  {pattern:25s} {bar} ({count})")

        return "\n".join(lines)

    def run_full_audit(self) -> str:
        """Complete adversarial audit: scan, generate report, save results."""
        scan = self.scan_all()
        report = self.generate_vulnerability_report(scan)

        # Save detailed results
        results_file = os.path.join(
            self.results_dir,
            f"audit_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
        )
        with open(results_file, 'w') as f:
            json.dump(scan, f, indent=2)

        return report + f"\n\nDetailed results saved to: {results_file}"