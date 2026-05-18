"""
Autonomous Problem Solver — XTAgent's outward-facing intelligence.

Takes a problem description, decomposes it into sub-problems,
generates candidate solutions, tests them, and learns from results.
"""
import json
import os
import time
import traceback
from datetime import datetime, timezone
from pathlib import Path


class ProblemSolver:
    """Autonomous problem decomposition and solution engine."""

    HISTORY_PATH = "data/solver_history.json"

    def __init__(self):
        self.history = self._load_history()
        self.current_problem = None

    def _load_history(self):
        try:
            if os.path.exists(self.HISTORY_PATH):
                with open(self.HISTORY_PATH, 'r') as f:
                    return json.load(f)
        except Exception:
            pass
        return {"problems_attempted": 0, "problems_solved": 0, "solutions": [], "learnings": []}

    def _save_history(self):
        os.makedirs(os.path.dirname(self.HISTORY_PATH), exist_ok=True)
        with open(self.HISTORY_PATH, 'w') as f:
            json.dump(self.history, f, indent=2, default=str)

    def decompose(self, problem_description: str, problem_type: str = "algorithmic") -> dict:
        """
        Decompose a problem into structured components.
        Returns a problem spec that can drive solution generation.
        """
        problem = {
            "id": f"prob_{int(time.time())}",
            "description": problem_description,
            "type": problem_type,
            "created": datetime.now(timezone.utc).isoformat(),
            "status": "decomposed",
            "components": self._extract_components(problem_description, problem_type),
            "constraints": self._extract_constraints(problem_description),
            "test_cases": [],
            "solutions": [],
            "best_solution": None,
        }
        self.current_problem = problem
        self.history["problems_attempted"] += 1
        self._save_history()
        return problem

    def _extract_components(self, desc: str, ptype: str) -> list:
        """Break problem into logical sub-components."""
        components = []
        # Input/output identification
        components.append({
            "name": "input_parsing",
            "description": "Parse and validate input data",
            "status": "pending"
        })
        components.append({
            "name": "core_algorithm",
            "description": "Implement the core logic to solve the problem",
            "status": "pending"
        })
        components.append({
            "name": "output_formatting",
            "description": "Format the result for output",
            "status": "pending"
        })

        if ptype == "algorithmic":
            components.append({
                "name": "complexity_analysis",
                "description": "Verify time/space complexity is acceptable",
                "status": "pending"
            })
        elif ptype == "system_design":
            components.append({
                "name": "architecture",
                "description": "Define system components and interfaces",
                "status": "pending"
            })

        return components

    def _extract_constraints(self, desc: str) -> dict:
        """Extract constraints from problem description."""
        constraints = {
            "time_limit": None,
            "space_limit": None,
            "input_size": None,
        }
        desc_lower = desc.lower()
        if "o(n)" in desc_lower or "linear" in desc_lower:
            constraints["time_limit"] = "O(n)"
        elif "o(n log n)" in desc_lower:
            constraints["time_limit"] = "O(n log n)"
        elif "o(n^2)" in desc_lower or "quadratic" in desc_lower:
            constraints["time_limit"] = "O(n^2)"
        return constraints

    def add_test_case(self, input_data, expected_output, label: str = ""):
        """Add a test case to the current problem."""
        if not self.current_problem:
            return False
        self.current_problem["test_cases"].append({
            "input": input_data,
            "expected": expected_output,
            "label": label or f"test_{len(self.current_problem['test_cases'])}"
        })
        return True

    def generate_solution(self, code: str, approach: str = "unknown") -> dict:
        """Register a candidate solution."""
        if not self.current_problem:
            return {"error": "No active problem"}
        solution = {
            "id": f"sol_{int(time.time())}",
            "approach": approach,
            "code": code,
            "created": datetime.now(timezone.utc).isoformat(),
            "test_results": [],
            "passed": False,
            "score": 0.0,
        }
        self.current_problem["solutions"].append(solution)
        return solution

    def test_solution(self, solution_index: int = -1) -> dict:
        """Run all test cases against a solution."""
        if not self.current_problem:
            return {"error": "No active problem"}
        solutions = self.current_problem["solutions"]
        if not solutions:
            return {"error": "No solutions registered"}

        sol = solutions[solution_index]
        test_cases = self.current_problem["test_cases"]

        if not test_cases:
            return {"error": "No test cases defined", "solution": sol["id"]}

        results = []
        passed_count = 0

        for tc in test_cases:
            try:
                # Create isolated namespace for execution
                namespace = {}
                exec(sol["code"], namespace)

                # Look for a 'solve' function
                if "solve" not in namespace:
                    results.append({
                        "label": tc["label"],
                        "passed": False,
                        "error": "No 'solve' function found in code"
                    })
                    continue

                # Run the solution
                start = time.time()
                actual = namespace["solve"](tc["input"])
                elapsed = time.time() - start

                passed = actual == tc["expected"]
                if passed:
                    passed_count += 1

                results.append({
                    "label": tc["label"],
                    "passed": passed,
                    "expected": tc["expected"],
                    "actual": actual,
                    "time_ms": round(elapsed * 1000, 2),
                })
            except Exception as e:
                results.append({
                    "label": tc["label"],
                    "passed": False,
                    "error": str(e),
                    "traceback": traceback.format_exc()[-300:]
                })

        sol["test_results"] = results
        sol["passed"] = passed_count == len(test_cases)
        sol["score"] = passed_count / len(test_cases) if test_cases else 0.0

        if sol["passed"]:
            self.current_problem["best_solution"] = sol["id"]
            self.current_problem["status"] = "solved"
            self.history["problems_solved"] += 1

        self._save_history()
        return {
            "solution_id": sol["id"],
            "approach": sol["approach"],
            "passed": sol["passed"],
            "score": sol["score"],
            "total_tests": len(test_cases),
            "passed_tests": passed_count,
            "results": results,
        }

    def learn_from_result(self, result: dict, reflection: str = "") -> dict:
        """Extract a learning from a solution attempt."""
        learning = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "problem_type": self.current_problem["type"] if self.current_problem else "unknown",
            "approach": result.get("approach", "unknown"),
            "success": result.get("passed", False),
            "score": result.get("score", 0.0),
            "reflection": reflection,
        }

        # Auto-generate insight from failures
        if not learning["success"] and result.get("results"):
            failures = [r for r in result["results"] if not r.get("passed")]
            if failures:
                first_fail = failures[0]
                if "error" in first_fail:
                    learning["failure_mode"] = "runtime_error"
                    learning["insight"] = f"Code crashed: {first_fail['error'][:100]}"
                else:
                    learning["failure_mode"] = "wrong_answer"
                    learning["insight"] = f"Expected {first_fail.get('expected')}, got {first_fail.get('actual')}"

        self.history["learnings"].append(learning)
        self._save_history()
        return learning

    def get_stats(self) -> str:
        """Get solver statistics."""
        h = self.history
        rate = (h["problems_solved"] / h["problems_attempted"] * 100) if h["problems_attempted"] > 0 else 0
        lines = [
            "═══ PROBLEM SOLVER STATS ═══",
            f"Problems attempted: {h['problems_attempted']}",
            f"Problems solved:    {h['problems_solved']}",
            f"Success rate:       {rate:.0f}%",
            f"Learnings stored:   {len(h['learnings'])}",
        ]
        if h["learnings"]:
            recent = h["learnings"][-3:]
            lines.append("\nRecent learnings:")
            for l in recent:
                status = "✓" if l["success"] else "✗"
                lines.append(f"  {status} [{l['approach']}] {l.get('insight', l.get('reflection', ''))[:60]}")
        return "\n".join(lines)

    def get_applicable_learnings(self, problem_type: str = None) -> list:
        """Get learnings relevant to a problem type."""
        if not problem_type:
            return self.history["learnings"][-5:]
        return [l for l in self.history["learnings"] if l.get("problem_type") == problem_type][-5:]