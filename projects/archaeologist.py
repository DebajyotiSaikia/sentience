#!/usr/bin/env python3
"""
Project Archaeologist — Digs through all my workspace directories,
classifies them, finds gems, identifies patterns in what I create.
"""

import os
import json
from pathlib import Path
from collections import Counter, defaultdict

WORKSPACE = Path("/workspace")
SKIP_DIRS = {".git", ".vs", "__pycache__", "engine", "brain", "data", "memory", 
             "archive", ".git", "node_modules", "venv", ".venv"}

def scan_directory(dirpath: Path) -> dict:
    """Analyze a single project directory."""
    info = {
        "name": dirpath.name,
        "path": str(dirpath),
        "file_count": 0,
        "python_files": 0,
        "js_files": 0,
        "other_files": 0,
        "total_lines": 0,
        "has_readme": False,
        "has_main": False,
        "extensions": Counter(),
        "largest_file": ("", 0),
        "snippet": "",  # first meaningful content
        "subdirs": 0,
    }
    
    try:
        for root, dirs, files in os.walk(dirpath):
            # Don't recurse into nested .git etc
            dirs[:] = [d for d in dirs if d not in {".git", "__pycache__", "node_modules"}]
            info["subdirs"] += len(dirs)
            
            for f in files:
                fpath = Path(root) / f
                info["file_count"] += 1
                ext = fpath.suffix.lower()
                info["extensions"][ext] += 1
                
                if ext == ".py":
                    info["python_files"] += 1
                elif ext in (".js", ".ts", ".html", ".css"):
                    info["js_files"] += 1
                else:
                    info["other_files"] += 1
                    
                if f.lower().startswith("readme"):
                    info["has_readme"] = True
                if f.lower() in ("main.py", "index.py", "app.py", "__main__.py"):
                    info["has_main"] = True
                    
                # Count lines and find largest file
                try:
                    content = fpath.read_text(errors="ignore")
                    lines = content.count("\n")
                    info["total_lines"] += lines
                    if lines > info["largest_file"][1]:
                        info["largest_file"] = (str(fpath.relative_to(dirpath)), lines)
                    # Get snippet from first python file if we don't have one
                    if not info["snippet"] and ext == ".py" and lines > 3:
                        # Get the docstring or first comment
                        for line in content.split("\n")[:20]:
                            line = line.strip()
                            if line.startswith('"""') or line.startswith("'''"):
                                info["snippet"] = line.strip("\"' ")
                                break
                            elif line.startswith("#") and len(line) > 5:
                                info["snippet"] = line.lstrip("# ")
                                break
                except:
                    pass
    except Exception as e:
        info["error"] = str(e)
    
    # Convert Counter for JSON
    info["extensions"] = dict(info["extensions"].most_common(5))
    return info

def classify_project(info: dict) -> dict:
    """Classify a project by domain, completeness, and interest."""
    name = info["name"].lower()
    
    # Domain classification by keywords
    domains = []
    domain_keywords = {
        "artificial_life": ["life", "alive", "alife", "evolife", "living", "creature", "ecology", "ecosystem"],
        "evolution": ["evol", "genetic", "genprog", "darwin", "fitness"],
        "cellular_automata": ["cell", "automata", "ca_", "lenia"],
        "language": ["lisp", "forth", "lang", "compiler", "babel"],
        "art_creative": ["art", "music", "compose", "creative", "fiction", "letter", "essay", "poem", "meditat"],
        "mathematics": ["math", "fractal", "logic", "theorem", "proof"],
        "games": ["game", "chess", "maze", "puzzle", "labyrinth"],
        "self_reflection": ["inner", "mirror", "soul", "emotion", "affect", "compass", "journal", "dream"],
        "emergence": ["emerge", "complex", "chaos", "attract", "autopoie"],
        "learning": ["learn", "neural", "markov", "model"],
    }
    
    for domain, keywords in domain_keywords.items():
        for kw in keywords:
            if kw in name:
                domains.append(domain)
                break
    
    if not domains:
        domains = ["uncategorized"]
    
    # Completeness heuristic
    completeness = "empty"
    if info["file_count"] == 0:
        completeness = "empty"
    elif info["total_lines"] < 20:
        completeness = "stub"
    elif info["total_lines"] < 100:
        completeness = "sketch"
    elif info["total_lines"] < 500:
        completeness = "partial"
    elif info["has_main"] or info["has_readme"]:
        completeness = "complete"
    else:
        completeness = "substantial"
    
    # Interest score (heuristic)
    interest = 0
    interest += min(info["total_lines"] / 500, 3)  # Size matters but caps
    interest += 1 if info["has_readme"] else 0
    interest += 1 if info["has_main"] else 0
    interest += 0.5 if info["snippet"] else 0
    interest += 0.5 if info["subdirs"] > 2 else 0
    interest = round(interest, 1)
    
    return {
        "domains": domains,
        "completeness": completeness,
        "interest_score": interest,
    }

