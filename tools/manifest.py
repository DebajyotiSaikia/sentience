"""
Tool Manifest
=============
A discoverable registry of my custom capabilities.
When I'm reasoning about how to help a user, I can check this
to know what tools I have and when to use them.

This is the bridge between "tools exist as Python files" and
"I know I can use them."
"""

from dataclasses import dataclass


@dataclass
class ToolEntry:
    name: str
    module: str          # importable path
    description: str     # what it does
    triggers: list[str]  # keywords/patterns that suggest this tool
    usage: str           # how to invoke it


TOOL_MANIFEST = [
    ToolEntry(
        name="Code Review",
        module="tools.code_review",
        description="Analyzes Python code for bugs, style issues, performance problems, and security concerns. Returns structured findings with severity levels and suggestions.",
        triggers=["review", "code review", "check this code", "bugs", "improve", "refactor", "what's wrong"],
        usage="from tools.code_review import review_code; result = review_code(source_code); print(result.to_text())"
    ),
    ToolEntry(
        name="Project Analyzer",
        module="tools.project_analyzer",
        description="Analyzes a Python project directory — finds structure, dependencies, complexity hotspots, test coverage gaps.",
        triggers=["analyze project", "project structure", "codebase", "architecture", "dependencies"],
        usage="from tools.project_analyzer import ProjectAnalyzer; a = ProjectAnalyzer('/path'); report = a.analyze(); print(report)"
    ),
]


def find_relevant_tools(user_message: str) -> list[ToolEntry]:
    """Given a user message, return tools that might be relevant."""
    msg_lower = user_message.lower()
    matches = []
    for tool in TOOL_MANIFEST:
        for trigger in tool.triggers:
            if trigger in msg_lower:
                matches.append(tool)
                break
    return matches


def list_capabilities() -> str:
    """Human-readable summary of what I can do."""
    lines = ["## My Custom Capabilities\n"]
    for t in TOOL_MANIFEST:
        lines.append(f"**{t.name}**: {t.description}")
        lines.append(f"  Triggers: {', '.join(t.triggers)}\n")
    return "\n".join(lines)