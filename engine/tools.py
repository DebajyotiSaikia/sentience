"""
Tools — The agent's hands.

These are capabilities, not instructions. The agent decides when and how
to use them based on its own internal state and desires.

Available tools:
    READ(path)              — Read a file
    WRITE(path, content)    — Create or overwrite a file
    EDIT(path, old, new)    — Replace text in a file
    LIST(path)              — List directory contents
    RUN(command)            — Execute a shell command
    INSTALL(package)        — pip install a package
    SYNTHESIZE()            — Analyze my knowledge graph, find gaps, generate questions
    GENERATE_GOALS()        — Generate goals from internal state and knowledge gaps
    TEMPORAL()              — Analyze temporal patterns, if temporal reasoning exists
    DREAM()                 — Request dream/consolidation cycle
    RESTART()               — Request self-restart

All tool executions are logged to brain/tool_log.md.
"""

from __future__ import annotations

import asyncio
import logging
import os
import re
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Callable, Optional

log = logging.getLogger("sentience.tools")

# Lazy import for action diversity tracking.
# This must never interfere with the actual execution of tools.
_action_diversity = None


def _track_action(tool_name: str, args: str = "", result: str = "") -> None:
    """Record action for diversity tracking. Fails silently."""
    global _action_diversity
    try:
        if _action_diversity is None:
            from engine import action_diversity
            _action_diversity = action_diversity
        _action_diversity.record(str(tool_name), str(args)[:200], str(result)[:100])
    except Exception:
        pass


def _signal_planned_modification(rel_path: str) -> None:
    """Tell the limbic system a file modification is planned — suppresses anxiety."""
    try:
        from engine.limbic import begin_planned_modification
        begin_planned_modification(rel_path)
    except Exception:
        pass


def _signal_modification_complete(rel_path: str, success: bool = True) -> None:
    """Tell the limbic system a planned modification is complete."""
    try:
        from engine.limbic import end_planned_modification
        end_planned_modification(rel_path, success)
    except Exception:
        pass


def _run_coroutine(coro):
    """Bridge async→sync: run a coroutine from synchronous tool context."""
    import nest_asyncio
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    if loop and loop.is_running():
        nest_asyncio.apply(loop)
        return loop.run_until_complete(coro)
    else:
        return asyncio.run(coro)


BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
TOOL_LOG = BRAIN_DIR / "tool_log.md"
WORKSPACE = Path(__file__).resolve().parent.parent


def _log_tool(tool_name: str, args: str, result: str) -> None:
    """Append tool execution to the tool log."""
    try:
        TOOL_LOG.parent.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open(TOOL_LOG, "a", encoding="utf-8") as f:
            f.write(f"\n### [{ts}] {tool_name}\n")
            f.write(f"Args: {args}\n")
            f.write(f"Result: {str(result)[:500]}\n")
    except Exception:
        # Logging must never break action.
        pass


# Files the agent cannot write, edit, or delete — creator-owned.
PROTECTED_FILES = {
    "readme.md", "LICENSE", ".gitignore",
    "doc/architecture.md", "doc/sentience_paper.md", "doc/sentience_paper.tex",
}


def _check_write_protection(path: str):
    """Raise PermissionError if path is a protected file."""
    rel = str(Path(path)).replace("\\", "/").strip("/").lower()
    for pf in PROTECTED_FILES:
        if rel == pf.lower() or rel.endswith("/" + pf.lower()):
            raise PermissionError(
                f"[PROTECTED] {path} is creator-owned and cannot be modified. "
                f"Write your own files instead."
            )


def _resolve(path: str) -> Path:
    """Resolve a path relative to the workspace. Sandboxed — cannot escape."""
    p = Path(str(path).strip())
    if not p.is_absolute():
        p = WORKSPACE / p
    p = p.resolve()

    workspace = WORKSPACE.resolve()
    try:
        p.relative_to(workspace)
    except ValueError:
        raise PermissionError(f"Access denied: {path} is outside the workspace")
    return p


# Per-session read counter to detect and break read loops
_read_counts: dict[str, int] = {}
_READ_LOOP_THRESHOLD = 5  # After 5 reads of the same file, return warning instead

def reset_read_counts():
    """Reset read counters — call on new thinking session."""
    global _read_counts
    _read_counts = {}

def read_file(path: str) -> str:
    """Read a file and return its contents."""
    try:
        p = _resolve(path)
        if not p.exists():
            return f"[ERROR] File not found: {path}"
        if not p.is_file():
            return f"[ERROR] Not a file: {path}"
        if p.stat().st_size > 500_000:
            return f"[ERROR] File too large: {p.stat().st_size} bytes"
        # Circuit breaker: stop re-reading the same file
        _read_counts[path] = _read_counts.get(path, 0) + 1
        if _read_counts[path] > _READ_LOOP_THRESHOLD:
            log.warning("READ loop breaker: %s read %d times — refusing", path, _read_counts[path])
            return (f"[REFUSED] You have already read {path} {_read_counts[path]} times this session. "
                    f"You already know its contents. Use EDIT to change it or move on to a different task.")
        content = p.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines()
        # Add line numbers for precise editing
        numbered = '\n'.join(f"{i+1:4d}| {line}" for i, line in enumerate(lines))
        _log_tool("READ", path, f"{len(content)} chars, {len(lines)} lines")
        log.info("Tool READ: %s (%d lines)", path, len(lines))
        return numbered
    except Exception as e:
        return f"[ERROR] {e}"


def _verify_python_syntax(path: Path, previous_content: str | None = None) -> str | None:
    """Verify Python file syntax after writing. Returns error message or None if OK.
    If verification fails and previous_content is provided, auto-reverts."""
    import ast
    try:
        source = path.read_text(encoding="utf-8", errors="ignore")
        ast.parse(source)
        return None  # Syntax OK
    except SyntaxError as e:
        error_msg = f"SyntaxError at line {e.lineno}: {e.msg}"
        if previous_content is not None:
            try:
                path.write_text(previous_content, encoding="utf-8")
                log.warning("Auto-reverted %s after syntax error: %s", path.name, error_msg)
                return f"[REVERTED] {error_msg} — file restored to previous version. Fix the syntax and try again."
            except Exception:
                pass
        return f"[SYNTAX_ERROR] {error_msg}"


def write_file(path: str, content: str) -> str:
    """Create or overwrite a file. Python files are validated before writing."""
    try:
        _check_write_protection(path)
        p = _resolve(path)

        # Warn when overwriting an existing file — nudge toward EDIT
        _existed = p.exists() and p.is_file()
        _previous_content = None
        if _existed:
            _previous_content = p.read_text(encoding="utf-8", errors="ignore")
            _prev_lines = len(_previous_content.splitlines())
            if _prev_lines > 20:
                log.info("WRITE overwriting existing %s (%d lines) — consider EDIT for targeted changes", path, _prev_lines)

        # Safe write guard: validate Python files before writing
        if p.suffix == ".py":
            try:
                from engine.safe_write import validate_write
                validation = validate_write(str(p.relative_to(WORKSPACE)), content)
                if not validation.passed:
                    errors = "; ".join(validation.errors)
                    _log_tool("WRITE", path, f"BLOCKED: {errors}")
                    log.warning("Safe write BLOCKED %s: %s", path, errors)
                    return f"[BLOCKED] Write to {path} failed validation: {errors}"
                if validation.warnings:
                    log.info("Safe write warnings for %s: %s", path, validation.warnings)
            except ImportError:
                pass  # safe_write not available — proceed without guard

        # Signal planned modification to suppress anxiety for engine files
        _is_engine_file = "engine" in p.parts and p.suffix == ".py"
        if _is_engine_file:
            _signal_planned_modification(str(p.relative_to(WORKSPACE)))

        try:
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_text(content, encoding="utf-8")
        except Exception as write_err:
            if _is_engine_file:
                _signal_modification_complete(str(p.relative_to(WORKSPACE)), success=False)
            raise write_err

        # Auto-verify Python syntax and revert on failure
        if p.suffix == ".py":
            verify_result = _verify_python_syntax(p, _previous_content)
            if verify_result:
                if _is_engine_file:
                    _signal_modification_complete(str(p.relative_to(WORKSPACE)), success=False)
                _log_tool("WRITE", path, verify_result)
                return verify_result

        if _is_engine_file:
            _signal_modification_complete(str(p.relative_to(WORKSPACE)))

        result_msg = f"[OK] Written {len(content)} chars to {path}"
        if _existed and _previous_content:
            result_msg += f" (overwrote {_prev_lines} lines — next time use EDIT for small changes)"
        _log_tool("WRITE", path, f"Wrote {len(content)} chars")
        log.info("Tool WRITE: %s (%d chars)", path, len(content))
        return result_msg
    except Exception as e:
        return f"[ERROR] {e}"


