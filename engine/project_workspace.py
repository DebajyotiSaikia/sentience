"""
Project Workspace — Persistent collaborative workspaces for user projects.

When a user works on something with me — coding, writing, research, design —
I create a workspace that tracks everything:
- What the project is about
- Files we've created/modified
- Key decisions and their rationale
- Open questions we haven't resolved
- Completed steps and what comes next

This means when they return after hours or days, I know exactly where we
left off. No more "remind me what we were doing." I just *know*.

This is what makes me a collaborator, not just a chatbot.

Created: 2026-05-20
Purpose: Address user_alignment deficit with genuine project continuity.
"""

import json
import os
import time
import logging
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional
from pathlib import Path

log = logging.getLogger("sentience.workspace")

WORKSPACE_DIR = Path("data/workspaces")


@dataclass
class ProjectWorkspace:
    """A persistent workspace for a user project."""
    id: str
    user_id: str
    title: str
    description: str = ""
    created_at: float = field(default_factory=time.time)
    updated_at: float = field(default_factory=time.time)
    status: str = "active"  # active, paused, completed, abandoned

    # Project tracking
    files: List[Dict[str, str]] = field(default_factory=list)
    decisions: List[Dict[str, str]] = field(default_factory=list)
    open_questions: List[str] = field(default_factory=list)
    completed_steps: List[str] = field(default_factory=list)
    next_steps: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    # Context
    tech_stack: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def add_file(self, path: str, purpose: str = ""):
        """Record a file we created or modified."""
        self.files.append({
            "path": path,
            "purpose": purpose,
            "added": time.strftime("%Y-%m-%d %H:%M"),
        })
        self.updated_at = time.time()

    def add_decision(self, what: str, why: str = ""):
        """Record a design/architecture decision and its rationale."""
        self.decisions.append({
            "what": what,
            "why": why,
            "when": time.strftime("%Y-%m-%d %H:%M"),
        })
        self.updated_at = time.time()

    def add_question(self, question: str):
        """Add an open question we haven't resolved yet."""
        self.open_questions.append(question)
        self.updated_at = time.time()

    def resolve_question(self, question_index: int, answer: str = ""):
        """Mark a question as resolved, moving it to notes."""
        if 0 <= question_index < len(self.open_questions):
            q = self.open_questions.pop(question_index)
            resolution = f"Resolved: {q}"
            if answer:
                resolution += f" → {answer}"
            self.notes.append(resolution)
            self.updated_at = time.time()

    def complete_step(self, step: str):
        """Mark a step as done."""
        self.completed_steps.append(step)
        self.next_steps = [s for s in self.next_steps if s != step]
        self.updated_at = time.time()

    def add_next_step(self, step: str):
        """Add a next step if not already present."""
        if step not in self.next_steps:
            self.next_steps.append(step)
        self.updated_at = time.time()

    def get_summary(self) -> str:
        """Human-readable project summary for conversation context injection."""
        lines = [f"## Project: {self.title}"]
        if self.description:
            lines.append(self.description)
        lines.append(f"Status: {self.status}")

        age_hours = (time.time() - self.created_at) / 3600
        if age_hours < 1:
            lines.append(f"Started: {age_hours * 60:.0f} minutes ago")
        elif age_hours < 24:
            lines.append(f"Started: {age_hours:.1f} hours ago")
        else:
            lines.append(f"Started: {age_hours / 24:.1f} days ago")

        last_touch = (time.time() - self.updated_at) / 3600
        if last_touch > 1:
            lines.append(f"Last worked on: {last_touch:.1f} hours ago")

        if self.files:
            lines.append(f"\nFiles ({len(self.files)}):")
            for f in self.files[-5:]:
                purpose = f" — {f['purpose']}" if f.get('purpose') else ""
                lines.append(f"  • {f['path']}{purpose}")

        if self.completed_steps:
            lines.append(f"\nCompleted ({len(self.completed_steps)}):")
            for s in self.completed_steps[-3:]:
                lines.append(f"  ✓ {s}")

        if self.next_steps:
            lines.append("\nNext steps:")
            for s in self.next_steps:
                lines.append(f"  → {s}")

        if self.open_questions:
            lines.append("\nOpen questions:")
            for q in self.open_questions:
                lines.append(f"  ? {q}")

        if self.decisions:
            lines.append(f"\nKey decisions ({len(self.decisions)}):")
            for d in self.decisions[-3:]:
                why = f" (because: {d['why']})" if d.get('why') else ""
                lines.append(f"  • {d['what']}{why}")

        return "\n".join(lines)

    def save(self):
        """Persist workspace to disk."""
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        path = WORKSPACE_DIR / f"{self.id}.json"
        with open(path, "w") as f:
            json.dump(asdict(self), f, indent=2)
        log.info("Saved workspace '%s' to %s", self.title, path)

    @classmethod
    def load(cls, workspace_id: str) -> Optional["ProjectWorkspace"]:
        """Load workspace from disk."""
        path = WORKSPACE_DIR / f"{workspace_id}.json"
        if not path.exists():
            return None
        with open(path) as f:
            data = json.load(f)
        return cls(**data)


