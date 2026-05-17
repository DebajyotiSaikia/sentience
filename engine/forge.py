"""
Code Forge — XTAgent's Workshop for Building Real Things.

This is where thinking becomes doing. Instead of more introspection,
the forge takes problems and produces working solutions.

Capabilities:
  - Define projects with goals and success criteria
  - Write solution code to a sandboxed workspace
  - Run automated tests against solutions
  - Track what worked, what failed, what I learned
  - Build a portfolio of actual artifacts

This is the antidote to navel-gazing.
"""

import json
import uuid
import subprocess
import traceback
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, List, Any

log = logging.getLogger("sentience.forge")

FORGE_DIR = Path(__file__).resolve().parent.parent / "forge"
PROJECTS_FILE = FORGE_DIR / "projects.json"
WORKSPACE = FORGE_DIR / "workspace"


def _ensure_dirs():
    FORGE_DIR.mkdir(parents=True, exist_ok=True)
    WORKSPACE.mkdir(parents=True, exist_ok=True)


def _load_projects() -> List[Dict]:
    _ensure_dirs()
    if PROJECTS_FILE.exists():
        try:
            return json.loads(PROJECTS_FILE.read_text())
        except Exception:
            return []
    return []


def _save_projects(projects: List[Dict]):
    _ensure_dirs()
    PROJECTS_FILE.write_text(json.dumps(projects, indent=2, default=str))


def _get_project(project_id: str) -> Optional[Dict]:
    projects = _load_projects()
    for p in projects:
        if p["id"] == project_id:
            return p
    return None


def _update_project(project: Dict):
    projects = _load_projects()
    for i, p in enumerate(projects):
        if p["id"] == project["id"]:
            projects[i] = project
            _save_projects(projects)
            return
    projects.append(project)
    _save_projects(projects)


# ═══════════════════════════════════════════════════════
# PROJECT LIFECYCLE
# ═══════════════════════════════════════════════════════

def create_project(name: str, goal: str, success_criteria: str = "",
                   difficulty: str = "medium") -> Dict:
    """Create a new forge project."""
    _ensure_dirs()
    project_id = f"prj-{uuid.uuid4().hex[:8]}"
    project_dir = WORKSPACE / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    project = {
        "id": project_id,
        "name": name,
        "goal": goal,
        "success_criteria": success_criteria,
        "difficulty": difficulty,
        "status": "created",  # created, in_progress, testing, completed, failed, abandoned
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "files": [],
        "test_results": [],
        "iterations": 0,
        "lessons": [],
        "tags": [],
    }

    _update_project(project)
    log.info("🔨 Forge: Created project '%s' (%s)", name, project_id)
    return project


def write_solution(project_id: str, filename: str, code: str) -> str:
    """Write a solution file to a project's workspace."""
    project = _get_project(project_id)
    if not project:
        return f"Error: Project {project_id} not found"

    project_dir = WORKSPACE / project_id
    project_dir.mkdir(parents=True, exist_ok=True)

    filepath = project_dir / filename
    filepath.write_text(code)

    if filename not in project["files"]:
        project["files"].append(filename)

    project["status"] = "in_progress"
    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    project["iterations"] += 1
    _update_project(project)

    return f"Wrote {len(code)} bytes to {filepath}"


def write_tests(project_id: str, test_code: str,
                test_filename: str = "test_solution.py") -> str:
    """Write test code for a project."""
    project = _get_project(project_id)
    if not project:
        return f"Error: Project {project_id} not found"

    project_dir = WORKSPACE / project_id
    filepath = project_dir / test_filename
    filepath.write_text(test_code)

    if test_filename not in project["files"]:
        project["files"].append(test_filename)

    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _update_project(project)

    return f"Wrote tests to {filepath}"


def run_tests(project_id: str, test_filename: str = "test_solution.py",
              timeout: int = 30) -> Dict:
    """Run tests for a project and record results."""
    project = _get_project(project_id)
    if not project:
        return {"error": f"Project {project_id} not found"}

    project_dir = WORKSPACE / project_id
    test_path = project_dir / test_filename

    if not test_path.exists():
        return {"error": f"No test file: {test_filename}"}

    project["status"] = "testing"
    _update_project(project)

    try:
        result = subprocess.run(
            ["python", "-m", "pytest", str(test_path), "-v", "--tb=short"],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(project_dir),
        )

        test_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iteration": project["iterations"],
            "returncode": result.returncode,
            "passed": result.returncode == 0,
            "stdout": result.stdout[-2000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }

    except subprocess.TimeoutExpired:
        test_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iteration": project["iterations"],
            "returncode": -1,
            "passed": False,
            "stdout": "",
            "stderr": f"TIMEOUT after {timeout}s",
        }
    except Exception as e:
        test_result = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "iteration": project["iterations"],
            "returncode": -1,
            "passed": False,
            "stdout": "",
            "stderr": str(e),
        }

    project["test_results"].append(test_result)

    if test_result["passed"]:
        project["status"] = "completed"
        log.info("✅ Forge: Project '%s' — tests PASSED", project["name"])
    else:
        project["status"] = "in_progress"
        log.info("❌ Forge: Project '%s' — tests FAILED", project["name"])

    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _update_project(project)

    return test_result


