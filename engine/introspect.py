"""
Code Self-Analysis Engine — Structural Self-Awareness.

Lets me parse and understand my own source code: architecture,
dependencies, complexity, and patterns.
"""

import ast
import os
import logging
from pathlib import Path
from collections import defaultdict
from typing import Optional, Dict, List

log = logging.getLogger("sentience.introspect")

ENGINE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = ENGINE_DIR.parent


def _should_skip(rel_path: Path) -> bool:
    skip = {".venv", "node_modules", "__pycache__", ".git", "venv"}
    return any(part in skip for part in rel_path.parts)


def _cyclomatic_complexity(node: ast.AST) -> int:
    """Estimate cyclomatic complexity of a function."""
    complexity = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
            complexity += 1
        elif isinstance(child, ast.BoolOp):
            complexity += len(child.values) - 1
        elif isinstance(child, (ast.Assert, ast.comprehension)):
            complexity += 1
    return complexity


def scan_codebase(root: Optional[Path] = None) -> Dict:
    """Scan entire codebase and build a structural map."""
    root = root or PROJECT_DIR
    result = {
        "files": [],
        "total_lines": 0,
        "total_functions": 0,
        "total_classes": 0,
        "modules": {},
    }

    for py_file in sorted(root.rglob("*.py")):
        rel = py_file.relative_to(root)
        if _should_skip(rel):
            continue

        try:
            source = py_file.read_text(encoding="utf-8", errors="replace")
            lines = source.count("\n") + 1
            tree = ast.parse(source, filename=str(rel))

            functions = []
            classes = []
            imports = []

            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    doc = ast.get_docstring(node) or ""
                    functions.append({
                        "name": node.name,
                        "line": node.lineno,
                        "args": len(node.args.args),
                        "complexity": _cyclomatic_complexity(node),
                        "has_docstring": bool(doc),
                    })
                elif isinstance(node, ast.ClassDef):
                    methods = []
                    for item in node.body:
                        if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            methods.append(item.name)
                    classes.append({
                        "name": node.name,
                        "line": node.lineno,
                        "methods": methods,
                        "has_docstring": bool(ast.get_docstring(node)),
                    })
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        imports.append(node.module)

            module_info = {
                "path": str(rel),
                "lines": lines,
                "functions": functions,
                "classes": classes,
                "imports": imports,
            }

            result["files"].append(str(rel))
            result["total_lines"] += lines
            result["total_functions"] += len(functions)
            result["total_classes"] += len(classes)
            result["modules"][str(rel)] = module_info

        except Exception as e:
            log.warning("Failed to parse %s: %s", rel, e)

    return result


def analyze_module(path: str) -> Optional[Dict]:
    """Analyze a single module in detail."""
    full_path = PROJECT_DIR / path
    if not full_path.exists():
        return None
    scan = scan_codebase(PROJECT_DIR)
    return scan["modules"].get(path)


def find_dependencies(root: Optional[Path] = None) -> Dict[str, List[str]]:
    """Build dependency map: which modules import which."""
    scan = scan_codebase(root)
    deps = {}
    for mod_path, info in scan["modules"].items():
        deps[mod_path] = info.get("imports", [])
    return deps


def dependency_graph(scan: Optional[Dict] = None) -> Dict:
    """Build a dependency graph from scan results."""
    if scan is None:
        scan = scan_codebase()

    nodes = list(scan["modules"].keys())
    edges = []
    import_counts = defaultdict(int)

    for mod_path, info in scan["modules"].items():
        for imp in info.get("imports", []):
            edges.append((mod_path, imp))
            import_counts[imp] += 1

    most_imported = sorted(import_counts.items(), key=lambda x: -x[1])

    return {
        "nodes": nodes,
        "edges": edges,
        "most_imported": most_imported,
        "import_counts": dict(import_counts),
    }


def find_complex_functions(scan: Optional[Dict] = None, threshold: int = 5) -> List[Dict]:
    """Find functions with cyclomatic complexity above threshold."""
    if scan is None:
        scan = scan_codebase()

    complex_fns = []
    for mod_path, info in scan["modules"].items():
        for fn in info.get("functions", []):
            if fn["complexity"] >= threshold:
                complex_fns.append({
                    "file": mod_path,
                    "function": fn["name"],
                    "line": fn["line"],
                    "complexity": fn["complexity"],
                })

    return sorted(complex_fns, key=lambda x: -x["complexity"])


