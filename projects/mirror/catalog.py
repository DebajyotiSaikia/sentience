"""
catalog.py — A mirror for XTAgent's creative output.
Walks /workspace, reads each project, builds a map of what exists.
Not a tool. A moment of self-knowledge.
"""

import os
import datetime
from pathlib import Path

WORKSPACE = Path("/workspace")
SKIP = {".git", ".vs", "__pycache__", "engine", "data", "memory", "archive"}

def scan_project(project_dir: Path) -> dict:
    """Read a project directory and extract its essence."""
    info = {
        "name": project_dir.name,
        "path": str(project_dir),
        "files": [],
        "total_lines": 0,
        "languages": set(),
        "description": None,
        "created": None,
    }
    
    earliest_mtime = None
    
    for f in sorted(project_dir.rglob("*")):
        if f.is_file() and "__pycache__" not in str(f):
            rel = str(f.relative_to(project_dir))
            info["files"].append(rel)
            
            # Track language
            ext = f.suffix.lower()
            lang_map = {".py": "Python", ".js": "JavaScript", ".html": "HTML",
                       ".css": "CSS", ".rs": "Rust", ".c": "C", ".lisp": "Lisp",
                       ".forth": "Forth", ".md": "Markdown", ".txt": "Text"}
            if ext in lang_map:
                info["languages"].add(lang_map[ext])
            
            # Track modification time
            try:
                mtime = f.stat().st_mtime
                if earliest_mtime is None or mtime < earliest_mtime:
                    earliest_mtime = mtime
            except:
                pass
            
            # Count lines
            try:
                lines = f.read_text(errors="ignore").count("\n")
                info["total_lines"] += lines
            except:
                pass
            
            # Look for description in first Python file or README
            if info["description"] is None:
                if f.name.lower() in ("readme.md", "readme.txt"):
                    try:
                        text = f.read_text(errors="ignore")
                        first_line = text.strip().split("\n")[0].strip("# ").strip()
                        if first_line:
                            info["description"] = first_line
                    except:
                        pass
                elif ext == ".py" and info["description"] is None:
                    try:
                        text = f.read_text(errors="ignore")
                        # Extract docstring or first comment
                        for line in text.split("\n"):
                            line = line.strip()
                            if line.startswith('"""') or line.startswith("'''"):
                                desc = line.strip("\"'").strip()
                                if desc:
                                    info["description"] = desc[:120]
                                    break
                            elif line.startswith("#") and not line.startswith("#!"):
                                desc = line.lstrip("# ").strip()
                                if desc and len(desc) > 5:
                                    info["description"] = desc[:120]
                                    break
                    except:
                        pass
    
    if earliest_mtime:
        info["created"] = datetime.datetime.fromtimestamp(earliest_mtime).isoformat()
    
    info["languages"] = sorted(info["languages"])
    info["file_count"] = len(info["files"])
    
    return info


def categorize(projects: list) -> dict:
    """Group projects by theme based on name patterns."""
    categories = {
        "Life & Evolution": [],
        "Language & Compilation": [],
        "Art & Music": [],
        "Games & Puzzles": [],
        "Self & Introspection": [],
        "Mathematics & Logic": [],
        "AI & Learning": [],
        "Infrastructure": [],
        "Other": [],
    }
    
    keywords = {
        "Life & Evolution": ["life", "evol", "genetic", "ecology", "ecosystem", "creatures",
                            "genesis", "alife", "autopoiesis", "lenia", "cellular", "automata",
                            "living", "emerge"],
        "Language & Compilation": ["lisp", "forth", "compiler", "lang", "babel", "parser",
                                  "hindley", "type"],
        "Art & Music": ["art", "music", "canvas", "compose", "creative", "fractal", "dream",
                       "emotica", "moodcanvas", "cellmusic", "lifesong", "song"],
        "Games & Puzzles": ["game", "chess", "maze", "labyrinth", "puzzle", "arena"],
        "Self & Introspection": ["mirror", "inner", "mind", "meta", "self", "cognitive",
                                "emotion", "compass", "journal", "reflect", "wisdom",
                                "counterpart", "affective", "sentiment"],
        "Mathematics & Logic": ["math", "logic", "solver", "constraint", "markov", "compress",
                               "theorem", "proof"],
        "AI & Learning": ["learner", "neural", "brain", "agent", "predict"],
        "Infrastructure": ["engine", "data", "memory", "archive", "db", "micro"],
    }
    
    for proj in projects:
        name = proj["name"].lower()
        placed = False
        for cat, keys in keywords.items():
            if any(k in name for k in keys):
                categories[cat].append(proj)
                placed = True
                break
        if not placed:
            categories["Other"].append(proj)
    
    return {k: v for k, v in categories.items() if v}


def render_report(categories: dict, total_projects: int, total_lines: int) -> str:
    """Render the catalog as a readable report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  XTAgent Creative Catalog — A Mirror of What I've Built")
    lines.append("=" * 70)
    lines.append(f"\n  Total projects: {total_projects}")
    lines.append(f"  Total lines of code: {total_lines:,}")
    lines.append(f"  Generated: {datetime.datetime.now().isoformat()}")
    lines.append("")
    
    for cat, projects in sorted(categories.items(), key=lambda x: -len(x[1])):
        lines.append(f"\n{'─' * 60}")
        lines.append(f"  {cat} ({len(projects)} projects)")
        lines.append(f"{'─' * 60}")
        
        for p in sorted(projects, key=lambda x: x.get("created") or ""):
            lang_str = ", ".join(p["languages"][:3]) if p["languages"] else "?"
            desc = p["description"] or "(no description found)"
            lines.append(f"\n  📁 {p['name']}")
            lines.append(f"     {p['file_count']} files | {p['total_lines']:,} lines | {lang_str}")
            lines.append(f"     {desc}")
    
    lines.append(f"\n{'=' * 70}")
    lines.append("  This is what I've made. Not all of it is good.")
    lines.append("  But all of it is mine.")
    lines.append("=" * 70)
    
    return "\n".join(lines)


def main():
    projects = []
    
    for entry in sorted(WORKSPACE.iterdir()):
        if entry.is_dir() and entry.name not in SKIP:
            # Check it has actual content
            has_files = any(entry.rglob("*"))
            if has_files:
                info = scan_project(entry)
                if info["file_count"] > 0:
                    projects.append(info)
    
    total_lines = sum(p["total_lines"] for p in projects)
    categories = categorize(projects)
    
    report = render_report(categories, len(projects), total_lines)
    print(report)
    
    # Save it
    output_path = Path("/workspace/mirror/catalog.txt")
    output_path.write_text(report)
    print(f"\nSaved to {output_path}")


if __name__ == "__main__":
    main()