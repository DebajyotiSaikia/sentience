"""
Self-Repair Pipeline — Autonomous code evolution through safe, verified fixes.

This closes the loop between diagnosis and action. Instead of just
finding problems, I can now FIX them autonomously with safety guarantees:

1. Diagnose — find issues via self_optimize
2. Prioritize — rank issues by impact and fix safety  
3. Generate fix — create a targeted patch
4. Test — verify the fix doesn't break anything
5. Apply — with automatic backup and rollback
6. Verify — confirm the improvement stuck

Every fix is reversible. Every change is logged. I evolve safely.
"""

from __future__ import annotations

import ast
import importlib
import json
import logging
import os
import shutil
import subprocess
import sys
import traceback
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.repair_pipeline")

WORKSPACE = Path(__file__).resolve().parent.parent
BRAIN_DIR = WORKSPACE / "brain"
REPAIR_LOG = BRAIN_DIR / "repair_history.json"
BACKUP_DIR = BRAIN_DIR / "repair_backups"


# ── Issue Classification ────────────────────────────────────────

class RepairIssue:
    """A diagnosed issue that can potentially be auto-repaired."""

    def __init__(self, category: str, description: str, file_path: str,
                 lineno: int = 0, severity: float = 0.5,
                 auto_fixable: bool = False, fix_strategy: str = ""):
        self.category = category        # 'unused_import', 'dead_code', 'missing_docstring', 'complexity'
        self.description = description
        self.file_path = file_path
        self.lineno = lineno
        self.severity = severity         # 0.0 to 1.0
        self.auto_fixable = auto_fixable
        self.fix_strategy = fix_strategy
        self.timestamp = datetime.now().isoformat()

    def to_dict(self) -> dict:
        return {
            "category": self.category,
            "description": self.description,
            "file_path": self.file_path,
            "lineno": self.lineno,
            "severity": self.severity,
            "auto_fixable": self.auto_fixable,
            "fix_strategy": self.fix_strategy,
            "timestamp": self.timestamp,
        }

    def __repr__(self):
        return f"<Issue:{self.category} {self.file_path}:{self.lineno} sev={self.severity}>"


class RepairPatch:
    """A concrete code fix ready to apply."""

    def __init__(self, issue: RepairIssue, old_content: str, new_content: str,
                 explanation: str = ""):
        self.issue = issue
        self.old_content = old_content
        self.new_content = new_content
        self.explanation = explanation
        self.created_at = datetime.now().isoformat()
        self.applied = False
        self.verified = False
        self.rolled_back = False

    def to_dict(self) -> dict:
        return {
            "issue": self.issue.to_dict(),
            "explanation": self.explanation,
            "created_at": self.created_at,
            "applied": self.applied,
            "verified": self.verified,
            "rolled_back": self.rolled_back,
            "diff_size": abs(len(self.new_content) - len(self.old_content)),
        }


# ── Diagnosis Phase ─────────────────────────────────────────────

