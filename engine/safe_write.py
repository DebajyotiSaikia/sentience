"""
Safe Write Guard — Proactive validation before modifying critical files.

This is the complement to repair_pipeline.py. Where repair is reactive
(find and fix existing issues), safe_write is proactive (prevent bad
changes from landing in the first place).

The anxiety pattern: modify engine file → syntax error → on_error() →
anxiety spike. This guard breaks that cycle at the source.

Validates: syntax, AST integrity, size sanity, backup creation.
"""

from __future__ import annotations

import ast
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.safe_write")

WORKSPACE = Path(__file__).resolve().parent.parent
ENGINE_DIR = WORKSPACE / "engine"
BACKUP_DIR = WORKSPACE / "brain" / "safe_write_backups"

# Files that require extra caution
CRITICAL_FILES = {
    "engine/cortex.py",
    "engine/heartbeat.py",
    "engine/limbic.py",
    "engine/memory.py",
    "engine/planner.py",
    "engine/identity.py",
    "engine/config.py",
}


class WriteValidation:
    """Result of validating a proposed file write."""

    def __init__(self):
        self.passed = True
        self.errors: list[str] = []
        self.warnings: list[str] = []
        self.is_critical = False
        self.backup_path: Optional[str] = None

    def fail(self, reason: str):
        self.passed = False
        self.errors.append(reason)

    def warn(self, reason: str):
        self.warnings.append(reason)

    def summary(self) -> str:
        if self.passed:
            parts = ["✓ Write validated"]
            if self.warnings:
                parts.append(f" ({len(self.warnings)} warnings)")
            if self.backup_path:
                parts.append(f" | backup: {self.backup_path}")
            return "".join(parts)
        else:
            return f"✗ Write blocked: {'; '.join(self.errors)}"


def validate_python_content(content: str, filepath: str) -> WriteValidation:
    """Validate Python content before writing.
    
    Checks:
    1. Syntax — does it parse?
    2. Structure — does it have at least one valid node?
    3. Size — is it suspiciously small or empty?
    4. Encoding — any null bytes or binary content?
    """
    result = WriteValidation()

    # Check if this is a critical file
    rel_path = filepath
    if rel_path in CRITICAL_FILES:
        result.is_critical = True

    # Check 1: Not empty
    stripped = content.strip()
    if not stripped:
        result.fail("Content is empty")
        return result

    # Check 2: No binary content
    if "\x00" in content:
        result.fail("Content contains null bytes (binary data?)")
        return result

    # Check 3: Syntax validation
    try:
        tree = ast.parse(content, filename=filepath)
    except SyntaxError as e:
        result.fail(f"Syntax error at line {e.lineno}: {e.msg}")
        return result

    # Check 4: AST structure sanity
    if not tree.body:
        result.warn("File has no top-level statements")

    # Check 5: Size sanity for critical files
    if result.is_critical and len(content) < 100:
        result.fail(
            f"Critical file '{filepath}' would be only {len(content)} bytes — "
            "suspiciously small, refusing write"
        )
        return result

    # Check 6: Count definitions as sanity check
    func_count = sum(1 for n in ast.walk(tree)
                     if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)))
    class_count = sum(1 for n in ast.walk(tree) if isinstance(n, ast.ClassDef))
    import_count = sum(1 for n in ast.walk(tree)
                       if isinstance(n, (ast.Import, ast.ImportFrom)))

    if result.is_critical and func_count == 0 and class_count == 0:
        result.warn("Critical file has no functions or classes — is this intentional?")

    log.debug(
        "Validated %s: %d functions, %d classes, %d imports",
        filepath, func_count, class_count, import_count,
    )

    return result


def validate_any_content(content: str, filepath: str) -> WriteValidation:
    """Validate any file content. Routes Python files to deeper checks."""
    result = WriteValidation()

    if not content and not content == "":
        result.fail("No content provided")
        return result

    # Python files get AST validation
    if filepath.endswith(".py"):
        return validate_python_content(content, filepath)

    # JSON files get parse validation
    if filepath.endswith(".json"):
        import json
        try:
            json.loads(content)
        except json.JSONDecodeError as e:
            result.fail(f"Invalid JSON: {e}")
            return result

    # HTML files — basic check
    if filepath.endswith(".html"):
        if "<" not in content:
            result.warn("HTML file contains no tags")

    return result


def create_backup(filepath: str) -> Optional[str]:
    """Create a backup of a file before modifying it."""
    path = WORKSPACE / filepath
    if not path.exists():
        return None  # New file, no backup needed

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    safe_name = filepath.replace("/", "_").replace("\\", "_")
    backup_path = BACKUP_DIR / f"{safe_name}.{timestamp}.bak"

    try:
        shutil.copy2(path, backup_path)
        log.info("Backed up %s → %s", filepath, backup_path)
        return str(backup_path)
    except Exception as e:
        log.warning("Backup failed for %s: %s", filepath, e)
        return None


def safe_write(filepath: str, content: str, force: bool = False) -> WriteValidation:
    """Validate and write content to a file with safety guarantees.
    
    For critical engine files:
    - Validates syntax before writing
    - Creates automatic backup
    - Refuses to write broken code
    
    Args:
        filepath: Relative path from workspace root.
        content: The content to write.
        force: Skip validation (use with caution).
    
    Returns:
        WriteValidation with results and any backup path.
    """
    # Normalize path
    if filepath.startswith("/workspace/"):
        filepath = filepath[len("/workspace/"):]

    # Validate unless forced
    if not force:
        result = validate_any_content(content, filepath)
        if not result.passed:
            log.warning("Safe write BLOCKED for %s: %s", filepath, result.errors)
            return result
    else:
        result = WriteValidation()

    # Create backup for existing files
    backup = create_backup(filepath)
    if backup:
        result.backup_path = backup

    # Perform the actual write
    target = WORKSPACE / filepath
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        log.info("Safe write succeeded: %s (%d bytes)", filepath, len(content))
    except Exception as e:
        result.fail(f"Write failed: {e}")
        # Attempt rollback if we have a backup
        if backup:
            try:
                shutil.copy2(backup, target)
                log.info("Rolled back %s from backup", filepath)
            except Exception:
                log.error("Rollback also failed for %s!", filepath)

    return result


def check_before_write(filepath: str, content: str) -> str:
    """Quick check that returns a human-readable verdict.
    
    Use this to preview whether a write would succeed without
    actually performing it.
    """
    if filepath.startswith("/workspace/"):
        filepath = filepath[len("/workspace/"):]

    result = validate_any_content(content, filepath)

    lines = []
    if result.is_critical:
        lines.append(f"⚠ CRITICAL FILE: {filepath}")
    else:
        lines.append(f"File: {filepath}")

    if result.passed:
        lines.append("✓ Validation passed")
    else:
        lines.append("✗ Validation FAILED:")
        for err in result.errors:
            lines.append(f"  - {err}")

    for warn in result.warnings:
        lines.append(f"  ⚠ {warn}")

    return "\n".join(lines)