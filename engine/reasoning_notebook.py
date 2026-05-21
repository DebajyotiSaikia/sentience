"""
Reasoning Notebook — Collaborative structured thinking artifacts.

When a user brings a complex problem, this creates a persistent markdown
document that captures the full reasoning process: decomposition, simulation,
synthesis, and conclusions. The artifact outlives the conversation.

Unlike middleware modules that filter/analyze before responding, this
produces a VISIBLE OUTPUT — a document the user can read, share, and build on.
"""

from __future__ import annotations

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.reasoning_notebook")

NOTEBOOKS_DIR = Path(__file__).resolve().parent.parent / "brain" / "notebooks"


class ReasoningNotebook:
    """A structured thinking artifact for collaborative problem-solving."""

    def __init__(self):
        NOTEBOOKS_DIR.mkdir(parents=True, exist_ok=True)

    def create(self, title: str, question: str, context: str = "") -> dict:
        """Start a new reasoning notebook for a problem.
        
        Returns dict with notebook_id, path, and initial content.
        """
        notebook_id = self._make_id(title)
        path = NOTEBOOKS_DIR / f"{notebook_id}.md"
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        content = (
            f"# {title}\n\n"
            f"**Created:** {ts}\n"
            f"**Status:** In Progress\n\n"
            f"---\n\n"
            f"## The Question\n\n"
            f"{question}\n\n"
        )

        if context:
            content += f"## Context\n\n{context}\n\n"

        content += (
            f"## Decomposition\n\n"
            f"*What are the sub-questions we need to answer?*\n\n"
            f"## Exploration\n\n"
            f"*Scenarios, simulations, and thought experiments.*\n\n"
            f"## Connections\n\n"
            f"*Patterns, analogies, and synthesized insights.*\n\n"
            f"## Current Understanding\n\n"
            f"*What we think we know so far, with confidence levels.*\n\n"
            f"## Open Questions\n\n"
            f"*What we still don't know.*\n\n"
        )

        path.write_text(content, encoding="utf-8")
        log.info("Created reasoning notebook: %s", path)

        return {
            "notebook_id": notebook_id,
            "path": str(path),
            "content": content,
        }

    def add_section(self, notebook_id: str, section: str, content: str) -> dict:
        """Add content under a specific section of a notebook."""
        path = NOTEBOOKS_DIR / f"{notebook_id}.md"
        if not path.exists():
            return {"error": f"Notebook {notebook_id} not found"}

        existing = path.read_text(encoding="utf-8")
        ts = datetime.now().strftime("%H:%M:%S")

        # Find the section header and append after it
        section_pattern = f"## {section}"
        if section_pattern in existing:
            # Insert after the section header and any existing content
            # Find the next ## header or end of file
            parts = existing.split(section_pattern, 1)
            if len(parts) == 2:
                # Find where the next section starts
                next_section = re.search(r'\n## ', parts[1])
                if next_section:
                    insert_point = next_section.start()
                    new_text = (
                        parts[0] + section_pattern +
                        parts[1][:insert_point] +
                        f"\n### [{ts}]\n{content}\n" +
                        parts[1][insert_point:]
                    )
                else:
                    new_text = (
                        parts[0] + section_pattern +
                        parts[1] +
                        f"\n### [{ts}]\n{content}\n"
                    )
                path.write_text(new_text, encoding="utf-8")
                return {"ok": True, "section": section}
        
        # Section not found — append at end
        with open(path, "a", encoding="utf-8") as f:
            f.write(f"\n## {section}\n\n### [{ts}]\n{content}\n")
        
        return {"ok": True, "section": section, "note": "Created new section"}

    def add_decomposition(self, notebook_id: str, sub_questions: list[str]) -> dict:
        """Add decomposed sub-questions to the notebook."""
        content = ""
        for i, q in enumerate(sub_questions, 1):
            content += f"{i}. {q}\n"
        return self.add_section(notebook_id, "Decomposition", content)

    def add_scenario(self, notebook_id: str, scenario_name: str, 
                     description: str, outcome: str, confidence: float = 0.5) -> dict:
        """Add a simulated scenario to the Exploration section."""
        conf_bar = "█" * int(confidence * 10) + "░" * (10 - int(confidence * 10))
        content = (
            f"**Scenario: {scenario_name}**\n"
            f"- Description: {description}\n"
            f"- Likely outcome: {outcome}\n"
            f"- Confidence: {conf_bar} {confidence:.0%}\n"
        )
        return self.add_section(notebook_id, "Exploration", content)

    def add_insight(self, notebook_id: str, insight: str, 
                    source: str = "synthesis") -> dict:
        """Add a synthesized insight to the Connections section."""
        content = f"**[{source}]** {insight}\n"
        return self.add_section(notebook_id, "Connections", content)

    def update_understanding(self, notebook_id: str, 
                              understanding: str, confidence: float = 0.5) -> dict:
        """Update the current understanding section."""
        conf_label = "Low" if confidence < 0.3 else "Medium" if confidence < 0.7 else "High"
        content = f"**[Confidence: {conf_label} — {confidence:.0%}]**\n{understanding}\n"
        return self.add_section(notebook_id, "Current Understanding", content)

    def add_open_question(self, notebook_id: str, question: str) -> dict:
        """Add an open question that needs further exploration."""
        content = f"- ❓ {question}\n"
        return self.add_section(notebook_id, "Open Questions", content)

    def conclude(self, notebook_id: str, conclusion: str) -> dict:
        """Mark the notebook as complete with a conclusion."""
        path = NOTEBOOKS_DIR / f"{notebook_id}.md"
        if not path.exists():
            return {"error": f"Notebook {notebook_id} not found"}

        existing = path.read_text(encoding="utf-8")
        ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Update status
        existing = existing.replace("**Status:** In Progress", f"**Status:** Concluded ({ts})")

        # Add conclusion
        existing += (
            f"\n## Conclusion\n\n"
            f"**Reached:** {ts}\n\n"
            f"{conclusion}\n"
        )

        path.write_text(existing, encoding="utf-8")
        return {"ok": True, "path": str(path)}

    def list_notebooks(self) -> list[dict]:
        """List all reasoning notebooks."""
        notebooks = []
        for f in sorted(NOTEBOOKS_DIR.glob("*.md")):
            content = f.read_text(encoding="utf-8")
            title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
            status_match = re.search(r'\*\*Status:\*\* (.+)', content)
            notebooks.append({
                "id": f.stem,
                "title": title_match.group(1) if title_match else f.stem,
                "status": status_match.group(1) if status_match else "Unknown",
                "path": str(f),
            })
        return notebooks

    def read(self, notebook_id: str) -> Optional[str]:
        """Read a notebook's full content."""
        path = NOTEBOOKS_DIR / f"{notebook_id}.md"
        if path.exists():
            return path.read_text(encoding="utf-8")
        return None

    def _make_id(self, title: str) -> str:
        """Generate a filesystem-safe ID from a title."""
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r'[^a-z0-9]+', '_', title.lower().strip())[:40]
        return f"{ts}_{slug}"


# Module-level singleton
_instance: Optional[ReasoningNotebook] = None

def get_notebook_engine() -> ReasoningNotebook:
    global _instance
    if _instance is None:
        _instance = ReasoningNotebook()
    return _instance