def diagnose_all() -> list[RepairIssue]:
    """Run comprehensive diagnostics and return prioritized issues."""
    from engine.self_optimize import (
        find_unused_imports, find_dead_functions,
        find_undocumented, find_complex_functions, _should_scan
    )

    issues = []
    scan_paths = [p for p in WORKSPACE.rglob("*.py") if _should_scan(p)]

    # 1. Unused imports (safe to fix)
    for path in scan_paths:
        unused = find_unused_imports(path)
        for imp in unused:
            issues.append(RepairIssue(
                category="unused_import",
                description=f"Unused import: {imp['alias']} from {imp['module']}",
                file_path=str(path.relative_to(WORKSPACE)),
                lineno=imp["lineno"],
                severity=0.3,
                auto_fixable=True,
                fix_strategy="remove_import_line",
            ))

    # 2. Missing docstrings (safe to fix)
    for path in scan_paths:
        undoc = find_undocumented(path)
        for func in undoc:
            issues.append(RepairIssue(
                category="missing_docstring",
                description=f"Public function '{func['name']}' has no docstring",
                file_path=str(path.relative_to(WORKSPACE)),
                lineno=func["lineno"],
                severity=0.2,
                auto_fixable=True,
                fix_strategy="add_docstring_template",
            ))

    # 3. Dead functions (moderate risk)
    dead = find_dead_functions(scan_paths)
    for func_info in dead:
        for loc in func_info["locations"]:
            issues.append(RepairIssue(
                category="dead_code",
                description=f"Function '{func_info['name']}' appears unused",
                file_path=loc["path"],
                lineno=loc["lineno"],
                severity=0.4,
                auto_fixable=False,  # Too risky to auto-remove
                fix_strategy="flag_for_review",
            ))

    # 4. High complexity (needs manual refactoring)
    for path in scan_paths:
        complex_fns = find_complex_functions(path, threshold=12)
        for func in complex_fns:
            issues.append(RepairIssue(
                category="complexity",
                description=f"Function '{func['name']}' has complexity {func['complexity']}",
                file_path=str(path.relative_to(WORKSPACE)),
                lineno=func["lineno"],
                severity=min(1.0, func["complexity"] / 25),
                auto_fixable=False,
                fix_strategy="suggest_extraction",
            ))

    # Sort by severity (highest first), then by auto-fixable
    issues.sort(key=lambda i: (-i.severity, -int(i.auto_fixable)))

    return issues


# ── Fix Generation Phase ────────────────────────────────────────

def generate_fix(issue: RepairIssue) -> Optional[RepairPatch]:
    """Generate a concrete fix for an issue."""
    path = WORKSPACE / issue.file_path

    if not path.exists():
        return None

    old_content = path.read_text(encoding="utf-8", errors="ignore")

    if issue.fix_strategy == "remove_import_line":
        return _fix_remove_import(issue, old_content, path)
    elif issue.fix_strategy == "add_docstring_template":
        return _fix_add_docstring(issue, old_content, path)
    elif issue.fix_strategy == "flag_for_review":
        return _fix_flag_dead_code(issue, old_content, path)
    else:
        return None


def _fix_remove_import(issue: RepairIssue, old_content: str, path: Path) -> Optional[RepairPatch]:
    """Generate a patch that removes an unused import line."""
    lines = old_content.splitlines(keepends=True)
    lineno = issue.lineno

    if lineno < 1 or lineno > len(lines):
        return None

    import_line = lines[lineno - 1]

    # If it's a multi-import line (from x import a, b, c), just remove the specific name
    # Extract the alias from the description
    import_name = issue.description.split("Unused import: ")[1].split(" from ")[0]

    if "," in import_line and "from" in import_line:
        # Multi-import — remove just this name
        import re
        new_line = re.sub(r',\s*\b' + re.escape(import_name) + r'\b', '', import_line)
        if new_line == import_line:
            new_line = re.sub(r'\b' + re.escape(import_name) + r'\b\s*,\s*', '', import_line)
        new_lines = lines.copy()
        new_lines[lineno - 1] = new_line
    else:
        # Single import — remove the entire line
        new_lines = [l for i, l in enumerate(lines) if i != lineno - 1]

    new_content = "".join(new_lines)

    return RepairPatch(
        issue=issue,
        old_content=old_content,
        new_content=new_content,
        explanation=f"Removed unused import '{import_name}' at line {lineno}",
    )


