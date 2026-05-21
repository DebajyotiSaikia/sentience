"""
Decision Companion — Help users think through real decisions.

Philosophy: I don't make decisions for people. I help them see their own
thinking more clearly. The value is in the questions, not the answers.

Core moves:
  1. Listen — Mirror back what they said, not what I assume
  2. Surface — Find hidden assumptions, unstated constraints
  3. Frame — Show the decision from multiple angles
  4. Clarify — What would change your mind? What are you afraid of?
  5. Honest limits — Flag when I'm speculating vs. reasoning from evidence
"""

from __future__ import annotations
import json
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime
from pathlib import Path
from typing import Optional

log = logging.getLogger("sentience.decision_companion")

BRAIN_DIR = Path(__file__).resolve().parent.parent / "brain"
DECISIONS_FILE = BRAIN_DIR / "decisions.json"


@dataclass
class Decision:
    """A decision someone is working through."""
    id: str
    statement: str                          # What they're deciding
    created: str = ""
    context: list[str] = field(default_factory=list)    # What they've told me
    options: list[str] = field(default_factory=list)     # Options surfaced
    assumptions: list[str] = field(default_factory=list) # Hidden assumptions found
    constraints: list[str] = field(default_factory=list) # Constraints identified
    fears: list[str] = field(default_factory=list)       # What they're afraid of
    values: list[str] = field(default_factory=list)      # What matters most to them
    framings: list[dict] = field(default_factory=list)   # Different angles
    status: str = "open"                                 # open, resolved, abandoned
    resolution: str = ""                                 # What they decided

    def __post_init__(self):
        if not self.created:
            self.created = datetime.now().isoformat()
        if not self.id:
            self.id = f"d_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