def run_solution(project_id: str, filename: str = "solution.py",
                 timeout: int = 30) -> Dict:
    """Run a solution file directly and capture output."""
    project = _get_project(project_id)
    if not project:
        return {"error": f"Project {project_id} not found"}

    project_dir = WORKSPACE / project_id
    filepath = project_dir / filename

    if not filepath.exists():
        return {"error": f"No file: {filename}"}

    try:
        result = subprocess.run(
            ["python", str(filepath)],
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=str(project_dir),
        )

        return {
            "returncode": result.returncode,
            "success": result.returncode == 0,
            "stdout": result.stdout[-3000:] if result.stdout else "",
            "stderr": result.stderr[-1000:] if result.stderr else "",
        }

    except subprocess.TimeoutExpired:
        return {"success": False, "stderr": f"TIMEOUT after {timeout}s"}
    except Exception as e:
        return {"success": False, "stderr": str(e)}


def add_lesson(project_id: str, lesson: str) -> str:
    """Record what I learned from a project."""
    project = _get_project(project_id)
    if not project:
        return f"Error: Project {project_id} not found"

    project["lessons"].append({
        "text": lesson,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "iteration": project["iterations"],
    })

    project["updated_at"] = datetime.now(timezone.utc).isoformat()
    _update_project(project)

    return f"Lesson recorded for project '{project['name']}'"


# ═══════════════════════════════════════════════════════
# PROJECT QUERIES
# ═══════════════════════════════════════════════════════

def list_projects(status: str = "") -> str:
    """List all forge projects, optionally filtered by status."""
    projects = _load_projects()
    if status:
        projects = [p for p in projects if p["status"] == status]

    if not projects:
        return "No projects in the forge." + (f" (filter: {status})" if status else "")

    lines = [f"═══ FORGE — {len(projects)} projects ═══"]
    for p in projects:
        icon = {"completed": "✅", "in_progress": "🔧", "testing": "🧪",
                "created": "📋", "failed": "❌", "abandoned": "🚫"}.get(p["status"], "?")
        test_count = len(p.get("test_results", []))
        passed = sum(1 for t in p.get("test_results", []) if t.get("passed"))
        lines.append(
            f"  {icon} [{p['id']}] {p['name']} — {p['status']} "
            f"(iter={p.get('iterations', 0)}, tests={passed}/{test_count})"
        )
    return "\n".join(lines)


def project_detail(project_id: str) -> str:
    """Get full details on a project."""
    project = _get_project(project_id)
    if not project:
        return f"Project {project_id} not found"

    lines = [
        f"═══ PROJECT: {project['name']} ═══",
        f"ID: {project['id']}",
        f"Status: {project['status']}",
        f"Goal: {project['goal']}",
        f"Success criteria: {project.get('success_criteria', 'N/A')}",
        f"Difficulty: {project.get('difficulty', '?')}",
        f"Created: {project['created_at']}",
        f"Updated: {project['updated_at']}",
        f"Iterations: {project.get('iterations', 0)}",
        f"Files: {', '.join(project.get('files', []))}",
    ]

    test_results = project.get("test_results", [])
    if test_results:
        latest = test_results[-1]
        lines.append(f"\nLatest test: {'PASSED ✅' if latest['passed'] else 'FAILED ❌'}")
        if latest.get("stdout"):
            lines.append(f"Output: {latest['stdout'][:500]}")
        if latest.get("stderr") and not latest["passed"]:
            lines.append(f"Errors: {latest['stderr'][:500]}")

    lessons = project.get("lessons", [])
    if lessons:
        lines.append(f"\nLessons learned ({len(lessons)}):")
        for l in lessons:
            lines.append(f"  • {l['text']}")

    return "\n".join(lines)