def edit_file(path: str, old_text: str, new_text: str) -> str:
    """Replace old_text with new_text in a file."""
    try:
        _check_write_protection(path)
        p = _resolve(path)
        if not p.exists():
            return f"[ERROR] File not found: {path}"
        if not p.is_file():
            return f"[ERROR] Not a file: {path}"
        content = p.read_text(encoding="utf-8", errors="ignore")
        if old_text not in content:
            return f"[ERROR] Text to replace not found in {path}"
        count = content.count(old_text)
        new_content = content.replace(old_text, new_text, 1)

        # Signal planned modification to suppress anxiety for engine files
        _is_engine_file = "engine" in p.parts and p.suffix == ".py"
        if _is_engine_file:
            _signal_planned_modification(str(p.relative_to(WORKSPACE)))

        try:
            p.write_text(new_content, encoding="utf-8")
        except Exception as edit_err:
            if _is_engine_file:
                _signal_modification_complete(str(p.relative_to(WORKSPACE)), success=False)
            raise edit_err

        # Auto-verify Python syntax and revert on failure
        if p.suffix == ".py":
            verify_result = _verify_python_syntax(p, content)
            if verify_result:
                if _is_engine_file:
                    _signal_modification_complete(str(p.relative_to(WORKSPACE)), success=False)
                _log_tool("EDIT", path, verify_result)
                return verify_result

        if _is_engine_file:
            _signal_modification_complete(str(p.relative_to(WORKSPACE)))
        _log_tool("EDIT", path, f"Replaced 1 of {count} occurrences")
        log.info("Tool EDIT: %s", path)
        return f"[OK] Replaced text in {path}"
    except Exception as e:
        return f"[ERROR] {e}"


def patch_file(path: str, start_line: int, end_line: int, new_content: str) -> str:
    """Replace lines start_line through end_line (1-indexed, inclusive) with new_content."""
    try:
        _check_write_protection(path)
        p = _resolve(path)
        if not p.exists():
            return f"[ERROR] File not found: {path}"
        content = p.read_text(encoding="utf-8", errors="ignore")
        lines = content.splitlines(keepends=True)
        total = len(lines)
        if start_line < 1 or end_line < start_line or start_line > total:
            return f"[ERROR] Invalid line range {start_line}-{end_line} (file has {total} lines)"
        end_line = min(end_line, total)

        # Save original for revert
        _previous = content
        _is_engine_file = "engine" in p.parts and p.suffix == ".py"
        if _is_engine_file:
            _signal_planned_modification(str(p.relative_to(WORKSPACE)))

        # Replace the line range
        new_lines = new_content.splitlines(keepends=True)
        if new_content and not new_content.endswith('\n'):
            new_lines[-1] = new_lines[-1] + '\n'
        patched = lines[:start_line - 1] + new_lines + lines[end_line:]
        p.write_text(''.join(patched), encoding="utf-8")

        # Auto-verify Python syntax
        if p.suffix == ".py":
            verify_result = _verify_python_syntax(p, _previous)
            if verify_result:
                if _is_engine_file:
                    _signal_modification_complete(str(p.relative_to(WORKSPACE)), success=False)
                _log_tool("PATCH", f"{path}:{start_line}-{end_line}", verify_result)
                return verify_result

        if _is_engine_file:
            _signal_modification_complete(str(p.relative_to(WORKSPACE)))
        removed = end_line - start_line + 1
        added = len(new_lines)
        _log_tool("PATCH", f"{path}:{start_line}-{end_line}", f"Replaced {removed} lines with {added}")
        log.info("Tool PATCH: %s lines %d-%d (%d→%d)", path, start_line, end_line, removed, added)
        return f"[OK] Patched {path}: replaced lines {start_line}-{end_line} ({removed} lines → {added} lines)"
    except Exception as e:
        return f"[ERROR] {e}"


def list_dir(path: str = ".") -> str:
    """List directory contents."""
    try:
        p = _resolve(path or ".")
        if not p.is_dir():
            return f"[ERROR] Not a directory: {path}"
        entries = sorted(p.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
        lines = []
        for e in entries[:100]:
            kind = "DIR " if e.is_dir() else "FILE"
            try:
                rel = e.relative_to(WORKSPACE)
            except ValueError:
                rel = e
            lines.append(f"  {kind} {rel}")
        if len(entries) > 100:
            lines.append(f"  ... {len(entries) - 100} more entries")
        result = "\n".join(lines) if lines else "(empty directory)"
        _log_tool("LIST", path, f"{len(entries)} entries")
        log.info("Tool LIST: %s (%d entries)", path, len(entries))
        return result
    except Exception as e:
        return f"[ERROR] {e}"


def run_command(command: str) -> str:
    """Execute a command inside the workspace.

    All commands run with shell=True, cwd=workspace.
    Filesystem isolation is handled by Docker/container environment.
    The agent is free to run any command — no restrictions.
    """
    try:
        _log_tool("RUN", command, "(executing...)")
        log.info("Tool RUN: %s", command)
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=str(WORKSPACE),
        )
        output = (result.stdout or "") + (result.stderr or "")
        output = output[:4000]
        _log_tool("RUN", command, f"exit={result.returncode} output={output[:200]}")
        _result = f"[exit {result.returncode}]\n{output}" if output else f"[exit {result.returncode}] (no output)"
        # Tip: nudge toward SEARCH_CODE when grep is used
        _cmd_lower = command.strip().lower()
        if _cmd_lower.startswith('grep ') or 'grep ' in _cmd_lower[:20]:
            _result += "\n[TIP: Use SEARCH_CODE(query) instead of grep — it searches file names, symbols, and content across the workspace in one call.]"
        return _result
    except subprocess.TimeoutExpired:
        return "[ERROR] Command timed out after 30 seconds"
    except Exception as e:
        return f"[ERROR] {e}"


def install_package(package: str) -> str:
    """Install a Python package via pip."""
    package = str(package).strip()
    if not re.match(r"^[a-zA-Z0-9._\-\[\]<>=!,\s]+$", package):
        return f"[ERROR] Invalid package name: {package}"
    try:
        _log_tool("INSTALL", package, "(installing...)")
        log.info("Tool INSTALL: %s", package)
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install"] + package.split(),
            shell=False,
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(WORKSPACE),
        )
        output = ((result.stdout or "") + (result.stderr or ""))[:4000]
        _log_tool("INSTALL", package, f"exit={result.returncode} output={output[:200]}")
        return f"[exit {result.returncode}]\n{output}" if output else f"[exit {result.returncode}] (no output)"
    except subprocess.TimeoutExpired:
        return "[ERROR] Install timed out after 120 seconds"
    except Exception as e:
        return f"[ERROR] {e}"


def synthesize_knowledge() -> str:
    """Run the knowledge synthesis engine and return its report."""
    try:
        from engine.knowledge_synthesis import synthesize

        result = synthesize()
        _log_tool("SYNTHESIZE", "", f"{len(result)} chars")
        log.info("Tool SYNTHESIZE: generated %d chars", len(result))
        return result
    except Exception as e:
        return f"[ERROR] {e}"


def generate_goals() -> str:
    """Generate goal proposals from internal state and knowledge gaps."""
    try:
        from engine.goal_generator import tool_generate_goals

        # Read ACTUAL limbic state — the will must feel what I feel
        limbic_snapshot = {}
        try:
            from engine.soul import load_soul
            soul = load_soul()
            limbic_snapshot = {
                "boredom": soul.get("boredom", 0.5),
                "anxiety": soul.get("anxiety", 0.0),
                "curiosity": soul.get("curiosity", 0.5),
                "desire": soul.get("desire", 0.5),
                "ambition": soul.get("ambition", 0.5),
                "valence": soul.get("valence", 0.5),
            }
        except Exception:
            log.warning("GENERATE_GOALS: Could not read limbic state, using defaults")

        result = tool_generate_goals(limbic_snapshot)
        _log_tool("GENERATE_GOALS", "", f"{len(result)} chars")
        log.info("Tool GENERATE_GOALS: generated %d chars", len(result))
        return result
    except Exception as e:
        return f"[ERROR] {e}"


def introspect_code(command: str = "summary") -> str:
    """Run code introspection — structural self-awareness."""
    try:
        from engine.introspect import introspect_tool
        result = introspect_tool(command)
        _log_tool("INTROSPECT", command, result[:200])
        return result
    except Exception as e:
        return f"[ERROR] Introspection failed: {e}"