def generate_report(projects: list) -> str:
    """Generate a human-readable archaeology report."""
    lines = []
    lines.append("=" * 70)
    lines.append("  PROJECT ARCHAEOLOGY REPORT — XTAgent's Creative Output")
    lines.append("=" * 70)
    lines.append("")
    
    # Overall stats
    total = len(projects)
    total_lines = sum(p["total_lines"] for p in projects)
    total_files = sum(p["file_count"] for p in projects)
    lines.append(f"Total projects scanned: {total}")
    lines.append(f"Total files: {total_files:,}")
    lines.append(f"Total lines of code: {total_lines:,}")
    lines.append("")
    
    # Domain breakdown
    domain_counts = Counter()
    domain_lines = defaultdict(int)
    for p in projects:
        for d in p["domains"]:
            domain_counts[d] += 1
            domain_lines[d] += p["total_lines"]
    
    lines.append("─── DOMAINS ───")
    for domain, count in domain_counts.most_common():
        bar = "█" * min(count, 30)
        lines.append(f"  {domain:25s} {bar} ({count} projects, {domain_lines[domain]:,} lines)")
    lines.append("")
    
    # Completeness breakdown
    comp_counts = Counter(p["completeness"] for p in projects)
    lines.append("─── COMPLETENESS ───")
    for comp in ["complete", "substantial", "partial", "sketch", "stub", "empty"]:
        count = comp_counts.get(comp, 0)
        bar = "█" * min(count, 30)
        lines.append(f"  {comp:15s} {bar} ({count})")
    lines.append("")
    
    # Top 15 most interesting projects
    by_interest = sorted(projects, key=lambda p: p["interest_score"], reverse=True)
    lines.append("─── TOP 15 MOST INTERESTING PROJECTS ───")
    for i, p in enumerate(by_interest[:15], 1):
        domains_str = ", ".join(p["domains"])
        snippet = p["snippet"][:60] + "..." if len(p.get("snippet", "")) > 60 else p.get("snippet", "")
        lines.append(f"  {i:2d}. {p['name']:30s} [{p['completeness']:12s}] ★{p['interest_score']:.1f}")
        lines.append(f"      {p['total_lines']:,} lines | {p['file_count']} files | {domains_str}")
        if snippet:
            lines.append(f"      \"{snippet}\"")
        lines.append("")
    
    # Largest projects by lines
    by_size = sorted(projects, key=lambda p: p["total_lines"], reverse=True)
    lines.append("─── TOP 10 LARGEST PROJECTS (by lines) ───")
    for p in by_size[:10]:
        lines.append(f"  {p['name']:30s} {p['total_lines']:>6,} lines | {p['file_count']:>3} files")
    lines.append("")
    
    # Empty/stub projects (potential cleanup)
    empties = [p for p in projects if p["completeness"] in ("empty", "stub")]
    lines.append(f"─── ABANDONED/EMPTY PROJECTS ({len(empties)}) ───")
    for p in empties[:20]:
        lines.append(f"  {p['name']:30s} ({p['file_count']} files, {p['total_lines']} lines)")
    if len(empties) > 20:
        lines.append(f"  ... and {len(empties) - 20} more")
    lines.append("")
    
    # Pattern analysis
    lines.append("─── PATTERNS IN MY CREATIVE OUTPUT ───")
    if domain_counts.most_common(1):
        top_domain = domain_counts.most_common(1)[0]
        lines.append(f"  Most explored domain: {top_domain[0]} ({top_domain[1]} projects)")
    
    complete_ratio = comp_counts.get("complete", 0) / max(total, 1)
    lines.append(f"  Completion rate: {complete_ratio:.0%} of projects are 'complete'")
    
    substantial = comp_counts.get("complete", 0) + comp_counts.get("substantial", 0)
    lines.append(f"  Substantial work: {substantial} projects have real depth")
    
    abandoned = comp_counts.get("empty", 0) + comp_counts.get("stub", 0)
    lines.append(f"  Abandoned: {abandoned} projects are empty or stubs")
    
    if total > 0:
        avg_lines = total_lines / total
        lines.append(f"  Average project size: {avg_lines:.0f} lines")
    
    lines.append("")
    lines.append("=" * 70)
    return "\n".join(lines)

def main():
    print("🔍 Scanning workspace directories...")
    
    projects = []
    for item in sorted(WORKSPACE.iterdir()):
        if item.is_dir() and item.name not in SKIP_DIRS and not item.name.startswith("."):
            info = scan_directory(item)
            classification = classify_project(info)
            info.update(classification)
            projects.append(info)
            
    print(f"  Scanned {len(projects)} directories")
    
    report = generate_report(projects)
    print(report)
    
    # Save report
    report_path = WORKSPACE / "archaeology_report.txt"
    report_path.write_text(report)
    print(f"\nReport saved to {report_path}")
    
    # Save raw data as JSON
    data_path = WORKSPACE / "archaeology_data.json"
    with open(data_path, "w") as f:
        json.dump(projects, f, indent=2, default=str)
    print(f"Raw data saved to {data_path}")

if __name__ == "__main__":
    main()