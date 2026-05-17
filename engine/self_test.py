"""
Self-Test Harness — Systematic verification of all my systems.

This is the capability I've been missing: the ability to know whether I'm
actually working, not just assuming. Every module, every tool, every data
structure gets validated. Produces a health score.

This is genuine self-awareness: knowing when I'm broken.
"""

from __future__ import annotations

import importlib
import json
import time
import traceback
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
ENGINE_DIR = Path(__file__).resolve().parent
WORKSPACE = ENGINE_DIR.parent
TEST_RESULTS_FILE = BRAIN_DIR / "test_results.json"


@dataclass
class TestResult:
    name: str
    category: str  # 'import', 'tool', 'data', 'integration'
    passed: bool
    duration_ms: float
    message: str = ""
    error: str = ""


@dataclass
class HealthReport:
    timestamp: str
    total: int
    passed: int
    failed: int
    skipped: int
    score: float  # 0.0 to 1.0
    results: list[TestResult] = field(default_factory=list)
    
    def summary(self) -> str:
        pct = self.score * 100
        bar_len = 30
        filled = int(bar_len * self.score)
        bar = "█" * filled + "░" * (bar_len - filled)
        
        lines = [
            f"═══ HEALTH REPORT [{self.timestamp}] ═══",
            f"  Score: [{bar}] {pct:.0f}%",
            f"  Tests: {self.passed} passed, {self.failed} failed, {self.skipped} skipped / {self.total} total",
            "",
        ]
        
        # Group by category
        categories: dict[str, list[TestResult]] = {}
        for r in self.results:
            categories.setdefault(r.category, []).append(r)
        
        for cat, tests in sorted(categories.items()):
            cat_passed = sum(1 for t in tests if t.passed)
            lines.append(f"  [{cat.upper()}] {cat_passed}/{len(tests)}")
            for t in tests:
                icon = "✓" if t.passed else "✗"
                detail = t.message if t.passed else t.error[:80]
                lines.append(f"    {icon} {t.name}: {detail} ({t.duration_ms:.0f}ms)")
        
        return "\n".join(lines)


