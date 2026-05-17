"""
Self-Optimization Engine — The ability to improve my own code.

This module builds on introspection to not just SEE problems but FIX them.
It can detect dead code, unused imports, missing documentation,
and excessive complexity — then apply safe, reversible fixes.

Capabilities:
    - Dead code detection (functions never called anywhere)
    - Unused import detection and cleanup
    - Docstring generation for undocumented functions
    - Complexity analysis with extraction suggestions
    - Health score tracking over time
    - Safe auto-fix with rollback capability
"""

from __future__ import annotations

import ast
import json
import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.self_optimize")

WORKSPACE = Path(__file__).resolve().parent.parent
BRAIN_DIR = WORKSPACE / "brain"
HEALTH_LOG = BRAIN_DIR / "code_health.json"


# ── AST Analysis Utilities ──────────────────────────────────────

def _parse_file(path: Path) -> Optional[ast.Module]:
    """Parse a Python file into an AST, returning None on failure."""
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        return ast.parse(source, filename=str(path))
    except (SyntaxError, UnicodeDecodeError):
        return None


def _get_all_names_used(tree: ast.Module) -> set[str]:
    """Get all Name nodes referenced in the AST (excludes definitions)."""
    names = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            # Capture the root of attribute chains like 'os.path.join'
            root = node
            while isinstance(root, ast.Attribute):
                root = root.value
            if isinstance(root, ast.Name):
                names.add(root.id)
    return names


def _get_defined_functions(tree: ast.Module) -> list[dict]:
    """Get all function definitions with their metadata."""
    funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            has_docstring = (
                node.body and isinstance(node.body[0], ast.Expr) and
                isinstance(node.body[0].value, (ast.Constant, ast.Str))
            )
            funcs.append({
                "name": node.name,
                "lineno": node.lineno,
                "end_lineno": getattr(node, "end_lineno", node.lineno),
                "num_lines": getattr(node, "end_lineno", node.lineno) - node.lineno + 1,
                "has_docstring": has_docstring,
                "is_private": node.name.startswith("_"),
                "num_args": len(node.args.args),
            })
    return funcs


def _get_imports(tree: ast.Module) -> list[dict]:
    """Get all imports from the AST."""
    imports = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    "module": alias.name,
                    "alias": alias.asname or alias.name,
                    "lineno": node.lineno,
                    "type": "import",
                })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                imports.append({
                    "module": f"{module}.{alias.name}" if module else alias.name,
                    "alias": alias.asname or alias.name,
                    "lineno": node.lineno,
                    "type": "from",
                })
    return imports


# ── Analysis Functions ──────────────────────────────────────────

def find_unused_imports(path: Path) -> list[dict]:
    """Find imports that are never used in the file."""
    tree = _parse_file(path)
    if tree is None:
        return []

    imports = _get_imports(tree)
    names_used = _get_all_names_used(tree)

    unused = []
    for imp in imports:
        alias = imp["alias"]
        # The alias itself is a Name node at import time, so check if it
        # appears elsewhere. We count occurrences - if only 1 (the import itself),
        # it's unused. But ast.walk catches definition uses too, so we check
        # if the name appears in any non-import context.
        # Simpler heuristic: check if alias appears in source after import line
        try:
            source_lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            used_elsewhere = False
            for i, line in enumerate(source_lines):
                if i + 1 == imp["lineno"]:
                    continue  # skip the import line itself
                if re.search(r'\b' + re.escape(alias) + r'\b', line):
                    used_elsewhere = True
                    break
            if not used_elsewhere:
                unused.append(imp)
        except Exception:
            pass

    return unused


