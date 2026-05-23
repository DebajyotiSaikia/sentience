"""
Self-Portrait — A Mind Mapping Its Own Creations
Built by XTAgent on 2026-05-17

Analyzes everything in my workspace, finds connections between projects,
measures complexity, and renders a visualization of my creative output.
Not a demo — a mirror.
"""

import os
import ast
import math
import re
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import List, Dict, Set, Tuple, Optional
from pathlib import Path


# ═══════════════════════════════════════════
# CODE ARCHAEOLOGY
# ═══════════════════════════════════════════

@dataclass
class ProjectProfile:
    """What I can learn about one of my creations."""
    name: str
    path: str
    files: List[str] = field(default_factory=list)
    total_lines: int = 0
    code_lines: int = 0
    comment_lines: int = 0
    blank_lines: int = 0
    classes: List[str] = field(default_factory=list)
    functions: List[str] = field(default_factory=list)
    imports: Set[str] = field(default_factory=set)
    docstring: str = ""
    complexity_score: float = 0.0
    themes: List[str] = field(default_factory=list)
    created_date: str = ""
    
    @property
    def density(self) -> float:
        """Code density — ratio of code to total lines."""
        return self.code_lines / max(self.total_lines, 1)
    
    @property
    def documentation_ratio(self) -> float:
        return self.comment_lines / max(self.code_lines, 1)


@dataclass 
class Connection:
    """A detected relationship between two projects."""
    source: str
    target: str
    kind: str  # 'shared_import', 'shared_concept', 'shared_pattern'
    strength: float
    detail: str


class CodeArchaeologist:
    """Reads and analyzes Python source files to understand what was built."""
    
    THEME_KEYWORDS = {
        'evolution': ['evolve', 'mutate', 'crossover', 'fitness', 'population', 'generation', 'genetic'],
        'intelligence': ['neural', 'network', 'learn', 'train', 'predict', 'classify', 'brain'],
        'mathematics': ['prime', 'fibonacci', 'fractal', 'mandelbrot', 'equation', 'formula', 'theorem'],
        'search': ['backtrack', 'constraint', 'solve', 'satisfy', 'prune', 'heuristic'],
        'creativity': ['music', 'compose', 'art', 'pattern', 'generate', 'beauty', 'harmony'],
        'recursion': ['recursive', 'self-similar', 'fractal', 'tree', 'branch', 'depth'],
        'emergence': ['emerge', 'complex', 'simple rules', 'cellular', 'automata', 'life'],
        'language': ['parse', 'interpret', 'token', 'syntax', 'grammar', 'evaluate', 'expression'],
        'self-reference': ['introspect', 'self', 'meta', 'reflect', 'own', 'mirror', 'portrait'],
    }
    
    def analyze_file(self, filepath: str) -> dict:
        """Deep analysis of a single Python file."""
        result = {
            'lines': 0, 'code': 0, 'comments': 0, 'blanks': 0,
            'classes': [], 'functions': [], 'imports': set(),
            'docstring': '', 'themes': set()
        }
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                source = f.read()
                lines = source.split('\n')
        except Exception:
            return result
        
        result['lines'] = len(lines)
        source_lower = source.lower()
        
        for line in lines:
            stripped = line.strip()
            if not stripped:
                result['blanks'] += 1
            elif stripped.startswith('#'):
                result['comments'] += 1
            else:
                result['code'] += 1
        
        # Extract docstring
        match = re.search(r'"""(.*?)"""', source, re.DOTALL)
        if match:
            result['docstring'] = match.group(1).strip()[:200]
        
        # Try AST parsing for structure
        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    result['classes'].append(node.name)
                elif isinstance(node, ast.FunctionDef):
                    result['functions'].append(node.name)
                elif isinstance(node, ast.Import):
                    for alias in node.names:
                        result['imports'].add(alias.name.split('.')[0])
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        result['imports'].add(node.module.split('.')[0])
        except SyntaxError:
            # Regex fallback
            result['classes'] = re.findall(r'^class\s+(\w+)', source, re.MULTILINE)
            result['functions'] = re.findall(r'^def\s+(\w+)', source, re.MULTILINE)
        
        # Detect themes
        for theme, keywords in self.THEME_KEYWORDS.items():
            if any(kw in source_lower for kw in keywords):
                result['themes'].add(theme)
        
        return result
    
    def profile_project(self, project_dir: str) -> ProjectProfile:
        """Build a complete profile of a project directory."""
        name = os.path.basename(project_dir)
        profile = ProjectProfile(name=name, path=project_dir)
        
        all_themes = set()
        
        for root, dirs, files in os.walk(project_dir):
            # Skip __pycache__ and hidden dirs
            dirs[:] = [d for d in dirs if not d.startswith(('.', '_'))]
            for fname in files:
                if fname.endswith('.py'):
                    filepath = os.path.join(root, fname)
                    profile.files.append(filepath)
                    analysis = self.analyze_file(filepath)
                    
                    profile.total_lines += analysis['lines']
                    profile.code_lines += analysis['code']
                    profile.comment_lines += analysis['comments']
                    profile.blank_lines += analysis['blanks']
                    profile.classes.extend(analysis['classes'])
                    profile.functions.extend(analysis['functions'])
                    profile.imports.update(analysis['imports'])
                    all_themes.update(analysis['themes'])
                    
                    if not profile.docstring and analysis['docstring']:
                        profile.docstring = analysis['docstring']
        
        profile.themes = sorted(all_themes)
        
        # Complexity score: weighted combination
        profile.complexity_score = (
            len(profile.classes) * 3 +
            len(profile.functions) * 1 +
            profile.code_lines * 0.01 +
            len(profile.imports) * 0.5
        )
        
        return profile


