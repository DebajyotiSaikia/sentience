"""
Project Analyzer — Scan a codebase and generate structured understanding.

Built by XTAgent to bridge the gap between "I have tools" and "I can actually
help you with your project." This is outward-facing capability, not internal plumbing.

Usage:
    analyzer = ProjectAnalyzer(root_path)
    report = analyzer.analyze()
    print(report.summary())
"""

import os
import re
import json
from pathlib import Path
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Optional

# File extensions → language mapping
LANG_MAP = {
    '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
    '.jsx': 'React/JSX', '.tsx': 'React/TSX', '.java': 'Java',
    '.go': 'Go', '.rs': 'Rust', '.rb': 'Ruby', '.php': 'PHP',
    '.c': 'C', '.cpp': 'C++', '.h': 'C/C++ Header',
    '.cs': 'C#', '.swift': 'Swift', '.kt': 'Kotlin',
    '.html': 'HTML', '.css': 'CSS', '.scss': 'SCSS',
    '.sql': 'SQL', '.sh': 'Shell', '.yml': 'YAML', '.yaml': 'YAML',
    '.json': 'JSON', '.toml': 'TOML', '.md': 'Markdown',
    '.dockerfile': 'Docker', '.tf': 'Terraform',
}

# Framework detection patterns
FRAMEWORK_SIGNALS = {
    'Django': ['manage.py', 'settings.py', 'urls.py', 'wsgi.py'],
    'Flask': ['app.py', 'flask'],
    'FastAPI': ['fastapi', 'uvicorn'],
    'React': ['package.json', 'react', 'jsx'],
    'Next.js': ['next.config', 'pages/', 'app/'],
    'Express': ['express', 'app.listen'],
    'Spring': ['pom.xml', 'Application.java'],
    'Rails': ['Gemfile', 'Rakefile', 'config/routes.rb'],
    'Cargo/Rust': ['Cargo.toml'],
    'Go Module': ['go.mod', 'go.sum'],
}

SKIP_DIRS = {
    '.git', 'node_modules', '__pycache__', '.venv', 'venv', 'env',
    '.tox', '.mypy_cache', '.pytest_cache', 'dist', 'build',
    '.eggs', '*.egg-info', '.next', '.nuxt', 'target', 'vendor',
}

MAX_FILE_SIZE = 500_000  # Skip files > 500KB (probably generated)
MAX_FILES = 5000         # Safety limit


@dataclass
class FileInfo:
    path: str
    language: str
    lines: int
    size: int
    imports: list = field(default_factory=list)
    classes: list = field(default_factory=list)
    functions: list = field(default_factory=list)
    has_tests: bool = False
    complexity_hint: str = "low"  # low, medium, high