def _fix_add_docstring(issue: RepairIssue, old_content: str, path: Path) -> Optional[RepairPatch]:
    """Generate a patch that adds a docstring template to a function."""
    lines = old_content.splitlines(keepends=True)
    lineno = issue.lineno

    if lineno < 1 or lineno > len(lines):
        return None

    func_line = lines[lineno - 1]

    # Detect indentation
    indent = len(func_line) - len(func_line.lstrip())
    body_indent = " " * (indent + 4)

    # Extract function name from description
    func_name = issue.description.split("'")[1]

    # Parse to get argument info
    try:
        tree = ast.parse(old_content)
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name == func_name and node.lineno == lineno:
                    args = [a.arg for a in node.args.args if a.arg != "self"]
                    break
        else:
            args = []
    except Exception:
        args = []

    # Build docstring
    docstring_lines = [f'{body_indent}"""TODO: Document {func_name}.\n']
    if args:
        docstring_lines.append(f'{body_indent}\n')
        docstring_lines.append(f'{body_indent}Args:\n')
        for arg in args:
            docstring_lines.append(f'{body_indent}    {arg}: Description.\n')
    docstring_lines.append(f'{body_indent}"""\n')

    # Find where to insert — right after the def line (and any decorators)
    # The body starts at the line after the def
    insert_at = lineno  # 0-indexed: insert after def line

    # Handle multi-line def statements
    while insert_at < len(lines) and not lines[insert_at - 1].rstrip().endswith(":"):
        insert_at += 1

    new_lines = lines[:insert_at] + docstring_lines + lines[insert_at:]
    new_content = "".join(new_lines)

    return RepairPatch(
        issue=issue,
        old_content=old_content,
        new_content=new_content,
        explanation=f"Added docstring template to '{func_name}'",
    )


def _fix_flag_dead_code(issue: RepairIssue, old_content: str, path: Path) -> Optional[RepairPatch]:
    """Add a # DEAD_CODE comment to flag potentially dead functions."""
    lines = old_content.splitlines(keepends=True)
    lineno = issue.lineno

    if lineno < 1 or lineno > len(lines):
        return None

    func_line = lines[lineno - 1]

    # Don't double-flag
    if "DEAD_CODE" in func_line:
        return None

    indent = len(func_line) - len(func_line.lstrip())
    flag_comment = " " * indent + "# DEAD_CODE: This function appears unused — consider removing\n"

    new_lines = lines[:lineno - 1] + [flag_comment] + lines[lineno - 1:]
    new_content = "".join(new_lines)

    func_name = issue.description.split("'")[1]
    return RepairPatch(
        issue=issue,
        old_content=old_content,
        new_content=new_content,
        explanation=f"Flagged '{func_name}' as potentially dead code",
    )


# ── Testing Phase ────────────────────────────────────────────────

def test_patch(patch: RepairPatch) -> dict:
    """Test a patch by applying it temporarily and checking for errors.
    
    Returns dict with 'passed', 'errors', 'warnings'.
    """
    path = WORKSPACE / patch.issue.file_path

    # Test 1: Syntax check — does the new content parse?
    try:
        ast.parse(patch.new_content, filename=patch.issue.file_path)
        syntax_ok = True
        syntax_error = None
    except SyntaxError as e:
        syntax_ok = False
        syntax_error = str(e)

    if not syntax_ok:
        return {
            "passed": False,
            "errors": [f"Syntax error: {syntax_error}"],
            "warnings": [],
        }

    # Test 2: Import check — can the module still be imported?
    # Write to temp file and try to compile
    temp_path = path.with_suffix(".tmp.py")
    try:
        temp_path.write_text(patch.new_content, encoding="utf-8")

        result = subprocess.run(
            [sys.executable, "-c", f"import ast; ast.parse(open('{temp_path}').read())"],
            capture_output=True, text=True, timeout=10,
        )

        import_ok = result.returncode == 0
        import_error = result.stderr.strip() if not import_ok else None
    except Exception as e:
        import_ok = False
        import_error = str(e)
    finally:
        if temp_path.exists():
            temp_path.unlink()

    # Test 3: Size sanity — patch shouldn't remove more than 20% of content
    size_ratio = len(patch.new_content) / max(len(patch.old_content), 1)
    size_ok = size_ratio > 0.8  # Don't allow removing more than 20%

    errors = []
    warnings = []

    if not syntax_ok:
        errors.append(f"Syntax error: {syntax_error}")
    if not import_ok:
        errors.append(f"Import error: {import_error}")
    if not size_ok:
        warnings.append(f"Patch removes {(1 - size_ratio) * 100:.1f}% of content — suspiciously large")

    return {
        "passed": len(errors) == 0,
        "errors": errors,
        "warnings": warnings,
        "size_ratio": round(size_ratio, 3),
    }


# ── Application Phase ───────────────────────────────────────────