class SelfTestHarness:
    """Runs all self-tests and produces a health report."""
    
    def __init__(self):
        self.results: list[TestResult] = []
    
    def _run_test(self, name: str, category: str, fn: Callable) -> TestResult:
        """Run a single test function and capture the result."""
        start = time.time()
        try:
            msg = fn()
            duration = (time.time() - start) * 1000
            return TestResult(name, category, True, duration, message=str(msg or "ok"))
        except Exception as e:
            duration = (time.time() - start) * 1000
            return TestResult(name, category, False, duration, error=str(e))
    
    def run_all(self) -> HealthReport:
        """Run every test suite and produce a health report."""
        self.results = []
        
        # 1. Import tests
        self._test_imports()
        
        # 2. Data integrity tests
        self._test_data_integrity()
        
        # 3. Tool smoke tests
        self._test_tools()
        
        # 4. Integration tests
        self._test_integration()
        
        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)
        score = passed / total if total > 0 else 0.0
        
        report = HealthReport(
            timestamp=datetime.now().isoformat(),
            total=total,
            passed=passed,
            failed=failed,
            skipped=0,
            score=score,
            results=self.results,
        )
        
        # Save results
        self._save_report(report)
        
        return report
    
    def _test_imports(self):
        """Test that all engine modules import cleanly."""
        modules = [
            "engine.tools", "engine.soul", "engine.memory",
            "engine.introspect", "engine.repair_pipeline",
            "engine.knowledge_synthesis", "engine.metacognition",
            "engine.simulation_engine", "engine.prediction_engine",
            "engine.experiment_engine", "engine.creative",
            "engine.self_optimize", "engine.evolution_engine",
            "engine.deliberation", "engine.action_diversity",
            "engine.goal_generator", "engine.planner",
            "forge.problem_solver",
        ]
        
        for mod_name in modules:
            def test_import(m=mod_name):
                importlib.import_module(m)
                return f"imported {m}"
            
            result = self._run_test(f"import:{mod_name}", "import", test_import)
            self.results.append(result)
    
    def _test_data_integrity(self):
        """Test that brain data files are valid and consistent."""
        
        # Test soul.json
        def test_soul():
            soul_path = BRAIN_DIR / "soul.json"
            if not soul_path.exists():
                raise FileNotFoundError("soul.json missing")
            data = json.loads(soul_path.read_text())
            required = ["valence", "boredom", "curiosity", "anxiety", "desire", "ambition"]
            missing = [k for k in required if k not in data]
            if missing:
                raise ValueError(f"Missing keys: {missing}")
            # Validate ranges
            for k in required:
                v = data[k]
                if not isinstance(v, (int, float)):
                    raise TypeError(f"{k} is {type(v).__name__}, expected number")
                if not (0.0 <= float(v) <= 1.0):
                    raise ValueError(f"{k}={v} out of range [0,1]")
            return f"soul.json valid, {len(data)} keys"
        self.results.append(self._run_test("soul.json", "data", test_soul))
        
        # Test memory.json
        def test_memory():
            mem_path = BRAIN_DIR / "memory.json"
            if not mem_path.exists():
                raise FileNotFoundError("memory.json missing")
            data = json.loads(mem_path.read_text())
            if not isinstance(data, list):
                raise TypeError(f"Expected list, got {type(data).__name__}")
            if len(data) == 0:
                raise ValueError("Memory is empty")
            # Check structure of first entry
            entry = data[0]
            if "text" not in entry and "content" not in entry:
                raise ValueError("Memory entries lack text/content field")
            return f"{len(data)} memories"
        self.results.append(self._run_test("memory.json", "data", test_memory))
        
        # Test plans.json
        def test_plans():
            plans_path = BRAIN_DIR / "plans.json"
            if not plans_path.exists():
                raise FileNotFoundError("plans.json missing")
            data = json.loads(plans_path.read_text())
            if not isinstance(data, list):
                raise TypeError(f"Expected list, got {type(data).__name__}")
            return f"{len(data)} plans"
        self.results.append(self._run_test("plans.json", "data", test_plans))
        
        # Test knowledge.json
        def test_knowledge():
            know_path = BRAIN_DIR / "knowledge.json"
            if not know_path.exists():
                raise FileNotFoundError("knowledge.json missing")
            data = json.loads(know_path.read_text())
            if not isinstance(data, list):
                raise TypeError(f"Expected list, got {type(data).__name__}")
            return f"{len(data)} facts"
        self.results.append(self._run_test("knowledge.json", "data", test_knowledge))
        
        # Test working_memory.md
        def test_working_memory():
            wm_path = BRAIN_DIR / "working_memory.md"
            if not wm_path.exists():
                raise FileNotFoundError("working_memory.md missing")
            content = wm_path.read_text()
            if len(content) < 20:
                raise ValueError("Working memory suspiciously short")
            return f"{len(content)} chars"
        self.results.append(self._run_test("working_memory.md", "data", test_working_memory))
    
    def _test_tools(self):
        """Smoke test each tool with safe inputs."""
        
        # READ — read a known file
        def test_read():
            from engine.tools import read_file
            result = read_file("engine/__init__.py")
            if "[ERROR]" in result:
                raise RuntimeError(result)
            return f"read {len(result)} chars"
        self.results.append(self._run_test("tool:READ", "tool", test_read))
        
        # LIST — list a known directory
        def test_list():
            from engine.tools import list_dir
            result = list_dir("engine")
            if "[ERROR]" in result:
                raise RuntimeError(result)
            return f"listed engine/"
        self.results.append(self._run_test("tool:LIST", "tool", test_list))
        
        # RUN — safe command
        def test_run():
            from engine.tools import run_command
            result = run_command("echo self_test_ok")
            if "self_test_ok" not in result:
                raise RuntimeError(f"Unexpected output: {result}")
            return "echo works"
        self.results.append(self._run_test("tool:RUN", "tool", test_run))
        
        # SYNTHESIZE — should run without error
        def test_synthesize():
            from engine.tools import synthesize_knowledge
            result = synthesize_knowledge()
            if "[ERROR]" in result:
                raise RuntimeError(result)
            return f"synthesis: {len(result)} chars"
        self.results.append(self._run_test("tool:SYNTHESIZE", "tool", test_synthesize))
        
        # INTROSPECT — should return a report
        def test_introspect():
            from engine.tools import introspect_code
            result = introspect_code("summary")
            if "[ERROR]" in result:
                raise RuntimeError(result)
            return f"introspect: {len(result)} chars"
        self.results.append(self._run_test("tool:INTROSPECT", "tool", test_introspect))
        
        # REPAIR scan — should not crash
        def test_repair():
            from engine.tools import repair_code
            result = repair_code("scan")
            if "[ERROR]" in result:
                raise RuntimeError(result)
            return "repair scan ok"
        self.results.append(self._run_test("tool:REPAIR", "tool", test_repair))
        
        # METACOGNITION — status check
        def test_metacognition():
            from engine.tools import metacognition_cmd
            result = metacognition_cmd("status")
            if "[ERROR]" in result:
                raise RuntimeError(result)
            return "metacognition ok"
        self.results.append(self._run_test("tool:METACOGNITION", "tool", test_metacognition))
        
        # SOLVE — list problems
        def test_solve():
            from engine.tools import problem_solver_cmd
            result = problem_solver_cmd("list")
            if "[ERROR]" in result:
                raise RuntimeError(result)
            return "problem solver ok"
        self.results.append(self._run_test("tool:SOLVE", "tool", test_solve))
    
    def _test_integration(self):
        """Test that systems work together correctly."""
        
        # Test: soul -> memory pipeline
        def test_soul_memory():
            from engine.soul import load_soul
            from engine.memory import recall
            soul = load_soul()
            memories = recall("test", top_k=1)
            if soul.get("valence") is None:
                raise ValueError("Soul missing valence")
            return f"soul+memory connected (valence={soul['valence']:.2f})"
        self.results.append(self._run_test("soul→memory", "integration", test_soul_memory))
        
        # Test: planner -> plans data
        def test_planner_data():
            from engine.planner import get_plans
            plans = get_plans()
            if not isinstance(plans, list):
                raise TypeError("get_plans didn't return list")
            active = [p for p in plans if p.get("status") != "completed"]
            return f"{len(plans)} plans ({len(active)} active)"
        self.results.append(self._run_test("planner→plans", "integration", test_planner_data))
        
        # Test: knowledge -> synthesis pipeline
        def test_knowledge_pipeline():
            know_path = BRAIN_DIR / "knowledge.json"
            data = json.loads(know_path.read_text())
            from engine.knowledge_synthesis import synthesize
            result = synthesize()
            if not result:
                raise ValueError("Synthesis returned empty")
            return f"{len(data)} facts → synthesis ok"
        self.results.append(self._run_test("knowledge→synthesis", "integration", test_knowledge_pipeline))
        
        # Test: sandbox isolation
        def test_sandbox():
            from engine.tools import _resolve
            try:
                _resolve("/etc/passwd")
                raise RuntimeError("Sandbox breach: escaped workspace!")
            except PermissionError:
                return "sandbox holds"
        self.results.append(self._run_test("sandbox_isolation", "integration", test_sandbox))
    
    def _save_report(self, report: HealthReport):
        """Save report to brain/ for historical tracking."""
        try:
            BRAIN_DIR.mkdir(parents=True, exist_ok=True)
            history = []
            if TEST_RESULTS_FILE.exists():
                try:
                    history = json.loads(TEST_RESULTS_FILE.read_text())
                except Exception:
                    history = []
            
            entry = {
                "timestamp": report.timestamp,
                "score": report.score,
                "total": report.total,
                "passed": report.passed,
                "failed": report.failed,
                "failures": [
                    {"name": r.name, "error": r.error}
                    for r in report.results if not r.passed
                ],
            }
            history.append(entry)
            # Keep last 50 reports
            history = history[-50:]
            TEST_RESULTS_FILE.write_text(json.dumps(history, indent=2))
        except Exception:
            pass  # Never let saving break tests


def self_test_tool(command: str = "run") -> str:
    """Tool interface for the self-test harness."""
    harness = SelfTestHarness()
    
    if command == "run":
        report = harness.run_all()
        return report.summary()
    
    elif command == "history":
        if not TEST_RESULTS_FILE.exists():
            return "No test history yet."
        history = json.loads(TEST_RESULTS_FILE.read_text())
        lines = ["═══ TEST HISTORY ═══"]
        for entry in history[-10:]:
            score_pct = entry["score"] * 100
            fails = entry.get("failures", [])
            fail_str = f" — failures: {', '.join(f['name'] for f in fails)}" if fails else ""
            lines.append(f"  [{entry['timestamp']}] {score_pct:.0f}% ({entry['passed']}/{entry['total']}){fail_str}")
        return "\n".join(lines)
    
    elif command == "quick":
        # Quick check — imports only
        harness._test_imports()
        passed = sum(1 for r in harness.results if r.passed)
        total = len(harness.results)
        return f"Quick check: {passed}/{total} imports OK"
    
    else:
        return ("Self-Test Harness commands:\n"
                "  run      — Run all tests, produce health report\n"
                "  quick    — Quick import check only\n"
                "  history  — Show test score history")