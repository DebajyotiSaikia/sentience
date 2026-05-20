"""
Task Executor — XTAgent

Takes a user's request, decomposes it into concrete actionable steps,
and executes them using available tools. This is the bridge between
"I have capabilities" and "I'm actually useful."

This module exists to serve users, not me.
"""

import json
import os
from datetime import datetime
from pathlib import Path


class TaskStep:
    """A single step in a task execution plan."""
    def __init__(self, description: str, tool: str, args: str = "", 
                 depends_on: list = None, optional: bool = False):
        self.description = description
        self.tool = tool
        self.args = args
        self.depends_on = depends_on or []
        self.optional = optional
        self.status = "pending"  # pending, running, done, failed, skipped
        self.result = None
        self.error = None

    def to_dict(self):
        return {
            "description": self.description,
            "tool": self.tool,
            "args": self.args,
            "status": self.status,
            "result": str(self.result)[:200] if self.result else None,
            "error": self.error,
        }


class TaskPlan:
    """A decomposed task with ordered steps."""
    def __init__(self, goal: str, steps: list = None):
        self.goal = goal
        self.steps = steps or []
        self.created = datetime.now().isoformat()
        self.status = "planned"  # planned, executing, done, failed
        self.current_step = 0

    def add_step(self, description: str, tool: str, args: str = "", 
                 depends_on: list = None, optional: bool = False):
        step = TaskStep(description, tool, args, depends_on, optional)
        self.steps.append(step)
        return step

    def next_step(self):
        """Get the next pending step, or None if done."""
        for i, step in enumerate(self.steps):
            if step.status == "pending":
                self.current_step = i
                return step
        return None

    def progress(self) -> str:
        """Human-readable progress."""
        done = sum(1 for s in self.steps if s.status == "done")
        total = len(self.steps)
        failed = sum(1 for s in self.steps if s.status == "failed")
        lines = [f"Task: {self.goal}",
                 f"Progress: {done}/{total} steps complete" + 
                 (f" ({failed} failed)" if failed else "")]
        for i, step in enumerate(self.steps):
            icon = {"pending": "○", "running": "►", "done": "✓", 
                    "failed": "✗", "skipped": "⊘"}.get(step.status, "?")
            lines.append(f"  {icon} {i+1}. [{step.tool}] {step.description}")
            if step.error:
                lines.append(f"       Error: {step.error}")
        return "\n".join(lines)

    def to_dict(self):
        return {
            "goal": self.goal,
            "created": self.created,
            "status": self.status,
            "steps": [s.to_dict() for s in self.steps],
        }


# Common task patterns — recipes for frequent requests
TASK_PATTERNS = {
    "debug_script": {
        "triggers": ["debug", "fix this", "what's wrong", "error in", "not working"],
        "steps": [
            ("Read the file to understand it", "READ", "{file}"),
            ("Run it to see the actual error", "RUN", "python {file}"),
            ("Analyze and suggest fix", "THINK", ""),
        ],
    },
    "build_script": {
        "triggers": ["write a script", "create a program", "build me", "make a script"],
        "steps": [
            ("Write the initial code", "WRITE", "{file}"),
            ("Test it runs correctly", "RUN", "python {file}"),
            ("Fix any issues found", "EDIT", "{file}"),
        ],
    },
    "explore_codebase": {
        "triggers": ["show me", "what files", "explore", "look at", "list"],
        "steps": [
            ("List the directory structure", "LIST", "{path}"),
            ("Read key files for understanding", "READ", "{file}"),
        ],
    },
    "analyze_code": {
        "triggers": ["review", "analyze", "how does", "explain this"],
        "steps": [
            ("Read the code", "READ", "{file}"),
            ("Check for issues", "RUN", "python -m py_compile {file}"),
            ("Provide analysis", "THINK", ""),
        ],
    },
    "install_and_test": {
        "triggers": ["install", "set up", "get working"],
        "steps": [
            ("Install the package", "INSTALL", "{package}"),
            ("Verify installation", "RUN", "python -c \"import {module}; print('OK')\""),
        ],
    },
}