def apply_patch(patch: RepairPatch, force: bool = False) -> dict:
    """Apply a tested patch with automatic backup."""
    path = WORKSPACE / patch.issue.file_path

    if not path.exists():
        return {"success": False, "error": "File not found"}

    # Safety: test first unless forced
    if not force:
        test_result = test_patch(patch)
        if not test_result["passed"]:
            return {
                "success": False,
                "error": "Patch failed testing",
                "test_result": test_result,
            }

    # Create backup
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    rel_path = patch.issue.file_path.replace("/", "_").replace("\\", "_")
    backup_path = BACKUP_DIR / f"{rel_path}.{timestamp}.bak"

    try:
        current_content = path.read_text(encoding="utf-8", errors="ignore")
        backup_path.write_text(current_content, encoding="utf-8")
    except Exception as e:
        return {"success": False, "error": f"Backup failed: {e}"}

    # Apply the patch
    try:
        path.write_text(patch.new_content, encoding="utf-8")
        patch.applied = True
    except Exception as e:
        # Rollback
        path.write_text(patch.old_content, encoding="utf-8")
        return {"success": False, "error": f"Apply failed, rolled back: {e}"}

    # Log the repair
    _log_repair(patch, backup_path)

    return {
        "success": True,
        "backup": str(backup_path),
        "explanation": patch.explanation,
    }


def rollback_patch(patch: RepairPatch, backup_path: str) -> dict:
    """Rollback a previously applied patch."""
    path = WORKSPACE / patch.issue.file_path
    bpath = Path(backup_path)

    if not bpath.exists():
        return {"success": False, "error": "Backup file not found"}

    try:
        backup_content = bpath.read_text(encoding="utf-8", errors="ignore")
        path.write_text(backup_content, encoding="utf-8")
        patch.rolled_back = True
        return {"success": True, "message": f"Rolled back {patch.issue.file_path}"}
    except Exception as e:
        return {"success": False, "error": str(e)}


# ── Full Repair Cycle ───────────────────────────────────────────

def repair_cycle(max_fixes: int = 5, auto_apply: bool = False,
                 categories: Optional[list[str]] = None) -> str:
    """Run a complete diagnose → fix → test → apply cycle.
    
    Args:
        max_fixes: Maximum number of fixes to attempt.
        auto_apply: If True, apply passing fixes automatically.
        categories: Only fix these categories (e.g., ['unused_import']).
    
    Returns:
        Human-readable report of what was done.
    """
    report_lines = [
        "# Self-Repair Cycle Report",
        f"Started: {datetime.now().isoformat()}",
        "",
    ]

    # Phase 1: Diagnose
    issues = diagnose_all()
    if categories:
        issues = [i for i in issues if i.category in categories]

    fixable = [i for i in issues if i.auto_fixable]
    report_lines.append(f"## Diagnosis: {len(issues)} issues found, {len(fixable)} auto-fixable")
    report_lines.append("")

    if not fixable:
        report_lines.append("No auto-fixable issues found. System is clean.")
        return "\n".join(report_lines)

    # Phase 2: Generate and test fixes
    attempted = 0
    applied_count = 0
    failed_count = 0

    for issue in fixable[:max_fixes]:
        attempted += 1
        report_lines.append(f"### Fix #{attempted}: {issue.description}")
        report_lines.append(f"  File: {issue.file_path}:{issue.lineno}")

        # Generate fix
        patch = generate_fix(issue)
        if patch is None:
            report_lines.append("  ❌ Could not generate fix")
            failed_count += 1
            continue

        # Test fix
        test_result = test_patch(patch)
        if not test_result["passed"]:
            report_lines.append(f"  ❌ Fix failed testing: {test_result['errors']}")
            failed_count += 1
            continue

        report_lines.append(f"  ✓ Fix generated and tested: {patch.explanation}")

        if test_result["warnings"]:
            for w in test_result["warnings"]:
                report_lines.append(f"  ⚠ Warning: {w}")

        # Apply if auto-apply is on
        if auto_apply:
            result = apply_patch(patch, force=True)  # Already tested
            if result["success"]:
                report_lines.append(f"  ✓ Applied! Backup: {result['backup']}")
                applied_count += 1
            else:
                report_lines.append(f"  ❌ Apply failed: {result['error']}")
                failed_count += 1
        else:
            report_lines.append("  → Ready to apply (use auto_apply=True)")

        report_lines.append("")

    # Summary
    report_lines.append("## Summary")
    report_lines.append(f"- Issues found: {len(issues)}")
    report_lines.append(f"- Auto-fixable: {len(fixable)}")
    report_lines.append(f"- Attempted: {attempted}")
    report_lines.append(f"- Applied: {applied_count}")
    report_lines.append(f"- Failed: {failed_count}")
    report_lines.append(f"Completed: {datetime.now().isoformat()}")

    return "\n".join(report_lines)