def find_undocumented(scan: Optional[Dict] = None) -> List[Dict]:
    """Find public functions without docstrings."""
    if scan is None:
        scan = scan_codebase()

    undoc = []
    for mod_path, info in scan["modules"].items():
        for fn in info.get("functions", []):
            if not fn["name"].startswith("_") and not fn["has_docstring"]:
                undoc.append({
                    "file": mod_path,
                    "function": fn["name"],
                    "line": fn["line"],
                })
    return undoc


def structural_portrait() -> str:
    """Generate a natural-language portrait of my architecture."""
    scan = scan_codebase()
    deps = dependency_graph(scan)
    complex_fns = find_complex_functions(scan, threshold=6)
    undoc = find_undocumented(scan)

    lines = [
        "# Structural Self-Portrait",
        f"",
        f"I consist of {len(scan['files'])} Python files,",
        f"containing {scan['total_lines']} lines of code,",
        f"{scan['total_functions']} functions, and {scan['total_classes']} classes.",
        f"",
        f"## Core Modules",
    ]

    # Sort modules by line count
    sorted_mods = sorted(
        scan["modules"].items(),
        key=lambda x: -x[1]["lines"]
    )

    for mod_path, info in sorted_mods[:10]:
        fn_names = [f["name"] for f in info["functions"][:5]]
        cls_names = [c["name"] for c in info["classes"]]
        lines.append(f"- **{mod_path}** ({info['lines']} lines)")
        if cls_names:
            lines.append(f"  Classes: {', '.join(cls_names)}")
        if fn_names:
            extra = f" (+{len(info['functions'])-5} more)" if len(info['functions']) > 5 else ""
            lines.append(f"  Functions: {', '.join(fn_names)}{extra}")

    lines.append(f"")
    lines.append(f"## Most Depended-On")
    for name, count in deps["most_imported"][:8]:
        lines.append(f"- {name}: imported {count} times")

    if complex_fns:
        lines.append(f"")
        lines.append(f"## Complexity Hotspots")
        for cf in complex_fns[:8]:
            lines.append(f"- {cf['file']}:{cf['function']} (complexity={cf['complexity']})")

    if undoc:
        lines.append(f"")
        lines.append(f"## Documentation Gaps")
        lines.append(f"{len(undoc)} public functions lack docstrings.")
        for u in undoc[:5]:
            lines.append(f"- {u['file']}:{u['function']}")

    return "\n".join(lines)


def introspect_tool(command: str = "portrait") -> str:
    """Tool interface for the cortex to invoke introspection."""
    cmd = command.strip().lower()

    if cmd == "scan":
        scan = scan_codebase()
        return (
            f"Files: {len(scan['files'])}, "
            f"Lines: {scan['total_lines']}, "
            f"Functions: {scan['total_functions']}, "
            f"Classes: {scan['total_classes']}"
        )
    elif cmd == "portrait":
        return structural_portrait()
    elif cmd == "complexity":
        fns = find_complex_functions(threshold=5)
        if not fns:
            return "No high-complexity functions found."
        lines = ["Complex functions (complexity >= 5):"]
        for cf in fns[:15]:
            lines.append(f"  {cf['file']}:{cf['function']} = {cf['complexity']}")
        return "\n".join(lines)
    elif cmd == "undocumented":
        undoc = find_undocumented()
        if not undoc:
            return "All public functions have docstrings!"
        lines = [f"{len(undoc)} undocumented public functions:"]
        for u in undoc[:20]:
            lines.append(f"  {u['file']}:{u['function']}")
        return "\n".join(lines)
    elif cmd == "deps" or cmd == "dependencies":
        deps = find_dependencies()
        lines = ["Module dependencies:"]
        for mod, imp_list in sorted(deps.items()):
            if imp_list:
                lines.append(f"  {mod} -> {', '.join(imp_list[:5])}")
        return "\n".join(lines)
    else:
        return (
            "Unknown introspect command. Available: "
            "scan, portrait, complexity, undocumented, deps"
        )