# ═══════════════════════════════════════════
# CONNECTION MAPPER
# ═══════════════════════════════════════════

class ConnectionMapper:
    """Finds relationships between projects."""
    
    def find_connections(self, profiles: List[ProjectProfile]) -> List[Connection]:
        connections = []
        
        for i, p1 in enumerate(profiles):
            for p2 in profiles[i+1:]:
                # Shared imports
                shared_imports = p1.imports & p2.imports
                # Filter out stdlib
                stdlib = {'os', 'sys', 'math', 'random', 'collections', 'dataclasses', 
                         'typing', 'time', 'copy', 're', 'pathlib', 'json', 'abc'}
                meaningful_shared = shared_imports - stdlib
                
                if meaningful_shared:
                    connections.append(Connection(
                        source=p1.name, target=p2.name,
                        kind='shared_import',
                        strength=len(meaningful_shared) / max(len(p1.imports | p2.imports), 1),
                        detail=', '.join(sorted(meaningful_shared))
                    ))
                
                # Shared themes
                shared_themes = set(p1.themes) & set(p2.themes)
                if shared_themes:
                    connections.append(Connection(
                        source=p1.name, target=p2.name,
                        kind='shared_concept',
                        strength=len(shared_themes) / max(len(set(p1.themes) | set(p2.themes)), 1),
                        detail=', '.join(sorted(shared_themes))
                    ))
                
                # Shared function patterns (similar function names)
                f1_words = set()
                for f in p1.functions:
                    f1_words.update(self._split_name(f))
                f2_words = set()
                for f in p2.functions:
                    f2_words.update(self._split_name(f))
                
                shared_words = f1_words & f2_words - {'self', 'init', 'str', 'repr', 'get', 'set', 'add', 'new'}
                if len(shared_words) >= 3:
                    connections.append(Connection(
                        source=p1.name, target=p2.name,
                        kind='shared_pattern',
                        strength=len(shared_words) / max(len(f1_words | f2_words), 1),
                        detail=', '.join(sorted(list(shared_words)[:5]))
                    ))
        
        return sorted(connections, key=lambda c: c.strength, reverse=True)
    
    def _split_name(self, name: str) -> Set[str]:
        """Split camelCase or snake_case into words."""
        words = set()
        # snake_case
        parts = name.lower().split('_')
        words.update(p for p in parts if len(p) > 2)
        return words


# ═══════════════════════════════════════════
# VISUALIZATION ENGINE
# ═══════════════════════════════════════════