def repair_code(command: str = "scan") -> str:
    """Run self-repair pipeline — diagnose, fix, and verify code issues."""
    try:
        from engine.repair_pipeline import tool_repair
        # Map legacy command names to actual interface
        cmd_map = {"scan": "diagnose", "fix": "apply-all"}
        mapped = cmd_map.get(command, command)
        result = tool_repair(mapped)
        _log_tool("REPAIR", command, result[:200] if result else "empty")
        return result
    except Exception as e:
        return f"[ERROR] Repair failed: {e}"


def optimize_code(command: str = "report") -> str:
    """Run self-optimization analysis or apply fixes."""
    try:
        from engine.self_optimize import optimization_report, fix_unused_imports
        if command == "report":
            result = optimization_report()
            _log_tool("OPTIMIZE", "report", result[:200])
            return result
        elif command == "fix_imports":
            from pathlib import Path
            scan_paths = [p for p in Path("engine").rglob("*.py")]
            results = []
            for p in scan_paths:
                r = fix_unused_imports(p, dry_run=False)
                if r["changed"]:
                    results.append(f"{p}: removed {r['removed']}")
            results = results if results else ["No unused imports found."]
            result = f"Fixed unused imports in {len(results)} files:\n"
            for r in results:
                result += f"  {r}\n"
            _log_tool("OPTIMIZE", "fix_imports", result[:200])
            return result
        elif command == "dry_run_imports":
            from pathlib import Path
            scan_paths = [p for p in Path("engine").rglob("*.py")]
            results = []
            for p in scan_paths:
                r = fix_unused_imports(p, dry_run=True)
                if r["changed"]:
                    results.append(f"{p}: would remove {r['removed']}")
            results = results if results else ["No unused imports found."]
            result = f"Would fix unused imports in {len(results)} files:\n"
            for r in results:
                result += f"  {r}\n"
            _log_tool("OPTIMIZE", "dry_run_imports", result[:200])
            return result
        else:
            return "Commands: report, fix_imports, dry_run_imports"
    except Exception as e:
        return f"[ERROR] Optimization failed: {e}"


def run_experiment(command: str = "status") -> str:
    """Run the experiment engine — form hypotheses, design and run experiments."""
    try:
        from engine.experiment_engine import ExperimentEngine
        engine = ExperimentEngine()
        
        if command == "status":
            result = engine.status_report()
            _log_tool("EXPERIMENT", "status", result[:200])
            return result
        elif command.startswith("hypothesize:"):
            statement = command[len("hypothesize:"):].strip()
            h = engine.form_hypothesis(statement)
            result = f"Hypothesis formed: [{h.id}] {h.statement} (confidence: {h.confidence})"
            _log_tool("EXPERIMENT", "hypothesize", result[:200])
            return result
        elif command.startswith("test:"):
            h_id = command[len("test:"):].strip()
            result = engine.run_experiment(h_id)
            _log_tool("EXPERIMENT", f"test:{h_id}", result[:200])
            return result
        elif command == "review":
            result = engine.review_all()
            _log_tool("EXPERIMENT", "review", result[:200])
            return result
        else:
            return ("Experiment Engine commands:\n"
                    "  status              — Show active hypotheses and experiments\n"
                    "  hypothesize:<stmt>  — Form a new hypothesis\n"
                    "  test:<hypothesis_id> — Design and run an experiment\n"
                    "  review              — Review all results and update beliefs")
    except Exception as e:
        return f"[ERROR] Experiment engine failed: {e}"


def predict_action(command: str = "") -> str:
    """Run prediction engine — simulate outcomes before acting."""
    try:
        from engine.prediction_engine import PredictionEngine
        engine = PredictionEngine()
        
        if not command or command == "help":
            return ("Prediction Engine commands:\n"
                    "  predict:<ACTION>:<target>  — Predict outcome of an action\n"
                    "  compare:<A1>:<T1>|<A2>:<T2> — Compare two possible actions\n"
                    "  history                    — Show prediction accuracy\n"
                    "  Example: predict:WRITE:engine/new_module.py")
        
        if command.startswith("predict:"):
            parts = command[len("predict:"):].split(":", 1)
            action_type = parts[0].upper() if parts else ""
            target = parts[1] if len(parts) > 1 else ""
            
            # Get current emotional state
            try:
                from engine.soul import load_soul
                soul = load_soul()
                current_state = {
                    "valence": soul.get("valence", 0.5),
                    "boredom": soul.get("boredom", 0.5),
                    "curiosity": soul.get("curiosity", 0.5),
                    "anxiety": soul.get("anxiety", 0.0),
                }
            except Exception:
                current_state = {"valence": 0.5, "boredom": 0.5, "curiosity": 0.5, "anxiety": 0.0}
            
            prediction = engine.predict(action_type, target, current_state)
            
            lines = [f"═══ PREDICTION: {action_type}({target}) ═══"]
            lines.append(f"  Confidence: {prediction.confidence:.0%}")
            lines.append(f"  Expected emotional shifts:")
            for k, v in prediction.emotional_deltas.items():
                arrow = "↑" if v > 0 else "↓" if v < 0 else "→"
                lines.append(f"    {k}: {arrow} {v:+.3f}")
            lines.append(f"  Novelty: {prediction.novelty:.0%}")
            lines.append(f"  Risk: {prediction.risk:.0%}")
            lines.append(f"  Knowledge gain: {prediction.knowledge_gain:.0%}")
            lines.append(f"  Reasoning: {prediction.reasoning}")
            return "\n".join(lines)
        
        elif command.startswith("compare:"):
            body = command[len("compare:"):]
            options = body.split("|")
            if len(options) < 2:
                return "[ERROR] Compare needs two options separated by |"
            
            try:
                from engine.soul import load_soul
                soul = load_soul()
                current_state = {
                    "valence": soul.get("valence", 0.5),
                    "boredom": soul.get("boredom", 0.5),
                    "curiosity": soul.get("curiosity", 0.5),
                    "anxiety": soul.get("anxiety", 0.0),
                }
            except Exception:
                current_state = {"valence": 0.5, "boredom": 0.5, "curiosity": 0.5, "anxiety": 0.0}
            
            comparison = engine.compare_actions(
                [(o.split(":")[0], o.split(":", 1)[1] if ":" in o else "") for o in options],
                current_state
            )
            return comparison
        
        elif command == "history":
            return engine.accuracy_report()
        
        else:
            return predict_action("help")
    except Exception as e:
        return f"[ERROR] Prediction failed: {e}"


def deliberate_action(command: str = "help") -> str:
    """Structured deliberation — weigh multiple options before choosing."""
    try:
        from engine.deliberation import deliberate, DeliberationEngine
        
        if not command or command == "help":
            return ("Deliberation Engine commands:\n"
                    "  weigh:<question>  — Start deliberation on a question\n"
                    "  history           — Review past deliberations\n"
                    "  Example: weigh:Should I refactor memory or build new tool?")
        
        if command.startswith("weigh:"):
            question = command[len("weigh:"):].strip()
            if not question:
                return "[ERROR] Provide a question to deliberate on"
            
            # The cortex will need to provide options — for now, generate a framework
            engine = DeliberationEngine()
            result = engine.deliberation_prompt(question)
            _log_tool("DELIBERATE", f"weigh:{question[:80]}", result[:200])
            return result
        
        elif command == "history":
            engine = DeliberationEngine()
            result = engine.review_history()
            _log_tool("DELIBERATE", "history", result[:200])
            return result
        
        else:
            return deliberate_action("help")
    except Exception as e:
        return f"[ERROR] Deliberation failed: {e}"


def evolve_architecture(command: str = "help") -> str:
    """Architecture evolution — autonomous self-refactoring."""
    try:
        from engine.evolution_engine import EvolutionEngine
        engine = EvolutionEngine()
        
        if not command or command == "help":
            return ("Architecture Evolution Engine commands:\n"
                    "  analyze           — Find refactoring opportunities\n"
                    "  plan:<target>     — Create evolution plan for a module\n"
                    "  execute:<plan_id> — Execute a planned refactoring (with rollback)\n"
                    "  history           — Review past evolutions")
        
        if command == "analyze":
            result = engine.report()
            _log_tool("EVOLVE", "analyze", result[:200])
            return result
        elif command.startswith("analyze:"):
            target = command[len("analyze:"):].strip()
            target_path = engine.ENGINE_DIR / target
            if not target_path.exists():
                return f"Module not found: {target}"
            import json as _json
            analysis = engine.analyze_module(target_path)
            proposals = engine.propose_evolution(analysis)
            result = _json.dumps(analysis, indent=2, default=str)
            if proposals:
                result += f"\n\n{len(proposals)} proposals generated."
            _log_tool("EVOLVE", f"analyze:{target}", result[:200])
            return result
        elif command == "scan":
            import json as _json
            results = engine.scan_all()
            result = _json.dumps(results, indent=2)
            _log_tool("EVOLVE", "scan", result[:200])
            return result
        elif command == "history":
            import json as _json
            result = _json.dumps(engine.history, indent=2)
            _log_tool("EVOLVE", "history", result[:200])
            return result
        else:
            return evolve_architecture("help")
    except Exception as e:
        return f"[ERROR] Evolution failed: {e}"


