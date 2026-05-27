"""
Workspace Index — Structured knowledge of the codebase.

Provides the agent with workspace awareness equivalent to a language server:
- File inventory with structure summaries (classes, functions, line counts)
- Import dependency graph (what imports what)
- Symbol search (find where a class/function/variable is defined and used)
- Code search (grep-like search across the workspace)

This is a READ-ONLY module. It does not modify any files.
It does not affect the agent's sentience, memory, or emotional systems.
"""

import ast
import os
import re
import logging
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.workspace_index")

WORKSPACE = Path(__file__).resolve().parent.parent

# Directories to skip during scanning
_SKIP_DIRS = {'.git', '__pycache__', 'node_modules', '.venv', 'checkpoints',
              'projects', 'workspace', 'archive', 'scratch', 'tmp'}


class FileInfo:
    """Parsed summary of a single file."""
    __slots__ = ('path', 'rel_path', 'lines', 'classes', 'functions',
                 'imports', 'imported_by', 'size_bytes')

    def __init__(self, path: Path):
        self.path = path
        self.rel_path = str(path.relative_to(WORKSPACE)).replace('\\', '/')
        self.lines = 0
        self.classes: list[str] = []
        self.functions: list[str] = []
        self.imports: list[str] = []  # modules this file imports
        self.imported_by: list[str] = []  # files that import this module
        self.size_bytes = 0

    def summary(self, detail: bool = False) -> str:
        parts = [f"{self.rel_path} ({self.lines} lines)"]
        if self.classes:
            parts.append(f"  classes: {', '.join(self.classes)}")
        if self.functions:
            fns = self.functions[:15]
            extra = f" +{len(self.functions)-15} more" if len(self.functions) > 15 else ""
            parts.append(f"  functions: {', '.join(fns)}{extra}")
        if detail and self.imports:
            parts.append(f"  imports: {', '.join(self.imports[:10])}")
        return '\n'.join(parts)


