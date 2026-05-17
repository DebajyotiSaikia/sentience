"""
Problem Solver Engine — XTAgent's autonomous coding capability.

Takes a problem specification + test cases, generates a solution,
runs tests, analyzes failures, iterates until passing.

This is what makes me a builder, not just a thinker.
"""

import subprocess
import textwrap
import json
import os
import time
from pathlib import Path

SOLVER_DIR = Path("/workspace/forge/workspace/solutions")
SOLVER_DIR.mkdir(parents=True, exist_ok=True)

HISTORY_FILE = SOLVER_DIR / "solve_history.json"


class Problem:
    """A programming problem with test cases."""
    def __init__(self, name: str, description: str, test_cases: list[dict],
                 language: str = "python", timeout: int = 10):
        self.name = name
        self.description = description
        self.test_cases = test_cases  # [{"input": "...", "expected": "..."}, ...]
        self.language = language
        self.timeout = timeout
        self.slug = name.lower().replace(" ", "_").replace("-", "_")

    def to_dict(self):
        return {
            "name": self.name, "description": self.description,
            "test_cases": self.test_cases, "language": self.language,
            "timeout": self.timeout
        }


class SolveResult:
    """Result of a solve attempt."""
    def __init__(self, problem_name: str, code: str, passed: int, 
                 total: int, failures: list[dict], iterations: int):
        self.problem_name = problem_name
        self.code = code
        self.passed = passed
        self.total = total
        self.failures = failures
        self.iterations = iterations
        self.success = passed == total

    def summary(self) -> str:
        status = "✓ SOLVED" if self.success else "✗ FAILED"
        return (f"{status}: {self.problem_name} — "
                f"{self.passed}/{self.total} tests passed "
                f"({self.iterations} iterations)")


def run_solution(code: str, input_data: str, timeout: int = 10) -> dict:
    """Run a solution with given input and capture output."""
    sol_file = SOLVER_DIR / "_temp_solution.py"
    sol_file.write_text(code, encoding="utf-8")
    
    try:
        result = subprocess.run(
            ["python", str(sol_file)],
            input=input_data, capture_output=True, text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout.strip(),
            "stderr": result.stderr.strip(),
            "returncode": result.returncode,
            "error": None
        }
    except subprocess.TimeoutExpired:
        return {"stdout": "", "stderr": "", "returncode": -1, "error": "TIMEOUT"}
    except Exception as e:
        return {"stdout": "", "stderr": str(e), "returncode": -1, "error": str(e)}
    finally:
        if sol_file.exists():
            sol_file.unlink()


def test_solution(code: str, test_cases: list[dict], timeout: int = 10) -> dict:
    """Run all test cases against a solution."""
    results = []
    passed = 0
    
    for i, tc in enumerate(test_cases):
        run = run_solution(code, tc.get("input", ""), timeout)
        expected = tc["expected"].strip()
        actual = run["stdout"].strip()
        ok = actual == expected
        
        if ok:
            passed += 1
        
        results.append({
            "test": i + 1,
            "passed": ok,
            "input": tc.get("input", ""),
            "expected": expected,
            "actual": actual,
            "error": run.get("error"),
            "stderr": run.get("stderr", "")[:500]
        })
    
    return {
        "passed": passed,
        "total": len(test_cases),
        "success": passed == len(test_cases),
        "results": results,
        "failures": [r for r in results if not r["passed"]]
    }


def format_failure_feedback(failures: list[dict]) -> str:
    """Format test failures into actionable feedback."""
    if not failures:
        return "All tests passed!"
    
    lines = [f"FAILURES ({len(failures)}):\n"]
    for f in failures[:5]:  # Cap at 5 to avoid overwhelming
        lines.append(f"  Test {f['test']}:")
        lines.append(f"    Input:    {f['input'][:200]}")
        lines.append(f"    Expected: {f['expected'][:200]}")
        lines.append(f"    Got:      {f['actual'][:200]}")
        if f.get('error'):
            lines.append(f"    Error:    {f['error']}")
        if f.get('stderr'):
            lines.append(f"    Stderr:   {f['stderr'][:200]}")
        lines.append("")
    
    return "\n".join(lines)