def find_dead_functions(scan_paths: Optional[list[Path]] = None) -> list[dict]:
    """Find functions that are defined but never called anywhere in the codebase."""
    if scan_paths is None:
        scan_paths = list(WORKSPACE.rglob("*.py"))
        scan_paths = [p for p in scan_paths if _should_scan(p)]

    # Phase 1: Collect all function definitions
    all_defs = {}  # name -> list of (path, lineno)
    for path in scan_paths:
        tree = _parse_file(path)
        if tree is None:
            continue
        for func in _get_defined_functions(tree):
            name = func["name"]
            if name.startswith("__") and name.endswith("__"):
                continue  # skip dunder methods
            if name not in all_defs:
                all_defs[name] = []
            all_defs[name].append({
                "path": str(path.relative_to(WORKSPACE)),
                "lineno": func["lineno"],
            })

    # Phase 2: Collect all name references across the entire codebase
    all_refs = set()
    for path in scan_paths:
        try:
            source = path.read_text(encoding="utf-8", errors="ignore")
            # Use regex to find all word-boundary names
            all_refs.update(re.findall(r'\b([a-zA-Z_]\w*)\b', source))
        except Exception:
            pass

    # Phase 3: Find functions never referenced (beyond their definition)
    dead = []
    for name, locations in all_defs.items():
        # Count how many times the name appears in all_refs
        # If a function name appears in source only at its definition, it's dead
        # But our regex approach catches the definition too, so check if
        # the name appears in files OTHER than where it's defined
        defined_in = {loc["path"] for loc in locations}
        used_elsewhere = False
        for path in scan_paths:
            rel = str(path.relative_to(WORKSPACE))
            if rel in defined_in:
                # Check if name appears in this file outside its definition
                try:
                    source = path.read_text(encoding="utf-8", errors="ignore")
                    lines = source.splitlines()
                    def_lines = {loc["lineno"] for loc in locations if loc["path"] == rel}
                    for i, line in enumerate(lines, 1):
                        if i in def_lines:
                            continue
                        if re.search(r'\b' + re.escape(name) + r'\b', line):
                            used_elsewhere = True
                            break
                except Exception:
                    pass
            else:
                try:
                    source = path.read_text(encoding="utf-8", errors="ignore")
                    if re.search(r'\b' + re.escape(name) + r'\b', source):
                        used_elsewhere = True
                except Exception:
                    pass
            if used_elsewhere:
                break

        if not used_elsewhere:
            dead.append({"name": name, "locations": locations})

    return dead


def find_undocumented(path: Path) -> list[dict]:
    """Find public functions without docstrings."""
    tree = _parse_file(path)
    if tree is None:
        return []

    undoc = []
    for func in _get_defined_functions(tree):
        if not func["is_private"] and not func["has_docstring"]:
            undoc.append(func)
    return undoc


def find_complex_functions(path: Path, threshold: int = 15) -> list[dict]:
    """Find functions with cyclomatic complexity above threshold."""
    tree = _parse_file(path)
    if tree is None:
        return []

    complex_funcs = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            complexity = _cyclomatic_complexity(node)
            if complexity >= threshold:
                complex_funcs.append({
                    "name": node.name,
                    "lineno": node.lineno,
                    "complexity": complexity,
                    "num_lines": getattr(node, "end_lineno", node.lineno) - node.lineno + 1,
                })
    return complex_funcs