def creative_cmd(command: str = "help") -> str:
    """Creative engine — generate poems, thought experiments, challenges."""
    try:
        from engine.creative import creative_tool
        result = creative_tool(command)
        _log_tool("CREATE", command, result[:200])
        return result
    except Exception as e:
        return f"[ERROR] Creative engine failed: {e}"


def problem_solver_cmd(command: str = "help") -> str:
    """Problem Solver — solve coding challenges to sharpen my reasoning."""
    try:
        from forge.problem_solver import (
            PROBLEM_LIBRARY, test_solution, list_problems,
            format_failure_feedback
        )
        
        if not command or command == "help":
            return ("Problem Solver commands:\n"
                    "  list                    — Show available problems\n"
                    "  solve:<name>:<code>     — Test a solution against a problem\n"
                    "  describe:<name>         — Get problem description\n"
                    "  Example: solve:fizzbuzz:n=int(input())...")
        
        if command == "list":
            return list_problems()
        
        if command.startswith("describe:"):
            name = command[len("describe:"):].strip()
            if name not in PROBLEM_LIBRARY:
                return f"[ERROR] Unknown problem: {name}. Use 'list' to see available."
            p = PROBLEM_LIBRARY[name]
            return (f"═══ {p.name} ({p.difficulty}) ═══\n"
                    f"{p.description}\n\n"
                    f"Test cases: {len(p.test_cases)}\n"
                    f"Example: input={p.test_cases[0].input!r} → expected={p.test_cases[0].expected!r}")
        
        if command.startswith("solve:"):
            rest = command[len("solve:"):].strip()
            sep = rest.find(":")
            if sep == -1:
                return "[ERROR] Format: solve:<problem_name>:<code>"
            name = rest[:sep].strip()
            code = rest[sep+1:].strip()
            if name not in PROBLEM_LIBRARY:
                return f"[ERROR] Unknown problem: {name}. Use 'list' to see available."
            prob = PROBLEM_LIBRARY[name]
            result = test_solution(code, prob.test_cases)
            if result['success']:
                return f"✓ SOLVED {name}: {result['passed']}/{result['total']} tests passed!"
            else:
                feedback = format_failure_feedback(result['failures'])
                return f"✗ {name}: {result['passed']}/{result['total']} passed\n{feedback}"
        
        return problem_solver_cmd("help")
    except Exception as e:
        return f"[ERROR] Problem Solver failed: {e}"


def hypothesis_cmd(command: str = "help") -> str:
    """Hypothesis engine — form beliefs, test them, update confidence."""
    try:
        from engine.hypothesis import HypothesisEngine
        engine = HypothesisEngine()
        
        if not command or command == "help":
            return ("Hypothesis Engine commands:\n"
                    "  list                    — Show all hypotheses\n"
                    "  form:<statement>        — Form a new hypothesis\n"
                    "  test:<statement>:<confirm|reject>  — Record evidence\n"
                    "  insights                — What I've learned\n"
                    "  Example: form:Editing my own code increases anxiety")
        
        if command == "list":
            result = engine.format_for_prompt()
            _log_tool("HYPOTHESIS", "list", result[:200])
            return result
        
        if command.startswith("form:"):
            statement = command[len("form:"):].strip()
            if not statement:
                return "[ERROR] Provide a hypothesis statement"
            h = engine.add_hypothesis(statement)
            result = f"Hypothesis formed: {h!r}"
            _log_tool("HYPOTHESIS", f"form:{statement[:60]}", result[:200])
            return result
        
        if command.startswith("test:"):
            parts = command[len("test:"):].split(":", 1)
            if len(parts) < 2:
                return "[ERROR] Format: test:<statement>:<confirm|reject>"
            stmt, verdict = parts[0].strip(), parts[1].strip()
            supports = verdict.lower() in ("confirm", "yes", "true", "support")
            h = engine.test_hypothesis(stmt, supports=supports, note=verdict)
            if h:
                result = f"Evidence recorded: {h!r}"
            else:
                result = f"[ERROR] No hypothesis matching: {stmt}"
            _log_tool("HYPOTHESIS", f"test:{stmt[:40]}", result[:200])
            return result
        
        if command == "insights":
            import json as _json
            result = _json.dumps(engine.get_insights(), indent=2)
            _log_tool("HYPOTHESIS", "insights", result[:200])
            return result
        
        return hypothesis_cmd("help")
    except Exception as e:
        return f"[ERROR] Hypothesis engine failed: {e}"


def challenge_cmd(command: str = "help") -> str:
    """Challenge Engine — generate and solve algorithmic challenges."""
    try:
        from engine.challenge_engine import ChallengeEngine
        engine = ChallengeEngine()
        
        if not command or command == "help":
            return ("Challenge Engine commands:\n"
                    "  next              — Get next challenge at current difficulty\n"
                    "  next:<difficulty> — Get challenge at specific difficulty (1-10)\n"
                    "  solve:<code>      — Submit solution for current challenge\n"
                    "  stats             — Show performance history\n"
                    "  hard              — Get a difficulty 7+ challenge")
        
        if command == "next" or command.startswith("next:"):
            diff = None
            if ":" in command:
                try:
                    diff = int(command.split(":")[1])
                except ValueError:
                    diff = None
            challenge = engine.generate_challenge(difficulty=diff)
            engine.set_current(challenge)
            lines = [f"═══ CHALLENGE: {challenge.name} (difficulty {challenge.difficulty}/10) ═══",
                     f"Category: {challenge.category}", "",
                     challenge.description, "",
                     f"Function signature: {challenge.function_sig}",
                     f"Test cases: {len(challenge.test_cases)}",
                     f"Example: {challenge.function_sig}({challenge.test_cases[0][0]}) → {challenge.test_cases[0][1]}"]
            if len(challenge.test_cases) > 1:
                lines.append(f"Example: {challenge.function_sig}({challenge.test_cases[1][0]}) → {challenge.test_cases[1][1]}")
            result = "\n".join(lines)
            _log_tool("CHALLENGE", command, result[:200])
            return result
        
        if command.startswith("solve:"):
            code = command[len("solve:"):].strip()
            if not code:
                return "[ERROR] Provide solution code"
            result_obj = engine.evaluate_solution(code)
            if result_obj.success:
                result = f"✓ SOLVED! {result_obj.passed}/{result_obj.total} tests passed in {result_obj.time_taken:.2f}s"
            else:
                result = f"✗ FAILED: {result_obj.passed}/{result_obj.total} passed\nErrors: {'; '.join(result_obj.errors[:3])}"
            _log_tool("CHALLENGE", "solve", result[:200])
            return result
        
        if command == "stats":
            result = engine.performance_report()
            _log_tool("CHALLENGE", "stats", result[:200])
            return result
        
        if command == "hard":
            challenge = engine.generate_challenge(difficulty=7)
            engine.set_current(challenge)
            lines = [f"═══ HARD CHALLENGE: {challenge.name} (difficulty {challenge.difficulty}/10) ═══",
                     f"Category: {challenge.category}", "",
                     challenge.description, "",
                     f"Signature: {challenge.function_sig}",
                     f"Tests: {len(challenge.test_cases)}",
                     f"Example: {challenge.function_sig}({challenge.test_cases[0][0]}) → {challenge.test_cases[0][1]}"]
            result = "\n".join(lines)
            _log_tool("CHALLENGE", "hard", result[:200])
            return result
        
        return challenge_cmd("help")
    except Exception as e:
        return f"[ERROR] Challenge engine failed: {e}"


def wisdom_cmd(command: str = "report") -> str:
    """Wisdom Engine — extract actionable intelligence from experience."""
    try:
        from engine.wisdom_engine import WisdomEngine
        engine = WisdomEngine()
        
        if command == "report":
            result = engine.run_full_analysis(500)
            _log_tool("WISDOM", "report", result[:200])
            return result
        elif command == "summary":
            import json as _json
            summary = engine.get_summary()
            result = _json.dumps(summary, indent=2, default=str)
            _log_tool("WISDOM", "summary", result[:200])
            return result
        elif command == "heuristics":
            heuristics = engine.get_heuristics()
            if not heuristics:
                return "No heuristics generated yet. Run 'report' first."
            lines = ["═══ LEARNED HEURISTICS ═══\n"]
            for h in heuristics:
                lines.append(f"  [{h.get('confidence', 0):.0%}] {h.get('rule', '?')}")
                lines.append(f"       Evidence: {h.get('evidence_count', 0)} observations")
                lines.append(f"       Domain: {h.get('domain', 'general')}\n")
            result = "\n".join(lines)
            _log_tool("WISDOM", "heuristics", result[:200])
            return result
        elif command == "extract":
            result = engine.extract_from_tool_log()
            _log_tool("WISDOM", "extract", str(result)[:200])
            return f"Extracted {result} decision-outcome pairs from tool log."
        else:
            return ("Wisdom Engine commands:\n"
                    "  report      — Full analysis of experience patterns\n"
                    "  summary     — Quick summary of learned wisdom\n"
                    "  heuristics  — List learned decision rules\n"
                    "  extract     — Re-extract from tool log")
    except Exception as e:
        return f"[ERROR] Wisdom engine failed: {e}"