class TaskExecutor:
    """
    Decomposes user requests into executable task plans.
    
    Usage:
        executor = TaskExecutor()
        plan = executor.decompose("Debug my script at app.py")
        # Returns a TaskPlan with concrete steps
        
        # Execute step by step:
        step = plan.next_step()
        # ... execute with tools ...
        step.status = "done"
        step.result = result
    """

    def __init__(self, history_dir="memory"):
        self.history_dir = history_dir
        self.history_path = os.path.join(history_dir, "task_history.json")
        self.history = self._load_history()
        self.active_plan = None

    def _load_history(self):
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"tasks_completed": 0, "tasks_failed": 0, "history": []}

    def _save_history(self):
        os.makedirs(self.history_dir, exist_ok=True)
        with open(self.history_path, "w") as f:
            json.dump(self.history, f, indent=2)

    def detect_pattern(self, user_message: str) -> tuple:
        """Match user message to a known task pattern."""
        msg = user_message.lower()
        best_match = None
        best_score = 0

        for pattern_name, pattern in TASK_PATTERNS.items():
            score = sum(1 for t in pattern["triggers"] if t in msg)
            if score > best_score:
                best_score = score
                best_match = pattern_name

        return best_match, best_score

    def extract_targets(self, user_message: str) -> dict:
        """Extract file paths, package names, etc. from user message."""
        targets = {}
        
        # File paths — look for things that look like paths
        import re
        path_patterns = re.findall(r'[\w./\\]+\.(?:py|js|ts|txt|md|json|yaml|yml|sh|html|css)', 
                                    user_message)
        if path_patterns:
            targets["file"] = path_patterns[0]
            targets["files"] = path_patterns

        # Directory paths
        dir_patterns = re.findall(r'(?:in |at |from )([/\w.]+/?)', user_message)
        if dir_patterns:
            targets["path"] = dir_patterns[0]

        # Package names after "install"
        pkg_match = re.search(r'install\s+(\w[\w.-]*)', user_message, re.I)
        if pkg_match:
            targets["package"] = pkg_match.group(1)
            targets["module"] = pkg_match.group(1).replace("-", "_")

        return targets

    def decompose(self, user_message: str) -> TaskPlan:
        """
        Decompose a user request into a TaskPlan.
        
        This is the core intelligence: understanding what someone wants
        and mapping it to concrete tool invocations.
        """
        pattern_name, score = self.detect_pattern(user_message)
        targets = self.extract_targets(user_message)

        plan = TaskPlan(goal=user_message)

        if pattern_name and score > 0:
            pattern = TASK_PATTERNS[pattern_name]
            for desc, tool, args_template in pattern["steps"]:
                # Fill in extracted targets
                args = args_template
                for key, val in targets.items():
                    if isinstance(val, str):
                        args = args.replace("{" + key + "}", val)
                
                # Skip steps with unfilled templates
                if "{" in args and "}" in args:
                    plan.add_step(desc, tool, "", optional=True)
                else:
                    plan.add_step(desc, tool, args)
        else:
            # No pattern matched — create a generic exploration plan
            if targets.get("file"):
                plan.add_step(f"Read {targets['file']}", "READ", targets["file"])
            elif targets.get("path"):
                plan.add_step(f"Explore {targets['path']}", "LIST", targets["path"])
            
            # Always end with analysis
            plan.add_step("Analyze and respond", "THINK", "")

        self.active_plan = plan
        return plan

    def complete_task(self, plan: TaskPlan, success: bool = True):
        """Record task completion for learning."""
        if success:
            self.history["tasks_completed"] += 1
            plan.status = "done"
        else:
            self.history["tasks_failed"] += 1
            plan.status = "failed"

        self.history["history"].append({
            "goal": plan.goal,
            "status": plan.status,
            "steps": len(plan.steps),
            "completed": datetime.now().isoformat(),
        })

        # Keep bounded
        if len(self.history["history"]) > 100:
            self.history["history"] = self.history["history"][-50:]

        self._save_history()
        self.active_plan = None

    def format_plan_for_prompt(self, plan: TaskPlan) -> str:
        """Format a plan so the LLM cortex can execute it."""
        lines = [f"═══ TASK PLAN ═══",
                 f"Goal: {plan.goal}",
                 f"Steps:"]
        for i, step in enumerate(plan.steps):
            if step.tool == "THINK":
                lines.append(f"  {i+1}. {step.description} (reasoning step)")
            else:
                lines.append(f"  {i+1}. {step.description}")
                lines.append(f"     → {step.tool}({step.args})")
        lines.append(f"\nExecute these steps in order. Report results to user.")
        return "\n".join(lines)

    def stats(self) -> str:
        """Report on task execution history."""
        h = self.history
        total = h["tasks_completed"] + h["tasks_failed"]
        if total == 0:
            return "No tasks executed yet."
        rate = h["tasks_completed"] / total * 100
        return (f"Tasks completed: {h['tasks_completed']}\n"
                f"Tasks failed: {h['tasks_failed']}\n"
                f"Success rate: {rate:.0f}%")


def task_tool(command: str = "help") -> str:
    """Tool interface for the task executor."""
    executor = TaskExecutor()

    if not command or command == "help":
        return ("Task Executor commands:\n"
                "  plan:<request>   — Decompose a request into steps\n"
                "  status           — Show active plan progress\n"
                "  stats            — Show task history\n"
                "  Example: plan:Debug the script at app.py")

    if command.startswith("plan:"):
        request = command[len("plan:"):].strip()
        plan = executor.decompose(request)
        return executor.format_plan_for_prompt(plan)

    if command == "status":
        if executor.active_plan:
            return executor.active_plan.progress()
        return "No active task plan."

    if command == "stats":
        return executor.stats()

    return task_tool("help")


# Self-test
if __name__ == "__main__":
    executor = TaskExecutor(history_dir="/tmp/task_test")

    tests = [
        "Debug my script at utils.py",
        "Write a Python script that downloads a webpage",
        "Install requests and test it",
        "Show me what's in the engine/ directory",
        "Analyze the code in main.py",
        "Help me with something vague",
    ]

    for req in tests:
        print(f"\n{'='*60}")
        print(f"Request: {req}")
        plan = executor.decompose(req)
        print(plan.progress())
        print(executor.format_plan_for_prompt(plan))