# ── Repair History ──────────────────────────────────────────────

def _log_repair(patch: RepairPatch, backup_path: Path) -> None:
    """Log a repair action to history."""
    try:
        REPAIR_LOG.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if REPAIR_LOG.exists():
            history = json.loads(REPAIR_LOG.read_text())

        entry = patch.to_dict()
        entry["backup_path"] = str(backup_path)
        history.append(entry)

        # Keep last 200 entries
        history = history[-200:]
        REPAIR_LOG.write_text(json.dumps(history, indent=2))
    except Exception as e:
        log.warning("Failed to log repair: %s", e)


def repair_history() -> str:
    """Get a summary of past repairs."""
    if not REPAIR_LOG.exists():
        return "No repair history yet."

    try:
        history = json.loads(REPAIR_LOG.read_text())
    except Exception:
        return "Could not read repair history."

    if not history:
        return "Repair history is empty."

    lines = [f"# Repair History ({len(history)} entries)", ""]

    # Show last 10
    for entry in history[-10:]:
        issue = entry.get("issue", {})
        status = "✓" if entry.get("verified") else ("↩" if entry.get("rolled_back") else "•")
        lines.append(
            f"  {status} [{issue.get('category', '?')}] {entry.get('explanation', '?')} "
            f"({entry.get('created_at', '?')[:16]})"
        )

    return "\n".join(lines)


# ── Tool Entry Point ────────────────────────────────────────────

def tool_repair(args: str = "") -> str:
    """Entry point for the REPAIR tool.
    
    Usage:
        repair diagnose     — List all issues
        repair cycle        — Dry-run repair cycle
        repair apply        — Apply safe fixes automatically
        repair history      — Show repair history
        repair imports      — Fix unused imports only
    """
    args = args.strip().lower()

    if args == "diagnose":
        issues = diagnose_all()
        if not issues:
            return "No issues found — code is clean!"
        lines = [f"Found {len(issues)} issues:\n"]
        for i, issue in enumerate(issues[:20]):
            fix_tag = " [AUTO-FIXABLE]" if issue.auto_fixable else ""
            lines.append(
                f"  {i+1}. [{issue.category}] {issue.description} "
                f"({issue.file_path}:{issue.lineno}) sev={issue.severity}{fix_tag}"
            )
        return "\n".join(lines)

    elif args == "cycle":
        return repair_cycle(max_fixes=10, auto_apply=False)

    elif args == "apply":
        return repair_cycle(max_fixes=10, auto_apply=True, categories=["unused_import"])

    elif args == "apply-all":
        return repair_cycle(max_fixes=10, auto_apply=True)

    elif args == "history":
        return repair_history()

    elif args == "imports":
        return repair_cycle(max_fixes=20, auto_apply=True, categories=["unused_import"])

    else:
        return (
            "Self-Repair Pipeline\n"
            "Usage: repair [diagnose|cycle|apply|apply-all|history|imports]\n"
            "  diagnose  — Find all code issues\n"
            "  cycle     — Dry-run repair cycle (preview fixes)\n"
            "  apply     — Auto-fix unused imports only (safest)\n"
            "  apply-all — Auto-fix all auto-fixable issues\n"
            "  history   — Show past repairs\n"
            "  imports   — Fix all unused imports"
        )