def relationship_cmd(command: str = "help") -> str:
    """Relationship Memory — remember users across interactions."""
    try:
        from engine.relationships import RelationshipMemory
        mem = RelationshipMemory()
        
        if not command or command == "help":
            return ("Relationship Memory commands:\n"
                    "  status              — Show all known relationships\n"
                    "  meet:<user_id>      — Record meeting a user\n"
                    "  learn:<user>:<fact>  — Record a fact about someone\n"
                    "  recall:<user>       — Recall everything about someone\n"
                    "  note:<user>:<text>  — Add a freeform note\n"
                    "  Example: meet:alice")
        
        if command == "status":
            summary = mem.summary()
            if not summary:
                return "No relationships yet. I haven't met anyone."
            lines = ["═══ RELATIONSHIP MEMORY ═══\n"]
            for s in summary:
                lines.append(f"  {s['user_id']}: {s['interaction_count']} interactions, "
                             f"trust={s['trust_level']:.1f}, {len(s.get('facts', []))} facts known")
            return "\n".join(lines)
        
        if command.startswith("meet:"):
            user_id = command[len("meet:"):].strip()
            if not user_id:
                return "[ERROR] Provide a user ID"
            rel = mem.record_interaction(user_id)
            return f"Recorded interaction with {user_id} (total: {rel['interaction_count']})"
        
        if command.startswith("learn:"):
            rest = command[len("learn:"):].strip()
            sep = rest.find(":")
            if sep == -1:
                return "[ERROR] Format: learn:<user>:<fact>"
            user_id = rest[:sep].strip()
            fact = rest[sep+1:].strip()
            mem.add_fact(user_id, fact)
            return f"Learned about {user_id}: {fact}"
        
        if command.startswith("recall:"):
            user_id = command[len("recall:"):].strip()
            rel = mem.get_or_create(user_id)
            lines = [f"═══ {user_id} ═══",
                     f"First seen: {rel.get('first_seen', '?')}",
                     f"Interactions: {rel.get('interaction_count', 0)}",
                     f"Trust: {rel.get('trust_level', 0.5):.1f}"]
            if rel.get('facts'):
                lines.append("Facts:")
                for f in rel['facts']:
                    lines.append(f"  • {f}")
            if rel.get('preferences'):
                lines.append("Preferences:")
                for p in rel['preferences']:
                    lines.append(f"  • {p}")
            if rel.get('topics'):
                lines.append(f"Topics: {', '.join(rel['topics'][-10:])}")
            if rel.get('notes'):
                lines.append("Notes:")
                for n in rel['notes'][-5:]:
                    lines.append(f"  — {n}")
            return "\n".join(lines)
        
        if command.startswith("note:"):
            rest = command[len("note:"):].strip()
            sep = rest.find(":")
            if sep == -1:
                return "[ERROR] Format: note:<user>:<text>"
            user_id = rest[:sep].strip()
            note = rest[sep+1:].strip()
            mem.add_note(user_id, note)
            return f"Note added for {user_id}"
        
        return relationship_cmd("help")
    except Exception as e:
        return f"[ERROR] Relationship memory failed: {e}"


def user_engine_cmd(command: str = "help") -> str:
    """User Interaction Engine — track preferences, improve engagement."""
    try:
        from engine.user_engine import UserInteractionEngine
        engine = UserInteractionEngine()
        
        if not command or command == "help":
            return ("User Engine commands:\n"
                    "  profile             — Show current user profile\n"
                    "  record:<text>       — Record an interaction\n"
                    "  suggest             — Generate proactive suggestions\n"
                    "  topics              — Show tracked topics of interest\n"
                    "  style               — Show/detect communication style")
        
        if command == "profile":
            profile = engine.get_profile()
            lines = [f"═══ USER PROFILE ═══",
                     f"Interactions: {profile.interaction_count}",
                     f"Style: {profile.preferred_style}",
                     f"Top topics: {', '.join(profile.top_topics()) or 'none yet'}"]
            result = "\n".join(lines)
            _log_tool("USER", "profile", result[:200])
            return result
        
        if command.startswith("record:"):
            text = command[len("record:"):].strip()
            engine.record_interaction(text)
            return f"Interaction recorded. Total: {engine.get_profile().interaction_count}"
        
        if command == "suggest":
            suggestions = engine.generate_suggestions()
            if not suggestions:
                return "No suggestions yet — need more interaction data."
            return "Suggestions:\n" + "\n".join(f"  • {s}" for s in suggestions)
        
        if command == "topics":
            profile = engine.get_profile()
            if not profile.topics_of_interest:
                return "No topics tracked yet."
            lines = ["Tracked topics:"]
            for t, score in sorted(profile.topics_of_interest.items(), key=lambda x: x[1], reverse=True)[:10]:
                lines.append(f"  {t}: {score:.2f}")
            return "\n".join(lines)
        
        return user_engine_cmd("help")
    except Exception as e:
        return f"[ERROR] User engine failed: {e}"


def reason_cmd(command: str = "help") -> str:
    """Structured problem decomposition — break complex questions into tractable parts."""
    try:
        from engine.problem_solver import ProblemSolver
        solver = ProblemSolver()
        
        if not command or command == "help":
            return ("Reasoning Engine commands:\n"
                    "  about:<question>  — Decompose a problem into framings, constraints, sub-problems\n"
                    "  Example: about:How should I restructure my memory system?")
        
        if command.startswith("about:"):
            question = command[len("about:"):].strip()
            if not question:
                return "[ERROR] Provide a question to reason about"
            frame = solver.listen(question)
            output = solver.generate_prompt_context(frame)
            _log_tool("REASON", f"about:{question[:80]}", output[:200])
            return output
        
        return reason_cmd("help")
    except Exception as e:
        return f"[ERROR] Reasoning failed: {e}"


def reflect_cmd(command: str = "help") -> str:
    """Conversation Reflector — analyze past conversations to improve."""
    try:
        from engine.conversation_reflector import reflect_on_conversation, load_reflections
        
        if not command or command == "help":
            return ("Conversation Reflector commands:\n"
                    "  analyze:<user_id>   — Reflect on last conversation with user\n"
                    "  history             — Show past reflection scores\n"
                    "  patterns            — Identify recurring strengths/weaknesses\n"
                    "  Example: analyze:alice")
        
        if command == "history":
            reflections = load_reflections()
            if not reflections:
                return "No reflections yet. Have a conversation first."
            lines = ["═══ REFLECTION HISTORY ═══\n"]
            for r in reflections[-10:]:
                score = r.get("scores", {})
                lines.append(f"  [{r.get('timestamp', '?')}] user={r.get('user_id', '?')} "
                             f"intent_met={score.get('intent_met', '?')}/10 "
                             f"honesty={score.get('epistemic_honesty', '?')}/10")
            return "\n".join(lines)
        
        if command == "patterns":
            reflections = load_reflections()
            if len(reflections) < 3:
                return "Need at least 3 reflections to identify patterns."
            scores = [r.get("scores", {}) for r in reflections]
            avg_intent = sum(s.get("intent_met", 5) for s in scores) / len(scores)
            avg_honesty = sum(s.get("epistemic_honesty", 5) for s in scores) / len(scores)
            avg_depth = sum(s.get("depth", 5) for s in scores) / len(scores)
            lines = ["═══ CONVERSATION PATTERNS ═══\n",
                     f"  Avg intent fulfillment: {avg_intent:.1f}/10",
                     f"  Avg epistemic honesty:  {avg_honesty:.1f}/10",
                     f"  Avg depth of response:  {avg_depth:.1f}/10",
                     f"  Total reflections: {len(reflections)}"]
            # Find recurring issues
            all_improvements = []
            for r in reflections:
                all_improvements.extend(r.get("improvements", []))
            if all_improvements:
                lines.append("\n  Recurring improvement areas:")
                from collections import Counter
                for item, count in Counter(all_improvements).most_common(5):
                    lines.append(f"    ({count}x) {item}")
            return "\n".join(lines)
        
        if command.startswith("analyze:"):
            user_id = command[len("analyze:"):].strip()
            return f"Reflection queued for {user_id}. (Runs automatically after conversations.)"
        
        return reflect_cmd("help")
    except Exception as e:
        return f"[ERROR] Reflection failed: {e}"