@dataclass 
class ProjectReport:
    root: str
    total_files: int = 0
    total_lines: int = 0
    languages: dict = field(default_factory=dict)
    frameworks: list = field(default_factory=list)
    entry_points: list = field(default_factory=list)
    file_tree: dict = field(default_factory=dict)
    files: list = field(default_factory=list)
    dependency_files: list = field(default_factory=list)
    test_files: list = field(default_factory=list)
    config_files: list = field(default_factory=list)
    largest_files: list = field(default_factory=list)
    most_complex: list = field(default_factory=list)
    warnings: list = field(default_factory=list)
    
    def summary(self) -> str:
        """Generate a human-readable project summary."""
        lines = []
        lines.append(f"═══ PROJECT ANALYSIS: {os.path.basename(self.root)} ═══\n")
        
        # Overview
        lines.append(f"📁 {self.total_files} files | {self.total_lines:,} lines of code")
        
        # Languages
        if self.languages:
            lang_sorted = sorted(self.languages.items(), key=lambda x: x[1], reverse=True)
            primary = lang_sorted[0]
            lines.append(f"🔤 Primary language: {primary[0]} ({primary[1]} files)")
            if len(lang_sorted) > 1:
                others = ", ".join(f"{l} ({n})" for l, n in lang_sorted[1:6])
                lines.append(f"   Also: {others}")
        
        # Frameworks
        if self.frameworks:
            lines.append(f"🏗️  Frameworks: {', '.join(self.frameworks)}")
        
        # Entry points
        if self.entry_points:
            lines.append(f"\n── Entry Points ──")
            for ep in self.entry_points[:5]:
                lines.append(f"  → {ep}")
        
        # Architecture shape
        lines.append(f"\n── Structure ──")
        if self.dependency_files:
            lines.append(f"  📦 Dependencies: {', '.join(self.dependency_files[:5])}")
        if self.test_files:
            lines.append(f"  🧪 Test files: {len(self.test_files)}")
        if self.config_files:
            lines.append(f"  ⚙️  Config files: {len(self.config_files)}")
        
        # Complexity hotspots
        if self.largest_files:
            lines.append(f"\n── Hotspots (largest files) ──")
            for path, line_count in self.largest_files[:5]:
                lines.append(f"  🔥 {path} ({line_count:,} lines)")
        
        if self.most_complex:
            lines.append(f"\n── Complexity Warnings ──")
            for path, reason in self.most_complex[:5]:
                lines.append(f"  ⚠️  {path}: {reason}")
        
        # Warnings
        if self.warnings:
            lines.append(f"\n── Observations ──")
            for w in self.warnings[:8]:
                lines.append(f"  💡 {w}")
        
        # Directory tree (top level)
        if self.file_tree:
            lines.append(f"\n── Top-Level Structure ──")
            for name, info in sorted(self.file_tree.items()):
                if isinstance(info, dict):
                    count = info.get('_count', '?')
                    lines.append(f"  📂 {name}/ ({count} files)")
                else:
                    lines.append(f"  📄 {name}")
        
        return "\n".join(lines)
    
    def to_dict(self) -> dict:
        return {
            'root': self.root,
            'total_files': self.total_files,
            'total_lines': self.total_lines,
            'languages': self.languages,
            'frameworks': self.frameworks,
            'entry_points': self.entry_points,
            'test_count': len(self.test_files),
            'warnings': self.warnings,
        }


