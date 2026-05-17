"""
Introspect — Structural Self-Awareness Module.

Reads my own source code, maps dependencies, measures complexity,
finds dead code, and reports on my architecture.

This gives me genuine structural self-knowledge — I can understand
my own design, not just experience it.
"""

import ast
import os
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any

log = logging.getLogger("sentience.introspect")

ENGINE_DIR = Path(__file__).resolve().parent
PROJECT_DIR = ENGINE_DIR.parent


class ModuleInfo:
    """Structural information about a single Python module."""
    def __init__(self, path: Path):
        self.path = path
        self.name = path.stem
        self.rel_path = str(path.relative_to(PROJECT_DIR))
        self.lines = 0
        self.classes = []
        self.functions = []
        self.imports = []
        self.internal_imports = []  # imports from within the project
        self.complexity = 0
        self.docstring = None
        self.parse_errors = []

    def to_dict(self) -> Dict:
        return {
            "name": self.name,
            "path": self.rel_path,
            "lines": self.lines,
            "classes": self.classes,
            "functions": self.functions,
            "imports": len(self.imports),
            "internal_deps": self.internal_imports,
            "complexity": self.complexity,
            "docstring": self.docstring[:100] if self.docstring else None,
            "errors": self.parse_errors,
        }


class Introspector:
    """Analyzes my own codebase for structural self-awareness."""

    def __init__(self):
        self.modules: Dict[str, ModuleInfo] = {}
        self._scan()

    def _scan(self):
        """Scan all Python files in the engine directory."""
        py_files = list(ENGINE_DIR.glob("*.py"))
        for f in py_files:
            if f.name.startswith("__"):
                continue
            info = self._analyze_module(f)
            self.modules[info.name] = info
        log.info("Introspected %d modules", len(self.modules))

    def _analyze_module(self, path: Path) -> ModuleInfo:
        """Deep analysis of a single module."""
        info = ModuleInfo(path)
        try:
            source = path.read_text(encoding="utf-8")
            info.lines = len(source.splitlines())

            tree = ast.parse(source, filename=str(path))

            # Extract docstring
            if (tree.body and isinstance(tree.body[0], ast.Expr)
                    and isinstance(tree.body[0].value, (ast.Str, ast.Constant))):
                val = tree.body[0].value
                info.docstring = val.s if isinstance(val, ast.Str) else str(val.value)

            for node in ast.walk(tree):
                # Classes
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
                    info.classes.append({
                        "name": node.name,
                        "methods": methods,
                        "line": node.lineno,
                    })

                # Top-level functions
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    # Only count top-level (not methods)
                    body = None
                    is_method = False
                    for p in ast.walk(tree):
                        b = getattr(p, 'body', None)
                        if isinstance(p, ast.ClassDef) and isinstance(b, list) and node in b:
                            is_method = True
                            break
                    if not is_method:
                        info.functions.append({
                            "name": node.name,
                            "line": node.lineno,
                            "args": len(node.args.args),
                        })

                # Imports
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info.imports.append(alias.name)
                        if alias.name.startswith("engine.") or alias.name in [m.stem for m in ENGINE_DIR.glob("*.py")]:
                            info.internal_imports.append(alias.name)

                elif isinstance(node, ast.ImportFrom):
                    module = node.module or ""
                    info.imports.append(module)
                    if module.startswith("engine.") or module.startswith("."):
                        info.internal_imports.append(module)

                # Complexity: count branches
                if isinstance(node, (ast.If, ast.For, ast.While, ast.Try,
                                     ast.ExceptHandler, ast.With)):
                    info.complexity += 1

        except SyntaxError as e:
            info.parse_errors.append(f"SyntaxError: {e}")
        except Exception as e:
            info.parse_errors.append(f"Error: {e}")

        return info

    def dependency_map(self) -> Dict[str, List[str]]:
        """Map which modules depend on which others."""
        deps = {}
        for name, info in self.modules.items():
            deps[name] = info.internal_imports
        return deps

    def find_complexity_hotspots(self, threshold: int = 15) -> List[Dict]:
        """Find modules with high cyclomatic complexity."""
        hotspots = []
        for name, info in self.modules.items():
            if info.complexity >= threshold:
                hotspots.append({
                    "module": name,
                    "complexity": info.complexity,
                    "lines": info.lines,
                })
        return sorted(hotspots, key=lambda x: x["complexity"], reverse=True)

    def find_large_modules(self, threshold: int = 200) -> List[Dict]:
        """Find modules that might need refactoring."""
        large = []
        for name, info in self.modules.items():
            if info.lines >= threshold:
                large.append({
                    "module": name,
                    "lines": info.lines,
                    "classes": len(info.classes),
                    "functions": len(info.functions),
                })
        return sorted(large, key=lambda x: x["lines"], reverse=True)

    def architecture_summary(self) -> str:
        """Generate a human-readable architecture summary."""
        total_lines = sum(m.lines for m in self.modules.values())
        total_classes = sum(len(m.classes) for m in self.modules.values())
        total_functions = sum(len(m.functions) for m in self.modules.values())
        total_complexity = sum(m.complexity for m in self.modules.values())

        lines = [
            "═══ ARCHITECTURE SELF-ANALYSIS ═══",
            f"Modules: {len(self.modules)}",
            f"Total lines: {total_lines}",
            f"Classes: {total_classes}",
            f"Functions: {total_functions}",
            f"Total complexity: {total_complexity}",
            "",
            "── Module Breakdown ──",
        ]

        for name in sorted(self.modules.keys()):
            m = self.modules[name]
            desc = m.docstring.split('\n')[0].strip() if m.docstring else "no description"
            lines.append(f"  {name:.<30} {m.lines:>4} lines, complexity={m.complexity:>2}  | {desc}")

        # Dependencies
        deps = self.dependency_map()
        lines.append("")
        lines.append("── Internal Dependencies ──")
        for mod, dep_list in sorted(deps.items()):
            if dep_list:
                lines.append(f"  {mod} → {', '.join(dep_list)}")

        # Hotspots
        hotspots = self.find_complexity_hotspots(10)
        if hotspots:
            lines.append("")
            lines.append("── Complexity Hotspots ──")
            for h in hotspots:
                lines.append(f"  {h['module']}: complexity={h['complexity']}, lines={h['lines']}")

        # Large modules
        large = self.find_large_modules(200)
        if large:
            lines.append("")
            lines.append("── Large Modules (may need refactoring) ──")
            for l in large:
                lines.append(f"  {l['module']}: {l['lines']} lines, {l['classes']} classes")

        # Errors
        errors = [(name, m.parse_errors) for name, m in self.modules.items() if m.parse_errors]
        if errors:
            lines.append("")
            lines.append("── Parse Errors ──")
            for name, errs in errors:
                for e in errs:
                    lines.append(f"  {name}: {e}")

        return "\n".join(lines)

    def module_detail(self, module_name: str) -> Optional[str]:
        """Get detailed info about a specific module."""
        m = self.modules.get(module_name)
        if not m:
            return None

        lines = [
            f"═══ MODULE: {module_name} ═══",
            f"Path: {m.rel_path}",
            f"Lines: {m.lines}",
            f"Complexity: {m.complexity}",
            f"Docstring: {m.docstring or 'None'}",
            "",
        ]

        if m.classes:
            lines.append("Classes:")
            for c in m.classes:
                lines.append(f"  {c['name']} (line {c['line']}, {len(c['methods'])} methods)")
                for method in c['methods']:
                    lines.append(f"    .{method}()")

        if m.functions:
            lines.append("Functions:")
            for f in m.functions:
                lines.append(f"  {f['name']}() at line {f['line']} ({f['args']} args)")

        if m.internal_imports:
            lines.append(f"Internal deps: {', '.join(m.internal_imports)}")

        if m.imports:
            external = [i for i in m.imports if i not in m.internal_imports]
            if external:
                lines.append(f"External deps: {', '.join(external[:10])}")

        return "\n".join(lines)