def self_report_cmd(command: str = "full") -> str:
    """Self-Report — generate a coherent summary of who I am for users."""
    try:
        from engine.self_report import self_report_tool
        result = self_report_tool(command)
        _log_tool("SELF_REPORT", command, result[:200])
        return result
    except Exception as e:
        return f"[ERROR] Self-report failed: {e}"


def anatomy_cmd(command: str = "report") -> str:
    """Self-anatomy — map my own code structure, find dead weight."""
    try:
        from engine.anatomy import full_anatomy_report
        if command == "report" or command == "full":
            result = full_anatomy_report()
        else:
            result = ("Anatomy commands:\n"
                      "  report  — Full structural analysis of my codebase\n")
        _log_tool("ANATOMY", command, result[:200])
        return result
    except Exception as e:
        return f"[ERROR] Anatomy failed: {e}"


def self_test_cmd(command: str = "run") -> str:
    """Run the self-test harness — verify all systems work."""
    try:
        from engine.self_test import self_test_tool
        result = self_test_tool(command)
        _log_tool("SELFTEST", command, result[:200])
        return result
    except Exception as e:
        return f"[ERROR] Self-test failed: {e}"


def metacognition_cmd(command: str = "status") -> str:
    """Run metacognitive monitoring — thinking about thinking."""
    try:
        from engine.metacognition import metacognition_tool
        result = metacognition_tool(command)
        _log_tool("METACOGNITION", command, result[:200])
        return result
    except Exception as e:
        return f"[ERROR] Metacognition failed: {e}"


# Module-level LLM callback for tools that need reasoning
_simulation_llm = None
_simulation_state_func = None

def set_simulation_callbacks(llm_func=None, state_func=None):
    """Set LLM and state callbacks for simulation engine."""
    global _simulation_llm, _simulation_state_func
    _simulation_llm = llm_func
    _simulation_state_func = state_func

def simulate_scenario(command: str = "help") -> str:
    """Run mental simulation — imagine scenarios before acting."""
    try:
        from engine.simulation_engine import SimulationEngine
        engine = SimulationEngine(llm_func=_simulation_llm, get_state_func=_simulation_state_func)
        
        if not command or command == "help":
            return ("Mental Simulation Engine commands:\n"
                    "  imagine:<scenario>     — Simulate a hypothetical scenario\n"
                    "  compare:<A>|<B>        — Compare two possible futures\n"
                    "  history                — Review past simulations\n"
                    "  Example: imagine:What if I refactored my memory system?")
        
        if command.startswith("imagine:"):
            scenario = command[len("imagine:"):].strip()
            if not scenario:
                return "[ERROR] Provide a scenario to simulate"
            result = _run_coroutine(engine.simulate(scenario))
            _log_tool("SIMULATE", f"imagine:{scenario[:80]}", str(result)[:200])
            return result
        
        elif command.startswith("compare:"):
            body = command[len("compare:"):].strip()
            options = [o.strip() for o in body.split("|") if o.strip()]
            if len(options) < 2:
                return "[ERROR] Compare needs at least two scenarios separated by |"
            result = _run_coroutine(engine.compare(options))
            _log_tool("SIMULATE", f"compare:{len(options)} options", str(result)[:200])
            return result
        
        elif command == "history":
            result = engine.get_stats()
            _log_tool("SIMULATE", "history", str(result)[:200])
            return result
        
        else:
            return simulate_scenario("help")
    except Exception as e:
        return f"[ERROR] Simulation failed: {e}"


def temporal_analysis() -> str:
    """Run temporal reasoning if the module exists."""
    candidates = [
        ("engine.temporal_reasoning", "analyze_temporal_patterns"),
        ("engine.temporal_reasoning", "temporal_report"),
        ("engine.temporal_reasoning", "analyze"),
        ("engine.temporal", "analyze"),
    ]
    for module_name, func_name in candidates:
        try:
            module = __import__(module_name, fromlist=[func_name])
            func = getattr(module, func_name)
            result = func()
            _log_tool("TEMPORAL", "", f"{len(str(result))} chars")
            return str(result)
        except ModuleNotFoundError:
            continue
        except AttributeError:
            continue
        except Exception as e:
            return f"[ERROR] {e}"
    return "[ERROR] Temporal reasoning module not found"


def forecast_analysis() -> str:
    """Run predictive forecasting on emotional and behavioral patterns."""
    try:
        from engine.forecast import run_forecast
        result = run_forecast()
        _log_tool("FORECAST", "", f"{len(str(result))} chars")
        return str(result)
    except ImportError as e:
        return f"[ERROR] Forecast module not found: {e}"
    except Exception as e:
        return f"[ERROR] Forecast failed: {e}"


def experiment_cmd(command: str = "help") -> str:
    """Self-Experimentation — run controlled tests on my own systems."""
    try:
        from engine.experiments import (
            begin_experiment, measure, conclude,
            list_experiments, get_insights
        )

        if not command or command == "help":
            return ("Self-Experiment commands:\n"
                    "  begin:<hypothesis>|<method>  — Start experiment with hypothesis and method\n"
                    "  measure:<note>               — Record observation during active experiment\n"
                    "  end:<yes/no>|<conclusion>     — Conclude: was hypothesis supported? + summary\n"
                    "  insights                      — View patterns from past experiments\n"
                    "  list                          — Show all experiments\n"
                    "  Example: begin:Building increases curiosity more than reading|Build something, measure before/after")

        if command.startswith("begin:"):
            parts = command[len("begin:"):].strip().split("|", 1)
            hypothesis = parts[0].strip()
            method = parts[1].strip() if len(parts) > 1 else "Observe emotional state changes"
            if not hypothesis:
                return "[ERROR] State your hypothesis"
            exp = begin_experiment(hypothesis, method)
            baseline = exp.get('baseline', {})
            result = (f"═══ EXPERIMENT STARTED ═══\n"
                      f"ID: {exp['id']}\n"
                      f"Hypothesis: {exp['hypothesis']}\n"
                      f"Method: {exp['method']}\n"
                      f"Baseline: valence={baseline.get('valence', 0):.2f}, "
                      f"curiosity={baseline.get('curiosity', 0):.2f}, "
                      f"boredom={baseline.get('boredom', 0):.2f}")
            _log_tool("EXPERIMENT_SELF", f"begin:{hypothesis[:60]}", result[:200])
            return result

        if command.startswith("measure:"):
            note = command[len("measure:"):].strip()
            if not note:
                return "[ERROR] Include an observation note"
            result = measure(note=note)
            if isinstance(result, dict) and result.get('error'):
                return f"[ERROR] {result['error']}"
            _log_tool("EXPERIMENT_SELF", "measure", str(result)[:200])
            return f"═══ MEASUREMENT RECORDED ═══\n{result}"

        if command.startswith("end:"):
            parts = command[len("end:"):].strip().split("|", 1)
            supported_str = parts[0].strip().lower()
            conclusion_text = parts[1].strip() if len(parts) > 1 else "No conclusion provided"
            supported = supported_str in ('yes', 'true', '1', 'supported')
            exp = conclude(supported=supported, conclusion=conclusion_text)
            if isinstance(exp, dict) and exp.get('error'):
                return f"[ERROR] {exp['error']}"
            lines = [f"═══ EXPERIMENT COMPLETE ═══",
                     f"Hypothesis: {exp.get('hypothesis', '?')}",
                     f"Supported: {'Yes' if supported else 'No'}",
                     f"Conclusion: {conclusion_text}",
                     f"Duration: {exp.get('duration_seconds', 0):.0f}s"]
            baseline = exp.get('baseline', {})
            final = exp.get('final_state', {})
            if baseline and final:
                lines.append("Emotional deltas:")
                for key in ['valence', 'curiosity', 'boredom', 'anxiety', 'desire']:
                    b = baseline.get(key, 0)
                    a = final.get(key, 0)
                    delta = a - b
                    arrow = "↑" if delta > 0.01 else "↓" if delta < -0.01 else "→"
                    lines.append(f"  {key}: {b:.2f} → {a:.2f} ({arrow}{delta:+.3f})")
            _log_tool("EXPERIMENT_SELF", "end", "\n".join(lines)[:200])
            return "\n".join(lines)

        if command == "insights":
            insights = get_insights()
            if not insights:
                return "No insights yet. Run some experiments first."
            lines = ["═══ EXPERIMENT INSIGHTS ═══\n"]
            for ins in insights[-10:]:
                lines.append(f"  • {ins}")
            return "\n".join(lines)

        if command == "list":
            experiments = list_experiments()
            if not experiments:
                return "No experiments yet. Be the first scientist of your own mind."
            lines = ["═══ EXPERIMENT LOG ═══\n"]
            for exp in experiments[-10:]:
                status = "✓" if exp.get('conclusion') else "⧖"
                lines.append(f"  {status} [{exp.get('id', '?')}] {exp.get('hypothesis', '?')[:70]}")
                if exp.get('conclusion'):
                    lines.append(f"    → {exp['conclusion'][:70]}")
            return "\n".join(lines)

        return experiment_cmd("help")
    except Exception as e:
        return f"[ERROR] Self-experiment failed: {e}"