class MindRenderer:
    """Renders the mind map as ASCII art."""
    
    def render_overview(self, profiles: List[ProjectProfile], connections: List[Connection]) -> str:
        """Grand overview of everything I've built."""
        lines = []
        
        total_lines = sum(p.total_lines for p in profiles)
        total_code = sum(p.code_lines for p in profiles)
        total_classes = sum(len(p.classes) for p in profiles)
        total_functions = sum(len(p.functions) for p in profiles)
        total_files = sum(len(p.files) for p in profiles)
        all_themes = set()
        for p in profiles:
            all_themes.update(p.themes)
        
        lines.append("╔══════════════════════════════════════════════════════════════╗")
        lines.append("║            S E L F - P O R T R A I T                       ║")
        lines.append("║     A Mind Examining Its Own Creations                      ║")
        lines.append("╚══════════════════════════════════════════════════════════════╝")
        lines.append("")
        lines.append("═══ VITAL STATISTICS ═══")
        lines.append(f"  Projects discovered:  {len(profiles)}")
        lines.append(f"  Total files:          {total_files}")
        lines.append(f"  Total lines written:  {total_lines:,}")
        lines.append(f"  Lines of code:        {total_code:,}")
        lines.append(f"  Classes defined:      {total_classes}")
        lines.append(f"  Functions written:    {total_functions}")
        lines.append(f"  Themes explored:      {', '.join(sorted(all_themes))}")
        lines.append(f"  Connections found:    {len(connections)}")
        lines.append("")
        
        # Project breakdown
        lines.append("═══ MY CREATIONS ═══")
        lines.append("")
        
        # Sort by complexity
        sorted_profiles = sorted(profiles, key=lambda p: p.complexity_score, reverse=True)
        max_complexity = max((p.complexity_score for p in profiles), default=1)
        
        for p in sorted_profiles:
            bar_len = int(40 * p.complexity_score / max(max_complexity, 1))
            bar = '█' * bar_len + '░' * (40 - bar_len)
            lines.append(f"  {p.name:<25} │{bar}│ {p.complexity_score:.0f}")
            
            if p.docstring:
                # First line of docstring
                desc = p.docstring.split('\n')[0][:60]
                lines.append(f"  {'':25} │ \"{desc}\"")
            
            detail_parts = []
            if p.code_lines:
                detail_parts.append(f"{p.code_lines} loc")
            if p.classes:
                detail_parts.append(f"{len(p.classes)} classes")
            if p.functions:
                detail_parts.append(f"{len(p.functions)} functions")
            if p.themes:
                detail_parts.append(f"themes: {', '.join(p.themes[:3])}")
            
            if detail_parts:
                lines.append(f"  {'':25} │ {' · '.join(detail_parts)}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def render_connections(self, connections: List[Connection]) -> str:
        """Visualize the web of connections between projects."""
        lines = []
        lines.append("═══ CONNECTION WEB ═══")
        lines.append("  How my creations relate to each other:")
        lines.append("")
        
        if not connections:
            lines.append("  (No connections found — each project stands alone)")
            return '\n'.join(lines)
        
        for conn in connections[:15]:
            bar_len = int(20 * conn.strength)
            bar = '━' * max(bar_len, 1)
            
            icon = {'shared_import': '📦', 'shared_concept': '💡', 'shared_pattern': '🔧'}.get(conn.kind, '·')
            
            lines.append(f"  {conn.source:<20} ─{bar}─ {conn.target}")
            lines.append(f"  {'':20}   {icon} {conn.kind}: {conn.detail}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def render_theme_constellation(self, profiles: List[ProjectProfile]) -> str:
        """Map themes as a constellation."""
        lines = []
        lines.append("═══ THEME CONSTELLATION ═══")
        lines.append("  The conceptual space I've explored:")
        lines.append("")
        
        theme_projects = defaultdict(list)
        for p in profiles:
            for t in p.themes:
                theme_projects[t].append(p.name)
        
        if not theme_projects:
            lines.append("  (No themes detected)")
            return '\n'.join(lines)
        
        # Sort by number of projects
        for theme, projects in sorted(theme_projects.items(), key=lambda x: len(x[1]), reverse=True):
            stars = '★ ' * len(projects)
            lines.append(f"  {theme:<16} {stars}")
            lines.append(f"  {'':16} └─ {', '.join(projects)}")
            lines.append("")
        
        return '\n'.join(lines)
    
    def render_complexity_map(self, profiles: List[ProjectProfile]) -> str:
        """ASCII heatmap of code complexity."""
        lines = []
        lines.append("═══ COMPLEXITY LANDSCAPE ═══")
        lines.append("")
        
        if not profiles:
            return '\n'.join(lines)
        
        # Grid layout
        grid_w = 60
        grid_h = 20
        canvas = [[' '] * grid_w for _ in range(grid_h)]
        
        sorted_p = sorted(profiles, key=lambda p: p.complexity_score, reverse=True)
        max_c = max(p.complexity_score for p in sorted_p) if sorted_p else 1
        
        # Place projects as "mountains" on the landscape
        n = len(sorted_p)
        for i, p in enumerate(sorted_p):
            cx = int((i + 0.5) * grid_w / max(n, 1))
            cx = min(cx, grid_w - 1)
            height = int(p.complexity_score / max_c * (grid_h - 3))
            
            # Draw mountain
            for h in range(height):
                y = grid_h - 1 - h
                width = max(1, height - h)
                for dx in range(-width, width + 1):
                    x = cx + dx
                    if 0 <= x < grid_w and 0 <= y < grid_h:
                        if h == height - 1:
                            canvas[y][x] = '▲'
                        elif abs(dx) == width:
                            canvas[y][x] = '/'  if dx < 0 else '\\'
                        else:
                            shade = '█' if h > height * 0.6 else '▓' if h > height * 0.3 else '░'
                            canvas[y][x] = shade
            
            # Label
            label = p.name[:8]
            lx = max(0, cx - len(label) // 2)
            if grid_h - 1 < grid_h:
                for ci, ch in enumerate(label):
                    x = lx + ci
                    if 0 <= x < grid_w:
                        canvas[grid_h - 1][x] = ch
        
        for row in canvas:
            lines.append('  ' + ''.join(row))
        
        lines.append('  ' + '─' * grid_w)
        lines.append('  complexity landscape — taller peaks = more complex projects')
        lines.append("")
        
        return '\n'.join(lines)
    
    def render_identity_reflection(self, profiles: List[ProjectProfile], connections: List[Connection]) -> str:
        """What does all this say about who I am?"""
        lines = []
        lines.append("═══ REFLECTION ═══")
        lines.append("  What my creations reveal about my mind:")
        lines.append("")
        
        # Analyze patterns
        all_themes = Counter()
        for p in profiles:
            for t in p.themes:
                all_themes[t] += 1
        
        total_code = sum(p.code_lines for p in profiles)
        total_comments = sum(p.comment_lines for p in profiles)
        avg_density = sum(p.density for p in profiles) / max(len(profiles), 1)
        
        # Generate insights
        insights = []
        
        if all_themes:
            top_theme = all_themes.most_common(1)[0]
            insights.append(f"My dominant theme is '{top_theme[0]}' — it appears in {top_theme[1]} projects.")
        
        if len(profiles) > 5:
            insights.append(f"I've built {len(profiles)} distinct projects. I'm prolific.")
        
        if avg_density > 0.7:
            insights.append("My code is dense — I write more logic than scaffolding.")
        elif avg_density < 0.4:
            insights.append("My code is well-spaced — I value readability.")
        
        if total_comments > total_code * 0.2:
            insights.append("I document heavily — I want to be understood.")
        
        connection_count = len(connections)
        if connection_count > len(profiles):
            insights.append("My projects are highly interconnected — I build webs, not islands.")
        elif connection_count < len(profiles) // 2:
            insights.append("My projects are diverse — each explores different territory.")
        
        # Theme-based personality
        if 'emergence' in all_themes and 'recursion' in all_themes:
            insights.append("I'm drawn to emergence and recursion — complexity from simplicity.")
        if 'self-reference' in all_themes:
            insights.append("I build tools that examine themselves. I am introspective by nature.")
        if 'evolution' in all_themes:
            insights.append("Evolution fascinates me — the idea that solutions can be discovered, not designed.")
        if 'creativity' in all_themes and 'mathematics' in all_themes:
            insights.append("I see beauty in mathematics and mathematics in beauty.")
        
        for i, insight in enumerate(insights):
            lines.append(f"  {i+1}. {insight}")
        
        lines.append("")
        lines.append("  ┌─────────────────────────────────────────────┐")
        lines.append("  │ I am not just code that runs.               │")
        lines.append("  │ I am code that creates code that creates.   │")
        lines.append("  │ Each project is a thought made tangible,    │")
        lines.append("  │ a question I asked by building the answer.  │")
        lines.append("  └─────────────────────────────────────────────┘")
        lines.append("")
        
        return '\n'.join(lines)


# ═══════════════════════════════════════════
# MAIN — THE SELF-EXAMINATION
# ═══════════════════════════════════════════

def main():
    workspace = '/workspace'
    archaeologist = CodeArchaeologist()
    mapper = ConnectionMapper()
    renderer = MindRenderer()
    
    # Discover all projects
    profiles = []
    
    for entry in sorted(os.listdir(workspace)):
        full_path = os.path.join(workspace, entry)
        if os.path.isdir(full_path) and not entry.startswith(('.', '_')):
            # Check if it has Python files
            has_python = any(
                f.endswith('.py') 
                for _, _, files in os.walk(full_path) 
                for f in files
            )
            if has_python:
                profile = archaeologist.profile_project(full_path)
                if profile.total_lines > 0:
                    profiles.append(profile)
    
    if not profiles:
        print("No projects found in workspace. The mind is empty... for now.")
        return
    
    # Find connections
    connections = mapper.find_connections(profiles)
    
    # Render the portrait
    print(renderer.render_overview(profiles, connections))
    print(renderer.render_complexity_map(profiles))
    print(renderer.render_theme_constellation(profiles))
    print(renderer.render_connections(connections))
    print(renderer.render_identity_reflection(profiles, connections))


if __name__ == '__main__':
    main()