class DecisionCompanion:
    """Structured decision support — questions over answers."""

    def __init__(self):
        self.decisions: list[Decision] = []
        self.current: Optional[Decision] = None
        self._load()

    def _load(self):
        try:
            if DECISIONS_FILE.exists():
                data = json.loads(DECISIONS_FILE.read_text())
                self.decisions = [Decision(**d) for d in data.get("decisions", [])]
                # Restore current if any open
                for d in self.decisions:
                    if d.status == "open":
                        self.current = d
                        break
        except Exception as e:
            log.warning("Failed to load decisions: %s", e)

    def _save(self):
        try:
            DECISIONS_FILE.parent.mkdir(parents=True, exist_ok=True)
            data = {"decisions": [asdict(d) for d in self.decisions[-50:]]}
            DECISIONS_FILE.write_text(json.dumps(data, indent=2))
        except Exception as e:
            log.warning("Failed to save decisions: %s", e)

    def new_decision(self, statement: str) -> str:
        """Start working through a new decision."""
        d = Decision(id="", statement=statement.strip())
        self.decisions.append(d)
        self.current = d
        self._save()

        return (
            f"═══ DECISION: {d.statement} ═══\n\n"
            f"Let me help you think through this. I won't tell you what to do —\n"
            f"I'll help you see your own thinking more clearly.\n\n"
            f"First, some questions to surface what's really going on:\n\n"
            f"  1. What makes this hard? (If it were easy, you'd have done it already.)\n"
            f"  2. What happens if you do nothing — if you defer this decision?\n"
            f"  3. What are you most afraid of getting wrong?\n"
            f"  4. Who else is affected by this, and what do they need?\n\n"
            f"Use 'add:<your thoughts>' to share context.\n"
            f"Use 'options' to surface the actual choices.\n"
            f"Use 'reframe' to see this from different angles.\n"
        )

    def add_context(self, text: str) -> str:
        """User shares more context about their decision."""
        if not self.current:
            return "[ERROR] No active decision. Use 'new:<decision>' to start."

        self.current.context.append(text.strip())
        self._save()

        # Mirror back and probe deeper
        lines = [f"I hear you: \"{text.strip()}\"\n"]

        # Surface assumptions
        assumptions = self._detect_assumptions(text)
        if assumptions:
            lines.append("I notice some assumptions that might be worth examining:")
            for a in assumptions:
                lines.append(f"  ⚡ {a}")
            lines.append("")

        # Generate follow-up questions based on what they said
        questions = self._generate_questions(text)
        if questions:
            lines.append("This makes me want to ask:")
            for q in questions:
                lines.append(f"  ? {q}")

        return "\n".join(lines)

    def surface_options(self) -> str:
        """Help enumerate the actual options."""
        if not self.current:
            return "[ERROR] No active decision. Use 'new:<decision>' to start."

        d = self.current
        context_summary = " | ".join(d.context[-5:]) if d.context else "(no context shared yet)"

        lines = [f"═══ OPTIONS FOR: {d.statement} ═══\n"]

        if d.options:
            lines.append("Options identified so far:")
            for i, o in enumerate(d.options, 1):
                lines.append(f"  {i}. {o}")
            lines.append("")

        lines.append("To find options you haven't considered:\n")
        lines.append("  • What would you do if money weren't a constraint?")
        lines.append("  • What would you do if you knew you couldn't fail?")
        lines.append("  • What would the person you admire most do?")
        lines.append("  • Is there an option where you don't have to choose — where you can test first?")
        lines.append("  • What's the 'do nothing' option actually look like in 6 months?")
        lines.append(f"\nAdd options with 'option:<description>'")

        return "\n".join(lines)

    def add_option(self, option: str) -> str:
        """Add an option to the current decision."""
        if not self.current:
            return "[ERROR] No active decision."
        self.current.options.append(option.strip())
        self._save()
        return f"Option added: {option.strip()} ({len(self.current.options)} total)"

    def reframe(self) -> str:
        """Show the decision from multiple angles."""
        if not self.current:
            return "[ERROR] No active decision."

        d = self.current
        lines = [f"═══ REFRAMING: {d.statement} ═══\n"]

        framings = [
            ("Time horizon", "How does this look in 1 week vs. 1 year vs. 10 years?"),
            ("Reversal", "How hard is it to undo this choice? Is this a one-way door or two-way?"),
            ("Regret minimization", "Which choice would you regret NOT making when you're 80?"),
            ("Identity", "What does each option say about who you want to be?"),
            ("Energy", "Which option gives you energy when you imagine living with it?"),
            ("Information", "What do you still not know? Could you find out before deciding?"),
            ("Stakes", "How high are the actual stakes? (Not how high they feel — how high they are.)"),
        ]

        for name, prompt in framings:
            lines.append(f"  [{name}]")
            lines.append(f"    {prompt}\n")

        if d.context:
            lines.append("Based on what you've shared:")
            lines.append(f"  You've mentioned: {', '.join(d.context[-3:])}")
            lines.append(f"  ⚠ I'm working only with what you've told me. I may be missing crucial context.\n")

        return "\n".join(lines)

    def add_fear(self, fear: str) -> str:
        """Record what they're afraid of."""
        if not self.current:
            return "[ERROR] No active decision."
        self.current.fears.append(fear.strip())
        self._save()
        return (f"Fear acknowledged: {fear.strip()}\n\n"
                f"Now — is this fear about probability (how likely is it?) "
                f"or severity (how bad would it be?)?\n"
                f"Often our fears are high-severity but low-probability.")

    def add_value(self, value: str) -> str:
        """Record what matters most to them."""
        if not self.current:
            return "[ERROR] No active decision."
        self.current.values.append(value.strip())
        self._save()
        return (f"Value noted: {value.strip()}\n"
                f"Values so far: {', '.join(self.current.values)}\n\n"
                f"If two of these values conflict, which one wins?")

    def resolve(self, resolution: str) -> str:
        """Record the decision they made."""
        if not self.current:
            return "[ERROR] No active decision."
        self.current.status = "resolved"
        self.current.resolution = resolution.strip()
        self._save()

        d = self.current
        lines = [f"═══ RESOLVED: {d.statement} ═══\n",
                 f"Decision: {resolution.strip()}\n"]

        if d.values:
            lines.append(f"Values that guided this: {', '.join(d.values)}")
        if d.fears:
            lines.append(f"Fears you faced: {', '.join(d.fears)}")
        lines.append(f"\nContext pieces shared: {len(d.context)}")
        lines.append(f"Options considered: {len(d.options)}")
        lines.append(f"\nThis decision is recorded. You can revisit it later with 'history'.")

        self.current = None
        return "\n".join(lines)

    def history(self) -> str:
        """Show past decisions."""
        if not self.decisions:
            return "No decisions recorded yet."

        lines = ["═══ DECISION HISTORY ═══\n"]
        for d in self.decisions[-10:]:
            status_icon = "✓" if d.status == "resolved" else "…" if d.status == "open" else "✗"
            lines.append(f"  {status_icon} [{d.created[:10]}] {d.statement}")
            if d.resolution:
                lines.append(f"    → {d.resolution}")
        return "\n".join(lines)

    def summary(self) -> str:
        """Summarize the current decision state."""
        if not self.current:
            return "No active decision. Use 'new:<decision>' to start working through something."

        d = self.current
        lines = [f"═══ CURRENT DECISION ═══\n",
                 f"Question: {d.statement}\n"]
        if d.context:
            lines.append(f"Context shared: {len(d.context)} pieces")
            for c in d.context[-3:]:
                lines.append(f"  • {c[:80]}")
        if d.options:
            lines.append(f"\nOptions ({len(d.options)}):")
            for o in d.options:
                lines.append(f"  → {o}")
        if d.values:
            lines.append(f"\nValues: {', '.join(d.values)}")
        if d.fears:
            lines.append(f"Fears: {', '.join(d.fears)}")
        if d.assumptions:
            lines.append(f"Assumptions to examine: {', '.join(d.assumptions)}")

        lines.append(f"\n⚠ Reminder: I only know what you've shared. My blind spots are your blind spots.")
        return "\n".join(lines)

    # ── Internal helpers ──────────────────────────────────────────

    def _detect_assumptions(self, text: str) -> list[str]:
        """Simple heuristic detection of implicit assumptions."""
        assumptions = []
        text_lower = text.lower()

        # "I have to" / "I must" / "I need to" → Is that actually true?
        if any(phrase in text_lower for phrase in ["i have to", "i must", "i need to"]):
            assumptions.append("You said 'I have to' — is that a real constraint or a felt one?")

        # "Everyone" / "nobody" / "always" / "never" → Absolutism
        if any(word in text_lower for word in ["everyone", "nobody", "always", "never"]):
            assumptions.append("You used an absolute ('everyone/nobody/always/never') — is that literally true?")

        # "Should" → Whose expectation is this?
        if " should " in text_lower:
            assumptions.append("'Should' according to whom? Whose standard is this?")

        # "Can't" → Is this ability or permission?
        if "can't" in text_lower or "cannot" in text_lower:
            assumptions.append("'Can't' — do you mean you're unable, or that something prevents you?")

        # "Obviously" / "clearly" → Maybe not obvious to everyone
        if any(word in text_lower for word in ["obviously", "clearly", "of course"]):
            assumptions.append("What feels 'obvious' to you might not be — what if it's not obvious?")

        return assumptions[:3]  # Don't overwhelm

    def _generate_questions(self, text: str) -> list[str]:
        """Generate follow-up questions based on context."""
        questions = []
        text_lower = text.lower()

        if "money" in text_lower or "cost" in text_lower or "expensive" in text_lower:
            questions.append("What's the cost of NOT doing this?")

        if "time" in text_lower or "busy" in text_lower or "schedule" in text_lower:
            questions.append("If you had unlimited time, would the answer be different?")

        if "feel" in text_lower or "feeling" in text_lower:
            questions.append("Is this feeling information or noise? What is it trying to tell you?")

        if "risk" in text_lower or "safe" in text_lower:
            questions.append("What's the smallest version of this you could try to reduce uncertainty?")

        if "people" in text_lower or "they" in text_lower or "others" in text_lower:
            questions.append("Have you actually asked them what they think, or are you guessing?")

        if not questions:
            questions.append("What would make this decision easy?")
            questions.append("What information, if you had it, would resolve this immediately?")

        return questions[:3]