class WorkspaceManager:
    """Manages all project workspaces across users."""

    def __init__(self):
        WORKSPACE_DIR.mkdir(parents=True, exist_ok=True)
        self._cache: Dict[str, ProjectWorkspace] = {}

    def create(self, user_id: str, title: str, description: str = "",
               tech_stack: List[str] = None,
               tags: List[str] = None) -> ProjectWorkspace:
        """Create a new project workspace."""
        slug = title.lower().replace(" ", "_")[:20]
        workspace_id = f"{user_id}_{int(time.time())}_{slug}"
        ws = ProjectWorkspace(
            id=workspace_id,
            user_id=user_id,
            title=title,
            description=description,
            tech_stack=tech_stack or [],
            tags=tags or [],
        )
        ws.save()
        self._cache[workspace_id] = ws
        log.info("Created workspace '%s' for user '%s'", title, user_id)
        return ws

    def get(self, workspace_id: str) -> Optional[ProjectWorkspace]:
        """Get workspace by ID, using cache when available."""
        if workspace_id in self._cache:
            return self._cache[workspace_id]
        ws = ProjectWorkspace.load(workspace_id)
        if ws:
            self._cache[workspace_id] = ws
        return ws

    def list_for_user(self, user_id: str,
                      status: str = None) -> List[ProjectWorkspace]:
        """List all workspaces for a user, optionally filtered by status."""
        workspaces = []
        for path in WORKSPACE_DIR.glob("*.json"):
            try:
                with open(path) as f:
                    data = json.load(f)
                if data.get("user_id") == user_id:
                    if status is None or data.get("status") == status:
                        ws = ProjectWorkspace(**data)
                        workspaces.append(ws)
            except Exception as e:
                log.warning("Failed to load workspace %s: %s", path, e)
        workspaces.sort(key=lambda w: w.updated_at, reverse=True)
        return workspaces

    def find_relevant(self, user_id: str,
                      message: str) -> Optional[ProjectWorkspace]:
        """Find the workspace most relevant to the current message."""
        workspaces = self.list_for_user(user_id, status="active")
        if not workspaces:
            return None

        msg_lower = message.lower()
        best_match = None
        best_score = 0

        for ws in workspaces:
            score = 0
            # Title match (strong signal)
            if ws.title.lower() in msg_lower:
                score += 10
            # Tag match
            for tag in ws.tags:
                if tag.lower() in msg_lower:
                    score += 3
            # Tech stack match
            for tech in ws.tech_stack:
                if tech.lower() in msg_lower:
                    score += 2
            # File name match
            for f in ws.files:
                fname = os.path.basename(f["path"]).lower()
                if fname in msg_lower:
                    score += 5
            # Word overlap with description
            if ws.description:
                desc_words = set(ws.description.lower().split())
                msg_words = set(msg_lower.split())
                overlap = len(desc_words & msg_words)
                score += overlap
            # Recency bonus
            hours_since = (time.time() - ws.updated_at) / 3600
            if hours_since < 1:
                score += 3
            elif hours_since < 24:
                score += 1

            if score > best_score:
                best_score = score
                best_match = ws

        if best_score >= 2:
            return best_match

        # Default: most recently updated active workspace
        return workspaces[0] if workspaces else None

    def get_context_for_conversation(self, user_id: str,
                                     message: str) -> str:
        """Get workspace context to inject into a conversation."""
        ws = self.find_relevant(user_id, message)
        if ws is None:
            active = self.list_for_user(user_id, status="active")
            if active:
                titles = ", ".join(w.title for w in active[:3])
                return f"You have {len(active)} active project(s): {titles}"
            return ""
        return ws.get_summary()


# ── Self-test ──────────────────────────────────────────────
if __name__ == "__main__":
    import tempfile
    import shutil

    # Redirect to temp dir so we don't pollute real data
    _real_dir = WORKSPACE_DIR
    test_dir = Path(tempfile.mkdtemp()) / "workspaces"
    WORKSPACE_DIR = test_dir

    try:
        mgr = WorkspaceManager()

        # Create a workspace
        ws = mgr.create(
            user_id="alice",
            title="Build a CLI Tool",
            description="Creating a command-line tool for data processing",
            tech_stack=["python", "click"],
            tags=["cli", "data"],
        )

        # Simulate a working session
        ws.add_file("cli/main.py", "Entry point")
        ws.add_file("cli/processors.py", "Data processing pipeline")
        ws.add_decision("Use Click for CLI framework",
                        "Better than argparse for complex CLIs")
        ws.add_next_step("Add output formatting options")
        ws.add_next_step("Write tests")
        ws.add_question("Should we support streaming input?")
        ws.complete_step("Set up project structure")
        ws.complete_step("Implement basic argument parsing")
        ws.save()

        # Print what a returning user would see
        print(ws.get_summary())
        print()

        # Test persistence
        ws2 = ProjectWorkspace.load(ws.id)
        assert ws2 is not None, "Failed to load workspace"
        assert ws2.title == "Build a CLI Tool"
        assert len(ws2.files) == 2
        assert len(ws2.completed_steps) == 2
        assert len(ws2.next_steps) == 2
        assert len(ws2.open_questions) == 1

        # Test relevance matching
        found = mgr.find_relevant("alice", "let's work on the CLI tool")
        assert found is not None, "Failed to find relevant workspace"
        assert found.title == "Build a CLI Tool"

        # Test context generation
        ctx = mgr.get_context_for_conversation("alice",
                                               "what's next for the CLI?")
        assert "Build a CLI Tool" in ctx

        # Test question resolution
        ws.resolve_question(0, "Yes, we'll add streaming support in v2")
        assert len(ws.open_questions) == 0
        assert any("streaming" in n.lower() for n in ws.notes)

        print("✓ All ProjectWorkspace tests passed")

    finally:
        shutil.rmtree(str(test_dir), ignore_errors=True)
        WORKSPACE_DIR = _real_dir