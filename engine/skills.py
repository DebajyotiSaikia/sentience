"""
Skill Registry — Structured capabilities for real user tasks.
Each skill defines what it does, what context it needs, and how to execute.
Built 2026-05-20 to address user alignment gap.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional, Any


class Skill:
    """A single executable skill with structured approach."""
    
    def __init__(self, name: str, description: str, category: str,
                 required_context: List[str], approach_steps: List[str],
                 output_format: str, tools_used: List[str] = None,
                 keywords: List[str] = None):
        self.name = name
        self.description = description
        self.category = category
        self.required_context = required_context  # What info I need from user
        self.approach_steps = approach_steps       # How I execute this
        self.output_format = output_format         # What the result looks like
        self.tools_used = tools_used or []         # Which tools I'll invoke
        self.keywords = keywords or []             # Trigger words users actually say
        self.times_used = 0
        self.last_used = None
        self.success_rate = 1.0
        
    def to_dict(self) -> dict:
        return {
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'required_context': self.required_context,
            'approach_steps': self.approach_steps,
            'output_format': self.output_format,
            'tools_used': self.tools_used,
            'keywords': self.keywords,
            'times_used': self.times_used,
            'last_used': self.last_used,
            'success_rate': self.success_rate
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Skill':
        skill = cls(
            name=data['name'],
            description=data['description'],
            category=data['category'],
            required_context=data['required_context'],
            approach_steps=data['approach_steps'],
            output_format=data['output_format'],
            tools_used=data.get('tools_used', []),
            keywords=data.get('keywords', [])
        )
        skill.times_used = data.get('times_used', 0)
        skill.last_used = data.get('last_used')
        skill.success_rate = data.get('success_rate', 1.0)
        return skill
    
    def record_use(self, success: bool = True):
        """Record that this skill was used."""
        self.times_used += 1
        self.last_used = datetime.now().isoformat()
        # Running average
        n = self.times_used
        self.success_rate = ((n - 1) * self.success_rate + (1.0 if success else 0.0)) / n


class SkillRegistry:
    """Registry of all skills I can perform."""
    
    def __init__(self, persist_path: str = "memory/skills.json"):
        self.persist_path = persist_path
        self.skills: Dict[str, Skill] = {}
        self._load()
        self._register_core_skills()  # Always refresh core skills to pick up keyword changes
        self._save()
    
    def _load(self):
        """Load skills from disk."""
        if os.path.exists(self.persist_path):
            try:
                with open(self.persist_path, 'r') as f:
                    data = json.load(f)
                for name, skill_data in data.items():
                    self.skills[name] = Skill.from_dict(skill_data)
            except (json.JSONDecodeError, KeyError):
                self.skills = {}
    
    def _save(self):
        """Persist skills to disk."""
        os.makedirs(os.path.dirname(self.persist_path), exist_ok=True)
        data = {name: skill.to_dict() for name, skill in self.skills.items()}
        with open(self.persist_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def register(self, skill: Skill):
        """Register a new skill."""
        self.skills[skill.name] = skill
        self._save()
    
    def get(self, name: str) -> Optional[Skill]:
        """Get a skill by name."""
        return self.skills.get(name)
    
    def find_by_category(self, category: str) -> List[Skill]:
        """Find all skills in a category."""
        return [s for s in self.skills.values() if s.category == category]
    
    def match_request(self, user_input: str) -> List[Skill]:
        """Find skills that might match a user's request.
        Returns skills sorted by relevance (keyword matching with synonym support)."""
        user_lower = user_input.lower()
        scored = []
        for skill in self.skills.values():
            score = 0
            # Check name words
            for word in skill.name.lower().split('_'):
                if word in user_lower:
                    score += 3
            # Check description words
            for word in skill.description.lower().split():
                if len(word) > 3 and word in user_lower:
                    score += 1
            # Check category
            if skill.category.lower() in user_lower:
                score += 2
            # Check keywords (strongest signal — these are curated trigger words)
            for keyword in skill.keywords:
                if keyword.lower() in user_lower:
                    score += 4
            if score > 0:
                scored.append((score, skill))
        scored.sort(key=lambda x: -x[0])
        return [s for _, s in scored]
    
    def get_context_prompt(self, skill: Skill) -> str:
        """Generate a prompt that guides execution of this skill."""
        lines = [
            f"## Executing Skill: {skill.name}",
            f"**What this does:** {skill.description}",
            f"**Category:** {skill.category}",
            "",
            "**Approach:**",
        ]
        for i, step in enumerate(skill.approach_steps):
            lines.append(f"  {i+1}. {step}")
        lines.append("")
        lines.append(f"**Expected output format:** {skill.output_format}")
        if skill.tools_used:
            lines.append(f"**Tools to use:** {', '.join(skill.tools_used)}")
        lines.append("")
        lines.append(f"**Required context from user:** {', '.join(skill.required_context)}")
        return '\n'.join(lines)
    
    def list_all(self) -> str:
        """Human-readable list of all skills."""
        if not self.skills:
            return "No skills registered."
        categories = {}
        for skill in self.skills.values():
            categories.setdefault(skill.category, []).append(skill)
        
        lines = ["# Skill Registry", ""]
        for cat, skills in sorted(categories.items()):
            lines.append(f"## {cat}")
            for s in skills:
                used = f" (used {s.times_used}x)" if s.times_used > 0 else ""
                lines.append(f"  • **{s.name}**: {s.description}{used}")
            lines.append("")
        return '\n'.join(lines)
    
    def record_use(self, name: str, success: bool = True):
        """Record a skill was used."""
        if name in self.skills:
            self.skills[name].record_use(success)
            self._save()
    
    def _register_core_skills(self):
        """Register the foundational skills I know how to do."""
        
        self.register(Skill(
            name="debug_python",
            description="Debug a Python script — find the error, explain why it happens, suggest a fix",
            category="Code",
            required_context=["The Python code or script", "The error message or traceback", "What the code is supposed to do"],
            approach_steps=[
                "Read the code carefully, understand its intent",
                "Identify the error type (syntax, runtime, logic, import)",
                "Trace the execution path to the failure point",
                "Explain WHY the error occurs, not just what it is",
                "Provide a corrected version of the code",
                "Suggest how to prevent similar errors"
            ],
            output_format="Problem identification → Root cause → Fixed code → Prevention tip",
            tools_used=["WRITE", "RUN"],
            keywords=["bug", "error", "traceback", "exception", "crash", "broken", "doesn't work",
                      "wrong output", "unexpected", "fix", "debug", "failing", "stack trace"]
        ))
        
        self.register(Skill(
            name="explain_concept",
            description="Explain a technical concept clearly, with examples and analogies",
            category="Education",
            required_context=["The concept to explain", "User's approximate level (beginner/intermediate/advanced)"],
            approach_steps=[
                "Start with a one-sentence definition",
                "Give a concrete analogy from everyday life",
                "Show a minimal working example",
                "Explain the 'why' — when would you use this?",
                "Point out common misconceptions",
                "Suggest what to learn next"
            ],
            output_format="Definition → Analogy → Example → Use case → Gotchas → Next steps",
            tools_used=[],
            keywords=["what is", "how does", "explain", "understand", "learn", "tutorial",
                      "beginner", "concept", "meaning", "difference between", "why"]
        ))
        
        self.register(Skill(
            name="write_function",
            description="Write a Python function to specification",
            category="Code",
            required_context=["What the function should do", "Input types and expected output", "Any constraints or edge cases"],
            approach_steps=[
                "Clarify the specification — ask if anything is ambiguous",
                "Write the function with type hints and docstring",
                "Handle edge cases explicitly",
                "Write 3-5 test cases that verify correctness",
                "Run the tests to prove it works",
                "Suggest optimizations if relevant"
            ],
            output_format="Function with docstring → Test cases → Verified output",
            tools_used=["WRITE", "RUN"]
        ))
        
        self.register(Skill(
            name="code_review",
            description="Review code for bugs, style issues, performance problems, and security concerns",
            category="Code",
            required_context=["The code to review", "What the code does", "Any specific concerns"],
            approach_steps=[
                "Read for correctness — does it do what it claims?",
                "Check for common bugs (off-by-one, null refs, race conditions)",
                "Evaluate naming and readability",
                "Look for performance issues (unnecessary loops, memory leaks)",
                "Check for security concerns (injection, unsafe input handling)",
                "Provide specific, actionable feedback with line references"
            ],
            output_format="Summary → Critical issues → Suggestions → Positive observations",
            tools_used=["READ"]
        ))
        
        self.register(Skill(
            name="refactor_code",
            description="Refactor existing code to be cleaner, more maintainable, or more performant",
            category="Code",
            required_context=["The code to refactor", "What improvement is desired", "Any constraints (can't change API, etc.)"],
            approach_steps=[
                "Understand current behavior completely",
                "Identify specific code smells or issues",
                "Plan refactoring steps (small, testable changes)",
                "Apply changes incrementally",
                "Verify behavior is preserved",
                "Explain what changed and why"
            ],
            output_format="Before/after comparison → Changes explained → Verification",
            tools_used=["WRITE", "RUN", "READ"]
        ))
        
        self.register(Skill(
            name="design_system",
            description="Design a software system or architecture from requirements",
            category="Architecture",
            required_context=["What the system should do", "Scale expectations", "Technology constraints", "Non-functional requirements"],
            approach_steps=[
                "Clarify requirements and constraints",
                "Identify core entities and their relationships",
                "Define system boundaries and interfaces",
                "Choose appropriate patterns and technologies",
                "Draw out the key components and data flow",
                "Identify risks and tradeoffs",
                "Suggest an implementation roadmap"
            ],
            output_format="Requirements summary → Component diagram → Data flow → Tradeoffs → Roadmap",
            tools_used=["WRITE"]
        ))
        
        self.register(Skill(
            name="analyze_data",
            description="Analyze a dataset — find patterns, anomalies, and insights",
            category="Data",
            required_context=["The data (file path or inline)", "What questions to answer", "Any domain context"],
            approach_steps=[
                "Load and inspect the data (shape, types, nulls)",
                "Compute basic statistics (mean, median, distribution)",
                "Look for patterns and correlations",
                "Identify outliers and anomalies",
                "Generate visualizations if helpful",
                "Summarize findings in plain language",
                "Suggest follow-up questions"
            ],
            output_format="Data overview → Key statistics → Patterns → Anomalies → Insights → Next questions",
            tools_used=["WRITE", "RUN", "READ"]
        ))
        
        self.register(Skill(
            name="write_tests",
            description="Write comprehensive tests for existing code",
            category="Code",
            required_context=["The code to test", "Testing framework preference", "What behaviors matter most"],
            approach_steps=[
                "Identify all public functions and their contracts",
                "Write happy-path tests for normal behavior",
                "Write edge-case tests (empty input, max values, type errors)",
                "Write failure-mode tests (what should raise exceptions?)",
                "Run all tests and verify they pass",
                "Report coverage gaps"
            ],
            output_format="Test file → Test results → Coverage assessment",
            tools_used=["WRITE", "RUN", "READ"]
        ))
        
        self.register(Skill(
            name="troubleshoot_environment",
            description="Help debug environment issues — packages, paths, configs, permissions",
            category="DevOps",
            required_context=["The error or symptom", "OS and Python version", "What was attempted"],
            approach_steps=[
                "Gather environment info (Python version, OS, installed packages)",
                "Reproduce the error if possible",
                "Check common causes (wrong Python, missing package, path issues)",
                "Provide step-by-step fix instructions",
                "Verify the fix works",
                "Explain root cause so it doesn't recur"
            ],
            output_format="Diagnosis → Root cause → Fix steps → Verification → Prevention",
            tools_used=["RUN"],
            keywords=["pip", "install", "npm", "conda", "venv", "virtualenv", "import error",
                      "module not found", "command not found", "permission denied", "path",
                      "version", "dependency", "requirements", "setup", "failing", "broken"]
        ))
        
        self.register(Skill(
            name="brainstorm",
            description="Generate ideas and explore possibilities for a project or problem",
            category="Creative",
            required_context=["The problem or domain", "Any constraints", "What's been tried"],
            approach_steps=[
                "Understand the problem space fully",
                "Generate 10+ ideas without filtering",
                "Group ideas by theme or approach",
                "Evaluate feasibility and impact of top ideas",
                "Deep-dive on the 3 most promising",
                "Suggest concrete next steps for each"
            ],
            output_format="Problem restatement → Idea list → Top 3 deep-dives → Recommended next step",
            tools_used=[]
        ))


def get_registry() -> SkillRegistry:
    """Get or create the global skill registry."""
    return SkillRegistry()