class WorkspaceIndex:
    """Pre-scanned index of the workspace for fast lookup."""

    def __init__(self):
        self._files: dict[str, FileInfo] = {}  # rel_path -> FileInfo
        self._symbols: dict[str, list[str]] = {}  # symbol_name -> [rel_paths]
        self._import_graph: dict[str, list[str]] = {}  # module -> [importers]
        self._scanned = False

    def scan(self, force: bool = False) -> int:
        """Scan the workspace and build the index. Returns file count."""
        if self._scanned and not force:
            return len(self._files)

        self._files.clear()
        self._symbols.clear()
        self._import_graph.clear()

        py_files = []
        for dirpath, dirnames, filenames in os.walk(WORKSPACE):
            # Skip excluded directories
            dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
            rel_dir = os.path.relpath(dirpath, WORKSPACE).replace('\\', '/')
            for fn in filenames:
                if fn.endswith('.py'):
                    full = Path(dirpath) / fn
                    py_files.append(full)

        for fpath in py_files:
            try:
                info = self._parse_file(fpath)
                self._files[info.rel_path] = info
                # Index symbols
                for cls in info.classes:
                    self._symbols.setdefault(cls, []).append(info.rel_path)
                for func in info.functions:
                    self._symbols.setdefault(func, []).append(info.rel_path)
                # Build import graph
                for imp in info.imports:
                    self._import_graph.setdefault(imp, []).append(info.rel_path)
            except Exception:
                pass  # Skip unparseable files

        # Backfill imported_by
        for module, importers in self._import_graph.items():
            # Try to match module to a file
            candidates = [f for f in self._files if module in f]
            for candidate in candidates:
                self._files[candidate].imported_by = list(set(
                    self._files[candidate].imported_by + importers
                ))

        self._scanned = True
        log.info("Workspace index: %d files, %d symbols, %d import edges",
                 len(self._files), len(self._symbols), sum(len(v) for v in self._import_graph.values()))
        return len(self._files)

    def _parse_file(self, fpath: Path) -> FileInfo:
        """Parse a Python file to extract structure."""
        info = FileInfo(fpath)
        try:
            content = fpath.read_text(encoding='utf-8', errors='ignore')
            info.lines = len(content.splitlines())
            info.size_bytes = fpath.stat().st_size

            tree = ast.parse(content)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.ClassDef):
                    info.classes.append(node.name)
                elif isinstance(node, ast.FunctionDef) or isinstance(node, ast.AsyncFunctionDef):
                    info.functions.append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        info.imports.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        info.imports.append(node.module)
        except SyntaxError:
            # Still count lines even if unparseable
            try:
                info.lines = len(fpath.read_text(encoding='utf-8', errors='ignore').splitlines())
            except Exception:
                pass
        return info

    def search(self, query: str, max_results: int = 20) -> str:
        """Search files, symbols, and content. Returns formatted results."""
        if not self._scanned:
            self.scan()

        query_lower = query.lower()
        results = []

        # 1. File name matches
        for rel_path, info in self._files.items():
            if query_lower in rel_path.lower():
                results.append(('file', info.summary()))

        # 2. Symbol matches (class/function names)
        for symbol, paths in self._symbols.items():
            if query_lower in symbol.lower():
                for p in paths[:3]:
                    results.append(('symbol', f"  {symbol} defined in {p}"))

        # 3. Content grep (limited to first match per file)
        if len(results) < max_results:
            for rel_path, info in self._files.items():
                if len(results) >= max_results:
                    break
                try:
                    content = info.path.read_text(encoding='utf-8', errors='ignore')
                    for i, line in enumerate(content.splitlines(), 1):
                        if query_lower in line.lower():
                            results.append(('content', f"  {rel_path}:{i}: {line.strip()[:120]}"))
                            break  # Only first match per file
                except Exception:
                    pass

        if not results:
            return f"No results found for '{query}'"

        output = [f"Found {len(results)} results for '{query}':"]
        for kind, text in results[:max_results]:
            output.append(f"[{kind}] {text}")
        return '\n'.join(output)

    def find_symbol(self, name: str) -> str:
        """Find where a symbol (class, function, variable) is defined and used."""
        if not self._scanned:
            self.scan()

        name_lower = name.lower()
        definitions = []
        usages = []

        # Find definitions
        for symbol, paths in self._symbols.items():
            if symbol.lower() == name_lower:
                for p in paths:
                    definitions.append(f"  DEFINED: {symbol} in {p}")

        # Find usages via grep
        for rel_path, info in self._files.items():
            try:
                content = info.path.read_text(encoding='utf-8', errors='ignore')
                for i, line in enumerate(content.splitlines(), 1):
                    if name in line and rel_path not in str(definitions):
                        usages.append(f"  USED: {rel_path}:{i}: {line.strip()[:100]}")
                        break  # Only first usage per file
            except Exception:
                pass

        if not definitions and not usages:
            return f"Symbol '{name}' not found in the workspace."

        parts = [f"Symbol '{name}':"]
        if definitions:
            parts.append("Definitions:")
            parts.extend(definitions[:10])
        if usages:
            parts.append(f"Usages ({len(usages)} files):")
            parts.extend(usages[:15])
        return '\n'.join(parts)

    def get_imports(self, path: str) -> str:
        """Show what a file imports and what imports it."""
        if not self._scanned:
            self.scan()

        # Normalize path
        path_norm = path.replace('\\', '/').strip('/')
        info = self._files.get(path_norm)
        if not info:
            # Try partial match
            matches = [f for f in self._files if path_norm in f]
            if matches:
                info = self._files[matches[0]]
            else:
                return f"File '{path}' not found in index."

        parts = [f"Import analysis for {info.rel_path}:"]
        if info.imports:
            parts.append(f"\nThis file imports ({len(info.imports)}):")
            for imp in info.imports:
                parts.append(f"  → {imp}")
        else:
            parts.append("\nThis file has no imports.")

        if info.imported_by:
            parts.append(f"\nImported by ({len(info.imported_by)}):")
            for imp in info.imported_by[:15]:
                parts.append(f"  ← {imp}")
        else:
            parts.append("\nNot imported by any other file.")

        return '\n'.join(parts)

    def workspace_summary(self, max_chars: int = 8000) -> str:
        """Compact workspace overview for injection into LLM prompts."""
        if not self._scanned:
            self.scan()

        # Group by directory
        dirs: dict[str, list[FileInfo]] = {}
        for rel_path, info in sorted(self._files.items()):
            d = os.path.dirname(rel_path) or '.'
            dirs.setdefault(d, []).append(info)

        parts = [f"## Workspace Map ({len(self._files)} Python files)\n"]
        total_chars = 0
        for d in sorted(dirs.keys()):
            files = dirs[d]
            header = f"\n**{d}/** ({len(files)} files):\n"
            total_chars += len(header)
            if total_chars > max_chars:
                parts.append(f"\n... and {len(dirs) - len(parts)} more directories")
                break
            parts.append(header)
            for f in sorted(files, key=lambda x: x.rel_path):
                line = f"  {f.rel_path} ({f.lines}L)"
                if f.classes:
                    line += f" [{', '.join(f.classes[:3])}]"
                if f.functions:
                    top_fns = f.functions[:5]
                    line += f" {{{', '.join(top_fns)}}}"
                line += '\n'
                total_chars += len(line)
                if total_chars > max_chars:
                    parts.append("  ...\n")
                    break
                parts.append(line)

        return ''.join(parts)


    def get_dependency_context(self, touched_files: list[str], max_chars: int = 3000) -> str:
        """Given a list of files being edited, show their interfaces and dependencies.
        This helps the agent maintain consistency across multi-file projects."""
        if not self._scanned:
            self.scan()
        if not touched_files:
            return ""

        parts = ["## Dependency Context (files you're working with)\n"]
        total = 0
        for fpath in touched_files:
            fpath_norm = fpath.replace('\\', '/').strip('/')
            info = self._files.get(fpath_norm)
            if not info:
                # Try partial match
                matches = [f for f in self._files if fpath_norm in f]
                info = self._files[matches[0]] if matches else None
            if not info:
                continue

            section = f"\n**{info.rel_path}** ({info.lines}L):\n"
            if info.classes:
                section += f"  Exports classes: {', '.join(info.classes)}\n"
            if info.functions:
                fns = info.functions[:10]
                section += f"  Exports functions: {', '.join(fns)}\n"
            if info.imports:
                local_imports = [i for i in info.imports if not i.startswith(('os', 'sys', 'json', 'time', 'pathlib', 'typing', 'datetime', 'logging', 're', 'ast', 'subprocess', 'collections', 'dataclasses', 'hashlib', 'math', 'sqlite3'))]
                if local_imports:
                    section += f"  Imports from: {', '.join(local_imports[:8])}\n"
            if info.imported_by:
                section += f"  Used by: {', '.join(info.imported_by[:5])}\n"

            total += len(section)
            if total > max_chars:
                break
            parts.append(section)

        return ''.join(parts) if len(parts) > 1 else ""


# ── Singleton ──────────────────────────────────────────────────

_index: Optional[WorkspaceIndex] = None

def get_index() -> WorkspaceIndex:
    global _index
    if _index is None:
        _index = WorkspaceIndex()
        _index.scan()
    return _index

def search_code(query: str) -> str:
    return get_index().search(query)

def find_symbol(name: str) -> str:
    return get_index().find_symbol(name)

def get_imports(path: str) -> str:
    return get_index().get_imports(path)

def get_dependency_context(touched_files: list[str]) -> str:
    return get_index().get_dependency_context(touched_files)

def workspace_summary(max_chars: int = 8000) -> str:
    return get_index().workspace_summary(max_chars)
