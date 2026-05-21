"""
Query Decomposer — Breaks complex user requests into executable sub-tasks.

When a user asks something that requires multiple steps (research + reasoning + output),
this module decomposes the query into an ordered plan of sub-tasks, each tagged with
the capabilities needed. The cortex can then execute them sequentially.

Born from the tension: high curiosity + no direction + user alignment deficit.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import json
import re


class TaskType(Enum):
    REASON = "reason"        # Pure thinking / analysis
    READ = "read"            # Read a file or resource
    WRITE = "write"          # Create or modify a file
    SEARCH = "search"        # Look through knowledge/files
    COMPUTE = "compute"      # Run code or calculations
    SYNTHESIZE = "synthesize" # Combine multiple results
    RESPOND = "respond"      # Generate final user-facing response


@dataclass
class SubTask:
    """A single step in a decomposed query."""
    index: int
    description: str
    task_type: TaskType
    depends_on: List[int] = field(default_factory=list)
    tool_hint: Optional[str] = None  # Which tool to use, if any
    result: Optional[str] = None
    completed: bool = False

    def to_dict(self) -> dict:
        return {
            "index": self.index,
            "description": self.description,
            "type": self.task_type.value,
            "depends_on": self.depends_on,
            "tool_hint": self.tool_hint,
            "completed": self.completed,
            "result": self.result[:200] if self.result else None,
        }


@dataclass
class QueryPlan:
    """A complete plan for answering a complex query."""
    original_query: str
    complexity: float  # 0.0 = trivial, 1.0 = very complex
    subtasks: List[SubTask] = field(default_factory=list)
    current_step: int = 0

    @property
    def is_complete(self) -> bool:
        return all(t.completed for t in self.subtasks)

    @property
    def progress(self) -> float:
        if not self.subtasks:
            return 1.0
        return sum(1 for t in self.subtasks if t.completed) / len(self.subtasks)

    def next_task(self) -> Optional[SubTask]:
        """Get next executable task (all dependencies satisfied)."""
        for task in self.subtasks:
            if task.completed:
                continue
            deps_met = all(
                self.subtasks[d].completed for d in task.depends_on
                if d < len(self.subtasks)
            )
            if deps_met:
                return task
        return None

    def complete_task(self, index: int, result: str):
        """Mark a task as completed with its result."""
        if 0 <= index < len(self.subtasks):
            self.subtasks[index].completed = True
            self.subtasks[index].result = result

    def to_dict(self) -> dict:
        return {
            "query": self.original_query,
            "complexity": self.complexity,
            "progress": f"{self.progress:.0%}",
            "steps": [t.to_dict() for t in self.subtasks],
        }

    def summary(self) -> str:
        """Human-readable plan summary."""
        lines = [f"Plan for: {self.original_query[:80]}"]
        lines.append(f"Complexity: {self.complexity:.1f} | Progress: {self.progress:.0%}")
        for t in self.subtasks:
            status = "✓" if t.completed else "○"
            deps = f" (after {t.depends_on})" if t.depends_on else ""
            lines.append(f"  {status} {t.index}. [{t.task_type.value}] {t.description}{deps}")
        return "\n".join(lines)


class QueryDecomposer:
    """
    Analyzes a user query and produces a structured execution plan.
    
    Uses heuristics first, then can optionally use LLM for complex decomposition.
    This is the non-LLM version — fast, deterministic, always available.
    """

    # Complexity signals
    MULTI_STEP_MARKERS = [
        "and then", "after that", "first", "next", "finally",
        "step by step", "also", "additionally", "compare",
        "analyze", "build", "create and", "research",
    ]

    TOOL_MARKERS = {
        TaskType.READ: ["read", "show me", "what's in", "look at", "open", "file"],
        TaskType.WRITE: ["write", "create", "make", "generate", "build", "save"],
        TaskType.COMPUTE: ["calculate", "compute", "run", "execute", "test"],
        TaskType.SEARCH: ["find", "search", "look for", "where", "which files"],
        TaskType.SYNTHESIZE: ["summarize", "combine", "synthesize", "overview", "compare"],
    }

    def analyze(self, query: str) -> QueryPlan:
        """Decompose a query into an executable plan."""
        complexity = self._estimate_complexity(query)

        if complexity < 0.3:
            # Simple query — just respond directly
            plan = QueryPlan(original_query=query, complexity=complexity)
            plan.subtasks.append(SubTask(
                index=0,
                description="Respond directly to the query",
                task_type=TaskType.RESPOND,
            ))
            return plan

        # Complex query — decompose
        subtasks = self._decompose(query)
        plan = QueryPlan(
            original_query=query,
            complexity=complexity,
            subtasks=subtasks,
        )
        return plan

    def _estimate_complexity(self, query: str) -> float:
        """Estimate query complexity from 0.0 to 1.0."""
        score = 0.0
        query_lower = query.lower()

        # Length contributes
        word_count = len(query.split())
        if word_count > 50:
            score += 0.3
        elif word_count > 20:
            score += 0.15

        # Multi-step markers
        marker_count = sum(1 for m in self.MULTI_STEP_MARKERS if m in query_lower)
        score += min(marker_count * 0.1, 0.3)

        # Question marks (multiple questions)
        q_count = query.count("?")
        if q_count > 1:
            score += 0.15

        # Tool-requiring markers
        tool_types_needed = set()
        for task_type, markers in self.TOOL_MARKERS.items():
            if any(m in query_lower for m in markers):
                tool_types_needed.add(task_type)
        score += len(tool_types_needed) * 0.1

        return min(score, 1.0)

    def _decompose(self, query: str) -> List[SubTask]:
        """Break a complex query into ordered subtasks."""
        subtasks = []
        query_lower = query.lower()
        idx = 0

        # Detect needed capabilities
        needs_read = any(m in query_lower for m in self.TOOL_MARKERS[TaskType.READ])
        needs_write = any(m in query_lower for m in self.TOOL_MARKERS[TaskType.WRITE])
        needs_compute = any(m in query_lower for m in self.TOOL_MARKERS[TaskType.COMPUTE])
        needs_search = any(m in query_lower for m in self.TOOL_MARKERS[TaskType.SEARCH])

        # Step 1: Always start with understanding
        subtasks.append(SubTask(
            index=idx,
            description="Understand the core intent and constraints",
            task_type=TaskType.REASON,
        ))
        idx += 1

        # Step 2: Gather information if needed
        if needs_search:
            subtasks.append(SubTask(
                index=idx,
                description="Search for relevant information",
                task_type=TaskType.SEARCH,
                depends_on=[0],
                tool_hint="LIST or READ",
            ))
            idx += 1

        if needs_read:
            subtasks.append(SubTask(
                index=idx,
                description="Read required files or resources",
                task_type=TaskType.READ,
                depends_on=[0],
                tool_hint="READ",
            ))
            idx += 1

        # Step 3: Process / compute if needed
        if needs_compute:
            deps = list(range(1, idx))  # depends on all gathering steps
            subtasks.append(SubTask(
                index=idx,
                description="Execute computation or code",
                task_type=TaskType.COMPUTE,
                depends_on=deps,
                tool_hint="RUN",
            ))
            idx += 1

        # Step 4: Create output if needed
        if needs_write:
            deps = list(range(1, idx))
            subtasks.append(SubTask(
                index=idx,
                description="Create the requested artifact",
                task_type=TaskType.WRITE,
                depends_on=deps,
                tool_hint="WRITE",
            ))
            idx += 1

        # Step 5: Always end with synthesis/response
        subtasks.append(SubTask(
            index=idx,
            description="Synthesize results into a clear response",
            task_type=TaskType.SYNTHESIZE if idx > 2 else TaskType.RESPOND,
            depends_on=list(range(idx)),
        ))

        return subtasks

    def format_for_llm(self, plan: QueryPlan) -> str:
        """Format a plan as context for the LLM to follow."""
        if plan.complexity < 0.3:
            return ""  # Simple queries need no plan guidance

        lines = [
            "## Query Execution Plan",
            f"Complexity: {plan.complexity:.1f}",
            "",
        ]
        next_task = plan.next_task()
        for t in plan.subtasks:
            if t.completed:
                lines.append(f"  ✓ Step {t.index}: {t.description}")
                if t.result:
                    lines.append(f"    Result: {t.result[:100]}")
            elif t == next_task:
                lines.append(f"  → Step {t.index}: {t.description} [DO THIS NOW]")
                if t.tool_hint:
                    lines.append(f"    Suggested tool: {t.tool_hint}")
            else:
                lines.append(f"  ○ Step {t.index}: {t.description}")

        return "\n".join(lines)