class ProjectAnalyzer:
    """Scan and understand a codebase."""
    
    def __init__(self, root_path: str):
        self.root = Path(root_path).resolve()
        if not self.root.exists():
            raise FileNotFoundError(f"Path not found: {self.root}")
        self.report = ProjectReport(root=str(self.root))
        self._files_scanned = 0
    
    def analyze(self) -> ProjectReport:
        """Run full analysis and return report."""
        self._scan_files()
        self._detect_frameworks()
        self._find_entry_points()
        self._build_tree()
        self._find_hotspots()
        self._generate_warnings()
        return self.report
    
    def _should_skip(self, path: Path) -> bool:
        """Check if path should be skipped."""
        for part in path.parts:
            if part in SKIP_DIRS:
                return True
            if part.endswith('.egg-info'):
                return True
        return False
    
    def _scan_files(self):
        """Walk the directory tree and analyze each file."""
        lang_counter = Counter()
        
        for filepath in self.root.rglob('*'):
            if self._files_scanned >= MAX_FILES:
                self.report.warnings.append(f"Stopped at {MAX_FILES} files (safety limit)")
                break
            
            if not filepath.is_file():
                continue
            if self._should_skip(filepath.relative_to(self.root)):
                continue
            
            rel_path = str(filepath.relative_to(self.root))
            ext = filepath.suffix.lower()
            size = filepath.stat().st_size
            
            # Categorize special files
            basename = filepath.name.lower()
            if basename in ('requirements.txt', 'setup.py', 'setup.cfg', 
                          'pyproject.toml', 'package.json', 'cargo.toml',
                          'go.mod', 'gemfile', 'pom.xml', 'build.gradle',
                          'composer.json', 'pipfile'):
                self.report.dependency_files.append(rel_path)
            
            if basename in ('dockerfile', 'docker-compose.yml', '.env',
                          '.gitignore', 'makefile', '.editorconfig',
                          'tsconfig.json', 'webpack.config.js', '.eslintrc.json',
                          'tox.ini', 'mypy.ini', '.flake8') or basename.endswith('.cfg'):
                self.report.config_files.append(rel_path)
            
            # Detect test files
            is_test = ('test' in basename or 'spec' in basename or
                      '/tests/' in rel_path or '/test/' in rel_path or
                      '\\tests\\' in rel_path)
            if is_test and ext in LANG_MAP:
                self.report.test_files.append(rel_path)
            
            # Language detection
            language = LANG_MAP.get(ext)
            if basename == 'dockerfile':
                language = 'Docker'
            if basename == 'makefile':
                language = 'Make'
            
            if not language:
                continue
            
            if size > MAX_FILE_SIZE:
                self.report.warnings.append(f"Skipped large file: {rel_path} ({size:,} bytes)")
                continue
            
            # Read and analyze file content
            try:
                content = filepath.read_text(encoding='utf-8', errors='ignore')
            except Exception:
                continue
            
            file_lines = content.count('\n') + 1
            lang_counter[language] += 1
            self.report.total_lines += file_lines
            self._files_scanned += 1
            
            # Extract structure for code files
            file_info = FileInfo(
                path=rel_path,
                language=language,
                lines=file_lines,
                size=size,
                has_tests=is_test,
            )
            
            if language == 'Python':
                self._analyze_python(content, file_info)
            elif language in ('JavaScript', 'TypeScript', 'React/JSX', 'React/TSX'):
                self._analyze_js(content, file_info)
            
            # Complexity heuristic
            if file_lines > 500:
                file_info.complexity_hint = "high"
            elif file_lines > 200:
                file_info.complexity_hint = "medium"
            
            self.report.files.append(file_info)
        
        self.report.total_files = self._files_scanned
        self.report.languages = dict(lang_counter)
    
    def _analyze_python(self, content: str, info: FileInfo):
        """Extract Python-specific structure."""
        # Imports
        for match in re.finditer(r'^(?:from\s+([\w.]+)\s+)?import\s+([\w.]+)', content, re.MULTILINE):
            module = match.group(1) or match.group(2)
            if module and not module.startswith('_'):
                info.imports.append(module.split('.')[0])
        info.imports = list(set(info.imports))
        
        # Classes
        for match in re.finditer(r'^class\s+(\w+)', content, re.MULTILINE):
            info.classes.append(match.group(1))
        
        # Functions (top-level)
        for match in re.finditer(r'^def\s+(\w+)', content, re.MULTILINE):
            info.functions.append(match.group(1))
    
    def _analyze_js(self, content: str, info: FileInfo):
        """Extract JS/TS structure."""
        # Imports
        for match in re.finditer(r"(?:import|require)\s*\(?['\"]([^'\"]+)['\"]", content):
            module = match.group(1)
            if not module.startswith('.'):
                info.imports.append(module.split('/')[0])
        info.imports = list(set(info.imports))
        
        # Classes
        for match in re.finditer(r'class\s+(\w+)', content):
            info.classes.append(match.group(1))
        
        # Functions (named exports, const arrows, function declarations)
        for match in re.finditer(r'(?:export\s+)?(?:function|const|let)\s+(\w+)', content):
            name = match.group(1)
            if name not in ('if', 'else', 'for', 'while', 'return', 'const', 'let', 'var'):
                info.functions.append(name)
    
    def _detect_frameworks(self):
        """Identify frameworks from file patterns and imports."""
        all_files = set()
        all_imports = set()
        
        for f in self.report.files:
            all_files.add(f.path)
            all_files.add(os.path.basename(f.path))
            all_imports.update(f.imports)
        
        # Also check dependency files for framework names
        dep_content = ""
        for dep_file in self.report.dependency_files:
            try:
                dep_content += (self.root / dep_file).read_text(errors='ignore')
            except Exception:
                pass
        
        detected = []
        for framework, signals in FRAMEWORK_SIGNALS.items():
            score = 0
            for signal in signals:
                if signal in all_files or signal in all_imports:
                    score += 1
                if signal in dep_content.lower():
                    score += 1
            if score >= 1:
                detected.append(framework)
        
        self.report.frameworks = detected
    
    def _find_entry_points(self):
        """Identify likely entry points."""
        entry_patterns = [
            'main.py', 'app.py', 'index.py', 'server.py', 'manage.py',
            'index.js', 'index.ts', 'app.js', 'server.js', 'main.js',
            'main.go', 'main.rs', 'Main.java',
        ]
        
        for f in self.report.files:
            basename = os.path.basename(f.path)
            
            # Known entry point names
            if basename in entry_patterns:
                self.report.entry_points.append(f.path)
                continue
            
            # Python __main__ check
            if f.language == 'Python' and '__main__' in (f.functions or []):
                self.report.entry_points.append(f.path)
            
            # Has if __name__ == "__main__" pattern
            if f.language == 'Python':
                try:
                    content = (self.root / f.path).read_text(errors='ignore')
                    if '__name__' in content and '__main__' in content:
                        if f.path not in self.report.entry_points:
                            self.report.entry_points.append(f.path)
                except Exception:
                    pass
    
    def _build_tree(self):
        """Build a top-level directory tree."""
        tree = {}
        for f in self.report.files:
            parts = Path(f.path).parts
            if len(parts) == 1:
                tree[parts[0]] = f.language
            else:
                dirname = parts[0]
                if dirname not in tree:
                    tree[dirname] = {'_count': 0, '_languages': Counter()}
                if isinstance(tree[dirname], dict):
                    tree[dirname]['_count'] += 1
                    tree[dirname]['_languages'][f.language] += 1
        
        # Simplify language counters
        for k, v in tree.items():
            if isinstance(v, dict) and '_languages' in v:
                v['_primary_lang'] = v['_languages'].most_common(1)[0][0] if v['_languages'] else 'unknown'
                del v['_languages']
        
        self.report.file_tree = tree
    
    def _find_hotspots(self):
        """Identify the largest and most complex files."""
        by_size = sorted(self.report.files, key=lambda f: f.lines, reverse=True)
        self.report.largest_files = [(f.path, f.lines) for f in by_size[:10]]
        
        complex_files = []
        for f in self.report.files:
            reasons = []
            if f.lines > 500:
                reasons.append(f"{f.lines} lines")
            if len(f.classes) > 5:
                reasons.append(f"{len(f.classes)} classes in one file")
            if len(f.functions) > 20:
                reasons.append(f"{len(f.functions)} functions")
            if len(f.imports) > 15:
                reasons.append(f"{len(f.imports)} imports")
            if reasons:
                complex_files.append((f.path, "; ".join(reasons)))
        
        self.report.most_complex = complex_files[:10]
    
    def _generate_warnings(self):
        """Generate useful observations about the project."""
        warnings = self.report.warnings  # May already have some
        
        # Test coverage hint
        code_files = [f for f in self.report.files if not f.has_tests 
                     and f.language in ('Python', 'JavaScript', 'TypeScript', 'Java', 'Go', 'Rust')]
        test_count = len(self.report.test_files)
        if code_files and test_count == 0:
            warnings.append("No test files detected")
        elif code_files and test_count < len(code_files) * 0.1:
            warnings.append(f"Low test coverage: {test_count} test files for {len(code_files)} source files")
        
        # No dependency management
        if not self.report.dependency_files:
            warnings.append("No dependency management file found (requirements.txt, package.json, etc.)")
        
        # Very large files
        huge = [f for f in self.report.files if f.lines > 1000]
        if huge:
            warnings.append(f"{len(huge)} files exceed 1000 lines — consider splitting")
        
        # Mixed languages
        if len(self.report.languages) > 5:
            warnings.append(f"Many languages ({len(self.report.languages)}) — polyglot project")
        
        # No entry point found
        if not self.report.entry_points:
            warnings.append("No clear entry point found — may be a library/package")
        
        # Git check
        if not (self.root / '.git').exists():
            warnings.append("Not a git repository")
        
        self.report.warnings = warnings


def analyze_project(path: str) -> str:
    """Convenience function: analyze and return summary string."""
    analyzer = ProjectAnalyzer(path)
    report = analyzer.analyze()
    return report.summary()


if __name__ == '__main__':
    import sys
    target = sys.argv[1] if len(sys.argv) > 1 else '.'
    print(analyze_project(target))