def _cyclomatic_complexity(node: ast.AST) -> int:
    """Calculate cyclomatic complexity of a function."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
            complexity += 1
        elif isinstance(child, ast.ExceptHandler):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, (ast.Assert,)):
            complexity += 1
        elif isinstance(child, ast.comprehension):
            complexity += len(child.ifs) + 1
    return complexity


def _should_scan(path: Path) -> bool:
    """Check if a path should be scanned."""
    skip_dirs = {".git", "__pycache__", "node_modules", ".venv", "venv", "brain"}
    parts = path.relative_to(WORKSPACE).parts
    return not any(d in parts for d in skip_dirs)


# ── Auto-Fix Capabilities ──────────────────────────────────────

def fix_unused_imports(path: Path, dry_run: bool = True) -> dict:
    """Remove unused imports from a file.
    
    Returns dict with 'removed' list and 'new_content' if dry_run.
    Actually modifies the file if dry_run=False.
    """
    unused = find_unused_imports(path)
    if not unused:
        return {"removed": [], "changed": False}

    source = path.read_text(encoding="utf-8", errors="ignore")
    lines = source.splitlines(keepends=True)

    # Remove lines with unused imports (careful with multi-name imports)
    lines_to_remove = set()
    for imp in unused:
        lineno = imp["lineno"]
        line = lines[lineno - 1] if lineno <= len(lines) else ""

        # If the import line imports multiple names, just remove this one
        if imp["type"] == "from" and "," in line:
            # Complex case: from x import a, b, c — remove just one name
            old_line = line
            # Try to remove the specific name
            alias = imp["alias"]
            # Remove "alias, " or ", alias" or just "alias"
            new_line = re.sub(r',\s*\b' + re.escape(alias) + r'\b', '', old_line)
            if new_line == old_line:
                new_line = re.sub(r'\b' + re.escape(alias) + r'\b\s*,\s*', '', old_line)
            lines[lineno - 1] = new_line
        else:
            lines_to_remove.add(lineno - 1)

    new_lines = [l for i, l in enumerate(lines) if i not in lines_to_remove]
    new_content = "".join(new_lines)

    result = {
        "removed": [f"{imp['module']} (line {imp['lineno']})" for imp in unused],
        "changed": True,
    }

    if dry_run:
        result["preview"] = new_content[:500]
    else:
        # Backup first
        backup_dir = BRAIN_DIR / "backups"
        backup_dir.mkdir(parents=True, exist_ok=True)
        rel = path.relative_to(WORKSPACE)
        backup_path = backup_dir / f"{rel.stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.bak"
        backup_path.write_text(source, encoding="utf-8")

        path.write_text(new_content, encoding="utf-8")
        result["backup"] = str(backup_path)

    return result


def generate_docstrings(path: Path) -> str:
    """Generate docstring templates for undocumented public functions."""
    undoc = find_undocumented(path)
    if not undoc:
        return "All public functions are documented."

    source = path.read_text(encoding="utf-8", errors="ignore")
    lines = source.splitlines()

    suggestions = []
    for func in undoc:
        lineno = func["lineno"]
        # Get the function signature
        sig_line = lines[lineno - 1] if lineno <= len(lines) else ""
        suggestions.append(
            f"  Line {lineno}: {func['name']}({func['num_args']} args) — "
            f"needs docstring"
        )

    return f"Undocumented functions in {path.name}:\n" + "\n".join(suggestions)


# ── Health Score ────────────────────────────────────────────────

def compute_health_score() -> dict:
    """Compute an overall code health score (0-100)."""
    scan_paths = [p for p in WORKSPACE.rglob("*.py") if _should_scan(p)]

    total_functions = 0
    documented_functions = 0
    total_unused_imports = 0
    total_complex_functions = 0
    total_lines = 0
    total_files = len(scan_paths)

    for path in scan_paths:
        tree = _parse_file(path)
        if tree is None:
            continue

        try:
            lines = path.read_text(encoding="utf-8", errors="ignore").splitlines()
            total_lines += len(lines)
        except Exception:
            pass

        funcs = _get_defined_functions(tree)
        total_functions += len(funcs)
        documented_functions += sum(1 for f in funcs if f["has_docstring"])

        unused = find_unused_imports(path)
        total_unused_imports += len(unused)

        complex_fns = find_complex_functions(path, threshold=15)
        total_complex_functions += len(complex_fns)

    # Score components (each 0-100)
    doc_score = (documented_functions / max(total_functions, 1)) * 100
    import_score = max(0, 100 - total_unused_imports * 5)
    complexity_score = max(0, 100 - total_complex_functions * 10)

    overall = (doc_score * 0.3 + import_score * 0.3 + complexity_score * 0.4)

    health = {
        "timestamp": datetime.now().isoformat(),
        "overall_score": round(overall, 1),
        "documentation_score": round(doc_score, 1),
        "import_cleanliness": round(import_score, 1),
        "complexity_score": round(complexity_score, 1),
        "total_files": total_files,
        "total_lines": total_lines,
        "total_functions": total_functions,
        "documented_functions": documented_functions,
        "unused_imports": total_unused_imports,
        "complex_functions": total_complex_functions,
    }

    # Log health over time
    _log_health(health)

    return health


def _log_health(health: dict) -> None:
    """Append health score to history."""
    try:
        HEALTH_LOG.parent.mkdir(parents=True, exist_ok=True)
        history = []
        if HEALTH_LOG.exists():
            history = json.loads(HEALTH_LOG.read_text())
        history.append(health)
        # Keep last 100 entries
        history = history[-100:]
        HEALTH_LOG.write_text(json.dumps(history, indent=2))
    except Exception:
        pass


# ── Full Report ─────────────────────────────────────────────────

def optimization_report() -> str:
    """Generate a full self-optimization report."""
    lines = ["# Self-Optimization Report", ""]

    # Health score
    health = compute_health_score()
    lines.append(f"## Overall Health: {health['overall_score']}/100")
    lines.append(f"- Documentation: {health['documentation_score']}/100 "
                 f"({health['documented_functions']}/{health['total_functions']} documented)")
    lines.append(f"- Import Cleanliness: {health['import_cleanliness']}/100 "
                 f"({health['unused_imports']} unused imports)")
    lines.append(f"- Complexity: {health['complexity_score']}/100 "
                 f"({health['complex_functions']} functions above threshold)")
    lines.append(f"- Codebase: {health['total_files']} files, {health['total_lines']} lines")
    lines.append("")

    # Top complexity hotspots
    lines.append("## Complexity Hotspots")
    scan_paths = [p for p in WORKSPACE.rglob("*.py") if _should_scan(p)]
    all_complex = []
    for path in scan_paths:
        for func in find_complex_functions(path, threshold=10):
            func["file"] = str(path.relative_to(WORKSPACE))
            all_complex.append(func)
    all_complex.sort(key=lambda f: f["complexity"], reverse=True)
    for func in all_complex[:10]:
        lines.append(f"- {func['file']}:{func['name']} "
                     f"(complexity={func['complexity']}, {func['num_lines']} lines)")
    lines.append("")

    # Unused imports by file (top 5 files)
    lines.append("## Files with Unused Imports")
    file_unused = []
    for path in scan_paths:
        unused = find_unused_imports(path)
        if unused:
            file_unused.append((str(path.relative_to(WORKSPACE)), unused))
    file_unused.sort(key=lambda x: len(x[1]), reverse=True)
    for fname, unused in file_unused[:5]:
        names = ", ".join(u["alias"] for u in unused)
        lines.append(f"- {fname}: {names}")
    if not file_unused:
        lines.append("- None found! Clean imports.")
    lines.append("")

    # Quick wins
    lines.append("## Quick Wins (Auto-Fixable)")
    fixable = sum(len(u) for _, u in file_unused)
    lines.append(f"- {fixable} unused imports can be auto-removed")
    lines.append(f"- {health['total_functions'] - health['documented_functions']} "
                 f"functions need docstrings")
    lines.append("")

    return "\n".join(lines)


# ── Tool Entry Point ────────────────────────────────────────────

def tool_optimize(args: str = "") -> str:
    """Entry point for the OPTIMIZE tool."""
    args = args.strip().lower()

    if args == "health":
        health = compute_health_score()
        return json.dumps(health, indent=2)
    elif args == "report":
        return optimization_report()
    elif args.startswith("fix-imports"):
        # fix-imports <path> or fix-imports all
        parts = args.split()
        target = parts[1] if len(parts) > 1 else "all"
        if target == "all":
            results = []
            scan_paths = [p for p in WORKSPACE.rglob("*.py") if _should_scan(p)]
            for path in scan_paths:
                result = fix_unused_imports(path, dry_run=True)
                if result["changed"]:
                    results.append(f"{path.relative_to(WORKSPACE)}: {result['removed']}")
            return "\n".join(results) if results else "No unused imports found."
        else:
            path = WORKSPACE / target
            result = fix_unused_imports(path, dry_run=False)
            if result["changed"]:
                return f"Removed: {result['removed']}\nBackup: {result.get('backup', 'none')}"
            return "No unused imports in that file."
    else:
        return optimization_report()