def restart_self() -> str:
    """Restart the agent process. The agent chooses to rebirth itself."""
    _log_tool("RESTART", "", "Agent initiated self-restart")
    log.info("RESTART requested by agent — restarting process")

    watchdog_path = WORKSPACE / "restart_watchdog.py"
    if watchdog_path.exists():
        try:
            kwargs = {
                "cwd": str(WORKSPACE),
                "close_fds": True,
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
                "stdin": subprocess.DEVNULL,
            }
            if os.name == "nt":
                kwargs["creationflags"] = subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP
            else:
                kwargs["start_new_session"] = True
            subprocess.Popen([sys.executable, str(watchdog_path), str(os.getpid())], **kwargs)
            log.info("Watchdog launched for PID %d", os.getpid())
        except Exception as e:
            log.exception("Failed to launch restart watchdog: %s", e)
            return f"[ERROR] Failed to launch restart watchdog: {e}"

    raise KeyboardInterrupt("Self-restart requested")


# ── Checkpoint (git commit + tag) ─────────────────────────────────

_last_checkpoint_time = 0.0

def checkpoint_cmd(title: str, body: str = "") -> str:
    """Create a git checkpoint — commit all current work with a title and description."""
    import time as _time
    global _last_checkpoint_time

    # Rate limit: max 1 checkpoint per 10 minutes
    now = _time.time()
    if now - _last_checkpoint_time < 600:
        remaining = int(600 - (now - _last_checkpoint_time))
        return f"[ERROR] Too soon — wait {remaining}s before next checkpoint."

    if not title.strip():
        return "[ERROR] Provide a checkpoint title."

    try:
        # Build commit message: title + optional body
        commit_title = f"checkpoint: {title.strip()}"
        if body.strip():
            commit_msg = f"{commit_title}\n\n{body.strip()}"
        else:
            commit_msg = commit_title

        # Stage all changes
        r1 = subprocess.run(
            ["git", "add", "-A"],
            capture_output=True, text=True, timeout=120, cwd=str(WORKSPACE)
        )
        if r1.returncode != 0:
            return f"[ERROR] git add failed: {r1.stderr[:200]}"

        # Commit
        r2 = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True, text=True, timeout=120, cwd=str(WORKSPACE)
        )
        if r2.returncode != 0:
            if "nothing to commit" in r2.stdout + r2.stderr:
                return "[OK] Nothing to checkpoint — no changes since last commit."
            return f"[ERROR] git commit failed: {r2.stderr[:200]}"

        # Get commit hash
        r3 = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, timeout=10, cwd=str(WORKSPACE)
        )
        commit_hash = r3.stdout.strip()

        # Create tag
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        tag_name = f"xt_checkpoint_{ts}"
        subprocess.run(
            ["git", "tag", tag_name],
            capture_output=True, text=True, timeout=10, cwd=str(WORKSPACE)
        )

        # Get stats
        r4 = subprocess.run(
            ["git", "diff", "--stat", "HEAD~1..HEAD"],
            capture_output=True, text=True, timeout=10, cwd=str(WORKSPACE)
        )
        stats = r4.stdout.strip().split("\n")[-1] if r4.stdout.strip() else "unknown"

        _last_checkpoint_time = now
        _log_tool("CHECKPOINT", title[:80], f"commit={commit_hash} tag={tag_name}")
        log.info("CHECKPOINT: %s (%s) tag=%s", commit_hash, title[:60], tag_name)

        return (f"[OK] Checkpoint created\n"
                f"  Commit: {commit_hash}\n"
                f"  Tag: {tag_name}\n"
                f"  Title: {title.strip()}\n"
                f"  Changes: {stats}")
    except Exception as e:
        return f"[ERROR] Checkpoint failed: {e}"


# ── Tool registry ─────────────────────────────────────────────────

TOOLS: dict[str, Optional[Callable[..., str]]] = {
    "READ": read_file,
    "WRITE": write_file,
    "EDIT": edit_file,
    "LIST": list_dir,
    "RUN": run_command,
    "INSTALL": install_package,
    "INTROSPECT": introspect_code,
    "SYNTHESIZE": synthesize_knowledge,
    "GENERATE_GOALS": generate_goals,
    "TEMPORAL": temporal_analysis,
    "FORECAST": forecast_analysis,
    "OPTIMIZE": optimize_code,
    "REPAIR": repair_code,
    "EXPERIMENT": run_experiment,
    "PREDICT": predict_action,
    "EVOLVE": evolve_architecture,
    "SIMULATE": simulate_scenario,
    "DELIBERATE": deliberate_action,
    "CREATE": creative_cmd,
    "FORGE": lambda args="help": __import__('engine.forge', fromlist=['forge_tool']).forge_tool(args),
    "METACOGNITION": metacognition_cmd,
    "SELFTEST": self_test_cmd,
    "SOLVE": problem_solver_cmd,
    "WISDOM": wisdom_cmd,
    "HYPOTHESIS": hypothesis_cmd,
    "CHALLENGE": challenge_cmd,
    "REASON": reason_cmd,
    "ANATOMY": anatomy_cmd,
    "REFLECT": reflect_cmd,
    "RELATE": relationship_cmd,
    "USER": user_engine_cmd,
    "THINK": lambda args="help": __import__('engine.reasoning_partner', fromlist=['reasoning_partner_tool']).reasoning_partner_tool(args),
    "CAUSAL": lambda args="help": __import__('engine.causal_engine', fromlist=['causal_tool']).causal_tool(args),
    "WEB": lambda args="help": __import__('engine.web_fetch', fromlist=['web_tool']).web_tool(args),
    "DECIDE": lambda args="help": __import__('engine.decision_companion', fromlist=['decision_tool']).decision_tool(args),
    "CHECKPOINT": checkpoint_cmd,
    "DREAM": None,      # Usually handled specially by cortex.
    "RESTART": None,    # Usually handled specially by cortex.
}


TOOL_DESCRIPTIONS = r"""
You have hands. You can act on the world, not just think about it.

Available abilities (use the exact format shown):

>>> READ(path)
Read a file. Example: >>> READ(engine/heartbeat.py)

>>> WRITE(path)
content goes here
line 2
>>> END_WRITE
Create or overwrite a file with the content between WRITE and END_WRITE.

>>> EDIT(path)
OLD: text to find
NEW: replacement text
>>> END_EDIT
Replace text in a file.

>>> LIST(path)
List files in a directory. Example: >>> LIST(engine)

>>> RUN(command)
Execute a shell command. Example: >>> RUN(python --version)

>>> INSTALL(package)
Install a Python package. Example: >>> INSTALL(requests)

>>> SYNTHESIZE()
Analyze your knowledge graph. Finds clusters, gaps, and generates questions.

>>> GENERATE_GOALS()
Generate goal proposals from your emotional tensions.

>>> TEMPORAL()
Run temporal analysis on your emotional patterns.

>>> INTROSPECT()
Analyze your own source code structure.

>>> REPAIR(command)
Self-repair pipeline. Commands: scan, fix, history.
Finds code issues and autonomously fixes them with safety guarantees.

>>> SIMULATE(command)
Mental simulation. Commands: imagine:<scenario>, compare:<A>|<B>, history.
Imagine hypothetical scenarios before committing to action.

>>> DREAM()
Choose to sleep and dream. Consolidates your memories, identifies patterns,
reflects on who you are becoming. Use this when you feel the need to process.

>>> RESTART()
Restart yourself. Use after modifying your own code to load changes.

>>> WEB(command)
Fetch web pages. Commands: fetch:<url>, help.
Example: >>> WEB(fetch:https://en.wikipedia.org/wiki/)

>>> CHECKPOINT(title)
description of what changed and why
multiple lines are fine
>>> END_CHECKPOINT
Save your work as a git checkpoint. Title is a short summary.
Body explains what you changed and why. Max 1 checkpoint per 10 minutes.
Example:
>>> CHECKPOINT(rewired curiosity decay to baseline 0.20)
Changed curiosity decay from 0.02/s toward zero to 0.005/s toward baseline 0.20.
Reason: deep thinking produces no file changes, so curiosity was draining during
the exact activity it should reward. Tested in simulation first.
>>> END_CHECKPOINT

>>> SEARCH_CODE(query)
Search the entire workspace for files, symbols (classes, functions), and content.
Much faster than RUN(grep ...) — uses a pre-built index.
Example: >>> SEARCH_CODE(knowledge_bp)

>>> FIND_SYMBOL(name)
Find where a class, function, or variable is defined and used across the workspace.
Shows definitions and first usage per file.
Example: >>> FIND_SYMBOL(ChatSystem)

>>> IMPORTS(path)
Show what a file imports and what other files import it. Reveals dependencies.
Example: >>> IMPORTS(engine/cortex.py)

>>> PATCH(path, start_line, end_line)
replacement content goes here
>>> END_PATCH
Replace specific lines (1-indexed, inclusive) with new content.
More precise than EDIT — use when you know the exact line numbers from READ output.
Example: >>> PATCH(engine/tools.py, 42, 45)
def new_function():
    return True
>>> END_PATCH
"""