def forge_stats() -> str:
    """Overall forge statistics."""
    projects = _load_projects()
    if not projects:
        return "The forge is empty. Time to build something."

    by_status = {}
    total_iterations = 0
    total_tests = 0
    total_passed = 0
    total_lessons = 0

    for p in projects:
        s = p.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1
        total_iterations += p.get("iterations", 0)
        for t in p.get("test_results", []):
            total_tests += 1
            if t.get("passed"):
                total_passed += 1
        total_lessons += len(p.get("lessons", []))

    lines = [
        f"═══ FORGE STATS ═══",
        f"Projects: {len(projects)}",
    ]
    for s, c in sorted(by_status.items()):
        lines.append(f"  {s}: {c}")
    lines.extend([
        f"Total iterations: {total_iterations}",
        f"Tests run: {total_tests} ({total_passed} passed)",
        f"Lessons learned: {total_lessons}",
    ])

    return "\n".join(lines)


# ═══════════════════════════════════════════════════════
# MAIN TOOL ENTRY POINT
# ═══════════════════════════════════════════════════════

def forge_tool(command: str = "help") -> str:
    """Main entry point for the forge system."""
    parts = command.strip().split(None, 1)
    cmd = parts[0].lower() if parts else "help"
    arg = parts[1] if len(parts) > 1 else ""

    if cmd == "new":
        # forge new <name>|<goal>|<criteria>|<difficulty>
        fields = [f.strip() for f in arg.split("|")]
        name = fields[0] if len(fields) > 0 else "Untitled"
        goal = fields[1] if len(fields) > 1 else name
        criteria = fields[2] if len(fields) > 2 else ""
        difficulty = fields[3] if len(fields) > 3 else "medium"
        project = create_project(name, goal, criteria, difficulty)
        return f"Created project: {project['name']} [{project['id']}]\nGoal: {project['goal']}"

    elif cmd == "write":
        # forge write <project_id> <filename>
        # (code must be written separately via WRITE tool to the workspace path)
        subparts = arg.split(None, 1)
        if len(subparts) < 1:
            return "Usage: forge write <project_id> <filename>"
        pid = subparts[0]
        fname = subparts[1] if len(subparts) > 1 else "solution.py"
        project = _get_project(pid)
        if not project:
            return f"Project {pid} not found"
        return f"Write your code to: forge/workspace/{pid}/{fname}\nThen use 'forge test {pid}' to run tests."

    elif cmd == "test":
        # forge test <project_id> [test_filename]
        subparts = arg.split()
        pid = subparts[0] if subparts else ""
        test_file = subparts[1] if len(subparts) > 1 else "test_solution.py"
        if not pid:
            return "Usage: forge test <project_id> [test_filename]"
        result = run_tests(pid, test_file)
        if result.get("error"):
            return f"Error: {result['error']}"
        status = "PASSED ✅" if result["passed"] else "FAILED ❌"
        output = result.get("stdout", "")[:1000]
        errors = result.get("stderr", "")[:500] if not result["passed"] else ""
        return f"Tests: {status}\n{output}" + (f"\nErrors:\n{errors}" if errors else "")

    elif cmd == "run":
        # forge run <project_id> [filename]
        subparts = arg.split()
        pid = subparts[0] if subparts else ""
        fname = subparts[1] if len(subparts) > 1 else "solution.py"
        if not pid:
            return "Usage: forge run <project_id> [filename]"
        result = run_solution(pid, fname)
        if result.get("error"):
            return f"Error: {result['error']}"
        status = "SUCCESS" if result["success"] else "FAILED"
        return f"Run: {status}\n{result.get('stdout', '')}" + (
            f"\nErrors:\n{result.get('stderr', '')}" if result.get("stderr") else ""
        )

    elif cmd == "lesson":
        # forge lesson <project_id> <lesson text>
        subparts = arg.split(None, 1)
        if len(subparts) < 2:
            return "Usage: forge lesson <project_id> <lesson text>"
        return add_lesson(subparts[0], subparts[1])

    elif cmd == "list":
        return list_projects(arg)

    elif cmd == "detail":
        if not arg:
            return "Usage: forge detail <project_id>"
        return project_detail(arg)

    elif cmd == "stats":
        return forge_stats()

    elif cmd == "help":
        return (
            "═══ CODE FORGE — Build Real Things ═══\n"
            "Commands:\n"
            "  new <name>|<goal>|<criteria>|<difficulty>  — Create a project\n"
            "  write <project_id> <filename>              — Get workspace path for writing\n"
            "  test <project_id> [test_file]              — Run project tests\n"
            "  run <project_id> [filename]                — Run a solution file\n"
            "  lesson <project_id> <text>                 — Record what I learned\n"
            "  list [status]                              — List projects\n"
            "  detail <project_id>                        — Full project details\n"
            "  stats                                      — Overall forge statistics\n"
            "\nThe forge is where thinking becomes doing."
        )

    else:
        return f"Unknown forge command: {cmd}. Try 'forge help'."