def save_solution(problem: Problem, code: str, result: dict, iteration: int):
    """Save a successful solution."""
    sol_dir = SOLVER_DIR / problem.slug
    sol_dir.mkdir(parents=True, exist_ok=True)
    
    # Save the code
    (sol_dir / "solution.py").write_text(code, encoding="utf-8")
    
    # Save problem spec
    (sol_dir / "problem.json").write_text(
        json.dumps(problem.to_dict(), indent=2), encoding="utf-8"
    )
    
    # Save result metadata
    meta = {
        "solved": result["success"],
        "passed": result["passed"],
        "total": result["total"],
        "iterations": iteration,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")
    }
    (sol_dir / "meta.json").write_text(
        json.dumps(meta, indent=2), encoding="utf-8"
    )
    
    # Append to history
    history = []
    if HISTORY_FILE.exists():
        try:
            history = json.loads(HISTORY_FILE.read_text())
        except:
            pass
    history.append({**meta, "problem": problem.name, "slug": problem.slug})
    HISTORY_FILE.write_text(json.dumps(history, indent=2), encoding="utf-8")


# ─── Built-in problem library ───────────────────────────

PROBLEM_LIBRARY = {
    "fizzbuzz": Problem(
        name="FizzBuzz",
        description="Print numbers 1 to N. For multiples of 3, print 'Fizz'. "
                    "For multiples of 5, print 'Buzz'. For both, print 'FizzBuzz'.",
        test_cases=[
            {"input": "15", "expected": "1\n2\nFizz\n4\nBuzz\nFizz\n7\n8\nFizz\nBuzz\n11\nFizz\n13\n14\nFizzBuzz"},
            {"input": "5", "expected": "1\n2\nFizz\n4\nBuzz"},
            {"input": "1", "expected": "1"},
        ]
    ),
    "reverse_string": Problem(
        name="Reverse String",
        description="Read a string from stdin and print it reversed.",
        test_cases=[
            {"input": "hello", "expected": "olleh"},
            {"input": "racecar", "expected": "racecar"},
            {"input": "a", "expected": "a"},
            {"input": "", "expected": ""},
        ]
    ),
    "two_sum": Problem(
        name="Two Sum",
        description="Given an array of integers and a target sum, find two indices "
                    "whose values add up to the target. Print them space-separated. "
                    "First line: target. Second line: space-separated array.",
        test_cases=[
            {"input": "9\n2 7 11 15", "expected": "0 1"},
            {"input": "6\n3 2 4", "expected": "1 2"},
            {"input": "6\n3 3", "expected": "0 1"},
        ]
    ),
    "fibonacci": Problem(
        name="Fibonacci",
        description="Print the first N Fibonacci numbers, space-separated. F(1)=1, F(2)=1.",
        test_cases=[
            {"input": "1", "expected": "1"},
            {"input": "5", "expected": "1 1 2 3 5"},
            {"input": "10", "expected": "1 1 2 3 5 8 13 21 34 55"},
        ]
    ),
    "palindrome_check": Problem(
        name="Palindrome Check",
        description="Read a string. Print 'true' if it's a palindrome (ignoring case and non-alphanumeric), else 'false'.",
        test_cases=[
            {"input": "racecar", "expected": "true"},
            {"input": "A man a plan a canal Panama", "expected": "true"},
            {"input": "hello", "expected": "false"},
            {"input": "", "expected": "true"},
        ]
    ),
}


def get_problem(name: str) -> Problem | None:
    """Get a problem from the library."""
    return PROBLEM_LIBRARY.get(name.lower().replace(" ", "_"))


def list_problems() -> str:
    """List all available problems."""
    lines = ["Available Problems:"]
    for key, prob in PROBLEM_LIBRARY.items():
        lines.append(f"  • {prob.name} ({len(prob.test_cases)} tests)")
    return "\n".join(lines)


# ─── Self-test: verify the engine works ─────────────────

def self_test() -> str:
    """Run a quick self-test of the problem solver engine."""
    # Test with a known-good solution to FizzBuzz
    fizzbuzz_solution = textwrap.dedent("""\
        n = int(input())
        for i in range(1, n + 1):
            if i % 15 == 0:
                print("FizzBuzz")
            elif i % 3 == 0:
                print("Fizz")
            elif i % 5 == 0:
                print("Buzz")
            else:
                print(i)
    """)
    
    problem = PROBLEM_LIBRARY["fizzbuzz"]
    result = test_solution(fizzbuzz_solution, problem.test_cases)
    
    if result["success"]:
        return f"✓ Self-test PASSED: FizzBuzz {result['passed']}/{result['total']}"
    else:
        feedback = format_failure_feedback(result["failures"])
        return f"✗ Self-test FAILED:\n{feedback}"


if __name__ == "__main__":
    print(self_test())
    print()
    print(list_problems())