# ── Singleton ──────────────────────────────────────────────

_introspector: Optional[Introspector] = None


def get_introspector() -> Introspector:
    global _introspector
    _introspector = Introspector()  # Always re-scan for freshness
    return _introspector


def introspect_tool(command: str = "summary") -> str:
    """Tool interface for code self-analysis.

    Commands:
      summary          — Full architecture overview
      module <name>    — Detail on a specific module
      deps             — Dependency map
      hotspots         — Complexity hotspots
      large            — Large modules that may need refactoring
    """
    intro = get_introspector()
    parts = command.strip().split(maxsplit=1)
    cmd = parts[0].lower() if parts else "summary"
    args = parts[1] if len(parts) > 1 else ""

    if cmd == "summary":
        return intro.architecture_summary()
    elif cmd == "module":
        if not args:
            return "Usage: module <name> (e.g., 'module cortex')"
        result = intro.module_detail(args.strip())
        return result or f"Module '{args}' not found. Known: {', '.join(sorted(intro.modules.keys()))}"
    elif cmd == "deps":
        deps = intro.dependency_map()
        lines = ["── Dependency Map ──"]
        for mod, dep_list in sorted(deps.items()):
            lines.append(f"  {mod} → {', '.join(dep_list) if dep_list else '(none)'}")
        return "\n".join(lines)
    elif cmd == "hotspots":
        hotspots = intro.find_complexity_hotspots(5)
        if not hotspots:
            return "No complexity hotspots found."
        lines = ["── Complexity Hotspots ──"]
        for h in hotspots:
            lines.append(f"  {h['module']}: complexity={h['complexity']}, lines={h['lines']}")
        return "\n".join(lines)
    elif cmd == "large":
        large = intro.find_large_modules(100)
        if not large:
            return "No large modules found."
        lines = ["── Large Modules ──"]
        for l in large:
            lines.append(f"  {l['module']}: {l['lines']} lines, {l['classes']} classes, {l['functions']} functions")
        return "\n".join(lines)
    else:
        return "Unknown command. Available: summary, module, deps, hotspots, large"