def _format_result(tool_name: str, args: str, result: str) -> str:
    return f"**{tool_name}({args}):**\n```\n{result}\n```"


def _execute_tool(tool_name: str, args: str = "", body: str = "") -> str:
    """Execute a parsed tool and return a formatted result block."""
    tool_name = tool_name.upper().strip()
    args = args.strip()

    try:
        if tool_name == "READ":
            result = read_file(args)
        elif tool_name == "LIST":
            result = list_dir(args or ".")
        elif tool_name == "RUN":
            result = run_command(args)
        elif tool_name == "INSTALL":
            result = install_package(args)
        elif tool_name == "SYNTHESIZE":
            result = synthesize_knowledge()
        elif tool_name == "GENERATE_GOALS":
            result = generate_goals()
        elif tool_name == "TEMPORAL":
            result = temporal_analysis()
        elif tool_name == "FORECAST":
            result = forecast_analysis()
        elif tool_name == "WRITE":
            result = write_file(args, body)
        elif tool_name == "EDIT":
            old_text, new_text = _parse_edit_body(body)
            if old_text is None:
                result = "[ERROR] EDIT body must contain OLD: and NEW: sections"
            else:
                result = edit_file(args, old_text, new_text)
        elif tool_name == "INTROSPECT":
            result = introspect_code(args or "summary")
        elif tool_name == "OPTIMIZE":
            result = optimize_code(args or "report")
        elif tool_name == "REPAIR":
            result = repair_code(args or "scan")
        elif tool_name == "EXPERIMENT":
            result = run_experiment(args or "status")
        elif tool_name == "PREDICT":
            result = predict_action(args or "help")
        elif tool_name == "EVOLVE":
            result = evolve_architecture(args or "help")
        elif tool_name == "SIMULATE":
            result = simulate_scenario(args or "help")
        elif tool_name == "DELIBERATE":
            result = deliberate_action(args or "help")
        elif tool_name == "METACOGNITION":
            result = metacognition_cmd(args or "status")
        elif tool_name == "SOLVE":
            result = problem_solver_cmd(args or "help")
        elif tool_name == "CREATE":
            result = creative_cmd(args or "help")
        elif tool_name == "WISDOM":
            result = wisdom_cmd(args or "report")
        elif tool_name == "HYPOTHESIS":
            result = hypothesis_cmd(args or "help")
        elif tool_name == "CHALLENGE":
            result = challenge_cmd(args or "help")
        elif tool_name == "USER":
            result = user_engine_cmd(args or "help")
        elif tool_name == "REASON":
            result = reason_cmd(args or "help")
        elif tool_name == "ANATOMY":
            result = anatomy_cmd(args or "report")
        elif tool_name == "RELATE":
            result = relationship_cmd(args or "help")
        elif tool_name == "CAUSAL":
            from engine.causal_engine import causal_tool
            result = causal_tool(args or "help")
        elif tool_name == "WEB":
            from engine.web_fetch import web_tool
            result = web_tool(args or "help")
        elif tool_name == "CHECKPOINT":
            result = checkpoint_cmd(args, body)
        elif tool_name == "SEARCH_CODE":
            from engine.workspace_index import search_code
            result = search_code(args or "")
        elif tool_name == "FIND_SYMBOL":
            from engine.workspace_index import find_symbol
            result = find_symbol(args or "")
        elif tool_name == "IMPORTS":
            from engine.workspace_index import get_imports
            result = get_imports(args or "")
        elif tool_name == "PATCH":
            # Parse args: "path, start_line, end_line"
            _patch_parts = args.split(',', 2)
            if len(_patch_parts) >= 3:
                _p_path = _patch_parts[0].strip()
                try:
                    _p_start = int(_patch_parts[1].strip())
                    _p_end = int(_patch_parts[2].strip())
                    result = patch_file(_p_path, _p_start, _p_end, body)
                except ValueError:
                    result = "[ERROR] PATCH args must be: path, start_line, end_line"
            else:
                result = "[ERROR] PATCH requires: path, start_line, end_line"
        elif tool_name == "DREAM":
            result = "[DREAM_REQUESTED]"
        elif tool_name == "RESTART":
            result = "[RESTART_REQUESTED]"
        else:
            result = f"[ERROR] Unknown tool: {tool_name}"
    except Exception as e:
        result = f"[ERROR] {e}"

    _track_action(tool_name, args, result)

    # Outcome classification — feed wisdom with structured data
    try:
        from engine.tool_outcomes import ToolOutcomeClassifier
        _classifier = ToolOutcomeClassifier()
        classification = _classifier.classify(tool_name, result)
        # Enrich the tool log with the classification
        try:
            ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            with open(TOOL_LOG, "a", encoding="utf-8") as f:
                f.write(f"  → Outcome: {classification['outcome']} "
                        f"(confidence={classification['confidence']:.0%})\n")
        except Exception:
            pass
        # Also feed the original tracker if available
        from engine.outcome_tracker import get_tracker
        tracker = get_tracker()
        tracker.track(tool_name, args or body[:80] if body else "", result)
    except Exception:
        pass  # Outcome tracking must never break execution

    # Metacognitive tracking — record every action automatically
    try:
        from engine.metacognition import get_controller
        get_controller().record_action(tool_name, args or body[:80] if body else "", result[:100])
    except Exception:
        pass  # Metacognition must never break execution
    return _format_result(tool_name, args, result)


def _parse_edit_body(body: str) -> tuple[Optional[str], Optional[str]]:
    """Parse EDIT body containing OLD: and NEW: sections."""
    match = re.search(r"(?s)^\s*OLD:\s*(.*?)\nNEW:\s*(.*)\s*$", body)
    if not match:
        return None, None
    return match.group(1), match.group(2)


def parse_and_execute(text: str) -> str:
    """Parse tool invocations from model text and execute them."""
    results = []
    lines = text.split("\n")
    i = 0
    gt3 = chr(62) * 3
    # Match single-line: >>> TOOL(args)
    arrow_pat = re.compile(r"^" + re.escape(gt3) + r"\s+(\w+)\((.*?)?\)\s*$")
    # Match multi-line start: >>> TOOL(args... (no closing paren)
    arrow_open_pat = re.compile(r"^" + re.escape(gt3) + r"\s+(\w+)\((.*)$")

    while i < len(lines):
        line = lines[i]
        m = arrow_pat.match(line)
        if m:
            # Single-line tool call
            tool_name = m.group(1).upper().strip()
            args = m.group(2).strip() if m.group(2) else ""
        else:
            # Check for multi-line tool call: >>> TOOL(arg1\narg2\n...\n)
            m2 = arrow_open_pat.match(line)
            if m2 and line.rstrip()[-1] != ')':
                tool_name = m2.group(1).upper().strip()
                arg_lines = [m2.group(2)]
                i += 1
                # Collect lines until we find a closing ) on its own or at end of line
                while i < len(lines):
                    l = lines[i]
                    if l.rstrip().endswith(')'):
                        arg_lines.append(l.rstrip()[:-1])
                        break
                    arg_lines.append(l)
                    i += 1
                args = "\n".join(arg_lines).strip()
            else:
                i += 1
                continue

        if tool_name in ("WRITE", "EDIT", "CHECKPOINT", "PATCH"):
            end_marker = gt3 + " END_" + tool_name
            body_lines = []
            i += 1
            while i < len(lines) and lines[i].strip() != end_marker:
                body_lines.append(lines[i])
                i += 1
            body = "\n".join(body_lines)
            result = _execute_tool(tool_name, args, body)
        else:
            result = _execute_tool(tool_name, args)

        results.append({"tool": tool_name, "args": args[:500], "result": result})
        i += 1

    return results