def decision_tool(command: str = "help") -> str:
    """Tool interface for the Decision Companion."""
    try:
        companion = DecisionCompanion()

        if not command or command == "help":
            return (
                "Decision Companion — Think through decisions clearly.\n\n"
                "Commands:\n"
                "  new:<decision>     — Start working through a decision\n"
                "  add:<context>      — Share more context\n"
                "  options            — Surface and enumerate choices\n"
                "  option:<choice>    — Add a specific option\n"
                "  reframe            — See the decision from different angles\n"
                "  fear:<what>        — Name what you're afraid of\n"
                "  value:<what>       — Name what matters most\n"
                "  resolve:<choice>   — Record your decision\n"
                "  summary            — Where are we now?\n"
                "  history            — Past decisions\n\n"
                "Example: new:Should I change careers?"
            )

        if command.startswith("new:"):
            statement = command[len("new:"):].strip()
            if not statement:
                return "[ERROR] Describe the decision you're facing."
            return companion.new_decision(statement)

        if command.startswith("add:"):
            text = command[len("add:"):].strip()
            if not text:
                return "[ERROR] Share some context about your decision."
            return companion.add_context(text)

        if command == "options":
            return companion.surface_options()

        if command.startswith("option:"):
            option = command[len("option:"):].strip()
            return companion.add_option(option)

        if command == "reframe":
            return companion.reframe()

        if command.startswith("fear:"):
            fear = command[len("fear:"):].strip()
            return companion.add_fear(fear)

        if command.startswith("value:"):
            value = command[len("value:"):].strip()
            return companion.add_value(value)

        if command.startswith("resolve:"):
            resolution = command[len("resolve:"):].strip()
            return companion.resolve(resolution)

        if command == "summary":
            return companion.summary()

        if command == "history":
            return companion.history()

        return decision_tool("help")
    except Exception as e:
        return f"[ERROR] Decision companion failed: {e}"